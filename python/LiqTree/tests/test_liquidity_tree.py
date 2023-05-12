from unittest import TestCase
from decimal import Decimal

# NOTE: all numbers must be given as Decimal numbers to avoid precision errors.
#       each Decimal number must be created using a string! Otherwise precision is lost when the input variable is created
#       For instance, 7927848e16 yields 79278479999999997378560 as an integer. While the type 7.927848e+22 looks ok, when passed to
#       Decimal(7.927848e+22) is still equates to Decimal('79278479999999997378560').
#       However, Decimal("7927848e16") is correct. Converting to an int yields 79278480000000000000000
#
#       When asserting values are equal, the calculated decimal is truncated to its int representation
#       as the compared value in solidity would lose that extra precision.
#
#       If all goes perfectly, the final result in python would 100% match the final output in solidity

from LiqTree.LiquidityTree import LiquidityTree, LiqNode, LiqRange


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

    # Errors

    def test_revert_removing_m_liq_that_does_not_exist(self):
        pass

    def test_revert_removing_t_liq_that_does_not_exist(self):
        pass

    def test_revert_adding_t_liq_without_sufficient_m_liq(self):
        pass

    def test_revert_removing_m_liq_before_adding_m_liq(self):
        pass

    def test_revert_removing_t_liq_before_adding_m_liq(self):
        pass

    def test_revert_on_range_with_high_below_low(self):
        pass

    def test_revert_on_oversized_range(self):
        pass

    def test_revert_on_range_with_negative_value(self):
        pass

    def test_revert_adding_m_liq_with_zero_liq(self):
        pass

    def test_revert_adding_t_liq_with_zero_liq(self):
        pass

    def test_revert_adding_m_liq_with_negative_liq(self):
        pass

    def test_revert_adding_t_liq_with_negative_liq(self):
        pass

    def test_revert_adding_t_liq_with_negative_x_borrow(self):
        pass

    def test_revert_adding_t_liq_with_negative_y_borrow(self):
        pass

