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


class TestDenseLiquidityTree(TestCase):
    def setUp(self) -> None:
        self.liq_tree = LiquidityTree(depth=4)

    def test_root_only(self):
        liq_tree: LiquidityTree = self.liq_tree

        # T0
        liq_tree.add_inf_range_m_liq(Decimal("8430"))
        liq_tree.add_inf_range_t_liq(Decimal("4381"), Decimal("832e18"), Decimal("928e6"))
        self.assertEqual(True, True)

        # T3600 (1hr) --- 5.4% APR as Q192.64
        liq_tree.token_y_fee_rate_snapshot += Decimal("113712805933826")           # Q192.64 - 2097631028964689100923538627362816
        liq_tree.token_x_fee_rate_snapshot += Decimal("113712805933826")           # Q192.64 - 2097631028964689100923538627362816

        # Verify root state
        root: LiqNode = liq_tree.root
        self.assertEqual(root.m_liq, Decimal("8430"))                              #
        self.assertEqual(root.subtree_m_liq, Decimal("134880"))                    #
        self.assertEqual(root.t_liq, Decimal("4381"))                              #
        self.assertEqual(root.token_x_borrowed, Decimal("832e18"))            #
        self.assertEqual(root.token_x_subtree_borrowed, Decimal("832e18"))    #
        self.assertEqual(root.token_y_borrowed, Decimal("928e6"))             #
        self.assertEqual(root.token_y_subtree_borrowed, Decimal("928e6"))     #

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
        self.assertEqual(int(root.token_y_cummulative_earned_per_m_liq), Decimal("13251906"))
        self.assertEqual(int(root.token_y_cummulative_earned_per_m_subtree_liq), Decimal("13251906"))

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

        self.assertEqual(int(root.token_x_cummulative_earned_per_m_liq), Decimal("2563695146166521368513"))
        self.assertEqual(int(root.token_x_cummulative_earned_per_m_subtree_liq), Decimal("2563695146166521368513"))
        self.assertEqual(int(root.token_y_cummulative_earned_per_m_liq), Decimal("2019821011409"))
        self.assertEqual(int(root.token_y_cummulative_earned_per_m_subtree_liq), Decimal("2019821011409"))

        self.assertEqual(root.m_liq, Decimal("14035"))
        self.assertEqual(root.subtree_m_liq, Decimal("224560"))
        self.assertEqual(root.t_liq, Decimal("6745"))
        self.assertEqual(root.token_x_borrowed, Decimal("9794e18"))
        self.assertEqual(root.token_x_subtree_borrowed, Decimal("9794e18"))
        self.assertEqual(root.token_y_borrowed, Decimal("7927062e6"))
        self.assertEqual(root.token_y_subtree_borrowed, Decimal("7927062e6"))

    def test_left_leg_only(self):
        liq_tree: LiquidityTree = self.liq_tree

        root: LiqNode = liq_tree.root
        L: LiqNode = liq_tree.nodes[(8 << 24) | 16]     # 134217744
        LL: LiqNode = liq_tree.nodes[(4 << 24) | 16]    # 67108880
        LR: LiqNode = liq_tree.nodes[(4 << 24) | 20]    # 67108884
        LLR: LiqNode = liq_tree.nodes[(2 << 24) | 18]   # 33554450
        LLRR: LiqNode = liq_tree.nodes[(1 << 24) | 19]  # 16777235

        # T0 - populate tree with data excluding fee calculations
        liq_tree.add_inf_range_m_liq(Decimal("8430"))                       # root
        liq_tree.add_m_liq(LiqRange(low=0, high=7), Decimal("377"))         # L
        liq_tree.add_m_liq(LiqRange(low=0, high=3), Decimal("9082734"))     # LL
        liq_tree.add_m_liq(LiqRange(low=4, high=7), Decimal("1111"))        # LR
        liq_tree.add_m_liq(LiqRange(low=2, high=3), Decimal("45346"))       # LLR
        liq_tree.add_m_liq(LiqRange(low=3, high=3), Decimal("287634865"))   # LLRR

        liq_tree.add_inf_range_t_liq(Decimal("4430"), Decimal("492e18"), Decimal("254858e6"))                       # root
        liq_tree.add_t_liq(LiqRange(low=0, high=7), Decimal("77"), Decimal("998e18"), Decimal("353e6"))             # L
        liq_tree.add_t_liq(LiqRange(low=0, high=3), Decimal("82734"), Decimal("765e18"), Decimal("99763e6"))        # LL
        liq_tree.add_t_liq(LiqRange(low=4, high=7), Decimal("111"), Decimal("24e18"), Decimal("552e6"))             # LR
        liq_tree.add_t_liq(LiqRange(low=2, high=3), Decimal("5346"), Decimal("53e18"), Decimal("8765e6"))           # LLR
        liq_tree.add_t_liq(LiqRange(low=3, high=3), Decimal("7634865"), Decimal("701e18"), Decimal("779531e6"))     # LLRR

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
        self.assertEqual(root.subtree_m_liq, Decimal("324198833"))  # 8430*16 + 377*8 + 9082734*4 + 1111*4 + 45346*2 + 287634865*1
        self.assertEqual(L.subtree_m_liq, Decimal("324063953"))     # 377*8 + 9082734*4 + 1111*4 + 45346*2 + 287634865*1
        self.assertEqual(LL.subtree_m_liq, Decimal("324056493"))    # 9082734*4 + 45346*2 + 287634865*1
        self.assertEqual(LR.subtree_m_liq, Decimal("4444"))         # 1111*4
        self.assertEqual(LLR.subtree_m_liq, Decimal("287725557"))   # 45346*2 + 287634865*1
        self.assertEqual(LLRR.subtree_m_liq, Decimal("287634865"))  # 287634865*1

        # borrowed_x
        self.assertEqual(root.token_x_borrowed, Decimal("492e18"))
        self.assertEqual(L.token_x_borrowed, Decimal("998e18"))
        self.assertEqual(LL.token_x_borrowed, Decimal("765e18"))
        self.assertEqual(LR.token_x_borrowed, Decimal("24e18"))
        self.assertEqual(LLR.token_x_borrowed, Decimal("53e18"))
        self.assertEqual(LLRR.token_x_borrowed, Decimal("701e18"))

        # borrowed_y
        self.assertEqual(root.token_y_borrowed, Decimal("254858e6"))
        self.assertEqual(L.token_y_borrowed, Decimal("353e6"))
        self.assertEqual(LL.token_y_borrowed, Decimal("99763e6"))
        self.assertEqual(LR.token_y_borrowed, Decimal("552e6"))
        self.assertEqual(LLR.token_y_borrowed, Decimal("8765e6"))
        self.assertEqual(LLRR.token_y_borrowed, Decimal("779531e6"))

        # subtree_borrowed_x
        self.assertEqual(root.token_x_subtree_borrowed, Decimal("3033e18"))     # 492e18 + 998e18 + 765e18 + 53e18 + 701e18 + 24e18
        self.assertEqual(L.token_x_subtree_borrowed, Decimal("2541e18"))        # 998e18 + 765e18 + 53e18 + 701e18 + 24e18
        self.assertEqual(LL.token_x_subtree_borrowed, Decimal("1519e18"))       # 765e18 + 53e18 + 701e18
        self.assertEqual(LR.token_x_subtree_borrowed, Decimal("24e18"))
        self.assertEqual(LLR.token_x_subtree_borrowed, Decimal("754e18"))       # 53e18 + 701e18
        self.assertEqual(LLRR.token_x_subtree_borrowed, Decimal("701e18"))      # 701e18

        # subtree_borrowed_y
        self.assertEqual(root.token_y_subtree_borrowed, Decimal("1143822e6"))   # 254858e6 + 353e6 + 99763e6 + 8765e6 + 779531e6 + 552e6
        self.assertEqual(L.token_y_subtree_borrowed, Decimal("888964e6"))       # 353e6 + 99763e6 + 8765e6 + 779531e6 + 552e6
        self.assertEqual(LL.token_y_subtree_borrowed, Decimal("888059e6"))      # 99763e6 + 8765e6 + 779531e6
        self.assertEqual(LR.token_y_subtree_borrowed, Decimal("552e6"))
        self.assertEqual(LLR.token_y_subtree_borrowed, Decimal("788296e6"))     # 8765e6 + 779531e6
        self.assertEqual(LLRR.token_y_subtree_borrowed, Decimal("779531e6"))    # 779531e6
        
        # T98273
        liq_tree.token_x_fee_rate_snapshot += Decimal("4541239648278065")       # 7.9% APR as Q192.64 T98273 - T0
        liq_tree.token_y_fee_rate_snapshot += Decimal("13278814667749784")     # 23.1% APR as Q192.64 T98273 - T0
        
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
        self.assertEqual(root.subtree_m_liq, Decimal("324212503"))  # 8430*16 + 377*8 + 9082734*4 + 3845*4 + 45346*2 + 287637599*1
        self.assertEqual(L.subtree_m_liq, Decimal("324077623"))     # 377*8 + 9082734*4 + 3845*4 + 45346*2 + 287637599*1
        self.assertEqual(LL.subtree_m_liq, Decimal("324059227"))    # 9082734*4 + 45346*2 + 287637599*1
        self.assertEqual(LR.subtree_m_liq, Decimal("15380"))        # 3845*4
        self.assertEqual(LLR.subtree_m_liq, Decimal("287728291"))   # 45346*2 + 287637599*1
        self.assertEqual(LLRR.subtree_m_liq, Decimal("287637599"))  # 287637599*1
        
        # T2876298273
        # Apply change that requires fee calculation
        # remove_m_liq
        
        liq_tree.token_x_fee_rate_snapshot += Decimal("16463537718422861220174597")    # 978567.9% APR as Q192.64 T2876298273 - T98273
        liq_tree.token_y_fee_rate_snapshot += Decimal("3715979586694123491881712207")  # 220872233.1% APR as Q192.64 T2876298273 - T98273

        liq_tree.remove_m_liq(LiqRange(low=3, high=7), Decimal("2734"))  # LLRR, LR

        # root
        self.assertEqual(int(root.token_x_cummulative_earned_per_m_liq), Decimal("1354374549844117328"))  # 373601278 + 1354374549470516050
        self.assertEqual(int(root.token_x_cummulative_earned_per_m_subtree_liq), Decimal("8349223596904894021"))  # 2303115199 + 8349223594601778821
        self.assertEqual(int(root.token_y_cummulative_earned_per_m_liq), Decimal("158351473404"))         # 0 + 158351473403
        self.assertEqual(int(root.token_y_cummulative_earned_per_m_subtree_liq), Decimal("710693401864"))         # 2 + 710693401861

        # L
        self.assertEqual(int(L.token_x_cummulative_earned_per_m_liq), Decimal("2747859799935140578"))    # 757991165 + 2747859799177149412
        self.assertEqual(int(L.token_x_cummulative_earned_per_m_subtree_liq), Decimal("6996304360355904017"))    # 1929915382 + 6996304358425988634
        self.assertEqual(int(L.token_y_cummulative_earned_per_m_liq), Decimal("219375887"))              # 0 + 219375887
        self.assertEqual(int(L.token_y_cummulative_earned_per_m_subtree_liq), Decimal("552456845957"))           # 1 + 552456845955

        # LL
        self.assertEqual(int(LL.token_x_cummulative_earned_per_m_liq), Decimal("2106654304686669588"))   # 581096415 + 2106654304105573173
        self.assertEqual(int(LL.token_x_cummulative_earned_per_m_subtree_liq), Decimal("4183016848129478568"))   # 1153837196 + 4183016846975641372
        self.assertEqual(int(LL.token_y_cummulative_earned_per_m_liq), Decimal("62008538706"))           # 0 + 62008538706
        self.assertEqual(int(LL.token_y_cummulative_earned_per_m_subtree_liq), Decimal("551980602778"))          # 1 + 551980602776

        # LR
        self.assertEqual(int(LR.token_x_cummulative_earned_per_m_liq), Decimal("423248578107618890129"))     # 148929881804 + 423248577958689008325
        self.assertEqual(int(LR.token_x_cummulative_earned_per_m_subtree_liq), Decimal("423248578107618890129"))     # 148929881804 + 423248577958689008325
        self.assertEqual(int(LR.token_y_cummulative_earned_per_m_liq), Decimal("2197219781195"))             # 10 + 2197219781185
        self.assertEqual(int(LR.token_y_cummulative_earned_per_m_subtree_liq), Decimal("2197219781195"))             # 10 + 2197219781185

        # LLR
        self.assertEqual(int(LLR.token_x_cummulative_earned_per_m_liq), Decimal("154626415017241477"))       # 42651943 + 154626414974589533
        self.assertEqual(int(LLR.token_x_cummulative_earned_per_m_subtree_liq), Decimal("2199779564584907057"))      # 606784254 + 2199779563978122803
        self.assertEqual(int(LLR.token_y_cummulative_earned_per_m_liq), Decimal("5771781665"))               # 0 + 5771781665
        self.assertEqual(int(LLR.token_y_cummulative_earned_per_m_subtree_liq), Decimal("519095539055"))             # 1 + 519095539054

        # LLRR
        self.assertEqual(int(LLRR.token_x_cummulative_earned_per_m_liq), Decimal("2108117905996538333"))     # 581500584 + 2108117905415037748
        self.assertEqual(int(LLRR.token_x_cummulative_earned_per_m_subtree_liq), Decimal("2108117905996538333"))     # 581500584 + 2108117905415037748
        self.assertEqual(int(LLRR.token_y_cummulative_earned_per_m_liq), Decimal("529127613135"))            # 1 + 529127613134
        self.assertEqual(int(LLRR.token_y_cummulative_earned_per_m_subtree_liq), Decimal("529127613135"))            # 1 + 529127613134

        # m_liq
        self.assertEqual(root.m_liq, Decimal("8430"))
        self.assertEqual(L.m_liq, Decimal("377"))
        self.assertEqual(LL.m_liq, Decimal("9082734"))
        self.assertEqual(LR.m_liq, Decimal("1111"))
        self.assertEqual(LLR.m_liq, Decimal("45346"))
        self.assertEqual(LLRR.m_liq, Decimal("287634865"))

        # subtree_m_liq
        self.assertEqual(root.subtree_m_liq, Decimal("324198833"))  # 8430*16 + 377*8 + 9082734*4 + 1111*4 + 45346*2 + 287634865*1
        self.assertEqual(L.subtree_m_liq, Decimal("324063953"))     # 377*8 + 9082734*4 + 1111*4 + 45346*2 + 287634865*1
        self.assertEqual(LL.subtree_m_liq, Decimal("324056493"))    # 9082734*4 + 45346*2 + 287634865*1
        self.assertEqual(LR.subtree_m_liq, Decimal("4444"))         # 1111*4
        self.assertEqual(LLR.subtree_m_liq, Decimal("287725557"))   # 45346*2 + 287634865*1
        self.assertEqual(LLRR.subtree_m_liq, Decimal("287634865"))  # 287634865*1

