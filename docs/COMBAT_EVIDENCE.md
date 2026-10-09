# Offline combat evidence intake — real recording acquisition boundary

**Status:** executable recording/transcription intake; **no current-patch Celtic Heroes gameplay sessions have been verified by this repository**. This is the next scientific data-collection step after [`COMBAT_VALIDATION.md`](COMBAT_VALIDATION.md), not a release of a calibrated DPS calculator.

The available public Codex calculator reports modeled *Practical Rotation Guide* DPS, not independently captured, timestamped player combat logs. Forum anecdotes do not pin the patch, rotation and enemy for a numerical training/holdout study. The project therefore must obtain authorized first-party recordings rather than presenting historical or synthetic figures as calibration evidence. No game-client injection, scraping, automatic control, session credentials or server packet collection is used.

## Capture protocol

1. Pick **one** boss, verified game version, class/build, loadout, skill priority, mount/pet state and combat policy. Specify a fixed fight horizon (e.g., `60` seconds) *before* recording. Ensure the scenario JSON explicitly supplies measured post-mitigation damage, hit chance, attacks, skill timings, cooldowns and resource inputs; it must be tagged `"evidence":"observed"` and carry an HTTPS source for the scenario **parameters**. A source URL alone does not validate the values.
2. Obtain permission to record your own client/gameplay. Record complete, independent runs with a visible timing reference. Prefer a private local video or exported player-visible combat log, with audio/chat/usernames hidden. Keep every original source file unchanged. Do not put original recordings, account details, usernames or private messages in Git.
3. Transcribe player-visible events and their timestamps, **without inventing missing damage or inferring unobserved ticks**. If damage numbers, attack attribution, duration, or potion counts cannot be read reliably, discard that run as incomplete. Mark the last event `window_end` at the preselected horizon, `player_died`, or `boss_killed`; no damage after the terminal event is allowed.
4. Assign each independent recording to `calibration` or `holdout` **before inspecting the held-out outcomes**. Keep a dated external record of the chosen split and frozen scenario SHA. The intake file's checksum **cannot prove chronology or blind design**. Do not tune on holdout sessions.
5. Run the intake and then the existing evaluator. Start with repeatable Rogue and resource-starved caster benchmarks, including separate shield/offhand and mount compatibility checks. Only report real-game calibration once independent traces and held-out error analyses support it.

## Local input contract

Put a `manifest.json`, the source recordings and their transcribed JSON files in the same private directory. Relative paths are required and cannot escape that directory, even through symlinks. Manifest and transcript JSON are limited to 5 MB each; original recordings are streamed in chunks and capped at 5 GB per file. Strict schemas deliberately exclude character names, account identifiers and free-text chat.

`manifest.json`:

```json
{
  "schema_version": 1,
  "evidence_kind": "recorded_gameplay",
  "patch_id": "MEASURED_PATCH_IDENTIFIER",
  "boss_id": "SOURCED_BOSS_ID",
  "build_id": "anonymous-build-01",
  "sessions": [
    {"session_id": "run-01", "split": "calibration", "recording_file": "run-01.mp4", "transcript_file": "run-01.json"},
    {"session_id": "run-02", "split": "holdout", "recording_file": "run-02.mp4", "transcript_file": "run-02.json"}
  ]
}
```

`run-01.json` is a **format example only** (numbers and events below are fabricated, not gameplay):

```json
{
  "schema_version": 1,
  "duration_s": 60,
  "events": [
    {"t_s": 2.3, "type": "auto_damage", "amount": 100},
    {"t_s": 3.0, "type": "skill_damage", "amount": 150},
    {"t_s": 11.0, "type": "hp_potion"},
    {"t_s": 60, "type": "window_end"}
  ]
}
```

Event types: `auto_damage`, `skill_damage`, `dot_damage`, `pet_damage`, `enemy_damage`, `hp_potion`, `energy_potion`, `player_died`, `boss_killed`, `window_end`. All outgoing damage is post-mitigation damage visible on your screen. `enemy_damage` is audited independently, never added to the player's damage. Damage events require `amount`; every other event forbids it. Times are seconds from fight start, sorted, within the fixed window. Exactly one final terminal event must appear; a full-window run ends at its prechosen horizon.

## Run

```bash
python -m ch_tables.combat_evidence \
  --manifest private-study/manifest.json \
  --scenario private-study/frozen_scenario.json \
  --output private-study/validated_observations.json

python -m ch_tables.combat_validation \
  --scenario private-study/frozen_scenario.json \
  --observations private-study/validated_observations.json \
  --seeds 128
```

The first command writes `validated_observations.receipt.json` (scenario/manifest SHA-256, recording/transcript digests and damage breakdown) and **last** writes `validated_observations.json` as the validated output marker. It uses safe temporary-file replacement. It never copies, parses, uploads, or publishes the recording bytes, and both outputs exclude local file paths.

A checksum ensures the same bytes can be checked later. It does **not** establish that a video is authentic, recorded on the claimed patch, complete, or correctly transcribed. The generated bundle is compatible with `combat_validation.evaluate_holdout`; its status remains `empirical_holdout_*_not_game_verified` until the evidence is independently validated. Synthetic tests stay `synthetic_regression_only`. A positive model score is not proof of accurate armor, cast interruption, buff stacking, mount usage or real BIS rankings.

**External research boundary:** [The Codex damage builder](https://the-codex.ch/damagebuilder) is a community model, not a timestamped first-party player trace. No current-patch, source-verifiable paired Rogue/caster logs were located during this implementation. Acquire consented recordings before calibrating.