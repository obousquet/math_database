import unittest

from render_utils import match


class ReferenceListMatchingTests(unittest.TestCase):
    def test_scalar_reference_still_matches(self):
        self.assertTrue(match("#classes/median", {"id": 50, "short_name": "median"}, table="classes"))

    def test_reference_array_matches_any_member(self):
        refs = ["#classes/partial_cubes", "#classes/median"]
        self.assertTrue(match(refs, {"id": 50, "short_name": "median"}, table="classes"))
        self.assertFalse(match(refs, {"id": 80, "short_name": "trees"}, table="classes"))

    def test_reference_array_respects_table(self):
        refs = ["#invariants/ordering_width", "#classes/median"]
        self.assertFalse(match(refs, {"id": 2, "short_name": "ordering_width"}, table="classes"))
        self.assertTrue(match(refs, {"id": 2, "short_name": "ordering_width"}, table="invariants"))


if __name__ == "__main__":
    unittest.main()
