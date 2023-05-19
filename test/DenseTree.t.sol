// SPDX-License-Identifier: BSL-1.1
pragma solidity ^0.8.18;

import { console } from "forge-std/console.sol";
import { Test } from "forge-std/Test.sol";

import { FeeRateSnapshot, FeeRateSnapshotImpl } from "src/FeeRateSnapshot.sol";
import { LiqTree, LiqTreeImpl, LiqRange, LKey, LKeyImpl, LiqNode } from "src/Tree.sol";

/**
 * In practice, the LiqTree will have many nodes. So many, that testing at that scale is intractable.
 * Thus the reason for this file. A smaller scale LiqTree, where we can more easily populate the values densely.
 */ 
contract DenseTreeTreeStructureTest is Test {
    LiqTree public liqTree;
    using LiqTreeImpl for LiqTree;
    using LKeyImpl for LKey;
    using FeeRateSnapshotImpl for FeeRateSnapshot;
    
    function setUp() public {
        // A depth of 4 creates a tree that covers an absolute range of 16 ([0, 15];);. 
        // ie. A complete tree matching the ascii documentation. 
        liqTree.init(4);
    }

    function testRootNodeOnly() public {
        LiqNode storage root = liqTree.nodes[liqTree.root];

        liqTree.addInfRangeMLiq(8430);
        liqTree.addInfRangeTLiq(4381, 832e18, 928e6);

        liqTree.feeRateSnapshotTokenY.add(113712805933826);  // 5.4% APR as Q192.64 = 0.054 * 3600 / (365 * 24 * 60 * 60) * 2^64 = 113712805933826
        liqTree.feeRateSnapshotTokenX.add(113712805933826);

        // Verify root state is as expected
        assertEq(root.mLiq, 8430);
        assertEq(root.subtreeMLiq, 134880);
        assertEq(root.tLiq, 4381);
        assertEq(root.tokenX.borrowed, 832e18);
        assertEq(root.tokenX.subtreeBorrowed, 832e18);
        assertEq(root.tokenY.borrowed, 928e6);
        assertEq(root.tokenY.subtreeBorrowed, 928e6);

        // Testing add_inf_range_mLiq
        liqTree.addInfRangeMLiq(9287);

        // earn_x      = 113712805933826 * 832e18 / 134880 / 2**64 = 38024667284.1612625482053537908689136045718673850859328662514
        // earn_y      = 113712805933826 * 928e6 / 134880 / 2**64  = 0.0424121288938721774576136638436614805589455443910573866585112692
        assertEq(root.tokenX.cummulativeEarnedPerMLiq, 38024667284);
        assertEq(root.tokenX.subtreeCummulativeEarnedPerMLiq, 38024667284);
        assertEq(root.tokenY.cummulativeEarnedPerMLiq, 0);
        assertEq(root.tokenY.subtreeCummulativeEarnedPerMLiq, 0);

        assertEq(root.mLiq, 17717);
        assertEq(root.subtreeMLiq, 283472);
        assertEq(root.tLiq, 4381);
        assertEq(root.tokenX.borrowed, 832e18);
        assertEq(root.tokenX.subtreeBorrowed, 832e18);
        assertEq(root.tokenY.borrowed, 928e6);
        assertEq(root.tokenY.subtreeBorrowed, 928e6);

        // Testing remove_inf_range_mLiq
        liqTree.feeRateSnapshotTokenY.add(74672420010376264941568);
        liqTree.feeRateSnapshotTokenX.add(74672420010376264941568);

        liqTree.removeInfRangeMLiq(3682);

        // earn_x      = 74672420010376264941568 * 832e18 / 283472 / 2**64 = 11881018231077496190.0999040469605463678952418581023875373934
        // earn_y      = 74672420010376264941568 * 928e6 / 283472 / 2**64  = 13251904.9500479765197268160523790709488062313032680476378619
        assertEq(root.tokenX.cummulativeEarnedPerMLiq, 11881018269102163474);          // 11881018231077496190 + 38024667284 = 11881018269102163474
        assertEq(root.tokenX.subtreeCummulativeEarnedPerMLiq, 11881018269102163474);  // 11881018231077496190 + 38024667284 = 11881018269102163474
        assertEq(root.tokenY.cummulativeEarnedPerMLiq, 13251904);
        assertEq(root.tokenY.subtreeCummulativeEarnedPerMLiq, 13251904);

        assertEq(root.mLiq, 14035);
        assertEq(root.subtreeMLiq, 224560);
        assertEq(root.tLiq, 4381);
        assertEq(root.tokenX.borrowed, 832e18);
        assertEq(root.tokenX.subtreeBorrowed, 832e18);
        assertEq(root.tokenY.borrowed, 928e6);
        assertEq(root.tokenY.subtreeBorrowed, 928e6);

        // Testing add_inf_range_tLiq
        liqTree.feeRateSnapshotTokenY.add(6932491854677024);
        liqTree.feeRateSnapshotTokenX.add(6932491854677024);

        liqTree.addInfRangeTLiq(7287, 9184e18, 7926920e6);

        // earn_x      = 6932491854677024 * 832e18 / 224560 / 2**64 = 1392388963085.50927075184684754182568989829487082029858389739
        // earn_y      = 6932491854677024 * 928e6 / 224560 / 2**64  = 1.5530492280569141866078291761043440387327135097611022666547915924
        assertEq(root.tokenX.cummulativeEarnedPerMLiq, 11881019661491126559);           // 11881018269102163474 + 1392388963085 = 11881019661491126559
        assertEq(root.tokenX.subtreeCummulativeEarnedPerMLiq, 11881019661491126559);   // 11881018269102163474 + 1392388963085 = 11881019661491126559
        assertEq(root.tokenY.cummulativeEarnedPerMLiq, 13251905);
        assertEq(root.tokenY.subtreeCummulativeEarnedPerMLiq, 13251905);

        assertEq(root.mLiq, 14035);
        assertEq(root.subtreeMLiq, 224560);
        assertEq(root.tLiq, 11668);
        assertEq(root.tokenX.borrowed, 10016e18);
        assertEq(root.tokenX.subtreeBorrowed, 10016e18);
        assertEq(root.tokenY.borrowed, 7927848e6);
        assertEq(root.tokenY.subtreeBorrowed, 7927848e6);

        // Testing remove_inf_range_tLiq
        liqTree.feeRateSnapshotTokenY.add(1055375100301031600000000);
        liqTree.feeRateSnapshotTokenX.add(1055375100301031600000000);

        liqTree.removeInfRangeTLiq(4923, 222e18, 786e6);

        // earn_x      = 1055375100301031600000000 * 10016e18 / 224560 / 2**64  = 2551814126505030241953.87164028103035638433335980020216618053
        // earn_y      = 1055375100301031600000000 * 7927848e6 / 224560 / 2**64 = 2019807759503.25988354767545683493270255599285721099372431609
        assertEq(root.tokenX.cummulativeEarnedPerMLiq, 2563695146166521368512);          // 2551814126505030241953 + 11881019661491126559 = 2563695146166521368512
        assertEq(root.tokenX.subtreeCummulativeEarnedPerMLiq, 2563695146166521368512);  // 2551814126505030241953 + 11881019661491126559 = 2563695146166521368512
        assertEq(root.tokenY.cummulativeEarnedPerMLiq, 2019821011408);                   // 2019807759503 + 13251905 = 2019821011408
        assertEq(root.tokenY.subtreeCummulativeEarnedPerMLiq, 2019821011408);           // 2019807759503 + 13251905 = 2019821011408

        assertEq(root.mLiq, 14035);
        assertEq(root.subtreeMLiq, 224560);
        assertEq(root.tLiq, 6745);
        assertEq(root.tokenX.borrowed, 9794e18);
        assertEq(root.tokenX.subtreeBorrowed, 9794e18);
        assertEq(root.tokenY.borrowed, 7927062e6);
        assertEq(root.tokenY.subtreeBorrowed, 7927062e6);
    }

    function testLeftLegOnly() public {
        // Mirrors test_right_leg_only
        // Manual calculations are shown there.

        LiqNode storage root = liqTree.nodes[liqTree.root];

        LiqNode storage L = liqTree.nodes[LKey.wrap((8 << 24) | 16)];  // 134217744
        LiqNode storage LL = liqTree.nodes[LKey.wrap((4 << 24) | 16)];  // 67108880
        LiqNode storage LR = liqTree.nodes[LKey.wrap((4 << 24) | 20)];  // 67108884
        LiqNode storage LLR = liqTree.nodes[LKey.wrap((2 << 24) | 18)];  // 33554450
        LiqNode storage LLRR = liqTree.nodes[LKey.wrap((1 << 24) | 19)];  // 16777235

        // T0 - populate tree with data excluding fee calculations
        liqTree.addInfRangeMLiq(8430);  // root
        liqTree.addMLiq(LiqRange(0, 7), 377);  // L
        liqTree.addMLiq(LiqRange(0, 3), 9082734);  // LL
        liqTree.addMLiq(LiqRange(4, 7), 1111);  // LR
        liqTree.addMLiq(LiqRange(2, 3), 45346);  // LLR
        liqTree.addMLiq(LiqRange(3, 3), 287634865);  // LLRR

        liqTree.addInfRangeTLiq(4430, 492e18, 254858e6);  // root
        liqTree.addTLiq(LiqRange(0, 7), 77, 998e18, 353e6);  // L
        liqTree.addTLiq(LiqRange(0, 3), 82734, 765e18, 99763e6);  // LL
        liqTree.addTLiq(LiqRange(4, 7), 111, 24e18, 552e6);  // LR
        liqTree.addTLiq(LiqRange(2, 3), 5346, 53e18, 8765e6);  // LLR
        liqTree.addTLiq(LiqRange(3, 3), 7634865, 701e18, 779531e6);  // LLRR

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
        assertEq(root.subtreeMLiq, 324198833);
        assertEq(L.subtreeMLiq, 324063953);
        assertEq(LL.subtreeMLiq, 324056493);
        assertEq(LR.subtreeMLiq, 4444);
        assertEq(LLR.subtreeMLiq, 287725557);
        assertEq(LLRR.subtreeMLiq, 287634865);

        // borrowed_x
        assertEq(root.tokenX.borrowed, 492e18);
        assertEq(L.tokenX.borrowed, 998e18);
        assertEq(LL.tokenX.borrowed, 765e18);
        assertEq(LR.tokenX.borrowed, 24e18);
        assertEq(LLR.tokenX.borrowed, 53e18);
        assertEq(LLRR.tokenX.borrowed, 701e18);

        // subtree_borrowed_x
        assertEq(root.tokenX.subtreeBorrowed, 3033e18);
        assertEq(L.tokenX.subtreeBorrowed, 2541e18);
        assertEq(LL.tokenX.subtreeBorrowed, 1519e18);
        assertEq(LR.tokenX.subtreeBorrowed, 24e18);
        assertEq(LLR.tokenX.subtreeBorrowed, 754e18);
        assertEq(LLRR.tokenX.subtreeBorrowed, 701e18);

        // borrowed_y
        assertEq(root.tokenY.borrowed, 254858e6);
        assertEq(L.tokenY.borrowed, 353e6);
        assertEq(LL.tokenY.borrowed, 99763e6);
        assertEq(LR.tokenY.borrowed, 552e6);
        assertEq(LLR.tokenY.borrowed, 8765e6);
        assertEq(LLRR.tokenY.borrowed, 779531e6);

        // subtree_borrowed_y
        assertEq(root.tokenY.subtreeBorrowed, 1143822e6);
        assertEq(L.tokenY.subtreeBorrowed, 888964e6);
        assertEq(LL.tokenY.subtreeBorrowed, 888059e6);
        assertEq(LR.tokenY.subtreeBorrowed, 552e6);
        assertEq(LLR.tokenY.subtreeBorrowed, 788296e6);
        assertEq(LLRR.tokenY.subtreeBorrowed, 779531e6);

        // T98273
        liqTree.feeRateSnapshotTokenX.add(4541239648278065);
        liqTree.feeRateSnapshotTokenY.add(13278814667749784);

        // Apply change that requires fee calculation
        // addMLiq
        liqTree.addMLiq(LiqRange(3, 7), 2734);  // LLRR, LR

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
        assertEq(root.subtreeMLiq, 324212503);
        assertEq(L.subtreeMLiq, 324077623);
        assertEq(LL.subtreeMLiq, 324059227);
        assertEq(LR.subtreeMLiq, 15380);
        assertEq(LLR.subtreeMLiq, 287728291);
        assertEq(LLRR.subtreeMLiq, 287637599);

        // T2876298273
        liqTree.feeRateSnapshotTokenX.add(16463537718422861220174597);
        liqTree.feeRateSnapshotTokenY.add(3715979586694123491881712207);

        // Apply change that requires fee calculation
        // remove_mLiq
        liqTree.removeMLiq(LiqRange(3, 7), 2734);  // LLRR, LR

        // root
        assertEq(root.tokenX.cummulativeEarnedPerMLiq, 1354374549844117328);
        assertEq(root.tokenX.subtreeCummulativeEarnedPerMLiq, 8349223596904894020);
        assertEq(root.tokenY.cummulativeEarnedPerMLiq, 158351473403);
        assertEq(root.tokenY.subtreeCummulativeEarnedPerMLiq, 710693401863);

        // L
        assertEq(L.tokenX.cummulativeEarnedPerMLiq, 2747859799935140577);
        assertEq(L.tokenX.subtreeCummulativeEarnedPerMLiq, 6996304360355904016);
        assertEq(L.tokenY.cummulativeEarnedPerMLiq, 219375887);
        assertEq(L.tokenY.subtreeCummulativeEarnedPerMLiq, 552456845956);

        // LL
        assertEq(LL.tokenX.cummulativeEarnedPerMLiq, 2106654304686669588);
        assertEq(LL.tokenX.subtreeCummulativeEarnedPerMLiq, 4183016848129478568);
        assertEq(LL.tokenY.cummulativeEarnedPerMLiq, 62008538706);
        assertEq(LL.tokenY.subtreeCummulativeEarnedPerMLiq, 551980602777);

        // LR
        assertEq(LR.tokenX.cummulativeEarnedPerMLiq, 423248578107618890129);
        assertEq(LR.tokenX.subtreeCummulativeEarnedPerMLiq, 423248578107618890129);
        assertEq(LR.tokenY.cummulativeEarnedPerMLiq, 2197219781195);
        assertEq(LR.tokenY.subtreeCummulativeEarnedPerMLiq, 2197219781195);

        // LLR
        assertEq(LLR.tokenX.cummulativeEarnedPerMLiq, 154626415017241476);
        assertEq(LLR.tokenX.subtreeCummulativeEarnedPerMLiq, 2199779564584907057);
        assertEq(LLR.tokenY.cummulativeEarnedPerMLiq, 5771781665);
        assertEq(LLR.tokenY.subtreeCummulativeEarnedPerMLiq, 519095539055);

        // LLRR
        assertEq(LLRR.tokenX.cummulativeEarnedPerMLiq, 2108117905996538332);
        assertEq(LLRR.tokenX.subtreeCummulativeEarnedPerMLiq, 2108117905996538332);
        assertEq(LLRR.tokenY.cummulativeEarnedPerMLiq, 529127613135);
        assertEq(LLRR.tokenY.subtreeCummulativeEarnedPerMLiq, 529127613135);

        // mLiq
        assertEq(root.mLiq, 8430);
        assertEq(L.mLiq, 377);
        assertEq(LL.mLiq, 9082734);
        assertEq(LR.mLiq, 1111);
        assertEq(LLR.mLiq, 45346);
        assertEq(LLRR.mLiq, 287634865);

        // subtreeMLiq
        assertEq(root.subtreeMLiq, 324198833);
        assertEq(L.subtreeMLiq, 324063953);
        assertEq(LL.subtreeMLiq, 324056493);
        assertEq(LR.subtreeMLiq, 4444);
        assertEq(LLR.subtreeMLiq, 287725557);
        assertEq(LLRR.subtreeMLiq, 287634865);

        // T9214298113
        liqTree.feeRateSnapshotTokenX.add(11381610389149375791104);
        liqTree.feeRateSnapshotTokenY.add(185394198934916215865344);

        // Apply change that requires fee calculation
        // addTLiq
        liqTree.addTLiq(LiqRange(3, 7), 1000, 1000e18, 1000e6);  // LLRR, LR

        // root
        assertEq(root.tokenX.cummulativeEarnedPerMLiq, 1355310898622008714);
        assertEq(root.tokenX.subtreeCummulativeEarnedPerMLiq, 8354995844553968361);
        assertEq(root.tokenY.cummulativeEarnedPerMLiq, 158359374060);
        assertEq(root.tokenY.subtreeCummulativeEarnedPerMLiq, 710728860612);

        // L
        assertEq(L.tokenX.cummulativeEarnedPerMLiq, 2749759536746020654);
        assertEq(L.tokenX.subtreeCummulativeEarnedPerMLiq, 7001141265402443371);
        assertEq(L.tokenY.cummulativeEarnedPerMLiq, 219386832);
        assertEq(L.tokenY.subtreeCummulativeEarnedPerMLiq, 552484409781);

        // LL
        assertEq(LL.tokenX.cummulativeEarnedPerMLiq, 2108110694023652835);
        assertEq(LL.tokenX.subtreeCummulativeEarnedPerMLiq, 4185908685257423082);
        assertEq(LL.tokenY.cummulativeEarnedPerMLiq, 62011632404);
        assertEq(LL.tokenY.subtreeCummulativeEarnedPerMLiq, 552008141912);

        // LR
        assertEq(LR.tokenX.cummulativeEarnedPerMLiq, 423621837838722923425);
        assertEq(LR.tokenX.subtreeCummulativeEarnedPerMLiq, 423621837838722923425);
        assertEq(LR.tokenY.cummulativeEarnedPerMLiq, 2197359621190);
        assertEq(LR.tokenY.subtreeCummulativeEarnedPerMLiq, 2197359621190);

        // LLR
        assertEq(LLR.tokenX.cummulativeEarnedPerMLiq, 154733312657952738);
        assertEq(LLR.tokenX.subtreeCummulativeEarnedPerMLiq, 2201300334794271053);
        assertEq(LLR.tokenY.cummulativeEarnedPerMLiq, 5772069627);
        assertEq(LLR.tokenY.subtreeCummulativeEarnedPerMLiq, 519121437518);

        // LLRR
        assertEq(LLRR.tokenX.cummulativeEarnedPerMLiq, 2109575308294031901);
        assertEq(LLRR.tokenX.subtreeCummulativeEarnedPerMLiq, 2109575308294031901);
        assertEq(LLRR.tokenY.cummulativeEarnedPerMLiq, 529154012121);
        assertEq(LLRR.tokenY.subtreeCummulativeEarnedPerMLiq, 529154012121);

        // tLiq
        assertEq(root.tLiq, 4430);
        assertEq(L.tLiq, 77);
        assertEq(LL.tLiq, 82734);
        assertEq(LR.tLiq, 1111);
        assertEq(LLR.tLiq, 5346);
        assertEq(LLRR.tLiq, 7635865);

        // borrowed_x
        assertEq(root.tokenX.borrowed, 492e18);
        assertEq(L.tokenX.borrowed, 998e18);
        assertEq(LL.tokenX.borrowed, 765e18);
        assertEq(LR.tokenX.borrowed, 1024e18);
        assertEq(LLR.tokenX.borrowed, 53e18);
        assertEq(LLRR.tokenX.borrowed, 1701e18);

        // subtree_borrowed_x
        assertEq(root.tokenX.subtreeBorrowed, 5033e18);
        assertEq(L.tokenX.subtreeBorrowed, 4541e18);
        assertEq(LL.tokenX.subtreeBorrowed, 2519e18);
        assertEq(LR.tokenX.subtreeBorrowed, 1024e18);
        assertEq(LLR.tokenX.subtreeBorrowed, 1754e18);
        assertEq(LLRR.tokenX.subtreeBorrowed, 1701e18);

        // borrowed_y
        assertEq(root.tokenY.borrowed, 254858e6);
        assertEq(L.tokenY.borrowed, 353e6);
        assertEq(LL.tokenY.borrowed, 99763e6);
        assertEq(LR.tokenY.borrowed, 1552e6);
        assertEq(LLR.tokenY.borrowed, 8765e6);
        assertEq(LLRR.tokenY.borrowed, 780531e6);

        // subtree_borrowed_y
        assertEq(root.tokenY.subtreeBorrowed, 1145822e6);
        assertEq(L.tokenY.subtreeBorrowed, 890964e6);
        assertEq(LL.tokenY.subtreeBorrowed, 889059e6);
        assertEq(LR.tokenY.subtreeBorrowed, 1552e6);
        assertEq(LLR.tokenY.subtreeBorrowed, 789296e6);
        assertEq(LLRR.tokenY.subtreeBorrowed, 780531e6);

        // T32876298273
        // 3.3) addTLiq
        liqTree.feeRateSnapshotTokenX.add(2352954287417905205553);
        liqTree.feeRateSnapshotTokenY.add(6117681147286553534438);

        // Apply change that requires fee calculation
        // addTLiq
        liqTree.removeTLiq(LiqRange(3, 7), 1000, 1000e18, 1000e6);  // LLRR, LR

        // root
        assertEq(root.tokenX.cummulativeEarnedPerMLiq, 1355504472799662735);
        assertEq(root.tokenX.subtreeCummulativeEarnedPerMLiq, 8356976045440416914);
        assertEq(root.tokenY.cummulativeEarnedPerMLiq, 158359634767);
        assertEq(root.tokenY.subtreeCummulativeEarnedPerMLiq, 710730032734);

        // L
        assertEq(L.tokenX.cummulativeEarnedPerMLiq, 2750152275007241346);
        assertEq(L.tokenX.subtreeCummulativeEarnedPerMLiq, 7002928263843528706);
        assertEq(L.tokenY.cummulativeEarnedPerMLiq, 219387193);
        assertEq(L.tokenY.subtreeCummulativeEarnedPerMLiq, 552485321384);

        // LL
        assertEq(LL.tokenX.cummulativeEarnedPerMLiq, 2108411777738297592);
        assertEq(LL.tokenX.subtreeCummulativeEarnedPerMLiq, 4186900096861593203);
        assertEq(LL.tokenY.cummulativeEarnedPerMLiq, 62011734490);
        assertEq(LL.tokenY.subtreeCummulativeEarnedPerMLiq, 552009051678);

        // LR
        assertEq(LR.tokenX.cummulativeEarnedPerMLiq, 426914215366679462837);
        assertEq(LR.tokenX.subtreeCummulativeEarnedPerMLiq, 426914215366679462837);
        assertEq(LR.tokenY.cummulativeEarnedPerMLiq, 2197372595215);
        assertEq(LR.tokenY.subtreeCummulativeEarnedPerMLiq, 2197372595215);

        // LLR
        assertEq(LLR.tokenX.cummulativeEarnedPerMLiq, 154755411926283537);
        assertEq(LLR.tokenX.subtreeCummulativeEarnedPerMLiq, 2202031695485822406);
        assertEq(LLR.tokenY.cummulativeEarnedPerMLiq, 5772079129);
        assertEq(LLR.tokenY.subtreeCummulativeEarnedPerMLiq, 519122293205);

        // LLRR
        assertEq(LLRR.tokenX.cummulativeEarnedPerMLiq, 2110306406167095651);
        assertEq(LLRR.tokenX.subtreeCummulativeEarnedPerMLiq, 2110306406167095651);
        assertEq(LLRR.tokenY.cummulativeEarnedPerMLiq, 529154884358);
        assertEq(LLRR.tokenY.subtreeCummulativeEarnedPerMLiq, 529154884358);

        // tLiq
        assertEq(root.tLiq, 4430);
        assertEq(L.tLiq, 77);
        assertEq(LL.tLiq, 82734);
        assertEq(LR.tLiq, 111);
        assertEq(LLR.tLiq, 5346);
        assertEq(LLRR.tLiq, 7634865);

        // subtreeMLiq
        assertEq(root.subtreeMLiq, 324198833);
        assertEq(L.subtreeMLiq, 324063953);
        assertEq(LL.subtreeMLiq, 324056493);
        assertEq(LR.subtreeMLiq, 4444);
        assertEq(LLR.subtreeMLiq, 287725557);
        assertEq(LLRR.subtreeMLiq, 287634865);

        // borrowed_x
        assertEq(root.tokenX.borrowed, 492e18);
        assertEq(L.tokenX.borrowed, 998e18);
        assertEq(LL.tokenX.borrowed, 765e18);
        assertEq(LR.tokenX.borrowed, 24e18);
        assertEq(LLR.tokenX.borrowed, 53e18);
        assertEq(LLRR.tokenX.borrowed, 701e18);

        // subtree_borrowed_x
        assertEq(root.tokenX.subtreeBorrowed, 3033e18);
        assertEq(L.tokenX.subtreeBorrowed, 2541e18);
        assertEq(LL.tokenX.subtreeBorrowed, 1519e18);
        assertEq(LR.tokenX.subtreeBorrowed, 24e18);
        assertEq(LLR.tokenX.subtreeBorrowed, 754e18);
        assertEq(LLRR.tokenX.subtreeBorrowed, 701e18);

        // borrowed_y
        assertEq(root.tokenY.borrowed, 254858e6);
        assertEq(L.tokenY.borrowed, 353e6);
        assertEq(LL.tokenY.borrowed, 99763e6);
        assertEq(LR.tokenY.borrowed, 552e6);
        assertEq(LLR.tokenY.borrowed, 8765e6);
        assertEq(LLRR.tokenY.borrowed, 779531e6);

        // subtree_borrowed_y
        assertEq(root.tokenY.subtreeBorrowed, 1143822e6);
        assertEq(L.tokenY.subtreeBorrowed, 888964e6);
        assertEq(LL.tokenY.subtreeBorrowed, 888059e6);
        assertEq(LR.tokenY.subtreeBorrowed, 552e6);
        assertEq(LLR.tokenY.subtreeBorrowed, 788296e6);
        assertEq(LLRR.tokenY.subtreeBorrowed, 779531e6);
    }

    function testRightLegOnly() public {

        LiqNode storage root = liqTree.nodes[liqTree.root];

        LiqNode storage R = liqTree.nodes[LKey.wrap((8 << 24) | 24)];
        LiqNode storage RR = liqTree.nodes[LKey.wrap((4 << 24) | 28)];
        LiqNode storage RL = liqTree.nodes[LKey.wrap((4 << 24) | 24)];
        LiqNode storage RRL = liqTree.nodes[LKey.wrap((2 << 24) | 28)];
        LiqNode storage RRLL = liqTree.nodes[LKey.wrap((1 << 24) | 28)];

        // T0 - populate tree with data excluding fee calculations
        liqTree.addInfRangeMLiq(8430);                        // root
        liqTree.addMLiq(LiqRange(8, 15), 377);         // R
        liqTree.addMLiq(LiqRange(12, 15), 9082734);    // RR
        liqTree.addMLiq(LiqRange(8, 11), 1111);        // RL
        liqTree.addMLiq(LiqRange(12, 13), 45346);      // RRL
        liqTree.addMLiq(LiqRange(12, 12), 287634865);  // RRLL

        liqTree.addInfRangeTLiq(4430, 492e18, 254858e6);                      // root
        liqTree.addTLiq(LiqRange(8, 15), 77, 998e18, 353e6);           // R
        liqTree.addTLiq(LiqRange(12, 15), 82734, 765e18, 99763e6);     // RR
        liqTree.addTLiq(LiqRange(8, 11), 111, 24e18, 552e6);           // RL
        liqTree.addTLiq(LiqRange(12, 13), 5346, 53e18, 8765e6);        // RRL
        liqTree.addTLiq(LiqRange(12, 12), 7634865, 701e18, 779531e6);  // RRLL

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
        assertEq(root.subtreeMLiq, 324198833);  // 8430*16 + 377*8 + 9082734*4 + 1111*4 + 45346*2 + 287634865*1
        assertEq(R.subtreeMLiq, 324063953);     // 377*8 + 9082734*4 + 1111*4 + 45346*2 + 287634865*1
        assertEq(RR.subtreeMLiq, 324056493);    // 9082734*4 + 45346*2 + 287634865*1
        assertEq(RL.subtreeMLiq, 4444);         // 1111*4
        assertEq(RRL.subtreeMLiq, 287725557);   // 45346*2 + 287634865*1
        assertEq(RRLL.subtreeMLiq, 287634865);  // 287634865*1

        // borrowed_x
        assertEq(root.tokenX.borrowed, 492e18);
        assertEq(R.tokenX.borrowed, 998e18);
        assertEq(RR.tokenX.borrowed, 765e18);
        assertEq(RL.tokenX.borrowed, 24e18);
        assertEq(RRL.tokenX.borrowed, 53e18);
        assertEq(RRLL.tokenX.borrowed, 701e18);

        // subtree_borrowed_x
        assertEq(root.tokenX.subtreeBorrowed, 3033e18);  // 492e18 + 998e18 + 765e18 + 53e18 + 701e18 + 24e18
        assertEq(R.tokenX.subtreeBorrowed, 2541e18);     // 998e18 + 765e18 + 53e18 + 701e18 + 24e18
        assertEq(RR.tokenX.subtreeBorrowed, 1519e18);    // 765e18 + 53e18 + 701e18
        assertEq(RL.tokenX.subtreeBorrowed, 24e18);      // 24e18
        assertEq(RRL.tokenX.subtreeBorrowed, 754e18);    // 53e18 + 701e18
        assertEq(RRLL.tokenX.subtreeBorrowed, 701e18);   // 701e18

        // borrowed_y
        assertEq(root.tokenY.borrowed, 254858e6);
        assertEq(R.tokenY.borrowed, 353e6);
        assertEq(RR.tokenY.borrowed, 99763e6);
        assertEq(RL.tokenY.borrowed, 552e6);
        assertEq(RRL.tokenY.borrowed, 8765e6);
        assertEq(RRLL.tokenY.borrowed, 779531e6);

        // subtree_borrowed_y
        assertEq(root.tokenY.subtreeBorrowed, 1143822e6);  // 254858e6 + 353e6 + 99763e6 + 8765e6 + 779531e6 + 552e6
        assertEq(R.tokenY.subtreeBorrowed, 888964e6);      // 353e6 + 99763e6 + 8765e6 + 779531e6 + 552e6
        assertEq(RR.tokenY.subtreeBorrowed, 888059e6);     // 99763e6 + 8765e6 + 779531e6
        assertEq(RL.tokenY.subtreeBorrowed, 552e6);        // 552e6
        assertEq(RRL.tokenY.subtreeBorrowed, 788296e6);    // 8765e6 + 779531e6
        assertEq(RRLL.tokenY.subtreeBorrowed, 779531e6);   // 779531e6

        // T98273
        liqTree.feeRateSnapshotTokenX.add(4541239648278065);   // 7.9% APR as Q192.64 T98273 - T0
        liqTree.feeRateSnapshotTokenY.add(13278814667749784);  // 23.1% APR as Q192.64 T98273 - T0

        // Apply change that requires fee calculation
        // addMLiq
        liqTree.addMLiq(LiqRange(8, 12), 2734);  // RRLL, RL

        // root
        //           total_mLiq = subtreeMLiq + aux_level * range
        //           earn_x = rate_diff * borrow / total_mLiq / q_conversion
        //
        //           earn_x     = 4541239648278065 * 492e18 / 324198833 / 2**64 = 373601278.675896709674247960788128930863427771780474615825402
        //           earn_x_sub = 4541239648278065 * 3033e18 / 324198833 / 2**64 = 2303115199.64226569195527248998047773843247242237841363780171
        //
        //           earn_y     = 13278814667749784 * 254858e6 / 324198833 / 2**64 = 0.5658826914495360518450511013487630736056981385516828024975012016
        //           earn_y_sub = 13278814667749784 * 1143822e6 / 324198833 / 2**64 = 2.5397243637601771413630729302079780755472335819729532779755660779
        assertEq(root.tokenX.cummulativeEarnedPerMLiq, 373601278);
        assertEq(root.tokenX.subtreeCummulativeEarnedPerMLiq, 2303115199);
        assertEq(root.tokenY.cummulativeEarnedPerMLiq, 0);
        assertEq(root.tokenY.subtreeCummulativeEarnedPerMLiq, 2);

        // R
        //           total_mLiq = 324063953 + 8430 * 8 = 324131393
        //
        //           earn_x      = 4541239648278065 * 998e18 / 324131393 / 2**64 = 757991165.739306427787211084069081135461126639210612444989968
        //           earn_x_sub  = 4541239648278065 * 2541e18 / 324131393 / 2**64 = 1929915382.90939642585902140743440397315302884793002627527005
        //
        //           earn_y      = 13278814667749784 * 353e6 / 324131393 / 2**64 = 0.0007839587228619296743658765199435031723124415958637831459168088
        //           earn_y_sub  = 13278814667749784 * 888964e6 / 324131393 / 2**64 = 1.9742523572527831474305582285412361305143267162194111063081870320
        assertEq(R.tokenX.cummulativeEarnedPerMLiq, 757991165);
        assertEq(R.tokenX.subtreeCummulativeEarnedPerMLiq, 1929915382);
        assertEq(R.tokenY.cummulativeEarnedPerMLiq, 0);
        assertEq(R.tokenY.subtreeCummulativeEarnedPerMLiq, 1);

        // RR
        //           total_mLiq = 324056493 + (377 + 8430) * 4 = 324091721
        //
        //           earn_x      = 4541239648278065 * 765e18 / 324091721 / 2**64 = 581096415.560225831923714717876078601550264387092272644849535
        //           earn_x_sub  = 4541239648278065 * 1519e18 / 324091721 / 2**64 = 1153837196.38690593293087928948204365458150536469694398369469
        //
        //           earn_y      = 13278814667749784 * 99763e6 / 324091721 / 2**64 = 0.2215854043845212215658200680605818096232476901747430889861663960
        //           earn_y_sub  = 13278814667749784 * 888059e6 / 324091721 / 2**64 = 1.9724839131974131842719305135352006382347335233392357172695883598
        assertEq(RR.tokenX.cummulativeEarnedPerMLiq, 581096415);
        assertEq(RR.tokenX.subtreeCummulativeEarnedPerMLiq, 1153837196);
        assertEq(RR.tokenY.cummulativeEarnedPerMLiq, 0);
        assertEq(RR.tokenY.subtreeCummulativeEarnedPerMLiq, 1);

        // RL
        //           total_mLiq = 4444 + (377 + 8430) * 4 = 39672
        //
        //           earn_x      = 4541239648278065 * 24e18 / 39672 / 2**64 = 148929881804.004419784834421574153374302771710945632482252911
        //           earn_x_sub  = 4541239648278065 * 24e18 / 39672 / 2**64 = 148929881804.004419784834421574153374302771710945632482252911
        //
        //           earn_y      = 13278814667749784 * 552e6 / 39672 / 2**64 = 10.016005848413612945928345245285743980736658202469601316734724742
        //           earn_y_sub  = 13278814667749784 * 552e6 / 39672 / 2**64 = 10.016005848413612945928345245285743980736658202469601316734724742
        assertEq(RL.tokenX.cummulativeEarnedPerMLiq, 148929881804);
        assertEq(RL.tokenX.subtreeCummulativeEarnedPerMLiq, 148929881804);
        assertEq(RL.tokenY.cummulativeEarnedPerMLiq, 10);
        assertEq(RL.tokenY.subtreeCummulativeEarnedPerMLiq, 10);

        // RRL
        //           total_mLiq = 287725557 + (9082734 + 377 + 8430) * 2 = 305908639
        //
        //           earn_x      = 4541239648278065 * 53e18 / 305908639 / 2**64 = 42651943.5921096141810155248335108410236545389757231280339726
        //           earn_x_sub  = 4541239648278065 * 754e18 / 305908639 / 2**64 = 606784254.121710360235579353291833474185575894107457330898403
        //
        //           earn_y      = 13278814667749784 * 8765e6 / 305908639 / 2**64 = 0.0206252758466917150640245207131723061423410095348761855275430371
        //           earn_y_sub  = 13278814667749784 * 788296e6 / 305908639 / 2**64 = 1.8549711864054412114215942475882345970088817401374509465624718757
        assertEq(RRL.tokenX.cummulativeEarnedPerMLiq, 42651943);
        assertEq(RRL.tokenX.subtreeCummulativeEarnedPerMLiq, 606784254);
        assertEq(RRL.tokenY.cummulativeEarnedPerMLiq, 0);
        assertEq(RRL.tokenY.subtreeCummulativeEarnedPerMLiq, 1);

        // RRLL
        //           total_mLiq = 287634865 + (45346 + 9082734 + 377 + 8430) * 1 = 296771752
        //
        //           earn_x      = 4541239648278065 * 701e18 / 296771752 / 2**64 = 581500584.766017533363270505955415005042190229659676220491523
        //           earn_x_sub  = 4541239648278065 * 701e18 / 296771752 / 2**64 = 581500584.766017533363270505955415005042190229659676220491523
        //
        //           earn_y      = 13278814667749784 * 779531e6 / 296771752 / 2**64 = 1.8908210002218903501728143334071499784764070319492513392714860291
        //           earn_y_sub  = 13278814667749784 * 779531e6 / 296771752 / 2**64 = 1.8908210002218903501728143334071499784764070319492513392714860291
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
        assertEq(root.subtreeMLiq, 324212503);  // 8430*16 + 377*8 + 9082734*4 + 3845*4 + 45346*2 + 287637599*1
        assertEq(R.subtreeMLiq, 324077623);     // 377*8 + 9082734*4 + 3845*4 + 45346*2 + 287637599*1
        assertEq(RR.subtreeMLiq, 324059227);    // 9082734*4 + 45346*2 + 287637599*1
        assertEq(RL.subtreeMLiq, 15380);        // 3845*4
        assertEq(RRL.subtreeMLiq, 287728291);   // 45346*2 + 287637599*1
        assertEq(RRLL.subtreeMLiq, 287637599);  // 287637599*1

        // T2876298273
        liqTree.feeRateSnapshotTokenX.add(16463537718422861220174597);    // 978567.9% APR as Q192.64 T2876298273 - T98273
        liqTree.feeRateSnapshotTokenY.add(3715979586694123491881712207);  // 220872233.1% APR as Q192.64 T2876298273 - T98273

        // Apply change that requires fee calculation
        // remove_mLiq
        liqTree.removeMLiq(LiqRange(8, 12), 2734);  // RRLL, RL

        // root
        //           total_mLiq = 324212503
        //
        //           earn_x      = 16463537718422861220174597 * 492e18 / 324212503 / 2**64  = 1354374549470516050.18864221581152444619216774937383131887026
        //           earn_x_sub  = 16463537718422861220174597 * 3033e18 / 324212503 / 2**64 = 8349223594601778821.58973951332592204329439996717648453279172
        //
        //           earn_y      = 3715979586694123491881712207 * 254858e6 / 324212503 / 2**64  = 158351473403.760477087118657111090258803416110827691474619042
        //           earn_y_sub  = 3715979586694123491881712207 * 1143822e6 / 324212503 / 2**64 = 710693401861.570429112455707155049015549996557766096092261976
        assertEq(root.tokenX.cummulativeEarnedPerMLiq, 1354374549844117328);          // 373601278 + 1354374549470516050 = 1354374549844117328
        assertEq(root.tokenX.subtreeCummulativeEarnedPerMLiq, 8349223596904894020);  // 2303115199 + 8349223594601778821 = 8349223596904894020
        assertEq(root.tokenY.cummulativeEarnedPerMLiq, 158351473403);                 // 0 + 158351473403 = 158351473403
        assertEq(root.tokenY.subtreeCummulativeEarnedPerMLiq, 710693401863);         // 2 + 710693401861 = 710693401863

        // R
        //           total_mLiq = 324077623 + 8430 * 8 = 324145063
        //
        //           earn_x      = 16463537718422861220174597 * 998e18 / 324145063 / 2**64  = 2747859799177149412.40503918202324257122793136834755591677703
        //           earn_x_sub  = 16463537718422861220174597 * 2541e18 / 324145063 / 2**64 = 6996304358425988634.18958372897901740830678718133380719892830
        //
        //           earn_y      = 3715979586694123491881712207 * 353e6 / 324145063 / 2**64    = 219375887.687723491736647414380713113554572979392890952782027
        //           earn_y_sub  = 3715979586694123491881712207 * 888964e6 / 324145063 / 2**64 = 552456845955.890725518915105035513462543703722529807118835474
        assertEq(R.tokenX.cummulativeEarnedPerMLiq, 2747859799935140577);          // 757991165 + 2747859799177149412 = 2747859799935140577
        assertEq(R.tokenX.subtreeCummulativeEarnedPerMLiq, 6996304360355904016);  // 1929915382 + 6996304358425988634 = 6996304360355904016
        assertEq(R.tokenY.cummulativeEarnedPerMLiq, 219375887);                    // 0 + 219375887 = 219375887 = 219375887
        assertEq(R.tokenY.subtreeCummulativeEarnedPerMLiq, 552456845956);         // 1 + 552456845955 = 552456845956

        // RR
        //           total_mLiq = 324059227 + (377 + 8430) * 4 = 324094455
        //
        //           earn_x      = 16463537718422861220174597 * 765e18 / 324094455 / 2**64 = 2106654304105573173.10473569019029577351750175393657598084186
        //           earn_x_sub  = 16463537718422861220174597 * 1519e18 / 324094455 / 2**64 = 4183016846975641372.47855361228635199996481720814334498679581
        //
        //           earn_y      = 3715979586694123491881712207 * 99763e6 / 324094455 / 2**64  = 62008538706.1288411875002441524622314240784801570453009535875
        //           earn_y_sub  = 3715979586694123491881712207 * 888059e6 / 324094455 / 2**64 = 551980602776.841840924293368501262560029627326862519099461143
        assertEq(RR.tokenX.cummulativeEarnedPerMLiq, 2106654304686669588);          // 581096415 + 2106654304105573173 = 2106654304686669588
        assertEq(RR.tokenX.subtreeCummulativeEarnedPerMLiq, 4183016848129478568);  // 1153837196 + 4183016846975641372 = 4183016848129478568
        assertEq(RR.tokenY.cummulativeEarnedPerMLiq, 62008538706);                  // 0 + 62008538706 = 62008538706
        assertEq(RR.tokenY.subtreeCummulativeEarnedPerMLiq, 551980602777);         // 1 + 551980602776 = 551980602777

        // RL
        //           total_mLiq = 15380 + (377 + 8430) * 4 = 50608
        //
        //           earn_x      = 16463537718422861220174597 * 24e18 / 50608 / 2**64 = 423248577958689008325.429426909965566945601510047930853109815
        //           earn_x_sub  = 16463537718422861220174597 * 24e18 / 50608 / 2**64 = 423248577958689008325.429426909965566945601510047930853109815
        //
        //           earn_y      = 3715979586694123491881712207 * 552e6 / 50608 / 2**64 = 2197219781185.45157550848350683783177940360867452683580030548
        //           earn_y_sub  = 3715979586694123491881712207 * 552e6 / 50608 / 2**64 = 2197219781185.45157550848350683783177940360867452683580030548
        assertEq(RL.tokenX.cummulativeEarnedPerMLiq, 423248578107618890129);          // 148929881804 + 423248577958689008325 = 423248578107618890129
        assertEq(RL.tokenX.subtreeCummulativeEarnedPerMLiq, 423248578107618890129);  // 148929881804 + 423248577958689008325 = 423248578107618890129
        assertEq(RL.tokenY.cummulativeEarnedPerMLiq, 2197219781195);                  // 10 + 2197219781185 = 2197219781195
        assertEq(RL.tokenY.subtreeCummulativeEarnedPerMLiq, 2197219781195);          // 10 + 2197219781185 = 2197219781195

        // RRL
        //           total_mLiq = 287728291 + (9082734 + 377 + 8430) * 2 = 305911373
        //
        //           earn_x      = 16463537718422861220174597 * 53e18 / 305911373 / 2**64 = 154626414974589533.957746783298485424790431468186321359344549
        //           earn_x_sub  = 16463537718422861220174597 * 754e18 / 305911373 / 2**64 = 2199779563978122803.85171838881241528852802503797143971595830
        //
        //           earn_y      = 3715979586694123491881712207 * 8765e6 / 305911373 / 2**64 = 5771781665.52844938596716448955303604219154769320799186650875
        //           earn_y_sub  = 3715979586694123491881712207 * 788296e6 / 305911373 / 2**64 = 519095539054.126016789546137872983468330339792397614050929992
        assertEq(RRL.tokenX.cummulativeEarnedPerMLiq, 154626415017241476);           // 42651943 + 154626414974589533 = 154626415017241476 (sol losses 1 wei)
        assertEq(RRL.tokenX.subtreeCummulativeEarnedPerMLiq, 2199779564584907057);  // 606784254 + 2199779563978122803 = 2199779564584907057
        assertEq(RRL.tokenY.cummulativeEarnedPerMLiq, 5771781665);                   // 0 + 5771781665 = 5771781665
        assertEq(RRL.tokenY.subtreeCummulativeEarnedPerMLiq, 519095539055);         // 1 + 519095539054 = 519095539055

        // RRLL
        //           total_mLiq = 287637599 + (45346 + 9082734 + 377 + 8430) * 1 = 296774486
        //
        //           earn_x      = 16463537718422861220174597 * 701e18 / 296774486 / 2**64 = 2108117905415037748.37451632639936795389368532390933657093156
        //           earn_x_sub  = 16463537718422861220174597 * 701e18 / 296774486 / 2**64 = 2108117905415037748.37451632639936795389368532390933657093156
        //
        //           earn_y      = 3715979586694123491881712207 * 779531e6 / 296774486 / 2**64 = 529127613134.050803777279185858502873428448836282593499892809
        //           earn_y_sub  = 3715979586694123491881712207 * 779531e6 / 296774486 / 2**64 = 529127613134.050803777279185858502873428448836282593499892809
        assertEq(RRLL.tokenX.cummulativeEarnedPerMLiq, 2108117905996538332);          // 581500584 + 2108117905415037748 = 2108117905996538332
        assertEq(RRLL.tokenX.subtreeCummulativeEarnedPerMLiq, 2108117905996538332);  // 581500584 + 2108117905415037748 = 2108117905996538332
        assertEq(RRLL.tokenY.cummulativeEarnedPerMLiq, 529127613135);                 // 1 + 529127613134 = 529127613135
        assertEq(RRLL.tokenY.subtreeCummulativeEarnedPerMLiq, 529127613135);         // 1 + 529127613134 = 529127613135

        // mLiq
        assertEq(root.mLiq, 8430);
        assertEq(R.mLiq, 377);
        assertEq(RR.mLiq, 9082734);
        assertEq(RL.mLiq, 1111);
        assertEq(RRL.mLiq, 45346);
        assertEq(RRLL.mLiq, 287634865);

        // subtreeMLiq
        assertEq(root.subtreeMLiq, 324198833);
        assertEq(R.subtreeMLiq, 324063953);
        assertEq(RR.subtreeMLiq, 324056493);
        assertEq(RL.subtreeMLiq, 4444);
        assertEq(RRL.subtreeMLiq, 287725557);
        assertEq(RRLL.subtreeMLiq, 287634865);

        // T9214298113
        liqTree.feeRateSnapshotTokenX.add(11381610389149375791104);   // 307% APR as Q192.64 T9214298113 - T2876298273
        liqTree.feeRateSnapshotTokenY.add(185394198934916215865344);  // 5000.7% APR as Q192.64 T9214298113 - T2876298273

        // Apply change that requires fee calculation
        // addTLiq
        liqTree.addTLiq(LiqRange(8, 12), 1000, 1000e18, 1000e6);  // RRLL, RL

        // root
        //           total_mLiq = 324198833
        //
        //           earn_x      = 11381610389149375791104 * 492e18 / 324198833 / 2**64  = 936348777891386.743735803607164207960477914490210395050990205
        //           earn_x_sub  = 11381610389149375791104 * 3033e18 / 324198833 / 2**64 = 5772247649074341.45071278931001837956123885091221164266189693
        //
        //           earn_y      = 185394198934916215865344 * 254858e6 / 324198833 / 2**64  = 7900657.61872699474175109887651599451346454839027751836478695
        //           earn_y_sub  = 185394198934916215865344 * 1143822e6 / 324198833 / 2**64 = 35458749.5733606501640098620374258523427949943453374491326438
        assertEq(root.tokenX.cummulativeEarnedPerMLiq, 1355310898622008714);          // 373601278 + 1354374549470516050 + 936348777891386 = 1355310898622008714
        assertEq(root.tokenX.subtreeCummulativeEarnedPerMLiq, 8354995844553968361);  // 2303115199 + 8349223594601778821 + 5772247649074341 = 8354995844553968361
        assertEq(root.tokenY.cummulativeEarnedPerMLiq, 158359374060);                 // 0 + 158351473403 + 7900657 = 158359374060
        assertEq(root.tokenY.subtreeCummulativeEarnedPerMLiq, 710728860612);         // 2 + 710693401861 + 35458749 = 710728860612

        // R
        //           total_mLiq = 324063953 + 8430 * 8 = 324131393
        //
        //           earn_x      = 11381610389149375791104 * 998e18 / 324131393 / 2**64  = 1899736810880077.58842507649572740061066261792173891653870132
        //           earn_x_sub  = 11381610389149375791104 * 2541e18 / 324131393 / 2**64 = 4836905046539355.86391595127819972440049470154222303299082171
        //
        //           earn_y      = 185394198934916215865344 * 353e6 / 324131393 / 2**64    = 10945.359436035932129843115196215424291564802240553108041589788249
        //           earn_y_sub  = 185394198934916215865344 * 888964e6 / 324131393 / 2**64 = 27563825.7951735024642318840149814403397354471925525584619938
        assertEq(R.tokenX.cummulativeEarnedPerMLiq, 2749759536746020654);          // 757991165 + 2747859799177149412 + 1899736810880077 = 2749759536746020654
        assertEq(R.tokenX.subtreeCummulativeEarnedPerMLiq, 7001141265402443371);  // 1929915382 + 6996304358425988634 + 4836905046539355 = 7001141265402443371
        assertEq(R.tokenY.cummulativeEarnedPerMLiq, 219386832);                    // 0 + 219375887 + 10945 = 219386832
        assertEq(R.tokenY.subtreeCummulativeEarnedPerMLiq, 552484409781);         // 1 + 552456845955 + 27563825 = 552484409781

        // RR
        //           total_mLiq = 324056493 + (377 + 8430) * 4 = 324091721
        //
        //           earn_x      = 11381610389149375791104 * 765e18 / 324091721 / 2**64  = 1456389336983247.97581853577374895245788594982344519686141566
        //           earn_x_sub  = 11381610389149375791104 * 1519e18 / 324091721 / 2**64 = 2891837127944514.60819392920303876965167157879975588762417044
        //
        //           earn_y      = 185394198934916215865344 * 99763e6 / 324091721 / 2**64  = 3093698.46401352576654665825318763474490453834363760251685046
        //           earn_y_sub  = 185394198934916215865344 * 888059e6 / 324091721 / 2**64 = 27539135.3934162733549879091613880669579421169863823827823111
        assertEq(RR.tokenX.cummulativeEarnedPerMLiq, 2108110694023652835);          // 581096415 + 2106654304105573173+ 1456389336983247 = 2108110694023652835
        assertEq(RR.tokenX.subtreeCummulativeEarnedPerMLiq, 4185908685257423082);  // 1153837196 + 4183016846975641372 + 2891837127944514 = 4185908685257423082
        assertEq(RR.tokenY.cummulativeEarnedPerMLiq, 62011632404);                  // 0 + 62008538706 + 3093698 = 62011632404
        assertEq(RR.tokenY.subtreeCummulativeEarnedPerMLiq, 552008141912);         // 1 + 551980602776 + 27539135 = 552008141912

        // RL
        //           total_mLiq = 4444 + (377 + 8430) * 4 = 39672
        //
        //           earn_x      = 11381610389149375791104 * 24e18 / 39672 / 2**64 = 373259731104033296.286645111573225645606473079249848759830611
        //           earn_x_sub  = 11381610389149375791104 * 24e18 / 39672 / 2**64 = 373259731104033296.286645111573225645606473079249848759830611
        //
        //           earn_y      = 185394198934916215865344 * 552e6 / 39672 / 2**64 = 139839995.304998697233270837982279275016069267997580157289776
        //           earn_y_sub  = 185394198934916215865344 * 552e6 / 39672 / 2**64 = 139839995.304998697233270837982279275016069267997580157289776
        assertEq(RL.tokenX.cummulativeEarnedPerMLiq, 423621837838722923425);          // 148929881804 + 423248577958689008325 + 373259731104033296 = 423621837838722923425
        assertEq(RL.tokenX.subtreeCummulativeEarnedPerMLiq, 423621837838722923425);  // 148929881804 + 423248577958689008325 + 373259731104033296 = 423621837838722923425
        assertEq(RL.tokenY.cummulativeEarnedPerMLiq, 2197359621190);                  // 10 + 2197219781185 + 139839995 = 2197359621190
        assertEq(RL.tokenY.subtreeCummulativeEarnedPerMLiq, 2197359621190);          // 10 + 2197219781185 + 139839995 = 2197359621190

        // RRL
        //           total_mLiq = 287725557 + (9082734 + 377 + 8430) * 2 = 305908639
        //
        //           earn_x      = 11381610389149375791104 * 53e18 / 305908639 / 2**64  = 106897640711262.335596794608928382455998365904272484439381916
        //           earn_x_sub  = 11381610389149375791104 * 754e18 / 305908639 / 2**64 = 1520770209363996.24603741764400000701552392248719723145837669
        //
        //           earn_y      = 185394198934916215865344 * 8765e6 / 305908639 / 2**64   = 287962.93864210284405202260308978443477406072046236000546555339354
        //           earn_y_sub  = 185394198934916215865344 * 788296e6 / 305908639 / 2**64 = 25898463.5116731435886860479093285465823905270619049107665115
        assertEq(RRL.tokenX.cummulativeEarnedPerMLiq, 154733312657952738);           // 42651943 + 154626414974589533 + 106897640711262 = 154733312657952738
        assertEq(RRL.tokenX.subtreeCummulativeEarnedPerMLiq, 2201300334794271053);  // 606784254 + 2199779563978122803 + 1520770209363996 = 2201300334794271053
        assertEq(RRL.tokenY.cummulativeEarnedPerMLiq, 5772069627);                   // 0 + 5771781665 + 287962 = 5772069627
        assertEq(RRL.tokenY.subtreeCummulativeEarnedPerMLiq, 519121437518);         // 1 + 519095539054 + 25898463 = 519121437518

        // RRLL
        //           total_mLiq = 287634865 + (45346 + 9082734 + 377 + 8430) * 1 = 296771752
        //
        //           earn_x      = 11381610389149375791104 * 701e18 / 296771752 / 2**64 = 1457402297493569.71876500861500730007660377831377967536479010
        //           earn_x_sub  = 11381610389149375791104 * 701e18 / 296771752 / 2**64 = 1457402297493569.71876500861500730007660377831377967536479010
        //
        //           earn_y      = 185394198934916215865344 * 779531e6 / 296771752 / 2**64 = 26398986.1622835510939886934876573358559478744206759947961624
        //           earn_y_sub  = 185394198934916215865344 * 779531e6 / 296771752 / 2**64 = 26398986.1622835510939886934876573358559478744206759947961624
        assertEq(RRLL.tokenX.cummulativeEarnedPerMLiq, 2109575308294031901);          // 581500584 + 2108117905415037748 + 1457402297493569 = 2109575308294031901
        assertEq(RRLL.tokenX.subtreeCummulativeEarnedPerMLiq, 2109575308294031901);  // 581500584 + 2108117905415037748 + 1457402297493569 = 2109575308294031901
        assertEq(RRLL.tokenY.cummulativeEarnedPerMLiq, 529154012121);                 // 1 + 529127613134 + 26398986 = 529154012121
        assertEq(RRLL.tokenY.subtreeCummulativeEarnedPerMLiq, 529154012121);         // 1 + 529127613134 + 26398986 = 529154012121

        // tLiq
        assertEq(root.tLiq, 4430);
        assertEq(R.tLiq, 77);
        assertEq(RR.tLiq, 82734);
        assertEq(RL.tLiq, 1111);
        assertEq(RRL.tLiq, 5346);
        assertEq(RRLL.tLiq, 7635865);

        // borrowed_x
        assertEq(root.tokenX.borrowed, 492e18);
        assertEq(R.tokenX.borrowed, 998e18);
        assertEq(RR.tokenX.borrowed, 765e18);
        assertEq(RL.tokenX.borrowed, 1024e18);
        assertEq(RRL.tokenX.borrowed, 53e18);
        assertEq(RRLL.tokenX.borrowed, 1701e18);

        // subtree_borrowed_x
        assertEq(root.tokenX.subtreeBorrowed, 5033e18);  // 492e18 + 998e18 + 765e18 + 53e18 + 701e18 + 24e18
        assertEq(R.tokenX.subtreeBorrowed, 4541e18);     // 998e18 + 765e18 + 53e18 + 701e18 + 24e18
        assertEq(RR.tokenX.subtreeBorrowed, 2519e18);    // 765e18 + 53e18 + 701e18
        assertEq(RL.tokenX.subtreeBorrowed, 1024e18);
        assertEq(RRL.tokenX.subtreeBorrowed, 1754e18);   // 53e18 + 701e18
        assertEq(RRLL.tokenX.subtreeBorrowed, 1701e18);  // 701e18

        // borrowed_y
        assertEq(root.tokenY.borrowed, 254858e6);
        assertEq(R.tokenY.borrowed, 353e6);
        assertEq(RR.tokenY.borrowed, 99763e6);
        assertEq(RL.tokenY.borrowed, 1552e6);
        assertEq(RRL.tokenY.borrowed, 8765e6);
        assertEq(RRLL.tokenY.borrowed, 780531e6);

        // subtree_borrowed_y
        assertEq(root.tokenY.subtreeBorrowed, 1145822e6);  // 254858e6 + 353e6 + 99763e6 + 8765e6 + 779531e6 + 552e6
        assertEq(R.tokenY.subtreeBorrowed, 890964e6);      // 353e6 + 99763e6 + 8765e6 + 779531e6 + 552e6
        assertEq(RR.tokenY.subtreeBorrowed, 889059e6);     // 99763e6 + 8765e6 + 779531e6
        assertEq(RL.tokenY.subtreeBorrowed, 1552e6);
        assertEq(RRL.tokenY.subtreeBorrowed, 789296e6);    // 8765e6 + 779531e6
        assertEq(RRLL.tokenY.subtreeBorrowed, 780531e6);   // 779531e6

        // T32876298273
        // 3.3) addTLiq
        liqTree.feeRateSnapshotTokenX.add(2352954287417905205553);  // 17% APR as Q192.64 T32876298273 - T9214298113
        liqTree.feeRateSnapshotTokenY.add(6117681147286553534438);  // 44.2% APR as Q192.64 T32876298273 - T9214298113

        // Apply change that requires fee calculation
        // removeTLiq
        liqTree.removeTLiq(LiqRange(8, 12), 1000, 1000e18, 1000e6);  // RRLL, RL

        // root
        //           total_mLiq = 324198833
        //
        //           earn_x      = 2352954287417905205553 * 492e18 / 324198833 / 2**64  = 193574177654021.169606366690127570750614868262308175138961180
        //           earn_x_sub  = 2352954287417905205553 * 5033e18 / 324198833 / 2**64 = 1980200886448553.95656269014514647070700128448007529567965776
        //
        //           earn_y      = 6117681147286553534438 * 254858e6 / 324198833 / 2**64  = 260707.74837037839600245251693715160678794344236990061534290681026
        //           earn_y_sub  = 6117681147286553534438 * 1145822e6 / 324198833 / 2**64 = 1172122.01952947804057287645615189999290967884478087508680692
        assertEq(root.tokenX.cummulativeEarnedPerMLiq, 1355504472799662735);         // 373601278 + 1354374549470516050 + 936348777891386 + 193574177654021 = 1355504472799662735
        assertEq(root.tokenX.subtreeCummulativeEarnedPerMLiq, 8356976045440416914); // 2303115199 + 8349223594601778821 + 5772247649074341 + 1980200886448553 = 8356976045440416914
        assertEq(root.tokenY.cummulativeEarnedPerMLiq, 158359634767);                // 0 + 158351473403 + 7900657 + 260707 = 158359634767
        assertEq(root.tokenY.subtreeCummulativeEarnedPerMLiq, 710730032734);        // 2 + 710693401861 + 35458749 + 1172122 = 710730032734

        // R
        //           total_mLiq = 324063953 + 8430 * 8 = 324131393
        //
        //           earn_x      = 2352954287417905205553 * 998e18 / 324131393 / 2**64  = 392738261220692.635199129066166314911263418663640357414414483
        //           earn_x_sub  = 2352954287417905205553 * 4541e18 / 324131393 / 2**64 = 1786998441085335.92829583676298721043291301017193473248382381
        //
        //           earn_y      = 6117681147286553534438 * 353e6 / 324131393 / 2**64    = 361.17753121077324707993230558447820693195086120933424789750836934
        //           earn_y_sub  = 6117681147286553534438 * 890964e6 / 324131393 / 2**64 = 911603.90344950531249667084054608793530005288132156736216361373026
        assertEq(R.tokenX.cummulativeEarnedPerMLiq, 2750152275007241346);          // 757991165 + 2747859799177149412 + 1899736810880077 + 392738261220692 = 2750152275007241346
        assertEq(R.tokenX.subtreeCummulativeEarnedPerMLiq, 7002928263843528706);  // 1929915382 + 6996304358425988634 + 4836905046539355 + 1786998441085335 = 7002928263843528706
        assertEq(R.tokenY.cummulativeEarnedPerMLiq, 219387193);                    // 0 + 219375887 + 10945 + 361 = 219387193
        assertEq(R.tokenY.subtreeCummulativeEarnedPerMLiq, 552485321384);         // 1 + 552456845955 + 27563825 + 911603 = 552485321384

        // RR
        //           total_mLiq = 324056493 + (377 + 8430) * 4 = 324091721
        //
        //           earn_x      = 2352954287417905205553 * 765e18 / 324091721 / 2**64  = 301083714644757.116282263044928314612316183509300881282164628
        //           earn_x_sub  = 2352954287417905205553 * 2519e18 / 324091721 / 2**64 = 991411604170121.798581726287809705239770544130626039150029671
        //
        //           earn_y      = 6117681147286553534438 * 99763e6 / 324091721 / 2**64  = 102086.58565055261555338276382365173781133864709615634713615821960
        //           earn_y_sub  = 6117681147286553534438 * 889059e6 / 324091721 / 2**64 = 909766.12323100405793004346924503062625232727813579850073199172604
        assertEq(RR.tokenX.cummulativeEarnedPerMLiq, 2108411777738297592);          // 581096415 + 2106654304105573173+ 1456389336983247 + 301083714644757 = 2108411777738297592
        assertEq(RR.tokenX.subtreeCummulativeEarnedPerMLiq, 4186900096861593203);  // 1153837196 + 4183016846975641372 + 2891837127944514 + 991411604170121 = 4186900096861593203
        assertEq(RR.tokenY.cummulativeEarnedPerMLiq, 62011734490);                  // 0 + 62008538706 + 3093698 + 102086 = 62011734490
        assertEq(RR.tokenY.subtreeCummulativeEarnedPerMLiq, 552009051678);         // 1 + 551980602776 + 27539135 + 909766 = 552009051678

        // RL
        //           total_mLiq = 4444 + (377 + 8430) * 4 = 39672
        //
        //           earn_x      = 2352954287417905205553 * 1024e18 / 39672 / 2**64 = 3292377527956539412.11877691362144195603424231355578266196876
        //           earn_x_sub  = 2352954287417905205553 * 1024e18 / 39672 / 2**64 = 3292377527956539412.11877691362144195603424231355578266196876
        //
        //           earn_y      = 6117681147286553534438 * 1552e6 / 39672 / 2**64 = 12974025.1961037381208809794236997935340918048320067315891063
        //           earn_y_sub  = 6117681147286553534438 * 1552e6 / 39672 / 2**64 = 12974025.1961037381208809794236997935340918048320067315891063
        assertEq(RL.tokenX.cummulativeEarnedPerMLiq, 426914215366679462837);          // 148929881804 + 423248577958689008325 + 373259731104033296 + 3292377527956539412 = 426914215366679462837
        assertEq(RL.tokenX.subtreeCummulativeEarnedPerMLiq, 426914215366679462837);  // 148929881804 + 423248577958689008325 + 373259731104033296 + 3292377527956539412 = 426914215366679462837
        assertEq(RL.tokenY.cummulativeEarnedPerMLiq, 2197372595215);                  // 10 + 2197219781185 + 139839995 + 12974025 = 2197372595215
        assertEq(RL.tokenY.subtreeCummulativeEarnedPerMLiq, 2197372595215);          // 10 + 2197219781185 + 139839995 + 12974025 = 2197372595215

        // RRL
        //           total_mLiq = 287725557 + (9082734 + 377 + 8430) * 2 = 305908639
        //
        //           earn_x      = 2352954287417905205553 * 53e18 / 305908639 / 2**64   = 22099268330799.1616184419285239088656103478160451926038962236
        //           earn_x_sub  = 2352954287417905205553 * 1754e18 / 305908639 / 2**64 = 731360691551353.386391455521338417929821699421571091079886346
        //
        //           earn_y      = 6117681147286553534438 * 8765e6 / 305908639 / 2**64   = 9502.2684149166432853337655386227368949210477797554902569919214852
        //           earn_y_sub  = 6117681147286553534438 * 789296e6 / 305908639 / 2**64 = 855687.67265488270148782656070425233773115839456587443672363898010
        assertEq(RRL.tokenX.cummulativeEarnedPerMLiq, 154755411926283537);           // 42651943 + 154626414974589533 + 106897640711262 + 22099268330799 = 154755411926283537
        assertEq(RRL.tokenX.subtreeCummulativeEarnedPerMLiq, 2202031695485822406);  // 606784254 + 2199779563978122803 + 1520770209363996 + 731360691551353 = 2202031695485822406
        assertEq(RRL.tokenY.cummulativeEarnedPerMLiq, 5772079129);                   // 0 + 5771781665 + 287962 + 9502 = 5772079129
        assertEq(RRL.tokenY.subtreeCummulativeEarnedPerMLiq, 519122293205);         // 1 + 519095539054 + 25898463 + 855687 = 519122293205

        // RRLL
        //           total_mLiq = 287634865 + (45346 + 9082734 + 377 + 8430) * 1 = 296771752
        //
        //           earn_x      = 2352954287417905205553 * 1701e18 / 296771752 / 2**64 = 731097873063750.150068233826063023165648387512288880115659770
        //           earn_x_sub  = 2352954287417905205553 * 1701e18 / 296771752 / 2**64 = 731097873063750.150068233826063023165648387512288880115659770
        //
        //           earn_y      = 6117681147286553534438 * 780531e6 / 296771752 / 2**64 = 872237.41346080959306032387265895687662997868016869971844802082307
        //           earn_y_sub  = 6117681147286553534438 * 780531e6 / 296771752 / 2**64 = 872237.41346080959306032387265895687662997868016869971844802082307
        assertEq(RRLL.tokenX.cummulativeEarnedPerMLiq, 2110306406167095651);          // 581500584 + 2108117905415037748 + 1457402297493569 + 731097873063750 = 2110306406167095651
        assertEq(RRLL.tokenX.subtreeCummulativeEarnedPerMLiq, 2110306406167095651);  // 581500584 + 2108117905415037748 + 1457402297493569 + 731097873063750 = 2110306406167095651
        assertEq(RRLL.tokenY.cummulativeEarnedPerMLiq, 529154884358);                 // 1 + 529127613134 + 26398986 + 872237 = 529154884358
        assertEq(RRLL.tokenY.subtreeCummulativeEarnedPerMLiq, 529154884358);         // 1 + 529127613134 + 26398986 + 872237 = 529154884358

        // tLiq
        assertEq(root.tLiq, 4430);
        assertEq(R.tLiq, 77);
        assertEq(RR.tLiq, 82734);
        assertEq(RL.tLiq, 111);
        assertEq(RRL.tLiq, 5346);
        assertEq(RRLL.tLiq, 7634865);

        // subtreeMLiq
        assertEq(root.subtreeMLiq, 324198833);  // 8430*16 + 377*8 + 9082734*4 + 1111*4 + 45346*2 + 287634865*1
        assertEq(R.subtreeMLiq, 324063953);     // 377*8 + 9082734*4 + 1111*4 + 45346*2 + 287634865*1
        assertEq(RR.subtreeMLiq, 324056493);    // 9082734*4 + 45346*2 + 287634865*1
        assertEq(RL.subtreeMLiq, 4444);         // 1111*4
        assertEq(RRL.subtreeMLiq, 287725557);   // 45346*2 + 287634865*1
        assertEq(RRLL.subtreeMLiq, 287634865);  // 287634865*1

        // borrowed_x
        assertEq(root.tokenX.borrowed, 492e18);
        assertEq(R.tokenX.borrowed, 998e18);
        assertEq(RR.tokenX.borrowed, 765e18);
        assertEq(RL.tokenX.borrowed, 24e18);
        assertEq(RRL.tokenX.borrowed, 53e18);
        assertEq(RRLL.tokenX.borrowed, 701e18);

        // subtree_borrowed_x
        assertEq(root.tokenX.subtreeBorrowed, 3033e18);  // 492e18 + 998e18 + 765e18 + 53e18 + 701e18 + 24e18
        assertEq(R.tokenX.subtreeBorrowed, 2541e18);     // 998e18 + 765e18 + 53e18 + 701e18 + 24e18
        assertEq(RR.tokenX.subtreeBorrowed, 1519e18);    // 765e18 + 53e18 + 701e18
        assertEq(RL.tokenX.subtreeBorrowed, 24e18);
        assertEq(RRL.tokenX.subtreeBorrowed, 754e18);   // 53e18 + 701e18
        assertEq(RRLL.tokenX.subtreeBorrowed, 701e18);  // 701e18

        // borrowed_y
        assertEq(root.tokenY.borrowed, 254858e6);
        assertEq(R.tokenY.borrowed, 353e6);
        assertEq(RR.tokenY.borrowed, 99763e6);
        assertEq(RL.tokenY.borrowed, 552e6);
        assertEq(RRL.tokenY.borrowed, 8765e6);
        assertEq(RRLL.tokenY.borrowed, 779531e6);

        // subtree_borrowed_y
        assertEq(root.tokenY.subtreeBorrowed, 1143822e6);  // 254858e6 + 353e6 + 99763e6 + 8765e6 + 779531e6 + 552e6
        assertEq(R.tokenY.subtreeBorrowed, 888964e6);      // 353e6 + 99763e6 + 8765e6 + 779531e6 + 552e6
        assertEq(RR.tokenY.subtreeBorrowed, 888059e6);     // 99763e6 + 8765e6 + 779531e6
        assertEq(RL.tokenY.subtreeBorrowed, 552e6);
        assertEq(RRL.tokenY.subtreeBorrowed, 788296e6);    // 8765e6 + 779531e6
        assertEq(RRLL.tokenY.subtreeBorrowed, 779531e6);   // 779531e6
    }

    // BELOW WAS BEFORE PYTHON

/*


    // function testRightLegOnly() public {
    //     LiqNode storage root = liqTree.nodes[liqTree.root];
    //     LiqNode storage R = liqTree.nodes[_nodeKey(1, 1, liqTree.offset)];
    //     LiqNode storage RR = liqTree.nodes[_nodeKey(2, 3, liqTree.offset)];
    //     LiqNode storage RL = liqTree.nodes[_nodeKey(2, 2, liqTree.offset)];
    //     LiqNode storage RRL = liqTree.nodes[_nodeKey(3, 6, liqTree.offset)];
    //     LiqNode storage RRLL = liqTree.nodes[_nodeKey(4, 12, liqTree.offset)];

    //     // Step 1); Allocate different mLiq + tLiq values for each node
    //     vm.warp(0); // T0

    //     liqTree.addInfRangeMLiq(8430);                // root   (INF);
    //     liqTree.addMLiq(LiqRange(8, 15), 377);        // R     (8-15);
    //     liqTree.addMLiq(LiqRange(12, 15), 9082734);   // RR   (12-15);
    //     liqTree.addMLiq(LiqRange(8, 11), 1111);       // RL    (8-11);
    //     liqTree.addMLiq(LiqRange(12, 13), 45346);     // RRL  (12-13);
    //     liqTree.addMLiq(LiqRange(12, 12), 287634865); // RRLL    (12);

    //     liqTree.addInfRangeTLiq(4430, 492e18, 254858e6);              // root
    //     liqTree.addTLiq(LiqRange(8, 15), 77, 998e18, 353e6);          // R 
    //     liqTree.addTLiq(LiqRange(12, 15), 82734, 765e18, 99763e6);    // RR
    //     liqTree.addTLiq(LiqRange(8, 11), 111, 24e18, 552e6);          // RL
    //     liqTree.addTLiq(LiqRange(12, 13), 5346, 53e18, 8765e6);       // RRL
    //     liqTree.addTLiq(LiqRange(12, 12), 7634865, 701e18, 779531e6); // RRLL

    //     // mLiq
    //     assertEq(root.mLiq, 8430);
    //     assertEq(R.mLiq, 377);
    //     assertEq(RR.mLiq, 9082734);
    //     assertEq(RL.mLiq, 1111);
    //     assertEq(RRL.mLiq, 45346);
    //     assertEq(RRLL.mLiq, 287634865);

    //     // tLiq
    //     assertEq(root.tLiq, 4430);
    //     assertEq(R.tLiq, 77);
    //     assertEq(RR.tLiq, 82734);
    //     assertEq(RL.tLiq, 111);
    //     assertEq(RRL.tLiq, 5346);
    //     assertEq(RRLL.tLiq, 7634865);

    //     // subtreeMLiq
    //     assertEq(root.subtreeMLiq, 324198833); // 8430*16 + 377*8 + 9082734*4 + 1111*4 + 45346*2 + 287634865*1
    //     assertEq(R.subtreeMLiq, 324063953);    // 377*8 + 9082734*4 + 1111*4 + 45346*2 + 287634865*1
    //     assertEq(RR.subtreeMLiq, 324056493);   // 9082734*4 + 45346*2 + 287634865*1
    //     assertEq(RL.subtreeMLiq, 4444);        // 1111*4
    //     assertEq(RRL.subtreeMLiq, 287725557);  // 45346*2 + 287634865*1
    //     assertEq(RRLL.subtreeMLiq, 287634865); // 287634865*1

    //     // borrowedX
    //     assertEq(root.tokenX.borrowed, 492e18);
    //     assertEq(R.tokenX.borrowed, 998e18);
    //     assertEq(RR.tokenX.borrowed, 765e18);
    //     assertEq(RL.tokenX.borrowed, 24e18);
    //     assertEq(RRL.tokenX.borrowed, 53e18);
    //     assertEq(RRLL.tokenX.borrowed, 701e18);
 
    //     // borrowedY
    //     assertEq(root.tokenY.borrowed, 254858e6);
    //     assertEq(R.tokenY.borrowed, 353e6);
    //     assertEq(RR.tokenY.borrowed, 99763e6);
    //     assertEq(RL.tokenY.borrowed, 552e6);
    //     assertEq(RRL.tokenY.borrowed, 8765e6);
    //     assertEq(RRLL.tokenY.borrowed, 779531e6);

    //     // subtreeBorrowedX
    //     assertEq(root.tokenX.subtreeBorrowed, 3033e18); // 492e18 + 998e18 + 765e18 + 53e18 + 701e18 + 24e18
    //     assertEq(R.tokenX.subtreeBorrowed, 2541e18);    // 998e18 + 765e18 + 53e18 + 701e18 + 24e18
    //     assertEq(RR.tokenX.subtreeBorrowed, 1519e18);   // 765e18 + 53e18 + 701e18
    //     assertEq(RL.tokenX.subtreeBorrowed, 24e18);
    //     assertEq(RRL.tokenX.subtreeBorrowed, 754e18);   // 53e18 + 701e18
    //     assertEq(RRLL.tokenX.subtreeBorrowed, 701e18);  // 701e18

    //     // subtreeBorrowedY
    //     assertEq(root.tokenY.subtreeBorrowed, 1143822e6); // 254858e6 + 353e6 + 99763e6 + 8765e6 + 779531e6 + 552e6
    //     assertEq(R.tokenY.subtreeBorrowed, 888964e6);     // 353e6 + 99763e6 + 8765e6 + 779531e6 + 552e6
    //     assertEq(RR.tokenY.subtreeBorrowed, 888059e6);    // 99763e6 + 8765e6 + 779531e6
    //     assertEq(RL.tokenY.subtreeBorrowed, 552e6);
    //     assertEq(RRL.tokenY.subtreeBorrowed, 788296e6);   // 8765e6 + 779531e6
    //     assertEq(RRLL.tokenY.subtreeBorrowed, 779531e6);  // 779531e6

    //     // Step 2); Assign different rates for X & Y
    //     vm.warp(98273); // T98273
    //     liqTree.feeRateSnapshotTokenX.add(4541239648278065);  // 7.9% APR as Q192.64 T98273 - T0
    //     liqTree.feeRateSnapshotTokenY.add(13278814667749784); // 23.1% APR as Q192.64 T98273 - T0

    //     // Step 3); Apply change that effects the entire tree, to calculate the fees at each node
    //     // 3.1); addMLiq
    //     liqTree.addMLiq(LiqRange(8, 12), 2734); // RRLL, RL

    //     // root
    //     assertEq(root.tokenX.cummulativeEarnedPerMLiq, 373601278);
    //     assertEq(root.tokenX.subtreeCummulativeEarnedPerMLiq, 2303115199);
    //     assertEq(root.tokenY.cummulativeEarnedPerMLiq, 0);
    //     assertEq(root.tokenY.subtreeCummulativeEarnedPerMLiq, 2);

    //     // R
    //     assertEq(R.tokenX.cummulativeEarnedPerMLiq, 757991165);
    //     assertEq(R.tokenX.subtreeCummulativeEarnedPerMLiq, 1929915382);
    //     assertEq(R.tokenY.cummulativeEarnedPerMLiq, 0);
    //     assertEq(R.tokenY.subtreeCummulativeEarnedPerMLiq, 1);

    //     // RR
    //     assertEq(RR.tokenX.cummulativeEarnedPerMLiq, 581096415);
    //     assertEq(RR.tokenX.subtreeCummulativeEarnedPerMLiq, 1153837196);
    //     assertEq(RR.tokenY.cummulativeEarnedPerMLiq, 0);
    //     assertEq(RR.tokenY.subtreeCummulativeEarnedPerMLiq, 1);

    //     // RL
    //     assertEq(RL.tokenX.cummulativeEarnedPerMLiq, 148929881804);
    //     assertEq(RL.tokenX.subtreeCummulativeEarnedPerMLiq, 148929881804);
    //     assertEq(RL.tokenY.cummulativeEarnedPerMLiq, 10);
    //     assertEq(RL.tokenY.subtreeCummulativeEarnedPerMLiq, 10);

    //     // RRL
    //     assertEq(RRL.tokenX.cummulativeEarnedPerMLiq, 42651943);
    //     assertEq(RRL.tokenX.subtreeCummulativeEarnedPerMLiq, 606784254);
    //     assertEq(RRL.tokenY.cummulativeEarnedPerMLiq, 0);
    //     assertEq(RRL.tokenY.subtreeCummulativeEarnedPerMLiq, 1);

    //     // RRLL
    //     assertEq(RRLL.tokenX.cummulativeEarnedPerMLiq, 581500584);
    //     assertEq(RRLL.tokenX.subtreeCummulativeEarnedPerMLiq, 581500584);
    //     assertEq(RRLL.tokenY.cummulativeEarnedPerMLiq, 1);
    //     assertEq(RRLL.tokenY.subtreeCummulativeEarnedPerMLiq, 1);

    //     // mLiq
    //     assertEq(root.mLiq, 8430);
    //     assertEq(R.mLiq, 377);
    //     assertEq(RR.mLiq, 9082734);
    //     assertEq(RL.mLiq, 3845);
    //     assertEq(RRL.mLiq, 45346);
    //     assertEq(RRLL.mLiq, 287637599);

    //     // subtreeMLiq
    //     assertEq(root.subtreeMLiq, 324212503); // 8430*16 + 377*8 + 9082734*4 + 3845*4 + 45346*2 + 287637599*1
    //     assertEq(R.subtreeMLiq, 324077623);    // 377*8 + 9082734*4 + 3845*4 + 45346*2 + 287637599*1
    //     assertEq(RR.subtreeMLiq, 324059227);   // 9082734*4 + 45346*2 + 287637599*1
    //     assertEq(RL.subtreeMLiq, 15380);       // 3845*4
    //     assertEq(RRL.subtreeMLiq, 287728291);  // 45346*2 + 287637599*1
    //     assertEq(RRLL.subtreeMLiq, 287637599); // 287637599*1

    //     // 3.2); removeMLiq
    //     vm.warp(2876298273); // T2876298273
    //     liqTree.feeRateSnapshotTokenX.add(16463537718422861220174597);   // 978567.9% APR as Q192.64 T2876298273 - T98273
    //     liqTree.feeRateSnapshotTokenY.add(3715979586694123491881712207); // 220872233.1% APR as Q192.64 T2876298273 - T98273

    //     liqTree.removeMLiq(LiqRange(8, 12), 2734); // RRLL, RL

    //     // root
    //     assertEq(root.tokenX.cummulativeEarnedPerMLiq, 373601278 + 1354374549470516050);         // 1354374549844117328
    //     assertEq(root.tokenX.subtreeCummulativeEarnedPerMLiq, 2303115199 + 8349223594601778821); // 8349223596904894020
    //     assertEq(root.tokenY.cummulativeEarnedPerMLiq, 0 + 158351473403);                        // 158351473403
    //     assertEq(root.tokenY.subtreeCummulativeEarnedPerMLiq, 2 + 710693401861);                 // 710693401863

    //     // R
    //     assertEq(R.tokenX.cummulativeEarnedPerMLiq, 757991165 + 2747859799177149412);         // 2747859799935140577
    //     assertEq(R.tokenX.subtreeCummulativeEarnedPerMLiq, 1929915382 + 6996304358425988634); // 6996304360355904016
    //     assertEq(R.tokenY.cummulativeEarnedPerMLiq, 0 + 219375887);                           // 219375887
    //     assertEq(R.tokenY.subtreeCummulativeEarnedPerMLiq, 1 + 552456845955);                 // 552456845956

    //     // RR
    //     assertEq(RR.tokenX.cummulativeEarnedPerMLiq, 581096415 + 2106654304105573173);         // 2106654304686669588
    //     assertEq(RR.tokenX.subtreeCummulativeEarnedPerMLiq, 1153837196 + 4183016846975641372); // 4183016848129478568
    //     assertEq(RR.tokenY.cummulativeEarnedPerMLiq, 0 + 62008538706);                         // 62008538706
    //     assertEq(RR.tokenY.subtreeCummulativeEarnedPerMLiq, 1 + 551980602776);                 // 551980602777

    //     // RL
    //     assertEq(RL.tokenX.cummulativeEarnedPerMLiq, 148929881804 + 423248577958689008325);        // 423248578107618890129
    //     assertEq(RL.tokenX.subtreeCummulativeEarnedPerMLiq, 148929881804 + 423248577958689008325); // 423248578107618890129
    //     assertEq(RL.tokenY.cummulativeEarnedPerMLiq, 10 + 2197219781185);                          // 2197219781195
    //     assertEq(RL.tokenY.subtreeCummulativeEarnedPerMLiq, 10 + 2197219781185);                   // 2197219781195

    //     // RRL
    //     assertEq(RRL.tokenX.cummulativeEarnedPerMLiq, 42651943 + 154626414974589533);          // 154626415017241476
    //     assertEq(RRL.tokenX.subtreeCummulativeEarnedPerMLiq, 606784254 + 2199779563978122803); // 2199779564584907057
    //     assertEq(RRL.tokenY.cummulativeEarnedPerMLiq, 0 + 5771781665);                         // 5771781665
    //     assertEq(RRL.tokenY.subtreeCummulativeEarnedPerMLiq, 1 + 519095539054);                // 519095539055

    //     // RRLL
    //     assertEq(RRLL.tokenX.cummulativeEarnedPerMLiq, 581500584 + 2108117905415037748);         // 2108117905996538332
    //     assertEq(RRLL.tokenX.subtreeCummulativeEarnedPerMLiq, 581500584 + 2108117905415037748);  // 2108117905996538332
    //     assertEq(RRLL.tokenY.cummulativeEarnedPerMLiq, 1 + 529127613134);                        // 529127613135
    //     assertEq(RRLL.tokenY.subtreeCummulativeEarnedPerMLiq, 1 + 529127613134);                 // 529127613135
        
    //     // mLiq
    //     assertEq(root.mLiq, 8430);
    //     assertEq(R.mLiq, 377);
    //     assertEq(RR.mLiq, 9082734);
    //     assertEq(RL.mLiq, 1111);
    //     assertEq(RRL.mLiq, 45346);
    //     assertEq(RRLL.mLiq, 287634865);

    //     // subtreeMLiq
    //     assertEq(root.subtreeMLiq, 324198833); // 8430*16 + 377*8 + 9082734*4 + 1111*4 + 45346*2 + 287634865*1
    //     assertEq(R.subtreeMLiq, 324063953);    // 377*8 + 9082734*4 + 1111*4 + 45346*2 + 287634865*1
    //     assertEq(RR.subtreeMLiq, 324056493);   // 9082734*4 + 45346*2 + 287634865*1
    //     assertEq(RL.subtreeMLiq, 4444);        // 1111*4
    //     assertEq(RRL.subtreeMLiq, 287725557);  // 45346*2 + 287634865*1
    //     assertEq(RRLL.subtreeMLiq, 287634865); // 287634865*1

    //     // 3.3); addTLiq
    //     vm.warp(9214298113); // T2876298273
    //     liqTree.feeRateSnapshotTokenX.add(11381610389149375791104);   // 307% APR as Q192.64 T9214298113 - T2876298273
    //     liqTree.feeRateSnapshotTokenY.add(185394198934916215865344);  // 5000.7% APR as Q192.64 T9214298113 - T2876298273

    //     liqTree.addTLiq(LiqRange(8, 12), 1000, 1000e18, 1000e6); // RRLL, RL

    //     // root
    //     assertEq(root.tokenX.cummulativeEarnedPerMLiq, 1354374549844117328 + 936348777891386);         // 1355310898622008714
    //     assertEq(root.tokenX.subtreeCummulativeEarnedPerMLiq, 8349223596904894020 + 5772247649074341); // 8354995844553968361
    //     assertEq(root.tokenY.cummulativeEarnedPerMLiq, 158351473403 + 7900657);                        // 158359374060
    //     assertEq(root.tokenY.subtreeCummulativeEarnedPerMLiq, 710693401863 + 35458749);                // 710728860612

    //     // R
    //     assertEq(R.tokenX.cummulativeEarnedPerMLiq, 2747859799935140577 + 1899736810880077);        // 2749759536746020654
    //     assertEq(R.tokenX.subtreeCummulativeEarnedPerMLiq, 6996304360355904016 + 4836905046539355); // 7001141265402443371
    //     assertEq(R.tokenY.cummulativeEarnedPerMLiq, 219375887 + 10945);                             // 219386832
    //     assertEq(R.tokenY.subtreeCummulativeEarnedPerMLiq, 552456845956 + 27563825);                // 552484409781

    //     // RR
    //     assertEq(RR.tokenX.cummulativeEarnedPerMLiq, 2106654304686669588 + 1456389336983247);        // 2108110694023652835
    //     assertEq(RR.tokenX.subtreeCummulativeEarnedPerMLiq, 4183016848129478568 + 2891837127944514); // 4185908685257423082
    //     assertEq(RR.tokenY.cummulativeEarnedPerMLiq, 62008538706 + 3093698);                         // 62011632404
    //     assertEq(RR.tokenY.subtreeCummulativeEarnedPerMLiq, 551980602777 + 27539135);                // 552008141912

    //     // RL
    //     assertEq(RL.tokenX.cummulativeEarnedPerMLiq, 423248578107618890129 + 373259731104033296);        // 423621837838722923425
    //     assertEq(RL.tokenX.subtreeCummulativeEarnedPerMLiq, 423248578107618890129 + 373259731104033296); // 423621837838722923425
    //     assertEq(RL.tokenY.cummulativeEarnedPerMLiq, 2197219781195 + 139839995);                         // 2197359621190
    //     assertEq(RL.tokenY.subtreeCummulativeEarnedPerMLiq, 2197219781195 + 139839995);                  // 2197359621190

    //     // RRL
    //     assertEq(RRL.tokenX.cummulativeEarnedPerMLiq, 154626415017241476 + 106897640711262);          // 154733312657952738
    //     assertEq(RRL.tokenX.subtreeCummulativeEarnedPerMLiq, 2199779564584907057 + 1520770209363996); // 2201300334794271053
    //     assertEq(RRL.tokenY.cummulativeEarnedPerMLiq, 5771781665 + 287962);                           // 5772069627
    //     assertEq(RRL.tokenY.subtreeCummulativeEarnedPerMLiq, 519095539055 + 25898463);                // 519121437518

    //     // RRLL
    //     assertEq(RRLL.tokenX.cummulativeEarnedPerMLiq, 2108117905996538332 + 1457402297493569);        // 2109575308294031901
    //     assertEq(RRLL.tokenX.subtreeCummulativeEarnedPerMLiq, 2108117905996538332 + 1457402297493569); // 2109575308294031901
    //     assertEq(RRLL.tokenY.cummulativeEarnedPerMLiq, 529127613135 + 26398986);                       // 529154012121
    //     assertEq(RRLL.tokenY.subtreeCummulativeEarnedPerMLiq, 529127613135 + 26398986);                // 529154012121

    //     // tLiq
    //     assertEq(root.tLiq, 4430);
    //     assertEq(R.tLiq, 77);
    //     assertEq(RR.tLiq, 82734);
    //     assertEq(RL.tLiq, 1111);
    //     assertEq(RRL.tLiq, 5346);
    //     assertEq(RRLL.tLiq, 7635865);

    //     // borrowedX
    //     assertEq(root.tokenX.borrowed, 492e18);
    //     assertEq(R.tokenX.borrowed, 998e18);
    //     assertEq(RR.tokenX.borrowed, 765e18);
    //     assertEq(RL.tokenX.borrowed, 1024e18);
    //     assertEq(RRL.tokenX.borrowed, 53e18);
    //     assertEq(RRLL.tokenX.borrowed, 1701e18);

    //     // borrowedY
    //     assertEq(root.tokenY.borrowed, 254858e6);
    //     assertEq(R.tokenY.borrowed, 353e6);
    //     assertEq(RR.tokenY.borrowed, 99763e6);
    //     assertEq(RL.tokenY.borrowed, 1552e6);
    //     assertEq(RRL.tokenY.borrowed, 8765e6);
    //     assertEq(RRLL.tokenY.borrowed, 780531e6);

    //     // subtreeBorrowedX
    //     assertEq(root.tokenX.subtreeBorrowed, 5033e18);  // 492e18 + 998e18 + 765e18 + 53e18 + 701e18 + 24e18
    //     assertEq(R.tokenX.subtreeBorrowed, 4541e18);     // 998e18 + 765e18 + 53e18 + 701e18 + 24e18
    //     assertEq(RR.tokenX.subtreeBorrowed, 2519e18);    // 765e18 + 53e18 + 701e18
    //     assertEq(RL.tokenX.subtreeBorrowed, 1024e18);
    //     assertEq(RRL.tokenX.subtreeBorrowed, 1754e18);   // 53e18 + 701e18
    //     assertEq(RRLL.tokenX.subtreeBorrowed, 1701e18);  // 701e18

    //     // subtreeBorrowedY
    //     assertEq(root.tokenY.subtreeBorrowed, 1145822e6); // 254858e6 + 353e6 + 99763e6 + 8765e6 + 779531e6 + 552e6
    //     assertEq(R.tokenY.subtreeBorrowed, 890964e6);     // 353e6 + 99763e6 + 8765e6 + 779531e6 + 552e6
    //     assertEq(RR.tokenY.subtreeBorrowed, 889059e6);    // 99763e6 + 8765e6 + 779531e6
    //     assertEq(RL.tokenY.subtreeBorrowed, 1552e6);
    //     assertEq(RRL.tokenY.subtreeBorrowed, 789296e6);   // 8765e6 + 779531e6
    //     assertEq(RRLL.tokenY.subtreeBorrowed, 780531e6);  // 779531e6

    //     // 3.4); removeTLiq
    //     // 3.3); addTLiq
    //     vm.warp(32876298273); // T32876298273
    //     liqTree.feeRateSnapshotTokenX.add(2352954287417905205553); // 17% APR as Q192.64 T32876298273 - T9214298113
    //     liqTree.feeRateSnapshotTokenY.add(6117681147286553534438); // 44.2% APR as Q192.64 T32876298273 - T9214298113

    //     liqTree.removeTLiq(LiqRange(8, 12), 1000, 1000e18, 1000e6); // RRLL, RL

    //     // root
    //     // A = 0
    //     // m = 324198833
    //     //     x: 492e18 * 2352954287417905205553 / 324198833 / 2**64
    //     // x sub: 5033e18 * 2352954287417905205553 / 324198833 / 2**64
    //     //     y: 254858e6 * 6117681147286553534438 / 324198833 / 2**64
    //     // y sub: 1145822e6 * 6117681147286553534438 / 324198833 / 2**64
    //     assertEq(root.tokenX.cummulativeEarnedPerMLiq, 1355310898622008714 + 193574177654021);
    //     assertEq(root.tokenX.subtreeCummulativeEarnedPerMLiq, 8354995844553968361 + 1980200886448553);
    //     assertEq(root.tokenY.cummulativeEarnedPerMLiq, 158359374060 + 260707);
    //     assertEq(root.tokenY.subtreeCummulativeEarnedPerMLiq, 710728860612 + 1172122);

    //     // R
    //     // 998e18 * 2352954287417905205553 / 324131393 / 2**64
    //     // 4541e18 * 2352954287417905205553 / 324131393 / 2**64
    //     // 353e6 * 6117681147286553534438 / 324131393 / 2**64
    //     // 890964e6 * 6117681147286553534438 / 324131393 / 2**64
    //     assertEq(R.tokenX.cummulativeEarnedPerMLiq, 2749759536746020654 + 392738261220692);
    //     assertEq(R.tokenX.subtreeCummulativeEarnedPerMLiq, 7001141265402443371 + 1786998441085335);
    //     assertEq(R.tokenY.cummulativeEarnedPerMLiq, 219386832 + 361);
    //     assertEq(R.tokenY.subtreeCummulativeEarnedPerMLiq, 552484409781 + 911603);

    //     // RR
    //     // 765e18 * 2352954287417905205553 / 324091721 / 2**64
    //     // 2519e18 * 2352954287417905205553 / 324091721 / 2**64
    //     // 99763e6 * 6117681147286553534438 / 324091721 / 2**64
    //     // 889059e6 * 6117681147286553534438 / 324091721 / 2**64
    //     assertEq(RR.tokenX.cummulativeEarnedPerMLiq, 2108110694023652835 + 301083714644757);
    //     assertEq(RR.tokenX.subtreeCummulativeEarnedPerMLiq, 4185908685257423082 + 991411604170121);
    //     assertEq(RR.tokenY.cummulativeEarnedPerMLiq, 62011632404 + 102086);
    //     assertEq(RR.tokenY.subtreeCummulativeEarnedPerMLiq, 552008141912 + 909766);

    //     // RL
    //     // 1024e18 * 2352954287417905205553 / 39672 / 2**64
    //     // 1024e18 * 2352954287417905205553 / 39672 / 2**64
    //     // 1552e6 * 6117681147286553534438 / 39672 / 2**64
    //     // 1552e6 * 6117681147286553534438 / 39672 / 2**64
    //     assertEq(RL.tokenX.cummulativeEarnedPerMLiq, 423621837838722923425 + 3292377527956539412);
    //     assertEq(RL.tokenX.subtreeCummulativeEarnedPerMLiq, 423621837838722923425 + 3292377527956539412);
    //     assertEq(RL.tokenY.cummulativeEarnedPerMLiq, 2197359621190 + 12974025);
    //     assertEq(RL.tokenY.subtreeCummulativeEarnedPerMLiq, 2197359621190 + 12974025);

    //     // RRL
    //     // 53e18 * 2352954287417905205553 / 305908639 / 2**64
    //     // 1754e18 * 2352954287417905205553 / 305908639 / 2**64
    //     // 8765e6 * 6117681147286553534438 / 305908639 / 2**64
    //     // 789296e6 * 6117681147286553534438 / 305908639 / 2**64
    //     assertEq(RRL.tokenX.cummulativeEarnedPerMLiq, 154733312657952738 + 22099268330799);
    //     assertEq(RRL.tokenX.subtreeCummulativeEarnedPerMLiq, 2201300334794271053 + 731360691551353);
    //     assertEq(RRL.tokenY.cummulativeEarnedPerMLiq, 5772069627 + 9502);
    //     assertEq(RRL.tokenY.subtreeCummulativeEarnedPerMLiq, 519121437518 + 855687);

    //     // RRLL
    //     // 1701e18 * 2352954287417905205553 / 296771752 / 2**64
    //     // 1701e18 * 2352954287417905205553 / 296771752 / 2**64
    //     // 780531e6 * 6117681147286553534438 / 296771752 / 2**64
    //     // 780531e6 * 6117681147286553534438 / 296771752 / 2**64
    //     assertEq(RRLL.tokenX.cummulativeEarnedPerMLiq, 2109575308294031901 + 731097873063750);
    //     assertEq(RRLL.tokenX.subtreeCummulativeEarnedPerMLiq, 2109575308294031901 + 731097873063750);
    //     assertEq(RRLL.tokenY.cummulativeEarnedPerMLiq, 529154012121 + 872237);
    //     assertEq(RRLL.tokenY.subtreeCummulativeEarnedPerMLiq, 529154012121 + 872237);

    //     // tLiq
    //     assertEq(root.tLiq, 4430);
    //     assertEq(R.tLiq, 77);
    //     assertEq(RR.tLiq, 82734);
    //     assertEq(RL.tLiq, 111);
    //     assertEq(RRL.tLiq, 5346);
    //     assertEq(RRLL.tLiq, 7634865);

    //     // subtreeMLiq
    //     assertEq(root.subtreeMLiq, 324198833); // 8430*16 + 377*8 + 9082734*4 + 1111*4 + 45346*2 + 287634865*1
    //     assertEq(R.subtreeMLiq, 324063953);    // 377*8 + 9082734*4 + 1111*4 + 45346*2 + 287634865*1
    //     assertEq(RR.subtreeMLiq, 324056493);   // 9082734*4 + 45346*2 + 287634865*1
    //     assertEq(RL.subtreeMLiq, 4444);        // 1111*4
    //     assertEq(RRL.subtreeMLiq, 287725557);  // 45346*2 + 287634865*1
    //     assertEq(RRLL.subtreeMLiq, 287634865); // 287634865*1

    //     // borrowedX
    //     assertEq(root.tokenX.borrowed, 492e18);
    //     assertEq(R.tokenX.borrowed, 998e18);
    //     assertEq(RR.tokenX.borrowed, 765e18);
    //     assertEq(RL.tokenX.borrowed, 24e18);
    //     assertEq(RRL.tokenX.borrowed, 53e18);
    //     assertEq(RRLL.tokenX.borrowed, 701e18);

    //     // borrowedY
    //     assertEq(root.tokenY.borrowed, 254858e6);
    //     assertEq(R.tokenY.borrowed, 353e6);
    //     assertEq(RR.tokenY.borrowed, 99763e6);
    //     assertEq(RL.tokenY.borrowed, 552e6);
    //     assertEq(RRL.tokenY.borrowed, 8765e6);
    //     assertEq(RRLL.tokenY.borrowed, 779531e6);

    //     // subtreeBorrowedX
    //     assertEq(root.tokenX.subtreeBorrowed, 3033e18); // 492e18 + 998e18 + 765e18 + 53e18 + 701e18 + 24e18
    //     assertEq(R.tokenX.subtreeBorrowed, 2541e18);    // 998e18 + 765e18 + 53e18 + 701e18 + 24e18
    //     assertEq(RR.tokenX.subtreeBorrowed, 1519e18);   // 765e18 + 53e18 + 701e18
    //     assertEq(RL.tokenX.subtreeBorrowed, 24e18);
    //     assertEq(RRL.tokenX.subtreeBorrowed, 754e18);   // 53e18 + 701e18
    //     assertEq(RRLL.tokenX.subtreeBorrowed, 701e18);  // 701e18

    //     // subtreeBorrowedY
    //     assertEq(root.tokenY.subtreeBorrowed, 1143822e6); // 254858e6 + 353e6 + 99763e6 + 8765e6 + 779531e6 + 552e6
    //     assertEq(R.tokenY.subtreeBorrowed, 888964e6);     // 353e6 + 99763e6 + 8765e6 + 779531e6 + 552e6
    //     assertEq(RR.tokenY.subtreeBorrowed, 888059e6);    // 99763e6 + 8765e6 + 779531e6
    //     assertEq(RL.tokenY.subtreeBorrowed, 552e6);
    //     assertEq(RRL.tokenY.subtreeBorrowed, 788296e6);   // 8765e6 + 779531e6
    //     assertEq(RRLL.tokenY.subtreeBorrowed, 779531e6);  // 779531e6
    // }
    /*
    function testLeftAndRightLegBelowPeak(); public {

    }

    function testLeftAndRightLegAtOrHigherThanPeak(); public {

    }

    function testLeftAndRightLegSameDistanceToStop(); public {

    }

    function testLeftLegLowerThanRightLeg(); public {

    }

    function testRightLegLowerThanLeftLeg(); public {

    }
    */

    function _nodeKey(uint24 depth, uint24 index, uint24 offset) public returns (LKey) {
        uint24 baseStep = uint24(offset / 2 ** depth);

        uint24 range = offset >> depth;
        uint24 base = offset + baseStep * index;
        return LKeyImpl.makeKey(range, base);
    }
}

