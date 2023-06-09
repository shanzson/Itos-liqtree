from unittest import TestCase

from FloatingPoint.UnsignedDecimal import UnsignedDecimal
from Tree.LiquidityTree import LiquidityTree, LiqNode, LiqRange


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
#
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
#          /   \          /   \          /   \          /   \            /   \          /   \          /   \          /   \
#         /     \        /     \        /     \        /     \          /     \        /     \        /     \        /     \
#   LLLL(0) LLLR(1) LLRL(2) LLRR(3) LRLL(4) LRLR(5) LRRL(6) LRRR(7) RLLL(8) RLLR(9) RLRL(10) RLRR(11) RRLL(12) RRLR(13) RRRL(14) RRRR(15)


class TestDenseLiquidityTreeSolTruncation(TestCase):
    def setUp(self) -> None:
        self.liq_tree = LiquidityTree(depth=4, sol_truncation=True)

    def test_root_only(self):
        liq_tree: LiquidityTree = self.liq_tree

        liq_tree.add_wide_m_liq(UnsignedDecimal("8430"))
        liq_tree.add_wide_t_liq(UnsignedDecimal("4381"), UnsignedDecimal("832e18"), UnsignedDecimal("928e6"))

        liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("113712805933826")  # 5.4% APR as Q192.64 = 0.054 * 3600 / (365 * 24 * 60 * 60) * 2^64 = 113712805933826
        liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("113712805933826")

        # Verify root state is as expected
        root: LiqNode = liq_tree.root
        self.assertEqual(root.m_liq, UnsignedDecimal("8430"))
        self.assertEqual(root.subtree_m_liq, UnsignedDecimal("134880"))
        self.assertEqual(root.t_liq, UnsignedDecimal("4381"))
        self.assertEqual(root.token_x_borrow, UnsignedDecimal("832e18"))
        self.assertEqual(root.token_x_subtree_borrow, UnsignedDecimal("832e18"))
        self.assertEqual(root.token_y_borrow, UnsignedDecimal("928e6"))
        self.assertEqual(root.token_y_subtree_borrow, UnsignedDecimal("928e6"))

        # Testing add_wide_m_liq
        liq_tree.add_wide_m_liq(UnsignedDecimal("9287"))

        # earn_x      = 113712805933826 * 832e18 / 134880 / 2**64 = 38024667284.1612625482053537908689136045718673850859328662514
        # earn_y      = 113712805933826 * 928e6 / 134880 / 2**64  = 0.0424121288938721774576136638436614805589455443910573866585112692
        self.assertEqual(root.token_x_cumulative_earned_per_m_liq, UnsignedDecimal("38024667284"))
        self.assertEqual(root.token_x_cumulative_earned_per_m_subtree_liq, UnsignedDecimal("38024667284"))
        self.assertEqual(root.token_y_cumulative_earned_per_m_liq, UnsignedDecimal("0"))
        self.assertEqual(root.token_y_cumulative_earned_per_m_subtree_liq, UnsignedDecimal("0"))

        self.assertEqual(root.m_liq, UnsignedDecimal("17717"))
        self.assertEqual(root.subtree_m_liq, UnsignedDecimal("283472"))
        self.assertEqual(root.t_liq, UnsignedDecimal("4381"))
        self.assertEqual(root.token_x_borrow, UnsignedDecimal("832e18"))
        self.assertEqual(root.token_x_subtree_borrow, UnsignedDecimal("832e18"))
        self.assertEqual(root.token_y_borrow, UnsignedDecimal("928e6"))
        self.assertEqual(root.token_y_subtree_borrow, UnsignedDecimal("928e6"))

        # Testing remove_wide_m_liq
        liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("74672420010376264941568")
        liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("74672420010376264941568")

        liq_tree.remove_wide_m_liq(UnsignedDecimal("3682"))

        # earn_x      = 74672420010376264941568 * 832e18 / 283472 / 2**64 = 11881018231077496190.0999040469605463678952418581023875373934
        # earn_y      = 74672420010376264941568 * 928e6 / 283472 / 2**64  = 13251904.9500479765197268160523790709488062313032680476378619
        self.assertEqual(root.token_x_cumulative_earned_per_m_liq, UnsignedDecimal("11881018269102163474"))  # 11881018231077496190 + 38024667284 = 11881018269102163474
        self.assertEqual(root.token_x_cumulative_earned_per_m_subtree_liq, UnsignedDecimal("11881018269102163474"))  # 11881018231077496190 + 38024667284 = 11881018269102163474
        self.assertEqual(root.token_y_cumulative_earned_per_m_liq, UnsignedDecimal("13251904"))
        self.assertEqual(root.token_y_cumulative_earned_per_m_subtree_liq, UnsignedDecimal("13251904"))

        self.assertEqual(root.m_liq, UnsignedDecimal("14035"))
        self.assertEqual(root.subtree_m_liq, UnsignedDecimal("224560"))
        self.assertEqual(root.t_liq, UnsignedDecimal("4381"))
        self.assertEqual(root.token_x_borrow, UnsignedDecimal("832e18"))
        self.assertEqual(root.token_x_subtree_borrow, UnsignedDecimal("832e18"))
        self.assertEqual(root.token_y_borrow, UnsignedDecimal("928e6"))
        self.assertEqual(root.token_y_subtree_borrow, UnsignedDecimal("928e6"))

        # Testing add_wide_t_liq
        liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("6932491854677024")
        liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("6932491854677024")

        liq_tree.add_wide_t_liq(UnsignedDecimal("7287"), UnsignedDecimal("9184e18"), UnsignedDecimal("7926920e6"))

        # earn_x      = 6932491854677024 * 832e18 / 224560 / 2**64 = 1392388963085.50927075184684754182568989829487082029858389739
        # earn_y      = 6932491854677024 * 928e6 / 224560 / 2**64  = 1.5530492280569141866078291761043440387327135097611022666547915924
        self.assertEqual(root.token_x_cumulative_earned_per_m_liq, UnsignedDecimal("11881019661491126559"))  # 11881018269102163474 + 1392388963085 = 11881019661491126559
        self.assertEqual(root.token_x_cumulative_earned_per_m_subtree_liq, UnsignedDecimal("11881019661491126559"))  # 11881018269102163474 + 1392388963085 = 11881019661491126559
        self.assertEqual(root.token_y_cumulative_earned_per_m_liq, UnsignedDecimal("13251905"))
        self.assertEqual(root.token_y_cumulative_earned_per_m_subtree_liq, UnsignedDecimal("13251905"))

        self.assertEqual(root.m_liq, UnsignedDecimal("14035"))
        self.assertEqual(root.subtree_m_liq, UnsignedDecimal("224560"))
        self.assertEqual(root.t_liq, UnsignedDecimal("11668"))
        self.assertEqual(root.token_x_borrow, UnsignedDecimal("10016e18"))
        self.assertEqual(root.token_x_subtree_borrow, UnsignedDecimal("10016e18"))
        self.assertEqual(root.token_y_borrow, UnsignedDecimal("7927848e6"))
        self.assertEqual(root.token_y_subtree_borrow, UnsignedDecimal("7927848e6"))

        # Testing remove_wide_t_liq
        liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("1055375100301031600000000")
        liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("1055375100301031600000000")

        liq_tree.remove_wide_t_liq(UnsignedDecimal("4923"), UnsignedDecimal("222e18"), UnsignedDecimal("786e6"))

        # earn_x      = 1055375100301031600000000 * 10016e18 / 224560 / 2**64  = 2551814126505030241953.87164028103035638433335980020216618053
        # earn_y      = 1055375100301031600000000 * 7927848e6 / 224560 / 2**64 = 2019807759503.25988354767545683493270255599285721099372431609
        self.assertEqual(root.token_x_cumulative_earned_per_m_liq,
                         UnsignedDecimal("2563695146166521368512"))  # 2551814126505030241953 + 11881019661491126559 = 2563695146166521368512
        self.assertEqual(root.token_x_cumulative_earned_per_m_subtree_liq,
                         UnsignedDecimal("2563695146166521368512"))  # 2551814126505030241953 + 11881019661491126559 = 2563695146166521368512
        self.assertEqual(root.token_y_cumulative_earned_per_m_liq, UnsignedDecimal("2019821011408"))  # 2019807759503 + 13251905 = 2019821011408
        self.assertEqual(root.token_y_cumulative_earned_per_m_subtree_liq, UnsignedDecimal("2019821011408"))  # 2019807759503 + 13251905 = 2019821011408

        self.assertEqual(root.m_liq, UnsignedDecimal("14035"))
        self.assertEqual(root.subtree_m_liq, UnsignedDecimal("224560"))
        self.assertEqual(root.t_liq, UnsignedDecimal("6745"))
        self.assertEqual(root.token_x_borrow, UnsignedDecimal("9794e18"))
        self.assertEqual(root.token_x_subtree_borrow, UnsignedDecimal("9794e18"))
        self.assertEqual(root.token_y_borrow, UnsignedDecimal("7927062e6"))
        self.assertEqual(root.token_y_subtree_borrow, UnsignedDecimal("7927062e6"))

    def test_left_leg_only(self):
        # Mirrors test_right_leg_only
        # Manual calculations are shown there.

        liq_tree: LiquidityTree = self.liq_tree

        root: LiqNode = liq_tree.root
        L: LiqNode = liq_tree.nodes[(8 << 24) | 16]  # 134217744
        LL: LiqNode = liq_tree.nodes[(4 << 24) | 16]  # 67108880
        LR: LiqNode = liq_tree.nodes[(4 << 24) | 20]  # 67108884
        LLR: LiqNode = liq_tree.nodes[(2 << 24) | 18]  # 33554450
        LLRR: LiqNode = liq_tree.nodes[(1 << 24) | 19]  # 16777235

        # T0 - populate tree with data excluding fee calculations
        liq_tree.add_wide_m_liq(UnsignedDecimal("8430"))  # root
        liq_tree.add_m_liq(LiqRange(low=0, high=7), UnsignedDecimal("377"))  # L
        liq_tree.add_m_liq(LiqRange(low=0, high=3), UnsignedDecimal("9082734"))  # LL
        liq_tree.add_m_liq(LiqRange(low=4, high=7), UnsignedDecimal("1111"))  # LR
        liq_tree.add_m_liq(LiqRange(low=2, high=3), UnsignedDecimal("45346"))  # LLR
        liq_tree.add_m_liq(LiqRange(low=3, high=3), UnsignedDecimal("287634865"))  # LLRR

        liq_tree.add_wide_t_liq(UnsignedDecimal("4430"), UnsignedDecimal("492e18"), UnsignedDecimal("254858e6"))  # root
        liq_tree.add_t_liq(LiqRange(low=0, high=7), UnsignedDecimal("77"), UnsignedDecimal("998e18"), UnsignedDecimal("353e6"))  # L
        liq_tree.add_t_liq(LiqRange(low=0, high=3), UnsignedDecimal("82734"), UnsignedDecimal("765e18"), UnsignedDecimal("99763e6"))  # LL
        liq_tree.add_t_liq(LiqRange(low=4, high=7), UnsignedDecimal("111"), UnsignedDecimal("24e18"), UnsignedDecimal("552e6"))  # LR
        liq_tree.add_t_liq(LiqRange(low=2, high=3), UnsignedDecimal("5346"), UnsignedDecimal("53e18"), UnsignedDecimal("8765e6"))  # LLR
        liq_tree.add_t_liq(LiqRange(low=3, high=3), UnsignedDecimal("7634865"), UnsignedDecimal("701e18"), UnsignedDecimal("779531e6"))  # LLRR

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

        # borrow_x
        self.assertEqual(root.token_x_borrow, UnsignedDecimal("492e18"))
        self.assertEqual(L.token_x_borrow, UnsignedDecimal("998e18"))
        self.assertEqual(LL.token_x_borrow, UnsignedDecimal("765e18"))
        self.assertEqual(LR.token_x_borrow, UnsignedDecimal("24e18"))
        self.assertEqual(LLR.token_x_borrow, UnsignedDecimal("53e18"))
        self.assertEqual(LLRR.token_x_borrow, UnsignedDecimal("701e18"))

        # subtree_borrow_x
        self.assertEqual(root.token_x_subtree_borrow, UnsignedDecimal("3033e18"))
        self.assertEqual(L.token_x_subtree_borrow, UnsignedDecimal("2541e18"))
        self.assertEqual(LL.token_x_subtree_borrow, UnsignedDecimal("1519e18"))
        self.assertEqual(LR.token_x_subtree_borrow, UnsignedDecimal("24e18"))
        self.assertEqual(LLR.token_x_subtree_borrow, UnsignedDecimal("754e18"))
        self.assertEqual(LLRR.token_x_subtree_borrow, UnsignedDecimal("701e18"))

        # borrow_y
        self.assertEqual(root.token_y_borrow, UnsignedDecimal("254858e6"))
        self.assertEqual(L.token_y_borrow, UnsignedDecimal("353e6"))
        self.assertEqual(LL.token_y_borrow, UnsignedDecimal("99763e6"))
        self.assertEqual(LR.token_y_borrow, UnsignedDecimal("552e6"))
        self.assertEqual(LLR.token_y_borrow, UnsignedDecimal("8765e6"))
        self.assertEqual(LLRR.token_y_borrow, UnsignedDecimal("779531e6"))

        # subtree_borrow_y
        self.assertEqual(root.token_y_subtree_borrow, UnsignedDecimal("1143822e6"))
        self.assertEqual(L.token_y_subtree_borrow, UnsignedDecimal("888964e6"))
        self.assertEqual(LL.token_y_subtree_borrow, UnsignedDecimal("888059e6"))
        self.assertEqual(LR.token_y_subtree_borrow, UnsignedDecimal("552e6"))
        self.assertEqual(LLR.token_y_subtree_borrow, UnsignedDecimal("788296e6"))
        self.assertEqual(LLRR.token_y_subtree_borrow, UnsignedDecimal("779531e6"))

        # T98273
        liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("4541239648278065")
        liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("13278814667749784")

        # Apply change that requires fee calculation
        # add_m_liq
        liq_tree.add_m_liq(LiqRange(low=3, high=7), UnsignedDecimal("2734"))  # LLRR, LR

        # root
        self.assertEqual(root.token_x_cumulative_earned_per_m_liq, UnsignedDecimal("373601278"))
        self.assertEqual(root.token_x_cumulative_earned_per_m_subtree_liq, UnsignedDecimal("2303115199"))
        self.assertEqual(root.token_y_cumulative_earned_per_m_liq, UnsignedDecimal("0"))
        self.assertEqual(root.token_y_cumulative_earned_per_m_subtree_liq, UnsignedDecimal("2"))

        # L
        self.assertEqual(L.token_x_cumulative_earned_per_m_liq, UnsignedDecimal("757991165"))
        self.assertEqual(L.token_x_cumulative_earned_per_m_subtree_liq, UnsignedDecimal("1929915382"))
        self.assertEqual(L.token_y_cumulative_earned_per_m_liq, UnsignedDecimal("0"))
        self.assertEqual(L.token_y_cumulative_earned_per_m_subtree_liq, UnsignedDecimal("1"))

        # LL
        self.assertEqual(LL.token_x_cumulative_earned_per_m_liq, UnsignedDecimal("581096415"))
        self.assertEqual(LL.token_x_cumulative_earned_per_m_subtree_liq, UnsignedDecimal("1153837196"))
        self.assertEqual(LL.token_y_cumulative_earned_per_m_liq, UnsignedDecimal("0"))
        self.assertEqual(LL.token_y_cumulative_earned_per_m_subtree_liq, UnsignedDecimal("1"))

        # LR
        self.assertEqual(LR.token_x_cumulative_earned_per_m_liq, UnsignedDecimal("148929881804"))
        self.assertEqual(LR.token_x_cumulative_earned_per_m_subtree_liq, UnsignedDecimal("148929881804"))
        self.assertEqual(LR.token_y_cumulative_earned_per_m_liq, UnsignedDecimal("10"))
        self.assertEqual(LR.token_y_cumulative_earned_per_m_subtree_liq, UnsignedDecimal("10"))

        # LLR
        self.assertEqual(LLR.token_x_cumulative_earned_per_m_liq, UnsignedDecimal("42651943"))
        self.assertEqual(LLR.token_x_cumulative_earned_per_m_subtree_liq, UnsignedDecimal("606784254"))
        self.assertEqual(LLR.token_y_cumulative_earned_per_m_liq, UnsignedDecimal("0"))
        self.assertEqual(LLR.token_y_cumulative_earned_per_m_subtree_liq, UnsignedDecimal("1"))

        # LLRR
        self.assertEqual(LLRR.token_x_cumulative_earned_per_m_liq, UnsignedDecimal("581500584"))
        self.assertEqual(LLRR.token_x_cumulative_earned_per_m_subtree_liq, UnsignedDecimal("581500584"))
        self.assertEqual(LLRR.token_y_cumulative_earned_per_m_liq, UnsignedDecimal("1"))
        self.assertEqual(LLRR.token_y_cumulative_earned_per_m_subtree_liq, UnsignedDecimal("1"))

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
        self.assertEqual(root.token_x_cumulative_earned_per_m_liq, UnsignedDecimal("1354374549844117328"))
        self.assertEqual(root.token_x_cumulative_earned_per_m_subtree_liq, UnsignedDecimal("8349223596904894020"))
        self.assertEqual(root.token_y_cumulative_earned_per_m_liq, UnsignedDecimal("158351473403"))
        self.assertEqual(root.token_y_cumulative_earned_per_m_subtree_liq, UnsignedDecimal("710693401863"))

        # L
        self.assertEqual(L.token_x_cumulative_earned_per_m_liq, UnsignedDecimal("2747859799935140577"))
        self.assertEqual(L.token_x_cumulative_earned_per_m_subtree_liq, UnsignedDecimal("6996304360355904016"))
        self.assertEqual(L.token_y_cumulative_earned_per_m_liq, UnsignedDecimal("219375887"))
        self.assertEqual(L.token_y_cumulative_earned_per_m_subtree_liq, UnsignedDecimal("552456845956"))

        # LL
        self.assertEqual(LL.token_x_cumulative_earned_per_m_liq, UnsignedDecimal("2106654304686669588"))
        self.assertEqual(LL.token_x_cumulative_earned_per_m_subtree_liq, UnsignedDecimal("4183016848129478568"))
        self.assertEqual(LL.token_y_cumulative_earned_per_m_liq, UnsignedDecimal("62008538706"))
        self.assertEqual(LL.token_y_cumulative_earned_per_m_subtree_liq, UnsignedDecimal("551980602777"))

        # LR
        self.assertEqual(LR.token_x_cumulative_earned_per_m_liq, UnsignedDecimal("423248578107618890129"))
        self.assertEqual(LR.token_x_cumulative_earned_per_m_subtree_liq, UnsignedDecimal("423248578107618890129"))
        self.assertEqual(LR.token_y_cumulative_earned_per_m_liq, UnsignedDecimal("2197219781195"))
        self.assertEqual(LR.token_y_cumulative_earned_per_m_subtree_liq, UnsignedDecimal("2197219781195"))

        # LLR
        self.assertEqual(LLR.token_x_cumulative_earned_per_m_liq, UnsignedDecimal("154626415017241476"))
        self.assertEqual(LLR.token_x_cumulative_earned_per_m_subtree_liq, UnsignedDecimal("2199779564584907057"))
        self.assertEqual(LLR.token_y_cumulative_earned_per_m_liq, UnsignedDecimal("5771781665"))
        self.assertEqual(LLR.token_y_cumulative_earned_per_m_subtree_liq, UnsignedDecimal("519095539055"))

        # LLRR
        self.assertEqual(LLRR.token_x_cumulative_earned_per_m_liq, UnsignedDecimal("2108117905996538332"))
        self.assertEqual(LLRR.token_x_cumulative_earned_per_m_subtree_liq, UnsignedDecimal("2108117905996538332"))
        self.assertEqual(LLRR.token_y_cumulative_earned_per_m_liq, UnsignedDecimal("529127613135"))
        self.assertEqual(LLRR.token_y_cumulative_earned_per_m_subtree_liq, UnsignedDecimal("529127613135"))

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
        self.assertEqual(root.token_x_cumulative_earned_per_m_liq, UnsignedDecimal("1355310898622008714"))
        self.assertEqual(root.token_x_cumulative_earned_per_m_subtree_liq, UnsignedDecimal("8354995844553968361"))
        self.assertEqual(root.token_y_cumulative_earned_per_m_liq, UnsignedDecimal("158359374060"))
        self.assertEqual(root.token_y_cumulative_earned_per_m_subtree_liq, UnsignedDecimal("710728860612"))

        # L
        self.assertEqual(L.token_x_cumulative_earned_per_m_liq, UnsignedDecimal("2749759536746020654"))
        self.assertEqual(L.token_x_cumulative_earned_per_m_subtree_liq, UnsignedDecimal("7001141265402443371"))
        self.assertEqual(L.token_y_cumulative_earned_per_m_liq, UnsignedDecimal("219386832"))
        self.assertEqual(L.token_y_cumulative_earned_per_m_subtree_liq, UnsignedDecimal("552484409781"))

        # LL
        self.assertEqual(LL.token_x_cumulative_earned_per_m_liq, UnsignedDecimal("2108110694023652835"))
        self.assertEqual(LL.token_x_cumulative_earned_per_m_subtree_liq, UnsignedDecimal("4185908685257423082"))
        self.assertEqual(LL.token_y_cumulative_earned_per_m_liq, UnsignedDecimal("62011632404"))
        self.assertEqual(LL.token_y_cumulative_earned_per_m_subtree_liq, UnsignedDecimal("552008141912"))

        # LR
        self.assertEqual(LR.token_x_cumulative_earned_per_m_liq, UnsignedDecimal("423621837838722923425"))
        self.assertEqual(LR.token_x_cumulative_earned_per_m_subtree_liq, UnsignedDecimal("423621837838722923425"))
        self.assertEqual(LR.token_y_cumulative_earned_per_m_liq, UnsignedDecimal("2197359621190"))
        self.assertEqual(LR.token_y_cumulative_earned_per_m_subtree_liq, UnsignedDecimal("2197359621190"))

        # LLR
        self.assertEqual(LLR.token_x_cumulative_earned_per_m_liq, UnsignedDecimal("154733312657952738"))
        self.assertEqual(LLR.token_x_cumulative_earned_per_m_subtree_liq, UnsignedDecimal("2201300334794271053"))
        self.assertEqual(LLR.token_y_cumulative_earned_per_m_liq, UnsignedDecimal("5772069627"))
        self.assertEqual(LLR.token_y_cumulative_earned_per_m_subtree_liq, UnsignedDecimal("519121437518"))

        # LLRR
        self.assertEqual(LLRR.token_x_cumulative_earned_per_m_liq, UnsignedDecimal("2109575308294031901"))
        self.assertEqual(LLRR.token_x_cumulative_earned_per_m_subtree_liq, UnsignedDecimal("2109575308294031901"))
        self.assertEqual(LLRR.token_y_cumulative_earned_per_m_liq, UnsignedDecimal("529154012121"))
        self.assertEqual(LLRR.token_y_cumulative_earned_per_m_subtree_liq, UnsignedDecimal("529154012121"))

        # t_liq
        self.assertEqual(root.t_liq, UnsignedDecimal("4430"))
        self.assertEqual(L.t_liq, UnsignedDecimal("77"))
        self.assertEqual(LL.t_liq, UnsignedDecimal("82734"))
        self.assertEqual(LR.t_liq, UnsignedDecimal("1111"))
        self.assertEqual(LLR.t_liq, UnsignedDecimal("5346"))
        self.assertEqual(LLRR.t_liq, UnsignedDecimal("7635865"))

        # borrow_x
        self.assertEqual(root.token_x_borrow, UnsignedDecimal("492e18"))
        self.assertEqual(L.token_x_borrow, UnsignedDecimal("998e18"))
        self.assertEqual(LL.token_x_borrow, UnsignedDecimal("765e18"))
        self.assertEqual(LR.token_x_borrow, UnsignedDecimal("1024e18"))
        self.assertEqual(LLR.token_x_borrow, UnsignedDecimal("53e18"))
        self.assertEqual(LLRR.token_x_borrow, UnsignedDecimal("1701e18"))

        # subtree_borrow_x
        self.assertEqual(root.token_x_subtree_borrow, UnsignedDecimal("5033e18"))
        self.assertEqual(L.token_x_subtree_borrow, UnsignedDecimal("4541e18"))
        self.assertEqual(LL.token_x_subtree_borrow, UnsignedDecimal("2519e18"))
        self.assertEqual(LR.token_x_subtree_borrow, UnsignedDecimal("1024e18"))
        self.assertEqual(LLR.token_x_subtree_borrow, UnsignedDecimal("1754e18"))
        self.assertEqual(LLRR.token_x_subtree_borrow, UnsignedDecimal("1701e18"))

        # borrow_y
        self.assertEqual(root.token_y_borrow, UnsignedDecimal("254858e6"))
        self.assertEqual(L.token_y_borrow, UnsignedDecimal("353e6"))
        self.assertEqual(LL.token_y_borrow, UnsignedDecimal("99763e6"))
        self.assertEqual(LR.token_y_borrow, UnsignedDecimal("1552e6"))
        self.assertEqual(LLR.token_y_borrow, UnsignedDecimal("8765e6"))
        self.assertEqual(LLRR.token_y_borrow, UnsignedDecimal("780531e6"))

        # subtree_borrow_y
        self.assertEqual(root.token_y_subtree_borrow, UnsignedDecimal("1145822e6"))
        self.assertEqual(L.token_y_subtree_borrow, UnsignedDecimal("890964e6"))
        self.assertEqual(LL.token_y_subtree_borrow, UnsignedDecimal("889059e6"))
        self.assertEqual(LR.token_y_subtree_borrow, UnsignedDecimal("1552e6"))
        self.assertEqual(LLR.token_y_subtree_borrow, UnsignedDecimal("789296e6"))
        self.assertEqual(LLRR.token_y_subtree_borrow, UnsignedDecimal("780531e6"))

        # T32876298273
        # 3.3) addTLiq
        liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("2352954287417905205553")
        liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("6117681147286553534438")

        # Apply change that requires fee calculation
        # add_t_liq
        liq_tree.remove_t_liq(LiqRange(low=3, high=7), UnsignedDecimal("1000"), UnsignedDecimal("1000e18"), UnsignedDecimal("1000e6"))  # LLRR, LR

        # root
        self.assertEqual(root.token_x_cumulative_earned_per_m_liq, UnsignedDecimal("1355504472799662735"))
        self.assertEqual(root.token_x_cumulative_earned_per_m_subtree_liq, UnsignedDecimal("8356976045440416914"))
        self.assertEqual(root.token_y_cumulative_earned_per_m_liq, UnsignedDecimal("158359634767"))
        self.assertEqual(root.token_y_cumulative_earned_per_m_subtree_liq, UnsignedDecimal("710730032734"))

        # L
        self.assertEqual(L.token_x_cumulative_earned_per_m_liq, UnsignedDecimal("2750152275007241346"))
        self.assertEqual(L.token_x_cumulative_earned_per_m_subtree_liq, UnsignedDecimal("7002928263843528706"))
        self.assertEqual(L.token_y_cumulative_earned_per_m_liq, UnsignedDecimal("219387193"))
        self.assertEqual(L.token_y_cumulative_earned_per_m_subtree_liq, UnsignedDecimal("552485321384"))

        # LL
        self.assertEqual(LL.token_x_cumulative_earned_per_m_liq, UnsignedDecimal("2108411777738297592"))
        self.assertEqual(LL.token_x_cumulative_earned_per_m_subtree_liq, UnsignedDecimal("4186900096861593203"))
        self.assertEqual(LL.token_y_cumulative_earned_per_m_liq, UnsignedDecimal("62011734490"))
        self.assertEqual(LL.token_y_cumulative_earned_per_m_subtree_liq, UnsignedDecimal("552009051678"))

        # LR
        self.assertEqual(LR.token_x_cumulative_earned_per_m_liq, UnsignedDecimal("426914215366679462837"))
        self.assertEqual(LR.token_x_cumulative_earned_per_m_subtree_liq, UnsignedDecimal("426914215366679462837"))
        self.assertEqual(LR.token_y_cumulative_earned_per_m_liq, UnsignedDecimal("2197372595215"))
        self.assertEqual(LR.token_y_cumulative_earned_per_m_subtree_liq, UnsignedDecimal("2197372595215"))

        # LLR
        self.assertEqual(LLR.token_x_cumulative_earned_per_m_liq, UnsignedDecimal("154755411926283537"))
        self.assertEqual(LLR.token_x_cumulative_earned_per_m_subtree_liq, UnsignedDecimal("2202031695485822406"))
        self.assertEqual(LLR.token_y_cumulative_earned_per_m_liq, UnsignedDecimal("5772079129"))
        self.assertEqual(LLR.token_y_cumulative_earned_per_m_subtree_liq, UnsignedDecimal("519122293205"))

        # LLRR
        self.assertEqual(LLRR.token_x_cumulative_earned_per_m_liq, UnsignedDecimal("2110306406167095651"))
        self.assertEqual(LLRR.token_x_cumulative_earned_per_m_subtree_liq, UnsignedDecimal("2110306406167095651"))
        self.assertEqual(LLRR.token_y_cumulative_earned_per_m_liq, UnsignedDecimal("529154884358"))
        self.assertEqual(LLRR.token_y_cumulative_earned_per_m_subtree_liq, UnsignedDecimal("529154884358"))

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

        # borrow_x
        self.assertEqual(root.token_x_borrow, UnsignedDecimal("492e18"))
        self.assertEqual(L.token_x_borrow, UnsignedDecimal("998e18"))
        self.assertEqual(LL.token_x_borrow, UnsignedDecimal("765e18"))
        self.assertEqual(LR.token_x_borrow, UnsignedDecimal("24e18"))
        self.assertEqual(LLR.token_x_borrow, UnsignedDecimal("53e18"))
        self.assertEqual(LLRR.token_x_borrow, UnsignedDecimal("701e18"))

        # subtree_borrow_x
        self.assertEqual(root.token_x_subtree_borrow, UnsignedDecimal("3033e18"))
        self.assertEqual(L.token_x_subtree_borrow, UnsignedDecimal("2541e18"))
        self.assertEqual(LL.token_x_subtree_borrow, UnsignedDecimal("1519e18"))
        self.assertEqual(LR.token_x_subtree_borrow, UnsignedDecimal("24e18"))
        self.assertEqual(LLR.token_x_subtree_borrow, UnsignedDecimal("754e18"))
        self.assertEqual(LLRR.token_x_subtree_borrow, UnsignedDecimal("701e18"))

        # borrow_y
        self.assertEqual(root.token_y_borrow, UnsignedDecimal("254858e6"))
        self.assertEqual(L.token_y_borrow, UnsignedDecimal("353e6"))
        self.assertEqual(LL.token_y_borrow, UnsignedDecimal("99763e6"))
        self.assertEqual(LR.token_y_borrow, UnsignedDecimal("552e6"))
        self.assertEqual(LLR.token_y_borrow, UnsignedDecimal("8765e6"))
        self.assertEqual(LLRR.token_y_borrow, UnsignedDecimal("779531e6"))

        # subtree_borrow_y
        self.assertEqual(root.token_y_subtree_borrow, UnsignedDecimal("1143822e6"))
        self.assertEqual(L.token_y_subtree_borrow, UnsignedDecimal("888964e6"))
        self.assertEqual(LL.token_y_subtree_borrow, UnsignedDecimal("888059e6"))
        self.assertEqual(LR.token_y_subtree_borrow, UnsignedDecimal("552e6"))
        self.assertEqual(LLR.token_y_subtree_borrow, UnsignedDecimal("788296e6"))
        self.assertEqual(LLRR.token_y_subtree_borrow, UnsignedDecimal("779531e6"))

    def test_simple_example(self):
        liq_tree: LiquidityTree = self.liq_tree

        RL: LiqNode = liq_tree.nodes[(4 << 24) | 24]

        liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("4541239648278065")

        # RL
        liq_tree.add_m_liq(LiqRange(low=8, high=11), UnsignedDecimal("1111"))
        liq_tree.add_t_liq(LiqRange(low=8, high=11), UnsignedDecimal("111"), UnsignedDecimal("24e18"), UnsignedDecimal("0"))

        # RLL
        liq_tree.add_m_liq(LiqRange(low=8, high=9), UnsignedDecimal("20"))
        liq_tree.add_t_liq(LiqRange(low=8, high=9), UnsignedDecimal("20"), UnsignedDecimal("14e18"), UnsignedDecimal("0"))

        # RLLR
        liq_tree.add_m_liq(LiqRange(low=9, high=9), UnsignedDecimal("4"))
        liq_tree.add_t_liq(LiqRange(low=9, high=9), UnsignedDecimal("4"), UnsignedDecimal("4e18"), UnsignedDecimal("0"))

        # Trigger Fees
        liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("4541239648278065")
        liq_tree.remove_t_liq(LiqRange(low=8, high=9), UnsignedDecimal("20"), UnsignedDecimal("14e18"), UnsignedDecimal("0"))
        liq_tree.add_t_liq(LiqRange(low=8, high=9), UnsignedDecimal("20"), UnsignedDecimal("14e18"), UnsignedDecimal("0"))

        self.assertEqual(RL.subtree_m_liq, 4488)
        self.assertEqual(RL.token_x_borrow, 24e18)
        self.assertEqual(RL.token_x_subtree_borrow, 42e18)
        self.assertEqual(RL.token_x_cumulative_earned_per_m_liq, 1316476441828)
        self.assertEqual(RL.token_x_cumulative_earned_per_m_subtree_liq, 2303833773200)

        '''
                  m_liq         borrowX
        [8]   =>  1131            38e18
        [9]   =>  1135            42e18
        [10]  =>  1111            24e18
        [11]  =>  1111            24e18


        RL
        feesX 8-11
            earn_x     = 4541239648278065 * 24e18 / 4488 / 2**64 = 1316476441828.98024547770748054585843701861838605952135381851
            earn_sub_x = 4541239648278065 * 42e18 / 4488 / 2**64 = 2303833773200.71542958598809095525226478258217560416236918240

        RL
        vs Tree
            4488       = 1131 + 1131 + 1135 + 1111
            earn_x     = 4541239648278065 * (min X?) / 4488 / 2**64 = 1317650818672.71706996073844172386544722113276463762975823762
            earn_sub_x = 4541239648278065 * (max X?) / 4488 / 2**64 = 2086280462898.46869410450253272945362476679354400958045054290

        '''

    def test_right_leg_only(self):
        liq_tree: LiquidityTree = self.liq_tree

        root: LiqNode = liq_tree.root
        R: LiqNode = liq_tree.nodes[(8 << 24) | 24]
        RR: LiqNode = liq_tree.nodes[(4 << 24) | 28]
        RL: LiqNode = liq_tree.nodes[(4 << 24) | 24]
        RRL: LiqNode = liq_tree.nodes[(2 << 24) | 28]
        RRLL: LiqNode = liq_tree.nodes[(1 << 24) | 28]

        # T0 - populate tree with data excluding fee calculations
        liq_tree.add_wide_m_liq(UnsignedDecimal("8430"))  # root
        liq_tree.add_m_liq(LiqRange(low=8, high=15), UnsignedDecimal("377"))  # R
        liq_tree.add_m_liq(LiqRange(low=12, high=15), UnsignedDecimal("9082734"))  # RR
        liq_tree.add_m_liq(LiqRange(low=8, high=11), UnsignedDecimal("1111"))  # RL
        liq_tree.add_m_liq(LiqRange(low=12, high=13), UnsignedDecimal("45346"))  # RRL
        liq_tree.add_m_liq(LiqRange(low=12, high=12), UnsignedDecimal("287634865"))  # RRLL

        liq_tree.add_wide_t_liq(UnsignedDecimal("4430"), UnsignedDecimal("492e18"), UnsignedDecimal("254858e6"))  # root
        liq_tree.add_t_liq(LiqRange(low=8, high=15), UnsignedDecimal("77"), UnsignedDecimal("998e18"), UnsignedDecimal("353e6"))  # R
        liq_tree.add_t_liq(LiqRange(low=12, high=15), UnsignedDecimal("82734"), UnsignedDecimal("765e18"), UnsignedDecimal("99763e6"))  # RR
        liq_tree.add_t_liq(LiqRange(low=8, high=11), UnsignedDecimal("111"), UnsignedDecimal("24e18"), UnsignedDecimal("552e6"))  # RL
        liq_tree.add_t_liq(LiqRange(low=12, high=13), UnsignedDecimal("5346"), UnsignedDecimal("53e18"), UnsignedDecimal("8765e6"))  # RRL
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
        self.assertEqual(root.subtree_m_liq, UnsignedDecimal("324198833"))  # 8430*16 + 377*8 + 9082734*4 + 1111*4 + 45346*2 + 287634865*1
        self.assertEqual(R.subtree_m_liq, UnsignedDecimal("324063953"))  # 377*8 + 9082734*4 + 1111*4 + 45346*2 + 287634865*1
        self.assertEqual(RR.subtree_m_liq, UnsignedDecimal("324056493"))  # 9082734*4 + 45346*2 + 287634865*1
        self.assertEqual(RL.subtree_m_liq, UnsignedDecimal("4444"))  # 1111*4
        self.assertEqual(RRL.subtree_m_liq, UnsignedDecimal("287725557"))  # 45346*2 + 287634865*1
        self.assertEqual(RRLL.subtree_m_liq, UnsignedDecimal("287634865"))  # 287634865*1

        # borrow_x
        self.assertEqual(root.token_x_borrow, UnsignedDecimal("492e18"))
        self.assertEqual(R.token_x_borrow, UnsignedDecimal("998e18"))
        self.assertEqual(RR.token_x_borrow, UnsignedDecimal("765e18"))
        self.assertEqual(RL.token_x_borrow, UnsignedDecimal("24e18"))
        self.assertEqual(RRL.token_x_borrow, UnsignedDecimal("53e18"))
        self.assertEqual(RRLL.token_x_borrow, UnsignedDecimal("701e18"))

        # subtree_borrow_x
        self.assertEqual(root.token_x_subtree_borrow, UnsignedDecimal("3033e18"))  # 492e18 + 998e18 + 765e18 + 53e18 + 701e18 + 24e18
        self.assertEqual(R.token_x_subtree_borrow, UnsignedDecimal("2541e18"))  # 998e18 + 765e18 + 53e18 + 701e18 + 24e18
        self.assertEqual(RR.token_x_subtree_borrow, UnsignedDecimal("1519e18"))  # 765e18 + 53e18 + 701e18
        self.assertEqual(RL.token_x_subtree_borrow, UnsignedDecimal("24e18"))  # 24e18
        self.assertEqual(RRL.token_x_subtree_borrow, UnsignedDecimal("754e18"))  # 53e18 + 701e18
        self.assertEqual(RRLL.token_x_subtree_borrow, UnsignedDecimal("701e18"))  # 701e18

        # borrow_y
        self.assertEqual(root.token_y_borrow, UnsignedDecimal("254858e6"))
        self.assertEqual(R.token_y_borrow, UnsignedDecimal("353e6"))
        self.assertEqual(RR.token_y_borrow, UnsignedDecimal("99763e6"))
        self.assertEqual(RL.token_y_borrow, UnsignedDecimal("552e6"))
        self.assertEqual(RRL.token_y_borrow, UnsignedDecimal("8765e6"))
        self.assertEqual(RRLL.token_y_borrow, UnsignedDecimal("779531e6"))

        # subtree_borrow_y
        self.assertEqual(root.token_y_subtree_borrow, UnsignedDecimal("1143822e6"))  # 254858e6 + 353e6 + 99763e6 + 8765e6 + 779531e6 + 552e6
        self.assertEqual(R.token_y_subtree_borrow, UnsignedDecimal("888964e6"))  # 353e6 + 99763e6 + 8765e6 + 779531e6 + 552e6
        self.assertEqual(RR.token_y_subtree_borrow, UnsignedDecimal("888059e6"))  # 99763e6 + 8765e6 + 779531e6
        self.assertEqual(RL.token_y_subtree_borrow, UnsignedDecimal("552e6"))  # 552e6
        self.assertEqual(RRL.token_y_subtree_borrow, UnsignedDecimal("788296e6"))  # 8765e6 + 779531e6
        self.assertEqual(RRLL.token_y_subtree_borrow, UnsignedDecimal("779531e6"))  # 779531e6

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
        self.assertEqual(root.token_x_cumulative_earned_per_m_liq, UnsignedDecimal("373601278"))
        self.assertEqual(root.token_x_cumulative_earned_per_m_subtree_liq, UnsignedDecimal("2303115199"))
        self.assertEqual(root.token_y_cumulative_earned_per_m_liq, UnsignedDecimal("0"))
        self.assertEqual(root.token_y_cumulative_earned_per_m_subtree_liq, UnsignedDecimal("2"))

        # R
        #           total_m_liq = 324063953 + 8430 * 8 = 324131393
        #
        #           earn_x      = 4541239648278065 * 998e18 / 324131393 / 2**64 = 757991165.739306427787211084069081135461126639210612444989968
        #           earn_x_sub  = 4541239648278065 * 2541e18 / 324131393 / 2**64 = 1929915382.90939642585902140743440397315302884793002627527005
        #
        #           earn_y      = 13278814667749784 * 353e6 / 324131393 / 2**64 = 0.0007839587228619296743658765199435031723124415958637831459168088
        #           earn_y_sub  = 13278814667749784 * 888964e6 / 324131393 / 2**64 = 1.9742523572527831474305582285412361305143267162194111063081870320
        self.assertEqual(R.token_x_cumulative_earned_per_m_liq, UnsignedDecimal("757991165"))
        self.assertEqual(R.token_x_cumulative_earned_per_m_subtree_liq, UnsignedDecimal("1929915382"))
        self.assertEqual(R.token_y_cumulative_earned_per_m_liq, UnsignedDecimal("0"))
        self.assertEqual(R.token_y_cumulative_earned_per_m_subtree_liq, UnsignedDecimal("1"))

        # RR
        #           total_m_liq = 324056493 + (377 + 8430) * 4 = 324091721
        #
        #           earn_x      = 4541239648278065 * 765e18 / 324091721 / 2**64 = 581096415.560225831923714717876078601550264387092272644849535
        #           earn_x_sub  = 4541239648278065 * 1519e18 / 324091721 / 2**64 = 1153837196.38690593293087928948204365458150536469694398369469
        #
        #           earn_y      = 13278814667749784 * 99763e6 / 324091721 / 2**64 = 0.2215854043845212215658200680605818096232476901747430889861663960
        #           earn_y_sub  = 13278814667749784 * 888059e6 / 324091721 / 2**64 = 1.9724839131974131842719305135352006382347335233392357172695883598
        self.assertEqual(RR.token_x_cumulative_earned_per_m_liq, UnsignedDecimal("581096415"))
        self.assertEqual(RR.token_x_cumulative_earned_per_m_subtree_liq, UnsignedDecimal("1153837196"))
        self.assertEqual(RR.token_y_cumulative_earned_per_m_liq, UnsignedDecimal("0"))
        self.assertEqual(RR.token_y_cumulative_earned_per_m_subtree_liq, UnsignedDecimal("1"))

        # RL
        #           total_m_liq = 4444 + (377 + 8430) * 4 = 39672
        #
        #           earn_x      = 4541239648278065 * 24e18 / 39672 / 2**64 = 148929881804.004419784834421574153374302771710945632482252911
        #           earn_x_sub  = 4541239648278065 * 24e18 / 39672 / 2**64 = 148929881804.004419784834421574153374302771710945632482252911
        #
        #           earn_y      = 13278814667749784 * 552e6 / 39672 / 2**64 = 10.016005848413612945928345245285743980736658202469601316734724742
        #           earn_y_sub  = 13278814667749784 * 552e6 / 39672 / 2**64 = 10.016005848413612945928345245285743980736658202469601316734724742
        self.assertEqual(RL.token_x_cumulative_earned_per_m_liq, UnsignedDecimal("148929881804"))
        self.assertEqual(RL.token_x_cumulative_earned_per_m_subtree_liq, UnsignedDecimal("148929881804"))
        self.assertEqual(RL.token_y_cumulative_earned_per_m_liq, UnsignedDecimal("10"))
        self.assertEqual(RL.token_y_cumulative_earned_per_m_subtree_liq, UnsignedDecimal("10"))

        # RRL
        #           total_m_liq = 287725557 + (9082734 + 377 + 8430) * 2 = 305908639
        #
        #           earn_x      = 4541239648278065 * 53e18 / 305908639 / 2**64 = 42651943.5921096141810155248335108410236545389757231280339726
        #           earn_x_sub  = 4541239648278065 * 754e18 / 305908639 / 2**64 = 606784254.121710360235579353291833474185575894107457330898403
        #
        #           earn_y      = 13278814667749784 * 8765e6 / 305908639 / 2**64 = 0.0206252758466917150640245207131723061423410095348761855275430371
        #           earn_y_sub  = 13278814667749784 * 788296e6 / 305908639 / 2**64 = 1.8549711864054412114215942475882345970088817401374509465624718757
        self.assertEqual(RRL.token_x_cumulative_earned_per_m_liq, UnsignedDecimal("42651943"))
        self.assertEqual(RRL.token_x_cumulative_earned_per_m_subtree_liq, UnsignedDecimal("606784254"))
        self.assertEqual(RRL.token_y_cumulative_earned_per_m_liq, UnsignedDecimal("0"))
        self.assertEqual(RRL.token_y_cumulative_earned_per_m_subtree_liq, UnsignedDecimal("1"))

        # RRLL
        #           total_m_liq = 287634865 + (45346 + 9082734 + 377 + 8430) * 1 = 296771752
        #
        #           earn_x      = 4541239648278065 * 701e18 / 296771752 / 2**64 = 581500584.766017533363270505955415005042190229659676220491523
        #           earn_x_sub  = 4541239648278065 * 701e18 / 296771752 / 2**64 = 581500584.766017533363270505955415005042190229659676220491523
        #
        #           earn_y      = 13278814667749784 * 779531e6 / 296771752 / 2**64 = 1.8908210002218903501728143334071499784764070319492513392714860291
        #           earn_y_sub  = 13278814667749784 * 779531e6 / 296771752 / 2**64 = 1.8908210002218903501728143334071499784764070319492513392714860291
        self.assertEqual(RRLL.token_x_cumulative_earned_per_m_liq, UnsignedDecimal("581500584"))
        self.assertEqual(RRLL.token_x_cumulative_earned_per_m_subtree_liq, UnsignedDecimal("581500584"))
        self.assertEqual(RRLL.token_y_cumulative_earned_per_m_liq, UnsignedDecimal("1"))
        self.assertEqual(RRLL.token_y_cumulative_earned_per_m_subtree_liq, UnsignedDecimal("1"))

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
        #           earn_x      = 16463537718422861220174597 * 492e18 / 324212503 / 2**64  = 1354374549470516050.18864221581152444619216774937383131887026
        #           earn_x_sub  = 16463537718422861220174597 * 3033e18 / 324212503 / 2**64 = 8349223594601778821.58973951332592204329439996717648453279172
        #
        #           earn_y      = 3715979586694123491881712207 * 254858e6 / 324212503 / 2**64  = 158351473403.760477087118657111090258803416110827691474619042
        #           earn_y_sub  = 3715979586694123491881712207 * 1143822e6 / 324212503 / 2**64 = 710693401861.570429112455707155049015549996557766096092261976
        self.assertEqual(root.token_x_cumulative_earned_per_m_liq, UnsignedDecimal("1354374549844117328"))  # 373601278 + 1354374549470516050 = 1354374549844117328
        self.assertEqual(root.token_x_cumulative_earned_per_m_subtree_liq, UnsignedDecimal("8349223596904894020"))  # 2303115199 + 8349223594601778821 = 8349223596904894020
        self.assertEqual(root.token_y_cumulative_earned_per_m_liq, UnsignedDecimal("158351473403"))  # 0 + 158351473403 = 158351473403
        self.assertEqual(root.token_y_cumulative_earned_per_m_subtree_liq, UnsignedDecimal("710693401863"))  # 2 + 710693401861 = 710693401863

        # R
        #           total_m_liq = 324077623 + 8430 * 8 = 324145063
        #
        #           earn_x      = 16463537718422861220174597 * 998e18 / 324145063 / 2**64  = 2747859799177149412.40503918202324257122793136834755591677703
        #           earn_x_sub  = 16463537718422861220174597 * 2541e18 / 324145063 / 2**64 = 6996304358425988634.18958372897901740830678718133380719892830
        #
        #           earn_y      = 3715979586694123491881712207 * 353e6 / 324145063 / 2**64    = 219375887.687723491736647414380713113554572979392890952782027
        #           earn_y_sub  = 3715979586694123491881712207 * 888964e6 / 324145063 / 2**64 = 552456845955.890725518915105035513462543703722529807118835474
        self.assertEqual(R.token_x_cumulative_earned_per_m_liq, UnsignedDecimal("2747859799935140577"))  # 757991165 + 2747859799177149412 = 2747859799935140577
        self.assertEqual(R.token_x_cumulative_earned_per_m_subtree_liq, UnsignedDecimal("6996304360355904016"))  # 1929915382 + 6996304358425988634 = 6996304360355904016
        self.assertEqual(R.token_y_cumulative_earned_per_m_liq, UnsignedDecimal("219375887"))  # 0 + 219375887 = 219375887 = 219375887
        self.assertEqual(R.token_y_cumulative_earned_per_m_subtree_liq, UnsignedDecimal("552456845956"))  # 1 + 552456845955 = 552456845956

        # RR
        #           total_m_liq = 324059227 + (377 + 8430) * 4 = 324094455
        #
        #           earn_x      = 16463537718422861220174597 * 765e18 / 324094455 / 2**64 = 2106654304105573173.10473569019029577351750175393657598084186
        #           earn_x_sub  = 16463537718422861220174597 * 1519e18 / 324094455 / 2**64 = 4183016846975641372.47855361228635199996481720814334498679581
        #
        #           earn_y      = 3715979586694123491881712207 * 99763e6 / 324094455 / 2**64  = 62008538706.1288411875002441524622314240784801570453009535875
        #           earn_y_sub  = 3715979586694123491881712207 * 888059e6 / 324094455 / 2**64 = 551980602776.841840924293368501262560029627326862519099461143
        self.assertEqual(RR.token_x_cumulative_earned_per_m_liq, UnsignedDecimal("2106654304686669588"))  # 581096415 + 2106654304105573173 = 2106654304686669588
        self.assertEqual(RR.token_x_cumulative_earned_per_m_subtree_liq, UnsignedDecimal("4183016848129478568"))  # 1153837196 + 4183016846975641372 = 4183016848129478568
        self.assertEqual(RR.token_y_cumulative_earned_per_m_liq, UnsignedDecimal("62008538706"))  # 0 + 62008538706 = 62008538706
        self.assertEqual(RR.token_y_cumulative_earned_per_m_subtree_liq, UnsignedDecimal("551980602777"))  # 1 + 551980602776 = 551980602777

        # RL
        #           total_m_liq = 15380 + (377 + 8430) * 4 = 50608
        #
        #           earn_x      = 16463537718422861220174597 * 24e18 / 50608 / 2**64 = 423248577958689008325.429426909965566945601510047930853109815
        #           earn_x_sub  = 16463537718422861220174597 * 24e18 / 50608 / 2**64 = 423248577958689008325.429426909965566945601510047930853109815
        #
        #           earn_y      = 3715979586694123491881712207 * 552e6 / 50608 / 2**64 = 2197219781185.45157550848350683783177940360867452683580030548
        #           earn_y_sub  = 3715979586694123491881712207 * 552e6 / 50608 / 2**64 = 2197219781185.45157550848350683783177940360867452683580030548
        self.assertEqual(RL.token_x_cumulative_earned_per_m_liq, UnsignedDecimal("423248578107618890129"))  # 148929881804 + 423248577958689008325 = 423248578107618890129
        self.assertEqual(RL.token_x_cumulative_earned_per_m_subtree_liq, UnsignedDecimal("423248578107618890129"))  # 148929881804 + 423248577958689008325 = 423248578107618890129
        self.assertEqual(RL.token_y_cumulative_earned_per_m_liq, UnsignedDecimal("2197219781195"))  # 10 + 2197219781185 = 2197219781195
        self.assertEqual(RL.token_y_cumulative_earned_per_m_subtree_liq, UnsignedDecimal("2197219781195"))  # 10 + 2197219781185 = 2197219781195

        # RRL
        #           total_m_liq = 287728291 + (9082734 + 377 + 8430) * 2 = 305911373
        #
        #           earn_x      = 16463537718422861220174597 * 53e18 / 305911373 / 2**64 = 154626414974589533.957746783298485424790431468186321359344549
        #           earn_x_sub  = 16463537718422861220174597 * 754e18 / 305911373 / 2**64 = 2199779563978122803.85171838881241528852802503797143971595830
        #
        #           earn_y      = 3715979586694123491881712207 * 8765e6 / 305911373 / 2**64 = 5771781665.52844938596716448955303604219154769320799186650875
        #           earn_y_sub  = 3715979586694123491881712207 * 788296e6 / 305911373 / 2**64 = 519095539054.126016789546137872983468330339792397614050929992
        self.assertEqual(RRL.token_x_cumulative_earned_per_m_liq, UnsignedDecimal("154626415017241476"))  # 42651943 + 154626414974589533 = 154626415017241476 (sol losses 1 wei)
        self.assertEqual(RRL.token_x_cumulative_earned_per_m_subtree_liq, UnsignedDecimal("2199779564584907057"))  # 606784254 + 2199779563978122803 = 2199779564584907057
        self.assertEqual(RRL.token_y_cumulative_earned_per_m_liq, UnsignedDecimal("5771781665"))  # 0 + 5771781665 = 5771781665
        self.assertEqual(RRL.token_y_cumulative_earned_per_m_subtree_liq, UnsignedDecimal("519095539055"))  # 1 + 519095539054 = 519095539055

        # RRLL
        #           total_m_liq = 287637599 + (45346 + 9082734 + 377 + 8430) * 1 = 296774486
        #
        #           earn_x      = 16463537718422861220174597 * 701e18 / 296774486 / 2**64 = 2108117905415037748.37451632639936795389368532390933657093156
        #           earn_x_sub  = 16463537718422861220174597 * 701e18 / 296774486 / 2**64 = 2108117905415037748.37451632639936795389368532390933657093156
        #
        #           earn_y      = 3715979586694123491881712207 * 779531e6 / 296774486 / 2**64 = 529127613134.050803777279185858502873428448836282593499892809
        #           earn_y_sub  = 3715979586694123491881712207 * 779531e6 / 296774486 / 2**64 = 529127613134.050803777279185858502873428448836282593499892809
        self.assertEqual(RRLL.token_x_cumulative_earned_per_m_liq, UnsignedDecimal("2108117905996538332"))  # 581500584 + 2108117905415037748 = 2108117905996538332
        self.assertEqual(RRLL.token_x_cumulative_earned_per_m_subtree_liq, UnsignedDecimal("2108117905996538332"))  # 581500584 + 2108117905415037748 = 2108117905996538332
        self.assertEqual(RRLL.token_y_cumulative_earned_per_m_liq, UnsignedDecimal("529127613135"))  # 1 + 529127613134 = 529127613135
        self.assertEqual(RRLL.token_y_cumulative_earned_per_m_subtree_liq, UnsignedDecimal("529127613135"))  # 1 + 529127613134 = 529127613135

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
        #           earn_x      = 11381610389149375791104 * 492e18 / 324198833 / 2**64  = 936348777891386.743735803607164207960477914490210395050990205
        #           earn_x_sub  = 11381610389149375791104 * 3033e18 / 324198833 / 2**64 = 5772247649074341.45071278931001837956123885091221164266189693
        #
        #           earn_y      = 185394198934916215865344 * 254858e6 / 324198833 / 2**64  = 7900657.61872699474175109887651599451346454839027751836478695
        #           earn_y_sub  = 185394198934916215865344 * 1143822e6 / 324198833 / 2**64 = 35458749.5733606501640098620374258523427949943453374491326438
        self.assertEqual(root.token_x_cumulative_earned_per_m_liq,
                         UnsignedDecimal("1355310898622008714"))  # 373601278 + 1354374549470516050 + 936348777891386 = 1355310898622008714
        self.assertEqual(root.token_x_cumulative_earned_per_m_subtree_liq,
                         UnsignedDecimal("8354995844553968361"))  # 2303115199 + 8349223594601778821 + 5772247649074341 = 8354995844553968361
        self.assertEqual(root.token_y_cumulative_earned_per_m_liq, UnsignedDecimal("158359374060"))  # 0 + 158351473403 + 7900657 = 158359374060
        self.assertEqual(root.token_y_cumulative_earned_per_m_subtree_liq, UnsignedDecimal("710728860612"))  # 2 + 710693401861 + 35458749 = 710728860612

        # R
        #           total_m_liq = 324063953 + 8430 * 8 = 324131393
        #
        #           earn_x      = 11381610389149375791104 * 998e18 / 324131393 / 2**64  = 1899736810880077.58842507649572740061066261792173891653870132
        #           earn_x_sub  = 11381610389149375791104 * 2541e18 / 324131393 / 2**64 = 4836905046539355.86391595127819972440049470154222303299082171
        #
        #           earn_y      = 185394198934916215865344 * 353e6 / 324131393 / 2**64    = 10945.359436035932129843115196215424291564802240553108041589788249
        #           earn_y_sub  = 185394198934916215865344 * 888964e6 / 324131393 / 2**64 = 27563825.7951735024642318840149814403397354471925525584619938
        self.assertEqual(R.token_x_cumulative_earned_per_m_liq, UnsignedDecimal("2749759536746020654"))  # 757991165 + 2747859799177149412 + 1899736810880077 = 2749759536746020654
        self.assertEqual(R.token_x_cumulative_earned_per_m_subtree_liq,
                         UnsignedDecimal("7001141265402443371"))  # 1929915382 + 6996304358425988634 + 4836905046539355 = 7001141265402443371
        self.assertEqual(R.token_y_cumulative_earned_per_m_liq, UnsignedDecimal("219386832"))  # 0 + 219375887 + 10945 = 219386832
        self.assertEqual(R.token_y_cumulative_earned_per_m_subtree_liq, UnsignedDecimal("552484409781"))  # 1 + 552456845955 + 27563825 = 552484409781

        # RR
        #           total_m_liq = 324056493 + (377 + 8430) * 4 = 324091721
        #
        #           earn_x      = 11381610389149375791104 * 765e18 / 324091721 / 2**64  = 1456389336983247.97581853577374895245788594982344519686141566
        #           earn_x_sub  = 11381610389149375791104 * 1519e18 / 324091721 / 2**64 = 2891837127944514.60819392920303876965167157879975588762417044
        #
        #           earn_y      = 185394198934916215865344 * 99763e6 / 324091721 / 2**64  = 3093698.46401352576654665825318763474490453834363760251685046
        #           earn_y_sub  = 185394198934916215865344 * 888059e6 / 324091721 / 2**64 = 27539135.3934162733549879091613880669579421169863823827823111
        self.assertEqual(RR.token_x_cumulative_earned_per_m_liq, UnsignedDecimal("2108110694023652835"))  # 581096415 + 2106654304105573173+ 1456389336983247 = 2108110694023652835
        self.assertEqual(RR.token_x_cumulative_earned_per_m_subtree_liq,
                         UnsignedDecimal("4185908685257423082"))  # 1153837196 + 4183016846975641372 + 2891837127944514 = 4185908685257423082
        self.assertEqual(RR.token_y_cumulative_earned_per_m_liq, UnsignedDecimal("62011632404"))  # 0 + 62008538706 + 3093698 = 62011632404
        self.assertEqual(RR.token_y_cumulative_earned_per_m_subtree_liq, UnsignedDecimal("552008141912"))  # 1 + 551980602776 + 27539135 = 552008141912

        # RL
        #           total_m_liq = 4444 + (377 + 8430) * 4 = 39672
        #
        #           earn_x      = 11381610389149375791104 * 24e18 / 39672 / 2**64 = 373259731104033296.286645111573225645606473079249848759830611
        #           earn_x_sub  = 11381610389149375791104 * 24e18 / 39672 / 2**64 = 373259731104033296.286645111573225645606473079249848759830611
        #
        #           earn_y      = 185394198934916215865344 * 552e6 / 39672 / 2**64 = 139839995.304998697233270837982279275016069267997580157289776
        #           earn_y_sub  = 185394198934916215865344 * 552e6 / 39672 / 2**64 = 139839995.304998697233270837982279275016069267997580157289776
        self.assertEqual(RL.token_x_cumulative_earned_per_m_liq,
                         UnsignedDecimal("423621837838722923425"))  # 148929881804 + 423248577958689008325 + 373259731104033296 = 423621837838722923425
        self.assertEqual(RL.token_x_cumulative_earned_per_m_subtree_liq,
                         UnsignedDecimal("423621837838722923425"))  # 148929881804 + 423248577958689008325 + 373259731104033296 = 423621837838722923425
        self.assertEqual(RL.token_y_cumulative_earned_per_m_liq, UnsignedDecimal("2197359621190"))  # 10 + 2197219781185 + 139839995 = 2197359621190
        self.assertEqual(RL.token_y_cumulative_earned_per_m_subtree_liq, UnsignedDecimal("2197359621190"))  # 10 + 2197219781185 + 139839995 = 2197359621190

        # RRL
        #           total_m_liq = 287725557 + (9082734 + 377 + 8430) * 2 = 305908639
        #
        #           earn_x      = 11381610389149375791104 * 53e18 / 305908639 / 2**64  = 106897640711262.335596794608928382455998365904272484439381916
        #           earn_x_sub  = 11381610389149375791104 * 754e18 / 305908639 / 2**64 = 1520770209363996.24603741764400000701552392248719723145837669
        #
        #           earn_y      = 185394198934916215865344 * 8765e6 / 305908639 / 2**64   = 287962.93864210284405202260308978443477406072046236000546555339354
        #           earn_y_sub  = 185394198934916215865344 * 788296e6 / 305908639 / 2**64 = 25898463.5116731435886860479093285465823905270619049107665115
        self.assertEqual(RRL.token_x_cumulative_earned_per_m_liq, UnsignedDecimal("154733312657952738"))  # 42651943 + 154626414974589533 + 106897640711262 = 154733312657952738
        self.assertEqual(RRL.token_x_cumulative_earned_per_m_subtree_liq,
                         UnsignedDecimal("2201300334794271053"))  # 606784254 + 2199779563978122803 + 1520770209363996 = 2201300334794271053
        self.assertEqual(RRL.token_y_cumulative_earned_per_m_liq, UnsignedDecimal("5772069627"))  # 0 + 5771781665 + 287962 = 5772069627
        self.assertEqual(RRL.token_y_cumulative_earned_per_m_subtree_liq, UnsignedDecimal("519121437518"))  # 1 + 519095539054 + 25898463 = 519121437518

        # RRLL
        #           total_m_liq = 287634865 + (45346 + 9082734 + 377 + 8430) * 1 = 296771752
        #
        #           earn_x      = 11381610389149375791104 * 701e18 / 296771752 / 2**64 = 1457402297493569.71876500861500730007660377831377967536479010
        #           earn_x_sub  = 11381610389149375791104 * 701e18 / 296771752 / 2**64 = 1457402297493569.71876500861500730007660377831377967536479010
        #
        #           earn_y      = 185394198934916215865344 * 779531e6 / 296771752 / 2**64 = 26398986.1622835510939886934876573358559478744206759947961624
        #           earn_y_sub  = 185394198934916215865344 * 779531e6 / 296771752 / 2**64 = 26398986.1622835510939886934876573358559478744206759947961624
        self.assertEqual(RRLL.token_x_cumulative_earned_per_m_liq,
                         UnsignedDecimal("2109575308294031901"))  # 581500584 + 2108117905415037748 + 1457402297493569 = 2109575308294031901
        self.assertEqual(RRLL.token_x_cumulative_earned_per_m_subtree_liq,
                         UnsignedDecimal("2109575308294031901"))  # 581500584 + 2108117905415037748 + 1457402297493569 = 2109575308294031901
        self.assertEqual(RRLL.token_y_cumulative_earned_per_m_liq, UnsignedDecimal("529154012121"))  # 1 + 529127613134 + 26398986 = 529154012121
        self.assertEqual(RRLL.token_y_cumulative_earned_per_m_subtree_liq, UnsignedDecimal("529154012121"))  # 1 + 529127613134 + 26398986 = 529154012121

        # t_liq
        self.assertEqual(root.t_liq, UnsignedDecimal("4430"))
        self.assertEqual(R.t_liq, UnsignedDecimal("77"))
        self.assertEqual(RR.t_liq, UnsignedDecimal("82734"))
        self.assertEqual(RL.t_liq, UnsignedDecimal("1111"))
        self.assertEqual(RRL.t_liq, UnsignedDecimal("5346"))
        self.assertEqual(RRLL.t_liq, UnsignedDecimal("7635865"))

        # borrow_x
        self.assertEqual(root.token_x_borrow, UnsignedDecimal("492e18"))
        self.assertEqual(R.token_x_borrow, UnsignedDecimal("998e18"))
        self.assertEqual(RR.token_x_borrow, UnsignedDecimal("765e18"))
        self.assertEqual(RL.token_x_borrow, UnsignedDecimal("1024e18"))
        self.assertEqual(RRL.token_x_borrow, UnsignedDecimal("53e18"))
        self.assertEqual(RRLL.token_x_borrow, UnsignedDecimal("1701e18"))

        # subtree_borrow_x
        self.assertEqual(root.token_x_subtree_borrow, UnsignedDecimal("5033e18"))  # 492e18 + 998e18 + 765e18 + 53e18 + 701e18 + 24e18
        self.assertEqual(R.token_x_subtree_borrow, UnsignedDecimal("4541e18"))  # 998e18 + 765e18 + 53e18 + 701e18 + 24e18
        self.assertEqual(RR.token_x_subtree_borrow, UnsignedDecimal("2519e18"))  # 765e18 + 53e18 + 701e18
        self.assertEqual(RL.token_x_subtree_borrow, UnsignedDecimal("1024e18"))
        self.assertEqual(RRL.token_x_subtree_borrow, UnsignedDecimal("1754e18"))  # 53e18 + 701e18
        self.assertEqual(RRLL.token_x_subtree_borrow, UnsignedDecimal("1701e18"))  # 701e18

        # borrow_y
        self.assertEqual(root.token_y_borrow, UnsignedDecimal("254858e6"))
        self.assertEqual(R.token_y_borrow, UnsignedDecimal("353e6"))
        self.assertEqual(RR.token_y_borrow, UnsignedDecimal("99763e6"))
        self.assertEqual(RL.token_y_borrow, UnsignedDecimal("1552e6"))
        self.assertEqual(RRL.token_y_borrow, UnsignedDecimal("8765e6"))
        self.assertEqual(RRLL.token_y_borrow, UnsignedDecimal("780531e6"))

        # subtree_borrow_y
        self.assertEqual(root.token_y_subtree_borrow, UnsignedDecimal("1145822e6"))  # 254858e6 + 353e6 + 99763e6 + 8765e6 + 779531e6 + 552e6
        self.assertEqual(R.token_y_subtree_borrow, UnsignedDecimal("890964e6"))  # 353e6 + 99763e6 + 8765e6 + 779531e6 + 552e6
        self.assertEqual(RR.token_y_subtree_borrow, UnsignedDecimal("889059e6"))  # 99763e6 + 8765e6 + 779531e6
        self.assertEqual(RL.token_y_subtree_borrow, UnsignedDecimal("1552e6"))
        self.assertEqual(RRL.token_y_subtree_borrow, UnsignedDecimal("789296e6"))  # 8765e6 + 779531e6
        self.assertEqual(RRLL.token_y_subtree_borrow, UnsignedDecimal("780531e6"))  # 779531e6

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
        #           earn_x      = 2352954287417905205553 * 492e18 / 324198833 / 2**64  = 193574177654021.169606366690127570750614868262308175138961180
        #           earn_x_sub  = 2352954287417905205553 * 5033e18 / 324198833 / 2**64 = 1980200886448553.95656269014514647070700128448007529567965776
        #
        #           earn_y      = 6117681147286553534438 * 254858e6 / 324198833 / 2**64  = 260707.74837037839600245251693715160678794344236990061534290681026
        #           earn_y_sub  = 6117681147286553534438 * 1145822e6 / 324198833 / 2**64 = 1172122.01952947804057287645615189999290967884478087508680692
        self.assertEqual(root.token_x_cumulative_earned_per_m_liq,
                         UnsignedDecimal("1355504472799662735"))  # 373601278 + 1354374549470516050 + 936348777891386 + 193574177654021 = 1355504472799662735
        self.assertEqual(root.token_x_cumulative_earned_per_m_subtree_liq,
                         UnsignedDecimal("8356976045440416914"))  # 2303115199 + 8349223594601778821 + 5772247649074341 + 1980200886448553 = 8356976045440416914
        self.assertEqual(root.token_y_cumulative_earned_per_m_liq, UnsignedDecimal("158359634767"))  # 0 + 158351473403 + 7900657 + 260707 = 158359634767
        self.assertEqual(root.token_y_cumulative_earned_per_m_subtree_liq, UnsignedDecimal("710730032734"))  # 2 + 710693401861 + 35458749 + 1172122 = 710730032734

        # R
        #           total_m_liq = 324063953 + 8430 * 8 = 324131393
        #
        #           earn_x      = 2352954287417905205553 * 998e18 / 324131393 / 2**64  = 392738261220692.635199129066166314911263418663640357414414483
        #           earn_x_sub  = 2352954287417905205553 * 4541e18 / 324131393 / 2**64 = 1786998441085335.92829583676298721043291301017193473248382381
        #
        #           earn_y      = 6117681147286553534438 * 353e6 / 324131393 / 2**64    = 361.17753121077324707993230558447820693195086120933424789750836934
        #           earn_y_sub  = 6117681147286553534438 * 890964e6 / 324131393 / 2**64 = 911603.90344950531249667084054608793530005288132156736216361373026
        self.assertEqual(R.token_x_cumulative_earned_per_m_liq,
                         UnsignedDecimal("2750152275007241346"))  # 757991165 + 2747859799177149412 + 1899736810880077 + 392738261220692 = 2750152275007241346
        self.assertEqual(R.token_x_cumulative_earned_per_m_subtree_liq,
                         UnsignedDecimal("7002928263843528706"))  # 1929915382 + 6996304358425988634 + 4836905046539355 + 1786998441085335 = 7002928263843528706
        self.assertEqual(R.token_y_cumulative_earned_per_m_liq, UnsignedDecimal("219387193"))  # 0 + 219375887 + 10945 + 361 = 219387193
        self.assertEqual(R.token_y_cumulative_earned_per_m_subtree_liq, UnsignedDecimal("552485321384"))  # 1 + 552456845955 + 27563825 + 911603 = 552485321384

        # RR
        #           total_m_liq = 324056493 + (377 + 8430) * 4 = 324091721
        #
        #           earn_x      = 2352954287417905205553 * 765e18 / 324091721 / 2**64  = 301083714644757.116282263044928314612316183509300881282164628
        #           earn_x_sub  = 2352954287417905205553 * 2519e18 / 324091721 / 2**64 = 991411604170121.798581726287809705239770544130626039150029671
        #
        #           earn_y      = 6117681147286553534438 * 99763e6 / 324091721 / 2**64  = 102086.58565055261555338276382365173781133864709615634713615821960
        #           earn_y_sub  = 6117681147286553534438 * 889059e6 / 324091721 / 2**64 = 909766.12323100405793004346924503062625232727813579850073199172604
        self.assertEqual(RR.token_x_cumulative_earned_per_m_liq,
                         UnsignedDecimal("2108411777738297592"))  # 581096415 + 2106654304105573173+ 1456389336983247 + 301083714644757 = 2108411777738297592
        self.assertEqual(RR.token_x_cumulative_earned_per_m_subtree_liq,
                         UnsignedDecimal("4186900096861593203"))  # 1153837196 + 4183016846975641372 + 2891837127944514 + 991411604170121 = 4186900096861593203
        self.assertEqual(RR.token_y_cumulative_earned_per_m_liq, UnsignedDecimal("62011734490"))  # 0 + 62008538706 + 3093698 + 102086 = 62011734490
        self.assertEqual(RR.token_y_cumulative_earned_per_m_subtree_liq, UnsignedDecimal("552009051678"))  # 1 + 551980602776 + 27539135 + 909766 = 552009051678

        # RL
        #           total_m_liq = 4444 + (377 + 8430) * 4 = 39672
        #
        #           earn_x      = 2352954287417905205553 * 1024e18 / 39672 / 2**64 = 3292377527956539412.11877691362144195603424231355578266196876
        #           earn_x_sub  = 2352954287417905205553 * 1024e18 / 39672 / 2**64 = 3292377527956539412.11877691362144195603424231355578266196876
        #
        #           earn_y      = 6117681147286553534438 * 1552e6 / 39672 / 2**64 = 12974025.1961037381208809794236997935340918048320067315891063
        #           earn_y_sub  = 6117681147286553534438 * 1552e6 / 39672 / 2**64 = 12974025.1961037381208809794236997935340918048320067315891063
        self.assertEqual(RL.token_x_cumulative_earned_per_m_liq,
                         UnsignedDecimal("426914215366679462837"))  # 148929881804 + 423248577958689008325 + 373259731104033296 + 3292377527956539412 = 426914215366679462837
        self.assertEqual(RL.token_x_cumulative_earned_per_m_subtree_liq,
                         UnsignedDecimal("426914215366679462837"))  # 148929881804 + 423248577958689008325 + 373259731104033296 + 3292377527956539412 = 426914215366679462837
        self.assertEqual(RL.token_y_cumulative_earned_per_m_liq, UnsignedDecimal("2197372595215"))  # 10 + 2197219781185 + 139839995 + 12974025 = 2197372595215
        self.assertEqual(RL.token_y_cumulative_earned_per_m_subtree_liq, UnsignedDecimal("2197372595215"))  # 10 + 2197219781185 + 139839995 + 12974025 = 2197372595215

        # RRL
        #           total_m_liq = 287725557 + (9082734 + 377 + 8430) * 2 = 305908639
        #
        #           earn_x      = 2352954287417905205553 * 53e18 / 305908639 / 2**64   = 22099268330799.1616184419285239088656103478160451926038962236
        #           earn_x_sub  = 2352954287417905205553 * 1754e18 / 305908639 / 2**64 = 731360691551353.386391455521338417929821699421571091079886346
        #
        #           earn_y      = 6117681147286553534438 * 8765e6 / 305908639 / 2**64   = 9502.2684149166432853337655386227368949210477797554902569919214852
        #           earn_y_sub  = 6117681147286553534438 * 789296e6 / 305908639 / 2**64 = 855687.67265488270148782656070425233773115839456587443672363898010
        self.assertEqual(RRL.token_x_cumulative_earned_per_m_liq,
                         UnsignedDecimal("154755411926283537"))  # 42651943 + 154626414974589533 + 106897640711262 + 22099268330799 = 154755411926283537
        self.assertEqual(RRL.token_x_cumulative_earned_per_m_subtree_liq,
                         UnsignedDecimal("2202031695485822406"))  # 606784254 + 2199779563978122803 + 1520770209363996 + 731360691551353 = 2202031695485822406
        self.assertEqual(RRL.token_y_cumulative_earned_per_m_liq, UnsignedDecimal("5772079129"))  # 0 + 5771781665 + 287962 + 9502 = 5772079129
        self.assertEqual(RRL.token_y_cumulative_earned_per_m_subtree_liq, UnsignedDecimal("519122293205"))  # 1 + 519095539054 + 25898463 + 855687 = 519122293205

        # RRLL
        #           total_m_liq = 287634865 + (45346 + 9082734 + 377 + 8430) * 1 = 296771752
        #
        #           earn_x      = 2352954287417905205553 * 1701e18 / 296771752 / 2**64 = 731097873063750.150068233826063023165648387512288880115659770
        #           earn_x_sub  = 2352954287417905205553 * 1701e18 / 296771752 / 2**64 = 731097873063750.150068233826063023165648387512288880115659770
        #
        #           earn_y      = 6117681147286553534438 * 780531e6 / 296771752 / 2**64 = 872237.41346080959306032387265895687662997868016869971844802082307
        #           earn_y_sub  = 6117681147286553534438 * 780531e6 / 296771752 / 2**64 = 872237.41346080959306032387265895687662997868016869971844802082307
        self.assertEqual(RRLL.token_x_cumulative_earned_per_m_liq,
                         UnsignedDecimal("2110306406167095651"))  # 581500584 + 2108117905415037748 + 1457402297493569 + 731097873063750 = 2110306406167095651
        self.assertEqual(RRLL.token_x_cumulative_earned_per_m_subtree_liq,
                         UnsignedDecimal("2110306406167095651"))  # 581500584 + 2108117905415037748 + 1457402297493569 + 731097873063750 = 2110306406167095651
        self.assertEqual(RRLL.token_y_cumulative_earned_per_m_liq, UnsignedDecimal("529154884358"))  # 1 + 529127613134 + 26398986 + 872237 = 529154884358
        self.assertEqual(RRLL.token_y_cumulative_earned_per_m_subtree_liq, UnsignedDecimal("529154884358"))  # 1 + 529127613134 + 26398986 + 872237 = 529154884358

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

        # borrow_x
        self.assertEqual(root.token_x_borrow, UnsignedDecimal("492e18"))
        self.assertEqual(R.token_x_borrow, UnsignedDecimal("998e18"))
        self.assertEqual(RR.token_x_borrow, UnsignedDecimal("765e18"))
        self.assertEqual(RL.token_x_borrow, UnsignedDecimal("24e18"))
        self.assertEqual(RRL.token_x_borrow, UnsignedDecimal("53e18"))
        self.assertEqual(RRLL.token_x_borrow, UnsignedDecimal("701e18"))

        # subtree_borrow_x
        self.assertEqual(root.token_x_subtree_borrow, UnsignedDecimal("3033e18"))  # 492e18 + 998e18 + 765e18 + 53e18 + 701e18 + 24e18
        self.assertEqual(R.token_x_subtree_borrow, UnsignedDecimal("2541e18"))  # 998e18 + 765e18 + 53e18 + 701e18 + 24e18
        self.assertEqual(RR.token_x_subtree_borrow, UnsignedDecimal("1519e18"))  # 765e18 + 53e18 + 701e18
        self.assertEqual(RL.token_x_subtree_borrow, UnsignedDecimal("24e18"))
        self.assertEqual(RRL.token_x_subtree_borrow, UnsignedDecimal("754e18"))  # 53e18 + 701e18
        self.assertEqual(RRLL.token_x_subtree_borrow, UnsignedDecimal("701e18"))  # 701e18

        # borrow_y
        self.assertEqual(root.token_y_borrow, UnsignedDecimal("254858e6"))
        self.assertEqual(R.token_y_borrow, UnsignedDecimal("353e6"))
        self.assertEqual(RR.token_y_borrow, UnsignedDecimal("99763e6"))
        self.assertEqual(RL.token_y_borrow, UnsignedDecimal("552e6"))
        self.assertEqual(RRL.token_y_borrow, UnsignedDecimal("8765e6"))
        self.assertEqual(RRLL.token_y_borrow, UnsignedDecimal("779531e6"))

        # subtree_borrow_y
        self.assertEqual(root.token_y_subtree_borrow, UnsignedDecimal("1143822e6"))  # 254858e6 + 353e6 + 99763e6 + 8765e6 + 779531e6 + 552e6
        self.assertEqual(R.token_y_subtree_borrow, UnsignedDecimal("888964e6"))  # 353e6 + 99763e6 + 8765e6 + 779531e6 + 552e6
        self.assertEqual(RR.token_y_subtree_borrow, UnsignedDecimal("888059e6"))  # 99763e6 + 8765e6 + 779531e6
        self.assertEqual(RL.token_y_subtree_borrow, UnsignedDecimal("552e6"))
        self.assertEqual(RRL.token_y_subtree_borrow, UnsignedDecimal("788296e6"))  # 8765e6 + 779531e6
        self.assertEqual(RRLL.token_y_subtree_borrow, UnsignedDecimal("779531e6"))  # 779531e6

    def test_left_and_right_leg_stopping_below_peak(self):
        #   Range: (1, 4)
        #
        #                                  L(0-7)
        #                             __--  --__
        #                        __---          ---__
        #                      /                       \
        #                   LL(0-3)                     LR(4-7)
        #                 /   \                         /
        #               /       \                     /
        #             /           \                 /
        #           LLL(0-1)       LLR(2-3)       LRL(4-5)
        #              \                         /
        #               \                       /
        #           LLLR(1)                   LRLL(4)

        liq_tree = self.liq_tree

        # 1st (1, 4)
        root: LiqNode = liq_tree.nodes[liq_tree.root_key]
        L: LiqNode = liq_tree.nodes[(8 << 24) | 16]
        LL: LiqNode = liq_tree.nodes[(4 << 24) | 16]
        LR: LiqNode = liq_tree.nodes[(4 << 24) | 20]
        LLL: LiqNode = liq_tree.nodes[(2 << 24) | 16]
        LLR: LiqNode = liq_tree.nodes[(2 << 24) | 18]
        LRL: LiqNode = liq_tree.nodes[(2 << 24) | 20]
        LLLR: LiqNode = liq_tree.nodes[(1 << 24) | 17]
        LRLL: LiqNode = liq_tree.nodes[(1 << 24) | 20]

        # Pre-populate nodes w/o fee calculation
        liq_tree.add_wide_m_liq(UnsignedDecimal("432"))
        liq_tree.add_m_liq(LiqRange(low=0, high=7), UnsignedDecimal("98237498262"))  # L
        liq_tree.add_m_liq(LiqRange(low=0, high=3), UnsignedDecimal("932141354"))  # LL
        liq_tree.add_m_liq(LiqRange(low=4, high=7), UnsignedDecimal("151463465"))  # LR
        liq_tree.add_m_liq(LiqRange(low=0, high=1), UnsignedDecimal("45754683688356"))  # LLL
        liq_tree.add_m_liq(LiqRange(low=2, high=3), UnsignedDecimal("245346257245745"))  # LLR
        liq_tree.add_m_liq(LiqRange(low=4, high=5), UnsignedDecimal("243457472"))  # LRL
        liq_tree.add_m_liq(LiqRange(low=1, high=1), UnsignedDecimal("2462"))  # LLLR
        liq_tree.add_m_liq(LiqRange(low=4, high=4), UnsignedDecimal("45656756785"))  # LRLL

        liq_tree.add_t_liq(LiqRange(low=0, high=7), UnsignedDecimal("5645645"), UnsignedDecimal("4357e18"), UnsignedDecimal("345345345e6"))  # L
        liq_tree.add_t_liq(LiqRange(low=0, high=3), UnsignedDecimal("3456835"), UnsignedDecimal("293874927834e18"), UnsignedDecimal("2345346e6"))  # LL
        liq_tree.add_t_liq(LiqRange(low=4, high=7), UnsignedDecimal("51463465"), UnsignedDecimal("23452e18"), UnsignedDecimal("12341235e6"))  # LR
        liq_tree.add_t_liq(LiqRange(low=0, high=1), UnsignedDecimal("23453467234"), UnsignedDecimal("134235e18"), UnsignedDecimal("34534634e6"))  # LLL
        liq_tree.add_t_liq(LiqRange(low=2, high=3), UnsignedDecimal("456756745"), UnsignedDecimal("1233463e18"), UnsignedDecimal("2341356e6"))  # LLR
        liq_tree.add_t_liq(LiqRange(low=4, high=5), UnsignedDecimal("3457472"), UnsignedDecimal("45e18"), UnsignedDecimal("1324213563456457e6"))  # LRL
        liq_tree.add_t_liq(LiqRange(low=1, high=1), UnsignedDecimal("262"), UnsignedDecimal("4567e18"), UnsignedDecimal("1235146e6"))  # LLLR
        liq_tree.add_t_liq(LiqRange(low=4, high=4), UnsignedDecimal("4564573"), UnsignedDecimal("4564564e18"), UnsignedDecimal("6345135e6"))  # LRLL

        # Verify initial state
        # m_liq
        self.assertEqual(root.m_liq, UnsignedDecimal("432"))
        self.assertEqual(L.m_liq, UnsignedDecimal("98237498262"))
        self.assertEqual(LL.m_liq, UnsignedDecimal("932141354"))
        self.assertEqual(LR.m_liq, UnsignedDecimal("151463465"))
        self.assertEqual(LLL.m_liq, UnsignedDecimal("45754683688356"))
        self.assertEqual(LLR.m_liq, UnsignedDecimal("245346257245745"))
        self.assertEqual(LRL.m_liq, UnsignedDecimal("243457472"))
        self.assertEqual(LLLR.m_liq, UnsignedDecimal("2462"))
        self.assertEqual(LRLL.m_liq, UnsignedDecimal("45656756785"))

        # t_liq
        self.assertEqual(root.t_liq, UnsignedDecimal("0"))
        self.assertEqual(L.t_liq, UnsignedDecimal("5645645"))
        self.assertEqual(LL.t_liq, UnsignedDecimal("3456835"))
        self.assertEqual(LR.t_liq, UnsignedDecimal("51463465"))
        self.assertEqual(LLL.t_liq, UnsignedDecimal("23453467234"))
        self.assertEqual(LLR.t_liq, UnsignedDecimal("456756745"))
        self.assertEqual(LRL.t_liq, UnsignedDecimal("3457472"))
        self.assertEqual(LLLR.t_liq, UnsignedDecimal("262"))
        self.assertEqual(LRLL.t_liq, UnsignedDecimal("4564573"))

        # subtree_m_liq
        self.assertEqual(root.subtree_m_liq, UnsignedDecimal(
            "583038259954677"))  # 432*16 + 98237498262*8 + 932141354*4 + 151463465*4 + 45754683688356*2 + 245346257245745*2 + 243457472*2 + 2462*1 + 45656756785*1 = 583038259954677
        self.assertEqual(L.subtree_m_liq, UnsignedDecimal(
            "583038259947765"))  # 98237498262*8 + 932141354*4 + 151463465*4 + 45754683688356*2 + 245346257245745*2 + 243457472*2 + 2462*1 + 45656756785*1 = 583038259947765
        self.assertEqual(LL.subtree_m_liq, UnsignedDecimal("582205610436080"))  # 932141354*4 + 45754683688356*2 + 245346257245745*2 + 2462*1 = 582205610436080
        self.assertEqual(LR.subtree_m_liq, UnsignedDecimal("46749525589"))  # 151463465*4 + 243457472*2 + 45656756785*1 = 46749525589
        self.assertEqual(LLL.subtree_m_liq, UnsignedDecimal("91509367379174"))  # 45754683688356*2 + 2462*1 = 91509367379174
        self.assertEqual(LLR.subtree_m_liq, UnsignedDecimal("490692514491490"))  # 245346257245745*2 = 490692514491490
        self.assertEqual(LRL.subtree_m_liq, UnsignedDecimal("46143671729"))  # 243457472*2 + 45656756785*1 = 46143671729
        self.assertEqual(LLLR.subtree_m_liq, UnsignedDecimal("2462"))  # 2462*1 = 2462
        self.assertEqual(LRLL.subtree_m_liq, UnsignedDecimal("45656756785"))  # 45656756785*1 = 45656756785

        # borrow_x
        self.assertEqual(root.token_x_borrow, UnsignedDecimal("0"))
        self.assertEqual(L.token_x_borrow, UnsignedDecimal("4357e18"))
        self.assertEqual(LL.token_x_borrow, UnsignedDecimal("293874927834e18"))
        self.assertEqual(LR.token_x_borrow, UnsignedDecimal("23452e18"))
        self.assertEqual(LLL.token_x_borrow, UnsignedDecimal("134235e18"))
        self.assertEqual(LLR.token_x_borrow, UnsignedDecimal("1233463e18"))
        self.assertEqual(LRL.token_x_borrow, UnsignedDecimal("45e18"))
        self.assertEqual(LLLR.token_x_borrow, UnsignedDecimal("4567e18"))
        self.assertEqual(LRLL.token_x_borrow, UnsignedDecimal("4564564e18"))

        # subtree_borrow_x
        self.assertEqual(root.token_x_subtree_borrow,
                         UnsignedDecimal("293880892517e18"))  # 0 + 4357e18 + 293874927834e18 + 23452e18 + 134235e18 + 1233463e18 + 45e18 + 4567e18 + 4564564e18 = 293880892517e18
        self.assertEqual(L.token_x_subtree_borrow,
                         UnsignedDecimal("293880892517e18"))  # 4357e18 + 293874927834e18 + 23452e18 + 134235e18 + 1233463e18 + 45e18 + 4567e18 + 4564564e18 = 293880892517e18
        self.assertEqual(LL.token_x_subtree_borrow, UnsignedDecimal("293876300099e18"))  # 293874927834e18 + 134235e18 + 1233463e18 + 4567e18 = 293876300099e18
        self.assertEqual(LR.token_x_subtree_borrow, UnsignedDecimal("4588061e18"))  # 23452e18 + 45e18 + 4564564e18 = 4588061e18
        self.assertEqual(LLL.token_x_subtree_borrow, UnsignedDecimal("138802e18"))  # 134235e18 + 4567e18 = 138802e18
        self.assertEqual(LLR.token_x_subtree_borrow, UnsignedDecimal("1233463e18"))  # 1233463e18
        self.assertEqual(LRL.token_x_subtree_borrow, UnsignedDecimal("4564609e18"))  # 45e18 + 4564564e18 = 4564609e18
        self.assertEqual(LLLR.token_x_subtree_borrow, UnsignedDecimal("4567e18"))  # 4567e18
        self.assertEqual(LRLL.token_x_subtree_borrow, UnsignedDecimal("4564564e18"))  # 4564564e18

        # borrow_y
        self.assertEqual(root.token_y_borrow, UnsignedDecimal("0"))
        self.assertEqual(L.token_y_borrow, UnsignedDecimal("345345345e6"))
        self.assertEqual(LL.token_y_borrow, UnsignedDecimal("2345346e6"))
        self.assertEqual(LR.token_y_borrow, UnsignedDecimal("12341235e6"))
        self.assertEqual(LLL.token_y_borrow, UnsignedDecimal("34534634e6"))
        self.assertEqual(LLR.token_y_borrow, UnsignedDecimal("2341356e6"))
        self.assertEqual(LRL.token_y_borrow, UnsignedDecimal("1324213563456457e6"))
        self.assertEqual(LLLR.token_y_borrow, UnsignedDecimal("1235146e6"))
        self.assertEqual(LRLL.token_y_borrow, UnsignedDecimal("6345135e6"))

        # subtree_borrow_y
        self.assertEqual(root.token_y_subtree_borrow, UnsignedDecimal(
            "1324213967944654e6"))  # 0 + 345345345e6 + 2345346e6 + 12341235e6 + 34534634e6 + 2341356e6 + 1324213563456457e6 + 1235146e6 + 6345135e6 = 1324213967944654e6
        self.assertEqual(L.token_y_subtree_borrow, UnsignedDecimal(
            "1324213967944654e6"))  # 345345345e6 + 2345346e6 + 12341235e6 + 34534634e6 + 2341356e6 + 1324213563456457e6 + 1235146e6 + 6345135e6 = 1324213967944654e6
        self.assertEqual(LL.token_y_subtree_borrow, UnsignedDecimal("40456482e6"))  # 2345346e6 + 34534634e6 + 2341356e6 + 1235146e6 = 40456482e6
        self.assertEqual(LR.token_y_subtree_borrow, UnsignedDecimal("1324213582142827e6"))  # 12341235e6 + 1324213563456457e6 + 6345135e6 = 1324213582142827e6
        self.assertEqual(LLL.token_y_subtree_borrow, UnsignedDecimal("35769780e6"))  # 34534634e6 + 1235146e6 = 35769780e6
        self.assertEqual(LLR.token_y_subtree_borrow, UnsignedDecimal("2341356e6"))  # 2341356e6
        self.assertEqual(LRL.token_y_subtree_borrow, UnsignedDecimal("1324213569801592e6"))  # 1324213563456457e6 + 6345135e6 = 1324213569801592e6
        self.assertEqual(LLLR.token_y_subtree_borrow, UnsignedDecimal("1235146e6"))  # 1235146e6
        self.assertEqual(LRLL.token_y_subtree_borrow, UnsignedDecimal("6345135e6"))  # 6345135e6

        # Test fees while targeting (1, 4)
        # 1) Trigger fee update through path L->LL->LLR by updating LLR
        liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("997278349210980290827452342352346")
        liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("7978726162930599238079167453467080976862")

        liq_tree.add_m_liq(LiqRange(low=2, high=3), UnsignedDecimal("564011300817682367503451461"))  # LLR
        liq_tree.remove_m_liq(LiqRange(low=2, high=3), UnsignedDecimal("564011300817682367503451461"))  # LLR

        # LLR
        #
        #   total_m_liq = 490692514491490 + (932141354 + 98237498262 + 432) * 2 = 490890853771586
        #
        #   earn_x      = 997278349210980290827452342352346 * 1233463e18 / 490890853771586 / 2**64 = 135843184601648135054031.953000417177564160084206701934727792
        #   earn_x_sub  = 997278349210980290827452342352346 * 1233463e18 / 490890853771586 / 2**64 = 135843184601648135054031.953000417177564160084206701934727792
        #
        #   earn_y      = 7978726162930599238079167453467080976862 * 2341356e6 / 490890853771586 / 2**64 = 2062986327173371860.88896572844074868101158495986576204342125
        #   earn_y_sub  = 7978726162930599238079167453467080976862 * 2341356e6 / 490890853771586 / 2**64 = 2062986327173371860.88896572844074868101158495986576204342125
        self.assertEqual(LLR.token_x_cumulative_earned_per_m_liq, UnsignedDecimal("135843184601648135054031"))
        self.assertEqual(LLR.token_x_cumulative_earned_per_m_subtree_liq, UnsignedDecimal("135843184601648135054031"))
        self.assertEqual(LLR.token_y_cumulative_earned_per_m_liq, UnsignedDecimal("2062986327173371860"))
        self.assertEqual(LLR.token_y_cumulative_earned_per_m_subtree_liq, UnsignedDecimal("2062986327173371860"))

        # LL
        #
        #   total_m_liq = 582205610436080 + (98237498262 + 432) * 4 = 582598560430856
        #
        #   earn_x      = 997278349210980290827452342352346 * 293874927834e18 / 582598560430856 / 2**64 = 27270292518041237351900241102.9072917119646623397725295368780
        #   earn_x_sub  = 997278349210980290827452342352346 * 293876300099e18 / 582598560430856 / 2**64 = 27270419858159151079872803581.0095490519975481585750941907483
        #
        #   earn_y      = 7978726162930599238079167453467080976862 * 2345346e6 / 582598560430856 / 2**64 = 1741210798541653346.44401134728453048205241418030400364012179
        #   earn_y_sub  = 7978726162930599238079167453467080976862 * 40456482e6 / 582598560430856 / 2**64 = 30035339489101405447.4912908710324004754969276780541880790817
        self.assertEqual(LL.token_x_cumulative_earned_per_m_liq, UnsignedDecimal("27270292518041237351900241102"))
        self.assertEqual(LL.token_x_cumulative_earned_per_m_subtree_liq, UnsignedDecimal("27270419858159151079872803581"))
        self.assertEqual(LL.token_y_cumulative_earned_per_m_liq, UnsignedDecimal("1741210798541653346"))
        self.assertEqual(LL.token_y_cumulative_earned_per_m_subtree_liq, UnsignedDecimal("30035339489101405447"))

        # L
        #
        #   total_m_liq = 583038259947765 + (432) * 8 = 583038259951221
        #
        #   earn_x      = 997278349210980290827452342352346 * 4357e18 / 583038259951221 / 2**64 = 404005403049228369014.124610642017839196445240663620779618212
        #   earn_x_sub  = 997278349210980290827452342352346 * 293880892517e18 / 583038259951221 / 2**64 = 27250279648794479314672290097.5284183991019310121509607727857
        #
        #   earn_y      = 7978726162930599238079167453467080976862 * 345345345e6 / 583038259951221 / 2**64 = 256194846273571639740.673516172246801895282064962841499611008
        #   earn_y_sub  = 7978726162930599238079167453467080976862 * 1324213967944654e6 / 583038259951221 / 2**64 = 982369673901053899051127131.509115296130579701967553185312315
        self.assertEqual(L.token_x_cumulative_earned_per_m_liq, UnsignedDecimal("404005403049228369014"))
        self.assertEqual(L.token_x_cumulative_earned_per_m_subtree_liq, UnsignedDecimal("27250279648794479314672290097"))
        self.assertEqual(L.token_y_cumulative_earned_per_m_liq, UnsignedDecimal("256194846273571639740"))
        self.assertEqual(L.token_y_cumulative_earned_per_m_subtree_liq, UnsignedDecimal("982369673901053899051127131"))

        # 2) Trigger fee update through path L->LR->LRL->LRLL by updating LRLL
        liq_tree.add_m_liq(LiqRange(low=4, high=4), UnsignedDecimal("45656756785"))  # LRLL
        liq_tree.remove_m_liq(LiqRange(low=4, high=4), UnsignedDecimal("45656756785"))  # LRLL

        # LRLL
        #   total_m_liq = 45656756785 + (243457472 + 151463465 + 98237498262 + 432) * 1 = 144289176416
        #
        #   earn_x      = 997278349210980290827452342352346 * 4564564e18 / 144289176416 / 2**64 = 1710260298962014449572659226.45857973175650767716107059096213
        #   earn_x_sub  = 997278349210980290827452342352346 * 4564564e18 / 144289176416 / 2**64 = 1710260298962014449572659226.45857973175650767716107059096213
        #
        #   earn_y      = 7978726162930599238079167453467080976862 * 6345135e6 / 144289176416 / 2**64 = 19020457094450723823822.1304935642458081127558849886746302550
        #   earn_y_sub  = 7978726162930599238079167453467080976862 * 6345135e6 / 144289176416 / 2**64 = 19020457094450723823822.1304935642458081127558849886746302550
        self.assertEqual(LRLL.token_x_cumulative_earned_per_m_liq, UnsignedDecimal("1710260298962014449572659226"))
        self.assertEqual(LRLL.token_x_cumulative_earned_per_m_subtree_liq, UnsignedDecimal("1710260298962014449572659226"))
        self.assertEqual(LRLL.token_y_cumulative_earned_per_m_liq, UnsignedDecimal("19020457094450723823822"))
        self.assertEqual(LRLL.token_y_cumulative_earned_per_m_subtree_liq, UnsignedDecimal("19020457094450723823822"))

        # LRL
        #   total_m_liq = 46143671729 + (151463465 + 98237498262 + 432) * 2 = 242921596047
        #
        #   earn_x      = 997278349210980290827452342352346 * 45e18 / 242921596047 / 2**64 = 10014817880995372310152.4742715985679179265308809095477236672
        #   earn_x_sub  = 997278349210980290827452342352346 * 4564609e18 / 242921596047 / 2**64 = 1015860618510053453450506120.72016150011730453772839221611958
        #
        #   earn_y      = 7978726162930599238079167453467080976862 * 1324213563456457e6 / 242921596047 / 2**64 = 2357793377238426581071757403793.96341043019973158984354448841
        #   earn_y_sub  = 7978726162930599238079167453467080976862 * 1324213569801592e6 / 242921596047 / 2**64 = 2357793388536088599903418420664.92708711347544674139375617462
        self.assertEqual(LRL.token_x_cumulative_earned_per_m_liq, UnsignedDecimal("10014817880995372310152"))
        self.assertEqual(LRL.token_x_cumulative_earned_per_m_subtree_liq, UnsignedDecimal("1015860618510053453450506120"))
        self.assertEqual(LRL.token_y_cumulative_earned_per_m_liq, UnsignedDecimal("2357793377238426581071757403793"))
        self.assertEqual(LRL.token_y_cumulative_earned_per_m_subtree_liq, UnsignedDecimal("2357793388536088599903418420664"))

        # LR
        #   total_m_liq = 46749525589 + (98237498262 + 432) * 4 = 439699520365
        #
        #   earn_x      = 997278349210980290827452342352346 * 23452e18 / 439699520365 / 2**64 = 2883504023897755903335799.02165969971328846599101621918354759
        #   earn_x_sub  = 997278349210980290827452342352346 * 4588061e18 / 439699520365 / 2**64 = 564117872905865676599639663.786245246727357690738865154506505
        #
        #   earn_y      = 7978726162930599238079167453467080976862 * 12341235e6 / 439699520365 / 2**64 = 12139937971620398360316.5575159331335181718549141795773004218
        #   earn_y_sub  = 7978726162930599238079167453467080976862 * 1324213582142827e6 / 439699520365 / 2**64 = 1302614426221619876588878010887.22237028229312127108609228047
        self.assertEqual(LR.token_x_cumulative_earned_per_m_liq, UnsignedDecimal("2883504023897755903335799"))
        self.assertEqual(LR.token_x_cumulative_earned_per_m_subtree_liq, UnsignedDecimal("564117872905865676599639663"))
        self.assertEqual(LR.token_y_cumulative_earned_per_m_liq, UnsignedDecimal("12139937971620398360316"))
        self.assertEqual(LR.token_y_cumulative_earned_per_m_subtree_liq, UnsignedDecimal("1302614426221619876588878010887"))

        # L
        # Borrows have not changed. Results should be the same!
        self.assertEqual(L.token_x_cumulative_earned_per_m_liq, UnsignedDecimal("404005403049228369014"))
        self.assertEqual(L.token_x_cumulative_earned_per_m_subtree_liq, UnsignedDecimal("27250279648794479314672290097"))
        self.assertEqual(L.token_y_cumulative_earned_per_m_liq, UnsignedDecimal("256194846273571639740"))
        self.assertEqual(L.token_y_cumulative_earned_per_m_subtree_liq, UnsignedDecimal("982369673901053899051127131"))

        # 3) Trigger fee update for remaining nodes by updating the range (1,3) LLLR, LLL
        #    For this last one, also update the rates to increment accumulated fees in L
        #    While previous step does not, meaning we also tested that nothing should have accumulated.
        #
        #    For un-accumulated nodes
        #    x_rate = 129987217567345826 + 997278349210980290827452342352346 = 997278349210980420814669909698172
        #    y_rate = 234346579834678237846892 + 7978726162930599238079167453467080976862 = 7978726162930599472425747288145318823754
        liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("129987217567345826")
        liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("234346579834678237846892")

        liq_tree.add_t_liq(LiqRange(low=1, high=3), UnsignedDecimal("32"), UnsignedDecimal("8687384723"), UnsignedDecimal("56758698"))  # LLLR, LLL
        liq_tree.remove_t_liq(LiqRange(low=1, high=3), UnsignedDecimal("32"), UnsignedDecimal("8687384723"), UnsignedDecimal("56758698"))  # LLLR, LLL

        # LLLR
        #   total_m_liq = 2462 + (45754683688356 + 932141354 + 98237498262 + 432) * 1 = 45853853330866
        #
        #   earn_x      = 997278349210980420814669909698172 * 4567e18 / 45853853330866 / 2**64 = 5384580105567269319768.51254007088771506177689554397322456673
        #   earn_x_sub  = 997278349210980420814669909698172 * 4567e18 / 45853853330866 / 2**64 = 5384580105567269319768.51254007088771506177689554397322456673
        #
        #   earn_y      = 7978726162930599472425747288145318823754 * 1235146e6 / 45853853330866 / 2**64 = 11650814730151920570.8396639745369843707702302526968216514839
        #   earn_y_sub  = 7978726162930599472425747288145318823754 * 1235146e6 / 45853853330866 / 2**64 = 11650814730151920570.8396639745369843707702302526968216514839
        self.assertEqual(LLLR.token_x_cumulative_earned_per_m_liq, UnsignedDecimal("5384580105567269319768"))
        self.assertEqual(LLLR.token_x_cumulative_earned_per_m_subtree_liq, UnsignedDecimal("5384580105567269319768"))
        self.assertEqual(LLLR.token_y_cumulative_earned_per_m_liq, UnsignedDecimal("11650814730151920570"))
        self.assertEqual(LLLR.token_y_cumulative_earned_per_m_subtree_liq, UnsignedDecimal("11650814730151920570"))

        # LLL
        #   total_m_liq = 91509367379174 + (932141354 + 98237498262 + 432) * 2 = 91707706659270
        #
        #   earn_x      = 997278349210980420814669909698172 * 134235e18 / 91707706659270 / 2**64 = 79132812622096209716370.5876318860028597239769562864471324430
        #   earn_x_sub  = 997278349210980420814669909698172 * 138802e18 / 91707706659270 / 2**64 = 81825102674952122032641.7871976834727823250825007372997718729
        #
        #   earn_y      = 7978726162930599472425747288145318823754 * 34534634e6 / 91707706659270 / 2**64 = 162878162791446141833.294568661856722588591983837787778442557
        #   earn_y_sub  = 7978726162930599472425747288145318823754 * 35769780e6 / 91707706659270 / 2**64 = 168703570156678491951.753228258608716065007834501481165880576
        self.assertEqual(LLL.token_x_cumulative_earned_per_m_liq, UnsignedDecimal("79132812622096209716370"))
        self.assertEqual(LLL.token_x_cumulative_earned_per_m_subtree_liq, UnsignedDecimal("81825102674952122032641"))
        self.assertEqual(LLL.token_y_cumulative_earned_per_m_liq, UnsignedDecimal("162878162791446141833"))
        self.assertEqual(LLL.token_y_cumulative_earned_per_m_subtree_liq, UnsignedDecimal("168703570156678491951"))

        # LL
        #   Note: LL previously accumulated fees, so we use the new rate as provided. Then add to the previously accumulated fees.
        #         The results SHOULD be the same as if the two rates were added, and accumulated once.
        #         However, that is not the case. Due to decimal truncation that happens over two transactions. See below.
        #
        #   total_m_liq = 582205610436080 + (98237498262 + 432) * 4 = 582598560430856
        #
        #   Expected in 1 transaction
        #   earn_x      = 1299872175673458264503459867290698790837483436947198765949906360687986981 * 293874927834e18 / 582598560430856 / 2**64 = 35544634549344534575302731950184064775098096623320842527740739153078.75082067380701457525147559485733770210963
        #   earn_x_sub  = 1299872175673458264503459867290698790837483436947198765949906360687986981 * 293876300099e18 / 582598560430856 / 2**64 = 35544800526953748684785622304061478291909912715982970794626727543515.67837110616273194884758309091127470639015
        #
        #   earn_y      = 2343465798346782378468923640892347700326625400777465238079512798813357853648 * 2345346e6 / 582598560430856 / 2**64 = 511418473421538198191409430001729877691494201326333679.0963768041829950138557552907316220422703628558848163908
        #   earn_y_sub  = 2343465798346782378468923640892347700326625400777465238079512798813357853648 * 40456482e6 / 582598560430856 / 2**64 = 8821808067741790988384310101577867302175515556793408995.669016189358355860561774047790233928773909697150300378
        #
        #   Expected in 2 transactions
        #   earn_x      = 129987217567345826 * 293874927834e18 / 582598560430856 / 2**64 = 3554463454934.45344521569040863374143258749172847837137687025
        #   earn_x_sub  = 129987217567345826 * 293876300099e18 / 582598560430856 / 2**64 = 3554480052695.37485616392194040566938030042839994115185549318
        #
        #   earn_y      = 234346579834678237846892 * 2345346e6 / 582598560430856 / 2**64 = 51.141847342153819819140863544368355730624773075228977719082842282
        #   earn_y_sub  = 234346579834678237846892 * 40456482e6 / 582598560430856 / 2**64 = 882.18080677417909883842963957010802883055121959492790529434721584
        #
        #   acc_x       = 3554463454934 + 27270292518041237351900241102 = 27270292518041240906363696036
        #   acc_x_sub   = 3554480052695 + 27270419858159151079872803581 = 27270419858159154634352856276
        #
        #   acc_y       = 51 + 1741210798541653346 = 1741210798541653397
        #   acc_y_sub   = 882 + 30035339489101405447 = 30035339489101406329
        self.assertEqual(LL.token_x_cumulative_earned_per_m_liq, UnsignedDecimal("27270292518041240906363696036"))  # 1 wei lost
        self.assertEqual(LL.token_x_cumulative_earned_per_m_subtree_liq, UnsignedDecimal("27270419858159154634352856276"))
        self.assertEqual(LL.token_y_cumulative_earned_per_m_liq, UnsignedDecimal("1741210798541653397"))  # 1 wei lost
        self.assertEqual(LL.token_y_cumulative_earned_per_m_subtree_liq, UnsignedDecimal("30035339489101406329"))

        # L
        #   Note: (same situation as LL above)
        #
        #   total_m_liq = 583038259947765 + (432) * 8 = 583038259951221
        #
        #   Expected in 1 transaction
        #   earn_x      = 1299872175673458264503459867290698790837483436947198765949906360687986981 * 4357e18 / 583038259951221 / 2**64 = 526588572449127820710280925096499286631826368408350578683678.8949320786875222752967719865098507132989325023672
        #   earn_x_sub  = 1299872175673458264503459867290698790837483436947198765949906360687986981 * 293880892517e18 / 583038259951221 / 2**64 = 35518549382741014580801587134532851665736731679050016244983472266163.77158207946190817820623319059828307670852
        #
        #   earn_y      = 2343465798346782378468923640892347700326625400777465238079512798813357853648 * 345345345e6 / 583038259951221 / 2**64 = 75248084430347809841211701855286934435441672114601405440.36959084052843872095985545406590238625971175786589905
        #   earn_y_sub  = 2343465798346782378468923640892347700326625400777465238079512798813357853648 * 1324213967944654e6 / 583038259951221 / 2**64 = 288535999996598223755002019090052510701800094598545473522203908.3456298612650105591841256935791299290626023275
        #
        # --
        #   earn_x      = 129987217567345826 * 4357e18 / 583038259951221 / 2**64 = 52658.857244912781888589346071378112785850967017095980665781805581
        #   acc_x       = 52658 + 404005403049228369014 = 404005403049228421672
        #   earn_x_sub  = 129987217567345826 * 293880892517e18 / 583038259951221 / 2**64 = 3551854938274.10144577461323882349951197727139690881248462550
        #   acc_x_sub   = 3551854938274 + 27250279648794479314672290097 = 27250279648794482866527228371
        #
        #   earn_y      = 234346579834678237846892 * 345345345e6 / 583038259951221 / 2**64 = 7524.8084430347809841211584947169489394855931019950463150426607553
        #   acc_y       = 7524 + 256194846273571639740 = 256194846273571647264
        #   earn_y_sub  = 234346579834678237846892 * 1324213967944654e6 / 583038259951221 / 2**64 = 28853599999.6598223755001570810194889233587464872923634206316
        #   acc_y_sub   = 28853599999 + 982369673901053899051127131 = 982369673901053927904727130
        self.assertEqual(L.token_x_cumulative_earned_per_m_liq, UnsignedDecimal("404005403049228421672"))
        self.assertEqual(L.token_x_cumulative_earned_per_m_subtree_liq, UnsignedDecimal("27250279648794482866527228371"))
        self.assertEqual(L.token_y_cumulative_earned_per_m_liq, UnsignedDecimal("256194846273571647264"))  # 1 wei lost
        self.assertEqual(L.token_y_cumulative_earned_per_m_subtree_liq, UnsignedDecimal("982369673901053927904727130"))  # 1 wei lost

        # 4) Confirm root fees are correct (although behavior leading to this state should have been previously tested at L and LL
        #   total_m_liq = 583038259954677
        #
        #   earn_x      = 997278349210980420814669909698172 * 0 / 583038259954677 / 2**64 = 0
        #   earn_x_sub  = 997278349210980420814669909698172 * 293880892517e18 / 583038259954677 / 2**64 = 27250279648632954930995939801.6330981070932019410874863041294
        #
        #   earn_y      = 7978726162930599472425747288145318823754 * 0 / 583038259954677 / 2**64 = 0
        #   earn_y_sub  = 7978726162930599472425747288145318823754 * 1324213967944654e6 / 583038259954677 / 2**64 = 982369673895230863062865876.398682260578858069936100777250356
        self.assertEqual(root.token_x_cumulative_earned_per_m_liq, UnsignedDecimal("0"))
        self.assertEqual(root.token_x_cumulative_earned_per_m_subtree_liq, UnsignedDecimal("27250279648632954930995939801"))
        self.assertEqual(root.token_y_cumulative_earned_per_m_liq, UnsignedDecimal("0"))
        self.assertEqual(root.token_y_cumulative_earned_per_m_subtree_liq, UnsignedDecimal("982369673895230863062865875"))  # 1 wei lost

    # def test_left_and_right_leg_stopping_below_peak(self):
    #     #   Range: (1, 4)
    #     #
    #     #                                  L(0-7)
    #     #                             __--  --__
    #     #                        __---          ---__
    #     #                      /                       \
    #     #                   LL(0-3)                     LR(4-7)
    #     #                 /   \                         /
    #     #               /       \                     /
    #     #             /           \                 /
    #     #           LLL(0-1)       LLR(2-3)       LRL(4-5)
    #     #              \                         /
    #     #               \                       /
    #     #           LLLR(1)                   LRLL(4)
    #
    #     liq_tree = self.liq_tree
    #
    #     # 1st (1, 4)
    #     root: LiqNode = liq_tree.nodes[liq_tree.root_key]
    #     L: LiqNode = liq_tree.nodes[(8 << 24) | 16]
    #     LL: LiqNode = liq_tree.nodes[(4 << 24) | 16]
    #     LR: LiqNode = liq_tree.nodes[(4 << 24) | 20]
    #     LLL: LiqNode = liq_tree.nodes[(2 << 24) | 16]
    #     LLR: LiqNode = liq_tree.nodes[(2 << 24) | 18]
    #     LRL: LiqNode = liq_tree.nodes[(2 << 24) | 20]
    #     LLLR: LiqNode = liq_tree.nodes[(1 << 24) | 17]
    #     LRLL: LiqNode = liq_tree.nodes[(1 << 24) | 20]
    #
    #     # Pre-populate nodes w/o fee calculation
    #     liq_tree.add_wide_m_liq(UnsignedDecimal("432"))
    #     liq_tree.add_m_liq(LiqRange(low=0, high=7), UnsignedDecimal("98237498262"))      # L
    #     liq_tree.add_m_liq(LiqRange(low=0, high=3), UnsignedDecimal("932141354"))        # LL
    #     liq_tree.add_m_liq(LiqRange(low=4, high=7), UnsignedDecimal("151463465"))        # LR
    #     liq_tree.add_m_liq(LiqRange(low=0, high=1), UnsignedDecimal("45754683688356"))   # LLL
    #     liq_tree.add_m_liq(LiqRange(low=2, high=3), UnsignedDecimal("245346257245745"))  # LLR
    #     liq_tree.add_m_liq(LiqRange(low=4, high=5), UnsignedDecimal("243457472"))        # LRL
    #     liq_tree.add_m_liq(LiqRange(low=1, high=1), UnsignedDecimal("2462"))             # LLLR
    #     liq_tree.add_m_liq(LiqRange(low=4, high=4), UnsignedDecimal("45656756785"))      # LRLL
    #
    #     liq_tree.add_t_liq(LiqRange(low=0, high=7), UnsignedDecimal("5645645"), UnsignedDecimal("4357e18"), UnsignedDecimal("345345345e6"))        # L
    #     liq_tree.add_t_liq(LiqRange(low=0, high=3), UnsignedDecimal("3456835"), UnsignedDecimal("293874927834e18"), UnsignedDecimal("2345346e6"))  # LL
    #     liq_tree.add_t_liq(LiqRange(low=4, high=7), UnsignedDecimal("51463465"), UnsignedDecimal("23452e18"), UnsignedDecimal("12341235e6"))       # LR
    #     liq_tree.add_t_liq(LiqRange(low=0, high=1), UnsignedDecimal("23453467234"), UnsignedDecimal("134235e18"), UnsignedDecimal("34534634e6"))   # LLL
    #     liq_tree.add_t_liq(LiqRange(low=2, high=3), UnsignedDecimal("456756745"), UnsignedDecimal("1233463e18"), UnsignedDecimal("2341356e6"))     # LLR
    #     liq_tree.add_t_liq(LiqRange(low=4, high=5), UnsignedDecimal("3457472"), UnsignedDecimal("45e18"), UnsignedDecimal("1324213563456457e6"))   # LRL
    #     liq_tree.add_t_liq(LiqRange(low=1, high=1), UnsignedDecimal("262"), UnsignedDecimal("4567e18"), UnsignedDecimal("1235146e6"))              # LLLR
    #     liq_tree.add_t_liq(LiqRange(low=4, high=4), UnsignedDecimal("4564573"), UnsignedDecimal("4564564e18"), UnsignedDecimal("6345135e6"))       # LRLL
    #
    #     # Verify initial state
    #     # m_liq
    #     self.assertEqual(root.m_liq, UnsignedDecimal("432"))
    #     self.assertEqual(L.m_liq, UnsignedDecimal("98237498262"))
    #     self.assertEqual(LL.m_liq, UnsignedDecimal("932141354"))
    #     self.assertEqual(LR.m_liq, UnsignedDecimal("151463465"))
    #     self.assertEqual(LLL.m_liq, UnsignedDecimal("45754683688356"))
    #     self.assertEqual(LLR.m_liq, UnsignedDecimal("245346257245745"))
    #     self.assertEqual(LRL.m_liq, UnsignedDecimal("243457472"))
    #     self.assertEqual(LLLR.m_liq, UnsignedDecimal("2462"))
    #     self.assertEqual(LRLL.m_liq, UnsignedDecimal("45656756785"))
    #
    #     # t_liq
    #     self.assertEqual(root.t_liq, UnsignedDecimal("0"))
    #     self.assertEqual(L.t_liq, UnsignedDecimal("5645645"))
    #     self.assertEqual(LL.t_liq, UnsignedDecimal("3456835"))
    #     self.assertEqual(LR.t_liq, UnsignedDecimal("51463465"))
    #     self.assertEqual(LLL.t_liq, UnsignedDecimal("23453467234"))
    #     self.assertEqual(LLR.t_liq, UnsignedDecimal("456756745"))
    #     self.assertEqual(LRL.t_liq, UnsignedDecimal("3457472"))
    #     self.assertEqual(LLLR.t_liq, UnsignedDecimal("262"))
    #     self.assertEqual(LRLL.t_liq, UnsignedDecimal("4564573"))
    #
    #     # subtree_m_liq
    #     self.assertEqual(root.subtree_m_liq, UnsignedDecimal("583038259954677"))  # 432*16 + 98237498262*8 + 932141354*4 + 151463465*4 + 45754683688356*2 + 245346257245745*2 + 243457472*2 + 2462*1 + 45656756785*1 = 583038259954677
    #     self.assertEqual(L.subtree_m_liq, UnsignedDecimal("583038259947765"))     # 98237498262*8 + 932141354*4 + 151463465*4 + 45754683688356*2 + 245346257245745*2 + 243457472*2 + 2462*1 + 45656756785*1 = 583038259947765
    #     self.assertEqual(LL.subtree_m_liq, UnsignedDecimal("582205610436080"))    # 932141354*4 + 45754683688356*2 + 245346257245745*2 + 2462*1 = 582205610436080
    #     self.assertEqual(LR.subtree_m_liq, UnsignedDecimal("46749525589"))        # 151463465*4 + 243457472*2 + 45656756785*1 = 46749525589
    #     self.assertEqual(LLL.subtree_m_liq, UnsignedDecimal("91509367379174"))    # 45754683688356*2 + 2462*1 = 91509367379174
    #     self.assertEqual(LLR.subtree_m_liq, UnsignedDecimal("490692514491490"))   # 245346257245745*2 = 490692514491490
    #     self.assertEqual(LRL.subtree_m_liq, UnsignedDecimal("46143671729"))       # 243457472*2 + 45656756785*1 = 46143671729
    #     self.assertEqual(LLLR.subtree_m_liq, UnsignedDecimal("2462"))             # 2462*1 = 2462
    #     self.assertEqual(LRLL.subtree_m_liq, UnsignedDecimal("45656756785"))      # 45656756785*1 = 45656756785
    #
    #     # borrow_x
    #     self.assertEqual(root.token_x_borrow, UnsignedDecimal("0"))
    #     self.assertEqual(L.token_x_borrow, UnsignedDecimal("4357e18"))
    #     self.assertEqual(LL.token_x_borrow, UnsignedDecimal("293874927834e18"))
    #     self.assertEqual(LR.token_x_borrow, UnsignedDecimal("23452e18"))
    #     self.assertEqual(LLL.token_x_borrow, UnsignedDecimal("134235e18"))
    #     self.assertEqual(LLR.token_x_borrow, UnsignedDecimal("1233463e18"))
    #     self.assertEqual(LRL.token_x_borrow, UnsignedDecimal("45e18"))
    #     self.assertEqual(LLLR.token_x_borrow, UnsignedDecimal("4567e18"))
    #     self.assertEqual(LRLL.token_x_borrow, UnsignedDecimal("4564564e18"))
    #
    #     # subtree_borrow_x
    #     self.assertEqual(root.token_x_subtree_borrow, UnsignedDecimal("293880892517e18"))  # 0 + 4357e18 + 293874927834e18 + 23452e18 + 134235e18 + 1233463e18 + 45e18 + 4567e18 + 4564564e18 = 293880892517e18
    #     self.assertEqual(L.token_x_subtree_borrow, UnsignedDecimal("293880892517e18"))     # 4357e18 + 293874927834e18 + 23452e18 + 134235e18 + 1233463e18 + 45e18 + 4567e18 + 4564564e18 = 293880892517e18
    #     self.assertEqual(LL.token_x_subtree_borrow, UnsignedDecimal("293876300099e18"))    # 293874927834e18 + 134235e18 + 1233463e18 + 4567e18 = 293876300099e18
    #     self.assertEqual(LR.token_x_subtree_borrow, UnsignedDecimal("4588061e18"))         # 23452e18 + 45e18 + 4564564e18 = 4588061e18
    #     self.assertEqual(LLL.token_x_subtree_borrow, UnsignedDecimal("138802e18"))         # 134235e18 + 4567e18 = 138802e18
    #     self.assertEqual(LLR.token_x_subtree_borrow, UnsignedDecimal("1233463e18"))        # 1233463e18
    #     self.assertEqual(LRL.token_x_subtree_borrow, UnsignedDecimal("4564609e18"))        # 45e18 + 4564564e18 = 4564609e18
    #     self.assertEqual(LLLR.token_x_subtree_borrow, UnsignedDecimal("4567e18"))          # 4567e18
    #     self.assertEqual(LRLL.token_x_subtree_borrow, UnsignedDecimal("4564564e18"))       # 4564564e18
    #
    #     # borrow_y
    #     self.assertEqual(root.token_y_borrow, UnsignedDecimal("0"))
    #     self.assertEqual(L.token_y_borrow, UnsignedDecimal("345345345e6"))
    #     self.assertEqual(LL.token_y_borrow, UnsignedDecimal("2345346e6"))
    #     self.assertEqual(LR.token_y_borrow, UnsignedDecimal("12341235e6"))
    #     self.assertEqual(LLL.token_y_borrow, UnsignedDecimal("34534634e6"))
    #     self.assertEqual(LLR.token_y_borrow, UnsignedDecimal("2341356e6"))
    #     self.assertEqual(LRL.token_y_borrow, UnsignedDecimal("1324213563456457e6"))
    #     self.assertEqual(LLLR.token_y_borrow, UnsignedDecimal("1235146e6"))
    #     self.assertEqual(LRLL.token_y_borrow, UnsignedDecimal("6345135e6"))
    #
    #     # subtree_borrow_y
    #     self.assertEqual(root.token_y_subtree_borrow, UnsignedDecimal("1324213967944654e6"))  # 0 + 345345345e6 + 2345346e6 + 12341235e6 + 34534634e6 + 2341356e6 + 1324213563456457e6 + 1235146e6 + 6345135e6 = 1324213967944654e6
    #     self.assertEqual(L.token_y_subtree_borrow, UnsignedDecimal("1324213967944654e6"))     # 345345345e6 + 2345346e6 + 12341235e6 + 34534634e6 + 2341356e6 + 1324213563456457e6 + 1235146e6 + 6345135e6 = 1324213967944654e6
    #     self.assertEqual(LL.token_y_subtree_borrow, UnsignedDecimal("40456482e6"))            # 2345346e6 + 34534634e6 + 2341356e6 + 1235146e6 = 40456482e6
    #     self.assertEqual(LR.token_y_subtree_borrow, UnsignedDecimal("1324213582142827e6"))    # 12341235e6 + 1324213563456457e6 + 6345135e6 = 1324213582142827e6
    #     self.assertEqual(LLL.token_y_subtree_borrow, UnsignedDecimal("35769780e6"))           # 34534634e6 + 1235146e6 = 35769780e6
    #     self.assertEqual(LLR.token_y_subtree_borrow, UnsignedDecimal("2341356e6"))            # 2341356e6
    #     self.assertEqual(LRL.token_y_subtree_borrow, UnsignedDecimal("1324213569801592e6"))   # 1324213563456457e6 + 6345135e6 = 1324213569801592e6
    #     self.assertEqual(LLLR.token_y_subtree_borrow, UnsignedDecimal("1235146e6"))           # 1235146e6
    #     self.assertEqual(LRLL.token_y_subtree_borrow, UnsignedDecimal("6345135e6"))           # 6345135e6
    #
    #     # Test fees while targeting (1, 4)
    #     # 1) Trigger fee update through path L->LL->LLR by updating LLR
    #     liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("997278349210980290827452342352346")
    #     liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("7978726162930599238079167453467080976862")
    #
    #     liq_tree.add_m_liq(LiqRange(low=2, high=3), UnsignedDecimal("564011300817682367503451461"))     # LLR
    #     liq_tree.remove_m_liq(LiqRange(low=2, high=3), UnsignedDecimal("564011300817682367503451461"))  # LLR
    #
    #     # LLR
    #     #
    #     #   total_m_liq = 490692514491490 + (932141354 + 98237498262 + 432) * 2 = 490890853771586
    #     #
    #     #   earn_x      = 997278349210980290827452342352346 * 1233463e18 / 490890853771586 / 2**64 = 135843184601648135054031.953000417177564160084206701934727792
    #     #   earn_x_sub  = 997278349210980290827452342352346 * 1233463e18 / 490890853771586 / 2**64 = 135843184601648135054031.953000417177564160084206701934727792
    #     #
    #     #   earn_y      = 7978726162930599238079167453467080976862 * 2341356e6 / 490890853771586 / 2**64 = 2062986327173371860.88896572844074868101158495986576204342125
    #     #   earn_y_sub  = 7978726162930599238079167453467080976862 * 2341356e6 / 490890853771586 / 2**64 = 2062986327173371860.88896572844074868101158495986576204342125
    #     self.assertEqual(LLR.token_x_cumulative_earned_per_m_liq, UnsignedDecimal("135843184601648135054031"))
    #     self.assertEqual(LLR.token_x_cumulative_earned_per_m_subtree_liq, UnsignedDecimal("135843184601648135054031"))
    #     self.assertEqual(LLR.token_y_cumulative_earned_per_m_liq, UnsignedDecimal("2062986327173371860"))
    #     self.assertEqual(LLR.token_y_cumulative_earned_per_m_subtree_liq, UnsignedDecimal("2062986327173371860"))
    #
    #     # LL
    #     #
    #     #   total_m_liq = 582205610436080 + (98237498262 + 432) * 4 = 582598560430856
    #     #
    #     #   earn_x      = 997278349210980290827452342352346 * 293874927834e18 / 582598560430856 / 2**64 = 27270292518041237351900241102.9072917119646623397725295368780
    #     #   earn_x_sub  = 997278349210980290827452342352346 * 293876300099e18 / 582598560430856 / 2**64 = 27270419858159151079872803581.0095490519975481585750941907483
    #     #
    #     #   earn_y      = 7978726162930599238079167453467080976862 * 2345346e6 / 582598560430856 / 2**64 = 1741210798541653346.44401134728453048205241418030400364012179
    #     #   earn_y_sub  = 7978726162930599238079167453467080976862 * 40456482e6 / 582598560430856 / 2**64 = 30035339489101405447.4912908710324004754969276780541880790817
    #     self.assertEqual(LL.token_x_cumulative_earned_per_m_liq, UnsignedDecimal("27270292518041237351900241102"))
    #     self.assertEqual(LL.token_x_cumulative_earned_per_m_subtree_liq, UnsignedDecimal("27270419858159151079872803581"))
    #     self.assertEqual(LL.token_y_cumulative_earned_per_m_liq, UnsignedDecimal("1741210798541653346"))
    #     self.assertEqual(LL.token_y_cumulative_earned_per_m_subtree_liq, UnsignedDecimal("30035339489101405447"))
    #
    #     # L
    #     #
    #     #   total_m_liq = 583038259947765 + (432) * 8 = 583038259951221
    #     #
    #     #   earn_x      = 997278349210980290827452342352346 * 4357e18 / 583038259951221 / 2**64 = 404005403049228369014.124610642017839196445240663620779618212
    #     #   earn_x_sub  = 997278349210980290827452342352346 * 293880892517e18 / 583038259951221 / 2**64 = 27250279648794479314672290097.5284183991019310121509607727857
    #     #
    #     #   earn_y      = 7978726162930599238079167453467080976862 * 345345345e6 / 583038259951221 / 2**64 = 256194846273571639740.673516172246801895282064962841499611008
    #     #   earn_y_sub  = 7978726162930599238079167453467080976862 * 1324213967944654e6 / 583038259951221 / 2**64 = 982369673901053899051127131.509115296130579701967553185312315
    #     self.assertEqual(L.token_x_cumulative_earned_per_m_liq, UnsignedDecimal("404005403049228369014"))
    #     self.assertEqual(L.token_x_cumulative_earned_per_m_subtree_liq, UnsignedDecimal("27250279648794479314672290097"))
    #     self.assertEqual(L.token_y_cumulative_earned_per_m_liq, UnsignedDecimal("256194846273571639740"))
    #     self.assertEqual(L.token_y_cumulative_earned_per_m_subtree_liq, UnsignedDecimal("982369673901053899051127131"))
    #
    #     # 2) Trigger fee update through path L->LR->LRL->LRLL by updating LRLL
    #     liq_tree.add_m_liq(LiqRange(low=4, high=4), UnsignedDecimal("45656756785"))     # LRLL
    #     liq_tree.remove_m_liq(LiqRange(low=4, high=4), UnsignedDecimal("45656756785"))  # LRLL
    #
    #     # LRLL
    #     #   total_m_liq = 45656756785 + (243457472 + 151463465 + 98237498262 + 432) * 1 = 144289176416
    #     #
    #     #   earn_x      = 997278349210980290827452342352346 * 4564564e18 / 144289176416 / 2**64 = 1710260298962014449572659226.45857973175650767716107059096213
    #     #   earn_x_sub  = 997278349210980290827452342352346 * 4564564e18 / 144289176416 / 2**64 = 1710260298962014449572659226.45857973175650767716107059096213
    #     #
    #     #   earn_y      = 7978726162930599238079167453467080976862 * 6345135e6 / 144289176416 / 2**64 = 19020457094450723823822.1304935642458081127558849886746302550
    #     #   earn_y_sub  = 7978726162930599238079167453467080976862 * 6345135e6 / 144289176416 / 2**64 = 19020457094450723823822.1304935642458081127558849886746302550
    #     self.assertEqual(LRLL.token_x_cumulative_earned_per_m_liq, UnsignedDecimal("1710260298962014449572659226"))
    #     self.assertEqual(LRLL.token_x_cumulative_earned_per_m_subtree_liq, UnsignedDecimal("1710260298962014449572659226"))
    #     self.assertEqual(LRLL.token_y_cumulative_earned_per_m_liq, UnsignedDecimal("19020457094450723823822"))
    #     self.assertEqual(LRLL.token_y_cumulative_earned_per_m_subtree_liq, UnsignedDecimal("19020457094450723823822"))
    #
    #     # LRL
    #     #   total_m_liq = 46143671729 + (151463465 + 98237498262 + 432) * 2 = 242921596047
    #     #
    #     #   earn_x      = 997278349210980290827452342352346 * 45e18 / 242921596047 / 2**64 = 10014817880995372310152.4742715985679179265308809095477236672
    #     #   earn_x_sub  = 997278349210980290827452342352346 * 4564609e18 / 242921596047 / 2**64 = 1015860618510053453450506120.72016150011730453772839221611958
    #     #
    #     #   earn_y      = 7978726162930599238079167453467080976862 * 1324213563456457e6 / 242921596047 / 2**64 = 2357793377238426581071757403793.96341043019973158984354448841
    #     #   earn_y_sub  = 7978726162930599238079167453467080976862 * 1324213569801592e6 / 242921596047 / 2**64 = 2357793388536088599903418420664.92708711347544674139375617462
    #     self.assertEqual(LRL.token_x_cumulative_earned_per_m_liq, UnsignedDecimal("10014817880995372310152"))
    #     self.assertEqual(LRL.token_x_cumulative_earned_per_m_subtree_liq, UnsignedDecimal("1015860618510053453450506120"))
    #     self.assertEqual(LRL.token_y_cumulative_earned_per_m_liq, UnsignedDecimal("2357793377238426581071757403793"))
    #     self.assertEqual(LRL.token_y_cumulative_earned_per_m_subtree_liq, UnsignedDecimal("2357793388536088599903418420664"))
    #
    #     # LR
    #     #   total_m_liq = 46749525589 + (98237498262 + 432) * 4 = 439699520365
    #     #
    #     #   earn_x      = 997278349210980290827452342352346 * 23452e18 / 439699520365 / 2**64 = 2883504023897755903335799.02165969971328846599101621918354759
    #     #   earn_x_sub  = 997278349210980290827452342352346 * 4588061e18 / 439699520365 / 2**64 = 564117872905865676599639663.786245246727357690738865154506505
    #     #
    #     #   earn_y      = 7978726162930599238079167453467080976862 * 12341235e6 / 439699520365 / 2**64 = 12139937971620398360316.5575159331335181718549141795773004218
    #     #   earn_y_sub  = 7978726162930599238079167453467080976862 * 1324213582142827e6 / 439699520365 / 2**64 = 1302614426221619876588878010887.22237028229312127108609228047
    #     self.assertEqual(LR.token_x_cumulative_earned_per_m_liq, UnsignedDecimal("2883504023897755903335799"))
    #     self.assertEqual(LR.token_x_cumulative_earned_per_m_subtree_liq, UnsignedDecimal("564117872905865676599639663"))
    #     self.assertEqual(LR.token_y_cumulative_earned_per_m_liq, UnsignedDecimal("12139937971620398360316"))
    #     self.assertEqual(LR.token_y_cumulative_earned_per_m_subtree_liq, UnsignedDecimal("1302614426221619876588878010887"))
    #
    #     # L
    #     # Borrows have not changed. Results should be the same!
    #     self.assertEqual(L.token_x_cumulative_earned_per_m_liq, UnsignedDecimal("404005403049228369014"))
    #     self.assertEqual(L.token_x_cumulative_earned_per_m_subtree_liq, UnsignedDecimal("27250279648794479314672290097"))
    #     self.assertEqual(L.token_y_cumulative_earned_per_m_liq, UnsignedDecimal("256194846273571639740"))
    #     self.assertEqual(L.token_y_cumulative_earned_per_m_subtree_liq, UnsignedDecimal("982369673901053899051127131"))
    #
    #     # 3) Trigger fee update for remaining nodes by updating the range (1,3) LLLR, LLL
    #     #    For this last one, also update the rates to increment accumulated fees in L
    #     #    While previous step does not, meaning we also tested that nothing should have accumulated.
    #     #
    #     #    For un-accumulated nodes
    #     #    x_rate = 1299872175673458264503459867290698790836486158597987785659078908345634635 + 997278349210980290827452342352346 = 1299872175673458264503459867290698790837483436947198765949906360687986981
    #     #    y_rate = 2343465798346782378468923640892347692347899237846866000000345345346276876786 + 7978726162930599238079167453467080976862 = 2343465798346782378468923640892347700326625400777465238079512798813357853648
    #     liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("1299872175673458264503459867290698790836486158597987785659078908345634635")
    #     liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("2343465798346782378468923640892347692347899237846866000000345345346276876786")
    #
    #     liq_tree.add_t_liq(LiqRange(low=1, high=3), UnsignedDecimal("32"), UnsignedDecimal("8687384723"), UnsignedDecimal("56758698"))     # LLLR, LLL
    #     liq_tree.remove_t_liq(LiqRange(low=1, high=3), UnsignedDecimal("32"), UnsignedDecimal("8687384723"), UnsignedDecimal("56758698"))  # LLLR, LLL
    #
    #     # LLLR
    #     #   total_m_liq = 2462 + (45754683688356 + 932141354 + 98237498262 + 432) * 1 = 45853853330866
    #     #
    #     #   earn_x      = 1299872175673458264503459867290698790837483436947198765949906360687986981 * 4567e18 / 45853853330866 / 2**64 = 7018367402089271512449831285542283070529383839730059006659936.130773551243944000002576389036236651338347389250
    #     #   earn_x_sub  = 1299872175673458264503459867290698790837483436947198765949906360687986981 * 4567e18 / 45853853330866 / 2**64 = 7018367402089271512449831285542283070529383839730059006659936.130773551243944000002576389036236651338347389250
    #     #
    #     #   earn_y      = 2343465798346782378468923640892347700326625400777465238079512798813357853648 * 1235146e6 / 45853853330866 / 2**64 = 3422010642480475838452596727805190892411656925119587969.85330
    #     #   earn_y_sub  = 2343465798346782378468923640892347700326625400777465238079512798813357853648 * 1235146e6 / 45853853330866 / 2**64 = 3422010642480475838452596727805190892411656925119587969.85330
    #     self.assertEqual(LLLR.token_x_cumulative_earned_per_m_liq, UnsignedDecimal("7018367402089271512449831285542283070529383839730059006659936"))
    #     self.assertEqual(LLLR.token_x_cumulative_earned_per_m_subtree_liq, UnsignedDecimal("7018367402089271512449831285542283070529383839730059006659936"))
    #     self.assertEqual(LLLR.token_y_cumulative_earned_per_m_liq, UnsignedDecimal("3422010642480475838452596727805190892411656925119587969"))
    #     self.assertEqual(LLLR.token_y_cumulative_earned_per_m_subtree_liq, UnsignedDecimal("3422010642480475838452596727805190892411656925119587969"))
    #
    #     # LLL
    #     #   total_m_liq = 91509367379174 + (932141354 + 98237498262 + 432) * 2 = 91707706659270
    #     #
    #     #   earn_x      = 1299872175673458264503459867290698790837483436947198765949906360687986981 * 134235e18 / 91707706659270 / 2**64 = 103143261248603614450474086559218941021145887312254123476968651.5651280159520663266949783703392275566984071552
    #     #   earn_x_sub  = 1299872175673458264503459867290698790837483436947198765949906360687986981 * 138802e18 / 91707706659270 / 2**64 = 106652444949742458322752666313500260376333232396286339977280163.7020367182193817579462613160489102195765062015
    #     #
    #     #   earn_y      = 2343465798346782378468923640892347700326625400777465238079512798813357853648 * 34534634e6 / 91707706659270 / 2**64 = 47839642068767865474791702768817452956001093815727619460.5120
    #     #   earn_y_sub  = 2343465798346782378468923640892347700326625400777465238079512798813357853648 * 35769780e6 / 91707706659270 / 2**64 = 49550647390054037320994765830325323627188543696392945355.2695
    #     self.assertEqual(LLL.token_x_cumulative_earned_per_m_liq, UnsignedDecimal("103143261248603614450474086559218941021145887312254123476968651"))
    #     self.assertEqual(LLL.token_x_cumulative_earned_per_m_subtree_liq, UnsignedDecimal("106652444949742458322752666313500260376333232396286339977280163"))
    #     self.assertEqual(LLL.token_y_cumulative_earned_per_m_liq, UnsignedDecimal("47839642068767865474791702768817452956001093815727619460"))
    #     self.assertEqual(LLL.token_y_cumulative_earned_per_m_subtree_liq, UnsignedDecimal("49550647390054037320994765830325323627188543696392945355"))
    #
    #     # LL
    #     #   Note: LL previously accumulated fees, so we use the new rate as provided. Then add to the previously accumulated fees.
    #     #         The results SHOULD be the same as if the two rates were added, and accumulated once.
    #     #         However, that is not the case. Due to decimal truncation that happens over two transactions. See below.
    #     #
    #     #   total_m_liq = 582205610436080 + (98237498262 + 432) * 4 = 582598560430856
    #     #
    #     #   Expected in 1 transaction
    #     #   earn_x      = 1299872175673458264503459867290698790837483436947198765949906360687986981 * 293874927834e18 / 582598560430856 / 2**64 = 35544634549344534575302731950184064775098096623320842527740739153078.75082067380701457525147559485733770210963
    #     #   earn_x_sub  = 1299872175673458264503459867290698790837483436947198765949906360687986981 * 293876300099e18 / 582598560430856 / 2**64 = 35544800526953748684785622304061478291909912715982970794626727543515.67837110616273194884758309091127470639015
    #     #
    #     #   earn_y      = 2343465798346782378468923640892347700326625400777465238079512798813357853648 * 2345346e6 / 582598560430856 / 2**64 = 511418473421538198191409430001729877691494201326333679.0963768041829950138557552907316220422703628558848163908
    #     #   earn_y_sub  = 2343465798346782378468923640892347700326625400777465238079512798813357853648 * 40456482e6 / 582598560430856 / 2**64 = 8821808067741790988384310101577867302175515556793408995.669016189358355860561774047790233928773909697150300378
    #     #
    #     #   Expected in 2 transactions
    #     #   earn_x      = 1299872175673458264503459867290698790836486158597987785659078908345634635 * 293874927834e18 / 582598560430856 / 2**64 = 35544634549344534575302731950184064775070826330802801290388838911975.84352896184235223547894605797930653522893
    #     #   earn_x_sub  = 1299872175673458264503459867290698790836486158597987785659078908345634635 * 293876300099e18 / 582598560430856 / 2**64 = 35544800526953748684785622304061478291882642296124811643546854739934.66882205416518379027248890016297306691608
    #     #
    #     #   earn_y      = 2343465798346782378468923640892347692347899237846866000000345345346276876786 * 2345346e6 / 582598560430856 / 2**64 = 511418473421538198191409430001729875950283402784680332.652365
    #     #   earn_y_sub  = 2343465798346782378468923640892347692347899237846866000000345345346276876786 * 40456482e6 / 582598560430856 / 2**64 = 8821808067741790988384310101577867272140176067692003548.17772
    #     #
    #     #   acc_x       = 35544634549344534575302731950184064775070826330802801290388838911975 + 27270292518041237351900241102 = 35544634549344534575302731950184064775098096623320842527740739153077
    #     #   acc_x_sub   = 35544800526953748684785622304061478291882642296124811643546854739934 + 27270419858159151079872803581 = 35544800526953748684785622304061478291909912715982970794626727543515
    #     #
    #     #   acc_y       = 511418473421538198191409430001729875950283402784680332 + 1741210798541653346 = 511418473421538198191409430001729877691494201326333678
    #     #   acc_y_sub   = 8821808067741790988384310101577867272140176067692003548 + 30035339489101405447 = 8821808067741790988384310101577867302175515556793408995
    #     self.assertEqual(LL.token_x_cumulative_earned_per_m_liq, UnsignedDecimal("35544634549344534575302731950184064775098096623320842527740739153077"))          # 1 wei lost
    #     self.assertEqual(LL.token_x_cumulative_earned_per_m_subtree_liq, UnsignedDecimal("35544800526953748684785622304061478291909912715982970794626727543515"))
    #     self.assertEqual(LL.token_y_cumulative_earned_per_m_liq, UnsignedDecimal("511418473421538198191409430001729877691494201326333678"))                        # 1 wei lost
    #     self.assertEqual(LL.token_y_cumulative_earned_per_m_subtree_liq, UnsignedDecimal("8821808067741790988384310101577867302175515556793408995"))
    #
    #     # L
    #     #   Note: (same situation as LL above)
    #     #
    #     #   total_m_liq = 583038259947765 + (432) * 8 = 583038259951221
    #     #
    #     #   Expected in 1 transaction
    #     #   earn_x      = 1299872175673458264503459867290698790837483436947198765949906360687986981 * 4357e18 / 583038259951221 / 2**64 = 526588572449127820710280925096499286631826368408350578683678.8949320786875222752967719865098507132989325023672
    #     #   earn_x_sub  = 1299872175673458264503459867290698790837483436947198765949906360687986981 * 293880892517e18 / 583038259951221 / 2**64 = 35518549382741014580801587134532851665736731679050016244983472266163.77158207946190817820623319059828307670852
    #     #
    #     #   earn_y      = 2343465798346782378468923640892347700326625400777465238079512798813357853648 * 345345345e6 / 583038259951221 / 2**64 = 75248084430347809841211701855286934435441672114601405440.36959084052843872095985545406590238625971175786589905
    #     #   earn_y_sub  = 2343465798346782378468923640892347700326625400777465238079512798813357853648 * 1324213967944654e6 / 583038259951221 / 2**64 = 288535999996598223755002019090052510701800094598545473522203908.3456298612650105591841256935791299290626023275
    #     self.assertEqual(L.token_x_cumulative_earned_per_m_liq, UnsignedDecimal("526588572449127820710280925096499286631826368408350578683678"))
    #     self.assertEqual(L.token_x_cumulative_earned_per_m_subtree_liq, UnsignedDecimal("35518549382741014580801587134532851665736731679050016244983472266163"))
    #     self.assertEqual(L.token_y_cumulative_earned_per_m_liq, UnsignedDecimal("75248084430347809841211701855286934435441672114601405439"))                 # 1 wei lost
    #     self.assertEqual(L.token_y_cumulative_earned_per_m_subtree_liq, UnsignedDecimal("288535999996598223755002019090052510701800094598545473522203907"))  # 1 wei lost
    #
    #     # 4) Confirm root fees are correct (although behavior leading to this state should have been previously tested at L and LL
    #     #   total_m_liq = 583038259954677
    #     #
    #     #   earn_x      = 1299872175673458264503459867290698790837483436947198765949906360687986981 * 0 / 583038259954677 / 2**64 = 0
    #     #   earn_x_sub  = 1299872175673458264503459867290698790837483436947198765949906360687986981 * 293880892517e18 / 583038259954677 / 2**64 = 35518549382530475899041156539352565759624323835558718083224151423775.00522789294925623241122948225991829258658
    #     #
    #     #   earn_y      = 2343465798346782378468923640892347700326625400777465238079512798813357853648 * 0 / 583038259954677 / 2**64 = 0
    #     #   earn_y_sub  = 2343465798346782378468923640892347700326625400777465238079512798813357853648 * 1324213967944654e6 / 583038259954677 / 2**64 = 288535999994887906466277673329665978776994301813328609583743065.1742475963990666755167810305856663430573507628
    #     self.assertEqual(root.token_x_cumulative_earned_per_m_liq, UnsignedDecimal("0"))
    #     self.assertEqual(root.token_x_cumulative_earned_per_m_subtree_liq, UnsignedDecimal("35518549382530475899041156539352565759624323835558718083224151423774"))  # 1 wei lost
    #     self.assertEqual(root.token_y_cumulative_earned_per_m_liq, UnsignedDecimal("0"))
    #     self.assertEqual(root.token_y_cumulative_earned_per_m_subtree_liq, UnsignedDecimal("288535999994887906466277673329665978776994301813328609583743064"))       # 1 wei lost

    def test_left_and_right_leg_stopping_at_or_above_peak(self):
        #   Range: (0, 1)
        #
        #           LLL(0-1)
        #          /   \
        #         /     \
        #   LLLL(0) LLLR(1)

        liq_tree = self.liq_tree

        # 4th (0, 1)
        root: LiqNode = liq_tree.nodes[liq_tree.root_key]
        L: LiqNode = liq_tree.nodes[(8 << 24) | 16]
        LL: LiqNode = liq_tree.nodes[(4 << 24) | 16]
        LLL: LiqNode = liq_tree.nodes[(2 << 24) | 16]
        LLLL: LiqNode = liq_tree.nodes[(1 << 24) | 16]
        LLLR: LiqNode = liq_tree.nodes[(1 << 24) | 17]

        liq_tree.add_m_liq(LiqRange(low=0, high=1), UnsignedDecimal("8264"))  # LLL
        liq_tree.add_m_liq(LiqRange(low=0, high=0), UnsignedDecimal("2582"))  # LLLL
        liq_tree.add_m_liq(LiqRange(low=1, high=1), UnsignedDecimal("1111"))  # LLLR

        liq_tree.add_t_liq(LiqRange(low=0, high=1), UnsignedDecimal("726"), UnsignedDecimal("346e18"), UnsignedDecimal("132e6"))  # LLL
        liq_tree.add_t_liq(LiqRange(low=0, high=0), UnsignedDecimal("245"), UnsignedDecimal("100e18"), UnsignedDecimal("222e6"))  # LLLL
        liq_tree.add_t_liq(LiqRange(low=1, high=1), UnsignedDecimal("342"), UnsignedDecimal("234e18"), UnsignedDecimal("313e6"))  # LLLR

        # Verify initial tree state
        # m_liq
        self.assertEqual(root.m_liq, UnsignedDecimal("0"))
        self.assertEqual(L.m_liq, UnsignedDecimal("0"))
        self.assertEqual(LL.m_liq, UnsignedDecimal("0"))
        self.assertEqual(LLL.m_liq, UnsignedDecimal("8264"))
        self.assertEqual(LLLL.m_liq, UnsignedDecimal("2582"))
        self.assertEqual(LLLR.m_liq, UnsignedDecimal("1111"))

        # t_liq
        self.assertEqual(root.t_liq, UnsignedDecimal("0"))
        self.assertEqual(L.t_liq, UnsignedDecimal("0"))
        self.assertEqual(LL.t_liq, UnsignedDecimal("0"))
        self.assertEqual(LLL.t_liq, UnsignedDecimal("726"))
        self.assertEqual(LLLL.t_liq, UnsignedDecimal("245"))
        self.assertEqual(LLLR.t_liq, UnsignedDecimal("342"))

        # subtree_m_liq
        self.assertEqual(root.subtree_m_liq, UnsignedDecimal("20221"))
        self.assertEqual(L.subtree_m_liq, UnsignedDecimal("20221"))
        self.assertEqual(LL.subtree_m_liq, UnsignedDecimal("20221"))
        self.assertEqual(LLL.subtree_m_liq, UnsignedDecimal("20221"))  # 8264*2 + 2582*1 + 1111*1 = 20221
        self.assertEqual(LLLL.subtree_m_liq, UnsignedDecimal("2582"))
        self.assertEqual(LLLR.subtree_m_liq, UnsignedDecimal("1111"))

        # borrow_x
        self.assertEqual(root.token_x_borrow, UnsignedDecimal("0"))
        self.assertEqual(L.token_x_borrow, UnsignedDecimal("0"))
        self.assertEqual(LL.token_x_borrow, UnsignedDecimal("0"))
        self.assertEqual(LLL.token_x_borrow, UnsignedDecimal("346e18"))
        self.assertEqual(LLLL.token_x_borrow, UnsignedDecimal("100e18"))
        self.assertEqual(LLLR.token_x_borrow, UnsignedDecimal("234e18"))

        # subtree_borrow_x
        self.assertEqual(root.token_x_subtree_borrow, UnsignedDecimal("680e18"))
        self.assertEqual(L.token_x_subtree_borrow, UnsignedDecimal("680e18"))
        self.assertEqual(LL.token_x_subtree_borrow, UnsignedDecimal("680e18"))
        self.assertEqual(LLL.token_x_subtree_borrow, UnsignedDecimal("680e18"))  # 346e18 + 100e18 + 234e18 = 680e18
        self.assertEqual(LLLL.token_x_subtree_borrow, UnsignedDecimal("100e18"))
        self.assertEqual(LLLR.token_x_subtree_borrow, UnsignedDecimal("234e18"))

        # borrow_y
        self.assertEqual(root.token_y_borrow, UnsignedDecimal("0"))
        self.assertEqual(L.token_y_borrow, UnsignedDecimal("0"))
        self.assertEqual(LL.token_y_borrow, UnsignedDecimal("0"))
        self.assertEqual(LLL.token_y_borrow, UnsignedDecimal("132e6"))
        self.assertEqual(LLLL.token_y_borrow, UnsignedDecimal("222e6"))
        self.assertEqual(LLLR.token_y_borrow, UnsignedDecimal("313e6"))

        # subtree_borrow_y
        self.assertEqual(root.token_y_subtree_borrow, UnsignedDecimal("667e6"))
        self.assertEqual(L.token_y_subtree_borrow, UnsignedDecimal("667e6"))
        self.assertEqual(LL.token_y_subtree_borrow, UnsignedDecimal("667e6"))
        self.assertEqual(LLL.token_y_subtree_borrow, UnsignedDecimal("667e6"))  # 132e6 + 222e6 + 313e6 = 667e6
        self.assertEqual(LLLL.token_y_subtree_borrow, UnsignedDecimal("222e6"))
        self.assertEqual(LLLR.token_y_subtree_borrow, UnsignedDecimal("313e6"))

        liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("997278349210980290827452342352346")
        liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("7978726162930599238079167453467080976862")

        liq_tree.add_m_liq(LiqRange(low=0, high=1), UnsignedDecimal("1234567"))
        liq_tree.remove_m_liq(LiqRange(low=0, high=1), UnsignedDecimal("1234567"))

        # LLLR
        # (not updated)
        self.assertEqual(LLLR.token_x_cumulative_earned_per_m_liq, UnsignedDecimal("0"))
        self.assertEqual(LLLR.token_x_cumulative_earned_per_m_subtree_liq, UnsignedDecimal("0"))
        self.assertEqual(LLLR.token_y_cumulative_earned_per_m_liq, UnsignedDecimal("0"))
        self.assertEqual(LLLR.token_y_cumulative_earned_per_m_subtree_liq, UnsignedDecimal("0"))

        # LLLL
        # (not updated)
        self.assertEqual(LLLL.token_x_cumulative_earned_per_m_liq, UnsignedDecimal("0"))
        self.assertEqual(LLLL.token_x_cumulative_earned_per_m_subtree_liq, UnsignedDecimal("0"))
        self.assertEqual(LLLL.token_y_cumulative_earned_per_m_liq, UnsignedDecimal("0"))
        self.assertEqual(LLLL.token_y_cumulative_earned_per_m_subtree_liq, UnsignedDecimal("0"))

        # LLL
        #
        #   total_m_liq = 20221 + (0 + 0 + 0) * 2 = 20221
        #
        #   earn_x      = 997278349210980290827452342352346 * 346e18 / 20221 / 2**64 = 925060501618136152524292214349.283139885351240161578507230288
        #   earn_x_sub  = 997278349210980290827452342352346 * 680e18 / 20221 / 2**64 = 1818037980058764692822308398143.09981249144174367015429166646
        #
        #   earn_y      = 7978726162930599238079167453467080976862 * 132e6 / 20221 / 2**64 = 2823482754602022855424507.24027059608531549133804868998511635
        #   earn_y_sub  = 7978726162930599238079167453467080976862 * 667e6 / 20221 / 2**64 = 14267143919087494277031411.5853067241583744903218066380308530
        self.assertEqual(LLL.token_x_cumulative_earned_per_m_liq, UnsignedDecimal("925060501618136152524292214349"))
        self.assertEqual(LLL.token_x_cumulative_earned_per_m_subtree_liq, UnsignedDecimal("1818037980058764692822308398143"))
        self.assertEqual(LLL.token_y_cumulative_earned_per_m_liq, UnsignedDecimal("2823482754602022855424507"))
        self.assertEqual(LLL.token_y_cumulative_earned_per_m_subtree_liq, UnsignedDecimal("14267143919087494277031411"))

        # LL
        #   NOTE: subtree earn is not 'diluted' because liq contributing to total_m_liq along the path to the root is 0.
        #
        #   total_m_liq = 20221 + (0 + 0) * 4 = 20221
        #
        #   earn_x      = 997278349210980290827452342352346 * 0 / 20221 / 2**64 = 0
        #   earn_x_sub  = 997278349210980290827452342352346 * 680e18 / 20221 / 2**64 = 1818037980058764692822308398143.09981249144174367015429166646
        #
        #   earn_y      = 7978726162930599238079167453467080976862 * 0 / 20221 / 2**64 = 0
        #   earn_y_sub  = 7978726162930599238079167453467080976862 * 667e6 / 20221 / 2**64 = 14267143919087494277031411.5853067241583744903218066380308530
        self.assertEqual(LL.token_x_cumulative_earned_per_m_liq, UnsignedDecimal("0"))
        self.assertEqual(LL.token_x_cumulative_earned_per_m_subtree_liq, UnsignedDecimal("1818037980058764692822308398143"))
        self.assertEqual(LL.token_y_cumulative_earned_per_m_liq, UnsignedDecimal("0"))
        self.assertEqual(LL.token_y_cumulative_earned_per_m_subtree_liq, UnsignedDecimal("14267143919087494277031411"))

        # L
        #   NOTE: subtree earn is not 'diluted' because liq contributing to total_m_liq along the path to the root is 0.
        self.assertEqual(L.token_x_cumulative_earned_per_m_liq, UnsignedDecimal("0"))
        self.assertEqual(L.token_x_cumulative_earned_per_m_subtree_liq, UnsignedDecimal("1818037980058764692822308398143"))
        self.assertEqual(L.token_y_cumulative_earned_per_m_liq, UnsignedDecimal("0"))
        self.assertEqual(L.token_y_cumulative_earned_per_m_subtree_liq, UnsignedDecimal("14267143919087494277031411"))

        # root
        #   NOTE: subtree earn is not 'diluted' because liq contributing to total_m_liq along the path to the root is 0.
        self.assertEqual(root.token_x_cumulative_earned_per_m_liq, UnsignedDecimal("0"))
        self.assertEqual(root.token_x_cumulative_earned_per_m_subtree_liq, UnsignedDecimal("1818037980058764692822308398143"))
        self.assertEqual(root.token_y_cumulative_earned_per_m_liq, UnsignedDecimal("0"))
        self.assertEqual(root.token_y_cumulative_earned_per_m_subtree_liq, UnsignedDecimal("14267143919087494277031411"))

        # Verify ending tree state
        # Will be the same as initial state, because any changes to the tree (minus fees) were undone
        # m_liq
        self.assertEqual(root.m_liq, UnsignedDecimal("0"))
        self.assertEqual(L.m_liq, UnsignedDecimal("0"))
        self.assertEqual(LL.m_liq, UnsignedDecimal("0"))
        self.assertEqual(LLL.m_liq, UnsignedDecimal("8264"))
        self.assertEqual(LLLL.m_liq, UnsignedDecimal("2582"))
        self.assertEqual(LLLR.m_liq, UnsignedDecimal("1111"))

        # t_liq
        self.assertEqual(root.t_liq, UnsignedDecimal("0"))
        self.assertEqual(L.t_liq, UnsignedDecimal("0"))
        self.assertEqual(LL.t_liq, UnsignedDecimal("0"))
        self.assertEqual(LLL.t_liq, UnsignedDecimal("726"))
        self.assertEqual(LLLL.t_liq, UnsignedDecimal("245"))
        self.assertEqual(LLLR.t_liq, UnsignedDecimal("342"))

        # subtree_m_liq
        self.assertEqual(root.subtree_m_liq, UnsignedDecimal("20221"))
        self.assertEqual(L.subtree_m_liq, UnsignedDecimal("20221"))
        self.assertEqual(LL.subtree_m_liq, UnsignedDecimal("20221"))
        self.assertEqual(LLL.subtree_m_liq, UnsignedDecimal("20221"))
        self.assertEqual(LLLL.subtree_m_liq, UnsignedDecimal("2582"))
        self.assertEqual(LLLR.subtree_m_liq, UnsignedDecimal("1111"))

        # borrow_x
        self.assertEqual(root.token_x_borrow, UnsignedDecimal("0"))
        self.assertEqual(L.token_x_borrow, UnsignedDecimal("0"))
        self.assertEqual(LL.token_x_borrow, UnsignedDecimal("0"))
        self.assertEqual(LLL.token_x_borrow, UnsignedDecimal("346e18"))
        self.assertEqual(LLLL.token_x_borrow, UnsignedDecimal("100e18"))
        self.assertEqual(LLLR.token_x_borrow, UnsignedDecimal("234e18"))

        # subtree_borrow_x
        self.assertEqual(root.token_x_subtree_borrow, UnsignedDecimal("680e18"))
        self.assertEqual(L.token_x_subtree_borrow, UnsignedDecimal("680e18"))
        self.assertEqual(LL.token_x_subtree_borrow, UnsignedDecimal("680e18"))
        self.assertEqual(LLL.token_x_subtree_borrow, UnsignedDecimal("680e18"))
        self.assertEqual(LLLL.token_x_subtree_borrow, UnsignedDecimal("100e18"))
        self.assertEqual(LLLR.token_x_subtree_borrow, UnsignedDecimal("234e18"))

        # borrow_y
        self.assertEqual(root.token_y_borrow, UnsignedDecimal("0"))
        self.assertEqual(L.token_y_borrow, UnsignedDecimal("0"))
        self.assertEqual(LL.token_y_borrow, UnsignedDecimal("0"))
        self.assertEqual(LLL.token_y_borrow, UnsignedDecimal("132e6"))
        self.assertEqual(LLLL.token_y_borrow, UnsignedDecimal("222e6"))
        self.assertEqual(LLLR.token_y_borrow, UnsignedDecimal("313e6"))

        # subtree_borrow_y
        self.assertEqual(root.token_y_subtree_borrow, UnsignedDecimal("667e6"))
        self.assertEqual(L.token_y_subtree_borrow, UnsignedDecimal("667e6"))
        self.assertEqual(LL.token_y_subtree_borrow, UnsignedDecimal("667e6"))
        self.assertEqual(LLL.token_y_subtree_borrow, UnsignedDecimal("667e6"))
        self.assertEqual(LLLL.token_y_subtree_borrow, UnsignedDecimal("222e6"))
        self.assertEqual(LLLR.token_y_subtree_borrow, UnsignedDecimal("313e6"))

    def test_complete_tree(self):
        '''
        We've done enough testing to capture all enumerated cases of tree structure, etc.
        Now we trust python to yield correct results. And compare these directly to solidity. They should match.

        In this test, we first add m_liq and t_liq to each node individually. Then we apply the four methods:
            add_m_liq, remove_m_liq, add_t_liq, remove_t_liq, (add_Wide_m_liq, remove_Wide_m_liq, add_Wide_t_liq, remove_Wide_t_liq)
        while accumulating fees.

        Entered values for liq, and borrow have no significance here, except for being different from one another.
        We will cover all possible ranges.
            ex. (0, 0), (0, 1), (0, 2), ... etc.
        '''

        liq_tree: LiquidityTree = self.liq_tree

        root: LiqNode = liq_tree.nodes[liq_tree.root_key]

        L: LiqNode = liq_tree.nodes[(8 << 24) | 16]
        R: LiqNode = liq_tree.nodes[(8 << 24) | 24]

        LL: LiqNode = liq_tree.nodes[(4 << 24) | 16]
        LR: LiqNode = liq_tree.nodes[(4 << 24) | 20]
        RL: LiqNode = liq_tree.nodes[(4 << 24) | 24]
        RR: LiqNode = liq_tree.nodes[(4 << 24) | 28]

        LLL: LiqNode = liq_tree.nodes[(2 << 24) | 16]
        LLR: LiqNode = liq_tree.nodes[(2 << 24) | 18]
        LRL: LiqNode = liq_tree.nodes[(2 << 24) | 20]
        LRR: LiqNode = liq_tree.nodes[(2 << 24) | 22]
        RLL: LiqNode = liq_tree.nodes[(2 << 24) | 24]
        RLR: LiqNode = liq_tree.nodes[(2 << 24) | 26]
        RRL: LiqNode = liq_tree.nodes[(2 << 24) | 28]
        RRR: LiqNode = liq_tree.nodes[(2 << 24) | 30]

        LLLL: LiqNode = liq_tree.nodes[(1 << 24) | 16]
        LLLR: LiqNode = liq_tree.nodes[(1 << 24) | 17]
        LLRL: LiqNode = liq_tree.nodes[(1 << 24) | 18]
        LLRR: LiqNode = liq_tree.nodes[(1 << 24) | 19]
        LRLL: LiqNode = liq_tree.nodes[(1 << 24) | 20]
        LRLR: LiqNode = liq_tree.nodes[(1 << 24) | 21]
        LRRL: LiqNode = liq_tree.nodes[(1 << 24) | 22]
        LRRR: LiqNode = liq_tree.nodes[(1 << 24) | 23]
        RLLL: LiqNode = liq_tree.nodes[(1 << 24) | 24]
        RLLR: LiqNode = liq_tree.nodes[(1 << 24) | 25]
        RLRL: LiqNode = liq_tree.nodes[(1 << 24) | 26]
        RLRR: LiqNode = liq_tree.nodes[(1 << 24) | 27]
        RRLL: LiqNode = liq_tree.nodes[(1 << 24) | 28]
        RRLR: LiqNode = liq_tree.nodes[(1 << 24) | 29]
        RRRL: LiqNode = liq_tree.nodes[(1 << 24) | 30]
        RRRR: LiqNode = liq_tree.nodes[(1 << 24) | 31]

        # Start with an accumulated rate for each token before modifying tree state -----------------------------------------
        liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("34541239648278065")
        liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("713278814667749784")

        # Add m_liq + t_liq to all nodes ------------------------------------------------------------------------------------
        liq_tree.add_wide_m_liq(UnsignedDecimal("837205720"))  # root
        liq_tree.add_wide_t_liq(UnsignedDecimal("137205720"), UnsignedDecimal("92749012637e18"), UnsignedDecimal("936252847e6"))

        liq_tree.add_m_liq(LiqRange(0, 7), UnsignedDecimal("628294582176"))  # L
        liq_tree.add_t_liq(LiqRange(0, 7), UnsignedDecimal("28294582176"), UnsignedDecimal("41423892459e18"), UnsignedDecimal("178263465237e6"))
        liq_tree.add_m_liq(LiqRange(8, 15), UnsignedDecimal("9846145183924"))  # R
        liq_tree.add_t_liq(LiqRange(8, 15), UnsignedDecimal("846145183924"), UnsignedDecimal("2983456295e18"), UnsignedDecimal("297562903e6"))

        liq_tree.add_m_liq(LiqRange(0, 3), UnsignedDecimal("1325348245562823"))  # LL
        liq_tree.add_t_liq(LiqRange(0, 3), UnsignedDecimal("325348245562823"), UnsignedDecimal("28678729387565786e18"), UnsignedDecimal("1287576451867e6"))
        liq_tree.add_m_liq(LiqRange(4, 7), UnsignedDecimal("3456457562345467878"))  # LR
        liq_tree.add_t_liq(LiqRange(4, 7), UnsignedDecimal("456457562345467878"), UnsignedDecimal("872538467082357693e18"), UnsignedDecimal("9879867896e6"))
        liq_tree.add_m_liq(LiqRange(8, 11), UnsignedDecimal("76483482619394619652"))  # RL
        liq_tree.add_t_liq(LiqRange(8, 11), UnsignedDecimal("6483482619394619652"), UnsignedDecimal("6785678523564273e18"), UnsignedDecimal("978623685429837e6"))
        liq_tree.add_m_liq(LiqRange(12, 15), UnsignedDecimal("8623526734267390879"))  # RR
        liq_tree.add_t_liq(LiqRange(12, 15), UnsignedDecimal("86235267342673908"), UnsignedDecimal("498723597863764293e18"), UnsignedDecimal("7856675879087e6"))

        liq_tree.add_m_liq(LiqRange(0, 1), UnsignedDecimal("98987279836478238567234"))  # LLL
        liq_tree.add_t_liq(LiqRange(0, 1), UnsignedDecimal("8987279836478238567234"), UnsignedDecimal("45623798462985629837462e18"), UnsignedDecimal("8725348762398423567587e6"))
        liq_tree.add_m_liq(LiqRange(2, 3), UnsignedDecimal("7986785755674657823"))  # LLR
        liq_tree.add_t_liq(LiqRange(2, 3), UnsignedDecimal("986785755674657823"), UnsignedDecimal("298364785638476530459368e18"), UnsignedDecimal("3465873645937459364e6"))
        liq_tree.add_m_liq(LiqRange(4, 5), UnsignedDecimal("232467458683765"))  # LRL
        liq_tree.add_t_liq(LiqRange(4, 5), UnsignedDecimal("132467458683765"), UnsignedDecimal("27364762534827634902374982e18"), UnsignedDecimal("56736409827398427340e6"))
        liq_tree.add_m_liq(LiqRange(6, 7), UnsignedDecimal("777839863652735"))  # LRR
        liq_tree.add_t_liq(LiqRange(6, 7), UnsignedDecimal("277839863652735"), UnsignedDecimal("7653642903472903784290347e18"), UnsignedDecimal("7834626734902734902368e6"))
        liq_tree.add_m_liq(LiqRange(8, 9), UnsignedDecimal("3131567868944634354"))  # RLL
        liq_tree.add_t_liq(LiqRange(8, 9), UnsignedDecimal("2131567868944634354"), UnsignedDecimal("23452367423084927398437e18"), UnsignedDecimal("9834787362478562378e6"))
        liq_tree.add_m_liq(LiqRange(10, 11), UnsignedDecimal("78724563469237853906739487"))  # RLR
        liq_tree.add_t_liq(LiqRange(10, 11), UnsignedDecimal("8724563469237853906739487"), UnsignedDecimal("2765723642783492e18"), UnsignedDecimal("98576798364725367423e6"))
        liq_tree.add_m_liq(LiqRange(12, 13), UnsignedDecimal("7556478634723908752323756"))  # RRL
        liq_tree.add_t_liq(LiqRange(12, 13), UnsignedDecimal("5556478634723908752323756"), UnsignedDecimal("28635482364798629384e18"),
                           UnsignedDecimal("83764587364859348795634987e6"))
        liq_tree.add_m_liq(LiqRange(14, 15), UnsignedDecimal("54534789284573456239862722"))  # RRR
        liq_tree.add_t_liq(LiqRange(14, 15), UnsignedDecimal("34534789284573456239862722"), UnsignedDecimal("27364527863428346239867e18"),
                           UnsignedDecimal("9834657827356482367482369e6"))

        liq_tree.add_m_liq(LiqRange(0, 0), UnsignedDecimal("92736478234923748923"))  # LLLL
        liq_tree.add_t_liq(LiqRange(0, 0), UnsignedDecimal("9736478234923748923"), UnsignedDecimal("5734523421634563e18"), UnsignedDecimal("72634678523487263e6"))
        liq_tree.add_m_liq(LiqRange(1, 1), UnsignedDecimal("76238216349082735923684"))  # LLLR
        liq_tree.add_t_liq(LiqRange(1, 1), UnsignedDecimal("7623821634908273592368"), UnsignedDecimal("346456345234235235e18"), UnsignedDecimal("26734872634892639847623789e6"))
        liq_tree.add_m_liq(LiqRange(2, 2), UnsignedDecimal("2345345345353"))  # LLRL
        liq_tree.add_t_liq(LiqRange(2, 2), UnsignedDecimal("234534534535"), UnsignedDecimal("82735476982534798263498e18"), UnsignedDecimal("763467253674523798462397e6"))
        liq_tree.add_m_liq(LiqRange(3, 3), UnsignedDecimal("12341234213421354513456"))  # LLRR
        liq_tree.add_t_liq(LiqRange(3, 3), UnsignedDecimal("1234123421342135451345"), UnsignedDecimal("2367452364752903485729403875e18"), UnsignedDecimal("987349053045739487e6"))
        liq_tree.add_m_liq(LiqRange(4, 4), UnsignedDecimal("456467567878689"))  # LRLL
        liq_tree.add_t_liq(LiqRange(4, 4), UnsignedDecimal("45646756787868"), UnsignedDecimal("236452378462398476238746e18"), UnsignedDecimal("984764582736478236478e6"))
        liq_tree.add_m_liq(LiqRange(5, 5), UnsignedDecimal("89805856756746"))  # LRLR
        liq_tree.add_t_liq(LiqRange(5, 5), UnsignedDecimal("8980585675674"), UnsignedDecimal("8374278364628364e18"), UnsignedDecimal("8763867548273647826e6"))
        liq_tree.add_m_liq(LiqRange(6, 6), UnsignedDecimal("34545756857245324534634"))  # LRRL
        liq_tree.add_t_liq(LiqRange(6, 6), UnsignedDecimal("3454575685724532453463"), UnsignedDecimal("3456457456345634e18"), UnsignedDecimal("8726347825634876237846e6"))
        liq_tree.add_m_liq(LiqRange(7, 7), UnsignedDecimal("2334646757867856856346"))  # LRRR
        liq_tree.add_t_liq(LiqRange(7, 7), UnsignedDecimal("233464675786785685634"), UnsignedDecimal("236542867349237498e18"), UnsignedDecimal("798647852364627983e6"))
        liq_tree.add_m_liq(LiqRange(8, 8), UnsignedDecimal("24674758679564563445747"))  # RLLL
        liq_tree.add_t_liq(LiqRange(8, 8), UnsignedDecimal("2467475867956456344574"), UnsignedDecimal("51427634238746298457982345e18"), UnsignedDecimal("74986238476283746e6"))
        liq_tree.add_m_liq(LiqRange(9, 9), UnsignedDecimal("547867967467456457536856873"))  # RLLR
        liq_tree.add_t_liq(LiqRange(9, 9), UnsignedDecimal("54786796746745645753685687"), UnsignedDecimal("634529836428376523e18"), UnsignedDecimal("868746576834678534e6"))
        liq_tree.add_m_liq(LiqRange(10, 10), UnsignedDecimal("34564375645457568568456"))  # RLRL
        liq_tree.add_t_liq(LiqRange(10, 10), UnsignedDecimal("3456437564545756856845"), UnsignedDecimal("1212312312423452454e18"), UnsignedDecimal("3423423648236487e6"))
        liq_tree.add_m_liq(LiqRange(11, 11), UnsignedDecimal("32546475786796896785674564"))  # RLRR
        liq_tree.add_t_liq(LiqRange(11, 11), UnsignedDecimal("3254647578679689678567456"), UnsignedDecimal("287346234623487923642786e18"),
                           UnsignedDecimal("827364826734823748963e6"))
        liq_tree.add_m_liq(LiqRange(12, 12), UnsignedDecimal("5856745645634534563453"))  # RRLL
        liq_tree.add_t_liq(LiqRange(12, 12), UnsignedDecimal("585674564563453456345"), UnsignedDecimal("2837427354234786237896e18"), UnsignedDecimal("73649082374029384628376e6"))
        liq_tree.add_m_liq(LiqRange(13, 13), UnsignedDecimal("4574785673643563456"))  # RRLR
        liq_tree.add_t_liq(LiqRange(13, 13), UnsignedDecimal("457478567364356345"), UnsignedDecimal("82635472634823674e18"), UnsignedDecimal("2387642836423689768e6"))
        liq_tree.add_m_liq(LiqRange(14, 14), UnsignedDecimal("24534645747456745"))  # RRRL
        liq_tree.add_t_liq(LiqRange(14, 14), UnsignedDecimal("2453464574745674"), UnsignedDecimal("23645278462837429736e18"), UnsignedDecimal("3542364237842638e6"))
        liq_tree.add_m_liq(LiqRange(15, 15), UnsignedDecimal("6345346534645746"))  # RRRR
        liq_tree.add_t_liq(LiqRange(15, 15), UnsignedDecimal("6345346534645743"), UnsignedDecimal("37465276342938487e18"), UnsignedDecimal("23984623847623867e6"))

        # Interact with the tree. Using all methods. Over all possible ranges
        # Ranges that start with 0 -------------------------------------------------------------------------------------

        # LiqRange(0, 0)
        liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("283564826358762378954279863")
        liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("2753476253583645873647859364")
        liq_tree.add_m_liq(LiqRange(0, 0), UnsignedDecimal("234534567456"))
        liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("245457456745342")
        liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("2345356747467456743")
        liq_tree.remove_m_liq(LiqRange(0, 0), UnsignedDecimal("2453464574674"))
        liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("456456756586578")
        liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("5634564564356435")
        liq_tree.add_t_liq(LiqRange(0, 0), UnsignedDecimal("3564575678567"), UnsignedDecimal("35664576857e18"), UnsignedDecimal("3565685685672375e6"))
        liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("34575687568567345")
        liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("345654675678567345")
        liq_tree.remove_t_liq(LiqRange(0, 0), UnsignedDecimal("3564575678567"), UnsignedDecimal("3564575678567e18"), UnsignedDecimal("3565467683463e6"))

        # LiqRange(0, 1)
        liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("78567456345")
        liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("234535756856785673")
        liq_tree.add_m_liq(LiqRange(0, 1), UnsignedDecimal("253464575685786"))
        liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("67968435")
        liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("2454575685679")
        liq_tree.remove_m_liq(LiqRange(0, 1), UnsignedDecimal("234535645756867"))
        liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("2345356568")
        liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("678678456")
        liq_tree.add_t_liq(LiqRange(0, 1), UnsignedDecimal("23476"), UnsignedDecimal("24543634e18"), UnsignedDecimal("34535674564e5"))
        liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("2345357645")
        liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("243253453")
        liq_tree.remove_t_liq(LiqRange(0, 1), UnsignedDecimal("13476"), UnsignedDecimal("45646745674e18"), UnsignedDecimal("23453457457e6"))

        # LiqRange(0, 2)
        liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("6735468234823")
        liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("56456456")
        liq_tree.add_m_liq(LiqRange(0, 2), UnsignedDecimal("23453456457"))
        liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("245346457457456")
        liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("2345346456474")
        liq_tree.remove_m_liq(LiqRange(0, 2), UnsignedDecimal("2345346"))
        liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("2345457")
        liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("457645745745643")
        liq_tree.add_t_liq(LiqRange(0, 2), UnsignedDecimal("645674564"), UnsignedDecimal("34545745745e18"), UnsignedDecimal("6745357452734e6"))
        liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("22345457456745")
        liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("345645754723")
        liq_tree.remove_t_liq(LiqRange(0, 2), UnsignedDecimal("87623487623"), UnsignedDecimal("7623467823e18"), UnsignedDecimal("524315237816e6"))

        # LiqRange(0, 3)
        liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("53452634236874")
        liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("4564574574546345")
        liq_tree.add_m_liq(LiqRange(0, 3), UnsignedDecimal("234534634567"))
        liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("45645753")
        liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("245345346")
        liq_tree.remove_m_liq(LiqRange(0, 3), UnsignedDecimal("678567856875"))
        liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("45645634")
        liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("45647456785")
        liq_tree.add_t_liq(LiqRange(0, 3), UnsignedDecimal("356456457"), UnsignedDecimal("23464574e18"), UnsignedDecimal("234534567e6"))
        liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("35645374")
        liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("2356456454645")
        liq_tree.remove_t_liq(LiqRange(0, 3), UnsignedDecimal("45645747568"), UnsignedDecimal("8672538476e18"), UnsignedDecimal("2456456435e6"))

        # LiqRange(0, 4)
        liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("2342454")
        liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("45645745")
        liq_tree.add_m_liq(LiqRange(0, 4), UnsignedDecimal("32452345"))
        liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("934765")
        liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("24534534")
        liq_tree.remove_m_liq(LiqRange(0, 4), UnsignedDecimal("456456"))
        liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("245")
        liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("2345")
        liq_tree.add_t_liq(LiqRange(0, 4), UnsignedDecimal("476574"), UnsignedDecimal("346356355e18"), UnsignedDecimal("45357467456e6"))
        liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("245234")
        liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("24634642")
        liq_tree.remove_t_liq(LiqRange(0, 4), UnsignedDecimal("2245346456"), UnsignedDecimal("87637465238746e18"), UnsignedDecimal("834527836e6"))

        # LiqRange(0, 5)
        liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("76354826342")
        liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("45645")
        liq_tree.add_m_liq(LiqRange(0, 5), UnsignedDecimal("345345"))
        liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("674567")
        liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("456346")
        liq_tree.remove_m_liq(LiqRange(0, 5), UnsignedDecimal("34646"))
        liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("34634")
        liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("234534534")
        liq_tree.add_t_liq(LiqRange(0, 5), UnsignedDecimal("656454"), UnsignedDecimal("3574573e18"), UnsignedDecimal("245435745e6"))
        liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("345453")
        liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("453634")
        liq_tree.remove_t_liq(LiqRange(0, 5), UnsignedDecimal("45346346"), UnsignedDecimal("324564564e18"), UnsignedDecimal("3434645e6"))

        # LiqRange(0, 6)
        liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("678456456")
        liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("24352356457")
        liq_tree.add_m_liq(LiqRange(0, 6), UnsignedDecimal("234534534"))
        liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("45756756")
        liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("2345345")
        liq_tree.remove_m_liq(LiqRange(0, 6), UnsignedDecimal("456"))
        liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("24")
        liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("245346")
        liq_tree.add_t_liq(LiqRange(0, 6), UnsignedDecimal("4545"), UnsignedDecimal("456457e18"), UnsignedDecimal("3456467e6"))
        liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("24534")
        liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("4745645")
        liq_tree.remove_t_liq(LiqRange(0, 6), UnsignedDecimal("34534534"), UnsignedDecimal("47253765e18"), UnsignedDecimal("7856856e6"))

        # LiqRange(0, 7)
        liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("76238467283764")
        liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("23453563456734567")
        liq_tree.add_m_liq(LiqRange(0, 7), UnsignedDecimal("345236634634"))
        liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("3246457467")
        liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("3453453456")
        liq_tree.remove_m_liq(LiqRange(0, 7), UnsignedDecimal("342345"))
        liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("45746756")
        liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("5685685678")
        liq_tree.add_t_liq(LiqRange(0, 7), UnsignedDecimal("6796786"), UnsignedDecimal("46745674e18"), UnsignedDecimal("7567567e6"))
        liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("5345346")
        liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("575685656")
        liq_tree.remove_t_liq(LiqRange(0, 7), UnsignedDecimal("345345345"), UnsignedDecimal("456457457e18"), UnsignedDecimal("4564564564e6"))

        # LiqRange(0, 8)
        liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("2342453")
        liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("5675675")
        liq_tree.add_m_liq(LiqRange(0, 8), UnsignedDecimal("45345345"))
        liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("56756756")
        liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("34534534")
        liq_tree.remove_m_liq(LiqRange(0, 8), UnsignedDecimal("5675675"))
        liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("345345")
        liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("34534534")
        liq_tree.add_t_liq(LiqRange(0, 8), UnsignedDecimal("45646756"), UnsignedDecimal("2343456e18"), UnsignedDecimal("34354534e6"))
        liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("3453")
        liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("675675")
        liq_tree.remove_t_liq(LiqRange(0, 8), UnsignedDecimal("534534"), UnsignedDecimal("5645645e18"), UnsignedDecimal("42342343e6"))

        # LiqRange(0, 9)
        liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("345345")
        liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("445656")
        liq_tree.add_m_liq(LiqRange(0, 9), UnsignedDecimal("345345"))
        liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("2345235")
        liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("34534534")
        liq_tree.remove_m_liq(LiqRange(0, 9), UnsignedDecimal("556456"))
        liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("56756743")
        liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("345345345")
        liq_tree.add_t_liq(LiqRange(0, 9), UnsignedDecimal("56756756"), UnsignedDecimal("345345345345e18"), UnsignedDecimal("45645645e6"))
        liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("4564564")
        liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("54564")
        liq_tree.remove_t_liq(LiqRange(0, 9), UnsignedDecimal("345345"), UnsignedDecimal("3634534e18"), UnsignedDecimal("5675675e6"))

        # LiqRange(0, 10)
        liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("234234")
        liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("2454353")
        liq_tree.add_m_liq(LiqRange(0, 10), UnsignedDecimal("345345"))
        liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("34234")
        liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("34234")
        liq_tree.remove_m_liq(LiqRange(0, 10), UnsignedDecimal("564564"))
        liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("34534")
        liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("3453")
        liq_tree.add_t_liq(LiqRange(0, 10), UnsignedDecimal("4745674"), UnsignedDecimal("345345e18"), UnsignedDecimal("3453453e6"))
        liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("34534")
        liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("245234")
        liq_tree.remove_t_liq(LiqRange(0, 10), UnsignedDecimal("345345"), UnsignedDecimal("4564564e18"), UnsignedDecimal("78675e6"))

        # LiqRange(0, 11)
        liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("345634")
        liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("56756")
        liq_tree.add_m_liq(LiqRange(0, 11), UnsignedDecimal("345345345"))
        liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("567457346")
        liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("454")
        liq_tree.remove_m_liq(LiqRange(0, 11), UnsignedDecimal("56456"))
        liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("34543564674")
        liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("3453453")
        liq_tree.add_t_liq(LiqRange(0, 11), UnsignedDecimal("234236"), UnsignedDecimal("456456e28"), UnsignedDecimal("75675675e6"))
        liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("345345")
        liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("45456457")
        liq_tree.remove_t_liq(LiqRange(0, 11), UnsignedDecimal("2456345"), UnsignedDecimal("2342352e18"), UnsignedDecimal("456456e6"))

        # LiqRange(0, 12)
        liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("5464564")
        liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("234234")
        liq_tree.add_m_liq(LiqRange(0, 12), UnsignedDecimal("26345345"))
        liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("45674564")
        liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("234234")
        liq_tree.remove_m_liq(LiqRange(0, 12), UnsignedDecimal("534345534534"))
        liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("223232323")
        liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("454646456")
        liq_tree.add_t_liq(LiqRange(0, 12), UnsignedDecimal("214123213"), UnsignedDecimal("3453454e18"), UnsignedDecimal("456456457e6"))
        liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("234245356")
        liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("23423423")
        liq_tree.remove_t_liq(LiqRange(0, 12), UnsignedDecimal("7553453"), UnsignedDecimal("234534534e18"), UnsignedDecimal("5685675674e6"))

        # LiqRange(0, 13)
        liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("23445")
        liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("34543534")
        liq_tree.add_m_liq(LiqRange(0, 13), UnsignedDecimal("76574564"))
        liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("345346")
        liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("74678456")
        liq_tree.remove_m_liq(LiqRange(0, 13), UnsignedDecimal("45252"))
        liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("234234")
        liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("45674574")
        liq_tree.add_t_liq(LiqRange(0, 13), UnsignedDecimal("354635345"), UnsignedDecimal("46345634e18"), UnsignedDecimal("3453453e6"))
        liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("235454534")
        liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("34643564357")
        liq_tree.remove_t_liq(LiqRange(0, 13), UnsignedDecimal("23453454"), UnsignedDecimal("23453454e18"), UnsignedDecimal("2342352e6"))

        # LiqRange(0, 14)
        liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("453463563")
        liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("34564356")
        liq_tree.add_m_liq(LiqRange(0, 14), UnsignedDecimal("2342454"))
        liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("456457457")
        liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("3453452345")
        liq_tree.remove_m_liq(LiqRange(0, 14), UnsignedDecimal("234234234"))
        liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("6345634534")
        liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("23423423")
        liq_tree.add_t_liq(LiqRange(0, 14), UnsignedDecimal("1345645646"), UnsignedDecimal("232342e18"), UnsignedDecimal("345345345e6"))
        liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("34523452352")
        liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("7457457456")
        liq_tree.remove_t_liq(LiqRange(0, 14), UnsignedDecimal("1345645646"), UnsignedDecimal("25634624e18"), UnsignedDecimal("23434635e6"))

        # LiqRange(0, 15) aka root
        liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("3453645745674")
        liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("4574563456456")
        liq_tree.add_wide_m_liq(UnsignedDecimal("34534534534"))
        liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("2342342342")
        liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("3533463457467")
        liq_tree.remove_wide_m_liq(UnsignedDecimal("678678678"))
        liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("56456456456")
        liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("34532464567568")
        liq_tree.add_wide_t_liq(UnsignedDecimal("3463456456456"), UnsignedDecimal("34575684564e18"), UnsignedDecimal("345345746745e6"))
        liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("3645746746787")
        liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("2342342")
        liq_tree.remove_wide_t_liq(UnsignedDecimal("3574534534"), UnsignedDecimal("4567452342e18"), UnsignedDecimal("234535734563e6"))

        # region Ranges that start with 1 -------------------------------------------------------------------------------------
        # LiqRange(1, 1)
        liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("75345234")
        liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("674563456")
        liq_tree.add_m_liq(LiqRange(1, 1), UnsignedDecimal("34534"))
        liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("234234")
        liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("53453")
        liq_tree.remove_m_liq(LiqRange(1, 1), UnsignedDecimal("234345345"))
        liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("453453")
        liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("453453453")
        liq_tree.add_t_liq(LiqRange(1, 1), UnsignedDecimal("234234"), UnsignedDecimal("34534e18"), UnsignedDecimal("4534e6"))
        liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("9834")
        liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("97234")
        liq_tree.remove_t_liq(LiqRange(1, 1), UnsignedDecimal("34534"), UnsignedDecimal("234e18"), UnsignedDecimal("23e8"))

        # LiqRange(1, 2)
        liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("75345234")
        liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("674563456")
        liq_tree.add_m_liq(LiqRange(1, 2), UnsignedDecimal("34534"))
        liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("234234")
        liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("53453")
        liq_tree.remove_m_liq(LiqRange(1, 2), UnsignedDecimal("234345345"))
        liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("453453")
        liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("453453453")
        liq_tree.add_t_liq(LiqRange(1, 2), UnsignedDecimal("234234"), UnsignedDecimal("34534e18"), UnsignedDecimal("4534e6"))
        liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("9834")
        liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("97234")
        liq_tree.remove_t_liq(LiqRange(1, 2), UnsignedDecimal("34534"), UnsignedDecimal("234e18"), UnsignedDecimal("23e8"))

        # LiqRange(1, 3)
        liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("75345234")
        liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("674563456")
        liq_tree.add_m_liq(LiqRange(1, 3), UnsignedDecimal("34534"))
        liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("234234")
        liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("53453")
        liq_tree.remove_m_liq(LiqRange(1, 3), UnsignedDecimal("234345345"))
        liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("453453")
        liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("453453453")
        liq_tree.add_t_liq(LiqRange(1, 3), UnsignedDecimal("234234"), UnsignedDecimal("34534e18"), UnsignedDecimal("4534e6"))
        liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("9834")
        liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("97234")
        liq_tree.remove_t_liq(LiqRange(1, 3), UnsignedDecimal("34534"), UnsignedDecimal("234e18"), UnsignedDecimal("23e8"))

        # LiqRange(1, 4)
        liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("75345234")
        liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("674563456")
        liq_tree.add_m_liq(LiqRange(1, 4), UnsignedDecimal("34534"))
        liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("234234")
        liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("53453")
        liq_tree.remove_m_liq(LiqRange(1, 4), UnsignedDecimal("234345345"))
        liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("453453")
        liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("453453453")
        liq_tree.add_t_liq(LiqRange(1, 4), UnsignedDecimal("234234"), UnsignedDecimal("34534e18"), UnsignedDecimal("4534e6"))
        liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("9834")
        liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("97234")
        liq_tree.remove_t_liq(LiqRange(1, 4), UnsignedDecimal("34534"), UnsignedDecimal("234e18"), UnsignedDecimal("23e8"))

        # LiqRange(1, 5)
        liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("75345234")
        liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("674563456")
        liq_tree.add_m_liq(LiqRange(1, 5), UnsignedDecimal("34534"))
        liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("234234")
        liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("53453")
        liq_tree.remove_m_liq(LiqRange(1, 5), UnsignedDecimal("234345345"))
        liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("453453")
        liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("453453453")
        liq_tree.add_t_liq(LiqRange(1, 5), UnsignedDecimal("234234"), UnsignedDecimal("34534e18"), UnsignedDecimal("4534e6"))
        liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("9834")
        liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("97234")
        liq_tree.remove_t_liq(LiqRange(1, 5), UnsignedDecimal("34534"), UnsignedDecimal("234e18"), UnsignedDecimal("23e8"))

        # LiqRange(1, 6)
        liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("75345234")
        liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("674563456")
        liq_tree.add_m_liq(LiqRange(1, 6), UnsignedDecimal("34534"))
        liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("234234")
        liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("53453")
        liq_tree.remove_m_liq(LiqRange(1, 6), UnsignedDecimal("234345345"))
        liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("453453")
        liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("453453453")
        liq_tree.add_t_liq(LiqRange(1, 6), UnsignedDecimal("234234"), UnsignedDecimal("34534e18"), UnsignedDecimal("4534e6"))
        liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("9834")
        liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("97234")
        liq_tree.remove_t_liq(LiqRange(1, 6), UnsignedDecimal("34534"), UnsignedDecimal("234e18"), UnsignedDecimal("23e8"))

        # LiqRange(1, 7)
        liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("45745645")
        liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("46")
        liq_tree.add_m_liq(LiqRange(1, 7), UnsignedDecimal("457467"))
        liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("3453")
        liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("345346")
        liq_tree.remove_m_liq(LiqRange(1, 7), UnsignedDecimal("73345"))
        liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("345345")
        liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("56756")
        liq_tree.add_t_liq(LiqRange(1, 7), UnsignedDecimal("6357457457"), UnsignedDecimal("456468745"), UnsignedDecimal("3453e6"))
        liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("68567")
        liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("3467")
        liq_tree.remove_t_liq(LiqRange(1, 7), UnsignedDecimal("3634534"), UnsignedDecimal("3453463e18"), UnsignedDecimal("34534e6"))

        # LiqRange(1, 8)
        liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("56457")
        liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("456456")
        liq_tree.add_m_liq(LiqRange(1, 8), UnsignedDecimal("3465346"))
        liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("343")
        liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("3453746")
        liq_tree.remove_m_liq(LiqRange(1, 8), UnsignedDecimal("756756"))
        liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("57457")
        liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("45346346")
        liq_tree.add_t_liq(LiqRange(1, 8), UnsignedDecimal("23424"), UnsignedDecimal("223423e18"), UnsignedDecimal("34634534e6"))
        liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("23423")
        liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("34634")
        liq_tree.remove_t_liq(LiqRange(1, 8), UnsignedDecimal("345345"), UnsignedDecimal("23423e18"), UnsignedDecimal("3434e6"))

        # LiqRange(1, 9)
        liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("3453")
        liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("3573")
        liq_tree.add_m_liq(LiqRange(1, 9), UnsignedDecimal("345345"))
        liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("45745")
        liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("4523")
        liq_tree.remove_m_liq(LiqRange(1, 9), UnsignedDecimal("34534"))
        liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("34534")
        liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("6745674")
        liq_tree.add_t_liq(LiqRange(1, 9), UnsignedDecimal("573534"), UnsignedDecimal("2342354e18"), UnsignedDecimal("3453453e6"))
        liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("234234")
        liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("64563453")
        liq_tree.remove_t_liq(LiqRange(1, 9), UnsignedDecimal("34535754"), UnsignedDecimal("3453467435e18"), UnsignedDecimal("4564e6"))

        # LiqRange(1, 10)
        liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("457457")
        liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("4534534")
        liq_tree.add_m_liq(LiqRange(1, 10), UnsignedDecimal("34534634"))
        liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("34534")
        liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("47574")
        liq_tree.remove_m_liq(LiqRange(1, 10), UnsignedDecimal("4574574"))
        liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("6745674")
        liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("34525")
        liq_tree.add_t_liq(LiqRange(1, 10), UnsignedDecimal("3453453"), UnsignedDecimal("5645634523e18"), UnsignedDecimal("46346534e6"))
        liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("345357")
        liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("756745")
        liq_tree.remove_t_liq(LiqRange(1, 10), UnsignedDecimal("345346475"), UnsignedDecimal("745645e18"), UnsignedDecimal("78564564e6"))

        # LiqRange(1, 11)
        liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("457457")
        liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("4434524")
        liq_tree.add_m_liq(LiqRange(1, 11), UnsignedDecimal("3453453467"))
        liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("35756785685")
        liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("5664564")
        liq_tree.remove_m_liq(LiqRange(1, 11), UnsignedDecimal("345346346"))
        liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("234235")
        liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("6347356")
        liq_tree.add_t_liq(LiqRange(1, 11), UnsignedDecimal("57463"), UnsignedDecimal("34634563e18"), UnsignedDecimal("453463e6"))
        liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("34524")
        liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("2342345")
        liq_tree.remove_t_liq(LiqRange(1, 11), UnsignedDecimal("634634"), UnsignedDecimal("453576353e18"), UnsignedDecimal("5734534e6"))

        # LiqRange(1, 12)
        liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("3423423")
        liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("3453456")
        liq_tree.add_m_liq(LiqRange(1, 12), UnsignedDecimal("4564574"))
        liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("345245")
        liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("234235")
        liq_tree.remove_m_liq(LiqRange(1, 12), UnsignedDecimal("4574564"))
        liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("2342342")
        liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("6345634")
        liq_tree.add_t_liq(LiqRange(1, 12), UnsignedDecimal("34634567"), UnsignedDecimal("23424e18"), UnsignedDecimal("3453464e6"))
        liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("345345")
        liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("234235")
        liq_tree.remove_t_liq(LiqRange(1, 12), UnsignedDecimal("4564564"), UnsignedDecimal("2342342e18"), UnsignedDecimal("456456e6"))

        # LiqRange(1, 13)
        liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("456457")
        liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("456457")
        liq_tree.add_m_liq(LiqRange(1, 13), UnsignedDecimal("567568"))
        liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("567567")
        liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("97867")
        liq_tree.remove_m_liq(LiqRange(1, 13), UnsignedDecimal("9785"))
        liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("67758")
        liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("35645674")
        liq_tree.add_t_liq(LiqRange(1, 13), UnsignedDecimal("235363565"), UnsignedDecimal("234534635e18"), UnsignedDecimal("456745643e6"))
        liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("345346")
        liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("45674565")
        liq_tree.remove_t_liq(LiqRange(1, 13), UnsignedDecimal("4545345"), UnsignedDecimal("34535635e18"), UnsignedDecimal("7564353e6"))

        # LiqRange(1, 14)
        liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("4567435634")
        liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("234234235")
        liq_tree.add_m_liq(LiqRange(1, 14), UnsignedDecimal("357635634"))
        liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("23535636")
        liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("234534643576345")
        liq_tree.remove_m_liq(LiqRange(1, 14), UnsignedDecimal("23425346456"))
        liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("3452342352")
        liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("356734634532")
        liq_tree.add_t_liq(LiqRange(1, 14), UnsignedDecimal("35235235"), UnsignedDecimal("346356343e18"), UnsignedDecimal("234265e6"))
        liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("2342456")
        liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("3563463")
        liq_tree.remove_t_liq(LiqRange(1, 14), UnsignedDecimal("234235"), UnsignedDecimal("4564565e18"), UnsignedDecimal("4564563452e6"))

        # LiqRange(1, 15)
        liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("234234")
        liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("2463634534563")
        liq_tree.add_m_liq(LiqRange(1, 15), UnsignedDecimal("34634636"))
        liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("1234245346")
        liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("3453453")
        liq_tree.remove_m_liq(LiqRange(1, 15), UnsignedDecimal("34534636"))
        liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("3463463")
        liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("234523452")
        liq_tree.add_t_liq(LiqRange(1, 15), UnsignedDecimal("234534534"), UnsignedDecimal("1234235235e18"), UnsignedDecimal("23423456346e6"))
        liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("134235235")
        liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("3634634523")
        liq_tree.remove_t_liq(LiqRange(1, 15), UnsignedDecimal("2342352356"), UnsignedDecimal("3465343e18"), UnsignedDecimal("3562342346e6"))

        # endregion

        # m_liq
        self.assertEqual(root.m_liq, UnsignedDecimal("34693061576"))

        self.assertEqual(L.m_liq, UnsignedDecimal("439440851037"))
        self.assertEqual(R.m_liq, UnsignedDecimal("9846145283924"))

        self.assertEqual(LL.m_liq, UnsignedDecimal("1324904479181181"))
        self.assertEqual(LR.m_liq, UnsignedDecimal("3456457542419875553"))
        self.assertEqual(RL.m_liq, UnsignedDecimal("76483482065306300976"))
        self.assertEqual(RR.m_liq, UnsignedDecimal("8623526734267390879"))

        self.assertEqual(LLL.m_liq, UnsignedDecimal("98987279855430619607264"))
        self.assertEqual(LLR.m_liq, UnsignedDecimal("7986785734811822254"))
        self.assertEqual(LRL.m_liq, UnsignedDecimal("232467224906920"))
        self.assertEqual(LRR.m_liq, UnsignedDecimal("777839863652735"))
        self.assertEqual(RLL.m_liq, UnsignedDecimal("3131567868974474895"))
        self.assertEqual(RLR.m_liq, UnsignedDecimal("78724563469237853906739487"))
        self.assertEqual(RRL.m_liq, UnsignedDecimal("7556478634723885529808249"))
        self.assertEqual(RRR.m_liq, UnsignedDecimal("54534789284573456239862722"))

        self.assertEqual(LLLL.m_liq, UnsignedDecimal("92736476015993741705"))
        self.assertEqual(LLLR.m_liq, UnsignedDecimal("76238216349061404466493"))
        self.assertEqual(LLRL.m_liq, UnsignedDecimal("2368562145653"))
        self.assertEqual(LLRR.m_liq, UnsignedDecimal("12341234213421354513456"))
        self.assertEqual(LRLL.m_liq, UnsignedDecimal("456467365563767"))
        self.assertEqual(LRLR.m_liq, UnsignedDecimal("89805856756746"))
        self.assertEqual(LRRL.m_liq, UnsignedDecimal("34545756857245324757901"))
        self.assertEqual(LRRR.m_liq, UnsignedDecimal("2334646757867856856346"))
        self.assertEqual(RLLL.m_liq, UnsignedDecimal("24674758679564605824007"))
        self.assertEqual(RLLR.m_liq, UnsignedDecimal("547867967467456457536856873"))
        self.assertEqual(RLRL.m_liq, UnsignedDecimal("34564375645457598309297"))
        self.assertEqual(RLRR.m_liq, UnsignedDecimal("32546475786796896785674564"))
        self.assertEqual(RRLL.m_liq, UnsignedDecimal("5856745645100215364274"))
        self.assertEqual(RRLR.m_liq, UnsignedDecimal("4574785673643563456"))
        self.assertEqual(RRRL.m_liq, UnsignedDecimal("24534622447854143"))
        self.assertEqual(RRRR.m_liq, UnsignedDecimal("6345346534645746"))

        # t_liq
        self.assertEqual(root.t_liq, UnsignedDecimal("3460019127642"))

        self.assertEqual(L.t_liq, UnsignedDecimal("28597487121"))
        self.assertEqual(R.t_liq, UnsignedDecimal("844037366102"))

        self.assertEqual(LL.t_liq, UnsignedDecimal("325300632181949"))
        self.assertEqual(LR.t_liq, UnsignedDecimal("456457566510607868"))
        self.assertEqual(RL.t_liq, UnsignedDecimal("6483482620225461246"))
        self.assertEqual(RR.t_liq, UnsignedDecimal("86235267342673908"))

        self.assertEqual(LLL.t_liq, UnsignedDecimal("8987279836391260764175"))
        self.assertEqual(LLR.t_liq, UnsignedDecimal("986785759840596613"))
        self.assertEqual(LRL.t_liq, UnsignedDecimal("132467379863284"))
        self.assertEqual(LRR.t_liq, UnsignedDecimal("277839863652735"))
        self.assertEqual(RLL.t_liq, UnsignedDecimal("2131567868629590852"))
        self.assertEqual(RLR.t_liq, UnsignedDecimal("8724563469237853906739487"))
        self.assertEqual(RRL.t_liq, UnsignedDecimal("5556478634723909349324867"))
        self.assertEqual(RRR.t_liq, UnsignedDecimal("34534789284573456239862722"))

        self.assertEqual(LLLL.t_liq, UnsignedDecimal("9736478234923748923"))
        self.assertEqual(LLLR.t_liq, UnsignedDecimal("7623821634912439930558"))
        self.assertEqual(LLRL.t_liq, UnsignedDecimal("147556921176"))
        self.assertEqual(LLRR.t_liq, UnsignedDecimal("1234123421342135451345"))
        self.assertEqual(LRLL.t_liq, UnsignedDecimal("45644512117686"))
        self.assertEqual(LRLR.t_liq, UnsignedDecimal("8980585675674"))
        self.assertEqual(LRRL.t_liq, UnsignedDecimal("3454575685724498123174"))
        self.assertEqual(LRRR.t_liq, UnsignedDecimal("233464675786785685634"))
        self.assertEqual(RLLL.t_liq, UnsignedDecimal("2467475867956501134875"))
        self.assertEqual(RLLR.t_liq, UnsignedDecimal("54786796746745645753685687"))
        self.assertEqual(RLRL.t_liq, UnsignedDecimal("3456437564545419364152"))
        self.assertEqual(RLRR.t_liq, UnsignedDecimal("3254647578679689678567456"))
        self.assertEqual(RRLL.t_liq, UnsignedDecimal("585674564563690096108"))
        self.assertEqual(RRLR.t_liq, UnsignedDecimal("457478567364356345"))
        self.assertEqual(RRRL.t_liq, UnsignedDecimal("2453464609746674"))
        self.assertEqual(RRRR.t_liq, UnsignedDecimal("6345346534645743"))

        # subtree_m_liq
        self.assertEqual(root.subtree_m_liq, UnsignedDecimal("862435110165848273097702739"))

        self.assertEqual(L.subtree_m_liq, UnsignedDecimal("323556957638501881815645"))
        self.assertEqual(R.subtree_m_liq, UnsignedDecimal("862111553208209216126901878"))

        self.assertEqual(LL.subtree_m_liq, UnsignedDecimal("286662725622816094451067"))
        self.assertEqual(LR.subtree_m_liq, UnsignedDecimal("36894232012170260556282"))
        self.assertEqual(RL.subtree_m_liq, UnsignedDecimal("737923121524118083514297409"))
        self.assertEqual(RR.subtree_m_liq, UnsignedDecimal("124188431684012363450333077"))

        self.assertEqual(LLL.subtree_m_liq, UnsignedDecimal("274305512535938637422726"))
        self.assertEqual(LLR.subtree_m_liq, UnsignedDecimal("12357207787259540303617"))
        self.assertEqual(LRL.subtree_m_liq, UnsignedDecimal("1011207672134353"))
        self.assertEqual(LRR.subtree_m_liq, UnsignedDecimal("36880405170792908919717"))
        self.assertEqual(RLL.subtree_m_liq, UnsignedDecimal("547892648489271760091630670"))
        self.assertEqual(RLR.subtree_m_liq, UnsignedDecimal("190030167100918062197462835"))
        self.assertEqual(RRL.subtree_m_liq, UnsignedDecimal("15118818589878544918544228"))
        self.assertEqual(RRR.subtree_m_liq, UnsignedDecimal("109069578600026881462225333"))

        self.assertEqual(LLLL.subtree_m_liq, UnsignedDecimal("92736476015993741705"))
        self.assertEqual(LLLR.subtree_m_liq, UnsignedDecimal("76238216349061404466493"))
        self.assertEqual(LLRL.subtree_m_liq, UnsignedDecimal("2368562145653"))
        self.assertEqual(LLRR.subtree_m_liq, UnsignedDecimal("12341234213421354513456"))
        self.assertEqual(LRLL.subtree_m_liq, UnsignedDecimal("456467365563767"))
        self.assertEqual(LRLR.subtree_m_liq, UnsignedDecimal("89805856756746"))
        self.assertEqual(LRRL.subtree_m_liq, UnsignedDecimal("34545756857245324757901"))
        self.assertEqual(LRRR.subtree_m_liq, UnsignedDecimal("2334646757867856856346"))
        self.assertEqual(RLLL.subtree_m_liq, UnsignedDecimal("24674758679564605824007"))
        self.assertEqual(RLLR.subtree_m_liq, UnsignedDecimal("547867967467456457536856873"))
        self.assertEqual(RLRL.subtree_m_liq, UnsignedDecimal("34564375645457598309297"))
        self.assertEqual(RLRR.subtree_m_liq, UnsignedDecimal("32546475786796896785674564"))
        self.assertEqual(RRLL.subtree_m_liq, UnsignedDecimal("5856745645100215364274"))
        self.assertEqual(RRLR.subtree_m_liq, UnsignedDecimal("4574785673643563456"))
        self.assertEqual(RRRL.subtree_m_liq, UnsignedDecimal("24534622447854143"))
        self.assertEqual(RRRR.subtree_m_liq, UnsignedDecimal("6345346534645746"))

        # borrow_x
        self.assertEqual(root.token_x_borrow, UnsignedDecimal("122757244859000000000000000000"))

        self.assertEqual(L.token_x_borrow, UnsignedDecimal("4564946112436545000000000000000000"))
        self.assertEqual(R.token_x_borrow, UnsignedDecimal("4214226187000000000000000000"))

        self.assertEqual(LL.token_x_borrow, UnsignedDecimal("28591083251822194000000000000000000"))
        self.assertEqual(LR.token_x_borrow, UnsignedDecimal("872538470624167989000000000456468745"))
        self.assertEqual(RL.token_x_borrow, UnsignedDecimal("11350238408160809000000000000000000"))
        self.assertEqual(RR.token_x_borrow, UnsignedDecimal("498723597863764293000000000000000000"))

        self.assertEqual(LLL.token_x_borrow, UnsignedDecimal("45623798462966929913344000000000000000000"))
        self.assertEqual(LLR.token_x_borrow, UnsignedDecimal("298364785638480072406864000000000456468745"))
        self.assertEqual(LRL.token_x_borrow, UnsignedDecimal("27364762534827634534656283000000000000000000"))
        self.assertEqual(LRR.token_x_borrow, UnsignedDecimal("7653642903472903784290347000000000000000000"))
        self.assertEqual(RLL.token_x_borrow, UnsignedDecimal("23452367423432458653826000000000000000000"))
        self.assertEqual(RLR.token_x_borrow, UnsignedDecimal("2765723642783492000000000000000000"))
        self.assertEqual(RRL.token_x_borrow, UnsignedDecimal("28635482365337910060000000000000000000"))
        self.assertEqual(RRR.token_x_borrow, UnsignedDecimal("27364527863428346239867000000000000000000"))

        self.assertEqual(LLLL.token_x_borrow, UnsignedDecimal("5730994510532853000000000000000000"))
        self.assertEqual(LLLR.token_x_borrow, UnsignedDecimal("346456348776251331000000000456468745"))
        self.assertEqual(LLRL.token_x_borrow, UnsignedDecimal("82735476982561720575720000000000000000000"))
        self.assertEqual(LLRR.token_x_borrow, UnsignedDecimal("2367452364752903485729403875000000000000000000"))
        self.assertEqual(LRLL.token_x_borrow, UnsignedDecimal("236452378374761357390655000000000000000000"))
        self.assertEqual(LRLR.token_x_borrow, UnsignedDecimal("8374278364628364000000000000000000"))
        self.assertEqual(LRRL.token_x_borrow, UnsignedDecimal("3456457409582626000000000000000000"))
        self.assertEqual(LRRR.token_x_borrow, UnsignedDecimal("236542867349237498000000000000000000"))
        self.assertEqual(RLLL.token_x_borrow, UnsignedDecimal("51427634238746298454880156000000000000000000"))
        self.assertEqual(RLLR.token_x_borrow, UnsignedDecimal("634529836428376523000000000000000000"))
        self.assertEqual(RLRL.token_x_borrow, UnsignedDecimal("1212312318064122113000000000000000000"))
        self.assertEqual(RLRR.token_x_borrow, UnsignedDecimal("287346234623487923642786000000000000000000"))
        self.assertEqual(RRLL.token_x_borrow, UnsignedDecimal("2837427354234552837898000000000000000000"))
        self.assertEqual(RRLR.token_x_borrow, UnsignedDecimal("82635472634823674000000000000000000"))
        self.assertEqual(RRRL.token_x_borrow, UnsignedDecimal("23645278463153819232000000000000000000"))
        self.assertEqual(RRRR.token_x_borrow, UnsignedDecimal("37465276342938487000000000000000000"))

        # subtree_borrow_x
        self.assertEqual(root.token_x_subtree_borrow, UnsignedDecimal("2454902637693472541111720750000000001369406235"))

        self.assertEqual(L.token_x_subtree_borrow, UnsignedDecimal("2403133948136918240527296488000000001369406235"))
        self.assertEqual(R.token_x_subtree_borrow, UnsignedDecimal("51768689556554177827179403000000000000000000"))

        self.assertEqual(LL.token_x_subtree_borrow, UnsignedDecimal("2367879089194765920990906181000000000912937490"))
        self.assertEqual(LR.token_x_subtree_borrow, UnsignedDecimal("35254858937587373423953762000000000456468745"))
        self.assertEqual(RL.token_x_subtree_borrow, UnsignedDecimal("51738434701751335380619705000000000000000000"))
        self.assertEqual(RR.token_x_subtree_borrow, UnsignedDecimal("30254854802838232333511000000000000000000"))

        self.assertEqual(LLL.token_x_subtree_borrow, UnsignedDecimal("45624150650310216697528000000000456468745"))
        self.assertEqual(LLR.token_x_subtree_borrow, UnsignedDecimal("2367833465015524527522386459000000000456468745"))
        self.assertEqual(LRL.token_x_subtree_borrow, UnsignedDecimal("27601214921576674256675302000000000000000000"))
        self.assertEqual(LRR.token_x_subtree_borrow, UnsignedDecimal("7653643143472228543110471000000000000000000"))
        self.assertEqual(RLL.token_x_subtree_borrow, UnsignedDecimal("51451087240699567341910505000000000000000000"))
        self.assertEqual(RLR.token_x_subtree_borrow, UnsignedDecimal("287347449701529630548391000000000000000000"))
        self.assertEqual(RRL.token_x_subtree_borrow, UnsignedDecimal("2866145472072525571632000000000000000000"))
        self.assertEqual(RRR.token_x_subtree_borrow, UnsignedDecimal("27388210607167842997586000000000000000000"))

        self.assertEqual(LLLL.token_x_subtree_borrow, UnsignedDecimal("5730994510532853000000000000000000"))
        self.assertEqual(LLLR.token_x_subtree_borrow, UnsignedDecimal("346456348776251331000000000456468745"))
        self.assertEqual(LLRL.token_x_subtree_borrow, UnsignedDecimal("82735476982561720575720000000000000000000"))
        self.assertEqual(LLRR.token_x_subtree_borrow, UnsignedDecimal("2367452364752903485729403875000000000000000000"))
        self.assertEqual(LRLL.token_x_subtree_borrow, UnsignedDecimal("236452378374761357390655000000000000000000"))
        self.assertEqual(LRLR.token_x_subtree_borrow, UnsignedDecimal("8374278364628364000000000000000000"))
        self.assertEqual(LRRL.token_x_subtree_borrow, UnsignedDecimal("3456457409582626000000000000000000"))
        self.assertEqual(LRRR.token_x_subtree_borrow, UnsignedDecimal("236542867349237498000000000000000000"))
        self.assertEqual(RLLL.token_x_subtree_borrow, UnsignedDecimal("51427634238746298454880156000000000000000000"))
        self.assertEqual(RLLR.token_x_subtree_borrow, UnsignedDecimal("634529836428376523000000000000000000"))
        self.assertEqual(RLRL.token_x_subtree_borrow, UnsignedDecimal("1212312318064122113000000000000000000"))
        self.assertEqual(RLRR.token_x_subtree_borrow, UnsignedDecimal("287346234623487923642786000000000000000000"))
        self.assertEqual(RRLL.token_x_subtree_borrow, UnsignedDecimal("2837427354234552837898000000000000000000"))
        self.assertEqual(RRLR.token_x_subtree_borrow, UnsignedDecimal("82635472634823674000000000000000000"))
        self.assertEqual(RRRL.token_x_subtree_borrow, UnsignedDecimal("23645278463153819232000000000000000000"))
        self.assertEqual(RRRR.token_x_subtree_borrow, UnsignedDecimal("37465276342938487000000000000000000"))

        # borrow_y
        self.assertEqual(root.token_y_borrow, UnsignedDecimal("111746265029000000"))

        self.assertEqual(L.token_y_borrow, UnsignedDecimal("168910846992000000"))
        self.assertEqual(R.token_y_borrow, UnsignedDecimal("20158676903000000"))

        self.assertEqual(LL.token_y_borrow, UnsignedDecimal("1330115070330000000"))
        self.assertEqual(LR.token_y_borrow, UnsignedDecimal("25629380814000000"))
        self.assertEqual(RL.token_y_borrow, UnsignedDecimal("978614737019690000000"))
        self.assertEqual(RR.token_y_borrow, UnsignedDecimal("7856675879087000000"))

        self.assertEqual(LLL.token_y_borrow, UnsignedDecimal("8725348768599465892504400000"))
        self.assertEqual(LLR.token_y_borrow, UnsignedDecimal("3465873661686981218000000"))
        self.assertEqual(LRL.token_y_borrow, UnsignedDecimal("56736409827636032519000000"))
        self.assertEqual(LRR.token_y_borrow, UnsignedDecimal("7834626734902734902368000000"))
        self.assertEqual(RLL.token_y_borrow, UnsignedDecimal("9834787362493137985000000"))
        self.assertEqual(RLR.token_y_borrow, UnsignedDecimal("98576798364725367423000000"))
        self.assertEqual(RRL.token_y_borrow, UnsignedDecimal("83764587364859345003508901000000"))
        self.assertEqual(RRR.token_y_borrow, UnsignedDecimal("9834657827356482367482369000000"))

        self.assertEqual(LLLL.token_y_borrow, UnsignedDecimal("76196798741476175000000"))
        self.assertEqual(LLLR.token_y_borrow, UnsignedDecimal("26734872634892655597150111000000"))
        self.assertEqual(LLRL.token_y_borrow, UnsignedDecimal("763467253680744840679549000000"))
        self.assertEqual(LLRR.token_y_borrow, UnsignedDecimal("987349053045739487000000"))
        self.assertEqual(LRLL.token_y_borrow, UnsignedDecimal("984764582781001178332000000"))
        self.assertEqual(LRLR.token_y_borrow, UnsignedDecimal("8763867548273647826000000"))
        self.assertEqual(LRRL.token_y_borrow, UnsignedDecimal("8726347825634871839691000000"))
        self.assertEqual(LRRR.token_y_borrow, UnsignedDecimal("798647852364627983000000"))
        self.assertEqual(RLLL.token_y_borrow, UnsignedDecimal("74986238502927037000000"))
        self.assertEqual(RLLR.token_y_borrow, UnsignedDecimal("868746576834678534000000"))
        self.assertEqual(RLRL.token_y_borrow, UnsignedDecimal("3423423619393235000000"))
        self.assertEqual(RLRR.token_y_borrow, UnsignedDecimal("827364826734823748963000000"))
        self.assertEqual(RRLL.token_y_borrow, UnsignedDecimal("73649082374024158406167000000"))
        self.assertEqual(RRLR.token_y_borrow, UnsignedDecimal("2387642836423689768000000"))
        self.assertEqual(RRRL.token_y_borrow, UnsignedDecimal("3542359995424161000000"))
        self.assertEqual(RRRR.token_y_borrow, UnsignedDecimal("23984623847623867000000"))

        # subtree_borrow_y
        self.assertEqual(root.token_y_subtree_borrow, UnsignedDecimal("121198515219146561028675018400000"))

        self.assertEqual(L.token_y_subtree_borrow, UnsignedDecimal("27524681804831584915445899400000"))
        self.assertEqual(R.token_y_subtree_borrow, UnsignedDecimal("93673833414314864366964090000000"))

        self.assertEqual(LL.token_y_subtree_borrow, UnsignedDecimal("27507069766762843492989374400000"))
        self.assertEqual(LR.token_y_subtree_borrow, UnsignedDecimal("17612038068572511609533000000"))
        self.assertEqual(RL.token_y_subtree_borrow, UnsignedDecimal("936724547315736272867000000"))
        self.assertEqual(RR.token_y_subtree_borrow, UnsignedDecimal("93672896689767528472014320000000"))

        self.assertEqual(LLL.token_y_subtree_borrow, UnsignedDecimal("26743598059858053804518790400000"))
        self.assertEqual(LLR.token_y_subtree_borrow, UnsignedDecimal("763471706903459573400254000000"))
        self.assertEqual(LRL.token_y_subtree_borrow, UnsignedDecimal("1050264860156910858677000000"))
        self.assertEqual(LRR.token_y_subtree_borrow, UnsignedDecimal("16561773208389971370042000000"))
        self.assertEqual(RLL.token_y_subtree_borrow, UnsignedDecimal("10778520177830743556000000"))
        self.assertEqual(RLR.token_y_subtree_borrow, UnsignedDecimal("925945048523168509621000000"))
        self.assertEqual(RRL.token_y_subtree_borrow, UnsignedDecimal("83838238834876205585604836000000"))
        self.assertEqual(RRR.token_y_subtree_borrow, UnsignedDecimal("9834657854883466210530397000000"))

        self.assertEqual(LLLL.token_y_subtree_borrow, UnsignedDecimal("76196798741476175000000"))
        self.assertEqual(LLLR.token_y_subtree_borrow, UnsignedDecimal("26734872634892655597150111000000"))
        self.assertEqual(LLRL.token_y_subtree_borrow, UnsignedDecimal("763467253680744840679549000000"))
        self.assertEqual(LLRR.token_y_subtree_borrow, UnsignedDecimal("987349053045739487000000"))
        self.assertEqual(LRLL.token_y_subtree_borrow, UnsignedDecimal("984764582781001178332000000"))
        self.assertEqual(LRLR.token_y_subtree_borrow, UnsignedDecimal("8763867548273647826000000"))
        self.assertEqual(LRRL.token_y_subtree_borrow, UnsignedDecimal("8726347825634871839691000000"))
        self.assertEqual(LRRR.token_y_subtree_borrow, UnsignedDecimal("798647852364627983000000"))
        self.assertEqual(RLLL.token_y_subtree_borrow, UnsignedDecimal("74986238502927037000000"))
        self.assertEqual(RLLR.token_y_subtree_borrow, UnsignedDecimal("868746576834678534000000"))
        self.assertEqual(RLRL.token_y_subtree_borrow, UnsignedDecimal("3423423619393235000000"))
        self.assertEqual(RLRR.token_y_subtree_borrow, UnsignedDecimal("827364826734823748963000000"))
        self.assertEqual(RRLL.token_y_subtree_borrow, UnsignedDecimal("73649082374024158406167000000"))
        self.assertEqual(RRLR.token_y_subtree_borrow, UnsignedDecimal("2387642836423689768000000"))
        self.assertEqual(RRRL.token_y_subtree_borrow, UnsignedDecimal("3542359995424161000000"))
        self.assertEqual(RRRR.token_y_subtree_borrow, UnsignedDecimal("23984623847623867000000"))

        # token_x_cumulative_earned_per_m_liq
        self.assertEqual(root.token_x_cumulative_earned_per_m_liq, UnsignedDecimal("1653162341"))

        self.assertEqual(L.token_x_cumulative_earned_per_m_liq, UnsignedDecimal("1968034923387"))
        self.assertEqual(R.token_x_cumulative_earned_per_m_liq, UnsignedDecimal("53197209"))

        self.assertEqual(LL.token_x_cumulative_earned_per_m_liq, UnsignedDecimal("1537875992445232346"))
        self.assertEqual(LR.token_x_cumulative_earned_per_m_liq, UnsignedDecimal("363545476413679861713"))
        self.assertEqual(RL.token_x_cumulative_earned_per_m_liq, UnsignedDecimal("141356179733701"))
        self.assertEqual(RR.token_x_cumulative_earned_per_m_liq, UnsignedDecimal("61732151382143711"))

        self.assertEqual(LLL.token_x_cumulative_earned_per_m_liq, UnsignedDecimal("2556757494839963014198184"))
        self.assertEqual(LLR.token_x_cumulative_earned_per_m_liq, UnsignedDecimal("371158797429650858973438625"))
        self.assertEqual(LRL.token_x_cumulative_earned_per_m_liq, UnsignedDecimal("60841441341419381047595034241085"))
        self.assertEqual(LRR.token_x_cumulative_earned_per_m_liq, UnsignedDecimal("3189508411491199598333431314"))
        self.assertEqual(RLL.token_x_cumulative_earned_per_m_liq, UnsignedDecimal("657996725303326136999"))
        self.assertEqual(RLR.token_x_cumulative_earned_per_m_liq, UnsignedDecimal("223727062042489"))
        self.assertEqual(RRL.token_x_cumulative_earned_per_m_liq, UnsignedDecimal("29115133709213782165"))
        self.assertEqual(RRR.token_x_cumulative_earned_per_m_liq, UnsignedDecimal("3856709189487099165901"))

        self.assertEqual(LLLL.token_x_cumulative_earned_per_m_liq, UnsignedDecimal("889700619080860150"))
        self.assertEqual(LLLR.token_x_cumulative_earned_per_m_liq, UnsignedDecimal("30393719776417661690"))
        self.assertEqual(LLRL.token_x_cumulative_earned_per_m_liq, UnsignedDecimal("159213596840619244523447699163"))
        self.assertEqual(LLRR.token_x_cumulative_earned_per_m_liq, UnsignedDecimal("0"))
        self.assertEqual(LRLL.token_x_cumulative_earned_per_m_liq, UnsignedDecimal("1051376974879620344655023882438"))
        self.assertEqual(LRLR.token_x_cumulative_earned_per_m_liq, UnsignedDecimal("0"))
        self.assertEqual(LRRL.token_x_cumulative_earned_per_m_liq, UnsignedDecimal("1537891441852978794"))
        self.assertEqual(LRRR.token_x_cumulative_earned_per_m_liq, UnsignedDecimal("0"))
        self.assertEqual(RLLL.token_x_cumulative_earned_per_m_liq, UnsignedDecimal("31935758833446278128768039723"))
        self.assertEqual(RLLR.token_x_cumulative_earned_per_m_liq, UnsignedDecimal("0"))
        self.assertEqual(RLRL.token_x_cumulative_earned_per_m_liq, UnsignedDecimal("236616939696375723"))
        self.assertEqual(RLRR.token_x_cumulative_earned_per_m_liq, UnsignedDecimal("0"))
        self.assertEqual(RRLL.token_x_cumulative_earned_per_m_liq, UnsignedDecimal("5767677373168060851383"))
        self.assertEqual(RRLR.token_x_cumulative_earned_per_m_liq, UnsignedDecimal("0"))
        self.assertEqual(RRRL.token_x_cumulative_earned_per_m_liq, UnsignedDecimal("6665049232753208950"))
        self.assertEqual(RRRR.token_x_cumulative_earned_per_m_liq, UnsignedDecimal("0"))

        # token_x_cumulative_earned_per_m_subtree_liq
        self.assertEqual(root.token_x_cumulative_earned_per_m_subtree_liq, UnsignedDecimal("43756288901278965565289120"))

        self.assertEqual(L.token_x_cumulative_earned_per_m_subtree_liq, UnsignedDecimal("114172069341113006721615069516"))
        self.assertEqual(R.token_x_cumulative_earned_per_m_subtree_liq, UnsignedDecimal("923073628282275460400546"))

        self.assertEqual(LL.token_x_cumulative_earned_per_m_subtree_liq, UnsignedDecimal("126975792932608136142575516378"))
        self.assertEqual(LR.token_x_cumulative_earned_per_m_subtree_liq, UnsignedDecimal("14689030881642935495954673055"))
        self.assertEqual(RL.token_x_cumulative_earned_per_m_subtree_liq, UnsignedDecimal("1077791623755590749427001"))
        self.assertEqual(RR.token_x_cumulative_earned_per_m_subtree_liq, UnsignedDecimal("3744954689799430215251"))

        self.assertEqual(LLL.token_x_cumulative_earned_per_m_subtree_liq, UnsignedDecimal("2556777231614922263512088"))
        self.assertEqual(LLR.token_x_cumulative_earned_per_m_subtree_liq, UnsignedDecimal("2945529310733483531304171330809"))
        self.assertEqual(LRL.token_x_cumulative_earned_per_m_subtree_liq, UnsignedDecimal("61367157725965120112844741263941"))
        self.assertEqual(LRR.token_x_cumulative_earned_per_m_subtree_liq, UnsignedDecimal("3189508511506300233910914258"))
        self.assertEqual(RLL.token_x_cumulative_earned_per_m_subtree_liq, UnsignedDecimal("1443549229249734665667944"))
        self.assertEqual(RLR.token_x_cumulative_earned_per_m_subtree_liq, UnsignedDecimal("23244332771593818172928"))
        self.assertEqual(RRL.token_x_cumulative_earned_per_m_subtree_liq, UnsignedDecimal("2914154110846149087494"))
        self.assertEqual(RRR.token_x_cumulative_earned_per_m_subtree_liq, UnsignedDecimal("3860046994395227474433"))

        self.assertEqual(LLLL.token_x_cumulative_earned_per_m_subtree_liq, UnsignedDecimal("889700619080860150"))
        self.assertEqual(LLLR.token_x_cumulative_earned_per_m_subtree_liq, UnsignedDecimal("30393719776417661690"))
        self.assertEqual(LLRL.token_x_cumulative_earned_per_m_subtree_liq, UnsignedDecimal("159213596840619244523447699163"))
        self.assertEqual(LLRR.token_x_cumulative_earned_per_m_subtree_liq, UnsignedDecimal("0"))
        self.assertEqual(LRLL.token_x_cumulative_earned_per_m_subtree_liq, UnsignedDecimal("1051376974879620344655023882438"))
        self.assertEqual(LRLR.token_x_cumulative_earned_per_m_subtree_liq, UnsignedDecimal("0"))
        self.assertEqual(LRRL.token_x_cumulative_earned_per_m_subtree_liq, UnsignedDecimal("1537891441852978794"))
        self.assertEqual(LRRR.token_x_cumulative_earned_per_m_subtree_liq, UnsignedDecimal("0"))
        self.assertEqual(RLLL.token_x_cumulative_earned_per_m_subtree_liq, UnsignedDecimal("31935758833446278128768039723"))
        self.assertEqual(RLLR.token_x_cumulative_earned_per_m_subtree_liq, UnsignedDecimal("0"))
        self.assertEqual(RLRL.token_x_cumulative_earned_per_m_subtree_liq, UnsignedDecimal("236616939696375723"))
        self.assertEqual(RLRR.token_x_cumulative_earned_per_m_subtree_liq, UnsignedDecimal("0"))
        self.assertEqual(RRLL.token_x_cumulative_earned_per_m_subtree_liq, UnsignedDecimal("5767677373168060851383"))
        self.assertEqual(RRLR.token_x_cumulative_earned_per_m_subtree_liq, UnsignedDecimal("0"))
        self.assertEqual(RRRL.token_x_cumulative_earned_per_m_subtree_liq, UnsignedDecimal("6665049232753208950"))
        self.assertEqual(RRRR.token_x_cumulative_earned_per_m_subtree_liq, UnsignedDecimal("0"))

        # token_y_cumulative_earned_per_m_liq
        self.assertEqual(root.token_y_cumulative_earned_per_m_liq, UnsignedDecimal("0"))

        self.assertEqual(L.token_y_cumulative_earned_per_m_liq, UnsignedDecimal("82"))
        self.assertEqual(R.token_y_cumulative_earned_per_m_liq, UnsignedDecimal("0"))

        self.assertEqual(LL.token_y_cumulative_earned_per_m_liq, UnsignedDecimal("670"))
        self.assertEqual(LR.token_y_cumulative_earned_per_m_liq, UnsignedDecimal("39"))
        self.assertEqual(RL.token_y_cumulative_earned_per_m_liq, UnsignedDecimal("197"))
        self.assertEqual(RR.token_y_cumulative_earned_per_m_liq, UnsignedDecimal("9"))

        self.assertEqual(LLL.token_y_cumulative_earned_per_m_liq, UnsignedDecimal("4747990803139"))
        self.assertEqual(LLR.token_y_cumulative_earned_per_m_liq, UnsignedDecimal("41865270006"))
        self.assertEqual(LRL.token_y_cumulative_earned_per_m_liq, UnsignedDecimal("1224894367084578"))
        self.assertEqual(LRR.token_y_cumulative_earned_per_m_liq, UnsignedDecimal("31703181193601"))
        self.assertEqual(RLL.token_y_cumulative_earned_per_m_liq, UnsignedDecimal("2679359"))
        self.assertEqual(RLR.token_y_cumulative_earned_per_m_liq, UnsignedDecimal("77430742"))
        self.assertEqual(RRL.token_y_cumulative_earned_per_m_liq, UnsignedDecimal("826996583538488"))
        self.assertEqual(RRR.token_y_cumulative_earned_per_m_liq, UnsignedDecimal("13459135450531"))

        self.assertEqual(LLLL.token_y_cumulative_earned_per_m_liq, UnsignedDecimal("109425756"))
        self.assertEqual(LLLR.token_y_cumulative_earned_per_m_liq, UnsignedDecimal("22774163335023745"))
        self.assertEqual(LLRL.token_y_cumulative_earned_per_m_liq, UnsignedDecimal("14266182294798018313"))
        self.assertEqual(LLRR.token_y_cumulative_earned_per_m_liq, UnsignedDecimal("0"))
        self.assertEqual(LRLL.token_y_cumulative_earned_per_m_liq, UnsignedDecimal("42518327403210687"))
        self.assertEqual(LRLR.token_y_cumulative_earned_per_m_liq, UnsignedDecimal("0"))
        self.assertEqual(LRRL.token_y_cumulative_earned_per_m_liq, UnsignedDecimal("37701268286368"))
        self.assertEqual(LRRR.token_y_cumulative_earned_per_m_liq, UnsignedDecimal("0"))
        self.assertEqual(RLLL.token_y_cumulative_earned_per_m_liq, UnsignedDecimal("452159061"))
        self.assertEqual(RLLR.token_y_cumulative_earned_per_m_liq, UnsignedDecimal("0"))
        self.assertEqual(RLRL.token_y_cumulative_earned_per_m_liq, UnsignedDecimal("6488"))
        self.assertEqual(RLRR.token_y_cumulative_earned_per_m_liq, UnsignedDecimal("0"))
        self.assertEqual(RRLL.token_y_cumulative_earned_per_m_liq, UnsignedDecimal("1453692415004"))
        self.assertEqual(RRLR.token_y_cumulative_earned_per_m_liq, UnsignedDecimal("0"))
        self.assertEqual(RRRL.token_y_cumulative_earned_per_m_liq, UnsignedDecimal("9695"))
        self.assertEqual(RRRR.token_y_cumulative_earned_per_m_liq, UnsignedDecimal("0"))

        # token_y_cumulative_earned_per_m_subtree_liq
        self.assertEqual(root.token_y_cumulative_earned_per_m_subtree_liq, UnsignedDecimal("20976473812693"))

        self.assertEqual(L.token_y_cumulative_earned_per_m_subtree_liq, UnsignedDecimal("12697937271018899"))
        self.assertEqual(R.token_y_cumulative_earned_per_m_subtree_liq, UnsignedDecimal("16218714968180"))

        self.assertEqual(LL.token_y_cumulative_earned_per_m_subtree_liq, UnsignedDecimal("14323023895032874"))
        self.assertEqual(LR.token_y_cumulative_earned_per_m_subtree_liq, UnsignedDecimal("71254575045205"))
        self.assertEqual(RL.token_y_cumulative_earned_per_m_subtree_liq, UnsignedDecimal("189479572"))
        self.assertEqual(RR.token_y_cumulative_earned_per_m_subtree_liq, UnsignedDecimal("112588600574925"))

        self.assertEqual(LLL.token_y_cumulative_earned_per_m_subtree_liq, UnsignedDecimal("14552811706670570"))
        self.assertEqual(LLR.token_y_cumulative_earned_per_m_subtree_liq, UnsignedDecimal("9222191117511089"))
        self.assertEqual(LRL.token_y_cumulative_earned_per_m_subtree_liq, UnsignedDecimal("22674390484203729"))
        self.assertEqual(LRR.token_y_cumulative_earned_per_m_subtree_liq, UnsignedDecimal("67017984988846"))
        self.assertEqual(RLL.token_y_cumulative_earned_per_m_subtree_liq, UnsignedDecimal("2936467"))
        self.assertEqual(RLR.token_y_cumulative_earned_per_m_subtree_liq, UnsignedDecimal("727317315"))
        self.assertEqual(RRL.token_y_cumulative_earned_per_m_subtree_liq, UnsignedDecimal("827723734665148"))
        self.assertEqual(RRR.token_y_cumulative_earned_per_m_subtree_liq, UnsignedDecimal("13459135488203"))

        self.assertEqual(LLLL.token_y_cumulative_earned_per_m_subtree_liq, UnsignedDecimal("109425756"))
        self.assertEqual(LLLR.token_y_cumulative_earned_per_m_subtree_liq, UnsignedDecimal("22774163335023745"))
        self.assertEqual(LLRL.token_y_cumulative_earned_per_m_subtree_liq, UnsignedDecimal("14266182294798018313"))
        self.assertEqual(LLRR.token_y_cumulative_earned_per_m_subtree_liq, UnsignedDecimal("0"))
        self.assertEqual(LRLL.token_y_cumulative_earned_per_m_subtree_liq, UnsignedDecimal("42518327403210687"))
        self.assertEqual(LRLR.token_y_cumulative_earned_per_m_subtree_liq, UnsignedDecimal("0"))
        self.assertEqual(LRRL.token_y_cumulative_earned_per_m_subtree_liq, UnsignedDecimal("37701268286368"))
        self.assertEqual(LRRR.token_y_cumulative_earned_per_m_subtree_liq, UnsignedDecimal("0"))
        self.assertEqual(RLLL.token_y_cumulative_earned_per_m_subtree_liq, UnsignedDecimal("452159061"))
        self.assertEqual(RLLR.token_y_cumulative_earned_per_m_subtree_liq, UnsignedDecimal("0"))
        self.assertEqual(RLRL.token_y_cumulative_earned_per_m_subtree_liq, UnsignedDecimal("6488"))
        self.assertEqual(RLRR.token_y_cumulative_earned_per_m_subtree_liq, UnsignedDecimal("0"))
        self.assertEqual(RRLL.token_y_cumulative_earned_per_m_subtree_liq, UnsignedDecimal("1453692415004"))
        self.assertEqual(RRLR.token_y_cumulative_earned_per_m_subtree_liq, UnsignedDecimal("0"))
        self.assertEqual(RRRL.token_y_cumulative_earned_per_m_subtree_liq, UnsignedDecimal("9695"))
        self.assertEqual(RRRR.token_y_cumulative_earned_per_m_subtree_liq, UnsignedDecimal("0"))

        return

        # # region Ranges that start with 2 -------------------------------------------------------------------------------------
        # # LiqRange(2, 2)
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.add_m_liq(UnsignedDecimal("0"))
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.remove_m_liq(UnsignedDecimal("0"))
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.add_t_liq(UnsignedDecimal("0"), UnsignedDecimal("0"))
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.remove_t_liq(UnsignedDecimal("0"), UnsignedDecimal("0"))
        #
        # # LiqRange(2, 3)
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.add_m_liq(UnsignedDecimal("0"))
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.remove_m_liq(UnsignedDecimal("0"))
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.add_t_liq(UnsignedDecimal("0"), UnsignedDecimal("0"))
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.remove_t_liq(UnsignedDecimal("0"), UnsignedDecimal("0"))
        #
        # # LiqRange(2, 4)
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.add_m_liq(UnsignedDecimal("0"))
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.remove_m_liq(UnsignedDecimal("0"))
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.add_t_liq(UnsignedDecimal("0"), UnsignedDecimal("0"))
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.remove_t_liq(UnsignedDecimal("0"), UnsignedDecimal("0"))
        #
        # # LiqRange(2, 5)
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.add_m_liq(UnsignedDecimal("0"))
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.remove_m_liq(UnsignedDecimal("0"))
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.add_t_liq(UnsignedDecimal("0"), UnsignedDecimal("0"))
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.remove_t_liq(UnsignedDecimal("0"), UnsignedDecimal("0"))
        #
        # # LiqRange(2, 6)
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.add_m_liq(UnsignedDecimal("0"))
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.remove_m_liq(UnsignedDecimal("0"))
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.add_t_liq(UnsignedDecimal("0"), UnsignedDecimal("0"))
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.remove_t_liq(UnsignedDecimal("0"), UnsignedDecimal("0"))
        #
        # # LiqRange(2, 7)
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.add_m_liq(UnsignedDecimal("0"))
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.remove_m_liq(UnsignedDecimal("0"))
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.add_t_liq(UnsignedDecimal("0"), UnsignedDecimal("0"))
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.remove_t_liq(UnsignedDecimal("0"), UnsignedDecimal("0"))
        #
        # # LiqRange(2, 8)
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.add_m_liq(UnsignedDecimal("0"))
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.remove_m_liq(UnsignedDecimal("0"))
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.add_t_liq(UnsignedDecimal("0"), UnsignedDecimal("0"))
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.remove_t_liq(UnsignedDecimal("0"), UnsignedDecimal("0"))
        #
        # # LiqRange(2, 9)
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.add_m_liq(UnsignedDecimal("0"))
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.remove_m_liq(UnsignedDecimal("0"))
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.add_t_liq(UnsignedDecimal("0"), UnsignedDecimal("0"))
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.remove_t_liq(UnsignedDecimal("0"), UnsignedDecimal("0"))
        #
        # # LiqRange(2, 10)
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.add_m_liq(UnsignedDecimal("0"))
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.remove_m_liq(UnsignedDecimal("0"))
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.add_t_liq(UnsignedDecimal("0"), UnsignedDecimal("0"))
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.remove_t_liq(UnsignedDecimal("0"), UnsignedDecimal("0"))
        #
        # # LiqRange(2, 11)
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.add_m_liq(UnsignedDecimal("0"))
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.remove_m_liq(UnsignedDecimal("0"))
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.add_t_liq(UnsignedDecimal("0"), UnsignedDecimal("0"))
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.remove_t_liq(UnsignedDecimal("0"), UnsignedDecimal("0"))
        #
        # # LiqRange(2, 12)
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.add_m_liq(UnsignedDecimal("0"))
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.remove_m_liq(UnsignedDecimal("0"))
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.add_t_liq(UnsignedDecimal("0"), UnsignedDecimal("0"))
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.remove_t_liq(UnsignedDecimal("0"), UnsignedDecimal("0"))
        #
        # # LiqRange(2, 13)
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.add_m_liq(UnsignedDecimal("0"))
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.remove_m_liq(UnsignedDecimal("0"))
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.add_t_liq(UnsignedDecimal("0"), UnsignedDecimal("0"))
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.remove_t_liq(UnsignedDecimal("0"), UnsignedDecimal("0"))
        #
        # # LiqRange(2, 14)
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.add_m_liq(UnsignedDecimal("0"))
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.remove_m_liq(UnsignedDecimal("0"))
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.add_t_liq(UnsignedDecimal("0"), UnsignedDecimal("0"))
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.remove_t_liq(UnsignedDecimal("0"), UnsignedDecimal("0"))
        #
        # # LiqRange(2, 15)
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.add_m_liq(UnsignedDecimal("0"))
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.remove_m_liq(UnsignedDecimal("0"))
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.add_t_liq(UnsignedDecimal("0"), UnsignedDecimal("0"))
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.remove_t_liq(UnsignedDecimal("0"), UnsignedDecimal("0"))
        #
        # #endregion
        #
        # # region Ranges that start with 3 -------------------------------------------------------------------------------------
        # # LiqRange(3, 3)
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.add_m_liq(UnsignedDecimal("0"))
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.remove_m_liq(UnsignedDecimal("0"))
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.add_t_liq(UnsignedDecimal("0"), UnsignedDecimal("0"))
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.remove_t_liq(UnsignedDecimal("0"), UnsignedDecimal("0"))
        #
        # # LiqRange(3, 4)
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.add_m_liq(UnsignedDecimal("0"))
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.remove_m_liq(UnsignedDecimal("0"))
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.add_t_liq(UnsignedDecimal("0"), UnsignedDecimal("0"))
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.remove_t_liq(UnsignedDecimal("0"), UnsignedDecimal("0"))
        #
        # # LiqRange(3, 5)
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.add_m_liq(UnsignedDecimal("0"))
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.remove_m_liq(UnsignedDecimal("0"))
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.add_t_liq(UnsignedDecimal("0"), UnsignedDecimal("0"))
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.remove_t_liq(UnsignedDecimal("0"), UnsignedDecimal("0"))
        #
        # # LiqRange(3, 6)
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.add_m_liq(UnsignedDecimal("0"))
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.remove_m_liq(UnsignedDecimal("0"))
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.add_t_liq(UnsignedDecimal("0"), UnsignedDecimal("0"))
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.remove_t_liq(UnsignedDecimal("0"), UnsignedDecimal("0"))
        #
        # # LiqRange(3, 7)
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.add_m_liq(UnsignedDecimal("0"))
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.remove_m_liq(UnsignedDecimal("0"))
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.add_t_liq(UnsignedDecimal("0"), UnsignedDecimal("0"))
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.remove_t_liq(UnsignedDecimal("0"), UnsignedDecimal("0"))
        #
        # # LiqRange(3, 8)
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.add_m_liq(UnsignedDecimal("0"))
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.remove_m_liq(UnsignedDecimal("0"))
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.add_t_liq(UnsignedDecimal("0"), UnsignedDecimal("0"))
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.remove_t_liq(UnsignedDecimal("0"), UnsignedDecimal("0"))
        #
        # # LiqRange(3, 9)
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.add_m_liq(UnsignedDecimal("0"))
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.remove_m_liq(UnsignedDecimal("0"))
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.add_t_liq(UnsignedDecimal("0"), UnsignedDecimal("0"))
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.remove_t_liq(UnsignedDecimal("0"), UnsignedDecimal("0"))
        #
        # # LiqRange(3, 10)
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.add_m_liq(UnsignedDecimal("0"))
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.remove_m_liq(UnsignedDecimal("0"))
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.add_t_liq(UnsignedDecimal("0"), UnsignedDecimal("0"))
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.remove_t_liq(UnsignedDecimal("0"), UnsignedDecimal("0"))
        #
        # # LiqRange(3, 11)
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.add_m_liq(UnsignedDecimal("0"))
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.remove_m_liq(UnsignedDecimal("0"))
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.add_t_liq(UnsignedDecimal("0"), UnsignedDecimal("0"))
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.remove_t_liq(UnsignedDecimal("0"), UnsignedDecimal("0"))
        #
        # # LiqRange(3, 12)
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.add_m_liq(UnsignedDecimal("0"))
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.remove_m_liq(UnsignedDecimal("0"))
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.add_t_liq(UnsignedDecimal("0"), UnsignedDecimal("0"))
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.remove_t_liq(UnsignedDecimal("0"), UnsignedDecimal("0"))
        #
        # # LiqRange(3, 13)
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.add_m_liq(UnsignedDecimal("0"))
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.remove_m_liq(UnsignedDecimal("0"))
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.add_t_liq(UnsignedDecimal("0"), UnsignedDecimal("0"))
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.remove_t_liq(UnsignedDecimal("0"), UnsignedDecimal("0"))
        #
        # # LiqRange(3, 14)
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.add_m_liq(UnsignedDecimal("0"))
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.remove_m_liq(UnsignedDecimal("0"))
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.add_t_liq(UnsignedDecimal("0"), UnsignedDecimal("0"))
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.remove_t_liq(UnsignedDecimal("0"), UnsignedDecimal("0"))
        #
        # # LiqRange(3, 15)
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.add_m_liq(UnsignedDecimal("0"))
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.remove_m_liq(UnsignedDecimal("0"))
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.add_t_liq(UnsignedDecimal("0"), UnsignedDecimal("0"))
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.remove_t_liq(UnsignedDecimal("0"), UnsignedDecimal("0"))
        #
        # #endregion
        #
        # # region Ranges that start with 4 -------------------------------------------------------------------------------------
        # # LiqRange(4, 4)
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.add_m_liq(UnsignedDecimal("0"))
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.remove_m_liq(UnsignedDecimal("0"))
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.add_t_liq(UnsignedDecimal("0"), UnsignedDecimal("0"))
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.remove_t_liq(UnsignedDecimal("0"), UnsignedDecimal("0"))
        #
        # # LiqRange(4, 5)
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.add_m_liq(UnsignedDecimal("0"))
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.remove_m_liq(UnsignedDecimal("0"))
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.add_t_liq(UnsignedDecimal("0"), UnsignedDecimal("0"))
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.remove_t_liq(UnsignedDecimal("0"), UnsignedDecimal("0"))
        #
        # # LiqRange(4, 6)
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.add_m_liq(UnsignedDecimal("0"))
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.remove_m_liq(UnsignedDecimal("0"))
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.add_t_liq(UnsignedDecimal("0"), UnsignedDecimal("0"))
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.remove_t_liq(UnsignedDecimal("0"), UnsignedDecimal("0"))
        #
        # # LiqRange(4, 7)
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.add_m_liq(UnsignedDecimal("0"))
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.remove_m_liq(UnsignedDecimal("0"))
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.add_t_liq(UnsignedDecimal("0"), UnsignedDecimal("0"))
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.remove_t_liq(UnsignedDecimal("0"), UnsignedDecimal("0"))
        #
        # # LiqRange(4, 8)
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.add_m_liq(UnsignedDecimal("0"))
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.remove_m_liq(UnsignedDecimal("0"))
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.add_t_liq(UnsignedDecimal("0"), UnsignedDecimal("0"))
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.remove_t_liq(UnsignedDecimal("0"), UnsignedDecimal("0"))
        #
        # # LiqRange(4, 9)
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.add_m_liq(UnsignedDecimal("0"))
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.remove_m_liq(UnsignedDecimal("0"))
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.add_t_liq(UnsignedDecimal("0"), UnsignedDecimal("0"))
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.remove_t_liq(UnsignedDecimal("0"), UnsignedDecimal("0"))
        #
        # # LiqRange(4, 10)
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.add_m_liq(UnsignedDecimal("0"))
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.remove_m_liq(UnsignedDecimal("0"))
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.add_t_liq(UnsignedDecimal("0"), UnsignedDecimal("0"))
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.remove_t_liq(UnsignedDecimal("0"), UnsignedDecimal("0"))
        #
        # # LiqRange(4, 11)
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.add_m_liq(UnsignedDecimal("0"))
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.remove_m_liq(UnsignedDecimal("0"))
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.add_t_liq(UnsignedDecimal("0"), UnsignedDecimal("0"))
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.remove_t_liq(UnsignedDecimal("0"), UnsignedDecimal("0"))
        #
        # # LiqRange(4, 12)
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.add_m_liq(UnsignedDecimal("0"))
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.remove_m_liq(UnsignedDecimal("0"))
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.add_t_liq(UnsignedDecimal("0"), UnsignedDecimal("0"))
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.remove_t_liq(UnsignedDecimal("0"), UnsignedDecimal("0"))
        #
        # # LiqRange(4, 13)
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.add_m_liq(UnsignedDecimal("0"))
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.remove_m_liq(UnsignedDecimal("0"))
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.add_t_liq(UnsignedDecimal("0"), UnsignedDecimal("0"))
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.remove_t_liq(UnsignedDecimal("0"), UnsignedDecimal("0"))
        #
        # # LiqRange(4, 14)
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.add_m_liq(UnsignedDecimal("0"))
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.remove_m_liq(UnsignedDecimal("0"))
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.add_t_liq(UnsignedDecimal("0"), UnsignedDecimal("0"))
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.remove_t_liq(UnsignedDecimal("0"), UnsignedDecimal("0"))
        #
        # # LiqRange(4, 15)
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.add_m_liq(UnsignedDecimal("0"))
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.remove_m_liq(UnsignedDecimal("0"))
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.add_t_liq(UnsignedDecimal("0"), UnsignedDecimal("0"))
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.remove_t_liq(UnsignedDecimal("0"), UnsignedDecimal("0"))
        #
        # #endregion
        #
        # # region Ranges that start with 5 -------------------------------------------------------------------------------------
        # # LiqRange(5, 5)
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.add_m_liq(UnsignedDecimal("0"))
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.remove_m_liq(UnsignedDecimal("0"))
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.add_t_liq(UnsignedDecimal("0"), UnsignedDecimal("0"))
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.remove_t_liq(UnsignedDecimal("0"), UnsignedDecimal("0"))
        #
        # # LiqRange(5, 6)
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.add_m_liq(UnsignedDecimal("0"))
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.remove_m_liq(UnsignedDecimal("0"))
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.add_t_liq(UnsignedDecimal("0"), UnsignedDecimal("0"))
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.remove_t_liq(UnsignedDecimal("0"), UnsignedDecimal("0"))
        #
        # # LiqRange(5, 7)
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.add_m_liq(UnsignedDecimal("0"))
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.remove_m_liq(UnsignedDecimal("0"))
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.add_t_liq(UnsignedDecimal("0"), UnsignedDecimal("0"))
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.remove_t_liq(UnsignedDecimal("0"), UnsignedDecimal("0"))
        #
        # # LiqRange(5, 8)
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.add_m_liq(UnsignedDecimal("0"))
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.remove_m_liq(UnsignedDecimal("0"))
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.add_t_liq(UnsignedDecimal("0"), UnsignedDecimal("0"))
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.remove_t_liq(UnsignedDecimal("0"), UnsignedDecimal("0"))
        #
        # # LiqRange(5, 9)
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.add_m_liq(UnsignedDecimal("0"))
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.remove_m_liq(UnsignedDecimal("0"))
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.add_t_liq(UnsignedDecimal("0"), UnsignedDecimal("0"))
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.remove_t_liq(UnsignedDecimal("0"), UnsignedDecimal("0"))
        #
        # # LiqRange(5, 10)
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.add_m_liq(UnsignedDecimal("0"))
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.remove_m_liq(UnsignedDecimal("0"))
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.add_t_liq(UnsignedDecimal("0"), UnsignedDecimal("0"))
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.remove_t_liq(UnsignedDecimal("0"), UnsignedDecimal("0"))
        #
        # # LiqRange(5, 11)
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.add_m_liq(UnsignedDecimal("0"))
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.remove_m_liq(UnsignedDecimal("0"))
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.add_t_liq(UnsignedDecimal("0"), UnsignedDecimal("0"))
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.remove_t_liq(UnsignedDecimal("0"), UnsignedDecimal("0"))
        #
        # # LiqRange(5, 12)
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.add_m_liq(UnsignedDecimal("0"))
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.remove_m_liq(UnsignedDecimal("0"))
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.add_t_liq(UnsignedDecimal("0"), UnsignedDecimal("0"))
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.remove_t_liq(UnsignedDecimal("0"), UnsignedDecimal("0"))
        #
        # # LiqRange(5, 13)
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.add_m_liq(UnsignedDecimal("0"))
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.remove_m_liq(UnsignedDecimal("0"))
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.add_t_liq(UnsignedDecimal("0"), UnsignedDecimal("0"))
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.remove_t_liq(UnsignedDecimal("0"), UnsignedDecimal("0"))
        #
        # # LiqRange(5, 14)
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.add_m_liq(UnsignedDecimal("0"))
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.remove_m_liq(UnsignedDecimal("0"))
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.add_t_liq(UnsignedDecimal("0"), UnsignedDecimal("0"))
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.remove_t_liq(UnsignedDecimal("0"), UnsignedDecimal("0"))
        #
        # # LiqRange(5, 15)
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.add_m_liq(UnsignedDecimal("0"))
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.remove_m_liq(UnsignedDecimal("0"))
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.add_t_liq(UnsignedDecimal("0"), UnsignedDecimal("0"))
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.remove_t_liq(UnsignedDecimal("0"), UnsignedDecimal("0"))
        #
        # #endregion
        #
        # # region Ranges that start with 6 -------------------------------------------------------------------------------------
        # # LiqRange(6, 6)
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.add_m_liq(UnsignedDecimal("0"))
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.remove_m_liq(UnsignedDecimal("0"))
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.add_t_liq(UnsignedDecimal("0"), UnsignedDecimal("0"))
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.remove_t_liq(UnsignedDecimal("0"), UnsignedDecimal("0"))
        #
        # # LiqRange(6, 7)
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.add_m_liq(UnsignedDecimal("0"))
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.remove_m_liq(UnsignedDecimal("0"))
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.add_t_liq(UnsignedDecimal("0"), UnsignedDecimal("0"))
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.remove_t_liq(UnsignedDecimal("0"), UnsignedDecimal("0"))
        #
        # # LiqRange(6, 8)
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.add_m_liq(UnsignedDecimal("0"))
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.remove_m_liq(UnsignedDecimal("0"))
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.add_t_liq(UnsignedDecimal("0"), UnsignedDecimal("0"))
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.remove_t_liq(UnsignedDecimal("0"), UnsignedDecimal("0"))
        #
        # # LiqRange(6, 9)
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.add_m_liq(UnsignedDecimal("0"))
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.remove_m_liq(UnsignedDecimal("0"))
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.add_t_liq(UnsignedDecimal("0"), UnsignedDecimal("0"))
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.remove_t_liq(UnsignedDecimal("0"), UnsignedDecimal("0"))
        #
        # # LiqRange(6, 10)
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.add_m_liq(UnsignedDecimal("0"))
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.remove_m_liq(UnsignedDecimal("0"))
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.add_t_liq(UnsignedDecimal("0"), UnsignedDecimal("0"))
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.remove_t_liq(UnsignedDecimal("0"), UnsignedDecimal("0"))
        #
        # # LiqRange(6, 11)
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.add_m_liq(UnsignedDecimal("0"))
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.remove_m_liq(UnsignedDecimal("0"))
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.add_t_liq(UnsignedDecimal("0"), UnsignedDecimal("0"))
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.remove_t_liq(UnsignedDecimal("0"), UnsignedDecimal("0"))
        #
        # # LiqRange(6, 12)
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.add_m_liq(UnsignedDecimal("0"))
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.remove_m_liq(UnsignedDecimal("0"))
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.add_t_liq(UnsignedDecimal("0"), UnsignedDecimal("0"))
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.remove_t_liq(UnsignedDecimal("0"), UnsignedDecimal("0"))
        #
        # # LiqRange(6, 13)
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.add_m_liq(UnsignedDecimal("0"))
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.remove_m_liq(UnsignedDecimal("0"))
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.add_t_liq(UnsignedDecimal("0"), UnsignedDecimal("0"))
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.remove_t_liq(UnsignedDecimal("0"), UnsignedDecimal("0"))
        #
        # # LiqRange(6, 14)
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.add_m_liq(UnsignedDecimal("0"))
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.remove_m_liq(UnsignedDecimal("0"))
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.add_t_liq(UnsignedDecimal("0"), UnsignedDecimal("0"))
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.remove_t_liq(UnsignedDecimal("0"), UnsignedDecimal("0"))
        #
        # # LiqRange(6, 15)
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.add_m_liq(UnsignedDecimal("0"))
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.remove_m_liq(UnsignedDecimal("0"))
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.add_t_liq(UnsignedDecimal("0"), UnsignedDecimal("0"))
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.remove_t_liq(UnsignedDecimal("0"), UnsignedDecimal("0"))
        #
        # #endregion
        #
        # # region Ranges that start with 7 -------------------------------------------------------------------------------------
        # # LiqRange(7, 7)
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.add_m_liq(UnsignedDecimal("0"))
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.remove_m_liq(UnsignedDecimal("0"))
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.add_t_liq(UnsignedDecimal("0"), UnsignedDecimal("0"))
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.remove_t_liq(UnsignedDecimal("0"), UnsignedDecimal("0"))
        #
        # # LiqRange(7, 8)
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.add_m_liq(UnsignedDecimal("0"))
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.remove_m_liq(UnsignedDecimal("0"))
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.add_t_liq(UnsignedDecimal("0"), UnsignedDecimal("0"))
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.remove_t_liq(UnsignedDecimal("0"), UnsignedDecimal("0"))
        #
        # # LiqRange(7, 9)
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.add_m_liq(UnsignedDecimal("0"))
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.remove_m_liq(UnsignedDecimal("0"))
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.add_t_liq(UnsignedDecimal("0"), UnsignedDecimal("0"))
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.remove_t_liq(UnsignedDecimal("0"), UnsignedDecimal("0"))
        #
        # # LiqRange(7, 10)
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.add_m_liq(UnsignedDecimal("0"))
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.remove_m_liq(UnsignedDecimal("0"))
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.add_t_liq(UnsignedDecimal("0"), UnsignedDecimal("0"))
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.remove_t_liq(UnsignedDecimal("0"), UnsignedDecimal("0"))
        #
        # # LiqRange(7, 11)
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.add_m_liq(UnsignedDecimal("0"))
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.remove_m_liq(UnsignedDecimal("0"))
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.add_t_liq(UnsignedDecimal("0"), UnsignedDecimal("0"))
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.remove_t_liq(UnsignedDecimal("0"), UnsignedDecimal("0"))
        #
        # # LiqRange(7, 12)
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.add_m_liq(UnsignedDecimal("0"))
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.remove_m_liq(UnsignedDecimal("0"))
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.add_t_liq(UnsignedDecimal("0"), UnsignedDecimal("0"))
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.remove_t_liq(UnsignedDecimal("0"), UnsignedDecimal("0"))
        #
        # # LiqRange(7, 13)
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.add_m_liq(UnsignedDecimal("0"))
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.remove_m_liq(UnsignedDecimal("0"))
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.add_t_liq(UnsignedDecimal("0"), UnsignedDecimal("0"))
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.remove_t_liq(UnsignedDecimal("0"), UnsignedDecimal("0"))
        #
        # # LiqRange(7, 14)
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.add_m_liq(UnsignedDecimal("0"))
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.remove_m_liq(UnsignedDecimal("0"))
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.add_t_liq(UnsignedDecimal("0"), UnsignedDecimal("0"))
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.remove_t_liq(UnsignedDecimal("0"), UnsignedDecimal("0"))
        #
        # # LiqRange(7, 15)
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.add_m_liq(UnsignedDecimal("0"))
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.remove_m_liq(UnsignedDecimal("0"))
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.add_t_liq(UnsignedDecimal("0"), UnsignedDecimal("0"))
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.remove_t_liq(UnsignedDecimal("0"), UnsignedDecimal("0"))
        #
        # #endregion
        #
        # # region Ranges that start with 8 -------------------------------------------------------------------------------------
        # # LiqRange(8, 8)
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.add_m_liq(UnsignedDecimal("0"))
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.remove_m_liq(UnsignedDecimal("0"))
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.add_t_liq(UnsignedDecimal("0"), UnsignedDecimal("0"))
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.remove_t_liq(UnsignedDecimal("0"), UnsignedDecimal("0"))
        #
        # # LiqRange(8, 9)
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.add_m_liq(UnsignedDecimal("0"))
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.remove_m_liq(UnsignedDecimal("0"))
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.add_t_liq(UnsignedDecimal("0"), UnsignedDecimal("0"))
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.remove_t_liq(UnsignedDecimal("0"), UnsignedDecimal("0"))
        #
        # # LiqRange(8, 10)
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.add_m_liq(UnsignedDecimal("0"))
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.remove_m_liq(UnsignedDecimal("0"))
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.add_t_liq(UnsignedDecimal("0"), UnsignedDecimal("0"))
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.remove_t_liq(UnsignedDecimal("0"), UnsignedDecimal("0"))
        #
        # # LiqRange(8, 11)
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.add_m_liq(UnsignedDecimal("0"))
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.remove_m_liq(UnsignedDecimal("0"))
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.add_t_liq(UnsignedDecimal("0"), UnsignedDecimal("0"))
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.remove_t_liq(UnsignedDecimal("0"), UnsignedDecimal("0"))
        #
        # # LiqRange(8, 12)
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.add_m_liq(UnsignedDecimal("0"))
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.remove_m_liq(UnsignedDecimal("0"))
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.add_t_liq(UnsignedDecimal("0"), UnsignedDecimal("0"))
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.remove_t_liq(UnsignedDecimal("0"), UnsignedDecimal("0"))
        #
        # # LiqRange(8, 13)
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.add_m_liq(UnsignedDecimal("0"))
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.remove_m_liq(UnsignedDecimal("0"))
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.add_t_liq(UnsignedDecimal("0"), UnsignedDecimal("0"))
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.remove_t_liq(UnsignedDecimal("0"), UnsignedDecimal("0"))
        #
        # # LiqRange(8, 14)
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.add_m_liq(UnsignedDecimal("0"))
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.remove_m_liq(UnsignedDecimal("0"))
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.add_t_liq(UnsignedDecimal("0"), UnsignedDecimal("0"))
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.remove_t_liq(UnsignedDecimal("0"), UnsignedDecimal("0"))
        #
        # # LiqRange(8, 15)
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.add_m_liq(UnsignedDecimal("0"))
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.remove_m_liq(UnsignedDecimal("0"))
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.add_t_liq(UnsignedDecimal("0"), UnsignedDecimal("0"))
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.remove_t_liq(UnsignedDecimal("0"), UnsignedDecimal("0"))
        #
        # #endregion
        #
        # # region Ranges that start with 9 -------------------------------------------------------------------------------------
        # # LiqRange(9, 9)
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.add_m_liq(UnsignedDecimal("0"))
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.remove_m_liq(UnsignedDecimal("0"))
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.add_t_liq(UnsignedDecimal("0"), UnsignedDecimal("0"))
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.remove_t_liq(UnsignedDecimal("0"), UnsignedDecimal("0"))
        #
        # # LiqRange(9, 10)
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.add_m_liq(UnsignedDecimal("0"))
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.remove_m_liq(UnsignedDecimal("0"))
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.add_t_liq(UnsignedDecimal("0"), UnsignedDecimal("0"))
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.remove_t_liq(UnsignedDecimal("0"), UnsignedDecimal("0"))
        #
        # # LiqRange(9, 11)
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.add_m_liq(UnsignedDecimal("0"))
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.remove_m_liq(UnsignedDecimal("0"))
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.add_t_liq(UnsignedDecimal("0"), UnsignedDecimal("0"))
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.remove_t_liq(UnsignedDecimal("0"), UnsignedDecimal("0"))
        #
        # # LiqRange(9, 12)
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.add_m_liq(UnsignedDecimal("0"))
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.remove_m_liq(UnsignedDecimal("0"))
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.add_t_liq(UnsignedDecimal("0"), UnsignedDecimal("0"))
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.remove_t_liq(UnsignedDecimal("0"), UnsignedDecimal("0"))
        #
        # # LiqRange(9, 13)
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.add_m_liq(UnsignedDecimal("0"))
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.remove_m_liq(UnsignedDecimal("0"))
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.add_t_liq(UnsignedDecimal("0"), UnsignedDecimal("0"))
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.remove_t_liq(UnsignedDecimal("0"), UnsignedDecimal("0"))
        #
        # # LiqRange(9, 14)
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.add_m_liq(UnsignedDecimal("0"))
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.remove_m_liq(UnsignedDecimal("0"))
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.add_t_liq(UnsignedDecimal("0"), UnsignedDecimal("0"))
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.remove_t_liq(UnsignedDecimal("0"), UnsignedDecimal("0"))
        #
        # # LiqRange(9, 15)
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.add_m_liq(UnsignedDecimal("0"))
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.remove_m_liq(UnsignedDecimal("0"))
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.add_t_liq(UnsignedDecimal("0"), UnsignedDecimal("0"))
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.remove_t_liq(UnsignedDecimal("0"), UnsignedDecimal("0"))
        #
        # #endregion
        #
        # # region Ranges that start with 10 -------------------------------------------------------------------------------------
        # # LiqRange(10, 10)
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.add_m_liq(UnsignedDecimal("0"))
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.remove_m_liq(UnsignedDecimal("0"))
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.add_t_liq(UnsignedDecimal("0"), UnsignedDecimal("0"))
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.remove_t_liq(UnsignedDecimal("0"), UnsignedDecimal("0"))
        #
        # # LiqRange(10, 11)
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.add_m_liq(UnsignedDecimal("0"))
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.remove_m_liq(UnsignedDecimal("0"))
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.add_t_liq(UnsignedDecimal("0"), UnsignedDecimal("0"))
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.remove_t_liq(UnsignedDecimal("0"), UnsignedDecimal("0"))
        #
        # # LiqRange(10, 12)
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.add_m_liq(UnsignedDecimal("0"))
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.remove_m_liq(UnsignedDecimal("0"))
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.add_t_liq(UnsignedDecimal("0"), UnsignedDecimal("0"))
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.remove_t_liq(UnsignedDecimal("0"), UnsignedDecimal("0"))
        #
        # # LiqRange(10, 13)
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.add_m_liq(UnsignedDecimal("0"))
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.remove_m_liq(UnsignedDecimal("0"))
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.add_t_liq(UnsignedDecimal("0"), UnsignedDecimal("0"))
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.remove_t_liq(UnsignedDecimal("0"), UnsignedDecimal("0"))
        #
        # # LiqRange(10, 14)
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.add_m_liq(UnsignedDecimal("0"))
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.remove_m_liq(UnsignedDecimal("0"))
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.add_t_liq(UnsignedDecimal("0"), UnsignedDecimal("0"))
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.remove_t_liq(UnsignedDecimal("0"), UnsignedDecimal("0"))
        #
        # # LiqRange(10, 15)
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.add_m_liq(UnsignedDecimal("0"))
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.remove_m_liq(UnsignedDecimal("0"))
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.add_t_liq(UnsignedDecimal("0"), UnsignedDecimal("0"))
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.remove_t_liq(UnsignedDecimal("0"), UnsignedDecimal("0"))
        #
        # #endregion
        #
        # # region Ranges that start with 11 -------------------------------------------------------------------------------------
        # # LiqRange(11, 11)
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.add_m_liq(UnsignedDecimal("0"))
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.remove_m_liq(UnsignedDecimal("0"))
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.add_t_liq(UnsignedDecimal("0"), UnsignedDecimal("0"))
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.remove_t_liq(UnsignedDecimal("0"), UnsignedDecimal("0"))
        #
        # # LiqRange(11, 12)
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.add_m_liq(UnsignedDecimal("0"))
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.remove_m_liq(UnsignedDecimal("0"))
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.add_t_liq(UnsignedDecimal("0"), UnsignedDecimal("0"))
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.remove_t_liq(UnsignedDecimal("0"), UnsignedDecimal("0"))
        #
        # # LiqRange(11, 13)
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.add_m_liq(UnsignedDecimal("0"))
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.remove_m_liq(UnsignedDecimal("0"))
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.add_t_liq(UnsignedDecimal("0"), UnsignedDecimal("0"))
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.remove_t_liq(UnsignedDecimal("0"), UnsignedDecimal("0"))
        #
        # # LiqRange(11, 14)
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.add_m_liq(UnsignedDecimal("0"))
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.remove_m_liq(UnsignedDecimal("0"))
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.add_t_liq(UnsignedDecimal("0"), UnsignedDecimal("0"))
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.remove_t_liq(UnsignedDecimal("0"), UnsignedDecimal("0"))
        #
        # # LiqRange(11, 15)
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.add_m_liq(UnsignedDecimal("0"))
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.remove_m_liq(UnsignedDecimal("0"))
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.add_t_liq(UnsignedDecimal("0"), UnsignedDecimal("0"))
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.remove_t_liq(UnsignedDecimal("0"), UnsignedDecimal("0"))
        #
        # #endregion
        #
        # # region Ranges that start with 12 -------------------------------------------------------------------------------------
        # # LiqRange(12, 12)
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.add_m_liq(UnsignedDecimal("0"))
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.remove_m_liq(UnsignedDecimal("0"))
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.add_t_liq(UnsignedDecimal("0"), UnsignedDecimal("0"))
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.remove_t_liq(UnsignedDecimal("0"), UnsignedDecimal("0"))
        #
        # # LiqRange(12, 13)
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.add_m_liq(UnsignedDecimal("0"))
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.remove_m_liq(UnsignedDecimal("0"))
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.add_t_liq(UnsignedDecimal("0"), UnsignedDecimal("0"))
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.remove_t_liq(UnsignedDecimal("0"), UnsignedDecimal("0"))
        #
        # # LiqRange(12, 14)
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.add_m_liq(UnsignedDecimal("0"))
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.remove_m_liq(UnsignedDecimal("0"))
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.add_t_liq(UnsignedDecimal("0"), UnsignedDecimal("0"))
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.remove_t_liq(UnsignedDecimal("0"), UnsignedDecimal("0"))
        #
        # # LiqRange(12, 15)
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.add_m_liq(UnsignedDecimal("0"))
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.remove_m_liq(UnsignedDecimal("0"))
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.add_t_liq(UnsignedDecimal("0"), UnsignedDecimal("0"))
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.remove_t_liq(UnsignedDecimal("0"), UnsignedDecimal("0"))
        #
        # #endregion
        #
        # # region Ranges that start with 13 -------------------------------------------------------------------------------------
        # # LiqRange(13, 13)
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.add_m_liq(UnsignedDecimal("0"))
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.remove_m_liq(UnsignedDecimal("0"))
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.add_t_liq(UnsignedDecimal("0"), UnsignedDecimal("0"))
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.remove_t_liq(UnsignedDecimal("0"), UnsignedDecimal("0"))
        #
        # # LiqRange(13, 14)
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.add_m_liq(UnsignedDecimal("0"))
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.remove_m_liq(UnsignedDecimal("0"))
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.add_t_liq(UnsignedDecimal("0"), UnsignedDecimal("0"))
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.remove_t_liq(UnsignedDecimal("0"), UnsignedDecimal("0"))
        #
        # # LiqRange(13, 15)
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.add_m_liq(UnsignedDecimal("0"))
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.remove_m_liq(UnsignedDecimal("0"))
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.add_t_liq(UnsignedDecimal("0"), UnsignedDecimal("0"))
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.remove_t_liq(UnsignedDecimal("0"), UnsignedDecimal("0"))
        #
        # #endregion
        #
        # # region Ranges that start with 14 -------------------------------------------------------------------------------------
        # # LiqRange(14, 14)
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.add_m_liq(UnsignedDecimal("0"))
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.remove_m_liq(UnsignedDecimal("0"))
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.add_t_liq(UnsignedDecimal("0"), UnsignedDecimal("0"))
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.remove_t_liq(UnsignedDecimal("0"), UnsignedDecimal("0"))
        #
        # # LiqRange(14, 15)
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.add_m_liq(UnsignedDecimal("0"))
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.remove_m_liq(UnsignedDecimal("0"))
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.add_t_liq(UnsignedDecimal("0"), UnsignedDecimal("0"))
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.remove_t_liq(UnsignedDecimal("0"), UnsignedDecimal("0"))
        #
        # #endregion
        #
        # # region Ranges that start with 15 -------------------------------------------------------------------------------------
        # # LiqRange(15, 15)
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.add_m_liq(UnsignedDecimal("0"))
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.remove_m_liq(UnsignedDecimal("0"))
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.add_t_liq(UnsignedDecimal("0"), UnsignedDecimal("0"))
        # liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("0")
        # liq_tree.remove_t_liq(UnsignedDecimal("0"), UnsignedDecimal("0"))
        #
        # #endregion

    # def test_left_and_right_leg_stopping_below_peak_BROKEN(self):
    #     liq_tree = self.liq_tree
    #
    #     root: LiqNode = liq_tree.nodes[liq_tree.root_key]
    #     L: LiqNode = liq_tree.nodes[(8 << 24) | 16]
    #
    #     # 1st (1, 4) - subtree below LL
    #     LL: LiqNode = liq_tree.nodes[(4 << 24) | 16]
    #     LLL: LiqNode = liq_tree.nodes[(2 << 24) | 16]
    #     LLR: LiqNode = liq_tree.nodes[(2 << 24) | 18]
    #     LLLL: LiqNode = liq_tree.nodes[(1 << 24) | 16]
    #     LLLR: LiqNode = liq_tree.nodes[(1 << 24) | 17]
    #     LLRL: LiqNode = liq_tree.nodes[(1 << 24) | 18]
    #     LLRR: LiqNode = liq_tree.nodes[(1 << 24) | 19]
    #
    #     # Possible sub-ranges
    #     # (1,1), (1,2), (1,3), (1,4)
    #     # (2,2), (2,3), (2,4)
    #     # (3,3), (3,4)
    #     # (4,4)
    #
    #     # Apply operations over all sub-ranges
    #     # We don't want to organize all calls into sections like this, because there could be bugs depending on the order of calls (ie. add_t_liq before remove_t_liq)
    #     # As other tests will cover the correct ordering like the example mentioned, we should mix things up. But we DO know add_m_liq is before add_t_liq, and either add must be called before a remove
    #     # NOTE: these values are 'random'
    #     liq_tree.add_m_liq(LiqRange(low=1, high=1), UnsignedDecimal("98237498262"))  # LLLL
    #     liq_tree.add_m_liq(LiqRange(low=1, high=2), UnsignedDecimal("932141354"))  # LLL
    #     liq_tree.add_m_liq(LiqRange(low=1, high=3), UnsignedDecimal("151463465"))  # LLL, LLRL
    #     liq_tree.add_m_liq(LiqRange(low=1, high=4), UnsignedDecimal("45754683688356"))  # LL
    #     liq_tree.add_m_liq(LiqRange(low=2, high=2), UnsignedDecimal("245346257245745"))  # LLLR
    #     liq_tree.add_m_liq(LiqRange(low=2, high=3), UnsignedDecimal("243457472"))  # LLLR, LLRL
    #     liq_tree.add_m_liq(LiqRange(low=2, high=4), UnsignedDecimal("2462"))  # LLLR, LLR
    #     liq_tree.add_m_liq(LiqRange(low=3, high=3), UnsignedDecimal("45656756785"))  # LLRL
    #     liq_tree.add_m_liq(LiqRange(low=3, high=4), UnsignedDecimal("554"))  # LLR
    #     liq_tree.add_m_liq(LiqRange(low=4, high=4), UnsignedDecimal("262"))  # LLRR
    #
    #     liq_tree.add_t_liq(LiqRange(low=1, high=1), UnsignedDecimal("5645645"), UnsignedDecimal("4357e18"), UnsignedDecimal("345345345e6"))  # LLLL
    #     liq_tree.add_t_liq(LiqRange(low=1, high=2), UnsignedDecimal("3456835"), UnsignedDecimal("293874927834e18"), UnsignedDecimal("2345346e6"))  # LLL
    #     liq_tree.add_t_liq(LiqRange(low=1, high=3), UnsignedDecimal("56858345635"), UnsignedDecimal("23452e18"), UnsignedDecimal("12341235e6"))  # LLL, LLRL
    #     liq_tree.add_t_liq(LiqRange(low=1, high=4), UnsignedDecimal("23453467234"), UnsignedDecimal("134235e18"), UnsignedDecimal("34534634e6"))  # LL
    #     liq_tree.add_t_liq(LiqRange(low=2, high=2), UnsignedDecimal("456756745"), UnsignedDecimal("1233463e18"), UnsignedDecimal("2341356e6"))  # LLLR
    #     liq_tree.add_t_liq(LiqRange(low=2, high=3), UnsignedDecimal("34534652457"), UnsignedDecimal("45e18"), UnsignedDecimal("1324213563456457e6"))  # LLLR, LLRL
    #     liq_tree.add_t_liq(LiqRange(low=2, high=4), UnsignedDecimal("12121345"), UnsignedDecimal("4567e18"), UnsignedDecimal("1235146e6"))  # LLLR, LLR
    #     liq_tree.add_t_liq(LiqRange(low=3, high=3), UnsignedDecimal("4564573"), UnsignedDecimal("4564564e18"), UnsignedDecimal("6345135e6"))  # LLRL
    #     liq_tree.add_t_liq(LiqRange(low=3, high=4), UnsignedDecimal("3456242"), UnsignedDecimal("2564587456e18"), UnsignedDecimal("1234135e6"))  # LLR
    #     liq_tree.add_t_liq(LiqRange(low=4, high=4), UnsignedDecimal("2145245745"), UnsignedDecimal("76585673e18"), UnsignedDecimal("4564574e6"))  # LLRR
    #
    #     # Operations that accumulate fees
    #     liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("67967856253453452367574")
    #     liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("23464675683452345234568562")
    #     liq_tree.remove_t_liq(LiqRange(low=1, high=1), UnsignedDecimal("13426354645"), UnsignedDecimal("4e18"), UnsignedDecimal("5e6"))  # LLLL
    #     liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("457568568356234515")
    #     liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("3464756758679689")
    #     liq_tree.remove_t_liq(LiqRange(low=1, high=2), UnsignedDecimal("245346457"), UnsignedDecimal("1243234e18"), UnsignedDecimal("454564e6"))  # LLL
    #     liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("446476458")
    #     liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("35656867")
    #     liq_tree.remove_t_liq(LiqRange(low=1, high=3), UnsignedDecimal("2345136457"), UnsignedDecimal("134345e18"), UnsignedDecimal("245e6"))  # LLL, LLRL
    #     liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("32456")
    #     liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("246")
    #     liq_tree.remove_t_liq(LiqRange(low=1, high=4), UnsignedDecimal("345675686796"), UnsignedDecimal("4545e18"), UnsignedDecimal("45745e6"))  # LL
    #     liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("6796")
    #     liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("464564756785684")
    #     liq_tree.remove_t_liq(LiqRange(low=2, high=2), UnsignedDecimal("68978907"), UnsignedDecimal("23454e18"), UnsignedDecimal("5677e6"))  # LLLR
    #     liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("3454568796798643673")
    #     liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("3456475784245234553434523453456346")
    #     liq_tree.remove_t_liq(LiqRange(low=2, high=3), UnsignedDecimal("8908978"), UnsignedDecimal("856454e18"), UnsignedDecimal("4577865e6"))  # LLLR, LLRL
    #     liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("4573568356983683682578725")
    #     liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("234624576468356835688356368368482342")
    #     liq_tree.remove_t_liq(LiqRange(low=2, high=4), UnsignedDecimal("679678"), UnsignedDecimal("3456457e18"), UnsignedDecimal("56756756e6"))  # LLLR, LLR
    #     liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("3256457252452572172577252424547457")
    #     liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("35745675685835626345234624")
    #     liq_tree.remove_t_liq(LiqRange(low=3, high=3), UnsignedDecimal("65756"), UnsignedDecimal("56756e18"), UnsignedDecimal("34564567e6"))  # LLRL
    #     liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("345646856785673572456245")
    #     liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("2356457568367824623454576788")
    #     liq_tree.remove_t_liq(LiqRange(low=3, high=4), UnsignedDecimal("54444"), UnsignedDecimal("4564564e18"), UnsignedDecimal("56756786e6"))  # LLR
    #     liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("456325876883562457")
    #     liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("5767983835654356214356")
    #     liq_tree.remove_t_liq(LiqRange(low=4, high=4), UnsignedDecimal("443"), UnsignedDecimal("4564564e18"), UnsignedDecimal("56754e6"))  # LLRR
    #
    #     liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("3456568679362657567867956")
    #     liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("35735736783579799798988790078")
    #     liq_tree.add_m_liq(LiqRange(low=1, high=1), UnsignedDecimal("75645"))  # LLLL
    #     liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("678908690870808")
    #     liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("56890598759879798769")
    #     liq_tree.add_m_liq(LiqRange(low=1, high=2), UnsignedDecimal("8567567"))  # LLL
    #     liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("70890900879879467474")
    #     liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("4678679468674786666")
    #     liq_tree.add_m_liq(LiqRange(low=1, high=3), UnsignedDecimal("456456"))  # LLL, LLRL
    #     liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("46877777777777777")
    #     liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("3465675698689467357")
    #     liq_tree.add_m_liq(LiqRange(low=1, high=4), UnsignedDecimal("356767894766"))  # LL
    #     liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("346745684567943673567")
    #     liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("5455665565656556556")
    #     liq_tree.add_m_liq(LiqRange(low=2, high=2), UnsignedDecimal("34563457"))  # LLLR
    #     liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("54574562523462347457")
    #     liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("346468567843652647")
    #     liq_tree.add_m_liq(LiqRange(low=2, high=3), UnsignedDecimal("245346"))  # LLLR, LLRL
    #     liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("435736487858735734")
    #     liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("345756856785784")
    #     liq_tree.add_m_liq(LiqRange(low=2, high=4), UnsignedDecimal("35654373573456"))  # LLLR, LLR
    #     liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("9782315978324963149086")
    #     liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("1977947657153479167908478603")
    #     liq_tree.add_m_liq(LiqRange(low=3, high=3), UnsignedDecimal("24546457452"))  # LLRL
    #     liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("877907987198867986767967167846785637245673")
    #     liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("01749857934067931408619045791874695714676")
    #     liq_tree.add_m_liq(LiqRange(low=3, high=4), UnsignedDecimal("356345645745675675685678"))  # LLR
    #     liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("9987698779879879874987786384537456725474327243259947838356837568356725984687365")
    #     liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("9878678625678156565671567256742164782194785174671462314967193478691843769813476987")
    #     liq_tree.add_m_liq(LiqRange(low=4, high=4), UnsignedDecimal("459789686783566564767"))  # LLRR
    #     liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("2546456746735")
    #     liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("2454567346736")
    #
    #     liq_tree.remove_m_liq(LiqRange(low=1, high=1), UnsignedDecimal("67967867"))  # LLLL
    #     liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("7676767327272772272727722727272")
    #     liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("2727772727272777777777777722727")
    #     liq_tree.remove_m_liq(LiqRange(low=1, high=2), UnsignedDecimal("45635457"))  # LLL
    #     liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("198759265398245671987469087")
    #     liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("19746587349687357810349578017946")
    #     liq_tree.remove_m_liq(LiqRange(low=1, high=3), UnsignedDecimal("567567373"))  # LLL, LLRL
    #     liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("98717986587364907214036834590682")
    #     liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("9716395673986702964617823679805")
    #     liq_tree.remove_m_liq(LiqRange(low=1, high=4), UnsignedDecimal("4575437856335"))  # LL
    #     liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("976987080780203980798239742934235")
    #     liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("6978978987459873981798273497823942")
    #     liq_tree.remove_m_liq(LiqRange(low=2, high=2), UnsignedDecimal("23455745645"))  # LLLR
    #     liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("434522534253453462436234623462346")
    #     liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("23462345134634623634623462456724566")
    #     liq_tree.remove_m_liq(LiqRange(low=2, high=3), UnsignedDecimal("2345346574"))  # LLLR, LLRL
    #     liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("79878979876987698798454564564564")
    #     liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("5645635645634621462476262756245624565")
    #     liq_tree.remove_m_liq(LiqRange(low=2, high=4), UnsignedDecimal("24534646856"))  # LLLR, LLR
    #     liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("24512645624662342346234634631463462246462")
    #     liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("214664623234616414624646236234234634646232463")
    #     liq_tree.remove_m_liq(LiqRange(low=3, high=3), UnsignedDecimal("47568568564"))  # LLRL
    #     liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("12221211212244155551555555555555555555555555555")
    #     liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("155555555555555555555555555555555555555555555555")
    #     liq_tree.remove_m_liq(LiqRange(low=3, high=4), UnsignedDecimal("24545656855"))  # LLR
    #     liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("9874787246782564286735426553525832786234623")
    #     liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("67845986765986736798567832459782739845798230")
    #     liq_tree.remove_m_liq(LiqRange(low=4, high=4), UnsignedDecimal("3452464675675"))  # LLRR
    #     liq_tree.token_x_fee_rate_snapshot += UnsignedDecimal("98726348906735986783495701378450983165908231479581324")
    #     liq_tree.token_y_fee_rate_snapshot += UnsignedDecimal("98749857398456981264570398459047569823794785961235")
    #
    #     # Verify state is correct for all effected nodes (includes L and root)
    #     # m_liq
    #     self.assertEqual(root.m_liq, UnsignedDecimal("0"))
    #     self.assertEqual(L.m_liq, UnsignedDecimal("0"))
    #     self.assertEqual(LL.m_liq, UnsignedDecimal("0"))
    #     self.assertEqual(LLL.m_liq, UnsignedDecimal("0"))
    #     self.assertEqual(LLR.m_liq, UnsignedDecimal("45755078611755"))
    #     self.assertEqual(LLLL.m_liq, UnsignedDecimal("0"))
    #     self.assertEqual(LLLR.m_liq, UnsignedDecimal("41634662758839"))
    #     self.assertEqual(LLRL.m_liq, UnsignedDecimal("245323731137021"))
    #     self.assertEqual(LLRR.m_liq, UnsignedDecimal("356345645745673764675050"))
    #
    #     # t_liq
    #     self.assertEqual(root.t_liq, UnsignedDecimal("0"))
    #     self.assertEqual(L.t_liq, UnsignedDecimal("0"))
    #     self.assertEqual(LL.t_liq, UnsignedDecimal("0"))
    #     self.assertEqual(LLL.t_liq, UnsignedDecimal("0"))
    #     self.assertEqual(LLR.t_liq, UnsignedDecimal("5346"))
    #     self.assertEqual(LLLL.t_liq, UnsignedDecimal("7634865"))
    #     self.assertEqual(LLLR.t_liq, UnsignedDecimal("7634865"))
    #     self.assertEqual(LLRL.t_liq, UnsignedDecimal("7634865"))
    #     self.assertEqual(LLRR.t_liq, UnsignedDecimal("7634865"))
    #
    #     # subtree_m_liq
    #     self.assertEqual(root.subtree_m_liq, UnsignedDecimal("324198833"))
    #     self.assertEqual(L.subtree_m_liq, UnsignedDecimal("324063953"))
    #     self.assertEqual(LL.subtree_m_liq, UnsignedDecimal("324056493"))
    #     self.assertEqual(LLL.subtree_m_liq, UnsignedDecimal("4444"))
    #     self.assertEqual(LLR.subtree_m_liq, UnsignedDecimal("287725557"))
    #     self.assertEqual(LLLL.subtree_m_liq, UnsignedDecimal("287634865"))
    #     self.assertEqual(LLLR.subtree_m_liq, UnsignedDecimal("287634865"))
    #     self.assertEqual(LLRL.subtree_m_liq, UnsignedDecimal("287634865"))
    #     self.assertEqual(LLRR.subtree_m_liq, UnsignedDecimal("287634865"))
    #
    #     # borrow_x
    #     self.assertEqual(root.token_x_borrow, UnsignedDecimal("492e18"))
    #     self.assertEqual(L.token_x_borrow, UnsignedDecimal("998e18"))
    #     self.assertEqual(LL.token_x_borrow, UnsignedDecimal("765e18"))
    #     self.assertEqual(LLL.token_x_borrow, UnsignedDecimal("24e18"))
    #     self.assertEqual(LLR.token_x_borrow, UnsignedDecimal("53e18"))
    #     self.assertEqual(LLLL.token_x_borrow, UnsignedDecimal("701e18"))
    #     self.assertEqual(LLLR.token_x_borrow, UnsignedDecimal("701e18"))
    #     self.assertEqual(LLRL.token_x_borrow, UnsignedDecimal("701e18"))
    #     self.assertEqual(LLRR.token_x_borrow, UnsignedDecimal("701e18"))
    #
    #     # subtree_borrow_x
    #     self.assertEqual(root.token_x_subtree_borrow, UnsignedDecimal("3033e18"))
    #     self.assertEqual(L.token_x_subtree_borrow, UnsignedDecimal("2541e18"))
    #     self.assertEqual(LL.token_x_subtree_borrow, UnsignedDecimal("1519e18"))
    #     self.assertEqual(LLL.token_x_subtree_borrow, UnsignedDecimal("24e18"))
    #     self.assertEqual(LLR.token_x_subtree_borrow, UnsignedDecimal("754e18"))
    #     self.assertEqual(LLLL.token_x_subtree_borrow, UnsignedDecimal("701e18"))
    #     self.assertEqual(LLLR.token_x_subtree_borrow, UnsignedDecimal("701e18"))
    #     self.assertEqual(LLRL.token_x_subtree_borrow, UnsignedDecimal("701e18"))
    #     self.assertEqual(LLRR.token_x_subtree_borrow, UnsignedDecimal("701e18"))
    #
    #     # borrow_y
    #     self.assertEqual(root.token_y_borrow, UnsignedDecimal("254858e6"))
    #     self.assertEqual(L.token_y_borrow, UnsignedDecimal("353e6"))
    #     self.assertEqual(LL.token_y_borrow, UnsignedDecimal("99763e6"))
    #     self.assertEqual(LLL.token_y_borrow, UnsignedDecimal("552e6"))
    #     self.assertEqual(LLR.token_y_borrow, UnsignedDecimal("8765e6"))
    #     self.assertEqual(LLLL.token_y_borrow, UnsignedDecimal("779531e6"))
    #     self.assertEqual(LLLR.token_y_borrow, UnsignedDecimal("779531e6"))
    #     self.assertEqual(LLRL.token_y_borrow, UnsignedDecimal("779531e6"))
    #     self.assertEqual(LLRR.token_y_borrow, UnsignedDecimal("779531e6"))
    #
    #     # subtree_borrow_y
    #     self.assertEqual(root.token_y_subtree_borrow, UnsignedDecimal("1143822e6"))
    #     self.assertEqual(L.token_y_subtree_borrow, UnsignedDecimal("888964e6"))
    #     self.assertEqual(LL.token_y_subtree_borrow, UnsignedDecimal("888059e6"))
    #     self.assertEqual(LLL.token_y_subtree_borrow, UnsignedDecimal("552e6"))
    #     self.assertEqual(LLR.token_y_subtree_borrow, UnsignedDecimal("788296e6"))
    #     self.assertEqual(LLLL.token_y_subtree_borrow, UnsignedDecimal("779531e6"))
    #     self.assertEqual(LLLR.token_y_subtree_borrow, UnsignedDecimal("779531e6"))
    #     self.assertEqual(LLRL.token_y_subtree_borrow, UnsignedDecimal("779531e6"))
    #     self.assertEqual(LLRR.token_y_subtree_borrow, UnsignedDecimal("779531e6"))


'''

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
