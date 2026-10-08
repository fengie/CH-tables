import unittest
from ch_tables.companions import PetCandidate, pet_shortlist
from ch_tables.economy import EffortBudget


class CompanionTests(unittest.TestCase):
    def test_pet_candidates_need_measured_dps_and_release(self):
        config = EffortBudget(world="Epona", gold=1_000)
        pets = [
            PetCandidate("dragon", "Dragon", "Red", 200, item_id=1,
                         owned=True, measured_marginal_dps=75,
                         evidence_kind="observed",
                         evidence_url="https://example.org/actual-test"),
            PetCandidate("chicken", "Chicken", "Brown", 200, item_id=2,
                         owned=True, token_cost=32),
            PetCandidate("prototype", "Dragon", "Purple", 200, item_id=3,
                         owned=False, release_status="unverified",
                         measured_marginal_dps=999999,
                         evidence_kind="user_estimate"),
        ]
        result = pet_shortlist(pets, character_level=220, effort=config)
        self.assertEqual(len(result["ranked_measured_pets"]), 1)
        self.assertEqual(result["default_pet_ranking"]["pet"], "dragon")
        self.assertEqual(result["feasible_but_unmeasured_pets"][0]["pet"], "chicken")
        self.assertEqual(result["ineligible_pets"][0]["pet"], "prototype")

    def test_token_budget_and_level_limit(self):
        pets = [
            PetCandidate("cheap", "Wolf", "Brown", 200, owned=True,
                         measured_marginal_dps=10, evidence_kind="user_estimate"),
            PetCandidate("premium", "Wolf", "Golden", 240, owned=False,
                         token_cost=128,
                         measured_marginal_dps=200,
                         evidence_kind="community_model"),
            PetCandidate("token_farm", "Wolf", "Grey", 200,
                         token_cost=128, item_id=4,
                         release_status="released_documented",
                         measured_marginal_dps=100,
                         evidence_kind="user_estimate"),
        ]
        result = pet_shortlist(pets, character_level=220,
                               effort=EffortBudget(world="Sulis", gold=200),
                               owned_pet_tokens=32)
        self.assertEqual(len(result["ranked_measured_pets"]), 1)
        self.assertEqual(len(result["ineligible_pets"]), 2)

    def test_cannot_claim_unknown_pet_dps(self):
        with self.assertRaisesRegex(ValueError, "unmeasured"):
            PetCandidate("fake", "Dragon", "Red", 1, owned=True,
                         measured_marginal_dps=1000)


if __name__ == "__main__":
    unittest.main()
