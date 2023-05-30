from unittest import TestCase

from Bucket.LiquidityBucket import LiquidityBucket, Snapshot
from ILiquidity import *
from UnsignedDecimal import UnsignedDecimal
from LiquidityExceptions import *


class TestLiquidityBucket(TestCase):
    def setUp(self) -> None:
        self.liq_bucket = LiquidityBucket(size=16)

    # region Floating Point Helpers
        
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
        try: self.assertFloatingPointEqual(UnsignedDecimal("1.1") + UnsignedDecimal("1e-49"), UnsignedDecimal("1.1"))
        except AssertionError: is_assert_thrown = True
        self.assertTrue(is_assert_thrown)

    def testFailAssertFloatingPointEqualFirstMinusDeltaUnderTolerance(self):
        is_assert_thrown: bool = False
        try: self.assertFloatingPointEqual(UnsignedDecimal("1.1") - UnsignedDecimal("1e-49"), UnsignedDecimal("1.1"))
        except AssertionError: is_assert_thrown = True
        self.assertTrue(is_assert_thrown)

    def testFailAssertFloatingPointEqualSecondPlusDeltaOverTolerance(self):
        is_assert_thrown: bool = False
        try: self.assertFloatingPointEqual(UnsignedDecimal("1.1"), UnsignedDecimal("1.1") + UnsignedDecimal("1e-49"))
        except AssertionError: is_assert_thrown = True
        self.assertTrue(is_assert_thrown)

    def testFailAssertFloatingPointEqualSecondMinusDeltaUnderTolerance(self):
        is_assert_thrown: bool = False
        try: self.assertFloatingPointEqual(UnsignedDecimal("1.1"), UnsignedDecimal("1.1") - UnsignedDecimal("1e-49"))
        except AssertionError: is_assert_thrown = True
        self.assertTrue(is_assert_thrown)


    # endregion

    # We can think of the liquidity tree as a state machine.
    # Describing that, each node has the following relationship.
    #
    #                addTLiq    => removeTLiq
    #   addMLiq =>
    #               removeMLiq
    #
    # Where the previous node must happen at least once,
    # Before it's valid to execute the next step.
    # At which point, it is (can be) valid to transition to any other node.
    # Of course, we need to test and protect against invalid transitions.
    # However, for the next few sections, we will take advantages of this fact.
    # Allowing us to simplify the scope of our focus, while testing all cases.

    # region add mLiq
    # Other liquidity methods are not valid before addingMLiq
    def test_add_m_liq_to_single_tick(self):
        (min_m_liq, acc_rate_x, acc_rate_y) = self.liq_bucket.add_m_liq(LiqRange(8, 8), UnsignedDecimal("1111"))
        self.assertEqual(min_m_liq, UnsignedDecimal("1111"))
        self.assertEqual(acc_rate_x, UnsignedDecimal("0"))
        self.assertEqual(acc_rate_y, UnsignedDecimal("0"))

        # Range mLiq was added
        (min_m_liq, max_t_liq) = self.liq_bucket.query_min_m_liq_max_t_liq(LiqRange(8, 8))
        self.assertEqual(min_m_liq, UnsignedDecimal("1111"))
        self.assertEqual(max_t_liq, UnsignedDecimal("0"))

        # Range covering range which mLiq was added
        (min_m_liq, max_t_liq) = self.liq_bucket.query_min_m_liq_max_t_liq(LiqRange(8, 11))
        self.assertEqual(min_m_liq, UnsignedDecimal("0"))
        self.assertEqual(max_t_liq, UnsignedDecimal("0"))

        # Range outside range which mLiq was added
        (min_m_liq, max_t_liq) = self.liq_bucket.query_min_m_liq_max_t_liq(LiqRange(1, 2))
        self.assertEqual(min_m_liq, UnsignedDecimal("0"))
        self.assertEqual(max_t_liq, UnsignedDecimal("0"))

        # Wide range
        (wide_min_m_liq, wide_max_t_liq) = self.liq_bucket.query_wide_min_m_liq_max_t_liq()
        self.assertEqual(wide_min_m_liq, UnsignedDecimal("0"))
        self.assertEqual(wide_max_t_liq, UnsignedDecimal("0"))

        # Verify that mLiq can accumulate, checking previous range(s) of accumulation
        (min_m_liq, acc_rate_x, acc_rate_y) = self.liq_bucket.add_m_liq(LiqRange(8, 8), UnsignedDecimal("20"))
        self.assertEqual(min_m_liq, UnsignedDecimal("1131"))
        self.assertEqual(acc_rate_x, UnsignedDecimal("0"))
        self.assertEqual(acc_rate_y, UnsignedDecimal("0"))

        (min_m_liq, _) = self.liq_bucket.query_min_m_liq_max_t_liq(LiqRange(8, 8))
        self.assertEqual(min_m_liq, UnsignedDecimal("1131"))

    def test_add_m_liq_to_multiple_independent_ticks(self):
        (min_m_liq, acc_rate_x, acc_rate_y) = self.liq_bucket.add_m_liq(LiqRange(8, 10), UnsignedDecimal("456"))
        self.assertEqual(min_m_liq, UnsignedDecimal("456"))
        self.assertEqual(acc_rate_x, UnsignedDecimal("0"))
        self.assertEqual(acc_rate_y, UnsignedDecimal("0"))

        (min_m_liq, acc_rate_x, acc_rate_y) = self.liq_bucket.add_m_liq(LiqRange(12, 14), UnsignedDecimal("123"))
        self.assertEqual(min_m_liq, UnsignedDecimal("123"))
        self.assertEqual(acc_rate_x, UnsignedDecimal("0"))
        self.assertEqual(acc_rate_y, UnsignedDecimal("0"))

        # Ranges mLiq was added
        (min_m_liq, max_t_liq) = self.liq_bucket.query_min_m_liq_max_t_liq(LiqRange(8, 10))
        self.assertEqual(min_m_liq, UnsignedDecimal("456"))
        self.assertEqual(max_t_liq, UnsignedDecimal("0"))

        (min_m_liq, max_t_liq) = self.liq_bucket.query_min_m_liq_max_t_liq(LiqRange(12, 14))
        self.assertEqual(min_m_liq, UnsignedDecimal("123"))
        self.assertEqual(max_t_liq, UnsignedDecimal("0"))

        # Ranges covering ranges which mLiq was added
        (min_m_liq, max_t_liq) = self.liq_bucket.query_min_m_liq_max_t_liq(LiqRange(8, 11))
        self.assertEqual(min_m_liq, UnsignedDecimal("0"))
        self.assertEqual(max_t_liq, UnsignedDecimal("0"))

        (min_m_liq, max_t_liq) = self.liq_bucket.query_min_m_liq_max_t_liq(LiqRange(12, 15))
        self.assertEqual(min_m_liq, UnsignedDecimal("0"))
        self.assertEqual(max_t_liq, UnsignedDecimal("0"))

        # Range overlapping both ranges which mLiq was added
        (min_m_liq, max_t_liq) = self.liq_bucket.query_min_m_liq_max_t_liq(LiqRange(8, 14))
        self.assertEqual(min_m_liq, UnsignedDecimal("0"))
        self.assertEqual(max_t_liq, UnsignedDecimal("0"))

        # Wide range
        (wide_min_m_liq, wide_max_t_liq) = self.liq_bucket.query_wide_min_m_liq_max_t_liq()
        self.assertEqual(wide_min_m_liq, UnsignedDecimal("0"))
        self.assertEqual(wide_max_t_liq, UnsignedDecimal("0"))

        # Verify that mLiq can accumulate, checking previous range(s) of accumulation
        (min_m_liq, acc_rate_x, acc_rate_y) = self.liq_bucket.add_m_liq(LiqRange(8, 10), UnsignedDecimal("20"))
        self.assertEqual(min_m_liq, UnsignedDecimal("476"))
        self.assertEqual(acc_rate_x, UnsignedDecimal("0"))
        self.assertEqual(acc_rate_y, UnsignedDecimal("0"))

        (min_m_liq, _) = self.liq_bucket.query_min_m_liq_max_t_liq(LiqRange(8, 10))
        self.assertEqual(min_m_liq, UnsignedDecimal("476"))

        (min_m_liq, acc_rate_x, acc_rate_y) = self.liq_bucket.add_m_liq(LiqRange(12, 14), UnsignedDecimal("20"))
        self.assertEqual(min_m_liq, UnsignedDecimal("143"))
        self.assertEqual(acc_rate_x, UnsignedDecimal("0"))
        self.assertEqual(acc_rate_y, UnsignedDecimal("0"))

        (min_m_liq, _) = self.liq_bucket.query_min_m_liq_max_t_liq(LiqRange(12, 14))
        self.assertEqual(min_m_liq, UnsignedDecimal("143"))

    def test_add_m_liq_to_multiple_overlapping_ticks(self):
        (min_m_liq, acc_rate_x, acc_rate_y) = self.liq_bucket.add_m_liq(LiqRange(1, 4), UnsignedDecimal("22"))
        self.assertEqual(min_m_liq, UnsignedDecimal("22"))
        self.assertEqual(acc_rate_x, UnsignedDecimal("0"))
        self.assertEqual(acc_rate_y, UnsignedDecimal("0"))

        (min_m_liq, acc_rate_x, acc_rate_y) = self.liq_bucket.add_m_liq(LiqRange(3, 7), UnsignedDecimal("77"))
        self.assertEqual(min_m_liq, UnsignedDecimal("77"))
        self.assertEqual(acc_rate_x, UnsignedDecimal("0"))
        self.assertEqual(acc_rate_y, UnsignedDecimal("0"))

        # Query lower non-overlapping range
        (min_m_liq, max_t_liq) = self.liq_bucket.query_min_m_liq_max_t_liq(LiqRange(1, 2))
        self.assertEqual(min_m_liq, UnsignedDecimal("22"))
        self.assertEqual(max_t_liq, UnsignedDecimal("0"))

        # Query overlap between ranges
        (min_m_liq, max_t_liq) = self.liq_bucket.query_min_m_liq_max_t_liq(LiqRange(3, 4))
        self.assertEqual(min_m_liq, UnsignedDecimal("99"))
        self.assertEqual(max_t_liq, UnsignedDecimal("0"))

        # Query upper non-overlapping range
        (min_m_liq, max_t_liq) = self.liq_bucket.query_min_m_liq_max_t_liq(LiqRange(5, 7))
        self.assertEqual(min_m_liq, UnsignedDecimal("77"))
        self.assertEqual(max_t_liq, UnsignedDecimal("0"))

        # Wide range
        (wide_min_m_liq, wide_max_t_liq) = self.liq_bucket.query_wide_min_m_liq_max_t_liq()
        self.assertEqual(wide_min_m_liq, UnsignedDecimal("0"))
        self.assertEqual(wide_max_t_liq, UnsignedDecimal("0"))

        # Verify that min_m_liq can accumulate
        (min_m_liq, acc_rate_x, acc_rate_y) = self.liq_bucket.add_m_liq(LiqRange(1, 4), UnsignedDecimal(5))
        self.assertEqual(min_m_liq, UnsignedDecimal("27"))
        self.assertEqual(acc_rate_x, UnsignedDecimal("0"))
        self.assertEqual(acc_rate_y, UnsignedDecimal("0"))

        (min_m_liq, acc_rate_x, acc_rate_y) = self.liq_bucket.add_m_liq(LiqRange(3, 7), UnsignedDecimal(7))
        self.assertEqual(min_m_liq, UnsignedDecimal("84"))
        self.assertEqual(acc_rate_x, UnsignedDecimal("0"))
        self.assertEqual(acc_rate_y, UnsignedDecimal("0"))

        (min_m_liq, _) = self.liq_bucket.query_min_m_liq_max_t_liq(LiqRange(1, 2))
        self.assertEqual(min_m_liq, UnsignedDecimal("27"))

        (min_m_liq, _) = self.liq_bucket.query_min_m_liq_max_t_liq(LiqRange(3, 4))
        self.assertEqual(min_m_liq, UnsignedDecimal("111"))

        (min_m_liq, _) = self.liq_bucket.query_min_m_liq_max_t_liq(LiqRange(5, 7))
        self.assertEqual(min_m_liq, UnsignedDecimal("84"))

    def test_add_m_liq_to_wide_range(self):
        (wide_min_m_liq, wide_acc_rate_x, wide_acc_rate_y) = self.liq_bucket.add_wide_m_liq(UnsignedDecimal("22"))
        self.assertEqual(wide_min_m_liq, UnsignedDecimal("22"))
        self.assertEqual(wide_acc_rate_x, UnsignedDecimal("0"))
        self.assertEqual(wide_acc_rate_y, UnsignedDecimal("0"))

        # Query wide Range
        (wide_min_m_liq, wide_max_t_liq) = self.liq_bucket.query_wide_min_m_liq_max_t_liq()
        self.assertEqual(wide_min_m_liq, UnsignedDecimal("22"))
        self.assertEqual(wide_max_t_liq, UnsignedDecimal("0"))

        # Query single tick range
        (min_m_liq, max_t_liq) = self.liq_bucket.query_min_m_liq_max_t_liq(LiqRange(5, 5))
        self.assertEqual(min_m_liq, UnsignedDecimal("22"))
        self.assertEqual(max_t_liq, UnsignedDecimal("0"))

        # Query multi tick range
        (min_m_liq, max_t_liq) = self.liq_bucket.query_min_m_liq_max_t_liq(LiqRange(2, 10))
        self.assertEqual(min_m_liq, UnsignedDecimal("22"))
        self.assertEqual(max_t_liq, UnsignedDecimal("0"))

        # Verify wide_min_m_liq can be accumulated
        (wide_min_m_liq, wide_acc_rate_x, wide_acc_rate_y) = self.liq_bucket.add_wide_m_liq(UnsignedDecimal(1))
        self.assertEqual(wide_min_m_liq, UnsignedDecimal("23"))
        self.assertEqual(wide_acc_rate_x, UnsignedDecimal("0"))
        self.assertEqual(wide_acc_rate_y, UnsignedDecimal("0"))

        (min_m_liq, _) = self.liq_bucket.query_min_m_liq_max_t_liq(LiqRange(5, 5))
        self.assertEqual(min_m_liq, UnsignedDecimal("23"))

        (min_m_liq, _) = self.liq_bucket.query_min_m_liq_max_t_liq(LiqRange(2, 10))
        self.assertEqual(min_m_liq, UnsignedDecimal("23"))

    def test_add_m_liq_to_wide_range_and_limited_range(self):
        (wide_min_m_liq, wide_acc_rate_x, wide_acc_rate_y) = self.liq_bucket.add_wide_m_liq(UnsignedDecimal(11))
        self.assertEqual(wide_min_m_liq, UnsignedDecimal("11"))
        self.assertEqual(wide_acc_rate_x, UnsignedDecimal("0"))
        self.assertEqual(wide_acc_rate_y, UnsignedDecimal("0"))

        (min_m_liq, acc_rate_x, acc_rate_y) = self.liq_bucket.add_m_liq(LiqRange(3, 7), UnsignedDecimal(8))
        self.assertEqual(min_m_liq, UnsignedDecimal("19"))
        self.assertEqual(acc_rate_x, UnsignedDecimal("0"))
        self.assertEqual(acc_rate_y, UnsignedDecimal("0"))

        # Query wide Range
        (wide_min_m_liq, wide_max_t_liq) = self.liq_bucket.query_wide_min_m_liq_max_t_liq()
        self.assertEqual(wide_min_m_liq, UnsignedDecimal("11"))
        self.assertEqual(wide_max_t_liq, UnsignedDecimal("0"))

        # Query single tick range outside overlap
        (min_m_liq, max_t_liq) = self.liq_bucket.query_min_m_liq_max_t_liq(LiqRange(1, 1))
        self.assertEqual(min_m_liq, UnsignedDecimal("11"))
        self.assertEqual(max_t_liq, UnsignedDecimal("0"))

        # Query single tick range in overlap
        (min_m_liq, max_t_liq) = self.liq_bucket.query_min_m_liq_max_t_liq(LiqRange(5, 5))
        self.assertEqual(min_m_liq, UnsignedDecimal("19"))
        self.assertEqual(max_t_liq, UnsignedDecimal("0"))

        # Query multi tick range outside overlap
        (min_m_liq, max_t_liq) = self.liq_bucket.query_min_m_liq_max_t_liq(LiqRange(0, 2))
        self.assertEqual(min_m_liq, UnsignedDecimal("11"))
        self.assertEqual(max_t_liq, UnsignedDecimal("0"))

        # Query multi tick range in lower partial overlap
        (min_m_liq, max_t_liq) = self.liq_bucket.query_min_m_liq_max_t_liq(LiqRange(1, 5))
        self.assertEqual(min_m_liq, UnsignedDecimal("11"))
        self.assertEqual(max_t_liq, UnsignedDecimal("0"))

        # Query multi tick range in overlap
        (min_m_liq, max_t_liq) = self.liq_bucket.query_min_m_liq_max_t_liq(LiqRange(4, 6))
        self.assertEqual(min_m_liq, UnsignedDecimal("19"))
        self.assertEqual(max_t_liq, UnsignedDecimal("0"))

        # Query multi tick range in upper partial overlap
        (min_m_liq, max_t_liq) = self.liq_bucket.query_min_m_liq_max_t_liq(LiqRange(4, 10))
        self.assertEqual(min_m_liq, UnsignedDecimal("11"))
        self.assertEqual(max_t_liq, UnsignedDecimal("0"))

        # Verify that mLiq can accumulate, checking previous range(s) of accumulation
        (wide_min_m_liq, wide_acc_rate_x, wide_acc_rate_y) = self.liq_bucket.add_wide_m_liq(UnsignedDecimal("3"))
        self.assertEqual(wide_min_m_liq, UnsignedDecimal("14"))
        self.assertEqual(wide_acc_rate_x, UnsignedDecimal("0"))
        self.assertEqual(wide_acc_rate_y, UnsignedDecimal("0"))

        (min_m_liq, acc_rate_x, acc_rate_y) = self.liq_bucket.add_m_liq(LiqRange(3, 4), UnsignedDecimal("8"))
        self.assertEqual(min_m_liq, UnsignedDecimal("30"))
        self.assertEqual(acc_rate_x, UnsignedDecimal("0"))
        self.assertEqual(acc_rate_y, UnsignedDecimal("0"))

        (wide_min_m_liq, _) = self.liq_bucket.query_wide_min_m_liq_max_t_liq()
        self.assertEqual(wide_min_m_liq, UnsignedDecimal("14"))

        (min_m_liq, _) = self.liq_bucket.query_min_m_liq_max_t_liq(LiqRange(3, 3))
        self.assertEqual(min_m_liq, UnsignedDecimal("30"))

        (min_m_liq, _) = self.liq_bucket.query_min_m_liq_max_t_liq(LiqRange(3, 4))
        self.assertEqual(min_m_liq, UnsignedDecimal("30"))

        (min_m_liq, _) = self.liq_bucket.query_min_m_liq_max_t_liq(LiqRange(3, 6))
        self.assertEqual(min_m_liq, UnsignedDecimal("22"))

        (min_m_liq, _) = self.liq_bucket.query_min_m_liq_max_t_liq(LiqRange(3, 11))
        self.assertEqual(min_m_liq, UnsignedDecimal("14"))

    # endregion

    # region remove mLiq
    # Only addingMLiq is a valid liquidity action before removeMLiq

    def test_remove_m_liq_at_single_tick(self):
        (_, _, _) = self.liq_bucket.add_m_liq(LiqRange(8, 8), UnsignedDecimal("1111"))
        (min_m_liq, acc_rate_x, acc_rate_y) = self.liq_bucket.remove_m_liq(LiqRange(8, 8), UnsignedDecimal("111"))
        self.assertEqual(min_m_liq, UnsignedDecimal("1000"))
        self.assertEqual(acc_rate_x, UnsignedDecimal("0"))
        self.assertEqual(acc_rate_y, UnsignedDecimal("0"))

        # Range mLiq was added
        (min_m_liq, max_t_liq) = self.liq_bucket.query_min_m_liq_max_t_liq(LiqRange(8, 8))
        self.assertEqual(min_m_liq, UnsignedDecimal("1000"))
        self.assertEqual(max_t_liq, UnsignedDecimal("0"))

        # Range covering range which mLiq was added
        (min_m_liq, max_t_liq) = self.liq_bucket.query_min_m_liq_max_t_liq(LiqRange(8, 11))
        self.assertEqual(min_m_liq, UnsignedDecimal("0"))
        self.assertEqual(max_t_liq, UnsignedDecimal("0"))

        # Range outside range which mLiq was added
        (min_m_liq, max_t_liq) = self.liq_bucket.query_min_m_liq_max_t_liq(LiqRange(1, 2))
        self.assertEqual(min_m_liq, UnsignedDecimal("0"))
        self.assertEqual(max_t_liq, UnsignedDecimal("0"))

        # Wide range
        (wide_min_m_liq, wide_max_t_liq) = self.liq_bucket.query_wide_min_m_liq_max_t_liq()
        self.assertEqual(wide_min_m_liq, UnsignedDecimal("0"))
        self.assertEqual(wide_max_t_liq, UnsignedDecimal("0"))

        # Verify that mLiq can accumulate, checking previous range(s) of accumulation
        (_, _, _) = self.liq_bucket.add_m_liq(LiqRange(8, 8), UnsignedDecimal("20"))
        (min_m_liq, acc_rate_x, acc_rate_y) = self.liq_bucket.remove_m_liq(LiqRange(8, 8), UnsignedDecimal("4"))
        self.assertEqual(min_m_liq, UnsignedDecimal("1016"))
        self.assertEqual(acc_rate_x, UnsignedDecimal("0"))
        self.assertEqual(acc_rate_y, UnsignedDecimal("0"))

        (min_m_liq, _) = self.liq_bucket.query_min_m_liq_max_t_liq(LiqRange(8, 8))
        self.assertEqual(min_m_liq, UnsignedDecimal("1016"))

    def test_remove_m_liq_at_multiple_independent_ticks(self):
        (_, _, _) = self.liq_bucket.add_m_liq(LiqRange(8, 10), UnsignedDecimal("456"))
        (min_m_liq, acc_rate_x, acc_rate_y) = self.liq_bucket.remove_m_liq(LiqRange(8, 10), UnsignedDecimal("56"))
        self.assertEqual(min_m_liq, UnsignedDecimal("400"))
        self.assertEqual(acc_rate_x, UnsignedDecimal("0"))
        self.assertEqual(acc_rate_y, UnsignedDecimal("0"))

        (_, _, _) = self.liq_bucket.add_m_liq(LiqRange(12, 14), UnsignedDecimal("123"))
        (min_m_liq, acc_rate_x, acc_rate_y) = self.liq_bucket.remove_m_liq(LiqRange(12, 14), UnsignedDecimal("23"))
        self.assertEqual(min_m_liq, UnsignedDecimal("100"))
        self.assertEqual(acc_rate_x, UnsignedDecimal("0"))
        self.assertEqual(acc_rate_y, UnsignedDecimal("0"))

        # Ranges mLiq was removed
        (min_m_liq, max_t_liq) = self.liq_bucket.query_min_m_liq_max_t_liq(LiqRange(8, 10))
        self.assertEqual(min_m_liq, UnsignedDecimal("400"))
        self.assertEqual(max_t_liq, UnsignedDecimal("0"))

        (min_m_liq, max_t_liq) = self.liq_bucket.query_min_m_liq_max_t_liq(LiqRange(12, 14))
        self.assertEqual(min_m_liq, UnsignedDecimal("100"))
        self.assertEqual(max_t_liq, UnsignedDecimal("0"))

        # Ranges covering ranges which mLiq was removed
        (min_m_liq, max_t_liq) = self.liq_bucket.query_min_m_liq_max_t_liq(LiqRange(8, 11))
        self.assertEqual(min_m_liq, UnsignedDecimal("0"))
        self.assertEqual(max_t_liq, UnsignedDecimal("0"))

        (min_m_liq, max_t_liq) = self.liq_bucket.query_min_m_liq_max_t_liq(LiqRange(12, 15))
        self.assertEqual(min_m_liq, UnsignedDecimal("0"))
        self.assertEqual(max_t_liq, UnsignedDecimal("0"))

        # Range overlapping both ranges which mLiq was removed
        (min_m_liq, max_t_liq) = self.liq_bucket.query_min_m_liq_max_t_liq(LiqRange(8, 14))
        self.assertEqual(min_m_liq, UnsignedDecimal("0"))
        self.assertEqual(max_t_liq, UnsignedDecimal("0"))

        # Wide range
        (wide_min_m_liq, wide_max_t_liq) = self.liq_bucket.query_wide_min_m_liq_max_t_liq()
        self.assertEqual(wide_min_m_liq, UnsignedDecimal("0"))
        self.assertEqual(wide_max_t_liq, UnsignedDecimal("0"))

        # Verify that mLiq can accumulate, checking previous range(s) of accumulation
        (min_m_liq, acc_rate_x, acc_rate_y) = self.liq_bucket.add_m_liq(LiqRange(8, 10), UnsignedDecimal("20"))
        (min_m_liq, acc_rate_x, acc_rate_y) = self.liq_bucket.remove_m_liq(LiqRange(8, 10), UnsignedDecimal("10"))
        self.assertEqual(min_m_liq, UnsignedDecimal("410"))
        self.assertEqual(acc_rate_x, UnsignedDecimal("0"))
        self.assertEqual(acc_rate_y, UnsignedDecimal("0"))

        (min_m_liq, _) = self.liq_bucket.query_min_m_liq_max_t_liq(LiqRange(8, 10))
        self.assertEqual(min_m_liq, UnsignedDecimal("410"))

        (min_m_liq, acc_rate_x, acc_rate_y) = self.liq_bucket.add_m_liq(LiqRange(12, 14), UnsignedDecimal("20"))
        (min_m_liq, acc_rate_x, acc_rate_y) = self.liq_bucket.remove_m_liq(LiqRange(12, 14), UnsignedDecimal("10"))
        self.assertEqual(min_m_liq, UnsignedDecimal("110"))
        self.assertEqual(acc_rate_x, UnsignedDecimal("0"))
        self.assertEqual(acc_rate_y, UnsignedDecimal("0"))

        (min_m_liq, _) = self.liq_bucket.query_min_m_liq_max_t_liq(LiqRange(12, 14))
        self.assertEqual(min_m_liq, UnsignedDecimal("110"))

    def test_remove_m_liq_to_multiple_overlapping_ticks(self):
        (_, _, _) = self.liq_bucket.add_m_liq(LiqRange(1, 4), UnsignedDecimal("22"))
        (min_m_liq, acc_rate_x, acc_rate_y) = self.liq_bucket.remove_m_liq(LiqRange(1, 4), UnsignedDecimal("2"))
        self.assertEqual(min_m_liq, UnsignedDecimal("20"))
        self.assertEqual(acc_rate_x, UnsignedDecimal("0"))
        self.assertEqual(acc_rate_y, UnsignedDecimal("0"))

        (_, _, _) = self.liq_bucket.add_m_liq(LiqRange(3, 7), UnsignedDecimal("77"))
        (min_m_liq, acc_rate_x, acc_rate_y) = self.liq_bucket.remove_m_liq(LiqRange(3, 7), UnsignedDecimal("7"))
        self.assertEqual(min_m_liq, UnsignedDecimal("70"))
        self.assertEqual(acc_rate_x, UnsignedDecimal("0"))
        self.assertEqual(acc_rate_y, UnsignedDecimal("0"))

        # Query lower non-overlapping range
        (min_m_liq, max_t_liq) = self.liq_bucket.query_min_m_liq_max_t_liq(LiqRange(1, 2))
        self.assertEqual(min_m_liq, UnsignedDecimal("20"))
        self.assertEqual(max_t_liq, UnsignedDecimal("0"))

        # Query overlap between ranges
        (min_m_liq, max_t_liq) = self.liq_bucket.query_min_m_liq_max_t_liq(LiqRange(3, 4))
        self.assertEqual(min_m_liq, UnsignedDecimal("90"))
        self.assertEqual(max_t_liq, UnsignedDecimal("0"))

        # Query upper non-overlapping range
        (min_m_liq, max_t_liq) = self.liq_bucket.query_min_m_liq_max_t_liq(LiqRange(5, 7))
        self.assertEqual(min_m_liq, UnsignedDecimal("70"))
        self.assertEqual(max_t_liq, UnsignedDecimal("0"))

        # Wide range
        (wide_min_m_liq, wide_max_t_liq) = self.liq_bucket.query_wide_min_m_liq_max_t_liq()
        self.assertEqual(wide_min_m_liq, UnsignedDecimal("0"))
        self.assertEqual(wide_max_t_liq, UnsignedDecimal("0"))

        # Verify that min_m_liq can accumulate
        (_, _, _) = self.liq_bucket.add_m_liq(LiqRange(1, 4), UnsignedDecimal("5"))
        (min_m_liq, acc_rate_x, acc_rate_y) = self.liq_bucket.remove_m_liq(LiqRange(1, 4), UnsignedDecimal("2"))
        self.assertEqual(min_m_liq, UnsignedDecimal("23"))
        self.assertEqual(acc_rate_x, UnsignedDecimal("0"))
        self.assertEqual(acc_rate_y, UnsignedDecimal("0"))

        (_, _, _) = self.liq_bucket.add_m_liq(LiqRange(3, 7), UnsignedDecimal(7))
        (min_m_liq, acc_rate_x, acc_rate_y) = self.liq_bucket.remove_m_liq(LiqRange(3, 7), UnsignedDecimal("1"))
        self.assertEqual(min_m_liq, UnsignedDecimal("76"))
        self.assertEqual(acc_rate_x, UnsignedDecimal("0"))
        self.assertEqual(acc_rate_y, UnsignedDecimal("0"))

        (min_m_liq, _) = self.liq_bucket.query_min_m_liq_max_t_liq(LiqRange(1, 2))
        self.assertEqual(min_m_liq, UnsignedDecimal("23"))

        (min_m_liq, _) = self.liq_bucket.query_min_m_liq_max_t_liq(LiqRange(3, 4))
        self.assertEqual(min_m_liq, UnsignedDecimal("99"))

        (min_m_liq, _) = self.liq_bucket.query_min_m_liq_max_t_liq(LiqRange(5, 7))
        self.assertEqual(min_m_liq, UnsignedDecimal("76"))

    def test_remove_m_liq_to_wide_range(self):
        (_, _, _) = self.liq_bucket.add_wide_m_liq(UnsignedDecimal("22"))
        (wide_min_m_liq, wide_acc_rate_x, wide_acc_rate_y) = self.liq_bucket.remove_wide_m_liq(UnsignedDecimal("2"))
        self.assertEqual(wide_min_m_liq, UnsignedDecimal("20"))
        self.assertEqual(wide_acc_rate_x, UnsignedDecimal("0"))
        self.assertEqual(wide_acc_rate_y, UnsignedDecimal("0"))

        # Query wide Range
        (wide_min_m_liq, wide_max_t_liq) = self.liq_bucket.query_wide_min_m_liq_max_t_liq()
        self.assertEqual(wide_min_m_liq, UnsignedDecimal("20"))
        self.assertEqual(wide_max_t_liq, UnsignedDecimal("0"))

        # Query single tick range
        (min_m_liq, max_t_liq) = self.liq_bucket.query_min_m_liq_max_t_liq(LiqRange(5, 5))
        self.assertEqual(min_m_liq, UnsignedDecimal("20"))
        self.assertEqual(max_t_liq, UnsignedDecimal("0"))

        # Query multi tick range
        (min_m_liq, max_t_liq) = self.liq_bucket.query_min_m_liq_max_t_liq(LiqRange(2, 10))
        self.assertEqual(min_m_liq, UnsignedDecimal("20"))
        self.assertEqual(max_t_liq, UnsignedDecimal("0"))

        # Verify wide_min_m_liq can be accumulated
        (_, _, _) = self.liq_bucket.add_wide_m_liq(UnsignedDecimal("8"))
        (wide_min_m_liq, wide_acc_rate_x, wide_acc_rate_y) = self.liq_bucket.remove_wide_m_liq(UnsignedDecimal("1"))
        self.assertEqual(wide_min_m_liq, UnsignedDecimal("27"))
        self.assertEqual(wide_acc_rate_x, UnsignedDecimal("0"))
        self.assertEqual(wide_acc_rate_y, UnsignedDecimal("0"))

        (min_m_liq, _) = self.liq_bucket.query_min_m_liq_max_t_liq(LiqRange(5, 5))
        self.assertEqual(min_m_liq, UnsignedDecimal("27"))

        (min_m_liq, _) = self.liq_bucket.query_min_m_liq_max_t_liq(LiqRange(2, 10))
        self.assertEqual(min_m_liq, UnsignedDecimal("27"))

    def test_remove_m_liq_to_wide_range_and_limited_range(self):
        (_, _, _) = self.liq_bucket.add_wide_m_liq(UnsignedDecimal("11"))
        (wide_min_m_liq, wide_acc_rate_x, wide_acc_rate_y) = self.liq_bucket.remove_wide_m_liq(UnsignedDecimal("3"))
        self.assertEqual(wide_min_m_liq, UnsignedDecimal("8"))
        self.assertEqual(wide_acc_rate_x, UnsignedDecimal("0"))
        self.assertEqual(wide_acc_rate_y, UnsignedDecimal("0"))

        (_, _, _) = self.liq_bucket.add_m_liq(LiqRange(3, 7), UnsignedDecimal("8"))
        (min_m_liq, acc_rate_x, acc_rate_y) = self.liq_bucket.remove_m_liq(LiqRange(3, 7), UnsignedDecimal("4"))
        self.assertEqual(min_m_liq, UnsignedDecimal("12"))
        self.assertEqual(acc_rate_x, UnsignedDecimal("0"))
        self.assertEqual(acc_rate_y, UnsignedDecimal("0"))

        # Query wide Range
        (wide_min_m_liq, wide_max_t_liq) = self.liq_bucket.query_wide_min_m_liq_max_t_liq()
        self.assertEqual(wide_min_m_liq, UnsignedDecimal("8"))
        self.assertEqual(wide_max_t_liq, UnsignedDecimal("0"))

        # Query single tick range outside overlap
        (min_m_liq, max_t_liq) = self.liq_bucket.query_min_m_liq_max_t_liq(LiqRange(1, 1))
        self.assertEqual(min_m_liq, UnsignedDecimal("8"))
        self.assertEqual(max_t_liq, UnsignedDecimal("0"))

        # Query single tick range in overlap
        (min_m_liq, max_t_liq) = self.liq_bucket.query_min_m_liq_max_t_liq(LiqRange(5, 5))
        self.assertEqual(min_m_liq, UnsignedDecimal("12"))
        self.assertEqual(max_t_liq, UnsignedDecimal("0"))

        # Query multi tick range outside overlap
        (min_m_liq, max_t_liq) = self.liq_bucket.query_min_m_liq_max_t_liq(LiqRange(0, 2))
        self.assertEqual(min_m_liq, UnsignedDecimal("8"))
        self.assertEqual(max_t_liq, UnsignedDecimal("0"))

        # Query multi tick range in lower partial overlap
        (min_m_liq, max_t_liq) = self.liq_bucket.query_min_m_liq_max_t_liq(LiqRange(1, 5))
        self.assertEqual(min_m_liq, UnsignedDecimal("8"))
        self.assertEqual(max_t_liq, UnsignedDecimal("0"))

        # Query multi tick range in overlap
        (min_m_liq, max_t_liq) = self.liq_bucket.query_min_m_liq_max_t_liq(LiqRange(4, 6))
        self.assertEqual(min_m_liq, UnsignedDecimal("12"))
        self.assertEqual(max_t_liq, UnsignedDecimal("0"))

        # Query multi tick range in upper partial overlap
        (min_m_liq, max_t_liq) = self.liq_bucket.query_min_m_liq_max_t_liq(LiqRange(4, 10))
        self.assertEqual(min_m_liq, UnsignedDecimal("8"))
        self.assertEqual(max_t_liq, UnsignedDecimal("0"))

        # Verify that mLiq can accumulate, checking previous range(s) of accumulation
        (_, _, _) = self.liq_bucket.add_wide_m_liq(UnsignedDecimal(3))
        (wide_min_m_liq, wide_acc_rate_x, wide_acc_rate_y) = self.liq_bucket.remove_wide_m_liq(UnsignedDecimal("2"))
        self.assertEqual(wide_min_m_liq, UnsignedDecimal("9"))
        self.assertEqual(wide_acc_rate_x, UnsignedDecimal("0"))
        self.assertEqual(wide_acc_rate_y, UnsignedDecimal("0"))

        (_, _, _) = self.liq_bucket.add_m_liq(LiqRange(3, 4), UnsignedDecimal("8"))
        (min_m_liq, acc_rate_x, acc_rate_y) = self.liq_bucket.remove_m_liq(LiqRange(3, 4), UnsignedDecimal("2"))
        self.assertEqual(min_m_liq, UnsignedDecimal("19"))
        self.assertEqual(acc_rate_x, UnsignedDecimal("0"))
        self.assertEqual(acc_rate_y, UnsignedDecimal("0"))

        (wide_min_m_liq, _) = self.liq_bucket.query_wide_min_m_liq_max_t_liq()
        self.assertEqual(wide_min_m_liq, UnsignedDecimal("9"))

        (min_m_liq, _) = self.liq_bucket.query_min_m_liq_max_t_liq(LiqRange(3, 3))
        self.assertEqual(min_m_liq, UnsignedDecimal("19"))

        (min_m_liq, _) = self.liq_bucket.query_min_m_liq_max_t_liq(LiqRange(3, 4))
        self.assertEqual(min_m_liq, UnsignedDecimal("19"))

        (min_m_liq, _) = self.liq_bucket.query_min_m_liq_max_t_liq(LiqRange(3, 6))
        self.assertEqual(min_m_liq, UnsignedDecimal("13"))

        (min_m_liq, _) = self.liq_bucket.query_min_m_liq_max_t_liq(LiqRange(3, 11))
        self.assertEqual(min_m_liq, UnsignedDecimal("9"))

    # endregion

    # region add tLiq (NEEDS ATTENTION)
    # Only addingMLiq is a valid liquidity action before removeMLiq

    def test_add_t_liq_to_single_tick(self):
        (min_m_liq, acc_rate_x, acc_rate_y) = self.liq_bucket.add_m_liq(LiqRange(8, 8), UnsignedDecimal(1111))
        self.assertEqual(min_m_liq, UnsignedDecimal(1111))
        self.assertEqual(acc_rate_x, UnsignedDecimal("0"))
        self.assertEqual(acc_rate_y, UnsignedDecimal("0"))

        max_t_liq = self.liq_bucket.add_t_liq(LiqRange(8, 8), UnsignedDecimal(34), UnsignedDecimal(1), UnsignedDecimal(3))
        self.assertEqual(max_t_liq, UnsignedDecimal(34))

        # Range mLiq + tLiq was added
        (min_m_liq, max_t_liq) = self.liq_bucket.query_min_m_liq_max_t_liq(LiqRange(8, 8))
        self.assertEqual(min_m_liq, UnsignedDecimal(1111))
        self.assertEqual(max_t_liq, UnsignedDecimal(34))

        # Range covering range which mLiq + tLiq was added
        (min_m_liq, max_t_liq) = self.liq_bucket.query_min_m_liq_max_t_liq(LiqRange(8, 11))
        self.assertEqual(min_m_liq, UnsignedDecimal("0"))
        self.assertEqual(max_t_liq, UnsignedDecimal(34))

        # Range outside range which mLiq + tLiq was added
        (min_m_liq, max_t_liq) = self.liq_bucket.query_min_m_liq_max_t_liq(LiqRange(1, 2))
        self.assertEqual(min_m_liq, UnsignedDecimal("0"))
        self.assertEqual(max_t_liq, UnsignedDecimal("0"))

        # Wide range
        (wide_min_m_liq, wide_max_t_liq) = self.liq_bucket.query_wide_min_m_liq_max_t_liq()
        self.assertEqual(wide_min_m_liq, UnsignedDecimal("0"))
        self.assertEqual(wide_max_t_liq, UnsignedDecimal(34))

        # Verify that mLiq can accumulate, checking previous range(s) of accumulation
        (min_m_liq, acc_rate_x, acc_rate_y) = self.liq_bucket.add_m_liq(LiqRange(8, 8), UnsignedDecimal(20))
        self.assertEqual(min_m_liq, UnsignedDecimal(1131))
        self.assertEqual(acc_rate_x, UnsignedDecimal("0"))
        self.assertEqual(acc_rate_y, UnsignedDecimal("0"))

        max_t_liq = self.liq_bucket.add_t_liq(LiqRange(8, 8), UnsignedDecimal(20), UnsignedDecimal(1), UnsignedDecimal(3))
        self.assertEqual(max_t_liq, UnsignedDecimal(54))

        (min_m_liq, max_t_liq) = self.liq_bucket.query_min_m_liq_max_t_liq(LiqRange(8, 8))
        self.assertEqual(min_m_liq, UnsignedDecimal(1131))
        self.assertEqual(max_t_liq, UnsignedDecimal(54))

    def test_add_t_liq_to_multiple_independent_ticks(self):
        (min_m_liq, acc_rate_x, acc_rate_y) = self.liq_bucket.add_m_liq(LiqRange(8, 10), UnsignedDecimal(456))
        self.assertEqual(min_m_liq, UnsignedDecimal(456))
        self.assertEqual(acc_rate_x, UnsignedDecimal("0"))
        self.assertEqual(acc_rate_y, UnsignedDecimal("0"))

        (min_m_liq, acc_rate_x, acc_rate_y) = self.liq_bucket.add_m_liq(LiqRange(12, 14), UnsignedDecimal(123))
        (min_m_liq, acc_rate_x, acc_rate_y) = self.liq_bucket.add_m_liq(LiqRange(12, 14), UnsignedDecimal(123))
        self.assertEqual(min_m_liq, UnsignedDecimal(123))
        self.assertEqual(acc_rate_x, UnsignedDecimal("0"))
        self.assertEqual(acc_rate_y, UnsignedDecimal("0"))

        # Ranges mLiq was added
        (min_m_liq, max_t_liq) = self.liq_bucket.query_min_m_liq_max_t_liq(LiqRange(8, 10))
        self.assertEqual(min_m_liq, UnsignedDecimal(456))
        self.assertEqual(max_t_liq, UnsignedDecimal("0"))

        (min_m_liq, max_t_liq) = self.liq_bucket.query_min_m_liq_max_t_liq(LiqRange(12, 14))
        self.assertEqual(min_m_liq, UnsignedDecimal(123))
        self.assertEqual(max_t_liq, UnsignedDecimal("0"))

        # Ranges covering ranges which mLiq was added
        (min_m_liq, max_t_liq) = self.liq_bucket.query_min_m_liq_max_t_liq(LiqRange(8, 11))
        self.assertEqual(min_m_liq, UnsignedDecimal("0"))
        self.assertEqual(max_t_liq, UnsignedDecimal("0"))

        (min_m_liq, max_t_liq) = self.liq_bucket.query_min_m_liq_max_t_liq(LiqRange(12, 15))
        self.assertEqual(min_m_liq, UnsignedDecimal("0"))
        self.assertEqual(max_t_liq, UnsignedDecimal("0"))

        # Range overlapping both ranges which mLiq was added
        (min_m_liq, max_t_liq) = self.liq_bucket.query_min_m_liq_max_t_liq(LiqRange(8, 14))
        self.assertEqual(min_m_liq, UnsignedDecimal("0"))
        self.assertEqual(max_t_liq, UnsignedDecimal("0"))

        # Wide range
        (wide_min_m_liq, wide_max_t_liq) = self.liq_bucket.query_wide_min_m_liq_max_t_liq()
        self.assertEqual(wide_min_m_liq, UnsignedDecimal("0"))
        self.assertEqual(wide_max_t_liq, UnsignedDecimal("0"))

        # Verify that mLiq can accumulate, checking previous range(s) of accumulation
        (min_m_liq, acc_rate_x, acc_rate_y) = self.liq_bucket.add_m_liq(LiqRange(8, 10), UnsignedDecimal(20))
        (min_m_liq, acc_rate_x, acc_rate_y) = self.liq_bucket.add_m_liq(LiqRange(8, 10), UnsignedDecimal(20))
        self.assertEqual(min_m_liq, UnsignedDecimal(476))
        self.assertEqual(acc_rate_x, UnsignedDecimal("0"))
        self.assertEqual(acc_rate_y, UnsignedDecimal("0"))

        (min_m_liq, _) = self.liq_bucket.query_min_m_liq_max_t_liq(LiqRange(8, 10))
        self.assertEqual(min_m_liq, UnsignedDecimal(476))

        (min_m_liq, acc_rate_x, acc_rate_y) = self.liq_bucket.add_m_liq(LiqRange(12, 14), UnsignedDecimal(20))
        (min_m_liq, acc_rate_x, acc_rate_y) = self.liq_bucket.add_m_liq(LiqRange(12, 14), UnsignedDecimal(20))
        self.assertEqual(min_m_liq, UnsignedDecimal(143))
        self.assertEqual(acc_rate_x, UnsignedDecimal("0"))
        self.assertEqual(acc_rate_y, UnsignedDecimal("0"))

        (min_m_liq, _) = self.liq_bucket.query_min_m_liq_max_t_liq(LiqRange(12, 14))
        self.assertEqual(min_m_liq, UnsignedDecimal(143))

    def test_add_t_liq_to_multiple_overlapping_ticks(self):
        (min_m_liq, acc_rate_x, acc_rate_y) = self.liq_bucket.add_m_liq(LiqRange(1, 4), UnsignedDecimal(22))
        self.assertEqual(min_m_liq, UnsignedDecimal(22))
        self.assertEqual(acc_rate_x, UnsignedDecimal("0"))
        self.assertEqual(acc_rate_y, UnsignedDecimal("0"))

        (min_m_liq, acc_rate_x, acc_rate_y) = self.liq_bucket.add_m_liq(LiqRange(3, 7), UnsignedDecimal(77))
        self.assertEqual(min_m_liq, UnsignedDecimal(77))
        self.assertEqual(acc_rate_x, UnsignedDecimal("0"))
        self.assertEqual(acc_rate_y, UnsignedDecimal("0"))

        # Query lower non-overlapping range
        (min_m_liq, max_t_liq) = self.liq_bucket.query_min_m_liq_max_t_liq(LiqRange(1, 2))
        self.assertEqual(min_m_liq, UnsignedDecimal(22))
        self.assertEqual(max_t_liq, UnsignedDecimal("0"))

        # Query overlap between ranges
        (min_m_liq, max_t_liq) = self.liq_bucket.query_min_m_liq_max_t_liq(LiqRange(3, 4))
        self.assertEqual(min_m_liq, UnsignedDecimal(99))
        self.assertEqual(max_t_liq, UnsignedDecimal("0"))

        # Query upper non-overlapping range
        (min_m_liq, max_t_liq) = self.liq_bucket.query_min_m_liq_max_t_liq(LiqRange(5, 7))
        self.assertEqual(min_m_liq, UnsignedDecimal(77))
        self.assertEqual(max_t_liq, UnsignedDecimal("0"))

        # Wide range
        (wide_min_m_liq, wide_max_t_liq) = self.liq_bucket.query_wide_min_m_liq_max_t_liq()
        self.assertEqual(wide_min_m_liq, UnsignedDecimal("0"))
        self.assertEqual(wide_max_t_liq, UnsignedDecimal("0"))

        # Verify that min_m_liq can accumulate
        (min_m_liq, acc_rate_x, acc_rate_y) = self.liq_bucket.add_m_liq(LiqRange(1, 4), UnsignedDecimal(5))
        self.assertEqual(min_m_liq, UnsignedDecimal(27))
        self.assertEqual(acc_rate_x, UnsignedDecimal("0"))
        self.assertEqual(acc_rate_y, UnsignedDecimal("0"))

        (min_m_liq, acc_rate_x, acc_rate_y) = self.liq_bucket.add_m_liq(LiqRange(3, 7), UnsignedDecimal(7))
        self.assertEqual(min_m_liq, UnsignedDecimal(84))
        self.assertEqual(acc_rate_x, UnsignedDecimal("0"))
        self.assertEqual(acc_rate_y, UnsignedDecimal("0"))

        (min_m_liq, _) = self.liq_bucket.query_min_m_liq_max_t_liq(LiqRange(1, 2))
        self.assertEqual(min_m_liq, UnsignedDecimal(27))

        (min_m_liq, _) = self.liq_bucket.query_min_m_liq_max_t_liq(LiqRange(3, 4))
        self.assertEqual(min_m_liq, UnsignedDecimal(111))

        (min_m_liq, _) = self.liq_bucket.query_min_m_liq_max_t_liq(LiqRange(5, 7))
        self.assertEqual(min_m_liq, UnsignedDecimal(84))

    def test_add_t_liq_to_wide_range(self):
        (wide_min_m_liq, wide_acc_rate_x, wide_acc_rate_y) = self.liq_bucket.add_wide_m_liq(UnsignedDecimal(22))
        self.assertEqual(wide_min_m_liq, UnsignedDecimal(22))
        self.assertEqual(wide_acc_rate_x, UnsignedDecimal("0"))
        self.assertEqual(wide_acc_rate_y, UnsignedDecimal("0"))

        # Query wide Range
        (wide_min_m_liq, wide_max_t_liq) = self.liq_bucket.query_wide_min_m_liq_max_t_liq()
        self.assertEqual(wide_min_m_liq, UnsignedDecimal(22))
        self.assertEqual(wide_max_t_liq, UnsignedDecimal("0"))

        # Query single tick range
        (min_m_liq, max_t_liq) = self.liq_bucket.query_min_m_liq_max_t_liq(LiqRange(5, 5))
        self.assertEqual(min_m_liq, UnsignedDecimal(22))
        self.assertEqual(max_t_liq, UnsignedDecimal("0"))

        # Query multi tick range
        (min_m_liq, max_t_liq) = self.liq_bucket.query_min_m_liq_max_t_liq(LiqRange(2, 10))
        self.assertEqual(min_m_liq, UnsignedDecimal(22))
        self.assertEqual(max_t_liq, UnsignedDecimal("0"))

        # Verify wide_min_m_liq can be accumulated
        (wide_min_m_liq, wide_acc_rate_x, wide_acc_rate_y) = self.liq_bucket.add_wide_m_liq(UnsignedDecimal(1))
        self.assertEqual(wide_min_m_liq, UnsignedDecimal(23))
        self.assertEqual(wide_acc_rate_x, UnsignedDecimal("0"))
        self.assertEqual(wide_acc_rate_y, UnsignedDecimal("0"))

        (min_m_liq, _) = self.liq_bucket.query_min_m_liq_max_t_liq(LiqRange(5, 5))
        self.assertEqual(min_m_liq, UnsignedDecimal(23))

        (min_m_liq, _) = self.liq_bucket.query_min_m_liq_max_t_liq(LiqRange(2, 10))
        self.assertEqual(min_m_liq, UnsignedDecimal(23))

    def test_add_t_liq_to_wide_range_and_limited_range(self):
        (wide_min_m_liq, wide_acc_rate_x, wide_acc_rate_y) = self.liq_bucket.add_wide_m_liq(UnsignedDecimal(11))
        self.assertEqual(wide_min_m_liq, UnsignedDecimal(11))
        self.assertEqual(wide_acc_rate_x, UnsignedDecimal("0"))
        self.assertEqual(wide_acc_rate_y, UnsignedDecimal("0"))

        (min_m_liq, acc_rate_x, acc_rate_y) = self.liq_bucket.add_m_liq(LiqRange(3, 7), UnsignedDecimal(8))
        self.assertEqual(min_m_liq, UnsignedDecimal(19))
        self.assertEqual(acc_rate_x, UnsignedDecimal("0"))
        self.assertEqual(acc_rate_y, UnsignedDecimal("0"))

        # Query wide Range
        (wide_min_m_liq, wide_max_t_liq) = self.liq_bucket.query_wide_min_m_liq_max_t_liq()
        self.assertEqual(wide_min_m_liq, UnsignedDecimal(11))
        self.assertEqual(wide_max_t_liq, UnsignedDecimal("0"))

        # Query single tick range outside overlap
        (min_m_liq, max_t_liq) = self.liq_bucket.query_min_m_liq_max_t_liq(LiqRange(1, 1))
        self.assertEqual(min_m_liq, UnsignedDecimal(11))
        self.assertEqual(max_t_liq, UnsignedDecimal("0"))

        # Query single tick range in overlap
        (min_m_liq, max_t_liq) = self.liq_bucket.query_min_m_liq_max_t_liq(LiqRange(5, 5))
        self.assertEqual(min_m_liq, UnsignedDecimal(19))
        self.assertEqual(max_t_liq, UnsignedDecimal("0"))

        # Query multi tick range outside overlap
        (min_m_liq, max_t_liq) = self.liq_bucket.query_min_m_liq_max_t_liq(LiqRange(0, 2))
        self.assertEqual(min_m_liq, UnsignedDecimal(11))
        self.assertEqual(max_t_liq, UnsignedDecimal("0"))

        # Query multi tick range in lower partial overlap
        (min_m_liq, max_t_liq) = self.liq_bucket.query_min_m_liq_max_t_liq(LiqRange(1, 5))
        self.assertEqual(min_m_liq, UnsignedDecimal(11))
        self.assertEqual(max_t_liq, UnsignedDecimal("0"))

        # Query multi tick range in overlap
        (min_m_liq, max_t_liq) = self.liq_bucket.query_min_m_liq_max_t_liq(LiqRange(4, 6))
        self.assertEqual(min_m_liq, UnsignedDecimal(19))
        self.assertEqual(max_t_liq, UnsignedDecimal("0"))

        # Query multi tick range in upper partial overlap
        (min_m_liq, max_t_liq) = self.liq_bucket.query_min_m_liq_max_t_liq(LiqRange(4, 10))
        self.assertEqual(min_m_liq, UnsignedDecimal(11))
        self.assertEqual(max_t_liq, UnsignedDecimal("0"))

        # Verify that mLiq can accumulate, checking previous range(s) of accumulation
        (wide_min_m_liq, wide_acc_rate_x, wide_acc_rate_y) = self.liq_bucket.add_wide_m_liq(UnsignedDecimal(3))
        self.assertEqual(wide_min_m_liq, UnsignedDecimal(14))
        self.assertEqual(wide_acc_rate_x, UnsignedDecimal("0"))
        self.assertEqual(wide_acc_rate_y, UnsignedDecimal("0"))

        (min_m_liq, acc_rate_x, acc_rate_y) = self.liq_bucket.add_m_liq(LiqRange(3, 4), UnsignedDecimal(8))
        self.assertEqual(min_m_liq, UnsignedDecimal(30))
        self.assertEqual(acc_rate_x, UnsignedDecimal("0"))
        self.assertEqual(acc_rate_y, UnsignedDecimal("0"))

        (wide_min_m_liq, _) = self.liq_bucket.query_wide_min_m_liq_max_t_liq()
        self.assertEqual(wide_min_m_liq, UnsignedDecimal(14))

        (min_m_liq, _) = self.liq_bucket.query_min_m_liq_max_t_liq(LiqRange(3, 3))
        self.assertEqual(min_m_liq, UnsignedDecimal(30))

        (min_m_liq, _) = self.liq_bucket.query_min_m_liq_max_t_liq(LiqRange(3, 4))
        self.assertEqual(min_m_liq, UnsignedDecimal(30))

        (min_m_liq, _) = self.liq_bucket.query_min_m_liq_max_t_liq(LiqRange(3, 6))
        self.assertEqual(min_m_liq, UnsignedDecimal(22))

        (min_m_liq, _) = self.liq_bucket.query_min_m_liq_max_t_liq(LiqRange(3, 11))
        self.assertEqual(min_m_liq, UnsignedDecimal(14))

    # endregion

    # region Fees

    # Naming below only mentions m_liq distribution.
    # But there are many ways fees can accumulate at different m_liq distributions.
    # We will test all cases within each method.
    # NOTE: m_liq distribution defines how fees can accumulate.
    # Without m_liq, a borrow can not occur. Meaning fees can not accumulate.
    # Therefore, to be exhaustive, we only need to check ranges surrounding the m_liq distribution.
    # Ex. wide, overlapping, non-overlapping, fully contained, exact

    # Remember, from the liquidity tree
    # totalMLiq = node.subtreeMLiq + A[level] * node.range
    # fees = borrow * rate / totalMLiq / Q192.64 conversion

    def test_fee_accumulation_with_m_liq_at_one_tick_over_one_range(self):
        self.liq_bucket.add_m_liq(LiqRange(8, 8), UnsignedDecimal("456"))
        self.liq_bucket.add_t_liq(LiqRange(8, 8), UnsignedDecimal("456"), UnsignedDecimal("7"), UnsignedDecimal("4"))

        self.liq_bucket.token_x_fee_rate_snapshot += UnsignedDecimal("74")
        self.liq_bucket.token_y_fee_rate_snapshot += UnsignedDecimal("374")

        # Querying the exact range (also fully contained)
        (acc_rate_x, acc_rate_y) = self.liq_bucket.query_accumulated_fee_rates(LiqRange(8, 8))
        self.assertFloatingPointEqual(acc_rate_x, UnsignedDecimal("1.1359649122807017543859649122807017543859649122807017543859649122"))  # 7 * 74 / 456
        self.assertFloatingPointEqual(acc_rate_y, UnsignedDecimal("3.2807017543859649122807017543859649122807017543859649122807017543"))  # 4 * 374 / 456

        # Querying an overlapping range
        (acc_rate_x, acc_rate_y) = self.liq_bucket.query_accumulated_fee_rates(LiqRange(4, 10))
        self.assertFloatingPointEqual(acc_rate_x, UnsignedDecimal("1.1359649122807017543859649122807017543859649122807017543859649122"))
        self.assertFloatingPointEqual(acc_rate_y, UnsignedDecimal("3.2807017543859649122807017543859649122807017543859649122807017543"))

        # Querying a non-overlapping range
        (acc_rate_x, acc_rate_y) = self.liq_bucket.query_accumulated_fee_rates(LiqRange(1, 2))
        self.assertFloatingPointEqual(acc_rate_x, UnsignedDecimal("0"))
        self.assertFloatingPointEqual(acc_rate_y, UnsignedDecimal("0"))

        # Querying the wide range
        (acc_rate_x, acc_rate_y) = self.liq_bucket.query_wide_accumulated_fee_rates()
        self.assertFloatingPointEqual(acc_rate_x, UnsignedDecimal("1.1359649122807017543859649122807017543859649122807017543859649122"))
        self.assertFloatingPointEqual(acc_rate_y, UnsignedDecimal("3.2807017543859649122807017543859649122807017543859649122807017543"))

    def test_fee_accumulation_with_m_liq_at_multiple_ticks_over_one_range(self):
        self.liq_bucket.add_m_liq(LiqRange(8, 12), UnsignedDecimal("1456"))
        self.liq_bucket.add_t_liq(LiqRange(8, 12), UnsignedDecimal("1456"), UnsignedDecimal("12"), UnsignedDecimal("36"))

        self.liq_bucket.token_x_fee_rate_snapshot += UnsignedDecimal("274")
        self.liq_bucket.token_y_fee_rate_snapshot += UnsignedDecimal("2374")

        # Querying the exact range
        (acc_rate_x, acc_rate_y) = self.liq_bucket.query_accumulated_fee_rates(LiqRange(8, 14))
        self.assertFloatingPointEqual(acc_rate_x, UnsignedDecimal("0.4516483516483516483516483516483516483516483516483516483516483516"))  # (5*12/5) * 274 / (1456*5)
        self.assertFloatingPointEqual(acc_rate_y, UnsignedDecimal("11.739560439560439560439560439560439560439560439560439560439560439"))  # (5*36/5) * 2374 / (1456*5)

        # Querying a fully contained range
        (acc_rate_x, acc_rate_y) = self.liq_bucket.query_accumulated_fee_rates(LiqRange(9, 10))
        self.assertFloatingPointEqual(acc_rate_x, UnsignedDecimal("0.1806593406593406593406593406593406593406593406593406593406593406"))  # (2/5) * 12 * 274 / (1456*5)
        self.assertFloatingPointEqual(acc_rate_y, UnsignedDecimal("4.6958241758241758241758241758241758241758241758241758241758241758"))  # (2/5) * 36 * 2374 / (1456*5)

        # Querying an overlapping range
        (acc_rate_x, acc_rate_y) = self.liq_bucket.query_accumulated_fee_rates(LiqRange(1, 10))
        self.assertFloatingPointEqual(acc_rate_x, UnsignedDecimal("0.2709890109890109890109890109890109890109890109890109890109890109"))  # (3/5) * 12 * 274 / (1456*5)
        self.assertFloatingPointEqual(acc_rate_y, UnsignedDecimal("7.0437362637362637362637362637362637362637362637362637362637362637"))  # (3/5) * 36 * 2374 / (1456*5)

        # Querying a non-overlapping range
        (acc_rate_x, acc_rate_y) = self.liq_bucket.query_accumulated_fee_rates(LiqRange(1, 2))
        self.assertFloatingPointEqual(acc_rate_x, UnsignedDecimal("0"))
        self.assertFloatingPointEqual(acc_rate_y, UnsignedDecimal("0"))

        # Querying the wide range
        (acc_rate_x, acc_rate_y) = self.liq_bucket.query_wide_accumulated_fee_rates()
        self.assertFloatingPointEqual(acc_rate_x, UnsignedDecimal("0.4516483516483516483516483516483516483516483516483516483516483516"))
        self.assertFloatingPointEqual(acc_rate_y, UnsignedDecimal("11.739560439560439560439560439560439560439560439560439560439560439"))

    def test_fee_accumulation_with_m_liq_over_wide_range(self):
        self.liq_bucket.add_wide_m_liq(UnsignedDecimal("300"))
        self.liq_bucket.add_wide_t_liq(UnsignedDecimal("200"), UnsignedDecimal("1600"), UnsignedDecimal("3200"))

        self.liq_bucket.token_x_fee_rate_snapshot += UnsignedDecimal("21")
        self.liq_bucket.token_y_fee_rate_snapshot += UnsignedDecimal("36")

        # Querying the exact range
        (acc_rate_x, acc_rate_y) = self.liq_bucket.query_accumulated_fee_rates(LiqRange(0, 15))
        self.assertFloatingPointEqual(acc_rate_x, UnsignedDecimal("7"))   # 1600 * 21 / (300*16)
        self.assertFloatingPointEqual(acc_rate_y, UnsignedDecimal("24"))  # 3200 * 36 / (300*16)

        # Querying a fully contained range
        # (overlapping and non-overlapping do not exist, so query a contained range over different ticks)
        (acc_rate_x, acc_rate_y) = self.liq_bucket.query_accumulated_fee_rates(LiqRange(9, 10))
        self.assertFloatingPointEqual(acc_rate_x, UnsignedDecimal("0.875"))  # 2/16 * 7
        self.assertFloatingPointEqual(acc_rate_y, UnsignedDecimal("3"))  # 2/16 * 24

        (acc_rate_x, acc_rate_y) = self.liq_bucket.query_accumulated_fee_rates(LiqRange(1, 10))
        self.assertFloatingPointEqual(acc_rate_x, UnsignedDecimal("4.375"))  # 10/16 * 7
        self.assertFloatingPointEqual(acc_rate_y, UnsignedDecimal("15"))  # 10/16 * 24

        # Querying the wide range
        (acc_rate_x, acc_rate_y) = self.liq_bucket.query_wide_accumulated_fee_rates()
        self.assertFloatingPointEqual(acc_rate_x, UnsignedDecimal("7"))
        self.assertFloatingPointEqual(acc_rate_y, UnsignedDecimal("24"))

    def test_fee_accumulation_with_m_liq_at_one_tick_over_multiple_non_overlapping_ranges(self):
        pass

    def test_fee_accumulation_with_m_liq_at_multiple_ticks_over_multiple_non_overlapping_ranges(self):
        # rx: 800 * 500 / (700*4) = 142.85714285714285714285714285714285714285714285714285714285714285
        # ry: 2400 * 1200 / (700*4) = 1028.5714285714285714285714285714285714285714285714285714285714285
        self.liq_bucket.add_m_liq(LiqRange(8, 11), UnsignedDecimal("700"))
        self.liq_bucket.add_t_liq(LiqRange(8, 11), UnsignedDecimal("400"), UnsignedDecimal("800"), UnsignedDecimal("2400"))

        # lx: 700 * 500 / (200*3) = 583.33333333333333333333333333333333333333333333333333333333333333
        # ly: 2700 * 1200 / (200*3) = 5400
        self.liq_bucket.add_m_liq(LiqRange(2, 4), UnsignedDecimal("200"))
        self.liq_bucket.add_t_liq(LiqRange(2, 4), UnsignedDecimal("1"), UnsignedDecimal("700"), UnsignedDecimal("2700"))

        self.liq_bucket.token_x_fee_rate_snapshot += UnsignedDecimal("500")
        self.liq_bucket.token_y_fee_rate_snapshot += UnsignedDecimal("1200")

        # Query partially overlapping the inside of both ranges
        (acc_rate_x, acc_rate_y) = self.liq_bucket.query_accumulated_fee_rates(LiqRange(4, 9))
        self.assertFloatingPointEqual(acc_rate_x, UnsignedDecimal("265.87301587301587301587301587301587301587301587301587301587301587"))  # (1/3) * lx + (2/4) * rx
        self.assertFloatingPointEqual(acc_rate_y, UnsignedDecimal("2314.2857142857142857142857142857142857142857142857142857142857142"))  # (1/3) * ly + (2/4) * ry

        # Query fully overlapping both ranges
        (acc_rate_x, acc_rate_y) = self.liq_bucket.query_accumulated_fee_rates(LiqRange(1, 13))
        self.assertFloatingPointEqual(acc_rate_x, UnsignedDecimal("726.19047619047619047619047619047619047619047619047619047619047619"))  # lx + rx
        self.assertFloatingPointEqual(acc_rate_y, UnsignedDecimal("6428.5714285714285714285714285714285714285714285714285714285714285"))  # ly + ry

        # Query partially overlapping the inside left range
        (acc_rate_x, acc_rate_y) = self.liq_bucket.query_accumulated_fee_rates(LiqRange(3, 7))
        self.assertFloatingPointEqual(acc_rate_x, UnsignedDecimal("388.88888888888888888888888888888888888888888888888888888888888888"))  # (2/3) * lx
        self.assertFloatingPointEqual(acc_rate_y, UnsignedDecimal("3600"))  # (2/3) * ly

        # Query partially overlapping the inside right range
        (acc_rate_x, acc_rate_y) = self.liq_bucket.query_accumulated_fee_rates(LiqRange(5, 10))
        self.assertFloatingPointEqual(acc_rate_x, UnsignedDecimal("107.14285714285714285714285714285714285714285714285714285714285714"))  # (3/4) * rx
        self.assertFloatingPointEqual(acc_rate_y, UnsignedDecimal("771.42857142857142857142857142857142857142857142857142857142857142"))  # (3/4) * ry

        # Querying the wide range
        (acc_rate_x, acc_rate_y) = self.liq_bucket.query_wide_accumulated_fee_rates()
        self.assertFloatingPointEqual(acc_rate_x, UnsignedDecimal("726.19047619047619047619047619047619047619047619047619047619047619"))  # lx + # rx
        self.assertFloatingPointEqual(acc_rate_y, UnsignedDecimal("6428.5714285714285714285714285714285714285714285714285714285714285"))  # lx + rx

    def test_fee_accumulation_with_m_liq_at_one_tick_over_multiple_overlapping_ranges(self):
        pass

    def test_fee_accumulation_with_m_liq_at_multiple_ticks_over_multiple_non_overlapping_ranges(self):
        self.liq_bucket.add_m_liq(LiqRange(1, 7), UnsignedDecimal(200))
        self.liq_bucket.add_t_liq(LiqRange(1, 7), UnsignedDecimal(100), UnsignedDecimal(500), UnsignedDecimal(300))

        self.liq_bucket.add_m_liq(LiqRange(3, 5), UnsignedDecimal(214))
        self.liq_bucket.add_t_liq(LiqRange(3, 5), UnsignedDecimal(410), UnsignedDecimal(98), UnsignedDecimal(17))

        self.liq_bucket.token_x_fee_rate_snapshot += UnsignedDecimal(533)
        self.liq_bucket.token_y_fee_rate_snapshot += UnsignedDecimal(234)

        # Ticks (mLiq)      (borrowX)           (borrowY)
        # 0:    0       |       0         |         0
        # 1:  200       |   500/7         |     300/7
        # 2:  200       |   500/7         |     300/7
        # 3:  200 + 214 |   500/7 + 98/3  |     300/7 + 17/3
        # 4:  200 + 214 |   500/7 + 98/3  |     300/7 + 17/3
        # 5:  200 + 214 |   500/7 + 98/3  |     300/7 + 17/3
        # 6:  200       |   500/7         |     300/7
        # 7:  200       |   500/7         |     300/7
        # 8:    0       |       0         |         0

        # mLiq is distributed differently over 2 regions
        # Thus the fee calculation can be different in 2 types of ticks
        # Then for queries, we take the sum of each depending on the tick type
        # m1 (1-2, 6-7)
        #   x: 500/7 * 533 / (200*7) = 27.193877551020408163265306122448979591836734693877551020408163265
        #   y: 300/7 * 234 / (200*7) = 7.1632653061224489795918367346938775510204081632653061224489795918
        # m2 (3-5)
        #   x: (500/7 + 98/3) * 533 / (200*7 + 214*3) = 27.170794272655193321207033254045986661069912783918660510237395643
        #   y: (300/7 + 17/3) * 234 / (200*7 + 214*3) = 5.5605149013572128165663914929340982230306422275080453337064502588

        # Querying larger range
        # m1x * 1 and m1y * 1
        (acc_rate_x, acc_rate_y) = self.liq_bucket.query_accumulated_fee_rates(LiqRange(1, 1))
        self.assertFloatingPointEqual(acc_rate_x, UnsignedDecimal("27.193877551020408163265306122448979591836734693877551020408163265"))
        self.assertFloatingPointEqual(acc_rate_y, UnsignedDecimal("7.1632653061224489795918367346938775510204081632653061224489795918"))

        (acc_rate_x, acc_rate_y) = self.liq_bucket.query_accumulated_fee_rates(LiqRange(2, 2))
        self.assertFloatingPointEqual(acc_rate_x, UnsignedDecimal("27.193877551020408163265306122448979591836734693877551020408163265"))
        self.assertFloatingPointEqual(acc_rate_y, UnsignedDecimal("7.1632653061224489795918367346938775510204081632653061224489795918"))

        (acc_rate_x, acc_rate_y) = self.liq_bucket.query_accumulated_fee_rates(LiqRange(6, 6))
        self.assertFloatingPointEqual(acc_rate_x, UnsignedDecimal("27.193877551020408163265306122448979591836734693877551020408163265"))
        self.assertFloatingPointEqual(acc_rate_y, UnsignedDecimal("7.1632653061224489795918367346938775510204081632653061224489795918"))

        (acc_rate_x, acc_rate_y) = self.liq_bucket.query_accumulated_fee_rates(LiqRange(7, 7))
        self.assertFloatingPointEqual(acc_rate_x, UnsignedDecimal("27.193877551020408163265306122448979591836734693877551020408163265"))
        self.assertFloatingPointEqual(acc_rate_y, UnsignedDecimal("7.1632653061224489795918367346938775510204081632653061224489795918"))

        (acc_rate_x, acc_rate_y) = self.liq_bucket.query_accumulated_fee_rates(LiqRange(7, 8))
        self.assertFloatingPointEqual(acc_rate_x, UnsignedDecimal("27.193877551020408163265306122448979591836734693877551020408163265"))
        self.assertFloatingPointEqual(acc_rate_y, UnsignedDecimal("7.1632653061224489795918367346938775510204081632653061224489795918"))

        # m1x * 2 and m1y * 2
        (acc_rate_x, acc_rate_y) = self.liq_bucket.query_accumulated_fee_rates(LiqRange(1, 2))
        self.assertFloatingPointEqual(acc_rate_x, UnsignedDecimal("54.38775510204081632653061224489795918367346938775510204081632653"))
        self.assertFloatingPointEqual(acc_rate_y, UnsignedDecimal("14.326530612244897959183673469387755102040816326530612244897959183"))

        (acc_rate_x, acc_rate_y) = self.liq_bucket.query_accumulated_fee_rates(LiqRange(6, 7))
        self.assertFloatingPointEqual(acc_rate_x, UnsignedDecimal("54.38775510204081632653061224489795918367346938775510204081632653"))
        self.assertFloatingPointEqual(acc_rate_y, UnsignedDecimal("14.326530612244897959183673469387755102040816326530612244897959183"))

        (acc_rate_x, acc_rate_y) = self.liq_bucket.query_accumulated_fee_rates(LiqRange(6, 8))
        self.assertFloatingPointEqual(acc_rate_x, UnsignedDecimal("54.38775510204081632653061224489795918367346938775510204081632653"))
        self.assertFloatingPointEqual(acc_rate_y, UnsignedDecimal("14.326530612244897959183673469387755102040816326530612244897959183"))

        # Querying smaller range
        # m2x * 1 and m2y * 1
        (acc_rate_x, acc_rate_y) = self.liq_bucket.query_accumulated_fee_rates(LiqRange(3, 3))
        self.assertFloatingPointEqual(acc_rate_x, UnsignedDecimal("27.170794272655193321207033254045986661069912783918660510237395643"))
        self.assertFloatingPointEqual(acc_rate_y, UnsignedDecimal("5.5605149013572128165663914929340982230306422275080453337064502588"))

        (acc_rate_x, acc_rate_y) = self.liq_bucket.query_accumulated_fee_rates(LiqRange(4, 4))
        self.assertFloatingPointEqual(acc_rate_x, UnsignedDecimal("27.170794272655193321207033254045986661069912783918660510237395643"))
        self.assertFloatingPointEqual(acc_rate_y, UnsignedDecimal("5.5605149013572128165663914929340982230306422275080453337064502588"))

        (acc_rate_x, acc_rate_y) = self.liq_bucket.query_accumulated_fee_rates(LiqRange(5, 5))
        self.assertFloatingPointEqual(acc_rate_x, UnsignedDecimal("27.170794272655193321207033254045986661069912783918660510237395643"))
        self.assertFloatingPointEqual(acc_rate_y, UnsignedDecimal("5.5605149013572128165663914929340982230306422275080453337064502588"))

        # m2x * 2 and m2y * 2
        (acc_rate_x, acc_rate_y) = self.liq_bucket.query_accumulated_fee_rates(LiqRange(3, 4))
        self.assertFloatingPointEqual(acc_rate_x, UnsignedDecimal("54.341588545310386642414066508091973322139825567837321020474791285"))
        self.assertFloatingPointEqual(acc_rate_y, UnsignedDecimal("11.121029802714425633132782985868196446061284455016090667412900517"))

        (acc_rate_x, acc_rate_y) = self.liq_bucket.query_accumulated_fee_rates(LiqRange(4, 5))
        self.assertFloatingPointEqual(acc_rate_x, UnsignedDecimal("54.341588545310386642414066508091973322139825567837321020474791285"))
        self.assertFloatingPointEqual(acc_rate_y, UnsignedDecimal("11.121029802714425633132782985868196446061284455016090667412900517"))

        # m2x * 3 and m2y * 3
        (acc_rate_x, acc_rate_y) = self.liq_bucket.query_accumulated_fee_rates(LiqRange(3, 5))
        self.assertFloatingPointEqual(acc_rate_x, UnsignedDecimal("81.512382817965579963621099762137959983209738351755981530712186928"))
        self.assertFloatingPointEqual(acc_rate_y, UnsignedDecimal("16.681544704071638449699174478802294669091926682524136001119350776"))

        # Querying overlap of larger range and range w/o mLiq
        (acc_rate_x, acc_rate_y) = self.liq_bucket.query_accumulated_fee_rates(LiqRange(0, 2))
        self.assertFloatingPointEqual(acc_rate_x, UnsignedDecimal("54.38775510204081632653061224489795918367346938775510204081632653"))
        self.assertFloatingPointEqual(acc_rate_y, UnsignedDecimal("14.326530612244897959183673469387755102040816326530612244897959183"))

        (acc_rate_x, acc_rate_y) = self.liq_bucket.query_accumulated_fee_rates(LiqRange(6, 12))
        self.assertFloatingPointEqual(acc_rate_x, UnsignedDecimal("54.38775510204081632653061224489795918367346938775510204081632653"))
        self.assertFloatingPointEqual(acc_rate_y, UnsignedDecimal("14.326530612244897959183673469387755102040816326530612244897959183"))

        # Querying overlap smaller range with lower and range w/o mLiq
        # m1x*1 + m2x*1 and m1y*1 + m2y*1
        (acc_rate_x, acc_rate_y) = self.liq_bucket.query_accumulated_fee_rates(LiqRange(2, 3))
        self.assertFloatingPointEqual(acc_rate_x, UnsignedDecimal("54.364671823675601484472339376494966252906647477796211530645558907"))
        self.assertFloatingPointEqual(acc_rate_y, UnsignedDecimal("12.723780207479661796158228227627975774051050390773351456155429850"))

        (acc_rate_x, acc_rate_y) = self.liq_bucket.query_accumulated_fee_rates(LiqRange(5, 6))
        self.assertFloatingPointEqual(acc_rate_x, UnsignedDecimal("54.364671823675601484472339376494966252906647477796211530645558907"))
        self.assertFloatingPointEqual(acc_rate_y, UnsignedDecimal("12.723780207479661796158228227627975774051050390773351456155429850"))

        # m1x*2 + m2x*1 and m1y*2 + m2y*1
        (acc_rate_x, acc_rate_y) = self.liq_bucket.query_accumulated_fee_rates(LiqRange(0, 3))
        self.assertFloatingPointEqual(acc_rate_x, UnsignedDecimal("81.558549374696009647737645498943945844743382171673762551053722174"))
        self.assertFloatingPointEqual(acc_rate_y, UnsignedDecimal("19.887045513602110775750064962321853325071458554038657578604409442"))

        (acc_rate_x, acc_rate_y) = self.liq_bucket.query_accumulated_fee_rates(LiqRange(1, 3))
        self.assertFloatingPointEqual(acc_rate_x, UnsignedDecimal("81.558549374696009647737645498943945844743382171673762551053722174"))
        self.assertFloatingPointEqual(acc_rate_y, UnsignedDecimal("19.887045513602110775750064962321853325071458554038657578604409442"))

        (acc_rate_x, acc_rate_y) = self.liq_bucket.query_accumulated_fee_rates(LiqRange(5, 7))
        self.assertFloatingPointEqual(acc_rate_x, UnsignedDecimal("81.558549374696009647737645498943945844743382171673762551053722174"))
        self.assertFloatingPointEqual(acc_rate_y, UnsignedDecimal("19.887045513602110775750064962321853325071458554038657578604409442"))

        (acc_rate_x, acc_rate_y) = self.liq_bucket.query_accumulated_fee_rates(LiqRange(5, 8))
        self.assertFloatingPointEqual(acc_rate_x, UnsignedDecimal("81.558549374696009647737645498943945844743382171673762551053722174"))
        self.assertFloatingPointEqual(acc_rate_y, UnsignedDecimal("19.887045513602110775750064962321853325071458554038657578604409442"))

        # m1x*2 + m2x*2 and m1y*2 + m2y*2
        (acc_rate_x, acc_rate_y) = self.liq_bucket.query_accumulated_fee_rates(LiqRange(0, 4))
        self.assertFloatingPointEqual(acc_rate_x, UnsignedDecimal("108.72934364735120296894467875298993250581329495559242306129111781"))
        self.assertFloatingPointEqual(acc_rate_y, UnsignedDecimal("25.447560414959323592316456455255951548102100781546702912310859701"))

        (acc_rate_x, acc_rate_y) = self.liq_bucket.query_accumulated_fee_rates(LiqRange(1, 4))
        self.assertFloatingPointEqual(acc_rate_x, UnsignedDecimal("108.72934364735120296894467875298993250581329495559242306129111781"))
        self.assertFloatingPointEqual(acc_rate_y, UnsignedDecimal("25.447560414959323592316456455255951548102100781546702912310859701"))

        (acc_rate_x, acc_rate_y) = self.liq_bucket.query_accumulated_fee_rates(LiqRange(4, 7))
        self.assertFloatingPointEqual(acc_rate_x, UnsignedDecimal("108.72934364735120296894467875298993250581329495559242306129111781"))
        self.assertFloatingPointEqual(acc_rate_y, UnsignedDecimal("25.447560414959323592316456455255951548102100781546702912310859701"))

        (acc_rate_x, acc_rate_y) = self.liq_bucket.query_accumulated_fee_rates(LiqRange(4, 8))
        self.assertFloatingPointEqual(acc_rate_x, UnsignedDecimal("108.72934364735120296894467875298993250581329495559242306129111781"))
        self.assertFloatingPointEqual(acc_rate_y, UnsignedDecimal("25.447560414959323592316456455255951548102100781546702912310859701"))

        # m1x*2 + m2x*3 and m1y*2 + m2y*3
        (acc_rate_x, acc_rate_y) = self.liq_bucket.query_accumulated_fee_rates(LiqRange(0, 5))
        self.assertFloatingPointEqual(acc_rate_x, UnsignedDecimal("135.90013792000639629015171200703591916688320773951108357152851346"))
        self.assertFloatingPointEqual(acc_rate_y, UnsignedDecimal("31.008075316316536408882847948190049771132743009054748246017309960"))

        (acc_rate_x, acc_rate_y) = self.liq_bucket.query_accumulated_fee_rates(LiqRange(1, 5))
        self.assertFloatingPointEqual(acc_rate_x, UnsignedDecimal("135.90013792000639629015171200703591916688320773951108357152851346"))
        self.assertFloatingPointEqual(acc_rate_y, UnsignedDecimal("31.008075316316536408882847948190049771132743009054748246017309960"))

        (acc_rate_x, acc_rate_y) = self.liq_bucket.query_accumulated_fee_rates(LiqRange(3, 7))
        self.assertFloatingPointEqual(acc_rate_x, UnsignedDecimal("135.90013792000639629015171200703591916688320773951108357152851346"))
        self.assertFloatingPointEqual(acc_rate_y, UnsignedDecimal("31.008075316316536408882847948190049771132743009054748246017309960"))

        (acc_rate_x, acc_rate_y) = self.liq_bucket.query_accumulated_fee_rates(LiqRange(3, 8))
        self.assertFloatingPointEqual(acc_rate_x, UnsignedDecimal("135.90013792000639629015171200703591916688320773951108357152851346"))
        self.assertFloatingPointEqual(acc_rate_y, UnsignedDecimal("31.008075316316536408882847948190049771132743009054748246017309960"))

        # Querying the wide range (4*m1 + 3*m2)
        (acc_rate_x, acc_rate_y) = self.liq_bucket.query_wide_accumulated_fee_rates()
        self.assertFloatingPointEqual(acc_rate_x, UnsignedDecimal("190.28789302204721261668232425193387835055667712726618561234483999"))
        self.assertFloatingPointEqual(acc_rate_y, UnsignedDecimal("45.334605928561434368066521417577804873173559335585360490915269143"))

    def test_fee_accumulation_with_m_liq_at_multiple_ticks_over_multiple_partially_overlapping_ranges(self):
        self.liq_bucket.add_m_liq(LiqRange(8, 14), UnsignedDecimal(456))
        self.liq_bucket.add_t_liq(LiqRange(8, 14), UnsignedDecimal(456), UnsignedDecimal(7), UnsignedDecimal(4))

        self.liq_bucket.token_x_fee_rate_snapshot += UnsignedDecimal(74)
        self.liq_bucket.token_y_fee_rate_snapshot += UnsignedDecimal(374)

        # Querying the exact range
        (acc_rate_x, acc_rate_y) = self.liq_bucket.query_accumulated_fee_rates(LiqRange(8, 14))
        self.assertFloatingPointEqual(acc_rate_x, UnsignedDecimal(1.1359649122807017543859649122807017543859649122807017543859649122))  # 7 * 74 / 456
        self.assertFloatingPointEqual(acc_rate_y, UnsignedDecimal(3.2807017543859649122807017543859649122807017543859649122807017543))  # 4 * 374 / 456

        # Querying a fully contained range
        (acc_rate_x, acc_rate_y) = self.liq_bucket.query_accumulated_fee_rates(LiqRange(9, 10))
        self.assertFloatingPointEqual(acc_rate_x, UnsignedDecimal(1.1359649122807017543859649122807017543859649122807017543859649122))
        self.assertFloatingPointEqual(acc_rate_y, UnsignedDecimal(3.2807017543859649122807017543859649122807017543859649122807017543))

        # Querying an overlapping range
        (acc_rate_x, acc_rate_y) = self.liq_bucket.query_accumulated_fee_rates(LiqRange(1, 10))
        self.assertFloatingPointEqual(acc_rate_x, UnsignedDecimal(1.1359649122807017543859649122807017543859649122807017543859649122))
        self.assertFloatingPointEqual(acc_rate_y, UnsignedDecimal(3.2807017543859649122807017543859649122807017543859649122807017543))

        # Querying a non-overlapping range
        (acc_rate_x, acc_rate_y) = self.liq_bucket.query_accumulated_fee_rates(LiqRange(1, 2))
        self.assertFloatingPointEqual(acc_rate_x, UnsignedDecimal("0"))
        self.assertFloatingPointEqual(acc_rate_y, UnsignedDecimal("0"))

        # # Querying the wide range
        (acc_rate_x, acc_rate_y) = self.liq_bucket.query_wide_accumulated_fee_rates()
        self.assertFloatingPointEqual(acc_rate_x, UnsignedDecimal(1.1359649122807017543859649122807017543859649122807017543859649122))
        self.assertFloatingPointEqual(acc_rate_y, UnsignedDecimal(3.2807017543859649122807017543859649122807017543859649122807017543))

    def test_fee_accumulation_with_m_liq_over_wide_range_and_at_multiple_ticks_over_multiple_partially_overlapping_ranges(self):
        self.liq_bucket.add_m_liq(LiqRange(8, 14), UnsignedDecimal(456))
        self.liq_bucket.add_t_liq(LiqRange(8, 14), UnsignedDecimal(456), UnsignedDecimal(7), UnsignedDecimal(4))

        self.liq_bucket.token_x_fee_rate_snapshot += UnsignedDecimal(74)
        self.liq_bucket.token_y_fee_rate_snapshot += UnsignedDecimal(374)

        # Querying the exact range
        (acc_rate_x, acc_rate_y) = self.liq_bucket.query_accumulated_fee_rates(LiqRange(8, 14))
        self.assertFloatingPointEqual(acc_rate_x, UnsignedDecimal(1.1359649122807017543859649122807017543859649122807017543859649122))  # 7 * 74 / 456
        self.assertFloatingPointEqual(acc_rate_y, UnsignedDecimal(3.2807017543859649122807017543859649122807017543859649122807017543))  # 4 * 374 / 456

        # Querying a fully contained range
        (acc_rate_x, acc_rate_y) = self.liq_bucket.query_accumulated_fee_rates(LiqRange(9, 10))
        self.assertFloatingPointEqual(acc_rate_x, UnsignedDecimal(1.1359649122807017543859649122807017543859649122807017543859649122))
        self.assertFloatingPointEqual(acc_rate_y, UnsignedDecimal(3.2807017543859649122807017543859649122807017543859649122807017543))

        # Querying an overlapping range
        (acc_rate_x, acc_rate_y) = self.liq_bucket.query_accumulated_fee_rates(LiqRange(1, 10))
        self.assertFloatingPointEqual(acc_rate_x, UnsignedDecimal(1.1359649122807017543859649122807017543859649122807017543859649122))
        self.assertFloatingPointEqual(acc_rate_y, UnsignedDecimal(3.2807017543859649122807017543859649122807017543859649122807017543))

        # Querying a non-overlapping range
        (acc_rate_x, acc_rate_y) = self.liq_bucket.query_accumulated_fee_rates(LiqRange(1, 2))
        self.assertFloatingPointEqual(acc_rate_x, UnsignedDecimal("0"))
        self.assertFloatingPointEqual(acc_rate_y, UnsignedDecimal("0"))

        # # Querying the wide range
        (acc_rate_x, acc_rate_y) = self.liq_bucket.query_wide_accumulated_fee_rates()
        self.assertFloatingPointEqual(acc_rate_x, UnsignedDecimal(1.1359649122807017543859649122807017543859649122807017543859649122))
        self.assertFloatingPointEqual(acc_rate_y, UnsignedDecimal(3.2807017543859649122807017543859649122807017543859649122807017543))

    # endregion



    #
    # # tLiq
    # def test_add_t_liq(self):
    #     self.liq_bucket.add_m_liq(LiqRange(8, 11), UnsignedDecimal(1111))
    #     self.liq_bucket.add_t_liq(LiqRange(8, 11), UnsignedDecimal(100), UnsignedDecimal(24e18), UnsignedDecimal(7e6))
    #
    #     t_liq = self.liq_bucket.query_t_liq(LiqRange(8, 11))
    #     self.assertEqual(t_liq, UnsignedDecimal(100))
    #
    #     t_liq = self.liq_bucket.query_t_liq(LiqRange(8, 8))
    #     self.assertEqual(t_liq, UnsignedDecimal(25))  # 25 * 4 = 100
    #
    # def test_revert_removing_m_liq_at_tick_with_zero_m_liq(self):
    #     self.assertRaises(LiquidityExceptionRemovingMoreMLiqThanExists, lambda: self.liq_bucket.remove_m_liq(LiqRange(3, 7), UnsignedDecimal(100)))
    #
    # def test_revert_removing_m_liq_at_tick_where_m_liq_is_lower_than_amount_to_remove(self):
    #     self.liq_bucket.add_m_liq(LiqRange(3, 7), UnsignedDecimal(90))
    #     self.assertRaises(LiquidityExceptionRemovingMoreMLiqThanExists, lambda: self.liq_bucket.remove_m_liq(LiqRange(3, 7), UnsignedDecimal(100)))
    #
    # def test_remove_t_liq(self):
    #     self.liq_bucket.add_m_liq(LiqRange(8, 11), UnsignedDecimal(1111))
    #     self.liq_bucket.add_t_liq(LiqRange(8, 11), UnsignedDecimal(100), UnsignedDecimal(24e18), UnsignedDecimal(7e6))
    #     self.liq_bucket.remove_t_liq(LiqRange(8, 11), UnsignedDecimal(20), UnsignedDecimal(24e18), UnsignedDecimal(7e6))
    #
    #     t_liq = self.liq_bucket.query_t_liq(LiqRange(8, 11))
    #     self.assertEqual(t_liq, UnsignedDecimal(80))
    #
    #     t_liq = self.liq_bucket.query_t_liq(LiqRange(8, 8))
    #     self.assertEqual(t_liq, UnsignedDecimal(20))
    #
    # def test_add_wide_m_liq(self):
    #     self.liq_bucket.add_wide_m_liq(UnsignedDecimal(1600))
    #
    #     wide_m_liq = self.liq_bucket.query_wide_m_liq()
    #     self.assertEqual(wide_m_liq, UnsignedDecimal(1600))
    #
    #     m_liq = self.liq_bucket.query_m_liq(LiqRange(8, 11))
    #     self.assertEqual(m_liq, UnsignedDecimal(400))
    #
    #     m_liq = self.liq_bucket.query_m_liq(LiqRange(8, 8))
    #     self.assertEqual(m_liq, UnsignedDecimal(100))
    #
    # def test_remove_wide_m_liq(self):
    #     self.liq_bucket.add_wide_m_liq(UnsignedDecimal(1600))
    #     self.liq_bucket.remove_wide_m_liq(UnsignedDecimal(800))
    #
    #     wide_m_liq = self.liq_bucket.query_wide_m_liq()
    #     self.assertEqual(wide_m_liq, UnsignedDecimal(800))
    #
    #     m_liq = self.liq_bucket.query_m_liq(LiqRange(8, 11))
    #     self.assertEqual(m_liq, UnsignedDecimal(200))
    #
    #     m_liq = self.liq_bucket.query_m_liq(LiqRange(8, 8))
    #     self.assertEqual(m_liq, UnsignedDecimal(50))
    #
    # def test_add_wide_t_liq(self):
    #     self.liq_bucket.add_wide_m_liq(UnsignedDecimal(1600))
    #     self.liq_bucket.add_wide_t_liq(UnsignedDecimal(400), UnsignedDecimal(24e18), UnsignedDecimal(7e6))
    #
    #     wide_t_liq = self.liq_bucket.query_wide_t_liq()
    #     self.assertEqual(wide_t_liq, UnsignedDecimal(400))
    #
    #     t_liq = self.liq_bucket.query_t_liq(LiqRange(8, 11))
    #     self.assertEqual(t_liq, UnsignedDecimal(100))
    #
    #     t_liq = self.liq_bucket.query_t_liq(LiqRange(8, 8))
    #     self.assertEqual(t_liq, UnsignedDecimal(25))
    #
    # def test_remove_wide_t_liq(self):
    #     self.liq_bucket.add_wide_m_liq(UnsignedDecimal(1600))
    #     self.liq_bucket.add_wide_t_liq(UnsignedDecimal(400), UnsignedDecimal(24e18), UnsignedDecimal(7e6))
    #     self.liq_bucket.remove_wide_t_liq(UnsignedDecimal(25), UnsignedDecimal(24e18), UnsignedDecimal(7e6))
    #
    #     wide_t_liq = self.liq_bucket.query_wide_t_liq()
    #     self.assertEqual(wide_t_liq, UnsignedDecimal(375))
    #
    #     t_liq = self.liq_bucket.query_t_liq(LiqRange(8, 11))
    #     self.assertEqual(t_liq, UnsignedDecimal(93))
    #
    #     t_liq = self.liq_bucket.query_t_liq(LiqRange(8, 8))
    #     self.assertEqual(t_liq, UnsignedDecimal(23))
    #
    # def test_fees(self):
    #     self.liq_bucket.add_m_liq(LiqRange(8, 11), UnsignedDecimal(1111))
    #     self.liq_bucket.add_t_liq(LiqRange(8, 11), UnsignedDecimal(111), UnsignedDecimal(24e18), UnsignedDecimal(7e6))
    #
    #     self.liq_bucket.token_x_fee_rate_snapshot += UnsignedDecimal(113712805933826)
    #
    #     # trigger fees - keeping tree state the same by undoing action
    #     self.liq_bucket.add_m_liq(LiqRange(8, 11), UnsignedDecimal(10))
    #     self.liq_bucket.remove_m_liq(LiqRange(8, 11), UnsignedDecimal(10))
    #
    #     # 8-11
    #     # 113712805933826 * 24e18 / 4444 / 2**64 = 33291000332.9100024179226406346006655493880262469301129331683
    #     # (min_m_liq, max_t_liq, acc_fees_x, acc_fees_y)
    #     (acc_x, acc_y) = self.liq_bucket.query_fees_in_range(LiqRange(8, 11))
    #     self.assertEqual(acc_x, UnsignedDecimal(33291000332))
    #
    #     # 8-8
    #     # 1/4 of 8-11 = 8322750083.227500604480660158650166387347006561732528233292075
    #     (acc_x, acc_y) = self.liq_bucket.query_fees_in_range(LiqRange(8, 8))
    #     self.assertEqual(acc_x, UnsignedDecimal(8322750083))

