from FloatingPoint.FloatingPointTestCase import FloatingPointTestCase
from FloatingPoint.UnsignedDecimal import UnsignedDecimal


class FloatingPointTestCaseTests(FloatingPointTestCase):
    def testAssertFloatingPointEqualFirstPlusTolerance(self):
        self.assertFloatingPointEqual(UnsignedDecimal("1.1") + UnsignedDecimal("1e-50"), UnsignedDecimal("1.1"))

    def testAssertFloatingPointEqualFirstMinusTolerance(self):
        self.assertFloatingPointEqual(UnsignedDecimal("1.1") - UnsignedDecimal("1e-50"), UnsignedDecimal("1.1"))

    def testAssertFloatingPointEqualSecondPlusTolerance(self):
        self.assertFloatingPointEqual(UnsignedDecimal("1.1"), UnsignedDecimal("1.1") + UnsignedDecimal("1e-50"))

    def testAssertFloatingPointEqualSecondMinusTolerance(self):
        self.assertFloatingPointEqual(UnsignedDecimal("1.1"), UnsignedDecimal("1.1") - UnsignedDecimal("1e-50"))

    def testAssertFloatingPointEqualFirstPlusDeltaOverTolerance(self):
        is_assert_thrown: bool = False
        try:
            self.assertFloatingPointEqual(UnsignedDecimal("1.1") + UnsignedDecimal("1e-49"), UnsignedDecimal("1.1"))
        except AssertionError:
            is_assert_thrown = True
        self.assertTrue(is_assert_thrown)

    def testFailAssertFloatingPointEqualFirstMinusDeltaUnderTolerance(self):
        is_assert_thrown: bool = False
        try:
            self.assertFloatingPointEqual(UnsignedDecimal("1.1") - UnsignedDecimal("1e-49"), UnsignedDecimal("1.1"))
        except AssertionError:
            is_assert_thrown = True
        self.assertTrue(is_assert_thrown)

    def testFailAssertFloatingPointEqualSecondPlusDeltaOverTolerance(self):
        is_assert_thrown: bool = False
        try:
            self.assertFloatingPointEqual(UnsignedDecimal("1.1"), UnsignedDecimal("1.1") + UnsignedDecimal("1e-49"))
        except AssertionError:
            is_assert_thrown = True
        self.assertTrue(is_assert_thrown)

    def testFailAssertFloatingPointEqualSecondMinusDeltaUnderTolerance(self):
        is_assert_thrown: bool = False
        try:
            self.assertFloatingPointEqual(UnsignedDecimal("1.1"), UnsignedDecimal("1.1") - UnsignedDecimal("1e-49"))
        except AssertionError:
            is_assert_thrown = True
        self.assertTrue(is_assert_thrown)
