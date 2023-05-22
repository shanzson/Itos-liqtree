from unittest import TestCase

from Bucket.LiquidityBucket import LiquidityBucket, Snapshot
from ILiquidity import *
from UnsignedDecimal import UnsignedDecimal
from LiquidityExceptions import *


class TestLiquidityBucket(TestCase):
    def setUp(self) -> None:
        self.liq_bucket = LiquidityBucket(size=16, sol_truncation=True)

    # mLiq

    def test_add_m_liq(self):
        self.liq_bucket.add_m_liq(LiqRange(8, 11), UnsignedDecimal(1111))

        m_liq = self.liq_bucket.query_m_liq(LiqRange(8, 11))
        self.assertEqual(m_liq, UnsignedDecimal(1111))

        m_liq = self.liq_bucket.query_m_liq(LiqRange(8, 8))
        self.assertEqual(m_liq, UnsignedDecimal(277))  # 277.75 * 4 = 1111

    # tLiq

    def test_remove_m_liq(self):
        self.liq_bucket.add_m_liq(LiqRange(8, 11), UnsignedDecimal(1111))
        self.liq_bucket.remove_m_liq(LiqRange(8, 11), UnsignedDecimal(111))

        m_liq = self.liq_bucket.query_m_liq(LiqRange(8, 11))
        self.assertEqual(m_liq, UnsignedDecimal(1000))

        m_liq = self.liq_bucket.query_m_liq(LiqRange(8, 8))
        self.assertEqual(m_liq, UnsignedDecimal(250))

    def test_revert_removing_m_liq_at_tick_with_zero_m_liq(self):
        self.assertRaises(LiquidityExceptionRemovingMoreMLiqThanExists, lambda: self.liq_bucket.remove_m_liq(LiqRange(3, 7), UnsignedDecimal(100)))

    def test_revert_removing_m_liq_at_tick_where_m_liq_is_lower_than_amount_to_remove(self):
        self.liq_bucket.add_m_liq(LiqRange(3, 7), UnsignedDecimal(90))
        self.assertRaises(LiquidityExceptionRemovingMoreMLiqThanExists, lambda: self.liq_bucket.remove_m_liq(LiqRange(3, 7), UnsignedDecimal(100)))


    def test_add_wide_m_liq(self):
        self.liq_bucket.add_wide_m_liq(UnsignedDecimal(1600))

    def test_a(self):
        self.liq_bucket.add_m_liq(LiqRange(8, 11), 1111)
        self.liq_bucket.add_t_liq(LiqRange(8, 11), 111, 24e18, 7e6)

        self.liq_bucket.token_x_fee_rate_snapshot += 113712805933826

        # trigger fees - keeping tree state the same by undoing action
        self.liq_bucket.add_m_liq(LiqRange(8, 11), 10)
        self.liq_bucket.remove_m_liq(LiqRange(8, 11), 10)

        # 8-11
        # 113712805933826 * 24e18 / 4444 / 2**64 = 33291000332.9100024179226406346006655493880262469301129331683
        # (min_m_liq, max_t_liq, acc_fees_x, acc_fees_y)


        # 8-8
        # 1/4 of 8-11 = 8322750083.227500604480660158650166387347006561732528233292075

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
        self.assertEqual(root.t_liq, UnsignedDecimal(0))
        self.assertEqual(root.token_x_borrowed, UnsignedDecimal(0))
        self.assertEqual(root.token_x_subtree_borrowed, UnsignedDecimal(0))
        self.assertEqual(root.token_y_borrowed, UnsignedDecimal(0))
        self.assertEqual(root.token_y_subtree_borrowed, UnsignedDecimal(0))

        self.assertEqual(self.liq_tree.token_x_fee_rate_snapshot, UnsignedDecimal(0))
        self.assertEqual(self.liq_tree.token_y_fee_rate_snapshot, UnsignedDecimal(0))

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

        self.assertEqual(self.liq_tree.token_x_fee_rate_snapshot, UnsignedDecimal(0))
        self.assertEqual(self.liq_tree.token_y_fee_rate_snapshot, UnsignedDecimal(0))

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
