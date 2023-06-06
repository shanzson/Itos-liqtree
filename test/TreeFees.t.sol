// SPDX-License-Identifier: BSL-1.1
pragma solidity ^0.8.18;

import { console } from "forge-std/console.sol";
import { Test } from "forge-std/Test.sol";

import { LiqTree, LiqTreeImpl, LiqRange, LKey, LKeyImpl, LiqNode } from "src/Tree.sol";

/** 
 * Fees are calculated in the liquidity tree using the following formulas:
 *
 *      nodeEarn += N.borrow * r / totalMLiq
 *      nodeSubtreeEarn += N.subtreeBorrow * r / totalMLiq
 *      totalMLq = N.subtreeMLiq + A[] * N.range
 *
 * For these tests, we will first isolate each variable. 
 * Computing tests over the 4 types of path traversals.
 * Then we will test them together
 */
contract TreeFeeTest is Test {
    LiqTree public liqTree;
    using LiqTreeImpl for LiqTree;
    using LKeyImpl for LKey;
    
    function setUp() public {
        // A depth of 4 creates a tree that covers an absolute range of 16 ([0, 15];);. 
        // ie. A complete tree matching the ascii documentation. 
        liqTree.init(4);
    }

    // Borrow

    function testBorrowAtRootNode() public {
        liqTree.addWideRangeMLiq(900);
        liqTree.addWideRangeTLiq(200, 57e18, 290e6);
        liqTree.removeWideRangeTLiq(50, 10e18, 1e6);

        LiqNode storage root = liqTree.nodes[liqTree.root];
        assertEq(root.tokenX.borrow, 47e18);
        assertEq(root.tokenY.borrow, 289e6);

        // other borrows should be empty
    }

    function testBorrowAtSingleNode() public {
        liqTree.addMLiq(LiqRange(0, 3), 500);
        liqTree.addTLiq(LiqRange(0, 3), 400, 43e18, 12e6);
        liqTree.removeTLiq(LiqRange(0, 3), 20, 20e18, 10e6);

        LiqNode storage zeroThree = liqTree.nodes[LKey.wrap(4 << 24 | 16)];
        assertEq(zeroThree.tokenX.borrow, 23e18);
        assertEq(zeroThree.tokenY.borrow, 2e6);

        // other borrows should be empty
    } 

    function testBorrowAtLeafNode() public {
        liqTree.addMLiq(LiqRange(3, 3), 100);
        liqTree.addTLiq(LiqRange(3, 3), 20, 22e18, 29e6);
        liqTree.removeTLiq(LiqRange(3, 3), 20, 20e18, 20e6);

        LiqNode storage threeThree = liqTree.nodes[LKey.wrap(1 << 24 | 19)];
        assertEq(threeThree.tokenX.borrow, 2e18);
        assertEq(threeThree.tokenY.borrow, 9e6);

        // other borrows should be empty
    }

    function testBorrowSplitAcrossSeveralNodesWalkingLeftLeg() public {
        // 1-7 => Nodes: 1-1, 2-3, 4-7 
        // 2nd traversal type, only left leg

        liqTree.addMLiq(LiqRange(1, 7), 100);
        liqTree.addTLiq(LiqRange(1, 7), 20, 12e18, 19e6);
        liqTree.removeTLiq(LiqRange(1, 7), 20, 10e18, 10e6);

        LiqNode storage oneOne = liqTree.nodes[LKey.wrap(1 << 24 | 17)];
        LiqNode storage twoThree = liqTree.nodes[LKey.wrap(2 << 24 | 18)];
        LiqNode storage fourSeven = liqTree.nodes[LKey.wrap(4 << 24 | 20)];

        // 1-1
        assertEq(oneOne.tokenX.borrow, 285714285714285714); // 2e18/7*1 = 285714285714285714.285714285714285714285714285714285714285714
        assertEq(oneOne.tokenY.borrow, 1285714);  // 9e6/7*1 = 1285714.2857142857142857142857142857142857142857142857142857142857142857142857142857142857142857142857142857142

        // 2-3
        assertEq(twoThree.tokenX.borrow, 571428571428571428); // 2e18/7*2 = 571428571428571428.571428571428571428571428571428571428571428
        assertEq(twoThree.tokenY.borrow, 2571428); // 9e6/7*2 = 2571428.57142857142857142857142857142857142857142857142857142

        // 4-7
        // x: 2e18/7 = 285714285714285714.285714285714285714285714285714285714285714
        //   floor() = 285714285714285714 * 4 = 1142857142857142856
        // y: 9e6/7  = 1285714.28571428571428571428571428571428571428571428571428571
        //   floor() = 1285714 * 4 = 5142856
        assertEq(fourSeven.tokenX.borrow, 1142857142857142856); // 2e18/7*4 = 1142857142857142857.14285714285714285714285714285714285714285 (1 wei lost in rounding)
        assertEq(fourSeven.tokenY.borrow, 5142856); // 9e6/7*4 = 5142857.14285714285714285714285714285714285714285714285714285 (1 wei lost in rounding)

        // other borrows should be empty
    }

    function testBorrowSplitAcrossSeveralNodesWalkingBothLegsBelowPeak() public {
        // 1-2 => Node: 1-1, 2-2
        // 1st traversal type, both legs below peak

        liqTree.addMLiq(LiqRange(1, 2), 100);
        liqTree.addTLiq(LiqRange(1, 2), 20, 74e18, 21e6);
        liqTree.removeTLiq(LiqRange(1, 2), 20, 2e18, 2e6);

        LiqNode storage oneOne = liqTree.nodes[LKey.wrap(1 << 24 | 17)];
        LiqNode storage twoTwo = liqTree.nodes[LKey.wrap(1 << 24 | 18)];

        // 1-1
        assertEq(oneOne.tokenX.borrow, 36000000000000000000); // 72e18/2*1 = 36000000000000000000
        assertEq(oneOne.tokenY.borrow, 9500000);  // 19e6/2*1 = 9500000

        // 2-2
        assertEq(twoTwo.tokenX.borrow, 36000000000000000000); 
        assertEq(twoTwo.tokenY.borrow, 9500000);

    }

    function testBorrowSplitAcrossSeveralNodesWalkingRightLeg() public {
        // 8-14 => Node: 8-11, 12-13, 14-14
        // 3rd traversal type, only right leg

        liqTree.addMLiq(LiqRange(8, 14), 100);
        liqTree.addTLiq(LiqRange(8, 14), 20, 474e18, 220e6);
        liqTree.removeTLiq(LiqRange(8, 14), 20, 2e18, 1e6);

        LiqNode storage eightEleven = liqTree.nodes[LKey.wrap(4 << 24 | 24)];
        LiqNode storage twelveThirteen = liqTree.nodes[LKey.wrap(2 << 24 | 28)];
        LiqNode storage fourteenFourteen = liqTree.nodes[LKey.wrap(1 << 24 | 30)];

        // 8-11
        // x: floor(472e18/7) = 67428571428571428571 * 4 = 269714285714285714284
        // y: floor(219e6/7) = 31285714 * 4 = 125142856
        assertEq(eightEleven.tokenX.borrow, 269714285714285714284); // 472e18/7*4 = 269714285714285714285.714285714285714285714285714285714285714 (1 wei lost)
        assertEq(eightEleven.tokenY.borrow, 125142856);  // 219e6/7*4 = 125142857.142857142857142857142857142857142857142857142857142 (1 wei lost)

        // 12-13
        // x: floor(472e18/7) * 2 = 134857142857142857142
        // y: floor(219e6/7) * 2 = 62571428
        assertEq(twelveThirteen.tokenX.borrow, 134857142857142857142); // 472e18/7*2 = 134857142857142857142.857142857142857142857142857142857142857
        assertEq(twelveThirteen.tokenY.borrow, 62571428);  // 219e6/7*2 = 62571428.5714285714285714285714285714285714285714285714285714

        // 14-14
        // x: floor(472e18/7) * 1 = 67428571428571428571
        // y: floor(219e6/7) * 1 = 31285714
        assertEq(fourteenFourteen.tokenX.borrow, 67428571428571428571); // 472e18/7*1 = 67428571428571428571.4285714285714285714285714285714285714285
        assertEq(fourteenFourteen.tokenY.borrow, 31285714); // 219e6/7*1 = 31285714.2857142857142857142857142857142857142857142857142857
    }

    function testBorrowSplitAcrossSeveralNodesWalkingBothLegsAtOrAbovePeak() public {
        // 8-15 => Node: 8-15
        // 4th traversal type, both legs at or above peak

        liqTree.addMLiq(LiqRange(8, 15), 100);
        liqTree.addTLiq(LiqRange(8, 15), 20, 1473e18, 5220e6);
        liqTree.removeTLiq(LiqRange(8, 15), 20, 1e18, 1e6);

        LiqNode storage eightFifteen = liqTree.nodes[LKey.wrap(8 << 24 | 24)];

        // 8-15
        // x: floor(1472e18/8) * 8 = 1472e18
        // y: floor(5219e6/8) * 8 = 5219e6
        assertEq(eightFifteen.tokenX.borrow, 1472e18);
        assertEq(eightFifteen.tokenY.borrow, 5219e6);
    }

    // Subtree Borrow

    // BROKEN
    function testSubtreeBorrowAtRootNode() public {
        liqTree.addWideRangeMLiq(900);
        liqTree.addWideRangeTLiq(200, 57e18, 290e6);
        liqTree.removeWideRangeTLiq(50, 10e18, 1e6);

        liqTree.addMLiq(LiqRange(4, 7), 100);
        liqTree.addTLiq(LiqRange(4, 7), 10, 200e18, 200e6);
        // liqTree.removeTLiq(LiqRange(4, 7), 10, 100e18, 100e6);

        LiqNode storage root = liqTree.nodes[liqTree.root];
        assertEq(root.tokenX.subtreeBorrow, 247e18);
        assertEq(root.tokenY.subtreeBorrow, 489e6);

        // (almost all other) borrows should be empty
    }

    function testSubtreeBorrowAtSingleNode() public {
        liqTree.addMLiq(LiqRange(0, 3), 500);
        liqTree.addTLiq(LiqRange(0, 3), 400, 43e18, 12e6);
        liqTree.removeTLiq(LiqRange(0, 3), 20, 20e18, 10e6);

        LiqNode storage zeroThree = liqTree.nodes[LKey.wrap(4 << 24 | 16)];
        assertEq(zeroThree.tokenX.subtreeBorrow, 23e18);
        assertEq(zeroThree.tokenY.subtreeBorrow, 2e6);

        // nodes above should include this amount

        // 0-7
        LiqNode storage zeroSeven = liqTree.nodes[LKey.wrap(8 << 24 | 16)];
        assertEq(zeroSeven.tokenX.subtreeBorrow, 23e18);
        assertEq(zeroSeven.tokenY.subtreeBorrow, 2e6);

        // 0-15
        LiqNode storage zeroFifteen = liqTree.nodes[liqTree.root];
        assertEq(zeroFifteen.tokenX.subtreeBorrow, 23e18);
        assertEq(zeroFifteen.tokenY.subtreeBorrow, 2e6);
        
        // other borrows should be empty
    } 

    function testSubtreeBorrowAtLeafNode() public {
        liqTree.addMLiq(LiqRange(3, 3), 100);
        liqTree.addTLiq(LiqRange(3, 3), 20, 22e18, 29e6);
        liqTree.removeTLiq(LiqRange(3, 3), 20, 20e18, 20e6);

        LiqNode storage threeThree = liqTree.nodes[LKey.wrap(1 << 24 | 19)];
        assertEq(threeThree.tokenX.subtreeBorrow, 2e18);
        assertEq(threeThree.tokenY.subtreeBorrow, 9e6);

        // nodes above should include this amount

        // 2-3
        LiqNode storage twoThree = liqTree.nodes[LKey.wrap(2 << 24 | 18)];
        assertEq(twoThree.tokenX.subtreeBorrow, 2e18);
        assertEq(twoThree.tokenY.subtreeBorrow, 9e6);

        // 0-3
        LiqNode storage zeroThree = liqTree.nodes[LKey.wrap(4 << 24 | 16)];
        assertEq(zeroThree.tokenX.subtreeBorrow, 2e18);
        assertEq(zeroThree.tokenY.subtreeBorrow, 9e6);

        // 0-7
        LiqNode storage zeroSeven = liqTree.nodes[LKey.wrap(8 << 24 | 16)];
        assertEq(zeroSeven.tokenX.subtreeBorrow, 2e18);
        assertEq(zeroSeven.tokenY.subtreeBorrow, 9e6);

        // 0-15
        LiqNode storage zeroFifteen = liqTree.nodes[liqTree.root];
        assertEq(zeroFifteen.tokenX.subtreeBorrow, 2e18);
        assertEq(zeroFifteen.tokenY.subtreeBorrow, 9e6);

        // other borrows should be empty
    }

    function testSubtreeBorrowSplitAcrossSeveralNodesWalkingLeftLeg() public {
        // 1-7 => Nodes: 1-1, 2-3, 4-7 
        // 2nd traversal type, only left leg

        liqTree.addMLiq(LiqRange(1, 7), 100);
        liqTree.addTLiq(LiqRange(1, 7), 20, 12e18, 19e6);
        liqTree.removeTLiq(LiqRange(1, 7), 20, 10e18, 10e6);

        LiqNode storage oneOne = liqTree.nodes[LKey.wrap(1 << 24 | 17)];
        LiqNode storage twoThree = liqTree.nodes[LKey.wrap(2 << 24 | 18)];
        LiqNode storage fourSeven = liqTree.nodes[LKey.wrap(4 << 24 | 20)];

        // 1-1
        assertEq(oneOne.tokenX.borrow, 285714285714285714); // 2e18/7*1 = 285714285714285714.285714285714285714285714285714285714285714
        assertEq(oneOne.tokenY.borrow, 1285714);  // 9e6/7*1 = 1285714.2857142857142857142857142857142857142857142857142857142857142857142857142857142857142857142857142857142

        // 2-3
        assertEq(twoThree.tokenX.borrow, 571428571428571428); // 2e18/7*2 = 571428571428571428.571428571428571428571428571428571428571428
        assertEq(twoThree.tokenY.borrow, 2571428); // 9e6/7*2 = 2571428.57142857142857142857142857142857142857142857142857142

        // 4-7
        // x: 2e18/7 = 285714285714285714.285714285714285714285714285714285714285714
        //   floor() = 285714285714285714 * 4 = 1142857142857142856
        // y: 9e6/7  = 1285714.28571428571428571428571428571428571428571428571428571
        //   floor() = 1285714 * 4 = 5142856
        assertEq(fourSeven.tokenX.borrow, 1142857142857142856); // 2e18/7*4 = 1142857142857142857.14285714285714285714285714285714285714285 (1 wei lost in rounding)
        assertEq(fourSeven.tokenY.borrow, 5142856); // 9e6/7*4 = 5142857.14285714285714285714285714285714285714285714285714285 (1 wei lost in rounding)

        // other borrows should be empty
    }

    function testSubtreeBorrowSplitAcrossSeveralNodesWalkingBothLegsBelowPeak() public {
        // 1-2 => Node: 1-1, 2-2
        // 1st traversal type, both legs below peak

        liqTree.addMLiq(LiqRange(1, 2), 100);
        liqTree.addTLiq(LiqRange(1, 2), 20, 74e18, 21e6);
        liqTree.removeTLiq(LiqRange(1, 2), 20, 2e18, 2e6);

        LiqNode storage oneOne = liqTree.nodes[LKey.wrap(1 << 24 | 17)];
        LiqNode storage twoTwo = liqTree.nodes[LKey.wrap(1 << 24 | 18)];

        // 1-1
        assertEq(oneOne.tokenX.borrow, 36000000000000000000); // 72e18/2*1 = 36000000000000000000
        assertEq(oneOne.tokenY.borrow, 9500000);  // 19e6/2*1 = 9500000

        // 2-2
        assertEq(twoTwo.tokenX.borrow, 36000000000000000000); 
        assertEq(twoTwo.tokenY.borrow, 9500000);

    }

    function testSubtreeBorrowSplitAcrossSeveralNodesWalkingRightLeg() public {
        // 8-14 => Node: 8-11, 12-13, 14-14
        // 3rd traversal type, only right leg

        liqTree.addMLiq(LiqRange(8, 14), 100);
        liqTree.addTLiq(LiqRange(8, 14), 20, 474e18, 220e6);
        liqTree.removeTLiq(LiqRange(8, 14), 20, 2e18, 1e6);

        LiqNode storage eightEleven = liqTree.nodes[LKey.wrap(4 << 24 | 24)];
        LiqNode storage twelveThirteen = liqTree.nodes[LKey.wrap(2 << 24 | 28)];
        LiqNode storage fourteenFourteen = liqTree.nodes[LKey.wrap(1 << 24 | 30)];

        // 8-11
        // x: floor(472e18/7) = 67428571428571428571 * 4 = 269714285714285714284
        // y: floor(219e6/7) = 31285714 * 4 = 125142856
        assertEq(eightEleven.tokenX.borrow, 269714285714285714284); // 472e18/7*4 = 269714285714285714285.714285714285714285714285714285714285714 (1 wei lost)
        assertEq(eightEleven.tokenY.borrow, 125142856);  // 219e6/7*4 = 125142857.142857142857142857142857142857142857142857142857142 (1 wei lost)

        // 12-13
        // x: floor(472e18/7) * 2 = 134857142857142857142
        // y: floor(219e6/7) * 2 = 62571428
        assertEq(twelveThirteen.tokenX.borrow, 134857142857142857142); // 472e18/7*2 = 134857142857142857142.857142857142857142857142857142857142857
        assertEq(twelveThirteen.tokenY.borrow, 62571428);  // 219e6/7*2 = 62571428.5714285714285714285714285714285714285714285714285714

        // 14-14
        // x: floor(472e18/7) * 1 = 67428571428571428571
        // y: floor(219e6/7) * 1 = 31285714
        assertEq(fourteenFourteen.tokenX.borrow, 67428571428571428571); // 472e18/7*1 = 67428571428571428571.4285714285714285714285714285714285714285
        assertEq(fourteenFourteen.tokenY.borrow, 31285714); // 219e6/7*1 = 31285714.2857142857142857142857142857142857142857142857142857
    }

    function testSubtreeBorrowSplitAcrossSeveralNodesWalkingBothLegsAtOrAbovePeak() public {
        // 8-15 => Node: 8-15
        // 4th traversal type, both legs at or above peak

        liqTree.addMLiq(LiqRange(8, 15), 100);
        liqTree.addTLiq(LiqRange(8, 15), 20, 1473e18, 5220e6);
        liqTree.removeTLiq(LiqRange(8, 15), 20, 1e18, 1e6);

        LiqNode storage eightFifteen = liqTree.nodes[LKey.wrap(8 << 24 | 24)];

        // 8-15
        // x: floor(1472e18/8) * 8 = 1472e18
        // y: floor(5219e6/8) * 8 = 5219e6
        assertEq(eightFifteen.tokenX.borrow, 1472e18);
        assertEq(eightFifteen.tokenY.borrow, 5219e6);
    }



    // subtreeMLiq

    // A[]

    // N.range

    // r
}