'''
from unittest import TestCase
from UnsignedDecimal import UnsignedDecimalIsSignedException

# NOTE: all numbers must be given as UnsignedDecimal numbers to avoid precision errors.
#       each UnsignedDecimal number must be created using a string! Otherwise precision is lost when the input variable is created
#       For instance, 7927848e16 yields 79278479999999997378560 as an integer. While the type 7.927848e+22 looks ok, when passed to
#       UnsignedDecimal(7.927848e+22) is still equates to UnsignedDecimal('79278479999999997378560').
#       However, UnsignedDecimal("7927848e16") is correct. Converting to an int yields 79278480000000000000000
#
#       When asserting values are equal, the calculated decimal is truncated to its int representation
#       as the compared value in solidity would lose that extra precision.
#
#       If all goes perfectly, the final result in python would 100% match the final output in solidity

from Tree.LiquidityTree import *

#                                                               root(0-16)
#                                                       ____----    ----____
#                                   __________----------                    ----------__________
#                                  L(0-7)                                                       R(8-15)
#                             __--  --__                                                    __--  --__
#                        __---          ---__                                          __---          ---__
#                      /                       \                                     /                       \
#                   LL(0-3)                     LR(4-7)                           RL(8-11)                     RR(12-15)
#                 /   \                         /   \                           /   \                         /   \
#               /       \                     /       \                       /       \                     /       \
#             /           \                 /           \                   /           \                 /           \
#           LLL(0-1)       LLR(2-3)       LRL(4-5)       LRR(6-7)         RLL(8-9)       RLR(10-11)     RRL(12-13)     RRR(14-15)
#          /    \          /    \          /    \          /    \         /    \          /    \          /    \          /    \
#         /      \        /      \        /      \        /      \       /      \        /      \        /      \        /      \
#   LLLL(0) LLLR(1) LLRL(2) LLRR(3) LRLL(4) LRLR(5) LRRL(6) LRRR(7) RLLL(8) RLLR(9) RLRL(10) RLRR(11) RRLL(12) RRLR(13) RRRL(14) RRRR(15)


# note: maybe test 12-13 specifically? (two legs but one starts at the stop)
class TestLiquidityTree(TestCase):
    def setUp(self) -> None:
        self.liq_tree = LiquidityTree(depth=4, sol_truncation=True)

    # region m_liq
    def test_adding_m_liq_root_only(self):
        root: LiqNode = self.liq_tree.nodes[self.liq_tree.root_key]
        self.liq_tree.add_wide_m_liq(UnsignedDecimal("123"))

        self.assertEqual(root.m_liq, UnsignedDecimal("123"))
        self.assertEqual(root.subtree_m_liq, UnsignedDecimal("1968"))
        self.assertEqual(root.t_liq, UnsignedDecimal("0"))
        self.assertEqual(root.token_x_borrowed, UnsignedDecimal("0"))
        self.assertEqual(root.token_x_subtree_borrowed, UnsignedDecimal("0"))
        self.assertEqual(root.token_y_borrowed, UnsignedDecimal("0"))
        self.assertEqual(root.token_y_subtree_borrowed, UnsignedDecimal("0"))

        self.assertEqual(self.liq_tree.token_x_fee_rate_snapshot, UnsignedDecimal("0"))
        self.assertEqual(self.liq_tree.token_y_fee_rate_snapshot, UnsignedDecimal("0"))

    def test_adding_m_liq_left_leg_only(self):
        # range 1-3
        liq_tree: LiquidityTree = self.liq_tree

        root: LiqNode = liq_tree.nodes[liq_tree.root_key]
        L: LiqNode = liq_tree.nodes[(8 << 24) | 16]
        LL: LiqNode = liq_tree.nodes[(4 << 24) | 16]
        LLL: LiqNode = liq_tree.nodes[(2 << 24) | 16]
        LLR: LiqNode = liq_tree.nodes[(2 << 24) | 18]
        LLLL: LiqNode = liq_tree.nodes[(1 << 24) | 16]
        LLLR: LiqNode = liq_tree.nodes[(1 << 24) | 17]
        LLRL: LiqNode = liq_tree.nodes[(1 << 24) | 18]
        LLRR: LiqNode = liq_tree.nodes[(1 << 24) | 19]

        self.liq_tree.add_m_liq(LiqRange(low=1, high=3), UnsignedDecimal("123"))  # LLLR, LLR

        # m_liq
        self.assertEqual(root.m_liq, UnsignedDecimal("0"))
        self.assertEqual(L.m_liq, UnsignedDecimal("0"))
        self.assertEqual(LL.m_liq, UnsignedDecimal("0"))
        self.assertEqual(LLL.m_liq, UnsignedDecimal("0"))
        self.assertEqual(LLR.m_liq, UnsignedDecimal("123"))
        self.assertEqual(LLLL.m_liq, UnsignedDecimal("0"))
        self.assertEqual(LLLR.m_liq, UnsignedDecimal("123"))
        self.assertEqual(LLRL.m_liq, UnsignedDecimal("0"))
        self.assertEqual(LLRR.m_liq, UnsignedDecimal("0"))

        # t_liq
        self.assertEqual(root.t_liq, UnsignedDecimal("0"))
        self.assertEqual(L.t_liq, UnsignedDecimal("0"))
        self.assertEqual(LL.t_liq, UnsignedDecimal("0"))
        self.assertEqual(LLL.t_liq, UnsignedDecimal("0"))
        self.assertEqual(LLR.t_liq, UnsignedDecimal("0"))
        self.assertEqual(LLLL.t_liq, UnsignedDecimal("0"))
        self.assertEqual(LLLR.t_liq, UnsignedDecimal("0"))
        self.assertEqual(LLRL.t_liq, UnsignedDecimal("0"))
        self.assertEqual(LLRR.t_liq, UnsignedDecimal("0"))

        # subtree_m_liq
        self.assertEqual(root.subtree_m_liq, UnsignedDecimal("369"))
        self.assertEqual(L.subtree_m_liq, UnsignedDecimal("369"))
        self.assertEqual(LL.subtree_m_liq, UnsignedDecimal("369"))
        self.assertEqual(LLL.subtree_m_liq, UnsignedDecimal("123"))
        self.assertEqual(LLR.subtree_m_liq, UnsignedDecimal("246"))
        self.assertEqual(LLLL.subtree_m_liq, UnsignedDecimal("0"))
        self.assertEqual(LLLR.subtree_m_liq, UnsignedDecimal("123"))
        self.assertEqual(LLRL.subtree_m_liq, UnsignedDecimal("0"))
        self.assertEqual(LLRR.subtree_m_liq, UnsignedDecimal("0"))

        # borrowed_x
        self.assertEqual(root.token_x_borrowed, UnsignedDecimal("0"))
        self.assertEqual(L.token_x_borrowed, UnsignedDecimal("0"))
        self.assertEqual(LL.token_x_borrowed, UnsignedDecimal("0"))
        self.assertEqual(LLL.token_x_borrowed, UnsignedDecimal("0"))
        self.assertEqual(LLR.token_x_borrowed, UnsignedDecimal("0"))
        self.assertEqual(LLLL.token_x_borrowed, UnsignedDecimal("0"))
        self.assertEqual(LLLR.token_x_borrowed, UnsignedDecimal("0"))
        self.assertEqual(LLRL.token_x_borrowed, UnsignedDecimal("0"))
        self.assertEqual(LLRR.token_x_borrowed, UnsignedDecimal("0"))

        # subtree_borrowed_x
        self.assertEqual(root.token_x_subtree_borrowed, UnsignedDecimal("0"))
        self.assertEqual(L.token_x_subtree_borrowed, UnsignedDecimal("0"))
        self.assertEqual(LL.token_x_subtree_borrowed, UnsignedDecimal("0"))
        self.assertEqual(LLL.token_x_subtree_borrowed, UnsignedDecimal("0"))
        self.assertEqual(LLR.token_x_subtree_borrowed, UnsignedDecimal("0"))
        self.assertEqual(LLLL.token_x_subtree_borrowed, UnsignedDecimal("0"))
        self.assertEqual(LLLR.token_x_subtree_borrowed, UnsignedDecimal("0"))
        self.assertEqual(LLRL.token_x_subtree_borrowed, UnsignedDecimal("0"))
        self.assertEqual(LLRR.token_x_subtree_borrowed, UnsignedDecimal("0"))

        # borrowed_y
        self.assertEqual(root.token_y_borrowed, UnsignedDecimal("0"))
        self.assertEqual(L.token_y_borrowed, UnsignedDecimal("0"))
        self.assertEqual(LL.token_y_borrowed, UnsignedDecimal("0"))
        self.assertEqual(LLL.token_y_borrowed, UnsignedDecimal("0"))
        self.assertEqual(LLR.token_y_borrowed, UnsignedDecimal("0"))
        self.assertEqual(LLLL.token_y_borrowed, UnsignedDecimal("0"))
        self.assertEqual(LLLR.token_y_borrowed, UnsignedDecimal("0"))
        self.assertEqual(LLRL.token_y_borrowed, UnsignedDecimal("0"))
        self.assertEqual(LLRR.token_y_borrowed, UnsignedDecimal("0"))

        # subtree_borrowed_y
        self.assertEqual(root.token_y_subtree_borrowed, UnsignedDecimal("0"))
        self.assertEqual(L.token_y_subtree_borrowed, UnsignedDecimal("0"))
        self.assertEqual(LL.token_y_subtree_borrowed, UnsignedDecimal("0"))
        self.assertEqual(LLL.token_y_subtree_borrowed, UnsignedDecimal("0"))
        self.assertEqual(LLR.token_y_subtree_borrowed, UnsignedDecimal("0"))
        self.assertEqual(LLLL.token_y_subtree_borrowed, UnsignedDecimal("0"))
        self.assertEqual(LLLR.token_y_subtree_borrowed, UnsignedDecimal("0"))
        self.assertEqual(LLRL.token_y_subtree_borrowed, UnsignedDecimal("0"))
        self.assertEqual(LLRR.token_y_subtree_borrowed, UnsignedDecimal("0"))

        # token_x_cumulative_earned_per_m_liq
        self.assertEqual(root.token_x_cumulative_earned_per_m_liq, UnsignedDecimal("0"))
        self.assertEqual(L.token_x_cumulative_earned_per_m_liq, UnsignedDecimal("0"))
        self.assertEqual(LL.token_x_cumulative_earned_per_m_liq, UnsignedDecimal("0"))
        self.assertEqual(LLL.token_x_cumulative_earned_per_m_liq, UnsignedDecimal("0"))
        self.assertEqual(LLR.token_x_cumulative_earned_per_m_liq, UnsignedDecimal("0"))
        self.assertEqual(LLLL.token_x_cumulative_earned_per_m_liq, UnsignedDecimal("0"))
        self.assertEqual(LLLR.token_x_cumulative_earned_per_m_liq, UnsignedDecimal("0"))
        self.assertEqual(LLRL.token_x_cumulative_earned_per_m_liq, UnsignedDecimal("0"))
        self.assertEqual(LLRR.token_x_cumulative_earned_per_m_liq, UnsignedDecimal("0"))

        # token_x_cumulative_earned_per_m_subtree_liq
        self.assertEqual(root.token_x_cumulative_earned_per_m_subtree_liq, UnsignedDecimal("0"))
        self.assertEqual(L.token_x_cumulative_earned_per_m_subtree_liq, UnsignedDecimal("0"))
        self.assertEqual(LL.token_x_cumulative_earned_per_m_subtree_liq, UnsignedDecimal("0"))
        self.assertEqual(LLL.token_x_cumulative_earned_per_m_subtree_liq, UnsignedDecimal("0"))
        self.assertEqual(LLR.token_x_cumulative_earned_per_m_subtree_liq, UnsignedDecimal("0"))
        self.assertEqual(LLLL.token_x_cumulative_earned_per_m_subtree_liq, UnsignedDecimal("0"))
        self.assertEqual(LLLR.token_x_cumulative_earned_per_m_subtree_liq, UnsignedDecimal("0"))
        self.assertEqual(LLRL.token_x_cumulative_earned_per_m_subtree_liq, UnsignedDecimal("0"))
        self.assertEqual(LLRR.token_x_cumulative_earned_per_m_subtree_liq, UnsignedDecimal("0"))

        # token_y_cumulative_earned_per_m_liq
        self.assertEqual(root.token_y_cumulative_earned_per_m_liq, UnsignedDecimal("0"))
        self.assertEqual(L.token_y_cumulative_earned_per_m_liq, UnsignedDecimal("0"))
        self.assertEqual(LL.token_y_cumulative_earned_per_m_liq, UnsignedDecimal("0"))
        self.assertEqual(LLL.token_y_cumulative_earned_per_m_liq, UnsignedDecimal("0"))
        self.assertEqual(LLR.token_y_cumulative_earned_per_m_liq, UnsignedDecimal("0"))
        self.assertEqual(LLLL.token_y_cumulative_earned_per_m_liq, UnsignedDecimal("0"))
        self.assertEqual(LLLR.token_y_cumulative_earned_per_m_liq, UnsignedDecimal("0"))
        self.assertEqual(LLRL.token_y_cumulative_earned_per_m_liq, UnsignedDecimal("0"))
        self.assertEqual(LLRR.token_y_cumulative_earned_per_m_liq, UnsignedDecimal("0"))

        # token_y_cumulative_earned_per_m_subtree_liq
        self.assertEqual(root.token_y_cumulative_earned_per_m_subtree_liq, UnsignedDecimal("0"))
        self.assertEqual(L.token_y_cumulative_earned_per_m_subtree_liq, UnsignedDecimal("0"))
        self.assertEqual(LL.token_y_cumulative_earned_per_m_subtree_liq, UnsignedDecimal("0"))
        self.assertEqual(LLL.token_y_cumulative_earned_per_m_subtree_liq, UnsignedDecimal("0"))
        self.assertEqual(LLR.token_y_cumulative_earned_per_m_subtree_liq, UnsignedDecimal("0"))
        self.assertEqual(LLLL.token_y_cumulative_earned_per_m_subtree_liq, UnsignedDecimal("0"))
        self.assertEqual(LLLR.token_y_cumulative_earned_per_m_subtree_liq, UnsignedDecimal("0"))
        self.assertEqual(LLRL.token_y_cumulative_earned_per_m_subtree_liq, UnsignedDecimal("0"))
        self.assertEqual(LLRR.token_y_cumulative_earned_per_m_subtree_liq, UnsignedDecimal("0"))

    def test_adding_m_liq_right_leg_only(self):
        # range 8-10
        liq_tree: LiquidityTree = self.liq_tree

        root: LiqNode = liq_tree.nodes[liq_tree.root_key]
        R: LiqNode = liq_tree.nodes[(8 << 24) | 24]
        RL: LiqNode = liq_tree.nodes[(4 << 24) | 24]
        RLL: LiqNode = liq_tree.nodes[(2 << 24) | 24]
        RLR: LiqNode = liq_tree.nodes[(2 << 24) | 26]
        RLLL: LiqNode = liq_tree.nodes[(1 << 24) | 24]
        RLLR: LiqNode = liq_tree.nodes[(1 << 24) | 25]
        RLRL: LiqNode = liq_tree.nodes[(1 << 24) | 26]
        RLRR: LiqNode = liq_tree.nodes[(1 << 24) | 27]

        self.liq_tree.add_m_liq(LiqRange(low=8, high=10), UnsignedDecimal("100"))  # RLL, RLRL

        # m_liq
        self.assertEqual(root.m_liq, UnsignedDecimal("0"))
        self.assertEqual(R.m_liq, UnsignedDecimal("0"))
        self.assertEqual(RL.m_liq, UnsignedDecimal("0"))
        self.assertEqual(RLL.m_liq, UnsignedDecimal("100"))
        self.assertEqual(RLR.m_liq, UnsignedDecimal("0"))
        self.assertEqual(RLLL.m_liq, UnsignedDecimal("0"))
        self.assertEqual(RLLR.m_liq, UnsignedDecimal("0"))
        self.assertEqual(RLRL.m_liq, UnsignedDecimal("100"))
        self.assertEqual(RLRR.m_liq, UnsignedDecimal("0"))

        # t_liq
        self.assertEqual(root.t_liq, UnsignedDecimal("0"))
        self.assertEqual(R.t_liq, UnsignedDecimal("0"))
        self.assertEqual(RL.t_liq, UnsignedDecimal("0"))
        self.assertEqual(RLL.t_liq, UnsignedDecimal("0"))
        self.assertEqual(RLR.t_liq, UnsignedDecimal("0"))
        self.assertEqual(RLLL.t_liq, UnsignedDecimal("0"))
        self.assertEqual(RLLR.t_liq, UnsignedDecimal("0"))
        self.assertEqual(RLRL.t_liq, UnsignedDecimal("0"))
        self.assertEqual(RLRR.t_liq, UnsignedDecimal("0"))

        # subtree_m_liq
        self.assertEqual(root.subtree_m_liq, UnsignedDecimal("300"))
        self.assertEqual(R.subtree_m_liq, UnsignedDecimal("300"))
        self.assertEqual(RL.subtree_m_liq, UnsignedDecimal("300"))
        self.assertEqual(RLL.subtree_m_liq, UnsignedDecimal("200"))
        self.assertEqual(RLR.subtree_m_liq, UnsignedDecimal("100"))
        self.assertEqual(RLLL.subtree_m_liq, UnsignedDecimal("0"))
        self.assertEqual(RLLR.subtree_m_liq, UnsignedDecimal("0"))
        self.assertEqual(RLRL.subtree_m_liq, UnsignedDecimal("100"))
        self.assertEqual(RLRR.subtree_m_liq, UnsignedDecimal("0"))

        # borrowed_x
        self.assertEqual(root.token_x_borrowed, UnsignedDecimal("0"))
        self.assertEqual(R.token_x_borrowed, UnsignedDecimal("0"))
        self.assertEqual(RL.token_x_borrowed, UnsignedDecimal("0"))
        self.assertEqual(RLL.token_x_borrowed, UnsignedDecimal("0"))
        self.assertEqual(RLR.token_x_borrowed, UnsignedDecimal("0"))
        self.assertEqual(RLLL.token_x_borrowed, UnsignedDecimal("0"))
        self.assertEqual(RLLR.token_x_borrowed, UnsignedDecimal("0"))
        self.assertEqual(RLRL.token_x_borrowed, UnsignedDecimal("0"))
        self.assertEqual(RLRR.token_x_borrowed, UnsignedDecimal("0"))

        # subtree_borrowed_x
        self.assertEqual(root.token_x_subtree_borrowed, UnsignedDecimal("0"))
        self.assertEqual(R.token_x_subtree_borrowed, UnsignedDecimal("0"))
        self.assertEqual(RL.token_x_subtree_borrowed, UnsignedDecimal("0"))
        self.assertEqual(RLL.token_x_subtree_borrowed, UnsignedDecimal("0"))
        self.assertEqual(RLR.token_x_subtree_borrowed, UnsignedDecimal("0"))
        self.assertEqual(RLLL.token_x_subtree_borrowed, UnsignedDecimal("0"))
        self.assertEqual(RLLR.token_x_subtree_borrowed, UnsignedDecimal("0"))
        self.assertEqual(RLRL.token_x_subtree_borrowed, UnsignedDecimal("0"))
        self.assertEqual(RLRR.token_x_subtree_borrowed, UnsignedDecimal("0"))

        # borrowed_y
        self.assertEqual(root.token_y_borrowed, UnsignedDecimal("0"))
        self.assertEqual(R.token_y_borrowed, UnsignedDecimal("0"))
        self.assertEqual(RL.token_y_borrowed, UnsignedDecimal("0"))
        self.assertEqual(RLL.token_y_borrowed, UnsignedDecimal("0"))
        self.assertEqual(RLR.token_y_borrowed, UnsignedDecimal("0"))
        self.assertEqual(RLLL.token_y_borrowed, UnsignedDecimal("0"))
        self.assertEqual(RLLR.token_y_borrowed, UnsignedDecimal("0"))
        self.assertEqual(RLRL.token_y_borrowed, UnsignedDecimal("0"))
        self.assertEqual(RLRR.token_y_borrowed, UnsignedDecimal("0"))

        # subtree_borrowed_y
        self.assertEqual(root.token_y_subtree_borrowed, UnsignedDecimal("0"))
        self.assertEqual(R.token_y_subtree_borrowed, UnsignedDecimal("0"))
        self.assertEqual(RL.token_y_subtree_borrowed, UnsignedDecimal("0"))
        self.assertEqual(RLL.token_y_subtree_borrowed, UnsignedDecimal("0"))
        self.assertEqual(RLR.token_y_subtree_borrowed, UnsignedDecimal("0"))
        self.assertEqual(RLLL.token_y_subtree_borrowed, UnsignedDecimal("0"))
        self.assertEqual(RLLR.token_y_subtree_borrowed, UnsignedDecimal("0"))
        self.assertEqual(RLRL.token_y_subtree_borrowed, UnsignedDecimal("0"))
        self.assertEqual(RLRR.token_y_subtree_borrowed, UnsignedDecimal("0"))

        # token_x_cumulative_earned_per_m_liq
        self.assertEqual(root.token_x_cumulative_earned_per_m_liq, UnsignedDecimal("0"))
        self.assertEqual(R.token_x_cumulative_earned_per_m_liq, UnsignedDecimal("0"))
        self.assertEqual(RL.token_x_cumulative_earned_per_m_liq, UnsignedDecimal("0"))
        self.assertEqual(RLL.token_x_cumulative_earned_per_m_liq, UnsignedDecimal("0"))
        self.assertEqual(RLR.token_x_cumulative_earned_per_m_liq, UnsignedDecimal("0"))
        self.assertEqual(RLLL.token_x_cumulative_earned_per_m_liq, UnsignedDecimal("0"))
        self.assertEqual(RLLR.token_x_cumulative_earned_per_m_liq, UnsignedDecimal("0"))
        self.assertEqual(RLRL.token_x_cumulative_earned_per_m_liq, UnsignedDecimal("0"))
        self.assertEqual(RLRR.token_x_cumulative_earned_per_m_liq, UnsignedDecimal("0"))

        # token_x_cumulative_earned_per_m_subtree_liq
        self.assertEqual(root.token_x_cumulative_earned_per_m_subtree_liq, UnsignedDecimal("0"))
        self.assertEqual(R.token_x_cumulative_earned_per_m_subtree_liq, UnsignedDecimal("0"))
        self.assertEqual(RL.token_x_cumulative_earned_per_m_subtree_liq, UnsignedDecimal("0"))
        self.assertEqual(RLL.token_x_cumulative_earned_per_m_subtree_liq, UnsignedDecimal("0"))
        self.assertEqual(RLR.token_x_cumulative_earned_per_m_subtree_liq, UnsignedDecimal("0"))
        self.assertEqual(RLLL.token_x_cumulative_earned_per_m_subtree_liq, UnsignedDecimal("0"))
        self.assertEqual(RLLR.token_x_cumulative_earned_per_m_subtree_liq, UnsignedDecimal("0"))
        self.assertEqual(RLRL.token_x_cumulative_earned_per_m_subtree_liq, UnsignedDecimal("0"))
        self.assertEqual(RLRR.token_x_cumulative_earned_per_m_subtree_liq, UnsignedDecimal("0"))

        # token_y_cumulative_earned_per_m_liq
        self.assertEqual(root.token_y_cumulative_earned_per_m_liq, UnsignedDecimal("0"))
        self.assertEqual(R.token_y_cumulative_earned_per_m_liq, UnsignedDecimal("0"))
        self.assertEqual(RL.token_y_cumulative_earned_per_m_liq, UnsignedDecimal("0"))
        self.assertEqual(RLL.token_y_cumulative_earned_per_m_liq, UnsignedDecimal("0"))
        self.assertEqual(RLR.token_y_cumulative_earned_per_m_liq, UnsignedDecimal("0"))
        self.assertEqual(RLLL.token_y_cumulative_earned_per_m_liq, UnsignedDecimal("0"))
        self.assertEqual(RLLR.token_y_cumulative_earned_per_m_liq, UnsignedDecimal("0"))
        self.assertEqual(RLRL.token_y_cumulative_earned_per_m_liq, UnsignedDecimal("0"))
        self.assertEqual(RLRR.token_y_cumulative_earned_per_m_liq, UnsignedDecimal("0"))

        # token_y_cumulative_earned_per_m_subtree_liq
        self.assertEqual(root.token_y_cumulative_earned_per_m_subtree_liq, UnsignedDecimal("0"))
        self.assertEqual(R.token_y_cumulative_earned_per_m_subtree_liq, UnsignedDecimal("0"))
        self.assertEqual(RL.token_y_cumulative_earned_per_m_subtree_liq, UnsignedDecimal("0"))
        self.assertEqual(RLL.token_y_cumulative_earned_per_m_subtree_liq, UnsignedDecimal("0"))
        self.assertEqual(RLR.token_y_cumulative_earned_per_m_subtree_liq, UnsignedDecimal("0"))
        self.assertEqual(RLLL.token_y_cumulative_earned_per_m_subtree_liq, UnsignedDecimal("0"))
        self.assertEqual(RLLR.token_y_cumulative_earned_per_m_subtree_liq, UnsignedDecimal("0"))
        self.assertEqual(RLRL.token_y_cumulative_earned_per_m_subtree_liq, UnsignedDecimal("0"))
        self.assertEqual(RLRR.token_y_cumulative_earned_per_m_subtree_liq, UnsignedDecimal("0"))

    def test_adding_m_liq_left_and_right_leg_stopping_below_peak(self):
        # range 11-14
        liq_tree: LiquidityTree = self.liq_tree

        root: LiqNode = liq_tree.nodes[liq_tree.root_key]
        R: LiqNode = liq_tree.nodes[(8 << 24) | 24]
        RL: LiqNode = liq_tree.nodes[(4 << 24) | 24]
        RR: LiqNode = liq_tree.nodes[(4 << 24) | 28]
        RLR: LiqNode = liq_tree.nodes[(2 << 24) | 26]
        RRL: LiqNode = liq_tree.nodes[(2 << 24) | 28]
        RRR: LiqNode = liq_tree.nodes[(2 << 24) | 30]
        RLRL: LiqNode = liq_tree.nodes[(1 << 24) | 26]
        RLRR: LiqNode = liq_tree.nodes[(1 << 24) | 27]
        RRLL: LiqNode = liq_tree.nodes[(1 << 24) | 28]
        RRLR: LiqNode = liq_tree.nodes[(1 << 24) | 29]
        RRRL: LiqNode = liq_tree.nodes[(1 << 24) | 30]
        RRRR: LiqNode = liq_tree.nodes[(1 << 24) | 301]

        self.liq_tree.add_m_liq(LiqRange(low=11, high=14), UnsignedDecimal("12"))  # RLRR, RRL, RRRL

        # m_liq
        self.assertEqual(root.m_liq, UnsignedDecimal("0"))
        self.assertEqual(R.m_liq, UnsignedDecimal("0"))
        self.assertEqual(RL.m_liq, UnsignedDecimal("0"))
        self.assertEqual(RR.m_liq, UnsignedDecimal("0"))
        self.assertEqual(RLR.m_liq, UnsignedDecimal("0"))
        self.assertEqual(RRL.m_liq, UnsignedDecimal("12"))
        self.assertEqual(RRR.m_liq, UnsignedDecimal("0"))
        self.assertEqual(RLRL.m_liq, UnsignedDecimal("0"))
        self.assertEqual(RLRR.m_liq, UnsignedDecimal("12"))
        self.assertEqual(RRLL.m_liq, UnsignedDecimal("0"))
        self.assertEqual(RRLR.m_liq, UnsignedDecimal("0"))
        self.assertEqual(RRRL.m_liq, UnsignedDecimal("12"))
        self.assertEqual(RRRR.m_liq, UnsignedDecimal("0"))

        # t_liq
        self.assertEqual(root.t_liq, UnsignedDecimal("0"))
        self.assertEqual(R.t_liq, UnsignedDecimal("0"))
        self.assertEqual(RL.t_liq, UnsignedDecimal("0"))
        self.assertEqual(RR.t_liq, UnsignedDecimal("0"))
        self.assertEqual(RLR.t_liq, UnsignedDecimal("0"))
        self.assertEqual(RRL.t_liq, UnsignedDecimal("0"))
        self.assertEqual(RRR.t_liq, UnsignedDecimal("0"))
        self.assertEqual(RLRL.t_liq, UnsignedDecimal("0"))
        self.assertEqual(RLRR.t_liq, UnsignedDecimal("0"))
        self.assertEqual(RRLL.t_liq, UnsignedDecimal("0"))
        self.assertEqual(RRLR.t_liq, UnsignedDecimal("0"))
        self.assertEqual(RRRL.t_liq, UnsignedDecimal("0"))
        self.assertEqual(RRRR.t_liq, UnsignedDecimal("0"))

        # subtree_m_liq
        self.assertEqual(root.subtree_m_liq, UnsignedDecimal("48"))
        self.assertEqual(R.subtree_m_liq, UnsignedDecimal("48"))
        self.assertEqual(RL.subtree_m_liq, UnsignedDecimal("12"))
        self.assertEqual(RR.subtree_m_liq, UnsignedDecimal("36"))
        self.assertEqual(RLR.subtree_m_liq, UnsignedDecimal("12"))
        self.assertEqual(RRL.subtree_m_liq, UnsignedDecimal("24"))
        self.assertEqual(RRR.subtree_m_liq, UnsignedDecimal("12"))
        self.assertEqual(RLRL.subtree_m_liq, UnsignedDecimal("0"))
        self.assertEqual(RLRR.subtree_m_liq, UnsignedDecimal("12"))
        self.assertEqual(RRLL.subtree_m_liq, UnsignedDecimal("0"))
        self.assertEqual(RRLR.subtree_m_liq, UnsignedDecimal("0"))
        self.assertEqual(RRRL.subtree_m_liq, UnsignedDecimal("12"))
        self.assertEqual(RRRR.subtree_m_liq, UnsignedDecimal("0"))

        # borrowed_x
        self.assertEqual(root.token_x_borrowed, UnsignedDecimal("0"))
        self.assertEqual(R.token_x_borrowed, UnsignedDecimal("0"))
        self.assertEqual(RL.token_x_borrowed, UnsignedDecimal("0"))
        self.assertEqual(RR.token_x_borrowed, UnsignedDecimal("0"))
        self.assertEqual(RLR.token_x_borrowed, UnsignedDecimal("0"))
        self.assertEqual(RRL.token_x_borrowed, UnsignedDecimal("0"))
        self.assertEqual(RRR.token_x_borrowed, UnsignedDecimal("0"))
        self.assertEqual(RLRL.token_x_borrowed, UnsignedDecimal("0"))
        self.assertEqual(RLRR.token_x_borrowed, UnsignedDecimal("0"))
        self.assertEqual(RRLL.token_x_borrowed, UnsignedDecimal("0"))
        self.assertEqual(RRLR.token_x_borrowed, UnsignedDecimal("0"))
        self.assertEqual(RRRL.token_x_borrowed, UnsignedDecimal("0"))
        self.assertEqual(RRRR.token_x_borrowed, UnsignedDecimal("0"))

        # subtree_borrowed_x
        self.assertEqual(root.token_x_subtree_borrowed, UnsignedDecimal("0"))
        self.assertEqual(R.token_x_subtree_borrowed, UnsignedDecimal("0"))
        self.assertEqual(RL.token_x_subtree_borrowed, UnsignedDecimal("0"))
        self.assertEqual(RR.token_x_subtree_borrowed, UnsignedDecimal("0"))
        self.assertEqual(RLR.token_x_subtree_borrowed, UnsignedDecimal("0"))
        self.assertEqual(RRL.token_x_subtree_borrowed, UnsignedDecimal("0"))
        self.assertEqual(RRR.token_x_subtree_borrowed, UnsignedDecimal("0"))
        self.assertEqual(RLRL.token_x_subtree_borrowed, UnsignedDecimal("0"))
        self.assertEqual(RLRR.token_x_subtree_borrowed, UnsignedDecimal("0"))
        self.assertEqual(RRLL.token_x_subtree_borrowed, UnsignedDecimal("0"))
        self.assertEqual(RRLR.token_x_subtree_borrowed, UnsignedDecimal("0"))
        self.assertEqual(RRRL.token_x_subtree_borrowed, UnsignedDecimal("0"))
        self.assertEqual(RRRR.token_x_subtree_borrowed, UnsignedDecimal("0"))

        # borrowed_y
        self.assertEqual(root.token_y_borrowed, UnsignedDecimal("0"))
        self.assertEqual(R.token_y_borrowed, UnsignedDecimal("0"))
        self.assertEqual(RL.token_y_borrowed, UnsignedDecimal("0"))
        self.assertEqual(RR.token_y_borrowed, UnsignedDecimal("0"))
        self.assertEqual(RLR.token_y_borrowed, UnsignedDecimal("0"))
        self.assertEqual(RRL.token_y_borrowed, UnsignedDecimal("0"))
        self.assertEqual(RRR.token_y_borrowed, UnsignedDecimal("0"))
        self.assertEqual(RLRL.token_y_borrowed, UnsignedDecimal("0"))
        self.assertEqual(RLRR.token_y_borrowed, UnsignedDecimal("0"))
        self.assertEqual(RRLL.token_y_borrowed, UnsignedDecimal("0"))
        self.assertEqual(RRLR.token_y_borrowed, UnsignedDecimal("0"))
        self.assertEqual(RRRL.token_y_borrowed, UnsignedDecimal("0"))
        self.assertEqual(RRRR.token_y_borrowed, UnsignedDecimal("0"))

        # subtree_borrowed_y
        self.assertEqual(root.token_y_subtree_borrowed, UnsignedDecimal("0"))
        self.assertEqual(R.token_y_subtree_borrowed, UnsignedDecimal("0"))
        self.assertEqual(RL.token_y_subtree_borrowed, UnsignedDecimal("0"))
        self.assertEqual(RR.token_y_subtree_borrowed, UnsignedDecimal("0"))
        self.assertEqual(RLR.token_y_subtree_borrowed, UnsignedDecimal("0"))
        self.assertEqual(RRL.token_y_subtree_borrowed, UnsignedDecimal("0"))
        self.assertEqual(RRR.token_y_subtree_borrowed, UnsignedDecimal("0"))
        self.assertEqual(RLRL.token_y_subtree_borrowed, UnsignedDecimal("0"))
        self.assertEqual(RLRR.token_y_subtree_borrowed, UnsignedDecimal("0"))
        self.assertEqual(RRLL.token_y_subtree_borrowed, UnsignedDecimal("0"))
        self.assertEqual(RRLR.token_y_subtree_borrowed, UnsignedDecimal("0"))
        self.assertEqual(RRRL.token_y_subtree_borrowed, UnsignedDecimal("0"))
        self.assertEqual(RRRR.token_y_subtree_borrowed, UnsignedDecimal("0"))

        # token_x_cumulative_earned_per_m_liq
        self.assertEqual(root.token_x_cumulative_earned_per_m_liq, UnsignedDecimal("0"))
        self.assertEqual(R.token_x_cumulative_earned_per_m_liq, UnsignedDecimal("0"))
        self.assertEqual(RL.token_x_cumulative_earned_per_m_liq, UnsignedDecimal("0"))
        self.assertEqual(RR.token_x_cumulative_earned_per_m_liq, UnsignedDecimal("0"))
        self.assertEqual(RLR.token_x_cumulative_earned_per_m_liq, UnsignedDecimal("0"))
        self.assertEqual(RRL.token_x_cumulative_earned_per_m_liq, UnsignedDecimal("0"))
        self.assertEqual(RRR.token_x_cumulative_earned_per_m_liq, UnsignedDecimal("0"))
        self.assertEqual(RLRL.token_x_cumulative_earned_per_m_liq, UnsignedDecimal("0"))
        self.assertEqual(RLRR.token_x_cumulative_earned_per_m_liq, UnsignedDecimal("0"))
        self.assertEqual(RRLL.token_x_cumulative_earned_per_m_liq, UnsignedDecimal("0"))
        self.assertEqual(RRLR.token_x_cumulative_earned_per_m_liq, UnsignedDecimal("0"))
        self.assertEqual(RRRL.token_x_cumulative_earned_per_m_liq, UnsignedDecimal("0"))
        self.assertEqual(RRRR.token_x_cumulative_earned_per_m_liq, UnsignedDecimal("0"))

        # token_x_cumulative_earned_per_m_subtree_liq
        self.assertEqual(root.token_x_cumulative_earned_per_m_subtree_liq, UnsignedDecimal("0"))
        self.assertEqual(R.token_x_cumulative_earned_per_m_subtree_liq, UnsignedDecimal("0"))
        self.assertEqual(RL.token_x_cumulative_earned_per_m_subtree_liq, UnsignedDecimal("0"))
        self.assertEqual(RR.token_x_cumulative_earned_per_m_subtree_liq, UnsignedDecimal("0"))
        self.assertEqual(RLR.token_x_cumulative_earned_per_m_subtree_liq, UnsignedDecimal("0"))
        self.assertEqual(RRL.token_x_cumulative_earned_per_m_subtree_liq, UnsignedDecimal("0"))
        self.assertEqual(RRR.token_x_cumulative_earned_per_m_subtree_liq, UnsignedDecimal("0"))
        self.assertEqual(RLRL.token_x_cumulative_earned_per_m_subtree_liq, UnsignedDecimal("0"))
        self.assertEqual(RLRR.token_x_cumulative_earned_per_m_subtree_liq, UnsignedDecimal("0"))
        self.assertEqual(RRLL.token_x_cumulative_earned_per_m_subtree_liq, UnsignedDecimal("0"))
        self.assertEqual(RRLR.token_x_cumulative_earned_per_m_subtree_liq, UnsignedDecimal("0"))
        self.assertEqual(RRRL.token_x_cumulative_earned_per_m_subtree_liq, UnsignedDecimal("0"))
        self.assertEqual(RRRR.token_x_cumulative_earned_per_m_subtree_liq, UnsignedDecimal("0"))

        # token_y_cumulative_earned_per_m_liq
        self.assertEqual(root.token_y_cumulative_earned_per_m_liq, UnsignedDecimal("0"))
        self.assertEqual(R.token_y_cumulative_earned_per_m_liq, UnsignedDecimal("0"))
        self.assertEqual(RL.token_y_cumulative_earned_per_m_liq, UnsignedDecimal("0"))
        self.assertEqual(RR.token_y_cumulative_earned_per_m_liq, UnsignedDecimal("0"))
        self.assertEqual(RLR.token_y_cumulative_earned_per_m_liq, UnsignedDecimal("0"))
        self.assertEqual(RRL.token_y_cumulative_earned_per_m_liq, UnsignedDecimal("0"))
        self.assertEqual(RRR.token_y_cumulative_earned_per_m_liq, UnsignedDecimal("0"))
        self.assertEqual(RLRL.token_y_cumulative_earned_per_m_liq, UnsignedDecimal("0"))
        self.assertEqual(RLRR.token_y_cumulative_earned_per_m_liq, UnsignedDecimal("0"))
        self.assertEqual(RRLL.token_y_cumulative_earned_per_m_liq, UnsignedDecimal("0"))
        self.assertEqual(RRLR.token_y_cumulative_earned_per_m_liq, UnsignedDecimal("0"))
        self.assertEqual(RRRL.token_y_cumulative_earned_per_m_liq, UnsignedDecimal("0"))
        self.assertEqual(RRRR.token_y_cumulative_earned_per_m_liq, UnsignedDecimal("0"))

        # token_y_cumulative_earned_per_m_subtree_liq
        self.assertEqual(root.token_y_cumulative_earned_per_m_subtree_liq, UnsignedDecimal("0"))
        self.assertEqual(R.token_y_cumulative_earned_per_m_subtree_liq, UnsignedDecimal("0"))
        self.assertEqual(RL.token_y_cumulative_earned_per_m_subtree_liq, UnsignedDecimal("0"))
        self.assertEqual(RR.token_y_cumulative_earned_per_m_subtree_liq, UnsignedDecimal("0"))
        self.assertEqual(RLR.token_y_cumulative_earned_per_m_subtree_liq, UnsignedDecimal("0"))
        self.assertEqual(RRL.token_y_cumulative_earned_per_m_subtree_liq, UnsignedDecimal("0"))
        self.assertEqual(RRR.token_y_cumulative_earned_per_m_subtree_liq, UnsignedDecimal("0"))
        self.assertEqual(RLRL.token_y_cumulative_earned_per_m_subtree_liq, UnsignedDecimal("0"))
        self.assertEqual(RLRR.token_y_cumulative_earned_per_m_subtree_liq, UnsignedDecimal("0"))
        self.assertEqual(RRLL.token_y_cumulative_earned_per_m_subtree_liq, UnsignedDecimal("0"))
        self.assertEqual(RRLR.token_y_cumulative_earned_per_m_subtree_liq, UnsignedDecimal("0"))
        self.assertEqual(RRRL.token_y_cumulative_earned_per_m_subtree_liq, UnsignedDecimal("0"))
        self.assertEqual(RRRR.token_y_cumulative_earned_per_m_subtree_liq, UnsignedDecimal("0"))

    def test_adding_m_liq_left_and_right_leg_at_or_higher_than_peak(self):
        # range 0-0
        liq_tree: LiquidityTree = self.liq_tree

        root: LiqNode = liq_tree.nodes[liq_tree.root_key]
        L: LiqNode = liq_tree.nodes[(8 << 24) | 16]
        LL: LiqNode = liq_tree.nodes[(4 << 24) | 16]
        LLL: LiqNode = liq_tree.nodes[(2 << 24) | 16]
        LLLL: LiqNode = liq_tree.nodes[(1 << 24) | 16]

        self.liq_tree.add_m_liq(LiqRange(low=0, high=0), UnsignedDecimal("7"))  # LLLL

        # m_liq
        self.assertEqual(root.m_liq, UnsignedDecimal("0"))
        self.assertEqual(L.m_liq, UnsignedDecimal("0"))
        self.assertEqual(LL.m_liq, UnsignedDecimal("0"))
        self.assertEqual(LLL.m_liq, UnsignedDecimal("0"))
        self.assertEqual(LLLL.m_liq, UnsignedDecimal("7"))

        # t_liq
        self.assertEqual(root.t_liq, UnsignedDecimal("0"))
        self.assertEqual(L.t_liq, UnsignedDecimal("0"))
        self.assertEqual(LL.t_liq, UnsignedDecimal("0"))
        self.assertEqual(LLL.t_liq, UnsignedDecimal("0"))
        self.assertEqual(LLLL.t_liq, UnsignedDecimal("0"))

        # subtree_m_liq
        self.assertEqual(root.subtree_m_liq, UnsignedDecimal("7"))
        self.assertEqual(L.subtree_m_liq, UnsignedDecimal("7"))
        self.assertEqual(LL.subtree_m_liq, UnsignedDecimal("7"))
        self.assertEqual(LLL.subtree_m_liq, UnsignedDecimal("7"))
        self.assertEqual(LLLL.subtree_m_liq, UnsignedDecimal("7"))

        # borrowed_x
        self.assertEqual(root.token_x_borrowed, UnsignedDecimal("0"))
        self.assertEqual(L.token_x_borrowed, UnsignedDecimal("0"))
        self.assertEqual(LL.token_x_borrowed, UnsignedDecimal("0"))
        self.assertEqual(LLL.token_x_borrowed, UnsignedDecimal("0"))
        self.assertEqual(LLLL.token_x_borrowed, UnsignedDecimal("0"))

        # subtree_borrowed_x
        self.assertEqual(root.token_x_subtree_borrowed, UnsignedDecimal("0"))
        self.assertEqual(L.token_x_subtree_borrowed, UnsignedDecimal("0"))
        self.assertEqual(LL.token_x_subtree_borrowed, UnsignedDecimal("0"))
        self.assertEqual(LLL.token_x_subtree_borrowed, UnsignedDecimal("0"))
        self.assertEqual(LLLL.token_x_subtree_borrowed, UnsignedDecimal("0"))

        # borrowed_y
        self.assertEqual(root.token_y_borrowed, UnsignedDecimal("0"))
        self.assertEqual(L.token_y_borrowed, UnsignedDecimal("0"))
        self.assertEqual(LL.token_y_borrowed, UnsignedDecimal("0"))
        self.assertEqual(LLL.token_y_borrowed, UnsignedDecimal("0"))
        self.assertEqual(LLLL.token_y_borrowed, UnsignedDecimal("0"))

        # subtree_borrowed_y
        self.assertEqual(root.token_y_subtree_borrowed, UnsignedDecimal("0"))
        self.assertEqual(L.token_y_subtree_borrowed, UnsignedDecimal("0"))
        self.assertEqual(LL.token_y_subtree_borrowed, UnsignedDecimal("0"))
        self.assertEqual(LLL.token_y_subtree_borrowed, UnsignedDecimal("0"))
        self.assertEqual(LLLL.token_y_subtree_borrowed, UnsignedDecimal("0"))

        # token_x_cumulative_earned_per_m_liq
        self.assertEqual(root.token_x_cumulative_earned_per_m_liq, UnsignedDecimal("0"))
        self.assertEqual(L.token_x_cumulative_earned_per_m_liq, UnsignedDecimal("0"))
        self.assertEqual(LL.token_x_cumulative_earned_per_m_liq, UnsignedDecimal("0"))
        self.assertEqual(LLL.token_x_cumulative_earned_per_m_liq, UnsignedDecimal("0"))
        self.assertEqual(LLLL.token_x_cumulative_earned_per_m_liq, UnsignedDecimal("0"))

        # token_x_cumulative_earned_per_m_subtree_liq
        self.assertEqual(root.token_x_cumulative_earned_per_m_subtree_liq, UnsignedDecimal("0"))
        self.assertEqual(L.token_x_cumulative_earned_per_m_subtree_liq, UnsignedDecimal("0"))
        self.assertEqual(LL.token_x_cumulative_earned_per_m_subtree_liq, UnsignedDecimal("0"))
        self.assertEqual(LLL.token_x_cumulative_earned_per_m_subtree_liq, UnsignedDecimal("0"))
        self.assertEqual(LLLL.token_x_cumulative_earned_per_m_subtree_liq, UnsignedDecimal("0"))

        # token_y_cumulative_earned_per_m_liq
        self.assertEqual(root.token_y_cumulative_earned_per_m_liq, UnsignedDecimal("0"))
        self.assertEqual(L.token_y_cumulative_earned_per_m_liq, UnsignedDecimal("0"))
        self.assertEqual(LL.token_y_cumulative_earned_per_m_liq, UnsignedDecimal("0"))
        self.assertEqual(LLL.token_y_cumulative_earned_per_m_liq, UnsignedDecimal("0"))
        self.assertEqual(LLLL.token_y_cumulative_earned_per_m_liq, UnsignedDecimal("0"))

        # token_y_cumulative_earned_per_m_subtree_liq
        self.assertEqual(root.token_y_cumulative_earned_per_m_subtree_liq, UnsignedDecimal("0"))
        self.assertEqual(L.token_y_cumulative_earned_per_m_subtree_liq, UnsignedDecimal("0"))
        self.assertEqual(LL.token_y_cumulative_earned_per_m_subtree_liq, UnsignedDecimal("0"))
        self.assertEqual(LLL.token_y_cumulative_earned_per_m_subtree_liq, UnsignedDecimal("0"))
        self.assertEqual(LLLL.token_y_cumulative_earned_per_m_subtree_liq, UnsignedDecimal("0"))

    def test_adding_m_liq_left_and_right_leg_same_distance_to_stop(self):
        # range 1-2

        liq_tree: LiquidityTree = self.liq_tree

        root: LiqNode = liq_tree.nodes[liq_tree.root_key]
        L: LiqNode = liq_tree.nodes[(8 << 24) | 16]
        LL: LiqNode = liq_tree.nodes[(4 << 24) | 16]
        LLL: LiqNode = liq_tree.nodes[(2 << 24) | 16]
        LLR: LiqNode = liq_tree.nodes[(2 << 24) | 18]
        LLLR: LiqNode = liq_tree.nodes[(1 << 24) | 17]
        LLRL: LiqNode = liq_tree.nodes[(1 << 24) | 18]

        self.liq_tree.add_m_liq(LiqRange(low=1, high=2), UnsignedDecimal("72"))  # LLLR, LLRL

        # m_liq
        self.assertEqual(root.m_liq, UnsignedDecimal("0"))
        self.assertEqual(L.m_liq, UnsignedDecimal("0"))
        self.assertEqual(LL.m_liq, UnsignedDecimal("0"))
        self.assertEqual(LLL.m_liq, UnsignedDecimal("0"))
        self.assertEqual(LLR.m_liq, UnsignedDecimal("0"))
        self.assertEqual(LLLR.m_liq, UnsignedDecimal("72"))
        self.assertEqual(LLRL.m_liq, UnsignedDecimal("72"))

        # t_liq
        self.assertEqual(root.t_liq, UnsignedDecimal("0"))
        self.assertEqual(L.t_liq, UnsignedDecimal("0"))
        self.assertEqual(LL.t_liq, UnsignedDecimal("0"))
        self.assertEqual(LLL.t_liq, UnsignedDecimal("0"))
        self.assertEqual(LLR.t_liq, UnsignedDecimal("0"))
        self.assertEqual(LLLR.t_liq, UnsignedDecimal("0"))
        self.assertEqual(LLRL.t_liq, UnsignedDecimal("0"))

        # subtree_m_liq
        self.assertEqual(root.subtree_m_liq, UnsignedDecimal("144"))
        self.assertEqual(L.subtree_m_liq, UnsignedDecimal("144"))
        self.assertEqual(LL.subtree_m_liq, UnsignedDecimal("144"))
        self.assertEqual(LLL.subtree_m_liq, UnsignedDecimal("72"))
        self.assertEqual(LLR.subtree_m_liq, UnsignedDecimal("72"))
        self.assertEqual(LLLR.subtree_m_liq, UnsignedDecimal("72"))
        self.assertEqual(LLRL.subtree_m_liq, UnsignedDecimal("72"))

        # borrowed_x
        self.assertEqual(root.token_x_borrowed, UnsignedDecimal("0"))
        self.assertEqual(L.token_x_borrowed, UnsignedDecimal("0"))
        self.assertEqual(LL.token_x_borrowed, UnsignedDecimal("0"))
        self.assertEqual(LLL.token_x_borrowed, UnsignedDecimal("0"))
        self.assertEqual(LLR.token_x_borrowed, UnsignedDecimal("0"))
        self.assertEqual(LLLR.token_x_borrowed, UnsignedDecimal("0"))
        self.assertEqual(LLRL.token_x_borrowed, UnsignedDecimal("0"))

        # subtree_borrowed_x
        self.assertEqual(root.token_x_subtree_borrowed, UnsignedDecimal("0"))
        self.assertEqual(L.token_x_subtree_borrowed, UnsignedDecimal("0"))
        self.assertEqual(LL.token_x_subtree_borrowed, UnsignedDecimal("0"))
        self.assertEqual(LLL.token_x_subtree_borrowed, UnsignedDecimal("0"))
        self.assertEqual(LLR.token_x_subtree_borrowed, UnsignedDecimal("0"))
        self.assertEqual(LLLR.token_x_subtree_borrowed, UnsignedDecimal("0"))
        self.assertEqual(LLRL.token_x_subtree_borrowed, UnsignedDecimal("0"))

        # borrowed_y
        self.assertEqual(root.token_y_borrowed, UnsignedDecimal("0"))
        self.assertEqual(L.token_y_borrowed, UnsignedDecimal("0"))
        self.assertEqual(LL.token_y_borrowed, UnsignedDecimal("0"))
        self.assertEqual(LLL.token_y_borrowed, UnsignedDecimal("0"))
        self.assertEqual(LLR.token_y_borrowed, UnsignedDecimal("0"))
        self.assertEqual(LLLR.token_y_borrowed, UnsignedDecimal("0"))
        self.assertEqual(LLRL.token_y_borrowed, UnsignedDecimal("0"))

        # subtree_borrowed_y
        self.assertEqual(root.token_y_subtree_borrowed, UnsignedDecimal("0"))
        self.assertEqual(L.token_y_subtree_borrowed, UnsignedDecimal("0"))
        self.assertEqual(LL.token_y_subtree_borrowed, UnsignedDecimal("0"))
        self.assertEqual(LLL.token_y_subtree_borrowed, UnsignedDecimal("0"))
        self.assertEqual(LLR.token_y_subtree_borrowed, UnsignedDecimal("0"))
        self.assertEqual(LLLR.token_y_subtree_borrowed, UnsignedDecimal("0"))
        self.assertEqual(LLRL.token_y_subtree_borrowed, UnsignedDecimal("0"))

        # token_x_cumulative_earned_per_m_liq
        self.assertEqual(root.token_x_cumulative_earned_per_m_liq, UnsignedDecimal("0"))
        self.assertEqual(L.token_x_cumulative_earned_per_m_liq, UnsignedDecimal("0"))
        self.assertEqual(LL.token_x_cumulative_earned_per_m_liq, UnsignedDecimal("0"))
        self.assertEqual(LLL.token_x_cumulative_earned_per_m_liq, UnsignedDecimal("0"))
        self.assertEqual(LLR.token_x_cumulative_earned_per_m_liq, UnsignedDecimal("0"))
        self.assertEqual(LLLR.token_x_cumulative_earned_per_m_liq, UnsignedDecimal("0"))
        self.assertEqual(LLRL.token_x_cumulative_earned_per_m_liq, UnsignedDecimal("0"))

        # token_x_cumulative_earned_per_m_subtree_liq
        self.assertEqual(root.token_x_cumulative_earned_per_m_subtree_liq, UnsignedDecimal("0"))
        self.assertEqual(L.token_x_cumulative_earned_per_m_subtree_liq, UnsignedDecimal("0"))
        self.assertEqual(LL.token_x_cumulative_earned_per_m_subtree_liq, UnsignedDecimal("0"))
        self.assertEqual(LLL.token_x_cumulative_earned_per_m_subtree_liq, UnsignedDecimal("0"))
        self.assertEqual(LLR.token_x_cumulative_earned_per_m_subtree_liq, UnsignedDecimal("0"))
        self.assertEqual(LLLR.token_x_cumulative_earned_per_m_subtree_liq, UnsignedDecimal("0"))
        self.assertEqual(LLRL.token_x_cumulative_earned_per_m_subtree_liq, UnsignedDecimal("0"))

        # token_y_cumulative_earned_per_m_liq
        self.assertEqual(root.token_y_cumulative_earned_per_m_liq, UnsignedDecimal("0"))
        self.assertEqual(L.token_y_cumulative_earned_per_m_liq, UnsignedDecimal("0"))
        self.assertEqual(LL.token_y_cumulative_earned_per_m_liq, UnsignedDecimal("0"))
        self.assertEqual(LLL.token_y_cumulative_earned_per_m_liq, UnsignedDecimal("0"))
        self.assertEqual(LLR.token_y_cumulative_earned_per_m_liq, UnsignedDecimal("0"))
        self.assertEqual(LLLR.token_y_cumulative_earned_per_m_liq, UnsignedDecimal("0"))
        self.assertEqual(LLRL.token_y_cumulative_earned_per_m_liq, UnsignedDecimal("0"))

        # token_y_cumulative_earned_per_m_subtree_liq
        self.assertEqual(root.token_y_cumulative_earned_per_m_subtree_liq, UnsignedDecimal("0"))
        self.assertEqual(L.token_y_cumulative_earned_per_m_subtree_liq, UnsignedDecimal("0"))
        self.assertEqual(LL.token_y_cumulative_earned_per_m_subtree_liq, UnsignedDecimal("0"))
        self.assertEqual(LLL.token_y_cumulative_earned_per_m_subtree_liq, UnsignedDecimal("0"))
        self.assertEqual(LLR.token_y_cumulative_earned_per_m_subtree_liq, UnsignedDecimal("0"))
        self.assertEqual(LLLR.token_y_cumulative_earned_per_m_subtree_liq, UnsignedDecimal("0"))
        self.assertEqual(LLRL.token_y_cumulative_earned_per_m_subtree_liq, UnsignedDecimal("0"))

    def test_adding_m_liq_left_leg_lower_than_right_leg(self):
        # range 1-5
        liq_tree: LiquidityTree = self.liq_tree

        root: LiqNode = liq_tree.nodes[liq_tree.root_key]
        L: LiqNode = liq_tree.nodes[(8 << 24) | 16]
        LL: LiqNode = liq_tree.nodes[(4 << 24) | 16]
        LR: LiqNode = liq_tree.nodes[(4 << 24) | 20]
        LLL: LiqNode = liq_tree.nodes[(2 << 24) | 16]
        LLR: LiqNode = liq_tree.nodes[(2 << 24) | 18]
        LRL: LiqNode = liq_tree.nodes[(2 << 24) | 20]
        LLLR: LiqNode = liq_tree.nodes[(1 << 24) | 17]
        LLRL: LiqNode = liq_tree.nodes[(1 << 24) | 18]
        LLRR: LiqNode = liq_tree.nodes[(1 << 24) | 19]
        LRLL: LiqNode = liq_tree.nodes[(1 << 24) | 20]
        LRLR: LiqNode = liq_tree.nodes[(1 << 24) | 21]


        self.liq_tree.add_m_liq(LiqRange(low=1, high=5), UnsignedDecimal("81"))  # LLLR, LLR, LRL

        # m_liq
        self.assertEqual(root.m_liq, UnsignedDecimal("0"))
        self.assertEqual(L.m_liq, UnsignedDecimal("0"))
        self.assertEqual(LL.m_liq, UnsignedDecimal("0"))
        self.assertEqual(LR.m_liq, UnsignedDecimal("0"))
        self.assertEqual(LLL.m_liq, UnsignedDecimal("0"))
        self.assertEqual(LLR.m_liq, UnsignedDecimal("81"))
        self.assertEqual(LRL.m_liq, UnsignedDecimal("81"))
        self.assertEqual(LLLR.m_liq, UnsignedDecimal("81"))
        self.assertEqual(LLRL.m_liq, UnsignedDecimal("0"))
        self.assertEqual(LLRR.m_liq, UnsignedDecimal("0"))
        self.assertEqual(LRLL.m_liq, UnsignedDecimal("0"))
        self.assertEqual(LRLR.m_liq, UnsignedDecimal("0"))

        # t_liq
        self.assertEqual(root.t_liq, UnsignedDecimal("0"))
        self.assertEqual(L.t_liq, UnsignedDecimal("0"))
        self.assertEqual(LL.t_liq, UnsignedDecimal("0"))
        self.assertEqual(LR.t_liq, UnsignedDecimal("0"))
        self.assertEqual(LLL.t_liq, UnsignedDecimal("0"))
        self.assertEqual(LLR.t_liq, UnsignedDecimal("0"))
        self.assertEqual(LRL.t_liq, UnsignedDecimal("0"))
        self.assertEqual(LLLR.t_liq, UnsignedDecimal("0"))
        self.assertEqual(LLRL.t_liq, UnsignedDecimal("0"))
        self.assertEqual(LLRR.t_liq, UnsignedDecimal("0"))
        self.assertEqual(LRLL.t_liq, UnsignedDecimal("0"))
        self.assertEqual(LRLR.t_liq, UnsignedDecimal("0"))

        # subtree_m_liq
        self.assertEqual(root.subtree_m_liq, UnsignedDecimal("405"))
        self.assertEqual(L.subtree_m_liq, UnsignedDecimal("405"))
        self.assertEqual(LL.subtree_m_liq, UnsignedDecimal("243"))
        self.assertEqual(LR.subtree_m_liq, UnsignedDecimal("162"))
        self.assertEqual(LLL.subtree_m_liq, UnsignedDecimal("81"))
        self.assertEqual(LLR.subtree_m_liq, UnsignedDecimal("162"))
        self.assertEqual(LRL.subtree_m_liq, UnsignedDecimal("162"))
        self.assertEqual(LLLR.subtree_m_liq, UnsignedDecimal("81"))
        self.assertEqual(LLRL.subtree_m_liq, UnsignedDecimal("0"))
        self.assertEqual(LLRR.subtree_m_liq, UnsignedDecimal("0"))
        self.assertEqual(LRLL.subtree_m_liq, UnsignedDecimal("0"))
        self.assertEqual(LRLR.subtree_m_liq, UnsignedDecimal("0"))

        # borrowed_x
        self.assertEqual(root.token_x_borrowed, UnsignedDecimal("0"))
        self.assertEqual(L.token_x_borrowed, UnsignedDecimal("0"))
        self.assertEqual(LL.token_x_borrowed, UnsignedDecimal("0"))
        self.assertEqual(LR.token_x_borrowed, UnsignedDecimal("0"))
        self.assertEqual(LLL.token_x_borrowed, UnsignedDecimal("0"))
        self.assertEqual(LLR.token_x_borrowed, UnsignedDecimal("0"))
        self.assertEqual(LRL.token_x_borrowed, UnsignedDecimal("0"))
        self.assertEqual(LLLR.token_x_borrowed, UnsignedDecimal("0"))
        self.assertEqual(LLRL.token_x_borrowed, UnsignedDecimal("0"))
        self.assertEqual(LLRR.token_x_borrowed, UnsignedDecimal("0"))
        self.assertEqual(LRLL.token_x_borrowed, UnsignedDecimal("0"))
        self.assertEqual(LRLR.token_x_borrowed, UnsignedDecimal("0"))

        # subtree_borrowed_x
        self.assertEqual(root.token_x_subtree_borrowed, UnsignedDecimal("0"))
        self.assertEqual(L.token_x_subtree_borrowed, UnsignedDecimal("0"))
        self.assertEqual(LL.token_x_subtree_borrowed, UnsignedDecimal("0"))
        self.assertEqual(LR.token_x_subtree_borrowed, UnsignedDecimal("0"))
        self.assertEqual(LLL.token_x_subtree_borrowed, UnsignedDecimal("0"))
        self.assertEqual(LLR.token_x_subtree_borrowed, UnsignedDecimal("0"))
        self.assertEqual(LRL.token_x_subtree_borrowed, UnsignedDecimal("0"))
        self.assertEqual(LLLR.token_x_subtree_borrowed, UnsignedDecimal("0"))
        self.assertEqual(LLRL.token_x_subtree_borrowed, UnsignedDecimal("0"))
        self.assertEqual(LLRR.token_x_subtree_borrowed, UnsignedDecimal("0"))
        self.assertEqual(LRLL.token_x_subtree_borrowed, UnsignedDecimal("0"))
        self.assertEqual(LRLR.token_x_subtree_borrowed, UnsignedDecimal("0"))

        # borrowed_y
        self.assertEqual(root.token_y_borrowed, UnsignedDecimal("0"))
        self.assertEqual(L.token_y_borrowed, UnsignedDecimal("0"))
        self.assertEqual(LL.token_y_borrowed, UnsignedDecimal("0"))
        self.assertEqual(LR.token_y_borrowed, UnsignedDecimal("0"))
        self.assertEqual(LLL.token_y_borrowed, UnsignedDecimal("0"))
        self.assertEqual(LLR.token_y_borrowed, UnsignedDecimal("0"))
        self.assertEqual(LRL.token_y_borrowed, UnsignedDecimal("0"))
        self.assertEqual(LLLR.token_y_borrowed, UnsignedDecimal("0"))
        self.assertEqual(LLRL.token_y_borrowed, UnsignedDecimal("0"))
        self.assertEqual(LLRR.token_y_borrowed, UnsignedDecimal("0"))
        self.assertEqual(LRLL.token_y_borrowed, UnsignedDecimal("0"))
        self.assertEqual(LRLR.token_y_borrowed, UnsignedDecimal("0"))

        # subtree_borrowed_y
        self.assertEqual(root.token_y_subtree_borrowed, UnsignedDecimal("0"))
        self.assertEqual(L.token_y_subtree_borrowed, UnsignedDecimal("0"))
        self.assertEqual(LL.token_y_subtree_borrowed, UnsignedDecimal("0"))
        self.assertEqual(LR.token_y_subtree_borrowed, UnsignedDecimal("0"))
        self.assertEqual(LLL.token_y_subtree_borrowed, UnsignedDecimal("0"))
        self.assertEqual(LLR.token_y_subtree_borrowed, UnsignedDecimal("0"))
        self.assertEqual(LRL.token_y_subtree_borrowed, UnsignedDecimal("0"))
        self.assertEqual(LLLR.token_y_subtree_borrowed, UnsignedDecimal("0"))
        self.assertEqual(LLRL.token_y_subtree_borrowed, UnsignedDecimal("0"))
        self.assertEqual(LLRR.token_y_subtree_borrowed, UnsignedDecimal("0"))
        self.assertEqual(LRLL.token_y_subtree_borrowed, UnsignedDecimal("0"))
        self.assertEqual(LRLR.token_y_subtree_borrowed, UnsignedDecimal("0"))

        # token_x_cumulative_earned_per_m_liq
        self.assertEqual(root.token_x_cumulative_earned_per_m_liq, UnsignedDecimal("0"))
        self.assertEqual(L.token_x_cumulative_earned_per_m_liq, UnsignedDecimal("0"))
        self.assertEqual(LL.token_x_cumulative_earned_per_m_liq, UnsignedDecimal("0"))
        self.assertEqual(LR.token_x_cumulative_earned_per_m_liq, UnsignedDecimal("0"))
        self.assertEqual(LLL.token_x_cumulative_earned_per_m_liq, UnsignedDecimal("0"))
        self.assertEqual(LLR.token_x_cumulative_earned_per_m_liq, UnsignedDecimal("0"))
        self.assertEqual(LRL.token_x_cumulative_earned_per_m_liq, UnsignedDecimal("0"))
        self.assertEqual(LLLR.token_x_cumulative_earned_per_m_liq, UnsignedDecimal("0"))
        self.assertEqual(LLRL.token_x_cumulative_earned_per_m_liq, UnsignedDecimal("0"))
        self.assertEqual(LLRR.token_x_cumulative_earned_per_m_liq, UnsignedDecimal("0"))
        self.assertEqual(LRLL.token_x_cumulative_earned_per_m_liq, UnsignedDecimal("0"))
        self.assertEqual(LRLR.token_x_cumulative_earned_per_m_liq, UnsignedDecimal("0"))

        # token_x_cumulative_earned_per_m_subtree_liq
        self.assertEqual(root.token_x_cumulative_earned_per_m_subtree_liq, UnsignedDecimal("0"))
        self.assertEqual(L.token_x_cumulative_earned_per_m_subtree_liq, UnsignedDecimal("0"))
        self.assertEqual(LL.token_x_cumulative_earned_per_m_subtree_liq, UnsignedDecimal("0"))
        self.assertEqual(LR.token_x_cumulative_earned_per_m_subtree_liq, UnsignedDecimal("0"))
        self.assertEqual(LLL.token_x_cumulative_earned_per_m_subtree_liq, UnsignedDecimal("0"))
        self.assertEqual(LLR.token_x_cumulative_earned_per_m_subtree_liq, UnsignedDecimal("0"))
        self.assertEqual(LRL.token_x_cumulative_earned_per_m_subtree_liq, UnsignedDecimal("0"))
        self.assertEqual(LLLR.token_x_cumulative_earned_per_m_subtree_liq, UnsignedDecimal("0"))
        self.assertEqual(LLRL.token_x_cumulative_earned_per_m_subtree_liq, UnsignedDecimal("0"))
        self.assertEqual(LLRR.token_x_cumulative_earned_per_m_subtree_liq, UnsignedDecimal("0"))
        self.assertEqual(LRLL.token_x_cumulative_earned_per_m_subtree_liq, UnsignedDecimal("0"))
        self.assertEqual(LRLR.token_x_cumulative_earned_per_m_subtree_liq, UnsignedDecimal("0"))

        # token_y_cumulative_earned_per_m_liq
        self.assertEqual(root.token_y_cumulative_earned_per_m_liq, UnsignedDecimal("0"))
        self.assertEqual(L.token_y_cumulative_earned_per_m_liq, UnsignedDecimal("0"))
        self.assertEqual(LL.token_y_cumulative_earned_per_m_liq, UnsignedDecimal("0"))
        self.assertEqual(LR.token_y_cumulative_earned_per_m_liq, UnsignedDecimal("0"))
        self.assertEqual(LLL.token_y_cumulative_earned_per_m_liq, UnsignedDecimal("0"))
        self.assertEqual(LLR.token_y_cumulative_earned_per_m_liq, UnsignedDecimal("0"))
        self.assertEqual(LRL.token_y_cumulative_earned_per_m_liq, UnsignedDecimal("0"))
        self.assertEqual(LLLR.token_y_cumulative_earned_per_m_liq, UnsignedDecimal("0"))
        self.assertEqual(LLRL.token_y_cumulative_earned_per_m_liq, UnsignedDecimal("0"))
        self.assertEqual(LLRR.token_y_cumulative_earned_per_m_liq, UnsignedDecimal("0"))
        self.assertEqual(LRLL.token_y_cumulative_earned_per_m_liq, UnsignedDecimal("0"))
        self.assertEqual(LRLR.token_y_cumulative_earned_per_m_liq, UnsignedDecimal("0"))

        # token_y_cumulative_earned_per_m_subtree_liq
        self.assertEqual(root.token_y_cumulative_earned_per_m_subtree_liq, UnsignedDecimal("0"))
        self.assertEqual(L.token_y_cumulative_earned_per_m_subtree_liq, UnsignedDecimal("0"))
        self.assertEqual(LL.token_y_cumulative_earned_per_m_subtree_liq, UnsignedDecimal("0"))
        self.assertEqual(LR.token_y_cumulative_earned_per_m_subtree_liq, UnsignedDecimal("0"))
        self.assertEqual(LLL.token_y_cumulative_earned_per_m_subtree_liq, UnsignedDecimal("0"))
        self.assertEqual(LLR.token_y_cumulative_earned_per_m_subtree_liq, UnsignedDecimal("0"))
        self.assertEqual(LRL.token_y_cumulative_earned_per_m_subtree_liq, UnsignedDecimal("0"))
        self.assertEqual(LLLR.token_y_cumulative_earned_per_m_subtree_liq, UnsignedDecimal("0"))
        self.assertEqual(LLRL.token_y_cumulative_earned_per_m_subtree_liq, UnsignedDecimal("0"))
        self.assertEqual(LLRR.token_y_cumulative_earned_per_m_subtree_liq, UnsignedDecimal("0"))
        self.assertEqual(LRLL.token_y_cumulative_earned_per_m_subtree_liq, UnsignedDecimal("0"))
        self.assertEqual(LRLR.token_y_cumulative_earned_per_m_subtree_liq, UnsignedDecimal("0"))

    def test_adding_m_liq_right_leg_lower_than_left_leg(self):
        # range 2-6
        liq_tree: LiquidityTree = self.liq_tree

        root: LiqNode = liq_tree.nodes[liq_tree.root_key]
        L: LiqNode = liq_tree.nodes[(8 << 24) | 16]
        LL: LiqNode = liq_tree.nodes[(4 << 24) | 16]
        LR: LiqNode = liq_tree.nodes[(4 << 24) | 20]
        LLR: LiqNode = liq_tree.nodes[(2 << 24) | 18]
        LRL: LiqNode = liq_tree.nodes[(2 << 24) | 20]
        LRR: LiqNode = liq_tree.nodes[(2 << 24) | 22]
        LLRL: LiqNode = liq_tree.nodes[(1 << 24) | 18]
        LLRR: LiqNode = liq_tree.nodes[(1 << 24) | 19]
        LRLL: LiqNode = liq_tree.nodes[(1 << 24) | 20]
        LRLR: LiqNode = liq_tree.nodes[(1 << 24) | 21]
        LRRL: LiqNode = liq_tree.nodes[(1 << 24) | 22]

        self.liq_tree.add_m_liq(LiqRange(low=2, high=6), UnsignedDecimal("2"))  # LLR, LRL, LRRL

        # m_liq
        self.assertEqual(root.m_liq, UnsignedDecimal("0"))
        self.assertEqual(L.m_liq, UnsignedDecimal("0"))
        self.assertEqual(LL.m_liq, UnsignedDecimal("0"))
        self.assertEqual(LR.m_liq, UnsignedDecimal("0"))
        self.assertEqual(LLR.m_liq, UnsignedDecimal("2"))
        self.assertEqual(LRL.m_liq, UnsignedDecimal("2"))
        self.assertEqual(LRR.m_liq, UnsignedDecimal("0"))
        self.assertEqual(LLRL.m_liq, UnsignedDecimal("0"))
        self.assertEqual(LLRR.m_liq, UnsignedDecimal("0"))
        self.assertEqual(LRLL.m_liq, UnsignedDecimal("0"))
        self.assertEqual(LRLR.m_liq, UnsignedDecimal("0"))
        self.assertEqual(LRRL.m_liq, UnsignedDecimal("2"))

        # t_liq
        self.assertEqual(root.t_liq, UnsignedDecimal("0"))
        self.assertEqual(L.t_liq, UnsignedDecimal("0"))
        self.assertEqual(LL.t_liq, UnsignedDecimal("0"))
        self.assertEqual(LR.t_liq, UnsignedDecimal("0"))
        self.assertEqual(LLR.t_liq, UnsignedDecimal("0"))
        self.assertEqual(LRL.t_liq, UnsignedDecimal("0"))
        self.assertEqual(LRR.t_liq, UnsignedDecimal("0"))
        self.assertEqual(LLRL.t_liq, UnsignedDecimal("0"))
        self.assertEqual(LLRR.t_liq, UnsignedDecimal("0"))
        self.assertEqual(LRLL.t_liq, UnsignedDecimal("0"))
        self.assertEqual(LRLR.t_liq, UnsignedDecimal("0"))
        self.assertEqual(LRRL.t_liq, UnsignedDecimal("0"))

        # subtree_m_liq
        self.assertEqual(root.subtree_m_liq, UnsignedDecimal("10"))
        self.assertEqual(L.subtree_m_liq, UnsignedDecimal("10"))
        self.assertEqual(LL.subtree_m_liq, UnsignedDecimal("4"))
        self.assertEqual(LR.subtree_m_liq, UnsignedDecimal("6"))
        self.assertEqual(LLR.subtree_m_liq, UnsignedDecimal("4"))
        self.assertEqual(LRL.subtree_m_liq, UnsignedDecimal("4"))
        self.assertEqual(LRR.subtree_m_liq, UnsignedDecimal("2"))
        self.assertEqual(LLRL.subtree_m_liq, UnsignedDecimal("0"))
        self.assertEqual(LLRR.subtree_m_liq, UnsignedDecimal("0"))
        self.assertEqual(LRLL.subtree_m_liq, UnsignedDecimal("0"))
        self.assertEqual(LRLR.subtree_m_liq, UnsignedDecimal("0"))
        self.assertEqual(LRRL.subtree_m_liq, UnsignedDecimal("2"))

        # borrowed_x
        self.assertEqual(root.token_x_borrowed, UnsignedDecimal("0"))
        self.assertEqual(L.token_x_borrowed, UnsignedDecimal("0"))
        self.assertEqual(LL.token_x_borrowed, UnsignedDecimal("0"))
        self.assertEqual(LR.token_x_borrowed, UnsignedDecimal("0"))
        self.assertEqual(LLR.token_x_borrowed, UnsignedDecimal("0"))
        self.assertEqual(LRL.token_x_borrowed, UnsignedDecimal("0"))
        self.assertEqual(LRR.token_x_borrowed, UnsignedDecimal("0"))
        self.assertEqual(LLRL.token_x_borrowed, UnsignedDecimal("0"))
        self.assertEqual(LLRR.token_x_borrowed, UnsignedDecimal("0"))
        self.assertEqual(LRLL.token_x_borrowed, UnsignedDecimal("0"))
        self.assertEqual(LRLR.token_x_borrowed, UnsignedDecimal("0"))
        self.assertEqual(LRRL.token_x_borrowed, UnsignedDecimal("0"))

        # subtree_borrowed_x
        self.assertEqual(root.token_x_subtree_borrowed, UnsignedDecimal("0"))
        self.assertEqual(L.token_x_subtree_borrowed, UnsignedDecimal("0"))
        self.assertEqual(LL.token_x_subtree_borrowed, UnsignedDecimal("0"))
        self.assertEqual(LR.token_x_subtree_borrowed, UnsignedDecimal("0"))
        self.assertEqual(LLR.token_x_subtree_borrowed, UnsignedDecimal("0"))
        self.assertEqual(LRL.token_x_subtree_borrowed, UnsignedDecimal("0"))
        self.assertEqual(LRR.token_x_subtree_borrowed, UnsignedDecimal("0"))
        self.assertEqual(LLRL.token_x_subtree_borrowed, UnsignedDecimal("0"))
        self.assertEqual(LLRR.token_x_subtree_borrowed, UnsignedDecimal("0"))
        self.assertEqual(LRLL.token_x_subtree_borrowed, UnsignedDecimal("0"))
        self.assertEqual(LRLR.token_x_subtree_borrowed, UnsignedDecimal("0"))
        self.assertEqual(LRRL.token_x_subtree_borrowed, UnsignedDecimal("0"))

        # borrowed_y
        self.assertEqual(root.token_y_borrowed, UnsignedDecimal("0"))
        self.assertEqual(L.token_y_borrowed, UnsignedDecimal("0"))
        self.assertEqual(LL.token_y_borrowed, UnsignedDecimal("0"))
        self.assertEqual(LR.token_y_borrowed, UnsignedDecimal("0"))
        self.assertEqual(LLR.token_y_borrowed, UnsignedDecimal("0"))
        self.assertEqual(LRL.token_y_borrowed, UnsignedDecimal("0"))
        self.assertEqual(LRR.token_y_borrowed, UnsignedDecimal("0"))
        self.assertEqual(LLRL.token_y_borrowed, UnsignedDecimal("0"))
        self.assertEqual(LLRR.token_y_borrowed, UnsignedDecimal("0"))
        self.assertEqual(LRLL.token_y_borrowed, UnsignedDecimal("0"))
        self.assertEqual(LRLR.token_y_borrowed, UnsignedDecimal("0"))
        self.assertEqual(LRRL.token_y_borrowed, UnsignedDecimal("0"))

        # subtree_borrowed_y
        self.assertEqual(root.token_y_subtree_borrowed, UnsignedDecimal("0"))
        self.assertEqual(L.token_y_subtree_borrowed, UnsignedDecimal("0"))
        self.assertEqual(LL.token_y_subtree_borrowed, UnsignedDecimal("0"))
        self.assertEqual(LR.token_y_subtree_borrowed, UnsignedDecimal("0"))
        self.assertEqual(LLR.token_y_subtree_borrowed, UnsignedDecimal("0"))
        self.assertEqual(LRL.token_y_subtree_borrowed, UnsignedDecimal("0"))
        self.assertEqual(LRR.token_y_subtree_borrowed, UnsignedDecimal("0"))
        self.assertEqual(LLRL.token_y_subtree_borrowed, UnsignedDecimal("0"))
        self.assertEqual(LLRR.token_y_subtree_borrowed, UnsignedDecimal("0"))
        self.assertEqual(LRLL.token_y_subtree_borrowed, UnsignedDecimal("0"))
        self.assertEqual(LRLR.token_y_subtree_borrowed, UnsignedDecimal("0"))
        self.assertEqual(LRRL.token_y_subtree_borrowed, UnsignedDecimal("0"))

        # token_x_cumulative_earned_per_m_liq
        self.assertEqual(root.token_x_cumulative_earned_per_m_liq, UnsignedDecimal("0"))
        self.assertEqual(L.token_x_cumulative_earned_per_m_liq, UnsignedDecimal("0"))
        self.assertEqual(LL.token_x_cumulative_earned_per_m_liq, UnsignedDecimal("0"))
        self.assertEqual(LR.token_x_cumulative_earned_per_m_liq, UnsignedDecimal("0"))
        self.assertEqual(LLR.token_x_cumulative_earned_per_m_liq, UnsignedDecimal("0"))
        self.assertEqual(LRL.token_x_cumulative_earned_per_m_liq, UnsignedDecimal("0"))
        self.assertEqual(LRR.token_x_cumulative_earned_per_m_liq, UnsignedDecimal("0"))
        self.assertEqual(LLRL.token_x_cumulative_earned_per_m_liq, UnsignedDecimal("0"))
        self.assertEqual(LLRR.token_x_cumulative_earned_per_m_liq, UnsignedDecimal("0"))
        self.assertEqual(LRLL.token_x_cumulative_earned_per_m_liq, UnsignedDecimal("0"))
        self.assertEqual(LRLR.token_x_cumulative_earned_per_m_liq, UnsignedDecimal("0"))
        self.assertEqual(LRRL.token_x_cumulative_earned_per_m_liq, UnsignedDecimal("0"))

        # token_x_cumulative_earned_per_m_subtree_liq
        self.assertEqual(root.token_x_cumulative_earned_per_m_subtree_liq, UnsignedDecimal("0"))
        self.assertEqual(L.token_x_cumulative_earned_per_m_subtree_liq, UnsignedDecimal("0"))
        self.assertEqual(LL.token_x_cumulative_earned_per_m_subtree_liq, UnsignedDecimal("0"))
        self.assertEqual(LR.token_x_cumulative_earned_per_m_subtree_liq, UnsignedDecimal("0"))
        self.assertEqual(LLR.token_x_cumulative_earned_per_m_subtree_liq, UnsignedDecimal("0"))
        self.assertEqual(LRL.token_x_cumulative_earned_per_m_subtree_liq, UnsignedDecimal("0"))
        self.assertEqual(LRR.token_x_cumulative_earned_per_m_subtree_liq, UnsignedDecimal("0"))
        self.assertEqual(LLRL.token_x_cumulative_earned_per_m_subtree_liq, UnsignedDecimal("0"))
        self.assertEqual(LLRR.token_x_cumulative_earned_per_m_subtree_liq, UnsignedDecimal("0"))
        self.assertEqual(LRLL.token_x_cumulative_earned_per_m_subtree_liq, UnsignedDecimal("0"))
        self.assertEqual(LRLR.token_x_cumulative_earned_per_m_subtree_liq, UnsignedDecimal("0"))
        self.assertEqual(LRRL.token_x_cumulative_earned_per_m_subtree_liq, UnsignedDecimal("0"))

        # token_y_cumulative_earned_per_m_liq
        self.assertEqual(root.token_y_cumulative_earned_per_m_liq, UnsignedDecimal("0"))
        self.assertEqual(L.token_y_cumulative_earned_per_m_liq, UnsignedDecimal("0"))
        self.assertEqual(LL.token_y_cumulative_earned_per_m_liq, UnsignedDecimal("0"))
        self.assertEqual(LR.token_y_cumulative_earned_per_m_liq, UnsignedDecimal("0"))
        self.assertEqual(LLR.token_y_cumulative_earned_per_m_liq, UnsignedDecimal("0"))
        self.assertEqual(LRL.token_y_cumulative_earned_per_m_liq, UnsignedDecimal("0"))
        self.assertEqual(LRR.token_y_cumulative_earned_per_m_liq, UnsignedDecimal("0"))
        self.assertEqual(LLRL.token_y_cumulative_earned_per_m_liq, UnsignedDecimal("0"))
        self.assertEqual(LLRR.token_y_cumulative_earned_per_m_liq, UnsignedDecimal("0"))
        self.assertEqual(LRLL.token_y_cumulative_earned_per_m_liq, UnsignedDecimal("0"))
        self.assertEqual(LRLR.token_y_cumulative_earned_per_m_liq, UnsignedDecimal("0"))
        self.assertEqual(LRRL.token_y_cumulative_earned_per_m_liq, UnsignedDecimal("0"))

        # token_y_cumulative_earned_per_m_subtree_liq
        self.assertEqual(root.token_y_cumulative_earned_per_m_subtree_liq, UnsignedDecimal("0"))
        self.assertEqual(L.token_y_cumulative_earned_per_m_subtree_liq, UnsignedDecimal("0"))
        self.assertEqual(LL.token_y_cumulative_earned_per_m_subtree_liq, UnsignedDecimal("0"))
        self.assertEqual(LR.token_y_cumulative_earned_per_m_subtree_liq, UnsignedDecimal("0"))
        self.assertEqual(LLR.token_y_cumulative_earned_per_m_subtree_liq, UnsignedDecimal("0"))
        self.assertEqual(LRL.token_y_cumulative_earned_per_m_subtree_liq, UnsignedDecimal("0"))
        self.assertEqual(LRR.token_y_cumulative_earned_per_m_subtree_liq, UnsignedDecimal("0"))
        self.assertEqual(LLRL.token_y_cumulative_earned_per_m_subtree_liq, UnsignedDecimal("0"))
        self.assertEqual(LLRR.token_y_cumulative_earned_per_m_subtree_liq, UnsignedDecimal("0"))
        self.assertEqual(LRLL.token_y_cumulative_earned_per_m_subtree_liq, UnsignedDecimal("0"))
        self.assertEqual(LRLR.token_y_cumulative_earned_per_m_subtree_liq, UnsignedDecimal("0"))
        self.assertEqual(LRRL.token_y_cumulative_earned_per_m_subtree_liq, UnsignedDecimal("0"))

    # endregion

    # t_liq
    def test_adding_t_liq_root_only(self):
        root: LiqNode = self.liq_tree.nodes[self.liq_tree.root_key]
        self.liq_tree.add_wide_t_liq(UnsignedDecimal("123"), UnsignedDecimal("456e18"), UnsignedDecimal("789e18"))

        self.assertEqual(root.m_liq, UnsignedDecimal("0"))
        self.assertEqual(root.subtree_m_liq, UnsignedDecimal("0"))
        self.assertEqual(root.t_liq, UnsignedDecimal("123"))
        self.assertEqual(root.token_x_borrowed, UnsignedDecimal("456e18"))
        self.assertEqual(root.token_x_subtree_borrowed, UnsignedDecimal("456e18"))
        self.assertEqual(root.token_y_borrowed, UnsignedDecimal("789e18"))
        self.assertEqual(root.token_y_subtree_borrowed, UnsignedDecimal("789e18"))

        self.assertEqual(self.liq_tree.token_x_fee_rate_snapshot, UnsignedDecimal("0"))
        self.assertEqual(self.liq_tree.token_y_fee_rate_snapshot, UnsignedDecimal("0"))

    def test_adding_t_liq_left_leg_only(self):
        # range 1-3
        liq_tree: LiquidityTree = self.liq_tree

        root: LiqNode = liq_tree.nodes[liq_tree.root_key]
        L: LiqNode = liq_tree.nodes[(8 << 24) | 16]
        LL: LiqNode = liq_tree.nodes[(4 << 24) | 16]
        LLL: LiqNode = liq_tree.nodes[(2 << 24) | 16]
        LLR: LiqNode = liq_tree.nodes[(2 << 24) | 18]
        LLLL: LiqNode = liq_tree.nodes[(1 << 24) | 16]
        LLLR: LiqNode = liq_tree.nodes[(1 << 24) | 17]
        LLRL: LiqNode = liq_tree.nodes[(1 << 24) | 18]
        LLRR: LiqNode = liq_tree.nodes[(1 << 24) | 19]

        self.liq_tree.add_m_liq(LiqRange(low=1, high=3), UnsignedDecimal("123"))  # LLLR, LLR
        self.liq_tree.add_t_liq(LiqRange(low=1, high=3), UnsignedDecimal("60"), UnsignedDecimal("456e18"), UnsignedDecimal("789e18"))  # LLLR, LLR

        # m_liq
        self.assertEqual(root.m_liq, UnsignedDecimal("0"))
        self.assertEqual(L.m_liq, UnsignedDecimal("0"))
        self.assertEqual(LL.m_liq, UnsignedDecimal("0"))
        self.assertEqual(LLL.m_liq, UnsignedDecimal("0"))
        self.assertEqual(LLR.m_liq, UnsignedDecimal("123"))
        self.assertEqual(LLLL.m_liq, UnsignedDecimal("0"))
        self.assertEqual(LLLR.m_liq, UnsignedDecimal("123"))
        self.assertEqual(LLRL.m_liq, UnsignedDecimal("0"))
        self.assertEqual(LLRR.m_liq, UnsignedDecimal("0"))

        # t_liq
        self.assertEqual(root.t_liq, UnsignedDecimal("0"))
        self.assertEqual(L.t_liq, UnsignedDecimal("0"))
        self.assertEqual(LL.t_liq, UnsignedDecimal("0"))
        self.assertEqual(LLL.t_liq, UnsignedDecimal("0"))
        self.assertEqual(LLR.t_liq, UnsignedDecimal("60"))
        self.assertEqual(LLLL.t_liq, UnsignedDecimal("0"))
        self.assertEqual(LLLR.t_liq, UnsignedDecimal("60"))
        self.assertEqual(LLRL.t_liq, UnsignedDecimal("0"))
        self.assertEqual(LLRR.t_liq, UnsignedDecimal("0"))

        # subtree_m_liq
        self.assertEqual(root.subtree_m_liq, UnsignedDecimal("369"))
        self.assertEqual(L.subtree_m_liq, UnsignedDecimal("369"))
        self.assertEqual(LL.subtree_m_liq, UnsignedDecimal("369"))
        self.assertEqual(LLL.subtree_m_liq, UnsignedDecimal("123"))
        self.assertEqual(LLR.subtree_m_liq, UnsignedDecimal("246"))
        self.assertEqual(LLLL.subtree_m_liq, UnsignedDecimal("0"))
        self.assertEqual(LLLR.subtree_m_liq, UnsignedDecimal("123"))
        self.assertEqual(LLRL.subtree_m_liq, UnsignedDecimal("0"))
        self.assertEqual(LLRR.subtree_m_liq, UnsignedDecimal("0"))

        # borrowed_x
        self.assertEqual(root.token_x_borrowed, UnsignedDecimal("0"))
        self.assertEqual(L.token_x_borrowed, UnsignedDecimal("0"))
        self.assertEqual(LL.token_x_borrowed, UnsignedDecimal("0"))
        self.assertEqual(LLL.token_x_borrowed, UnsignedDecimal("0"))
        self.assertEqual(LLR.token_x_borrowed, UnsignedDecimal("456e18"))
        self.assertEqual(LLLL.token_x_borrowed, UnsignedDecimal("0"))
        self.assertEqual(LLLR.token_x_borrowed, UnsignedDecimal("456e18"))
        self.assertEqual(LLRL.token_x_borrowed, UnsignedDecimal("0"))
        self.assertEqual(LLRR.token_x_borrowed, UnsignedDecimal("0"))

        # subtree_borrowed_x
        self.assertEqual(root.token_x_subtree_borrowed, UnsignedDecimal("912e18"))
        self.assertEqual(L.token_x_subtree_borrowed, UnsignedDecimal("912e18"))
        self.assertEqual(LL.token_x_subtree_borrowed, UnsignedDecimal("912e18"))
        self.assertEqual(LLL.token_x_subtree_borrowed, UnsignedDecimal("456e18"))
        self.assertEqual(LLR.token_x_subtree_borrowed, UnsignedDecimal("456e18"))
        self.assertEqual(LLLL.token_x_subtree_borrowed, UnsignedDecimal("0"))
        self.assertEqual(LLLR.token_x_subtree_borrowed, UnsignedDecimal("456e18"))
        self.assertEqual(LLRL.token_x_subtree_borrowed, UnsignedDecimal("0"))
        self.assertEqual(LLRR.token_x_subtree_borrowed, UnsignedDecimal("0"))

        # borrowed_y
        self.assertEqual(root.token_y_borrowed, UnsignedDecimal("0"))
        self.assertEqual(L.token_y_borrowed, UnsignedDecimal("0"))
        self.assertEqual(LL.token_y_borrowed, UnsignedDecimal("0"))
        self.assertEqual(LLL.token_y_borrowed, UnsignedDecimal("0"))
        self.assertEqual(LLR.token_y_borrowed, UnsignedDecimal("789e18"))
        self.assertEqual(LLLL.token_y_borrowed, UnsignedDecimal("0"))
        self.assertEqual(LLLR.token_y_borrowed, UnsignedDecimal("789e18"))
        self.assertEqual(LLRL.token_y_borrowed, UnsignedDecimal("0"))
        self.assertEqual(LLRR.token_y_borrowed, UnsignedDecimal("0"))

        # subtree_borrowed_y
        self.assertEqual(root.token_y_subtree_borrowed, UnsignedDecimal("1578e18"))
        self.assertEqual(L.token_y_subtree_borrowed, UnsignedDecimal("1578e18"))
        self.assertEqual(LL.token_y_subtree_borrowed, UnsignedDecimal("1578e18"))
        self.assertEqual(LLL.token_y_subtree_borrowed, UnsignedDecimal("789e18"))
        self.assertEqual(LLR.token_y_subtree_borrowed, UnsignedDecimal("789e18"))
        self.assertEqual(LLLL.token_y_subtree_borrowed, UnsignedDecimal("0"))
        self.assertEqual(LLLR.token_y_subtree_borrowed, UnsignedDecimal("789e18"))
        self.assertEqual(LLRL.token_y_subtree_borrowed, UnsignedDecimal("0"))
        self.assertEqual(LLRR.token_y_subtree_borrowed, UnsignedDecimal("0"))

        # token_x_cumulative_earned_per_m_liq
        self.assertEqual(root.token_x_cumulative_earned_per_m_liq, UnsignedDecimal("0"))
        self.assertEqual(L.token_x_cumulative_earned_per_m_liq, UnsignedDecimal("0"))
        self.assertEqual(LL.token_x_cumulative_earned_per_m_liq, UnsignedDecimal("0"))
        self.assertEqual(LLL.token_x_cumulative_earned_per_m_liq, UnsignedDecimal("0"))
        self.assertEqual(LLR.token_x_cumulative_earned_per_m_liq, UnsignedDecimal("0"))
        self.assertEqual(LLLL.token_x_cumulative_earned_per_m_liq, UnsignedDecimal("0"))
        self.assertEqual(LLLR.token_x_cumulative_earned_per_m_liq, UnsignedDecimal("0"))
        self.assertEqual(LLRL.token_x_cumulative_earned_per_m_liq, UnsignedDecimal("0"))
        self.assertEqual(LLRR.token_x_cumulative_earned_per_m_liq, UnsignedDecimal("0"))

        # token_x_cumulative_earned_per_m_subtree_liq
        self.assertEqual(root.token_x_cumulative_earned_per_m_subtree_liq, UnsignedDecimal("0"))
        self.assertEqual(L.token_x_cumulative_earned_per_m_subtree_liq, UnsignedDecimal("0"))
        self.assertEqual(LL.token_x_cumulative_earned_per_m_subtree_liq, UnsignedDecimal("0"))
        self.assertEqual(LLL.token_x_cumulative_earned_per_m_subtree_liq, UnsignedDecimal("0"))
        self.assertEqual(LLR.token_x_cumulative_earned_per_m_subtree_liq, UnsignedDecimal("0"))
        self.assertEqual(LLLL.token_x_cumulative_earned_per_m_subtree_liq, UnsignedDecimal("0"))
        self.assertEqual(LLLR.token_x_cumulative_earned_per_m_subtree_liq, UnsignedDecimal("0"))
        self.assertEqual(LLRL.token_x_cumulative_earned_per_m_subtree_liq, UnsignedDecimal("0"))
        self.assertEqual(LLRR.token_x_cumulative_earned_per_m_subtree_liq, UnsignedDecimal("0"))

        # token_y_cumulative_earned_per_m_liq
        self.assertEqual(root.token_y_cumulative_earned_per_m_liq, UnsignedDecimal("0"))
        self.assertEqual(L.token_y_cumulative_earned_per_m_liq, UnsignedDecimal("0"))
        self.assertEqual(LL.token_y_cumulative_earned_per_m_liq, UnsignedDecimal("0"))
        self.assertEqual(LLL.token_y_cumulative_earned_per_m_liq, UnsignedDecimal("0"))
        self.assertEqual(LLR.token_y_cumulative_earned_per_m_liq, UnsignedDecimal("0"))
        self.assertEqual(LLLL.token_y_cumulative_earned_per_m_liq, UnsignedDecimal("0"))
        self.assertEqual(LLLR.token_y_cumulative_earned_per_m_liq, UnsignedDecimal("0"))
        self.assertEqual(LLRL.token_y_cumulative_earned_per_m_liq, UnsignedDecimal("0"))
        self.assertEqual(LLRR.token_y_cumulative_earned_per_m_liq, UnsignedDecimal("0"))

        # token_y_cumulative_earned_per_m_subtree_liq
        self.assertEqual(root.token_y_cumulative_earned_per_m_subtree_liq, UnsignedDecimal("0"))
        self.assertEqual(L.token_y_cumulative_earned_per_m_subtree_liq, UnsignedDecimal("0"))
        self.assertEqual(LL.token_y_cumulative_earned_per_m_subtree_liq, UnsignedDecimal("0"))
        self.assertEqual(LLL.token_y_cumulative_earned_per_m_subtree_liq, UnsignedDecimal("0"))
        self.assertEqual(LLR.token_y_cumulative_earned_per_m_subtree_liq, UnsignedDecimal("0"))
        self.assertEqual(LLLL.token_y_cumulative_earned_per_m_subtree_liq, UnsignedDecimal("0"))
        self.assertEqual(LLLR.token_y_cumulative_earned_per_m_subtree_liq, UnsignedDecimal("0"))
        self.assertEqual(LLRL.token_y_cumulative_earned_per_m_subtree_liq, UnsignedDecimal("0"))
        self.assertEqual(LLRR.token_y_cumulative_earned_per_m_subtree_liq, UnsignedDecimal("0"))

    def test_adding_t_liq_right_leg_only(self):
        # range 8-10
        liq_tree: LiquidityTree = self.liq_tree

        root: LiqNode = liq_tree.nodes[liq_tree.root_key]
        R: LiqNode = liq_tree.nodes[(8 << 24) | 24]
        RL: LiqNode = liq_tree.nodes[(4 << 24) | 24]
        RLL: LiqNode = liq_tree.nodes[(2 << 24) | 24]
        RLR: LiqNode = liq_tree.nodes[(2 << 24) | 26]
        RLLL: LiqNode = liq_tree.nodes[(1 << 24) | 24]
        RLLR: LiqNode = liq_tree.nodes[(1 << 24) | 25]
        RLRL: LiqNode = liq_tree.nodes[(1 << 24) | 26]
        RLRR: LiqNode = liq_tree.nodes[(1 << 24) | 27]

        self.liq_tree.add_m_liq(LiqRange(low=8, high=10), UnsignedDecimal("100"))  # RLL, RLRL
        self.liq_tree.add_t_liq(LiqRange(low=8, high=10), UnsignedDecimal("80"), UnsignedDecimal("4e18"), UnsignedDecimal("10e18"))  # RLL, RLRL

        # m_liq
        self.assertEqual(root.m_liq, UnsignedDecimal("0"))
        self.assertEqual(R.m_liq, UnsignedDecimal("0"))
        self.assertEqual(RL.m_liq, UnsignedDecimal("0"))
        self.assertEqual(RLL.m_liq, UnsignedDecimal("100"))
        self.assertEqual(RLR.m_liq, UnsignedDecimal("0"))
        self.assertEqual(RLLL.m_liq, UnsignedDecimal("0"))
        self.assertEqual(RLLR.m_liq, UnsignedDecimal("0"))
        self.assertEqual(RLRL.m_liq, UnsignedDecimal("100"))
        self.assertEqual(RLRR.m_liq, UnsignedDecimal("0"))

        # t_liq
        self.assertEqual(root.t_liq, UnsignedDecimal("0"))
        self.assertEqual(R.t_liq, UnsignedDecimal("0"))
        self.assertEqual(RL.t_liq, UnsignedDecimal("0"))
        self.assertEqual(RLL.t_liq, UnsignedDecimal("80"))
        self.assertEqual(RLR.t_liq, UnsignedDecimal("0"))
        self.assertEqual(RLLL.t_liq, UnsignedDecimal("0"))
        self.assertEqual(RLLR.t_liq, UnsignedDecimal("0"))
        self.assertEqual(RLRL.t_liq, UnsignedDecimal("80"))
        self.assertEqual(RLRR.t_liq, UnsignedDecimal("0"))

        # subtree_m_liq
        self.assertEqual(root.subtree_m_liq, UnsignedDecimal("300"))
        self.assertEqual(R.subtree_m_liq, UnsignedDecimal("300"))
        self.assertEqual(RL.subtree_m_liq, UnsignedDecimal("300"))
        self.assertEqual(RLL.subtree_m_liq, UnsignedDecimal("200"))
        self.assertEqual(RLR.subtree_m_liq, UnsignedDecimal("100"))
        self.assertEqual(RLLL.subtree_m_liq, UnsignedDecimal("0"))
        self.assertEqual(RLLR.subtree_m_liq, UnsignedDecimal("0"))
        self.assertEqual(RLRL.subtree_m_liq, UnsignedDecimal("100"))
        self.assertEqual(RLRR.subtree_m_liq, UnsignedDecimal("0"))

        # borrowed_x
        self.assertEqual(root.token_x_borrowed, UnsignedDecimal("0"))
        self.assertEqual(R.token_x_borrowed, UnsignedDecimal("0"))
        self.assertEqual(RL.token_x_borrowed, UnsignedDecimal("0"))
        self.assertEqual(RLL.token_x_borrowed, UnsignedDecimal("4e18"))
        self.assertEqual(RLR.token_x_borrowed, UnsignedDecimal("0"))
        self.assertEqual(RLLL.token_x_borrowed, UnsignedDecimal("0"))
        self.assertEqual(RLLR.token_x_borrowed, UnsignedDecimal("0"))
        self.assertEqual(RLRL.token_x_borrowed, UnsignedDecimal("4e18"))
        self.assertEqual(RLRR.token_x_borrowed, UnsignedDecimal("0"))

        # subtree_borrowed_x
        self.assertEqual(root.token_x_subtree_borrowed, UnsignedDecimal("8e18"))
        self.assertEqual(R.token_x_subtree_borrowed, UnsignedDecimal("8e18"))
        self.assertEqual(RL.token_x_subtree_borrowed, UnsignedDecimal("8e18"))
        self.assertEqual(RLL.token_x_subtree_borrowed, UnsignedDecimal("4e18"))
        self.assertEqual(RLR.token_x_subtree_borrowed, UnsignedDecimal("4e18"))
        self.assertEqual(RLLL.token_x_subtree_borrowed, UnsignedDecimal("0"))
        self.assertEqual(RLLR.token_x_subtree_borrowed, UnsignedDecimal("0"))
        self.assertEqual(RLRL.token_x_subtree_borrowed, UnsignedDecimal("4e18"))
        self.assertEqual(RLRR.token_x_subtree_borrowed, UnsignedDecimal("0"))

        # borrowed_y
        self.assertEqual(root.token_y_borrowed, UnsignedDecimal("0"))
        self.assertEqual(R.token_y_borrowed, UnsignedDecimal("0"))
        self.assertEqual(RL.token_y_borrowed, UnsignedDecimal("0"))
        self.assertEqual(RLL.token_y_borrowed, UnsignedDecimal("10e18"))
        self.assertEqual(RLR.token_y_borrowed, UnsignedDecimal("0"))
        self.assertEqual(RLLL.token_y_borrowed, UnsignedDecimal("0"))
        self.assertEqual(RLLR.token_y_borrowed, UnsignedDecimal("0"))
        self.assertEqual(RLRL.token_y_borrowed, UnsignedDecimal("10e18"))
        self.assertEqual(RLRR.token_y_borrowed, UnsignedDecimal("0"))

        # subtree_borrowed_y
        self.assertEqual(root.token_y_subtree_borrowed, UnsignedDecimal("20e18"))
        self.assertEqual(R.token_y_subtree_borrowed, UnsignedDecimal("20e18"))
        self.assertEqual(RL.token_y_subtree_borrowed, UnsignedDecimal("20e18"))
        self.assertEqual(RLL.token_y_subtree_borrowed, UnsignedDecimal("10e18"))
        self.assertEqual(RLR.token_y_subtree_borrowed, UnsignedDecimal("10e18"))
        self.assertEqual(RLLL.token_y_subtree_borrowed, UnsignedDecimal("0"))
        self.assertEqual(RLLR.token_y_subtree_borrowed, UnsignedDecimal("0"))
        self.assertEqual(RLRL.token_y_subtree_borrowed, UnsignedDecimal("10e18"))
        self.assertEqual(RLRR.token_y_subtree_borrowed, UnsignedDecimal("0"))

        # token_x_cumulative_earned_per_m_liq
        self.assertEqual(root.token_x_cumulative_earned_per_m_liq, UnsignedDecimal("0"))
        self.assertEqual(R.token_x_cumulative_earned_per_m_liq, UnsignedDecimal("0"))
        self.assertEqual(RL.token_x_cumulative_earned_per_m_liq, UnsignedDecimal("0"))
        self.assertEqual(RLL.token_x_cumulative_earned_per_m_liq, UnsignedDecimal("0"))
        self.assertEqual(RLR.token_x_cumulative_earned_per_m_liq, UnsignedDecimal("0"))
        self.assertEqual(RLLL.token_x_cumulative_earned_per_m_liq, UnsignedDecimal("0"))
        self.assertEqual(RLLR.token_x_cumulative_earned_per_m_liq, UnsignedDecimal("0"))
        self.assertEqual(RLRL.token_x_cumulative_earned_per_m_liq, UnsignedDecimal("0"))
        self.assertEqual(RLRR.token_x_cumulative_earned_per_m_liq, UnsignedDecimal("0"))

        # token_x_cumulative_earned_per_m_subtree_liq
        self.assertEqual(root.token_x_cumulative_earned_per_m_subtree_liq, UnsignedDecimal("0"))
        self.assertEqual(R.token_x_cumulative_earned_per_m_subtree_liq, UnsignedDecimal("0"))
        self.assertEqual(RL.token_x_cumulative_earned_per_m_subtree_liq, UnsignedDecimal("0"))
        self.assertEqual(RLL.token_x_cumulative_earned_per_m_subtree_liq, UnsignedDecimal("0"))
        self.assertEqual(RLR.token_x_cumulative_earned_per_m_subtree_liq, UnsignedDecimal("0"))
        self.assertEqual(RLLL.token_x_cumulative_earned_per_m_subtree_liq, UnsignedDecimal("0"))
        self.assertEqual(RLLR.token_x_cumulative_earned_per_m_subtree_liq, UnsignedDecimal("0"))
        self.assertEqual(RLRL.token_x_cumulative_earned_per_m_subtree_liq, UnsignedDecimal("0"))
        self.assertEqual(RLRR.token_x_cumulative_earned_per_m_subtree_liq, UnsignedDecimal("0"))

        # token_y_cumulative_earned_per_m_liq
        self.assertEqual(root.token_y_cumulative_earned_per_m_liq, UnsignedDecimal("0"))
        self.assertEqual(R.token_y_cumulative_earned_per_m_liq, UnsignedDecimal("0"))
        self.assertEqual(RL.token_y_cumulative_earned_per_m_liq, UnsignedDecimal("0"))
        self.assertEqual(RLL.token_y_cumulative_earned_per_m_liq, UnsignedDecimal("0"))
        self.assertEqual(RLR.token_y_cumulative_earned_per_m_liq, UnsignedDecimal("0"))
        self.assertEqual(RLLL.token_y_cumulative_earned_per_m_liq, UnsignedDecimal("0"))
        self.assertEqual(RLLR.token_y_cumulative_earned_per_m_liq, UnsignedDecimal("0"))
        self.assertEqual(RLRL.token_y_cumulative_earned_per_m_liq, UnsignedDecimal("0"))
        self.assertEqual(RLRR.token_y_cumulative_earned_per_m_liq, UnsignedDecimal("0"))

        # token_y_cumulative_earned_per_m_subtree_liq
        self.assertEqual(root.token_y_cumulative_earned_per_m_subtree_liq, UnsignedDecimal("0"))
        self.assertEqual(R.token_y_cumulative_earned_per_m_subtree_liq, UnsignedDecimal("0"))
        self.assertEqual(RL.token_y_cumulative_earned_per_m_subtree_liq, UnsignedDecimal("0"))
        self.assertEqual(RLL.token_y_cumulative_earned_per_m_subtree_liq, UnsignedDecimal("0"))
        self.assertEqual(RLR.token_y_cumulative_earned_per_m_subtree_liq, UnsignedDecimal("0"))
        self.assertEqual(RLLL.token_y_cumulative_earned_per_m_subtree_liq, UnsignedDecimal("0"))
        self.assertEqual(RLLR.token_y_cumulative_earned_per_m_subtree_liq, UnsignedDecimal("0"))
        self.assertEqual(RLRL.token_y_cumulative_earned_per_m_subtree_liq, UnsignedDecimal("0"))
        self.assertEqual(RLRR.token_y_cumulative_earned_per_m_subtree_liq, UnsignedDecimal("0"))

    def test_adding_t_liq_left_and_right_leg_stopping_below_peak(self):
        pass

    def test_adding_t_liq_left_and_right_leg_at_or_higher_than_peak(self):
        pass

    def test_adding_t_liq_left_and_right_leg_same_distance_to_stop(self):
        pass

    def test_adding_t_liq_left_leg_lower_than_right_leg(self):
        pass

    def test_adding_t_liq_right_leg_lower_than_left_leg(self):
        pass

    # Fees
    def test_fee_accumulation_adding_m_liq_for_root(self):
        pass

    def test_fee_accumulation_removing_m_liq_for_root(self):
        pass

    def test_fee_accumulation_adding_t_liq_for_root(self):
        pass

    def test_fee_accumulation_removing_t_liq_for_root(self):
        pass

    def test_fee_accumulation_adding_m_liq_for_node_leaf(self):
        pass

    def test_fee_accumulation_adding_t_liq_for_node_leaf(self):
        pass

    def test_fee_accumulation_removing_m_liq_for_node_leaf(self):
        pass

    def test_fee_accumulation_removing_t_liq_for_node_leaf(self):
        pass

    def test_fee_accumulation_adding_m_liq_for_node_along_left_path(self):
        pass

    def test_fee_accumulation_removing_m_liq_for_node_along_left_path(self):
        pass

    def test_fee_accumulation_adding_t_liq_for_node_along_left_path(self):
        pass

    def test_fee_accumulation_removing_t_liq_for_node_along_left_path(self):
        pass

    def test_fee_accumulation_adding_m_liq_for_node_along_right_path(self):
        pass

    def test_fee_accumulation_removing_m_liq_for_node_along_right_path(self):
        pass

    def test_fee_accumulation_adding_t_liq_for_node_along_right_path(self):
        pass

    def test_fee_accumulation_removing_t_liq_for_node_along_right_path(self):
        pass

    def test_fee_accumulation_adding_m_liq_when_flipping_node_from_left_to_right_child(self):
        pass

    def test_fee_accumulation_removing_m_liq_when_flipping_node_from_left_to_right_child(self):
        pass

    def test_fee_accumulation_adding_t_liq_when_flipping_node_from_left_to_right_child(self):
        pass

    def test_fee_accumulation_removing_t_liq_when_flipping_node_from_left_to_right_child(self):
        pass

    def test_fee_accumulation_adding_m_liq_when_flipping_node_from_right_to_left_child(self):
        pass

    def test_fee_accumulation_removing_m_liq_when_flipping_node_from_right_to_left_child(self):
        pass

    def test_fee_accumulation_adding_t_liq_when_flipping_node_from_right_to_left_child(self):
        pass

    def test_fee_accumulation_removing_t_liq_when_flipping_node_from_right_to_left_child(self):
        pass

    # region Errors

    def test_revert_removing_m_without_sufficient_m_liq(self):
        self.assertRaises(UnsignedDecimalIsSignedException, lambda: self.liq_tree.remove_m_liq(LiqRange(3, 7), UnsignedDecimal("11")))

    def test_revert_removing_t_liq_without_sufficient_t_liq(self):
        self.liq_tree.add_m_liq(LiqRange(3, 7), UnsignedDecimal("10"))
        self.liq_tree.add_t_liq(LiqRange(3, 7), UnsignedDecimal("10"), UnsignedDecimal("2"), UnsignedDecimal("2"))
        self.assertRaises(UnsignedDecimalIsSignedException, lambda: self.liq_tree.remove_t_liq(LiqRange(3, 7), UnsignedDecimal("11"), UnsignedDecimal("2"), UnsignedDecimal("2")))

    def test_revert_removing_t_liq_without_sufficient_x_borrow(self):
        self.liq_tree.add_m_liq(LiqRange(3, 7), UnsignedDecimal("10"))
        self.liq_tree.add_t_liq(LiqRange(3, 7), UnsignedDecimal("10"), UnsignedDecimal("2"), UnsignedDecimal("2"))
        self.assertRaises(UnsignedDecimalIsSignedException, lambda: self.liq_tree.remove_t_liq(LiqRange(3, 7), UnsignedDecimal("1"), UnsignedDecimal("11"), UnsignedDecimal("1")))

    def test_revert_removing_t_liq_without_sufficient_y_borrow(self):
        self.liq_tree.add_m_liq(LiqRange(3, 7), UnsignedDecimal("10"))
        self.liq_tree.add_t_liq(LiqRange(3, 7), UnsignedDecimal("10"), UnsignedDecimal("2"), UnsignedDecimal("2"))
        self.assertRaises(UnsignedDecimalIsSignedException, lambda: self.liq_tree.remove_t_liq(LiqRange(3, 7), UnsignedDecimal("1"), UnsignedDecimal("1"), UnsignedDecimal("12")))

    def test_revert_adding_t_liq_without_sufficient_m_liq(self):
        self.assertRaises(LiquidityExceptionTLiqExceedsMLiq, lambda: self.liq_tree.add_t_liq(LiqRange(3, 6), UnsignedDecimal("1"), UnsignedDecimal("1"), UnsignedDecimal("1")))

    def test_revert_removing_m_liq_before_adding_m_liq(self):
        self.assertRaises(UnsignedDecimalIsSignedException, lambda: self.liq_tree.remove_m_liq(LiqRange(3, 6), UnsignedDecimal("1")))

    def test_revert_removing_t_liq_before_adding_m_liq(self):
        self.assertRaises(UnsignedDecimalIsSignedException, lambda: self.liq_tree.remove_t_liq(LiqRange(3, 6), UnsignedDecimal("1"), UnsignedDecimal("1"), UnsignedDecimal("1")))

    # region Range High Below Low

    def test_revert_adding_m_liq_on_range_with_high_below_low(self):
        self.assertRaises(LiquidityExceptionRangeHighBelowLow, lambda: self.liq_tree.add_m_liq(LiqRange(3, 2), UnsignedDecimal("2")))

    def test_revert_removing_m_liq_on_range_with_high_below_low(self):
        self.assertRaises(LiquidityExceptionRangeHighBelowLow, lambda: self.liq_tree.remove_m_liq(LiqRange(3, 2), UnsignedDecimal("2")))

    def test_revert_adding_t_liq_on_range_with_high_below_low(self):
        self.assertRaises(LiquidityExceptionRangeHighBelowLow, lambda: self.liq_tree.add_t_liq(LiqRange(3, 2), UnsignedDecimal("2"), UnsignedDecimal("2"), UnsignedDecimal("2")))

    def test_revert_removing_t_liq_on_range_with_high_below_low(self):
        self.assertRaises(LiquidityExceptionRangeHighBelowLow, lambda: self.liq_tree.remove_t_liq(LiqRange(3, 2), UnsignedDecimal("2"), UnsignedDecimal("2"), UnsignedDecimal("2")))

    # endregion

    # region Oversized Range

    def test_revert_adding_m_liq_on_oversized_range(self):
        self.assertRaises(LiquidityExceptionOversizedRange, lambda: self.liq_tree.add_m_liq(LiqRange(0, 20), UnsignedDecimal("2")))

    def test_revert_removing_m_liq_on_oversized_range(self):
        self.assertRaises(LiquidityExceptionOversizedRange, lambda: self.liq_tree.remove_m_liq(LiqRange(0, 20), UnsignedDecimal("2")))

    def test_revert_adding_t_liq_on_oversized_range(self):
        self.assertRaises(LiquidityExceptionOversizedRange, lambda: self.liq_tree.add_t_liq(LiqRange(0, 20), UnsignedDecimal("2"), UnsignedDecimal("2"), UnsignedDecimal("2")))

    def test_revert_removing_t_liq_on_oversized_range(self):
        self.assertRaises(LiquidityExceptionOversizedRange, lambda: self.liq_tree.remove_t_liq(LiqRange(0, 20), UnsignedDecimal("2"), UnsignedDecimal("2"), UnsignedDecimal("2")))

    # endregion

    # region Root Range

    def test_revert_adding_m_liq_on_root_range(self):
        self.assertRaises(LiquidityExceptionRootRange, lambda: self.liq_tree.add_m_liq(LiqRange(0, 15), UnsignedDecimal("2")))

    def test_revert_removing_m_liq_on_root_range(self):
        self.assertRaises(LiquidityExceptionRootRange, lambda: self.liq_tree.remove_m_liq(LiqRange(0, 15), UnsignedDecimal("2")))

    def test_revert_adding_t_liq_on_root_range(self):
        self.assertRaises(LiquidityExceptionRootRange, lambda: self.liq_tree.add_t_liq(LiqRange(0, 15), UnsignedDecimal("2"), UnsignedDecimal("2"), UnsignedDecimal("2")))

    def test_revert_removing_t_liq_on_root_range(self):
        self.assertRaises(LiquidityExceptionRootRange, lambda: self.liq_tree.remove_t_liq(LiqRange(0, 15), UnsignedDecimal("2"), UnsignedDecimal("2"), UnsignedDecimal("2")))

    # endregion

    # region Negative Range Value

    def test_revert_adding_m_liq_on_range_with_negative_low_value(self):
        self.assertRaises(LiquidityExceptionRangeContainsNegative, lambda: self.liq_tree.add_m_liq(LiqRange(-3, 7), UnsignedDecimal("2")))

    def test_revert_removing_m_liq_on_range_with_negative_low_value(self):
        self.liq_tree.add_m_liq(LiqRange(3, 7), UnsignedDecimal("10"))
        self.assertRaises(LiquidityExceptionRangeContainsNegative, lambda: self.liq_tree.remove_m_liq(LiqRange(-3, 7), UnsignedDecimal("2")))

    def test_revert_adding_t_liq_on_range_with_negative_low_value(self):
        self.liq_tree.add_m_liq(LiqRange(3, 7), UnsignedDecimal("10"))
        self.assertRaises(LiquidityExceptionRangeContainsNegative, lambda: self.liq_tree.add_t_liq(LiqRange(-3, 7), UnsignedDecimal("2"), UnsignedDecimal("2"), UnsignedDecimal("2")))

    def test_revert_removing_t_liq_on_range_with_negative_low_value(self):
        self.liq_tree.add_m_liq(LiqRange(3, 7), UnsignedDecimal("10"))
        self.liq_tree.add_t_liq(LiqRange(3, 7), UnsignedDecimal("10"), UnsignedDecimal("2"), UnsignedDecimal("2"))
        self.assertRaises(LiquidityExceptionRangeContainsNegative, lambda: self.liq_tree.remove_t_liq(LiqRange(-3, 7), UnsignedDecimal("2"), UnsignedDecimal("2"), UnsignedDecimal("2")))

    def test_revert_adding_m_liq_on_range_with_negative_high_value(self):
        self.assertRaises(LiquidityExceptionRangeContainsNegative, lambda: self.liq_tree.add_m_liq(LiqRange(3, -7), UnsignedDecimal("2")))

    def test_revert_removing_m_liq_on_range_with_negative_high_value(self):
        self.liq_tree.add_m_liq(LiqRange(3, 7), UnsignedDecimal("10"))
        self.assertRaises(LiquidityExceptionRangeContainsNegative, lambda: self.liq_tree.remove_m_liq(LiqRange(3, -7), UnsignedDecimal("2")))

    def test_revert_adding_t_liq_on_range_with_negative_high_value(self):
        self.liq_tree.add_m_liq(LiqRange(3, 7), UnsignedDecimal("10"))
        self.assertRaises(LiquidityExceptionRangeContainsNegative, lambda: self.liq_tree.add_t_liq(LiqRange(3, -7), UnsignedDecimal("2"), UnsignedDecimal("2"), UnsignedDecimal("2")))

    def test_revert_removing_t_liq_on_range_with_negative_high_value(self):
        self.liq_tree.add_m_liq(LiqRange(3, 7), UnsignedDecimal("10"))
        self.liq_tree.add_t_liq(LiqRange(3, 7), UnsignedDecimal("10"), UnsignedDecimal("2"), UnsignedDecimal("2"))
        self.assertRaises(LiquidityExceptionRangeContainsNegative, lambda: self.liq_tree.remove_t_liq(LiqRange(3, -7), UnsignedDecimal("2"), UnsignedDecimal("2"), UnsignedDecimal("2")))

    # endregion

    # region Zero Liquidity

    def test_revert_adding_m_liq_with_zero_liq(self):
        self.assertRaises(LiquidityExceptionZeroLiquidity, lambda: self.liq_tree.add_m_liq(LiqRange(3, 7), UnsignedDecimal("0")))

    def test_revert_removing_m_liq_with_zero_liq(self):
        self.liq_tree.add_m_liq(LiqRange(3, 7), UnsignedDecimal("10"))
        self.assertRaises(LiquidityExceptionZeroLiquidity, lambda: self.liq_tree.remove_m_liq(LiqRange(3, 7), UnsignedDecimal("0")))

    def test_revert_adding_t_liq_with_zero_liq(self):
        self.liq_tree.add_m_liq(LiqRange(3, 7), UnsignedDecimal("100"))
        self.assertRaises(LiquidityExceptionZeroLiquidity, lambda: self.liq_tree.add_t_liq(LiqRange(3, 7), UnsignedDecimal("0"), UnsignedDecimal("3"), UnsignedDecimal("2")))

    def test_revert_removing_t_liq_with_zero_liq(self):
        self.liq_tree.add_m_liq(LiqRange(3, 7), UnsignedDecimal("100"))
        self.liq_tree.add_t_liq(LiqRange(3, 7), UnsignedDecimal("100"), UnsignedDecimal("100"), UnsignedDecimal("100"))
        self.assertRaises(LiquidityExceptionZeroLiquidity, lambda: self.liq_tree.remove_t_liq(LiqRange(3, 7), UnsignedDecimal("0"), UnsignedDecimal("3"), UnsignedDecimal("2")))

    # endregion

    # region Negative Liq

    def test_revert_adding_m_liq_with_negative_liq(self):
        self.assertRaises(UnsignedDecimalIsSignedException, lambda: self.liq_tree.add_m_liq(LiqRange(3, 7), UnsignedDecimal("-10")))

    def test_revert_adding_t_liq_with_negative_liq(self):
        self.liq_tree.add_m_liq(LiqRange(3, 7), UnsignedDecimal("10"))
        self.assertRaises(UnsignedDecimalIsSignedException, lambda: self.liq_tree.remove_m_liq(LiqRange(3, 7), UnsignedDecimal("-7")))

    def test_revert_adding_t_liq_with_negative_x_borrow(self):
        self.liq_tree.add_m_liq(LiqRange(3, 7), UnsignedDecimal("100"))
        self.assertRaises(UnsignedDecimalIsSignedException, lambda: self.liq_tree.add_t_liq(LiqRange(3, 7), UnsignedDecimal("-93"), UnsignedDecimal("3"), UnsignedDecimal("2")))

    def test_revert_adding_t_liq_with_negative_y_borrow(self):
        self.liq_tree.add_m_liq(LiqRange(3, 7), UnsignedDecimal("100"))
        self.liq_tree.add_t_liq(LiqRange(3, 7), UnsignedDecimal("100"), UnsignedDecimal("100"), UnsignedDecimal("100"))
        self.assertRaises(UnsignedDecimalIsSignedException, lambda: self.liq_tree.remove_t_liq(LiqRange(3, 7), UnsignedDecimal("-30"), UnsignedDecimal("3"), UnsignedDecimal("2")))

    # endregion

    # endregion

'''
