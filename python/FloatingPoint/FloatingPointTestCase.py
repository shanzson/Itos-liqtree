from unittest import TestCase

from FloatingPoint.UnsignedDecimal import UnsignedDecimal


class FloatingPointTestCase(TestCase):
    def assertFloatingPointEqual(self, first: UnsignedDecimal, second: UnsignedDecimal) -> bool:
        # self.assertAlmostEqual does a diff between the two numbers which may trigger the unsigned decimal exception

        tolerance = UnsignedDecimal("1e-50")
        pass_condition: bool = False

        if first > second:
            pass_condition = (second + tolerance >= first)
        elif second > first:
            pass_condition = (first + tolerance >= second)
        else:
            pass_condition = True

        if not pass_condition:
            self.fail("{0} not equal to {1}".format(first, second))