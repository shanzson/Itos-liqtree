// SPDX-License-Identifier: BSL-1.1
pragma solidity ^0.8.18;

import { console } from "forge-std/console.sol";
import { Test } from "forge-std/Test.sol";

import { LiqTree, LiqTreeImpl, LiqRange, LKey, LKeyImpl, LiqNode } from "src/Tree.sol";


/**

    Fee Accumulation

    1. Node Calculations

        totalMLiq = N.subtreeMLiq + A[] * N.range
        nodeEarnPerMLiq += N.borrow * rate / totalMLiq
        nodeSubtreeEarnPerMLiq += N.subtreeBorrow * rate / totalMLiq

    2. Queries

        sum of earned fee rates over traversed nodes
        - if moving upward along the same path to the root, use the nodeEarnPerMLiq
        - if moving upward while flipping to the adjacent node, use the nodeSubtreeEarnPerMLiq

    3. Testing - isolate variables

        N.subtreeMLiq

        A[]


        N.range


        N.borrow


        rate


        totalMLiq


        N.subtreeBorrow


        rate



 */








/**
 * In practice, the LiqTree will have many nodes. So many, that testing at that scale is intractable.
 * Thus the reason for this file. A smaller scale LiqTree, where we can more easily populate the values densely.
 */ 
contract DenseTreeTreeStructureTest is Test {
    LiqTree public liqTree;
    using LiqTreeImpl for LiqTree;
    using LKeyImpl for LKey;
    
    function setUp() public {
        // A depth of 4 creates a tree that covers an absolute range of 16 ([0, 15];);. 
        // ie. A complete tree matching the ascii documentation. 
        liqTree.init(4);
    }

    function testFeesExampleOne() public {
    /*        
    *                                                              0-15
    *                                                      ____----    ----
    *                                  __________----------                 [right side]
    *                                0-7      
    *                            __--  --__           
    *                       __---          ---__         
    *                     /                       \      
    *                  0-3                          4-7 
    *                /   \                         /   \ 
    *              /       \                     /       \   
    *            /           \                 /           \        
    *          0-1            2-3            4-5            6-7   
    *         /   \          /   \          /   \          /   \ 
    *        /     \        /     \        /     \        /     \  
    *       0       1      2       3      4       5      6       7
    */
        LiqNode storage oneOne = liqTree.nodes[LKey.wrap((1 << 24) | 17)];
        LiqNode storage twoThree = liqTree.nodes[LKey.wrap((2 << 24) | 18)];
        LiqNode storage fourSeven = liqTree.nodes[LKey.wrap((4 << 24) | 20)];
        LiqNode storage threeThree = liqTree.nodes[LKey.wrap((1 << 24) | 19)];
        LiqNode storage fourFive = liqTree.nodes[LKey.wrap((2 << 24) | 20)];

        liqTree.addMLiq(LiqRange(1, 7), 200);
        liqTree.addTLiq(LiqRange(1, 7), 100, 500, 300);

        liqTree.addMLiq(LiqRange(3, 5), 214);
        liqTree.addTLiq(LiqRange(3, 5), 410, 98, 17);

        liqTree.feeRateSnapshotTokenX += 533;
        liqTree.feeRateSnapshotTokenY += 234;

        // trigger fees and undo to keep tree state the same
        liqTree.addMLiq(LiqRange(1, 7), 200);
        liqTree.removeMLiq(LiqRange(1, 7), 200);
        liqTree.addMLiq(LiqRange(3, 5), 214);
        liqTree.removeMLiq(LiqRange(3, 5), 214);

        // verify node states
        // (1-1)
        assertEq(oneOne.mLiq, 200);
        assertEq(oneOne.subtreeMLiq, 200);
        assertEq(oneOne.tLiq, 4381);
        assertEq(oneOne.tokenX.borrowed, 832e18);
        assertEq(oneOne.tokenX.subtreeBorrowed, 832e18);
        assertEq(oneOne.tokenY.borrowed, 928e6);
        assertEq(oneOne.tokenY.subtreeBorrowed, 928e6);

        // (2-3)
        assertEq(twoThree.mLiq, 200);
        assertEq(twoThree.subtreeMLiq, 283472);
        assertEq(twoThree.tLiq, 4381);
        assertEq(twoThree.tokenX.borrowed, 832e18);
        assertEq(twoThree.tokenX.subtreeBorrowed, 832e18);
        assertEq(twoThree.tokenY.borrowed, 928e6);
        assertEq(twoThree.tokenY.subtreeBorrowed, 928e6);

        // (4-7)
        assertEq(fourSeven.mLiq, 200);
        assertEq(fourSeven.subtreeMLiq, 283472);
        assertEq(fourSeven.tLiq, 4381);
        assertEq(fourSeven.tokenX.borrowed, 832e18);
        assertEq(fourSeven.tokenX.subtreeBorrowed, 832e18);
        assertEq(fourSeven.tokenY.borrowed, 928e6);
        assertEq(fourSeven.tokenY.subtreeBorrowed, 928e6);


        // (3-3)
        assertEq(threeThree.mLiq, 214);
        assertEq(threeThree.subtreeMLiq, 283472);
        assertEq(threeThree.tLiq, 4381);
        assertEq(threeThree.tokenX.borrowed, 832e18);
        assertEq(threeThree.tokenX.subtreeBorrowed, 832e18);
        assertEq(threeThree.tokenY.borrowed, 928e6);
        assertEq(threeThree.tokenY.subtreeBorrowed, 928e6);

        // (4-5)
        assertEq(fourFive.mLiq, 214);
        assertEq(fourFive.subtreeMLiq, 283472);
        assertEq(fourFive.tLiq, 4381);
        assertEq(fourFive.tokenX.borrowed, 832e18);
        assertEq(fourFive.tokenX.subtreeBorrowed, 832e18);
        assertEq(fourFive.tokenY.borrowed, 928e6);
        assertEq(fourFive.tokenY.subtreeBorrowed, 928e6);

    }

    /*        
    *                                                              0-15
    *                                                      ____----    ----____
    *                                  __________----------                    ----------__________
    *                                0-7                                                          8-15
    *                            __--  --__                                                    __--  --__
    *                       __---          ---__                                          __---          ---__
    *                     /                       \                                     /                       \
    *                  0-3                          4-7                             8-11                         12-15
    *                /   \                         /   \                           /   \                         /   \
    *              /       \                     /       \                       /       \                     /       \
    *            /           \                 /           \                   /           \                 /           \
    *          0-1            2-3            4-5            6-7              8-9           10-11          12-13          14-15
    *         /   \          /   \          /   \          /   \            /   \          /   \          /   \          /   \
    *        /     \        /     \        /     \        /     \          /     \        /     \        /     \        /     \
    *       0       1      2       3      4       5      6       7        8       9      10      11    12      13      14     15
    */

    function testSimpleFee() public {
        liqTree.addMLiq(LiqRange(8, 11), 1111);
        liqTree.addTLiq(LiqRange(8, 11), 111, 24e18, 7e6);

        liqTree.feeRateSnapshotTokenX += 113712805933826;

        LiqNode storage RL = liqTree.nodes[LKey.wrap((4 << 24) | 24)];
        LiqNode storage RLL = liqTree.nodes[LKey.wrap((2 << 24) | 24)];
        LiqNode storage RLLL = liqTree.nodes[LKey.wrap((1 << 24) | 24)];

        // trigger fees + undo
        liqTree.addTLiq(LiqRange(8, 11), 111, 24e18, 7e6);
        liqTree.removeTLiq(LiqRange(8, 11), 111, 24e18, 7e6);

        // 113712805933826 * 24e18 / 4444 / 2**64 = 33291000332.9100024179226406346006655493880262469301129331683
        assertEq(RL.tokenX.cumulativeEarnedPerMLiq, 33291000332);
        assertEq(RL.tokenX.subtreecumulativeEarnedPerMLiq, 33291000332);

        // RL feeX / 4 = 8322750083.22750060448066015865016638734700656173252823329207
        assertEq(RLLL.tokenX.cumulativeEarnedPerMLiq, 0);

        /*
            uint256 feeRateSnapshot;
            uint256 cumulativeEarnedPerMLiq;
            uint256 subtreecumulativeEarnedPerMLiq;
        */
    }

    function testRootNodeOnly() public {
        LiqNode storage root = liqTree.nodes[liqTree.root];

        liqTree.addInfRangeMLiq(8430);
        liqTree.addInfRangeTLiq(4381, 832e18, 928e6);

        liqTree.feeRateSnapshotTokenY += 113712805933826;  // 5.4% APR as Q192.64 = 0.054 * 3600 / (365 * 24 * 60 * 60) * 2^64 = 113712805933826
        liqTree.feeRateSnapshotTokenX += 113712805933826;

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
        assertEq(root.tokenX.cumulativeEarnedPerMLiq, 38024667284);
        assertEq(root.tokenX.subtreecumulativeEarnedPerMLiq, 38024667284);
        assertEq(root.tokenY.cumulativeEarnedPerMLiq, 0);
        assertEq(root.tokenY.subtreecumulativeEarnedPerMLiq, 0);

        assertEq(root.mLiq, 17717);
        assertEq(root.subtreeMLiq, 283472);
        assertEq(root.tLiq, 4381);
        assertEq(root.tokenX.borrowed, 832e18);
        assertEq(root.tokenX.subtreeBorrowed, 832e18);
        assertEq(root.tokenY.borrowed, 928e6);
        assertEq(root.tokenY.subtreeBorrowed, 928e6);

        // Testing remove_inf_range_mLiq
        liqTree.feeRateSnapshotTokenY += 74672420010376264941568;
        liqTree.feeRateSnapshotTokenX += 74672420010376264941568;

        liqTree.removeInfRangeMLiq(3682);

        // earn_x      = 74672420010376264941568 * 832e18 / 283472 / 2**64 = 11881018231077496190.0999040469605463678952418581023875373934
        // earn_y      = 74672420010376264941568 * 928e6 / 283472 / 2**64  = 13251904.9500479765197268160523790709488062313032680476378619
        assertEq(root.tokenX.cumulativeEarnedPerMLiq, 11881018269102163474);          // 11881018231077496190 + 38024667284 = 11881018269102163474
        assertEq(root.tokenX.subtreecumulativeEarnedPerMLiq, 11881018269102163474);  // 11881018231077496190 + 38024667284 = 11881018269102163474
        assertEq(root.tokenY.cumulativeEarnedPerMLiq, 13251904);
        assertEq(root.tokenY.subtreecumulativeEarnedPerMLiq, 13251904);

        assertEq(root.mLiq, 14035);
        assertEq(root.subtreeMLiq, 224560);
        assertEq(root.tLiq, 4381);
        assertEq(root.tokenX.borrowed, 832e18);
        assertEq(root.tokenX.subtreeBorrowed, 832e18);
        assertEq(root.tokenY.borrowed, 928e6);
        assertEq(root.tokenY.subtreeBorrowed, 928e6);

        // Testing add_inf_range_tLiq
        liqTree.feeRateSnapshotTokenY += 6932491854677024;
        liqTree.feeRateSnapshotTokenX += 6932491854677024;

        liqTree.addInfRangeTLiq(7287, 9184e18, 7926920e6);

        // earn_x      = 6932491854677024 * 832e18 / 224560 / 2**64 = 1392388963085.50927075184684754182568989829487082029858389739
        // earn_y      = 6932491854677024 * 928e6 / 224560 / 2**64  = 1.5530492280569141866078291761043440387327135097611022666547915924
        assertEq(root.tokenX.cumulativeEarnedPerMLiq, 11881019661491126559);           // 11881018269102163474 + 1392388963085 = 11881019661491126559
        assertEq(root.tokenX.subtreecumulativeEarnedPerMLiq, 11881019661491126559);   // 11881018269102163474 + 1392388963085 = 11881019661491126559
        assertEq(root.tokenY.cumulativeEarnedPerMLiq, 13251905);
        assertEq(root.tokenY.subtreecumulativeEarnedPerMLiq, 13251905);

        assertEq(root.mLiq, 14035);
        assertEq(root.subtreeMLiq, 224560);
        assertEq(root.tLiq, 11668);
        assertEq(root.tokenX.borrowed, 10016e18);
        assertEq(root.tokenX.subtreeBorrowed, 10016e18);
        assertEq(root.tokenY.borrowed, 7927848e6);
        assertEq(root.tokenY.subtreeBorrowed, 7927848e6);

        // Testing remove_inf_range_tLiq
        liqTree.feeRateSnapshotTokenY += 1055375100301031600000000;
        liqTree.feeRateSnapshotTokenX += 1055375100301031600000000;

        liqTree.removeInfRangeTLiq(4923, 222e18, 786e6);

        // earn_x      = 1055375100301031600000000 * 10016e18 / 224560 / 2**64  = 2551814126505030241953.87164028103035638433335980020216618053
        // earn_y      = 1055375100301031600000000 * 7927848e6 / 224560 / 2**64 = 2019807759503.25988354767545683493270255599285721099372431609
        assertEq(root.tokenX.cumulativeEarnedPerMLiq, 2563695146166521368512);          // 2551814126505030241953 + 11881019661491126559 = 2563695146166521368512
        assertEq(root.tokenX.subtreecumulativeEarnedPerMLiq, 2563695146166521368512);  // 2551814126505030241953 + 11881019661491126559 = 2563695146166521368512
        assertEq(root.tokenY.cumulativeEarnedPerMLiq, 2019821011408);                   // 2019807759503 + 13251905 = 2019821011408
        assertEq(root.tokenY.subtreecumulativeEarnedPerMLiq, 2019821011408);           // 2019807759503 + 13251905 = 2019821011408

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
        liqTree.feeRateSnapshotTokenX += 4541239648278065;
        liqTree.feeRateSnapshotTokenY += 13278814667749784;

        // Apply change that requires fee calculation
        // addMLiq
        liqTree.addMLiq(LiqRange(3, 7), 2734);  // LLRR, LR

        // root
        assertEq(root.tokenX.cumulativeEarnedPerMLiq, 373601278);
        assertEq(root.tokenX.subtreecumulativeEarnedPerMLiq, 2303115199);
        assertEq(root.tokenY.cumulativeEarnedPerMLiq, 0);
        assertEq(root.tokenY.subtreecumulativeEarnedPerMLiq, 2);

        // L
        assertEq(L.tokenX.cumulativeEarnedPerMLiq, 757991165);
        assertEq(L.tokenX.subtreecumulativeEarnedPerMLiq, 1929915382);
        assertEq(L.tokenY.cumulativeEarnedPerMLiq, 0);
        assertEq(L.tokenY.subtreecumulativeEarnedPerMLiq, 1);

        // LL
        assertEq(LL.tokenX.cumulativeEarnedPerMLiq, 581096415);
        assertEq(LL.tokenX.subtreecumulativeEarnedPerMLiq, 1153837196);
        assertEq(LL.tokenY.cumulativeEarnedPerMLiq, 0);
        assertEq(LL.tokenY.subtreecumulativeEarnedPerMLiq, 1);

        // LR
        assertEq(LR.tokenX.cumulativeEarnedPerMLiq, 148929881804);
        assertEq(LR.tokenX.subtreecumulativeEarnedPerMLiq, 148929881804);
        assertEq(LR.tokenY.cumulativeEarnedPerMLiq, 10);
        assertEq(LR.tokenY.subtreecumulativeEarnedPerMLiq, 10);

        // LLR
        assertEq(LLR.tokenX.cumulativeEarnedPerMLiq, 42651943);
        assertEq(LLR.tokenX.subtreecumulativeEarnedPerMLiq, 606784254);
        assertEq(LLR.tokenY.cumulativeEarnedPerMLiq, 0);
        assertEq(LLR.tokenY.subtreecumulativeEarnedPerMLiq, 1);

        // LLRR
        assertEq(LLRR.tokenX.cumulativeEarnedPerMLiq, 581500584);
        assertEq(LLRR.tokenX.subtreecumulativeEarnedPerMLiq, 581500584);
        assertEq(LLRR.tokenY.cumulativeEarnedPerMLiq, 1);
        assertEq(LLRR.tokenY.subtreecumulativeEarnedPerMLiq, 1);

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
        liqTree.feeRateSnapshotTokenX += 16463537718422861220174597;
        liqTree.feeRateSnapshotTokenY += 3715979586694123491881712207;

        // Apply change that requires fee calculation
        // remove_mLiq
        liqTree.removeMLiq(LiqRange(3, 7), 2734);  // LLRR, LR

        // root
        assertEq(root.tokenX.cumulativeEarnedPerMLiq, 1354374549844117328);
        assertEq(root.tokenX.subtreecumulativeEarnedPerMLiq, 8349223596904894020);
        assertEq(root.tokenY.cumulativeEarnedPerMLiq, 158351473403);
        assertEq(root.tokenY.subtreecumulativeEarnedPerMLiq, 710693401863);

        // L
        assertEq(L.tokenX.cumulativeEarnedPerMLiq, 2747859799935140577);
        assertEq(L.tokenX.subtreecumulativeEarnedPerMLiq, 6996304360355904016);
        assertEq(L.tokenY.cumulativeEarnedPerMLiq, 219375887);
        assertEq(L.tokenY.subtreecumulativeEarnedPerMLiq, 552456845956);

        // LL
        assertEq(LL.tokenX.cumulativeEarnedPerMLiq, 2106654304686669588);
        assertEq(LL.tokenX.subtreecumulativeEarnedPerMLiq, 4183016848129478568);
        assertEq(LL.tokenY.cumulativeEarnedPerMLiq, 62008538706);
        assertEq(LL.tokenY.subtreecumulativeEarnedPerMLiq, 551980602777);

        // LR
        assertEq(LR.tokenX.cumulativeEarnedPerMLiq, 423248578107618890129);
        assertEq(LR.tokenX.subtreecumulativeEarnedPerMLiq, 423248578107618890129);
        assertEq(LR.tokenY.cumulativeEarnedPerMLiq, 2197219781195);
        assertEq(LR.tokenY.subtreecumulativeEarnedPerMLiq, 2197219781195);

        // LLR
        assertEq(LLR.tokenX.cumulativeEarnedPerMLiq, 154626415017241476);
        assertEq(LLR.tokenX.subtreecumulativeEarnedPerMLiq, 2199779564584907057);
        assertEq(LLR.tokenY.cumulativeEarnedPerMLiq, 5771781665);
        assertEq(LLR.tokenY.subtreecumulativeEarnedPerMLiq, 519095539055);

        // LLRR
        assertEq(LLRR.tokenX.cumulativeEarnedPerMLiq, 2108117905996538332);
        assertEq(LLRR.tokenX.subtreecumulativeEarnedPerMLiq, 2108117905996538332);
        assertEq(LLRR.tokenY.cumulativeEarnedPerMLiq, 529127613135);
        assertEq(LLRR.tokenY.subtreecumulativeEarnedPerMLiq, 529127613135);

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
        liqTree.feeRateSnapshotTokenX += 11381610389149375791104;
        liqTree.feeRateSnapshotTokenY += 185394198934916215865344;

        // Apply change that requires fee calculation
        // addTLiq
        liqTree.addTLiq(LiqRange(3, 7), 1000, 1000e18, 1000e6);  // LLRR, LR

        // root
        assertEq(root.tokenX.cumulativeEarnedPerMLiq, 1355310898622008714);
        assertEq(root.tokenX.subtreecumulativeEarnedPerMLiq, 8354995844553968361);
        assertEq(root.tokenY.cumulativeEarnedPerMLiq, 158359374060);
        assertEq(root.tokenY.subtreecumulativeEarnedPerMLiq, 710728860612);

        // L
        assertEq(L.tokenX.cumulativeEarnedPerMLiq, 2749759536746020654);
        assertEq(L.tokenX.subtreecumulativeEarnedPerMLiq, 7001141265402443371);
        assertEq(L.tokenY.cumulativeEarnedPerMLiq, 219386832);
        assertEq(L.tokenY.subtreecumulativeEarnedPerMLiq, 552484409781);

        // LL
        assertEq(LL.tokenX.cumulativeEarnedPerMLiq, 2108110694023652835);
        assertEq(LL.tokenX.subtreecumulativeEarnedPerMLiq, 4185908685257423082);
        assertEq(LL.tokenY.cumulativeEarnedPerMLiq, 62011632404);
        assertEq(LL.tokenY.subtreecumulativeEarnedPerMLiq, 552008141912);

        // LR
        assertEq(LR.tokenX.cumulativeEarnedPerMLiq, 423621837838722923425);
        assertEq(LR.tokenX.subtreecumulativeEarnedPerMLiq, 423621837838722923425);
        assertEq(LR.tokenY.cumulativeEarnedPerMLiq, 2197359621190);
        assertEq(LR.tokenY.subtreecumulativeEarnedPerMLiq, 2197359621190);

        // LLR
        assertEq(LLR.tokenX.cumulativeEarnedPerMLiq, 154733312657952738);
        assertEq(LLR.tokenX.subtreecumulativeEarnedPerMLiq, 2201300334794271053);
        assertEq(LLR.tokenY.cumulativeEarnedPerMLiq, 5772069627);
        assertEq(LLR.tokenY.subtreecumulativeEarnedPerMLiq, 519121437518);

        // LLRR
        assertEq(LLRR.tokenX.cumulativeEarnedPerMLiq, 2109575308294031901);
        assertEq(LLRR.tokenX.subtreecumulativeEarnedPerMLiq, 2109575308294031901);
        assertEq(LLRR.tokenY.cumulativeEarnedPerMLiq, 529154012121);
        assertEq(LLRR.tokenY.subtreecumulativeEarnedPerMLiq, 529154012121);

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
        liqTree.feeRateSnapshotTokenX += 2352954287417905205553;
        liqTree.feeRateSnapshotTokenY += 6117681147286553534438;

        // Apply change that requires fee calculation
        // addTLiq
        liqTree.removeTLiq(LiqRange(3, 7), 1000, 1000e18, 1000e6);  // LLRR, LR

        // root
        assertEq(root.tokenX.cumulativeEarnedPerMLiq, 1355504472799662735);
        assertEq(root.tokenX.subtreecumulativeEarnedPerMLiq, 8356976045440416914);
        assertEq(root.tokenY.cumulativeEarnedPerMLiq, 158359634767);
        assertEq(root.tokenY.subtreecumulativeEarnedPerMLiq, 710730032734);

        // L
        assertEq(L.tokenX.cumulativeEarnedPerMLiq, 2750152275007241346);
        assertEq(L.tokenX.subtreecumulativeEarnedPerMLiq, 7002928263843528706);
        assertEq(L.tokenY.cumulativeEarnedPerMLiq, 219387193);
        assertEq(L.tokenY.subtreecumulativeEarnedPerMLiq, 552485321384);

        // LL
        assertEq(LL.tokenX.cumulativeEarnedPerMLiq, 2108411777738297592);
        assertEq(LL.tokenX.subtreecumulativeEarnedPerMLiq, 4186900096861593203);
        assertEq(LL.tokenY.cumulativeEarnedPerMLiq, 62011734490);
        assertEq(LL.tokenY.subtreecumulativeEarnedPerMLiq, 552009051678);

        // LR
        assertEq(LR.tokenX.cumulativeEarnedPerMLiq, 426914215366679462837);
        assertEq(LR.tokenX.subtreecumulativeEarnedPerMLiq, 426914215366679462837);
        assertEq(LR.tokenY.cumulativeEarnedPerMLiq, 2197372595215);
        assertEq(LR.tokenY.subtreecumulativeEarnedPerMLiq, 2197372595215);

        // LLR
        assertEq(LLR.tokenX.cumulativeEarnedPerMLiq, 154755411926283537);
        assertEq(LLR.tokenX.subtreecumulativeEarnedPerMLiq, 2202031695485822406);
        assertEq(LLR.tokenY.cumulativeEarnedPerMLiq, 5772079129);
        assertEq(LLR.tokenY.subtreecumulativeEarnedPerMLiq, 519122293205);

        // LLRR
        assertEq(LLRR.tokenX.cumulativeEarnedPerMLiq, 2110306406167095651);
        assertEq(LLRR.tokenX.subtreecumulativeEarnedPerMLiq, 2110306406167095651);
        assertEq(LLRR.tokenY.cumulativeEarnedPerMLiq, 529154884358);
        assertEq(LLRR.tokenY.subtreecumulativeEarnedPerMLiq, 529154884358);

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
        liqTree.feeRateSnapshotTokenX += 4541239648278065;   // 7.9% APR as Q192.64 T98273 - T0
        liqTree.feeRateSnapshotTokenY += 13278814667749784;  // 23.1% APR as Q192.64 T98273 - T0

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
        assertEq(root.tokenX.cumulativeEarnedPerMLiq, 373601278);
        assertEq(root.tokenX.subtreecumulativeEarnedPerMLiq, 2303115199);
        assertEq(root.tokenY.cumulativeEarnedPerMLiq, 0);
        assertEq(root.tokenY.subtreecumulativeEarnedPerMLiq, 2);

        // R
        //           total_mLiq = 324063953 + 8430 * 8 = 324131393
        //
        //           earn_x      = 4541239648278065 * 998e18 / 324131393 / 2**64 = 757991165.739306427787211084069081135461126639210612444989968
        //           earn_x_sub  = 4541239648278065 * 2541e18 / 324131393 / 2**64 = 1929915382.90939642585902140743440397315302884793002627527005
        //
        //           earn_y      = 13278814667749784 * 353e6 / 324131393 / 2**64 = 0.0007839587228619296743658765199435031723124415958637831459168088
        //           earn_y_sub  = 13278814667749784 * 888964e6 / 324131393 / 2**64 = 1.9742523572527831474305582285412361305143267162194111063081870320
        assertEq(R.tokenX.cumulativeEarnedPerMLiq, 757991165);
        assertEq(R.tokenX.subtreecumulativeEarnedPerMLiq, 1929915382);
        assertEq(R.tokenY.cumulativeEarnedPerMLiq, 0);
        assertEq(R.tokenY.subtreecumulativeEarnedPerMLiq, 1);

        // RR
        //           total_mLiq = 324056493 + (377 + 8430) * 4 = 324091721
        //
        //           earn_x      = 4541239648278065 * 765e18 / 324091721 / 2**64 = 581096415.560225831923714717876078601550264387092272644849535
        //           earn_x_sub  = 4541239648278065 * 1519e18 / 324091721 / 2**64 = 1153837196.38690593293087928948204365458150536469694398369469
        //
        //           earn_y      = 13278814667749784 * 99763e6 / 324091721 / 2**64 = 0.2215854043845212215658200680605818096232476901747430889861663960
        //           earn_y_sub  = 13278814667749784 * 888059e6 / 324091721 / 2**64 = 1.9724839131974131842719305135352006382347335233392357172695883598
        assertEq(RR.tokenX.cumulativeEarnedPerMLiq, 581096415);
        assertEq(RR.tokenX.subtreecumulativeEarnedPerMLiq, 1153837196);
        assertEq(RR.tokenY.cumulativeEarnedPerMLiq, 0);
        assertEq(RR.tokenY.subtreecumulativeEarnedPerMLiq, 1);

        // RL
        //           total_mLiq = 4444 + (377 + 8430) * 4 = 39672
        //
        //           earn_x      = 4541239648278065 * 24e18 / 39672 / 2**64 = 148929881804.004419784834421574153374302771710945632482252911
        //           earn_x_sub  = 4541239648278065 * 24e18 / 39672 / 2**64 = 148929881804.004419784834421574153374302771710945632482252911
        //
        //           earn_y      = 13278814667749784 * 552e6 / 39672 / 2**64 = 10.016005848413612945928345245285743980736658202469601316734724742
        //           earn_y_sub  = 13278814667749784 * 552e6 / 39672 / 2**64 = 10.016005848413612945928345245285743980736658202469601316734724742
        assertEq(RL.tokenX.cumulativeEarnedPerMLiq, 148929881804);
        assertEq(RL.tokenX.subtreecumulativeEarnedPerMLiq, 148929881804);
        assertEq(RL.tokenY.cumulativeEarnedPerMLiq, 10);
        assertEq(RL.tokenY.subtreecumulativeEarnedPerMLiq, 10);

        // RRL
        //           total_mLiq = 287725557 + (9082734 + 377 + 8430) * 2 = 305908639
        //
        //           earn_x      = 4541239648278065 * 53e18 / 305908639 / 2**64 = 42651943.5921096141810155248335108410236545389757231280339726
        //           earn_x_sub  = 4541239648278065 * 754e18 / 305908639 / 2**64 = 606784254.121710360235579353291833474185575894107457330898403
        //
        //           earn_y      = 13278814667749784 * 8765e6 / 305908639 / 2**64 = 0.0206252758466917150640245207131723061423410095348761855275430371
        //           earn_y_sub  = 13278814667749784 * 788296e6 / 305908639 / 2**64 = 1.8549711864054412114215942475882345970088817401374509465624718757
        assertEq(RRL.tokenX.cumulativeEarnedPerMLiq, 42651943);
        assertEq(RRL.tokenX.subtreecumulativeEarnedPerMLiq, 606784254);
        assertEq(RRL.tokenY.cumulativeEarnedPerMLiq, 0);
        assertEq(RRL.tokenY.subtreecumulativeEarnedPerMLiq, 1);

        // RRLL
        //           total_mLiq = 287634865 + (45346 + 9082734 + 377 + 8430) * 1 = 296771752
        //
        //           earn_x      = 4541239648278065 * 701e18 / 296771752 / 2**64 = 581500584.766017533363270505955415005042190229659676220491523
        //           earn_x_sub  = 4541239648278065 * 701e18 / 296771752 / 2**64 = 581500584.766017533363270505955415005042190229659676220491523
        //
        //           earn_y      = 13278814667749784 * 779531e6 / 296771752 / 2**64 = 1.8908210002218903501728143334071499784764070319492513392714860291
        //           earn_y_sub  = 13278814667749784 * 779531e6 / 296771752 / 2**64 = 1.8908210002218903501728143334071499784764070319492513392714860291
        assertEq(RRLL.tokenX.cumulativeEarnedPerMLiq, 581500584);
        assertEq(RRLL.tokenX.subtreecumulativeEarnedPerMLiq, 581500584);
        assertEq(RRLL.tokenY.cumulativeEarnedPerMLiq, 1);
        assertEq(RRLL.tokenY.subtreecumulativeEarnedPerMLiq, 1);

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
        liqTree.feeRateSnapshotTokenX += 16463537718422861220174597;    // 978567.9% APR as Q192.64 T2876298273 - T98273
        liqTree.feeRateSnapshotTokenY += 3715979586694123491881712207;  // 220872233.1% APR as Q192.64 T2876298273 - T98273

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
        assertEq(root.tokenX.cumulativeEarnedPerMLiq, 1354374549844117328);          // 373601278 + 1354374549470516050 = 1354374549844117328
        assertEq(root.tokenX.subtreecumulativeEarnedPerMLiq, 8349223596904894020);  // 2303115199 + 8349223594601778821 = 8349223596904894020
        assertEq(root.tokenY.cumulativeEarnedPerMLiq, 158351473403);                 // 0 + 158351473403 = 158351473403
        assertEq(root.tokenY.subtreecumulativeEarnedPerMLiq, 710693401863);         // 2 + 710693401861 = 710693401863

        // R
        //           total_mLiq = 324077623 + 8430 * 8 = 324145063
        //
        //           earn_x      = 16463537718422861220174597 * 998e18 / 324145063 / 2**64  = 2747859799177149412.40503918202324257122793136834755591677703
        //           earn_x_sub  = 16463537718422861220174597 * 2541e18 / 324145063 / 2**64 = 6996304358425988634.18958372897901740830678718133380719892830
        //
        //           earn_y      = 3715979586694123491881712207 * 353e6 / 324145063 / 2**64    = 219375887.687723491736647414380713113554572979392890952782027
        //           earn_y_sub  = 3715979586694123491881712207 * 888964e6 / 324145063 / 2**64 = 552456845955.890725518915105035513462543703722529807118835474
        assertEq(R.tokenX.cumulativeEarnedPerMLiq, 2747859799935140577);          // 757991165 + 2747859799177149412 = 2747859799935140577
        assertEq(R.tokenX.subtreecumulativeEarnedPerMLiq, 6996304360355904016);  // 1929915382 + 6996304358425988634 = 6996304360355904016
        assertEq(R.tokenY.cumulativeEarnedPerMLiq, 219375887);                    // 0 + 219375887 = 219375887 = 219375887
        assertEq(R.tokenY.subtreecumulativeEarnedPerMLiq, 552456845956);         // 1 + 552456845955 = 552456845956

        // RR
        //           total_mLiq = 324059227 + (377 + 8430) * 4 = 324094455
        //
        //           earn_x      = 16463537718422861220174597 * 765e18 / 324094455 / 2**64 = 2106654304105573173.10473569019029577351750175393657598084186
        //           earn_x_sub  = 16463537718422861220174597 * 1519e18 / 324094455 / 2**64 = 4183016846975641372.47855361228635199996481720814334498679581
        //
        //           earn_y      = 3715979586694123491881712207 * 99763e6 / 324094455 / 2**64  = 62008538706.1288411875002441524622314240784801570453009535875
        //           earn_y_sub  = 3715979586694123491881712207 * 888059e6 / 324094455 / 2**64 = 551980602776.841840924293368501262560029627326862519099461143
        assertEq(RR.tokenX.cumulativeEarnedPerMLiq, 2106654304686669588);          // 581096415 + 2106654304105573173 = 2106654304686669588
        assertEq(RR.tokenX.subtreecumulativeEarnedPerMLiq, 4183016848129478568);  // 1153837196 + 4183016846975641372 = 4183016848129478568
        assertEq(RR.tokenY.cumulativeEarnedPerMLiq, 62008538706);                  // 0 + 62008538706 = 62008538706
        assertEq(RR.tokenY.subtreecumulativeEarnedPerMLiq, 551980602777);         // 1 + 551980602776 = 551980602777

        // RL
        //           total_mLiq = 15380 + (377 + 8430) * 4 = 50608
        //
        //           earn_x      = 16463537718422861220174597 * 24e18 / 50608 / 2**64 = 423248577958689008325.429426909965566945601510047930853109815
        //           earn_x_sub  = 16463537718422861220174597 * 24e18 / 50608 / 2**64 = 423248577958689008325.429426909965566945601510047930853109815
        //
        //           earn_y      = 3715979586694123491881712207 * 552e6 / 50608 / 2**64 = 2197219781185.45157550848350683783177940360867452683580030548
        //           earn_y_sub  = 3715979586694123491881712207 * 552e6 / 50608 / 2**64 = 2197219781185.45157550848350683783177940360867452683580030548
        assertEq(RL.tokenX.cumulativeEarnedPerMLiq, 423248578107618890129);          // 148929881804 + 423248577958689008325 = 423248578107618890129
        assertEq(RL.tokenX.subtreecumulativeEarnedPerMLiq, 423248578107618890129);  // 148929881804 + 423248577958689008325 = 423248578107618890129
        assertEq(RL.tokenY.cumulativeEarnedPerMLiq, 2197219781195);                  // 10 + 2197219781185 = 2197219781195
        assertEq(RL.tokenY.subtreecumulativeEarnedPerMLiq, 2197219781195);          // 10 + 2197219781185 = 2197219781195

        // RRL
        //           total_mLiq = 287728291 + (9082734 + 377 + 8430) * 2 = 305911373
        //
        //           earn_x      = 16463537718422861220174597 * 53e18 / 305911373 / 2**64 = 154626414974589533.957746783298485424790431468186321359344549
        //           earn_x_sub  = 16463537718422861220174597 * 754e18 / 305911373 / 2**64 = 2199779563978122803.85171838881241528852802503797143971595830
        //
        //           earn_y      = 3715979586694123491881712207 * 8765e6 / 305911373 / 2**64 = 5771781665.52844938596716448955303604219154769320799186650875
        //           earn_y_sub  = 3715979586694123491881712207 * 788296e6 / 305911373 / 2**64 = 519095539054.126016789546137872983468330339792397614050929992
        assertEq(RRL.tokenX.cumulativeEarnedPerMLiq, 154626415017241476);           // 42651943 + 154626414974589533 = 154626415017241476 (sol losses 1 wei)
        assertEq(RRL.tokenX.subtreecumulativeEarnedPerMLiq, 2199779564584907057);  // 606784254 + 2199779563978122803 = 2199779564584907057
        assertEq(RRL.tokenY.cumulativeEarnedPerMLiq, 5771781665);                   // 0 + 5771781665 = 5771781665
        assertEq(RRL.tokenY.subtreecumulativeEarnedPerMLiq, 519095539055);         // 1 + 519095539054 = 519095539055

        // RRLL
        //           total_mLiq = 287637599 + (45346 + 9082734 + 377 + 8430) * 1 = 296774486
        //
        //           earn_x      = 16463537718422861220174597 * 701e18 / 296774486 / 2**64 = 2108117905415037748.37451632639936795389368532390933657093156
        //           earn_x_sub  = 16463537718422861220174597 * 701e18 / 296774486 / 2**64 = 2108117905415037748.37451632639936795389368532390933657093156
        //
        //           earn_y      = 3715979586694123491881712207 * 779531e6 / 296774486 / 2**64 = 529127613134.050803777279185858502873428448836282593499892809
        //           earn_y_sub  = 3715979586694123491881712207 * 779531e6 / 296774486 / 2**64 = 529127613134.050803777279185858502873428448836282593499892809
        assertEq(RRLL.tokenX.cumulativeEarnedPerMLiq, 2108117905996538332);          // 581500584 + 2108117905415037748 = 2108117905996538332
        assertEq(RRLL.tokenX.subtreecumulativeEarnedPerMLiq, 2108117905996538332);  // 581500584 + 2108117905415037748 = 2108117905996538332
        assertEq(RRLL.tokenY.cumulativeEarnedPerMLiq, 529127613135);                 // 1 + 529127613134 = 529127613135
        assertEq(RRLL.tokenY.subtreecumulativeEarnedPerMLiq, 529127613135);         // 1 + 529127613134 = 529127613135

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
        liqTree.feeRateSnapshotTokenX += 11381610389149375791104;   // 307% APR as Q192.64 T9214298113 - T2876298273
        liqTree.feeRateSnapshotTokenY += 185394198934916215865344;  // 5000.7% APR as Q192.64 T9214298113 - T2876298273

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
        assertEq(root.tokenX.cumulativeEarnedPerMLiq, 1355310898622008714);          // 373601278 + 1354374549470516050 + 936348777891386 = 1355310898622008714
        assertEq(root.tokenX.subtreecumulativeEarnedPerMLiq, 8354995844553968361);  // 2303115199 + 8349223594601778821 + 5772247649074341 = 8354995844553968361
        assertEq(root.tokenY.cumulativeEarnedPerMLiq, 158359374060);                 // 0 + 158351473403 + 7900657 = 158359374060
        assertEq(root.tokenY.subtreecumulativeEarnedPerMLiq, 710728860612);         // 2 + 710693401861 + 35458749 = 710728860612

        // R
        //           total_mLiq = 324063953 + 8430 * 8 = 324131393
        //
        //           earn_x      = 11381610389149375791104 * 998e18 / 324131393 / 2**64  = 1899736810880077.58842507649572740061066261792173891653870132
        //           earn_x_sub  = 11381610389149375791104 * 2541e18 / 324131393 / 2**64 = 4836905046539355.86391595127819972440049470154222303299082171
        //
        //           earn_y      = 185394198934916215865344 * 353e6 / 324131393 / 2**64    = 10945.359436035932129843115196215424291564802240553108041589788249
        //           earn_y_sub  = 185394198934916215865344 * 888964e6 / 324131393 / 2**64 = 27563825.7951735024642318840149814403397354471925525584619938
        assertEq(R.tokenX.cumulativeEarnedPerMLiq, 2749759536746020654);          // 757991165 + 2747859799177149412 + 1899736810880077 = 2749759536746020654
        assertEq(R.tokenX.subtreecumulativeEarnedPerMLiq, 7001141265402443371);  // 1929915382 + 6996304358425988634 + 4836905046539355 = 7001141265402443371
        assertEq(R.tokenY.cumulativeEarnedPerMLiq, 219386832);                    // 0 + 219375887 + 10945 = 219386832
        assertEq(R.tokenY.subtreecumulativeEarnedPerMLiq, 552484409781);         // 1 + 552456845955 + 27563825 = 552484409781

        // RR
        //           total_mLiq = 324056493 + (377 + 8430) * 4 = 324091721
        //
        //           earn_x      = 11381610389149375791104 * 765e18 / 324091721 / 2**64  = 1456389336983247.97581853577374895245788594982344519686141566
        //           earn_x_sub  = 11381610389149375791104 * 1519e18 / 324091721 / 2**64 = 2891837127944514.60819392920303876965167157879975588762417044
        //
        //           earn_y      = 185394198934916215865344 * 99763e6 / 324091721 / 2**64  = 3093698.46401352576654665825318763474490453834363760251685046
        //           earn_y_sub  = 185394198934916215865344 * 888059e6 / 324091721 / 2**64 = 27539135.3934162733549879091613880669579421169863823827823111
        assertEq(RR.tokenX.cumulativeEarnedPerMLiq, 2108110694023652835);          // 581096415 + 2106654304105573173+ 1456389336983247 = 2108110694023652835
        assertEq(RR.tokenX.subtreecumulativeEarnedPerMLiq, 4185908685257423082);  // 1153837196 + 4183016846975641372 + 2891837127944514 = 4185908685257423082
        assertEq(RR.tokenY.cumulativeEarnedPerMLiq, 62011632404);                  // 0 + 62008538706 + 3093698 = 62011632404
        assertEq(RR.tokenY.subtreecumulativeEarnedPerMLiq, 552008141912);         // 1 + 551980602776 + 27539135 = 552008141912

        // RL
        //           total_mLiq = 4444 + (377 + 8430) * 4 = 39672
        //
        //           earn_x      = 11381610389149375791104 * 24e18 / 39672 / 2**64 = 373259731104033296.286645111573225645606473079249848759830611
        //           earn_x_sub  = 11381610389149375791104 * 24e18 / 39672 / 2**64 = 373259731104033296.286645111573225645606473079249848759830611
        //
        //           earn_y      = 185394198934916215865344 * 552e6 / 39672 / 2**64 = 139839995.304998697233270837982279275016069267997580157289776
        //           earn_y_sub  = 185394198934916215865344 * 552e6 / 39672 / 2**64 = 139839995.304998697233270837982279275016069267997580157289776
        assertEq(RL.tokenX.cumulativeEarnedPerMLiq, 423621837838722923425);          // 148929881804 + 423248577958689008325 + 373259731104033296 = 423621837838722923425
        assertEq(RL.tokenX.subtreecumulativeEarnedPerMLiq, 423621837838722923425);  // 148929881804 + 423248577958689008325 + 373259731104033296 = 423621837838722923425
        assertEq(RL.tokenY.cumulativeEarnedPerMLiq, 2197359621190);                  // 10 + 2197219781185 + 139839995 = 2197359621190
        assertEq(RL.tokenY.subtreecumulativeEarnedPerMLiq, 2197359621190);          // 10 + 2197219781185 + 139839995 = 2197359621190

        // RRL
        //           total_mLiq = 287725557 + (9082734 + 377 + 8430) * 2 = 305908639
        //
        //           earn_x      = 11381610389149375791104 * 53e18 / 305908639 / 2**64  = 106897640711262.335596794608928382455998365904272484439381916
        //           earn_x_sub  = 11381610389149375791104 * 754e18 / 305908639 / 2**64 = 1520770209363996.24603741764400000701552392248719723145837669
        //
        //           earn_y      = 185394198934916215865344 * 8765e6 / 305908639 / 2**64   = 287962.93864210284405202260308978443477406072046236000546555339354
        //           earn_y_sub  = 185394198934916215865344 * 788296e6 / 305908639 / 2**64 = 25898463.5116731435886860479093285465823905270619049107665115
        assertEq(RRL.tokenX.cumulativeEarnedPerMLiq, 154733312657952738);           // 42651943 + 154626414974589533 + 106897640711262 = 154733312657952738
        assertEq(RRL.tokenX.subtreecumulativeEarnedPerMLiq, 2201300334794271053);  // 606784254 + 2199779563978122803 + 1520770209363996 = 2201300334794271053
        assertEq(RRL.tokenY.cumulativeEarnedPerMLiq, 5772069627);                   // 0 + 5771781665 + 287962 = 5772069627
        assertEq(RRL.tokenY.subtreecumulativeEarnedPerMLiq, 519121437518);         // 1 + 519095539054 + 25898463 = 519121437518

        // RRLL
        //           total_mLiq = 287634865 + (45346 + 9082734 + 377 + 8430) * 1 = 296771752
        //
        //           earn_x      = 11381610389149375791104 * 701e18 / 296771752 / 2**64 = 1457402297493569.71876500861500730007660377831377967536479010
        //           earn_x_sub  = 11381610389149375791104 * 701e18 / 296771752 / 2**64 = 1457402297493569.71876500861500730007660377831377967536479010
        //
        //           earn_y      = 185394198934916215865344 * 779531e6 / 296771752 / 2**64 = 26398986.1622835510939886934876573358559478744206759947961624
        //           earn_y_sub  = 185394198934916215865344 * 779531e6 / 296771752 / 2**64 = 26398986.1622835510939886934876573358559478744206759947961624
        assertEq(RRLL.tokenX.cumulativeEarnedPerMLiq, 2109575308294031901);          // 581500584 + 2108117905415037748 + 1457402297493569 = 2109575308294031901
        assertEq(RRLL.tokenX.subtreecumulativeEarnedPerMLiq, 2109575308294031901);  // 581500584 + 2108117905415037748 + 1457402297493569 = 2109575308294031901
        assertEq(RRLL.tokenY.cumulativeEarnedPerMLiq, 529154012121);                 // 1 + 529127613134 + 26398986 = 529154012121
        assertEq(RRLL.tokenY.subtreecumulativeEarnedPerMLiq, 529154012121);         // 1 + 529127613134 + 26398986 = 529154012121

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
        liqTree.feeRateSnapshotTokenX += 2352954287417905205553;  // 17% APR as Q192.64 T32876298273 - T9214298113
        liqTree.feeRateSnapshotTokenY += 6117681147286553534438;  // 44.2% APR as Q192.64 T32876298273 - T9214298113

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
        assertEq(root.tokenX.cumulativeEarnedPerMLiq, 1355504472799662735);         // 373601278 + 1354374549470516050 + 936348777891386 + 193574177654021 = 1355504472799662735
        assertEq(root.tokenX.subtreecumulativeEarnedPerMLiq, 8356976045440416914); // 2303115199 + 8349223594601778821 + 5772247649074341 + 1980200886448553 = 8356976045440416914
        assertEq(root.tokenY.cumulativeEarnedPerMLiq, 158359634767);                // 0 + 158351473403 + 7900657 + 260707 = 158359634767
        assertEq(root.tokenY.subtreecumulativeEarnedPerMLiq, 710730032734);        // 2 + 710693401861 + 35458749 + 1172122 = 710730032734

        // R
        //           total_mLiq = 324063953 + 8430 * 8 = 324131393
        //
        //           earn_x      = 2352954287417905205553 * 998e18 / 324131393 / 2**64  = 392738261220692.635199129066166314911263418663640357414414483
        //           earn_x_sub  = 2352954287417905205553 * 4541e18 / 324131393 / 2**64 = 1786998441085335.92829583676298721043291301017193473248382381
        //
        //           earn_y      = 6117681147286553534438 * 353e6 / 324131393 / 2**64    = 361.17753121077324707993230558447820693195086120933424789750836934
        //           earn_y_sub  = 6117681147286553534438 * 890964e6 / 324131393 / 2**64 = 911603.90344950531249667084054608793530005288132156736216361373026
        assertEq(R.tokenX.cumulativeEarnedPerMLiq, 2750152275007241346);          // 757991165 + 2747859799177149412 + 1899736810880077 + 392738261220692 = 2750152275007241346
        assertEq(R.tokenX.subtreecumulativeEarnedPerMLiq, 7002928263843528706);  // 1929915382 + 6996304358425988634 + 4836905046539355 + 1786998441085335 = 7002928263843528706
        assertEq(R.tokenY.cumulativeEarnedPerMLiq, 219387193);                    // 0 + 219375887 + 10945 + 361 = 219387193
        assertEq(R.tokenY.subtreecumulativeEarnedPerMLiq, 552485321384);         // 1 + 552456845955 + 27563825 + 911603 = 552485321384

        // RR
        //           total_mLiq = 324056493 + (377 + 8430) * 4 = 324091721
        //
        //           earn_x      = 2352954287417905205553 * 765e18 / 324091721 / 2**64  = 301083714644757.116282263044928314612316183509300881282164628
        //           earn_x_sub  = 2352954287417905205553 * 2519e18 / 324091721 / 2**64 = 991411604170121.798581726287809705239770544130626039150029671
        //
        //           earn_y      = 6117681147286553534438 * 99763e6 / 324091721 / 2**64  = 102086.58565055261555338276382365173781133864709615634713615821960
        //           earn_y_sub  = 6117681147286553534438 * 889059e6 / 324091721 / 2**64 = 909766.12323100405793004346924503062625232727813579850073199172604
        assertEq(RR.tokenX.cumulativeEarnedPerMLiq, 2108411777738297592);          // 581096415 + 2106654304105573173+ 1456389336983247 + 301083714644757 = 2108411777738297592
        assertEq(RR.tokenX.subtreecumulativeEarnedPerMLiq, 4186900096861593203);  // 1153837196 + 4183016846975641372 + 2891837127944514 + 991411604170121 = 4186900096861593203
        assertEq(RR.tokenY.cumulativeEarnedPerMLiq, 62011734490);                  // 0 + 62008538706 + 3093698 + 102086 = 62011734490
        assertEq(RR.tokenY.subtreecumulativeEarnedPerMLiq, 552009051678);         // 1 + 551980602776 + 27539135 + 909766 = 552009051678

        // RL
        //           total_mLiq = 4444 + (377 + 8430) * 4 = 39672
        //
        //           earn_x      = 2352954287417905205553 * 1024e18 / 39672 / 2**64 = 3292377527956539412.11877691362144195603424231355578266196876
        //           earn_x_sub  = 2352954287417905205553 * 1024e18 / 39672 / 2**64 = 3292377527956539412.11877691362144195603424231355578266196876
        //
        //           earn_y      = 6117681147286553534438 * 1552e6 / 39672 / 2**64 = 12974025.1961037381208809794236997935340918048320067315891063
        //           earn_y_sub  = 6117681147286553534438 * 1552e6 / 39672 / 2**64 = 12974025.1961037381208809794236997935340918048320067315891063
        assertEq(RL.tokenX.cumulativeEarnedPerMLiq, 426914215366679462837);          // 148929881804 + 423248577958689008325 + 373259731104033296 + 3292377527956539412 = 426914215366679462837
        assertEq(RL.tokenX.subtreecumulativeEarnedPerMLiq, 426914215366679462837);  // 148929881804 + 423248577958689008325 + 373259731104033296 + 3292377527956539412 = 426914215366679462837
        assertEq(RL.tokenY.cumulativeEarnedPerMLiq, 2197372595215);                  // 10 + 2197219781185 + 139839995 + 12974025 = 2197372595215
        assertEq(RL.tokenY.subtreecumulativeEarnedPerMLiq, 2197372595215);          // 10 + 2197219781185 + 139839995 + 12974025 = 2197372595215

        // RRL
        //           total_mLiq = 287725557 + (9082734 + 377 + 8430) * 2 = 305908639
        //
        //           earn_x      = 2352954287417905205553 * 53e18 / 305908639 / 2**64   = 22099268330799.1616184419285239088656103478160451926038962236
        //           earn_x_sub  = 2352954287417905205553 * 1754e18 / 305908639 / 2**64 = 731360691551353.386391455521338417929821699421571091079886346
        //
        //           earn_y      = 6117681147286553534438 * 8765e6 / 305908639 / 2**64   = 9502.2684149166432853337655386227368949210477797554902569919214852
        //           earn_y_sub  = 6117681147286553534438 * 789296e6 / 305908639 / 2**64 = 855687.67265488270148782656070425233773115839456587443672363898010
        assertEq(RRL.tokenX.cumulativeEarnedPerMLiq, 154755411926283537);           // 42651943 + 154626414974589533 + 106897640711262 + 22099268330799 = 154755411926283537
        assertEq(RRL.tokenX.subtreecumulativeEarnedPerMLiq, 2202031695485822406);  // 606784254 + 2199779563978122803 + 1520770209363996 + 731360691551353 = 2202031695485822406
        assertEq(RRL.tokenY.cumulativeEarnedPerMLiq, 5772079129);                   // 0 + 5771781665 + 287962 + 9502 = 5772079129
        assertEq(RRL.tokenY.subtreecumulativeEarnedPerMLiq, 519122293205);         // 1 + 519095539054 + 25898463 + 855687 = 519122293205

        // RRLL
        //           total_mLiq = 287634865 + (45346 + 9082734 + 377 + 8430) * 1 = 296771752
        //
        //           earn_x      = 2352954287417905205553 * 1701e18 / 296771752 / 2**64 = 731097873063750.150068233826063023165648387512288880115659770
        //           earn_x_sub  = 2352954287417905205553 * 1701e18 / 296771752 / 2**64 = 731097873063750.150068233826063023165648387512288880115659770
        //
        //           earn_y      = 6117681147286553534438 * 780531e6 / 296771752 / 2**64 = 872237.41346080959306032387265895687662997868016869971844802082307
        //           earn_y_sub  = 6117681147286553534438 * 780531e6 / 296771752 / 2**64 = 872237.41346080959306032387265895687662997868016869971844802082307
        assertEq(RRLL.tokenX.cumulativeEarnedPerMLiq, 2110306406167095651);          // 581500584 + 2108117905415037748 + 1457402297493569 + 731097873063750 = 2110306406167095651
        assertEq(RRLL.tokenX.subtreecumulativeEarnedPerMLiq, 2110306406167095651);  // 581500584 + 2108117905415037748 + 1457402297493569 + 731097873063750 = 2110306406167095651
        assertEq(RRLL.tokenY.cumulativeEarnedPerMLiq, 529154884358);                 // 1 + 529127613134 + 26398986 + 872237 = 529154884358
        assertEq(RRLL.tokenY.subtreecumulativeEarnedPerMLiq, 529154884358);         // 1 + 529127613134 + 26398986 + 872237 = 529154884358

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

    function testLeftAndRightLegStoppingBelowPeak() public {
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

        LiqNode storage L = liqTree.nodes[LKey.wrap((8 << 24) | 16)];
        LiqNode storage LL = liqTree.nodes[LKey.wrap((4 << 24) | 16)];
        LiqNode storage LR = liqTree.nodes[LKey.wrap((4 << 24) | 20)];
        LiqNode storage LLL = liqTree.nodes[LKey.wrap((2 << 24) | 16)];
        LiqNode storage LLR = liqTree.nodes[LKey.wrap((2 << 24) | 18)];
        LiqNode storage LRL = liqTree.nodes[LKey.wrap((2 << 24) | 20)];
        LiqNode storage LLLR = liqTree.nodes[LKey.wrap((1 << 24) | 17)];
        LiqNode storage LRLL = liqTree.nodes[LKey.wrap((1 << 24) | 20)];

        // Pre-populate nodes w/o fee calculation
        liqTree.addInfRangeMLiq(432);
        liqTree.addMLiq(LiqRange(0, 7), 98237498262);      // L
        liqTree.addMLiq(LiqRange(0, 3), 932141354);        // LL
        liqTree.addMLiq(LiqRange(4, 7), 151463465);        // LR
        liqTree.addMLiq(LiqRange(0, 1), 45754683688356);   // LLL
        liqTree.addMLiq(LiqRange(2, 3), 245346257245745);  // LLR
        liqTree.addMLiq(LiqRange(4, 5), 243457472);        // LRL
        liqTree.addMLiq(LiqRange(1, 1), 2462);             // LLLR
        liqTree.addMLiq(LiqRange(4, 4), 45656756785);      // LRLL

        liqTree.addTLiq(LiqRange(0, 7), 5645645, 4357e18, 345345345e6);        // L
        liqTree.addTLiq(LiqRange(0, 3), 3456835, 293874927834e18, 2345346e6);  // LL
        liqTree.addTLiq(LiqRange(4, 7), 51463465, 23452e18, 12341235e6);       // LR
        liqTree.addTLiq(LiqRange(0, 1), 23453467234, 134235e18, 34534634e6);   // LLL
        liqTree.addTLiq(LiqRange(2, 3), 456756745, 1233463e18, 2341356e6);     // LLR
        liqTree.addTLiq(LiqRange(4, 5), 3457472, 45e18, 1324213563456457e6);   // LRL
        liqTree.addTLiq(LiqRange(1, 1), 262, 4567e18, 1235146e6);              // LLLR
        liqTree.addTLiq(LiqRange(4, 4), 4564573, 4564564e18, 6345135e6);       // LRLL

        // Verify initial state
        // mLiq
        assertEq(root.mLiq, 432);
        assertEq(L.mLiq, 98237498262);
        assertEq(LL.mLiq, 932141354);
        assertEq(LR.mLiq, 151463465);
        assertEq(LLL.mLiq, 45754683688356);
        assertEq(LLR.mLiq, 245346257245745);
        assertEq(LRL.mLiq, 243457472);
        assertEq(LLLR.mLiq, 2462);
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
        assertEq(root.subtreeMLiq, 583038259954677);  // 432*16 + 98237498262*8 + 932141354*4 + 151463465*4 + 45754683688356*2 + 245346257245745*2 + 243457472*2 + 2462*1 + 45656756785*1 = 583038259954677
        assertEq(L.subtreeMLiq, 583038259947765);     // 98237498262*8 + 932141354*4 + 151463465*4 + 45754683688356*2 + 245346257245745*2 + 243457472*2 + 2462*1 + 45656756785*1 = 583038259947765
        assertEq(LL.subtreeMLiq, 582205610436080);    // 932141354*4 + 45754683688356*2 + 245346257245745*2 + 2462*1 = 582205610436080
        assertEq(LR.subtreeMLiq, 46749525589);        // 151463465*4 + 243457472*2 + 45656756785*1 = 46749525589
        assertEq(LLL.subtreeMLiq, 91509367379174);    // 45754683688356*2 + 2462*1 = 91509367379174
        assertEq(LLR.subtreeMLiq, 490692514491490);   // 245346257245745*2 = 490692514491490
        assertEq(LRL.subtreeMLiq, 46143671729);       // 243457472*2 + 45656756785*1 = 46143671729
        assertEq(LLLR.subtreeMLiq, 2462);             // 2462*1 = 2462
        assertEq(LRLL.subtreeMLiq, 45656756785);      // 45656756785*1 = 45656756785

        // borrowed_x
        assertEq(root.tokenX.borrowed, 0);
        assertEq(L.tokenX.borrowed, 4357e18);
        assertEq(LL.tokenX.borrowed, 293874927834e18);
        assertEq(LR.tokenX.borrowed, 23452e18);
        assertEq(LLL.tokenX.borrowed, 134235e18);
        assertEq(LLR.tokenX.borrowed, 1233463e18);
        assertEq(LRL.tokenX.borrowed, 45e18);
        assertEq(LLLR.tokenX.borrowed, 4567e18);
        assertEq(LRLL.tokenX.borrowed, 4564564e18);

        // subtree_borrowed_x
        assertEq(root.tokenX.subtreeBorrowed, 293880892517e18);  // 0 + 4357e18 + 293874927834e18 + 23452e18 + 134235e18 + 1233463e18 + 45e18 + 4567e18 + 4564564e18 = 293880892517e18
        assertEq(L.tokenX.subtreeBorrowed, 293880892517e18);     // 4357e18 + 293874927834e18 + 23452e18 + 134235e18 + 1233463e18 + 45e18 + 4567e18 + 4564564e18 = 293880892517e18
        assertEq(LL.tokenX.subtreeBorrowed, 293876300099e18);    // 293874927834e18 + 134235e18 + 1233463e18 + 4567e18 = 293876300099e18
        assertEq(LR.tokenX.subtreeBorrowed, 4588061e18);         // 23452e18 + 45e18 + 4564564e18 = 4588061e18
        assertEq(LLL.tokenX.subtreeBorrowed, 138802e18);         // 134235e18 + 4567e18 = 138802e18
        assertEq(LLR.tokenX.subtreeBorrowed, 1233463e18);        // 1233463e18
        assertEq(LRL.tokenX.subtreeBorrowed, 4564609e18);        // 45e18 + 4564564e18 = 4564609e18
        assertEq(LLLR.tokenX.subtreeBorrowed, 4567e18);          // 4567e18
        assertEq(LRLL.tokenX.subtreeBorrowed, 4564564e18);       // 4564564e18

        // borrowed_y
        assertEq(root.tokenY.borrowed, 0);
        assertEq(L.tokenY.borrowed, 345345345e6);
        assertEq(LL.tokenY.borrowed, 2345346e6);
        assertEq(LR.tokenY.borrowed, 12341235e6);
        assertEq(LLL.tokenY.borrowed, 34534634e6);
        assertEq(LLR.tokenY.borrowed, 2341356e6);
        assertEq(LRL.tokenY.borrowed, 1324213563456457e6);
        assertEq(LLLR.tokenY.borrowed, 1235146e6);
        assertEq(LRLL.tokenY.borrowed, 6345135e6);

        // subtree_borrowed_y
        assertEq(root.tokenY.subtreeBorrowed, 1324213967944654e6);  // 0 + 345345345e6 + 2345346e6 + 12341235e6 + 34534634e6 + 2341356e6 + 1324213563456457e6 + 1235146e6 + 6345135e6 = 1324213967944654e6
        assertEq(L.tokenY.subtreeBorrowed, 1324213967944654e6);     // 345345345e6 + 2345346e6 + 12341235e6 + 34534634e6 + 2341356e6 + 1324213563456457e6 + 1235146e6 + 6345135e6 = 1324213967944654e6
        assertEq(LL.tokenY.subtreeBorrowed, 40456482e6);            // 2345346e6 + 34534634e6 + 2341356e6 + 1235146e6 = 40456482e6
        assertEq(LR.tokenY.subtreeBorrowed, 1324213582142827e6);    // 12341235e6 + 1324213563456457e6 + 6345135e6 = 1324213582142827e6
        assertEq(LLL.tokenY.subtreeBorrowed, 35769780e6);           // 34534634e6 + 1235146e6 = 35769780e6
        assertEq(LLR.tokenY.subtreeBorrowed, 2341356e6);            // 2341356e6
        assertEq(LRL.tokenY.subtreeBorrowed, 1324213569801592e6);   // 1324213563456457e6 + 6345135e6 = 1324213569801592e6
        assertEq(LLLR.tokenY.subtreeBorrowed, 1235146e6);           // 1235146e6
        assertEq(LRLL.tokenY.subtreeBorrowed, 6345135e6);           // 6345135e6

        // Test fees while targeting (1, 4)
        // 1) Trigger fee update through path L->LL->LLR by updating LLR
        liqTree.feeRateSnapshotTokenX += 997278349210980290827452342352346;
        liqTree.feeRateSnapshotTokenY += 7978726162930599238079167453467080976862;

        liqTree.addMLiq(LiqRange(2, 3), 564011300817682367503451461);     // LLR
        liqTree.removeMLiq(LiqRange(2, 3), 564011300817682367503451461);  // LLR

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
        assertEq(LLR.tokenX.subtreecumulativeEarnedPerMLiq, 135843184601648135054031);
        assertEq(LLR.tokenY.cumulativeEarnedPerMLiq, 2062986327173371860);
        assertEq(LLR.tokenY.subtreecumulativeEarnedPerMLiq, 2062986327173371860);

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
        assertEq(LL.tokenX.subtreecumulativeEarnedPerMLiq, 27270419858159151079872803581);
        assertEq(LL.tokenY.cumulativeEarnedPerMLiq, 1741210798541653346);
        assertEq(LL.tokenY.subtreecumulativeEarnedPerMLiq, 30035339489101405447);

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
        assertEq(L.tokenX.subtreecumulativeEarnedPerMLiq, 27250279648794479314672290097);
        assertEq(L.tokenY.cumulativeEarnedPerMLiq, 256194846273571639740);
        assertEq(L.tokenY.subtreecumulativeEarnedPerMLiq, 982369673901053899051127131);

        // 2) Trigger fee update through path L->LR->LRL->LRLL by updating LRLL
        liqTree.addMLiq(LiqRange(4, 4), 45656756785);     // LRLL
        liqTree.removeMLiq(LiqRange(4, 4), 45656756785);  // LRLL

        // LRLL
        //   total_mLiq = 45656756785 + (243457472 + 151463465 + 98237498262 + 432) * 1 = 144289176416
        //
        //   earn_x      = 997278349210980290827452342352346 * 4564564e18 / 144289176416 / 2**64 = 1710260298962014449572659226.45857973175650767716107059096213
        //   earn_x_sub  = 997278349210980290827452342352346 * 4564564e18 / 144289176416 / 2**64 = 1710260298962014449572659226.45857973175650767716107059096213
        //
        //   earn_y      = 7978726162930599238079167453467080976862 * 6345135e6 / 144289176416 / 2**64 = 19020457094450723823822.1304935642458081127558849886746302550
        //   earn_y_sub  = 7978726162930599238079167453467080976862 * 6345135e6 / 144289176416 / 2**64 = 19020457094450723823822.1304935642458081127558849886746302550
        assertEq(LRLL.tokenX.cumulativeEarnedPerMLiq, 1710260298962014449572659226);
        assertEq(LRLL.tokenX.subtreecumulativeEarnedPerMLiq, 1710260298962014449572659226);
        assertEq(LRLL.tokenY.cumulativeEarnedPerMLiq, 19020457094450723823822);
        assertEq(LRLL.tokenY.subtreecumulativeEarnedPerMLiq, 19020457094450723823822);

        // LRL
        //   total_mLiq = 46143671729 + (151463465 + 98237498262 + 432) * 2 = 242921596047
        //
        //   earn_x      = 997278349210980290827452342352346 * 45e18 / 242921596047 / 2**64 = 10014817880995372310152.4742715985679179265308809095477236672
        //   earn_x_sub  = 997278349210980290827452342352346 * 4564609e18 / 242921596047 / 2**64 = 1015860618510053453450506120.72016150011730453772839221611958
        //
        //   earn_y      = 7978726162930599238079167453467080976862 * 1324213563456457e6 / 242921596047 / 2**64 = 2357793377238426581071757403793.96341043019973158984354448841
        //   earn_y_sub  = 7978726162930599238079167453467080976862 * 1324213569801592e6 / 242921596047 / 2**64 = 2357793388536088599903418420664.92708711347544674139375617462
        assertEq(LRL.tokenX.cumulativeEarnedPerMLiq, 10014817880995372310152);
        assertEq(LRL.tokenX.subtreecumulativeEarnedPerMLiq, 1015860618510053453450506120);
        assertEq(LRL.tokenY.cumulativeEarnedPerMLiq, 2357793377238426581071757403793);
        assertEq(LRL.tokenY.subtreecumulativeEarnedPerMLiq, 2357793388536088599903418420664);

        // LR
        //   total_mLiq = 46749525589 + (98237498262 + 432) * 4 = 439699520365
        //
        //   earn_x      = 997278349210980290827452342352346 * 23452e18 / 439699520365 / 2**64 = 2883504023897755903335799.02165969971328846599101621918354759
        //   earn_x_sub  = 997278349210980290827452342352346 * 4588061e18 / 439699520365 / 2**64 = 564117872905865676599639663.786245246727357690738865154506505
        //
        //   earn_y      = 7978726162930599238079167453467080976862 * 12341235e6 / 439699520365 / 2**64 = 12139937971620398360316.5575159331335181718549141795773004218
        //   earn_y_sub  = 7978726162930599238079167453467080976862 * 1324213582142827e6 / 439699520365 / 2**64 = 1302614426221619876588878010887.22237028229312127108609228047
        assertEq(LR.tokenX.cumulativeEarnedPerMLiq, 2883504023897755903335799);
        assertEq(LR.tokenX.subtreecumulativeEarnedPerMLiq, 564117872905865676599639663);
        assertEq(LR.tokenY.cumulativeEarnedPerMLiq, 12139937971620398360316);
        assertEq(LR.tokenY.subtreecumulativeEarnedPerMLiq, 1302614426221619876588878010887);

        // L
        // Borrows have not changed. Results should be the same!
        assertEq(L.tokenX.cumulativeEarnedPerMLiq, 404005403049228369014);
        assertEq(L.tokenX.subtreecumulativeEarnedPerMLiq, 27250279648794479314672290097);
        assertEq(L.tokenY.cumulativeEarnedPerMLiq, 256194846273571639740);
        assertEq(L.tokenY.subtreecumulativeEarnedPerMLiq, 982369673901053899051127131);

        // 3) Trigger fee update for remaining nodes by updating the range (1,3) LLLR, LLL
        //    For this last one, also update the rates to increment accumulated fees in L
        //    While previous step does not, meaning we also tested that nothing should have accumulated.
        //
        //    For un-accumulated nodes
        //    x_rate = 129987217567345826 + 997278349210980290827452342352346 = 997278349210980420814669909698172
        //    y_rate = 234346579834678237846892 + 7978726162930599238079167453467080976862 = 7978726162930599472425747288145318823754
        liqTree.feeRateSnapshotTokenX += 129987217567345826;
        liqTree.feeRateSnapshotTokenY += 234346579834678237846892;

        liqTree.addTLiq(LiqRange(1, 3), 32, 8687384723, 56758698);     // LLLR, LLL
        liqTree.removeTLiq(LiqRange(1, 3), 32, 8687384723, 56758698);  // LLLR, LLL

        // LLLR
        //   total_mLiq = 2462 + (45754683688356 + 932141354 + 98237498262 + 432) * 1 = 45853853330866
        //
        //   earn_x      = 997278349210980420814669909698172 * 4567e18 / 45853853330866 / 2**64 = 5384580105567269319768.51254007088771506177689554397322456673
        //   earn_x_sub  = 997278349210980420814669909698172 * 4567e18 / 45853853330866 / 2**64 = 5384580105567269319768.51254007088771506177689554397322456673
        //
        //   earn_y      = 7978726162930599472425747288145318823754 * 1235146e6 / 45853853330866 / 2**64 = 11650814730151920570.8396639745369843707702302526968216514839
        //   earn_y_sub  = 7978726162930599472425747288145318823754 * 1235146e6 / 45853853330866 / 2**64 = 11650814730151920570.8396639745369843707702302526968216514839
        assertEq(LLLR.tokenX.cumulativeEarnedPerMLiq, 5384580105567269319768);
        assertEq(LLLR.tokenX.subtreecumulativeEarnedPerMLiq, 5384580105567269319768);
        assertEq(LLLR.tokenY.cumulativeEarnedPerMLiq, 11650814730151920570);
        assertEq(LLLR.tokenY.subtreecumulativeEarnedPerMLiq, 11650814730151920570);

        // LLL
        //   total_mLiq = 91509367379174 + (932141354 + 98237498262 + 432) * 2 = 91707706659270
        //
        //   earn_x      = 997278349210980420814669909698172 * 134235e18 / 91707706659270 / 2**64 = 79132812622096209716370.5876318860028597239769562864471324430
        //   earn_x_sub  = 997278349210980420814669909698172 * 138802e18 / 91707706659270 / 2**64 = 81825102674952122032641.7871976834727823250825007372997718729
        //
        //   earn_y      = 7978726162930599472425747288145318823754 * 34534634e6 / 91707706659270 / 2**64 = 162878162791446141833.294568661856722588591983837787778442557
        //   earn_y_sub  = 7978726162930599472425747288145318823754 * 35769780e6 / 91707706659270 / 2**64 = 168703570156678491951.753228258608716065007834501481165880576
        assertEq(LLL.tokenX.cumulativeEarnedPerMLiq, 79132812622096209716370);
        assertEq(LLL.tokenX.subtreecumulativeEarnedPerMLiq, 81825102674952122032641);
        assertEq(LLL.tokenY.cumulativeEarnedPerMLiq, 162878162791446141833);
        assertEq(LLL.tokenY.subtreecumulativeEarnedPerMLiq, 168703570156678491951);

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
        assertEq(LL.tokenX.subtreecumulativeEarnedPerMLiq, 27270419858159154634352856276);
        assertEq(LL.tokenY.cumulativeEarnedPerMLiq, 1741210798541653397);
        assertEq(LL.tokenY.subtreecumulativeEarnedPerMLiq, 30035339489101406329);

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
        assertEq(L.tokenX.subtreecumulativeEarnedPerMLiq, 27250279648794482866527228371);
        assertEq(L.tokenY.cumulativeEarnedPerMLiq, 256194846273571647264);
        assertEq(L.tokenY.subtreecumulativeEarnedPerMLiq, 982369673901053927904727130);

        // 4) Confirm root fees are correct (although behavior leading to this state should have been previously tested at L and LL
        //   total_mLiq = 583038259954677
        //
        //   earn_x      = 997278349210980420814669909698172 * 0 / 583038259954677 / 2**64 = 0
        //   earn_x_sub  = 997278349210980420814669909698172 * 293880892517e18 / 583038259954677 / 2**64 = 27250279648632954930995939801.6330981070932019410874863041294
        //
        //   earn_y      = 7978726162930599472425747288145318823754 * 0 / 583038259954677 / 2**64 = 0
        //   earn_y_sub  = 7978726162930599472425747288145318823754 * 1324213967944654e6 / 583038259954677 / 2**64 = 982369673895230863062865876.398682260578858069936100777250356
        assertEq(root.tokenX.cumulativeEarnedPerMLiq, 0);
        assertEq(root.tokenX.subtreecumulativeEarnedPerMLiq, 27250279648632954930995939801);
        assertEq(root.tokenY.cumulativeEarnedPerMLiq, 0);
        assertEq(root.tokenY.subtreecumulativeEarnedPerMLiq, 982369673895230863062865875);       // 1 wei lost
    }

    function testLeftAndRightLegStoppingAtOrAbovePeak() public {
        //   Range: (0, 1)
        //
        //           LLL(0-1)
        //          /   \
        //         /     \
        //   LLLL(0) LLLR(1)

        // 4th (0, 1)
        LiqNode storage root = liqTree.nodes[liqTree.root];

        LiqNode storage L = liqTree.nodes[LKey.wrap((8 << 24) | 16)];
        LiqNode storage LL = liqTree.nodes[LKey.wrap((4 << 24) | 16)];
        LiqNode storage LLL = liqTree.nodes[LKey.wrap((2 << 24) | 16)];
        LiqNode storage LLLL = liqTree.nodes[LKey.wrap((1 << 24) | 16)];
        LiqNode storage LLLR = liqTree.nodes[LKey.wrap((1 << 24) | 17)];

        liqTree.addMLiq(LiqRange(0, 1), 8264);  // LLL
        liqTree.addMLiq(LiqRange(0, 0), 2582);  // LLLL
        liqTree.addMLiq(LiqRange(1, 1), 1111);  // LLLR

        liqTree.addTLiq(LiqRange(0, 1), 726, 346e18, 132e6);  // LLL
        liqTree.addTLiq(LiqRange(0, 0), 245, 100e18, 222e6);  // LLLL
        liqTree.addTLiq(LiqRange(1, 1), 342, 234e18, 313e6);  // LLLR

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
        assertEq(LLL.subtreeMLiq, 20221);  // 8264*2 + 2582*1 + 1111*1 = 20221
        assertEq(LLLL.subtreeMLiq, 2582);
        assertEq(LLLR.subtreeMLiq, 1111);

        // borrowed_x
        assertEq(root.tokenX.borrowed, 0);
        assertEq(L.tokenX.borrowed, 0);
        assertEq(LL.tokenX.borrowed, 0);
        assertEq(LLL.tokenX.borrowed, 346e18);
        assertEq(LLLL.tokenX.borrowed, 100e18);
        assertEq(LLLR.tokenX.borrowed, 234e18);

        // subtree_borrowed_x
        assertEq(root.tokenX.subtreeBorrowed, 680e18);
        assertEq(L.tokenX.subtreeBorrowed, 680e18);
        assertEq(LL.tokenX.subtreeBorrowed, 680e18);
        assertEq(LLL.tokenX.subtreeBorrowed, 680e18);  // 346e18 + 100e18 + 234e18 = 680e18
        assertEq(LLLL.tokenX.subtreeBorrowed, 100e18);
        assertEq(LLLR.tokenX.subtreeBorrowed, 234e18);

        // borrowed_y
        assertEq(root.tokenY.borrowed, 0);
        assertEq(L.tokenY.borrowed, 0);
        assertEq(LL.tokenY.borrowed, 0);
        assertEq(LLL.tokenY.borrowed, 132e6);
        assertEq(LLLL.tokenY.borrowed, 222e6);
        assertEq(LLLR.tokenY.borrowed, 313e6);

        // subtree_borrowed_y
        assertEq(root.tokenY.subtreeBorrowed, 667e6);
        assertEq(L.tokenY.subtreeBorrowed, 667e6);
        assertEq(LL.tokenY.subtreeBorrowed, 667e6);
        assertEq(LLL.tokenY.subtreeBorrowed, 667e6);  // 132e6 + 222e6 + 313e6 = 667e6
        assertEq(LLLL.tokenY.subtreeBorrowed, 222e6);
        assertEq(LLLR.tokenY.subtreeBorrowed, 313e6);

        liqTree.feeRateSnapshotTokenX += 997278349210980290827452342352346;
        liqTree.feeRateSnapshotTokenY += 7978726162930599238079167453467080976862;

        liqTree.addMLiq(LiqRange(0, 1), 1234567);
        liqTree.removeMLiq(LiqRange(0, 1), 1234567);

        // LLLR
        // (not updated)
        assertEq(LLLR.tokenX.cumulativeEarnedPerMLiq, 0);
        assertEq(LLLR.tokenX.subtreecumulativeEarnedPerMLiq, 0);
        assertEq(LLLR.tokenY.cumulativeEarnedPerMLiq, 0);
        assertEq(LLLR.tokenY.subtreecumulativeEarnedPerMLiq, 0);

        // LLLL
        // (not updated)
        assertEq(LLLL.tokenX.cumulativeEarnedPerMLiq, 0);
        assertEq(LLLL.tokenX.subtreecumulativeEarnedPerMLiq, 0);
        assertEq(LLLL.tokenY.cumulativeEarnedPerMLiq, 0);
        assertEq(LLLL.tokenY.subtreecumulativeEarnedPerMLiq, 0);

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
        assertEq(LLL.tokenX.subtreecumulativeEarnedPerMLiq, 1818037980058764692822308398143);
        assertEq(LLL.tokenY.cumulativeEarnedPerMLiq, 2823482754602022855424507);
        assertEq(LLL.tokenY.subtreecumulativeEarnedPerMLiq, 14267143919087494277031411);

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
        assertEq(LL.tokenX.subtreecumulativeEarnedPerMLiq, 1818037980058764692822308398143);
        assertEq(LL.tokenY.cumulativeEarnedPerMLiq, 0);
        assertEq(LL.tokenY.subtreecumulativeEarnedPerMLiq, 14267143919087494277031411);

        // L
        //   NOTE: subtree earn is not 'diluted' because liq contributing to total_mLiq along the path to the root is 0.
        assertEq(L.tokenX.cumulativeEarnedPerMLiq, 0);
        assertEq(L.tokenX.subtreecumulativeEarnedPerMLiq, 1818037980058764692822308398143);
        assertEq(L.tokenY.cumulativeEarnedPerMLiq, 0);
        assertEq(L.tokenY.subtreecumulativeEarnedPerMLiq, 14267143919087494277031411);

        // root
        //   NOTE: subtree earn is not 'diluted' because liq contributing to total_mLiq along the path to the root is 0.
        assertEq(root.tokenX.cumulativeEarnedPerMLiq, 0);
        assertEq(root.tokenX.subtreecumulativeEarnedPerMLiq, 1818037980058764692822308398143);
        assertEq(root.tokenY.cumulativeEarnedPerMLiq, 0);
        assertEq(root.tokenY.subtreecumulativeEarnedPerMLiq, 14267143919087494277031411);

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

        // borrowed_x
        assertEq(root.tokenX.borrowed, 0);
        assertEq(L.tokenX.borrowed, 0);
        assertEq(LL.tokenX.borrowed, 0);
        assertEq(LLL.tokenX.borrowed, 346e18);
        assertEq(LLLL.tokenX.borrowed, 100e18);
        assertEq(LLLR.tokenX.borrowed, 234e18);

        // subtree_borrowed_x
        assertEq(root.tokenX.subtreeBorrowed, 680e18);
        assertEq(L.tokenX.subtreeBorrowed, 680e18);
        assertEq(LL.tokenX.subtreeBorrowed, 680e18);
        assertEq(LLL.tokenX.subtreeBorrowed, 680e18);
        assertEq(LLLL.tokenX.subtreeBorrowed, 100e18);
        assertEq(LLLR.tokenX.subtreeBorrowed, 234e18);

        // borrowed_y
        assertEq(root.tokenY.borrowed, 0);
        assertEq(L.tokenY.borrowed, 0);
        assertEq(LL.tokenY.borrowed, 0);
        assertEq(LLL.tokenY.borrowed, 132e6);
        assertEq(LLLL.tokenY.borrowed, 222e6);
        assertEq(LLLR.tokenY.borrowed, 313e6);

        // subtree_borrowed_y
        assertEq(root.tokenY.subtreeBorrowed, 667e6);
        assertEq(L.tokenY.subtreeBorrowed, 667e6);
        assertEq(LL.tokenY.subtreeBorrowed, 667e6);
        assertEq(LLL.tokenY.subtreeBorrowed, 667e6);
        assertEq(LLLL.tokenY.subtreeBorrowed, 222e6);
        assertEq(LLLR.tokenY.subtreeBorrowed, 313e6);
    }

    // function testCompleteTree() public {
    //     LiqNode storage root = liqTree.nodes[liqTree.root];

    //     LiqNode storage L = liqTree.nodes[LKey.wrap((8 << 24) | 16)];
    //     LiqNode storage R = liqTree.nodes[LKey.wrap((8 << 24) | 24)];

    //     LiqNode storage LL = liqTree.nodes[LKey.wrap((4 << 24) | 16)];
    //     LiqNode storage LR = liqTree.nodes[LKey.wrap((4 << 24) | 20)];
    //     LiqNode storage RL = liqTree.nodes[LKey.wrap((4 << 24) | 24)];
    //     LiqNode storage RR = liqTree.nodes[LKey.wrap((4 << 24) | 28)];

    //     LiqNode storage LLL = liqTree.nodes[LKey.wrap((2 << 24) | 16)];
    //     LiqNode storage LLR = liqTree.nodes[LKey.wrap((2 << 24) | 18)];
    //     LiqNode storage LRL = liqTree.nodes[LKey.wrap((2 << 24) | 20)];
    //     LiqNode storage LRR = liqTree.nodes[LKey.wrap((2 << 24) | 22)];
    //     LiqNode storage RLL = liqTree.nodes[LKey.wrap((2 << 24) | 24)];
    //     LiqNode storage RLR = liqTree.nodes[LKey.wrap((2 << 24) | 26)];
    //     LiqNode storage RRL = liqTree.nodes[LKey.wrap((2 << 24) | 28)];
    //     LiqNode storage RRR = liqTree.nodes[LKey.wrap((2 << 24) | 30)];

    //     LiqNode storage LLLL = liqTree.nodes[LKey.wrap((1 << 24) | 16)];
    //     LiqNode storage LLLR = liqTree.nodes[LKey.wrap((1 << 24) | 17)];
    //     LiqNode storage LLRL = liqTree.nodes[LKey.wrap((1 << 24) | 18)];
    //     LiqNode storage LLRR = liqTree.nodes[LKey.wrap((1 << 24) | 19)];
    //     LiqNode storage LRLL = liqTree.nodes[LKey.wrap((1 << 24) | 20)];
    //     LiqNode storage LRLR = liqTree.nodes[LKey.wrap((1 << 24) | 21)];
    //     LiqNode storage LRRL = liqTree.nodes[LKey.wrap((1 << 24) | 22)];
    //     LiqNode storage LRRR = liqTree.nodes[LKey.wrap((1 << 24) | 23)];
    //     LiqNode storage RLLL = liqTree.nodes[LKey.wrap((1 << 24) | 24)];
    //     LiqNode storage RLLR = liqTree.nodes[LKey.wrap((1 << 24) | 25)];
    //     LiqNode storage RLRL = liqTree.nodes[LKey.wrap((1 << 24) | 26)];
    //     LiqNode storage RLRR = liqTree.nodes[LKey.wrap((1 << 24) | 27)];
    //     LiqNode storage RRLL = liqTree.nodes[LKey.wrap((1 << 24) | 28)];
    //     LiqNode storage RRLR = liqTree.nodes[LKey.wrap((1 << 24) | 29)];
    //     LiqNode storage RRRL = liqTree.nodes[LKey.wrap((1 << 24) | 30)];
    //     LiqNode storage RRRR = liqTree.nodes[LKey.wrap((1 << 24) | 31)];

    //     // Start with an accumulated rate for each token before modifying tree state -----------------------------------------
    //     liqTree.feeRateSnapshotTokenX += 34541239648278065;
    //     liqTree.feeRateSnapshotTokenY += 713278814667749784;

    //     // Add mLiq + tLiq to all nodes ------------------------------------------------------------------------------------
    //     liqTree.addInfRangeMLiq(837205720);  // root
    //     liqTree.addInfRangeTLiq(137205720, 92749012637e18, 936252847e6);

    //     liqTree.addMLiq(LiqRange(0, 7), 628294582176);   // L
    //     liqTree.addTLiq(LiqRange(0, 7), 28294582176, 41423892459e18, 178263465237e6);
    //     liqTree.addMLiq(LiqRange(8, 15), 9846145183924);  // R
    //     liqTree.addTLiq(LiqRange(8, 15), 846145183924, 2983456295e18, 297562903e6);

    //     liqTree.addMLiq(LiqRange(0, 3), 1325348245562823);  // LL
    //     liqTree.addTLiq(LiqRange(0, 3), 325348245562823, 28678729387565786e18, 1287576451867e6);
    //     liqTree.addMLiq(LiqRange(4, 7), 3456457562345467878);  // LR
    //     liqTree.addTLiq(LiqRange(4, 7), 456457562345467878, 872538467082357693e18, 9879867896e6);
    //     liqTree.addMLiq(LiqRange(8, 11), 76483482619394619652);  // RL
    //     liqTree.addTLiq(LiqRange(8, 11), 6483482619394619652, 6785678523564273e18, 978623685429837e6);
    //     liqTree.addMLiq(LiqRange(12, 15), 8623526734267390879);  // RR
    //     liqTree.addTLiq(LiqRange(12, 15), 86235267342673908, 498723597863764293e18, 7856675879087e6);

    //     liqTree.addMLiq(LiqRange(0, 1), 98987279836478238567234);  // LLL
    //     liqTree.addTLiq(LiqRange(0, 1), 8987279836478238567234, 45623798462985629837462e18, 8725348762398423567587e6);
    //     liqTree.addMLiq(LiqRange(2, 3), 7986785755674657823);  // LLR
    //     liqTree.addTLiq(LiqRange(2, 3), 986785755674657823, 298364785638476530459368e18, 3465873645937459364e6);
    //     liqTree.addMLiq(LiqRange(4, 5), 232467458683765);  // LRL
    //     liqTree.addTLiq(LiqRange(4, 5), 132467458683765, 27364762534827634902374982e18, 56736409827398427340e6);
    //     liqTree.addMLiq(LiqRange(6, 7), 777839863652735);  // LRR
    //     liqTree.addTLiq(LiqRange(6, 7), 277839863652735, 7653642903472903784290347e18, 7834626734902734902368e6);
    //     liqTree.addMLiq(LiqRange(8, 9), 3131567868944634354);  // RLL
    //     liqTree.addTLiq(LiqRange(8, 9), 2131567868944634354, 23452367423084927398437e18, 9834787362478562378e6);
    //     liqTree.addMLiq(LiqRange(10, 11), 78724563469237853906739487);  // RLR
    //     liqTree.addTLiq(LiqRange(10, 11), 8724563469237853906739487, 2765723642783492e18, 98576798364725367423e6);
    //     liqTree.addMLiq(LiqRange(12, 13), 7556478634723908752323756);  // RRL
    //     liqTree.addTLiq(LiqRange(12, 13), 5556478634723908752323756, 28635482364798629384e18, 83764587364859348795634987e6);
    //     liqTree.addMLiq(LiqRange(14, 15), 54534789284573456239862722);  // RRR
    //     liqTree.addTLiq(LiqRange(14, 15), 34534789284573456239862722, 27364527863428346239867e18, 9834657827356482367482369e6);

    //     liqTree.addMLiq(LiqRange(0, 0), 92736478234923748923);  // LLLL
    //     liqTree.addTLiq(LiqRange(0, 0), 9736478234923748923, 5734523421634563e18, 72634678523487263e6);
    //     liqTree.addMLiq(LiqRange(1, 1), 76238216349082735923684);  // LLLR
    //     liqTree.addTLiq(LiqRange(1, 1), 7623821634908273592368, 346456345234235235e18, 26734872634892639847623789e6);
    //     liqTree.addMLiq(LiqRange(2, 2), 2345345345353);  // LLRL
    //     liqTree.addTLiq(LiqRange(2, 2), 234534534535, 82735476982534798263498e18, 763467253674523798462397e6);
    //     liqTree.addMLiq(LiqRange(3, 3), 12341234213421354513456);  // LLRR
    //     liqTree.addTLiq(LiqRange(3, 3), 1234123421342135451345, 2367452364752903485729403875e18, 987349053045739487e6);
    //     liqTree.addMLiq(LiqRange(4, 4), 456467567878689);  // LRLL
    //     liqTree.addTLiq(LiqRange(4, 4), 45646756787868, 236452378462398476238746e18, 984764582736478236478e6);
    //     liqTree.addMLiq(LiqRange(5, 5), 89805856756746);  // LRLR
    //     liqTree.addTLiq(LiqRange(5, 5), 8980585675674, 8374278364628364e18, 8763867548273647826e6);
    //     liqTree.addMLiq(LiqRange(6, 6), 34545756857245324534634);  // LRRL
    //     liqTree.addTLiq(LiqRange(6, 6), 3454575685724532453463, 3456457456345634e18, 8726347825634876237846e6);
    //     liqTree.addMLiq(LiqRange(7, 7), 2334646757867856856346);  // LRRR
    //     liqTree.addTLiq(LiqRange(7, 7), 233464675786785685634, 236542867349237498e18, 798647852364627983e6);
    //     liqTree.addMLiq(LiqRange(8, 8), 24674758679564563445747);  // RLLL
    //     liqTree.addTLiq(LiqRange(8, 8), 2467475867956456344574, 51427634238746298457982345e18, 74986238476283746e6);
    //     liqTree.addMLiq(LiqRange(9, 9), 547867967467456457536856873);  // RLLR
    //     liqTree.addTLiq(LiqRange(9, 9), 54786796746745645753685687, 634529836428376523e18, 868746576834678534e6);
    //     liqTree.addMLiq(LiqRange(10, 10), 34564375645457568568456);  // RLRL
    //     liqTree.addTLiq(LiqRange(10, 10), 3456437564545756856845, 1212312312423452454e18, 3423423648236487e6);
    //     liqTree.addMLiq(LiqRange(11, 11), 32546475786796896785674564);  // RLRR
    //     liqTree.addTLiq(LiqRange(11, 11), 3254647578679689678567456, 287346234623487923642786e18, 827364826734823748963e6);
    //     liqTree.addMLiq(LiqRange(12, 12), 5856745645634534563453);  // RRLL
    //     liqTree.addTLiq(LiqRange(12, 12), 585674564563453456345, 2837427354234786237896e18, 73649082374029384628376e6);
    //     liqTree.addMLiq(LiqRange(13, 13), 4574785673643563456);  // RRLR
    //     liqTree.addTLiq(LiqRange(13, 13), 457478567364356345, 82635472634823674e18, 2387642836423689768e6);
    //     liqTree.addMLiq(LiqRange(14, 14), 24534645747456745);  // RRRL
    //     liqTree.addTLiq(LiqRange(14, 14), 2453464574745674, 23645278462837429736e18, 3542364237842638e6);
    //     liqTree.addMLiq(LiqRange(15, 15), 6345346534645746);  // RRRR
    //     liqTree.addTLiq(LiqRange(15, 15), 6345346534645743, 37465276342938487e18, 23984623847623867e6);

    //     // Interact with the tree. Using all methods. Over all possible ranges
    //     // Ranges that start with 0 -------------------------------------------------------------------------------------

    //     // LiqRange(0, 0)
    //     liqTree.feeRateSnapshotTokenX += 283564826358762378954279863;
    //     liqTree.feeRateSnapshotTokenY += 2753476253583645873647859364;
    //     liqTree.addMLiq(LiqRange(0, 0), 234534567456);
    //     liqTree.feeRateSnapshotTokenX += 245457456745342;
    //     liqTree.feeRateSnapshotTokenY += 2345356747467456743;
    //     liqTree.removeMLiq(LiqRange(0, 0), 2453464574674);
    //     liqTree.feeRateSnapshotTokenX += 456456756586578;
    //     liqTree.feeRateSnapshotTokenY += 5634564564356435;
    //     liqTree.addTLiq(LiqRange(0, 0), 3564575678567, 35664576857e18, 3565685685672375e6);
    //     liqTree.feeRateSnapshotTokenX += 34575687568567345;
    //     liqTree.feeRateSnapshotTokenY += 345654675678567345;
    //     liqTree.removeTLiq(LiqRange(0, 0), 3564575678567,3564575678567e18, 3565467683463e6);

    //     // LiqRange(0, 1)
    //     liqTree.feeRateSnapshotTokenX += 78567456345;
    //     liqTree.feeRateSnapshotTokenY += 234535756856785673;
    //     liqTree.addMLiq(LiqRange(0, 1), 253464575685786);
    //     liqTree.feeRateSnapshotTokenX += 67968435;
    //     liqTree.feeRateSnapshotTokenY += 2454575685679;
    //     liqTree.removeMLiq(LiqRange(0, 1), 234535645756867);
    //     liqTree.feeRateSnapshotTokenX += 2345356568;
    //     liqTree.feeRateSnapshotTokenY += 678678456;
    //     liqTree.addTLiq(LiqRange(0, 1), 23476, 24543634e18, 34535674564e5);
    //     liqTree.feeRateSnapshotTokenX += 2345357645;
    //     liqTree.feeRateSnapshotTokenY += 243253453;
    //     liqTree.removeTLiq(LiqRange(0, 1), 13476, 45646745674e18, 23453457457e6);

    //     // LiqRange(0, 2)
    //     liqTree.feeRateSnapshotTokenX += 6735468234823;
    //     liqTree.feeRateSnapshotTokenY += 56456456;
    //     liqTree.addMLiq(LiqRange(0, 2), 23453456457);
    //     liqTree.feeRateSnapshotTokenX += 245346457457456;
    //     liqTree.feeRateSnapshotTokenY += 2345346456474;
    //     liqTree.removeMLiq(LiqRange(0, 2), 2345346);
    //     liqTree.feeRateSnapshotTokenX += 2345457;
    //     liqTree.feeRateSnapshotTokenY += 457645745745643;
    //     liqTree.addTLiq(LiqRange(0, 2), 645674564, 34545745745e18, 6745357452734e6);
    //     liqTree.feeRateSnapshotTokenX += 22345457456745;
    //     liqTree.feeRateSnapshotTokenY += 345645754723;
    //     liqTree.removeTLiq(LiqRange(0, 2), 87623487623, 7623467823e18, 524315237816e6);

    //     // LiqRange(0, 3)
    //     liqTree.feeRateSnapshotTokenX += 53452634236874;
    //     liqTree.feeRateSnapshotTokenY += 4564574574546345;
    //     liqTree.addMLiq(LiqRange(0, 3), 234534634567);
    //     liqTree.feeRateSnapshotTokenX += 45645753;
    //     liqTree.feeRateSnapshotTokenY += 245345346;
    //     liqTree.removeMLiq(LiqRange(0, 3), 678567856875);
    //     liqTree.feeRateSnapshotTokenX += 45645634;
    //     liqTree.feeRateSnapshotTokenY += 45647456785;
    //     liqTree.addTLiq(LiqRange(0, 3), 356456457, 23464574e18, 234534567e6);
    //     liqTree.feeRateSnapshotTokenX += 35645374;
    //     liqTree.feeRateSnapshotTokenY += 2356456454645;
    //     liqTree.removeTLiq(LiqRange(0, 3), 45645747568, 8672538476e18, 2456456435e6);

    //     // LiqRange(0, 4)
    //     liqTree.feeRateSnapshotTokenX += 2342454;
    //     liqTree.feeRateSnapshotTokenY += 45645745;
    //     liqTree.addMLiq(LiqRange(0, 4), 32452345);
    //     liqTree.feeRateSnapshotTokenX += 934765;
    //     liqTree.feeRateSnapshotTokenY += 24534534;
    //     liqTree.removeMLiq(LiqRange(0, 4), 456456);
    //     liqTree.feeRateSnapshotTokenX += 245;
    //     liqTree.feeRateSnapshotTokenY += 2345;
    //     liqTree.addTLiq(LiqRange(0, 4), 476574, 346356355e18, 45357467456e6);
    //     liqTree.feeRateSnapshotTokenX += 245234;
    //     liqTree.feeRateSnapshotTokenY += 24634642;
    //     liqTree.removeTLiq(LiqRange(0, 4), 2245346456, 87637465238746e18, 834527836e6);

    //     // LiqRange(0, 5)
    //     liqTree.feeRateSnapshotTokenX += 76354826342;
    //     liqTree.feeRateSnapshotTokenY += 45645;
    //     liqTree.addMLiq(LiqRange(0, 5), 345345);
    //     liqTree.feeRateSnapshotTokenX += 674567;
    //     liqTree.feeRateSnapshotTokenY += 456346;
    //     liqTree.removeMLiq(LiqRange(0, 5), 34646);
    //     liqTree.feeRateSnapshotTokenX += 34634;
    //     liqTree.feeRateSnapshotTokenY += 234534534;
    //     liqTree.addTLiq(LiqRange(0, 5), 656454, 3574573e18, 245435745e6);
    //     liqTree.feeRateSnapshotTokenX += 345453;
    //     liqTree.feeRateSnapshotTokenY += 453634;
    //     liqTree.removeTLiq(LiqRange(0, 5), 45346346, 324564564e18, 3434645e6);

    //     // LiqRange(0, 6)
    //     liqTree.feeRateSnapshotTokenX += 678456456;
    //     liqTree.feeRateSnapshotTokenY += 24352356457;
    //     liqTree.addMLiq(LiqRange(0, 6), 234534534);
    //     liqTree.feeRateSnapshotTokenX += 45756756;
    //     liqTree.feeRateSnapshotTokenY += 2345345;
    //     liqTree.removeMLiq(LiqRange(0, 6), 456);
    //     liqTree.feeRateSnapshotTokenX += 24;
    //     liqTree.feeRateSnapshotTokenY += 245346;
    //     liqTree.addTLiq(LiqRange(0, 6), 4545, 456457e18, 3456467e6);
    //     liqTree.feeRateSnapshotTokenX += 24534;
    //     liqTree.feeRateSnapshotTokenY += 4745645;
    //     liqTree.removeTLiq(LiqRange(0, 6), 34534534, 47253765e18, 7856856e6);

    //     // LiqRange(0, 7)
    //     liqTree.feeRateSnapshotTokenX += 76238467283764;
    //     liqTree.feeRateSnapshotTokenY += 23453563456734567;
    //     liqTree.addMLiq(LiqRange(0, 7), 345236634634);
    //     liqTree.feeRateSnapshotTokenX += 3246457467;
    //     liqTree.feeRateSnapshotTokenY += 3453453456;
    //     liqTree.removeMLiq(LiqRange(0, 7), 342345);
    //     liqTree.feeRateSnapshotTokenX += 45746756;
    //     liqTree.feeRateSnapshotTokenY += 5685685678;
    //     liqTree.addTLiq(LiqRange(0, 7), 6796786, 46745674e18, 7567567e6);
    //     liqTree.feeRateSnapshotTokenX += 5345346;
    //     liqTree.feeRateSnapshotTokenY += 575685656;
    //     liqTree.removeTLiq(LiqRange(0, 7), 345345345, 456457457e18, 4564564564e6);

    //     // LiqRange(0, 8)
    //     liqTree.feeRateSnapshotTokenX += 2342453;
    //     liqTree.feeRateSnapshotTokenY += 5675675;
    //     liqTree.addMLiq(LiqRange(0, 8), 45345345);
    //     liqTree.feeRateSnapshotTokenX += 56756756;
    //     liqTree.feeRateSnapshotTokenY += 34534534;
    //     liqTree.removeMLiq(LiqRange(0, 8), 5675675);
    //     liqTree.feeRateSnapshotTokenX += 345345;
    //     liqTree.feeRateSnapshotTokenY += 34534534;
    //     liqTree.addTLiq(LiqRange(0, 8), 45646756, 2343456e18, 34354534e6);
    //     liqTree.feeRateSnapshotTokenX += 3453;
    //     liqTree.feeRateSnapshotTokenY += 675675;
    //     liqTree.removeTLiq(LiqRange(0, 8), 534534, 5645645e18, 42342343e6);

    //     // LiqRange(0, 9)
    //     liqTree.feeRateSnapshotTokenX += 345345;
    //     liqTree.feeRateSnapshotTokenY += 445656;
    //     liqTree.addMLiq(LiqRange(0, 9), 345345);
    //     liqTree.feeRateSnapshotTokenX += 2345235;
    //     liqTree.feeRateSnapshotTokenY += 34534534;
    //     liqTree.removeMLiq(LiqRange(0, 9), 556456);
    //     liqTree.feeRateSnapshotTokenX += 56756743;
    //     liqTree.feeRateSnapshotTokenY += 345345345;
    //     liqTree.addTLiq(LiqRange(0, 9), 56756756, 345345345345e18, 45645645e6);
    //     liqTree.feeRateSnapshotTokenX += 4564564;
    //     liqTree.feeRateSnapshotTokenY += 54564;
    //     liqTree.removeTLiq(LiqRange(0, 9), 345345, 3634534e18, 5675675e6);

    //     // LiqRange(0, 10)
    //     liqTree.feeRateSnapshotTokenX += 234234;
    //     liqTree.feeRateSnapshotTokenY += 2454353;
    //     liqTree.addMLiq(LiqRange(0, 10), 345345);
    //     liqTree.feeRateSnapshotTokenX += 34234;
    //     liqTree.feeRateSnapshotTokenY += 34234;
    //     liqTree.removeMLiq(LiqRange(0, 10), 564564);
    //     liqTree.feeRateSnapshotTokenX += 34534;
    //     liqTree.feeRateSnapshotTokenY += 3453;
    //     liqTree.addTLiq(LiqRange(0, 10), 4745674, 345345e18, 3453453e6);
    //     liqTree.feeRateSnapshotTokenX += 34534;
    //     liqTree.feeRateSnapshotTokenY += 245234;
    //     liqTree.removeTLiq(LiqRange(0, 10), 345345, 4564564e18, 78675e6);

    //     // LiqRange(0, 11)
    //     liqTree.feeRateSnapshotTokenX += 345634;
    //     liqTree.feeRateSnapshotTokenY += 56756;
    //     liqTree.addMLiq(LiqRange(0, 11), 345345345);
    //     liqTree.feeRateSnapshotTokenX += 567457346;
    //     liqTree.feeRateSnapshotTokenY += 454;
    //     liqTree.removeMLiq(LiqRange(0, 11), 56456);
    //     liqTree.feeRateSnapshotTokenX += 34543564674;
    //     liqTree.feeRateSnapshotTokenY += 3453453;
    //     liqTree.addTLiq(LiqRange(0, 11), 234236, 456456e28, 75675675e6);
    //     liqTree.feeRateSnapshotTokenX += 345345;
    //     liqTree.feeRateSnapshotTokenY += 45456457;
    //     liqTree.removeTLiq(LiqRange(0, 11), 2456345, 2342352e18, 456456e6);

    //     // LiqRange(0, 12)
    //     liqTree.feeRateSnapshotTokenX += 5464564;
    //     liqTree.feeRateSnapshotTokenY += 234234;
    //     liqTree.addMLiq(LiqRange(0, 12), 26345345);
    //     liqTree.feeRateSnapshotTokenX += 45674564;
    //     liqTree.feeRateSnapshotTokenY += 234234;
    //     liqTree.removeMLiq(LiqRange(0, 12), 534345534534);
    //     liqTree.feeRateSnapshotTokenX += 223232323;
    //     liqTree.feeRateSnapshotTokenY += 454646456;
    //     liqTree.addTLiq(LiqRange(0, 12), 214123213, 3453454e18, 456456457e6);
    //     liqTree.feeRateSnapshotTokenX += 234245356;
    //     liqTree.feeRateSnapshotTokenY += 23423423;
    //     liqTree.removeTLiq(LiqRange(0, 12), 7553453, 234534534e18, 5685675674e6);

    //     // LiqRange(0, 13)
    //     liqTree.feeRateSnapshotTokenX += 23445;
    //     liqTree.feeRateSnapshotTokenY += 34543534;
    //     liqTree.addMLiq(LiqRange(0, 13), 76574564);
    //     liqTree.feeRateSnapshotTokenX += 345346;
    //     liqTree.feeRateSnapshotTokenY += 74678456;
    //     liqTree.removeMLiq(LiqRange(0, 13), 45252);
    //     liqTree.feeRateSnapshotTokenX += 234234;
    //     liqTree.feeRateSnapshotTokenY += 45674574;
    //     liqTree.addTLiq(LiqRange(0, 13), 354635345, 46345634e18, 3453453e6);
    //     liqTree.feeRateSnapshotTokenX += 235454534;
    //     liqTree.feeRateSnapshotTokenY += 34643564357;
    //     liqTree.removeTLiq(LiqRange(0, 13), 23453454, 23453454e18, 2342352e6);

    //     // LiqRange(0, 14)
    //     liqTree.feeRateSnapshotTokenX += 453463563;
    //     liqTree.feeRateSnapshotTokenY += 34564356;
    //     liqTree.addMLiq(LiqRange(0, 14), 2342454);
    //     liqTree.feeRateSnapshotTokenX += 456457457;
    //     liqTree.feeRateSnapshotTokenY += 3453452345;
    //     liqTree.removeMLiq(LiqRange(0, 14), 234234234);
    //     liqTree.feeRateSnapshotTokenX += 6345634534;
    //     liqTree.feeRateSnapshotTokenY += 23423423;
    //     liqTree.addTLiq(LiqRange(0, 14), 1345645646, 232342e18, 345345345e6);
    //     liqTree.feeRateSnapshotTokenX += 34523452352;
    //     liqTree.feeRateSnapshotTokenY += 7457457456;
    //     liqTree.removeTLiq(LiqRange(0, 14), 1345645646, 25634624e18, 23434635e6);

    //     // LiqRange(0, 15) aka root
    //     liqTree.feeRateSnapshotTokenX += 3453645745674;
    //     liqTree.feeRateSnapshotTokenY += 4574563456456;
    //     liqTree.addInfRangeMLiq(34534534534);
    //     liqTree.feeRateSnapshotTokenX += 2342342342;
    //     liqTree.feeRateSnapshotTokenY += 3533463457467;
    //     liqTree.removeInfRangeMLiq(678678678);
    //     liqTree.feeRateSnapshotTokenX += 56456456456;
    //     liqTree.feeRateSnapshotTokenY += 34532464567568;
    //     liqTree.addInfRangeTLiq(3463456456456, 34575684564e18, 345345746745e6);
    //     liqTree.feeRateSnapshotTokenX += 3645746746787;
    //     liqTree.feeRateSnapshotTokenY += 2342342;
    //     liqTree.removeInfRangeTLiq(3574534534, 4567452342e18, 234535734563e6);

    //     // region Ranges that start with 1 -------------------------------------------------------------------------------------
    //     // LiqRange(1, 1)
    //     liqTree.feeRateSnapshotTokenX += 75345234;
    //     liqTree.feeRateSnapshotTokenY += 674563456;
    //     liqTree.addMLiq(LiqRange(1, 1), 34534);
    //     liqTree.feeRateSnapshotTokenX += 234234;
    //     liqTree.feeRateSnapshotTokenY += 53453;
    //     liqTree.removeMLiq(LiqRange(1, 1), 234345345);
    //     liqTree.feeRateSnapshotTokenX += 453453;
    //     liqTree.feeRateSnapshotTokenY += 453453453;
    //     liqTree.addTLiq(LiqRange(1, 1), 234234, 34534e18, 4534e6);
    //     liqTree.feeRateSnapshotTokenX += 9834;
    //     liqTree.feeRateSnapshotTokenY += 97234;
    //     liqTree.removeTLiq(LiqRange(1, 1), 34534, 234e18, 23e8);

    //     // LiqRange(1, 2)
    //     liqTree.feeRateSnapshotTokenX += 75345234;
    //     liqTree.feeRateSnapshotTokenY += 674563456;
    //     liqTree.addMLiq(LiqRange(1, 2), 34534);
    //     liqTree.feeRateSnapshotTokenX += 234234;
    //     liqTree.feeRateSnapshotTokenY += 53453;
    //     liqTree.removeMLiq(LiqRange(1, 2), 234345345);
    //     liqTree.feeRateSnapshotTokenX += 453453;
    //     liqTree.feeRateSnapshotTokenY += 453453453;
    //     liqTree.addTLiq(LiqRange(1, 2), 234234, 34534e18, 4534e6);
    //     liqTree.feeRateSnapshotTokenX += 9834;
    //     liqTree.feeRateSnapshotTokenY += 97234;
    //     liqTree.removeTLiq(LiqRange(1, 2), 34534, 234e18, 23e8);


    //     // LiqRange(1, 3)
    //     liqTree.feeRateSnapshotTokenX += 75345234;
    //     liqTree.feeRateSnapshotTokenY += 674563456;
    //     liqTree.addMLiq(LiqRange(1, 3), 34534);
    //     liqTree.feeRateSnapshotTokenX += 234234;
    //     liqTree.feeRateSnapshotTokenY += 53453;
    //     liqTree.removeMLiq(LiqRange(1, 3), 234345345);
    //     liqTree.feeRateSnapshotTokenX += 453453;
    //     liqTree.feeRateSnapshotTokenY += 453453453;
    //     liqTree.addTLiq(LiqRange(1, 3), 234234, 34534e18, 4534e6);
    //     liqTree.feeRateSnapshotTokenX += 9834;
    //     liqTree.feeRateSnapshotTokenY += 97234;
    //     liqTree.removeTLiq(LiqRange(1, 3), 34534, 234e18, 23e8);


    //     // LiqRange(1, 4)
    //     liqTree.feeRateSnapshotTokenX += 75345234;
    //     liqTree.feeRateSnapshotTokenY += 674563456;
    //     liqTree.addMLiq(LiqRange(1, 4), 34534);
    //     liqTree.feeRateSnapshotTokenX += 234234;
    //     liqTree.feeRateSnapshotTokenY += 5345);
    //     liqTree.removeMLiq(LiqRange(1, 4), 234345345);
    //     liqTree.feeRateSnapshotTokenX += 453453;
    //     liqTree.feeRateSnapshotTokenY += 453453453;
    //     liqTree.addTLiq(LiqRange(1, 4), 234234, 34534e18, 4534e6);
    //     liqTree.feeRateSnapshotTokenX += 9834;
    //     liqTree.feeRateSnapshotTokenY += 97234;
    //     liqTree.removeTLiq(LiqRange(1, 4), 34534, 234e18, 23e8);


    //     // LiqRange(1, 5)
    //     liqTree.feeRateSnapshotTokenX += 75345234;
    //     liqTree.feeRateSnapshotTokenY += 674563456;
    //     liqTree.addMLiq(LiqRange(1, 5), 34534);
    //     liqTree.feeRateSnapshotTokenX += 234234;
    //     liqTree.feeRateSnapshotTokenY += 53453;
    //     liqTree.removeMLiq(LiqRange(1, 5), 234345345);
    //     liqTree.feeRateSnapshotTokenX += 453453;
    //     liqTree.feeRateSnapshotTokenY += 453453453;
    //     liqTree.addTLiq(LiqRange(1, 5), 234234, 34534e18, 4534e6);
    //     liqTree.feeRateSnapshotTokenX += 9834;
    //     liqTree.feeRateSnapshotTokenY += 97234;
    //     liqTree.removeTLiq(LiqRange(1, 5), 34534, 234e18, 23e8);


    //     // LiqRange(1, 6)
    //     liqTree.feeRateSnapshotTokenX += 75345234;
    //     liqTree.feeRateSnapshotTokenY += 674563456;
    //     liqTree.addMLiq(LiqRange(1, 6), 34534);
    //     liqTree.feeRateSnapshotTokenX += 234234;
    //     liqTree.feeRateSnapshotTokenY += 53453;
    //     liqTree.removeMLiq(LiqRange(1, 6), 234345345);
    //     liqTree.feeRateSnapshotTokenX += 453453;
    //     liqTree.feeRateSnapshotTokenY += 453453453;
    //     liqTree.addTLiq(LiqRange(1, 6), 234234, 34534e18, 4534e6);
    //     liqTree.feeRateSnapshotTokenX += 9834;
    //     liqTree.feeRateSnapshotTokenY += 97234;
    //     liqTree.removeTLiq(LiqRange(1, 6), 34534, 234e18, 23e8);


    //     // LiqRange(1, 7)
    //     liqTree.feeRateSnapshotTokenX += 45745645;
    //     liqTree.feeRateSnapshotTokenY += 46;
    //     liqTree.addMLiq(LiqRange(1, 7), 457467);
    //     liqTree.feeRateSnapshotTokenX += 3453;
    //     liqTree.feeRateSnapshotTokenY += 345346;
    //     liqTree.removeMLiq(LiqRange(1, 7), 73345);
    //     liqTree.feeRateSnapshotTokenX += 345345;
    //     liqTree.feeRateSnapshotTokenY += 56756;
    //     liqTree.addTLiq(LiqRange(1, 7), 6357457457, 456468745, 3453e6);
    //     liqTree.feeRateSnapshotTokenX += 68567;
    //     liqTree.feeRateSnapshotTokenY += 3467;
    //     liqTree.removeTLiq(LiqRange(1, 7), 3634534, 3453463e18, 34534e6);

    //     // LiqRange(1, 8)
    //     liqTree.feeRateSnapshotTokenX += 56457;
    //     liqTree.feeRateSnapshotTokenY += 456456;
    //     liqTree.addMLiq(LiqRange(1, 8), 3465346);
    //     liqTree.feeRateSnapshotTokenX += 343;
    //     liqTree.feeRateSnapshotTokenY += 3453746;
    //     liqTree.removeMLiq(LiqRange(1, 8), 756756);
    //     liqTree.feeRateSnapshotTokenX += 57457;
    //     liqTree.feeRateSnapshotTokenY += 45346346;
    //     liqTree.addTLiq(LiqRange(1, 8), 23424, 223423e18, 34634534e6);
    //     liqTree.feeRateSnapshotTokenX += 23423;
    //     liqTree.feeRateSnapshotTokenY += 34634;
    //     liqTree.removeTLiq(LiqRange(1, 8), 345345, 23423e18, 3434e6);

    //     // LiqRange(1, 9)
    //     liqTree.feeRateSnapshotTokenX += 3453;
    //     liqTree.feeRateSnapshotTokenY += 3573;
    //     liqTree.addMLiq(LiqRange(1, 9), 345345);
    //     liqTree.feeRateSnapshotTokenX += 45745;
    //     liqTree.feeRateSnapshotTokenY += 4523;
    //     liqTree.removeMLiq(LiqRange(1, 9), 34534);
    //     liqTree.feeRateSnapshotTokenX += 34534;
    //     liqTree.feeRateSnapshotTokenY += 6745674;
    //     liqTree.addTLiq(LiqRange(1, 9), 573534, 2342354e18, 3453453e6);
    //     liqTree.feeRateSnapshotTokenX += 234234;
    //     liqTree.feeRateSnapshotTokenY += 64563453;
    //     liqTree.removeTLiq(LiqRange(1, 9), 34535754, 3453467435e18, 4564e6);

    //     // LiqRange(1, 10)
    //     liqTree.feeRateSnapshotTokenX += 457457;
    //     liqTree.feeRateSnapshotTokenY += 4534534;
    //     liqTree.addMLiq(LiqRange(1, 10), 34534634);
    //     liqTree.feeRateSnapshotTokenX += 34534;
    //     liqTree.feeRateSnapshotTokenY += 47574;
    //     liqTree.removeMLiq(LiqRange(1, 10), 4574574);
    //     liqTree.feeRateSnapshotTokenX += 6745674;
    //     liqTree.feeRateSnapshotTokenY += 34525;
    //     liqTree.addTLiq(LiqRange(1, 10), 3453453, 5645634523e18, 46346534e6);
    //     liqTree.feeRateSnapshotTokenX += 345357;
    //     liqTree.feeRateSnapshotTokenY += 756745;
    //     liqTree.removeTLiq(LiqRange(1, 10), 345346475, 745645e18, 78564564e6);

    //     // LiqRange(1, 11)
    //     liqTree.feeRateSnapshotTokenX += 457457;
    //     liqTree.feeRateSnapshotTokenY += 4434524;
    //     liqTree.addMLiq(LiqRange(1, 11), 3453453467);
    //     liqTree.feeRateSnapshotTokenX += 35756785685;
    //     liqTree.feeRateSnapshotTokenY += 5664564;
    //     liqTree.removeMLiq(LiqRange(1, 11), 345346346);
    //     liqTree.feeRateSnapshotTokenX += 234235;
    //     liqTree.feeRateSnapshotTokenY += 6347356;
    //     liqTree.addTLiq(LiqRange(1, 11), 57463, 34634563e18, 453463e6);
    //     liqTree.feeRateSnapshotTokenX += 34524;
    //     liqTree.feeRateSnapshotTokenY += 2342345;
    //     liqTree.removeTLiq(LiqRange(1, 11), 634634, 453576353e18, 5734534e6);

    //     // LiqRange(1, 12)
    //     liqTree.feeRateSnapshotTokenX += 3423423;
    //     liqTree.feeRateSnapshotTokenY += 3453456;
    //     liqTree.addMLiq(LiqRange(1, 12), 4564574);
    //     liqTree.feeRateSnapshotTokenX += 345245;
    //     liqTree.feeRateSnapshotTokenY += 234235;
    //     liqTree.removeMLiq(LiqRange(1, 12), 4574564);
    //     liqTree.feeRateSnapshotTokenX += 2342342;
    //     liqTree.feeRateSnapshotTokenY += 6345634;
    //     liqTree.addTLiq(LiqRange(1, 12), 34634567, 23424e18, 3453464e6);
    //     liqTree.feeRateSnapshotTokenX += 345345;
    //     liqTree.feeRateSnapshotTokenY += 234235;
    //     liqTree.removeTLiq(LiqRange(1, 12), 4564564, 2342342e18, 456456e6);

    //     // LiqRange(1, 13)
    //     liqTree.feeRateSnapshotTokenX += 456457;
    //     liqTree.feeRateSnapshotTokenY += 456457;
    //     liqTree.addMLiq(LiqRange(1, 13), 567568);
    //     liqTree.feeRateSnapshotTokenX += 567567;
    //     liqTree.feeRateSnapshotTokenY += 97867;
    //     liqTree.removeMLiq(LiqRange(1, 13), 9785);
    //     liqTree.feeRateSnapshotTokenX += 67758;
    //     liqTree.feeRateSnapshotTokenY += 35645674;
    //     liqTree.addTLiq(LiqRange(1, 13), 235363565, 234534635e18, 456745643e6);
    //     liqTree.feeRateSnapshotTokenX += 345346;
    //     liqTree.feeRateSnapshotTokenY += 45674565;
    //     liqTree.removeTLiq(LiqRange(1, 13), 4545345, 34535635e18, 7564353e6);

    //     // LiqRange(1, 14)
    //     liqTree.feeRateSnapshotTokenX += 4567435634;
    //     liqTree.feeRateSnapshotTokenY += 234234235;
    //     liqTree.addMLiq(LiqRange(1, 14), 357635634);
    //     liqTree.feeRateSnapshotTokenX += 23535636;
    //     liqTree.feeRateSnapshotTokenY += 234534643576345;
    //     liqTree.removeMLiq(LiqRange(1, 14), 23425346456);
    //     liqTree.feeRateSnapshotTokenX += 3452342352;
    //     liqTree.feeRateSnapshotTokenY += 356734634532;
    //     liqTree.addTLiq(LiqRange(1, 14), 35235235, 346356343e18, 234265e6);
    //     liqTree.feeRateSnapshotTokenX += 2342456;
    //     liqTree.feeRateSnapshotTokenY += 3563463;
    //     liqTree.removeTLiq(LiqRange(1, 14), 234235, 4564565e18, 4564563452e6);

    //     // LiqRange(1, 15)
    //     liqTree.feeRateSnapshotTokenX += 234234;
    //     liqTree.feeRateSnapshotTokenY += 2463634534563;
    //     liqTree.addMLiq(LiqRange(1, 15), 34634636);
    //     liqTree.feeRateSnapshotTokenX += 1234245346;
    //     liqTree.feeRateSnapshotTokenY += 3453453;
    //     liqTree.removeMLiq(LiqRange(1, 15), 34534636);
    //     liqTree.feeRateSnapshotTokenX += 3463463;
    //     liqTree.feeRateSnapshotTokenY += 234523452;
    //     liqTree.addTLiq(LiqRange(1, 15), 234534534, 1234235235e18, 23423456346e6);
    //     liqTree.feeRateSnapshotTokenX += 134235235;
    //     liqTree.feeRateSnapshotTokenY += 3634634523;
    //     liqTree.removeTLiq(LiqRange(1, 15), 2342352356, 3465343e18, 3562342346e6);

    //     // endregion


    //     // mLiq
    //     assertEq(root.mLiq, 34693061576);

    //     assertEq(L.mLiq, 439440851037);
    //     assertEq(R.mLiq, 9846145283924);

    //     assertEq(LL.mLiq, 1324904479181181);
    //     assertEq(LR.mLiq, 3456457542419875553);
    //     assertEq(RL.mLiq, 76483482065306300976);
    //     assertEq(RR.mLiq, 8623526734267390879);

    //     assertEq(LLL.mLiq, 98987279855430619607264);
    //     assertEq(LLR.mLiq, 7986785734811822254);
    //     assertEq(LRL.mLiq, 232467224906920);
    //     assertEq(LRR.mLiq, 777839863652735);
    //     assertEq(RLL.mLiq, 3131567868974474895);
    //     assertEq(RLR.mLiq, 78724563469237853906739487);
    //     assertEq(RRL.mLiq, 7556478634723885529808249);
    //     assertEq(RRR.mLiq, 54534789284573456239862722);

    //     assertEq(LLLL.mLiq, 92736476015993741705);
    //     assertEq(LLLR.mLiq, 76238216349061404466493);
    //     assertEq(LLRL.mLiq, 2368562145653);
    //     assertEq(LLRR.mLiq, 12341234213421354513456);
    //     assertEq(LRLL.mLiq, 456467365563767);
    //     assertEq(LRLR.mLiq, 89805856756746);
    //     assertEq(LRRL.mLiq, 34545756857245324757901);
    //     assertEq(LRRR.mLiq, 2334646757867856856346);
    //     assertEq(RLLL.mLiq, 24674758679564605824007);
    //     assertEq(RLLR.mLiq, 547867967467456457536856873);
    //     assertEq(RLRL.mLiq, 34564375645457598309297);
    //     assertEq(RLRR.mLiq, 32546475786796896785674564);
    //     assertEq(RRLL.mLiq, 5856745645100215364274);
    //     assertEq(RRLR.mLiq, 4574785673643563456);
    //     assertEq(RRRL.mLiq, 24534622447854143);
    //     assertEq(RRRR.mLiq, 6345346534645746);

    //     // tLiq
    //     assertEq(root.tLiq, 3460019127642);

    //     assertEq(L.tLiq, 28597487121);
    //     assertEq(R.tLiq, 844037366102);

    //     assertEq(LL.tLiq, 325300632181949);
    //     assertEq(LR.tLiq, 456457566510607868);
    //     assertEq(RL.tLiq, 6483482620225461246);
    //     assertEq(RR.tLiq, 86235267342673908);

    //     assertEq(LLL.tLiq, 8987279836391260764175);
    //     assertEq(LLR.tLiq, 986785759840596613);
    //     assertEq(LRL.tLiq, 132467379863284);
    //     assertEq(LRR.tLiq, 277839863652735);
    //     assertEq(RLL.tLiq, 2131567868629590852);
    //     assertEq(RLR.tLiq, 8724563469237853906739487);
    //     assertEq(RRL.tLiq, 5556478634723909349324867);
    //     assertEq(RRR.tLiq, 34534789284573456239862722);

    //     assertEq(LLLL.tLiq, 9736478234923748923);
    //     assertEq(LLLR.tLiq, 7623821634912439930558);
    //     assertEq(LLRL.tLiq, 147556921176);
    //     assertEq(LLRR.tLiq, 1234123421342135451345);
    //     assertEq(LRLL.tLiq, 45644512117686);
    //     assertEq(LRLR.tLiq, 8980585675674);
    //     assertEq(LRRL.tLiq, 3454575685724498123174);
    //     assertEq(LRRR.tLiq, 233464675786785685634);
    //     assertEq(RLLL.tLiq, 2467475867956501134875);
    //     assertEq(RLLR.tLiq, 54786796746745645753685687);
    //     assertEq(RLRL.tLiq, 3456437564545419364152);
    //     assertEq(RLRR.tLiq, 3254647578679689678567456);
    //     assertEq(RRLL.tLiq, 585674564563690096108);
    //     assertEq(RRLR.tLiq, 457478567364356345);
    //     assertEq(RRRL.tLiq, 2453464609746674);
    //     assertEq(RRRR.tLiq, 6345346534645743);

    //     // subtreeMLiq
    //     assertEq(root.subtreeMLiq, 862435110165848273097702739);

    //     assertEq(L.subtreeMLiq, 323556957638501881815645);
    //     assertEq(R.subtreeMLiq, 862111553208209216126901878);

    //     assertEq(LL.subtreeMLiq, 286662725622816094451067);
    //     assertEq(LR.subtreeMLiq, 36894232012170260556282);
    //     assertEq(RL.subtreeMLiq, 737923121524118083514297409);
    //     assertEq(RR.subtreeMLiq, 124188431684012363450333077);

    //     assertEq(LLL.subtreeMLiq, 274305512535938637422726);
    //     assertEq(LLR.subtreeMLiq, 12357207787259540303617);
    //     assertEq(LRL.subtreeMLiq, 1011207672134353);
    //     assertEq(LRR.subtreeMLiq, 36880405170792908919717);
    //     assertEq(RLL.subtreeMLiq, 547892648489271760091630670);
    //     assertEq(RLR.subtreeMLiq, 190030167100918062197462835);
    //     assertEq(RRL.subtreeMLiq, 15118818589878544918544228);
    //     assertEq(RRR.subtreeMLiq, 109069578600026881462225333);

    //     assertEq(LLLL.subtreeMLiq, 92736476015993741705);
    //     assertEq(LLLR.subtreeMLiq, 76238216349061404466493);
    //     assertEq(LLRL.subtreeMLiq, 2368562145653);
    //     assertEq(LLRR.subtreeMLiq, 12341234213421354513456);
    //     assertEq(LRLL.subtreeMLiq, 456467365563767);
    //     assertEq(LRLR.subtreeMLiq, 89805856756746);
    //     assertEq(LRRL.subtreeMLiq, 34545756857245324757901);
    //     assertEq(LRRR.subtreeMLiq, 2334646757867856856346);
    //     assertEq(RLLL.subtreeMLiq, 24674758679564605824007);
    //     assertEq(RLLR.subtreeMLiq, 547867967467456457536856873);
    //     assertEq(RLRL.subtreeMLiq, 34564375645457598309297);
    //     assertEq(RLRR.subtreeMLiq, 32546475786796896785674564);
    //     assertEq(RRLL.subtreeMLiq, 5856745645100215364274);
    //     assertEq(RRLR.subtreeMLiq, 4574785673643563456);
    //     assertEq(RRRL.subtreeMLiq, 24534622447854143);
    //     assertEq(RRRR.subtreeMLiq, 6345346534645746);

    //     // borrowed_x
    //     assertEq(root.tokenX.borrowed, 122757244859000000000000000000);

    //     assertEq(L.tokenX.borrowed, 4564946112436545000000000000000000);
    //     assertEq(R.tokenX.borrowed, 4214226187000000000000000000);

    //     assertEq(LL.tokenX.borrowed, 28591083251822194000000000000000000);
    //     assertEq(LR.tokenX.borrowed, 872538470624167989000000000456468745);
    //     assertEq(RL.tokenX.borrowed, 11350238408160809000000000000000000);
    //     assertEq(RR.tokenX.borrowed, 498723597863764293000000000000000000);

    //     assertEq(LLL.tokenX.borrowed, 45623798462966929913344000000000000000000);
    //     assertEq(LLR.tokenX.borrowed, 298364785638480072406864000000000456468745);
    //     assertEq(LRL.tokenX.borrowed, 27364762534827634534656283000000000000000000);
    //     assertEq(LRR.tokenX.borrowed, 7653642903472903784290347000000000000000000);
    //     assertEq(RLL.tokenX.borrowed, 23452367423432458653826000000000000000000);
    //     assertEq(RLR.tokenX.borrowed, 2765723642783492000000000000000000);
    //     assertEq(RRL.tokenX.borrowed, 28635482365337910060000000000000000000);
    //     assertEq(RRR.tokenX.borrowed, 27364527863428346239867000000000000000000);

    //     assertEq(LLLL.tokenX.borrowed, 5730994510532853000000000000000000);
    //     assertEq(LLLR.tokenX.borrowed, 346456348776251331000000000456468745);
    //     assertEq(LLRL.tokenX.borrowed, 82735476982561720575720000000000000000000);
    //     assertEq(LLRR.tokenX.borrowed, 2367452364752903485729403875000000000000000000);
    //     assertEq(LRLL.tokenX.borrowed, 236452378374761357390655000000000000000000);
    //     assertEq(LRLR.tokenX.borrowed, 8374278364628364000000000000000000);
    //     assertEq(LRRL.tokenX.borrowed, 3456457409582626000000000000000000);
    //     assertEq(LRRR.tokenX.borrowed, 236542867349237498000000000000000000);
    //     assertEq(RLLL.tokenX.borrowed, 51427634238746298454880156000000000000000000);
    //     assertEq(RLLR.tokenX.borrowed, 634529836428376523000000000000000000);
    //     assertEq(RLRL.tokenX.borrowed, 1212312318064122113000000000000000000);
    //     assertEq(RLRR.tokenX.borrowed, 287346234623487923642786000000000000000000);
    //     assertEq(RRLL.tokenX.borrowed, 2837427354234552837898000000000000000000);
    //     assertEq(RRLR.tokenX.borrowed, 82635472634823674000000000000000000);
    //     assertEq(RRRL.tokenX.borrowed, 23645278463153819232000000000000000000);
    //     assertEq(RRRR.tokenX.borrowed, 37465276342938487000000000000000000);

    //     // subtree_borrowed_x
    //     assertEq(root.tokenX.subtreeBorrowed, 2454902637693472541111720750000000001369406235);

    //     assertEq(L.tokenX.subtreeBorrowed, 2403133948136918240527296488000000001369406235);
    //     assertEq(R.tokenX.subtreeBorrowed, 51768689556554177827179403000000000000000000);

    //     assertEq(LL.tokenX.subtreeBorrowed, 2367879089194765920990906181000000000912937490);
    //     assertEq(LR.tokenX.subtreeBorrowed, 35254858937587373423953762000000000456468745);
    //     assertEq(RL.tokenX.subtreeBorrowed, 51738434701751335380619705000000000000000000);
    //     assertEq(RR.tokenX.subtreeBorrowed, 30254854802838232333511000000000000000000);

    //     assertEq(LLL.tokenX.subtreeBorrowed, 45624150650310216697528000000000456468745);
    //     assertEq(LLR.tokenX.subtreeBorrowed, 2367833465015524527522386459000000000456468745);
    //     assertEq(LRL.tokenX.subtreeBorrowed, 27601214921576674256675302000000000000000000);
    //     assertEq(LRR.tokenX.subtreeBorrowed, 7653643143472228543110471000000000000000000);
    //     assertEq(RLL.tokenX.subtreeBorrowed, 51451087240699567341910505000000000000000000);
    //     assertEq(RLR.tokenX.subtreeBorrowed, 287347449701529630548391000000000000000000);
    //     assertEq(RRL.tokenX.subtreeBorrowed, 2866145472072525571632000000000000000000);
    //     assertEq(RRR.tokenX.subtreeBorrowed, 27388210607167842997586000000000000000000);

    //     assertEq(LLLL.tokenX.subtreeBorrowed, 5730994510532853000000000000000000);
    //     assertEq(LLLR.tokenX.subtreeBorrowed, 346456348776251331000000000456468745);
    //     assertEq(LLRL.tokenX.subtreeBorrowed, 82735476982561720575720000000000000000000);
    //     assertEq(LLRR.tokenX.subtreeBorrowed, 2367452364752903485729403875000000000000000000);
    //     assertEq(LRLL.tokenX.subtreeBorrowed, 236452378374761357390655000000000000000000);
    //     assertEq(LRLR.tokenX.subtreeBorrowed, 8374278364628364000000000000000000);
    //     assertEq(LRRL.tokenX.subtreeBorrowed, 3456457409582626000000000000000000);
    //     assertEq(LRRR.tokenX.subtreeBorrowed, 236542867349237498000000000000000000);
    //     assertEq(RLLL.tokenX.subtreeBorrowed, 51427634238746298454880156000000000000000000);
    //     assertEq(RLLR.tokenX.subtreeBorrowed, 634529836428376523000000000000000000);
    //     assertEq(RLRL.tokenX.subtreeBorrowed, 1212312318064122113000000000000000000);
    //     assertEq(RLRR.tokenX.subtreeBorrowed, 287346234623487923642786000000000000000000);
    //     assertEq(RRLL.tokenX.subtreeBorrowed, 2837427354234552837898000000000000000000);
    //     assertEq(RRLR.tokenX.subtreeBorrowed, 82635472634823674000000000000000000);
    //     assertEq(RRRL.tokenX.subtreeBorrowed, 23645278463153819232000000000000000000);
    //     assertEq(RRRR.tokenX.subtreeBorrowed, 37465276342938487000000000000000000);

    //     // borrowed_y
    //     assertEq(root.tokenY.borrowed, 111746265029000000);

    //     assertEq(L.tokenY.borrowed, 168910846992000000);
    //     assertEq(R.tokenY.borrowed, 20158676903000000);

    //     assertEq(LL.tokenY.borrowed, 1330115070330000000);
    //     assertEq(LR.tokenY.borrowed, 25629380814000000);
    //     assertEq(RL.tokenY.borrowed, 978614737019690000000);
    //     assertEq(RR.tokenY.borrowed, 7856675879087000000);

    //     assertEq(LLL.tokenY.borrowed, 8725348768599465892504400000);
    //     assertEq(LLR.tokenY.borrowed, 3465873661686981218000000);
    //     assertEq(LRL.tokenY.borrowed, 56736409827636032519000000);
    //     assertEq(LRR.tokenY.borrowed, 7834626734902734902368000000);
    //     assertEq(RLL.tokenY.borrowed, 9834787362493137985000000);
    //     assertEq(RLR.tokenY.borrowed, 98576798364725367423000000);
    //     assertEq(RRL.tokenY.borrowed, 83764587364859345003508901000000);
    //     assertEq(RRR.tokenY.borrowed, 9834657827356482367482369000000);

    //     assertEq(LLLL.tokenY.borrowed, 76196798741476175000000);
    //     assertEq(LLLR.tokenY.borrowed, 26734872634892655597150111000000);
    //     assertEq(LLRL.tokenY.borrowed, 763467253680744840679549000000);
    //     assertEq(LLRR.tokenY.borrowed, 987349053045739487000000);
    //     assertEq(LRLL.tokenY.borrowed, 984764582781001178332000000);
    //     assertEq(LRLR.tokenY.borrowed, 8763867548273647826000000);
    //     assertEq(LRRL.tokenY.borrowed, 8726347825634871839691000000);
    //     assertEq(LRRR.tokenY.borrowed, 798647852364627983000000);
    //     assertEq(RLLL.tokenY.borrowed, 74986238502927037000000);
    //     assertEq(RLLR.tokenY.borrowed, 868746576834678534000000);
    //     assertEq(RLRL.tokenY.borrowed, 3423423619393235000000);
    //     assertEq(RLRR.tokenY.borrowed, 827364826734823748963000000);
    //     assertEq(RRLL.tokenY.borrowed, 73649082374024158406167000000);
    //     assertEq(RRLR.tokenY.borrowed, 2387642836423689768000000);
    //     assertEq(RRRL.tokenY.borrowed, 3542359995424161000000);
    //     assertEq(RRRR.tokenY.borrowed, 23984623847623867000000);

    //     // subtree_borrowed_y
    //     assertEq(root.tokenY.subtreeBorrowed, 121198515219146561028675018400000);

    //     assertEq(L.tokenY.subtreeBorrowed, 27524681804831584915445899400000);
    //     assertEq(R.tokenY.subtreeBorrowed, 93673833414314864366964090000000);

    //     assertEq(LL.tokenY.subtreeBorrowed, 27507069766762843492989374400000);
    //     assertEq(LR.tokenY.subtreeBorrowed, 17612038068572511609533000000);
    //     assertEq(RL.tokenY.subtreeBorrowed, 936724547315736272867000000);
    //     assertEq(RR.tokenY.subtreeBorrowed, 93672896689767528472014320000000);

    //     assertEq(LLL.tokenY.subtreeBorrowed, 26743598059858053804518790400000);
    //     assertEq(LLR.tokenY.subtreeBorrowed, 763471706903459573400254000000);
    //     assertEq(LRL.tokenY.subtreeBorrowed, 1050264860156910858677000000);
    //     assertEq(LRR.tokenY.subtreeBorrowed, 16561773208389971370042000000);
    //     assertEq(RLL.tokenY.subtreeBorrowed, 10778520177830743556000000);
    //     assertEq(RLR.tokenY.subtreeBorrowed, 925945048523168509621000000);
    //     assertEq(RRL.tokenY.subtreeBorrowed, 83838238834876205585604836000000);
    //     assertEq(RRR.tokenY.subtreeBorrowed, 9834657854883466210530397000000);

    //     assertEq(LLLL.tokenY.subtreeBorrowed, 76196798741476175000000);
    //     assertEq(LLLR.tokenY.subtreeBorrowed, 26734872634892655597150111000000);
    //     assertEq(LLRL.tokenY.subtreeBorrowed, 763467253680744840679549000000);
    //     assertEq(LLRR.tokenY.subtreeBorrowed, 987349053045739487000000);
    //     assertEq(LRLL.tokenY.subtreeBorrowed, 984764582781001178332000000);
    //     assertEq(LRLR.tokenY.subtreeBorrowed, 8763867548273647826000000);
    //     assertEq(LRRL.tokenY.subtreeBorrowed, 8726347825634871839691000000);
    //     assertEq(LRRR.tokenY.subtreeBorrowed, 798647852364627983000000);
    //     assertEq(RLLL.tokenY.subtreeBorrowed, 74986238502927037000000);
    //     assertEq(RLLR.tokenY.subtreeBorrowed, 868746576834678534000000);
    //     assertEq(RLRL.tokenY.subtreeBorrowed, 3423423619393235000000);
    //     assertEq(RLRR.tokenY.subtreeBorrowed, 827364826734823748963000000);
    //     assertEq(RRLL.tokenY.subtreeBorrowed, 73649082374024158406167000000);
    //     assertEq(RRLR.tokenY.subtreeBorrowed, 2387642836423689768000000);
    //     assertEq(RRRL.tokenY.subtreeBorrowed, 3542359995424161000000);
    //     assertEq(RRRR.tokenY.subtreeBorrowed, 23984623847623867000000);

    //     // tokenX.cumulativeEarnedPerMLiq
    //     assertEq(root.tokenX.cumulativeEarnedPerMLiq, 1653162341);

    //     assertEq(L.tokenX.cumulativeEarnedPerMLiq, 1968034923387);
    //     assertEq(R.tokenX.cumulativeEarnedPerMLiq, 53197209);

    //     assertEq(LL.tokenX.cumulativeEarnedPerMLiq, 1537875992445232346);
    //     assertEq(LR.tokenX.cumulativeEarnedPerMLiq, 363545476413679861713);
    //     assertEq(RL.tokenX.cumulativeEarnedPerMLiq, 141356179733701);
    //     assertEq(RR.tokenX.cumulativeEarnedPerMLiq, 61732151382143711);

    //     assertEq(LLL.tokenX.cumulativeEarnedPerMLiq, 2556757494839963014198184);
    //     assertEq(LLR.tokenX.cumulativeEarnedPerMLiq, 371158797429650858973438625);
    //     assertEq(LRL.tokenX.cumulativeEarnedPerMLiq, 60841441341419381047595034241085);
    //     assertEq(LRR.tokenX.cumulativeEarnedPerMLiq, 3189508411491199598333431314);
    //     assertEq(RLL.tokenX.cumulativeEarnedPerMLiq, 657996725303326136999);
    //     assertEq(RLR.tokenX.cumulativeEarnedPerMLiq, 223727062042489);
    //     assertEq(RRL.tokenX.cumulativeEarnedPerMLiq, 29115133709213782165);
    //     assertEq(RRR.tokenX.cumulativeEarnedPerMLiq, 3856709189487099165901);

    //     assertEq(LLLL.tokenX.cumulativeEarnedPerMLiq, 889700619080860150);
    //     assertEq(LLLR.tokenX.cumulativeEarnedPerMLiq, 30393719776417661690);
    //     assertEq(LLRL.tokenX.cumulativeEarnedPerMLiq, 159213596840619244523447699163);
    //     assertEq(LLRR.tokenX.cumulativeEarnedPerMLiq, 0);
    //     assertEq(LRLL.tokenX.cumulativeEarnedPerMLiq, 1051376974879620344655023882438);
    //     assertEq(LRLR.tokenX.cumulativeEarnedPerMLiq, 0);
    //     assertEq(LRRL.tokenX.cumulativeEarnedPerMLiq, 1537891441852978794);
    //     assertEq(LRRR.tokenX.cumulativeEarnedPerMLiq, 0);
    //     assertEq(RLLL.tokenX.cumulativeEarnedPerMLiq, 31935758833446278128768039723);
    //     assertEq(RLLR.tokenX.cumulativeEarnedPerMLiq, 0);
    //     assertEq(RLRL.tokenX.cumulativeEarnedPerMLiq, 236616939696375723);
    //     assertEq(RLRR.tokenX.cumulativeEarnedPerMLiq, 0);
    //     assertEq(RRLL.tokenX.cumulativeEarnedPerMLiq, 5767677373168060851383);
    //     assertEq(RRLR.tokenX.cumulativeEarnedPerMLiq, 0);
    //     assertEq(RRRL.tokenX.cumulativeEarnedPerMLiq, 6665049232753208950);
    //     assertEq(RRRR.tokenX.cumulativeEarnedPerMLiq, 0);

    //     // token_x_cumulative_earned_per_m_subtree_liq
    //     assertEq(root.tokenX.subtreecumulativeEarnedPerMLiq, 43756288901278965565289120);

    //     assertEq(L.tokenX.subtreecumulativeEarnedPerMLiq, 114172069341113006721615069516);
    //     assertEq(R.tokenX.subtreecumulativeEarnedPerMLiq, 923073628282275460400546);

    //     assertEq(LL.tokenX.subtreecumulativeEarnedPerMLiq, 126975792932608136142575516378);
    //     assertEq(LR.tokenX.subtreecumulativeEarnedPerMLiq, 14689030881642935495954673055);
    //     assertEq(RL.tokenX.subtreecumulativeEarnedPerMLiq, 1077791623755590749427001);
    //     assertEq(RR.tokenX.subtreecumulativeEarnedPerMLiq, 3744954689799430215251);

    //     assertEq(LLL.tokenX.subtreecumulativeEarnedPerMLiq, 2556777231614922263512088);
    //     assertEq(LLR.tokenX.subtreecumulativeEarnedPerMLiq, 2945529310733483531304171330809);
    //     assertEq(LRL.tokenX.subtreecumulativeEarnedPerMLiq, 61367157725965120112844741263941);
    //     assertEq(LRR.tokenX.subtreecumulativeEarnedPerMLiq, 3189508511506300233910914258);
    //     assertEq(RLL.tokenX.subtreecumulativeEarnedPerMLiq, 1443549229249734665667944);
    //     assertEq(RLR.tokenX.subtreecumulativeEarnedPerMLiq, 23244332771593818172928);
    //     assertEq(RRL.tokenX.subtreecumulativeEarnedPerMLiq, 2914154110846149087494);
    //     assertEq(RRR.tokenX.subtreecumulativeEarnedPerMLiq, 3860046994395227474433);

    //     assertEq(LLLL.tokenX.subtreecumulativeEarnedPerMLiq, 889700619080860150);
    //     assertEq(LLLR.tokenX.subtreecumulativeEarnedPerMLiq, 30393719776417661690);
    //     assertEq(LLRL.tokenX.subtreecumulativeEarnedPerMLiq, 159213596840619244523447699163);
    //     assertEq(LLRR.tokenX.subtreecumulativeEarnedPerMLiq, 0);
    //     assertEq(LRLL.tokenX.subtreecumulativeEarnedPerMLiq, 1051376974879620344655023882438);
    //     assertEq(LRLR.tokenX.subtreecumulativeEarnedPerMLiq, 0);
    //     assertEq(LRRL.tokenX.subtreecumulativeEarnedPerMLiq, 1537891441852978794);
    //     assertEq(LRRR.tokenX.subtreecumulativeEarnedPerMLiq, 0);
    //     assertEq(RLLL.tokenX.subtreecumulativeEarnedPerMLiq, 31935758833446278128768039723);
    //     assertEq(RLLR.tokenX.subtreecumulativeEarnedPerMLiq, 0);
    //     assertEq(RLRL.tokenX.subtreecumulativeEarnedPerMLiq, 236616939696375723);
    //     assertEq(RLRR.tokenX.subtreecumulativeEarnedPerMLiq, 0);
    //     assertEq(RRLL.tokenX.subtreecumulativeEarnedPerMLiq, 5767677373168060851383);
    //     assertEq(RRLR.tokenX.subtreecumulativeEarnedPerMLiq, 0);
    //     assertEq(RRRL.tokenX.subtreecumulativeEarnedPerMLiq, 6665049232753208950);
    //     assertEq(RRRR.tokenX.subtreecumulativeEarnedPerMLiq, 0);

    //     // tokenY.cumulativeEarnedPerMLiq
    //     assertEq(root.tokenY.cumulativeEarnedPerMLiq, 0);

    //     assertEq(L.tokenY.cumulativeEarnedPerMLiq, 82);
    //     assertEq(R.tokenY.cumulativeEarnedPerMLiq, 0);

    //     assertEq(LL.tokenY.cumulativeEarnedPerMLiq, 670);
    //     assertEq(LR.tokenY.cumulativeEarnedPerMLiq, 39);
    //     assertEq(RL.tokenY.cumulativeEarnedPerMLiq, 197);
    //     assertEq(RR.tokenY.cumulativeEarnedPerMLiq, 9);

    //     assertEq(LLL.tokenY.cumulativeEarnedPerMLiq, 4747990803139);
    //     assertEq(LLR.tokenY.cumulativeEarnedPerMLiq, 41865270006);
    //     assertEq(LRL.tokenY.cumulativeEarnedPerMLiq, 1224894367084578);
    //     assertEq(LRR.tokenY.cumulativeEarnedPerMLiq, 31703181193601);
    //     assertEq(RLL.tokenY.cumulativeEarnedPerMLiq, 2679359);
    //     assertEq(RLR.tokenY.cumulativeEarnedPerMLiq, 77430742);
    //     assertEq(RRL.tokenY.cumulativeEarnedPerMLiq, 826996583538488);
    //     assertEq(RRR.tokenY.cumulativeEarnedPerMLiq, 13459135450531);

    //     assertEq(LLLL.tokenY.cumulativeEarnedPerMLiq, 109425756);
    //     assertEq(LLLR.tokenY.cumulativeEarnedPerMLiq, 22774163335023745);
    //     assertEq(LLRL.tokenY.cumulativeEarnedPerMLiq, 14266182294798018313);
    //     assertEq(LLRR.tokenY.cumulativeEarnedPerMLiq, 0);
    //     assertEq(LRLL.tokenY.cumulativeEarnedPerMLiq, 42518327403210687);
    //     assertEq(LRLR.tokenY.cumulativeEarnedPerMLiq, 0);
    //     assertEq(LRRL.tokenY.cumulativeEarnedPerMLiq, 37701268286368);
    //     assertEq(LRRR.tokenY.cumulativeEarnedPerMLiq, 0);
    //     assertEq(RLLL.tokenY.cumulativeEarnedPerMLiq, 452159061);
    //     assertEq(RLLR.tokenY.cumulativeEarnedPerMLiq, 0);
    //     assertEq(RLRL.tokenY.cumulativeEarnedPerMLiq, 6488);
    //     assertEq(RLRR.tokenY.cumulativeEarnedPerMLiq, 0);
    //     assertEq(RRLL.tokenY.cumulativeEarnedPerMLiq, 1453692415004);
    //     assertEq(RRLR.tokenY.cumulativeEarnedPerMLiq, 0);
    //     assertEq(RRRL.tokenY.cumulativeEarnedPerMLiq, 9695);
    //     assertEq(RRRR.tokenY.cumulativeEarnedPerMLiq, 0);

    //     // token_y_cumulative_earned_per_m_subtree_liq
    //     assertEq(root.tokenY.subtreecumulativeEarnedPerMLiq, 20976473812693);

    //     assertEq(L.tokenY.subtreecumulativeEarnedPerMLiq, 12697937271018899);
    //     assertEq(R.tokenY.subtreecumulativeEarnedPerMLiq, 16218714968180);

    //     assertEq(LL.tokenY.subtreecumulativeEarnedPerMLiq, 14323023895032874);
    //     assertEq(LR.tokenY.subtreecumulativeEarnedPerMLiq, 71254575045205);
    //     assertEq(RL.tokenY.subtreecumulativeEarnedPerMLiq, 189479572);
    //     assertEq(RR.tokenY.subtreecumulativeEarnedPerMLiq, 112588600574925);

    //     assertEq(LLL.tokenY.subtreecumulativeEarnedPerMLiq, 14552811706670570);
    //     assertEq(LLR.tokenY.subtreecumulativeEarnedPerMLiq, 9222191117511089);
    //     assertEq(LRL.tokenY.subtreecumulativeEarnedPerMLiq, 22674390484203729);
    //     assertEq(LRR.tokenY.subtreecumulativeEarnedPerMLiq, 67017984988846);
    //     assertEq(RLL.tokenY.subtreecumulativeEarnedPerMLiq, 2936467);
    //     assertEq(RLR.tokenY.subtreecumulativeEarnedPerMLiq, 727317315);
    //     assertEq(RRL.tokenY.subtreecumulativeEarnedPerMLiq, 827723734665148);
    //     assertEq(RRR.tokenY.subtreecumulativeEarnedPerMLiq, 13459135488203);

    //     assertEq(LLLL.tokenY.subtreecumulativeEarnedPerMLiq, 109425756);
    //     assertEq(LLLR.tokenY.subtreecumulativeEarnedPerMLiq, 22774163335023745);
    //     assertEq(LLRL.tokenY.subtreecumulativeEarnedPerMLiq, 14266182294798018313);
    //     assertEq(LLRR.tokenY.subtreecumulativeEarnedPerMLiq, 0);
    //     assertEq(LRLL.tokenY.subtreecumulativeEarnedPerMLiq, 42518327403210687);
    //     assertEq(LRLR.tokenY.subtreecumulativeEarnedPerMLiq, 0);
    //     assertEq(LRRL.tokenY.subtreecumulativeEarnedPerMLiq, 37701268286368);
    //     assertEq(LRRR.tokenY.subtreecumulativeEarnedPerMLiq, 0);
    //     assertEq(RLLL.tokenY.subtreecumulativeEarnedPerMLiq, 452159061);
    //     assertEq(RLLR.tokenY.subtreecumulativeEarnedPerMLiq, 0);
    //     assertEq(RLRL.tokenY.subtreecumulativeEarnedPerMLiq, 6488);
    //     assertEq(RLRR.tokenY.subtreecumulativeEarnedPerMLiq, 0);
    //     assertEq(RRLL.tokenY.subtreecumulativeEarnedPerMLiq, 1453692415004);
    //     assertEq(RRLR.tokenY.subtreecumulativeEarnedPerMLiq, 0);
    //     assertEq(RRRL.tokenY.subtreecumulativeEarnedPerMLiq, 9695);
    //     assertEq(RRRR.tokenY.subtreecumulativeEarnedPerMLiq, 0);
    // }

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
    //     liqTree.feeRateSnapshotTokenX += 4541239648278065);  // 7.9% APR as Q192.64 T98273 - T0
    //     liqTree.feeRateSnapshotTokenY += 13278814667749784); // 23.1% APR as Q192.64 T98273 - T0

    //     // Step 3); Apply change that effects the entire tree, to calculate the fees at each node
    //     // 3.1); addMLiq
    //     liqTree.addMLiq(LiqRange(8, 12), 2734); // RRLL, RL

    //     // root
    //     assertEq(root.tokenX.cumulativeEarnedPerMLiq, 373601278);
    //     assertEq(root.tokenX.subtreecumulativeEarnedPerMLiq, 2303115199);
    //     assertEq(root.tokenY.cumulativeEarnedPerMLiq, 0);
    //     assertEq(root.tokenY.subtreecumulativeEarnedPerMLiq, 2);

    //     // R
    //     assertEq(R.tokenX.cumulativeEarnedPerMLiq, 757991165);
    //     assertEq(R.tokenX.subtreecumulativeEarnedPerMLiq, 1929915382);
    //     assertEq(R.tokenY.cumulativeEarnedPerMLiq, 0);
    //     assertEq(R.tokenY.subtreecumulativeEarnedPerMLiq, 1);

    //     // RR
    //     assertEq(RR.tokenX.cumulativeEarnedPerMLiq, 581096415);
    //     assertEq(RR.tokenX.subtreecumulativeEarnedPerMLiq, 1153837196);
    //     assertEq(RR.tokenY.cumulativeEarnedPerMLiq, 0);
    //     assertEq(RR.tokenY.subtreecumulativeEarnedPerMLiq, 1);

    //     // RL
    //     assertEq(RL.tokenX.cumulativeEarnedPerMLiq, 148929881804);
    //     assertEq(RL.tokenX.subtreecumulativeEarnedPerMLiq, 148929881804);
    //     assertEq(RL.tokenY.cumulativeEarnedPerMLiq, 10);
    //     assertEq(RL.tokenY.subtreecumulativeEarnedPerMLiq, 10);

    //     // RRL
    //     assertEq(RRL.tokenX.cumulativeEarnedPerMLiq, 42651943);
    //     assertEq(RRL.tokenX.subtreecumulativeEarnedPerMLiq, 606784254);
    //     assertEq(RRL.tokenY.cumulativeEarnedPerMLiq, 0);
    //     assertEq(RRL.tokenY.subtreecumulativeEarnedPerMLiq, 1);

    //     // RRLL
    //     assertEq(RRLL.tokenX.cumulativeEarnedPerMLiq, 581500584);
    //     assertEq(RRLL.tokenX.subtreecumulativeEarnedPerMLiq, 581500584);
    //     assertEq(RRLL.tokenY.cumulativeEarnedPerMLiq, 1);
    //     assertEq(RRLL.tokenY.subtreecumulativeEarnedPerMLiq, 1);

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
    //     liqTree.feeRateSnapshotTokenX += 16463537718422861220174597);   // 978567.9% APR as Q192.64 T2876298273 - T98273
    //     liqTree.feeRateSnapshotTokenY += 3715979586694123491881712207); // 220872233.1% APR as Q192.64 T2876298273 - T98273

    //     liqTree.removeMLiq(LiqRange(8, 12), 2734); // RRLL, RL

    //     // root
    //     assertEq(root.tokenX.cumulativeEarnedPerMLiq, 373601278 + 1354374549470516050);         // 1354374549844117328
    //     assertEq(root.tokenX.subtreecumulativeEarnedPerMLiq, 2303115199 + 8349223594601778821); // 8349223596904894020
    //     assertEq(root.tokenY.cumulativeEarnedPerMLiq, 0 + 158351473403);                        // 158351473403
    //     assertEq(root.tokenY.subtreecumulativeEarnedPerMLiq, 2 + 710693401861);                 // 710693401863

    //     // R
    //     assertEq(R.tokenX.cumulativeEarnedPerMLiq, 757991165 + 2747859799177149412);         // 2747859799935140577
    //     assertEq(R.tokenX.subtreecumulativeEarnedPerMLiq, 1929915382 + 6996304358425988634); // 6996304360355904016
    //     assertEq(R.tokenY.cumulativeEarnedPerMLiq, 0 + 219375887);                           // 219375887
    //     assertEq(R.tokenY.subtreecumulativeEarnedPerMLiq, 1 + 552456845955);                 // 552456845956

    //     // RR
    //     assertEq(RR.tokenX.cumulativeEarnedPerMLiq, 581096415 + 2106654304105573173);         // 2106654304686669588
    //     assertEq(RR.tokenX.subtreecumulativeEarnedPerMLiq, 1153837196 + 4183016846975641372); // 4183016848129478568
    //     assertEq(RR.tokenY.cumulativeEarnedPerMLiq, 0 + 62008538706);                         // 62008538706
    //     assertEq(RR.tokenY.subtreecumulativeEarnedPerMLiq, 1 + 551980602776);                 // 551980602777

    //     // RL
    //     assertEq(RL.tokenX.cumulativeEarnedPerMLiq, 148929881804 + 423248577958689008325);        // 423248578107618890129
    //     assertEq(RL.tokenX.subtreecumulativeEarnedPerMLiq, 148929881804 + 423248577958689008325); // 423248578107618890129
    //     assertEq(RL.tokenY.cumulativeEarnedPerMLiq, 10 + 2197219781185);                          // 2197219781195
    //     assertEq(RL.tokenY.subtreecumulativeEarnedPerMLiq, 10 + 2197219781185);                   // 2197219781195

    //     // RRL
    //     assertEq(RRL.tokenX.cumulativeEarnedPerMLiq, 42651943 + 154626414974589533);          // 154626415017241476
    //     assertEq(RRL.tokenX.subtreecumulativeEarnedPerMLiq, 606784254 + 2199779563978122803); // 2199779564584907057
    //     assertEq(RRL.tokenY.cumulativeEarnedPerMLiq, 0 + 5771781665);                         // 5771781665
    //     assertEq(RRL.tokenY.subtreecumulativeEarnedPerMLiq, 1 + 519095539054);                // 519095539055

    //     // RRLL
    //     assertEq(RRLL.tokenX.cumulativeEarnedPerMLiq, 581500584 + 2108117905415037748);         // 2108117905996538332
    //     assertEq(RRLL.tokenX.subtreecumulativeEarnedPerMLiq, 581500584 + 2108117905415037748);  // 2108117905996538332
    //     assertEq(RRLL.tokenY.cumulativeEarnedPerMLiq, 1 + 529127613134);                        // 529127613135
    //     assertEq(RRLL.tokenY.subtreecumulativeEarnedPerMLiq, 1 + 529127613134);                 // 529127613135
        
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
    //     liqTree.feeRateSnapshotTokenX += 11381610389149375791104);   // 307% APR as Q192.64 T9214298113 - T2876298273
    //     liqTree.feeRateSnapshotTokenY += 185394198934916215865344);  // 5000.7% APR as Q192.64 T9214298113 - T2876298273

    //     liqTree.addTLiq(LiqRange(8, 12), 1000, 1000e18, 1000e6); // RRLL, RL

    //     // root
    //     assertEq(root.tokenX.cumulativeEarnedPerMLiq, 1354374549844117328 + 936348777891386);         // 1355310898622008714
    //     assertEq(root.tokenX.subtreecumulativeEarnedPerMLiq, 8349223596904894020 + 5772247649074341); // 8354995844553968361
    //     assertEq(root.tokenY.cumulativeEarnedPerMLiq, 158351473403 + 7900657);                        // 158359374060
    //     assertEq(root.tokenY.subtreecumulativeEarnedPerMLiq, 710693401863 + 35458749);                // 710728860612

    //     // R
    //     assertEq(R.tokenX.cumulativeEarnedPerMLiq, 2747859799935140577 + 1899736810880077);        // 2749759536746020654
    //     assertEq(R.tokenX.subtreecumulativeEarnedPerMLiq, 6996304360355904016 + 4836905046539355); // 7001141265402443371
    //     assertEq(R.tokenY.cumulativeEarnedPerMLiq, 219375887 + 10945);                             // 219386832
    //     assertEq(R.tokenY.subtreecumulativeEarnedPerMLiq, 552456845956 + 27563825);                // 552484409781

    //     // RR
    //     assertEq(RR.tokenX.cumulativeEarnedPerMLiq, 2106654304686669588 + 1456389336983247);        // 2108110694023652835
    //     assertEq(RR.tokenX.subtreecumulativeEarnedPerMLiq, 4183016848129478568 + 2891837127944514); // 4185908685257423082
    //     assertEq(RR.tokenY.cumulativeEarnedPerMLiq, 62008538706 + 3093698);                         // 62011632404
    //     assertEq(RR.tokenY.subtreecumulativeEarnedPerMLiq, 551980602777 + 27539135);                // 552008141912

    //     // RL
    //     assertEq(RL.tokenX.cumulativeEarnedPerMLiq, 423248578107618890129 + 373259731104033296);        // 423621837838722923425
    //     assertEq(RL.tokenX.subtreecumulativeEarnedPerMLiq, 423248578107618890129 + 373259731104033296); // 423621837838722923425
    //     assertEq(RL.tokenY.cumulativeEarnedPerMLiq, 2197219781195 + 139839995);                         // 2197359621190
    //     assertEq(RL.tokenY.subtreecumulativeEarnedPerMLiq, 2197219781195 + 139839995);                  // 2197359621190

    //     // RRL
    //     assertEq(RRL.tokenX.cumulativeEarnedPerMLiq, 154626415017241476 + 106897640711262);          // 154733312657952738
    //     assertEq(RRL.tokenX.subtreecumulativeEarnedPerMLiq, 2199779564584907057 + 1520770209363996); // 2201300334794271053
    //     assertEq(RRL.tokenY.cumulativeEarnedPerMLiq, 5771781665 + 287962);                           // 5772069627
    //     assertEq(RRL.tokenY.subtreecumulativeEarnedPerMLiq, 519095539055 + 25898463);                // 519121437518

    //     // RRLL
    //     assertEq(RRLL.tokenX.cumulativeEarnedPerMLiq, 2108117905996538332 + 1457402297493569);        // 2109575308294031901
    //     assertEq(RRLL.tokenX.subtreecumulativeEarnedPerMLiq, 2108117905996538332 + 1457402297493569); // 2109575308294031901
    //     assertEq(RRLL.tokenY.cumulativeEarnedPerMLiq, 529127613135 + 26398986);                       // 529154012121
    //     assertEq(RRLL.tokenY.subtreecumulativeEarnedPerMLiq, 529127613135 + 26398986);                // 529154012121

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
    //     liqTree.feeRateSnapshotTokenX += 2352954287417905205553); // 17% APR as Q192.64 T32876298273 - T9214298113
    //     liqTree.feeRateSnapshotTokenY += 6117681147286553534438); // 44.2% APR as Q192.64 T32876298273 - T9214298113

    //     liqTree.removeTLiq(LiqRange(8, 12), 1000, 1000e18, 1000e6); // RRLL, RL

    //     // root
    //     // A = 0
    //     // m = 324198833
    //     //     x: 492e18 * 2352954287417905205553 / 324198833 / 2**64
    //     // x sub: 5033e18 * 2352954287417905205553 / 324198833 / 2**64
    //     //     y: 254858e6 * 6117681147286553534438 / 324198833 / 2**64
    //     // y sub: 1145822e6 * 6117681147286553534438 / 324198833 / 2**64
    //     assertEq(root.tokenX.cumulativeEarnedPerMLiq, 1355310898622008714 + 193574177654021);
    //     assertEq(root.tokenX.subtreecumulativeEarnedPerMLiq, 8354995844553968361 + 1980200886448553);
    //     assertEq(root.tokenY.cumulativeEarnedPerMLiq, 158359374060 + 260707);
    //     assertEq(root.tokenY.subtreecumulativeEarnedPerMLiq, 710728860612 + 1172122);

    //     // R
    //     // 998e18 * 2352954287417905205553 / 324131393 / 2**64
    //     // 4541e18 * 2352954287417905205553 / 324131393 / 2**64
    //     // 353e6 * 6117681147286553534438 / 324131393 / 2**64
    //     // 890964e6 * 6117681147286553534438 / 324131393 / 2**64
    //     assertEq(R.tokenX.cumulativeEarnedPerMLiq, 2749759536746020654 + 392738261220692);
    //     assertEq(R.tokenX.subtreecumulativeEarnedPerMLiq, 7001141265402443371 + 1786998441085335);
    //     assertEq(R.tokenY.cumulativeEarnedPerMLiq, 219386832 + 361);
    //     assertEq(R.tokenY.subtreecumulativeEarnedPerMLiq, 552484409781 + 911603);

    //     // RR
    //     // 765e18 * 2352954287417905205553 / 324091721 / 2**64
    //     // 2519e18 * 2352954287417905205553 / 324091721 / 2**64
    //     // 99763e6 * 6117681147286553534438 / 324091721 / 2**64
    //     // 889059e6 * 6117681147286553534438 / 324091721 / 2**64
    //     assertEq(RR.tokenX.cumulativeEarnedPerMLiq, 2108110694023652835 + 301083714644757);
    //     assertEq(RR.tokenX.subtreecumulativeEarnedPerMLiq, 4185908685257423082 + 991411604170121);
    //     assertEq(RR.tokenY.cumulativeEarnedPerMLiq, 62011632404 + 102086);
    //     assertEq(RR.tokenY.subtreecumulativeEarnedPerMLiq, 552008141912 + 909766);

    //     // RL
    //     // 1024e18 * 2352954287417905205553 / 39672 / 2**64
    //     // 1024e18 * 2352954287417905205553 / 39672 / 2**64
    //     // 1552e6 * 6117681147286553534438 / 39672 / 2**64
    //     // 1552e6 * 6117681147286553534438 / 39672 / 2**64
    //     assertEq(RL.tokenX.cumulativeEarnedPerMLiq, 423621837838722923425 + 3292377527956539412);
    //     assertEq(RL.tokenX.subtreecumulativeEarnedPerMLiq, 423621837838722923425 + 3292377527956539412);
    //     assertEq(RL.tokenY.cumulativeEarnedPerMLiq, 2197359621190 + 12974025);
    //     assertEq(RL.tokenY.subtreecumulativeEarnedPerMLiq, 2197359621190 + 12974025);

    //     // RRL
    //     // 53e18 * 2352954287417905205553 / 305908639 / 2**64
    //     // 1754e18 * 2352954287417905205553 / 305908639 / 2**64
    //     // 8765e6 * 6117681147286553534438 / 305908639 / 2**64
    //     // 789296e6 * 6117681147286553534438 / 305908639 / 2**64
    //     assertEq(RRL.tokenX.cumulativeEarnedPerMLiq, 154733312657952738 + 22099268330799);
    //     assertEq(RRL.tokenX.subtreecumulativeEarnedPerMLiq, 2201300334794271053 + 731360691551353);
    //     assertEq(RRL.tokenY.cumulativeEarnedPerMLiq, 5772069627 + 9502);
    //     assertEq(RRL.tokenY.subtreecumulativeEarnedPerMLiq, 519121437518 + 855687);

    //     // RRLL
    //     // 1701e18 * 2352954287417905205553 / 296771752 / 2**64
    //     // 1701e18 * 2352954287417905205553 / 296771752 / 2**64
    //     // 780531e6 * 6117681147286553534438 / 296771752 / 2**64
    //     // 780531e6 * 6117681147286553534438 / 296771752 / 2**64
    //     assertEq(RRLL.tokenX.cumulativeEarnedPerMLiq, 2109575308294031901 + 731097873063750);
    //     assertEq(RRLL.tokenX.subtreecumulativeEarnedPerMLiq, 2109575308294031901 + 731097873063750);
    //     assertEq(RRLL.tokenY.cumulativeEarnedPerMLiq, 529154012121 + 872237);
    //     assertEq(RRLL.tokenY.subtreecumulativeEarnedPerMLiq, 529154012121 + 872237);

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