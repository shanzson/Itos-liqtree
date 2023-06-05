from unittest import TestCase
from FloatingPoint.UnsignedDecimal import UnsignedDecimal
from FloatingPoint.FloatingPointTestCase import FloatingPointTestCase

# NOTE: all numbers must be given as Decimal numbers to avoid precision errors.
#       each Decimal number must be created using a string! Otherwise precision is lost when the input variable is created
#       For instance, 7927848e16 yields 79278479999999997378560 as an integer. While the type 7.927848e+22 looks ok, when passed to
#       UnsignedDecimal(7.927848e+22) is still equates to UnsignedDecimal('79278479999999997378560').
#       However, UnsignedDecimal("7927848e16") is correct. Converting to an int yields 79278480000000000000000
#
#       When asserting values are equal, the calculated decimal is truncated to its int representation
#       as the compared value in solidity would lose that extra precision.
#
#       If all goes perfectly, the final result in python would 100% match the final output in solidity

from Tree.LiquidityTree import LiquidityTree, LiqNode, LiqRange


class TestDenseLiquidityTreeExact(FloatingPointTestCase):
    def setUp(self) -> None:
        self.liq_tree = LiquidityTree(depth=4)

    def test_fee(self):
        liq_tree: LiquidityTree = self.liq_tree

        root: LiqNode = liq_tree.nodes[liq_tree.root_key]
        L: LiqNode = liq_tree.nodes[(8 << 24) | 16]  # 0-7
        LL: LiqNode = liq_tree.nodes[(4 << 24) | 16]  # 0-3
        LR: LiqNode = liq_tree.nodes[(4 << 24) | 20]  # 4-7
        LLL: LiqNode = liq_tree.nodes[(2 << 24) | 16]  # 0-1
        LLR: LiqNode = liq_tree.nodes[(2 << 24) | 18]  # 2-3
        LRL: LiqNode = liq_tree.nodes[(2 << 24) | 20]  # 4-5
        LRR: LiqNode = liq_tree.nodes[(2 << 24) | 22]  # 6-7
        LLLL: LiqNode = liq_tree.nodes[(1 << 24) | 16]  # 0-0
        LLLR: LiqNode = liq_tree.nodes[(1 << 24) | 17]  # 1-1
        LLRL: LiqNode = liq_tree.nodes[(1 << 24) | 18]  # 2-2
        LLRR: LiqNode = liq_tree.nodes[(1 << 24) | 19]  # 3-3
        LRLL: LiqNode = liq_tree.nodes[(1 << 24) | 19]  # 4-4
        LRLR: LiqNode = liq_tree.nodes[(1 << 24) | 19]  # 5-5
        LRRL: LiqNode = liq_tree.nodes[(1 << 24) | 19]  # 6-6
        LRRR: LiqNode = liq_tree.nodes[(1 << 24) | 19]  # 7-7
        RLLL: LiqNode = liq_tree.nodes[(1 << 24) | 19]  # 8-8

        liq_tree.add_m_liq(LiqRange(1, 7), UnsignedDecimal("200"))
        liq_tree.add_t_liq(LiqRange(1, 7), UnsignedDecimal("100"), UnsignedDecimal("500"), UnsignedDecimal("300"))

        liq_tree.add_m_liq(LiqRange(3, 5), UnsignedDecimal("214"))
        liq_tree.add_t_liq(LiqRange(3, 5), UnsignedDecimal("10"), UnsignedDecimal("98"), UnsignedDecimal("17"))

        liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("9832114591287191011328")  # 533 as Q192.64
        liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("4316538113248035078144")  # 234 as Q192.64

        # accumulate fees w/o changing node states
        liq_tree.add_m_liq(LiqRange(1, 7), UnsignedDecimal("200"))
        liq_tree.remove_m_liq(LiqRange(1, 7), UnsignedDecimal("200"))
        liq_tree.add_m_liq(LiqRange(3, 5), UnsignedDecimal("214"))
        liq_tree.remove_m_liq(LiqRange(3, 5), UnsignedDecimal("214"))

        # before querying, let's verify node states
        # Effected nodes (1-1), (2-3), (4-7), (3-3), (4-5)

        # // totalMLiq = 200 * 1 + (0) * 1 = 200
        # // N.borrowX = 1 * 500 / 7
        # // N.subtreeBorrowX = 1 * 500 / 7
        # // nodeEarnPerMLiqX += (1 * 500 / 7) * 533 / 200
        # // nodeSubtreeEarnPerMLiqX += (1 * 500 / 7) * 533 / 200

        # (1-1)
        # N.borrowX = 1 * 500 / 7 = 71.428571428571428571428571428571428571428571428571428571428571428
        # N.subtreeBorrowX = 1 * 500 / 7 = 71.428571428571428571428571428571428571428571428571428571428571428
        # totalMLiq = 200 * 1 + (0) * 1 = 200
        # nodeEarnPerMLiqX += (1 * 500 / 7) * 9832114591287191011328 / 200 / 2**64 = 190.35714285714285714285714285714285714285714285714285714285714285
        # nodeSubtreeEarnPerMLiqX += (1 * 500 / 7) * 9832114591287191011328 / 200 / 2**64 = 190.35714285714285714285714285714285714285714285714285714285714285
        self.assertFloatingPointEqual(LLLR.token_x_borrowed, UnsignedDecimal("71.428571428571428571428571428571428571428571428571428571428571428"))
        self.assertFloatingPointEqual(LLLR.token_x_subtree_borrowed, UnsignedDecimal("71.428571428571428571428571428571428571428571428571428571428571428"))
        self.assertFloatingPointEqual(LLLR.token_x_cumulative_earned_per_m_liq, UnsignedDecimal("190.35714285714285714285714285714285714285714285714285714285714285"))
        self.assertFloatingPointEqual(LLLR.token_x_cumulative_earned_per_m_subtree_liq, UnsignedDecimal("190.35714285714285714285714285714285714285714285714285714285714285"))

        # (0-1)
        # N.borrowX = 0
        # N.subtreeBorrowX = 1 * 500 / 7 = 71.428571428571428571428571428571428571428571428571428571428571428
        # totalMLiq = 0 + 200 * 1 + (0) * 1 = 200
        # nodeEarnPerMLiqX += 0
        # nodeSubtreeEarnPerMLiqX += (1 * 500 / 7) / 200 * 9832114591287191011328 / 2**64 = 190.35714285714285714285714285714285714285714285714285714285714285
        self.assertFloatingPointEqual(LLL.token_x_borrowed, UnsignedDecimal("0"))
        self.assertFloatingPointEqual(LLL.token_x_subtree_borrowed, UnsignedDecimal("71.428571428571428571428571428571428571428571428571428571428571428"))
        self.assertFloatingPointEqual(LLL.token_x_cumulative_earned_per_m_liq, UnsignedDecimal("0"))
        self.assertFloatingPointEqual(LLL.token_x_cumulative_earned_per_m_subtree_liq, UnsignedDecimal("190.35714285714285714285714285714285714285714285714285714285714285"))

        # (2-3)
        # N.borrowX = 2 * 500 / 7 = 142.85714285714285714285714285714285714285714285714285714285714285
        # N.subtreeBorrowX = 2 * 500 / 7 + 1 * 98 / 3 = 175.52380952380952380952380952380952380952380952380952380952380952
        # totalMLiq = (200 * 2 + 214 * 1) + (0) * 2 = 614
        # nodeEarnPerMLiqX += (2 * 500 / 7) * 9832114591287191011328 / 614 / 2**64 = 124.01116798510935318752908329455560725919032107957189390414146114
        # nodeSubtreeEarnPerMLiqX += (2 * 500 / 7 + 1 * 98 / 3) * 9832114591287191011328 / 614 / 2**64 = 152.36838839770435861641073367457732278579184116643400031022180859
        self.assertFloatingPointEqual(LLR.token_x_borrowed, UnsignedDecimal("142.85714285714285714285714285714285714285714285714285714285714285"))
        self.assertFloatingPointEqual(LLR.token_x_subtree_borrowed, UnsignedDecimal("175.52380952380952380952380952380952380952380952380952380952380952"))
        self.assertFloatingPointEqual(LLR.token_x_cumulative_earned_per_m_liq, UnsignedDecimal("124.01116798510935318752908329455560725919032107957189390414146114"))
        self.assertFloatingPointEqual(LLR.token_x_cumulative_earned_per_m_subtree_liq, UnsignedDecimal("152.36838839770435861641073367457732278579184116643400031022180859"))

        # (0-3)
        # N.borrowX = 0
        # N.subtreeBorrowX = (0-1).subtreeBorrowX + (2-3).subtreeBorrowX = 71.428571428571428571428571428571428571428571428571428571428571428 + 175.52380952380952380952380952380952380952380952380952380952380952 = 246.95238095238095238095238095238095238095238095238095238095238094
        # totalMLiq = 200*1 + 200*2 + 214*1 = 814
        # nodeEarnPerMLiqX += 0
        # nodeSubtreeEarnPerMLiqX += 246.95238095238095238095238095238095238095238095238095238095238094 * 9832114591287191011328 / 814 / 2**64 = 161.70223470223470223470223470223470223470223470223470223470223469
        self.assertFloatingPointEqual(LL.token_x_borrowed, UnsignedDecimal("0"))
        self.assertFloatingPointEqual(LL.token_x_subtree_borrowed, UnsignedDecimal("246.95238095238095238095238095238095238095238095238095238095238094"))
        self.assertFloatingPointEqual(LL.token_x_cumulative_earned_per_m_liq, UnsignedDecimal("0"))
        self.assertFloatingPointEqual(LL.token_x_cumulative_earned_per_m_subtree_liq, UnsignedDecimal("161.70223470223470223470223470223470223470223470223470223470223469"))

        # (4-7)
        # N.borrowX = 4 * 500 / 7 = 285.71428571428571428571428571428571428571428571428571428571428571
        # N.subtreeBorrowX = 4 * 500 / 7 + 2 * 98 / 3 = 351.04761904761904761904761904761904761904761904761904761904761904
        # totalMLiq = (4 * 200 + 214 * 2) + (0) * 4 = 1228
        # nodeEarnPerMLiqX += (4 * 500 / 7) * 9832114591287191011328 / 1228 / 2**64 = 124.01116798510935318752908329455560725919032107957189390414146114
        # nodeSubtreeEarnPerMLiqX += (4 * 500 / 7 + 2 * 98 / 3) * 9832114591287191011328 / 1228 / 2**64 = 152.36838839770435861641073367457732278579184116643400031022180859
        self.assertFloatingPointEqual(LR.token_x_borrowed, UnsignedDecimal("285.71428571428571428571428571428571428571428571428571428571428571"))
        self.assertFloatingPointEqual(LR.token_x_subtree_borrowed, UnsignedDecimal("351.04761904761904761904761904761904761904761904761904761904761904"))
        self.assertFloatingPointEqual(LLR.token_x_cumulative_earned_per_m_liq, UnsignedDecimal("124.01116798510935318752908329455560725919032107957189390414146114"))
        self.assertFloatingPointEqual(LLR.token_x_cumulative_earned_per_m_subtree_liq, UnsignedDecimal("152.36838839770435861641073367457732278579184116643400031022180859"))

        # (3-3)
        # N.borrowX = 1 * 98 / 3 = 32.666666666666666666666666666666666666666666666666666666666666666
        # N.subtreeBorrowX = 1 * 98 / 3 = 32.666666666666666666666666666666666666666666666666666666666666666
        # totalMLiq = 214 * 1 + (200) * 1 = 414
        # nodeEarnPerMLiqX += 1 * 98 / 3 * 9832114591287191011328 / 414 / 2**64 = 42.056360708534621578099838969404186795491143317230273752012882447
        # nodeSubtreeEarnPerMLiqX += 1 * 98 / 3 * 9832114591287191011328 / 41 = 42.056360708534621578099838969404186795491143317230273752012882447
        self.assertFloatingPointEqual(LLRR.token_x_borrowed, UnsignedDecimal("32.666666666666666666666666666666666666666666666666666666666666666"))
        self.assertFloatingPointEqual(LLRR.token_x_subtree_borrowed, UnsignedDecimal("32.666666666666666666666666666666666666666666666666666666666666666"))
        self.assertFloatingPointEqual(LLRR.token_x_cumulative_earned_per_m_liq, UnsignedDecimal("42.056360708534621578099838969404186795491143317230273752012882447"))
        self.assertFloatingPointEqual(LLRR.token_x_cumulative_earned_per_m_subtree_liq, UnsignedDecimal("42.056360708534621578099838969404186795491143317230273752012882447"))

        # (4-5)
        # N.borrowX = 2 * 98 / 3 = 65.333333333333333333333333333333333333333333333333333333333333333
        # N.subtreeBorrowX = 2 * 98 / 3 = 65.333333333333333333333333333333333333333333333333333333333333333
        # totalMLiq = 214 * 2 + (200) * 2 = 828
        # nodeEarnPerMLiqX += 2 * 98 / 3 * 9832114591287191011328 / 828 / 2**64 = 42.056360708534621578099838969404186795491143317230273752012882447
        # nodeSubtreeEarnPerMLiqX += 2 * 98 / 3 * 9832114591287191011328 / 828 / 2**64 = 42.056360708534621578099838969404186795491143317230273752012882447
        self.assertFloatingPointEqual(LRL.token_x_borrowed, UnsignedDecimal("65.333333333333333333333333333333333333333333333333333333333333333"))
        self.assertFloatingPointEqual(LRL.token_x_subtree_borrowed, UnsignedDecimal("65.333333333333333333333333333333333333333333333333333333333333333"))
        self.assertFloatingPointEqual(LLRR.token_x_cumulative_earned_per_m_liq, UnsignedDecimal("42.056360708534621578099838969404186795491143317230273752012882447"))
        self.assertFloatingPointEqual(LLRR.token_x_cumulative_earned_per_m_subtree_liq, UnsignedDecimal("42.056360708534621578099838969404186795491143317230273752012882447"))

        # Querying
        # Q(3-3)
        # acc_fee_rate_x = (3-3).nodeSubtreeEarnPerMLiqX + (2-3).nodeEarnPerMLiqX + (0-3).nodeEarnPerMLiqX + (0-7).nodeEarnPerMLiqX + (0-15).nodeEarnPerMLiqX
        #                = 42.056360708534621578099838969404186795491143317230273752012882447 + 124.01116798510935318752908329455560725919032107957189390414146114
        #                = 166.06752869364397476562892226395979405468146439680216765615434358
        (acc_fee_rate_x, _) = liq_tree.query_accumulated_fee_rates(LiqRange(3, 3))
        self.assertFloatingPointEqual(acc_fee_rate_x, UnsignedDecimal("166.06752869364397476562892226395979405468146439680216765615434358"))

        # Q(2-3)
        # acc_fee_rate_x = (2-3).nodeSubtreeEarnPerMLiqX = 152.36838839770435861641073367457732278579184116643400031022180859
        (acc_fee_rate_x, _) = liq_tree.query_accumulated_fee_rates(LiqRange(2, 3))
        self.assertFloatingPointEqual(acc_fee_rate_x, UnsignedDecimal("152.36838839770435861641073367457732278579184116643400031022180859"))

        # Q(5-7)
        # acc_fee_rate_x = (5-5).nodeSubtreeEarnPerMLiqX + (4-5).nodeEarnPerMLiqX + (6-7).nodeSubtreeEarnPerMLiqX + (4-7).nodeEarnPerMLiqX + (0-7).nodeEarnPerMLiqX + (0-15).nodeEarnPerMLiqX
        #                = 42.056360708534621578099838969404186795491143317230273752012882447 + 124.01116798510935318752908329455560725919032107957189390414146114
        #                = 166.06752869364397476562892226395979405468146439680216765615434358
        (acc_fee_rate_x, _) = liq_tree.query_accumulated_fee_rates(LiqRange(5, 7))
        self.assertFloatingPointEqual(acc_fee_rate_x, UnsignedDecimal("166.06752869364397476562892226395979405468146439680216765615434358"))

        # Q(4-7)
        # acc_fee_rate_x = (4-7).nodeSubtreeEarnPerMLiqX + (0-7).nodeEarnPerMLiqX + (0-15).nodeEarnPerMLiqX
        #                = 152.36838839770435861641073367457732278579184116643400031022180859
        (acc_fee_rate_x, _) = liq_tree.query_accumulated_fee_rates(LiqRange(4, 7))
        self.assertFloatingPointEqual(acc_fee_rate_x, UnsignedDecimal("152.36838839770435861641073367457732278579184116643400031022180859"))

        # Q(1-1)
        # acc_fee_rate_x = (1-1).nodeSubtreeEarnPerMLiqX = 190.35714285714285714285714285714285714285714285714285714285714285
        (acc_fee_rate_x, _) = liq_tree.query_accumulated_fee_rates(LiqRange(1, 1))
        self.assertFloatingPointEqual(acc_fee_rate_x, UnsignedDecimal("190.35714285714285714285714285714285714285714285714285714285714285"))

        # Q(0-0)
        # acc_fee_rate_x = (0-0).nodeSubtreeEarnPerMLiqX + (0-1).nodeEarnPerMLiqX + (0-2).nodeEarnPerMLiqX + (0-4).nodeEarnPerMLiqX + (0-7).nodeEarnPerMLiqX + (0-15).nodeEarnPerMLiqX
        #                = 0
        (acc_fee_rate_x, _) = liq_tree.query_accumulated_fee_rates(LiqRange(0, 0))
        self.assertFloatingPointEqual(acc_fee_rate_x, UnsignedDecimal("0"))

        # Q(0-1)
        # acc_fee_rate_x = (0-1).nodeSubtreeEarnPerMLiqX + (0-2).nodeEarnPerMLiqX + (0-4).nodeEarnPerMLiqX + (0-7).nodeEarnPerMLiqX + (0-15).nodeEarnPerMLiqX
        #                = 190.35714285714285714285714285714285714285714285714285714285714285
        (acc_fee_rate_x, _) = liq_tree.query_accumulated_fee_rates(LiqRange(0, 1))
        self.assertFloatingPointEqual(acc_fee_rate_x, UnsignedDecimal("190.35714285714285714285714285714285714285714285714285714285714285"))

        # Q(0-3)
        # acc_fee_rate_x = (0-3).nodeSubtreeEarnPerMLiqX + (0-7).nodeEarnPerMLiqX + (0-15).nodeEarnPerMLiqX
        #                = 161.70223470223470223470223470223470223470223470223470223470223469
        (acc_fee_rate_x, _) = liq_tree.query_accumulated_fee_rates(LiqRange(0, 3))
        self.assertFloatingPointEqual(acc_fee_rate_x, UnsignedDecimal("161.70223470223470223470223470223470223470223470223470223470223469"))

        # Q(1-7)
        # acc_fee_rate_x = (1-1).nodeSubtreeEarnPerMLiqX + (0-1).nodeEarnPerMLiqX + (0-3).nodeEarnPerMLiqX + (2-3).nodeSubtreeEarnPerMLiqX + (4-7).nodeSubtreeEarnPerMLiqX + (0-7).nodeEarnPerMLiqX + (0-15).nodeEarnPerMLiqX
        #                = 190.35714285714285714285714285714285714285714285714285714285714285 + 152.36838839770435861641073367457732278579184116643400031022180859 + 152.36838839770435861641073367457732278579184116643400031022180859
        #                = 495.09391965255157437567861020629750271444082519001085745307895143
        (acc_fee_rate_x, _) = liq_tree.query_accumulated_fee_rates(LiqRange(1, 7))
        self.assertFloatingPointEqual(acc_fee_rate_x, UnsignedDecimal("495.09391965255157437567861020629750271444082519001085745307895143"))

    def test_root_only(self):
        liq_tree: LiquidityTree = self.liq_tree

        # T0
        liq_tree.add_wide_m_liq(Decimal("8430"))
        liq_tree.add_wide_t_liq(Decimal("4381"), UnsignedDecimal("832e18"), UnsignedDecimal("928e6"))
        self.assertEqual(True, True)

        # T3600 (1hr) --- 5.4% APR as Q192.64
        liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("113712805933826")  # 0.054 * 3600 / (365 * 24 * 60 * 60) * 2^64
        liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("113712805933826")

        # Verify root state
        root: LiqNode = liq_tree.root
        self.assertEqual(root.m_liq, UnsignedDecimal("8430"))                              #
        self.assertEqual(root.subtree_m_liq, UnsignedDecimal("134880"))                    #
        self.assertEqual(root.t_liq, UnsignedDecimal("4381"))                              #
        self.assertEqual(root.token_x_borrowed, UnsignedDecimal("832e18"))            #
        self.assertEqual(root.token_x_subtree_borrowed, UnsignedDecimal("832e18"))    #
        self.assertEqual(root.token_y_borrowed, UnsignedDecimal("928e6"))             #
        self.assertEqual(root.token_y_subtree_borrowed, UnsignedDecimal("928e6"))     #

        # Testing 4 methods for proper fee accumulation:
        # add_wide_m_liq, remove_wide_m_liq
        # add_wide_t_liq, remove_wide_t_liq
        liq_tree.add_wide_m_liq(Decimal("9287"))

        self.assertEqual(int(root.token_x_cumulative_earned_per_m_liq), UnsignedDecimal("38024667284"))
        self.assertEqual(int(root.token_x_cumulative_earned_per_m_subtree_liq), UnsignedDecimal("38024667284"))
        self.assertEqual(int(root.token_y_cumulative_earned_per_m_liq), UnsignedDecimal("0"))
        self.assertEqual(int(root.token_y_cumulative_earned_per_m_subtree_liq), UnsignedDecimal("0"))

        self.assertEqual(root.m_liq, UnsignedDecimal("17717"))
        self.assertEqual(root.subtree_m_liq, UnsignedDecimal("283472"))
        self.assertEqual(root.t_liq, UnsignedDecimal("4381"))
        self.assertEqual(root.token_x_borrowed, UnsignedDecimal("832e18"))
        self.assertEqual(root.token_x_subtree_borrowed, UnsignedDecimal("832e18"))
        self.assertEqual(root.token_y_borrowed, UnsignedDecimal("928e6"))
        self.assertEqual(root.token_y_subtree_borrowed, UnsignedDecimal("928e6"))

        # T22000 -- 693792000.0% APR as Q192.64 from T22000 - T3600
        liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("74672420010376264941568")   # Q192.64 - 1377463021295958900099740410883797719973888
        liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("74672420010376264941568")   # Q192.64 - 1377463021295958900099740410883797719973888

        liq_tree.remove_wide_m_liq(Decimal("3682"))

        # rounding error
        self.assertEqual(int(root.token_x_cumulative_earned_per_m_liq), UnsignedDecimal("11881018269102163474"))
        self.assertEqual(int(root.token_x_cumulative_earned_per_m_subtree_liq), UnsignedDecimal("11881018269102163474"))
        self.assertEqual(int(root.token_y_cumulative_earned_per_m_liq), UnsignedDecimal("13251904"))
        self.assertEqual(int(root.token_y_cumulative_earned_per_m_subtree_liq), UnsignedDecimal("13251904"))

        self.assertEqual(root.m_liq, UnsignedDecimal("14035"))
        self.assertEqual(root.subtree_m_liq, UnsignedDecimal("224560"))
        self.assertEqual(root.t_liq, UnsignedDecimal("4381"))
        self.assertEqual(root.token_x_borrowed, UnsignedDecimal("832e18"))
        self.assertEqual(root.token_x_subtree_borrowed, UnsignedDecimal("832e18"))
        self.assertEqual(root.token_y_borrowed, UnsignedDecimal("928e6"))
        self.assertEqual(root.token_y_subtree_borrowed, UnsignedDecimal("928e6"))

        # T37002 --- 7.9% APR as Q192.64 T37002 - T22000
        liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("6932491854677024")  # Q192.64 - 127881903036303130599671671537270784
        liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("6932491854677024")  # Q192.64 - 127881903036303130599671671537270784

        liq_tree.add_wide_t_liq(Decimal("7287"), UnsignedDecimal("9184e18"), UnsignedDecimal("7926920e6"))

        # rounding error
        self.assertEqual(int(root.token_x_cumulative_earned_per_m_liq), UnsignedDecimal("11881019661491126559"))
        self.assertEqual(int(root.token_x_cumulative_earned_per_m_subtree_liq), UnsignedDecimal("11881019661491126559"))
        self.assertEqual(int(root.token_y_cumulative_earned_per_m_liq), UnsignedDecimal("13251906"))
        self.assertEqual(int(root.token_y_cumulative_earned_per_m_subtree_liq), UnsignedDecimal("13251906"))

        self.assertEqual(root.m_liq, UnsignedDecimal("14035"))
        self.assertEqual(root.subtree_m_liq, UnsignedDecimal("224560"))
        self.assertEqual(root.t_liq, UnsignedDecimal("11668"))
        self.assertEqual(root.token_x_borrowed, UnsignedDecimal("10016e18"))
        self.assertEqual(root.token_x_subtree_borrowed, UnsignedDecimal("10016e18"))
        self.assertEqual(root.token_y_borrowed, UnsignedDecimal("7927848e6"))
        self.assertEqual(root.token_y_subtree_borrowed, UnsignedDecimal("7927848e6"))

        # T57212 --- 11.1% APR as Q192.64 TT57212 - T37002
        liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("1055375100301031600000000")     # Q192.64 - 19468234377018678290990465858247065600000000
        liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("1055375100301031600000000")     # Q192.64 - 19468234377018678290990465858247065600000000

        liq_tree.remove_wide_t_liq(Decimal("4923"), UnsignedDecimal("222e18"), UnsignedDecimal("786e6"))

        self.assertEqual(int(root.token_x_cumulative_earned_per_m_liq), UnsignedDecimal("2563695146166521368513"))
        self.assertEqual(int(root.token_x_cumulative_earned_per_m_subtree_liq), UnsignedDecimal("2563695146166521368513"))
        self.assertEqual(int(root.token_y_cumulative_earned_per_m_liq), UnsignedDecimal("2019821011409"))
        self.assertEqual(int(root.token_y_cumulative_earned_per_m_subtree_liq), UnsignedDecimal("2019821011409"))

        self.assertEqual(root.m_liq, UnsignedDecimal("14035"))
        self.assertEqual(root.subtree_m_liq, UnsignedDecimal("224560"))
        self.assertEqual(root.t_liq, UnsignedDecimal("6745"))
        self.assertEqual(root.token_x_borrowed, UnsignedDecimal("9794e18"))
        self.assertEqual(root.token_x_subtree_borrowed, UnsignedDecimal("9794e18"))
        self.assertEqual(root.token_y_borrowed, UnsignedDecimal("7927062e6"))
        self.assertEqual(root.token_y_subtree_borrowed, UnsignedDecimal("7927062e6"))

    def test_left_leg_only(self):
        # Mirrors test_right_leg_only
        # Manual calculations are shown there.

        liq_tree: LiquidityTree = self.liq_tree

        root: LiqNode = liq_tree.root
        L: LiqNode = liq_tree.nodes[(8 << 24) | 16]     # 134217744
        LL: LiqNode = liq_tree.nodes[(4 << 24) | 16]    # 67108880
        LR: LiqNode = liq_tree.nodes[(4 << 24) | 20]    # 67108884
        LLR: LiqNode = liq_tree.nodes[(2 << 24) | 18]   # 33554450
        LLRR: LiqNode = liq_tree.nodes[(1 << 24) | 19]  # 16777235

        # T0 - populate tree with data excluding fee calculations
        liq_tree.add_wide_m_liq(Decimal("8430"))                       # root
        liq_tree.add_m_liq(LiqRange(low=0, high=7), UnsignedDecimal("377"))         # L
        liq_tree.add_m_liq(LiqRange(low=0, high=3), UnsignedDecimal("9082734"))     # LL
        liq_tree.add_m_liq(LiqRange(low=4, high=7), UnsignedDecimal("1111"))        # LR
        liq_tree.add_m_liq(LiqRange(low=2, high=3), UnsignedDecimal("45346"))       # LLR
        liq_tree.add_m_liq(LiqRange(low=3, high=3), UnsignedDecimal("287634865"))   # LLRR

        liq_tree.add_wide_t_liq(Decimal("4430"), UnsignedDecimal("492e18"), UnsignedDecimal("254858e6"))                       # root
        liq_tree.add_t_liq(LiqRange(low=0, high=7), UnsignedDecimal("77"), UnsignedDecimal("998e18"), UnsignedDecimal("353e6"))             # L
        liq_tree.add_t_liq(LiqRange(low=0, high=3), UnsignedDecimal("82734"), UnsignedDecimal("765e18"), UnsignedDecimal("99763e6"))        # LL
        liq_tree.add_t_liq(LiqRange(low=4, high=7), UnsignedDecimal("111"), UnsignedDecimal("24e18"), UnsignedDecimal("552e6"))             # LR
        liq_tree.add_t_liq(LiqRange(low=2, high=3), UnsignedDecimal("5346"), UnsignedDecimal("53e18"), UnsignedDecimal("8765e6"))           # LLR
        liq_tree.add_t_liq(LiqRange(low=3, high=3), UnsignedDecimal("7634865"), UnsignedDecimal("701e18"), UnsignedDecimal("779531e6"))     # LLRR

        # m_liq
        self.assertEqual(root.m_liq, UnsignedDecimal("8430"))
        self.assertEqual(L.m_liq, UnsignedDecimal("377"))
        self.assertEqual(LL.m_liq, UnsignedDecimal("9082734"))
        self.assertEqual(LR.m_liq, UnsignedDecimal("1111"))
        self.assertEqual(LLR.m_liq, UnsignedDecimal("45346"))
        self.assertEqual(LLRR.m_liq, UnsignedDecimal("287634865"))

        # t_liq
        self.assertEqual(root.t_liq, UnsignedDecimal("4430"))
        self.assertEqual(L.t_liq, UnsignedDecimal("77"))
        self.assertEqual(LL.t_liq, UnsignedDecimal("82734"))
        self.assertEqual(LR.t_liq, UnsignedDecimal("111"))
        self.assertEqual(LLR.t_liq, UnsignedDecimal("5346"))
        self.assertEqual(LLRR.t_liq, UnsignedDecimal("7634865"))

        # subtree_m_liq
        self.assertEqual(root.subtree_m_liq, UnsignedDecimal("324198833"))
        self.assertEqual(L.subtree_m_liq, UnsignedDecimal("324063953"))
        self.assertEqual(LL.subtree_m_liq, UnsignedDecimal("324056493"))
        self.assertEqual(LR.subtree_m_liq, UnsignedDecimal("4444"))
        self.assertEqual(LLR.subtree_m_liq, UnsignedDecimal("287725557"))
        self.assertEqual(LLRR.subtree_m_liq, UnsignedDecimal("287634865"))

        # borrowed_x
        self.assertEqual(root.token_x_borrowed, UnsignedDecimal("492e18"))
        self.assertEqual(L.token_x_borrowed, UnsignedDecimal("998e18"))
        self.assertEqual(LL.token_x_borrowed, UnsignedDecimal("765e18"))
        self.assertEqual(LR.token_x_borrowed, UnsignedDecimal("24e18"))
        self.assertEqual(LLR.token_x_borrowed, UnsignedDecimal("53e18"))
        self.assertEqual(LLRR.token_x_borrowed, UnsignedDecimal("701e18"))

        # subtree_borrowed_x
        self.assertEqual(root.token_x_subtree_borrowed, UnsignedDecimal("3033e18"))
        self.assertEqual(L.token_x_subtree_borrowed, UnsignedDecimal("2541e18"))
        self.assertEqual(LL.token_x_subtree_borrowed, UnsignedDecimal("1519e18"))
        self.assertEqual(LR.token_x_subtree_borrowed, UnsignedDecimal("24e18"))
        self.assertEqual(LLR.token_x_subtree_borrowed, UnsignedDecimal("754e18"))
        self.assertEqual(LLRR.token_x_subtree_borrowed, UnsignedDecimal("701e18"))

        # borrowed_y
        self.assertEqual(root.token_y_borrowed, UnsignedDecimal("254858e6"))
        self.assertEqual(L.token_y_borrowed, UnsignedDecimal("353e6"))
        self.assertEqual(LL.token_y_borrowed, UnsignedDecimal("99763e6"))
        self.assertEqual(LR.token_y_borrowed, UnsignedDecimal("552e6"))
        self.assertEqual(LLR.token_y_borrowed, UnsignedDecimal("8765e6"))
        self.assertEqual(LLRR.token_y_borrowed, UnsignedDecimal("779531e6"))

        # subtree_borrowed_y
        self.assertEqual(root.token_y_subtree_borrowed, UnsignedDecimal("1143822e6"))
        self.assertEqual(L.token_y_subtree_borrowed, UnsignedDecimal("888964e6"))
        self.assertEqual(LL.token_y_subtree_borrowed, UnsignedDecimal("888059e6"))
        self.assertEqual(LR.token_y_subtree_borrowed, UnsignedDecimal("552e6"))
        self.assertEqual(LLR.token_y_subtree_borrowed, UnsignedDecimal("788296e6"))
        self.assertEqual(LLRR.token_y_subtree_borrowed, UnsignedDecimal("779531e6"))

        # T98273
        liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("4541239648278065")
        liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("13278814667749784")

        # Apply change that requires fee calculation
        # add_m_liq
        liq_tree.add_m_liq(LiqRange(low=3, high=7), UnsignedDecimal("2734"))  # LLRR, LR

        # root
        self.assertEqual(int(root.token_x_cumulative_earned_per_m_liq), UnsignedDecimal("373601278"))
        self.assertEqual(int(root.token_x_cumulative_earned_per_m_subtree_liq), UnsignedDecimal("2303115199"))
        self.assertEqual(int(root.token_y_cumulative_earned_per_m_liq), UnsignedDecimal("0"))
        self.assertEqual(int(root.token_y_cumulative_earned_per_m_subtree_liq), UnsignedDecimal("2"))

        # L
        self.assertEqual(int(L.token_x_cumulative_earned_per_m_liq), UnsignedDecimal("757991165"))
        self.assertEqual(int(L.token_x_cumulative_earned_per_m_subtree_liq), UnsignedDecimal("1929915382"))
        self.assertEqual(int(L.token_y_cumulative_earned_per_m_liq), UnsignedDecimal("0"))
        self.assertEqual(int(L.token_y_cumulative_earned_per_m_subtree_liq), UnsignedDecimal("1"))

        # LL
        self.assertEqual(int(LL.token_x_cumulative_earned_per_m_liq), UnsignedDecimal("581096415"))
        self.assertEqual(int(LL.token_x_cumulative_earned_per_m_subtree_liq), UnsignedDecimal("1153837196"))
        self.assertEqual(int(LL.token_y_cumulative_earned_per_m_liq), UnsignedDecimal("0"))
        self.assertEqual(int(LL.token_y_cumulative_earned_per_m_subtree_liq), UnsignedDecimal("1"))

        # LR
        self.assertEqual(int(LR.token_x_cumulative_earned_per_m_liq), UnsignedDecimal("148929881804"))
        self.assertEqual(int(LR.token_x_cumulative_earned_per_m_subtree_liq), UnsignedDecimal("148929881804"))
        self.assertEqual(int(LR.token_y_cumulative_earned_per_m_liq), UnsignedDecimal("10"))
        self.assertEqual(int(LR.token_y_cumulative_earned_per_m_subtree_liq), UnsignedDecimal("10"))

        # LLR
        self.assertEqual(int(LLR.token_x_cumulative_earned_per_m_liq), UnsignedDecimal("42651943"))
        self.assertEqual(int(LLR.token_x_cumulative_earned_per_m_subtree_liq), UnsignedDecimal("606784254"))
        self.assertEqual(int(LLR.token_y_cumulative_earned_per_m_liq), UnsignedDecimal("0"))
        self.assertEqual(int(LLR.token_y_cumulative_earned_per_m_subtree_liq), UnsignedDecimal("1"))

        # LLRR
        self.assertEqual(int(LLRR.token_x_cumulative_earned_per_m_liq), UnsignedDecimal("581500584"))
        self.assertEqual(int(LLRR.token_x_cumulative_earned_per_m_subtree_liq), UnsignedDecimal("581500584"))
        self.assertEqual(int(LLRR.token_y_cumulative_earned_per_m_liq), UnsignedDecimal("1"))
        self.assertEqual(int(LLRR.token_y_cumulative_earned_per_m_subtree_liq), UnsignedDecimal("1"))

        # m_liq
        self.assertEqual(root.m_liq, UnsignedDecimal("8430"))
        self.assertEqual(L.m_liq, UnsignedDecimal("377"))
        self.assertEqual(LL.m_liq, UnsignedDecimal("9082734"))
        self.assertEqual(LR.m_liq, UnsignedDecimal("3845"))
        self.assertEqual(LLR.m_liq, UnsignedDecimal("45346"))
        self.assertEqual(LLRR.m_liq, UnsignedDecimal("287637599"))

        # subtree_m_liq
        self.assertEqual(root.subtree_m_liq, UnsignedDecimal("324212503"))
        self.assertEqual(L.subtree_m_liq, UnsignedDecimal("324077623"))
        self.assertEqual(LL.subtree_m_liq, UnsignedDecimal("324059227"))
        self.assertEqual(LR.subtree_m_liq, UnsignedDecimal("15380"))
        self.assertEqual(LLR.subtree_m_liq, UnsignedDecimal("287728291"))
        self.assertEqual(LLRR.subtree_m_liq, UnsignedDecimal("287637599"))

        # T2876298273
        liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("16463537718422861220174597")
        liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("3715979586694123491881712207")

        # Apply change that requires fee calculation
        # remove_m_liq
        liq_tree.remove_m_liq(LiqRange(low=3, high=7), UnsignedDecimal("2734"))  # LLRR, LR

        # root
        self.assertEqual(int(root.token_x_cumulative_earned_per_m_liq), UnsignedDecimal("1354374549844117328"))
        self.assertEqual(int(root.token_x_cumulative_earned_per_m_subtree_liq), UnsignedDecimal("8349223596904894021"))
        self.assertEqual(int(root.token_y_cumulative_earned_per_m_liq), UnsignedDecimal("158351473404"))
        self.assertEqual(int(root.token_y_cumulative_earned_per_m_subtree_liq), UnsignedDecimal("710693401864"))

        # L
        self.assertEqual(int(L.token_x_cumulative_earned_per_m_liq), UnsignedDecimal("2747859799935140578"))
        self.assertEqual(int(L.token_x_cumulative_earned_per_m_subtree_liq), UnsignedDecimal("6996304360355904017"))
        self.assertEqual(int(L.token_y_cumulative_earned_per_m_liq), UnsignedDecimal("219375887"))
        self.assertEqual(int(L.token_y_cumulative_earned_per_m_subtree_liq), UnsignedDecimal("552456845957"))

        # LL
        self.assertEqual(int(LL.token_x_cumulative_earned_per_m_liq), UnsignedDecimal("2106654304686669588"))
        self.assertEqual(int(LL.token_x_cumulative_earned_per_m_subtree_liq), UnsignedDecimal("4183016848129478568"))
        self.assertEqual(int(LL.token_y_cumulative_earned_per_m_liq), UnsignedDecimal("62008538706"))
        self.assertEqual(int(LL.token_y_cumulative_earned_per_m_subtree_liq), UnsignedDecimal("551980602778"))

        # LR
        self.assertEqual(int(LR.token_x_cumulative_earned_per_m_liq), UnsignedDecimal("423248578107618890129"))
        self.assertEqual(int(LR.token_x_cumulative_earned_per_m_subtree_liq), UnsignedDecimal("423248578107618890129"))
        self.assertEqual(int(LR.token_y_cumulative_earned_per_m_liq), UnsignedDecimal("2197219781195"))
        self.assertEqual(int(LR.token_y_cumulative_earned_per_m_subtree_liq), UnsignedDecimal("2197219781195"))

        # LLR
        self.assertEqual(int(LLR.token_x_cumulative_earned_per_m_liq), UnsignedDecimal("154626415017241477"))
        self.assertEqual(int(LLR.token_x_cumulative_earned_per_m_subtree_liq), UnsignedDecimal("2199779564584907057"))
        self.assertEqual(int(LLR.token_y_cumulative_earned_per_m_liq), UnsignedDecimal("5771781665"))
        self.assertEqual(int(LLR.token_y_cumulative_earned_per_m_subtree_liq), UnsignedDecimal("519095539055"))

        # LLRR
        self.assertEqual(int(LLRR.token_x_cumulative_earned_per_m_liq), UnsignedDecimal("2108117905996538333"))
        self.assertEqual(int(LLRR.token_x_cumulative_earned_per_m_subtree_liq), UnsignedDecimal("2108117905996538333"))
        self.assertEqual(int(LLRR.token_y_cumulative_earned_per_m_liq), UnsignedDecimal("529127613135"))
        self.assertEqual(int(LLRR.token_y_cumulative_earned_per_m_subtree_liq), UnsignedDecimal("529127613135"))

        # m_liq
        self.assertEqual(root.m_liq, UnsignedDecimal("8430"))
        self.assertEqual(L.m_liq, UnsignedDecimal("377"))
        self.assertEqual(LL.m_liq, UnsignedDecimal("9082734"))
        self.assertEqual(LR.m_liq, UnsignedDecimal("1111"))
        self.assertEqual(LLR.m_liq, UnsignedDecimal("45346"))
        self.assertEqual(LLRR.m_liq, UnsignedDecimal("287634865"))

        # subtree_m_liq
        self.assertEqual(root.subtree_m_liq, UnsignedDecimal("324198833"))
        self.assertEqual(L.subtree_m_liq, UnsignedDecimal("324063953"))
        self.assertEqual(LL.subtree_m_liq, UnsignedDecimal("324056493"))
        self.assertEqual(LR.subtree_m_liq, UnsignedDecimal("4444"))
        self.assertEqual(LLR.subtree_m_liq, UnsignedDecimal("287725557"))
        self.assertEqual(LLRR.subtree_m_liq, UnsignedDecimal("287634865"))

        # T9214298113
        liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("11381610389149375791104")
        liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("185394198934916215865344")

        # Apply change that requires fee calculation
        # add_t_liq
        liq_tree.add_t_liq(LiqRange(low=3, high=7), UnsignedDecimal("1000"), UnsignedDecimal("1000e18"), UnsignedDecimal("1000e6"))  # LLRR, LR

        # root
        self.assertEqual(int(root.token_x_cumulative_earned_per_m_liq), UnsignedDecimal("1355310898622008715"))
        self.assertEqual(int(root.token_x_cumulative_earned_per_m_subtree_liq), UnsignedDecimal("8354995844553968362"))
        self.assertEqual(int(root.token_y_cumulative_earned_per_m_liq), UnsignedDecimal("158359374061"))
        self.assertEqual(int(root.token_y_cumulative_earned_per_m_subtree_liq), UnsignedDecimal("710728860613"))

        # L
        self.assertEqual(int(L.token_x_cumulative_earned_per_m_liq), UnsignedDecimal("2749759536746020655"))
        self.assertEqual(int(L.token_x_cumulative_earned_per_m_subtree_liq), UnsignedDecimal("7001141265402443372"))
        self.assertEqual(int(L.token_y_cumulative_earned_per_m_liq), UnsignedDecimal("219386833"))
        self.assertEqual(int(L.token_y_cumulative_earned_per_m_subtree_liq), UnsignedDecimal("552484409783"))

        # LL
        self.assertEqual(int(LL.token_x_cumulative_earned_per_m_liq), UnsignedDecimal("2108110694023652836"))
        self.assertEqual(int(LL.token_x_cumulative_earned_per_m_subtree_liq), UnsignedDecimal("4185908685257423083"))
        self.assertEqual(int(LL.token_y_cumulative_earned_per_m_liq), UnsignedDecimal("62011632404"))
        self.assertEqual(int(LL.token_y_cumulative_earned_per_m_subtree_liq), UnsignedDecimal("552008141914"))

        # LR
        self.assertEqual(int(LR.token_x_cumulative_earned_per_m_liq), UnsignedDecimal("423621837838722923425"))
        self.assertEqual(int(LR.token_x_cumulative_earned_per_m_subtree_liq), UnsignedDecimal("423621837838722923425"))
        self.assertEqual(int(LR.token_y_cumulative_earned_per_m_liq), UnsignedDecimal("2197359621190"))
        self.assertEqual(int(LR.token_y_cumulative_earned_per_m_subtree_liq), UnsignedDecimal("2197359621190"))

        # LLR
        self.assertEqual(int(LLR.token_x_cumulative_earned_per_m_liq), UnsignedDecimal("154733312657952739"))
        self.assertEqual(int(LLR.token_x_cumulative_earned_per_m_subtree_liq), UnsignedDecimal("2201300334794271054"))
        self.assertEqual(int(LLR.token_y_cumulative_earned_per_m_liq), UnsignedDecimal("5772069628"))
        self.assertEqual(int(LLR.token_y_cumulative_earned_per_m_subtree_liq), UnsignedDecimal("519121437519"))

        # LLRR
        self.assertEqual(int(LLRR.token_x_cumulative_earned_per_m_liq), UnsignedDecimal("2109575308294031902"))
        self.assertEqual(int(LLRR.token_x_cumulative_earned_per_m_subtree_liq), UnsignedDecimal("2109575308294031902"))
        self.assertEqual(int(LLRR.token_y_cumulative_earned_per_m_liq), UnsignedDecimal("529154012122"))
        self.assertEqual(int(LLRR.token_y_cumulative_earned_per_m_subtree_liq), UnsignedDecimal("529154012122"))

        # t_liq
        self.assertEqual(root.t_liq, UnsignedDecimal("4430"))
        self.assertEqual(L.t_liq, UnsignedDecimal("77"))
        self.assertEqual(LL.t_liq, UnsignedDecimal("82734"))
        self.assertEqual(LR.t_liq, UnsignedDecimal("1111"))
        self.assertEqual(LLR.t_liq, UnsignedDecimal("5346"))
        self.assertEqual(LLRR.t_liq, UnsignedDecimal("7635865"))

        # borrowed_x
        self.assertEqual(root.token_x_borrowed, UnsignedDecimal("492e18"))
        self.assertEqual(L.token_x_borrowed, UnsignedDecimal("998e18"))
        self.assertEqual(LL.token_x_borrowed, UnsignedDecimal("765e18"))
        self.assertEqual(LR.token_x_borrowed, UnsignedDecimal("1024e18"))
        self.assertEqual(LLR.token_x_borrowed, UnsignedDecimal("53e18"))
        self.assertEqual(LLRR.token_x_borrowed, UnsignedDecimal("1701e18"))

        # subtree_borrowed_x
        self.assertEqual(root.token_x_subtree_borrowed, UnsignedDecimal("5033e18"))
        self.assertEqual(L.token_x_subtree_borrowed, UnsignedDecimal("4541e18"))
        self.assertEqual(LL.token_x_subtree_borrowed, UnsignedDecimal("2519e18"))
        self.assertEqual(LR.token_x_subtree_borrowed, UnsignedDecimal("1024e18"))
        self.assertEqual(LLR.token_x_subtree_borrowed, UnsignedDecimal("1754e18"))
        self.assertEqual(LLRR.token_x_subtree_borrowed, UnsignedDecimal("1701e18"))

        # borrowed_y
        self.assertEqual(root.token_y_borrowed, UnsignedDecimal("254858e6"))
        self.assertEqual(L.token_y_borrowed, UnsignedDecimal("353e6"))
        self.assertEqual(LL.token_y_borrowed, UnsignedDecimal("99763e6"))
        self.assertEqual(LR.token_y_borrowed, UnsignedDecimal("1552e6"))
        self.assertEqual(LLR.token_y_borrowed, UnsignedDecimal("8765e6"))
        self.assertEqual(LLRR.token_y_borrowed, UnsignedDecimal("780531e6"))

        # subtree_borrowed_y
        self.assertEqual(root.token_y_subtree_borrowed, UnsignedDecimal("1145822e6"))
        self.assertEqual(L.token_y_subtree_borrowed, UnsignedDecimal("890964e6"))
        self.assertEqual(LL.token_y_subtree_borrowed, UnsignedDecimal("889059e6"))
        self.assertEqual(LR.token_y_subtree_borrowed, UnsignedDecimal("1552e6"))
        self.assertEqual(LLR.token_y_subtree_borrowed, UnsignedDecimal("789296e6"))
        self.assertEqual(LLRR.token_y_subtree_borrowed, UnsignedDecimal("780531e6"))

        # T32876298273
        # 3.3) addTLiq
        liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("2352954287417905205553")
        liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("6117681147286553534438")

        # Apply change that requires fee calculation
        # add_t_liq
        liq_tree.remove_t_liq(LiqRange(low=3, high=7), UnsignedDecimal("1000"), UnsignedDecimal("1000e18"), UnsignedDecimal("1000e6"))  # LLRR, LR

        # root
        self.assertEqual(int(root.token_x_cumulative_earned_per_m_liq), UnsignedDecimal("1355504472799662736"))
        self.assertEqual(int(root.token_x_cumulative_earned_per_m_subtree_liq), UnsignedDecimal("8356976045440416916"))
        self.assertEqual(int(root.token_y_cumulative_earned_per_m_liq), UnsignedDecimal("158359634769"))
        self.assertEqual(int(root.token_y_cumulative_earned_per_m_subtree_liq), UnsignedDecimal("710730032735"))

        # L
        self.assertEqual(int(L.token_x_cumulative_earned_per_m_liq), UnsignedDecimal("2750152275007241348"))
        self.assertEqual(int(L.token_x_cumulative_earned_per_m_subtree_liq), UnsignedDecimal("7002928263843528708"))
        self.assertEqual(int(L.token_y_cumulative_earned_per_m_liq), UnsignedDecimal("219387194"))
        self.assertEqual(int(L.token_y_cumulative_earned_per_m_subtree_liq), UnsignedDecimal("552485321387"))

        # LL
        self.assertEqual(int(LL.token_x_cumulative_earned_per_m_liq), UnsignedDecimal("2108411777738297593"))
        self.assertEqual(int(LL.token_x_cumulative_earned_per_m_subtree_liq), UnsignedDecimal("4186900096861593205"))
        self.assertEqual(int(LL.token_y_cumulative_earned_per_m_liq), UnsignedDecimal("62011734491"))
        self.assertEqual(int(LL.token_y_cumulative_earned_per_m_subtree_liq), UnsignedDecimal("552009051680"))

        # LR
        self.assertEqual(int(LR.token_x_cumulative_earned_per_m_liq), UnsignedDecimal("426914215366679462837"))
        self.assertEqual(int(LR.token_x_cumulative_earned_per_m_subtree_liq), UnsignedDecimal("426914215366679462837"))
        self.assertEqual(int(LR.token_y_cumulative_earned_per_m_liq), UnsignedDecimal("2197372595215"))
        self.assertEqual(int(LR.token_y_cumulative_earned_per_m_subtree_liq), UnsignedDecimal("2197372595215"))

        # LLR
        self.assertEqual(int(LLR.token_x_cumulative_earned_per_m_liq), UnsignedDecimal("154755411926283539"))
        self.assertEqual(int(LLR.token_x_cumulative_earned_per_m_subtree_liq), UnsignedDecimal("2202031695485822407"))
        self.assertEqual(int(LLR.token_y_cumulative_earned_per_m_liq), UnsignedDecimal("5772079130"))
        self.assertEqual(int(LLR.token_y_cumulative_earned_per_m_subtree_liq), UnsignedDecimal("519122293207"))

        # LLRR
        self.assertEqual(int(LLRR.token_x_cumulative_earned_per_m_liq), UnsignedDecimal("2110306406167095653"))
        self.assertEqual(int(LLRR.token_x_cumulative_earned_per_m_subtree_liq), UnsignedDecimal("2110306406167095653"))
        self.assertEqual(int(LLRR.token_y_cumulative_earned_per_m_liq), UnsignedDecimal("529154884359"))
        self.assertEqual(int(LLRR.token_y_cumulative_earned_per_m_subtree_liq), UnsignedDecimal("529154884359"))

        # t_liq
        self.assertEqual(root.t_liq, UnsignedDecimal("4430"))
        self.assertEqual(L.t_liq, UnsignedDecimal("77"))
        self.assertEqual(LL.t_liq, UnsignedDecimal("82734"))
        self.assertEqual(LR.t_liq, UnsignedDecimal("111"))
        self.assertEqual(LLR.t_liq, UnsignedDecimal("5346"))
        self.assertEqual(LLRR.t_liq, UnsignedDecimal("7634865"))

        # subtree_m_liq
        self.assertEqual(root.subtree_m_liq, UnsignedDecimal("324198833"))
        self.assertEqual(L.subtree_m_liq, UnsignedDecimal("324063953"))
        self.assertEqual(LL.subtree_m_liq, UnsignedDecimal("324056493"))
        self.assertEqual(LR.subtree_m_liq, UnsignedDecimal("4444"))
        self.assertEqual(LLR.subtree_m_liq, UnsignedDecimal("287725557"))
        self.assertEqual(LLRR.subtree_m_liq, UnsignedDecimal("287634865"))

        # borrowed_x
        self.assertEqual(root.token_x_borrowed, UnsignedDecimal("492e18"))
        self.assertEqual(L.token_x_borrowed, UnsignedDecimal("998e18"))
        self.assertEqual(LL.token_x_borrowed, UnsignedDecimal("765e18"))
        self.assertEqual(LR.token_x_borrowed, UnsignedDecimal("24e18"))
        self.assertEqual(LLR.token_x_borrowed, UnsignedDecimal("53e18"))
        self.assertEqual(LLRR.token_x_borrowed, UnsignedDecimal("701e18"))

        # subtree_borrowed_x
        self.assertEqual(root.token_x_subtree_borrowed, UnsignedDecimal("3033e18"))
        self.assertEqual(L.token_x_subtree_borrowed, UnsignedDecimal("2541e18"))
        self.assertEqual(LL.token_x_subtree_borrowed, UnsignedDecimal("1519e18"))
        self.assertEqual(LR.token_x_subtree_borrowed, UnsignedDecimal("24e18"))
        self.assertEqual(LLR.token_x_subtree_borrowed, UnsignedDecimal("754e18"))
        self.assertEqual(LLRR.token_x_subtree_borrowed, UnsignedDecimal("701e18"))

        # borrowed_y
        self.assertEqual(root.token_y_borrowed, UnsignedDecimal("254858e6"))
        self.assertEqual(L.token_y_borrowed, UnsignedDecimal("353e6"))
        self.assertEqual(LL.token_y_borrowed, UnsignedDecimal("99763e6"))
        self.assertEqual(LR.token_y_borrowed, UnsignedDecimal("552e6"))
        self.assertEqual(LLR.token_y_borrowed, UnsignedDecimal("8765e6"))
        self.assertEqual(LLRR.token_y_borrowed, UnsignedDecimal("779531e6"))

        # subtree_borrowed_y
        self.assertEqual(root.token_y_subtree_borrowed, UnsignedDecimal("1143822e6"))
        self.assertEqual(L.token_y_subtree_borrowed, UnsignedDecimal("888964e6"))
        self.assertEqual(LL.token_y_subtree_borrowed, UnsignedDecimal("888059e6"))
        self.assertEqual(LR.token_y_subtree_borrowed, UnsignedDecimal("552e6"))
        self.assertEqual(LLR.token_y_subtree_borrowed, UnsignedDecimal("788296e6"))
        self.assertEqual(LLRR.token_y_subtree_borrowed, UnsignedDecimal("779531e6"))

    def test_right_leg_only(self):
        # Mirrors test_left_leg_only

        liq_tree: LiquidityTree = self.liq_tree

        root: LiqNode = liq_tree.root
        R: LiqNode = liq_tree.nodes[(8 << 24) | 24]
        RR: LiqNode = liq_tree.nodes[(4 << 24) | 28]
        RL: LiqNode = liq_tree.nodes[(4 << 24) | 24]
        RRL: LiqNode = liq_tree.nodes[(2 << 24) | 28]
        RRLL: LiqNode = liq_tree.nodes[(1 << 24) | 28]

        # T0 - populate tree with data excluding fee calculations
        liq_tree.add_wide_m_liq(Decimal("8430"))                        # root
        liq_tree.add_m_liq(LiqRange(low=8, high=15), UnsignedDecimal("377"))         # R
        liq_tree.add_m_liq(LiqRange(low=12, high=15), UnsignedDecimal("9082734"))    # RR
        liq_tree.add_m_liq(LiqRange(low=8, high=11), UnsignedDecimal("1111"))        # RL
        liq_tree.add_m_liq(LiqRange(low=12, high=13), UnsignedDecimal("45346"))      # RRL
        liq_tree.add_m_liq(LiqRange(low=12, high=12), UnsignedDecimal("287634865"))  # RRLL

        liq_tree.add_wide_t_liq(Decimal("4430"), UnsignedDecimal("492e18"), UnsignedDecimal("254858e6"))                      # root
        liq_tree.add_t_liq(LiqRange(low=8, high=15), UnsignedDecimal("77"), UnsignedDecimal("998e18"), UnsignedDecimal("353e6"))           # R
        liq_tree.add_t_liq(LiqRange(low=12, high=15), UnsignedDecimal("82734"), UnsignedDecimal("765e18"), UnsignedDecimal("99763e6"))     # RR
        liq_tree.add_t_liq(LiqRange(low=8, high=11), UnsignedDecimal("111"), UnsignedDecimal("24e18"), UnsignedDecimal("552e6"))           # RL
        liq_tree.add_t_liq(LiqRange(low=12, high=13), UnsignedDecimal("5346"), UnsignedDecimal("53e18"), UnsignedDecimal("8765e6"))        # RRL
        liq_tree.add_t_liq(LiqRange(low=12, high=12), UnsignedDecimal("7634865"), UnsignedDecimal("701e18"), UnsignedDecimal("779531e6"))  # RRLL

        # m_liq
        self.assertEqual(root.m_liq, UnsignedDecimal("8430"))
        self.assertEqual(R.m_liq, UnsignedDecimal("377"))
        self.assertEqual(RR.m_liq, UnsignedDecimal("9082734"))
        self.assertEqual(RL.m_liq, UnsignedDecimal("1111"))
        self.assertEqual(RRL.m_liq, UnsignedDecimal("45346"))
        self.assertEqual(RRLL.m_liq, UnsignedDecimal("287634865"))

        # t_liq
        self.assertEqual(root.t_liq, UnsignedDecimal("4430"))
        self.assertEqual(R.t_liq, UnsignedDecimal("77"))
        self.assertEqual(RR.t_liq, UnsignedDecimal("82734"))
        self.assertEqual(RL.t_liq, UnsignedDecimal("111"))
        self.assertEqual(RRL.t_liq, UnsignedDecimal("5346"))
        self.assertEqual(RRLL.t_liq, UnsignedDecimal("7634865"))

        # subtree_m_liq
        self.assertEqual(root.subtree_m_liq, UnsignedDecimal("324198833"))
        self.assertEqual(R.subtree_m_liq, UnsignedDecimal("324063953"))
        self.assertEqual(RR.subtree_m_liq, UnsignedDecimal("324056493"))
        self.assertEqual(RL.subtree_m_liq, UnsignedDecimal("4444"))
        self.assertEqual(RRL.subtree_m_liq, UnsignedDecimal("287725557"))
        self.assertEqual(RRLL.subtree_m_liq, UnsignedDecimal("287634865"))

        # borrowed_x
        self.assertEqual(root.token_x_borrowed, UnsignedDecimal("492e18"))
        self.assertEqual(R.token_x_borrowed, UnsignedDecimal("998e18"))
        self.assertEqual(RR.token_x_borrowed, UnsignedDecimal("765e18"))
        self.assertEqual(RL.token_x_borrowed, UnsignedDecimal("24e18"))
        self.assertEqual(RRL.token_x_borrowed, UnsignedDecimal("53e18"))
        self.assertEqual(RRLL.token_x_borrowed, UnsignedDecimal("701e18"))

        # subtree_borrowed_x
        self.assertEqual(root.token_x_subtree_borrowed, UnsignedDecimal("3033e18"))  # 492e18 + 998e18 + 765e18 + 53e18 + 701e18 + 24e18
        self.assertEqual(R.token_x_subtree_borrowed, UnsignedDecimal("2541e18"))  # 998e18 + 765e18 + 53e18 + 701e18 + 24e18
        self.assertEqual(RR.token_x_subtree_borrowed, UnsignedDecimal("1519e18"))  # 765e18 + 53e18 + 701e18
        self.assertEqual(RL.token_x_subtree_borrowed, UnsignedDecimal("24e18"))
        self.assertEqual(RRL.token_x_subtree_borrowed, UnsignedDecimal("754e18"))  # 53e18 + 701e18
        self.assertEqual(RRLL.token_x_subtree_borrowed, UnsignedDecimal("701e18"))  # 701e18

        # borrowed_y
        self.assertEqual(root.token_y_borrowed, UnsignedDecimal("254858e6"))
        self.assertEqual(R.token_y_borrowed, UnsignedDecimal("353e6"))
        self.assertEqual(RR.token_y_borrowed, UnsignedDecimal("99763e6"))
        self.assertEqual(RL.token_y_borrowed, UnsignedDecimal("552e6"))
        self.assertEqual(RRL.token_y_borrowed, UnsignedDecimal("8765e6"))
        self.assertEqual(RRLL.token_y_borrowed, UnsignedDecimal("779531e6"))

        # subtree_borrowed_y
        self.assertEqual(root.token_y_subtree_borrowed, UnsignedDecimal("1143822e6"))  # 254858e6 + 353e6 + 99763e6 + 8765e6 + 779531e6 + 552e6
        self.assertEqual(R.token_y_subtree_borrowed, UnsignedDecimal("888964e6"))  # 353e6 + 99763e6 + 8765e6 + 779531e6 + 552e6
        self.assertEqual(RR.token_y_subtree_borrowed, UnsignedDecimal("888059e6"))  # 99763e6 + 8765e6 + 779531e6
        self.assertEqual(RL.token_y_subtree_borrowed, UnsignedDecimal("552e6"))
        self.assertEqual(RRL.token_y_subtree_borrowed, UnsignedDecimal("788296e6"))  # 8765e6 + 779531e6
        self.assertEqual(RRLL.token_y_subtree_borrowed, UnsignedDecimal("779531e6"))  # 779531e6

        # T98273
        liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("4541239648278065")  # 7.9% APR as Q192.64 T98273 - T0
        liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("13278814667749784")  # 23.1% APR as Q192.64 T98273 - T0

        # Apply change that requires fee calculation
        # add_m_liq
        liq_tree.add_m_liq(LiqRange(low=8, high=12), UnsignedDecimal("2734"))  # RRLL, RL

        # root
        #           total_m_liq = subtree_m_liq + aux_level * range
        #           earn_x = rate_diff * borrow / total_m_liq / q_conversion
        #
        #           earn_x     = 4541239648278065 * 492e18 / 324198833 / 2**64 = 373601278.675896709674247960788128930863427771780474615825402
        #           earn_x_sub = 4541239648278065 * 3033e18 / 324198833 / 2**64 = 2303115199.64226569195527248998047773843247242237841363780171
        #
        #           earn_y     = 13278814667749784 * 254858e6 / 324198833 / 2**64 = 0.5658826914495360518450511013487630736056981385516828024975012016
        #           earn_y_sub = 13278814667749784 * 1143822e6 / 324198833 / 2**64 = 2.5397243637601771413630729302079780755472335819729532779755660779
        self.assertEqual(int(root.token_x_cumulative_earned_per_m_liq), UnsignedDecimal("373601278"))
        self.assertEqual(int(root.token_x_cumulative_earned_per_m_subtree_liq), UnsignedDecimal("2303115199"))
        self.assertEqual(int(root.token_y_cumulative_earned_per_m_liq), UnsignedDecimal("0"))
        self.assertEqual(int(root.token_y_cumulative_earned_per_m_subtree_liq), UnsignedDecimal("2"))

        # R
        #           total_m_liq = 324063953 + 8430 * 8 = 324131393
        #
        #           earn_x      = 4541239648278065 * 998e18 / 324131393 / 2**64 = 757991165.739306427787211084069081135461126639210612444989968
        #           earn_x_sub  = 4541239648278065 * 2541e18 / 324131393 / 2**64 = 1929915382.90939642585902140743440397315302884793002627527005
        #
        #           earn_y      = 13278814667749784 * 353e6 / 324131393 / 2**64 = 0.0007839587228619296743658765199435031723124415958637831459168088
        #           earn_y_sub  = 13278814667749784 * 888964e6 / 324131393 / 2**64 = 1.9742523572527831474305582285412361305143267162194111063081870320
        self.assertEqual(int(R.token_x_cumulative_earned_per_m_liq), UnsignedDecimal("757991165"))
        self.assertEqual(int(R.token_x_cumulative_earned_per_m_subtree_liq), UnsignedDecimal("1929915382"))
        self.assertEqual(int(R.token_y_cumulative_earned_per_m_liq), UnsignedDecimal("0"))
        self.assertEqual(int(R.token_y_cumulative_earned_per_m_subtree_liq), UnsignedDecimal("1"))

        # RR
        #           total_m_liq = 324056493 + (377 + 8430) * 4 = 324091721
        #
        #           earn_x      = 4541239648278065 * 765e18 / 324091721 / 2**64 = 581096415.560225831923714717876078601550264387092272644849535
        #           earn_x_sub  = 4541239648278065 * 1519e18 / 324091721 / 2**64 = 1153837196.38690593293087928948204365458150536469694398369469
        #
        #           earn_y      = 13278814667749784 * 99763e6 / 324091721 / 2**64 = 0.2215854043845212215658200680605818096232476901747430889861663960
        #           earn_y_sub  = 13278814667749784 * 888059e6 / 324091721 / 2**64 = 1.9724839131974131842719305135352006382347335233392357172695883598
        self.assertEqual(int(RR.token_x_cumulative_earned_per_m_liq), UnsignedDecimal("581096415"))
        self.assertEqual(int(RR.token_x_cumulative_earned_per_m_subtree_liq), UnsignedDecimal("1153837196"))
        self.assertEqual(int(RR.token_y_cumulative_earned_per_m_liq), UnsignedDecimal("0"))
        self.assertEqual(int(RR.token_y_cumulative_earned_per_m_subtree_liq), UnsignedDecimal("1"))

        # RL
        #           total_m_liq = 4444 + (377 + 8430) * 4 = 39672
        #
        #           earn_x      = 4541239648278065 * 24e18 / 39672 / 2**64 = 148929881804.004419784834421574153374302771710945632482252911
        #           earn_x_sub  = 4541239648278065 * 24e18 / 39672 / 2**64 = 148929881804.004419784834421574153374302771710945632482252911
        #
        #           earn_y      = 13278814667749784 * 552e6 / 39672 / 2**64 = 10.016005848413612945928345245285743980736658202469601316734724742
        #           earn_y_sub  = 13278814667749784 * 552e6 / 39672 / 2**64 = 10.016005848413612945928345245285743980736658202469601316734724742
        self.assertEqual(int(RL.token_x_cumulative_earned_per_m_liq), UnsignedDecimal("148929881804"))
        self.assertEqual(int(RL.token_x_cumulative_earned_per_m_subtree_liq), UnsignedDecimal("148929881804"))
        self.assertEqual(int(RL.token_y_cumulative_earned_per_m_liq), UnsignedDecimal("10"))
        self.assertEqual(int(RL.token_y_cumulative_earned_per_m_subtree_liq), UnsignedDecimal("10"))

        # RRL
        #           total_m_liq = 287725557 + (9082734 + 377 + 8430) * 2 = 305908639
        #
        #           earn_x      = 4541239648278065 * 53e18 / 305908639 / 2**64 = 42651943.5921096141810155248335108410236545389757231280339726
        #           earn_x_sub  = 4541239648278065 * 754e18 / 305908639 / 2**64 = 606784254.121710360235579353291833474185575894107457330898403
        #
        #           earn_y      = 13278814667749784 * 8765e6 / 305908639 / 2**64 = 0.0206252758466917150640245207131723061423410095348761855275430371
        #           earn_y_sub  = 13278814667749784 * 788296e6 / 305908639 / 2**64 = 1.8549711864054412114215942475882345970088817401374509465624718757
        self.assertEqual(int(RRL.token_x_cumulative_earned_per_m_liq), UnsignedDecimal("42651943"))
        self.assertEqual(int(RRL.token_x_cumulative_earned_per_m_subtree_liq), UnsignedDecimal("606784254"))
        self.assertEqual(int(RRL.token_y_cumulative_earned_per_m_liq), UnsignedDecimal("0"))
        self.assertEqual(int(RRL.token_y_cumulative_earned_per_m_subtree_liq), UnsignedDecimal("1"))

        # RRLL
        #           total_m_liq = 287634865 + (45346 + 9082734 + 377 + 8430) * 1 = 296771752
        #
        #           earn_x      = 4541239648278065 * 701e18 / 296771752 / 2**64 = 581500584.766017533363270505955415005042190229659676220491523
        #           earn_x_sub  = 4541239648278065 * 701e18 / 296771752 / 2**64 = 581500584.766017533363270505955415005042190229659676220491523
        #
        #           earn_y      = 13278814667749784 * 779531e6 / 296771752 / 2**64 = 1.8908210002218903501728143334071499784764070319492513392714860291
        #           earn_y_sub  = 13278814667749784 * 779531e6 / 296771752 / 2**64 = 1.8908210002218903501728143334071499784764070319492513392714860291
        self.assertEqual(int(RRLL.token_x_cumulative_earned_per_m_liq), UnsignedDecimal("581500584"))
        self.assertEqual(int(RRLL.token_x_cumulative_earned_per_m_subtree_liq), UnsignedDecimal("581500584"))
        self.assertEqual(int(RRLL.token_y_cumulative_earned_per_m_liq), UnsignedDecimal("1"))
        self.assertEqual(int(RRLL.token_y_cumulative_earned_per_m_subtree_liq), UnsignedDecimal("1"))

        # m_liq
        self.assertEqual(root.m_liq, UnsignedDecimal("8430"))
        self.assertEqual(R.m_liq, UnsignedDecimal("377"))
        self.assertEqual(RR.m_liq, UnsignedDecimal("9082734"))
        self.assertEqual(RL.m_liq, UnsignedDecimal("3845"))
        self.assertEqual(RRL.m_liq, UnsignedDecimal("45346"))
        self.assertEqual(RRLL.m_liq, UnsignedDecimal("287637599"))

        # subtree_m_liq
        self.assertEqual(root.subtree_m_liq, UnsignedDecimal("324212503"))  # 8430*16 + 377*8 + 9082734*4 + 3845*4 + 45346*2 + 287637599*1
        self.assertEqual(R.subtree_m_liq, UnsignedDecimal("324077623"))  # 377*8 + 9082734*4 + 3845*4 + 45346*2 + 287637599*1
        self.assertEqual(RR.subtree_m_liq, UnsignedDecimal("324059227"))  # 9082734*4 + 45346*2 + 287637599*1
        self.assertEqual(RL.subtree_m_liq, UnsignedDecimal("15380"))  # 3845*4
        self.assertEqual(RRL.subtree_m_liq, UnsignedDecimal("287728291"))  # 45346*2 + 287637599*1
        self.assertEqual(RRLL.subtree_m_liq, UnsignedDecimal("287637599"))  # 287637599*1

        # T2876298273
        liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("16463537718422861220174597")  # 978567.9% APR as Q192.64 T2876298273 - T98273
        liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("3715979586694123491881712207")  # 220872233.1% APR as Q192.64 T2876298273 - T98273

        # Apply change that requires fee calculation
        # remove_m_liq
        liq_tree.remove_m_liq(LiqRange(low=8, high=12), UnsignedDecimal("2734"))  # RRLL, RL

        # root
        #           total_m_liq = 324212503
        #
        #           earn_x      = 16463537718422861220174597 * 492e18 / 324212503 / 2**64 = 1354374549470516050.18864221581152444619216774937383131887026
        #           earn_x_sub  = 16463537718422861220174597 * 3033e18 / 324212503 / 2**64 = 8349223594601778821.58973951332592204329439996717648453279172
        #
        #           earn_y      = 3715979586694123491881712207 * 254858e6 / 324212503 / 2**64 = 158351473403.760477087118657111090258803416110827691474619042
        #           earn_y_sub  = 3715979586694123491881712207 * 1143822e6 / 324212503 / 2**64 = 710693401861.570429112455707155049015549996557766096092261976
        self.assertEqual(int(root.token_x_cumulative_earned_per_m_liq), UnsignedDecimal("1354374549844117328"))  # 373601278 + 1354374549470516050 = 1354374549844117328
        self.assertEqual(int(root.token_x_cumulative_earned_per_m_subtree_liq), UnsignedDecimal("8349223596904894021"))  # 2303115199 + 8349223594601778821 = 8349223596904894020 (sol losses 1 wei)
        self.assertEqual(int(root.token_y_cumulative_earned_per_m_liq), UnsignedDecimal("158351473404"))  # 0 + 158351473403 = 158351473403 (sol losses 1 wei)
        self.assertEqual(int(root.token_y_cumulative_earned_per_m_subtree_liq), UnsignedDecimal("710693401864"))  # 2 + 710693401861 = 710693401863 (sol losses 1 wei)

        # R
        #           total_m_liq = 324077623 + 8430 * 8 = 324145063
        #
        #           earn_x      = 16463537718422861220174597 * 998e18 / 324145063 / 2**64 = 2747859799177149412.40503918202324257122793136834755591677703
        #           earn_x_sub  = 16463537718422861220174597 * 2541e18 / 324145063 / 2**64 = 6996304358425988634.18958372897901740830678718133380719892830
        #
        #           earn_y      = 3715979586694123491881712207 * 353e6 / 324145063 / 2**64 = 219375887.687723491736647414380713113554572979392890952782027
        #           earn_y_sub  = 3715979586694123491881712207 * 888964e6 / 324145063 / 2**64 = 552456845955.890725518915105035513462543703722529807118835474
        self.assertEqual(int(R.token_x_cumulative_earned_per_m_liq), UnsignedDecimal("2747859799935140578"))  # 757991165 + 2747859799177149412 = 2747859799935140577 (sol losses 1 wei)
        self.assertEqual(int(R.token_x_cumulative_earned_per_m_subtree_liq), UnsignedDecimal("6996304360355904017"))  # 1929915382 + 6996304358425988634 = 6996304360355904016 (sol losses 1 wei)
        self.assertEqual(int(R.token_y_cumulative_earned_per_m_liq), UnsignedDecimal("219375887"))  # 0 + 219375887 = 219375887 = 219375887
        self.assertEqual(int(R.token_y_cumulative_earned_per_m_subtree_liq), UnsignedDecimal("552456845957"))  # 1 + 552456845956 = 552456845956 (sol losses 1 wei)

        # RR
        #           total_m_liq = 324059227 + (377 + 8430) * 4 = 324094455
        #
        #           earn_x      = 16463537718422861220174597 * 765e18 / 324094455 / 2**64 = 2106654304105573173.10473569019029577351750175393657598084186
        #           earn_x_sub  = 16463537718422861220174597 * 1519e18 / 324094455 / 2**64 = 4183016846975641372.47855361228635199996481720814334498679581
        #
        #           earn_y      = 3715979586694123491881712207 * 99763e6 / 324094455 / 2**64 = 62008538706.1288411875002441524622314240784801570453009535875
        #           earn_y_sub  = 3715979586694123491881712207 * 888059e6 / 324094455 / 2**64 = 551980602776.841840924293368501262560029627326862519099461143
        self.assertEqual(int(RR.token_x_cumulative_earned_per_m_liq), UnsignedDecimal("2106654304686669588"))  # 581096415 + 2106654304105573173 = 2106654304686669588
        self.assertEqual(int(RR.token_x_cumulative_earned_per_m_subtree_liq), UnsignedDecimal("4183016848129478568"))  # 1153837196 + 4183016846975641372 = 4183016848129478568
        self.assertEqual(int(RR.token_y_cumulative_earned_per_m_liq), UnsignedDecimal("62008538706"))  # 0 + 62008538706 = 62008538706
        self.assertEqual(int(RR.token_y_cumulative_earned_per_m_subtree_liq), UnsignedDecimal("551980602778"))  # 1 + 551980602776 = 551980602777 (sol losses 1 wei)

        # RL
        #           total_m_liq = 15380 + (377 + 8430) * 4 = 50608
        #
        #           earn_x      = 16463537718422861220174597 * 24e18 / 50608 / 2**64 = 423248577958689008325.429426909965566945601510047930853109815
        #           earn_x_sub  = 16463537718422861220174597 * 24e18 / 50608 / 2**64 = 423248577958689008325.429426909965566945601510047930853109815
        #
        #           earn_y      = 3715979586694123491881712207 * 552e6 / 50608 / 2**64 = 2197219781185.45157550848350683783177940360867452683580030548
        #           earn_y_sub  = 3715979586694123491881712207 * 552e6 / 50608 / 2**64 = 2197219781185.45157550848350683783177940360867452683580030548
        self.assertEqual(int(RL.token_x_cumulative_earned_per_m_liq), UnsignedDecimal("423248578107618890129"))  # 148929881804 + 423248577958689008325 = 423248578107618890129
        self.assertEqual(int(RL.token_x_cumulative_earned_per_m_subtree_liq), UnsignedDecimal("423248578107618890129"))  # 148929881804 + 423248577958689008325 = 423248578107618890129
        self.assertEqual(int(RL.token_y_cumulative_earned_per_m_liq), UnsignedDecimal("2197219781195"))  # 10 + 2197219781185 = 2197219781195
        self.assertEqual(int(RL.token_y_cumulative_earned_per_m_subtree_liq), UnsignedDecimal("2197219781195"))  # 10 + 2197219781185 = 2197219781195

        # RRL
        #           total_m_liq = 287728291 + (9082734 + 377 + 8430) * 2 = 305911373
        #
        #           earn_x      = 16463537718422861220174597 * 53e18 / 305911373 / 2**64 = 154626414974589533.957746783298485424790431468186321359344549
        #           earn_x_sub  = 16463537718422861220174597 * 754e18 / 305911373 / 2**64 = 2199779563978122803.85171838881241528852802503797143971595830
        #
        #           earn_y      = 3715979586694123491881712207 * 8765e6 / 305911373 / 2**64 = 5771781665.52844938596716448955303604219154769320799186650875
        #           earn_y_sub  = 3715979586694123491881712207 * 788296e6 / 305911373 / 2**64 = 519095539054.126016789546137872983468330339792397614050929992
        self.assertEqual(int(RRL.token_x_cumulative_earned_per_m_liq), UnsignedDecimal("154626415017241477"))  # 42651943 + 154626414974589533 = 154626415017241476 (sol losses 1 wei)
        self.assertEqual(int(RRL.token_x_cumulative_earned_per_m_subtree_liq), UnsignedDecimal("2199779564584907057"))  # 606784254 + 2199779563978122803 = 2199779564584907057
        self.assertEqual(int(RRL.token_y_cumulative_earned_per_m_liq), UnsignedDecimal("5771781665"))  # 0 + 5771781665 = 5771781665
        self.assertEqual(int(RRL.token_y_cumulative_earned_per_m_subtree_liq), UnsignedDecimal("519095539055"))  # 1 + 519095539054 = 519095539055

        # RRLL
        #           total_m_liq = 287637599 + (45346 + 9082734 + 377 + 8430) * 1 = 296774486
        #
        #           earn_x      = 16463537718422861220174597 * 701e18 / 296774486 / 2**64 = 2108117905415037748.37451632639936795389368532390933657093156
        #           earn_x_sub  = 16463537718422861220174597 * 701e18 / 296774486 / 2**64 = 2108117905415037748.37451632639936795389368532390933657093156
        #
        #           earn_y      = 3715979586694123491881712207 * 779531e6 / 296774486 / 2**64 = 529127613134.050803777279185858502873428448836282593499892809
        #           earn_y_sub  = 3715979586694123491881712207 * 779531e6 / 296774486 / 2**64 = 529127613134.050803777279185858502873428448836282593499892809
        self.assertEqual(int(RRLL.token_x_cumulative_earned_per_m_liq), UnsignedDecimal("2108117905996538333"))  # 581500584 + 2108117905415037748 = 2108117905996538332 (sol losses 1 wei)
        self.assertEqual(int(RRLL.token_x_cumulative_earned_per_m_subtree_liq), UnsignedDecimal("2108117905996538333"))  # 581500584 + 2108117905415037748 = 2108117905996538332 (sol losses 1 wei)
        self.assertEqual(int(RRLL.token_y_cumulative_earned_per_m_liq), UnsignedDecimal("529127613135"))  # 1 + 529127613134 = 529127613135
        self.assertEqual(int(RRLL.token_y_cumulative_earned_per_m_subtree_liq), UnsignedDecimal("529127613135"))  # 1 + 529127613134 = 529127613135

        # m_liq
        self.assertEqual(root.m_liq, UnsignedDecimal("8430"))
        self.assertEqual(R.m_liq, UnsignedDecimal("377"))
        self.assertEqual(RR.m_liq, UnsignedDecimal("9082734"))
        self.assertEqual(RL.m_liq, UnsignedDecimal("1111"))
        self.assertEqual(RRL.m_liq, UnsignedDecimal("45346"))
        self.assertEqual(RRLL.m_liq, UnsignedDecimal("287634865"))

        # subtree_m_liq
        self.assertEqual(root.subtree_m_liq, UnsignedDecimal("324198833"))
        self.assertEqual(R.subtree_m_liq, UnsignedDecimal("324063953"))
        self.assertEqual(RR.subtree_m_liq, UnsignedDecimal("324056493"))
        self.assertEqual(RL.subtree_m_liq, UnsignedDecimal("4444"))
        self.assertEqual(RRL.subtree_m_liq, UnsignedDecimal("287725557"))
        self.assertEqual(RRLL.subtree_m_liq, UnsignedDecimal("287634865"))

        # T9214298113
        liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("11381610389149375791104")  # 307% APR as Q192.64 T9214298113 - T2876298273
        liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("185394198934916215865344")  # 5000.7% APR as Q192.64 T9214298113 - T2876298273

        # Apply change that requires fee calculation
        # add_t_liq
        liq_tree.add_t_liq(LiqRange(low=8, high=12), UnsignedDecimal("1000"), UnsignedDecimal("1000e18"), UnsignedDecimal("1000e6"))  # RRLL, RL

        # root
        #           total_m_liq = 324198833
        #
        #           earn_x      = 11381610389149375791104 * 492e18 / 324198833 / 2**64 = 936348777891386.743735803607164207960477914490210395050990205
        #           earn_x_sub  = 11381610389149375791104 * 3033e18 / 324198833 / 2**64 = 5772247649074341.45071278931001837956123885091221164266189693
        #
        #           earn_y      = 185394198934916215865344 * 254858e6 / 324198833 / 2**64 = 7900657.61872699474175109887651599451346454839027751836478695
        #           earn_y_sub  = 185394198934916215865344 * 1143822e6 / 324198833 / 2**64 = 35458749.5733606501640098620374258523427949943453374491326438
        self.assertEqual(int(root.token_x_cumulative_earned_per_m_liq), UnsignedDecimal("1355310898622008715"))  # 373601278 + 1354374549470516050 + 936348777891386 = 1355310898622008714 (sol losses 1 wei)
        self.assertEqual(int(root.token_x_cumulative_earned_per_m_subtree_liq), UnsignedDecimal("8354995844553968362"))  # 2303115199 + 8349223594601778821 + 5772247649074341 = 8354995844553968361 (sol losses 1 wei)
        self.assertEqual(int(root.token_y_cumulative_earned_per_m_liq), UnsignedDecimal("158359374061"))  # 0 + 158351473403 + 7900657 = 158359374060 (sol losses 1 wei)
        self.assertEqual(int(root.token_y_cumulative_earned_per_m_subtree_liq), UnsignedDecimal("710728860613"))  # 2 + 710693401861 + 35458749 = 710728860612 (sol losses 1 wei)

        # R
        #           total_m_liq = 324063953 + 8430 * 8 = 324131393
        #
        #           earn_x      = 11381610389149375791104 * 998e18 / 324131393 / 2**64 = 1899736810880077.58842507649572740061066261792173891653870132
        #           earn_x_sub  = 11381610389149375791104 * 2541e18 / 324131393 / 2**64 = 4836905046539355.86391595127819972440049470154222303299082171
        #
        #           earn_y      = 185394198934916215865344 * 353e6 / 324131393 / 2**64 = 10945.359436035932129843115196215424291564802240553108041589788249
        #           earn_y_sub  = 185394198934916215865344 * 888964e6 / 324131393 / 2**64 = 27563825.7951735024642318840149814403397354471925525584619938
        self.assertEqual(int(R.token_x_cumulative_earned_per_m_liq), UnsignedDecimal("2749759536746020655"))  # 757991165 + 2747859799177149412 + 1899736810880077 = 2749759536746020654 (sol losses 1 wei)
        self.assertEqual(int(R.token_x_cumulative_earned_per_m_subtree_liq), UnsignedDecimal("7001141265402443372"))  # 1929915382 + 6996304358425988634 + 4836905046539355 = 7001141265402443371 (sol losses 1 wei)
        self.assertEqual(int(R.token_y_cumulative_earned_per_m_liq), UnsignedDecimal("219386833"))  # 0 + 219375887 + 10945 = 219386832 (sol losses 1 wei)
        self.assertEqual(int(R.token_y_cumulative_earned_per_m_subtree_liq), UnsignedDecimal("552484409783"))  # 1 + 552456845956 + 27563825 = 552484409782 (sol losses 1 wei)

        # RR
        #           total_m_liq = 324056493 + (377 + 8430) * 4 = 324091721
        #
        #           earn_x      = 11381610389149375791104 * 765e18 / 324091721 / 2**64 = 1456389336983247.97581853577374895245788594982344519686141566
        #           earn_x_sub  = 11381610389149375791104 * 1519e18 / 324091721 / 2**64 = 2891837127944514.60819392920303876965167157879975588762417044
        #
        #           earn_y      = 185394198934916215865344 * 99763e6 / 324091721 / 2**64 = 3093698.46401352576654665825318763474490453834363760251685046
        #           earn_y_sub  = 185394198934916215865344 * 888059e6 / 324091721 / 2**64 = 27539135.3934162733549879091613880669579421169863823827823111
        self.assertEqual(int(RR.token_x_cumulative_earned_per_m_liq), UnsignedDecimal("2108110694023652836"))  # 581096415 + 2106654304105573173+ 1456389336983247 = 2108110694023652835 (sol losses 1 wei)
        self.assertEqual(int(RR.token_x_cumulative_earned_per_m_subtree_liq), UnsignedDecimal("4185908685257423083"))  # 1153837196 + 4183016846975641372 + 2891837127944514 = 4185908685257423082 (sol losses 1 wei)
        self.assertEqual(int(RR.token_y_cumulative_earned_per_m_liq), UnsignedDecimal("62011632404"))  # 0 + 62008538706 + 3093698 = 62011632404
        self.assertEqual(int(RR.token_y_cumulative_earned_per_m_subtree_liq), UnsignedDecimal("552008141914"))  # 1 + 551980602776 + 27539135 = 552008141912 (sol losses 2 wei)

        # RL
        #           total_m_liq = 4444 + (377 + 8430) * 4 = 39672
        #
        #           earn_x      = 11381610389149375791104 * 24e18 / 39672 / 2**64 = 373259731104033296.286645111573225645606473079249848759830611
        #           earn_x_sub  = 11381610389149375791104 * 24e18 / 39672 / 2**64 = 373259731104033296.286645111573225645606473079249848759830611
        #
        #           earn_y      = 185394198934916215865344 * 552e6 / 39672 / 2**64 = 139839995.304998697233270837982279275016069267997580157289776
        #           earn_y_sub  = 185394198934916215865344 * 552e6 / 39672 / 2**64 = 139839995.304998697233270837982279275016069267997580157289776
        self.assertEqual(int(RL.token_x_cumulative_earned_per_m_liq), UnsignedDecimal("423621837838722923425"))  # 148929881804 + 423248577958689008325 + 373259731104033296 = 423621837838722923425
        self.assertEqual(int(RL.token_x_cumulative_earned_per_m_subtree_liq), UnsignedDecimal("423621837838722923425"))  # 148929881804 + 423248577958689008325 + 373259731104033296 = 423621837838722923425
        self.assertEqual(int(RL.token_y_cumulative_earned_per_m_liq), UnsignedDecimal("2197359621190"))  # 10 + 2197219781185 + 139839995 = 2197359621190
        self.assertEqual(int(RL.token_y_cumulative_earned_per_m_subtree_liq), UnsignedDecimal("2197359621190"))  # 10 + 2197219781185 + 139839995 = 2197359621190

        # RRL
        #           total_m_liq = 287725557 + (9082734 + 377 + 8430) * 2 = 305908639
        #
        #           earn_x      = 11381610389149375791104 * 53e18 / 305908639 / 2**64 = 106897640711262.335596794608928382455998365904272484439381916
        #           earn_x_sub  = 11381610389149375791104 * 754e18 / 305908639 / 2**64 = 1520770209363996.24603741764400000701552392248719723145837669
        #
        #           earn_y      = 185394198934916215865344 * 8765e6 / 305908639 / 2**64 = 287962.93864210284405202260308978443477406072046236000546555339354
        #           earn_y_sub  = 185394198934916215865344 * 788296e6 / 305908639 / 2**64 = 25898463.5116731435886860479093285465823905270619049107665115
        self.assertEqual(int(RRL.token_x_cumulative_earned_per_m_liq), UnsignedDecimal("154733312657952739"))  # 42651943 + 154626414974589533 + 106897640711262 = 154733312657952738 (sol losses 1 wei)
        self.assertEqual(int(RRL.token_x_cumulative_earned_per_m_subtree_liq), UnsignedDecimal("2201300334794271054"))  # 606784254 + 2199779563978122803 + 1520770209363996 = 2201300334794271053 (sol losses 1 wei)
        self.assertEqual(int(RRL.token_y_cumulative_earned_per_m_liq), UnsignedDecimal("5772069628"))  # 0 + 5771781665 + 287962 = 5772069627 (sol losses 1 wei)
        self.assertEqual(int(RRL.token_y_cumulative_earned_per_m_subtree_liq), UnsignedDecimal("519121437519"))  # 1 + 519095539054 + 25898463 = 519121437518 (sol losses 1 wei)

        # RRLL
        #           total_m_liq = 287634865 + (45346 + 9082734 + 377 + 8430) * 1 = 296771752
        #
        #           earn_x      = 11381610389149375791104 * 701e18 / 296771752 / 2**64 = 1457402297493569.71876500861500730007660377831377967536479010
        #           earn_x_sub  = 11381610389149375791104 * 701e18 / 296771752 / 2**64 = 1457402297493569.71876500861500730007660377831377967536479010
        #
        #           earn_y      = 185394198934916215865344 * 779531e6 / 296771752 / 2**64 = 26398986.1622835510939886934876573358559478744206759947961624
        #           earn_y_sub  = 185394198934916215865344 * 779531e6 / 296771752 / 2**64 = 26398986.1622835510939886934876573358559478744206759947961624
        self.assertEqual(int(RRLL.token_x_cumulative_earned_per_m_liq), UnsignedDecimal("2109575308294031902"))  # 581500584 + 2108117905415037748 + 1457402297493569 = 2109575308294031901 (sol losses 1 wei)
        self.assertEqual(int(RRLL.token_x_cumulative_earned_per_m_subtree_liq), UnsignedDecimal("2109575308294031902"))  # 581500584 + 2108117905415037748 + 1457402297493569 = 2109575308294031901 (sol losses 1 wei)
        self.assertEqual(int(RRLL.token_y_cumulative_earned_per_m_liq), UnsignedDecimal("529154012122"))  # 1 + 529127613134 + 26398986 = 529154012121 (sol losses 1 wei)
        self.assertEqual(int(RRLL.token_y_cumulative_earned_per_m_subtree_liq), UnsignedDecimal("529154012122"))  # 1 + 529127613134 + 26398986 = 529154012121 (sol losses 1 wei)

        # t_liq
        self.assertEqual(root.t_liq, UnsignedDecimal("4430"))
        self.assertEqual(R.t_liq, UnsignedDecimal("77"))
        self.assertEqual(RR.t_liq, UnsignedDecimal("82734"))
        self.assertEqual(RL.t_liq, UnsignedDecimal("1111"))
        self.assertEqual(RRL.t_liq, UnsignedDecimal("5346"))
        self.assertEqual(RRLL.t_liq, UnsignedDecimal("7635865"))

        # borrowed_x
        self.assertEqual(root.token_x_borrowed, UnsignedDecimal("492e18"))
        self.assertEqual(R.token_x_borrowed, UnsignedDecimal("998e18"))
        self.assertEqual(RR.token_x_borrowed, UnsignedDecimal("765e18"))
        self.assertEqual(RL.token_x_borrowed, UnsignedDecimal("1024e18"))
        self.assertEqual(RRL.token_x_borrowed, UnsignedDecimal("53e18"))
        self.assertEqual(RRLL.token_x_borrowed, UnsignedDecimal("1701e18"))

        # subtree_borrowed_x
        self.assertEqual(root.token_x_subtree_borrowed, UnsignedDecimal("5033e18"))  # 492e18 + 998e18 + 765e18 + 53e18 + 701e18 + 24e18
        self.assertEqual(R.token_x_subtree_borrowed, UnsignedDecimal("4541e18"))  # 998e18 + 765e18 + 53e18 + 701e18 + 24e18
        self.assertEqual(RR.token_x_subtree_borrowed, UnsignedDecimal("2519e18"))  # 765e18 + 53e18 + 701e18
        self.assertEqual(RL.token_x_subtree_borrowed, UnsignedDecimal("1024e18"))
        self.assertEqual(RRL.token_x_subtree_borrowed, UnsignedDecimal("1754e18"))  # 53e18 + 701e18
        self.assertEqual(RRLL.token_x_subtree_borrowed, UnsignedDecimal("1701e18"))  # 701e18

        # borrowed_y
        self.assertEqual(root.token_y_borrowed, UnsignedDecimal("254858e6"))
        self.assertEqual(R.token_y_borrowed, UnsignedDecimal("353e6"))
        self.assertEqual(RR.token_y_borrowed, UnsignedDecimal("99763e6"))
        self.assertEqual(RL.token_y_borrowed, UnsignedDecimal("1552e6"))
        self.assertEqual(RRL.token_y_borrowed, UnsignedDecimal("8765e6"))
        self.assertEqual(RRLL.token_y_borrowed, UnsignedDecimal("780531e6"))

        # subtree_borrowed_y
        self.assertEqual(root.token_y_subtree_borrowed, UnsignedDecimal("1145822e6"))  # 254858e6 + 353e6 + 99763e6 + 8765e6 + 779531e6 + 552e6
        self.assertEqual(R.token_y_subtree_borrowed, UnsignedDecimal("890964e6"))  # 353e6 + 99763e6 + 8765e6 + 779531e6 + 552e6
        self.assertEqual(RR.token_y_subtree_borrowed, UnsignedDecimal("889059e6"))  # 99763e6 + 8765e6 + 779531e6
        self.assertEqual(RL.token_y_subtree_borrowed, UnsignedDecimal("1552e6"))
        self.assertEqual(RRL.token_y_subtree_borrowed, UnsignedDecimal("789296e6"))  # 8765e6 + 779531e6
        self.assertEqual(RRLL.token_y_subtree_borrowed, UnsignedDecimal("780531e6"))  # 779531e6

        # T32876298273
        # 3.3) addTLiq
        liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("2352954287417905205553")  # 17% APR as Q192.64 T32876298273 - T9214298113
        liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("6117681147286553534438")  # 44.2% APR as Q192.64 T32876298273 - T9214298113

        # Apply change that requires fee calculation
        # remove_t_liq
        liq_tree.remove_t_liq(LiqRange(low=8, high=12), UnsignedDecimal("1000"), UnsignedDecimal("1000e18"), UnsignedDecimal("1000e6"))  # RRLL, RL

        # root
        #           total_m_liq = 324198833
        #
        #           earn_x      = 2352954287417905205553 * 492e18 / 324198833 / 2**64 = 193574177654021.169606366690127570750614868262308175138961180
        #           earn_x_sub  = 2352954287417905205553 * 5033e18 / 324198833 / 2**64 = 1980200886448553.95656269014514647070700128448007529567965776
        #
        #           earn_y      = 6117681147286553534438 * 254858e6 / 324198833 / 2**64 = 260707.74837037839600245251693715160678794344236990061534290681026
        #           earn_y_sub  = 6117681147286553534438 * 1145822e6 / 324198833 / 2**64 = 1172122.01952947804057287645615189999290967884478087508680692
        self.assertEqual(int(root.token_x_cumulative_earned_per_m_liq), UnsignedDecimal("1355504472799662736")) # 373601278 + 1354374549470516050 + 936348777891386 + 193574177654021 = 1355504472799662735 (sol losses 1 wei)
        self.assertEqual(int(root.token_x_cumulative_earned_per_m_subtree_liq), UnsignedDecimal("8356976045440416916")) # 2303115199 + 8349223594601778821 + 5772247649074341 + 1980200886448553 = 8356976045440416914 (sol losses 2 wei)
        self.assertEqual(int(root.token_y_cumulative_earned_per_m_liq), UnsignedDecimal("158359634769"))  # 0 + 158351473403 + 7900657 + 260707 = 158359634767 (sol losses 2 wei)
        self.assertEqual(int(root.token_y_cumulative_earned_per_m_subtree_liq), UnsignedDecimal("710730032735"))  # 2 + 710693401861 + 35458749 + 1172122 = 710730032734 (sol losses 1 wei)

        # R
        #           total_m_liq = 324063953 + 8430 * 8 = 324131393
        #
        #           earn_x      = 2352954287417905205553 * 998e18 / 324131393 / 2**64 = 392738261220692.635199129066166314911263418663640357414414483
        #           earn_x_sub  = 2352954287417905205553 * 4541e18 / 324131393 / 2**64 = 1786998441085335.92829583676298721043291301017193473248382381
        #
        #           earn_y      = 6117681147286553534438 * 353e6 / 324131393 / 2**64 = 361.17753121077324707993230558447820693195086120933424789750836934
        #           earn_y_sub  = 6117681147286553534438 * 890964e6 / 324131393 / 2**64 = 911603.90344950531249667084054608793530005288132156736216361373026
        self.assertEqual(int(R.token_x_cumulative_earned_per_m_liq), UnsignedDecimal("2750152275007241348"))  # 757991165 + 2747859799177149412 + 1899736810880077 + 392738261220692 = 2750152275007241346 (sol losses 2 wei)
        self.assertEqual(int(R.token_x_cumulative_earned_per_m_subtree_liq), UnsignedDecimal("7002928263843528708"))  # 1929915382 + 6996304358425988634 + 4836905046539355 + 1786998441085335 = 7002928263843528706 (sol losses 2 wei)
        self.assertEqual(int(R.token_y_cumulative_earned_per_m_liq), UnsignedDecimal("219387194"))  # 0 + 219375887 + 10945 + 361 = 219387193 (sol losses 1 wei)
        self.assertEqual(int(R.token_y_cumulative_earned_per_m_subtree_liq), UnsignedDecimal("552485321387"))  # 1 + 552456845956 + 27563825 + 911603 = 552485321385 (sol losses 2 wei)

        # RR
        #           total_m_liq = 324056493 + (377 + 8430) * 4 = 324091721
        #
        #           earn_x      = 2352954287417905205553 * 765e18 / 324091721 / 2**64 = 301083714644757.116282263044928314612316183509300881282164628
        #           earn_x_sub  = 2352954287417905205553 * 2519e18 / 324091721 / 2**64 = 991411604170121.798581726287809705239770544130626039150029671
        #
        #           earn_y      = 6117681147286553534438 * 99763e6 / 324091721 / 2**64 = 102086.58565055261555338276382365173781133864709615634713615821960
        #           earn_y_sub  = 6117681147286553534438 * 889059e6 / 324091721 / 2**64 = 909766.12323100405793004346924503062625232727813579850073199172604
        self.assertEqual(int(RR.token_x_cumulative_earned_per_m_liq), UnsignedDecimal("2108411777738297593"))  # 581096415 + 2106654304105573173+ 1456389336983247 + 301083714644757 = 2108411777738297592 (sol losses 1 wei)
        self.assertEqual(int(RR.token_x_cumulative_earned_per_m_subtree_liq), UnsignedDecimal("4186900096861593205"))  # 1153837196 + 4183016846975641372 + 2891837127944514 + 991411604170121 = 4186900096861593203 (sol losses 2 wei)
        self.assertEqual(int(RR.token_y_cumulative_earned_per_m_liq), UnsignedDecimal("62011734491"))  # 0 + 62008538706 + 3093698 + 102086 = 62011734490 (sol losses 1 wei)
        self.assertEqual(int(RR.token_y_cumulative_earned_per_m_subtree_liq), UnsignedDecimal("552009051680"))  # 1 + 551980602776 + 27539135 + 909766 = 552009051678 (sol losses 2 wei)

        # RL
        #           total_m_liq = 4444 + (377 + 8430) * 4 = 39672
        #
        #           earn_x      = 2352954287417905205553 * 1024e18 / 39672 / 2**64 = 3292377527956539412.11877691362144195603424231355578266196876
        #           earn_x_sub  = 2352954287417905205553 * 1024e18 / 39672 / 2**64 = 3292377527956539412.11877691362144195603424231355578266196876
        #
        #           earn_y      = 6117681147286553534438 * 1552e6 / 39672 / 2**64 = 12974025.1961037381208809794236997935340918048320067315891063
        #           earn_y_sub  = 6117681147286553534438 * 1552e6 / 39672 / 2**64 = 12974025.1961037381208809794236997935340918048320067315891063
        self.assertEqual(int(RL.token_x_cumulative_earned_per_m_liq), UnsignedDecimal("426914215366679462837"))  # 148929881804 + 423248577958689008325 + 373259731104033296 + 3292377527956539412 = 426914215366679462837
        self.assertEqual(int(RL.token_x_cumulative_earned_per_m_subtree_liq), UnsignedDecimal("426914215366679462837"))  # 148929881804 + 423248577958689008325 + 373259731104033296 + 3292377527956539412 = 426914215366679462837
        self.assertEqual(int(RL.token_y_cumulative_earned_per_m_liq), UnsignedDecimal("2197372595215"))  # 10 + 2197219781185 + 139839995 + 12974025 = 2197372595215
        self.assertEqual(int(RL.token_y_cumulative_earned_per_m_subtree_liq), UnsignedDecimal("2197372595215"))  # 10 + 2197219781185 + 139839995 + 12974025 = 2197372595215

        # RRL
        #           total_m_liq = 287725557 + (9082734 + 377 + 8430) * 2 = 305908639
        #
        #           earn_x      = 2352954287417905205553 * 53e18 / 305908639 / 2**64 = 22099268330799.1616184419285239088656103478160451926038962236
        #           earn_x_sub  = 2352954287417905205553 * 1754e18 / 305908639 / 2**64 = 731360691551353.386391455521338417929821699421571091079886346
        #
        #           earn_y      = 6117681147286553534438 * 8765e6 / 305908639 / 2**64 = 9502.2684149166432853337655386227368949210477797554902569919214852
        #           earn_y_sub  = 6117681147286553534438 * 789296e6 / 305908639 / 2**64 = 855687.67265488270148782656070425233773115839456587443672363898010
        self.assertEqual(int(RRL.token_x_cumulative_earned_per_m_liq), UnsignedDecimal("154755411926283539"))  # 42651943 + 154626414974589533 + 106897640711262 + 22099268330799 = 154755411926283537 (sol losses 2 wei)
        self.assertEqual(int(RRL.token_x_cumulative_earned_per_m_subtree_liq), UnsignedDecimal("2202031695485822407"))  # 606784254 + 2199779563978122803 + 1520770209363996 + 731360691551353 = 2202031695485822406 (sol losses 1 wei)
        self.assertEqual(int(RRL.token_y_cumulative_earned_per_m_liq), UnsignedDecimal("5772079130"))  # 0 + 5771781665 + 287962 + 9502 = 5772079129 (sol losses 1 wei)
        self.assertEqual(int(RRL.token_y_cumulative_earned_per_m_subtree_liq), UnsignedDecimal("519122293207"))  # 1 + 519095539054 + 25898463 + 855687 = 519122293205 (sol losses 2 wei)

        # RRLL
        #           total_m_liq = 287634865 + (45346 + 9082734 + 377 + 8430) * 1 = 296771752
        #
        #           earn_x      = 2352954287417905205553 * 1701e18 / 296771752 / 2**64 = 731097873063750.150068233826063023165648387512288880115659770
        #           earn_x_sub  = 2352954287417905205553 * 1701e18 / 296771752 / 2**64 = 731097873063750.150068233826063023165648387512288880115659770
        #
        #           earn_y      = 6117681147286553534438 * 780531e6 / 296771752 / 2**64 = 872237.41346080959306032387265895687662997868016869971844802082307
        #           earn_y_sub  = 6117681147286553534438 * 780531e6 / 296771752 / 2**64 = 872237.41346080959306032387265895687662997868016869971844802082307
        self.assertEqual(int(RRLL.token_x_cumulative_earned_per_m_liq), UnsignedDecimal("2110306406167095653"))  # 581500584 + 2108117905415037748 + 1457402297493569 + 731097873063750 = 2110306406167095651 (sol losses 2 wei)
        self.assertEqual(int(RRLL.token_x_cumulative_earned_per_m_subtree_liq), UnsignedDecimal("2110306406167095653"))  # 581500584 + 2108117905415037748 + 1457402297493569 + 731097873063750 = 2110306406167095651 (sol losses 2 wei)
        self.assertEqual(int(RRLL.token_y_cumulative_earned_per_m_liq), UnsignedDecimal("529154884359"))  # 1 + 529127613134 + 26398986 + 872237 = 529154884358 (sol losses 1 wei)
        self.assertEqual(int(RRLL.token_y_cumulative_earned_per_m_subtree_liq), UnsignedDecimal("529154884359"))  # 1 + 529127613134 + 26398986 + 872237 = 529154884358 (sol losses 1 wei)

        # t_liq
        self.assertEqual(root.t_liq, UnsignedDecimal("4430"))
        self.assertEqual(R.t_liq, UnsignedDecimal("77"))
        self.assertEqual(RR.t_liq, UnsignedDecimal("82734"))
        self.assertEqual(RL.t_liq, UnsignedDecimal("111"))
        self.assertEqual(RRL.t_liq, UnsignedDecimal("5346"))
        self.assertEqual(RRLL.t_liq, UnsignedDecimal("7634865"))

        # subtree_m_liq
        self.assertEqual(root.subtree_m_liq, UnsignedDecimal("324198833"))  # 8430*16 + 377*8 + 9082734*4 + 1111*4 + 45346*2 + 287634865*1
        self.assertEqual(R.subtree_m_liq, UnsignedDecimal("324063953"))  # 377*8 + 9082734*4 + 1111*4 + 45346*2 + 287634865*1
        self.assertEqual(RR.subtree_m_liq, UnsignedDecimal("324056493"))  # 9082734*4 + 45346*2 + 287634865*1
        self.assertEqual(RL.subtree_m_liq, UnsignedDecimal("4444"))  # 1111*4
        self.assertEqual(RRL.subtree_m_liq, UnsignedDecimal("287725557"))  # 45346*2 + 287634865*1
        self.assertEqual(RRLL.subtree_m_liq, UnsignedDecimal("287634865"))  # 287634865*1

        # borrowed_x
        self.assertEqual(root.token_x_borrowed, UnsignedDecimal("492e18"))
        self.assertEqual(R.token_x_borrowed, UnsignedDecimal("998e18"))
        self.assertEqual(RR.token_x_borrowed, UnsignedDecimal("765e18"))
        self.assertEqual(RL.token_x_borrowed, UnsignedDecimal("24e18"))
        self.assertEqual(RRL.token_x_borrowed, UnsignedDecimal("53e18"))
        self.assertEqual(RRLL.token_x_borrowed, UnsignedDecimal("701e18"))

        # subtree_borrowed_x
        self.assertEqual(root.token_x_subtree_borrowed, UnsignedDecimal("3033e18"))  # 492e18 + 998e18 + 765e18 + 53e18 + 701e18 + 24e18
        self.assertEqual(R.token_x_subtree_borrowed, UnsignedDecimal("2541e18"))  # 998e18 + 765e18 + 53e18 + 701e18 + 24e18
        self.assertEqual(RR.token_x_subtree_borrowed, UnsignedDecimal("1519e18"))  # 765e18 + 53e18 + 701e18
        self.assertEqual(RL.token_x_subtree_borrowed, UnsignedDecimal("24e18"))
        self.assertEqual(RRL.token_x_subtree_borrowed, UnsignedDecimal("754e18"))  # 53e18 + 701e18
        self.assertEqual(RRLL.token_x_subtree_borrowed, UnsignedDecimal("701e18"))  # 701e18

        # borrowed_y
        self.assertEqual(root.token_y_borrowed, UnsignedDecimal("254858e6"))
        self.assertEqual(R.token_y_borrowed, UnsignedDecimal("353e6"))
        self.assertEqual(RR.token_y_borrowed, UnsignedDecimal("99763e6"))
        self.assertEqual(RL.token_y_borrowed, UnsignedDecimal("552e6"))
        self.assertEqual(RRL.token_y_borrowed, UnsignedDecimal("8765e6"))
        self.assertEqual(RRLL.token_y_borrowed, UnsignedDecimal("779531e6"))

        # subtree_borrowed_y
        self.assertEqual(root.token_y_subtree_borrowed, UnsignedDecimal("1143822e6"))  # 254858e6 + 353e6 + 99763e6 + 8765e6 + 779531e6 + 552e6
        self.assertEqual(R.token_y_subtree_borrowed, UnsignedDecimal("888964e6"))  # 353e6 + 99763e6 + 8765e6 + 779531e6 + 552e6
        self.assertEqual(RR.token_y_subtree_borrowed, UnsignedDecimal("888059e6"))  # 99763e6 + 8765e6 + 779531e6
        self.assertEqual(RL.token_y_subtree_borrowed, UnsignedDecimal("552e6"))
        self.assertEqual(RRL.token_y_subtree_borrowed, UnsignedDecimal("788296e6"))  # 8765e6 + 779531e6
        self.assertEqual(RRLL.token_y_subtree_borrowed, UnsignedDecimal("779531e6"))  # 779531e6


