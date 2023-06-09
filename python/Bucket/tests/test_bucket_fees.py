from FloatingPoint.FloatingPointTestCase import FloatingPointTestCase
from Bucket.LiquidityBucket import LiquidityBucket

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


class TestBucketFees(FloatingPointTestCase):
    def setUp(self) -> None:
        self._bucket = LiquidityBucket(size=16, sol_truncation=True)

    # region SubtreeMLiq

    def _calculate_subtree_m_liq_for_range(self, liq_range: LiqRange) -> UnsignedDecimal:
        queried_indices = range(liq_range.low, liq_range.high + 1)
        buckets = [bucket for idx, bucket in enumerate(self._bucket._buckets) if idx in queried_indices]
        return sum([sum([snap.m_liq for snap in b.snapshots]) for b in buckets])

    def test_subtree_m_liq_at_single_node(self):
        self._bucket.add_m_liq(LiqRange(0, 3), 500)
        self.assertEqual(self._calculate_subtree_m_liq_for_range(LiqRange(0, 3)), 2000)

    def test_subtree_m_liq_at_leaf_node(self):
        self._bucket.add_m_liq(LiqRange(3, 3), 100)
        self.assertEqual(self._calculate_subtree_m_liq_for_range(LiqRange(3, 3)), 100)

    def test_subtree_m_liq_for_m_liq_split_across_several_nodes_walking_left_leg(self):
        self._bucket.add_m_liq(LiqRange(1, 7), 200)

        self.assertEqual(self._calculate_subtree_m_liq_for_range(LiqRange(1, 1)), 200)
        self.assertEqual(self._calculate_subtree_m_liq_for_range(LiqRange(2, 3)), 400)
        self.assertEqual(self._calculate_subtree_m_liq_for_range(LiqRange(4, 7)), 800)

        self.assertEqual(self._calculate_subtree_m_liq_for_range(LiqRange(0, 1)), 200)
        self.assertEqual(self._calculate_subtree_m_liq_for_range(LiqRange(0, 3)), 600)
        self.assertEqual(self._calculate_subtree_m_liq_for_range(LiqRange(0, 7)), 1400)
        self.assertEqual(self._calculate_subtree_m_liq_for_range(LiqRange(0, 15)), 1400)

    def test_subtree_m_liq_for_m_liq_split_across_several_nodes_walking_both_legs_below_peak(self):
        self._bucket.add_m_liq(LiqRange(1, 2), 70)

        self.assertEqual(self._calculate_subtree_m_liq_for_range(LiqRange(1, 1)), 70)
        self.assertEqual(self._calculate_subtree_m_liq_for_range(LiqRange(2, 2)), 70)

        self.assertEqual(self._calculate_subtree_m_liq_for_range(LiqRange(0, 1)), 70)
        self.assertEqual(self._calculate_subtree_m_liq_for_range(LiqRange(2, 3)), 70)
        self.assertEqual(self._calculate_subtree_m_liq_for_range(LiqRange(0, 3)), 140)
        self.assertEqual(self._calculate_subtree_m_liq_for_range(LiqRange(0, 7)), 140)
        self.assertEqual(self._calculate_subtree_m_liq_for_range(LiqRange(0, 15)), 140)

    def test_subtree_m_liq_for_m_liq_split_across_several_nodes_walking_right_leg(self):
        self._bucket.add_m_liq(LiqRange(8, 14), 9)

        self.assertEqual(self._calculate_subtree_m_liq_for_range(LiqRange(8, 11)), 36)
        self.assertEqual(self._calculate_subtree_m_liq_for_range(LiqRange(12, 13)), 18)
        self.assertEqual(self._calculate_subtree_m_liq_for_range(LiqRange(14, 14)), 9)

        self.assertEqual(self._calculate_subtree_m_liq_for_range(LiqRange(14, 15)), 9)
        self.assertEqual(self._calculate_subtree_m_liq_for_range(LiqRange(12, 15)), 27)
        self.assertEqual(self._calculate_subtree_m_liq_for_range(LiqRange(8, 15)), 63)
        self.assertEqual(self._calculate_subtree_m_liq_for_range(LiqRange(0, 15)), 63)

    def test_subtree_m_liq_for_m_liq_split_across_several_nodes_walking_both_legs_at_or_above_peak(self):
        self._bucket.add_m_liq(LiqRange(8, 15), 100)

        self.assertEqual(self._calculate_subtree_m_liq_for_range(LiqRange(8, 15)), 800)
        self.assertEqual(self._calculate_subtree_m_liq_for_range(LiqRange(0, 15)), 800)

    # endregion
