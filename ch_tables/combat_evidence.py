"""Offline, provenance-bound intake of human-transcribed fight recordings.

No video decoding, optical character recognition, client attachment, or game
mechanic inference. A checksum identifies local bytes; it never proves that
those bytes are genuine gameplay or that the transcription is complete.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import tempfile

from .combat_simulator import encounter_from_dict
from .combat_validation import load_observations, scenario_digest

MAX_JSON = 5_000_000
MAX_SOURCE = 5_000_000_000
MAX_EVENTS = 200_000
DAMAGE_KINDS = frozenset(("auto_damage", "skill_damage", "dot_damage",
                         "pet_damage", "enemy_damage"))
POTION_KINDS = frozenset(("hp_potion", "energy_potion"))
ENDING = {"window_end": "time_limit", "player_died": "player_died",
          "boss_killed": "boss_killed"}
EVENT_KINDS = DAMAGE_KINDS | POTION_KINDS | ENDING.keys()


def _json(path: Path, *, with_digest: bool = False):
    payload = path.read_bytes()
    if not 0 < len(payload) <= MAX_JSON:
        raise ValueError("JSON input must be 1..5MB")
    def reject_constant(value):
        raise ValueError(f"Nonfinite JSON number: {value}")
    doc = json.loads(payload.decode("utf-8"), parse_constant=reject_constant)
    if type(doc) is not dict:
        raise ValueError("Input JSON must be an object")
    return (doc, hashlib.sha256(payload).hexdigest()) if with_digest else doc


def _inside(root: Path, label: str) -> Path:
    if type(label) is not str or not label or Path(label).is_absolute() or \
       any(part in ("..", "") for part in Path(label).parts):
        raise ValueError("Evidence paths must be relative, without parent traversal")
    path = (root / label).resolve(strict=True)
    if not path.is_relative_to(root.resolve(strict=True)) or not path.is_file():
        raise ValueError("Evidence files must remain inside the manifest directory")
    return path


def _hash_file(path: Path, limit: int) -> str:
    size = path.stat().st_size
    if size < 1 or size > limit:
        raise ValueError("Evidence file empty or exceeds size limit")
    h = hashlib.sha256()
    with path.open("rb") as reader:
        for chunk in iter(lambda: reader.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _number(v, label: str) -> float:
    if type(v) not in (int, float) or not math.isfinite(v) or v < 0:
        raise ValueError(f"{label} must be a finite nonnegative number")
    return float(v)


def _transcript(raw: dict, horizon: float) -> tuple[dict, dict]:
    if set(raw) != {"schema_version", "duration_s", "events"} or \
       type(raw["schema_version"]) is not int or raw["schema_version"] != 1 or \
       type(raw["events"]) is not list:
        raise ValueError("Transcript schema requires version, duration and events")
    duration = _number(raw["duration_s"], "duration_s")
    if abs(duration - horizon) > 1e-6:
        raise ValueError("Transcription window differs from frozen scenario")
    events = raw["events"]
    if not 1 <= len(events) <= MAX_EVENTS:
        raise ValueError("At least one terminal event is required, event count bounded")
    total, enemy_total = 0.0, 0.0
    hp_pots = energy_pots = 0
    prev = -1.0
    ending = None
    breakdown: dict[str, float] = {name: 0.0 for name in DAMAGE_KINDS}
    for index, event in enumerate(events):
        if type(event) is not dict or not {"t_s", "type"} <= event.keys():
            raise ValueError(f"Event {index} missing time/type")
        kind = event["type"]
        if type(kind) is not str or kind not in EVENT_KINDS:
            raise ValueError(f"Event {index} has unsupported kind")
        needed = {"t_s", "type", "amount"} if kind in DAMAGE_KINDS else {"t_s", "type"}
        if set(event) != needed:
            raise ValueError(f"Event {index} has missing/extra fields")
        at = _number(event["t_s"], "t_s")
        if at < prev - 1e-9 or at > horizon + 1e-9 or ending is not None:
            raise ValueError("Events unordered, after terminal event, or outside window")
        prev = at
        if kind in DAMAGE_KINDS:
            amount = _number(event["amount"], "damage amount")
            breakdown[kind] += amount
            if kind == "enemy_damage":
                enemy_total += amount
            else:
                total += amount
        elif kind in POTION_KINDS:
            if kind == "hp_potion":
                hp_pots += 1
            else:
                energy_pots += 1
        else:
            ending = (ENDING[kind], at)
            if kind == "window_end" and abs(at - horizon) > 1e-6:
                raise ValueError("window_end must equal prechosen horizon")
    if ending is None:
        raise ValueError("Recording transcript must declare a terminal event")
    if not math.isfinite(total) or not math.isfinite(enemy_total):
        raise ValueError("Summed damage overflows")
    return {
        "duration_s": horizon, "elapsed_s": ending[1], "total_damage": total,
        "end_reason": ending[0], "hp_potions": hp_pots,
        "energy_potions": energy_pots,
    }, {"events": len(events), "damage_breakdown": breakdown,
         "enemy_damage": enemy_total}


def ingest(manifest_path: Path, scenario_path: Path) -> tuple[dict, dict]:
    """Convert offline observations to the exact existing validator schema."""
    manifest_path = Path(manifest_path)
    scenario = _json(Path(scenario_path))
    encounter = encounter_from_dict(scenario)
    manifest, manifest_hash = _json(manifest_path, with_digest=True)
    allowed = {"schema_version", "evidence_kind", "patch_id", "boss_id",
               "build_id", "sessions"}
    if set(manifest) != allowed or type(manifest["schema_version"]) is not int or \
       manifest["schema_version"] != 1 or type(manifest["sessions"]) is not list:
        raise ValueError("Unsupported manifest schema")
    kind = manifest["evidence_kind"]
    if kind not in ("synthetic", "recorded_gameplay"):
        raise ValueError("Manifest must declare synthetic or recorded_gameplay")
    if kind == "recorded_gameplay" and encounter.evidence != "observed":
        raise ValueError("Gameplay requires scenario with sourced, observed inputs")
    if kind == "synthetic" and encounter.evidence != "synthetic":
        raise ValueError("Synthetic data must use a synthetic scenario")
    if len(manifest["sessions"]) > 1000:
        raise ValueError("Too many sessions")
    root = manifest_path.resolve(strict=True).parent
    rows, receipts = [], []
    used_transcripts = set()
    for row in manifest["sessions"]:
        if type(row) is not dict or set(row) != {
                "session_id", "split", "recording_file", "transcript_file"}:
            raise ValueError("Session must identify local recording/transcript and split")
        source = _inside(root, row["recording_file"])
        transcript = _inside(root, row["transcript_file"])
        if source == transcript:
            raise ValueError("Source and transcript must be independent files")
        source_hash = _hash_file(source, MAX_SOURCE)
        transcript_doc, transcript_hash = _json(transcript, with_digest=True)
        if transcript_hash in used_transcripts:
            raise ValueError("Duplicate transcript content across sessions")
        used_transcripts.add(transcript_hash)
        summary, audit = _transcript(transcript_doc, encounter.duration_s)
        rows.append({"session_id": row["session_id"],
                     "recording_sha256": source_hash, "split": row["split"],
                     **summary})
        receipts.append({"session_id": row["session_id"],
                         "recording_sha256": source_hash,
                         "transcript_sha256": transcript_hash, **audit})
    digest = scenario_digest(scenario)
    bundle = {
        "schema_version": 1, "evidence_kind": kind,
        "patch_id": manifest["patch_id"], "boss_id": manifest["boss_id"],
        "build_id": manifest["build_id"], "scenario_sha256": digest,
        "frozen_model_sha256": digest, "sessions": rows,
    }
    load_observations(bundle)  # Run the full existing independent-session gate.
    receipt = {"schema_version": 1, "evidence_kind": kind,
               "scenario_sha256": digest,
               "manifest_sha256": manifest_hash,
               "session_receipts": receipts,
               "warning": "Checksums establish file identity, NOT gameplay authenticity, "
                          "complete transcription, patch accuracy, or true model calibration."}
    return bundle, receipt


def _write_atomic(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    data = (json.dumps(payload, indent=2, ensure_ascii=False,
                       allow_nan=False) + "\n").encode("utf-8")
    with tempfile.NamedTemporaryFile(mode="wb", dir=path.parent, prefix=".combat-",
                                     delete=False) as f:
        temp = Path(f.name)
        try:
            f.write(data)
            f.flush()
            os.fsync(f.fileno())
        except BaseException:
            temp.unlink(missing_ok=True)
            raise
    try:
        os.replace(temp, path)
    except BaseException:
        temp.unlink(missing_ok=True)
        raise


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--scenario", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    bundle, receipt = ingest(args.manifest, args.scenario)
    # The observations file is the commit marker. Do not write it unless every
    # source, transcript and full validator schema passes.
    _write_atomic(args.output.with_suffix(".receipt.json"), receipt)
    _write_atomic(args.output, bundle)
    print(json.dumps({"result": "validated_intake_not_game_calibration",
                      "sessions": len(bundle["sessions"]),
                      "output": str(args.output),
                      "receipt": str(args.output.with_suffix('.receipt.json'))}))


if __name__ == "__main__":
    main()