/*
contract DenseTreeCodeStructureTest is Test {
    LiqTree public liqTree;
    using LiqTreeImpl for LiqTree;
    using LKeyImpl for LKey;
    using FeeRateSnapshotImpl for FeeRateSnapshot;
    
    function setUp(); public {
        // A depth of 4 creates a tree that covers an absolute range of 16 ([0, 15];);. 
        // ie. A complete tree matching the ascii documentation. 
        liqTree.init(4);
    }

    // NOTE: Technically all these cases are already covered by leftLegOnly + rightLegOnly
    //       I'm not yet sure if this is necessary or not.
    //       Leaning toward no.


    function testLowOutterIfStatementOnly(); public {

    }

    function testLowInnerWhileWithoutInnerIf(); public {

    }

    function testLowInnerWhileWithInnerIf(); public {

    }

    function testHighOutterIfStatementOnly(); public {

    }

    function testHighInnerWhileWithoutInnerIf(); public {

    }

    function testHighInnerWhileWithInnerIf(); public {

    }

}


contract DenseTreeMathmaticalLimitationsTest is Test {
    LiqTree public liqTree;
    using LiqTreeImpl for LiqTree;
    using LKeyImpl for LKey;
    using FeeRateSnapshotImpl for FeeRateSnapshot;
    
    function setUp(); public {
        // A depth of 4 creates a tree that covers an absolute range of 16 ([0, 15];);. 
        // ie. A complete tree matching the ascii documentation. 
        liqTree.init(4);
    }

    function testNoFeeAccumulationWithoutRate(); public {

    }

    function testFeeAccumulationDoesNotRoundUp(); public {

    }

    function testNodeTraversedTwiceWithoutRateUpdateDoesNotAccumulateAdditionalFees(); public {

    }

    function testFeeAccumulationDoesNotOverflowUint256(); public {

    }

    function testFeeAccumulationAccuracyWithRidiculousRates(); public {

    }
    
}
*/