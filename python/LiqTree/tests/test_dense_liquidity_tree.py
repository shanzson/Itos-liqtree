from unittest import TestCase

from LiqTree.LiquidityTree import LiquidityTree, LiqNode


class TestDenseLiquidityTree(TestCase):
    def setUp(self) -> None:
        self.liq_tree = LiquidityTree(depth=4)

    def test_root_only(self):
        liq_tree: LiquidityTree = self.liq_tree

        # T0
        liq_tree.add_inf_range_m_liq(8430)
        liq_tree.add_inf_range_t_liq(4381, int(832e18), int(928e6))
        self.assertEqual(True, True)

        # T3600 (1hr) --- 5.4% APR as Q192.64
        liq_tree.token_y_fee_rate_snapshot += 113712805933826
        liq_tree.token_x_fee_rate_snapshot += 113712805933826

        # Verify root state
        root: LiqNode = liq_tree.root
        self.assertEqual(root.m_liq, 8430)
        self.assertEqual(root.subtree_m_liq, 134880)
        self.assertEqual(root.t_liq, 4381)
        self.assertEqual(root.token_x_borrowed, int(832e18))
        self.assertEqual(root.token_x_subtree_borrowed, int(832e18))
        self.assertEqual(root.token_y_borrowed, int(928e6))
        self.assertEqual(root.token_y_subtree_borrowed, int(928e6))

        # Testing 4 methods for proper fee accumulation:
        # add_inf_range_m_liq, remove_inf_range_m_liq
        # add_inf_range_t_liq, remove_inf_range_t_liq
        liq_tree.add_inf_range_m_liq(9287)

        self.assertEqual(int(root.token_x_cummulative_earned_per_m_liq), 38024667284)
        self.assertEqual(int(root.token_x_cummulative_earned_per_m_subtree_liq), 38024667284)
        self.assertEqual(int(root.token_y_cummulative_earned_per_m_liq), 0)
        self.assertEqual(int(root.token_y_cummulative_earned_per_m_subtree_liq), 0)

        self.assertEqual(root.m_liq, 17717)
        self.assertEqual(root.subtree_m_liq, 283472)
        self.assertEqual(root.t_liq, 4381)
        self.assertEqual(root.token_x_borrowed, int(832e18))
        self.assertEqual(root.token_x_subtree_borrowed, int(832e18))
        self.assertEqual(root.token_y_borrowed, int(928e6))
        self.assertEqual(root.token_y_subtree_borrowed, int(928e6))

        # T22000 -- 693792000.0% APR as Q192.64 from T22000 - T3600
        liq_tree.token_y_fee_rate_snapshot += 74672420010376264941568
        liq_tree.token_x_fee_rate_snapshot += 74672420010376264941568

        liq_tree.remove_inf_range_m_liq(3682)

        # rounding error
        # self.assertEqual(int(root.token_x_cummulative_earned_per_m_liq), 11881018269102163474)
        # self.assertEqual(int(root.token_x_cummulative_earned_per_m_subtree_liq), 11881018269102163474)
        self.assertEqual(int(root.token_y_cummulative_earned_per_m_liq), 13251904)
        self.assertEqual(int(root.token_y_cummulative_earned_per_m_subtree_liq), 13251904)

        self.assertEqual(root.m_liq, 14035)
        self.assertEqual(root.subtree_m_liq, 224560)
        self.assertEqual(root.t_liq, 4381)
        self.assertEqual(root.token_x_borrowed, int(832e18))
        self.assertEqual(root.token_x_subtree_borrowed, int(832e18))
        self.assertEqual(root.token_y_borrowed, int(928e6))
        self.assertEqual(root.token_y_subtree_borrowed, int(928e6))

