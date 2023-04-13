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
contract DenseTreeTest is Test {
    LiqTree public liqTree;
    using LiqTreeImpl for LiqTree;
    using LKeyImpl for LKey;
    using FeeRateSnapshotImpl for FeeRateSnapshot;
    
    function setUp() public {
        // A depth of 4 creates a tree that covers an absolute range of 16 ([0, 15]). 
        // ie. A complete tree matching the ascii documentation. 
        liqTree.init(4);
    }

    function testOutputRangeCombinations() public {
        uint24 range;
        uint24 base;

        // 16 is the offset
        for (uint24 i = 0; i < 16; i++) {
            for (uint24 j = i; j < 16; j++) {
                if (i == 0 && j == 15) {
                    continue;
                }

                console.log("\n\nOutputing (i, j)", i, j);
                (LKey low, LKey high, LKey peak, LKey stopRange) = liqTree.getKeys(i, j);

                (range, base) = peak.explode();
                console.log("Peak (r,b,v)", range, base, LKey.unwrap(peak));
                (range, base) = stopRange.explode();
                console.log("Stop (r,b,v)", range, base, LKey.unwrap(stopRange));
                (range, base) = low.explode();
                console.log("Low (r,b,v)", range, base, LKey.unwrap(low));
                (range, base) = high.explode();
                console.log("High (r,b,v)", range, base, LKey.unwrap(high));

            }
        }
    }

    function testRootNodeOnly() public {
        LKey root = liqTree.root;

        vm.warp(0); // T0
        liqTree.addInfRangeMLiq(8430); // Step 1
        liqTree.addInfRangeTLiq(4381, 832e18, 928e6); // Step 2

        vm.warp(60 * 60); // T3600 (1hr)
        liqTree.feeRateSnapshotTokenX.add(113712805933826); // 5.4% APR as Q192.64
        liqTree.feeRateSnapshotTokenY.add(113712805933826);

        // Verify root state is as expected
        assertEq(liqTree.nodes[root].mLiq, 8430);
        assertEq(liqTree.nodes[root].subtreeMLiq, 134880);
        assertEq(liqTree.nodes[root].tLiq, 4381);
        assertEq(liqTree.nodes[root].tokenX.borrowed, 832e18);
        assertEq(liqTree.nodes[root].tokenX.subtreeBorrowed, 832e18);
        assertEq(liqTree.nodes[root].tokenY.borrowed, 928e6);
        assertEq(liqTree.nodes[root].tokenY.subtreeBorrowed, 928e6);

        // Testing 4 methods addInfRangeMLiq, removeInfRangeMLiq, addInfRangeTLiq, removeInfRangeTLiq
        // Assert tree structure and fee calculations after each operation
        liqTree.addInfRangeMLiq(9287);

        assertEq(liqTree.nodes[root].tokenX.cummulativeEarnedPerMLiq, 38024667284);
        assertEq(liqTree.nodes[root].tokenX.subtreeCummulativeEarnedPerMLiq, 38024667284);
        assertEq(liqTree.nodes[root].tokenY.cummulativeEarnedPerMLiq, 0);
        assertEq(liqTree.nodes[root].tokenY.subtreeCummulativeEarnedPerMLiq, 0);

        assertEq(liqTree.nodes[root].mLiq, 17717);
        assertEq(liqTree.nodes[root].subtreeMLiq, 283472);
        assertEq(liqTree.nodes[root].tLiq, 4381);
        assertEq(liqTree.nodes[root].tokenX.borrowed, 832e18);
        assertEq(liqTree.nodes[root].tokenX.subtreeBorrowed, 832e18);
        assertEq(liqTree.nodes[root].tokenY.borrowed, 928e6);
        assertEq(liqTree.nodes[root].tokenY.subtreeBorrowed, 928e6);

        vm.warp(22000); // T22000
        liqTree.feeRateSnapshotTokenX.add(74672420010376264941568); // 693792000.0% APR as Q192.64 from T22000 - T3600
        liqTree.feeRateSnapshotTokenY.add(74672420010376264941568);

        liqTree.removeInfRangeMLiq(3682);

        /* 
                      1188101861132416784
            Expected: 11881018269102162284
              Actual: 11881018269102163474
      */

        // 11881018231077494784
        // 11881018269102162068

        // In code the rates are correct, both 74672420010376264941568
        // x num 62127453448633052431384576000000000000000000 (correct)
        // y num 69296005769629173865775104000000 (correct)
        // x earn as Q192.64 is 219166102643763942933991985099057402494 (off by +42933991985099057402494)
        // y earn as Q192.64 is 244454499102659782503298752 (ending 782503298752 should be 8e11)
        // x earn as token is 11881018231077496190 (real 1.18810182310774961900999040469605463678530107851649688655015 × 10^19)
        // y earn as token is 13251904 (real 1.32519049500479765197268160192844987932403455488383769989013 × 10^7)
        // X total 11881018269102163474 (off by 0)
        // Y total 13251904 (off by +1 if we round up)
        assertEq(liqTree.nodes[root].tokenX.cummulativeEarnedPerMLiq, 11881018269102163474);
        assertEq(liqTree.nodes[root].tokenX.subtreeCummulativeEarnedPerMLiq, 11881018269102163474);
        assertEq(liqTree.nodes[root].tokenY.cummulativeEarnedPerMLiq, 13251904);
        assertEq(liqTree.nodes[root].tokenY.subtreeCummulativeEarnedPerMLiq, 13251904);

        assertEq(liqTree.nodes[root].mLiq, 14035);
        assertEq(liqTree.nodes[root].subtreeMLiq, 224560);
        assertEq(liqTree.nodes[root].tLiq, 4381);
        assertEq(liqTree.nodes[root].tokenX.borrowed, 832e18);
        assertEq(liqTree.nodes[root].tokenX.subtreeBorrowed, 832e18);
        assertEq(liqTree.nodes[root].tokenY.borrowed, 928e6);
        assertEq(liqTree.nodes[root].tokenY.subtreeBorrowed, 928e6);

        vm.warp(37002); // T37002
        liqTree.feeRateSnapshotTokenX.add(6932491854677024); // 7.9% APR as Q192.64 T37002 - T22000
        liqTree.feeRateSnapshotTokenY.add(6932491854677024);

        liqTree.addInfRangeTLiq(7287, 9184e18, 7926920e6);

        assertEq(liqTree.nodes[root].tokenX.cummulativeEarnedPerMLiq, 11881019661491126559); // fix rounding, add 1
        assertEq(liqTree.nodes[root].tokenX.subtreeCummulativeEarnedPerMLiq, 11881019661491126559);
        assertEq(liqTree.nodes[root].tokenY.cummulativeEarnedPerMLiq, 13251905); // fix rounding, add 1
        assertEq(liqTree.nodes[root].tokenY.subtreeCummulativeEarnedPerMLiq, 13251905);

        assertEq(liqTree.nodes[root].mLiq, 14035);
        assertEq(liqTree.nodes[root].subtreeMLiq, 224560);
        assertEq(liqTree.nodes[root].tLiq, 11668);
        assertEq(liqTree.nodes[root].tokenX.borrowed, 10016e18);
        assertEq(liqTree.nodes[root].tokenX.subtreeBorrowed, 10016e18);
        assertEq(liqTree.nodes[root].tokenY.borrowed, 7927848e6);
        assertEq(liqTree.nodes[root].tokenY.subtreeBorrowed, 7927848e6);

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

        assertEq(liqTree.nodes[root].tokenX.cummulativeEarnedPerMLiq, 2563695146166521368512);
        assertEq(liqTree.nodes[root].tokenX.subtreeCummulativeEarnedPerMLiq, 2563695146166521368512);
        assertEq(liqTree.nodes[root].tokenY.cummulativeEarnedPerMLiq, 2019821011408);
        assertEq(liqTree.nodes[root].tokenY.subtreeCummulativeEarnedPerMLiq, 2019821011408);

        assertEq(liqTree.nodes[root].mLiq, 14035);
        assertEq(liqTree.nodes[root].subtreeMLiq, 224560);
        assertEq(liqTree.nodes[root].tLiq, 6745);
        assertEq(liqTree.nodes[root].tokenX.borrowed, 9794e18);
        assertEq(liqTree.nodes[root].tokenX.subtreeBorrowed, 9794e18);
        assertEq(liqTree.nodes[root].tokenY.borrowed, 7927062e6);
        assertEq(liqTree.nodes[root].tokenY.subtreeBorrowed, 7927062e6);
    }

    function testLeftLegOnly() public {
        LKey root = liqTree.root; // inf
        LKey L = _nodeKey(1, 0, 16); // 0-7
        LKey LL = _nodeKey(2, 0, 16); // 0-3
        LKey LR = _nodeKey(2, 1, 16); // 4-7
        LKey LLR = _nodeKey(3, 1, 16); // 2-3
        LKey LLRR = _nodeKey(4, 3, 16); // 3

        // Step 1) Allocate different mLiq + tLiq values for each node
        vm.warp(0); // T0

        liqTree.addInfRangeMLiq(8430); // root
        liqTree.addMLiq(LiqRange(0, 7), 377); // L 
        liqTree.addMLiq(LiqRange(0, 3), 9082734); // LL
        liqTree.addMLiq(LiqRange(4, 7), 1111); // LR
        liqTree.addMLiq(LiqRange(2, 3), 45346); // LLR
        liqTree.addMLiq(LiqRange(3, 3), 287634865); // LLRR

        liqTree.addInfRangeTLiq(4430, 492e18, 254858e6); // root
        liqTree.addTLiq(LiqRange(0, 7), 77, 998e18, 353e6); // L 
        liqTree.addTLiq(LiqRange(0, 3), 82734, 765e18, 99763e6); // LL
        liqTree.addTLiq(LiqRange(4, 7), 111, 24e18, 552e6); // LR
        liqTree.addTLiq(LiqRange(2, 3), 5346, 53e18, 8765e6); // LLR
        liqTree.addTLiq(LiqRange(3, 3), 7634865, 701e18, 779531e6); // LLRR

        // mLiq
        assertEq(liqTree.nodes[root].mLiq, 8430);
        assertEq(liqTree.nodes[L].mLiq, 377);
        assertEq(liqTree.nodes[LL].mLiq, 9082734);
        assertEq(liqTree.nodes[LR].mLiq, 1111);
        assertEq(liqTree.nodes[LLR].mLiq, 45346);
        assertEq(liqTree.nodes[LLRR].mLiq, 287634865);

        // tLiq
        assertEq(liqTree.nodes[root].tLiq, 4430);
        assertEq(liqTree.nodes[L].tLiq, 77);
        assertEq(liqTree.nodes[LL].tLiq, 82734);
        assertEq(liqTree.nodes[LR].tLiq, 111);
        assertEq(liqTree.nodes[LLR].tLiq, 5346);
        assertEq(liqTree.nodes[LLRR].tLiq, 7634865);

        // subtreeMLiq
        assertEq(liqTree.nodes[root].subtreeMLiq, 324198833); // 8430*16 + 377*8 + 9082734*4 + 1111*4 + 45346*2 + 287634865*1
        assertEq(liqTree.nodes[L].subtreeMLiq, 324063953);    // 377*8 + 9082734*4 + 1111*4 + 45346*2 + 287634865*1
        assertEq(liqTree.nodes[LL].subtreeMLiq, 324056493);   // 9082734*4 + 45346*2 + 287634865*1
        assertEq(liqTree.nodes[LR].subtreeMLiq, 4444);        // 1111*4
        assertEq(liqTree.nodes[LLR].subtreeMLiq, 287725557);  // 45346*2 + 287634865*1
        assertEq(liqTree.nodes[LLRR].subtreeMLiq, 287634865); // 287634865*1

        // borrowedX
        assertEq(liqTree.nodes[root].tokenX.borrowed, 492e18);
        assertEq(liqTree.nodes[L].tokenX.borrowed, 998e18);
        assertEq(liqTree.nodes[LL].tokenX.borrowed, 765e18);
        assertEq(liqTree.nodes[LR].tokenX.borrowed, 24e18);
        assertEq(liqTree.nodes[LLR].tokenX.borrowed, 53e18);
        assertEq(liqTree.nodes[LLRR].tokenX.borrowed, 701e18);

        // borrowedY
        assertEq(liqTree.nodes[root].tokenY.borrowed, 254858e6);
        assertEq(liqTree.nodes[L].tokenY.borrowed, 353e6);
        assertEq(liqTree.nodes[LL].tokenY.borrowed, 99763e6);
        assertEq(liqTree.nodes[LR].tokenY.borrowed, 552e6);
        assertEq(liqTree.nodes[LLR].tokenY.borrowed, 8765e6);
        assertEq(liqTree.nodes[LLRR].tokenY.borrowed, 779531e6);

        // subtreeBorrowedX
        assertEq(liqTree.nodes[root].tokenX.subtreeBorrowed, 3033e18); // 492e18 + 998e18 + 765e18 + 53e18 + 701e18 + 24e18
        assertEq(liqTree.nodes[L].tokenX.subtreeBorrowed, 2541e18);    // 998e18 + 765e18 + 53e18 + 701e18 + 24e18
        assertEq(liqTree.nodes[LL].tokenX.subtreeBorrowed, 1519e18);   // 765e18 + 53e18 + 701e18
        assertEq(liqTree.nodes[LR].tokenX.subtreeBorrowed, 24e18);
        assertEq(liqTree.nodes[LLR].tokenX.subtreeBorrowed, 754e18);   // 53e18 + 701e18
        assertEq(liqTree.nodes[LLRR].tokenX.subtreeBorrowed, 701e18);  // 701e18

        // subtreeBorrowedY
        assertEq(liqTree.nodes[root].tokenY.subtreeBorrowed, 1143822e6); // 254858e6 + 353e6 + 99763e6 + 8765e6 + 779531e6 + 552e6
        assertEq(liqTree.nodes[L].tokenY.subtreeBorrowed, 888964e6);     // 353e6 + 99763e6 + 8765e6 + 779531e6 + 552e6
        assertEq(liqTree.nodes[LL].tokenY.subtreeBorrowed, 888059e6);    // 99763e6 + 8765e6 + 779531e6
        assertEq(liqTree.nodes[LR].tokenY.subtreeBorrowed, 552e6);
        assertEq(liqTree.nodes[LLR].tokenY.subtreeBorrowed, 788296e6);   // 8765e6 + 779531e6
        assertEq(liqTree.nodes[LLRR].tokenY.subtreeBorrowed, 779531e6);  // 779531e6

        // Step 2) Assign different rates for X & Y
        vm.warp(98273); // T98273
        liqTree.feeRateSnapshotTokenX.add(4541239648278065);  // 7.9% APR as Q192.64 T98273 - T0
        liqTree.feeRateSnapshotTokenY.add(13278814667749784); // 23.1% APR as Q192.64 T98273 - T0

        // Step 3) Apply change that effects the entire tree, to calculate the fees at each node
        // 3.1) addMLiq
        liqTree.addMLiq(LiqRange(3, 7), 2734); // LLRR, LR

        // root
        assertEq(liqTree.nodes[root].tokenX.cummulativeEarnedPerMLiq, 373601278);
        assertEq(liqTree.nodes[root].tokenX.subtreeCummulativeEarnedPerMLiq, 2303115199);
        assertEq(liqTree.nodes[root].tokenY.cummulativeEarnedPerMLiq, 0);
        assertEq(liqTree.nodes[root].tokenY.subtreeCummulativeEarnedPerMLiq, 2);

        // L
        assertEq(liqTree.nodes[L].tokenX.cummulativeEarnedPerMLiq, 757991165);
        assertEq(liqTree.nodes[L].tokenX.subtreeCummulativeEarnedPerMLiq, 1929915382);
        assertEq(liqTree.nodes[L].tokenY.cummulativeEarnedPerMLiq, 0);
        assertEq(liqTree.nodes[L].tokenY.subtreeCummulativeEarnedPerMLiq, 1);

        // LL
        assertEq(liqTree.nodes[LL].tokenX.cummulativeEarnedPerMLiq, 581096415);
        assertEq(liqTree.nodes[LL].tokenX.subtreeCummulativeEarnedPerMLiq, 1153837196);
        assertEq(liqTree.nodes[LL].tokenY.cummulativeEarnedPerMLiq, 0);
        assertEq(liqTree.nodes[LL].tokenY.subtreeCummulativeEarnedPerMLiq, 1);

        // LR
        assertEq(liqTree.nodes[LR].tokenX.cummulativeEarnedPerMLiq, 148929881804);
        assertEq(liqTree.nodes[LR].tokenX.subtreeCummulativeEarnedPerMLiq, 148929881804);
        assertEq(liqTree.nodes[LR].tokenY.cummulativeEarnedPerMLiq, 10);
        assertEq(liqTree.nodes[LR].tokenY.subtreeCummulativeEarnedPerMLiq, 10);

        // LLR
        assertEq(liqTree.nodes[LLR].tokenX.cummulativeEarnedPerMLiq, 42651943);
        assertEq(liqTree.nodes[LLR].tokenX.subtreeCummulativeEarnedPerMLiq, 606784254);
        assertEq(liqTree.nodes[LLR].tokenY.cummulativeEarnedPerMLiq, 0);
        assertEq(liqTree.nodes[LLR].tokenY.subtreeCummulativeEarnedPerMLiq, 1);

        // LLRR
        assertEq(liqTree.nodes[LLRR].tokenX.cummulativeEarnedPerMLiq, 581500584);
        assertEq(liqTree.nodes[LLRR].tokenX.subtreeCummulativeEarnedPerMLiq, 581500584);
        assertEq(liqTree.nodes[LLRR].tokenY.cummulativeEarnedPerMLiq, 1);
        assertEq(liqTree.nodes[LLRR].tokenY.subtreeCummulativeEarnedPerMLiq, 1);

        // mLiq
        assertEq(liqTree.nodes[root].mLiq, 8430);
        assertEq(liqTree.nodes[L].mLiq, 377);
        assertEq(liqTree.nodes[LL].mLiq, 9082734);
        assertEq(liqTree.nodes[LR].mLiq, 3845);
        assertEq(liqTree.nodes[LLR].mLiq, 45346);
        assertEq(liqTree.nodes[LLRR].mLiq, 287637599);

        // subtreeMLiq
        assertEq(liqTree.nodes[root].subtreeMLiq, 324212503); // 8430*16 + 377*8 + 9082734*4 + 3845*4 + 45346*2 + 287637599*1
        assertEq(liqTree.nodes[L].subtreeMLiq, 324077623);    // 377*8 + 9082734*4 + 3845*4 + 45346*2 + 287637599*1
        assertEq(liqTree.nodes[LL].subtreeMLiq, 324059227);   // 9082734*4 + 45346*2 + 287637599*1
        assertEq(liqTree.nodes[LR].subtreeMLiq, 15380);       // 3845*4
        assertEq(liqTree.nodes[LLR].subtreeMLiq, 287728291);  // 45346*2 + 287637599*1
        assertEq(liqTree.nodes[LLRR].subtreeMLiq, 287637599); // 287637599*1

        // 3.2) removeMLiq
        vm.warp(2876298273); // T2876298273
        liqTree.feeRateSnapshotTokenX.add(16463537718422861220174597);   // 978567.9% APR as Q192.64 T2876298273 - T98273
        liqTree.feeRateSnapshotTokenY.add(3715979586694123491881712207); // 220872233.1% APR as Q192.64 T2876298273 - T98273

        liqTree.removeMLiq(LiqRange(3, 7), 2734); // LLRR, LR

        // root
        assertEq(liqTree.nodes[root].tokenX.cummulativeEarnedPerMLiq, 373601278 + 1354374549470516050);         // 1354374549844117328
        assertEq(liqTree.nodes[root].tokenX.subtreeCummulativeEarnedPerMLiq, 2303115199 + 8349223594601778821); // 8349223596904894020
        assertEq(liqTree.nodes[root].tokenY.cummulativeEarnedPerMLiq, 0 + 158351473403);                        // 158351473403
        assertEq(liqTree.nodes[root].tokenY.subtreeCummulativeEarnedPerMLiq, 2 + 710693401861);                 // 710693401863

        // L
        assertEq(liqTree.nodes[L].tokenX.cummulativeEarnedPerMLiq, 757991165 + 2747859799177149412);         // 2747859799935140577
        assertEq(liqTree.nodes[L].tokenX.subtreeCummulativeEarnedPerMLiq, 1929915382 + 6996304358425988634); // 6996304360355904016
        assertEq(liqTree.nodes[L].tokenY.cummulativeEarnedPerMLiq, 0 + 219375887);                           // 219375887
        assertEq(liqTree.nodes[L].tokenY.subtreeCummulativeEarnedPerMLiq, 1 + 552456845955);                 // 552456845956

        // LL
        assertEq(liqTree.nodes[LL].tokenX.cummulativeEarnedPerMLiq, 581096415 + 2106654304105573173);         // 2106654304686669588
        assertEq(liqTree.nodes[LL].tokenX.subtreeCummulativeEarnedPerMLiq, 1153837196 + 4183016846975641372); // 4183016848129478568
        assertEq(liqTree.nodes[LL].tokenY.cummulativeEarnedPerMLiq, 0 + 62008538706);                         // 62008538706
        assertEq(liqTree.nodes[LL].tokenY.subtreeCummulativeEarnedPerMLiq, 1 + 551980602776);                 // 551980602777

        // LR
        assertEq(liqTree.nodes[LR].tokenX.cummulativeEarnedPerMLiq, 148929881804 + 423248577958689008325);        // 423248578107618890129
        assertEq(liqTree.nodes[LR].tokenX.subtreeCummulativeEarnedPerMLiq, 148929881804 + 423248577958689008325); // 423248578107618890129
        assertEq(liqTree.nodes[LR].tokenY.cummulativeEarnedPerMLiq, 10 + 2197219781185);                          // 2197219781195
        assertEq(liqTree.nodes[LR].tokenY.subtreeCummulativeEarnedPerMLiq, 10 + 2197219781185);                   // 2197219781195

        // LLR
        assertEq(liqTree.nodes[LLR].tokenX.cummulativeEarnedPerMLiq, 42651943 + 154626414974589533);          // 154626415017241476
        assertEq(liqTree.nodes[LLR].tokenX.subtreeCummulativeEarnedPerMLiq, 606784254 + 2199779563978122803); // 2199779564584907057
        assertEq(liqTree.nodes[LLR].tokenY.cummulativeEarnedPerMLiq, 0 + 5771781665);                         // 5771781665
        assertEq(liqTree.nodes[LLR].tokenY.subtreeCummulativeEarnedPerMLiq, 1 + 519095539054);                // 519095539055

        // LLRR
        assertEq(liqTree.nodes[LLRR].tokenX.cummulativeEarnedPerMLiq, 581500584 + 2108117905415037748);         // 2108117905996538332
        assertEq(liqTree.nodes[LLRR].tokenX.subtreeCummulativeEarnedPerMLiq, 581500584 + 2108117905415037748);  // 2108117905996538332
        assertEq(liqTree.nodes[LLRR].tokenY.cummulativeEarnedPerMLiq, 1 + 529127613134);                        // 529127613135
        assertEq(liqTree.nodes[LLRR].tokenY.subtreeCummulativeEarnedPerMLiq, 1 + 529127613134);                 // 529127613135
        
        // mLiq
        assertEq(liqTree.nodes[root].mLiq, 8430);
        assertEq(liqTree.nodes[L].mLiq, 377);
        assertEq(liqTree.nodes[LL].mLiq, 9082734);
        assertEq(liqTree.nodes[LR].mLiq, 1111);
        assertEq(liqTree.nodes[LLR].mLiq, 45346);
        assertEq(liqTree.nodes[LLRR].mLiq, 287634865);

        // subtreeMLiq
        assertEq(liqTree.nodes[root].subtreeMLiq, 324198833); // 8430*16 + 377*8 + 9082734*4 + 1111*4 + 45346*2 + 287634865*1
        assertEq(liqTree.nodes[L].subtreeMLiq, 324063953);    // 377*8 + 9082734*4 + 1111*4 + 45346*2 + 287634865*1
        assertEq(liqTree.nodes[LL].subtreeMLiq, 324056493);   // 9082734*4 + 45346*2 + 287634865*1
        assertEq(liqTree.nodes[LR].subtreeMLiq, 4444);        // 1111*4
        assertEq(liqTree.nodes[LLR].subtreeMLiq, 287725557);  // 45346*2 + 287634865*1
        assertEq(liqTree.nodes[LLRR].subtreeMLiq, 287634865); // 287634865*1

        // 3.3) addTLiq
        vm.warp(9214298113); // T2876298273
        liqTree.feeRateSnapshotTokenX.add(11381610389149375791104);   // 307% APR as Q192.64 T9214298113 - T2876298273
        liqTree.feeRateSnapshotTokenY.add(185394198934916215865344);  // 5000.7% APR as Q192.64 T9214298113 - T2876298273

        liqTree.addTLiq(LiqRange(3, 7), 1000, 1000e18, 1000e6); // LLRR, LR

        // root
        assertEq(liqTree.nodes[root].tokenX.cummulativeEarnedPerMLiq, 1354374549844117328 + 936348777891386);         // 1355310898622008714
        assertEq(liqTree.nodes[root].tokenX.subtreeCummulativeEarnedPerMLiq, 8349223596904894020 + 5772247649074341); // 8354995844553968361
        assertEq(liqTree.nodes[root].tokenY.cummulativeEarnedPerMLiq, 158351473403 + 7900657);                        // 158359374060
        assertEq(liqTree.nodes[root].tokenY.subtreeCummulativeEarnedPerMLiq, 710693401863 + 35458749);                // 710728860612

        // L
        assertEq(liqTree.nodes[L].tokenX.cummulativeEarnedPerMLiq, 2747859799935140577 + 1899736810880077);        // 2749759536746020654
        assertEq(liqTree.nodes[L].tokenX.subtreeCummulativeEarnedPerMLiq, 6996304360355904016 + 4836905046539355); // 7001141265402443371
        assertEq(liqTree.nodes[L].tokenY.cummulativeEarnedPerMLiq, 219375887 + 10945);                             // 219386832
        assertEq(liqTree.nodes[L].tokenY.subtreeCummulativeEarnedPerMLiq, 552456845956 + 27563825);                // 552484409781

        // LL
        assertEq(liqTree.nodes[LL].tokenX.cummulativeEarnedPerMLiq, 2106654304686669588 + 1456389336983247);        // 2108110694023652835
        assertEq(liqTree.nodes[LL].tokenX.subtreeCummulativeEarnedPerMLiq, 4183016848129478568 + 2891837127944514); // 4185908685257423082
        assertEq(liqTree.nodes[LL].tokenY.cummulativeEarnedPerMLiq, 62008538706 + 3093698);                         // 62011632404
        assertEq(liqTree.nodes[LL].tokenY.subtreeCummulativeEarnedPerMLiq, 551980602777 + 27539135);                // 552008141912

        // LR
        assertEq(liqTree.nodes[LR].tokenX.cummulativeEarnedPerMLiq, 423248578107618890129 + 373259731104033296);        // 423621837838722923425
        assertEq(liqTree.nodes[LR].tokenX.subtreeCummulativeEarnedPerMLiq, 423248578107618890129 + 373259731104033296); // 423621837838722923425
        assertEq(liqTree.nodes[LR].tokenY.cummulativeEarnedPerMLiq, 2197219781195 + 139839995);                         // 2197359621190
        assertEq(liqTree.nodes[LR].tokenY.subtreeCummulativeEarnedPerMLiq, 2197219781195 + 139839995);                  // 2197359621190

        // LLR
        assertEq(liqTree.nodes[LLR].tokenX.cummulativeEarnedPerMLiq, 154626415017241476 + 106897640711262);          // 154733312657952738
        assertEq(liqTree.nodes[LLR].tokenX.subtreeCummulativeEarnedPerMLiq, 2199779564584907057 + 1520770209363996); // 2201300334794271053
        assertEq(liqTree.nodes[LLR].tokenY.cummulativeEarnedPerMLiq, 5771781665 + 287962);                           // 5772069627
        assertEq(liqTree.nodes[LLR].tokenY.subtreeCummulativeEarnedPerMLiq, 519095539055 + 25898463);                // 519121437518

        // LLRR
        assertEq(liqTree.nodes[LLRR].tokenX.cummulativeEarnedPerMLiq, 2108117905996538332 + 1457402297493569);        // 2109575308294031901
        assertEq(liqTree.nodes[LLRR].tokenX.subtreeCummulativeEarnedPerMLiq, 2108117905996538332 + 1457402297493569); // 2109575308294031901
        assertEq(liqTree.nodes[LLRR].tokenY.cummulativeEarnedPerMLiq, 529127613135 + 26398986);                       // 529154012121
        assertEq(liqTree.nodes[LLRR].tokenY.subtreeCummulativeEarnedPerMLiq, 529127613135 + 26398986);                // 529154012121

        // tLiq
        assertEq(liqTree.nodes[root].tLiq, 4430);
        assertEq(liqTree.nodes[L].tLiq, 77);
        assertEq(liqTree.nodes[LL].tLiq, 82734);
        assertEq(liqTree.nodes[LR].tLiq, 1111);
        assertEq(liqTree.nodes[LLR].tLiq, 5346);
        assertEq(liqTree.nodes[LLRR].tLiq, 7635865);

        // borrowedX
        assertEq(liqTree.nodes[root].tokenX.borrowed, 492e18);
        assertEq(liqTree.nodes[L].tokenX.borrowed, 998e18);
        assertEq(liqTree.nodes[LL].tokenX.borrowed, 765e18);
        assertEq(liqTree.nodes[LR].tokenX.borrowed, 1024e18);
        assertEq(liqTree.nodes[LLR].tokenX.borrowed, 53e18);
        assertEq(liqTree.nodes[LLRR].tokenX.borrowed, 1701e18);

        // borrowedY
        assertEq(liqTree.nodes[root].tokenY.borrowed, 254858e6);
        assertEq(liqTree.nodes[L].tokenY.borrowed, 353e6);
        assertEq(liqTree.nodes[LL].tokenY.borrowed, 99763e6);
        assertEq(liqTree.nodes[LR].tokenY.borrowed, 1552e6);
        assertEq(liqTree.nodes[LLR].tokenY.borrowed, 8765e6);
        assertEq(liqTree.nodes[LLRR].tokenY.borrowed, 780531e6);

        // subtreeBorrowedX
        assertEq(liqTree.nodes[root].tokenX.subtreeBorrowed, 5033e18);  // 492e18 + 998e18 + 765e18 + 53e18 + 701e18 + 24e18
        assertEq(liqTree.nodes[L].tokenX.subtreeBorrowed, 4541e18);     // 998e18 + 765e18 + 53e18 + 701e18 + 24e18
        assertEq(liqTree.nodes[LL].tokenX.subtreeBorrowed, 2519e18);    // 765e18 + 53e18 + 701e18
        assertEq(liqTree.nodes[LR].tokenX.subtreeBorrowed, 1024e18);
        assertEq(liqTree.nodes[LLR].tokenX.subtreeBorrowed, 1754e18);   // 53e18 + 701e18
        assertEq(liqTree.nodes[LLRR].tokenX.subtreeBorrowed, 1701e18);  // 701e18

        // subtreeBorrowedY
        assertEq(liqTree.nodes[root].tokenY.subtreeBorrowed, 1145822e6); // 254858e6 + 353e6 + 99763e6 + 8765e6 + 779531e6 + 552e6
        assertEq(liqTree.nodes[L].tokenY.subtreeBorrowed, 890964e6);     // 353e6 + 99763e6 + 8765e6 + 779531e6 + 552e6
        assertEq(liqTree.nodes[LL].tokenY.subtreeBorrowed, 889059e6);    // 99763e6 + 8765e6 + 779531e6
        assertEq(liqTree.nodes[LR].tokenY.subtreeBorrowed, 1552e6);
        assertEq(liqTree.nodes[LLR].tokenY.subtreeBorrowed, 789296e6);   // 8765e6 + 779531e6
        assertEq(liqTree.nodes[LLRR].tokenY.subtreeBorrowed, 780531e6);  // 779531e6

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
        assertEq(liqTree.nodes[root].tokenX.cummulativeEarnedPerMLiq, 1355310898622008714 + 193574177654021);
        assertEq(liqTree.nodes[root].tokenX.subtreeCummulativeEarnedPerMLiq, 8354995844553968361 + 1980200886448553);
        assertEq(liqTree.nodes[root].tokenY.cummulativeEarnedPerMLiq, 158359374060 + 260707);
        assertEq(liqTree.nodes[root].tokenY.subtreeCummulativeEarnedPerMLiq, 710728860612 + 1172122);

        // L
        // 998e18 * 2352954287417905205553 / 324131393 / 2**64
        // 4541e18 * 2352954287417905205553 / 324131393 / 2**64
        // 353e6 * 6117681147286553534438 / 324131393 / 2**64
        // 890964e6 * 6117681147286553534438 / 324131393 / 2**64
        assertEq(liqTree.nodes[L].tokenX.cummulativeEarnedPerMLiq, 2749759536746020654 + 392738261220692);
        assertEq(liqTree.nodes[L].tokenX.subtreeCummulativeEarnedPerMLiq, 7001141265402443371 + 1786998441085335);
        assertEq(liqTree.nodes[L].tokenY.cummulativeEarnedPerMLiq, 219386832 + 361);
        assertEq(liqTree.nodes[L].tokenY.subtreeCummulativeEarnedPerMLiq, 552484409781 + 911603);

        // LL
        // 765e18 * 2352954287417905205553 / 324091721 / 2**64
        // 2519e18 * 2352954287417905205553 / 324091721 / 2**64
        // 99763e6 * 6117681147286553534438 / 324091721 / 2**64
        // 889059e6 * 6117681147286553534438 / 324091721 / 2**64
        assertEq(liqTree.nodes[LL].tokenX.cummulativeEarnedPerMLiq, 2108110694023652835 + 301083714644757);
        assertEq(liqTree.nodes[LL].tokenX.subtreeCummulativeEarnedPerMLiq, 4185908685257423082 + 991411604170121);
        assertEq(liqTree.nodes[LL].tokenY.cummulativeEarnedPerMLiq, 62011632404 + 102086);
        assertEq(liqTree.nodes[LL].tokenY.subtreeCummulativeEarnedPerMLiq, 552008141912 + 909766);

        // LR
        // 1024e18 * 2352954287417905205553 / 39672 / 2**64
        // 1024e18 * 2352954287417905205553 / 39672 / 2**64
        // 1552e6 * 6117681147286553534438 / 39672 / 2**64
        // 1552e6 * 6117681147286553534438 / 39672 / 2**64
        assertEq(liqTree.nodes[LR].tokenX.cummulativeEarnedPerMLiq, 423621837838722923425 + 3292377527956539412);
        assertEq(liqTree.nodes[LR].tokenX.subtreeCummulativeEarnedPerMLiq, 423621837838722923425 + 3292377527956539412);
        assertEq(liqTree.nodes[LR].tokenY.cummulativeEarnedPerMLiq, 2197359621190 + 12974025);
        assertEq(liqTree.nodes[LR].tokenY.subtreeCummulativeEarnedPerMLiq, 2197359621190 + 12974025);

        // LLR
        // 53e18 * 2352954287417905205553 / 305908639 / 2**64
        // 1754e18 * 2352954287417905205553 / 305908639 / 2**64
        // 8765e6 * 6117681147286553534438 / 305908639 / 2**64
        // 789296e6 * 6117681147286553534438 / 305908639 / 2**64
        assertEq(liqTree.nodes[LLR].tokenX.cummulativeEarnedPerMLiq, 154733312657952738 + 22099268330799);
        assertEq(liqTree.nodes[LLR].tokenX.subtreeCummulativeEarnedPerMLiq, 2201300334794271053 + 731360691551353);
        assertEq(liqTree.nodes[LLR].tokenY.cummulativeEarnedPerMLiq, 5772069627 + 9502);
        assertEq(liqTree.nodes[LLR].tokenY.subtreeCummulativeEarnedPerMLiq, 519121437518 + 855687);

        // LLRR
        // 1701e18 * 2352954287417905205553 / 296771752 / 2**64
        // 1701e18 * 2352954287417905205553 / 296771752 / 2**64
        // 780531e6 * 6117681147286553534438 / 296771752 / 2**64
        // 780531e6 * 6117681147286553534438 / 296771752 / 2**64
        assertEq(liqTree.nodes[LLRR].tokenX.cummulativeEarnedPerMLiq, 2109575308294031901 + 731097873063750);
        assertEq(liqTree.nodes[LLRR].tokenX.subtreeCummulativeEarnedPerMLiq, 2109575308294031901 + 731097873063750);
        assertEq(liqTree.nodes[LLRR].tokenY.cummulativeEarnedPerMLiq, 529154012121 + 872237);
        assertEq(liqTree.nodes[LLRR].tokenY.subtreeCummulativeEarnedPerMLiq, 529154012121 + 872237);

        // tLiq
        assertEq(liqTree.nodes[root].tLiq, 4430);
        assertEq(liqTree.nodes[L].tLiq, 77);
        assertEq(liqTree.nodes[LL].tLiq, 82734);
        assertEq(liqTree.nodes[LR].tLiq, 111);
        assertEq(liqTree.nodes[LLR].tLiq, 5346);
        assertEq(liqTree.nodes[LLRR].tLiq, 7634865);

        // subtreeMLiq
        assertEq(liqTree.nodes[root].subtreeMLiq, 324198833); // 8430*16 + 377*8 + 9082734*4 + 1111*4 + 45346*2 + 287634865*1
        assertEq(liqTree.nodes[L].subtreeMLiq, 324063953);    // 377*8 + 9082734*4 + 1111*4 + 45346*2 + 287634865*1
        assertEq(liqTree.nodes[LL].subtreeMLiq, 324056493);   // 9082734*4 + 45346*2 + 287634865*1
        assertEq(liqTree.nodes[LR].subtreeMLiq, 4444);        // 1111*4
        assertEq(liqTree.nodes[LLR].subtreeMLiq, 287725557);  // 45346*2 + 287634865*1
        assertEq(liqTree.nodes[LLRR].subtreeMLiq, 287634865); // 287634865*1

        // borrowedX
        assertEq(liqTree.nodes[root].tokenX.borrowed, 492e18);
        assertEq(liqTree.nodes[L].tokenX.borrowed, 998e18);
        assertEq(liqTree.nodes[LL].tokenX.borrowed, 765e18);
        assertEq(liqTree.nodes[LR].tokenX.borrowed, 24e18);
        assertEq(liqTree.nodes[LLR].tokenX.borrowed, 53e18);
        assertEq(liqTree.nodes[LLRR].tokenX.borrowed, 701e18);

        // borrowedY
        assertEq(liqTree.nodes[root].tokenY.borrowed, 254858e6);
        assertEq(liqTree.nodes[L].tokenY.borrowed, 353e6);
        assertEq(liqTree.nodes[LL].tokenY.borrowed, 99763e6);
        assertEq(liqTree.nodes[LR].tokenY.borrowed, 552e6);
        assertEq(liqTree.nodes[LLR].tokenY.borrowed, 8765e6);
        assertEq(liqTree.nodes[LLRR].tokenY.borrowed, 779531e6);

        // subtreeBorrowedX
        assertEq(liqTree.nodes[root].tokenX.subtreeBorrowed, 3033e18); // 492e18 + 998e18 + 765e18 + 53e18 + 701e18 + 24e18
        assertEq(liqTree.nodes[L].tokenX.subtreeBorrowed, 2541e18);    // 998e18 + 765e18 + 53e18 + 701e18 + 24e18
        assertEq(liqTree.nodes[LL].tokenX.subtreeBorrowed, 1519e18);   // 765e18 + 53e18 + 701e18
        assertEq(liqTree.nodes[LR].tokenX.subtreeBorrowed, 24e18);
        assertEq(liqTree.nodes[LLR].tokenX.subtreeBorrowed, 754e18);   // 53e18 + 701e18
        assertEq(liqTree.nodes[LLRR].tokenX.subtreeBorrowed, 701e18);  // 701e18

        // subtreeBorrowedY
        assertEq(liqTree.nodes[root].tokenY.subtreeBorrowed, 1143822e6); // 254858e6 + 353e6 + 99763e6 + 8765e6 + 779531e6 + 552e6
        assertEq(liqTree.nodes[L].tokenY.subtreeBorrowed, 888964e6);     // 353e6 + 99763e6 + 8765e6 + 779531e6 + 552e6
        assertEq(liqTree.nodes[LL].tokenY.subtreeBorrowed, 888059e6);    // 99763e6 + 8765e6 + 779531e6
        assertEq(liqTree.nodes[LR].tokenY.subtreeBorrowed, 552e6);
        assertEq(liqTree.nodes[LLR].tokenY.subtreeBorrowed, 788296e6);   // 8765e6 + 779531e6
        assertEq(liqTree.nodes[LLRR].tokenY.subtreeBorrowed, 779531e6);  // 779531e6
    }

    function _nodeKey(uint24 depth, uint24 index, uint24 offset) public returns (LKey) {
        uint24 baseStep = uint24(offset / 2 ** depth);

        uint24 range = offset >> depth;
        uint24 base = offset + baseStep * index;
        return LKeyImpl.makeKey(range, base);
    }
}