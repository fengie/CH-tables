"""Identifiable, robust CH stat scaling recovery from controlled observations.

Pure-stdlib exploratory estimator. Never treats one Codex build as a fitted law.
For large studies consider scipy.optimize.least_squares(loss="soft_l1")
and sklearn GroupKFold/IsotonicRegression; see docs/SCALING_RESEARCH.md.
"""
from __future__ import annotations

from dataclasses import dataclass
from math import isfinite, log, sqrt
from statistics import median
from random import Random
from typing import Iterable

BASE = ("intercept", "sqrt_strength", "sqrt_weapon_ability")
HINGE1 = "strength_hinge_3000"
HINGE2 = "strength_hinge_3300"


@dataclass(frozen=True)
class DamageObservation:
    strength: float
    weapon_ability: float
    physical: float
    elemental: float
    displayed: float
    group: str
    source: str = ""
    patch: str = ""
    character: str = ""

    def validate(self) -> None:
        if any(not isfinite(float(x)) for x in
               (self.strength, self.weapon_ability, self.physical,
                self.elemental, self.displayed)):
            raise ValueError("Non-finite observation")
        if min(self.strength, self.weapon_ability, self.elemental) < 0 or self.physical <= 0:
            raise ValueError("Invalid damage inputs")
        if not self.group:
            raise ValueError("A nonempty session/group ID is mandatory")

    @property
    def normalized_target(self) -> float:
        self.validate()
        return (self.displayed - self.elemental) / self.physical


def features(row: DamageObservation, names: tuple[str, ...]) -> tuple[float, ...]:
    row.validate()
    x = sqrt(row.strength)
    mapping = {
        "intercept": 1.0,
        "sqrt_strength": x,
        "sqrt_weapon_ability": sqrt(row.weapon_ability),
        HINGE1: max(0.0, x - sqrt(3000)),
        HINGE2: max(0.0, x - sqrt(3300)),
    }
    return tuple(mapping[n] for n in names)


def solve_linear(a: list[list[float]], b: list[float]) -> list[float]:
    """Pivoted elimination, fail closed on weakly identified equations."""
    n = len(b)
    if n == 0 or len(a) != n or any(len(row) != n for row in a):
        raise ValueError("Invalid linear system")
    aug = [list(a[i]) + [b[i]] for i in range(n)]
    scale = max(abs(v) for row in a for v in row) or 1.0
    for col in range(n):
        pivot = max(range(col, n), key=lambda k: abs(aug[k][col]))
        if abs(aug[pivot][col]) <= 1e-11 * scale:
            raise ValueError("Parameters not identifiable; vary stats/ability independently")
        aug[col], aug[pivot] = aug[pivot], aug[col]
        div = aug[col][col]
        for j in range(col, n + 1):
            aug[col][j] /= div
        for i in range(n):
            if i == col:
                continue
            factor = aug[i][col]
            for j in range(col, n + 1):
                aug[i][j] -= factor * aug[col][j]
    return [aug[i][-1] for i in range(n)]


def weighted_fit(xs: list[tuple[float, ...]], ys: list[float],
                 weights: list[float]) -> tuple[float, ...]:
    p = len(xs[0])
    gram = [[0.0] * p for _ in range(p)]
    rhs = [0.0] * p
    for x, y, w in zip(xs, ys, weights):
        for i in range(p):
            rhs[i] += w * x[i] * y
            for j in range(p):
                gram[i][j] += w * x[i] * x[j]
    return tuple(solve_linear(gram, rhs))


def auto_terms(rows: list[DamageObservation]) -> tuple[str, ...]:
    result = list(BASE)
    # Hinge identification requires multiple independent observations in each
    # segment, not merely one high-STR screenshot.
    if sum(3000 < r.strength <= 3300 for r in rows) >= 4 and \
       len({r.strength for r in rows if 3000 < r.strength <= 3300}) >= 3:
        result.append(HINGE1)
    if HINGE1 in result and sum(r.strength > 3300 for r in rows) >= 4 and \
       len({r.strength for r in rows if r.strength > 3300}) >= 3:
        result.append(HINGE2)
    return tuple(result)


@dataclass(frozen=True)
class FitResult:
    terms: tuple[str, ...]
    coefficients: tuple[float, ...]
    n: int
    groups: int
    in_sample_mae: float
    heldout_group_mae: float | None
    warning: str

    def predict(self, row: DamageObservation) -> float:
        return (sum(c * x for c, x in zip(self.coefficients, features(row, self.terms)))
                * row.physical + row.elemental)

    def as_dict(self) -> dict:
        return {
            "model": "continuous_segmented_sqrt_strength_weapon_ability",
            "terms": list(self.terms),
            "coefficients": dict(zip(self.terms, self.coefficients)),
            "n": self.n, "independent_groups": self.groups,
            "mae_displayed": self.in_sample_mae,
            "heldout_group_mae_displayed": self.heldout_group_mae,
            "warning": self.warning,
        }