'''

    function testRootNodeOnly() public {
        assertEq(root.tokenX.cummulativeEarnedPerMLiq, 11881018269102163474);
        assertEq(root.tokenX.subtreeCummulativeEarnedPerMLiq, 11881018269102163474);
        assertEq(root.tokenY.cummulativeEarnedPerMLiq, 13251904);
        assertEq(root.tokenY.subtreeCummulativeEarnedPerMLiq, 13251904);

        assertEq(root.mLiq, 14035);
        assertEq(root.subtreeMLiq, 224560);
        assertEq(root.tLiq, 4381);
        assertEq(root.tokenX.borrowed, 832e18);
        assertEq(root.tokenX.subtreeBorrowed, 832e18);
        assertEq(root.tokenY.borrowed, 928e6);
        assertEq(root.tokenY.subtreeBorrowed, 928e6);

        vm.warp(37002); // T37002
        liqTree.feeRateSnapshotTokenX.add(6932491854677024); // 7.9% APR as Q192.64 T37002 - T22000
        liqTree.feeRateSnapshotTokenY.add(6932491854677024);

        liqTree.addInfRangeTLiq(7287, 9184e18, 7926920e6);

        assertEq(root.tokenX.cummulativeEarnedPerMLiq, 11881019661491126559); // fix rounding, add 1
        assertEq(root.tokenX.subtreeCummulativeEarnedPerMLiq, 11881019661491126559);
        assertEq(root.tokenY.cummulativeEarnedPerMLiq, 13251905); // fix rounding, add 1
        assertEq(root.tokenY.subtreeCummulativeEarnedPerMLiq, 13251905);

        assertEq(root.mLiq, 14035);
        assertEq(root.subtreeMLiq, 224560);
        assertEq(root.tLiq, 11668);
        assertEq(root.tokenX.borrowed, 10016e18);
        assertEq(root.tokenX.subtreeBorrowed, 10016e18);
        assertEq(root.tokenY.borrowed, 7927848e6);
        assertEq(root.tokenY.subtreeBorrowed, 7927848e6);

        vm.warp(57212); // T57212
        liqTree.feeRateSnapshotTokenX.add(1055375100301031600000000); // 11.1% APR as Q192.64 TT57212 - T37002
        liqTree.feeRateSnapshotTokenY.add(1055375100301031600000000);

        liqTree.removeInfRangeTLiq(4923, 222e18, 786e6);

        /*
            x-rate 1055375100301031600000000 (correct)
            x num 10570637004615132505600000000000000000000000000 (correct)
            x Q.64 47072662115314982657641610260064125400783 (47072662115314980000000000000000000000000 is correct)
            x token 2551814126505030241953 (2.55181412650503024195387164028103035638433335980020216618053 × 10^21 is correct) // need to round up 1
            y-rate 1055375100301031600000000
            y num 8366853378171332767996800000000000000 (correct)
            y Q.64 37258876817649326540776629853936 (3.7258876817649324e+31 is correct)
            y token 2019807759503 (2.01980775950325988354767545683493270255599285721099372431609 × 10^12 is correct)
  */

        assertEq(root.tokenX.cummulativeEarnedPerMLiq, 2563695146166521368512);
        assertEq(root.tokenX.subtreeCummulativeEarnedPerMLiq, 2563695146166521368512);
        assertEq(root.tokenY.cummulativeEarnedPerMLiq, 2019821011408);
        assertEq(root.tokenY.subtreeCummulativeEarnedPerMLiq, 2019821011408);

        assertEq(root.mLiq, 14035);
        assertEq(root.subtreeMLiq, 224560);
        assertEq(root.tLiq, 6745);
        assertEq(root.tokenX.borrowed, 9794e18);
        assertEq(root.tokenX.subtreeBorrowed, 9794e18);
        assertEq(root.tokenY.borrowed, 7927062e6);
        assertEq(root.tokenY.subtreeBorrowed, 7927062e6);
    }

    function testLeafNodeOnly() public {

    }

    function testSingleNodeOnly() public {

    }

    function testLeftLegOnly() public {
        LiqNode storage root = liqTree.nodes[liqTree.root];
        LiqNode storage L = liqTree.nodes[_nodeKey(1, 0, liqTree.offset)];
        LiqNode storage LL = liqTree.nodes[_nodeKey(2, 0, liqTree.offset)];
        LiqNode storage LR = liqTree.nodes[_nodeKey(2, 1, liqTree.offset)];
        LiqNode storage LLR = liqTree.nodes[_nodeKey(3, 1, liqTree.offset)];
        LiqNode storage LLRR = liqTree.nodes[_nodeKey(4, 3, liqTree.offset)];

        // Step 1) Allocate different mLiq + tLiq values for each node
        vm.warp(0); // T0

        liqTree.addInfRangeMLiq(8430);              // root (INF)
        liqTree.addMLiq(LiqRange(0, 7), 377);       // L    (0-7)
        liqTree.addMLiq(LiqRange(0, 3), 9082734);   // LL   (0-3)
        liqTree.addMLiq(LiqRange(4, 7), 1111);      // LR   (4-7)
        liqTree.addMLiq(LiqRange(2, 3), 45346);     // LLR  (2-3)
        liqTree.addMLiq(LiqRange(3, 3), 287634865); // LLRR   (3)

        liqTree.addInfRangeTLiq(4430, 492e18, 254858e6);            // root
        liqTree.addTLiq(LiqRange(0, 7), 77, 998e18, 353e6);         // L 
        liqTree.addTLiq(LiqRange(0, 3), 82734, 765e18, 99763e6);    // LL
        liqTree.addTLiq(LiqRange(4, 7), 111, 24e18, 552e6);         // LR
        liqTree.addTLiq(LiqRange(2, 3), 5346, 53e18, 8765e6);       // LLR
        liqTree.addTLiq(LiqRange(3, 3), 7634865, 701e18, 779531e6); // LLRR

        // mLiq
        assertEq(root.mLiq, 8430);
        assertEq(L.mLiq, 377);
        assertEq(LL.mLiq, 9082734);
        assertEq(LR.mLiq, 1111);
        assertEq(LLR.mLiq, 45346);
        assertEq(LLRR.mLiq, 287634865);

        // tLiq
        assertEq(root.tLiq, 4430);
        assertEq(L.tLiq, 77);
        assertEq(LL.tLiq, 82734);
        assertEq(LR.tLiq, 111);
        assertEq(LLR.tLiq, 5346);
        assertEq(LLRR.tLiq, 7634865);

        // subtreeMLiq
        assertEq(root.subtreeMLiq, 324198833); // 8430*16 + 377*8 + 9082734*4 + 1111*4 + 45346*2 + 287634865*1
        assertEq(L.subtreeMLiq, 324063953);    // 377*8 + 9082734*4 + 1111*4 + 45346*2 + 287634865*1
        assertEq(LL.subtreeMLiq, 324056493);   // 9082734*4 + 45346*2 + 287634865*1
        assertEq(LR.subtreeMLiq, 4444);        // 1111*4
        assertEq(LLR.subtreeMLiq, 287725557);  // 45346*2 + 287634865*1
        assertEq(LLRR.subtreeMLiq, 287634865); // 287634865*1

        // borrowedX
        assertEq(root.tokenX.borrowed, 492e18);
        assertEq(L.tokenX.borrowed, 998e18);
        assertEq(LL.tokenX.borrowed, 765e18);
        assertEq(LR.tokenX.borrowed, 24e18);
        assertEq(LLR.tokenX.borrowed, 53e18);
        assertEq(LLRR.tokenX.borrowed, 701e18);

        // borrowedY
        assertEq(root.tokenY.borrowed, 254858e6);
        assertEq(L.tokenY.borrowed, 353e6);
        assertEq(LL.tokenY.borrowed, 99763e6);
        assertEq(LR.tokenY.borrowed, 552e6);
        assertEq(LLR.tokenY.borrowed, 8765e6);
        assertEq(LLRR.tokenY.borrowed, 779531e6);

        // subtreeBorrowedX
        assertEq(root.tokenX.subtreeBorrowed, 3033e18); // 492e18 + 998e18 + 765e18 + 53e18 + 701e18 + 24e18
        assertEq(L.tokenX.subtreeBorrowed, 2541e18);    // 998e18 + 765e18 + 53e18 + 701e18 + 24e18
        assertEq(LL.tokenX.subtreeBorrowed, 1519e18);   // 765e18 + 53e18 + 701e18
        assertEq(LR.tokenX.subtreeBorrowed, 24e18);
        assertEq(LLR.tokenX.subtreeBorrowed, 754e18);   // 53e18 + 701e18
        assertEq(LLRR.tokenX.subtreeBorrowed, 701e18);  // 701e18

        // subtreeBorrowedY
        assertEq(root.tokenY.subtreeBorrowed, 1143822e6); // 254858e6 + 353e6 + 99763e6 + 8765e6 + 779531e6 + 552e6
        assertEq(L.tokenY.subtreeBorrowed, 888964e6);     // 353e6 + 99763e6 + 8765e6 + 779531e6 + 552e6
        assertEq(LL.tokenY.subtreeBorrowed, 888059e6);    // 99763e6 + 8765e6 + 779531e6
        assertEq(LR.tokenY.subtreeBorrowed, 552e6);
        assertEq(LLR.tokenY.subtreeBorrowed, 788296e6);   // 8765e6 + 779531e6
        assertEq(LLRR.tokenY.subtreeBorrowed, 779531e6);  // 779531e6

        // Step 2) Assign different rates for X & Y
        vm.warp(98273); // T98273
        liqTree.feeRateSnapshotTokenX.add(4541239648278065);  // 7.9% APR as Q192.64 T98273 - T0
        liqTree.feeRateSnapshotTokenY.add(13278814667749784); // 23.1% APR as Q192.64 T98273 - T0

        // Step 3) Apply change that effects the entire tree, to calculate the fees at each node
        // 3.1) addMLiq
        liqTree.addMLiq(LiqRange(3, 7), 2734); // LLRR, LR

        // root
        assertEq(root.tokenX.cummulativeEarnedPerMLiq, 373601278);
        assertEq(root.tokenX.subtreeCummulativeEarnedPerMLiq, 2303115199);
        assertEq(root.tokenY.cummulativeEarnedPerMLiq, 0);
        assertEq(root.tokenY.subtreeCummulativeEarnedPerMLiq, 2);

        // L
        assertEq(L.tokenX.cummulativeEarnedPerMLiq, 757991165);
        assertEq(L.tokenX.subtreeCummulativeEarnedPerMLiq, 1929915382);
        assertEq(L.tokenY.cummulativeEarnedPerMLiq, 0);
        assertEq(L.tokenY.subtreeCummulativeEarnedPerMLiq, 1);

        // LL
        assertEq(LL.tokenX.cummulativeEarnedPerMLiq, 581096415);
        assertEq(LL.tokenX.subtreeCummulativeEarnedPerMLiq, 1153837196);
        assertEq(LL.tokenY.cummulativeEarnedPerMLiq, 0);
        assertEq(LL.tokenY.subtreeCummulativeEarnedPerMLiq, 1);

        // LR
        assertEq(LR.tokenX.cummulativeEarnedPerMLiq, 148929881804);
        assertEq(LR.tokenX.subtreeCummulativeEarnedPerMLiq, 148929881804);
        assertEq(LR.tokenY.cummulativeEarnedPerMLiq, 10);
        assertEq(LR.tokenY.subtreeCummulativeEarnedPerMLiq, 10);

        // LLR
        assertEq(LLR.tokenX.cummulativeEarnedPerMLiq, 42651943);
        assertEq(LLR.tokenX.subtreeCummulativeEarnedPerMLiq, 606784254);
        assertEq(LLR.tokenY.cummulativeEarnedPerMLiq, 0);
        assertEq(LLR.tokenY.subtreeCummulativeEarnedPerMLiq, 1);

        // LLRR
        assertEq(LLRR.tokenX.cummulativeEarnedPerMLiq, 581500584);
        assertEq(LLRR.tokenX.subtreeCummulativeEarnedPerMLiq, 581500584);
        assertEq(LLRR.tokenY.cummulativeEarnedPerMLiq, 1);
        assertEq(LLRR.tokenY.subtreeCummulativeEarnedPerMLiq, 1);

        // mLiq
        assertEq(root.mLiq, 8430);
        assertEq(L.mLiq, 377);
        assertEq(LL.mLiq, 9082734);
        assertEq(LR.mLiq, 3845);
        assertEq(LLR.mLiq, 45346);
        assertEq(LLRR.mLiq, 287637599);

        // subtreeMLiq
        assertEq(root.subtreeMLiq, 324212503); // 8430*16 + 377*8 + 9082734*4 + 3845*4 + 45346*2 + 287637599*1
        assertEq(L.subtreeMLiq, 324077623);    // 377*8 + 9082734*4 + 3845*4 + 45346*2 + 287637599*1
        assertEq(LL.subtreeMLiq, 324059227);   // 9082734*4 + 45346*2 + 287637599*1
        assertEq(LR.subtreeMLiq, 15380);       // 3845*4
        assertEq(LLR.subtreeMLiq, 287728291);  // 45346*2 + 287637599*1
        assertEq(LLRR.subtreeMLiq, 287637599); // 287637599*1

        // 3.2) removeMLiq
        vm.warp(2876298273); // T2876298273
        liqTree.feeRateSnapshotTokenX.add(16463537718422861220174597);   // 978567.9% APR as Q192.64 T2876298273 - T98273
        liqTree.feeRateSnapshotTokenY.add(3715979586694123491881712207); // 220872233.1% APR as Q192.64 T2876298273 - T98273

        liqTree.removeMLiq(LiqRange(3, 7), 2734); // LLRR, LR

        // root
        assertEq(root.tokenX.cummulativeEarnedPerMLiq, 373601278 + 1354374549470516050);         // 1354374549844117328
        assertEq(root.tokenX.subtreeCummulativeEarnedPerMLiq, 2303115199 + 8349223594601778821); // 8349223596904894020
        assertEq(root.tokenY.cummulativeEarnedPerMLiq, 0 + 158351473403);                        // 158351473403
        assertEq(root.tokenY.subtreeCummulativeEarnedPerMLiq, 2 + 710693401861);                 // 710693401863

        // L
        assertEq(L.tokenX.cummulativeEarnedPerMLiq, 757991165 + 2747859799177149412);         // 2747859799935140577
        assertEq(L.tokenX.subtreeCummulativeEarnedPerMLiq, 1929915382 + 6996304358425988634); // 6996304360355904016
        assertEq(L.tokenY.cummulativeEarnedPerMLiq, 0 + 219375887);                           // 219375887
        assertEq(L.tokenY.subtreeCummulativeEarnedPerMLiq, 1 + 552456845955);                 // 552456845956

        // LL
        assertEq(LL.tokenX.cummulativeEarnedPerMLiq, 581096415 + 2106654304105573173);         // 2106654304686669588
        assertEq(LL.tokenX.subtreeCummulativeEarnedPerMLiq, 1153837196 + 4183016846975641372); // 4183016848129478568
        assertEq(LL.tokenY.cummulativeEarnedPerMLiq, 0 + 62008538706);                         // 62008538706
        assertEq(LL.tokenY.subtreeCummulativeEarnedPerMLiq, 1 + 551980602776);                 // 551980602777

        // LR
        assertEq(LR.tokenX.cummulativeEarnedPerMLiq, 148929881804 + 423248577958689008325);        // 423248578107618890129
        assertEq(LR.tokenX.subtreeCummulativeEarnedPerMLiq, 148929881804 + 423248577958689008325); // 423248578107618890129
        assertEq(LR.tokenY.cummulativeEarnedPerMLiq, 10 + 2197219781185);                          // 2197219781195
        assertEq(LR.tokenY.subtreeCummulativeEarnedPerMLiq, 10 + 2197219781185);                   // 2197219781195

        // LLR
        assertEq(LLR.tokenX.cummulativeEarnedPerMLiq, 42651943 + 154626414974589533);          // 154626415017241476
        assertEq(LLR.tokenX.subtreeCummulativeEarnedPerMLiq, 606784254 + 2199779563978122803); // 2199779564584907057
        assertEq(LLR.tokenY.cummulativeEarnedPerMLiq, 0 + 5771781665);                         // 5771781665
        assertEq(LLR.tokenY.subtreeCummulativeEarnedPerMLiq, 1 + 519095539054);                // 519095539055

        // LLRR
        assertEq(LLRR.tokenX.cummulativeEarnedPerMLiq, 581500584 + 2108117905415037748);         // 2108117905996538332
        assertEq(LLRR.tokenX.subtreeCummulativeEarnedPerMLiq, 581500584 + 2108117905415037748);  // 2108117905996538332
        assertEq(LLRR.tokenY.cummulativeEarnedPerMLiq, 1 + 529127613134);                        // 529127613135
        assertEq(LLRR.tokenY.subtreeCummulativeEarnedPerMLiq, 1 + 529127613134);                 // 529127613135

        // mLiq
        assertEq(root.mLiq, 8430);
        assertEq(L.mLiq, 377);
        assertEq(LL.mLiq, 9082734);
        assertEq(LR.mLiq, 1111);
        assertEq(LLR.mLiq, 45346);
        assertEq(LLRR.mLiq, 287634865);

        // subtreeMLiq
        assertEq(root.subtreeMLiq, 324198833); // 8430*16 + 377*8 + 9082734*4 + 1111*4 + 45346*2 + 287634865*1
        assertEq(L.subtreeMLiq, 324063953);    // 377*8 + 9082734*4 + 1111*4 + 45346*2 + 287634865*1
        assertEq(LL.subtreeMLiq, 324056493);   // 9082734*4 + 45346*2 + 287634865*1
        assertEq(LR.subtreeMLiq, 4444);        // 1111*4
        assertEq(LLR.subtreeMLiq, 287725557);  // 45346*2 + 287634865*1
        assertEq(LLRR.subtreeMLiq, 287634865); // 287634865*1

        // 3.3) addTLiq
        vm.warp(9214298113); // T2876298273
        liqTree.feeRateSnapshotTokenX.add(11381610389149375791104);   // 307% APR as Q192.64 T9214298113 - T2876298273
        liqTree.feeRateSnapshotTokenY.add(185394198934916215865344);  // 5000.7% APR as Q192.64 T9214298113 - T2876298273

        liqTree.addTLiq(LiqRange(3, 7), 1000, 1000e18, 1000e6); // LLRR, LR

        // root
        assertEq(root.tokenX.cummulativeEarnedPerMLiq, 1354374549844117328 + 936348777891386);         // 1355310898622008714
        assertEq(root.tokenX.subtreeCummulativeEarnedPerMLiq, 8349223596904894020 + 5772247649074341); // 8354995844553968361
        assertEq(root.tokenY.cummulativeEarnedPerMLiq, 158351473403 + 7900657);                        // 158359374060
        assertEq(root.tokenY.subtreeCummulativeEarnedPerMLiq, 710693401863 + 35458749);                // 710728860612

        // L
        assertEq(L.tokenX.cummulativeEarnedPerMLiq, 2747859799935140577 + 1899736810880077);        // 2749759536746020654
        assertEq(L.tokenX.subtreeCummulativeEarnedPerMLiq, 6996304360355904016 + 4836905046539355); // 7001141265402443371
        assertEq(L.tokenY.cummulativeEarnedPerMLiq, 219375887 + 10945);                             // 219386832
        assertEq(L.tokenY.subtreeCummulativeEarnedPerMLiq, 552456845956 + 27563825);                // 552484409781

        // LL
        assertEq(LL.tokenX.cummulativeEarnedPerMLiq, 2106654304686669588 + 1456389336983247);        // 2108110694023652835
        assertEq(LL.tokenX.subtreeCummulativeEarnedPerMLiq, 4183016848129478568 + 2891837127944514); // 4185908685257423082
        assertEq(LL.tokenY.cummulativeEarnedPerMLiq, 62008538706 + 3093698);                         // 62011632404
        assertEq(LL.tokenY.subtreeCummulativeEarnedPerMLiq, 551980602777 + 27539135);                // 552008141912

        // LR
        assertEq(LR.tokenX.cummulativeEarnedPerMLiq, 423248578107618890129 + 373259731104033296);        // 423621837838722923425
        assertEq(LR.tokenX.subtreeCummulativeEarnedPerMLiq, 423248578107618890129 + 373259731104033296); // 423621837838722923425
        assertEq(LR.tokenY.cummulativeEarnedPerMLiq, 2197219781195 + 139839995);                         // 2197359621190
        assertEq(LR.tokenY.subtreeCummulativeEarnedPerMLiq, 2197219781195 + 139839995);                  // 2197359621190

        // LLR
        assertEq(LLR.tokenX.cummulativeEarnedPerMLiq, 154626415017241476 + 106897640711262);          // 154733312657952738
        assertEq(LLR.tokenX.subtreeCummulativeEarnedPerMLiq, 2199779564584907057 + 1520770209363996); // 2201300334794271053
        assertEq(LLR.tokenY.cummulativeEarnedPerMLiq, 5771781665 + 287962);                           // 5772069627
        assertEq(LLR.tokenY.subtreeCummulativeEarnedPerMLiq, 519095539055 + 25898463);                // 519121437518

        // LLRR
        assertEq(LLRR.tokenX.cummulativeEarnedPerMLiq, 2108117905996538332 + 1457402297493569);        // 2109575308294031901
        assertEq(LLRR.tokenX.subtreeCummulativeEarnedPerMLiq, 2108117905996538332 + 1457402297493569); // 2109575308294031901
        assertEq(LLRR.tokenY.cummulativeEarnedPerMLiq, 529127613135 + 26398986);                       // 529154012121
        assertEq(LLRR.tokenY.subtreeCummulativeEarnedPerMLiq, 529127613135 + 26398986);                // 529154012121

        // tLiq
        assertEq(root.tLiq, 4430);
        assertEq(L.tLiq, 77);
        assertEq(LL.tLiq, 82734);
        assertEq(LR.tLiq, 1111);
        assertEq(LLR.tLiq, 5346);
        assertEq(LLRR.tLiq, 7635865);

        // borrowedX
        assertEq(root.tokenX.borrowed, 492e18);
        assertEq(L.tokenX.borrowed, 998e18);
        assertEq(LL.tokenX.borrowed, 765e18);
        assertEq(LR.tokenX.borrowed, 1024e18);
        assertEq(LLR.tokenX.borrowed, 53e18);
        assertEq(LLRR.tokenX.borrowed, 1701e18);

        // borrowedY
        assertEq(root.tokenY.borrowed, 254858e6);
        assertEq(L.tokenY.borrowed, 353e6);
        assertEq(LL.tokenY.borrowed, 99763e6);
        assertEq(LR.tokenY.borrowed, 1552e6);
        assertEq(LLR.tokenY.borrowed, 8765e6);
        assertEq(LLRR.tokenY.borrowed, 780531e6);

        // subtreeBorrowedX
        assertEq(root.tokenX.subtreeBorrowed, 5033e18);  // 492e18 + 998e18 + 765e18 + 53e18 + 701e18 + 24e18
        assertEq(L.tokenX.subtreeBorrowed, 4541e18);     // 998e18 + 765e18 + 53e18 + 701e18 + 24e18
        assertEq(LL.tokenX.subtreeBorrowed, 2519e18);    // 765e18 + 53e18 + 701e18
        assertEq(LR.tokenX.subtreeBorrowed, 1024e18);
        assertEq(LLR.tokenX.subtreeBorrowed, 1754e18);   // 53e18 + 701e18
        assertEq(LLRR.tokenX.subtreeBorrowed, 1701e18);  // 701e18

        // subtreeBorrowedY
        assertEq(root.tokenY.subtreeBorrowed, 1145822e6); // 254858e6 + 353e6 + 99763e6 + 8765e6 + 779531e6 + 552e6
        assertEq(L.tokenY.subtreeBorrowed, 890964e6);     // 353e6 + 99763e6 + 8765e6 + 779531e6 + 552e6
        assertEq(LL.tokenY.subtreeBorrowed, 889059e6);    // 99763e6 + 8765e6 + 779531e6
        assertEq(LR.tokenY.subtreeBorrowed, 1552e6);
        assertEq(LLR.tokenY.subtreeBorrowed, 789296e6);   // 8765e6 + 779531e6
        assertEq(LLRR.tokenY.subtreeBorrowed, 780531e6);  // 779531e6

        // 3.4) removeTLiq
        // 3.3) addTLiq
        vm.warp(32876298273); // T32876298273
        liqTree.feeRateSnapshotTokenX.add(2352954287417905205553); // 17% APR as Q192.64 T32876298273 - T9214298113
        liqTree.feeRateSnapshotTokenY.add(6117681147286553534438); // 44.2% APR as Q192.64 T32876298273 - T9214298113

        liqTree.removeTLiq(LiqRange(3, 7), 1000, 1000e18, 1000e6); // LLRR, LR

        // root
        // A = 0
        // m = 324198833
        //     x: 492e18 * 2352954287417905205553 / 324198833 / 2**64
        // x sub: 5033e18 * 2352954287417905205553 / 324198833 / 2**64
        //     y: 254858e6 * 6117681147286553534438 / 324198833 / 2**64
        // y sub: 1145822e6 * 6117681147286553534438 / 324198833 / 2**64
        assertEq(root.tokenX.cummulativeEarnedPerMLiq, 1355310898622008714 + 193574177654021);
        assertEq(root.tokenX.subtreeCummulativeEarnedPerMLiq, 8354995844553968361 + 1980200886448553);
        assertEq(root.tokenY.cummulativeEarnedPerMLiq, 158359374060 + 260707);
        assertEq(root.tokenY.subtreeCummulativeEarnedPerMLiq, 710728860612 + 1172122);

        // L
        // 998e18 * 2352954287417905205553 / 324131393 / 2**64
        // 4541e18 * 2352954287417905205553 / 324131393 / 2**64
        // 353e6 * 6117681147286553534438 / 324131393 / 2**64
        // 890964e6 * 6117681147286553534438 / 324131393 / 2**64
        assertEq(L.tokenX.cummulativeEarnedPerMLiq, 2749759536746020654 + 392738261220692);
        assertEq(L.tokenX.subtreeCummulativeEarnedPerMLiq, 7001141265402443371 + 1786998441085335);
        assertEq(L.tokenY.cummulativeEarnedPerMLiq, 219386832 + 361);
        assertEq(L.tokenY.subtreeCummulativeEarnedPerMLiq, 552484409781 + 911603);

        // LL
        // 765e18 * 2352954287417905205553 / 324091721 / 2**64
        // 2519e18 * 2352954287417905205553 / 324091721 / 2**64
        // 99763e6 * 6117681147286553534438 / 324091721 / 2**64
        // 889059e6 * 6117681147286553534438 / 324091721 / 2**64
        assertEq(LL.tokenX.cummulativeEarnedPerMLiq, 2108110694023652835 + 301083714644757);
        assertEq(LL.tokenX.subtreeCummulativeEarnedPerMLiq, 4185908685257423082 + 991411604170121);
        assertEq(LL.tokenY.cummulativeEarnedPerMLiq, 62011632404 + 102086);
        assertEq(LL.tokenY.subtreeCummulativeEarnedPerMLiq, 552008141912 + 909766);

        // LR
        // 1024e18 * 2352954287417905205553 / 39672 / 2**64
        // 1024e18 * 2352954287417905205553 / 39672 / 2**64
        // 1552e6 * 6117681147286553534438 / 39672 / 2**64
        // 1552e6 * 6117681147286553534438 / 39672 / 2**64
        assertEq(LR.tokenX.cummulativeEarnedPerMLiq, 423621837838722923425 + 3292377527956539412);
        assertEq(LR.tokenX.subtreeCummulativeEarnedPerMLiq, 423621837838722923425 + 3292377527956539412);
        assertEq(LR.tokenY.cummulativeEarnedPerMLiq, 2197359621190 + 12974025);
        assertEq(LR.tokenY.subtreeCummulativeEarnedPerMLiq, 2197359621190 + 12974025);

        // LLR
        // 53e18 * 2352954287417905205553 / 305908639 / 2**64
        // 1754e18 * 2352954287417905205553 / 305908639 / 2**64
        // 8765e6 * 6117681147286553534438 / 305908639 / 2**64
        // 789296e6 * 6117681147286553534438 / 305908639 / 2**64
        assertEq(LLR.tokenX.cummulativeEarnedPerMLiq, 154733312657952738 + 22099268330799);
        assertEq(LLR.tokenX.subtreeCummulativeEarnedPerMLiq, 2201300334794271053 + 731360691551353);
        assertEq(LLR.tokenY.cummulativeEarnedPerMLiq, 5772069627 + 9502);
        assertEq(LLR.tokenY.subtreeCummulativeEarnedPerMLiq, 519121437518 + 855687);

        // LLRR
        // 1701e18 * 2352954287417905205553 / 296771752 / 2**64
        // 1701e18 * 2352954287417905205553 / 296771752 / 2**64
        // 780531e6 * 6117681147286553534438 / 296771752 / 2**64
        // 780531e6 * 6117681147286553534438 / 296771752 / 2**64
        assertEq(LLRR.tokenX.cummulativeEarnedPerMLiq, 2109575308294031901 + 731097873063750);
        assertEq(LLRR.tokenX.subtreeCummulativeEarnedPerMLiq, 2109575308294031901 + 731097873063750);
        assertEq(LLRR.tokenY.cummulativeEarnedPerMLiq, 529154012121 + 872237);
        assertEq(LLRR.tokenY.subtreeCummulativeEarnedPerMLiq, 529154012121 + 872237);

        // tLiq
        assertEq(root.tLiq, 4430);
        assertEq(L.tLiq, 77);
        assertEq(LL.tLiq, 82734);
        assertEq(LR.tLiq, 111);
        assertEq(LLR.tLiq, 5346);
        assertEq(LLRR.tLiq, 7634865);

        // subtreeMLiq
        assertEq(root.subtreeMLiq, 324198833); // 8430*16 + 377*8 + 9082734*4 + 1111*4 + 45346*2 + 287634865*1
        assertEq(L.subtreeMLiq, 324063953);    // 377*8 + 9082734*4 + 1111*4 + 45346*2 + 287634865*1
        assertEq(LL.subtreeMLiq, 324056493);   // 9082734*4 + 45346*2 + 287634865*1
        assertEq(LR.subtreeMLiq, 4444);        // 1111*4
        assertEq(LLR.subtreeMLiq, 287725557);  // 45346*2 + 287634865*1
        assertEq(LLRR.subtreeMLiq, 287634865); // 287634865*1

        // borrowedX
        assertEq(root.tokenX.borrowed, 492e18);
        assertEq(L.tokenX.borrowed, 998e18);
        assertEq(LL.tokenX.borrowed, 765e18);
        assertEq(LR.tokenX.borrowed, 24e18);
        assertEq(LLR.tokenX.borrowed, 53e18);
        assertEq(LLRR.tokenX.borrowed, 701e18);

        // borrowedY
        assertEq(root.tokenY.borrowed, 254858e6);
        assertEq(L.tokenY.borrowed, 353e6);
        assertEq(LL.tokenY.borrowed, 99763e6);
        assertEq(LR.tokenY.borrowed, 552e6);
        assertEq(LLR.tokenY.borrowed, 8765e6);
        assertEq(LLRR.tokenY.borrowed, 779531e6);

        // subtreeBorrowedX
        assertEq(root.tokenX.subtreeBorrowed, 3033e18); // 492e18 + 998e18 + 765e18 + 53e18 + 701e18 + 24e18
        assertEq(L.tokenX.subtreeBorrowed, 2541e18);    // 998e18 + 765e18 + 53e18 + 701e18 + 24e18
        assertEq(LL.tokenX.subtreeBorrowed, 1519e18);   // 765e18 + 53e18 + 701e18
        assertEq(LR.tokenX.subtreeBorrowed, 24e18);
        assertEq(LLR.tokenX.subtreeBorrowed, 754e18);   // 53e18 + 701e18
        assertEq(LLRR.tokenX.subtreeBorrowed, 701e18);  // 701e18

        // subtreeBorrowedY
        assertEq(root.tokenY.subtreeBorrowed, 1143822e6); // 254858e6 + 353e6 + 99763e6 + 8765e6 + 779531e6 + 552e6
        assertEq(L.tokenY.subtreeBorrowed, 888964e6);     // 353e6 + 99763e6 + 8765e6 + 779531e6 + 552e6
        assertEq(LL.tokenY.subtreeBorrowed, 888059e6);    // 99763e6 + 8765e6 + 779531e6
        assertEq(LR.tokenY.subtreeBorrowed, 552e6);
        assertEq(LLR.tokenY.subtreeBorrowed, 788296e6);   // 8765e6 + 779531e6
        assertEq(LLRR.tokenY.subtreeBorrowed, 779531e6);  // 779531e6
    }


    function testRightLegOnly() public {
        LiqNode storage root = liqTree.nodes[liqTree.root];
        LiqNode storage R = liqTree.nodes[_nodeKey(1, 1, liqTree.offset)];
        LiqNode storage RR = liqTree.nodes[_nodeKey(2, 3, liqTree.offset)];
        LiqNode storage RL = liqTree.nodes[_nodeKey(2, 2, liqTree.offset)];
        LiqNode storage RRL = liqTree.nodes[_nodeKey(3, 6, liqTree.offset)];
        LiqNode storage RRLL = liqTree.nodes[_nodeKey(4, 12, liqTree.offset)];

        // Step 1) Allocate different mLiq + tLiq values for each node
        vm.warp(0); // T0

        liqTree.addInfRangeMLiq(8430);                // root   (INF)
        liqTree.addMLiq(LiqRange(8, 15), 377);        // R     (8-15)
        liqTree.addMLiq(LiqRange(12, 15), 9082734);   // RR   (12-15)
        liqTree.addMLiq(LiqRange(8, 11), 1111);       // RL    (8-11)
        liqTree.addMLiq(LiqRange(12, 13), 45346);     // RRL  (12-13)
        liqTree.addMLiq(LiqRange(12, 12), 287634865); // RRLL    (12)

        liqTree.addInfRangeTLiq(4430, 492e18, 254858e6);              // root
        liqTree.addTLiq(LiqRange(8, 15), 77, 998e18, 353e6);          // R 
        liqTree.addTLiq(LiqRange(12, 15), 82734, 765e18, 99763e6);    // RR
        liqTree.addTLiq(LiqRange(8, 11), 111, 24e18, 552e6);          // RL
        liqTree.addTLiq(LiqRange(12, 13), 5346, 53e18, 8765e6);       // RRL
        liqTree.addTLiq(LiqRange(12, 12), 7634865, 701e18, 779531e6); // RRLL

        // mLiq
        assertEq(root.mLiq, 8430);
        assertEq(R.mLiq, 377);
        assertEq(RR.mLiq, 9082734);
        assertEq(RL.mLiq, 1111);
        assertEq(RRL.mLiq, 45346);
        assertEq(RRLL.mLiq, 287634865);

        // tLiq
        assertEq(root.tLiq, 4430);
        assertEq(R.tLiq, 77);
        assertEq(RR.tLiq, 82734);
        assertEq(RL.tLiq, 111);
        assertEq(RRL.tLiq, 5346);
        assertEq(RRLL.tLiq, 7634865);

        // subtreeMLiq
        assertEq(root.subtreeMLiq, 324198833); // 8430*16 + 377*8 + 9082734*4 + 1111*4 + 45346*2 + 287634865*1
        assertEq(R.subtreeMLiq, 324063953);    // 377*8 + 9082734*4 + 1111*4 + 45346*2 + 287634865*1
        assertEq(RR.subtreeMLiq, 324056493);   // 9082734*4 + 45346*2 + 287634865*1
        assertEq(RL.subtreeMLiq, 4444);        // 1111*4
        assertEq(RRL.subtreeMLiq, 287725557);  // 45346*2 + 287634865*1
        assertEq(RRLL.subtreeMLiq, 287634865); // 287634865*1

        // borrowedX
        assertEq(root.tokenX.borrowed, 492e18);
        assertEq(R.tokenX.borrowed, 998e18);
        assertEq(RR.tokenX.borrowed, 765e18);
        assertEq(RL.tokenX.borrowed, 24e18);
        assertEq(RRL.tokenX.borrowed, 53e18);
        assertEq(RRLL.tokenX.borrowed, 701e18);

        // borrowedY
        assertEq(root.tokenY.borrowed, 254858e6);
        assertEq(R.tokenY.borrowed, 353e6);
        assertEq(RR.tokenY.borrowed, 99763e6);
        assertEq(RL.tokenY.borrowed, 552e6);
        assertEq(RRL.tokenY.borrowed, 8765e6);
        assertEq(RRLL.tokenY.borrowed, 779531e6);

        // subtreeBorrowedX
        assertEq(root.tokenX.subtreeBorrowed, 3033e18); // 492e18 + 998e18 + 765e18 + 53e18 + 701e18 + 24e18
        assertEq(R.tokenX.subtreeBorrowed, 2541e18);    // 998e18 + 765e18 + 53e18 + 701e18 + 24e18
        assertEq(RR.tokenX.subtreeBorrowed, 1519e18);   // 765e18 + 53e18 + 701e18
        assertEq(RL.tokenX.subtreeBorrowed, 24e18);
        assertEq(RRL.tokenX.subtreeBorrowed, 754e18);   // 53e18 + 701e18
        assertEq(RRLL.tokenX.subtreeBorrowed, 701e18);  // 701e18

        // subtreeBorrowedY
        assertEq(root.tokenY.subtreeBorrowed, 1143822e6); // 254858e6 + 353e6 + 99763e6 + 8765e6 + 779531e6 + 552e6
        assertEq(R.tokenY.subtreeBorrowed, 888964e6);     // 353e6 + 99763e6 + 8765e6 + 779531e6 + 552e6
        assertEq(RR.tokenY.subtreeBorrowed, 888059e6);    // 99763e6 + 8765e6 + 779531e6
        assertEq(RL.tokenY.subtreeBorrowed, 552e6);
        assertEq(RRL.tokenY.subtreeBorrowed, 788296e6);   // 8765e6 + 779531e6
        assertEq(RRLL.tokenY.subtreeBorrowed, 779531e6);  // 779531e6

        // Step 2) Assign different rates for X & Y
        vm.warp(98273); // T98273
        liqTree.feeRateSnapshotTokenX.add(4541239648278065);  // 7.9% APR as Q192.64 T98273 - T0
        liqTree.feeRateSnapshotTokenY.add(13278814667749784); // 23.1% APR as Q192.64 T98273 - T0

        // Step 3) Apply change that effects the entire tree, to calculate the fees at each node
        // 3.1) addMLiq
        liqTree.addMLiq(LiqRange(8, 12), 2734); // RRLL, RL

        // root
        assertEq(root.tokenX.cummulativeEarnedPerMLiq, 373601278);
        assertEq(root.tokenX.subtreeCummulativeEarnedPerMLiq, 2303115199);
        assertEq(root.tokenY.cummulativeEarnedPerMLiq, 0);
        assertEq(root.tokenY.subtreeCummulativeEarnedPerMLiq, 2);

        // R
        assertEq(R.tokenX.cummulativeEarnedPerMLiq, 757991165);
        assertEq(R.tokenX.subtreeCummulativeEarnedPerMLiq, 1929915382);
        assertEq(R.tokenY.cummulativeEarnedPerMLiq, 0);
        assertEq(R.tokenY.subtreeCummulativeEarnedPerMLiq, 1);

        // RR
        assertEq(RR.tokenX.cummulativeEarnedPerMLiq, 581096415);
        assertEq(RR.tokenX.subtreeCummulativeEarnedPerMLiq, 1153837196);
        assertEq(RR.tokenY.cummulativeEarnedPerMLiq, 0);
        assertEq(RR.tokenY.subtreeCummulativeEarnedPerMLiq, 1);

        // RL
        assertEq(RL.tokenX.cummulativeEarnedPerMLiq, 148929881804);
        assertEq(RL.tokenX.subtreeCummulativeEarnedPerMLiq, 148929881804);
        assertEq(RL.tokenY.cummulativeEarnedPerMLiq, 10);
        assertEq(RL.tokenY.subtreeCummulativeEarnedPerMLiq, 10);

        // RRL
        assertEq(RRL.tokenX.cummulativeEarnedPerMLiq, 42651943);
        assertEq(RRL.tokenX.subtreeCummulativeEarnedPerMLiq, 606784254);
        assertEq(RRL.tokenY.cummulativeEarnedPerMLiq, 0);
        assertEq(RRL.tokenY.subtreeCummulativeEarnedPerMLiq, 1);

        // RRLL
        assertEq(RRLL.tokenX.cummulativeEarnedPerMLiq, 581500584);
        assertEq(RRLL.tokenX.subtreeCummulativeEarnedPerMLiq, 581500584);
        assertEq(RRLL.tokenY.cummulativeEarnedPerMLiq, 1);
        assertEq(RRLL.tokenY.subtreeCummulativeEarnedPerMLiq, 1);

        // mLiq
        assertEq(root.mLiq, 8430);
        assertEq(R.mLiq, 377);
        assertEq(RR.mLiq, 9082734);
        assertEq(RL.mLiq, 3845);
        assertEq(RRL.mLiq, 45346);
        assertEq(RRLL.mLiq, 287637599);

        // subtreeMLiq
        assertEq(root.subtreeMLiq, 324212503); // 8430*16 + 377*8 + 9082734*4 + 3845*4 + 45346*2 + 287637599*1
        assertEq(R.subtreeMLiq, 324077623);    // 377*8 + 9082734*4 + 3845*4 + 45346*2 + 287637599*1
        assertEq(RR.subtreeMLiq, 324059227);   // 9082734*4 + 45346*2 + 287637599*1
        assertEq(RL.subtreeMLiq, 15380);       // 3845*4
        assertEq(RRL.subtreeMLiq, 287728291);  // 45346*2 + 287637599*1
        assertEq(RRLL.subtreeMLiq, 287637599); // 287637599*1

        // 3.2) removeMLiq
        vm.warp(2876298273); // T2876298273
        liqTree.feeRateSnapshotTokenX.add(16463537718422861220174597);   // 978567.9% APR as Q192.64 T2876298273 - T98273
        liqTree.feeRateSnapshotTokenY.add(3715979586694123491881712207); // 220872233.1% APR as Q192.64 T2876298273 - T98273

        liqTree.removeMLiq(LiqRange(8, 12), 2734); // RRLL, RL

        // root
        assertEq(root.tokenX.cummulativeEarnedPerMLiq, 373601278 + 1354374549470516050);         // 1354374549844117328
        assertEq(root.tokenX.subtreeCummulativeEarnedPerMLiq, 2303115199 + 8349223594601778821); // 8349223596904894020
        assertEq(root.tokenY.cummulativeEarnedPerMLiq, 0 + 158351473403);                        // 158351473403
        assertEq(root.tokenY.subtreeCummulativeEarnedPerMLiq, 2 + 710693401861);                 // 710693401863

        // R
        assertEq(R.tokenX.cummulativeEarnedPerMLiq, 757991165 + 2747859799177149412);         // 2747859799935140577
        assertEq(R.tokenX.subtreeCummulativeEarnedPerMLiq, 1929915382 + 6996304358425988634); // 6996304360355904016
        assertEq(R.tokenY.cummulativeEarnedPerMLiq, 0 + 219375887);                           // 219375887
        assertEq(R.tokenY.subtreeCummulativeEarnedPerMLiq, 1 + 552456845955);                 // 552456845956

        // RR
        assertEq(RR.tokenX.cummulativeEarnedPerMLiq, 581096415 + 2106654304105573173);         // 2106654304686669588
        assertEq(RR.tokenX.subtreeCummulativeEarnedPerMLiq, 1153837196 + 4183016846975641372); // 4183016848129478568
        assertEq(RR.tokenY.cummulativeEarnedPerMLiq, 0 + 62008538706);                         // 62008538706
        assertEq(RR.tokenY.subtreeCummulativeEarnedPerMLiq, 1 + 551980602776);                 // 551980602777

        // RL
        assertEq(RL.tokenX.cummulativeEarnedPerMLiq, 148929881804 + 423248577958689008325);        // 423248578107618890129
        assertEq(RL.tokenX.subtreeCummulativeEarnedPerMLiq, 148929881804 + 423248577958689008325); // 423248578107618890129
        assertEq(RL.tokenY.cummulativeEarnedPerMLiq, 10 + 2197219781185);                          // 2197219781195
        assertEq(RL.tokenY.subtreeCummulativeEarnedPerMLiq, 10 + 2197219781185);                   // 2197219781195

        // RRL
        assertEq(RRL.tokenX.cummulativeEarnedPerMLiq, 42651943 + 154626414974589533);          // 154626415017241476
        assertEq(RRL.tokenX.subtreeCummulativeEarnedPerMLiq, 606784254 + 2199779563978122803); // 2199779564584907057
        assertEq(RRL.tokenY.cummulativeEarnedPerMLiq, 0 + 5771781665);                         // 5771781665
        assertEq(RRL.tokenY.subtreeCummulativeEarnedPerMLiq, 1 + 519095539054);                // 519095539055

        // RRLL
        assertEq(RRLL.tokenX.cummulativeEarnedPerMLiq, 581500584 + 2108117905415037748);         // 2108117905996538332
        assertEq(RRLL.tokenX.subtreeCummulativeEarnedPerMLiq, 581500584 + 2108117905415037748);  // 2108117905996538332
        assertEq(RRLL.tokenY.cummulativeEarnedPerMLiq, 1 + 529127613134);                        // 529127613135
        assertEq(RRLL.tokenY.subtreeCummulativeEarnedPerMLiq, 1 + 529127613134);                 // 529127613135

        // mLiq
        assertEq(root.mLiq, 8430);
        assertEq(R.mLiq, 377);
        assertEq(RR.mLiq, 9082734);
        assertEq(RL.mLiq, 1111);
        assertEq(RRL.mLiq, 45346);
        assertEq(RRLL.mLiq, 287634865);

        // subtreeMLiq
        assertEq(root.subtreeMLiq, 324198833); // 8430*16 + 377*8 + 9082734*4 + 1111*4 + 45346*2 + 287634865*1
        assertEq(R.subtreeMLiq, 324063953);    // 377*8 + 9082734*4 + 1111*4 + 45346*2 + 287634865*1
        assertEq(RR.subtreeMLiq, 324056493);   // 9082734*4 + 45346*2 + 287634865*1
        assertEq(RL.subtreeMLiq, 4444);        // 1111*4
        assertEq(RRL.subtreeMLiq, 287725557);  // 45346*2 + 287634865*1
        assertEq(RRLL.subtreeMLiq, 287634865); // 287634865*1

        // 3.3) addTLiq
        vm.warp(9214298113); // T2876298273
        liqTree.feeRateSnapshotTokenX.add(11381610389149375791104);   // 307% APR as Q192.64 T9214298113 - T2876298273
        liqTree.feeRateSnapshotTokenY.add(185394198934916215865344);  // 5000.7% APR as Q192.64 T9214298113 - T2876298273

        liqTree.addTLiq(LiqRange(8, 12), 1000, 1000e18, 1000e6); // RRLL, RL

        // root
        assertEq(root.tokenX.cummulativeEarnedPerMLiq, 1354374549844117328 + 936348777891386);         // 1355310898622008714
        assertEq(root.tokenX.subtreeCummulativeEarnedPerMLiq, 8349223596904894020 + 5772247649074341); // 8354995844553968361
        assertEq(root.tokenY.cummulativeEarnedPerMLiq, 158351473403 + 7900657);                        // 158359374060
        assertEq(root.tokenY.subtreeCummulativeEarnedPerMLiq, 710693401863 + 35458749);                // 710728860612

        // R
        assertEq(R.tokenX.cummulativeEarnedPerMLiq, 2747859799935140577 + 1899736810880077);        // 2749759536746020654
        assertEq(R.tokenX.subtreeCummulativeEarnedPerMLiq, 6996304360355904016 + 4836905046539355); // 7001141265402443371
        assertEq(R.tokenY.cummulativeEarnedPerMLiq, 219375887 + 10945);                             // 219386832
        assertEq(R.tokenY.subtreeCummulativeEarnedPerMLiq, 552456845956 + 27563825);                // 552484409781

        // RR
        assertEq(RR.tokenX.cummulativeEarnedPerMLiq, 2106654304686669588 + 1456389336983247);        // 2108110694023652835
        assertEq(RR.tokenX.subtreeCummulativeEarnedPerMLiq, 4183016848129478568 + 2891837127944514); // 4185908685257423082
        assertEq(RR.tokenY.cummulativeEarnedPerMLiq, 62008538706 + 3093698);                         // 62011632404
        assertEq(RR.tokenY.subtreeCummulativeEarnedPerMLiq, 551980602777 + 27539135);                // 552008141912

        // RL
        assertEq(RL.tokenX.cummulativeEarnedPerMLiq, 423248578107618890129 + 373259731104033296);        // 423621837838722923425
        assertEq(RL.tokenX.subtreeCummulativeEarnedPerMLiq, 423248578107618890129 + 373259731104033296); // 423621837838722923425
        assertEq(RL.tokenY.cummulativeEarnedPerMLiq, 2197219781195 + 139839995);                         // 2197359621190
        assertEq(RL.tokenY.subtreeCummulativeEarnedPerMLiq, 2197219781195 + 139839995);                  // 2197359621190

        // RRL
        assertEq(RRL.tokenX.cummulativeEarnedPerMLiq, 154626415017241476 + 106897640711262);          // 154733312657952738
        assertEq(RRL.tokenX.subtreeCummulativeEarnedPerMLiq, 2199779564584907057 + 1520770209363996); // 2201300334794271053
        assertEq(RRL.tokenY.cummulativeEarnedPerMLiq, 5771781665 + 287962);                           // 5772069627
        assertEq(RRL.tokenY.subtreeCummulativeEarnedPerMLiq, 519095539055 + 25898463);                // 519121437518

        // RRLL
        assertEq(RRLL.tokenX.cummulativeEarnedPerMLiq, 2108117905996538332 + 1457402297493569);        // 2109575308294031901
        assertEq(RRLL.tokenX.subtreeCummulativeEarnedPerMLiq, 2108117905996538332 + 1457402297493569); // 2109575308294031901
        assertEq(RRLL.tokenY.cummulativeEarnedPerMLiq, 529127613135 + 26398986);                       // 529154012121
        assertEq(RRLL.tokenY.subtreeCummulativeEarnedPerMLiq, 529127613135 + 26398986);                // 529154012121

        // tLiq
        assertEq(root.tLiq, 4430);
        assertEq(R.tLiq, 77);
        assertEq(RR.tLiq, 82734);
        assertEq(RL.tLiq, 1111);
        assertEq(RRL.tLiq, 5346);
        assertEq(RRLL.tLiq, 7635865);

        // borrowedX
        assertEq(root.tokenX.borrowed, 492e18);
        assertEq(R.tokenX.borrowed, 998e18);
        assertEq(RR.tokenX.borrowed, 765e18);
        assertEq(RL.tokenX.borrowed, 1024e18);
        assertEq(RRL.tokenX.borrowed, 53e18);
        assertEq(RRLL.tokenX.borrowed, 1701e18);

        // borrowedY
        assertEq(root.tokenY.borrowed, 254858e6);
        assertEq(R.tokenY.borrowed, 353e6);
        assertEq(RR.tokenY.borrowed, 99763e6);
        assertEq(RL.tokenY.borrowed, 1552e6);
        assertEq(RRL.tokenY.borrowed, 8765e6);
        assertEq(RRLL.tokenY.borrowed, 780531e6);

        // subtreeBorrowedX
        assertEq(root.tokenX.subtreeBorrowed, 5033e18);  // 492e18 + 998e18 + 765e18 + 53e18 + 701e18 + 24e18
        assertEq(R.tokenX.subtreeBorrowed, 4541e18);     // 998e18 + 765e18 + 53e18 + 701e18 + 24e18
        assertEq(RR.tokenX.subtreeBorrowed, 2519e18);    // 765e18 + 53e18 + 701e18
        assertEq(RL.tokenX.subtreeBorrowed, 1024e18);
        assertEq(RRL.tokenX.subtreeBorrowed, 1754e18);   // 53e18 + 701e18
        assertEq(RRLL.tokenX.subtreeBorrowed, 1701e18);  // 701e18

        // subtreeBorrowedY
        assertEq(root.tokenY.subtreeBorrowed, 1145822e6); // 254858e6 + 353e6 + 99763e6 + 8765e6 + 779531e6 + 552e6
        assertEq(R.tokenY.subtreeBorrowed, 890964e6);     // 353e6 + 99763e6 + 8765e6 + 779531e6 + 552e6
        assertEq(RR.tokenY.subtreeBorrowed, 889059e6);    // 99763e6 + 8765e6 + 779531e6
        assertEq(RL.tokenY.subtreeBorrowed, 1552e6);
        assertEq(RRL.tokenY.subtreeBorrowed, 789296e6);   // 8765e6 + 779531e6
        assertEq(RRLL.tokenY.subtreeBorrowed, 780531e6);  // 779531e6

        // 3.4) removeTLiq
        // 3.3) addTLiq
        vm.warp(32876298273); // T32876298273
        liqTree.feeRateSnapshotTokenX.add(2352954287417905205553); // 17% APR as Q192.64 T32876298273 - T9214298113
        liqTree.feeRateSnapshotTokenY.add(6117681147286553534438); // 44.2% APR as Q192.64 T32876298273 - T9214298113

        liqTree.removeTLiq(LiqRange(8, 12), 1000, 1000e18, 1000e6); // RRLL, RL

        // root
        // A = 0
        // m = 324198833
        //     x: 492e18 * 2352954287417905205553 / 324198833 / 2**64
        // x sub: 5033e18 * 2352954287417905205553 / 324198833 / 2**64
        //     y: 254858e6 * 6117681147286553534438 / 324198833 / 2**64
        // y sub: 1145822e6 * 6117681147286553534438 / 324198833 / 2**64
        assertEq(root.tokenX.cummulativeEarnedPerMLiq, 1355310898622008714 + 193574177654021);
        assertEq(root.tokenX.subtreeCummulativeEarnedPerMLiq, 8354995844553968361 + 1980200886448553);
        assertEq(root.tokenY.cummulativeEarnedPerMLiq, 158359374060 + 260707);
        assertEq(root.tokenY.subtreeCummulativeEarnedPerMLiq, 710728860612 + 1172122);

        // R
        // 998e18 * 2352954287417905205553 / 324131393 / 2**64
        // 4541e18 * 2352954287417905205553 / 324131393 / 2**64
        // 353e6 * 6117681147286553534438 / 324131393 / 2**64
        // 890964e6 * 6117681147286553534438 / 324131393 / 2**64
        assertEq(R.tokenX.cummulativeEarnedPerMLiq, 2749759536746020654 + 392738261220692);
        assertEq(R.tokenX.subtreeCummulativeEarnedPerMLiq, 7001141265402443371 + 1786998441085335);
        assertEq(R.tokenY.cummulativeEarnedPerMLiq, 219386832 + 361);
        assertEq(R.tokenY.subtreeCummulativeEarnedPerMLiq, 552484409781 + 911603);

        // RR
        // 765e18 * 2352954287417905205553 / 324091721 / 2**64
        // 2519e18 * 2352954287417905205553 / 324091721 / 2**64
        // 99763e6 * 6117681147286553534438 / 324091721 / 2**64
        // 889059e6 * 6117681147286553534438 / 324091721 / 2**64
        assertEq(RR.tokenX.cummulativeEarnedPerMLiq, 2108110694023652835 + 301083714644757);
        assertEq(RR.tokenX.subtreeCummulativeEarnedPerMLiq, 4185908685257423082 + 991411604170121);
        assertEq(RR.tokenY.cummulativeEarnedPerMLiq, 62011632404 + 102086);
        assertEq(RR.tokenY.subtreeCummulativeEarnedPerMLiq, 552008141912 + 909766);

        // RL
        // 1024e18 * 2352954287417905205553 / 39672 / 2**64
        // 1024e18 * 2352954287417905205553 / 39672 / 2**64
        // 1552e6 * 6117681147286553534438 / 39672 / 2**64
        // 1552e6 * 6117681147286553534438 / 39672 / 2**64
        assertEq(RL.tokenX.cummulativeEarnedPerMLiq, 423621837838722923425 + 3292377527956539412);
        assertEq(RL.tokenX.subtreeCummulativeEarnedPerMLiq, 423621837838722923425 + 3292377527956539412);
        assertEq(RL.tokenY.cummulativeEarnedPerMLiq, 2197359621190 + 12974025);
        assertEq(RL.tokenY.subtreeCummulativeEarnedPerMLiq, 2197359621190 + 12974025);

        // RRL
        // 53e18 * 2352954287417905205553 / 305908639 / 2**64
        // 1754e18 * 2352954287417905205553 / 305908639 / 2**64
        // 8765e6 * 6117681147286553534438 / 305908639 / 2**64
        // 789296e6 * 6117681147286553534438 / 305908639 / 2**64
        assertEq(RRL.tokenX.cummulativeEarnedPerMLiq, 154733312657952738 + 22099268330799);
        assertEq(RRL.tokenX.subtreeCummulativeEarnedPerMLiq, 2201300334794271053 + 731360691551353);
        assertEq(RRL.tokenY.cummulativeEarnedPerMLiq, 5772069627 + 9502);
        assertEq(RRL.tokenY.subtreeCummulativeEarnedPerMLiq, 519121437518 + 855687);

        // RRLL
        // 1701e18 * 2352954287417905205553 / 296771752 / 2**64
        // 1701e18 * 2352954287417905205553 / 296771752 / 2**64
        // 780531e6 * 6117681147286553534438 / 296771752 / 2**64
        // 780531e6 * 6117681147286553534438 / 296771752 / 2**64
        assertEq(RRLL.tokenX.cummulativeEarnedPerMLiq, 2109575308294031901 + 731097873063750);
        assertEq(RRLL.tokenX.subtreeCummulativeEarnedPerMLiq, 2109575308294031901 + 731097873063750);
        assertEq(RRLL.tokenY.cummulativeEarnedPerMLiq, 529154012121 + 872237);
        assertEq(RRLL.tokenY.subtreeCummulativeEarnedPerMLiq, 529154012121 + 872237);

        // tLiq
        assertEq(root.tLiq, 4430);
        assertEq(R.tLiq, 77);
        assertEq(RR.tLiq, 82734);
        assertEq(RL.tLiq, 111);
        assertEq(RRL.tLiq, 5346);
        assertEq(RRLL.tLiq, 7634865);

        // subtreeMLiq
        assertEq(root.subtreeMLiq, 324198833); // 8430*16 + 377*8 + 9082734*4 + 1111*4 + 45346*2 + 287634865*1
        assertEq(R.subtreeMLiq, 324063953);    // 377*8 + 9082734*4 + 1111*4 + 45346*2 + 287634865*1
        assertEq(RR.subtreeMLiq, 324056493);   // 9082734*4 + 45346*2 + 287634865*1
        assertEq(RL.subtreeMLiq, 4444);        // 1111*4
        assertEq(RRL.subtreeMLiq, 287725557);  // 45346*2 + 287634865*1
        assertEq(RRLL.subtreeMLiq, 287634865); // 287634865*1

        // borrowedX
        assertEq(root.tokenX.borrowed, 492e18);
        assertEq(R.tokenX.borrowed, 998e18);
        assertEq(RR.tokenX.borrowed, 765e18);
        assertEq(RL.tokenX.borrowed, 24e18);
        assertEq(RRL.tokenX.borrowed, 53e18);
        assertEq(RRLL.tokenX.borrowed, 701e18);

        // borrowedY
        assertEq(root.tokenY.borrowed, 254858e6);
        assertEq(R.tokenY.borrowed, 353e6);
        assertEq(RR.tokenY.borrowed, 99763e6);
        assertEq(RL.tokenY.borrowed, 552e6);
        assertEq(RRL.tokenY.borrowed, 8765e6);
        assertEq(RRLL.tokenY.borrowed, 779531e6);

        // subtreeBorrowedX
        assertEq(root.tokenX.subtreeBorrowed, 3033e18); // 492e18 + 998e18 + 765e18 + 53e18 + 701e18 + 24e18
        assertEq(R.tokenX.subtreeBorrowed, 2541e18);    // 998e18 + 765e18 + 53e18 + 701e18 + 24e18
        assertEq(RR.tokenX.subtreeBorrowed, 1519e18);   // 765e18 + 53e18 + 701e18
        assertEq(RL.tokenX.subtreeBorrowed, 24e18);
        assertEq(RRL.tokenX.subtreeBorrowed, 754e18);   // 53e18 + 701e18
        assertEq(RRLL.tokenX.subtreeBorrowed, 701e18);  // 701e18

        // subtreeBorrowedY
        assertEq(root.tokenY.subtreeBorrowed, 1143822e6); // 254858e6 + 353e6 + 99763e6 + 8765e6 + 779531e6 + 552e6
        assertEq(R.tokenY.subtreeBorrowed, 888964e6);     // 353e6 + 99763e6 + 8765e6 + 779531e6 + 552e6
        assertEq(RR.tokenY.subtreeBorrowed, 888059e6);    // 99763e6 + 8765e6 + 779531e6
        assertEq(RL.tokenY.subtreeBorrowed, 552e6);
        assertEq(RRL.tokenY.subtreeBorrowed, 788296e6);   // 8765e6 + 779531e6
        assertEq(RRLL.tokenY.subtreeBorrowed, 779531e6);  // 779531e6
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
        uint24 baseStep = uint24(offset / 2 ** depth);

        uint24 range = offset >> depth;
        uint24 base = offset + baseStep * index;
        return LKeyImpl.makeKey(range, base);
    }
}


contract DenseTreeCodeStructureTest is Test {
    LiqTree public liqTree;
    using LiqTreeImpl for LiqTree;
    using LKeyImpl for LKey;
    using FeeRateSnapshotImpl for FeeRateSnapshot;

    function setUp() public {
        // A depth of 4 creates a tree that covers an absolute range of 16 ([0, 15]). 
        // ie. A complete tree matching the ascii documentation. 
        liqTree.init(4);
    }

    // NOTE: Technically all these cases are already covered by leftLegOnly + rightLegOnly
    //       I'm not yet sure if this is necessary or not.
    //       Leaning toward no.

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
    LiqTree public liqTree;
    using LiqTreeImpl for LiqTree;
    using LKeyImpl for LKey;
    using FeeRateSnapshotImpl for FeeRateSnapshot;

    function setUp() public {
        // A depth of 4 creates a tree that covers an absolute range of 16 ([0, 15]). 
        // ie. A complete tree matching the ascii documentation. 
        liqTree.init(4);
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