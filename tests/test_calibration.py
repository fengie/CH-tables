"""Synthetic identifiability and leakage regression tests (no fake game fits)."""
import math
import unittest

from ch_tables.calibration import (
    DamageObservation, auto_terms, fit_damage, grouped_bootstrap,
    next_experiment, BASE, HINGE1, HINGE2,
)


def sample(n=45, outlier=False):
    rows = []
    for i in range(n):
        s = 120 + (i * 347) % 2400
        ability = 410 + (i * 971) % 5000
        phys = 120 + (i % 7) * 30
        elemental = (i % 3) * 130
        displayed = (
            (0.96523 + 0.159132 * math.sqrt(s) +
             0.05972 * math.sqrt(ability)) * phys + elemental
        )
        if outlier and i == 0:
            displayed += 6000
        rows.append(DamageObservation(
            s, ability, phys, elemental, displayed,
            group=f"session-{i % 5}", patch="6.x", source="synthetic",
        ))
    return rows


class CalibrationTests(unittest.TestCase):
    def test_recovers_independently_varied_known_coefficients(self):
        rows = sample()
        result = fit_damage(rows)
        self.assertEqual(result.terms, BASE)
        self.assertEqual(result.groups, 5)
        self.assertIsNotNone(result.heldout_group_mae)
        self.assertAlmostEqual(result.coefficients[0], 0.96523, places=5)
        self.assertAlmostEqual(result.coefficients[1], 0.159132, places=5)
        self.assertAlmostEqual(result.coefficients[2], 0.05972, places=5)
        self.assertLess(result.in_sample_mae, 0.0001)

    def test_robust_to_single_corrupt_character_capture(self):
        rows = sample(outlier=True)
        result = fit_damage(rows)
        self.assertAlmostEqual(result.coefficients[1], 0.159132, places=2)
        self.assertAlmostEqual(result.coefficients[2], 0.05972, places=2)

    def test_disallows_identifiability_without_independent_swaps(self):
        repeated = [
            DamageObservation(1000, 5000, 100, 390, 1000, group=str(i % 3))
            for i in range(15)
        ]
        with self.assertRaisesRegex(ValueError, "identifiable"):
            fit_damage(repeated)

    def test_mixed_patches_disallowed(self):
        observations = sample()
        observations[0] = DamageObservation(100, 200, 50, 0, 100, group="x", patch="7.x")
        with self.assertRaisesRegex(ValueError, "Mixed patches"):
            fit_damage(observations)

    def test_high_strength_hinges_are_continuous_candidate_not_truth(self):
        samples = []
        strengths = [900, 1800, 2300, 2900, 3000, 3100, 3200, 3300, 3400, 3500, 3700, 4000]
        for j in range(6):
            for i, s in enumerate(strengths):
                ability = 200 + ((i * 933 + j * 401) % 4900)
                x = math.sqrt(s)
                h1 = max(0, x - math.sqrt(3000))
                h2 = max(0, x - math.sqrt(3300))
                norm = 1 + .159132 * x + .05972 * math.sqrt(ability) - .106088 * h1 - .039783 * h2
                samples.append(DamageObservation(
                    s, ability, 300, 30, norm * 300 + 30, group=str(j), patch="fixture"
                ))
        self.assertEqual(auto_terms(samples), BASE + (HINGE1, HINGE2))
        result = fit_damage(samples)
        self.assertLess(result.in_sample_mae, .001)
        self.assertAlmostEqual(result.coefficients[3], -.106088, places=3)
        self.assertAlmostEqual(result.coefficients[4], -.039783, places=3)

    def test_group_bootstrap_and_candidate_selection(self):
        intervals = grouped_bootstrap(sample(), trials=60)
        self.assertIn("sqrt_strength", intervals)
        self.assertLessEqual(intervals["sqrt_strength"][0], .159132 + 1e-5)
        self.assertGreaterEqual(intervals["sqrt_strength"][1], .159132 - 1e-5)
        options = sample(5)
        candidate = next_experiment(sample(), options)
        self.assertIn(candidate, options)

    def test_rejects_empty_inputs(self):
        with self.assertRaises(ValueError):
            fit_damage([])
        with self.assertRaises(ValueError):
            next_experiment(sample(), [])


if __name__ == "__main__":
    unittest.main()
