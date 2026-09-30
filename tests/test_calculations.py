import unittest

from ch_tables.calculations import (
    effective_dps,
    effective_dps_auto_only,
    effective_dps_with_deaths,
    required_uptime_to_match,
)
from ch_tables.data import RANGER, ROGUE, WARRIOR
from ch_tables.estimation import SURYA8_ESTIMATE, WARRIOR_CALIBRATION


class CalculationTests(unittest.TestCase):
    def test_rogue_90_percent_uptime(self):
        self.assertAlmostEqual(effective_dps(ROGUE, 0.90), 11697.93, places=2)

    def test_auto_only_20_percent_downtime(self):
        expected = 12997.7 - 5745.8 * 0.20
        self.assertAlmostEqual(effective_dps_auto_only(ROGUE, 0.20), expected, places=6)

    def test_three_deaths_20_seconds_each(self):
        result, uptime = effective_dps_with_deaths(
            ROGUE, fight_seconds=600, deaths=3, seconds_lost_per_death=20
        )
        self.assertAlmostEqual(uptime, 0.90)
        self.assertAlmostEqual(result, 11697.93, places=2)

    def test_ranger_95_percent_uptime_match(self):
        needed = required_uptime_to_match(ROGUE, RANGER, 0.95)
        self.assertAlmostEqual(needed, 0.9963316586780738, places=8)

    def test_warrior_calibration_has_three_sourced_points(self):
        self.assertEqual(len(WARRIOR_CALIBRATION), 3)
        self.assertTrue(all(point.source_url.startswith("https://the-codex.ch/") for point in WARRIOR_CALIBRATION))

    def test_surya8_practical_estimate(self):
        self.assertAlmostEqual(SURYA8_ESTIMATE.practical_dps, 11529.68018292683, places=6)
        self.assertAlmostEqual(SURYA8_ESTIMATE.auto_share, 0.489, places=6)
        self.assertAlmostEqual(SURYA8_ESTIMATE.auto_dps, 5638.01360945122, places=6)

    def test_surya8_empirical_range_contains_estimate(self):
        self.assertLessEqual(SURYA8_ESTIMATE.practical_dps_low, SURYA8_ESTIMATE.practical_dps)
        self.assertGreaterEqual(SURYA8_ESTIMATE.practical_dps_high, SURYA8_ESTIMATE.practical_dps)

    def test_warrior_build_has_no_missing_practical_metrics(self):
        self.assertIsNotNone(WARRIOR.practical_dps)
        self.assertIsNotNone(WARRIOR.auto_dps)
        self.assertGreater(WARRIOR.practical_dps, 0)
        self.assertGreater(WARRIOR.auto_dps, 0)


if __name__ == "__main__":
    unittest.main()
