from unittest import TestCase
from LiqTree.UnsignedDecimal import UnsignedDecimal, UnsignedDecimalIsSignedException

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

from LiqTree.LiquidityTree import *


class TestLiquidityTree(TestCase):
    def setUp(self) -> None:
        self.liq_tree = LiquidityTree(depth=4, sol_truncation=True)

    # m_liq
    def test_adding_m_liq_root_only(self):
        pass

    def test_adding_m_liq_left_leg_only(self):
        pass

    def test_adding_m_liq_right_leg_only(self):
        pass

    def test_adding_m_liq_left_and_right_leg_stopping_below_peak(self):
        pass

    def test_adding_m_liq_left_and_right_leg_at_or_higher_than_peak(self):
        pass

    def test_adding_m_liq_left_and_right_leg_same_distance_to_stop(self):
        pass

    def test_adding_m_liq_left_leg_lower_than_right_leg(self):
        pass

    def test_adding_m_liq_right_leg_lower_than_left_leg(self):
        pass

    # t_liq
    def test_adding_t_liq_root_only(self):
        pass

    def test_adding_t_liq_left_leg_only(self):
        pass

    def test_adding_t_liq_right_leg_only(self):
        pass

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
        self.assertRaises(LiqTreeExceptionTLiqExceedsMLiq, lambda: self.liq_tree.add_t_liq(LiqRange(3, 6), UnsignedDecimal("1"), UnsignedDecimal("1"), UnsignedDecimal("1")))

    def test_revert_removing_m_liq_before_adding_m_liq(self):
        self.assertRaises(UnsignedDecimalIsSignedException, lambda: self.liq_tree.remove_m_liq(LiqRange(3, 6), UnsignedDecimal("1")))

    def test_revert_removing_t_liq_before_adding_m_liq(self):
        self.assertRaises(UnsignedDecimalIsSignedException, lambda: self.liq_tree.remove_t_liq(LiqRange(3, 6), UnsignedDecimal("1"), UnsignedDecimal("1"), UnsignedDecimal("1")))

    # region Range High Below Low

    def test_revert_adding_m_liq_on_range_with_high_below_low(self):
        self.assertRaises(LiqTreeExceptionRangeHighBelowLow, lambda: self.liq_tree.add_m_liq(LiqRange(3, 2), UnsignedDecimal("2")))

    def test_revert_removing_m_liq_on_range_with_high_below_low(self):
        self.assertRaises(LiqTreeExceptionRangeHighBelowLow, lambda: self.liq_tree.remove_m_liq(LiqRange(3, 2), UnsignedDecimal("2")))

    def test_revert_adding_t_liq_on_range_with_high_below_low(self):
        self.assertRaises(LiqTreeExceptionRangeHighBelowLow, lambda: self.liq_tree.add_t_liq(LiqRange(3, 2), UnsignedDecimal("2"), UnsignedDecimal("2"), UnsignedDecimal("2")))

    def test_revert_removing_t_liq_on_range_with_high_below_low(self):
        self.assertRaises(LiqTreeExceptionRangeHighBelowLow, lambda: self.liq_tree.remove_t_liq(LiqRange(3, 2), UnsignedDecimal("2"), UnsignedDecimal("2"), UnsignedDecimal("2")))

    # endregion

    # region Oversized Range

    def test_revert_adding_m_liq_on_oversized_range(self):
        self.assertRaises(LiqTreeExceptionOversizedRange, lambda: self.liq_tree.add_m_liq(LiqRange(0, 20), UnsignedDecimal("2")))

    def test_revert_removing_m_liq_on_oversized_range(self):
        self.assertRaises(LiqTreeExceptionOversizedRange, lambda: self.liq_tree.remove_m_liq(LiqRange(0, 20), UnsignedDecimal("2")))

    def test_revert_adding_t_liq_on_oversized_range(self):
        self.assertRaises(LiqTreeExceptionOversizedRange, lambda: self.liq_tree.add_t_liq(LiqRange(0, 20), UnsignedDecimal("2"), UnsignedDecimal("2"), UnsignedDecimal("2")))

    def test_revert_removing_t_liq_on_oversized_range(self):
        self.assertRaises(LiqTreeExceptionOversizedRange, lambda: self.liq_tree.remove_t_liq(LiqRange(0, 20), UnsignedDecimal("2"), UnsignedDecimal("2"), UnsignedDecimal("2")))

    # endregion

    # region Root Range

    def test_revert_adding_m_liq_on_root_range(self):
        self.assertRaises(LiqTreeExceptionRootRange, lambda: self.liq_tree.add_m_liq(LiqRange(0, 15), UnsignedDecimal("2")))

    def test_revert_removing_m_liq_on_root_range(self):
        self.assertRaises(LiqTreeExceptionRootRange, lambda: self.liq_tree.remove_m_liq(LiqRange(0, 15), UnsignedDecimal("2")))

    def test_revert_adding_t_liq_on_root_range(self):
        self.assertRaises(LiqTreeExceptionRootRange, lambda: self.liq_tree.add_t_liq(LiqRange(0, 15), UnsignedDecimal("2"), UnsignedDecimal("2"), UnsignedDecimal("2")))

    def test_revert_removing_t_liq_on_root_range(self):
        self.assertRaises(LiqTreeExceptionRootRange, lambda: self.liq_tree.remove_t_liq(LiqRange(0, 15), UnsignedDecimal("2"), UnsignedDecimal("2"), UnsignedDecimal("2")))

    # endregion

    # region Negative Range Value

    def test_revert_adding_m_liq_on_range_with_negative_low_value(self):
        self.assertRaises(LiqTreeExceptionRangeContainsNegative, lambda: self.liq_tree.add_m_liq(LiqRange(-3, 7), UnsignedDecimal("2")))

    def test_revert_removing_m_liq_on_range_with_negative_low_value(self):
        self.liq_tree.add_m_liq(LiqRange(3, 7), UnsignedDecimal("10"))
        self.assertRaises(LiqTreeExceptionRangeContainsNegative, lambda: self.liq_tree.remove_m_liq(LiqRange(-3, 7), UnsignedDecimal("2")))

    def test_revert_adding_t_liq_on_range_with_negative_low_value(self):
        self.liq_tree.add_m_liq(LiqRange(3, 7), UnsignedDecimal("10"))
        self.assertRaises(LiqTreeExceptionRangeContainsNegative, lambda: self.liq_tree.add_t_liq(LiqRange(-3, 7), UnsignedDecimal("2"), UnsignedDecimal("2"), UnsignedDecimal("2")))

    def test_revert_removing_t_liq_on_range_with_negative_low_value(self):
        self.liq_tree.add_m_liq(LiqRange(3, 7), UnsignedDecimal("10"))
        self.liq_tree.add_t_liq(LiqRange(3, 7), UnsignedDecimal("10"), UnsignedDecimal("2"), UnsignedDecimal("2"))
        self.assertRaises(LiqTreeExceptionRangeContainsNegative, lambda: self.liq_tree.remove_t_liq(LiqRange(-3, 7), UnsignedDecimal("2"), UnsignedDecimal("2"), UnsignedDecimal("2")))

    def test_revert_adding_m_liq_on_range_with_negative_high_value(self):
        self.assertRaises(LiqTreeExceptionRangeContainsNegative, lambda: self.liq_tree.add_m_liq(LiqRange(3, -7), UnsignedDecimal("2")))

    def test_revert_removing_m_liq_on_range_with_negative_high_value(self):
        self.liq_tree.add_m_liq(LiqRange(3, 7), UnsignedDecimal("10"))
        self.assertRaises(LiqTreeExceptionRangeContainsNegative, lambda: self.liq_tree.remove_m_liq(LiqRange(3, -7), UnsignedDecimal("2")))

    def test_revert_adding_t_liq_on_range_with_negative_high_value(self):
        self.liq_tree.add_m_liq(LiqRange(3, 7), UnsignedDecimal("10"))
        self.assertRaises(LiqTreeExceptionRangeContainsNegative, lambda: self.liq_tree.add_t_liq(LiqRange(3, -7), UnsignedDecimal("2"), UnsignedDecimal("2"), UnsignedDecimal("2")))

    def test_revert_removing_t_liq_on_range_with_negative_high_value(self):
        self.liq_tree.add_m_liq(LiqRange(3, 7), UnsignedDecimal("10"))
        self.liq_tree.add_t_liq(LiqRange(3, 7), UnsignedDecimal("10"), UnsignedDecimal("2"), UnsignedDecimal("2"))
        self.assertRaises(LiqTreeExceptionRangeContainsNegative, lambda: self.liq_tree.remove_t_liq(LiqRange(3, -7), UnsignedDecimal("2"), UnsignedDecimal("2"), UnsignedDecimal("2")))

    # endregion

    # region Zero Liquidity

    def test_revert_adding_m_liq_with_zero_liq(self):
        self.assertRaises(LiqTreeExceptionZeroLiquidity, lambda: self.liq_tree.add_m_liq(LiqRange(3, 7), UnsignedDecimal("0")))

    def test_revert_removing_m_liq_with_zero_liq(self):
        self.liq_tree.add_m_liq(LiqRange(3, 7), UnsignedDecimal("10"))
        self.assertRaises(LiqTreeExceptionZeroLiquidity, lambda: self.liq_tree.remove_m_liq(LiqRange(3, 7), UnsignedDecimal("0")))

    def test_revert_adding_t_liq_with_zero_liq(self):
        self.liq_tree.add_m_liq(LiqRange(3, 7), UnsignedDecimal("100"))
        self.assertRaises(LiqTreeExceptionZeroLiquidity, lambda: self.liq_tree.add_t_liq(LiqRange(3, 7), UnsignedDecimal("0"), UnsignedDecimal("3"), UnsignedDecimal("2")))

    def test_revert_removing_t_liq_with_zero_liq(self):
        self.liq_tree.add_m_liq(LiqRange(3, 7), UnsignedDecimal("100"))
        self.liq_tree.add_t_liq(LiqRange(3, 7), UnsignedDecimal("100"), UnsignedDecimal("100"), UnsignedDecimal("100"))
        self.assertRaises(LiqTreeExceptionZeroLiquidity, lambda: self.liq_tree.remove_t_liq(LiqRange(3, 7), UnsignedDecimal("0"), UnsignedDecimal("3"), UnsignedDecimal("2")))

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