def _fit_once(rows: list[DamageObservation],
              terms: tuple[str, ...]) -> tuple[float, ...]:
    if len(rows) < max(8, 2 * len(terms) + 2):
        raise ValueError("Insufficient observations for parameter fitting")
    xs = [features(r, terms) for r in rows]
    ys = [r.normalized_target for r in rows]
    # IRLS Huber loss with a deterministic, robust MAD scale.
    coeffs = weighted_fit(xs, ys, [1.0] * len(xs))
    for _ in range(40):
        residuals = [y - sum(c * x for c, x in zip(coeffs, row))
                     for y, row in zip(ys, xs)]
        center = median(residuals)
        sigma = max(1e-5, 1.4826 * median(abs(e - center) for e in residuals))
        cutoff = 1.345 * sigma
        weights = [min(1.0, cutoff / max(abs(e), 1e-15)) for e in residuals]
        new = weighted_fit(xs, ys, weights)
        if max(abs(a - b) for a, b in zip(new, coeffs)) < 1e-9:
            return new
        coeffs = new
    return coeffs


def fit_damage(rows: Iterable[DamageObservation],
               terms: tuple[str, ...] | None = None,
               validate_groups: bool = True) -> FitResult:
    samples = list(rows)
    for r in samples:
        r.validate()
    if not samples:
        raise ValueError("No recorded measurements")
    patches = {r.patch for r in samples if r.patch}
    if len(patches) > 1:
        raise ValueError("Mixed patches require separate calibration")
    terms = terms or auto_terms(samples)
    coeffs = _fit_once(samples, terms)
    provisional = FitResult(terms, coeffs, len(samples),
                            len({r.group for r in samples}), 0, None, "")
    mae = sum(abs(provisional.predict(r) - r.displayed) for r in samples) / len(samples)
    grouped = {r.group for r in samples}
    heldout = []
    if validate_groups and len(grouped) >= 3:
        # Leave-one-experiment-session-out, never random row-level leakage.
        for group in sorted(grouped):
            train = [r for r in samples if r.group != group]
            test = [r for r in samples if r.group == group]
            try:
                hold_coeffs = _fit_once(train, terms)
            except ValueError:
                continue
            check = FitResult(terms, hold_coeffs, len(train), 0, 0, None, "")
            heldout.extend(abs(check.predict(r) - r.displayed) for r in test)
    hold_mae = sum(heldout) / len(heldout) if heldout else None
    warning = (
        "Empirical candidate, not engine truth. High-STR hinges assume "
        "continuity. No extrapolation beyond observed strength/ability "
        "ranges; crit, hit chance, armor, resist, and attack speed excluded."
    )
    return FitResult(terms, coeffs, len(samples), len(grouped), mae, hold_mae, warning)


def grouped_bootstrap(rows: list[DamageObservation], trials: int = 200,
                      seed: int = 41) -> dict[str, tuple[float, float]]:
    """Group-resampled percentile uncertainty, not confidence from duplicated rows."""
    fit = fit_damage(rows)
    groups = sorted({r.group for r in rows})
    if len(groups) < 3:
        raise ValueError("Bootstrap needs >=3 independent measurement sessions")
    rng = Random(seed)
    draws = {name: [] for name in fit.terms}
    for _ in range(trials):
        chosen = [rng.choice(groups) for _ in groups]
        subset = [r for g in chosen for r in rows if r.group == g]
        try:
            coeff = _fit_once(subset, fit.terms)
        except ValueError:
            continue
        for name, value in zip(fit.terms, coeff):
            draws[name].append(value)
    if len(draws[fit.terms[0]]) < max(20, trials // 5):
        raise ValueError("Insufficient identifiable bootstrap resamples")
    def pct(x: list[float], q: float) -> float:
        seq = sorted(x)
        pos = (len(seq) - 1) * q
        lo = int(pos)
        hi = min(lo + 1, len(seq) - 1)
        return seq[lo] + (seq[hi] - seq[lo]) * (pos - lo)
    return {name: (pct(d, 0.025), pct(d, 0.975))
            for name, d in draws.items()}


def next_experiment(rows: list[DamageObservation],
                    candidates: list[DamageObservation],
                    terms: tuple[str, ...] | None = None) -> DamageObservation:
    """Greedy D-optimal candidate under current X'X, using determinant proxy.

    Maximizes det(X'X+lambda I) via the determinant lemma for a new x;
    before enough rows exist, ridge stabilizes the score. Candidate
    designs must be achievable controlled one-variable swaps.
    """
    if not candidates:
        raise ValueError("Need candidate test configurations")
    terms = terms or auto_terms(rows or candidates)
    n = len(terms)
    base = [features(r, terms) for r in rows]
    gram = [[sum(x[i] * x[j] for x in base) +
             (0.01 if i == j else 0.0) for j in range(n)] for i in range(n)]
    # Numerical inverse columns via stable pivoted Gaussian elimination.
    inverse = [solve_linear(gram, [1.0 if k == j else 0.0 for k in range(n)])
               for j in range(n)]
    def score(candidate: DamageObservation):
        x = features(candidate, terms)
        return log(1.0 + sum(x[i] * inverse[j][i] * x[j]
                             for i in range(n) for j in range(n)))
    return max(candidates, key=score)
