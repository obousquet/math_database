"""Regression tests for upper-bound orientation and logarithm arguments."""

import unittest
from unittest.mock import patch

from render_utils import render_card, render_relationship_statement


class Cache:
    def lookup(self, reference):
        return None, {"symbol": {"A": "$L^*$", "B": r"\mathrm{E}"}[reference]}


class LogUpperTests(unittest.TestCase):
    def statement(self, **kwargs):
        return render_relationship_statement(
            {"parameter_1_id": "A", "parameter_2_id": "B",
             "relationship_type": "log_upper", "short_name": "test", **kwargs},
            Cache(),
        )

    def test_shift_is_inside_log_and_symbols_are_normalized(self):
        result = self.statement(multiplicative_constant="1", logarithm_base="2", argument_shift="2")
        self.assertIn(r"$L^* \le \log_{2}\left(\mathrm{E} + (2)\right)$", result)
        self.assertNotIn("$$", result)

    def test_default_log_and_coefficient(self):
        self.assertIn(r"$L^* \le c\log\left(\mathrm{E}\right)$", self.statement())

    def test_negative_shift(self):
        self.assertIn(r"\log\left(\mathrm{E} - (1)\right)", self.statement(argument_shift="-1"))

    def test_zero_shift(self):
        self.assertNotIn("+ (0)", self.statement(argument_shift="0"))

    def test_functional_upper_is_not_rendered_as_affine_domination(self):
        result = self.statement(relationship_type="functional_upper")
        self.assertIn(r"$L^* \le f\left(\mathrm{E}\right)$", result)
        self.assertNotIn(r"\ge", result)

    def test_incomparability_scope_is_visible_and_legacy_is_unchanged(self):
        for strength, label in (("affine", "affinely incomparable"),
                                ("functional", "functionally incomparable"),
                                (None, "incomparable")):
            self.assertIn(r"\text{(" + label + ")}", self.statement(
                relationship_type="incomparable", incomparability_strength=strength))


class OptionalFieldTests(unittest.TestCase):
    def card(self, value, hide=True):
        with patch('render_utils.load_utils.get_table_entries_cache'):
            return render_card('tests', {'columns': [
                {'name': 'optional', 'label': 'Optional', 'type': 'integer', 'hide_when_empty': hide}
            ]}, {'id': 1, 'name': 'Test', 'optional': value}, '/unused')

    def test_opt_in_empty_fields_are_hidden(self):
        for value in (None, ''):
            self.assertNotIn('Optional:', self.card(value))
            self.assertIn('Optional:', self.card(value, hide=False))

    def test_zero_is_not_empty(self):
        self.assertIn('<strong>Optional:</strong> 0', self.card(0))
        self.assertIn('<strong>Optional:</strong> False', self.card(False))


if __name__ == "__main__":
    unittest.main()
