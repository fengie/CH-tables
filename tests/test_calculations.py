import unittest

from ch_tables.calculations import (
    effective_dps,
    effective_dps_auto_only,
    effective_dps_with_deaths,
    required_uptime_to_match,
)
from ch_tables.data import RANGER, ROGUE


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


if __name__ == "__main__":
    unittest.main()