'''

        # 3.3) addTLiq
        vm.warp(9214298113) # T2876298273
        liq_tree.token_x_fee_rate_snapshot += 11381610389149375791104)   # 307% APR as Q192.64 T9214298113 - T2876298273
        liq_tree.token_y_fee_rate_snapshot += 185394198934916215865344)  # 5000.7% APR as Q192.64 T9214298113 - T2876298273

        liq_tree.addTLiq(LiqRange(3, 7), 1000, 1000e18, 1000e6) # LLRR, LR

        # root
        self.assertEqual(root.token_x_cummulative_earned_per_m_liq, 1354374549844117328 + 936348777891386)         # 1355310898622008714
        self.assertEqual(root.token_x_cummulative_earned_per_m_liq, 8349223596904894020 + 5772247649074341) # 8354995844553968361
        self.assertEqual(root.token_y_cummulative_earned_per_m_liq, 158351473403 + 7900657)                        # 158359374060
        self.assertEqual(root.token_y_cummulative_earned_per_m_liq, 710693401863 + 35458749)                # 710728860612

        # L
        self.assertEqual(L.token_x_cummulative_earned_per_m_liq, 2747859799935140577 + 1899736810880077)        # 2749759536746020654
        self.assertEqual(L.token_x_cummulative_earned_per_m_liq, 6996304360355904016 + 4836905046539355) # 7001141265402443371
        self.assertEqual(L.token_y_cummulative_earned_per_m_liq, 219375887 + 10945)                             # 219386832
        self.assertEqual(L.token_y_cummulative_earned_per_m_liq, 552456845956 + 27563825)                # 552484409781

        # LL
        self.assertEqual(LL.token_x_cummulative_earned_per_m_liq, 2106654304686669588 + 1456389336983247)        # 2108110694023652835
        self.assertEqual(LL.token_x_cummulative_earned_per_m_liq, 4183016848129478568 + 2891837127944514) # 4185908685257423082
        self.assertEqual(LL.token_y_cummulative_earned_per_m_liq, 62008538706 + 3093698)                         # 62011632404
        self.assertEqual(LL.token_y_cummulative_earned_per_m_liq, 551980602777 + 27539135)                # 552008141912

        # LR
        self.assertEqual(LR.token_x_cummulative_earned_per_m_liq, 423248578107618890129 + 373259731104033296)        # 423621837838722923425
        self.assertEqual(LR.token_x_cummulative_earned_per_m_liq, 423248578107618890129 + 373259731104033296) # 423621837838722923425
        self.assertEqual(LR.token_y_cummulative_earned_per_m_liq, 2197219781195 + 139839995)                         # 2197359621190
        self.assertEqual(LR.token_y_cummulative_earned_per_m_liq, 2197219781195 + 139839995)                  # 2197359621190

        # LLR
        self.assertEqual(LLR.token_x_cummulative_earned_per_m_liq, 154626415017241476 + 106897640711262)          # 154733312657952738
        self.assertEqual(LLR.token_x_cummulative_earned_per_m_liq, 2199779564584907057 + 1520770209363996) # 2201300334794271053
        self.assertEqual(LLR.token_y_cummulative_earned_per_m_liq, 5771781665 + 287962)                           # 5772069627
        self.assertEqual(LLR.token_y_cummulative_earned_per_m_liq, 519095539055 + 25898463)                # 519121437518

        # LLRR
        self.assertEqual(LLRR.token_x_cummulative_earned_per_m_liq, 2108117905996538332 + 1457402297493569)        # 2109575308294031901
        self.assertEqual(LLRR.token_x_cummulative_earned_per_m_liq, 2108117905996538332 + 1457402297493569) # 2109575308294031901
        self.assertEqual(LLRR.token_y_cummulative_earned_per_m_liq, 529127613135 + 26398986)                       # 529154012121
        self.assertEqual(LLRR.token_y_cummulative_earned_per_m_liq, 529127613135 + 26398986)                # 529154012121

        # t_liq
        self.assertEqual(root.t_liq, 4430)
        self.assertEqual(L.t_liq, 77)
        self.assertEqual(LL.t_liq, 82734)
        self.assertEqual(LR.t_liq, 1111)
        self.assertEqual(LLR.t_liq, 5346)
        self.assertEqual(LLRR.t_liq, 7635865)

        # borrowed_x
        self.assertEqual(root.token_x_borrowed, 492e18)
        self.assertEqual(L.token_x_borrowed, 998e18)
        self.assertEqual(LL.token_x_borrowed, 765e18)
        self.assertEqual(LR.token_x_borrowed, 1024e18)
        self.assertEqual(LLR.token_x_borrowed, 53e18)
        self.assertEqual(LLRR.token_x_borrowed, 1701e18)

        # borrowed_y
        self.assertEqual(root.token_y_borrowed, 254858e6)
        self.assertEqual(L.token_y_borrowed, 353e6)
        self.assertEqual(LL.token_y_borrowed, 99763e6)
        self.assertEqual(LR.token_y_borrowed, 1552e6)
        self.assertEqual(LLR.token_y_borrowed, 8765e6)
        self.assertEqual(LLRR.token_y_borrowed, 780531e6)

        # subtree_borrowed_x
        self.assertEqual(root.token_x_subtree_borrowed, 5033e18)  # 492e18 + 998e18 + 765e18 + 53e18 + 701e18 + 24e18
        self.assertEqual(L.token_x_subtree_borrowed, 4541e18)     # 998e18 + 765e18 + 53e18 + 701e18 + 24e18
        self.assertEqual(LL.token_x_subtree_borrowed, 2519e18)    # 765e18 + 53e18 + 701e18
        self.assertEqual(LR.token_x_subtree_borrowed, 1024e18)
        self.assertEqual(LLR.token_x_subtree_borrowed, 1754e18)   # 53e18 + 701e18
        self.assertEqual(LLRR.token_x_subtree_borrowed, 1701e18)  # 701e18

        # subtree_borrowed_y
        self.assertEqual(root.token_y_subtree_borrowed, 1145822e6) # 254858e6 + 353e6 + 99763e6 + 8765e6 + 779531e6 + 552e6
        self.assertEqual(L.token_y_subtree_borrowed, 890964e6)     # 353e6 + 99763e6 + 8765e6 + 779531e6 + 552e6
        self.assertEqual(LL.token_y_subtree_borrowed, 889059e6)    # 99763e6 + 8765e6 + 779531e6
        self.assertEqual(LR.token_y_subtree_borrowed, 1552e6)
        self.assertEqual(LLR.token_y_subtree_borrowed, 789296e6)   # 8765e6 + 779531e6
        self.assertEqual(LLRR.token_y_subtree_borrowed, 780531e6)  # 779531e6

        # 3.4) removeTLiq
        # 3.3) addTLiq
        vm.warp(32876298273) # T32876298273
        liq_tree.token_x_fee_rate_snapshot += 2352954287417905205553) # 17% APR as Q192.64 T32876298273 - T9214298113
        liq_tree.token_y_fee_rate_snapshot += 6117681147286553534438) # 44.2% APR as Q192.64 T32876298273 - T9214298113

        liq_tree.removeTLiq(LiqRange(3, 7), 1000, 1000e18, 1000e6) # LLRR, LR

        # root
        # A = 0
        # m = 324198833
        #     x: 492e18 * 2352954287417905205553 / 324198833 / 2**64
        # x sub: 5033e18 * 2352954287417905205553 / 324198833 / 2**64
        #     y: 254858e6 * 6117681147286553534438 / 324198833 / 2**64
        # y sub: 1145822e6 * 6117681147286553534438 / 324198833 / 2**64
        self.assertEqual(root.token_x_cummulative_earned_per_m_liq, 1355310898622008714 + 193574177654021)
        self.assertEqual(root.token_x_cummulative_earned_per_m_liq, 8354995844553968361 + 1980200886448553)
        self.assertEqual(root.token_y_cummulative_earned_per_m_liq, 158359374060 + 260707)
        self.assertEqual(root.token_y_cummulative_earned_per_m_liq, 710728860612 + 1172122)

        # L
        # 998e18 * 2352954287417905205553 / 324131393 / 2**64
        # 4541e18 * 2352954287417905205553 / 324131393 / 2**64
        # 353e6 * 6117681147286553534438 / 324131393 / 2**64
        # 890964e6 * 6117681147286553534438 / 324131393 / 2**64
        self.assertEqual(L.token_x_cummulative_earned_per_m_liq, 2749759536746020654 + 392738261220692)
        self.assertEqual(L.token_x_cummulative_earned_per_m_liq, 7001141265402443371 + 1786998441085335)
        self.assertEqual(L.token_y_cummulative_earned_per_m_liq, 219386832 + 361)
        self.assertEqual(L.token_y_cummulative_earned_per_m_liq, 552484409781 + 911603)

        # LL
        # 765e18 * 2352954287417905205553 / 324091721 / 2**64
        # 2519e18 * 2352954287417905205553 / 324091721 / 2**64
        # 99763e6 * 6117681147286553534438 / 324091721 / 2**64
        # 889059e6 * 6117681147286553534438 / 324091721 / 2**64
        self.assertEqual(LL.token_x_cummulative_earned_per_m_liq, 2108110694023652835 + 301083714644757)
        self.assertEqual(LL.token_x_cummulative_earned_per_m_liq, 4185908685257423082 + 991411604170121)
        self.assertEqual(LL.token_y_cummulative_earned_per_m_liq, 62011632404 + 102086)
        self.assertEqual(LL.token_y_cummulative_earned_per_m_liq, 552008141912 + 909766)

        # LR
        # 1024e18 * 2352954287417905205553 / 39672 / 2**64
        # 1024e18 * 2352954287417905205553 / 39672 / 2**64
        # 1552e6 * 6117681147286553534438 / 39672 / 2**64
        # 1552e6 * 6117681147286553534438 / 39672 / 2**64
        self.assertEqual(LR.token_x_cummulative_earned_per_m_liq, 423621837838722923425 + 3292377527956539412)
        self.assertEqual(LR.token_x_cummulative_earned_per_m_liq, 423621837838722923425 + 3292377527956539412)
        self.assertEqual(LR.token_y_cummulative_earned_per_m_liq, 2197359621190 + 12974025)
        self.assertEqual(LR.token_y_cummulative_earned_per_m_liq, 2197359621190 + 12974025)

        # LLR
        # 53e18 * 2352954287417905205553 / 305908639 / 2**64
        # 1754e18 * 2352954287417905205553 / 305908639 / 2**64
        # 8765e6 * 6117681147286553534438 / 305908639 / 2**64
        # 789296e6 * 6117681147286553534438 / 305908639 / 2**64
        self.assertEqual(LLR.token_x_cummulative_earned_per_m_liq, 154733312657952738 + 22099268330799)
        self.assertEqual(LLR.token_x_cummulative_earned_per_m_liq, 2201300334794271053 + 731360691551353)
        self.assertEqual(LLR.token_y_cummulative_earned_per_m_liq, 5772069627 + 9502)
        self.assertEqual(LLR.token_y_cummulative_earned_per_m_liq, 519121437518 + 855687)

        # LLRR
        # 1701e18 * 2352954287417905205553 / 296771752 / 2**64
        # 1701e18 * 2352954287417905205553 / 296771752 / 2**64
        # 780531e6 * 6117681147286553534438 / 296771752 / 2**64
        # 780531e6 * 6117681147286553534438 / 296771752 / 2**64
        self.assertEqual(LLRR.token_x_cummulative_earned_per_m_liq, 2109575308294031901 + 731097873063750)
        self.assertEqual(LLRR.token_x_cummulative_earned_per_m_liq, 2109575308294031901 + 731097873063750)
        self.assertEqual(LLRR.token_y_cummulative_earned_per_m_liq, 529154012121 + 872237)
        self.assertEqual(LLRR.token_y_cummulative_earned_per_m_liq, 529154012121 + 872237)

        # t_liq
        self.assertEqual(root.t_liq, 4430)
        self.assertEqual(L.t_liq, 77)
        self.assertEqual(LL.t_liq, 82734)
        self.assertEqual(LR.t_liq, 111)
        self.assertEqual(LLR.t_liq, 5346)
        self.assertEqual(LLRR.t_liq, 7634865)

        # subtree_m_liq
        self.assertEqual(root.subtree_m_liq, 324198833) # 8430*16 + 377*8 + 9082734*4 + 1111*4 + 45346*2 + 287634865*1
        self.assertEqual(L.subtree_m_liq, 324063953)    # 377*8 + 9082734*4 + 1111*4 + 45346*2 + 287634865*1
        self.assertEqual(LL.subtree_m_liq, 324056493)   # 9082734*4 + 45346*2 + 287634865*1
        self.assertEqual(LR.subtree_m_liq, 4444)        # 1111*4
        self.assertEqual(LLR.subtree_m_liq, 287725557)  # 45346*2 + 287634865*1
        self.assertEqual(LLRR.subtree_m_liq, 287634865) # 287634865*1

        # borrowed_x
        self.assertEqual(root.token_x_borrowed, 492e18)
        self.assertEqual(L.token_x_borrowed, 998e18)
        self.assertEqual(LL.token_x_borrowed, 765e18)
        self.assertEqual(LR.token_x_borrowed, 24e18)
        self.assertEqual(LLR.token_x_borrowed, 53e18)
        self.assertEqual(LLRR.token_x_borrowed, 701e18)

        # borrowed_y
        self.assertEqual(root.token_y_borrowed, 254858e6)
        self.assertEqual(L.token_y_borrowed, 353e6)
        self.assertEqual(LL.token_y_borrowed, 99763e6)
        self.assertEqual(LR.token_y_borrowed, 552e6)
        self.assertEqual(LLR.token_y_borrowed, 8765e6)
        self.assertEqual(LLRR.token_y_borrowed, 779531e6)

        # subtree_borrowed_x
        self.assertEqual(root.token_x_subtree_borrowed, 3033e18) # 492e18 + 998e18 + 765e18 + 53e18 + 701e18 + 24e18
        self.assertEqual(L.token_x_subtree_borrowed, 2541e18)    # 998e18 + 765e18 + 53e18 + 701e18 + 24e18
        self.assertEqual(LL.token_x_subtree_borrowed, 1519e18)   # 765e18 + 53e18 + 701e18
        self.assertEqual(LR.token_x_subtree_borrowed, 24e18)
        self.assertEqual(LLR.token_x_subtree_borrowed, 754e18)   # 53e18 + 701e18
        self.assertEqual(LLRR.token_x_subtree_borrowed, 701e18)  # 701e18

        # subtree_borrowed_y
        self.assertEqual(root.token_y_subtree_borrowed, 1143822e6) # 254858e6 + 353e6 + 99763e6 + 8765e6 + 779531e6 + 552e6
        self.assertEqual(L.token_y_subtree_borrowed, 888964e6)     # 353e6 + 99763e6 + 8765e6 + 779531e6 + 552e6
        self.assertEqual(LL.token_y_subtree_borrowed, 888059e6)    # 99763e6 + 8765e6 + 779531e6
        self.assertEqual(LR.token_y_subtree_borrowed, 552e6)
        self.assertEqual(LLR.token_y_subtree_borrowed, 788296e6)   # 8765e6 + 779531e6
        self.assertEqual(LLRR.token_y_subtree_borrowed, 779531e6)  # 779531e6
    }


    function testRightLegOnly() public {
        LiqNode storage root = liq_tree.nodes[liq_tree.root];
        LiqNode storage R = liq_tree.nodes[_nodeKey(1, 1, liq_tree.offset)];
        LiqNode storage RR = liq_tree.nodes[_nodeKey(2, 3, liq_tree.offset)];
        LiqNode storage RL = liq_tree.nodes[_nodeKey(2, 2, liq_tree.offset)];
        LiqNode storage RRL = liq_tree.nodes[_nodeKey(3, 6, liq_tree.offset)];
        LiqNode storage RRLL = liq_tree.nodes[_nodeKey(4, 12, liq_tree.offset)];

        # Step 1) Allocate different m_liq + t_liq values for each node
        vm.warp(0) # T0

        liq_tree.addInfRangeMLiq(8430)                # root   (INF)
        liq_tree.add_m_liq(LiqRange(8, 15), 377)        # R     (8-15)
        liq_tree.add_m_liq(LiqRange(12, 15), 9082734)   # RR   (12-15)
        liq_tree.add_m_liq(LiqRange(8, 11), 1111)       # RL    (8-11)
        liq_tree.add_m_liq(LiqRange(12, 13), 45346)     # RRL  (12-13)
        liq_tree.add_m_liq(LiqRange(12, 12), 287634865) # RRLL    (12)

        liq_tree.addInfRangeTLiq(4430, 492e18, 254858e6)              # root
        liq_tree.addTLiq(LiqRange(8, 15), 77, 998e18, 353e6)          # R 
        liq_tree.addTLiq(LiqRange(12, 15), 82734, 765e18, 99763e6)    # RR
        liq_tree.addTLiq(LiqRange(8, 11), 111, 24e18, 552e6)          # RL
        liq_tree.addTLiq(LiqRange(12, 13), 5346, 53e18, 8765e6)       # RRL
        liq_tree.addTLiq(LiqRange(12, 12), 7634865, 701e18, 779531e6) # RRLL

        # m_liq
        self.assertEqual(root.m_liq, 8430)
        self.assertEqual(R.m_liq, 377)
        self.assertEqual(RR.m_liq, 9082734)
        self.assertEqual(RL.m_liq, 1111)
        self.assertEqual(RRL.m_liq, 45346)
        self.assertEqual(RRLL.m_liq, 287634865)

        # t_liq
        self.assertEqual(root.t_liq, 4430)
        self.assertEqual(R.t_liq, 77)
        self.assertEqual(RR.t_liq, 82734)
        self.assertEqual(RL.t_liq, 111)
        self.assertEqual(RRL.t_liq, 5346)
        self.assertEqual(RRLL.t_liq, 7634865)

        # subtree_m_liq
        self.assertEqual(root.subtree_m_liq, 324198833) # 8430*16 + 377*8 + 9082734*4 + 1111*4 + 45346*2 + 287634865*1
        self.assertEqual(R.subtree_m_liq, 324063953)    # 377*8 + 9082734*4 + 1111*4 + 45346*2 + 287634865*1
        self.assertEqual(RR.subtree_m_liq, 324056493)   # 9082734*4 + 45346*2 + 287634865*1
        self.assertEqual(RL.subtree_m_liq, 4444)        # 1111*4
        self.assertEqual(RRL.subtree_m_liq, 287725557)  # 45346*2 + 287634865*1
        self.assertEqual(RRLL.subtree_m_liq, 287634865) # 287634865*1

        # borrowed_x
        self.assertEqual(root.token_x_borrowed, 492e18)
        self.assertEqual(R.token_x_borrowed, 998e18)
        self.assertEqual(RR.token_x_borrowed, 765e18)
        self.assertEqual(RL.token_x_borrowed, 24e18)
        self.assertEqual(RRL.token_x_borrowed, 53e18)
        self.assertEqual(RRLL.token_x_borrowed, 701e18)

        # borrowed_y
        self.assertEqual(root.token_y_borrowed, 254858e6)
        self.assertEqual(R.token_y_borrowed, 353e6)
        self.assertEqual(RR.token_y_borrowed, 99763e6)
        self.assertEqual(RL.token_y_borrowed, 552e6)
        self.assertEqual(RRL.token_y_borrowed, 8765e6)
        self.assertEqual(RRLL.token_y_borrowed, 779531e6)

        # subtree_borrowed_x
        self.assertEqual(root.token_x_subtree_borrowed, 3033e18) # 492e18 + 998e18 + 765e18 + 53e18 + 701e18 + 24e18
        self.assertEqual(R.token_x_subtree_borrowed, 2541e18)    # 998e18 + 765e18 + 53e18 + 701e18 + 24e18
        self.assertEqual(RR.token_x_subtree_borrowed, 1519e18)   # 765e18 + 53e18 + 701e18
        self.assertEqual(RL.token_x_subtree_borrowed, 24e18)
        self.assertEqual(RRL.token_x_subtree_borrowed, 754e18)   # 53e18 + 701e18
        self.assertEqual(RRLL.token_x_subtree_borrowed, 701e18)  # 701e18

        # subtree_borrowed_y
        self.assertEqual(root.token_y_subtree_borrowed, 1143822e6) # 254858e6 + 353e6 + 99763e6 + 8765e6 + 779531e6 + 552e6
        self.assertEqual(R.token_y_subtree_borrowed, 888964e6)     # 353e6 + 99763e6 + 8765e6 + 779531e6 + 552e6
        self.assertEqual(RR.token_y_subtree_borrowed, 888059e6)    # 99763e6 + 8765e6 + 779531e6
        self.assertEqual(RL.token_y_subtree_borrowed, 552e6)
        self.assertEqual(RRL.token_y_subtree_borrowed, 788296e6)   # 8765e6 + 779531e6
        self.assertEqual(RRLL.token_y_subtree_borrowed, 779531e6)  # 779531e6

        # Step 2) Assign different rates for X & Y
        vm.warp(98273) # T98273
        liq_tree.token_x_fee_rate_snapshot += 4541239648278065)  # 7.9% APR as Q192.64 T98273 - T0
        liq_tree.token_y_fee_rate_snapshot += 13278814667749784) # 23.1% APR as Q192.64 T98273 - T0

        # Step 3) Apply change that effects the entire tree, to calculate the fees at each node
        # 3.1) add_m_liq
        liq_tree.add_m_liq(LiqRange(8, 12), 2734) # RRLL, RL

        # root
        self.assertEqual(root.token_x_cummulative_earned_per_m_liq, 373601278)
        self.assertEqual(root.token_x_cummulative_earned_per_m_liq, 2303115199)
        self.assertEqual(root.token_y_cummulative_earned_per_m_liq, 0)
        self.assertEqual(root.token_y_cummulative_earned_per_m_liq, 2)

        # R
        self.assertEqual(R.token_x_cummulative_earned_per_m_liq, 757991165)
        self.assertEqual(R.token_x_cummulative_earned_per_m_liq, 1929915382)
        self.assertEqual(R.token_y_cummulative_earned_per_m_liq, 0)
        self.assertEqual(R.token_y_cummulative_earned_per_m_liq, 1)

        # RR
        self.assertEqual(RR.token_x_cummulative_earned_per_m_liq, 581096415)
        self.assertEqual(RR.token_x_cummulative_earned_per_m_liq, 1153837196)
        self.assertEqual(RR.token_y_cummulative_earned_per_m_liq, 0)
        self.assertEqual(RR.token_y_cummulative_earned_per_m_liq, 1)

        # RL
        self.assertEqual(RL.token_x_cummulative_earned_per_m_liq, 148929881804)
        self.assertEqual(RL.token_x_cummulative_earned_per_m_liq, 148929881804)
        self.assertEqual(RL.token_y_cummulative_earned_per_m_liq, 10)
        self.assertEqual(RL.token_y_cummulative_earned_per_m_liq, 10)

        # RRL
        self.assertEqual(RRL.token_x_cummulative_earned_per_m_liq, 42651943)
        self.assertEqual(RRL.token_x_cummulative_earned_per_m_liq, 606784254)
        self.assertEqual(RRL.token_y_cummulative_earned_per_m_liq, 0)
        self.assertEqual(RRL.token_y_cummulative_earned_per_m_liq, 1)

        # RRLL
        self.assertEqual(RRLL.token_x_cummulative_earned_per_m_liq, 581500584)
        self.assertEqual(RRLL.token_x_cummulative_earned_per_m_liq, 581500584)
        self.assertEqual(RRLL.token_y_cummulative_earned_per_m_liq, 1)
        self.assertEqual(RRLL.token_y_cummulative_earned_per_m_liq, 1)

        # m_liq
        self.assertEqual(root.m_liq, 8430)
        self.assertEqual(R.m_liq, 377)
        self.assertEqual(RR.m_liq, 9082734)
        self.assertEqual(RL.m_liq, 3845)
        self.assertEqual(RRL.m_liq, 45346)
        self.assertEqual(RRLL.m_liq, 287637599)

        # subtree_m_liq
        self.assertEqual(root.subtree_m_liq, 324212503) # 8430*16 + 377*8 + 9082734*4 + 3845*4 + 45346*2 + 287637599*1
        self.assertEqual(R.subtree_m_liq, 324077623)    # 377*8 + 9082734*4 + 3845*4 + 45346*2 + 287637599*1
        self.assertEqual(RR.subtree_m_liq, 324059227)   # 9082734*4 + 45346*2 + 287637599*1
        self.assertEqual(RL.subtree_m_liq, 15380)       # 3845*4
        self.assertEqual(RRL.subtree_m_liq, 287728291)  # 45346*2 + 287637599*1
        self.assertEqual(RRLL.subtree_m_liq, 287637599) # 287637599*1

        # 3.2) removeMLiq
        vm.warp(2876298273) # T2876298273
        liq_tree.token_x_fee_rate_snapshot += 16463537718422861220174597)   # 978567.9% APR as Q192.64 T2876298273 - T98273
        liq_tree.token_y_fee_rate_snapshot += 3715979586694123491881712207) # 220872233.1% APR as Q192.64 T2876298273 - T98273

        liq_tree.removeMLiq(LiqRange(8, 12), 2734) # RRLL, RL

        # root
        self.assertEqual(root.token_x_cummulative_earned_per_m_liq, 373601278 + 1354374549470516050)         # 1354374549844117328
        self.assertEqual(root.token_x_cummulative_earned_per_m_liq, 2303115199 + 8349223594601778821) # 8349223596904894020
        self.assertEqual(root.token_y_cummulative_earned_per_m_liq, 0 + 158351473403)                        # 158351473403
        self.assertEqual(root.token_y_cummulative_earned_per_m_liq, 2 + 710693401861)                 # 710693401863

        # R
        self.assertEqual(R.token_x_cummulative_earned_per_m_liq, 757991165 + 2747859799177149412)         # 2747859799935140577
        self.assertEqual(R.token_x_cummulative_earned_per_m_liq, 1929915382 + 6996304358425988634) # 6996304360355904016
        self.assertEqual(R.token_y_cummulative_earned_per_m_liq, 0 + 219375887)                           # 219375887
        self.assertEqual(R.token_y_cummulative_earned_per_m_liq, 1 + 552456845955)                 # 552456845956

        # RR
        self.assertEqual(RR.token_x_cummulative_earned_per_m_liq, 581096415 + 2106654304105573173)         # 2106654304686669588
        self.assertEqual(RR.token_x_cummulative_earned_per_m_liq, 1153837196 + 4183016846975641372) # 4183016848129478568
        self.assertEqual(RR.token_y_cummulative_earned_per_m_liq, 0 + 62008538706)                         # 62008538706
        self.assertEqual(RR.token_y_cummulative_earned_per_m_liq, 1 + 551980602776)                 # 551980602777

        # RL
        self.assertEqual(RL.token_x_cummulative_earned_per_m_liq, 148929881804 + 423248577958689008325)        # 423248578107618890129
        self.assertEqual(RL.token_x_cummulative_earned_per_m_liq, 148929881804 + 423248577958689008325) # 423248578107618890129
        self.assertEqual(RL.token_y_cummulative_earned_per_m_liq, 10 + 2197219781185)                          # 2197219781195
        self.assertEqual(RL.token_y_cummulative_earned_per_m_liq, 10 + 2197219781185)                   # 2197219781195

        # RRL
        self.assertEqual(RRL.token_x_cummulative_earned_per_m_liq, 42651943 + 154626414974589533)          # 154626415017241476
        self.assertEqual(RRL.token_x_cummulative_earned_per_m_liq, 606784254 + 2199779563978122803) # 2199779564584907057
        self.assertEqual(RRL.token_y_cummulative_earned_per_m_liq, 0 + 5771781665)                         # 5771781665
        self.assertEqual(RRL.token_y_cummulative_earned_per_m_liq, 1 + 519095539054)                # 519095539055

        # RRLL
        self.assertEqual(RRLL.token_x_cummulative_earned_per_m_liq, 581500584 + 2108117905415037748)         # 2108117905996538332
        self.assertEqual(RRLL.token_x_cummulative_earned_per_m_liq, 581500584 + 2108117905415037748)  # 2108117905996538332
        self.assertEqual(RRLL.token_y_cummulative_earned_per_m_liq, 1 + 529127613134)                        # 529127613135
        self.assertEqual(RRLL.token_y_cummulative_earned_per_m_liq, 1 + 529127613134)                 # 529127613135

        # m_liq
        self.assertEqual(root.m_liq, 8430)
        self.assertEqual(R.m_liq, 377)
        self.assertEqual(RR.m_liq, 9082734)
        self.assertEqual(RL.m_liq, 1111)
        self.assertEqual(RRL.m_liq, 45346)
        self.assertEqual(RRLL.m_liq, 287634865)

        # subtree_m_liq
        self.assertEqual(root.subtree_m_liq, 324198833) # 8430*16 + 377*8 + 9082734*4 + 1111*4 + 45346*2 + 287634865*1
        self.assertEqual(R.subtree_m_liq, 324063953)    # 377*8 + 9082734*4 + 1111*4 + 45346*2 + 287634865*1
        self.assertEqual(RR.subtree_m_liq, 324056493)   # 9082734*4 + 45346*2 + 287634865*1
        self.assertEqual(RL.subtree_m_liq, 4444)        # 1111*4
        self.assertEqual(RRL.subtree_m_liq, 287725557)  # 45346*2 + 287634865*1
        self.assertEqual(RRLL.subtree_m_liq, 287634865) # 287634865*1

        # 3.3) addTLiq
        vm.warp(9214298113) # T2876298273
        liq_tree.token_x_fee_rate_snapshot += 11381610389149375791104)   # 307% APR as Q192.64 T9214298113 - T2876298273
        liq_tree.token_y_fee_rate_snapshot += 185394198934916215865344)  # 5000.7% APR as Q192.64 T9214298113 - T2876298273

        liq_tree.addTLiq(LiqRange(8, 12), 1000, 1000e18, 1000e6) # RRLL, RL

        # root
        self.assertEqual(root.token_x_cummulative_earned_per_m_liq, 1354374549844117328 + 936348777891386)         # 1355310898622008714
        self.assertEqual(root.token_x_cummulative_earned_per_m_liq, 8349223596904894020 + 5772247649074341) # 8354995844553968361
        self.assertEqual(root.token_y_cummulative_earned_per_m_liq, 158351473403 + 7900657)                        # 158359374060
        self.assertEqual(root.token_y_cummulative_earned_per_m_liq, 710693401863 + 35458749)                # 710728860612

        # R
        self.assertEqual(R.token_x_cummulative_earned_per_m_liq, 2747859799935140577 + 1899736810880077)        # 2749759536746020654
        self.assertEqual(R.token_x_cummulative_earned_per_m_liq, 6996304360355904016 + 4836905046539355) # 7001141265402443371
        self.assertEqual(R.token_y_cummulative_earned_per_m_liq, 219375887 + 10945)                             # 219386832
        self.assertEqual(R.token_y_cummulative_earned_per_m_liq, 552456845956 + 27563825)                # 552484409781

        # RR
        self.assertEqual(RR.token_x_cummulative_earned_per_m_liq, 2106654304686669588 + 1456389336983247)        # 2108110694023652835
        self.assertEqual(RR.token_x_cummulative_earned_per_m_liq, 4183016848129478568 + 2891837127944514) # 4185908685257423082
        self.assertEqual(RR.token_y_cummulative_earned_per_m_liq, 62008538706 + 3093698)                         # 62011632404
        self.assertEqual(RR.token_y_cummulative_earned_per_m_liq, 551980602777 + 27539135)                # 552008141912

        # RL
        self.assertEqual(RL.token_x_cummulative_earned_per_m_liq, 423248578107618890129 + 373259731104033296)        # 423621837838722923425
        self.assertEqual(RL.token_x_cummulative_earned_per_m_liq, 423248578107618890129 + 373259731104033296) # 423621837838722923425
        self.assertEqual(RL.token_y_cummulative_earned_per_m_liq, 2197219781195 + 139839995)                         # 2197359621190
        self.assertEqual(RL.token_y_cummulative_earned_per_m_liq, 2197219781195 + 139839995)                  # 2197359621190

        # RRL
        self.assertEqual(RRL.token_x_cummulative_earned_per_m_liq, 154626415017241476 + 106897640711262)          # 154733312657952738
        self.assertEqual(RRL.token_x_cummulative_earned_per_m_liq, 2199779564584907057 + 1520770209363996) # 2201300334794271053
        self.assertEqual(RRL.token_y_cummulative_earned_per_m_liq, 5771781665 + 287962)                           # 5772069627
        self.assertEqual(RRL.token_y_cummulative_earned_per_m_liq, 519095539055 + 25898463)                # 519121437518

        # RRLL
        self.assertEqual(RRLL.token_x_cummulative_earned_per_m_liq, 2108117905996538332 + 1457402297493569)        # 2109575308294031901
        self.assertEqual(RRLL.token_x_cummulative_earned_per_m_liq, 2108117905996538332 + 1457402297493569) # 2109575308294031901
        self.assertEqual(RRLL.token_y_cummulative_earned_per_m_liq, 529127613135 + 26398986)                       # 529154012121
        self.assertEqual(RRLL.token_y_cummulative_earned_per_m_liq, 529127613135 + 26398986)                # 529154012121

        # t_liq
        self.assertEqual(root.t_liq, 4430)
        self.assertEqual(R.t_liq, 77)
        self.assertEqual(RR.t_liq, 82734)
        self.assertEqual(RL.t_liq, 1111)
        self.assertEqual(RRL.t_liq, 5346)
        self.assertEqual(RRLL.t_liq, 7635865)

        # borrowed_x
        self.assertEqual(root.token_x_borrowed, 492e18)
        self.assertEqual(R.token_x_borrowed, 998e18)
        self.assertEqual(RR.token_x_borrowed, 765e18)
        self.assertEqual(RL.token_x_borrowed, 1024e18)
        self.assertEqual(RRL.token_x_borrowed, 53e18)
        self.assertEqual(RRLL.token_x_borrowed, 1701e18)

        # borrowed_y
        self.assertEqual(root.token_y_borrowed, 254858e6)
        self.assertEqual(R.token_y_borrowed, 353e6)
        self.assertEqual(RR.token_y_borrowed, 99763e6)
        self.assertEqual(RL.token_y_borrowed, 1552e6)
        self.assertEqual(RRL.token_y_borrowed, 8765e6)
        self.assertEqual(RRLL.token_y_borrowed, 780531e6)

        # subtree_borrowed_x
        self.assertEqual(root.token_x_subtree_borrowed, 5033e18)  # 492e18 + 998e18 + 765e18 + 53e18 + 701e18 + 24e18
        self.assertEqual(R.token_x_subtree_borrowed, 4541e18)     # 998e18 + 765e18 + 53e18 + 701e18 + 24e18
        self.assertEqual(RR.token_x_subtree_borrowed, 2519e18)    # 765e18 + 53e18 + 701e18
        self.assertEqual(RL.token_x_subtree_borrowed, 1024e18)
        self.assertEqual(RRL.token_x_subtree_borrowed, 1754e18)   # 53e18 + 701e18
        self.assertEqual(RRLL.token_x_subtree_borrowed, 1701e18)  # 701e18

        # subtree_borrowed_y
        self.assertEqual(root.token_y_subtree_borrowed, 1145822e6) # 254858e6 + 353e6 + 99763e6 + 8765e6 + 779531e6 + 552e6
        self.assertEqual(R.token_y_subtree_borrowed, 890964e6)     # 353e6 + 99763e6 + 8765e6 + 779531e6 + 552e6
        self.assertEqual(RR.token_y_subtree_borrowed, 889059e6)    # 99763e6 + 8765e6 + 779531e6
        self.assertEqual(RL.token_y_subtree_borrowed, 1552e6)
        self.assertEqual(RRL.token_y_subtree_borrowed, 789296e6)   # 8765e6 + 779531e6
        self.assertEqual(RRLL.token_y_subtree_borrowed, 780531e6)  # 779531e6

        # 3.4) removeTLiq
        # 3.3) addTLiq
        vm.warp(32876298273) # T32876298273
        liq_tree.token_x_fee_rate_snapshot += 2352954287417905205553) # 17% APR as Q192.64 T32876298273 - T9214298113
        liq_tree.token_y_fee_rate_snapshot += 6117681147286553534438) # 44.2% APR as Q192.64 T32876298273 - T9214298113

        liq_tree.removeTLiq(LiqRange(8, 12), 1000, 1000e18, 1000e6) # RRLL, RL

        # root
        # A = 0
        # m = 324198833
        #     x: 492e18 * 2352954287417905205553 / 324198833 / 2**64
        # x sub: 5033e18 * 2352954287417905205553 / 324198833 / 2**64
        #     y: 254858e6 * 6117681147286553534438 / 324198833 / 2**64
        # y sub: 1145822e6 * 6117681147286553534438 / 324198833 / 2**64
        self.assertEqual(root.token_x_cummulative_earned_per_m_liq, 1355310898622008714 + 193574177654021)
        self.assertEqual(root.token_x_cummulative_earned_per_m_liq, 8354995844553968361 + 1980200886448553)
        self.assertEqual(root.token_y_cummulative_earned_per_m_liq, 158359374060 + 260707)
        self.assertEqual(root.token_y_cummulative_earned_per_m_liq, 710728860612 + 1172122)

        # R
        # 998e18 * 2352954287417905205553 / 324131393 / 2**64
        # 4541e18 * 2352954287417905205553 / 324131393 / 2**64
        # 353e6 * 6117681147286553534438 / 324131393 / 2**64
        # 890964e6 * 6117681147286553534438 / 324131393 / 2**64
        self.assertEqual(R.token_x_cummulative_earned_per_m_liq, 2749759536746020654 + 392738261220692)
        self.assertEqual(R.token_x_cummulative_earned_per_m_liq, 7001141265402443371 + 1786998441085335)
        self.assertEqual(R.token_y_cummulative_earned_per_m_liq, 219386832 + 361)
        self.assertEqual(R.token_y_cummulative_earned_per_m_liq, 552484409781 + 911603)

        # RR
        # 765e18 * 2352954287417905205553 / 324091721 / 2**64
        # 2519e18 * 2352954287417905205553 / 324091721 / 2**64
        # 99763e6 * 6117681147286553534438 / 324091721 / 2**64
        # 889059e6 * 6117681147286553534438 / 324091721 / 2**64
        self.assertEqual(RR.token_x_cummulative_earned_per_m_liq, 2108110694023652835 + 301083714644757)
        self.assertEqual(RR.token_x_cummulative_earned_per_m_liq, 4185908685257423082 + 991411604170121)
        self.assertEqual(RR.token_y_cummulative_earned_per_m_liq, 62011632404 + 102086)
        self.assertEqual(RR.token_y_cummulative_earned_per_m_liq, 552008141912 + 909766)

        # RL
        # 1024e18 * 2352954287417905205553 / 39672 / 2**64
        # 1024e18 * 2352954287417905205553 / 39672 / 2**64
        # 1552e6 * 6117681147286553534438 / 39672 / 2**64
        # 1552e6 * 6117681147286553534438 / 39672 / 2**64
        self.assertEqual(RL.token_x_cummulative_earned_per_m_liq, 423621837838722923425 + 3292377527956539412)
        self.assertEqual(RL.token_x_cummulative_earned_per_m_liq, 423621837838722923425 + 3292377527956539412)
        self.assertEqual(RL.token_y_cummulative_earned_per_m_liq, 2197359621190 + 12974025)
        self.assertEqual(RL.token_y_cummulative_earned_per_m_liq, 2197359621190 + 12974025)

        # RRL
        # 53e18 * 2352954287417905205553 / 305908639 / 2**64
        # 1754e18 * 2352954287417905205553 / 305908639 / 2**64
        # 8765e6 * 6117681147286553534438 / 305908639 / 2**64
        # 789296e6 * 6117681147286553534438 / 305908639 / 2**64
        self.assertEqual(RRL.token_x_cummulative_earned_per_m_liq, 154733312657952738 + 22099268330799)
        self.assertEqual(RRL.token_x_cummulative_earned_per_m_liq, 2201300334794271053 + 731360691551353)
        self.assertEqual(RRL.token_y_cummulative_earned_per_m_liq, 5772069627 + 9502)
        self.assertEqual(RRL.token_y_cummulative_earned_per_m_liq, 519121437518 + 855687)

        # RRLL
        # 1701e18 * 2352954287417905205553 / 296771752 / 2**64
        # 1701e18 * 2352954287417905205553 / 296771752 / 2**64
        # 780531e6 * 6117681147286553534438 / 296771752 / 2**64
        # 780531e6 * 6117681147286553534438 / 296771752 / 2**64
        self.assertEqual(RRLL.token_x_cummulative_earned_per_m_liq, 2109575308294031901 + 731097873063750)
        self.assertEqual(RRLL.token_x_cummulative_earned_per_m_liq, 2109575308294031901 + 731097873063750)
        self.assertEqual(RRLL.token_y_cummulative_earned_per_m_liq, 529154012121 + 872237)
        self.assertEqual(RRLL.token_y_cummulative_earned_per_m_liq, 529154012121 + 872237)

        # t_liq
        self.assertEqual(root.t_liq, 4430)
        self.assertEqual(R.t_liq, 77)
        self.assertEqual(RR.t_liq, 82734)
        self.assertEqual(RL.t_liq, 111)
        self.assertEqual(RRL.t_liq, 5346)
        self.assertEqual(RRLL.t_liq, 7634865)

        # subtree_m_liq
        self.assertEqual(root.subtree_m_liq, 324198833) # 8430*16 + 377*8 + 9082734*4 + 1111*4 + 45346*2 + 287634865*1
        self.assertEqual(R.subtree_m_liq, 324063953)    # 377*8 + 9082734*4 + 1111*4 + 45346*2 + 287634865*1
        self.assertEqual(RR.subtree_m_liq, 324056493)   # 9082734*4 + 45346*2 + 287634865*1
        self.assertEqual(RL.subtree_m_liq, 4444)        # 1111*4
        self.assertEqual(RRL.subtree_m_liq, 287725557)  # 45346*2 + 287634865*1
        self.assertEqual(RRLL.subtree_m_liq, 287634865) # 287634865*1

        # borrowed_x
        self.assertEqual(root.token_x_borrowed, 492e18)
        self.assertEqual(R.token_x_borrowed, 998e18)
        self.assertEqual(RR.token_x_borrowed, 765e18)
        self.assertEqual(RL.token_x_borrowed, 24e18)
        self.assertEqual(RRL.token_x_borrowed, 53e18)
        self.assertEqual(RRLL.token_x_borrowed, 701e18)

        # borrowed_y
        self.assertEqual(root.token_y_borrowed, 254858e6)
        self.assertEqual(R.token_y_borrowed, 353e6)
        self.assertEqual(RR.token_y_borrowed, 99763e6)
        self.assertEqual(RL.token_y_borrowed, 552e6)
        self.assertEqual(RRL.token_y_borrowed, 8765e6)
        self.assertEqual(RRLL.token_y_borrowed, 779531e6)

        # subtree_borrowed_x
        self.assertEqual(root.token_x_subtree_borrowed, 3033e18) # 492e18 + 998e18 + 765e18 + 53e18 + 701e18 + 24e18
        self.assertEqual(R.token_x_subtree_borrowed, 2541e18)    # 998e18 + 765e18 + 53e18 + 701e18 + 24e18
        self.assertEqual(RR.token_x_subtree_borrowed, 1519e18)   # 765e18 + 53e18 + 701e18
        self.assertEqual(RL.token_x_subtree_borrowed, 24e18)
        self.assertEqual(RRL.token_x_subtree_borrowed, 754e18)   # 53e18 + 701e18
        self.assertEqual(RRLL.token_x_subtree_borrowed, 701e18)  # 701e18

        # subtree_borrowed_y
        self.assertEqual(root.token_y_subtree_borrowed, 1143822e6) # 254858e6 + 353e6 + 99763e6 + 8765e6 + 779531e6 + 552e6
        self.assertEqual(R.token_y_subtree_borrowed, 888964e6)     # 353e6 + 99763e6 + 8765e6 + 779531e6 + 552e6
        self.assertEqual(RR.token_y_subtree_borrowed, 888059e6)    # 99763e6 + 8765e6 + 779531e6
        self.assertEqual(RL.token_y_subtree_borrowed, 552e6)
        self.assertEqual(RRL.token_y_subtree_borrowed, 788296e6)   # 8765e6 + 779531e6
        self.assertEqual(RRLL.token_y_subtree_borrowed, 779531e6)  # 779531e6
    }

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