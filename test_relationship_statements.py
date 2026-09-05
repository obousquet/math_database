"""Regression tests for upper-bound orientation and logarithm arguments."""

import unittest

from render_utils import render_relationship_statement


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


if __name__ == "__main__":
    unittest.main()