'''

    function testLeftAndRightLegBelowPeak() public {

    }

    function testLeftAndRightLegAtOrHigherThanPeak() public {

    }

    function testLeftAndRightLegSameDistanceToStop() public {

    }

    function testLeftLegLowerThanRightLeg() public {

    }

    function testRightLegLowerThanLeftLeg() public {

    }

    function _nodeKey(uint24 depth, uint24 index, uint24 offset) public returns (LKey) {
        uint24 baseStep = uint24(offset / 2 ** depth)

        uint24 range = offset >> depth;
        uint24 base = offset + baseStep * index;
        return LKeyImpl.makeKey(range, base)
    }
}


contract DenseTreeCodeStructureTest is Test {
    Tree public liq_tree;
    using LiqTreeImpl for Tree;
    using LKeyImpl for LKey;
    using FeeRateSnapshotImpl for FeeRateSnapshot;

    function setUp() public {
        # A depth of 4 creates a tree that covers an absolute range of 16 ([0, 15]).
        # ie. A complete tree matching the ascii documentation.
        liq_tree.init(4)
    }

    # NOTE: Technically all these cases are already covered by leftLegOnly + rightLegOnly
    #       I'm not yet sure if this is necessary or not.
    #       Leaning toward no.

    function testLowOutterIfStatementOnly() public {

    }

    function testLowInnerWhileWithoutInnerIf() public {

    }

    function testLowInnerWhileWithInnerIf() public {

    }

    function testHighOutterIfStatementOnly() public {

    }

    function testHighInnerWhileWithoutInnerIf() public {

    }

    function testHighInnerWhileWithInnerIf() public {

    }

}


contract DenseTreeMathmaticalLimitationsTest is Test {
    Tree public liq_tree;
    using LiqTreeImpl for Tree;
    using LKeyImpl for LKey;
    using FeeRateSnapshotImpl for FeeRateSnapshot;

    function setUp() public {
        # A depth of 4 creates a tree that covers an absolute range of 16 ([0, 15]).
        # ie. A complete tree matching the ascii documentation.
        liq_tree.init(4)
    }

    function testNoFeeAccumulationWithoutRate() public {

    }

    function testFeeAccumulationDoesNotRoundUp() public {

    }

    function testNodeTraversedTwiceWithoutRateUpdateDoesNotAccumulateAdditionalFees() public {

    }

    function testFeeAccumulationDoesNotOverflowUint256() public {

    }

    function testFeeAccumulationAccuracyWithRidiculousRates() public {

    }
}
'''
