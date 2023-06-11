from FloatingPoint.FloatingPointTestCase import FloatingPointTestCase

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


# NOTE: Refer to LiqTree/test/TreeFees.t.sol for mathematical proofs
class TestTreeFees(FloatingPointTestCase):
    def setUp(self) -> None:
        self._tree = LiquidityTree(depth=4, sol_truncation=True)

    # region Borrow

    def test_borrow_at_root_node(self):
        self._tree.add_wide_m_liq(UnsignedDecimal("900"))
        self._tree.add_wide_t_liq(UnsignedDecimal("200"), UnsignedDecimal("57e18"), UnsignedDecimal("290e6"))
        self._tree.remove_wide_t_liq(UnsignedDecimal("50"), UnsignedDecimal("10e18"), UnsignedDecimal("1e6"))

        root: LiqNode = self._tree.nodes[self._tree.root_key]
        self.assertEqual(root.token_x_borrow, UnsignedDecimal("47e18"))
        self.assertEqual(root.token_y_borrow, UnsignedDecimal("289e6"))

        # other borrows should be empty

    def test_borrow_at_single_node(self):
        self._tree.add_m_liq(LiqRange(0, 3), UnsignedDecimal("500"))
        self._tree.add_t_liq(LiqRange(0, 3), UnsignedDecimal("400"), UnsignedDecimal("43e18"), UnsignedDecimal("12e6"))
        self._tree.remove_t_liq(LiqRange(0, 3), UnsignedDecimal("20"), UnsignedDecimal("20e18"), UnsignedDecimal("10e6"))

        zero_three: LiqNode = self._tree.nodes[4 << 24 | 16]
        self.assertEqual(zero_three.token_x_borrow, UnsignedDecimal("23e18"))
        self.assertEqual(zero_three.token_y_borrow, UnsignedDecimal("2e6"))

    def test_borrow_at_leaf_node(self):
        self._tree.add_m_liq(LiqRange(3, 3), UnsignedDecimal("100"))
        self._tree.add_t_liq(LiqRange(3, 3), UnsignedDecimal("20"), UnsignedDecimal("22e18"), UnsignedDecimal("29e6"))
        self._tree.remove_t_liq(LiqRange(3, 3), UnsignedDecimal("20"), UnsignedDecimal("20e18"), UnsignedDecimal("20e6"))

        three_three: LiqNode = self._tree.nodes[1 << 24 | 19]
        self.assertEqual(three_three.token_x_borrow, UnsignedDecimal("2e18"))
        self.assertEqual(three_three.token_y_borrow, UnsignedDecimal("9e6"))

    def test_borrow_split_across_several_nodes_walking_left_leg(self):
        self._tree.add_m_liq(LiqRange(1, 7), UnsignedDecimal("100"))
        self._tree.add_t_liq(LiqRange(1, 7), UnsignedDecimal("20"), UnsignedDecimal("12e18"), UnsignedDecimal("19e6"))
        self._tree.remove_t_liq(LiqRange(1, 7), UnsignedDecimal("20"), UnsignedDecimal("10e18"), UnsignedDecimal("10e6"))

        one_one: LiqNode = self._tree.nodes[1 << 24 | 17]
        self.assertEqual(int(one_one.token_x_borrow), UnsignedDecimal("285714285714285714"))
        self.assertEqual(int(one_one.token_y_borrow), UnsignedDecimal("1285714"))

        two_three: LiqNode = self._tree.nodes[2 << 24 | 18]
        self.assertEqual(int(two_three.token_x_borrow), UnsignedDecimal("571428571428571428"))
        self.assertEqual(int(two_three.token_y_borrow), UnsignedDecimal("2571428"))

        four_seven: LiqNode = self._tree.nodes[4 << 24 | 20]
        self.assertEqual(int(four_seven.token_x_borrow), UnsignedDecimal("1142857142857142857"))  # 1 wei lost
        self.assertEqual(int(four_seven.token_y_borrow), UnsignedDecimal("5142857"))  # 1 wei lost

        # other borrows should be empty

    def test_borrow_split_across_several_nodes_walking_both_legs_below_peak(self):
        self._tree.add_m_liq(LiqRange(1, 2), UnsignedDecimal("100"))
        self._tree.add_t_liq(LiqRange(1, 2), UnsignedDecimal("20"), UnsignedDecimal("74e18"), UnsignedDecimal("21e6"))
        self._tree.remove_t_liq(LiqRange(1, 2), UnsignedDecimal("20"), UnsignedDecimal("2e18"), UnsignedDecimal("2e6"))

        one_one: LiqNode = self._tree.nodes[1 << 24 | 17]
        self.assertEqual(one_one.token_x_borrow, UnsignedDecimal("36000000000000000000"))
        self.assertEqual(one_one.token_y_borrow, UnsignedDecimal("9500000"))

        two_two: LiqNode = self._tree.nodes[1 << 24 | 18]
        self.assertEqual(two_two.token_x_borrow, UnsignedDecimal("36000000000000000000"))
        self.assertEqual(two_two.token_y_borrow, UnsignedDecimal("9500000"))

    def test_borrow_split_across_sever_nodes_walking_right_leg(self):
        self._tree.add_m_liq(LiqRange(8, 14), UnsignedDecimal("100"))
        self._tree.add_t_liq(LiqRange(8, 14), UnsignedDecimal("20"), UnsignedDecimal("474e18"), UnsignedDecimal("220e6"))
        self._tree.remove_t_liq(LiqRange(8, 14), UnsignedDecimal("20"), UnsignedDecimal("2e18"), UnsignedDecimal("1e6"))

        eight_eleven: LiqNode = self._tree.nodes[4 << 24 | 24]
        self.assertEqual(int(eight_eleven.token_x_borrow), UnsignedDecimal("269714285714285714285"))  # 1 wei lost
        self.assertEqual(int(eight_eleven.token_y_borrow), UnsignedDecimal("125142857"))  # 1 wei lost

        twelve_thirteen: LiqNode = self._tree.nodes[2 << 24 | 28]
        self.assertEqual(int(twelve_thirteen.token_x_borrow), UnsignedDecimal("134857142857142857142"))
        self.assertEqual(int(twelve_thirteen.token_y_borrow), UnsignedDecimal("62571428"))

        fourteen_fourteen: LiqNode = self._tree.nodes[1 << 24 | 30]
        self.assertEqual(int(fourteen_fourteen.token_x_borrow), UnsignedDecimal("67428571428571428571"))
        self.assertEqual(int(fourteen_fourteen.token_y_borrow), UnsignedDecimal("31285714"))

    def test_borrow_split_across_several_nodes_walking_both_legs_at_or_above_peak(self):
        self._tree.add_m_liq(LiqRange(8, 15), UnsignedDecimal("100"))
        self._tree.add_t_liq(LiqRange(8, 15), UnsignedDecimal("20"), UnsignedDecimal("1473e18"), UnsignedDecimal("5220e6"))
        self._tree.remove_t_liq(LiqRange(8, 15), UnsignedDecimal("20"), UnsignedDecimal("1e18"), UnsignedDecimal("1e6"))

        eight_fifteen: LiqNode = self._tree.nodes[8 << 24 | 24]
        self.assertEqual(int(eight_fifteen.token_x_borrow), UnsignedDecimal("1472e18"))
        self.assertEqual(int(eight_fifteen.token_y_borrow), UnsignedDecimal("5219e6"))

        # almost all other borrows should be empty

    # endregion

    # region Subtree Borrow

    def test_subtree_borrow_at_root_node(self):
        self._tree.add_wide_m_liq(UnsignedDecimal("900"))
        self._tree.add_wide_t_liq(UnsignedDecimal("200"), UnsignedDecimal("57e18"), UnsignedDecimal("290e6"))
        self._tree.remove_wide_t_liq(UnsignedDecimal("50"), UnsignedDecimal("10e18"), UnsignedDecimal("1e6"))

        self._tree.add_m_liq(LiqRange(4, 7), UnsignedDecimal("100"))
        self._tree.add_t_liq(LiqRange(4, 7), UnsignedDecimal("10"), UnsignedDecimal("200e18"), UnsignedDecimal("200e6"))
        self._tree.remove_t_liq(LiqRange(4, 7), UnsignedDecimal("10"), UnsignedDecimal("100e18"), UnsignedDecimal("100e6"))

        root: LiqNode = self._tree.nodes[self._tree.root_key]
        self.assertEqual(root.token_x_subtree_borrow, UnsignedDecimal("147e18"))
        self.assertEqual(root.token_y_subtree_borrow, UnsignedDecimal("389e6"))

    def test_subtree_borrow_at_single_node(self):
        self._tree.add_m_liq(LiqRange(0, 3), UnsignedDecimal("500"))
        self._tree.add_t_liq(LiqRange(0, 3), UnsignedDecimal("400"), UnsignedDecimal("43e18"), UnsignedDecimal("12e6"))
        self._tree.remove_t_liq(LiqRange(0, 3), UnsignedDecimal("20"), UnsignedDecimal("20e18"), UnsignedDecimal("10e6"))

        zero_three: LiqNode = self._tree.nodes[4 << 24 | 16]
        self.assertEqual(zero_three.token_x_subtree_borrow, UnsignedDecimal("23e18"))
        self.assertEqual(zero_three.token_y_subtree_borrow, UnsignedDecimal("2e6"))

        zero_fifteen: LiqNode = self._tree.nodes[self._tree.root_key]
        self.assertEqual(zero_fifteen.token_x_subtree_borrow, UnsignedDecimal("23e18"))
        self.assertEqual(zero_fifteen.token_y_subtree_borrow, UnsignedDecimal("2e6"))

        # other borrows should be empty

    def test_subtree_borrow_at_leaf_node(self):
        self._tree.add_m_liq(LiqRange(3, 3), UnsignedDecimal("100"))
        self._tree.add_t_liq(LiqRange(3, 3), UnsignedDecimal("20"), UnsignedDecimal("22e18"), UnsignedDecimal("29e6"))
        self._tree.remove_t_liq(LiqRange(3, 3), UnsignedDecimal("20"), UnsignedDecimal("20e18"), UnsignedDecimal("20e6"))

        three_three: LiqNode = self._tree.nodes[1 << 24 | 19]
        self.assertEqual(three_three.token_x_subtree_borrow, UnsignedDecimal("2e18"))
        self.assertEqual(three_three.token_y_subtree_borrow, UnsignedDecimal("9e6"))

        # nodes above should include this amount
        two_three: LiqNode = self._tree.nodes[2 << 24 | 18]
        self.assertEqual(two_three.token_x_subtree_borrow, UnsignedDecimal("2e18"))
        self.assertEqual(two_three.token_y_subtree_borrow, UnsignedDecimal("9e6"))

        zero_three: LiqNode = self._tree.nodes[4 << 24 | 16]
        self.assertEqual(zero_three.token_x_subtree_borrow, UnsignedDecimal("2e18"))
        self.assertEqual(zero_three.token_y_subtree_borrow, UnsignedDecimal("9e6"))

        zero_seven: LiqNode = self._tree.nodes[8 << 24 | 16]
        self.assertEqual(zero_seven.token_x_subtree_borrow, UnsignedDecimal("2e18"))
        self.assertEqual(zero_seven.token_y_subtree_borrow, UnsignedDecimal("9e6"))

        zero_fifteen = self._tree.nodes[self._tree.root_key]
        self.assertEqual(zero_fifteen.token_x_subtree_borrow, UnsignedDecimal("2e18"))
        self.assertEqual(zero_fifteen.token_y_subtree_borrow, UnsignedDecimal("9e6"))

        # other borrows should be empty

    def test_subtree_borrow_split_across_several_nodes_walking_left_leg(self):
        self._tree.add_m_liq(LiqRange(1, 7), UnsignedDecimal("100"))
        self._tree.add_t_liq(LiqRange(1, 7), UnsignedDecimal("20"), UnsignedDecimal("12e18"), UnsignedDecimal("19e6"))
        self._tree.remove_t_liq(LiqRange(1, 7), UnsignedDecimal("20"), UnsignedDecimal("10e18"), UnsignedDecimal("10e6"))

        one_one: LiqNode = self._tree.nodes[1 << 24 | 17]
        self.assertEqual(int(one_one.token_x_subtree_borrow), UnsignedDecimal("285714285714285714"))
        self.assertEqual(int(one_one.token_y_subtree_borrow), UnsignedDecimal("1285714"))

        two_three: LiqNode = self._tree.nodes[2 << 24 | 18]
        self.assertEqual(int(two_three.token_x_subtree_borrow), UnsignedDecimal("571428571428571428"))
        self.assertEqual(int(two_three.token_y_subtree_borrow), UnsignedDecimal("2571428"))

        four_seven: LiqNode = self._tree.nodes[4 << 24 | 20]
        self.assertEqual(int(four_seven.token_x_subtree_borrow), UnsignedDecimal("1142857142857142857"))  # 1 wei lost
        self.assertEqual(int(four_seven.token_y_subtree_borrow), UnsignedDecimal("5142857"))  # 1 wei lost

        # nodes above should include this amount
        zero_one: LiqNode = self._tree.nodes[2 << 24 | 16]
        self.assertEqual(int(zero_one.token_x_subtree_borrow), UnsignedDecimal("285714285714285714"))
        self.assertEqual(int(zero_one.token_y_subtree_borrow), UnsignedDecimal("1285714"))

        zero_three: LiqNode = self._tree.nodes[4 << 24 | 16]
        self.assertEqual(int(zero_three.token_x_subtree_borrow), UnsignedDecimal("857142857142857142"))
        self.assertEqual(int(zero_three.token_y_subtree_borrow), UnsignedDecimal("3857142"))

        zero_seven: LiqNode = self._tree.nodes[8 << 24 | 16]
        self.assertEqual(int(zero_seven.token_x_subtree_borrow), UnsignedDecimal("2000000000000000000"))  # 2 wei lost
        self.assertEqual(int(zero_seven.token_y_subtree_borrow), UnsignedDecimal("9000000"))  # 2 wei lost

        zero_fifteen: LiqNode = self._tree.nodes[self._tree.root_key]
        self.assertEqual(int(zero_fifteen.token_x_subtree_borrow), UnsignedDecimal("2000000000000000000"))  # 2 wei lost
        self.assertEqual(int(zero_fifteen.token_y_subtree_borrow), UnsignedDecimal("9000000"))  # 2 wei lost

        # other borrows should be empty

    def test_subtree_borrow_split_across_several_nodes_walking_both_legs_below_peak(self):
        self._tree.add_m_liq(LiqRange(1, 2), UnsignedDecimal("100"))
        self._tree.add_t_liq(LiqRange(1, 2), UnsignedDecimal("20"), UnsignedDecimal("74e18"), UnsignedDecimal("21e6"))
        self._tree.remove_t_liq(LiqRange(1, 2), UnsignedDecimal("20"), UnsignedDecimal("2e18"), UnsignedDecimal("2e6"))

        one_one: LiqNode = self._tree.nodes[1 << 24 | 17]
        self.assertEqual(one_one.token_x_subtree_borrow, UnsignedDecimal("36000000000000000000"))
        self.assertEqual(one_one.token_y_subtree_borrow, UnsignedDecimal("9500000"))

        two_two: LiqNode = self._tree.nodes[1 << 24 | 18]
        self.assertEqual(two_two.token_x_subtree_borrow, UnsignedDecimal("36000000000000000000"))
        self.assertEqual(two_two.token_y_subtree_borrow, UnsignedDecimal("9500000"))

        # nodes above should include this amount

        zero_one: LiqNode = self._tree.nodes[2 << 24 | 16]
        self.assertEqual(zero_one.token_x_subtree_borrow, UnsignedDecimal("36e18"))
        self.assertEqual(zero_one.token_y_subtree_borrow, UnsignedDecimal("9.5e6"))

        two_three: LiqNode = self._tree.nodes[1 << 24 | 18]
        self.assertEqual(two_three.token_x_subtree_borrow, UnsignedDecimal("36e18"))
        self.assertEqual(two_three.token_y_subtree_borrow, UnsignedDecimal("9.5e6"))

        zero_three: LiqNode = self._tree.nodes[4 << 24 | 16]
        self.assertEqual(zero_three.token_x_subtree_borrow, UnsignedDecimal("72e18"))
        self.assertEqual(zero_three.token_y_subtree_borrow, UnsignedDecimal("19e6"))

        zero_seven: LiqNode = self._tree.nodes[8 << 24 | 16]
        self.assertEqual(zero_seven.token_x_subtree_borrow, UnsignedDecimal("72e18"))
        self.assertEqual(zero_seven.token_y_subtree_borrow, UnsignedDecimal("19e6"))

        zero_fifteen: LiqNode = self._tree.nodes[self._tree.root_key]
        self.assertEqual(zero_fifteen.token_x_subtree_borrow, UnsignedDecimal("72e18"))
        self.assertEqual(zero_fifteen.token_y_subtree_borrow, UnsignedDecimal("19e6"))

        # all other nodes should have 0

    def test_subtree_borrow_split_across_several_nodes_walking_right_leg(self):
        self._tree.add_m_liq(LiqRange(8, 14), UnsignedDecimal("100"))
        self._tree.add_t_liq(LiqRange(8, 14), UnsignedDecimal("20"), UnsignedDecimal("474e18"), UnsignedDecimal("220e6"))
        self._tree.remove_t_liq(LiqRange(8, 14), UnsignedDecimal("20"), UnsignedDecimal("2e18"), UnsignedDecimal("1e6"))

        eight_eleven: LiqNode = self._tree.nodes[4 << 24 | 24]
        self.assertEqual(int(eight_eleven.token_x_subtree_borrow), UnsignedDecimal("269714285714285714285"))  # 1 wei lost
        self.assertEqual(int(eight_eleven.token_y_subtree_borrow), UnsignedDecimal("125142857"))  # 1 wei lost

        twelve_thirteen: LiqNode = self._tree.nodes[2 << 24 | 28]
        self.assertEqual(int(twelve_thirteen.token_x_subtree_borrow), UnsignedDecimal("134857142857142857142"))
        self.assertEqual(int(twelve_thirteen.token_y_subtree_borrow), UnsignedDecimal("62571428"))

        fourteen_fourteen: LiqNode = self._tree.nodes[1 << 24 | 30]
        self.assertEqual(int(fourteen_fourteen.token_x_subtree_borrow), UnsignedDecimal("67428571428571428571"))
        self.assertEqual(int(fourteen_fourteen.token_y_subtree_borrow), UnsignedDecimal("31285714"))

        # nodes above should include this amount

        fourteen_fifteen: LiqNode = self._tree.nodes[2 << 24 | 30]
        self.assertEqual(int(fourteen_fifteen.token_x_subtree_borrow), UnsignedDecimal("67428571428571428571"))
        self.assertEqual(int(fourteen_fifteen.token_y_subtree_borrow), UnsignedDecimal("31285714"))

        twelve_fifteen: LiqNode = self._tree.nodes[4 << 24 | 28]
        self.assertEqual(int(twelve_fifteen.token_x_subtree_borrow), UnsignedDecimal("202285714285714285714"))  # 1 wei lost
        self.assertEqual(int(twelve_fifteen.token_y_subtree_borrow), UnsignedDecimal("93857142"))

        eight_fifteen: LiqNode = self._tree.nodes[8 << 24 | 24]
        self.assertEqual(int(eight_fifteen.token_x_subtree_borrow), UnsignedDecimal("472000000000000000000"))  # 3 wei lost
        self.assertEqual(int(eight_fifteen.token_y_subtree_borrow), UnsignedDecimal("219000000"))  # 2 wei lost

        zero_fifteen: LiqNode = self._tree.nodes[self._tree.root_key]
        self.assertEqual(int(zero_fifteen.token_x_subtree_borrow), UnsignedDecimal("472000000000000000000"))  # 3 wei lost
        self.assertEqual(int(zero_fifteen.token_y_subtree_borrow), UnsignedDecimal("219000000"))  # 2 wei lost

    def test_subtree_borrow_split_across_several_nodes_walking_both_legs_at_or_above_peak(self):
        self._tree.add_m_liq(LiqRange(8, 15), UnsignedDecimal("100"))
        self._tree.add_t_liq(LiqRange(8, 15), UnsignedDecimal("20"), UnsignedDecimal("1473e18"), UnsignedDecimal("5220e6"))
        self._tree.remove_t_liq(LiqRange(8, 15), UnsignedDecimal("20"), UnsignedDecimal("1e18"), UnsignedDecimal("1e6"))

        eight_fifteen: LiqNode = self._tree.nodes[8 << 24 | 24]
        self.assertEqual(eight_fifteen.token_x_subtree_borrow, UnsignedDecimal("1472e18"))
        self.assertEqual(eight_fifteen.token_y_subtree_borrow, UnsignedDecimal("5219e6"))

        # nodes above should include this amount

        zero_fifteen: LiqNode = self._tree.nodes[self._tree.root_key]
        self.assertEqual(zero_fifteen.token_x_subtree_borrow, UnsignedDecimal("1472e18"))
        self.assertEqual(zero_fifteen.token_y_subtree_borrow, UnsignedDecimal("5219e6"))

        # all other nodes should have 0

    # endregion

    # region SubtreeMLiq

    # note: different from subtreeMLiq on the node
    def _calculate_subtree_m_liq_for_node(self, key: int) -> int:
        range = key >> 24

        node: LiqNode = self._tree.nodes[key]
        subtree_m_liq_for_node = node.m_liq * range
        if range == 1:
            return subtree_m_liq_for_node

        (left, right) = LiquidityKey.children(key)
        return subtree_m_liq_for_node + self._calculate_subtree_m_liq_for_node(left) + self._calculate_subtree_m_liq_for_node(right)

    def test_subtree_m_liq_at_single_node(self):
        self._tree.add_m_liq(LiqRange(0, 3), UnsignedDecimal("500"))
        self.assertEqual(self._calculate_subtree_m_liq_for_node(4 << 24 | 16), UnsignedDecimal("2000"))

    def test_subtree_m_liq_at_leaf_node(self):
        self._tree.add_m_liq(LiqRange(3, 3), UnsignedDecimal("100"))
        self.assertEqual(self._calculate_subtree_m_liq_for_node(1 << 24 | 19), UnsignedDecimal("100"))

    def test_subtree_m_liq_for_m_liq_split_across_several_nodes_walking_left_leg(self):
        self._tree.add_m_liq(LiqRange(1, 7), UnsignedDecimal("200"))

        self.assertEqual(self._calculate_subtree_m_liq_for_node(1 << 24 | 17), UnsignedDecimal("200"))
        self.assertEqual(self._calculate_subtree_m_liq_for_node(2 << 24 | 18), UnsignedDecimal("400"))
        self.assertEqual(self._calculate_subtree_m_liq_for_node(4 << 24 | 20), UnsignedDecimal("800"))

        self.assertEqual(self._calculate_subtree_m_liq_for_node(2 << 24 | 16), UnsignedDecimal("200"))
        self.assertEqual(self._calculate_subtree_m_liq_for_node(4 << 24 | 16), UnsignedDecimal("600"))
        self.assertEqual(self._calculate_subtree_m_liq_for_node(8 << 24 | 16), UnsignedDecimal("1400"))
        self.assertEqual(self._calculate_subtree_m_liq_for_node(self._tree.root_key), UnsignedDecimal("1400"))

    def test_subtree_m_liq_for_m_liq_split_across_several_nodes_walking_both_legs_below_peak(self):
        self._tree.add_m_liq(LiqRange(1, 2), UnsignedDecimal("70"))

        self.assertEqual(self._calculate_subtree_m_liq_for_node(1 << 24 | 17), UnsignedDecimal("70"))
        self.assertEqual(self._calculate_subtree_m_liq_for_node(1 << 24 | 18), UnsignedDecimal("70"))

        self.assertEqual(self._calculate_subtree_m_liq_for_node(2 << 24 | 16), UnsignedDecimal("70"))
        self.assertEqual(self._calculate_subtree_m_liq_for_node(2 << 24 | 18), UnsignedDecimal("70"))
        self.assertEqual(self._calculate_subtree_m_liq_for_node(4 << 24 | 16), UnsignedDecimal("140"))
        self.assertEqual(self._calculate_subtree_m_liq_for_node(8 << 24 | 16), UnsignedDecimal("140"))
        self.assertEqual(self._calculate_subtree_m_liq_for_node(self._tree.root_key), UnsignedDecimal("140"))

    def test_subtree_m_liq_for_m_liq_split_across_several_nodes_walking_right_leg(self):
        self._tree.add_m_liq(LiqRange(8, 14), UnsignedDecimal("9"))

        self.assertEqual(self._calculate_subtree_m_liq_for_node(4 << 24 | 24), UnsignedDecimal("36"))
        self.assertEqual(self._calculate_subtree_m_liq_for_node(2 << 24 | 28), UnsignedDecimal("18"))
        self.assertEqual(self._calculate_subtree_m_liq_for_node(1 << 24 | 30), UnsignedDecimal("9"))

        self.assertEqual(self._calculate_subtree_m_liq_for_node(2 << 24 | 30), UnsignedDecimal("9"))
        self.assertEqual(self._calculate_subtree_m_liq_for_node(4 << 24 | 28), UnsignedDecimal("27"))
        self.assertEqual(self._calculate_subtree_m_liq_for_node(8 << 24 | 24), UnsignedDecimal("63"))
        self.assertEqual(self._calculate_subtree_m_liq_for_node(self._tree.root_key), UnsignedDecimal("63"))

    def test_subtree_m_liq_for_m_liq_split_across_several_nodes_walking_both_legs_at_or_above_peak(self):
        self._tree.add_m_liq(LiqRange(8, 15), UnsignedDecimal("100"))

        self.assertEqual(self._calculate_subtree_m_liq_for_node(8 << 24 | 24), UnsignedDecimal("800"))
        self.assertEqual(self._calculate_subtree_m_liq_for_node(self._tree.root_key), UnsignedDecimal("800"))

    # endregion

    # region A[]

    def _allocate_auxillary_array(self):
        m_liq: UnsignedDecimal = UnsignedDecimal("16384")
        self._tree.add_wide_m_liq(m_liq)

        for j in [1, 2, 4, 8]:
            m_liq = UnsignedDecimal("1024") * j

            i = 0
            while i < 16:
                self._tree.add_m_liq(LiqRange(i, i + j - 1), m_liq)
                i += j
                m_liq += 1

    def test_aux_allocation(self):
        self._allocate_auxillary_array()

        self.assertEqual(self._tree.nodes[self._tree.root_key].m_liq, 16384)

        self.assertEqual(self._tree.nodes[8 << 24 | 16].m_liq, 8192)
        self.assertEqual(self._tree.nodes[8 << 24 | 24].m_liq, 8193)

        self.assertEqual(self._tree.nodes[4 << 24 | 16].m_liq, 4096)
        self.assertEqual(self._tree.nodes[4 << 24 | 20].m_liq, 4097)
        self.assertEqual(self._tree.nodes[4 << 24 | 24].m_liq, 4098)
        self.assertEqual(self._tree.nodes[4 << 24 | 28].m_liq, 4099)

        self.assertEqual(self._tree.nodes[2 << 24 | 16].m_liq, 2048)
        self.assertEqual(self._tree.nodes[2 << 24 | 18].m_liq, 2049)
        self.assertEqual(self._tree.nodes[2 << 24 | 20].m_liq, 2050)
        self.assertEqual(self._tree.nodes[2 << 24 | 22].m_liq, 2051)
        self.assertEqual(self._tree.nodes[2 << 24 | 24].m_liq, 2052)
        self.assertEqual(self._tree.nodes[2 << 24 | 26].m_liq, 2053)
        self.assertEqual(self._tree.nodes[2 << 24 | 28].m_liq, 2054)
        self.assertEqual(self._tree.nodes[2 << 24 | 30].m_liq, 2055)

        self.assertEqual(self._tree.nodes[1 << 24 | 16].m_liq, 1024)
        self.assertEqual(self._tree.nodes[1 << 24 | 17].m_liq, 1025)
        self.assertEqual(self._tree.nodes[1 << 24 | 18].m_liq, 1026)
        self.assertEqual(self._tree.nodes[1 << 24 | 19].m_liq, 1027)
        self.assertEqual(self._tree.nodes[1 << 24 | 20].m_liq, 1028)
        self.assertEqual(self._tree.nodes[1 << 24 | 21].m_liq, 1029)
        self.assertEqual(self._tree.nodes[1 << 24 | 22].m_liq, 1030)
        self.assertEqual(self._tree.nodes[1 << 24 | 23].m_liq, 1031)
        self.assertEqual(self._tree.nodes[1 << 24 | 24].m_liq, 1032)
        self.assertEqual(self._tree.nodes[1 << 24 | 25].m_liq, 1033)
        self.assertEqual(self._tree.nodes[1 << 24 | 26].m_liq, 1034)
        self.assertEqual(self._tree.nodes[1 << 24 | 27].m_liq, 1035)
        self.assertEqual(self._tree.nodes[1 << 24 | 28].m_liq, 1036)
        self.assertEqual(self._tree.nodes[1 << 24 | 29].m_liq, 1037)
        self.assertEqual(self._tree.nodes[1 << 24 | 30].m_liq, 1038)
        self.assertEqual(self._tree.nodes[1 << 24 | 31].m_liq, 1039)

    def test_aux_at_node_of_range_one(self):
        self._allocate_auxillary_array()

        self._tree.add_t_liq(LiqRange(0, 0), UnsignedDecimal("100"), UnsignedDecimal("1"), UnsignedDecimal("1"))
        self._tree.token_x_fee_rate_snapshot += UnsignedDecimal("1756720331627508019494912")
        self._tree.token_y_fee_rate_snapshot += UnsignedDecimal("1756720331627508019494912")
        self._tree.remove_t_liq(LiqRange(0, 0), UnsignedDecimal("100"), UnsignedDecimal("1"), UnsignedDecimal("1"))

        zero_zero: LiqNode = self._tree.nodes[1 << 24 | 16]
        self.assertEqual(zero_zero.token_x_cumulative_earned_per_m_liq, 3)
        self.assertEqual(zero_zero.token_x_cumulative_earned_per_m_subtree_liq, 3)
        self.assertEqual(zero_zero.token_y_cumulative_earned_per_m_liq, 3)
        self.assertEqual(zero_zero.token_x_cumulative_earned_per_m_subtree_liq, 3)

    def test_aux_at_node_of_range_two(self):
        self._allocate_auxillary_array()

        self._tree.add_t_liq(LiqRange(0, 1), UnsignedDecimal("100"), UnsignedDecimal("2"), UnsignedDecimal("2"))
        self._tree.token_x_fee_rate_snapshot += UnsignedDecimal("1756748001743618583822336")
        self._tree.token_y_fee_rate_snapshot += UnsignedDecimal("1756748001743618583822336")
        self._tree.remove_t_liq(LiqRange(0, 1), UnsignedDecimal("100"), UnsignedDecimal("1"), UnsignedDecimal("1"))

        zero_one: LiqNode = self._tree.nodes[2 << 24 | 16]
        self.assertEqual(zero_one.token_x_cumulative_earned_per_m_liq, 3)
        self.assertEqual(zero_one.token_x_cumulative_earned_per_m_subtree_liq, 3)
        self.assertEqual(zero_one.token_y_cumulative_earned_per_m_liq, 3)
        self.assertEqual(zero_one.token_x_cumulative_earned_per_m_subtree_liq, 3)

    def test_aux_at_node_of_range_four(self):
        self._allocate_auxillary_array()

        self._tree.add_t_liq(LiqRange(0, 3), UnsignedDecimal("100"), UnsignedDecimal("4"), UnsignedDecimal("4"))
        self._tree.token_x_fee_rate_snapshot += UnsignedDecimal("1756831012091950276804608")
        self._tree.token_y_fee_rate_snapshot += UnsignedDecimal("1756831012091950276804608")
        self._tree.remove_t_liq(LiqRange(0, 3), UnsignedDecimal("100"), UnsignedDecimal("1"), UnsignedDecimal("1"))

        zero_three: LiqNode = self._tree.nodes[4 << 24 | 16]
        self.assertEqual(zero_three.token_x_cumulative_earned_per_m_liq, 3)
        self.assertEqual(zero_three.token_x_cumulative_earned_per_m_subtree_liq, 3)
        self.assertEqual(zero_three.token_y_cumulative_earned_per_m_liq, 3)
        self.assertEqual(zero_three.token_x_cumulative_earned_per_m_subtree_liq, 3)

    def test_aux_at_node_of_range_eight(self):
        self._allocate_auxillary_array()

        self._tree.add_t_liq(LiqRange(0, 7), UnsignedDecimal("100"), UnsignedDecimal("8"), UnsignedDecimal("8"))
        self._tree.token_x_fee_rate_snapshot += UnsignedDecimal("1757024702904724227096576")
        self._tree.token_y_fee_rate_snapshot += UnsignedDecimal("1757024702904724227096576")
        self._tree.remove_t_liq(LiqRange(0, 7), UnsignedDecimal("100"), UnsignedDecimal("1"), UnsignedDecimal("1"))

        zero_seven: LiqNode = self._tree.nodes[8 << 24 | 16]
        self.assertEqual(zero_seven.token_x_cumulative_earned_per_m_liq, 3)
        self.assertEqual(zero_seven.token_x_cumulative_earned_per_m_subtree_liq, 3)
        self.assertEqual(zero_seven.token_y_cumulative_earned_per_m_liq, 3)
        self.assertEqual(zero_seven.token_x_cumulative_earned_per_m_subtree_liq, 3)

    def test_aux_at_node_of_range_sixteen(self):
        self._allocate_auxillary_array()

        self._tree.add_wide_t_liq(UnsignedDecimal("100"), UnsignedDecimal("16"), UnsignedDecimal("16"))
        self._tree.token_x_fee_rate_snapshot += UnsignedDecimal("1757439754646382692007936")
        self._tree.token_y_fee_rate_snapshot += UnsignedDecimal("1757439754646382692007936")
        self._tree.remove_wide_t_liq(UnsignedDecimal("100"), UnsignedDecimal("16"), UnsignedDecimal("16"))

        zero_fifteen: LiqNode = self._tree.nodes[self._tree.root_key]
        self.assertEqual(zero_fifteen.token_x_cumulative_earned_per_m_liq, 3)
        self.assertEqual(zero_fifteen.token_x_cumulative_earned_per_m_subtree_liq, 3)
        self.assertEqual(zero_fifteen.token_y_cumulative_earned_per_m_liq, 3)
        self.assertEqual(zero_fifteen.token_x_cumulative_earned_per_m_subtree_liq, 3)

    # endregion

    # region N.range

    def test_node_range_of_one_in_fee_calculation(self):
        self._tree.add_wide_m_liq(UnsignedDecimal("1"))
        self._tree.add_m_liq(LiqRange(0, 0), UnsignedDecimal("5"))
        self._tree.add_t_liq(LiqRange(0, 0), UnsignedDecimal("1"), UnsignedDecimal("18"), UnsignedDecimal("18"))

        self._tree.token_x_fee_rate_snapshot += UnsignedDecimal("18446744073709551616")
        self._tree.token_y_fee_rate_snapshot += UnsignedDecimal("18446744073709551616")
        self._tree.remove_t_liq(LiqRange(0, 0), UnsignedDecimal("1"), UnsignedDecimal("15"), UnsignedDecimal("15"))

        zero_zero: LiqNode = self._tree.nodes[1 << 24 | 16]
        self.assertEqual(zero_zero.token_x_cumulative_earned_per_m_liq, 3)
        self.assertEqual(zero_zero.token_x_cumulative_earned_per_m_subtree_liq, 3)
        self.assertEqual(zero_zero.token_y_cumulative_earned_per_m_liq, 3)
        self.assertEqual(zero_zero.token_x_cumulative_earned_per_m_subtree_liq, 3)

    def test_node_range_of_two_in_fee_calculation(self):
        self._tree.add_wide_m_liq(UnsignedDecimal("1"))
        self._tree.add_m_liq(LiqRange(0, 1), UnsignedDecimal("4"))
        self._tree.add_t_liq(LiqRange(0, 1), UnsignedDecimal("1"), UnsignedDecimal("31"), UnsignedDecimal("31"))

        self._tree.token_x_fee_rate_snapshot += UnsignedDecimal("18446744073709551616")
        self._tree.token_y_fee_rate_snapshot += UnsignedDecimal("18446744073709551616")
        self._tree.remove_t_liq(LiqRange(0, 1), UnsignedDecimal("1"), UnsignedDecimal("21"), UnsignedDecimal("21"))

        zero_one: LiqNode = self._tree.nodes[2 << 24 | 16]
        self.assertEqual(zero_one.token_x_cumulative_earned_per_m_liq, 3)
        self.assertEqual(zero_one.token_x_cumulative_earned_per_m_subtree_liq, 3)
        self.assertEqual(zero_one.token_y_cumulative_earned_per_m_liq, 3)
        self.assertEqual(zero_one.token_x_cumulative_earned_per_m_subtree_liq, 3)

    def test_node_range_of_four_in_fee_calculation(self):
        self._tree.add_wide_m_liq(UnsignedDecimal("1"))
        self._tree.add_m_liq(LiqRange(0, 3), UnsignedDecimal("24"))
        self._tree.add_t_liq(LiqRange(0, 3), UnsignedDecimal("1"), UnsignedDecimal("300"), UnsignedDecimal("300"))

        self._tree.token_x_fee_rate_snapshot += UnsignedDecimal("18446744073709551616")
        self._tree.token_y_fee_rate_snapshot += UnsignedDecimal("18446744073709551616")
        self._tree.remove_t_liq(LiqRange(0, 3), UnsignedDecimal("1"), UnsignedDecimal("300"), UnsignedDecimal("300"))

        zero_three: LiqNode = self._tree.nodes[4 << 24 | 16]
        self.assertEqual(zero_three.token_x_cumulative_earned_per_m_liq, 3)
        self.assertEqual(zero_three.token_x_cumulative_earned_per_m_subtree_liq, 3)
        self.assertEqual(zero_three.token_y_cumulative_earned_per_m_liq, 3)
        self.assertEqual(zero_three.token_x_cumulative_earned_per_m_subtree_liq, 3)

    def test_node_range_of_eight_in_fee_calculation(self):
        self._tree.add_wide_m_liq(UnsignedDecimal("1"))
        self._tree.add_m_liq(LiqRange(0, 7), UnsignedDecimal("47"))
        self._tree.add_t_liq(LiqRange(0, 7), UnsignedDecimal("1"), UnsignedDecimal("1152"), UnsignedDecimal("1152"))

        self._tree.token_x_fee_rate_snapshot += UnsignedDecimal("18446744073709551616")
        self._tree.token_y_fee_rate_snapshot += UnsignedDecimal("18446744073709551616")
        self._tree.remove_t_liq(LiqRange(0, 7), UnsignedDecimal("1"), UnsignedDecimal("1"), UnsignedDecimal("1"))

        zero_seven: LiqNode = self._tree.nodes[8 << 24 | 16]
        self.assertEqual(zero_seven.token_x_cumulative_earned_per_m_liq, 3)
        self.assertEqual(zero_seven.token_x_cumulative_earned_per_m_subtree_liq, 3)
        self.assertEqual(zero_seven.token_y_cumulative_earned_per_m_liq, 3)
        self.assertEqual(zero_seven.token_x_cumulative_earned_per_m_subtree_liq, 3)

    def test_node_range_of_sixteen_in_fee_calculation(self):
        self._tree.add_wide_m_liq(UnsignedDecimal("3"))
        self._tree.add_wide_t_liq(UnsignedDecimal("1"), UnsignedDecimal("144"), UnsignedDecimal("144"))

        self._tree.token_x_fee_rate_snapshot += UnsignedDecimal("18446744073709551616")
        self._tree.token_y_fee_rate_snapshot += UnsignedDecimal("18446744073709551616")
        self._tree.remove_wide_t_liq(UnsignedDecimal("1"), UnsignedDecimal("1"), UnsignedDecimal("1"))

        zero_fifteen: LiqNode = self._tree.nodes[self._tree.root_key]
        self.assertEqual(zero_fifteen.token_x_cumulative_earned_per_m_liq, 3)
        self.assertEqual(zero_fifteen.token_x_cumulative_earned_per_m_subtree_liq, 3)
        self.assertEqual(zero_fifteen.token_y_cumulative_earned_per_m_liq, 3)
        self.assertEqual(zero_fifteen.token_x_cumulative_earned_per_m_subtree_liq, 3)

    # endregion

    # region r

    def test_tree_initial_rates(self):
        self.assertEqual(self._tree.token_x_fee_rate_snapshot, 0)
        self.assertEqual(self._tree.token_y_fee_rate_snapshot, 0)

    def test_tree_rate_accumulation(self):
        self._tree.token_x_fee_rate_snapshot += 1
        self._tree.token_y_fee_rate_snapshot += 1
        self.assertEqual(self._tree.token_x_fee_rate_snapshot, 1)
        self.assertEqual(self._tree.token_y_fee_rate_snapshot, 1)

    def test_tree_multi_rate_accumulation(self):
        self._tree.token_x_fee_rate_snapshot += 1
        self._tree.token_y_fee_rate_snapshot += 1

        self._tree.token_x_fee_rate_snapshot += UnsignedDecimal("2378467856789361026348")
        self._tree.token_y_fee_rate_snapshot += UnsignedDecimal("7563853478956240629035625248956723456")

        self.assertEqual(self._tree.token_x_fee_rate_snapshot, UnsignedDecimal("2378467856789361026349"))
        self.assertEqual(self._tree.token_y_fee_rate_snapshot, UnsignedDecimal("7563853478956240629035625248956723457"))

    def test_node_initial_rates(self):
        # test all nodes?

        eight_fifteen: LiqNode = self._tree.nodes[8 << 24 | 24]
        self.assertEqual(eight_fifteen.token_x_fee_rate_snapshot, 0)
        self.assertEqual(eight_fifteen.token_y_fee_rate_snapshot, 0)

    def test_node_rate_accumulation_adding_m_liq(self):
        self._tree.token_x_fee_rate_snapshot += 1
        self._tree.token_y_fee_rate_snapshot += 1

        self._tree.add_m_liq(LiqRange(15, 15), UnsignedDecimal("100"))

        eight_fifteen: LiqNode = self._tree.nodes[8 << 24 | 24]
        self.assertEqual(eight_fifteen.token_x_fee_rate_snapshot, 1)
        self.assertEqual(eight_fifteen.token_y_fee_rate_snapshot, 1)

    def test_node_multi_rate_accumulation_adding_m_liq(self):
        self._tree.token_x_fee_rate_snapshot += 1
        self._tree.token_y_fee_rate_snapshot += 1

        self._tree.token_x_fee_rate_snapshot += UnsignedDecimal("8726349723049235689236")
        self._tree.token_y_fee_rate_snapshot += UnsignedDecimal("827369027349823649072634587236582365")
        self._tree.add_m_liq(LiqRange(15, 15), UnsignedDecimal("100"))

        eight_fifteen: LiqNode = self._tree.nodes[8 << 24 | 24]
        self.assertEqual(eight_fifteen.token_x_fee_rate_snapshot, UnsignedDecimal("8726349723049235689237"))
        self.assertEqual(eight_fifteen.token_y_fee_rate_snapshot, UnsignedDecimal("827369027349823649072634587236582366"))

    def test_node_rate_does_not_accumulate_when_adding_m_liq_to_other_nodes(self):
        self._tree.token_x_fee_rate_snapshot += 1
        self._tree.token_y_fee_rate_snapshot += 1

        self._tree.add_m_liq(LiqRange(0, 0), UnsignedDecimal("100"))

        eight_fifteen: LiqNode = self._tree.nodes[8 << 24 | 24]
        self.assertEqual(eight_fifteen.token_x_fee_rate_snapshot, UnsignedDecimal("0"))
        self.assertEqual(eight_fifteen.token_y_fee_rate_snapshot, UnsignedDecimal("0"))

    def test_node_rate_does_not_accumulate_when_adding_wide_m_liq(self):
        self._tree.token_x_fee_rate_snapshot += 1
        self._tree.token_y_fee_rate_snapshot += 1

        self._tree.add_wide_m_liq(UnsignedDecimal("100"))
        eight_fifteen: LiqNode = self._tree.nodes[8 << 24 | 24]
        self.assertEqual(eight_fifteen.token_x_fee_rate_snapshot, UnsignedDecimal("0"))
        self.assertEqual(eight_fifteen.token_y_fee_rate_snapshot, UnsignedDecimal("0"))

    def test_node_rate_accumulation_removing_m_liq(self):
        self._tree.add_m_liq(LiqRange(15, 15), UnsignedDecimal("100"))
        self._tree.token_x_fee_rate_snapshot += 1
        self._tree.token_y_fee_rate_snapshot += 1
        self._tree.remove_m_liq(LiqRange(15, 15), UnsignedDecimal("20"))

        eight_fifteen: LiqNode = self._tree.nodes[8 << 24 | 24]
        self.assertEqual(eight_fifteen.token_x_fee_rate_snapshot, UnsignedDecimal("1"))
        self.assertEqual(eight_fifteen.token_y_fee_rate_snapshot, UnsignedDecimal("1"))

    def test_node_multi_rate_accumulation_removing_m_liq(self):
        self._tree.token_x_fee_rate_snapshot += 1
        self._tree.token_y_fee_rate_snapshot += 1

        self._tree.add_m_liq(LiqRange(15, 15), UnsignedDecimal("100"))
        self._tree.token_x_fee_rate_snapshot += UnsignedDecimal("8726349723049235689236")
        self._tree.token_y_fee_rate_snapshot += UnsignedDecimal("827369027349823649072634587236582365")
        self._tree.remove_m_liq(LiqRange(15, 15), UnsignedDecimal("20"))

        eight_fifteen: LiqNode = self._tree.nodes[8 << 24 | 24]
        self.assertEqual(eight_fifteen.token_x_fee_rate_snapshot, UnsignedDecimal("8726349723049235689237"))
        self.assertEqual(eight_fifteen.token_y_fee_rate_snapshot, UnsignedDecimal("827369027349823649072634587236582366"))

    def test_node_rate_does_not_accumulate_when_removing_m_liq_from_other_nodes(self):
        self._tree.add_m_liq(LiqRange(0, 0), UnsignedDecimal("100"))
        self._tree.token_x_fee_rate_snapshot += 1
        self._tree.token_y_fee_rate_snapshot += 1
        self._tree.remove_m_liq(LiqRange(0, 0), UnsignedDecimal("100"))

        eight_fifteen: LiqNode = self._tree.nodes[8 << 24 | 24]
        self.assertEqual(eight_fifteen.token_x_fee_rate_snapshot, UnsignedDecimal("0"))
        self.assertEqual(eight_fifteen.token_y_fee_rate_snapshot, UnsignedDecimal("0"))

    def test_node_rate_does_not_accumulate_when_removing_wide_m_liq(self):
        self._tree.add_wide_m_liq(UnsignedDecimal("100"))
        self._tree.token_x_fee_rate_snapshot += 1
        self._tree.token_y_fee_rate_snapshot += 1
        self._tree.remove_wide_m_liq(UnsignedDecimal("100"))

        eight_fifteen: LiqNode = self._tree.nodes[8 << 24 | 24]
        self.assertEqual(eight_fifteen.token_x_fee_rate_snapshot, UnsignedDecimal("0"))
        self.assertEqual(eight_fifteen.token_y_fee_rate_snapshot, UnsignedDecimal("0"))

    def test_node_rate_accumulation_adding_t_liq(self):
        self._tree.add_m_liq(LiqRange(15, 15), UnsignedDecimal("100"))
        self._tree.token_x_fee_rate_snapshot += 1
        self._tree.token_y_fee_rate_snapshot += 1
        self._tree.add_t_liq(LiqRange(15, 15), UnsignedDecimal("10"), UnsignedDecimal("1"), UnsignedDecimal("1"))

        eight_fifteen: LiqNode = self._tree.nodes[8 << 24 | 24]
        self.assertEqual(eight_fifteen.token_x_fee_rate_snapshot, UnsignedDecimal("1"))
        self.assertEqual(eight_fifteen.token_y_fee_rate_snapshot, UnsignedDecimal("1"))

    def test_node_multi_rate_accumulation_adding_t_liq(self):
        self._tree.token_x_fee_rate_snapshot += 1
        self._tree.token_y_fee_rate_snapshot += 1

        self._tree.add_m_liq(LiqRange(15, 15), UnsignedDecimal("100"))
        self._tree.token_x_fee_rate_snapshot += UnsignedDecimal("8726349723049235689236")
        self._tree.token_y_fee_rate_snapshot += UnsignedDecimal("827369027349823649072634587236582365")
        self._tree.add_t_liq(LiqRange(15, 15), UnsignedDecimal("10"), UnsignedDecimal("1"), UnsignedDecimal("1"))

        eight_fifteen: LiqNode = self._tree.nodes[8 << 24 | 24]
        self.assertEqual(eight_fifteen.token_x_fee_rate_snapshot, UnsignedDecimal("8726349723049235689237"))
        self.assertEqual(eight_fifteen.token_y_fee_rate_snapshot, UnsignedDecimal("827369027349823649072634587236582366"))

    def test_node_rate_does_not_accumulate_when_adding_t_liq_to_other_nodes(self):
        self._tree.add_m_liq(LiqRange(0, 0), UnsignedDecimal("100"))
        self._tree.token_x_fee_rate_snapshot += 1
        self._tree.token_y_fee_rate_snapshot += 1
        self._tree.add_t_liq(LiqRange(0, 0), UnsignedDecimal("10"), UnsignedDecimal("1"), UnsignedDecimal("1"))

        eight_fifteen: LiqNode = self._tree.nodes[8 << 24 | 24]
        self.assertEqual(eight_fifteen.token_x_fee_rate_snapshot, UnsignedDecimal("0"))
        self.assertEqual(eight_fifteen.token_y_fee_rate_snapshot, UnsignedDecimal("0"))

    def test_node_rate_does_not_accumulate_when_adding_wide_t_liq(self):
        self._tree.add_wide_m_liq(UnsignedDecimal("100"))
        self._tree.token_x_fee_rate_snapshot += 1
        self._tree.token_y_fee_rate_snapshot += 1
        self._tree.add_wide_t_liq(UnsignedDecimal("10"), UnsignedDecimal("1"), UnsignedDecimal("1"))

        eight_fifteen: LiqNode = self._tree.nodes[8 << 24 | 24]
        self.assertEqual(eight_fifteen.token_x_fee_rate_snapshot, UnsignedDecimal("0"))
        self.assertEqual(eight_fifteen.token_y_fee_rate_snapshot, UnsignedDecimal("0"))

    def test_node_rate_accumulation_removing_t_liq(self):
        self._tree.add_m_liq(LiqRange(15, 15), UnsignedDecimal("100"))
        self._tree.add_t_liq(LiqRange(15, 15), UnsignedDecimal("10"), UnsignedDecimal("1"), UnsignedDecimal("1"))
        self._tree.token_x_fee_rate_snapshot += 1
        self._tree.token_y_fee_rate_snapshot += 1
        self._tree.remove_t_liq(LiqRange(15, 15), UnsignedDecimal("10"), UnsignedDecimal("1"), UnsignedDecimal("1"))

        eight_fifteen: LiqNode = self._tree.nodes[8 << 24 | 24]
        self.assertEqual(eight_fifteen.token_x_fee_rate_snapshot, UnsignedDecimal("1"))
        self.assertEqual(eight_fifteen.token_y_fee_rate_snapshot, UnsignedDecimal("1"))

    def test_node_multi_rate_accumulation_removing_t_liq(self):
        self._tree.token_x_fee_rate_snapshot += 1
        self._tree.token_y_fee_rate_snapshot += 1

        self._tree.add_m_liq(LiqRange(15, 15), UnsignedDecimal("100"))
        self._tree.add_t_liq(LiqRange(15, 15), UnsignedDecimal("10"), UnsignedDecimal("1"), UnsignedDecimal("1"))

        self._tree.token_x_fee_rate_snapshot += UnsignedDecimal("8726349723049235689236")
        self._tree.token_y_fee_rate_snapshot += UnsignedDecimal("827369027349823649072634587236582365")

        self._tree.remove_t_liq(LiqRange(15, 15), UnsignedDecimal("10"), UnsignedDecimal("1"), UnsignedDecimal("1"))

        eight_fifteen: LiqNode = self._tree.nodes[8 << 24 | 24]
        self.assertEqual(eight_fifteen.token_x_fee_rate_snapshot, UnsignedDecimal("8726349723049235689237"))
        self.assertEqual(eight_fifteen.token_y_fee_rate_snapshot, UnsignedDecimal("827369027349823649072634587236582366"))

    def test_node_rate_does_not_accumulate_when_removing_t_liq_from_other_nodes(self):
        self._tree.add_m_liq(LiqRange(0, 0), UnsignedDecimal("100"))
        self._tree.add_t_liq(LiqRange(0, 0), UnsignedDecimal("10"), UnsignedDecimal("1"), UnsignedDecimal("1"))
        self._tree.token_x_fee_rate_snapshot += 1
        self._tree.token_y_fee_rate_snapshot += 1
        self._tree.remove_t_liq(LiqRange(0, 0), UnsignedDecimal("10"), UnsignedDecimal("1"), UnsignedDecimal("1"))

        eight_fifteen: LiqNode = self._tree.nodes[8 << 24 | 24]
        self.assertEqual(eight_fifteen.token_x_fee_rate_snapshot, UnsignedDecimal("0"))
        self.assertEqual(eight_fifteen.token_y_fee_rate_snapshot, UnsignedDecimal("0"))

    def test_node_rate_does_not_accumulate_when_removing_wide_t_liq(self):
        self._tree.add_wide_m_liq(UnsignedDecimal("100"))
        self._tree.add_wide_t_liq(UnsignedDecimal("10"), UnsignedDecimal("1"), UnsignedDecimal("1"))
        self._tree.token_x_fee_rate_snapshot += 1
        self._tree.token_y_fee_rate_snapshot += 1
        self._tree.remove_wide_t_liq(UnsignedDecimal("10"), UnsignedDecimal("1"), UnsignedDecimal("1"))

        eight_fifteen: LiqNode = self._tree.nodes[8 << 24 | 24]
        self.assertEqual(eight_fifteen.token_x_fee_rate_snapshot, UnsignedDecimal("0"))
        self.assertEqual(eight_fifteen.token_y_fee_rate_snapshot, UnsignedDecimal("0"))

    # endregion
