"""Deterministic Quna/Mileage calculations in integer cents; no external dependencies."""
from __future__ import annotations

def normalized(packs: list[dict], target_quna: int) -> list[dict]:
    assert target_quna > 0
    results = []
    for pack in packs:
        count = (target_quna + pack['quna'] - 1) // pack['quna']
        results.append({'id': pack['id'], 'count': count, 'usd_cents': count * pack['usd_cents'], 'quna': count * pack['quna'], 'mileage': count * pack['mileage']})
    return results

def optimize(packs: list[dict], budget_cents: int, mileage_weight: float) -> dict:
    """Optimize subjective Quna + weighted Mileage, ≤budget; prefer fewer transactions."""
    if not 0 <= budget_cents <= 100_000 or not 0 <= mileage_weight <= 1:
        raise ValueError('invalid optimizer input')
    scores = [-float('inf')] * (budget_cents + 1)
    counts = [10**10] * (budget_cents + 1)
    previous = [None] * (budget_cents + 1)
    scores[0], counts[0] = 0, 0
    for cents in range(budget_cents + 1):
        if scores[cents] < 0:
            continue
        for i, pack in enumerate(packs):
            nxt = cents + pack['usd_cents']
            if nxt > budget_cents:
                continue
            score = scores[cents] + pack['quna'] + mileage_weight * pack['mileage']
            num = counts[cents] + 1
            if score > scores[nxt] + 1e-8 or (abs(score - scores[nxt]) < 1e-8 and num < counts[nxt]):
                scores[nxt], counts[nxt], previous[nxt] = score, num, (cents, i)
    best = max(range(budget_cents + 1), key=lambda c: (scores[c], -c))
    purchase_counts = {p['id']: 0 for p in packs}
    cursor = best
    while cursor:
        entry = previous[cursor]
        assert entry is not None
        last, i = entry
        purchase_counts[packs[i]['id']] += 1
        cursor = last
    return {'spent_cents':best,'quna':sum(p['quna']*purchase_counts[p['id']] for p in packs),'mileage':sum(p['mileage']*purchase_counts[p['id']] for p in packs),'counts':purchase_counts,'utility':scores[best]}
