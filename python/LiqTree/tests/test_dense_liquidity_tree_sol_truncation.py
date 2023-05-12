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


class TestDenseLiquidityTreeSolTruncation(TestCase):
    def setUp(self) -> None:
        self.liq_tree = LiquidityTree(depth=4, sol_truncation=True)

    def test_root_only(self):
        liq_tree: LiquidityTree = self.liq_tree

        # T0
        liq_tree.add_inf_range_m_liq(Decimal("8430"))
        liq_tree.add_inf_range_t_liq(Decimal("4381"), Decimal("832e18"), Decimal("928e6"))
        self.assertEqual(True, True)

        # T3600 (1hr) --- 5.4% APR as Q192.64
        liq_tree.token_y_fee_rate_snapshot += Decimal("113712805933826")  # 0.054 * 3600 / (365 * 24 * 60 * 60) * 2^64
        liq_tree.token_x_fee_rate_snapshot += Decimal("113712805933826")

        # Verify root state
        root: LiqNode = liq_tree.root
        self.assertEqual(root.m_liq, Decimal("8430"))
        self.assertEqual(root.subtree_m_liq, Decimal("134880"))
        self.assertEqual(root.t_liq, Decimal("4381"))
        self.assertEqual(root.token_x_borrowed, Decimal("832e18"))
        self.assertEqual(root.token_x_subtree_borrowed, Decimal("832e18"))
        self.assertEqual(root.token_y_borrowed, Decimal("928e6"))
        self.assertEqual(root.token_y_subtree_borrowed, Decimal("928e6"))

        # Testing 4 methods for proper fee accumulation:
        # add_inf_range_m_liq, remove_inf_range_m_liq
        # add_inf_range_t_liq, remove_inf_range_t_liq
        liq_tree.add_inf_range_m_liq(Decimal("9287"))

        self.assertEqual(int(root.token_x_cummulative_earned_per_m_liq), Decimal("38024667284"))
        self.assertEqual(int(root.token_x_cummulative_earned_per_m_subtree_liq), Decimal("38024667284"))
        self.assertEqual(int(root.token_y_cummulative_earned_per_m_liq), Decimal("0"))
        self.assertEqual(int(root.token_y_cummulative_earned_per_m_subtree_liq), Decimal("0"))

        self.assertEqual(root.m_liq, Decimal("17717"))
        self.assertEqual(root.subtree_m_liq, Decimal("283472"))
        self.assertEqual(root.t_liq, Decimal("4381"))
        self.assertEqual(root.token_x_borrowed, Decimal("832e18"))
        self.assertEqual(root.token_x_subtree_borrowed, Decimal("832e18"))
        self.assertEqual(root.token_y_borrowed, Decimal("928e6"))
        self.assertEqual(root.token_y_subtree_borrowed, Decimal("928e6"))

        # T22000 -- 693792000.0% APR as Q192.64 from T22000 - T3600
        liq_tree.token_y_fee_rate_snapshot += Decimal("74672420010376264941568")   # Q192.64 - 1377463021295958900099740410883797719973888
        liq_tree.token_x_fee_rate_snapshot += Decimal("74672420010376264941568")   # Q192.64 - 1377463021295958900099740410883797719973888

        liq_tree.remove_inf_range_m_liq(Decimal("3682"))

        # rounding error
        self.assertEqual(int(root.token_x_cummulative_earned_per_m_liq), Decimal("11881018269102163474"))
        self.assertEqual(int(root.token_x_cummulative_earned_per_m_subtree_liq), Decimal("11881018269102163474"))
        self.assertEqual(int(root.token_y_cummulative_earned_per_m_liq), Decimal("13251904"))
        self.assertEqual(int(root.token_y_cummulative_earned_per_m_subtree_liq), Decimal("13251904"))

        self.assertEqual(root.m_liq, Decimal("14035"))
        self.assertEqual(root.subtree_m_liq, Decimal("224560"))
        self.assertEqual(root.t_liq, Decimal("4381"))
        self.assertEqual(root.token_x_borrowed, Decimal("832e18"))
        self.assertEqual(root.token_x_subtree_borrowed, Decimal("832e18"))
        self.assertEqual(root.token_y_borrowed, Decimal("928e6"))
        self.assertEqual(root.token_y_subtree_borrowed, Decimal("928e6"))

        # T37002 --- 7.9% APR as Q192.64 T37002 - T22000
        liq_tree.token_y_fee_rate_snapshot += Decimal("6932491854677024")  # Q192.64 - 127881903036303130599671671537270784
        liq_tree.token_x_fee_rate_snapshot += Decimal("6932491854677024")  # Q192.64 - 127881903036303130599671671537270784

        liq_tree.add_inf_range_t_liq(Decimal("7287"), Decimal("9184e18"), Decimal("7926920e6"))

        # rounding error
        self.assertEqual(int(root.token_x_cummulative_earned_per_m_liq), Decimal("11881019661491126559"))
        self.assertEqual(int(root.token_x_cummulative_earned_per_m_subtree_liq), Decimal("11881019661491126559"))
        self.assertEqual(int(root.token_y_cummulative_earned_per_m_liq), Decimal("13251905"))
        self.assertEqual(int(root.token_y_cummulative_earned_per_m_subtree_liq), Decimal("13251905"))

        self.assertEqual(root.m_liq, Decimal("14035"))
        self.assertEqual(root.subtree_m_liq, Decimal("224560"))
        self.assertEqual(root.t_liq, Decimal("11668"))
        self.assertEqual(root.token_x_borrowed, Decimal("10016e18"))
        self.assertEqual(root.token_x_subtree_borrowed, Decimal("10016e18"))
        self.assertEqual(root.token_y_borrowed, Decimal("7927848e6"))
        self.assertEqual(root.token_y_subtree_borrowed, Decimal("7927848e6"))

        # T57212 --- 11.1% APR as Q192.64 TT57212 - T37002
        liq_tree.token_y_fee_rate_snapshot += Decimal("1055375100301031600000000")     # Q192.64 - 19468234377018678290990465858247065600000000
        liq_tree.token_x_fee_rate_snapshot += Decimal("1055375100301031600000000")     # Q192.64 - 19468234377018678290990465858247065600000000

        liq_tree.remove_inf_range_t_liq(Decimal("4923"), Decimal("222e18"), Decimal("786e6"))

        self.assertEqual(int(root.token_x_cummulative_earned_per_m_liq), Decimal("2563695146166521368512"))
        self.assertEqual(int(root.token_x_cummulative_earned_per_m_subtree_liq), Decimal("2563695146166521368512"))
        self.assertEqual(int(root.token_y_cummulative_earned_per_m_liq), Decimal("2019821011408"))
        self.assertEqual(int(root.token_y_cummulative_earned_per_m_subtree_liq), Decimal("2019821011408"))

        self.assertEqual(root.m_liq, Decimal("14035"))
        self.assertEqual(root.subtree_m_liq, Decimal("224560"))
        self.assertEqual(root.t_liq, Decimal("6745"))
        self.assertEqual(root.token_x_borrowed, Decimal("9794e18"))
        self.assertEqual(root.token_x_subtree_borrowed, Decimal("9794e18"))
        self.assertEqual(root.token_y_borrowed, Decimal("7927062e6"))
        self.assertEqual(root.token_y_subtree_borrowed, Decimal("7927062e6"))

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
        liq_tree.add_inf_range_m_liq(Decimal("8430"))  # root
        liq_tree.add_m_liq(LiqRange(low=0, high=7), Decimal("377"))  # L
        liq_tree.add_m_liq(LiqRange(low=0, high=3), Decimal("9082734"))  # LL
        liq_tree.add_m_liq(LiqRange(low=4, high=7), Decimal("1111"))  # LR
        liq_tree.add_m_liq(LiqRange(low=2, high=3), Decimal("45346"))  # LLR
        liq_tree.add_m_liq(LiqRange(low=3, high=3), Decimal("287634865"))  # LLRR

        liq_tree.add_inf_range_t_liq(Decimal("4430"), Decimal("492e18"), Decimal("254858e6"))  # root
        liq_tree.add_t_liq(LiqRange(low=0, high=7), Decimal("77"), Decimal("998e18"), Decimal("353e6"))  # L
        liq_tree.add_t_liq(LiqRange(low=0, high=3), Decimal("82734"), Decimal("765e18"), Decimal("99763e6"))  # LL
        liq_tree.add_t_liq(LiqRange(low=4, high=7), Decimal("111"), Decimal("24e18"), Decimal("552e6"))  # LR
        liq_tree.add_t_liq(LiqRange(low=2, high=3), Decimal("5346"), Decimal("53e18"), Decimal("8765e6"))  # LLR
        liq_tree.add_t_liq(LiqRange(low=3, high=3), Decimal("7634865"), Decimal("701e18"), Decimal("779531e6"))  # LLRR

        # m_liq
        self.assertEqual(root.m_liq, Decimal("8430"))
        self.assertEqual(L.m_liq, Decimal("377"))
        self.assertEqual(LL.m_liq, Decimal("9082734"))
        self.assertEqual(LR.m_liq, Decimal("1111"))
        self.assertEqual(LLR.m_liq, Decimal("45346"))
        self.assertEqual(LLRR.m_liq, Decimal("287634865"))

        # t_liq
        self.assertEqual(root.t_liq, Decimal("4430"))
        self.assertEqual(L.t_liq, Decimal("77"))
        self.assertEqual(LL.t_liq, Decimal("82734"))
        self.assertEqual(LR.t_liq, Decimal("111"))
        self.assertEqual(LLR.t_liq, Decimal("5346"))
        self.assertEqual(LLRR.t_liq, Decimal("7634865"))

        # subtree_m_liq
        self.assertEqual(root.subtree_m_liq, Decimal("324198833"))
        self.assertEqual(L.subtree_m_liq, Decimal("324063953"))
        self.assertEqual(LL.subtree_m_liq, Decimal("324056493"))
        self.assertEqual(LR.subtree_m_liq, Decimal("4444"))
        self.assertEqual(LLR.subtree_m_liq, Decimal("287725557"))
        self.assertEqual(LLRR.subtree_m_liq, Decimal("287634865"))

        # borrowed_x
        self.assertEqual(root.token_x_borrowed, Decimal("492e18"))
        self.assertEqual(L.token_x_borrowed, Decimal("998e18"))
        self.assertEqual(LL.token_x_borrowed, Decimal("765e18"))
        self.assertEqual(LR.token_x_borrowed, Decimal("24e18"))
        self.assertEqual(LLR.token_x_borrowed, Decimal("53e18"))
        self.assertEqual(LLRR.token_x_borrowed, Decimal("701e18"))

        # subtree_borrowed_x
        self.assertEqual(root.token_x_subtree_borrowed, Decimal("3033e18"))
        self.assertEqual(L.token_x_subtree_borrowed, Decimal("2541e18"))
        self.assertEqual(LL.token_x_subtree_borrowed, Decimal("1519e18"))
        self.assertEqual(LR.token_x_subtree_borrowed, Decimal("24e18"))
        self.assertEqual(LLR.token_x_subtree_borrowed, Decimal("754e18"))
        self.assertEqual(LLRR.token_x_subtree_borrowed, Decimal("701e18"))

        # borrowed_y
        self.assertEqual(root.token_y_borrowed, Decimal("254858e6"))
        self.assertEqual(L.token_y_borrowed, Decimal("353e6"))
        self.assertEqual(LL.token_y_borrowed, Decimal("99763e6"))
        self.assertEqual(LR.token_y_borrowed, Decimal("552e6"))
        self.assertEqual(LLR.token_y_borrowed, Decimal("8765e6"))
        self.assertEqual(LLRR.token_y_borrowed, Decimal("779531e6"))

        # subtree_borrowed_y
        self.assertEqual(root.token_y_subtree_borrowed, Decimal("1143822e6"))
        self.assertEqual(L.token_y_subtree_borrowed, Decimal("888964e6"))
        self.assertEqual(LL.token_y_subtree_borrowed, Decimal("888059e6"))
        self.assertEqual(LR.token_y_subtree_borrowed, Decimal("552e6"))
        self.assertEqual(LLR.token_y_subtree_borrowed, Decimal("788296e6"))
        self.assertEqual(LLRR.token_y_subtree_borrowed, Decimal("779531e6"))

        # T98273
        liq_tree.token_x_fee_rate_snapshot += Decimal("4541239648278065")
        liq_tree.token_y_fee_rate_snapshot += Decimal("13278814667749784")

        # Apply change that requires fee calculation
        # add_m_liq
        liq_tree.add_m_liq(LiqRange(low=3, high=7), Decimal("2734"))  # LLRR, LR

        # root
        self.assertEqual(int(root.token_x_cummulative_earned_per_m_liq), Decimal("373601278"))
        self.assertEqual(int(root.token_x_cummulative_earned_per_m_subtree_liq), Decimal("2303115199"))
        self.assertEqual(int(root.token_y_cummulative_earned_per_m_liq), Decimal("0"))
        self.assertEqual(int(root.token_y_cummulative_earned_per_m_subtree_liq), Decimal("2"))

        # L
        self.assertEqual(int(L.token_x_cummulative_earned_per_m_liq), Decimal("757991165"))
        self.assertEqual(int(L.token_x_cummulative_earned_per_m_subtree_liq), Decimal("1929915382"))
        self.assertEqual(int(L.token_y_cummulative_earned_per_m_liq), Decimal("0"))
        self.assertEqual(int(L.token_y_cummulative_earned_per_m_subtree_liq), Decimal("1"))

        # LL
        self.assertEqual(int(LL.token_x_cummulative_earned_per_m_liq), Decimal("581096415"))
        self.assertEqual(int(LL.token_x_cummulative_earned_per_m_subtree_liq), Decimal("1153837196"))
        self.assertEqual(int(LL.token_y_cummulative_earned_per_m_liq), Decimal("0"))
        self.assertEqual(int(LL.token_y_cummulative_earned_per_m_subtree_liq), Decimal("1"))

        # LR
        self.assertEqual(int(LR.token_x_cummulative_earned_per_m_liq), Decimal("148929881804"))
        self.assertEqual(int(LR.token_x_cummulative_earned_per_m_subtree_liq), Decimal("148929881804"))
        self.assertEqual(int(LR.token_y_cummulative_earned_per_m_liq), Decimal("10"))
        self.assertEqual(int(LR.token_y_cummulative_earned_per_m_subtree_liq), Decimal("10"))

        # LLR
        self.assertEqual(int(LLR.token_x_cummulative_earned_per_m_liq), Decimal("42651943"))
        self.assertEqual(int(LLR.token_x_cummulative_earned_per_m_subtree_liq), Decimal("606784254"))
        self.assertEqual(int(LLR.token_y_cummulative_earned_per_m_liq), Decimal("0"))
        self.assertEqual(int(LLR.token_y_cummulative_earned_per_m_subtree_liq), Decimal("1"))

        # LLRR
        self.assertEqual(int(LLRR.token_x_cummulative_earned_per_m_liq), Decimal("581500584"))
        self.assertEqual(int(LLRR.token_x_cummulative_earned_per_m_subtree_liq), Decimal("581500584"))
        self.assertEqual(int(LLRR.token_y_cummulative_earned_per_m_liq), Decimal("1"))
        self.assertEqual(int(LLRR.token_y_cummulative_earned_per_m_subtree_liq), Decimal("1"))

        # m_liq
        self.assertEqual(root.m_liq, Decimal("8430"))
        self.assertEqual(L.m_liq, Decimal("377"))
        self.assertEqual(LL.m_liq, Decimal("9082734"))
        self.assertEqual(LR.m_liq, Decimal("3845"))
        self.assertEqual(LLR.m_liq, Decimal("45346"))
        self.assertEqual(LLRR.m_liq, Decimal("287637599"))

        # subtree_m_liq
        self.assertEqual(root.subtree_m_liq, Decimal("324212503"))
        self.assertEqual(L.subtree_m_liq, Decimal("324077623"))
        self.assertEqual(LL.subtree_m_liq, Decimal("324059227"))
        self.assertEqual(LR.subtree_m_liq, Decimal("15380"))
        self.assertEqual(LLR.subtree_m_liq, Decimal("287728291"))
        self.assertEqual(LLRR.subtree_m_liq, Decimal("287637599"))

        # T2876298273
        liq_tree.token_x_fee_rate_snapshot += Decimal("16463537718422861220174597")
        liq_tree.token_y_fee_rate_snapshot += Decimal("3715979586694123491881712207")

        # Apply change that requires fee calculation
        # remove_m_liq
        liq_tree.remove_m_liq(LiqRange(low=3, high=7), Decimal("2734"))  # LLRR, LR

        # root
        self.assertEqual(int(root.token_x_cummulative_earned_per_m_liq), Decimal("1354374549844117328"))
        self.assertEqual(int(root.token_x_cummulative_earned_per_m_subtree_liq), Decimal("8349223596904894020"))
        self.assertEqual(int(root.token_y_cummulative_earned_per_m_liq), Decimal("158351473403"))
        self.assertEqual(int(root.token_y_cummulative_earned_per_m_subtree_liq), Decimal("710693401863"))

        # L
        self.assertEqual(int(L.token_x_cummulative_earned_per_m_liq), Decimal("2747859799935140577"))
        self.assertEqual(int(L.token_x_cummulative_earned_per_m_subtree_liq), Decimal("6996304360355904016"))
        self.assertEqual(int(L.token_y_cummulative_earned_per_m_liq), Decimal("219375887"))
        self.assertEqual(int(L.token_y_cummulative_earned_per_m_subtree_liq), Decimal("552456845956"))

        # LL
        self.assertEqual(int(LL.token_x_cummulative_earned_per_m_liq), Decimal("2106654304686669588"))
        self.assertEqual(int(LL.token_x_cummulative_earned_per_m_subtree_liq), Decimal("4183016848129478568"))
        self.assertEqual(int(LL.token_y_cummulative_earned_per_m_liq), Decimal("62008538706"))
        self.assertEqual(int(LL.token_y_cummulative_earned_per_m_subtree_liq), Decimal("551980602777"))

        # LR
        self.assertEqual(int(LR.token_x_cummulative_earned_per_m_liq), Decimal("423248578107618890129"))
        self.assertEqual(int(LR.token_x_cummulative_earned_per_m_subtree_liq), Decimal("423248578107618890129"))
        self.assertEqual(int(LR.token_y_cummulative_earned_per_m_liq), Decimal("2197219781195"))
        self.assertEqual(int(LR.token_y_cummulative_earned_per_m_subtree_liq), Decimal("2197219781195"))

        # LLR
        self.assertEqual(int(LLR.token_x_cummulative_earned_per_m_liq), Decimal("154626415017241476"))
        self.assertEqual(int(LLR.token_x_cummulative_earned_per_m_subtree_liq), Decimal("2199779564584907057"))
        self.assertEqual(int(LLR.token_y_cummulative_earned_per_m_liq), Decimal("5771781665"))
        self.assertEqual(int(LLR.token_y_cummulative_earned_per_m_subtree_liq), Decimal("519095539055"))

        # LLRR
        self.assertEqual(int(LLRR.token_x_cummulative_earned_per_m_liq), Decimal("2108117905996538332"))
        self.assertEqual(int(LLRR.token_x_cummulative_earned_per_m_subtree_liq), Decimal("2108117905996538332"))
        self.assertEqual(int(LLRR.token_y_cummulative_earned_per_m_liq), Decimal("529127613135"))
        self.assertEqual(int(LLRR.token_y_cummulative_earned_per_m_subtree_liq), Decimal("529127613135"))

        # m_liq
        self.assertEqual(root.m_liq, Decimal("8430"))
        self.assertEqual(L.m_liq, Decimal("377"))
        self.assertEqual(LL.m_liq, Decimal("9082734"))
        self.assertEqual(LR.m_liq, Decimal("1111"))
        self.assertEqual(LLR.m_liq, Decimal("45346"))
        self.assertEqual(LLRR.m_liq, Decimal("287634865"))

        # subtree_m_liq
        self.assertEqual(root.subtree_m_liq, Decimal("324198833"))
        self.assertEqual(L.subtree_m_liq, Decimal("324063953"))
        self.assertEqual(LL.subtree_m_liq, Decimal("324056493"))
        self.assertEqual(LR.subtree_m_liq, Decimal("4444"))
        self.assertEqual(LLR.subtree_m_liq, Decimal("287725557"))
        self.assertEqual(LLRR.subtree_m_liq, Decimal("287634865"))

        # T9214298113
        liq_tree.token_x_fee_rate_snapshot += Decimal("11381610389149375791104")
        liq_tree.token_y_fee_rate_snapshot += Decimal("185394198934916215865344")

        # Apply change that requires fee calculation
        # add_t_liq
        liq_tree.add_t_liq(LiqRange(low=3, high=7), Decimal("1000"), Decimal("1000e18"), Decimal("1000e6"))  # LLRR, LR

        # root
        self.assertEqual(int(root.token_x_cummulative_earned_per_m_liq), Decimal("1355310898622008714"))
        self.assertEqual(int(root.token_x_cummulative_earned_per_m_subtree_liq), Decimal("8354995844553968361"))
        self.assertEqual(int(root.token_y_cummulative_earned_per_m_liq), Decimal("158359374060"))
        self.assertEqual(int(root.token_y_cummulative_earned_per_m_subtree_liq), Decimal("710728860612"))

        # L
        self.assertEqual(int(L.token_x_cummulative_earned_per_m_liq), Decimal("2749759536746020654"))
        self.assertEqual(int(L.token_x_cummulative_earned_per_m_subtree_liq), Decimal("7001141265402443371"))
        self.assertEqual(int(L.token_y_cummulative_earned_per_m_liq), Decimal("219386832"))
        self.assertEqual(int(L.token_y_cummulative_earned_per_m_subtree_liq), Decimal("552484409781"))

        # LL
        self.assertEqual(int(LL.token_x_cummulative_earned_per_m_liq), Decimal("2108110694023652835"))
        self.assertEqual(int(LL.token_x_cummulative_earned_per_m_subtree_liq), Decimal("4185908685257423082"))
        self.assertEqual(int(LL.token_y_cummulative_earned_per_m_liq), Decimal("62011632404"))
        self.assertEqual(int(LL.token_y_cummulative_earned_per_m_subtree_liq), Decimal("552008141912"))

        # LR
        self.assertEqual(int(LR.token_x_cummulative_earned_per_m_liq), Decimal("423621837838722923425"))
        self.assertEqual(int(LR.token_x_cummulative_earned_per_m_subtree_liq), Decimal("423621837838722923425"))
        self.assertEqual(int(LR.token_y_cummulative_earned_per_m_liq), Decimal("2197359621190"))
        self.assertEqual(int(LR.token_y_cummulative_earned_per_m_subtree_liq), Decimal("2197359621190"))

        # LLR
        self.assertEqual(int(LLR.token_x_cummulative_earned_per_m_liq), Decimal("154733312657952738"))
        self.assertEqual(int(LLR.token_x_cummulative_earned_per_m_subtree_liq), Decimal("2201300334794271053"))
        self.assertEqual(int(LLR.token_y_cummulative_earned_per_m_liq), Decimal("5772069627"))
        self.assertEqual(int(LLR.token_y_cummulative_earned_per_m_subtree_liq), Decimal("519121437518"))

        # LLRR
        self.assertEqual(int(LLRR.token_x_cummulative_earned_per_m_liq), Decimal("2109575308294031901"))
        self.assertEqual(int(LLRR.token_x_cummulative_earned_per_m_subtree_liq), Decimal("2109575308294031901"))
        self.assertEqual(int(LLRR.token_y_cummulative_earned_per_m_liq), Decimal("529154012121"))
        self.assertEqual(int(LLRR.token_y_cummulative_earned_per_m_subtree_liq), Decimal("529154012121"))

        # t_liq
        self.assertEqual(root.t_liq, Decimal("4430"))
        self.assertEqual(L.t_liq, Decimal("77"))
        self.assertEqual(LL.t_liq, Decimal("82734"))
        self.assertEqual(LR.t_liq, Decimal("1111"))
        self.assertEqual(LLR.t_liq, Decimal("5346"))
        self.assertEqual(LLRR.t_liq, Decimal("7635865"))

        # borrowed_x
        self.assertEqual(root.token_x_borrowed, Decimal("492e18"))
        self.assertEqual(L.token_x_borrowed, Decimal("998e18"))
        self.assertEqual(LL.token_x_borrowed, Decimal("765e18"))
        self.assertEqual(LR.token_x_borrowed, Decimal("1024e18"))
        self.assertEqual(LLR.token_x_borrowed, Decimal("53e18"))
        self.assertEqual(LLRR.token_x_borrowed, Decimal("1701e18"))

        # subtree_borrowed_x
        self.assertEqual(root.token_x_subtree_borrowed, Decimal("5033e18"))
        self.assertEqual(L.token_x_subtree_borrowed, Decimal("4541e18"))
        self.assertEqual(LL.token_x_subtree_borrowed, Decimal("2519e18"))
        self.assertEqual(LR.token_x_subtree_borrowed, Decimal("1024e18"))
        self.assertEqual(LLR.token_x_subtree_borrowed, Decimal("1754e18"))
        self.assertEqual(LLRR.token_x_subtree_borrowed, Decimal("1701e18"))

        # borrowed_y
        self.assertEqual(root.token_y_borrowed, Decimal("254858e6"))
        self.assertEqual(L.token_y_borrowed, Decimal("353e6"))
        self.assertEqual(LL.token_y_borrowed, Decimal("99763e6"))
        self.assertEqual(LR.token_y_borrowed, Decimal("1552e6"))
        self.assertEqual(LLR.token_y_borrowed, Decimal("8765e6"))
        self.assertEqual(LLRR.token_y_borrowed, Decimal("780531e6"))

        # subtree_borrowed_y
        self.assertEqual(root.token_y_subtree_borrowed, Decimal("1145822e6"))
        self.assertEqual(L.token_y_subtree_borrowed, Decimal("890964e6"))
        self.assertEqual(LL.token_y_subtree_borrowed, Decimal("889059e6"))
        self.assertEqual(LR.token_y_subtree_borrowed, Decimal("1552e6"))
        self.assertEqual(LLR.token_y_subtree_borrowed, Decimal("789296e6"))
        self.assertEqual(LLRR.token_y_subtree_borrowed, Decimal("780531e6"))

        # T32876298273
        # 3.3) addTLiq
        liq_tree.token_x_fee_rate_snapshot += Decimal("2352954287417905205553")
        liq_tree.token_y_fee_rate_snapshot += Decimal("6117681147286553534438")

        # Apply change that requires fee calculation
        # add_t_liq
        liq_tree.remove_t_liq(LiqRange(low=3, high=7), Decimal("1000"), Decimal("1000e18"), Decimal("1000e6"))  # LLRR, LR

        # root
        self.assertEqual(int(root.token_x_cummulative_earned_per_m_liq), Decimal("1355504472799662735"))
        self.assertEqual(int(root.token_x_cummulative_earned_per_m_subtree_liq), Decimal("8356976045440416914"))
        self.assertEqual(int(root.token_y_cummulative_earned_per_m_liq), Decimal("158359634767"))
        self.assertEqual(int(root.token_y_cummulative_earned_per_m_subtree_liq), Decimal("710730032734"))

        # L
        self.assertEqual(int(L.token_x_cummulative_earned_per_m_liq), Decimal("2750152275007241346"))
        self.assertEqual(int(L.token_x_cummulative_earned_per_m_subtree_liq), Decimal("7002928263843528706"))
        self.assertEqual(int(L.token_y_cummulative_earned_per_m_liq), Decimal("219387193"))
        self.assertEqual(int(L.token_y_cummulative_earned_per_m_subtree_liq), Decimal("552485321384"))

        # LL
        self.assertEqual(int(LL.token_x_cummulative_earned_per_m_liq), Decimal("2108411777738297592"))
        self.assertEqual(int(LL.token_x_cummulative_earned_per_m_subtree_liq), Decimal("4186900096861593203"))
        self.assertEqual(int(LL.token_y_cummulative_earned_per_m_liq), Decimal("62011734490"))
        self.assertEqual(int(LL.token_y_cummulative_earned_per_m_subtree_liq), Decimal("552009051678"))

        # LR
        self.assertEqual(int(LR.token_x_cummulative_earned_per_m_liq), Decimal("426914215366679462837"))
        self.assertEqual(int(LR.token_x_cummulative_earned_per_m_subtree_liq), Decimal("426914215366679462837"))
        self.assertEqual(int(LR.token_y_cummulative_earned_per_m_liq), Decimal("2197372595215"))
        self.assertEqual(int(LR.token_y_cummulative_earned_per_m_subtree_liq), Decimal("2197372595215"))

        # LLR
        self.assertEqual(int(LLR.token_x_cummulative_earned_per_m_liq), Decimal("154755411926283537"))
        self.assertEqual(int(LLR.token_x_cummulative_earned_per_m_subtree_liq), Decimal("2202031695485822406"))
        self.assertEqual(int(LLR.token_y_cummulative_earned_per_m_liq), Decimal("5772079129"))
        self.assertEqual(int(LLR.token_y_cummulative_earned_per_m_subtree_liq), Decimal("519122293205"))

        # LLRR
        self.assertEqual(int(LLRR.token_x_cummulative_earned_per_m_liq), Decimal("2110306406167095651"))
        self.assertEqual(int(LLRR.token_x_cummulative_earned_per_m_subtree_liq), Decimal("2110306406167095651"))
        self.assertEqual(int(LLRR.token_y_cummulative_earned_per_m_liq), Decimal("529154884358"))
        self.assertEqual(int(LLRR.token_y_cummulative_earned_per_m_subtree_liq), Decimal("529154884358"))

        # t_liq
        self.assertEqual(root.t_liq, Decimal("4430"))
        self.assertEqual(L.t_liq, Decimal("77"))
        self.assertEqual(LL.t_liq, Decimal("82734"))
        self.assertEqual(LR.t_liq, Decimal("111"))
        self.assertEqual(LLR.t_liq, Decimal("5346"))
        self.assertEqual(LLRR.t_liq, Decimal("7634865"))

        # subtree_m_liq
        self.assertEqual(root.subtree_m_liq, Decimal("324198833"))
        self.assertEqual(L.subtree_m_liq, Decimal("324063953"))
        self.assertEqual(LL.subtree_m_liq, Decimal("324056493"))
        self.assertEqual(LR.subtree_m_liq, Decimal("4444"))
        self.assertEqual(LLR.subtree_m_liq, Decimal("287725557"))
        self.assertEqual(LLRR.subtree_m_liq, Decimal("287634865"))

        # borrowed_x
        self.assertEqual(root.token_x_borrowed, Decimal("492e18"))
        self.assertEqual(L.token_x_borrowed, Decimal("998e18"))
        self.assertEqual(LL.token_x_borrowed, Decimal("765e18"))
        self.assertEqual(LR.token_x_borrowed, Decimal("24e18"))
        self.assertEqual(LLR.token_x_borrowed, Decimal("53e18"))
        self.assertEqual(LLRR.token_x_borrowed, Decimal("701e18"))

        # subtree_borrowed_x
        self.assertEqual(root.token_x_subtree_borrowed, Decimal("3033e18"))
        self.assertEqual(L.token_x_subtree_borrowed, Decimal("2541e18"))
        self.assertEqual(LL.token_x_subtree_borrowed, Decimal("1519e18"))
        self.assertEqual(LR.token_x_subtree_borrowed, Decimal("24e18"))
        self.assertEqual(LLR.token_x_subtree_borrowed, Decimal("754e18"))
        self.assertEqual(LLRR.token_x_subtree_borrowed, Decimal("701e18"))

        # borrowed_y
        self.assertEqual(root.token_y_borrowed, Decimal("254858e6"))
        self.assertEqual(L.token_y_borrowed, Decimal("353e6"))
        self.assertEqual(LL.token_y_borrowed, Decimal("99763e6"))
        self.assertEqual(LR.token_y_borrowed, Decimal("552e6"))
        self.assertEqual(LLR.token_y_borrowed, Decimal("8765e6"))
        self.assertEqual(LLRR.token_y_borrowed, Decimal("779531e6"))

        # subtree_borrowed_y
        self.assertEqual(root.token_y_subtree_borrowed, Decimal("1143822e6"))
        self.assertEqual(L.token_y_subtree_borrowed, Decimal("888964e6"))
        self.assertEqual(LL.token_y_subtree_borrowed, Decimal("888059e6"))
        self.assertEqual(LR.token_y_subtree_borrowed, Decimal("552e6"))
        self.assertEqual(LLR.token_y_subtree_borrowed, Decimal("788296e6"))
        self.assertEqual(LLRR.token_y_subtree_borrowed, Decimal("779531e6"))

    def test_right_leg_only(self):
        # The results should be exactly the same as the test above.
        # Values are the same. Only the perspective is flipped.

        liq_tree: LiquidityTree = self.liq_tree

        root: LiqNode = liq_tree.root
        R: LiqNode = liq_tree.nodes[(8 << 24) | 24]
        RR: LiqNode = liq_tree.nodes[(4 << 24) | 28]
        RL: LiqNode = liq_tree.nodes[(4 << 24) | 24]
        RRL: LiqNode = liq_tree.nodes[(2 << 24) | 28]
        RRLL: LiqNode = liq_tree.nodes[(1 << 24) | 28]

        # T0 - populate tree with data excluding fee calculations
        liq_tree.add_inf_range_m_liq(Decimal("8430"))                        # root
        liq_tree.add_m_liq(LiqRange(low=8, high=15), Decimal("377"))         # R
        liq_tree.add_m_liq(LiqRange(low=12, high=15), Decimal("9082734"))    # RR
        liq_tree.add_m_liq(LiqRange(low=8, high=11), Decimal("1111"))        # RL
        liq_tree.add_m_liq(LiqRange(low=12, high=13), Decimal("45346"))      # RRL
        liq_tree.add_m_liq(LiqRange(low=12, high=12), Decimal("287634865"))  # RRLL

        liq_tree.add_inf_range_t_liq(Decimal("4430"), Decimal("492e18"), Decimal("254858e6"))                      # root
        liq_tree.add_t_liq(LiqRange(low=8, high=15), Decimal("77"), Decimal("998e18"), Decimal("353e6"))           # R
        liq_tree.add_t_liq(LiqRange(low=12, high=15), Decimal("82734"), Decimal("765e18"), Decimal("99763e6"))     # RR
        liq_tree.add_t_liq(LiqRange(low=8, high=11), Decimal("111"), Decimal("24e18"), Decimal("552e6"))           # RL
        liq_tree.add_t_liq(LiqRange(low=12, high=13), Decimal("5346"), Decimal("53e18"), Decimal("8765e6"))        # RRL
        liq_tree.add_t_liq(LiqRange(low=12, high=12), Decimal("7634865"), Decimal("701e18"), Decimal("779531e6"))  # RRLL

        # m_liq
        self.assertEqual(root.m_liq, Decimal("8430"))
        self.assertEqual(R.m_liq, Decimal("377"))
        self.assertEqual(RR.m_liq, Decimal("9082734"))
        self.assertEqual(RL.m_liq, Decimal("1111"))
        self.assertEqual(RRL.m_liq, Decimal("45346"))
        self.assertEqual(RRLL.m_liq, Decimal("287634865"))

        # t_liq
        self.assertEqual(root.t_liq, Decimal("4430"))
        self.assertEqual(R.t_liq, Decimal("77"))
        self.assertEqual(RR.t_liq, Decimal("82734"))
        self.assertEqual(RL.t_liq, Decimal("111"))
        self.assertEqual(RRL.t_liq, Decimal("5346"))
        self.assertEqual(RRLL.t_liq, Decimal("7634865"))

        # subtree_m_liq
        self.assertEqual(root.subtree_m_liq, Decimal("324198833"))  # 8430*16 + 377*8 + 9082734*4 + 1111*4 + 45346*2 + 287634865*1
        self.assertEqual(R.subtree_m_liq, Decimal("324063953"))     # 377*8 + 9082734*4 + 1111*4 + 45346*2 + 287634865*1
        self.assertEqual(RR.subtree_m_liq, Decimal("324056493"))    # 9082734*4 + 45346*2 + 287634865*1
        self.assertEqual(RL.subtree_m_liq, Decimal("4444"))         # 1111*4
        self.assertEqual(RRL.subtree_m_liq, Decimal("287725557"))   # 45346*2 + 287634865*1
        self.assertEqual(RRLL.subtree_m_liq, Decimal("287634865"))  # 287634865*1

        # borrowed_x
        self.assertEqual(root.token_x_borrowed, Decimal("492e18"))
        self.assertEqual(R.token_x_borrowed, Decimal("998e18"))
        self.assertEqual(RR.token_x_borrowed, Decimal("765e18"))
        self.assertEqual(RL.token_x_borrowed, Decimal("24e18"))
        self.assertEqual(RRL.token_x_borrowed, Decimal("53e18"))
        self.assertEqual(RRLL.token_x_borrowed, Decimal("701e18"))

        # subtree_borrowed_x
        self.assertEqual(root.token_x_subtree_borrowed, Decimal("3033e18"))  # 492e18 + 998e18 + 765e18 + 53e18 + 701e18 + 24e18
        self.assertEqual(R.token_x_subtree_borrowed, Decimal("2541e18"))     # 998e18 + 765e18 + 53e18 + 701e18 + 24e18
        self.assertEqual(RR.token_x_subtree_borrowed, Decimal("1519e18"))    # 765e18 + 53e18 + 701e18
        self.assertEqual(RL.token_x_subtree_borrowed, Decimal("24e18"))      # 24e18
        self.assertEqual(RRL.token_x_subtree_borrowed, Decimal("754e18"))    # 53e18 + 701e18
        self.assertEqual(RRLL.token_x_subtree_borrowed, Decimal("701e18"))   # 701e18

        # borrowed_y
        self.assertEqual(root.token_y_borrowed, Decimal("254858e6"))
        self.assertEqual(R.token_y_borrowed, Decimal("353e6"))
        self.assertEqual(RR.token_y_borrowed, Decimal("99763e6"))
        self.assertEqual(RL.token_y_borrowed, Decimal("552e6"))
        self.assertEqual(RRL.token_y_borrowed, Decimal("8765e6"))
        self.assertEqual(RRLL.token_y_borrowed, Decimal("779531e6"))

        # subtree_borrowed_y
        self.assertEqual(root.token_y_subtree_borrowed, Decimal("1143822e6"))  # 254858e6 + 353e6 + 99763e6 + 8765e6 + 779531e6 + 552e6
        self.assertEqual(R.token_y_subtree_borrowed, Decimal("888964e6"))      # 353e6 + 99763e6 + 8765e6 + 779531e6 + 552e6
        self.assertEqual(RR.token_y_subtree_borrowed, Decimal("888059e6"))     # 99763e6 + 8765e6 + 779531e6
        self.assertEqual(RL.token_y_subtree_borrowed, Decimal("552e6"))        # 552e6
        self.assertEqual(RRL.token_y_subtree_borrowed, Decimal("788296e6"))    # 8765e6 + 779531e6
        self.assertEqual(RRLL.token_y_subtree_borrowed, Decimal("779531e6"))   # 779531e6

        # T98273
        liq_tree.token_x_fee_rate_snapshot += Decimal("4541239648278065")   # 7.9% APR as Q192.64 T98273 - T0
        liq_tree.token_y_fee_rate_snapshot += Decimal("13278814667749784")  # 23.1% APR as Q192.64 T98273 - T0

        # Apply change that requires fee calculation
        # add_m_liq
        liq_tree.add_m_liq(LiqRange(low=8, high=12), Decimal("2734"))  # RRLL, RL

        # root
        #           total_m_liq = subtree_m_liq + aux_level * range
        #           earn_x = rate_diff * borrow / total_m_liq / q_conversion
        #
        #           earn_x     = 4541239648278065 * 492e18 / 324198833 / 2**64 = 373601278.675896709674247960788128930863427771780474615825402
        #           earn_x_sub = 4541239648278065 * 3033e18 / 324198833 / 2**64 = 2303115199.64226569195527248998047773843247242237841363780171
        #
        #           earn_y     = 13278814667749784 * 254858e6 / 324198833 / 2**64 = 0.5658826914495360518450511013487630736056981385516828024975012016
        #           earn_y_sub = 13278814667749784 * 1143822e6 / 324198833 / 2**64 = 2.5397243637601771413630729302079780755472335819729532779755660779
        self.assertEqual(int(root.token_x_cummulative_earned_per_m_liq), Decimal("373601278"))
        self.assertEqual(int(root.token_x_cummulative_earned_per_m_subtree_liq), Decimal("2303115199"))
        self.assertEqual(int(root.token_y_cummulative_earned_per_m_liq), Decimal("0"))
        self.assertEqual(int(root.token_y_cummulative_earned_per_m_subtree_liq), Decimal("2"))

        # R
        #           total_m_liq = 324063953 + 8430 * 8 = 324131393
        #
        #           earn_x      = 4541239648278065 * 998e18 / 324131393 / 2**64 = 757991165.739306427787211084069081135461126639210612444989968
        #           earn_x_sub  = 4541239648278065 * 2541e18 / 324131393 / 2**64 = 1929915382.90939642585902140743440397315302884793002627527005
        #
        #           earn_y      = 13278814667749784 * 353e6 / 324131393 / 2**64 = 0.0007839587228619296743658765199435031723124415958637831459168088
        #           earn_y_sub  = 13278814667749784 * 888964e6 / 324131393 / 2**64 = 1.9742523572527831474305582285412361305143267162194111063081870320
        self.assertEqual(int(R.token_x_cummulative_earned_per_m_liq), Decimal("757991165"))
        self.assertEqual(int(R.token_x_cummulative_earned_per_m_subtree_liq), Decimal("1929915382"))
        self.assertEqual(int(R.token_y_cummulative_earned_per_m_liq), Decimal("0"))
        self.assertEqual(int(R.token_y_cummulative_earned_per_m_subtree_liq), Decimal("1"))

        # RR
        #           total_m_liq = 324056493 + (377 + 8430) * 4 = 324091721
        #
        #           earn_x      = 4541239648278065 * 765e18 / 324091721 / 2**64 = 581096415.560225831923714717876078601550264387092272644849535
        #           earn_x_sub  = 4541239648278065 * 1519e18 / 324091721 / 2**64 = 1153837196.38690593293087928948204365458150536469694398369469
        #
        #           earn_y      = 13278814667749784 * 99763e6 / 324091721 / 2**64 = 0.2215854043845212215658200680605818096232476901747430889861663960
        #           earn_y_sub  = 13278814667749784 * 888059e6 / 324091721 / 2**64 = 1.9724839131974131842719305135352006382347335233392357172695883598
        self.assertEqual(int(RR.token_x_cummulative_earned_per_m_liq), Decimal("581096415"))
        self.assertEqual(int(RR.token_x_cummulative_earned_per_m_subtree_liq), Decimal("1153837196"))
        self.assertEqual(int(RR.token_y_cummulative_earned_per_m_liq), Decimal("0"))
        self.assertEqual(int(RR.token_y_cummulative_earned_per_m_subtree_liq), Decimal("1"))

        # RL
        #           total_m_liq = 4444 + (377 + 8430) * 4 = 39672
        #
        #           earn_x      = 4541239648278065 * 24e18 / 39672 / 2**64 = 148929881804.004419784834421574153374302771710945632482252911
        #           earn_x_sub  = 4541239648278065 * 24e18 / 39672 / 2**64 = 148929881804.004419784834421574153374302771710945632482252911
        #
        #           earn_y      = 13278814667749784 * 552e6 / 39672 / 2**64 = 10.016005848413612945928345245285743980736658202469601316734724742
        #           earn_y_sub  = 13278814667749784 * 552e6 / 39672 / 2**64 = 10.016005848413612945928345245285743980736658202469601316734724742
        self.assertEqual(int(RL.token_x_cummulative_earned_per_m_liq), Decimal("148929881804"))
        self.assertEqual(int(RL.token_x_cummulative_earned_per_m_subtree_liq), Decimal("148929881804"))
        self.assertEqual(int(RL.token_y_cummulative_earned_per_m_liq), Decimal("10"))
        self.assertEqual(int(RL.token_y_cummulative_earned_per_m_subtree_liq), Decimal("10"))

        # RRL
        #           total_m_liq = 287725557 + (9082734 + 377 + 8430) * 2 = 305908639
        #
        #           earn_x      = 4541239648278065 * 53e18 / 305908639 / 2**64 = 42651943.5921096141810155248335108410236545389757231280339726
        #           earn_x_sub  = 4541239648278065 * 754e18 / 305908639 / 2**64 = 606784254.121710360235579353291833474185575894107457330898403
        #
        #           earn_y      = 13278814667749784 * 8765e6 / 305908639 / 2**64 = 0.0206252758466917150640245207131723061423410095348761855275430371
        #           earn_y_sub  = 13278814667749784 * 788296e6 / 305908639 / 2**64 = 1.8549711864054412114215942475882345970088817401374509465624718757
        self.assertEqual(int(RRL.token_x_cummulative_earned_per_m_liq), Decimal("42651943"))
        self.assertEqual(int(RRL.token_x_cummulative_earned_per_m_subtree_liq), Decimal("606784254"))
        self.assertEqual(int(RRL.token_y_cummulative_earned_per_m_liq), Decimal("0"))
        self.assertEqual(int(RRL.token_y_cummulative_earned_per_m_subtree_liq), Decimal("1"))

        # RRLL
        #           total_m_liq = 287634865 + (45346 + 9082734 + 377 + 8430) * 1 = 296771752
        #
        #           earn_x      = 4541239648278065 * 701e18 / 296771752 / 2**64 = 581500584.766017533363270505955415005042190229659676220491523
        #           earn_x_sub  = 4541239648278065 * 701e18 / 296771752 / 2**64 = 581500584.766017533363270505955415005042190229659676220491523
        #
        #           earn_y      = 13278814667749784 * 779531e6 / 296771752 / 2**64 = 1.8908210002218903501728143334071499784764070319492513392714860291
        #           earn_y_sub  = 13278814667749784 * 779531e6 / 296771752 / 2**64 = 1.8908210002218903501728143334071499784764070319492513392714860291
        self.assertEqual(int(RRLL.token_x_cummulative_earned_per_m_liq), Decimal("581500584"))
        self.assertEqual(int(RRLL.token_x_cummulative_earned_per_m_subtree_liq), Decimal("581500584"))
        self.assertEqual(int(RRLL.token_y_cummulative_earned_per_m_liq), Decimal("1"))
        self.assertEqual(int(RRLL.token_y_cummulative_earned_per_m_subtree_liq), Decimal("1"))

        # m_liq
        self.assertEqual(root.m_liq, Decimal("8430"))
        self.assertEqual(R.m_liq, Decimal("377"))
        self.assertEqual(RR.m_liq, Decimal("9082734"))
        self.assertEqual(RL.m_liq, Decimal("3845"))
        self.assertEqual(RRL.m_liq, Decimal("45346"))
        self.assertEqual(RRLL.m_liq, Decimal("287637599"))

        # subtree_m_liq
        self.assertEqual(root.subtree_m_liq, Decimal("324212503"))  # 8430*16 + 377*8 + 9082734*4 + 3845*4 + 45346*2 + 287637599*1
        self.assertEqual(R.subtree_m_liq, Decimal("324077623"))     # 377*8 + 9082734*4 + 3845*4 + 45346*2 + 287637599*1
        self.assertEqual(RR.subtree_m_liq, Decimal("324059227"))    # 9082734*4 + 45346*2 + 287637599*1
        self.assertEqual(RL.subtree_m_liq, Decimal("15380"))        # 3845*4
        self.assertEqual(RRL.subtree_m_liq, Decimal("287728291"))   # 45346*2 + 287637599*1
        self.assertEqual(RRLL.subtree_m_liq, Decimal("287637599"))  # 287637599*1

        # T2876298273
        liq_tree.token_x_fee_rate_snapshot += Decimal("16463537718422861220174597")    # 978567.9% APR as Q192.64 T2876298273 - T98273
        liq_tree.token_y_fee_rate_snapshot += Decimal("3715979586694123491881712207")  # 220872233.1% APR as Q192.64 T2876298273 - T98273

        # Apply change that requires fee calculation
        # remove_m_liq
        liq_tree.remove_m_liq(LiqRange(low=8, high=12), Decimal("2734"))  # RRLL, RL

        # root
        #           total_m_liq = 324212503
        #
        #           earn_x      = 16463537718422861220174597 * 492e18 / 324212503 / 2**64  = 1354374549470516050.18864221581152444619216774937383131887026
        #           earn_x_sub  = 16463537718422861220174597 * 3033e18 / 324212503 / 2**64 = 8349223594601778821.58973951332592204329439996717648453279172
        #
        #           earn_y      = 3715979586694123491881712207 * 254858e6 / 324212503 / 2**64  = 158351473403.760477087118657111090258803416110827691474619042
        #           earn_y_sub  = 3715979586694123491881712207 * 1143822e6 / 324212503 / 2**64 = 710693401861.570429112455707155049015549996557766096092261976
        self.assertEqual(int(root.token_x_cummulative_earned_per_m_liq), Decimal("1354374549844117328"))          # 373601278 + 1354374549470516050 = 1354374549844117328
        self.assertEqual(int(root.token_x_cummulative_earned_per_m_subtree_liq), Decimal("8349223596904894020"))  # 2303115199 + 8349223594601778821 = 8349223596904894020
        self.assertEqual(int(root.token_y_cummulative_earned_per_m_liq), Decimal("158351473403"))                 # 0 + 158351473403 = 158351473403
        self.assertEqual(int(root.token_y_cummulative_earned_per_m_subtree_liq), Decimal("710693401863"))         # 2 + 710693401861 = 710693401863

        # R
        #           total_m_liq = 324077623 + 8430 * 8 = 324145063
        #
        #           earn_x      = 16463537718422861220174597 * 998e18 / 324145063 / 2**64  = 2747859799177149412.40503918202324257122793136834755591677703
        #           earn_x_sub  = 16463537718422861220174597 * 2541e18 / 324145063 / 2**64 = 6996304358425988634.18958372897901740830678718133380719892830
        #
        #           earn_y      = 3715979586694123491881712207 * 353e6 / 324145063 / 2**64    = 219375887.687723491736647414380713113554572979392890952782027
        #           earn_y_sub  = 3715979586694123491881712207 * 888964e6 / 324145063 / 2**64 = 552456845955.890725518915105035513462543703722529807118835474
        self.assertEqual(int(R.token_x_cummulative_earned_per_m_liq), Decimal("2747859799935140577"))          # 757991165 + 2747859799177149412 = 2747859799935140577
        self.assertEqual(int(R.token_x_cummulative_earned_per_m_subtree_liq), Decimal("6996304360355904016"))  # 1929915382 + 6996304358425988634 = 6996304360355904016
        self.assertEqual(int(R.token_y_cummulative_earned_per_m_liq), Decimal("219375887"))                    # 0 + 219375887 = 219375887 = 219375887
        self.assertEqual(int(R.token_y_cummulative_earned_per_m_subtree_liq), Decimal("552456845956"))         # 1 + 552456845955 = 552456845956

        # RR
        #           total_m_liq = 324059227 + (377 + 8430) * 4 = 324094455
        #
        #           earn_x      = 16463537718422861220174597 * 765e18 / 324094455 / 2**64 = 2106654304105573173.10473569019029577351750175393657598084186
        #           earn_x_sub  = 16463537718422861220174597 * 1519e18 / 324094455 / 2**64 = 4183016846975641372.47855361228635199996481720814334498679581
        #
        #           earn_y      = 3715979586694123491881712207 * 99763e6 / 324094455 / 2**64  = 62008538706.1288411875002441524622314240784801570453009535875
        #           earn_y_sub  = 3715979586694123491881712207 * 888059e6 / 324094455 / 2**64 = 551980602776.841840924293368501262560029627326862519099461143
        self.assertEqual(int(RR.token_x_cummulative_earned_per_m_liq), Decimal("2106654304686669588"))          # 581096415 + 2106654304105573173 = 2106654304686669588
        self.assertEqual(int(RR.token_x_cummulative_earned_per_m_subtree_liq), Decimal("4183016848129478568"))  # 1153837196 + 4183016846975641372 = 4183016848129478568
        self.assertEqual(int(RR.token_y_cummulative_earned_per_m_liq), Decimal("62008538706"))                  # 0 + 62008538706 = 62008538706
        self.assertEqual(int(RR.token_y_cummulative_earned_per_m_subtree_liq), Decimal("551980602777"))         # 1 + 551980602776 = 551980602777

        # RL
        #           total_m_liq = 15380 + (377 + 8430) * 4 = 50608
        #
        #           earn_x      = 16463537718422861220174597 * 24e18 / 50608 / 2**64 = 423248577958689008325.429426909965566945601510047930853109815
        #           earn_x_sub  = 16463537718422861220174597 * 24e18 / 50608 / 2**64 = 423248577958689008325.429426909965566945601510047930853109815
        #
        #           earn_y      = 3715979586694123491881712207 * 552e6 / 50608 / 2**64 = 2197219781185.45157550848350683783177940360867452683580030548
        #           earn_y_sub  = 3715979586694123491881712207 * 552e6 / 50608 / 2**64 = 2197219781185.45157550848350683783177940360867452683580030548
        self.assertEqual(int(RL.token_x_cummulative_earned_per_m_liq), Decimal("423248578107618890129"))          # 148929881804 + 423248577958689008325 = 423248578107618890129
        self.assertEqual(int(RL.token_x_cummulative_earned_per_m_subtree_liq), Decimal("423248578107618890129"))  # 148929881804 + 423248577958689008325 = 423248578107618890129
        self.assertEqual(int(RL.token_y_cummulative_earned_per_m_liq), Decimal("2197219781195"))                  # 10 + 2197219781185 = 2197219781195
        self.assertEqual(int(RL.token_y_cummulative_earned_per_m_subtree_liq), Decimal("2197219781195"))          # 10 + 2197219781185 = 2197219781195

        # RRL
        #           total_m_liq = 287728291 + (9082734 + 377 + 8430) * 2 = 305911373
        #
        #           earn_x      = 16463537718422861220174597 * 53e18 / 305911373 / 2**64 = 154626414974589533.957746783298485424790431468186321359344549
        #           earn_x_sub  = 16463537718422861220174597 * 754e18 / 305911373 / 2**64 = 2199779563978122803.85171838881241528852802503797143971595830
        #
        #           earn_y      = 3715979586694123491881712207 * 8765e6 / 305911373 / 2**64 = 5771781665.52844938596716448955303604219154769320799186650875
        #           earn_y_sub  = 3715979586694123491881712207 * 788296e6 / 305911373 / 2**64 = 519095539054.126016789546137872983468330339792397614050929992
        self.assertEqual(int(RRL.token_x_cummulative_earned_per_m_liq), Decimal("154626415017241476"))           # 42651943 + 154626414974589533 = 154626415017241476 (sol losses 1 wei)
        self.assertEqual(int(RRL.token_x_cummulative_earned_per_m_subtree_liq), Decimal("2199779564584907057"))  # 606784254 + 2199779563978122803 = 2199779564584907057
        self.assertEqual(int(RRL.token_y_cummulative_earned_per_m_liq), Decimal("5771781665"))                   # 0 + 5771781665 = 5771781665
        self.assertEqual(int(RRL.token_y_cummulative_earned_per_m_subtree_liq), Decimal("519095539055"))         # 1 + 519095539054 = 519095539055

        # RRLL
        #           total_m_liq = 287637599 + (45346 + 9082734 + 377 + 8430) * 1 = 296774486
        #
        #           earn_x      = 16463537718422861220174597 * 701e18 / 296774486 / 2**64 = 2108117905415037748.37451632639936795389368532390933657093156
        #           earn_x_sub  = 16463537718422861220174597 * 701e18 / 296774486 / 2**64 = 2108117905415037748.37451632639936795389368532390933657093156
        #
        #           earn_y      = 3715979586694123491881712207 * 779531e6 / 296774486 / 2**64 = 529127613134.050803777279185858502873428448836282593499892809
        #           earn_y_sub  = 3715979586694123491881712207 * 779531e6 / 296774486 / 2**64 = 529127613134.050803777279185858502873428448836282593499892809
        self.assertEqual(int(RRLL.token_x_cummulative_earned_per_m_liq), Decimal("2108117905996538332"))          # 581500584 + 2108117905415037748 = 2108117905996538332
        self.assertEqual(int(RRLL.token_x_cummulative_earned_per_m_subtree_liq), Decimal("2108117905996538332"))  # 581500584 + 2108117905415037748 = 2108117905996538332
        self.assertEqual(int(RRLL.token_y_cummulative_earned_per_m_liq), Decimal("529127613135"))                 # 1 + 529127613134 = 529127613135
        self.assertEqual(int(RRLL.token_y_cummulative_earned_per_m_subtree_liq), Decimal("529127613135"))         # 1 + 529127613134 = 529127613135

        # m_liq
        self.assertEqual(root.m_liq, Decimal("8430"))
        self.assertEqual(R.m_liq, Decimal("377"))
        self.assertEqual(RR.m_liq, Decimal("9082734"))
        self.assertEqual(RL.m_liq, Decimal("1111"))
        self.assertEqual(RRL.m_liq, Decimal("45346"))
        self.assertEqual(RRLL.m_liq, Decimal("287634865"))

        # subtree_m_liq
        self.assertEqual(root.subtree_m_liq, Decimal("324198833"))
        self.assertEqual(R.subtree_m_liq, Decimal("324063953"))
        self.assertEqual(RR.subtree_m_liq, Decimal("324056493"))
        self.assertEqual(RL.subtree_m_liq, Decimal("4444"))
        self.assertEqual(RRL.subtree_m_liq, Decimal("287725557"))
        self.assertEqual(RRLL.subtree_m_liq, Decimal("287634865"))

        # T9214298113
        liq_tree.token_x_fee_rate_snapshot += Decimal("11381610389149375791104")   # 307% APR as Q192.64 T9214298113 - T2876298273
        liq_tree.token_y_fee_rate_snapshot += Decimal("185394198934916215865344")  # 5000.7% APR as Q192.64 T9214298113 - T2876298273

        # Apply change that requires fee calculation
        # add_t_liq
        liq_tree.add_t_liq(LiqRange(low=8, high=12), Decimal("1000"), Decimal("1000e18"), Decimal("1000e6"))  # RRLL, RL

        # root
        #           total_m_liq = 324198833
        #
        #           earn_x      = 11381610389149375791104 * 492e18 / 324198833 / 2**64  = 936348777891386.743735803607164207960477914490210395050990205
        #           earn_x_sub  = 11381610389149375791104 * 3033e18 / 324198833 / 2**64 = 5772247649074341.45071278931001837956123885091221164266189693
        #
        #           earn_y      = 185394198934916215865344 * 254858e6 / 324198833 / 2**64  = 7900657.61872699474175109887651599451346454839027751836478695
        #           earn_y_sub  = 185394198934916215865344 * 1143822e6 / 324198833 / 2**64 = 35458749.5733606501640098620374258523427949943453374491326438
        self.assertEqual(int(root.token_x_cummulative_earned_per_m_liq), Decimal("1355310898622008714"))          # 373601278 + 1354374549470516050 + 936348777891386 = 1355310898622008714
        self.assertEqual(int(root.token_x_cummulative_earned_per_m_subtree_liq), Decimal("8354995844553968361"))  # 2303115199 + 8349223594601778821 + 5772247649074341 = 8354995844553968361
        self.assertEqual(int(root.token_y_cummulative_earned_per_m_liq), Decimal("158359374060"))                 # 0 + 158351473403 + 7900657 = 158359374060
        self.assertEqual(int(root.token_y_cummulative_earned_per_m_subtree_liq), Decimal("710728860612"))         # 2 + 710693401861 + 35458749 = 710728860612

        # R
        #           total_m_liq = 324063953 + 8430 * 8 = 324131393
        #
        #           earn_x      = 11381610389149375791104 * 998e18 / 324131393 / 2**64  = 1899736810880077.58842507649572740061066261792173891653870132
        #           earn_x_sub  = 11381610389149375791104 * 2541e18 / 324131393 / 2**64 = 4836905046539355.86391595127819972440049470154222303299082171
        #
        #           earn_y      = 185394198934916215865344 * 353e6 / 324131393 / 2**64    = 10945.359436035932129843115196215424291564802240553108041589788249
        #           earn_y_sub  = 185394198934916215865344 * 888964e6 / 324131393 / 2**64 = 27563825.7951735024642318840149814403397354471925525584619938
        self.assertEqual(int(R.token_x_cummulative_earned_per_m_liq), Decimal("2749759536746020654"))          # 757991165 + 2747859799177149412 + 1899736810880077 = 2749759536746020654
        self.assertEqual(int(R.token_x_cummulative_earned_per_m_subtree_liq), Decimal("7001141265402443371"))  # 1929915382 + 6996304358425988634 + 4836905046539355 = 7001141265402443371
        self.assertEqual(int(R.token_y_cummulative_earned_per_m_liq), Decimal("219386832"))                    # 0 + 219375887 + 10945 = 219386832
        self.assertEqual(int(R.token_y_cummulative_earned_per_m_subtree_liq), Decimal("552484409781"))         # 1 + 552456845955 + 27563825 = 552484409781

        # RR
        #           total_m_liq = 324056493 + (377 + 8430) * 4 = 324091721
        #
        #           earn_x      = 11381610389149375791104 * 765e18 / 324091721 / 2**64  = 1456389336983247.97581853577374895245788594982344519686141566
        #           earn_x_sub  = 11381610389149375791104 * 1519e18 / 324091721 / 2**64 = 2891837127944514.60819392920303876965167157879975588762417044
        #
        #           earn_y      = 185394198934916215865344 * 99763e6 / 324091721 / 2**64  = 3093698.46401352576654665825318763474490453834363760251685046
        #           earn_y_sub  = 185394198934916215865344 * 888059e6 / 324091721 / 2**64 = 27539135.3934162733549879091613880669579421169863823827823111
        self.assertEqual(int(RR.token_x_cummulative_earned_per_m_liq), Decimal("2108110694023652835"))          # 581096415 + 2106654304105573173+ 1456389336983247 = 2108110694023652835
        self.assertEqual(int(RR.token_x_cummulative_earned_per_m_subtree_liq), Decimal("4185908685257423082"))  # 1153837196 + 4183016846975641372 + 2891837127944514 = 4185908685257423082
        self.assertEqual(int(RR.token_y_cummulative_earned_per_m_liq), Decimal("62011632404"))                  # 0 + 62008538706 + 3093698 = 62011632404
        self.assertEqual(int(RR.token_y_cummulative_earned_per_m_subtree_liq), Decimal("552008141912"))         # 1 + 551980602776 + 27539135 = 552008141912

        # RL
        #           total_m_liq = 4444 + (377 + 8430) * 4 = 39672
        #
        #           earn_x      = 11381610389149375791104 * 24e18 / 39672 / 2**64 = 373259731104033296.286645111573225645606473079249848759830611
        #           earn_x_sub  = 11381610389149375791104 * 24e18 / 39672 / 2**64 = 373259731104033296.286645111573225645606473079249848759830611
        #
        #           earn_y      = 185394198934916215865344 * 552e6 / 39672 / 2**64 = 139839995.304998697233270837982279275016069267997580157289776
        #           earn_y_sub  = 185394198934916215865344 * 552e6 / 39672 / 2**64 = 139839995.304998697233270837982279275016069267997580157289776
        self.assertEqual(int(RL.token_x_cummulative_earned_per_m_liq), Decimal("423621837838722923425"))          # 148929881804 + 423248577958689008325 + 373259731104033296 = 423621837838722923425
        self.assertEqual(int(RL.token_x_cummulative_earned_per_m_subtree_liq), Decimal("423621837838722923425"))  # 148929881804 + 423248577958689008325 + 373259731104033296 = 423621837838722923425
        self.assertEqual(int(RL.token_y_cummulative_earned_per_m_liq), Decimal("2197359621190"))                  # 10 + 2197219781185 + 139839995 = 2197359621190
        self.assertEqual(int(RL.token_y_cummulative_earned_per_m_subtree_liq), Decimal("2197359621190"))          # 10 + 2197219781185 + 139839995 = 2197359621190

        # RRL
        #           total_m_liq = 287725557 + (9082734 + 377 + 8430) * 2 = 305908639
        #
        #           earn_x      = 11381610389149375791104 * 53e18 / 305908639 / 2**64  = 106897640711262.335596794608928382455998365904272484439381916
        #           earn_x_sub  = 11381610389149375791104 * 754e18 / 305908639 / 2**64 = 1520770209363996.24603741764400000701552392248719723145837669
        #
        #           earn_y      = 185394198934916215865344 * 8765e6 / 305908639 / 2**64   = 287962.93864210284405202260308978443477406072046236000546555339354
        #           earn_y_sub  = 185394198934916215865344 * 788296e6 / 305908639 / 2**64 = 25898463.5116731435886860479093285465823905270619049107665115
        self.assertEqual(int(RRL.token_x_cummulative_earned_per_m_liq), Decimal("154733312657952738"))           # 42651943 + 154626414974589533 + 106897640711262 = 154733312657952738
        self.assertEqual(int(RRL.token_x_cummulative_earned_per_m_subtree_liq), Decimal("2201300334794271053"))  # 606784254 + 2199779563978122803 + 1520770209363996 = 2201300334794271053
        self.assertEqual(int(RRL.token_y_cummulative_earned_per_m_liq), Decimal("5772069627"))                   # 0 + 5771781665 + 287962 = 5772069627
        self.assertEqual(int(RRL.token_y_cummulative_earned_per_m_subtree_liq), Decimal("519121437518"))         # 1 + 519095539054 + 25898463 = 519121437518

        # RRLL
        #           total_m_liq = 287634865 + (45346 + 9082734 + 377 + 8430) * 1 = 296771752
        #
        #           earn_x      = 11381610389149375791104 * 701e18 / 296771752 / 2**64 = 1457402297493569.71876500861500730007660377831377967536479010
        #           earn_x_sub  = 11381610389149375791104 * 701e18 / 296771752 / 2**64 = 1457402297493569.71876500861500730007660377831377967536479010
        #
        #           earn_y      = 185394198934916215865344 * 779531e6 / 296771752 / 2**64 = 26398986.1622835510939886934876573358559478744206759947961624
        #           earn_y_sub  = 185394198934916215865344 * 779531e6 / 296771752 / 2**64 = 26398986.1622835510939886934876573358559478744206759947961624
        self.assertEqual(int(RRLL.token_x_cummulative_earned_per_m_liq), Decimal("2109575308294031901"))          # 581500584 + 2108117905415037748 + 1457402297493569 = 2109575308294031901
        self.assertEqual(int(RRLL.token_x_cummulative_earned_per_m_subtree_liq), Decimal("2109575308294031901"))  # 581500584 + 2108117905415037748 + 1457402297493569 = 2109575308294031901
        self.assertEqual(int(RRLL.token_y_cummulative_earned_per_m_liq), Decimal("529154012121"))                 # 1 + 529127613134 + 26398986 = 529154012121
        self.assertEqual(int(RRLL.token_y_cummulative_earned_per_m_subtree_liq), Decimal("529154012121"))         # 1 + 529127613134 + 26398986 = 529154012121

        # t_liq
        self.assertEqual(root.t_liq, Decimal("4430"))
        self.assertEqual(R.t_liq, Decimal("77"))
        self.assertEqual(RR.t_liq, Decimal("82734"))
        self.assertEqual(RL.t_liq, Decimal("1111"))
        self.assertEqual(RRL.t_liq, Decimal("5346"))
        self.assertEqual(RRLL.t_liq, Decimal("7635865"))

        # borrowed_x
        self.assertEqual(root.token_x_borrowed, Decimal("492e18"))
        self.assertEqual(R.token_x_borrowed, Decimal("998e18"))
        self.assertEqual(RR.token_x_borrowed, Decimal("765e18"))
        self.assertEqual(RL.token_x_borrowed, Decimal("1024e18"))
        self.assertEqual(RRL.token_x_borrowed, Decimal("53e18"))
        self.assertEqual(RRLL.token_x_borrowed, Decimal("1701e18"))

        # subtree_borrowed_x
        self.assertEqual(root.token_x_subtree_borrowed, Decimal("5033e18"))  # 492e18 + 998e18 + 765e18 + 53e18 + 701e18 + 24e18
        self.assertEqual(R.token_x_subtree_borrowed, Decimal("4541e18"))     # 998e18 + 765e18 + 53e18 + 701e18 + 24e18
        self.assertEqual(RR.token_x_subtree_borrowed, Decimal("2519e18"))    # 765e18 + 53e18 + 701e18
        self.assertEqual(RL.token_x_subtree_borrowed, Decimal("1024e18"))
        self.assertEqual(RRL.token_x_subtree_borrowed, Decimal("1754e18"))   # 53e18 + 701e18
        self.assertEqual(RRLL.token_x_subtree_borrowed, Decimal("1701e18"))  # 701e18

        # borrowed_y
        self.assertEqual(root.token_y_borrowed, Decimal("254858e6"))
        self.assertEqual(R.token_y_borrowed, Decimal("353e6"))
        self.assertEqual(RR.token_y_borrowed, Decimal("99763e6"))
        self.assertEqual(RL.token_y_borrowed, Decimal("1552e6"))
        self.assertEqual(RRL.token_y_borrowed, Decimal("8765e6"))
        self.assertEqual(RRLL.token_y_borrowed, Decimal("780531e6"))

        # subtree_borrowed_y
        self.assertEqual(root.token_y_subtree_borrowed, Decimal("1145822e6"))  # 254858e6 + 353e6 + 99763e6 + 8765e6 + 779531e6 + 552e6
        self.assertEqual(R.token_y_subtree_borrowed, Decimal("890964e6"))      # 353e6 + 99763e6 + 8765e6 + 779531e6 + 552e6
        self.assertEqual(RR.token_y_subtree_borrowed, Decimal("889059e6"))     # 99763e6 + 8765e6 + 779531e6
        self.assertEqual(RL.token_y_subtree_borrowed, Decimal("1552e6"))
        self.assertEqual(RRL.token_y_subtree_borrowed, Decimal("789296e6"))    # 8765e6 + 779531e6
        self.assertEqual(RRLL.token_y_subtree_borrowed, Decimal("780531e6"))   # 779531e6

        # T32876298273
        # 3.3) addTLiq
        liq_tree.token_x_fee_rate_snapshot += Decimal("2352954287417905205553")  # 17% APR as Q192.64 T32876298273 - T9214298113
        liq_tree.token_y_fee_rate_snapshot += Decimal("6117681147286553534438")  # 44.2% APR as Q192.64 T32876298273 - T9214298113

        # Apply change that requires fee calculation
        # remove_t_liq
        liq_tree.remove_t_liq(LiqRange(low=8, high=12), Decimal("1000"), Decimal("1000e18"), Decimal("1000e6"))  # RRLL, RL

        # root
        #           total_m_liq = 324198833
        #
        #           earn_x      = 2352954287417905205553 * 492e18 / 324198833 / 2**64  = 193574177654021.169606366690127570750614868262308175138961180
        #           earn_x_sub  = 2352954287417905205553 * 5033e18 / 324198833 / 2**64 = 1980200886448553.95656269014514647070700128448007529567965776
        #
        #           earn_y      = 6117681147286553534438 * 254858e6 / 324198833 / 2**64  = 260707.74837037839600245251693715160678794344236990061534290681026
        #           earn_y_sub  = 6117681147286553534438 * 1145822e6 / 324198833 / 2**64 = 1172122.01952947804057287645615189999290967884478087508680692
        self.assertEqual(int(root.token_x_cummulative_earned_per_m_liq), Decimal("1355504472799662735"))         # 373601278 + 1354374549470516050 + 936348777891386 + 193574177654021 = 1355504472799662735
        self.assertEqual(int(root.token_x_cummulative_earned_per_m_subtree_liq), Decimal("8356976045440416914")) # 2303115199 + 8349223594601778821 + 5772247649074341 + 1980200886448553 = 8356976045440416914
        self.assertEqual(int(root.token_y_cummulative_earned_per_m_liq), Decimal("158359634767"))                # 0 + 158351473403 + 7900657 + 260707 = 158359634767
        self.assertEqual(int(root.token_y_cummulative_earned_per_m_subtree_liq), Decimal("710730032734"))        # 2 + 710693401861 + 35458749 + 1172122 = 710730032734

        # R
        #           total_m_liq = 324063953 + 8430 * 8 = 324131393
        #
        #           earn_x      = 2352954287417905205553 * 998e18 / 324131393 / 2**64  = 392738261220692.635199129066166314911263418663640357414414483
        #           earn_x_sub  = 2352954287417905205553 * 4541e18 / 324131393 / 2**64 = 1786998441085335.92829583676298721043291301017193473248382381
        #
        #           earn_y      = 6117681147286553534438 * 353e6 / 324131393 / 2**64    = 361.17753121077324707993230558447820693195086120933424789750836934
        #           earn_y_sub  = 6117681147286553534438 * 890964e6 / 324131393 / 2**64 = 911603.90344950531249667084054608793530005288132156736216361373026
        self.assertEqual(int(R.token_x_cummulative_earned_per_m_liq), Decimal("2750152275007241346"))          # 757991165 + 2747859799177149412 + 1899736810880077 + 392738261220692 = 2750152275007241346
        self.assertEqual(int(R.token_x_cummulative_earned_per_m_subtree_liq), Decimal("7002928263843528706"))  # 1929915382 + 6996304358425988634 + 4836905046539355 + 1786998441085335 = 7002928263843528706
        self.assertEqual(int(R.token_y_cummulative_earned_per_m_liq), Decimal("219387193"))                    # 0 + 219375887 + 10945 + 361 = 219387193
        self.assertEqual(int(R.token_y_cummulative_earned_per_m_subtree_liq), Decimal("552485321384"))         # 1 + 552456845955 + 27563825 + 911603 = 552485321384

        # RR
        #           total_m_liq = 324056493 + (377 + 8430) * 4 = 324091721
        #
        #           earn_x      = 2352954287417905205553 * 765e18 / 324091721 / 2**64  = 301083714644757.116282263044928314612316183509300881282164628
        #           earn_x_sub  = 2352954287417905205553 * 2519e18 / 324091721 / 2**64 = 991411604170121.798581726287809705239770544130626039150029671
        #
        #           earn_y      = 6117681147286553534438 * 99763e6 / 324091721 / 2**64  = 102086.58565055261555338276382365173781133864709615634713615821960
        #           earn_y_sub  = 6117681147286553534438 * 889059e6 / 324091721 / 2**64 = 909766.12323100405793004346924503062625232727813579850073199172604
        self.assertEqual(int(RR.token_x_cummulative_earned_per_m_liq), Decimal("2108411777738297592"))          # 581096415 + 2106654304105573173+ 1456389336983247 + 301083714644757 = 2108411777738297592
        self.assertEqual(int(RR.token_x_cummulative_earned_per_m_subtree_liq), Decimal("4186900096861593203"))  # 1153837196 + 4183016846975641372 + 2891837127944514 + 991411604170121 = 4186900096861593203
        self.assertEqual(int(RR.token_y_cummulative_earned_per_m_liq), Decimal("62011734490"))                  # 0 + 62008538706 + 3093698 + 102086 = 62011734490
        self.assertEqual(int(RR.token_y_cummulative_earned_per_m_subtree_liq), Decimal("552009051678"))         # 1 + 551980602776 + 27539135 + 909766 = 552009051678

        # RL
        #           total_m_liq = 4444 + (377 + 8430) * 4 = 39672
        #
        #           earn_x      = 2352954287417905205553 * 1024e18 / 39672 / 2**64 = 3292377527956539412.11877691362144195603424231355578266196876
        #           earn_x_sub  = 2352954287417905205553 * 1024e18 / 39672 / 2**64 = 3292377527956539412.11877691362144195603424231355578266196876
        #
        #           earn_y      = 6117681147286553534438 * 1552e6 / 39672 / 2**64 = 12974025.1961037381208809794236997935340918048320067315891063
        #           earn_y_sub  = 6117681147286553534438 * 1552e6 / 39672 / 2**64 = 12974025.1961037381208809794236997935340918048320067315891063
        self.assertEqual(int(RL.token_x_cummulative_earned_per_m_liq), Decimal("426914215366679462837"))          # 148929881804 + 423248577958689008325 + 373259731104033296 + 3292377527956539412 = 426914215366679462837
        self.assertEqual(int(RL.token_x_cummulative_earned_per_m_subtree_liq), Decimal("426914215366679462837"))  # 148929881804 + 423248577958689008325 + 373259731104033296 + 3292377527956539412 = 426914215366679462837
        self.assertEqual(int(RL.token_y_cummulative_earned_per_m_liq), Decimal("2197372595215"))                  # 10 + 2197219781185 + 139839995 + 12974025 = 2197372595215
        self.assertEqual(int(RL.token_y_cummulative_earned_per_m_subtree_liq), Decimal("2197372595215"))          # 10 + 2197219781185 + 139839995 + 12974025 = 2197372595215

        # RRL
        #           total_m_liq = 287725557 + (9082734 + 377 + 8430) * 2 = 305908639
        #
        #           earn_x      = 2352954287417905205553 * 53e18 / 305908639 / 2**64   = 22099268330799.1616184419285239088656103478160451926038962236
        #           earn_x_sub  = 2352954287417905205553 * 1754e18 / 305908639 / 2**64 = 731360691551353.386391455521338417929821699421571091079886346
        #
        #           earn_y      = 6117681147286553534438 * 8765e6 / 305908639 / 2**64   = 9502.2684149166432853337655386227368949210477797554902569919214852
        #           earn_y_sub  = 6117681147286553534438 * 789296e6 / 305908639 / 2**64 = 855687.67265488270148782656070425233773115839456587443672363898010
        self.assertEqual(int(RRL.token_x_cummulative_earned_per_m_liq), Decimal("154755411926283537"))           # 42651943 + 154626414974589533 + 106897640711262 + 22099268330799 = 154755411926283537
        self.assertEqual(int(RRL.token_x_cummulative_earned_per_m_subtree_liq), Decimal("2202031695485822406"))  # 606784254 + 2199779563978122803 + 1520770209363996 + 731360691551353 = 2202031695485822406
        self.assertEqual(int(RRL.token_y_cummulative_earned_per_m_liq), Decimal("5772079129"))                   # 0 + 5771781665 + 287962 + 9502 = 5772079129
        self.assertEqual(int(RRL.token_y_cummulative_earned_per_m_subtree_liq), Decimal("519122293205"))         # 1 + 519095539054 + 25898463 + 855687 = 519122293205

        # RRLL
        #           total_m_liq = 287634865 + (45346 + 9082734 + 377 + 8430) * 1 = 296771752
        #
        #           earn_x      = 2352954287417905205553 * 1701e18 / 296771752 / 2**64 = 731097873063750.150068233826063023165648387512288880115659770
        #           earn_x_sub  = 2352954287417905205553 * 1701e18 / 296771752 / 2**64 = 731097873063750.150068233826063023165648387512288880115659770
        #
        #           earn_y      = 6117681147286553534438 * 780531e6 / 296771752 / 2**64 = 872237.41346080959306032387265895687662997868016869971844802082307
        #           earn_y_sub  = 6117681147286553534438 * 780531e6 / 296771752 / 2**64 = 872237.41346080959306032387265895687662997868016869971844802082307
        self.assertEqual(int(RRLL.token_x_cummulative_earned_per_m_liq), Decimal("2110306406167095651"))          # 581500584 + 2108117905415037748 + 1457402297493569 + 731097873063750 = 2110306406167095651
        self.assertEqual(int(RRLL.token_x_cummulative_earned_per_m_subtree_liq), Decimal("2110306406167095651"))  # 581500584 + 2108117905415037748 + 1457402297493569 + 731097873063750 = 2110306406167095651
        self.assertEqual(int(RRLL.token_y_cummulative_earned_per_m_liq), Decimal("529154884358"))                 # 1 + 529127613134 + 26398986 + 872237 = 529154884358
        self.assertEqual(int(RRLL.token_y_cummulative_earned_per_m_subtree_liq), Decimal("529154884358"))         # 1 + 529127613134 + 26398986 + 872237 = 529154884358

        # t_liq
        self.assertEqual(root.t_liq, Decimal("4430"))
        self.assertEqual(R.t_liq, Decimal("77"))
        self.assertEqual(RR.t_liq, Decimal("82734"))
        self.assertEqual(RL.t_liq, Decimal("111"))
        self.assertEqual(RRL.t_liq, Decimal("5346"))
        self.assertEqual(RRLL.t_liq, Decimal("7634865"))

        # subtree_m_liq
        self.assertEqual(root.subtree_m_liq, Decimal("324198833"))  # 8430*16 + 377*8 + 9082734*4 + 1111*4 + 45346*2 + 287634865*1
        self.assertEqual(R.subtree_m_liq, Decimal("324063953"))     # 377*8 + 9082734*4 + 1111*4 + 45346*2 + 287634865*1
        self.assertEqual(RR.subtree_m_liq, Decimal("324056493"))    # 9082734*4 + 45346*2 + 287634865*1
        self.assertEqual(RL.subtree_m_liq, Decimal("4444"))         # 1111*4
        self.assertEqual(RRL.subtree_m_liq, Decimal("287725557"))   # 45346*2 + 287634865*1
        self.assertEqual(RRLL.subtree_m_liq, Decimal("287634865"))  # 287634865*1

        # borrowed_x
        self.assertEqual(root.token_x_borrowed, Decimal("492e18"))
        self.assertEqual(R.token_x_borrowed, Decimal("998e18"))
        self.assertEqual(RR.token_x_borrowed, Decimal("765e18"))
        self.assertEqual(RL.token_x_borrowed, Decimal("24e18"))
        self.assertEqual(RRL.token_x_borrowed, Decimal("53e18"))
        self.assertEqual(RRLL.token_x_borrowed, Decimal("701e18"))

        # subtree_borrowed_x
        self.assertEqual(root.token_x_subtree_borrowed, Decimal("3033e18"))  # 492e18 + 998e18 + 765e18 + 53e18 + 701e18 + 24e18
        self.assertEqual(R.token_x_subtree_borrowed, Decimal("2541e18"))     # 998e18 + 765e18 + 53e18 + 701e18 + 24e18
        self.assertEqual(RR.token_x_subtree_borrowed, Decimal("1519e18"))    # 765e18 + 53e18 + 701e18
        self.assertEqual(RL.token_x_subtree_borrowed, Decimal("24e18"))
        self.assertEqual(RRL.token_x_subtree_borrowed, Decimal("754e18"))   # 53e18 + 701e18
        self.assertEqual(RRLL.token_x_subtree_borrowed, Decimal("701e18"))  # 701e18

        # borrowed_y
        self.assertEqual(root.token_y_borrowed, Decimal("254858e6"))
        self.assertEqual(R.token_y_borrowed, Decimal("353e6"))
        self.assertEqual(RR.token_y_borrowed, Decimal("99763e6"))
        self.assertEqual(RL.token_y_borrowed, Decimal("552e6"))
        self.assertEqual(RRL.token_y_borrowed, Decimal("8765e6"))
        self.assertEqual(RRLL.token_y_borrowed, Decimal("779531e6"))

        # subtree_borrowed_y
        self.assertEqual(root.token_y_subtree_borrowed, Decimal("1143822e6"))  # 254858e6 + 353e6 + 99763e6 + 8765e6 + 779531e6 + 552e6
        self.assertEqual(R.token_y_subtree_borrowed, Decimal("888964e6"))      # 353e6 + 99763e6 + 8765e6 + 779531e6 + 552e6
        self.assertEqual(RR.token_y_subtree_borrowed, Decimal("888059e6"))     # 99763e6 + 8765e6 + 779531e6
        self.assertEqual(RL.token_y_subtree_borrowed, Decimal("552e6"))
        self.assertEqual(RRL.token_y_subtree_borrowed, Decimal("788296e6"))    # 8765e6 + 779531e6
        self.assertEqual(RRLL.token_y_subtree_borrowed, Decimal("779531e6"))   # 779531e6

    def test_left_and_right_leg_stopping_below_peak(self):
        liq_tree = self.liq_tree

        root: LiqNode = liq_tree.nodes[liq_tree.root_key]
        L: LiqNode = liq_tree.nodes[(8 << 24) | 16]

        # 1st (1, 4) - subtree below LL
        LL: LiqNode = liq_tree.nodes[(4 << 24) | 16]
        LLL: LiqNode = liq_tree.nodes[(2 << 24) | 16]
        LLR: LiqNode = liq_tree.nodes[(2 << 24) | 18]
        LLLL: LiqNode = liq_tree.nodes[(1 << 24) | 16]
        LLLR: LiqNode = liq_tree.nodes[(1 << 24) | 17]
        LLRL: LiqNode = liq_tree.nodes[(1 << 24) | 18]
        LLRR: LiqNode = liq_tree.nodes[(1 << 24) | 19]

        # Possible sub-ranges
        # (1,1), (1,2), (1,3), (1,4)
        # (2,2), (2,3), (2,4)
        # (3,3), (3,4)
        # (4,4)

        # Pre-populate nodes w/o fee calculation
        liq_tree.add_inf_range_m_liq(Decimal("432"))
        liq_tree.add_m_liq(LiqRange(low=1, high=1), Decimal("98237498262"))  # LLLL
        liq_tree.add_m_liq(LiqRange(low=1, high=2), Decimal("932141354"))  # LLL
        liq_tree.add_m_liq(LiqRange(low=1, high=3), Decimal("151463465"))  # LLL, LLRL
        liq_tree.add_m_liq(LiqRange(low=1, high=4), Decimal("45754683688356"))  # LL
        liq_tree.add_m_liq(LiqRange(low=2, high=2), Decimal("245346257245745"))  # LLLR
        liq_tree.add_m_liq(LiqRange(low=2, high=3), Decimal("243457472"))  # LLLR, LLRL
        liq_tree.add_m_liq(LiqRange(low=2, high=4), Decimal("2462"))  # LLLR, LLR
        liq_tree.add_m_liq(LiqRange(low=3, high=3), Decimal("45656756785"))  # LLRL
        liq_tree.add_m_liq(LiqRange(low=3, high=4), Decimal("554"))  # LLR
        liq_tree.add_m_liq(LiqRange(low=4, high=4), Decimal("262"))  # LLRR

        liq_tree.add_t_liq(LiqRange(low=1, high=1), Decimal("5645645"), Decimal("4357e18"), Decimal("345345345e6"))  # LLLL
        liq_tree.add_t_liq(LiqRange(low=1, high=2), Decimal("3456835"), Decimal("293874927834e18"), Decimal("2345346e6"))  # LLL
        liq_tree.add_t_liq(LiqRange(low=1, high=3), Decimal("56858345635"), Decimal("23452e18"), Decimal("12341235e6"))  # LLL, LLRL
        liq_tree.add_t_liq(LiqRange(low=1, high=4), Decimal("23453467234"), Decimal("134235e18"), Decimal("34534634e6"))  # LL
        liq_tree.add_t_liq(LiqRange(low=2, high=2), Decimal("456756745"), Decimal("1233463e18"), Decimal("2341356e6"))  # LLLR
        liq_tree.add_t_liq(LiqRange(low=2, high=3), Decimal("34534652457"), Decimal("45e18"), Decimal("1324213563456457e6"))  # LLLR, LLRL
        liq_tree.add_t_liq(LiqRange(low=2, high=4), Decimal("12121345"), Decimal("4567e18"), Decimal("1235146e6"))  # LLLR, LLR
        liq_tree.add_t_liq(LiqRange(low=3, high=3), Decimal("4564573"), Decimal("4564564e18"), Decimal("6345135e6"))  # LLRL
        liq_tree.add_t_liq(LiqRange(low=3, high=4), Decimal("3456242"), Decimal("2564587456e18"), Decimal("1234135e6"))  # LLR
        liq_tree.add_t_liq(LiqRange(low=4, high=4), Decimal("2145245745"), Decimal("76585673e18"), Decimal("4564574e6"))  # LLRR

        # Verify initial state
        # m_liq
        self.assertEqual(root.m_liq, Decimal("432"))
        self.assertEqual(L.m_liq, Decimal("98237498262"))
        self.assertEqual(LL.m_liq, Decimal("0"))
        self.assertEqual(LLL.m_liq, Decimal("0"))
        self.assertEqual(LLR.m_liq, Decimal("77163335364641"))
        self.assertEqual(LLLL.m_liq, Decimal("0"))
        self.assertEqual(LLLR.m_liq, Decimal("41634662758839"))
        self.assertEqual(LLRL.m_liq, Decimal("245323731137021"))
        self.assertEqual(LLRR.m_liq, Decimal("356345645745673764675050"))

        # t_liq
        self.assertEqual(root.t_liq, Decimal("0"))
        self.assertEqual(L.t_liq, Decimal("0"))
        self.assertEqual(LL.t_liq, Decimal("0"))
        self.assertEqual(LLL.t_liq, Decimal("0"))
        self.assertEqual(LLR.t_liq, Decimal("5346"))
        self.assertEqual(LLLL.t_liq, Decimal("7634865"))
        self.assertEqual(LLLR.t_liq, Decimal("7634865"))
        self.assertEqual(LLRL.t_liq, Decimal("7634865"))
        self.assertEqual(LLRR.t_liq, Decimal("7634865"))

        # subtree_m_liq
        self.assertEqual(root.subtree_m_liq, Decimal("324198833"))
        self.assertEqual(L.subtree_m_liq, Decimal("324063953"))
        self.assertEqual(LL.subtree_m_liq, Decimal("324056493"))
        self.assertEqual(LLL.subtree_m_liq, Decimal("4444"))
        self.assertEqual(LLR.subtree_m_liq, Decimal("287725557"))
        self.assertEqual(LLLL.subtree_m_liq, Decimal("287634865"))
        self.assertEqual(LLLR.subtree_m_liq, Decimal("287634865"))
        self.assertEqual(LLRL.subtree_m_liq, Decimal("287634865"))
        self.assertEqual(LLRR.subtree_m_liq, Decimal("287634865"))

        # borrowed_x
        self.assertEqual(root.token_x_borrowed, Decimal("492e18"))
        self.assertEqual(L.token_x_borrowed, Decimal("998e18"))
        self.assertEqual(LL.token_x_borrowed, Decimal("765e18"))
        self.assertEqual(LLL.token_x_borrowed, Decimal("24e18"))
        self.assertEqual(LLR.token_x_borrowed, Decimal("53e18"))
        self.assertEqual(LLLL.token_x_borrowed, Decimal("701e18"))
        self.assertEqual(LLLR.token_x_borrowed, Decimal("701e18"))
        self.assertEqual(LLRL.token_x_borrowed, Decimal("701e18"))
        self.assertEqual(LLRR.token_x_borrowed, Decimal("701e18"))

        # subtree_borrowed_x
        self.assertEqual(root.token_x_subtree_borrowed, Decimal("3033e18"))
        self.assertEqual(L.token_x_subtree_borrowed, Decimal("2541e18"))
        self.assertEqual(LL.token_x_subtree_borrowed, Decimal("1519e18"))
        self.assertEqual(LLL.token_x_subtree_borrowed, Decimal("24e18"))
        self.assertEqual(LLR.token_x_subtree_borrowed, Decimal("754e18"))
        self.assertEqual(LLLL.token_x_subtree_borrowed, Decimal("701e18"))
        self.assertEqual(LLLR.token_x_subtree_borrowed, Decimal("701e18"))
        self.assertEqual(LLRL.token_x_subtree_borrowed, Decimal("701e18"))
        self.assertEqual(LLRR.token_x_subtree_borrowed, Decimal("701e18"))

        # borrowed_y
        self.assertEqual(root.token_y_borrowed, Decimal("254858e6"))
        self.assertEqual(L.token_y_borrowed, Decimal("353e6"))
        self.assertEqual(LL.token_y_borrowed, Decimal("99763e6"))
        self.assertEqual(LLL.token_y_borrowed, Decimal("552e6"))
        self.assertEqual(LLR.token_y_borrowed, Decimal("8765e6"))
        self.assertEqual(LLLL.token_y_borrowed, Decimal("779531e6"))
        self.assertEqual(LLLR.token_y_borrowed, Decimal("779531e6"))
        self.assertEqual(LLRL.token_y_borrowed, Decimal("779531e6"))
        self.assertEqual(LLRR.token_y_borrowed, Decimal("779531e6"))

        # subtree_borrowed_y
        self.assertEqual(root.token_y_subtree_borrowed, Decimal("1143822e6"))
        self.assertEqual(L.token_y_subtree_borrowed, Decimal("888964e6"))
        self.assertEqual(LL.token_y_subtree_borrowed, Decimal("888059e6"))
        self.assertEqual(LLL.token_y_subtree_borrowed, Decimal("552e6"))
        self.assertEqual(LLR.token_y_subtree_borrowed, Decimal("788296e6"))
        self.assertEqual(LLLL.token_y_subtree_borrowed, Decimal("779531e6"))
        self.assertEqual(LLLR.token_y_subtree_borrowed, Decimal("779531e6"))
        self.assertEqual(LLRL.token_y_subtree_borrowed, Decimal("779531e6"))
        self.assertEqual(LLRR.token_y_subtree_borrowed, Decimal("779531e6"))

        # Test fees while targeting (1, 4)


    def test_left_and_right_leg_stopping_below_peak_BROKEN(self):
        liq_tree = self.liq_tree

        root: LiqNode = liq_tree.nodes[liq_tree.root_key]
        L: LiqNode = liq_tree.nodes[(8 << 24) | 16]

        # 1st (1, 4) - subtree below LL
        LL: LiqNode = liq_tree.nodes[(4 << 24) | 16]
        LLL: LiqNode = liq_tree.nodes[(2 << 24) | 16]
        LLR: LiqNode = liq_tree.nodes[(2 << 24) | 18]
        LLLL: LiqNode = liq_tree.nodes[(1 << 24) | 16]
        LLLR: LiqNode = liq_tree.nodes[(1 << 24) | 17]
        LLRL: LiqNode = liq_tree.nodes[(1 << 24) | 18]
        LLRR: LiqNode = liq_tree.nodes[(1 << 24) | 19]

        # Possible sub-ranges
        # (1,1), (1,2), (1,3), (1,4)
        # (2,2), (2,3), (2,4)
        # (3,3), (3,4)
        # (4,4)

        # Apply operations over all sub-ranges
        # We don't want to organize all calls into sections like this, because there could be bugs depending on the order of calls (ie. add_t_liq before remove_t_liq)
        # As other tests will cover the correct ordering like the example mentioned, we should mix things up. But we DO know add_m_liq is before add_t_liq, and either add must be called before a remove
        # NOTE: these values are 'random'
        liq_tree.add_m_liq(LiqRange(low=1, high=1), Decimal("98237498262"))  # LLLL
        liq_tree.add_m_liq(LiqRange(low=1, high=2), Decimal("932141354"))  # LLL
        liq_tree.add_m_liq(LiqRange(low=1, high=3), Decimal("151463465"))  # LLL, LLRL
        liq_tree.add_m_liq(LiqRange(low=1, high=4), Decimal("45754683688356"))  # LL
        liq_tree.add_m_liq(LiqRange(low=2, high=2), Decimal("245346257245745"))  # LLLR
        liq_tree.add_m_liq(LiqRange(low=2, high=3), Decimal("243457472"))  # LLLR, LLRL
        liq_tree.add_m_liq(LiqRange(low=2, high=4), Decimal("2462"))  # LLLR, LLR
        liq_tree.add_m_liq(LiqRange(low=3, high=3), Decimal("45656756785"))  # LLRL
        liq_tree.add_m_liq(LiqRange(low=3, high=4), Decimal("554"))  # LLR
        liq_tree.add_m_liq(LiqRange(low=4, high=4), Decimal("262"))  # LLRR

        liq_tree.add_t_liq(LiqRange(low=1, high=1), Decimal("5645645"), Decimal("4357e18"), Decimal("345345345e6"))  # LLLL
        liq_tree.add_t_liq(LiqRange(low=1, high=2), Decimal("3456835"), Decimal("293874927834e18"), Decimal("2345346e6"))  # LLL
        liq_tree.add_t_liq(LiqRange(low=1, high=3), Decimal("56858345635"), Decimal("23452e18"), Decimal("12341235e6"))  # LLL, LLRL
        liq_tree.add_t_liq(LiqRange(low=1, high=4), Decimal("23453467234"), Decimal("134235e18"), Decimal("34534634e6"))  # LL
        liq_tree.add_t_liq(LiqRange(low=2, high=2), Decimal("456756745"), Decimal("1233463e18"), Decimal("2341356e6"))  # LLLR
        liq_tree.add_t_liq(LiqRange(low=2, high=3), Decimal("34534652457"), Decimal("45e18"), Decimal("1324213563456457e6"))  # LLLR, LLRL
        liq_tree.add_t_liq(LiqRange(low=2, high=4), Decimal("12121345"), Decimal("4567e18"), Decimal("1235146e6"))  # LLLR, LLR
        liq_tree.add_t_liq(LiqRange(low=3, high=3), Decimal("4564573"), Decimal("4564564e18"), Decimal("6345135e6"))  # LLRL
        liq_tree.add_t_liq(LiqRange(low=3, high=4), Decimal("3456242"), Decimal("2564587456e18"), Decimal("1234135e6"))  # LLR
        liq_tree.add_t_liq(LiqRange(low=4, high=4), Decimal("2145245745"), Decimal("76585673e18"), Decimal("4564574e6"))  # LLRR

        # Operations that accumulate fees
        liq_tree.token_x_fee_rate_snapshot += Decimal("67967856253453452367574")
        liq_tree.token_y_fee_rate_snapshot += Decimal("23464675683452345234568562")
        liq_tree.remove_t_liq(LiqRange(low=1, high=1), Decimal("13426354645"), Decimal("4e18"), Decimal("5e6"))  # LLLL
        liq_tree.token_x_fee_rate_snapshot += Decimal("457568568356234515")
        liq_tree.token_y_fee_rate_snapshot += Decimal("3464756758679689")
        liq_tree.remove_t_liq(LiqRange(low=1, high=2), Decimal("245346457"), Decimal("1243234e18"), Decimal("454564e6"))  # LLL
        liq_tree.token_x_fee_rate_snapshot += Decimal("446476458")
        liq_tree.token_y_fee_rate_snapshot += Decimal("35656867")
        liq_tree.remove_t_liq(LiqRange(low=1, high=3), Decimal("2345136457"), Decimal("134345e18"), Decimal("245e6"))  # LLL, LLRL
        liq_tree.token_x_fee_rate_snapshot += Decimal("32456")
        liq_tree.token_y_fee_rate_snapshot += Decimal("246")
        liq_tree.remove_t_liq(LiqRange(low=1, high=4), Decimal("345675686796"), Decimal("4545e18"), Decimal("45745e6"))  # LL
        liq_tree.token_x_fee_rate_snapshot += Decimal("6796")
        liq_tree.token_y_fee_rate_snapshot += Decimal("464564756785684")
        liq_tree.remove_t_liq(LiqRange(low=2, high=2), Decimal("68978907"), Decimal("23454e18"), Decimal("5677e6"))  # LLLR
        liq_tree.token_x_fee_rate_snapshot += Decimal("3454568796798643673")
        liq_tree.token_y_fee_rate_snapshot += Decimal("3456475784245234553434523453456346")
        liq_tree.remove_t_liq(LiqRange(low=2, high=3), Decimal("8908978"), Decimal("856454e18"), Decimal("4577865e6"))  # LLLR, LLRL
        liq_tree.token_x_fee_rate_snapshot += Decimal("4573568356983683682578725")
        liq_tree.token_y_fee_rate_snapshot += Decimal("234624576468356835688356368368482342")
        liq_tree.remove_t_liq(LiqRange(low=2, high=4), Decimal("679678"), Decimal("3456457e18"), Decimal("56756756e6"))  # LLLR, LLR
        liq_tree.token_x_fee_rate_snapshot += Decimal("3256457252452572172577252424547457")
        liq_tree.token_y_fee_rate_snapshot += Decimal("35745675685835626345234624")
        liq_tree.remove_t_liq(LiqRange(low=3, high=3), Decimal("65756"), Decimal("56756e18"), Decimal("34564567e6"))  # LLRL
        liq_tree.token_x_fee_rate_snapshot += Decimal("345646856785673572456245")
        liq_tree.token_y_fee_rate_snapshot += Decimal("2356457568367824623454576788")
        liq_tree.remove_t_liq(LiqRange(low=3, high=4), Decimal("54444"), Decimal("4564564e18"), Decimal("56756786e6"))  # LLR
        liq_tree.token_x_fee_rate_snapshot += Decimal("456325876883562457")
        liq_tree.token_y_fee_rate_snapshot += Decimal("5767983835654356214356")
        liq_tree.remove_t_liq(LiqRange(low=4, high=4), Decimal("443"), Decimal("4564564e18"), Decimal("56754e6"))  # LLRR

        liq_tree.token_x_fee_rate_snapshot += Decimal("3456568679362657567867956")
        liq_tree.token_y_fee_rate_snapshot += Decimal("35735736783579799798988790078")
        liq_tree.add_m_liq(LiqRange(low=1, high=1), Decimal("75645"))  # LLLL
        liq_tree.token_x_fee_rate_snapshot += Decimal("678908690870808")
        liq_tree.token_y_fee_rate_snapshot += Decimal("56890598759879798769")
        liq_tree.add_m_liq(LiqRange(low=1, high=2), Decimal("8567567"))  # LLL
        liq_tree.token_x_fee_rate_snapshot += Decimal("70890900879879467474")
        liq_tree.token_y_fee_rate_snapshot += Decimal("4678679468674786666")
        liq_tree.add_m_liq(LiqRange(low=1, high=3), Decimal("456456"))  # LLL, LLRL
        liq_tree.token_x_fee_rate_snapshot += Decimal("46877777777777777")
        liq_tree.token_y_fee_rate_snapshot += Decimal("3465675698689467357")
        liq_tree.add_m_liq(LiqRange(low=1, high=4), Decimal("356767894766"))  # LL
        liq_tree.token_x_fee_rate_snapshot += Decimal("346745684567943673567")
        liq_tree.token_y_fee_rate_snapshot += Decimal("5455665565656556556")
        liq_tree.add_m_liq(LiqRange(low=2, high=2), Decimal("34563457"))  # LLLR
        liq_tree.token_x_fee_rate_snapshot += Decimal("54574562523462347457")
        liq_tree.token_y_fee_rate_snapshot += Decimal("346468567843652647")
        liq_tree.add_m_liq(LiqRange(low=2, high=3), Decimal("245346"))  # LLLR, LLRL
        liq_tree.token_x_fee_rate_snapshot += Decimal("435736487858735734")
        liq_tree.token_y_fee_rate_snapshot += Decimal("345756856785784")
        liq_tree.add_m_liq(LiqRange(low=2, high=4), Decimal("35654373573456"))  # LLLR, LLR
        liq_tree.token_x_fee_rate_snapshot += Decimal("9782315978324963149086")
        liq_tree.token_y_fee_rate_snapshot += Decimal("1977947657153479167908478603")
        liq_tree.add_m_liq(LiqRange(low=3, high=3), Decimal("24546457452"))  # LLRL
        liq_tree.token_x_fee_rate_snapshot += Decimal("877907987198867986767967167846785637245673")
        liq_tree.token_y_fee_rate_snapshot += Decimal("01749857934067931408619045791874695714676")
        liq_tree.add_m_liq(LiqRange(low=3, high=4), Decimal("356345645745675675685678"))  # LLR
        liq_tree.token_x_fee_rate_snapshot += Decimal("9987698779879879874987786384537456725474327243259947838356837568356725984687365")
        liq_tree.token_y_fee_rate_snapshot += Decimal("9878678625678156565671567256742164782194785174671462314967193478691843769813476987")
        liq_tree.add_m_liq(LiqRange(low=4, high=4), Decimal("459789686783566564767"))  # LLRR
        liq_tree.token_x_fee_rate_snapshot += Decimal("2546456746735")
        liq_tree.token_y_fee_rate_snapshot += Decimal("2454567346736")

        liq_tree.remove_m_liq(LiqRange(low=1, high=1), Decimal("67967867"))  # LLLL
        liq_tree.token_x_fee_rate_snapshot += Decimal("7676767327272772272727722727272")
        liq_tree.token_y_fee_rate_snapshot += Decimal("2727772727272777777777777722727")
        liq_tree.remove_m_liq(LiqRange(low=1, high=2), Decimal("45635457"))  # LLL
        liq_tree.token_x_fee_rate_snapshot += Decimal("198759265398245671987469087")
        liq_tree.token_y_fee_rate_snapshot += Decimal("19746587349687357810349578017946")
        liq_tree.remove_m_liq(LiqRange(low=1, high=3), Decimal("567567373"))  # LLL, LLRL
        liq_tree.token_x_fee_rate_snapshot += Decimal("98717986587364907214036834590682")
        liq_tree.token_y_fee_rate_snapshot += Decimal("9716395673986702964617823679805")
        liq_tree.remove_m_liq(LiqRange(low=1, high=4), Decimal("4575437856335"))  # LL
        liq_tree.token_x_fee_rate_snapshot += Decimal("976987080780203980798239742934235")
        liq_tree.token_y_fee_rate_snapshot += Decimal("6978978987459873981798273497823942")
        liq_tree.remove_m_liq(LiqRange(low=2, high=2), Decimal("23455745645"))  # LLLR
        liq_tree.token_x_fee_rate_snapshot += Decimal("434522534253453462436234623462346")
        liq_tree.token_y_fee_rate_snapshot += Decimal("23462345134634623634623462456724566")
        liq_tree.remove_m_liq(LiqRange(low=2, high=3), Decimal("2345346574"))  # LLLR, LLRL
        liq_tree.token_x_fee_rate_snapshot += Decimal("79878979876987698798454564564564")
        liq_tree.token_y_fee_rate_snapshot += Decimal("5645635645634621462476262756245624565")
        liq_tree.remove_m_liq(LiqRange(low=2, high=4), Decimal("24534646856"))  # LLLR, LLR
        liq_tree.token_x_fee_rate_snapshot += Decimal("24512645624662342346234634631463462246462")
        liq_tree.token_y_fee_rate_snapshot += Decimal("214664623234616414624646236234234634646232463")
        liq_tree.remove_m_liq(LiqRange(low=3, high=3), Decimal("47568568564"))  # LLRL
        liq_tree.token_x_fee_rate_snapshot += Decimal("12221211212244155551555555555555555555555555555")
        liq_tree.token_y_fee_rate_snapshot += Decimal("155555555555555555555555555555555555555555555555")
        liq_tree.remove_m_liq(LiqRange(low=3, high=4), Decimal("24545656855"))  # LLR
        liq_tree.token_x_fee_rate_snapshot += Decimal("9874787246782564286735426553525832786234623")
        liq_tree.token_y_fee_rate_snapshot += Decimal("67845986765986736798567832459782739845798230")
        liq_tree.remove_m_liq(LiqRange(low=4, high=4), Decimal("3452464675675"))  # LLRR
        liq_tree.token_x_fee_rate_snapshot += Decimal("98726348906735986783495701378450983165908231479581324")
        liq_tree.token_y_fee_rate_snapshot += Decimal("98749857398456981264570398459047569823794785961235")

        # Verify state is correct for all effected nodes (includes L and root)
        # m_liq
        self.assertEqual(root.m_liq, Decimal("0"))
        self.assertEqual(L.m_liq, Decimal("0"))
        self.assertEqual(LL.m_liq, Decimal("0"))
        self.assertEqual(LLL.m_liq, Decimal("0"))
        self.assertEqual(LLR.m_liq, Decimal("77163335364641"))
        self.assertEqual(LLLL.m_liq, Decimal("0"))
        self.assertEqual(LLLR.m_liq, Decimal("41634662758839"))
        self.assertEqual(LLRL.m_liq, Decimal("245323731137021"))
        self.assertEqual(LLRR.m_liq, Decimal("356345645745673764675050"))

        # t_liq
        self.assertEqual(root.t_liq, Decimal("0"))
        self.assertEqual(L.t_liq, Decimal("0"))
        self.assertEqual(LL.t_liq, Decimal("0"))
        self.assertEqual(LLL.t_liq, Decimal("0"))
        self.assertEqual(LLR.t_liq, Decimal("5346"))
        self.assertEqual(LLLL.t_liq, Decimal("7634865"))
        self.assertEqual(LLLR.t_liq, Decimal("7634865"))
        self.assertEqual(LLRL.t_liq, Decimal("7634865"))
        self.assertEqual(LLRR.t_liq, Decimal("7634865"))

        # subtree_m_liq
        self.assertEqual(root.subtree_m_liq, Decimal("324198833"))
        self.assertEqual(L.subtree_m_liq, Decimal("324063953"))
        self.assertEqual(LL.subtree_m_liq, Decimal("324056493"))
        self.assertEqual(LLL.subtree_m_liq, Decimal("4444"))
        self.assertEqual(LLR.subtree_m_liq, Decimal("287725557"))
        self.assertEqual(LLLL.subtree_m_liq, Decimal("287634865"))
        self.assertEqual(LLLR.subtree_m_liq, Decimal("287634865"))
        self.assertEqual(LLRL.subtree_m_liq, Decimal("287634865"))
        self.assertEqual(LLRR.subtree_m_liq, Decimal("287634865"))

        # borrowed_x
        self.assertEqual(root.token_x_borrowed, Decimal("492e18"))
        self.assertEqual(L.token_x_borrowed, Decimal("998e18"))
        self.assertEqual(LL.token_x_borrowed, Decimal("765e18"))
        self.assertEqual(LLL.token_x_borrowed, Decimal("24e18"))
        self.assertEqual(LLR.token_x_borrowed, Decimal("53e18"))
        self.assertEqual(LLLL.token_x_borrowed, Decimal("701e18"))
        self.assertEqual(LLLR.token_x_borrowed, Decimal("701e18"))
        self.assertEqual(LLRL.token_x_borrowed, Decimal("701e18"))
        self.assertEqual(LLRR.token_x_borrowed, Decimal("701e18"))

        # subtree_borrowed_x
        self.assertEqual(root.token_x_subtree_borrowed, Decimal("3033e18"))
        self.assertEqual(L.token_x_subtree_borrowed, Decimal("2541e18"))
        self.assertEqual(LL.token_x_subtree_borrowed, Decimal("1519e18"))
        self.assertEqual(LLL.token_x_subtree_borrowed, Decimal("24e18"))
        self.assertEqual(LLR.token_x_subtree_borrowed, Decimal("754e18"))
        self.assertEqual(LLLL.token_x_subtree_borrowed, Decimal("701e18"))
        self.assertEqual(LLLR.token_x_subtree_borrowed, Decimal("701e18"))
        self.assertEqual(LLRL.token_x_subtree_borrowed, Decimal("701e18"))
        self.assertEqual(LLRR.token_x_subtree_borrowed, Decimal("701e18"))

        # borrowed_y
        self.assertEqual(root.token_y_borrowed, Decimal("254858e6"))
        self.assertEqual(L.token_y_borrowed, Decimal("353e6"))
        self.assertEqual(LL.token_y_borrowed, Decimal("99763e6"))
        self.assertEqual(LLL.token_y_borrowed, Decimal("552e6"))
        self.assertEqual(LLR.token_y_borrowed, Decimal("8765e6"))
        self.assertEqual(LLLL.token_y_borrowed, Decimal("779531e6"))
        self.assertEqual(LLLR.token_y_borrowed, Decimal("779531e6"))
        self.assertEqual(LLRL.token_y_borrowed, Decimal("779531e6"))
        self.assertEqual(LLRR.token_y_borrowed, Decimal("779531e6"))

        # subtree_borrowed_y
        self.assertEqual(root.token_y_subtree_borrowed, Decimal("1143822e6"))
        self.assertEqual(L.token_y_subtree_borrowed, Decimal("888964e6"))
        self.assertEqual(LL.token_y_subtree_borrowed, Decimal("888059e6"))
        self.assertEqual(LLL.token_y_subtree_borrowed, Decimal("552e6"))
        self.assertEqual(LLR.token_y_subtree_borrowed, Decimal("788296e6"))
        self.assertEqual(LLLL.token_y_subtree_borrowed, Decimal("779531e6"))
        self.assertEqual(LLLR.token_y_subtree_borrowed, Decimal("779531e6"))
        self.assertEqual(LLRL.token_y_subtree_borrowed, Decimal("779531e6"))
        self.assertEqual(LLRR.token_y_subtree_borrowed, Decimal("779531e6"))


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
    LiqTree public liq_tree;
    using LiqTreeImpl for LiqTree;
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
    LiqTree public liq_tree;
    using LiqTreeImpl for LiqTree;
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