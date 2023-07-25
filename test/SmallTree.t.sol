// SPDX-License-Identifier: BSL-1.1
pragma solidity ^0.8.18;

import { console2 } from "forge-std/console2.sol";
import { Test } from "forge-std/Test.sol";

import { LiqTree, LiqTreeImpl, LiqRange, LKey, LKeyImpl, LiqNode, FeeSnap } from "src/Tree.sol";

// solhint-disable

/**
 * In practice, the LiqTree will have many nodes. So many, that testing at that scale is intractable.
 * Thus the reason for this file. A smaller scale LiqTree, where we can more easily populate the values densely.
 */
contract SmallTreeTest is Test {
    LiqTree public liqTree;
    using LiqTreeImpl for LiqTree;
    using LKeyImpl for LKey;

    function setUp() public {
        // A depth of 5 creates a tree that covers an absolute range of 16 ([0, 15];);.
        // ie. A complete tree matching the ascii documentation.
        liqTree.init(5);
    }

    // Helper for creating a LiqRange from the given indices. The tree offsets the input values
    // because it expects them to be zero centered. For testing, it is more convenient to interpret
    // the indices from 0 to the max range. This we undo the offset here.
    function range(int24 low, int24 high) public view returns (LiqRange memory lr) {
        lr.low = low - int24(liqTree.width / 2);
        lr.high = high - int24(liqTree.width / 2);
    }

    function testSimpleFee() public {
        FeeSnap memory fees;
        liqTree.addMLiq(range(8, 11), 1111, fees);
        liqTree.addTLiq(range(8, 11), 111, fees, 24e18, 7e6);

        fees.X += 113712805933826;

        LiqNode storage RL = liqTree.nodes[LKey.wrap((4 << 24) | 8)];
        // LiqNode storage RLL = liqTree.nodes[LKey.wrap((2 << 24) | 8)];
        LiqNode storage RLLL = liqTree.nodes[LKey.wrap((1 << 24) | 8)];

        // trigger fees + undo
        liqTree.addTLiq(range(8, 11), 111, fees, 24e18, 7e6);
        liqTree.removeTLiq(range(8, 11), 111, fees, 24e18, 7e6);

        // 113712805933826 * 24e18 / 4444 / 2**64 = 33291000332.9100024179226406346006655493880262469301129331683
        assertEq(RL.tokenX.cumulativeEarnedPerMLiq, 33291000332);
        assertEq(RL.tokenX.subtreeCumulativeEarnedPerMLiq, 33291000332);

        // RL feeX / 4 = 8322750083.22750060448066015865016638734700656173252823329207
        assertEq(RLLL.tokenX.cumulativeEarnedPerMLiq, 0);
    }

    // Tree structure tests

    function testRootNodeOnly() public {
        LiqNode storage root = liqTree.nodes[liqTree.root];
        FeeSnap memory fees;

        liqTree.addWideRangeMLiq(8430, fees);
        liqTree.addWideRangeTLiq(4381, fees, 832e18, 928e6);

        fees.Y += 113712805933826; // 5.4% APR as Q192.64 = 0.054 * 3600 / (365 * 24 * 60 * 60) * 2^64 = 113712805933826
        fees.X += 113712805933826;

        // Verify root state is as expected
        assertEq(root.mLiq, 8430);
        assertEq(root.subtreeMLiq, 134880);
        assertEq(root.tLiq, 4381);
        assertEq(root.tokenX.borrow, 832e18);
        assertEq(root.tokenX.subtreeBorrow, 832e18);
        assertEq(root.tokenY.borrow, 928e6);
        assertEq(root.tokenY.subtreeBorrow, 928e6);

        // Testing add_Wide_range_mLiq
        liqTree.addWideRangeMLiq(9287, fees);

        // earn_x      = 113712805933826 * 832e18 / 134880 / 2**64 = 38024667284.1612625482053537908689136045718673850859328662514
        // earn_y      = 113712805933826 * 928e6 / 134880 / 2**64  = 0.0424121288938721774576136638436614805589455443910573866585112692
        assertEq(root.tokenX.cumulativeEarnedPerMLiq, 38024667284);
        assertEq(root.tokenX.subtreeCumulativeEarnedPerMLiq, 38024667284);
        assertEq(root.tokenY.cumulativeEarnedPerMLiq, 0);
        assertEq(root.tokenY.subtreeCumulativeEarnedPerMLiq, 0);

        assertEq(root.mLiq, 17717);
        assertEq(root.subtreeMLiq, 283472);
        assertEq(root.tLiq, 4381);
        assertEq(root.tokenX.borrow, 832e18);
        assertEq(root.tokenX.subtreeBorrow, 832e18);
        assertEq(root.tokenY.borrow, 928e6);
        assertEq(root.tokenY.subtreeBorrow, 928e6);

        // Testing remove_Wide_range_mLiq
        fees.Y += 74672420010376264941568;
        fees.X += 74672420010376264941568;

        liqTree.removeWideRangeMLiq(3682, fees);

        // earn_x      = 74672420010376264941568 * 832e18 / 283472 / 2**64 = 11881018231077496190.0999040469605463678952418581023875373934
        // earn_y      = 74672420010376264941568 * 928e6 / 283472 / 2**64  = 13251904.9500479765197268160523790709488062313032680476378619
        assertEq(root.tokenX.cumulativeEarnedPerMLiq, 11881018269102163474); // 11881018231077496190 + 38024667284 = 11881018269102163474
        assertEq(root.tokenX.subtreeCumulativeEarnedPerMLiq, 11881018269102163474); // 11881018231077496190 + 38024667284 = 11881018269102163474
        assertEq(root.tokenY.cumulativeEarnedPerMLiq, 13251904);
        assertEq(root.tokenY.subtreeCumulativeEarnedPerMLiq, 13251904);

        assertEq(root.mLiq, 14035);
        assertEq(root.subtreeMLiq, 224560);
        assertEq(root.tLiq, 4381);
        assertEq(root.tokenX.borrow, 832e18);
        assertEq(root.tokenX.subtreeBorrow, 832e18);
        assertEq(root.tokenY.borrow, 928e6);
        assertEq(root.tokenY.subtreeBorrow, 928e6);

        // Testing add_Wide_range_tLiq
        fees.Y += 6932491854677024;
        fees.X += 6932491854677024;

        liqTree.addWideRangeTLiq(7287, fees, 9184e18, 7926920e6);

        // earn_x      = 6932491854677024 * 832e18 / 224560 / 2**64 = 1392388963085.50927075184684754182568989829487082029858389739
        // earn_y      = 6932491854677024 * 928e6 / 224560 / 2**64  = 1.5530492280569141866078291761043440387327135097611022666547915924
        assertEq(root.tokenX.cumulativeEarnedPerMLiq, 11881019661491126559); // 11881018269102163474 + 1392388963085 = 11881019661491126559
        assertEq(root.tokenX.subtreeCumulativeEarnedPerMLiq, 11881019661491126559); // 11881018269102163474 + 1392388963085 = 11881019661491126559
        assertEq(root.tokenY.cumulativeEarnedPerMLiq, 13251905);
        assertEq(root.tokenY.subtreeCumulativeEarnedPerMLiq, 13251905);

        assertEq(root.mLiq, 14035);
        assertEq(root.subtreeMLiq, 224560);
        assertEq(root.tLiq, 11668);
        assertEq(root.tokenX.borrow, 10016e18);
        assertEq(root.tokenX.subtreeBorrow, 10016e18);
        assertEq(root.tokenY.borrow, 7927848e6);
        assertEq(root.tokenY.subtreeBorrow, 7927848e6);

        // Testing remove_Wide_range_tLiq
        fees.Y += 1055375100301031600000000;
        fees.X += 1055375100301031600000000;

        liqTree.removeWideRangeTLiq(4923, fees, 222e18, 786e6);

        // earn_x      = 1055375100301031600000000 * 10016e18 / 224560 / 2**64  = 2551814126505030241953.87164028103035638433335980020216618053
        // earn_y      = 1055375100301031600000000 * 7927848e6 / 224560 / 2**64 = 2019807759503.25988354767545683493270255599285721099372431609
        assertEq(root.tokenX.cumulativeEarnedPerMLiq, 2563695146166521368512); // 2551814126505030241953 + 11881019661491126559 = 2563695146166521368512
        assertEq(root.tokenX.subtreeCumulativeEarnedPerMLiq, 2563695146166521368512); // 2551814126505030241953 + 11881019661491126559 = 2563695146166521368512
        assertEq(root.tokenY.cumulativeEarnedPerMLiq, 2019821011408); // 2019807759503 + 13251905 = 2019821011408
        assertEq(root.tokenY.subtreeCumulativeEarnedPerMLiq, 2019821011408); // 2019807759503 + 13251905 = 2019821011408

        assertEq(root.mLiq, 14035);
        assertEq(root.subtreeMLiq, 224560);
        assertEq(root.tLiq, 6745);
        assertEq(root.tokenX.borrow, 9794e18);
        assertEq(root.tokenX.subtreeBorrow, 9794e18);
        assertEq(root.tokenY.borrow, 7927062e6);
        assertEq(root.tokenY.subtreeBorrow, 7927062e6);
    }

    function testLeftLegOnly() public {
        // Mirrors test_right_leg_only
        // Manual calculations are shown there.
        FeeSnap memory fees;
        LiqNode storage root = liqTree.nodes[liqTree.root];

        LiqNode storage L = liqTree.nodes[LKey.wrap((8 << 24) | 0)];
        LiqNode storage LL = liqTree.nodes[LKey.wrap((4 << 24) | 0)];
        LiqNode storage LR = liqTree.nodes[LKey.wrap((4 << 24) | 4)];
        LiqNode storage LLR = liqTree.nodes[LKey.wrap((2 << 24) | 2)];
        LiqNode storage LLRR = liqTree.nodes[LKey.wrap((1 << 24) | 3)];

        // T0 - populate tree with data excluding fee calculations
        liqTree.addWideRangeMLiq(8430, fees); // root
        liqTree.addMLiq(range(0, 7), 377, fees); // L
        liqTree.addMLiq(range(0, 3), 9082734, fees); // LL
        liqTree.addMLiq(range(4, 7), 1111, fees); // LR
        liqTree.addMLiq(range(2, 3), 45346, fees); // LLR
        liqTree.addMLiq(range(3, 3), 287634865, fees); // LLRR

        liqTree.addWideRangeTLiq(4430, fees, 492e18, 254858e6); // root
        liqTree.addTLiq(range(0, 7), 77, fees, 998e18, 353e6); // L
        liqTree.addTLiq(range(0, 3), 82734, fees, 765e18, 99763e6); // LL
        liqTree.addTLiq(range(4, 7), 111, fees, 24e18, 552e6); // LR
        liqTree.addTLiq(range(2, 3), 5346, fees, 53e18, 8765e6); // LLR
        liqTree.addTLiq(range(3, 3), 7634865, fees, 701e18, 779531e6); // LLRR

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

        // borrow_x
        assertEq(root.tokenX.borrow, 492e18);
        assertEq(L.tokenX.borrow, 998e18);
        assertEq(LL.tokenX.borrow, 765e18);
        assertEq(LR.tokenX.borrow, 24e18);
        assertEq(LLR.tokenX.borrow, 53e18);
        assertEq(LLRR.tokenX.borrow, 701e18);

        // subtree_borrow_x
        assertEq(root.tokenX.subtreeBorrow, 3033e18);
        assertEq(L.tokenX.subtreeBorrow, 2541e18);
        assertEq(LL.tokenX.subtreeBorrow, 1519e18);
        assertEq(LR.tokenX.subtreeBorrow, 24e18);
        assertEq(LLR.tokenX.subtreeBorrow, 754e18);
        assertEq(LLRR.tokenX.subtreeBorrow, 701e18);

        // borrow_y
        assertEq(root.tokenY.borrow, 254858e6);
        assertEq(L.tokenY.borrow, 353e6);
        assertEq(LL.tokenY.borrow, 99763e6);
        assertEq(LR.tokenY.borrow, 552e6);
        assertEq(LLR.tokenY.borrow, 8765e6);
        assertEq(LLRR.tokenY.borrow, 779531e6);

        // subtree_borrow_y
        assertEq(root.tokenY.subtreeBorrow, 1143822e6);
        assertEq(L.tokenY.subtreeBorrow, 888964e6);
        assertEq(LL.tokenY.subtreeBorrow, 888059e6);
        assertEq(LR.tokenY.subtreeBorrow, 552e6);
        assertEq(LLR.tokenY.subtreeBorrow, 788296e6);
        assertEq(LLRR.tokenY.subtreeBorrow, 779531e6);

        // T98273
        fees.X += 4541239648278065;
        fees.Y += 13278814667749784;

        // Apply change that requires fee calculation
        // addMLiq
        liqTree.addMLiq(range(3, 7), 2734, fees); // LLRR, LR

        // root
        assertEq(root.tokenX.cumulativeEarnedPerMLiq, 373601278);
        assertEq(root.tokenX.subtreeCumulativeEarnedPerMLiq, 2303115199);
        assertEq(root.tokenY.cumulativeEarnedPerMLiq, 0);
        assertEq(root.tokenY.subtreeCumulativeEarnedPerMLiq, 2);

        // L
        assertEq(L.tokenX.cumulativeEarnedPerMLiq, 757991165);
        assertEq(L.tokenX.subtreeCumulativeEarnedPerMLiq, 1929915382);
        assertEq(L.tokenY.cumulativeEarnedPerMLiq, 0);
        assertEq(L.tokenY.subtreeCumulativeEarnedPerMLiq, 1);

        // LL
        assertEq(LL.tokenX.cumulativeEarnedPerMLiq, 581096415);
        assertEq(LL.tokenX.subtreeCumulativeEarnedPerMLiq, 1153837196);
        assertEq(LL.tokenY.cumulativeEarnedPerMLiq, 0);
        assertEq(LL.tokenY.subtreeCumulativeEarnedPerMLiq, 1);

        // LR
        assertEq(LR.tokenX.cumulativeEarnedPerMLiq, 148929881804);
        assertEq(LR.tokenX.subtreeCumulativeEarnedPerMLiq, 148929881804);
        assertEq(LR.tokenY.cumulativeEarnedPerMLiq, 10);
        assertEq(LR.tokenY.subtreeCumulativeEarnedPerMLiq, 10);

        // LLR
        assertEq(LLR.tokenX.cumulativeEarnedPerMLiq, 42651943);
        assertEq(LLR.tokenX.subtreeCumulativeEarnedPerMLiq, 606784254);
        assertEq(LLR.tokenY.cumulativeEarnedPerMLiq, 0);
        assertEq(LLR.tokenY.subtreeCumulativeEarnedPerMLiq, 1);

        // LLRR
        assertEq(LLRR.tokenX.cumulativeEarnedPerMLiq, 581500584);
        assertEq(LLRR.tokenX.subtreeCumulativeEarnedPerMLiq, 581500584);
        assertEq(LLRR.tokenY.cumulativeEarnedPerMLiq, 1);
        assertEq(LLRR.tokenY.subtreeCumulativeEarnedPerMLiq, 1);

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
        fees.X += 16463537718422861220174597;
        fees.Y += 3715979586694123491881712207;

        // Apply change that requires fee calculation
        // remove_mLiq
        liqTree.removeMLiq(range(3, 7), 2734, fees); // LLRR, LR

        // root
        assertEq(root.tokenX.cumulativeEarnedPerMLiq, 1354374549844117328);
        assertEq(root.tokenX.subtreeCumulativeEarnedPerMLiq, 8349223596904894020);
        assertEq(root.tokenY.cumulativeEarnedPerMLiq, 158351473403);
        assertEq(root.tokenY.subtreeCumulativeEarnedPerMLiq, 710693401863);

        // L
        assertEq(L.tokenX.cumulativeEarnedPerMLiq, 2747859799935140577);
        assertEq(L.tokenX.subtreeCumulativeEarnedPerMLiq, 6996304360355904016);
        assertEq(L.tokenY.cumulativeEarnedPerMLiq, 219375887);
        assertEq(L.tokenY.subtreeCumulativeEarnedPerMLiq, 552456845956);

        // LL
        assertEq(LL.tokenX.cumulativeEarnedPerMLiq, 2106654304686669588);
        assertEq(LL.tokenX.subtreeCumulativeEarnedPerMLiq, 4183016848129478568);
        assertEq(LL.tokenY.cumulativeEarnedPerMLiq, 62008538706);
        assertEq(LL.tokenY.subtreeCumulativeEarnedPerMLiq, 551980602777);

        // LR
        assertEq(LR.tokenX.cumulativeEarnedPerMLiq, 423248578107618890129);
        assertEq(LR.tokenX.subtreeCumulativeEarnedPerMLiq, 423248578107618890129);
        assertEq(LR.tokenY.cumulativeEarnedPerMLiq, 2197219781195);
        assertEq(LR.tokenY.subtreeCumulativeEarnedPerMLiq, 2197219781195);

        // LLR
        assertEq(LLR.tokenX.cumulativeEarnedPerMLiq, 154626415017241476);
        assertEq(LLR.tokenX.subtreeCumulativeEarnedPerMLiq, 2199779564584907057);
        assertEq(LLR.tokenY.cumulativeEarnedPerMLiq, 5771781665);
        assertEq(LLR.tokenY.subtreeCumulativeEarnedPerMLiq, 519095539055);

        // LLRR
        assertEq(LLRR.tokenX.cumulativeEarnedPerMLiq, 2108117905996538332);
        assertEq(LLRR.tokenX.subtreeCumulativeEarnedPerMLiq, 2108117905996538332);
        assertEq(LLRR.tokenY.cumulativeEarnedPerMLiq, 529127613135);
        assertEq(LLRR.tokenY.subtreeCumulativeEarnedPerMLiq, 529127613135);

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
        fees.X += 11381610389149375791104;
        fees.Y += 185394198934916215865344;

        // Apply change that requires fee calculation
        // addTLiq
        liqTree.addTLiq(range(3, 7), 1000, fees, 1000e18, 1000e6); // LLRR, LR

        // root
        assertEq(root.tokenX.cumulativeEarnedPerMLiq, 1355310898622008714);
        assertEq(root.tokenX.subtreeCumulativeEarnedPerMLiq, 8354995844553968361);
        assertEq(root.tokenY.cumulativeEarnedPerMLiq, 158359374060);
        assertEq(root.tokenY.subtreeCumulativeEarnedPerMLiq, 710728860612);

        // L
        assertEq(L.tokenX.cumulativeEarnedPerMLiq, 2749759536746020654);
        assertEq(L.tokenX.subtreeCumulativeEarnedPerMLiq, 7001141265402443371);
        assertEq(L.tokenY.cumulativeEarnedPerMLiq, 219386832);
        assertEq(L.tokenY.subtreeCumulativeEarnedPerMLiq, 552484409781);

        // LL
        assertEq(LL.tokenX.cumulativeEarnedPerMLiq, 2108110694023652835);
        assertEq(LL.tokenX.subtreeCumulativeEarnedPerMLiq, 4185908685257423082);
        assertEq(LL.tokenY.cumulativeEarnedPerMLiq, 62011632404);
        assertEq(LL.tokenY.subtreeCumulativeEarnedPerMLiq, 552008141912);

        // LR
        assertEq(LR.tokenX.cumulativeEarnedPerMLiq, 423621837838722923425);
        assertEq(LR.tokenX.subtreeCumulativeEarnedPerMLiq, 423621837838722923425);
        assertEq(LR.tokenY.cumulativeEarnedPerMLiq, 2197359621190);
        assertEq(LR.tokenY.subtreeCumulativeEarnedPerMLiq, 2197359621190);

        // LLR
        assertEq(LLR.tokenX.cumulativeEarnedPerMLiq, 154733312657952738);
        assertEq(LLR.tokenX.subtreeCumulativeEarnedPerMLiq, 2201300334794271053);
        assertEq(LLR.tokenY.cumulativeEarnedPerMLiq, 5772069627);
        assertEq(LLR.tokenY.subtreeCumulativeEarnedPerMLiq, 519121437518);

        // LLRR
        assertEq(LLRR.tokenX.cumulativeEarnedPerMLiq, 2109575308294031901);
        assertEq(LLRR.tokenX.subtreeCumulativeEarnedPerMLiq, 2109575308294031901);
        assertEq(LLRR.tokenY.cumulativeEarnedPerMLiq, 529154012121);
        assertEq(LLRR.tokenY.subtreeCumulativeEarnedPerMLiq, 529154012121);

        // tLiq
        assertEq(root.tLiq, 4430);
        assertEq(L.tLiq, 77);
        assertEq(LL.tLiq, 82734);
        assertEq(LR.tLiq, 1111);
        assertEq(LLR.tLiq, 5346);
        assertEq(LLRR.tLiq, 7635865);

        // borrow_x
        assertEq(root.tokenX.borrow, 492e18);
        assertEq(L.tokenX.borrow, 998e18);
        assertEq(LL.tokenX.borrow, 765e18);
        assertEq(LR.tokenX.borrow, 824e18, "LR x borrow");
        assertEq(LLR.tokenX.borrow, 53e18);
        assertEq(LLRR.tokenX.borrow, 901e18);

        // subtree_borrow_x
        assertEq(root.tokenX.subtreeBorrow, 4033e18);
        assertEq(L.tokenX.subtreeBorrow, 3541e18);
        assertEq(LL.tokenX.subtreeBorrow, 1719e18);
        assertEq(LR.tokenX.subtreeBorrow, 824e18);
        assertEq(LLR.tokenX.subtreeBorrow, 954e18);
        assertEq(LLRR.tokenX.subtreeBorrow, 901e18);

        // borrow_y
        assertEq(root.tokenY.borrow, 254858e6);
        assertEq(L.tokenY.borrow, 353e6);
        assertEq(LL.tokenY.borrow, 99763e6);
        assertEq(LR.tokenY.borrow, 1352000000);
        assertEq(LLR.tokenY.borrow, 8765e6);
        assertEq(LLRR.tokenY.borrow, 779731000000);

        // subtree_borrow_y
        assertEq(root.tokenY.subtreeBorrow, 1144822000000);
        assertEq(L.tokenY.subtreeBorrow, 889964000000);
        assertEq(LL.tokenY.subtreeBorrow, 888259000000);
        assertEq(LR.tokenY.subtreeBorrow, 1352000000);
        assertEq(LLR.tokenY.subtreeBorrow, 788496000000);
        assertEq(LLRR.tokenY.subtreeBorrow, 779731000000);

        // T32876298273
        // 3.3) addTLiq
        fees.X += 2352954287417905205553;
        fees.Y += 6117681147286553534438;

        // Apply change that requires fee calculation
        // addTLiq
        liqTree.removeTLiq(range(3, 7), 1000, fees, 1000e18, 1000e6); // LLRR, LR

        // root
        assertEq(root.tokenX.cumulativeEarnedPerMLiq, 1355504472799662735);
        assertEq(root.tokenX.subtreeCumulativeEarnedPerMLiq, 8356582601989900611);
        assertEq(root.tokenY.cumulativeEarnedPerMLiq, 158359634767);
        assertEq(root.tokenY.subtreeCumulativeEarnedPerMLiq, 710730031711);

        // L
        assertEq(L.tokenX.cumulativeEarnedPerMLiq, 2750152275007241346);
        assertEq(L.tokenX.subtreeCumulativeEarnedPerMLiq, 7002534738531684325);
        assertEq(L.tokenY.cumulativeEarnedPerMLiq, 219387193);
        assertEq(L.tokenY.subtreeCumulativeEarnedPerMLiq, 552485320361);

        // LL
        assertEq(LL.tokenX.cumulativeEarnedPerMLiq, 2108411777738297592);
        assertEq(LL.tokenX.subtreeCumulativeEarnedPerMLiq, 4186585238075036595);
        assertEq(LL.tokenY.cumulativeEarnedPerMLiq, 62011734490);
        assertEq(LL.tokenY.subtreeCumulativeEarnedPerMLiq, 552009050859);

        // LR
        assertEq(LR.tokenX.cumulativeEarnedPerMLiq, 426271172880750451233);
        assertEq(LR.tokenX.subtreeCumulativeEarnedPerMLiq, 426271172880750451233);
        assertEq(LR.tokenY.cumulativeEarnedPerMLiq, 2197370923304);
        assertEq(LR.tokenY.subtreeCumulativeEarnedPerMLiq, 2197370923304);

        // LLR
        assertEq(LLR.tokenX.cumulativeEarnedPerMLiq, 154755411926283537);
        assertEq(LLR.tokenX.subtreeCumulativeEarnedPerMLiq, 2201698121624225437);
        assertEq(LLR.tokenY.cumulativeEarnedPerMLiq, 5772079129);
        assertEq(LLR.tokenY.subtreeCumulativeEarnedPerMLiq, 519122292338);

        // LLRR
        assertEq(LLRR.tokenX.cumulativeEarnedPerMLiq, 2109962562370240271);
        assertEq(LLRR.tokenX.subtreeCumulativeEarnedPerMLiq, 2109962562370240271);
        assertEq(LLRR.tokenY.cumulativeEarnedPerMLiq, 529154883464);
        assertEq(LLRR.tokenY.subtreeCumulativeEarnedPerMLiq, 529154883464);

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

        // borrow_x
        assertEq(root.tokenX.borrow, 492e18);
        assertEq(L.tokenX.borrow, 998e18);
        assertEq(LL.tokenX.borrow, 765e18);
        assertEq(LR.tokenX.borrow, 24e18);
        assertEq(LLR.tokenX.borrow, 53e18);
        assertEq(LLRR.tokenX.borrow, 701e18);

        // subtree_borrow_x
        assertEq(root.tokenX.subtreeBorrow, 3033e18);
        assertEq(L.tokenX.subtreeBorrow, 2541e18);
        assertEq(LL.tokenX.subtreeBorrow, 1519e18);
        assertEq(LR.tokenX.subtreeBorrow, 24e18);
        assertEq(LLR.tokenX.subtreeBorrow, 754e18);
        assertEq(LLRR.tokenX.subtreeBorrow, 701e18);

        // borrow_y
        assertEq(root.tokenY.borrow, 254858e6);
        assertEq(L.tokenY.borrow, 353e6);
        assertEq(LL.tokenY.borrow, 99763e6);
        assertEq(LR.tokenY.borrow, 552e6);
        assertEq(LLR.tokenY.borrow, 8765e6);
        assertEq(LLRR.tokenY.borrow, 779531e6);

        // subtree_borrow_y
        assertEq(root.tokenY.subtreeBorrow, 1143822e6);
        assertEq(L.tokenY.subtreeBorrow, 888964e6);
        assertEq(LL.tokenY.subtreeBorrow, 888059e6);
        assertEq(LR.tokenY.subtreeBorrow, 552e6);
        assertEq(LLR.tokenY.subtreeBorrow, 788296e6);
        assertEq(LLRR.tokenY.subtreeBorrow, 779531e6);
    }

    function testRightLegOnly() public {
        FeeSnap memory fees;
        LiqNode storage root = liqTree.nodes[liqTree.root];

        LiqNode storage R = liqTree.nodes[LKey.wrap((8 << 24) | 8)];
        LiqNode storage RR = liqTree.nodes[LKey.wrap((4 << 24) | 12)];
        LiqNode storage RL = liqTree.nodes[LKey.wrap((4 << 24) | 8)];
        LiqNode storage RRL = liqTree.nodes[LKey.wrap((2 << 24) | 12)];
        LiqNode storage RRLL = liqTree.nodes[LKey.wrap((1 << 24) | 12)];

        // T0 - populate tree with data excluding fee calculations
        liqTree.addWideRangeMLiq(8430, fees); // root
        liqTree.addMLiq(range(8, 15), 377, fees); // R
        liqTree.addMLiq(range(12, 15), 9082734, fees); // RR
        liqTree.addMLiq(range(8, 11), 1111, fees); // RL
        liqTree.addMLiq(range(12, 13), 45346, fees); // RRL
        liqTree.addMLiq(range(12, 12), 287634865, fees); // RRLL

        liqTree.addWideRangeTLiq(4430, fees, 492e18, 254858e6); // root
        liqTree.addTLiq(range(8, 15), 77, fees, 998e18, 353e6); // R
        liqTree.addTLiq(range(12, 15), 82734, fees, 765e18, 99763e6); // RR
        liqTree.addTLiq(range(8, 11), 111, fees, 24e18, 552e6); // RL
        liqTree.addTLiq(range(12, 13), 5346, fees, 53e18, 8765e6); // RRL
        liqTree.addTLiq(range(12, 12), 7634865, fees, 701e18, 779531e6); // RRLL

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
        assertEq(R.subtreeMLiq, 324063953); // 377*8 + 9082734*4 + 1111*4 + 45346*2 + 287634865*1
        assertEq(RR.subtreeMLiq, 324056493); // 9082734*4 + 45346*2 + 287634865*1
        assertEq(RL.subtreeMLiq, 4444); // 1111*4
        assertEq(RRL.subtreeMLiq, 287725557); // 45346*2 + 287634865*1
        assertEq(RRLL.subtreeMLiq, 287634865); // 287634865*1

        // borrow_x
        assertEq(root.tokenX.borrow, 492e18);
        assertEq(R.tokenX.borrow, 998e18);
        assertEq(RR.tokenX.borrow, 765e18);
        assertEq(RL.tokenX.borrow, 24e18);
        assertEq(RRL.tokenX.borrow, 53e18);
        assertEq(RRLL.tokenX.borrow, 701e18);

        // subtree_borrow_x
        assertEq(root.tokenX.subtreeBorrow, 3033e18); // 492e18 + 998e18 + 765e18 + 53e18 + 701e18 + 24e18
        assertEq(R.tokenX.subtreeBorrow, 2541e18); // 998e18 + 765e18 + 53e18 + 701e18 + 24e18
        assertEq(RR.tokenX.subtreeBorrow, 1519e18); // 765e18 + 53e18 + 701e18
        assertEq(RL.tokenX.subtreeBorrow, 24e18); // 24e18
        assertEq(RRL.tokenX.subtreeBorrow, 754e18); // 53e18 + 701e18
        assertEq(RRLL.tokenX.subtreeBorrow, 701e18); // 701e18

        // borrow_y
        assertEq(root.tokenY.borrow, 254858e6);
        assertEq(R.tokenY.borrow, 353e6);
        assertEq(RR.tokenY.borrow, 99763e6);
        assertEq(RL.tokenY.borrow, 552e6);
        assertEq(RRL.tokenY.borrow, 8765e6);
        assertEq(RRLL.tokenY.borrow, 779531e6);

        // subtree_borrow_y
        assertEq(root.tokenY.subtreeBorrow, 1143822e6); // 254858e6 + 353e6 + 99763e6 + 8765e6 + 779531e6 + 552e6
        assertEq(R.tokenY.subtreeBorrow, 888964e6); // 353e6 + 99763e6 + 8765e6 + 779531e6 + 552e6
        assertEq(RR.tokenY.subtreeBorrow, 888059e6); // 99763e6 + 8765e6 + 779531e6
        assertEq(RL.tokenY.subtreeBorrow, 552e6); // 552e6
        assertEq(RRL.tokenY.subtreeBorrow, 788296e6); // 8765e6 + 779531e6
        assertEq(RRLL.tokenY.subtreeBorrow, 779531e6); // 779531e6

        // T98273
        fees.X += 4541239648278065; // 7.9% APR as Q192.64 T98273 - T0
        fees.Y += 13278814667749784; // 23.1% APR as Q192.64 T98273 - T0

        // Apply change that requires fee calculation
        // addMLiq
        liqTree.addMLiq(range(8, 12), 2734, fees); // RRLL, RL

        // root
        //           total_mLiq = subtreeMLiq + aux_level * range
        //           earn_x = rate_diff * borrow / total_mLiq / q_conversion
        //
        //           earn_x     = 4541239648278065 * 492e18 / 324198833 / 2**64 = 373601278.675896709674247960788128930863427771780474615825402
        //           earn_x_sub = 4541239648278065 * 3033e18 / 324198833 / 2**64 = 2303115199.64226569195527248998047773843247242237841363780171
        //
        //           earn_y     = 13278814667749784 * 254858e6 / 324198833 / 2**64 = 0.5658826914495360518450511013487630736056981385516828024975012016
        //           earn_y_sub = 13278814667749784 * 1143822e6 / 324198833 / 2**64 = 2.5397243637601771413630729302079780755472335819729532779755660779
        assertEq(root.tokenX.cumulativeEarnedPerMLiq, 373601278);
        assertEq(root.tokenX.subtreeCumulativeEarnedPerMLiq, 2303115199);
        assertEq(root.tokenY.cumulativeEarnedPerMLiq, 0);
        assertEq(root.tokenY.subtreeCumulativeEarnedPerMLiq, 2);

        // R
        //           total_mLiq = 324063953 + 8430 * 8 = 324131393
        //
        //           earn_x      = 4541239648278065 * 998e18 / 324131393 / 2**64 = 757991165.739306427787211084069081135461126639210612444989968
        //           earn_x_sub  = 4541239648278065 * 2541e18 / 324131393 / 2**64 = 1929915382.90939642585902140743440397315302884793002627527005
        //
        //           earn_y      = 13278814667749784 * 353e6 / 324131393 / 2**64 = 0.0007839587228619296743658765199435031723124415958637831459168088
        //           earn_y_sub  = 13278814667749784 * 888964e6 / 324131393 / 2**64 = 1.9742523572527831474305582285412361305143267162194111063081870320
        assertEq(R.tokenX.cumulativeEarnedPerMLiq, 757991165);
        assertEq(R.tokenX.subtreeCumulativeEarnedPerMLiq, 1929915382);
        assertEq(R.tokenY.cumulativeEarnedPerMLiq, 0);
        assertEq(R.tokenY.subtreeCumulativeEarnedPerMLiq, 1);

        // RR
        //           total_mLiq = 324056493 + (377 + 8430) * 4 = 324091721
        //
        //           earn_x      = 4541239648278065 * 765e18 / 324091721 / 2**64 = 581096415.560225831923714717876078601550264387092272644849535
        //           earn_x_sub  = 4541239648278065 * 1519e18 / 324091721 / 2**64 = 1153837196.38690593293087928948204365458150536469694398369469
        //
        //           earn_y      = 13278814667749784 * 99763e6 / 324091721 / 2**64 = 0.2215854043845212215658200680605818096232476901747430889861663960
        //           earn_y_sub  = 13278814667749784 * 888059e6 / 324091721 / 2**64 = 1.9724839131974131842719305135352006382347335233392357172695883598
        assertEq(RR.tokenX.cumulativeEarnedPerMLiq, 581096415);
        assertEq(RR.tokenX.subtreeCumulativeEarnedPerMLiq, 1153837196);
        assertEq(RR.tokenY.cumulativeEarnedPerMLiq, 0);
        assertEq(RR.tokenY.subtreeCumulativeEarnedPerMLiq, 1);

        // RL
        //           total_mLiq = 4444 + (377 + 8430) * 4 = 39672
        //
        //           earn_x      = 4541239648278065 * 24e18 / 39672 / 2**64 = 148929881804.004419784834421574153374302771710945632482252911
        //           earn_x_sub  = 4541239648278065 * 24e18 / 39672 / 2**64 = 148929881804.004419784834421574153374302771710945632482252911
        //
        //           earn_y      = 13278814667749784 * 552e6 / 39672 / 2**64 = 10.016005848413612945928345245285743980736658202469601316734724742
        //           earn_y_sub  = 13278814667749784 * 552e6 / 39672 / 2**64 = 10.016005848413612945928345245285743980736658202469601316734724742
        assertEq(RL.tokenX.cumulativeEarnedPerMLiq, 148929881804);
        assertEq(RL.tokenX.subtreeCumulativeEarnedPerMLiq, 148929881804);
        assertEq(RL.tokenY.cumulativeEarnedPerMLiq, 10);
        assertEq(RL.tokenY.subtreeCumulativeEarnedPerMLiq, 10);

        // RRL
        //           total_mLiq = 287725557 + (9082734 + 377 + 8430) * 2 = 305908639
        //
        //           earn_x      = 4541239648278065 * 53e18 / 305908639 / 2**64 = 42651943.5921096141810155248335108410236545389757231280339726
        //           earn_x_sub  = 4541239648278065 * 754e18 / 305908639 / 2**64 = 606784254.121710360235579353291833474185575894107457330898403
        //
        //           earn_y      = 13278814667749784 * 8765e6 / 305908639 / 2**64 = 0.0206252758466917150640245207131723061423410095348761855275430371
        //           earn_y_sub  = 13278814667749784 * 788296e6 / 305908639 / 2**64 = 1.8549711864054412114215942475882345970088817401374509465624718757
        assertEq(RRL.tokenX.cumulativeEarnedPerMLiq, 42651943);
        assertEq(RRL.tokenX.subtreeCumulativeEarnedPerMLiq, 606784254);
        assertEq(RRL.tokenY.cumulativeEarnedPerMLiq, 0);
        assertEq(RRL.tokenY.subtreeCumulativeEarnedPerMLiq, 1);

        // RRLL
        //           total_mLiq = 287634865 + (45346 + 9082734 + 377 + 8430) * 1 = 296771752
        //
        //           earn_x      = 4541239648278065 * 701e18 / 296771752 / 2**64 = 581500584.766017533363270505955415005042190229659676220491523
        //           earn_x_sub  = 4541239648278065 * 701e18 / 296771752 / 2**64 = 581500584.766017533363270505955415005042190229659676220491523
        //
        //           earn_y      = 13278814667749784 * 779531e6 / 296771752 / 2**64 = 1.8908210002218903501728143334071499784764070319492513392714860291
        //           earn_y_sub  = 13278814667749784 * 779531e6 / 296771752 / 2**64 = 1.8908210002218903501728143334071499784764070319492513392714860291
        assertEq(RRLL.tokenX.cumulativeEarnedPerMLiq, 581500584);
        assertEq(RRLL.tokenX.subtreeCumulativeEarnedPerMLiq, 581500584);
        assertEq(RRLL.tokenY.cumulativeEarnedPerMLiq, 1);
        assertEq(RRLL.tokenY.subtreeCumulativeEarnedPerMLiq, 1);

        // mLiq
        assertEq(root.mLiq, 8430);
        assertEq(R.mLiq, 377);
        assertEq(RR.mLiq, 9082734);
        assertEq(RL.mLiq, 3845);
        assertEq(RRL.mLiq, 45346);
        assertEq(RRLL.mLiq, 287637599);

        // subtreeMLiq
        assertEq(root.subtreeMLiq, 324212503); // 8430*16 + 377*8 + 9082734*4 + 3845*4 + 45346*2 + 287637599*1
        assertEq(R.subtreeMLiq, 324077623); // 377*8 + 9082734*4 + 3845*4 + 45346*2 + 287637599*1
        assertEq(RR.subtreeMLiq, 324059227); // 9082734*4 + 45346*2 + 287637599*1
        assertEq(RL.subtreeMLiq, 15380); // 3845*4
        assertEq(RRL.subtreeMLiq, 287728291); // 45346*2 + 287637599*1
        assertEq(RRLL.subtreeMLiq, 287637599); // 287637599*1

        // T2876298273
        fees.X += 16463537718422861220174597; // 978567.9% APR as Q192.64 T2876298273 - T98273
        fees.Y += 3715979586694123491881712207; // 220872233.1% APR as Q192.64 T2876298273 - T98273

        // Apply change that requires fee calculation
        // remove_mLiq
        liqTree.removeMLiq(range(8, 12), 2734, fees); // RRLL, RL

        // root
        //           total_mLiq = 324212503
        //
        //           earn_x      = 16463537718422861220174597 * 492e18 / 324212503 / 2**64  = 1354374549470516050.18864221581152444619216774937383131887026
        //           earn_x_sub  = 16463537718422861220174597 * 3033e18 / 324212503 / 2**64 = 8349223594601778821.58973951332592204329439996717648453279172
        //
        //           earn_y      = 3715979586694123491881712207 * 254858e6 / 324212503 / 2**64  = 158351473403.760477087118657111090258803416110827691474619042
        //           earn_y_sub  = 3715979586694123491881712207 * 1143822e6 / 324212503 / 2**64 = 710693401861.570429112455707155049015549996557766096092261976
        assertEq(root.tokenX.cumulativeEarnedPerMLiq, 1354374549844117328); // 373601278 + 1354374549470516050 = 1354374549844117328
        assertEq(root.tokenX.subtreeCumulativeEarnedPerMLiq, 8349223596904894020); // 2303115199 + 8349223594601778821 = 8349223596904894020
        assertEq(root.tokenY.cumulativeEarnedPerMLiq, 158351473403); // 0 + 158351473403 = 158351473403
        assertEq(root.tokenY.subtreeCumulativeEarnedPerMLiq, 710693401863); // 2 + 710693401861 = 710693401863

        // R
        //           total_mLiq = 324077623 + 8430 * 8 = 324145063
        //
        //           earn_x      = 16463537718422861220174597 * 998e18 / 324145063 / 2**64  = 2747859799177149412.40503918202324257122793136834755591677703
        //           earn_x_sub  = 16463537718422861220174597 * 2541e18 / 324145063 / 2**64 = 6996304358425988634.18958372897901740830678718133380719892830
        //
        //           earn_y      = 3715979586694123491881712207 * 353e6 / 324145063 / 2**64    = 219375887.687723491736647414380713113554572979392890952782027
        //           earn_y_sub  = 3715979586694123491881712207 * 888964e6 / 324145063 / 2**64 = 552456845955.890725518915105035513462543703722529807118835474
        assertEq(R.tokenX.cumulativeEarnedPerMLiq, 2747859799935140577); // 757991165 + 2747859799177149412 = 2747859799935140577
        assertEq(R.tokenX.subtreeCumulativeEarnedPerMLiq, 6996304360355904016); // 1929915382 + 6996304358425988634 = 6996304360355904016
        assertEq(R.tokenY.cumulativeEarnedPerMLiq, 219375887); // 0 + 219375887 = 219375887 = 219375887
        assertEq(R.tokenY.subtreeCumulativeEarnedPerMLiq, 552456845956); // 1 + 552456845955 = 552456845956

        // RR
        //           total_mLiq = 324059227 + (377 + 8430) * 4 = 324094455
        //
        //           earn_x      = 16463537718422861220174597 * 765e18 / 324094455 / 2**64 = 2106654304105573173.10473569019029577351750175393657598084186
        //           earn_x_sub  = 16463537718422861220174597 * 1519e18 / 324094455 / 2**64 = 4183016846975641372.47855361228635199996481720814334498679581
        //
        //           earn_y      = 3715979586694123491881712207 * 99763e6 / 324094455 / 2**64  = 62008538706.1288411875002441524622314240784801570453009535875
        //           earn_y_sub  = 3715979586694123491881712207 * 888059e6 / 324094455 / 2**64 = 551980602776.841840924293368501262560029627326862519099461143
        assertEq(RR.tokenX.cumulativeEarnedPerMLiq, 2106654304686669588); // 581096415 + 2106654304105573173 = 2106654304686669588
        assertEq(RR.tokenX.subtreeCumulativeEarnedPerMLiq, 4183016848129478568); // 1153837196 + 4183016846975641372 = 4183016848129478568
        assertEq(RR.tokenY.cumulativeEarnedPerMLiq, 62008538706); // 0 + 62008538706 = 62008538706
        assertEq(RR.tokenY.subtreeCumulativeEarnedPerMLiq, 551980602777); // 1 + 551980602776 = 551980602777

        // RL
        //           total_mLiq = 15380 + (377 + 8430) * 4 = 50608
        //
        //           earn_x      = 16463537718422861220174597 * 24e18 / 50608 / 2**64 = 423248577958689008325.429426909965566945601510047930853109815
        //           earn_x_sub  = 16463537718422861220174597 * 24e18 / 50608 / 2**64 = 423248577958689008325.429426909965566945601510047930853109815
        //
        //           earn_y      = 3715979586694123491881712207 * 552e6 / 50608 / 2**64 = 2197219781185.45157550848350683783177940360867452683580030548
        //           earn_y_sub  = 3715979586694123491881712207 * 552e6 / 50608 / 2**64 = 2197219781185.45157550848350683783177940360867452683580030548
        assertEq(RL.tokenX.cumulativeEarnedPerMLiq, 423248578107618890129); // 148929881804 + 423248577958689008325 = 423248578107618890129
        assertEq(RL.tokenX.subtreeCumulativeEarnedPerMLiq, 423248578107618890129); // 148929881804 + 423248577958689008325 = 423248578107618890129
        assertEq(RL.tokenY.cumulativeEarnedPerMLiq, 2197219781195); // 10 + 2197219781185 = 2197219781195
        assertEq(RL.tokenY.subtreeCumulativeEarnedPerMLiq, 2197219781195); // 10 + 2197219781185 = 2197219781195

        // RRL
        //           total_mLiq = 287728291 + (9082734 + 377 + 8430) * 2 = 305911373
        //
        //           earn_x      = 16463537718422861220174597 * 53e18 / 305911373 / 2**64 = 154626414974589533.957746783298485424790431468186321359344549
        //           earn_x_sub  = 16463537718422861220174597 * 754e18 / 305911373 / 2**64 = 2199779563978122803.85171838881241528852802503797143971595830
        //
        //           earn_y      = 3715979586694123491881712207 * 8765e6 / 305911373 / 2**64 = 5771781665.52844938596716448955303604219154769320799186650875
        //           earn_y_sub  = 3715979586694123491881712207 * 788296e6 / 305911373 / 2**64 = 519095539054.126016789546137872983468330339792397614050929992
        assertEq(RRL.tokenX.cumulativeEarnedPerMLiq, 154626415017241476); // 42651943 + 154626414974589533 = 154626415017241476 (sol losses 1 wei)
        assertEq(RRL.tokenX.subtreeCumulativeEarnedPerMLiq, 2199779564584907057); // 606784254 + 2199779563978122803 = 2199779564584907057
        assertEq(RRL.tokenY.cumulativeEarnedPerMLiq, 5771781665); // 0 + 5771781665 = 5771781665
        assertEq(RRL.tokenY.subtreeCumulativeEarnedPerMLiq, 519095539055); // 1 + 519095539054 = 519095539055

        // RRLL
        //           total_mLiq = 287637599 + (45346 + 9082734 + 377 + 8430) * 1 = 296774486
        //
        //           earn_x      = 16463537718422861220174597 * 701e18 / 296774486 / 2**64 = 2108117905415037748.37451632639936795389368532390933657093156
        //           earn_x_sub  = 16463537718422861220174597 * 701e18 / 296774486 / 2**64 = 2108117905415037748.37451632639936795389368532390933657093156
        //
        //           earn_y      = 3715979586694123491881712207 * 779531e6 / 296774486 / 2**64 = 529127613134.050803777279185858502873428448836282593499892809
        //           earn_y_sub  = 3715979586694123491881712207 * 779531e6 / 296774486 / 2**64 = 529127613134.050803777279185858502873428448836282593499892809
        assertEq(RRLL.tokenX.cumulativeEarnedPerMLiq, 2108117905996538332); // 581500584 + 2108117905415037748 = 2108117905996538332
        assertEq(RRLL.tokenX.subtreeCumulativeEarnedPerMLiq, 2108117905996538332); // 581500584 + 2108117905415037748 = 2108117905996538332
        assertEq(RRLL.tokenY.cumulativeEarnedPerMLiq, 529127613135); // 1 + 529127613134 = 529127613135
        assertEq(RRLL.tokenY.subtreeCumulativeEarnedPerMLiq, 529127613135); // 1 + 529127613134 = 529127613135

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
        fees.X += 11381610389149375791104; // 307% APR as Q192.64 T9214298113 - T2876298273
        fees.Y += 185394198934916215865344; // 5000.7% APR as Q192.64 T9214298113 - T2876298273

        // Apply change that requires fee calculation
        // addTLiq
        liqTree.addTLiq(range(8, 12), 1000, fees, 1000e18, 1000e6); // RRLL, RL

        // root
        //           total_mLiq = 324198833
        //
        //           earn_x      = 11381610389149375791104 * 492e18 / 324198833 / 2**64  = 936348777891386.743735803607164207960477914490210395050990205
        //           earn_x_sub  = 11381610389149375791104 * 3033e18 / 324198833 / 2**64 = 5772247649074341.45071278931001837956123885091221164266189693
        //
        //           earn_y      = 185394198934916215865344 * 254858e6 / 324198833 / 2**64  = 7900657.61872699474175109887651599451346454839027751836478695
        //           earn_y_sub  = 185394198934916215865344 * 1143822e6 / 324198833 / 2**64 = 35458749.5733606501640098620374258523427949943453374491326438
        assertEq(root.tokenX.cumulativeEarnedPerMLiq, 1355310898622008714); // 373601278 + 1354374549470516050 + 936348777891386 = 1355310898622008714
        assertEq(root.tokenX.subtreeCumulativeEarnedPerMLiq, 8354995844553968361); // 2303115199 + 8349223594601778821 + 5772247649074341 = 8354995844553968361
        assertEq(root.tokenY.cumulativeEarnedPerMLiq, 158359374060); // 0 + 158351473403 + 7900657 = 158359374060
        assertEq(root.tokenY.subtreeCumulativeEarnedPerMLiq, 710728860612); // 2 + 710693401861 + 35458749 = 710728860612

        // R
        //           total_mLiq = 324063953 + 8430 * 8 = 324131393
        //
        //           earn_x      = 11381610389149375791104 * 998e18 / 324131393 / 2**64  = 1899736810880077.58842507649572740061066261792173891653870132
        //           earn_x_sub  = 11381610389149375791104 * 2541e18 / 324131393 / 2**64 = 4836905046539355.86391595127819972440049470154222303299082171
        //
        //           earn_y      = 185394198934916215865344 * 353e6 / 324131393 / 2**64    = 10945.359436035932129843115196215424291564802240553108041589788249
        //           earn_y_sub  = 185394198934916215865344 * 888964e6 / 324131393 / 2**64 = 27563825.7951735024642318840149814403397354471925525584619938
        assertEq(R.tokenX.cumulativeEarnedPerMLiq, 2749759536746020654); // 757991165 + 2747859799177149412 + 1899736810880077 = 2749759536746020654
        assertEq(R.tokenX.subtreeCumulativeEarnedPerMLiq, 7001141265402443371); // 1929915382 + 6996304358425988634 + 4836905046539355 = 7001141265402443371
        assertEq(R.tokenY.cumulativeEarnedPerMLiq, 219386832); // 0 + 219375887 + 10945 = 219386832
        assertEq(R.tokenY.subtreeCumulativeEarnedPerMLiq, 552484409781); // 1 + 552456845955 + 27563825 = 552484409781

        // RR
        //           total_mLiq = 324056493 + (377 + 8430) * 4 = 324091721
        //
        //           earn_x      = 11381610389149375791104 * 765e18 / 324091721 / 2**64  = 1456389336983247.97581853577374895245788594982344519686141566
        //           earn_x_sub  = 11381610389149375791104 * 1519e18 / 324091721 / 2**64 = 2891837127944514.60819392920303876965167157879975588762417044
        //
        //           earn_y      = 185394198934916215865344 * 99763e6 / 324091721 / 2**64  = 3093698.46401352576654665825318763474490453834363760251685046
        //           earn_y_sub  = 185394198934916215865344 * 888059e6 / 324091721 / 2**64 = 27539135.3934162733549879091613880669579421169863823827823111
        assertEq(RR.tokenX.cumulativeEarnedPerMLiq, 2108110694023652835); // 581096415 + 2106654304105573173+ 1456389336983247 = 2108110694023652835
        assertEq(RR.tokenX.subtreeCumulativeEarnedPerMLiq, 4185908685257423082); // 1153837196 + 4183016846975641372 + 2891837127944514 = 4185908685257423082
        assertEq(RR.tokenY.cumulativeEarnedPerMLiq, 62011632404); // 0 + 62008538706 + 3093698 = 62011632404
        assertEq(RR.tokenY.subtreeCumulativeEarnedPerMLiq, 552008141912); // 1 + 551980602776 + 27539135 = 552008141912

        // RL
        //           total_mLiq = 4444 + (377 + 8430) * 4 = 39672
        //
        //           earn_x      = 11381610389149375791104 * 24e18 / 39672 / 2**64 = 373259731104033296.286645111573225645606473079249848759830611
        //           earn_x_sub  = 11381610389149375791104 * 24e18 / 39672 / 2**64 = 373259731104033296.286645111573225645606473079249848759830611
        //
        //           earn_y      = 185394198934916215865344 * 552e6 / 39672 / 2**64 = 139839995.304998697233270837982279275016069267997580157289776
        //           earn_y_sub  = 185394198934916215865344 * 552e6 / 39672 / 2**64 = 139839995.304998697233270837982279275016069267997580157289776
        assertEq(RL.tokenX.cumulativeEarnedPerMLiq, 423621837838722923425); // 148929881804 + 423248577958689008325 + 373259731104033296 = 423621837838722923425
        assertEq(RL.tokenX.subtreeCumulativeEarnedPerMLiq, 423621837838722923425); // 148929881804 + 423248577958689008325 + 373259731104033296 = 423621837838722923425
        assertEq(RL.tokenY.cumulativeEarnedPerMLiq, 2197359621190); // 10 + 2197219781185 + 139839995 = 2197359621190
        assertEq(RL.tokenY.subtreeCumulativeEarnedPerMLiq, 2197359621190); // 10 + 2197219781185 + 139839995 = 2197359621190

        // RRL
        //           total_mLiq = 287725557 + (9082734 + 377 + 8430) * 2 = 305908639
        //
        //           earn_x      = 11381610389149375791104 * 53e18 / 305908639 / 2**64  = 106897640711262.335596794608928382455998365904272484439381916
        //           earn_x_sub  = 11381610389149375791104 * 754e18 / 305908639 / 2**64 = 1520770209363996.24603741764400000701552392248719723145837669
        //
        //           earn_y      = 185394198934916215865344 * 8765e6 / 305908639 / 2**64   = 287962.93864210284405202260308978443477406072046236000546555339354
        //           earn_y_sub  = 185394198934916215865344 * 788296e6 / 305908639 / 2**64 = 25898463.5116731435886860479093285465823905270619049107665115
        assertEq(RRL.tokenX.cumulativeEarnedPerMLiq, 154733312657952738); // 42651943 + 154626414974589533 + 106897640711262 = 154733312657952738
        assertEq(RRL.tokenX.subtreeCumulativeEarnedPerMLiq, 2201300334794271053); // 606784254 + 2199779563978122803 + 1520770209363996 = 2201300334794271053
        assertEq(RRL.tokenY.cumulativeEarnedPerMLiq, 5772069627); // 0 + 5771781665 + 287962 = 5772069627
        assertEq(RRL.tokenY.subtreeCumulativeEarnedPerMLiq, 519121437518); // 1 + 519095539054 + 25898463 = 519121437518

        // RRLL
        //           total_mLiq = 287634865 + (45346 + 9082734 + 377 + 8430) * 1 = 296771752
        //
        //           earn_x      = 11381610389149375791104 * 701e18 / 296771752 / 2**64 = 1457402297493569.71876500861500730007660377831377967536479010
        //           earn_x_sub  = 11381610389149375791104 * 701e18 / 296771752 / 2**64 = 1457402297493569.71876500861500730007660377831377967536479010
        //
        //           earn_y      = 185394198934916215865344 * 779531e6 / 296771752 / 2**64 = 26398986.1622835510939886934876573358559478744206759947961624
        //           earn_y_sub  = 185394198934916215865344 * 779531e6 / 296771752 / 2**64 = 26398986.1622835510939886934876573358559478744206759947961624
        assertEq(RRLL.tokenX.cumulativeEarnedPerMLiq, 2109575308294031901); // 581500584 + 2108117905415037748 + 1457402297493569 = 2109575308294031901
        assertEq(RRLL.tokenX.subtreeCumulativeEarnedPerMLiq, 2109575308294031901); // 581500584 + 2108117905415037748 + 1457402297493569 = 2109575308294031901
        assertEq(RRLL.tokenY.cumulativeEarnedPerMLiq, 529154012121); // 1 + 529127613134 + 26398986 = 529154012121
        assertEq(RRLL.tokenY.subtreeCumulativeEarnedPerMLiq, 529154012121); // 1 + 529127613134 + 26398986 = 529154012121

        // tLiq
        assertEq(root.tLiq, 4430);
        assertEq(R.tLiq, 77);
        assertEq(RR.tLiq, 82734);
        assertEq(RL.tLiq, 1111);
        assertEq(RRL.tLiq, 5346);
        assertEq(RRLL.tLiq, 7635865);

        // borrow_x
        assertEq(root.tokenX.borrow, 492e18);
        assertEq(R.tokenX.borrow, 998e18);
        assertEq(RR.tokenX.borrow, 765e18);
        assertEq(RL.tokenX.borrow, 824e18); // 1000e18/5*4 + 24e18
        assertEq(RRL.tokenX.borrow, 53e18); // 53e18 + 1000e18/5
        assertEq(RRLL.tokenX.borrow, 901e18); // 1000e18/5 + 701e18

        // subtree_borrow_x
        assertEq(root.tokenX.subtreeBorrow, 4033e18); // 3033e18 + 1000e18
        assertEq(R.tokenX.subtreeBorrow, 3541e18); // 2541e18 + 1000e18
        assertEq(RR.tokenX.subtreeBorrow, 1719e18); // 765e18 + 954e18
        assertEq(RL.tokenX.subtreeBorrow, 824e18); // 1000e18/5*4 + 24e18
        assertEq(RRL.tokenX.subtreeBorrow, 954e18); // 53e18 + 901e18
        assertEq(RRLL.tokenX.subtreeBorrow, 901e18); // 1000e18/5 + 701e18

        // borrow_y
        assertEq(root.tokenY.borrow, 254858e6);
        assertEq(R.tokenY.borrow, 353e6);
        assertEq(RR.tokenY.borrow, 99763e6);
        assertEq(RL.tokenY.borrow, 1352000000); // 552e6 + 1000e6/5*4
        assertEq(RRL.tokenY.borrow, 8765e6);
        assertEq(RRLL.tokenY.borrow, 779731000000); // 779531e6 + 1000e6/5

        // subtree_borrow_y
        assertEq(root.tokenY.subtreeBorrow, 1144822000000); // 254858e6 + 889964000000
        assertEq(R.tokenY.subtreeBorrow, 889964000000); // 353e6 + 888259000000 + 1352000000
        assertEq(RR.tokenY.subtreeBorrow, 888259000000); // 99763e6 + 788496000000
        assertEq(RL.tokenY.subtreeBorrow, 1352000000); // 1000e6/5*4 + 552e6
        assertEq(RRL.tokenY.subtreeBorrow, 788496000000); // 8765e6 + 779731000000
        assertEq(RRLL.tokenY.subtreeBorrow, 779731000000); // 1000e6/5 + 779531e6

        // T32876298273
        // 3.3) addTLiq
        fees.X += 2352954287417905205553; // 17% APR as Q192.64 T32876298273 - T9214298113
        fees.Y += 6117681147286553534438; // 44.2% APR as Q192.64 T32876298273 - T9214298113

        // Apply change that requires fee calculation
        // removeTLiq
        liqTree.removeTLiq(range(8, 12), 1000, fees, 1000e18, 1000e6); // RRLL, RL

        // root
        //           total_mLiq = 324198833
        //
        //           earn_x      = 2352954287417905205553 * 492e18 / 324198833 / 2**64  = 193574177654021.169606366690127570750614868262308175138961180
        //           earn_x_sub  = 2352954287417905205553 * 4033e18 / 324198833 / 2**64 = 1586757435932250.76630584727903352202688976362172534621022447
        //
        //           earn_y      = 6117681147286553534438 * 254858e6 / 324198833 / 2**64  = 260707.74837037839600245251693715160678794344236990061534290681026
        //           earn_y_sub  = 6117681147286553534438 * 1144822000000 / 324198833 / 2**64 = 1171099.06655813565227820863125749937920797851188031908850456
        assertEq(root.tokenX.cumulativeEarnedPerMLiq, 1355504472799662735); // 373601278 + 1354374549470516050 + 936348777891386 + 193574177654021 = 1355504472799662735
        assertEq(root.tokenX.subtreeCumulativeEarnedPerMLiq, 8356582601989900611); // 8354995844553968361 + 1586757435932250 = 8356582601989900611
        assertEq(root.tokenY.cumulativeEarnedPerMLiq, 158359634767); // 0 + 158351473403 + 7900657 + 260707 = 158359634767
        assertEq(root.tokenY.subtreeCumulativeEarnedPerMLiq, 710730031711); // 710728860612 + 1171099 = 710730031711

        // R
        //           total_mLiq = 324063953 + 8430 * 8 = 324131393
        //
        //           earn_x      = 2352954287417905205553 * 998e18 / 324131393 / 2**64  = 392738261220692.635199129066166314911263418663640357414414483
        //           earn_x_sub  = 2352954287417905205553 * 3541e18 / 324131393 / 2**64 = 1393473129240954.53030071745821134378836048646087225010465098
        //
        //           earn_y      = 6117681147286553534438 * 353e6 / 324131393 / 2**64    = 361.17753121077324707993230558447820693195086120933424789750836934
        //           earn_y_sub  = 6117681147286553534438 * 889964000000 / 324131393 / 2**64 = 910580.73763870992086188349690420556077616633497253242095143948559
        assertEq(R.tokenX.cumulativeEarnedPerMLiq, 2750152275007241346); // 757991165 + 2747859799177149412 + 1899736810880077 + 392738261220692 = 2750152275007241346
        assertEq(R.tokenX.subtreeCumulativeEarnedPerMLiq, 7002534738531684325); // 7001141265402443371 + 1393473129240954 = 7002534738531684325
        assertEq(R.tokenY.cumulativeEarnedPerMLiq, 219387193); // 0 + 219375887 + 10945 + 361 = 219387193
        assertEq(R.tokenY.subtreeCumulativeEarnedPerMLiq, 552485320361); // 552484409781 + 910580 = 552485320361

        // RR
        //           total_mLiq = 324056493 + (377 + 8430) * 4 = 324091721
        //
        //           earn_x      = 2352954287417905205553 * 765e18 / 324091721 / 2**64  = 301083714644757.116282263044928314612316183509300881282164628
        //           earn_x_sub  = 2352954287417905205553 * 1719e18 / 324091721 / 2**64 = 676552817613513.049528379312721271658263424120899627351687576
        //
        //           earn_y      = 6117681147286553534438 * 99763e6 / 324091721 / 2**64  = 102086.58565055261555338276382365173781133864709615634713615821960
        //           earn_y_sub  = 6117681147286553534438 * 888259000000 / 324091721 / 2**64 = 908947.49038595687518250474034695296830049071630749617343921858795
        assertEq(RR.tokenX.cumulativeEarnedPerMLiq, 2108411777738297592); // 581096415 + 2106654304105573173+ 1456389336983247 + 301083714644757 = 2108411777738297592
        assertEq(RR.tokenX.subtreeCumulativeEarnedPerMLiq, 4186585238075036595); // 1153837196 + 4183016846975641372 + 2891837127944514 + 676552817613513 = 4186585238075036595
        assertEq(RR.tokenY.cumulativeEarnedPerMLiq, 62011734490); // 0 + 62008538706 + 3093698 + 102086 = 62011734490
        assertEq(RR.tokenY.subtreeCumulativeEarnedPerMLiq, 552009050859); // 552008141912 + 908947 = 552009050859

        // RL
        //           total_mLiq = 4444 + (377 + 8430) * 4 = 39672
        //
        //           earn_x      = 2352954287417905205553 * 824e18 / 39672 / 2**64 = 2649335042027527808.18932829767975407399630436168941886080299
        //           earn_x_sub  = 2352954287417905205553 * 824e18 / 39672 / 2**64 = 2649335042027527808.18932829767975407399630436168941886080299
        //
        //           earn_y      = 6117681147286553534438 * 1352000000 / 39672 / 2**64 = 11302114.7326883079506643583639446655013480155495316373121596
        //           earn_y_sub  = 6117681147286553534438 * 1352000000 / 39672 / 2**64 = 11302114.7326883079506643583639446655013480155495316373121596
        assertEq(RL.tokenX.cumulativeEarnedPerMLiq, 426271172880750451233); // 423621837838722923425 + 2649335042027527808 = 426271172880750451233
        assertEq(RL.tokenX.subtreeCumulativeEarnedPerMLiq, 426271172880750451233); // 423621837838722923425 + 2649335042027527808 = 426271172880750451233
        assertEq(RL.tokenY.cumulativeEarnedPerMLiq, 2197370923304); // 10 + 2197219781185 + 139839995 + 11302114 = 2197370923304
        assertEq(RL.tokenY.subtreeCumulativeEarnedPerMLiq, 2197370923304); // 10 + 2197219781185 + 139839995 + 11302114 = 2197370923304

        // RRL
        //           total_mLiq = 287725557 + (9082734 + 377 + 8430) * 2 = 305908639
        //
        //           earn_x      = 2352954287417905205553 * 53e18 / 305908639 / 2**64   = 22099268330799.1616184419285239088656103478160451926038962236
        //           earn_x_sub  = 2352954287417905205553 * 954e18 / 305908639 / 2**64 = 397786829954384.909131954713430359580986260688813466870132026
        //
        //           earn_y      = 6117681147286553534438 * 8765e6 / 305908639 / 2**64   = 9502.2684149166432853337655386227368949210477797554902569919214852
        //           earn_y_sub  = 6117681147286553534438 * 788496000000 / 305908639 / 2**64 = 854820.38061473058344695183025007114098090889790599943476065055601
        assertEq(RRL.tokenX.cumulativeEarnedPerMLiq, 154755411926283537); // 42651943 + 154626414974589533 + 106897640711262 + 22099268330799 = 154755411926283537
        assertEq(RRL.tokenX.subtreeCumulativeEarnedPerMLiq, 2201698121624225437); // 606784254 + 2199779563978122803 + 1520770209363996 + 397786829954384 = 2201698121624225437
        assertEq(RRL.tokenY.cumulativeEarnedPerMLiq, 5772079129); // 0 + 5771781665 + 287962 + 9502 = 5772079129
        assertEq(RRL.tokenY.subtreeCumulativeEarnedPerMLiq, 519122292338); // 1 + 519095539054 + 25898463 + 854820 = 519122292338

        // RRLL
        //           total_mLiq = 287634865 + (45346 + 9082734 + 377 + 8430) * 1 = 296771752
        //
        //           earn_x      = 2352954287417905205553 * 901e18 / 296771752 / 2**64 = 387254076208370.890776883408161542546883713785168889467495269
        //           earn_x_sub  = 2352954287417905205553 * 901e18 / 296771752 / 2**64 = 387254076208370.890776883408161542546883713785168889467495269
        //
        //           earn_y      = 6117681147286553534438 * 779731000000 / 296771752 / 2**64 = 871343.41958898560698616633234585314916584979490452064064744862714
        //           earn_y_sub  = 6117681147286553534438 * 779731000000 / 296771752 / 2**64 = 871343.41958898560698616633234585314916584979490452064064744862714
        assertEq(RRLL.tokenX.cumulativeEarnedPerMLiq, 2109962562370240271); // 581500584 + 2108117905415037748 + 1457402297493569 + 387254076208370 = 2109962562370240271
        assertEq(RRLL.tokenX.subtreeCumulativeEarnedPerMLiq, 2109962562370240271); // 581500584 + 2108117905415037748 + 1457402297493569 + 387254076208370 = 2109962562370240271
        assertEq(RRLL.tokenY.cumulativeEarnedPerMLiq, 529154883464); // 1 + 529127613134 + 26398986 + 871343 = 529154883464
        assertEq(RRLL.tokenY.subtreeCumulativeEarnedPerMLiq, 529154883464); // 1 + 529127613134 + 26398986 + 871343 = 529154883464

        // tLiq
        assertEq(root.tLiq, 4430);
        assertEq(R.tLiq, 77);
        assertEq(RR.tLiq, 82734);
        assertEq(RL.tLiq, 111);
        assertEq(RRL.tLiq, 5346);
        assertEq(RRLL.tLiq, 7634865);

        // subtreeMLiq
        assertEq(root.subtreeMLiq, 324198833); // 8430*16 + 377*8 + 9082734*4 + 1111*4 + 45346*2 + 287634865*1
        assertEq(R.subtreeMLiq, 324063953); // 377*8 + 9082734*4 + 1111*4 + 45346*2 + 287634865*1
        assertEq(RR.subtreeMLiq, 324056493); // 9082734*4 + 45346*2 + 287634865*1
        assertEq(RL.subtreeMLiq, 4444); // 1111*4
        assertEq(RRL.subtreeMLiq, 287725557); // 45346*2 + 287634865*1
        assertEq(RRLL.subtreeMLiq, 287634865); // 287634865*1

        // borrow_x
        assertEq(root.tokenX.borrow, 492e18);
        assertEq(R.tokenX.borrow, 998e18);
        assertEq(RR.tokenX.borrow, 765e18);
        assertEq(RL.tokenX.borrow, 24e18);
        assertEq(RRL.tokenX.borrow, 53e18);
        assertEq(RRLL.tokenX.borrow, 701e18);

        // subtree_borrow_x
        assertEq(root.tokenX.subtreeBorrow, 3033e18); // 492e18 + 998e18 + 765e18 + 53e18 + 701e18 + 24e18
        assertEq(R.tokenX.subtreeBorrow, 2541e18); // 998e18 + 765e18 + 53e18 + 701e18 + 24e18
        assertEq(RR.tokenX.subtreeBorrow, 1519e18); // 765e18 + 53e18 + 701e18
        assertEq(RL.tokenX.subtreeBorrow, 24e18);
        assertEq(RRL.tokenX.subtreeBorrow, 754e18); // 53e18 + 701e18
        assertEq(RRLL.tokenX.subtreeBorrow, 701e18); // 701e18

        // borrow_y
        assertEq(root.tokenY.borrow, 254858e6);
        assertEq(R.tokenY.borrow, 353e6);
        assertEq(RR.tokenY.borrow, 99763e6);
        assertEq(RL.tokenY.borrow, 552e6);
        assertEq(RRL.tokenY.borrow, 8765e6);
        assertEq(RRLL.tokenY.borrow, 779531e6);

        // subtree_borrow_y
        assertEq(root.tokenY.subtreeBorrow, 1143822e6); // 254858e6 + 353e6 + 99763e6 + 8765e6 + 779531e6 + 552e6
        assertEq(R.tokenY.subtreeBorrow, 888964e6); // 353e6 + 99763e6 + 8765e6 + 779531e6 + 552e6
        assertEq(RR.tokenY.subtreeBorrow, 888059e6); // 99763e6 + 8765e6 + 779531e6
        assertEq(RL.tokenY.subtreeBorrow, 552e6);
        assertEq(RRL.tokenY.subtreeBorrow, 788296e6); // 8765e6 + 779531e6
        assertEq(RRLL.tokenY.subtreeBorrow, 779531e6); // 779531e6
    }

    function testLeftAndRightLegStoppingBelowPeak() public {
        FeeSnap memory fees;

        //   Range: (1, 4)
        //
        //                                  L(0-7)
        //                             __--  --__
        //                        __---          ---__
        //                      /                       \
        //                   LL(0-3)                     LR(4-7)
        //                 /   \                         /
        //               /       \                     /
        //             /           \                 /
        //           LLL(0-1)       LLR(2-3)       LRL(4-5)
        //              \                         /
        //               \                       /
        //           LLLR(1)                   LRLL(4)

        // 1st (1, 4)
        LiqNode storage root = liqTree.nodes[liqTree.root];

        LiqNode storage L = liqTree.nodes[LKey.wrap((8 << 24) | 0)];
        LiqNode storage LL = liqTree.nodes[LKey.wrap((4 << 24) | 0)];
        LiqNode storage LR = liqTree.nodes[LKey.wrap((4 << 24) | 4)];
        LiqNode storage LLL = liqTree.nodes[LKey.wrap((2 << 24) | 0)];
        LiqNode storage LLR = liqTree.nodes[LKey.wrap((2 << 24) | 2)];
        LiqNode storage LRL = liqTree.nodes[LKey.wrap((2 << 24) | 4)];
        LiqNode storage LLLR = liqTree.nodes[LKey.wrap((1 << 24) | 1)];
        LiqNode storage LRLL = liqTree.nodes[LKey.wrap((1 << 24) | 4)];

        // Pre-populate nodes w/o fee calculation
        liqTree.addWideRangeMLiq(432, fees);
        liqTree.addMLiq(range(0, 7), 98237498262, fees); // L
        liqTree.addMLiq(range(0, 3), 932141354, fees); // LL
        liqTree.addMLiq(range(4, 7), 151463465, fees); // LR
        liqTree.addMLiq(range(0, 1), 45754683688356, fees); // LLL
        liqTree.addMLiq(range(2, 3), 245346257245745, fees); // LLR
        liqTree.addMLiq(range(4, 5), 243457472, fees); // LRL
        liqTree.addMLiq(range(1, 1), 2462, fees); // LLLR
        liqTree.addMLiq(range(4, 4), 45656756785, fees); // LRLL

        liqTree.addTLiq(range(0, 7), 5645645, fees, 4357e18, 345345345e6); // L
        liqTree.addTLiq(range(0, 3), 3456835, fees, 293874927834e18, 2345346e6); // LL
        liqTree.addTLiq(range(4, 7), 51463465, fees, 23452e18, 12341235e6); // LR
        liqTree.addTLiq(range(0, 1), 23453467234, fees, 134235e18, 34534634e6); // LLL
        liqTree.addTLiq(range(2, 3), 456756745, fees, 1233463e18, 2341356e6); // LLR
        liqTree.addTLiq(range(4, 5), 3457472, fees, 45e18, 1324213563456457e6); // LRL
        liqTree.addTLiq(range(1, 1), 262, fees, 4567e18, 1235146e6); // LLLR
        liqTree.addTLiq(range(4, 4), 4564573, fees, 4564564e18, 6345135e6); // LRLL

        // Verify initial state
        // mLiq
        assertEq(root.mLiq, 432);
        assertEq(L.mLiq, 98237498262);
        assertEq(LL.mLiq, 932141354);
        assertEq(LR.mLiq, 151463465);
        assertEq(LLL.mLiq, 45754683688356);
        assertEq(LLR.mLiq, 245346257245745);
        assertEq(LRL.mLiq, 243457472);
        assertEq(LLLR.mLiq, 2462, "LLLR mLiq");
        assertEq(LRLL.mLiq, 45656756785);

        // tLiq
        assertEq(root.tLiq, 0);
        assertEq(L.tLiq, 5645645);
        assertEq(LL.tLiq, 3456835);
        assertEq(LR.tLiq, 51463465);
        assertEq(LLL.tLiq, 23453467234);
        assertEq(LLR.tLiq, 456756745);
        assertEq(LRL.tLiq, 3457472);
        assertEq(LLLR.tLiq, 262);
        assertEq(LRLL.tLiq, 4564573);

        // subtreeMLiq
        assertEq(root.subtreeMLiq, 583038259954677); // 432*16 + 98237498262*8 + 932141354*4 + 151463465*4 + 45754683688356*2 + 245346257245745*2 + 243457472*2 + 2462*1 + 45656756785*1 = 583038259954677
        assertEq(L.subtreeMLiq, 583038259947765); // 98237498262*8 + 932141354*4 + 151463465*4 + 45754683688356*2 + 245346257245745*2 + 243457472*2 + 2462*1 + 45656756785*1 = 583038259947765
        assertEq(LL.subtreeMLiq, 582205610436080); // 932141354*4 + 45754683688356*2 + 245346257245745*2 + 2462*1 = 582205610436080
        assertEq(LR.subtreeMLiq, 46749525589); // 151463465*4 + 243457472*2 + 45656756785*1 = 46749525589
        assertEq(LLL.subtreeMLiq, 91509367379174); // 45754683688356*2 + 2462*1 = 91509367379174
        assertEq(LLR.subtreeMLiq, 490692514491490); // 245346257245745*2 = 490692514491490
        assertEq(LRL.subtreeMLiq, 46143671729); // 243457472*2 + 45656756785*1 = 46143671729
        assertEq(LLLR.subtreeMLiq, 2462, "LLLR SubtreeMLiq"); // 2462*1 = 2462
        assertEq(LRLL.subtreeMLiq, 45656756785); // 45656756785*1 = 45656756785

        // borrow_x
        assertEq(root.tokenX.borrow, 0);
        assertEq(L.tokenX.borrow, 4357e18);
        assertEq(LL.tokenX.borrow, 293874927834e18);
        assertEq(LR.tokenX.borrow, 23452e18);
        assertEq(LLL.tokenX.borrow, 134235e18);
        assertEq(LLR.tokenX.borrow, 1233463e18);
        assertEq(LRL.tokenX.borrow, 45e18);
        assertEq(LLLR.tokenX.borrow, 4567e18);
        assertEq(LRLL.tokenX.borrow, 4564564e18);

        // subtree_borrow_x
        assertEq(root.tokenX.subtreeBorrow, 293880892517e18); // 0 + 4357e18 + 293874927834e18 + 23452e18 + 134235e18 + 1233463e18 + 45e18 + 4567e18 + 4564564e18 = 293880892517e18
        assertEq(L.tokenX.subtreeBorrow, 293880892517e18); // 4357e18 + 293874927834e18 + 23452e18 + 134235e18 + 1233463e18 + 45e18 + 4567e18 + 4564564e18 = 293880892517e18
        assertEq(LL.tokenX.subtreeBorrow, 293876300099e18); // 293874927834e18 + 134235e18 + 1233463e18 + 4567e18 = 293876300099e18
        assertEq(LR.tokenX.subtreeBorrow, 4588061e18); // 23452e18 + 45e18 + 4564564e18 = 4588061e18
        assertEq(LLL.tokenX.subtreeBorrow, 138802e18); // 134235e18 + 4567e18 = 138802e18
        assertEq(LLR.tokenX.subtreeBorrow, 1233463e18); // 1233463e18
        assertEq(LRL.tokenX.subtreeBorrow, 4564609e18); // 45e18 + 4564564e18 = 4564609e18
        assertEq(LLLR.tokenX.subtreeBorrow, 4567e18); // 4567e18
        assertEq(LRLL.tokenX.subtreeBorrow, 4564564e18); // 4564564e18

        // borrow_y
        assertEq(root.tokenY.borrow, 0);
        assertEq(L.tokenY.borrow, 345345345e6);
        assertEq(LL.tokenY.borrow, 2345346e6);
        assertEq(LR.tokenY.borrow, 12341235e6);
        assertEq(LLL.tokenY.borrow, 34534634e6);
        assertEq(LLR.tokenY.borrow, 2341356e6);
        assertEq(LRL.tokenY.borrow, 1324213563456457e6);
        assertEq(LLLR.tokenY.borrow, 1235146e6);
        assertEq(LRLL.tokenY.borrow, 6345135e6);

        // subtree_borrow_y
        assertEq(root.tokenY.subtreeBorrow, 1324213967944654e6); // 0 + 345345345e6 + 2345346e6 + 12341235e6 + 34534634e6 + 2341356e6 + 1324213563456457e6 + 1235146e6 + 6345135e6 = 1324213967944654e6
        assertEq(L.tokenY.subtreeBorrow, 1324213967944654e6); // 345345345e6 + 2345346e6 + 12341235e6 + 34534634e6 + 2341356e6 + 1324213563456457e6 + 1235146e6 + 6345135e6 = 1324213967944654e6
        assertEq(LL.tokenY.subtreeBorrow, 40456482e6); // 2345346e6 + 34534634e6 + 2341356e6 + 1235146e6 = 40456482e6
        assertEq(LR.tokenY.subtreeBorrow, 1324213582142827e6); // 12341235e6 + 1324213563456457e6 + 6345135e6 = 1324213582142827e6
        assertEq(LLL.tokenY.subtreeBorrow, 35769780e6); // 34534634e6 + 1235146e6 = 35769780e6
        assertEq(LLR.tokenY.subtreeBorrow, 2341356e6); // 2341356e6
        assertEq(LRL.tokenY.subtreeBorrow, 1324213569801592e6); // 1324213563456457e6 + 6345135e6 = 1324213569801592e6
        assertEq(LLLR.tokenY.subtreeBorrow, 1235146e6); // 1235146e6
        assertEq(LRLL.tokenY.subtreeBorrow, 6345135e6); // 6345135e6

        // Test fees while targeting (1, 4)
        // 1) Trigger fee update through path L->LL->LLR by updating LLR
        fees.X += 997278349210980290827452342352346;
        fees.Y += 7978726162930599238079167453467080976862;

        liqTree.addMLiq(range(2, 3), 564011300817682367503451461, fees); // LLR
        liqTree.removeMLiq(range(2, 3), 564011300817682367503451461, fees); // LLR

        // LLR
        //
        //   total_mLiq = 490692514491490 + (932141354 + 98237498262 + 432) * 2 = 490890853771586
        //
        //   earn_x      = 997278349210980290827452342352346 * 1233463e18 / 490890853771586 / 2**64 = 135843184601648135054031.953000417177564160084206701934727792
        //   earn_x_sub  = 997278349210980290827452342352346 * 1233463e18 / 490890853771586 / 2**64 = 135843184601648135054031.953000417177564160084206701934727792
        //
        //   earn_y      = 7978726162930599238079167453467080976862 * 2341356e6 / 490890853771586 / 2**64 = 2062986327173371860.88896572844074868101158495986576204342125
        //   earn_y_sub  = 7978726162930599238079167453467080976862 * 2341356e6 / 490890853771586 / 2**64 = 2062986327173371860.88896572844074868101158495986576204342125
        assertEq(LLR.tokenX.cumulativeEarnedPerMLiq, 135843184601648135054031);
        assertEq(LLR.tokenX.subtreeCumulativeEarnedPerMLiq, 135843184601648135054031);
        assertEq(LLR.tokenY.cumulativeEarnedPerMLiq, 2062986327173371860);
        assertEq(LLR.tokenY.subtreeCumulativeEarnedPerMLiq, 2062986327173371860);

        // LL
        //
        //   total_mLiq = 582205610436080 + (98237498262 + 432) * 4 = 582598560430856
        //
        //   earn_x      = 997278349210980290827452342352346 * 293874927834e18 / 582598560430856 / 2**64 = 27270292518041237351900241102.9072917119646623397725295368780
        //   earn_x_sub  = 997278349210980290827452342352346 * 293876300099e18 / 582598560430856 / 2**64 = 27270419858159151079872803581.0095490519975481585750941907483
        //
        //   earn_y      = 7978726162930599238079167453467080976862 * 2345346e6 / 582598560430856 / 2**64 = 1741210798541653346.44401134728453048205241418030400364012179
        //   earn_y_sub  = 7978726162930599238079167453467080976862 * 40456482e6 / 582598560430856 / 2**64 = 30035339489101405447.4912908710324004754969276780541880790817
        assertEq(LL.tokenX.cumulativeEarnedPerMLiq, 27270292518041237351900241102);
        assertEq(LL.tokenX.subtreeCumulativeEarnedPerMLiq, 27270419858159151079872803581);
        assertEq(LL.tokenY.cumulativeEarnedPerMLiq, 1741210798541653346);
        assertEq(LL.tokenY.subtreeCumulativeEarnedPerMLiq, 30035339489101405447);

        // L
        //
        //   total_mLiq = 583038259947765 + (432) * 8 = 583038259951221
        //
        //   earn_x      = 997278349210980290827452342352346 * 4357e18 / 583038259951221 / 2**64 = 404005403049228369014.124610642017839196445240663620779618212
        //   earn_x_sub  = 997278349210980290827452342352346 * 293880892517e18 / 583038259951221 / 2**64 = 27250279648794479314672290097.5284183991019310121509607727857
        //
        //   earn_y      = 7978726162930599238079167453467080976862 * 345345345e6 / 583038259951221 / 2**64 = 256194846273571639740.673516172246801895282064962841499611008
        //   earn_y_sub  = 7978726162930599238079167453467080976862 * 1324213967944654e6 / 583038259951221 / 2**64 = 982369673901053899051127131.509115296130579701967553185312315
        assertEq(L.tokenX.cumulativeEarnedPerMLiq, 404005403049228369014);
        assertEq(L.tokenX.subtreeCumulativeEarnedPerMLiq, 27250279648794479314672290097);
        assertEq(L.tokenY.cumulativeEarnedPerMLiq, 256194846273571639740);
        assertEq(L.tokenY.subtreeCumulativeEarnedPerMLiq, 982369673901053899051127131);

        // 2) Trigger fee update through path L->LR->LRL->LRLL by updating LRLL
        liqTree.addMLiq(range(4, 4), 45656756785, fees); // LRLL
        liqTree.removeMLiq(range(4, 4), 45656756785, fees); // LRLL

        // LRLL
        //   total_mLiq = 45656756785 + (243457472 + 151463465 + 98237498262 + 432) * 1 = 144289176416
        //
        //   earn_x      = 997278349210980290827452342352346 * 4564564e18 / 144289176416 / 2**64 = 1710260298962014449572659226.45857973175650767716107059096213
        //   earn_x_sub  = 997278349210980290827452342352346 * 4564564e18 / 144289176416 / 2**64 = 1710260298962014449572659226.45857973175650767716107059096213
        //
        //   earn_y      = 7978726162930599238079167453467080976862 * 6345135e6 / 144289176416 / 2**64 = 19020457094450723823822.1304935642458081127558849886746302550
        //   earn_y_sub  = 7978726162930599238079167453467080976862 * 6345135e6 / 144289176416 / 2**64 = 19020457094450723823822.1304935642458081127558849886746302550
        assertEq(LRLL.tokenX.cumulativeEarnedPerMLiq, 1710260298962014449572659226);
        assertEq(LRLL.tokenX.subtreeCumulativeEarnedPerMLiq, 1710260298962014449572659226);
        assertEq(LRLL.tokenY.cumulativeEarnedPerMLiq, 19020457094450723823822);
        assertEq(LRLL.tokenY.subtreeCumulativeEarnedPerMLiq, 19020457094450723823822);

        // LRL
        //   total_mLiq = 46143671729 + (151463465 + 98237498262 + 432) * 2 = 242921596047
        //
        //   earn_x      = 997278349210980290827452342352346 * 45e18 / 242921596047 / 2**64 = 10014817880995372310152.4742715985679179265308809095477236672
        //   earn_x_sub  = 997278349210980290827452342352346 * 4564609e18 / 242921596047 / 2**64 = 1015860618510053453450506120.72016150011730453772839221611958
        //
        //   earn_y      = 7978726162930599238079167453467080976862 * 1324213563456457e6 / 242921596047 / 2**64 = 2357793377238426581071757403793.96341043019973158984354448841
        //   earn_y_sub  = 7978726162930599238079167453467080976862 * 1324213569801592e6 / 242921596047 / 2**64 = 2357793388536088599903418420664.92708711347544674139375617462
        assertEq(LRL.tokenX.cumulativeEarnedPerMLiq, 10014817880995372310152);
        assertEq(LRL.tokenX.subtreeCumulativeEarnedPerMLiq, 1015860618510053453450506120);
        assertEq(LRL.tokenY.cumulativeEarnedPerMLiq, 2357793377238426581071757403793);
        assertEq(LRL.tokenY.subtreeCumulativeEarnedPerMLiq, 2357793388536088599903418420664);

        // LR
        //   total_mLiq = 46749525589 + (98237498262 + 432) * 4 = 439699520365
        //
        //   earn_x      = 997278349210980290827452342352346 * 23452e18 / 439699520365 / 2**64 = 2883504023897755903335799.02165969971328846599101621918354759
        //   earn_x_sub  = 997278349210980290827452342352346 * 4588061e18 / 439699520365 / 2**64 = 564117872905865676599639663.786245246727357690738865154506505
        //
        //   earn_y      = 7978726162930599238079167453467080976862 * 12341235e6 / 439699520365 / 2**64 = 12139937971620398360316.5575159331335181718549141795773004218
        //   earn_y_sub  = 7978726162930599238079167453467080976862 * 1324213582142827e6 / 439699520365 / 2**64 = 1302614426221619876588878010887.22237028229312127108609228047
        assertEq(LR.tokenX.cumulativeEarnedPerMLiq, 2883504023897755903335799);
        assertEq(LR.tokenX.subtreeCumulativeEarnedPerMLiq, 564117872905865676599639663);
        assertEq(LR.tokenY.cumulativeEarnedPerMLiq, 12139937971620398360316);
        assertEq(LR.tokenY.subtreeCumulativeEarnedPerMLiq, 1302614426221619876588878010887);

        // L
        // Borrows have not changed. Results should be the same!
        assertEq(L.tokenX.cumulativeEarnedPerMLiq, 404005403049228369014);
        assertEq(L.tokenX.subtreeCumulativeEarnedPerMLiq, 27250279648794479314672290097);
        assertEq(L.tokenY.cumulativeEarnedPerMLiq, 256194846273571639740);
        assertEq(L.tokenY.subtreeCumulativeEarnedPerMLiq, 982369673901053899051127131);

        // 3) Trigger fee update for remaining nodes by updating the range (1,3) LLLR, LLL
        //    For this last one, also update the rates to increment accumulated fees in L
        //    While previous step does not, meaning we also tested that nothing should have accumulated.
        //
        //    For un-accumulated nodes
        //    x_rate = 129987217567345826 + 997278349210980290827452342352346 = 997278349210980420814669909698172
        //    y_rate = 234346579834678237846892 + 7978726162930599238079167453467080976862 = 7978726162930599472425747288145318823754
        fees.X += 129987217567345826;
        fees.Y += 234346579834678237846892;

        liqTree.addTLiq(range(1, 3), 32, fees, 8687384723, 56758698); // LLLR, LLL
        liqTree.removeTLiq(range(1, 3), 32, fees, 8687384723, 56758698); // LLLR, LLL

        // LLLR
        //   total_mLiq = 2462 + (45754683688356 + 932141354 + 98237498262 + 432) * 1 = 45853853330866
        //
        //   earn_x      = 997278349210980420814669909698172 * 4567e18 / 45853853330866 / 2**64 = 5384580105567269319768.51254007088771506177689554397322456673
        //   earn_x_sub  = 997278349210980420814669909698172 * 4567e18 / 45853853330866 / 2**64 = 5384580105567269319768.51254007088771506177689554397322456673
        //
        //   earn_y      = 7978726162930599472425747288145318823754 * 1235146e6 / 45853853330866 / 2**64 = 11650814730151920570.8396639745369843707702302526968216514839
        //   earn_y_sub  = 7978726162930599472425747288145318823754 * 1235146e6 / 45853853330866 / 2**64 = 11650814730151920570.8396639745369843707702302526968216514839
        assertEq(LLLR.tokenX.cumulativeEarnedPerMLiq, 5384580105567269319768);
        assertEq(LLLR.tokenX.subtreeCumulativeEarnedPerMLiq, 5384580105567269319768);
        assertEq(LLLR.tokenY.cumulativeEarnedPerMLiq, 11650814730151920570);
        assertEq(LLLR.tokenY.subtreeCumulativeEarnedPerMLiq, 11650814730151920570);

        // LLL
        //   total_mLiq = 91509367379174 + (932141354 + 98237498262 + 432) * 2 = 91707706659270
        //
        //   earn_x      = 997278349210980420814669909698172 * 134235e18 / 91707706659270 / 2**64 = 79132812622096209716370.5876318860028597239769562864471324430
        //   earn_x_sub  = 997278349210980420814669909698172 * 138802e18 / 91707706659270 / 2**64 = 81825102674952122032641.7871976834727823250825007372997718729
        //
        //   earn_y      = 7978726162930599472425747288145318823754 * 34534634e6 / 91707706659270 / 2**64 = 162878162791446141833.294568661856722588591983837787778442557
        //   earn_y_sub  = 7978726162930599472425747288145318823754 * 35769780e6 / 91707706659270 / 2**64 = 168703570156678491951.753228258608716065007834501481165880576
        assertEq(LLL.tokenX.cumulativeEarnedPerMLiq, 79132812622096209716370);
        assertEq(LLL.tokenX.subtreeCumulativeEarnedPerMLiq, 81825102674952122032641);
        assertEq(LLL.tokenY.cumulativeEarnedPerMLiq, 162878162791446141833);
        assertEq(LLL.tokenY.subtreeCumulativeEarnedPerMLiq, 168703570156678491951);

        // LL
        //   Note: LL previously accumulated fees, so we use the new rate as provided. Then add to the previously accumulated fees.
        //         The results SHOULD be the same as if the two rates were added, and accumulated once.
        //         However, that is not the case. Due to decimal truncation that happens over two transactions. See below.
        //
        //   total_mLiq = 582205610436080 + (98237498262 + 432) * 4 = 582598560430856
        //
        //   Expected in 1 transaction
        //   earn_x      = 1299872175673458264503459867290698790837483436947198765949906360687986981 * 293874927834e18 / 582598560430856 / 2**64 = 35544634549344534575302731950184064775098096623320842527740739153078.75082067380701457525147559485733770210963
        //   earn_x_sub  = 1299872175673458264503459867290698790837483436947198765949906360687986981 * 293876300099e18 / 582598560430856 / 2**64 = 35544800526953748684785622304061478291909912715982970794626727543515.67837110616273194884758309091127470639015
        //
        //   earn_y      = 2343465798346782378468923640892347700326625400777465238079512798813357853648 * 2345346e6 / 582598560430856 / 2**64 = 511418473421538198191409430001729877691494201326333679.0963768041829950138557552907316220422703628558848163908
        //   earn_y_sub  = 2343465798346782378468923640892347700326625400777465238079512798813357853648 * 40456482e6 / 582598560430856 / 2**64 = 8821808067741790988384310101577867302175515556793408995.669016189358355860561774047790233928773909697150300378
        //
        //   Expected in 2 transactions
        //   earn_x      = 129987217567345826 * 293874927834e18 / 582598560430856 / 2**64 = 3554463454934.45344521569040863374143258749172847837137687025
        //   earn_x_sub  = 129987217567345826 * 293876300099e18 / 582598560430856 / 2**64 = 3554480052695.37485616392194040566938030042839994115185549318
        //
        //   earn_y      = 234346579834678237846892 * 2345346e6 / 582598560430856 / 2**64 = 51.141847342153819819140863544368355730624773075228977719082842282
        //   earn_y_sub  = 234346579834678237846892 * 40456482e6 / 582598560430856 / 2**64 = 882.18080677417909883842963957010802883055121959492790529434721584
        //
        //   acc_x       = 3554463454934 + 27270292518041237351900241102 = 27270292518041240906363696036
        //   acc_x_sub   = 3554480052695 + 27270419858159151079872803581 = 27270419858159154634352856276
        //
        //   acc_y       = 51 + 1741210798541653346 = 1741210798541653397
        //   acc_y_sub   = 882 + 30035339489101405447 = 30035339489101406329
        assertEq(LL.tokenX.cumulativeEarnedPerMLiq, 27270292518041240906363696036);
        assertEq(LL.tokenX.subtreeCumulativeEarnedPerMLiq, 27270419858159154634352856276);
        assertEq(LL.tokenY.cumulativeEarnedPerMLiq, 1741210798541653397);
        assertEq(LL.tokenY.subtreeCumulativeEarnedPerMLiq, 30035339489101406329);

        // L
        //   Note: (same situation as LL above)
        //
        //   total_mLiq = 583038259947765 + (432) * 8 = 583038259951221
        //
        //   earn_x      = 129987217567345826 * 4357e18 / 583038259951221 / 2**64 = 52658.857244912781888589346071378112785850967017095980665781805581
        //   acc_x       = 52658 + 404005403049228369014 = 404005403049228421672
        //   earn_x_sub  = 129987217567345826 * 293880892517e18 / 583038259951221 / 2**64 = 3551854938274.10144577461323882349951197727139690881248462550
        //   acc_x_sub   = 3551854938274 + 27250279648794479314672290097 = 27250279648794482866527228371
        //
        //   earn_y      = 234346579834678237846892 * 345345345e6 / 583038259951221 / 2**64 = 7524.8084430347809841211584947169489394855931019950463150426607553
        //   acc_y       = 7524 + 256194846273571639740 = 256194846273571647264
        //   earn_y_sub  = 234346579834678237846892 * 1324213967944654e6 / 583038259951221 / 2**64 = 28853599999.6598223755001570810194889233587464872923634206316
        //   acc_y_sub   = 28853599999 + 982369673901053899051127131 = 982369673901053927904727130
        assertEq(L.tokenX.cumulativeEarnedPerMLiq, 404005403049228421672);
        assertEq(L.tokenX.subtreeCumulativeEarnedPerMLiq, 27250279648794482866527228371);
        assertEq(L.tokenY.cumulativeEarnedPerMLiq, 256194846273571647264);
        assertEq(L.tokenY.subtreeCumulativeEarnedPerMLiq, 982369673901053927904727130);

        // 4) Confirm root fees are correct (although behavior leading to this state should have been previously tested at L and LL
        //   total_mLiq = 583038259954677
        //
        //   earn_x      = 997278349210980420814669909698172 * 0 / 583038259954677 / 2**64 = 0
        //   earn_x_sub  = 997278349210980420814669909698172 * 293880892517e18 / 583038259954677 / 2**64 = 27250279648632954930995939801.6330981070932019410874863041294
        //
        //   earn_y      = 7978726162930599472425747288145318823754 * 0 / 583038259954677 / 2**64 = 0
        //   earn_y_sub  = 7978726162930599472425747288145318823754 * 1324213967944654e6 / 583038259954677 / 2**64 = 982369673895230863062865876.398682260578858069936100777250356
        assertEq(root.tokenX.cumulativeEarnedPerMLiq, 0);
        assertEq(root.tokenX.subtreeCumulativeEarnedPerMLiq, 27250279648632954930995939801);
        assertEq(root.tokenY.cumulativeEarnedPerMLiq, 0);
        assertEq(root.tokenY.subtreeCumulativeEarnedPerMLiq, 982369673895230863062865875); // 1 wei lost
    }

    function testLeftAndRightLegStoppingAtOrAbovePeak() public {
        FeeSnap memory fees;

        //   Range: (0, 1)
        //
        //           LLL(0-1)
        //          /   \
        //         /     \
        //   LLLL(0) LLLR(1)

        // 4th (0, 1)
        LiqNode storage root = liqTree.nodes[liqTree.root];

        LiqNode storage L = liqTree.nodes[LKey.wrap((8 << 24) | 0)];
        LiqNode storage LL = liqTree.nodes[LKey.wrap((4 << 24) | 0)];
        LiqNode storage LLL = liqTree.nodes[LKey.wrap((2 << 24) | 0)];
        LiqNode storage LLLL = liqTree.nodes[LKey.wrap((1 << 24) | 0)];
        LiqNode storage LLLR = liqTree.nodes[LKey.wrap((1 << 24) | 1)];

        liqTree.addMLiq(range(0, 1), 8264, fees); // LLL
        liqTree.addMLiq(range(0, 0), 2582, fees); // LLLL
        liqTree.addMLiq(range(1, 1), 1111, fees); // LLLR

        liqTree.addTLiq(range(0, 1), 726, fees, 346e18, 132e6); // LLL
        liqTree.addTLiq(range(0, 0), 245, fees, 100e18, 222e6); // LLLL
        liqTree.addTLiq(range(1, 1), 342, fees, 234e18, 313e6); // LLLR

        // Verify initial tree state
        // mLiq
        assertEq(root.mLiq, 0);
        assertEq(L.mLiq, 0);
        assertEq(LL.mLiq, 0);
        assertEq(LLL.mLiq, 8264);
        assertEq(LLLL.mLiq, 2582);
        assertEq(LLLR.mLiq, 1111);

        // tLiq
        assertEq(root.tLiq, 0);
        assertEq(L.tLiq, 0);
        assertEq(LL.tLiq, 0);
        assertEq(LLL.tLiq, 726);
        assertEq(LLLL.tLiq, 245);
        assertEq(LLLR.tLiq, 342);

        // subtreeMLiq
        assertEq(root.subtreeMLiq, 20221);
        assertEq(L.subtreeMLiq, 20221);
        assertEq(LL.subtreeMLiq, 20221);
        assertEq(LLL.subtreeMLiq, 20221); // 8264*2 + 2582*1 + 1111*1 = 20221
        assertEq(LLLL.subtreeMLiq, 2582);
        assertEq(LLLR.subtreeMLiq, 1111);

        // borrow_x
        assertEq(root.tokenX.borrow, 0);
        assertEq(L.tokenX.borrow, 0);
        assertEq(LL.tokenX.borrow, 0);
        assertEq(LLL.tokenX.borrow, 346e18);
        assertEq(LLLL.tokenX.borrow, 100e18);
        assertEq(LLLR.tokenX.borrow, 234e18);

        // subtree_borrow_x
        assertEq(root.tokenX.subtreeBorrow, 680e18);
        assertEq(L.tokenX.subtreeBorrow, 680e18);
        assertEq(LL.tokenX.subtreeBorrow, 680e18);
        assertEq(LLL.tokenX.subtreeBorrow, 680e18); // 346e18 + 100e18 + 234e18 = 680e18
        assertEq(LLLL.tokenX.subtreeBorrow, 100e18);
        assertEq(LLLR.tokenX.subtreeBorrow, 234e18);

        // borrow_y
        assertEq(root.tokenY.borrow, 0);
        assertEq(L.tokenY.borrow, 0);
        assertEq(LL.tokenY.borrow, 0);
        assertEq(LLL.tokenY.borrow, 132e6);
        assertEq(LLLL.tokenY.borrow, 222e6);
        assertEq(LLLR.tokenY.borrow, 313e6);

        // subtree_borrow_y
        assertEq(root.tokenY.subtreeBorrow, 667e6);
        assertEq(L.tokenY.subtreeBorrow, 667e6);
        assertEq(LL.tokenY.subtreeBorrow, 667e6);
        assertEq(LLL.tokenY.subtreeBorrow, 667e6); // 132e6 + 222e6 + 313e6 = 667e6
        assertEq(LLLL.tokenY.subtreeBorrow, 222e6);
        assertEq(LLLR.tokenY.subtreeBorrow, 313e6);

        fees.X += 997278349210980290827452342352346;
        fees.Y += 7978726162930599238079167453467080976862;

        liqTree.addMLiq(range(0, 1), 1234567, fees);
        liqTree.removeMLiq(range(0, 1), 1234567, fees);

        // LLLR
        // (not updated)
        assertEq(LLLR.tokenX.cumulativeEarnedPerMLiq, 0);
        assertEq(LLLR.tokenX.subtreeCumulativeEarnedPerMLiq, 0);
        assertEq(LLLR.tokenY.cumulativeEarnedPerMLiq, 0);
        assertEq(LLLR.tokenY.subtreeCumulativeEarnedPerMLiq, 0);

        // LLLL
        // (not updated)
        assertEq(LLLL.tokenX.cumulativeEarnedPerMLiq, 0);
        assertEq(LLLL.tokenX.subtreeCumulativeEarnedPerMLiq, 0);
        assertEq(LLLL.tokenY.cumulativeEarnedPerMLiq, 0);
        assertEq(LLLL.tokenY.subtreeCumulativeEarnedPerMLiq, 0);

        // LLL
        //
        //   total_mLiq = 20221 + (0 + 0 + 0) * 2 = 20221
        //
        //   earn_x      = 997278349210980290827452342352346 * 346e18 / 20221 / 2**64 = 925060501618136152524292214349.283139885351240161578507230288
        //   earn_x_sub  = 997278349210980290827452342352346 * 680e18 / 20221 / 2**64 = 1818037980058764692822308398143.09981249144174367015429166646
        //
        //   earn_y      = 7978726162930599238079167453467080976862 * 132e6 / 20221 / 2**64 = 2823482754602022855424507.24027059608531549133804868998511635
        //   earn_y_sub  = 7978726162930599238079167453467080976862 * 667e6 / 20221 / 2**64 = 14267143919087494277031411.5853067241583744903218066380308530
        assertEq(LLL.tokenX.cumulativeEarnedPerMLiq, 925060501618136152524292214349);
        assertEq(LLL.tokenX.subtreeCumulativeEarnedPerMLiq, 1818037980058764692822308398143);
        assertEq(LLL.tokenY.cumulativeEarnedPerMLiq, 2823482754602022855424507);
        assertEq(LLL.tokenY.subtreeCumulativeEarnedPerMLiq, 14267143919087494277031411);

        // LL
        //   NOTE: subtree earn is not 'diluted' because liq contributing to total_mLiq along the path to the root is 0.
        //
        //   total_mLiq = 20221 + (0 + 0) * 4 = 20221
        //
        //   earn_x      = 997278349210980290827452342352346 * 0 / 20221 / 2**64 = 0
        //   earn_x_sub  = 997278349210980290827452342352346 * 680e18 / 20221 / 2**64 = 1818037980058764692822308398143.09981249144174367015429166646
        //
        //   earn_y      = 7978726162930599238079167453467080976862 * 0 / 20221 / 2**64 = 0
        //   earn_y_sub  = 7978726162930599238079167453467080976862 * 667e6 / 20221 / 2**64 = 14267143919087494277031411.5853067241583744903218066380308530
        assertEq(LL.tokenX.cumulativeEarnedPerMLiq, 0);
        assertEq(LL.tokenX.subtreeCumulativeEarnedPerMLiq, 1818037980058764692822308398143);
        assertEq(LL.tokenY.cumulativeEarnedPerMLiq, 0);
        assertEq(LL.tokenY.subtreeCumulativeEarnedPerMLiq, 14267143919087494277031411);

        // L
        //   NOTE: subtree earn is not 'diluted' because liq contributing to total_mLiq along the path to the root is 0.
        assertEq(L.tokenX.cumulativeEarnedPerMLiq, 0);
        assertEq(L.tokenX.subtreeCumulativeEarnedPerMLiq, 1818037980058764692822308398143);
        assertEq(L.tokenY.cumulativeEarnedPerMLiq, 0);
        assertEq(L.tokenY.subtreeCumulativeEarnedPerMLiq, 14267143919087494277031411);

        // root
        //   NOTE: subtree earn is not 'diluted' because liq contributing to total_mLiq along the path to the root is 0.
        assertEq(root.tokenX.cumulativeEarnedPerMLiq, 0);
        assertEq(root.tokenX.subtreeCumulativeEarnedPerMLiq, 1818037980058764692822308398143);
        assertEq(root.tokenY.cumulativeEarnedPerMLiq, 0);
        assertEq(root.tokenY.subtreeCumulativeEarnedPerMLiq, 14267143919087494277031411);

        // Verify ending tree state
        // Will be the same as initial state, because any changes to the tree (minus fees) were undone
        // mLiq
        assertEq(root.mLiq, 0);
        assertEq(L.mLiq, 0);
        assertEq(LL.mLiq, 0);
        assertEq(LLL.mLiq, 8264);
        assertEq(LLLL.mLiq, 2582);
        assertEq(LLLR.mLiq, 1111);

        // tLiq
        assertEq(root.tLiq, 0);
        assertEq(L.tLiq, 0);
        assertEq(LL.tLiq, 0);
        assertEq(LLL.tLiq, 726);
        assertEq(LLLL.tLiq, 245);
        assertEq(LLLR.tLiq, 342);

        // subtreeMLiq
        assertEq(root.subtreeMLiq, 20221);
        assertEq(L.subtreeMLiq, 20221);
        assertEq(LL.subtreeMLiq, 20221);
        assertEq(LLL.subtreeMLiq, 20221);
        assertEq(LLLL.subtreeMLiq, 2582);
        assertEq(LLLR.subtreeMLiq, 1111);

        // borrow_x
        assertEq(root.tokenX.borrow, 0);
        assertEq(L.tokenX.borrow, 0);
        assertEq(LL.tokenX.borrow, 0);
        assertEq(LLL.tokenX.borrow, 346e18);
        assertEq(LLLL.tokenX.borrow, 100e18);
        assertEq(LLLR.tokenX.borrow, 234e18);

        // subtree_borrow_x
        assertEq(root.tokenX.subtreeBorrow, 680e18);
        assertEq(L.tokenX.subtreeBorrow, 680e18);
        assertEq(LL.tokenX.subtreeBorrow, 680e18);
        assertEq(LLL.tokenX.subtreeBorrow, 680e18);
        assertEq(LLLL.tokenX.subtreeBorrow, 100e18);
        assertEq(LLLR.tokenX.subtreeBorrow, 234e18);

        // borrow_y
        assertEq(root.tokenY.borrow, 0);
        assertEq(L.tokenY.borrow, 0);
        assertEq(LL.tokenY.borrow, 0);
        assertEq(LLL.tokenY.borrow, 132e6);
        assertEq(LLLL.tokenY.borrow, 222e6);
        assertEq(LLLR.tokenY.borrow, 313e6);

        // subtree_borrow_y
        assertEq(root.tokenY.subtreeBorrow, 667e6);
        assertEq(L.tokenY.subtreeBorrow, 667e6);
        assertEq(LL.tokenY.subtreeBorrow, 667e6);
        assertEq(LLL.tokenY.subtreeBorrow, 667e6);
        assertEq(LLLL.tokenY.subtreeBorrow, 222e6);
        assertEq(LLLR.tokenY.subtreeBorrow, 313e6);
    }

    // Borrow
    // multipliers: 1, 2, 4, 8, 16
    // denominators: 1-16
    // multiplier cannot be larger than divisor and 16 is technically reserved for the root which is tested separately

    // x16

    function testBorrowSplitAtRoot() public {
        FeeSnap memory fees;
        // root has a range of 16
        // 100 / 16 = 6.25
        liqTree.addWideRangeMLiq(100e18, fees);
        liqTree.addWideRangeTLiq(10e18, fees, 100, 100);
        LiqNode storage root = liqTree.nodes[liqTree.root];
        assertEq(root.tokenX.borrow, 100);
        assertEq(root.tokenX.subtreeBorrow, 100);
        assertEq(root.tokenY.borrow, 100);
        assertEq(root.tokenY.subtreeBorrow, 100);
    }

    // x1 (1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16)

    function testBorrowSplitDividedByOneAndMultipliedByOne() public {
        FeeSnap memory fees;
        liqTree.addMLiq(range(1, 1), 200e18, fees);
        liqTree.addTLiq(range(1, 1), 19, fees, 100, 100);

        LiqNode storage multOne = liqTree.nodes[LKey.wrap((1 << 24) | 1)];
        assertEq(multOne.tokenX.borrow, 100);
        assertEq(multOne.tokenX.subtreeBorrow, 100);
        assertEq(multOne.tokenY.borrow, 100);
        assertEq(multOne.tokenY.subtreeBorrow, 100);
    }

    function testBorrowSplitDividedByTwoAndMultipliedByOne() public {
        FeeSnap memory fees;
        // 21 / 2 = 10.5
        liqTree.addMLiq(range(1, 2), 288, fees);
        liqTree.addTLiq(range(1, 2), 19, fees, 21, 21);

        LiqNode storage multOne = liqTree.nodes[LKey.wrap((1 << 24) | 1)];
        assertEq(multOne.tokenX.borrow, 10);
        assertEq(multOne.tokenX.subtreeBorrow, 10);
        assertEq(multOne.tokenY.borrow, 10);
        assertEq(multOne.tokenY.subtreeBorrow, 10);
    }

    function testBorrowSplitDividedByThreeAndMultipliedByOne() public {
        FeeSnap memory fees;
        // 22 / 3 = 7.33333
        liqTree.addMLiq(range(1, 3), 288, fees);
        liqTree.addTLiq(range(1, 3), 19, fees, 22, 22);

        LiqNode storage multOne = liqTree.nodes[LKey.wrap((1 << 24) | 1)];
        assertEq(multOne.tokenX.borrow, 7);
        assertEq(multOne.tokenX.subtreeBorrow, 7);
        assertEq(multOne.tokenY.borrow, 7);
        assertEq(multOne.tokenY.subtreeBorrow, 7);
    }

    function testBorrowSplitDividedByFourAndMultipliedByOne() public {
        FeeSnap memory fees;
        // 22 / 4 = 5.5
        liqTree.addMLiq(range(1, 4), 288, fees);
        liqTree.addTLiq(range(1, 4), 19, fees, 22, 22);

        LiqNode storage multOne = liqTree.nodes[LKey.wrap((1 << 24) | 1)];
        assertEq(multOne.tokenX.borrow, 5);
        assertEq(multOne.tokenX.subtreeBorrow, 5);
        assertEq(multOne.tokenY.borrow, 5);
        assertEq(multOne.tokenY.subtreeBorrow, 5);
    }

    function testBorrowSplitDividedByFiveAndMultipliedByOne() public {
        FeeSnap memory fees;
        // 22 / 5 = 4.4
        liqTree.addMLiq(range(1, 5), 288, fees);
        liqTree.addTLiq(range(1, 5), 19, fees, 22, 22);

        LiqNode storage multOne = liqTree.nodes[LKey.wrap((1 << 24) | 1)];
        assertEq(multOne.tokenX.borrow, 4);
        assertEq(multOne.tokenX.subtreeBorrow, 4);
        assertEq(multOne.tokenY.borrow, 4);
        assertEq(multOne.tokenY.subtreeBorrow, 4);
    }

    function testBorrowSplitDividedBySixAndMultipliedByOne() public {
        FeeSnap memory fees;
        // 21 / 6 = 3.5
        liqTree.addMLiq(range(1, 6), 288, fees);
        liqTree.addTLiq(range(1, 6), 19, fees, 21, 21);

        LiqNode storage multOne = liqTree.nodes[LKey.wrap((1 << 24) | 1)];
        assertEq(multOne.tokenX.borrow, 3);
        assertEq(multOne.tokenX.subtreeBorrow, 3);
        assertEq(multOne.tokenY.borrow, 3);
        assertEq(multOne.tokenY.subtreeBorrow, 3);
    }

    // x2 (2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16)

    function testBorrowSplitDividedByTwoAndMultipliedByTwo() public {
        FeeSnap memory fees;
        // 511 / 2 = 255.5
        liqTree.addMLiq(range(2, 3), 288, fees);
        liqTree.addTLiq(range(2, 3), 19, fees, 511, 511);

        LiqNode storage multTwo = liqTree.nodes[LKey.wrap((2 << 24) | 2)];
        assertEq(multTwo.tokenX.borrow, 510);
        assertEq(multTwo.tokenX.subtreeBorrow, 510);
        assertEq(multTwo.tokenY.borrow, 510);
        assertEq(multTwo.tokenY.subtreeBorrow, 510);
    }

    function testBorrowSplitDividedByThreeAndMultipliedByTwo() public {
        FeeSnap memory fees;
        // 511 / 3 = 170.33
        liqTree.addMLiq(range(2, 4), 288, fees);
        liqTree.addTLiq(range(2, 4), 19, fees, 511, 511);

        LiqNode storage multTwo = liqTree.nodes[LKey.wrap((2 << 24) | 2)];
        assertEq(multTwo.tokenX.borrow, 340);
        assertEq(multTwo.tokenX.subtreeBorrow, 340);
        assertEq(multTwo.tokenY.borrow, 340);
        assertEq(multTwo.tokenY.subtreeBorrow, 340);
    }

    function testBorrowSplitDividedByFourAndMultipliedByTwo() public {
        FeeSnap memory fees;
        // 7 / 4 = 1.75
        liqTree.addMLiq(range(2, 5), 288, fees);
        liqTree.addTLiq(range(2, 5), 19, fees, 7, 7);

        LiqNode storage multTwo = liqTree.nodes[LKey.wrap((2 << 24) | 2)];
        assertEq(multTwo.tokenX.borrow, 2);
        assertEq(multTwo.tokenX.subtreeBorrow, 2);
        assertEq(multTwo.tokenY.borrow, 2);
        assertEq(multTwo.tokenY.subtreeBorrow, 2);
    }

    function testBorrowSplitDividedByFiveAndMultipliedByTwo() public {
        FeeSnap memory fees;
        // 499/5 = 99.8
        liqTree.addMLiq(range(2, 6), 288, fees);
        liqTree.addTLiq(range(2, 6), 19, fees, 7, 7);

        LiqNode storage multTwo = liqTree.nodes[LKey.wrap((2 << 24) | 2)];
        assertEq(multTwo.tokenX.borrow, 2);
        assertEq(multTwo.tokenX.subtreeBorrow, 2);
        assertEq(multTwo.tokenY.borrow, 2);
        assertEq(multTwo.tokenY.subtreeBorrow, 2);
    }

    function testBorrowSplitDividedBySixAndMultipliedByTwo() public {
        FeeSnap memory fees;
        // 499/5 = 99.8
        liqTree.addMLiq(range(2, 6), 288, fees);
        liqTree.addTLiq(range(2, 6), 19, fees, 7, 7);

        LiqNode storage multTwo = liqTree.nodes[LKey.wrap((2 << 24) | 2)];
        assertEq(multTwo.tokenX.borrow, 2);
        assertEq(multTwo.tokenX.subtreeBorrow, 2);
        assertEq(multTwo.tokenY.borrow, 2);
        assertEq(multTwo.tokenY.subtreeBorrow, 2);
    }

    // x4 (4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16)

    function testBorrowSplitDividedByFourAndMultipliedByFour() public {}

    function testBorrowSplitDividedByFiveAndMultipliedByFour() public {}

    function testBorrowSplitDividedBySixAndMultipliedByFour() public {}

    function testBorrowSplitDividedBySevenAndMultipliedByFour() public {}

    function testBorrowSplitDividedByEightAndMultipliedByFour() public {}

    function testBorrowSplitDividedByNineAndMultipliedByFour() public {}

    function testBorrowSplitDividedByTenAndMultipliedByFour() public {}

    function testBorrowSplitDividedByElevenAndMultipliedByFour() public {}

    function testBorrowSplitDividedByTwelveAndMultipliedByFour() public {}

    function testBorrowSplitDividedByThirteenAndMultipliedByFour() public {}

    function testBorrowSplitDividedByFourteenAndMultipliedByFour() public {}

    function testBorrowSplitDividedByFifteenAndMultipliedByFour() public {}

    // x8 (8, 9, 10, 11, 12, 13, 14, 15, 16)

    function testBorrowSplitDividedByEightAndMultipliedByEight() public {}

    function testBorrowSplitDividedByNineAndMultipliedByEight() public {}

    function testBorrowSplitDividedByTenAndMultipliedByEight() public {}

    function testBorrowSplitDividedByElevenAndMultipliedByEight() public {}

    function testBorrowSplitDividedByTwelveAndMultipliedByEight() public {}

    function testBorrowSplitDividedByThirteenAndMultipliedByEight() public {}

    function testBorrowSplitDividedByFourteenAndMultipliedByEight() public {}

    function testBorrowSplitDividedByFifteenAndMultipliedByEight() public {}
}
