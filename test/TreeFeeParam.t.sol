// SPDX-License-Identifier: BSL-1.1
pragma solidity ^0.8.18;

import { console } from "forge-std/console.sol";
import { Test } from "forge-std/Test.sol";

import { LiqTree, LiqTreeImpl, LiqRange, LKey, LKeyImpl, LiqNode, FeeSnap } from "src/Tree.sol";

// solhint-disable

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
contract TreeFeeParamTest is Test {
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

    // Borrow

    function testBorrowAtRootNode() public {
        FeeSnap memory fees;
        liqTree.addWideRangeMLiq(900, fees);
        liqTree.addWideRangeTLiq(200, fees, 57e18, 290e6);
        liqTree.removeWideRangeTLiq(50, fees, 10e18, 1e6);

        LiqNode storage root = liqTree.nodes[liqTree.root];
        assertEq(root.tokenX.borrow, 47e18);
        assertEq(root.tokenY.borrow, 289e6);

        // other borrows should be empty
    }

    function testBorrowAtSingleNode() public {
        FeeSnap memory fees;
        liqTree.addMLiq(range(0, 3), 500, fees);
        liqTree.addTLiq(range(0, 3), 400, fees, 43e18, 12e6);
        liqTree.removeTLiq(range(0, 3), 20, fees, 20e18, 10e6);

        LiqNode storage zeroThree = liqTree.nodes[LKey.wrap((4 << 24) | 0)];
        assertEq(zeroThree.tokenX.borrow, 23e18);
        assertEq(zeroThree.tokenY.borrow, 2e6);

        // other borrows should be empty
    }

    function testBorrowAtLeafNode() public {
        FeeSnap memory fees;
        liqTree.addMLiq(range(3, 3), 100, fees);
        liqTree.addTLiq(range(3, 3), 20, fees, 22e18, 29e6);
        liqTree.removeTLiq(range(3, 3), 20, fees, 20e18, 20e6);

        LiqNode storage threeThree = liqTree.nodes[LKey.wrap((1 << 24) | 3)];
        assertEq(threeThree.tokenX.borrow, 2e18);
        assertEq(threeThree.tokenY.borrow, 9e6);

        // other borrows should be empty
    }

    function testBorrowSplitAcrossSeveralNodesWalkingLeftLeg() public {
        FeeSnap memory fees;
        // 1-7 => Nodes: 1-1, 2-3, 4-7
        // 2nd traversal type, only left leg

        liqTree.addMLiq(range(1, 7), 100, fees);
        liqTree.addTLiq(range(1, 7), 20, fees, 12e18, 19e6);
        liqTree.removeTLiq(range(1, 7), 20, fees, 10e18, 10e6);

        LiqNode storage oneOne = liqTree.nodes[LKey.wrap((1 << 24) | 1)];
        LiqNode storage twoThree = liqTree.nodes[LKey.wrap((2 << 24) | 2)];
        LiqNode storage fourSeven = liqTree.nodes[LKey.wrap((4 << 24) | 4)];

        // 1-1
        assertEq(oneOne.tokenX.borrow, 285714285714285714); // 2e18/7*1 = 285714285714285714.285714285714285714285714285714285714285714
        assertEq(oneOne.tokenY.borrow, 1285714); // 9e6/7*1 = 1285714.2857142857142857142857142857142857142857142857142857142857142857142857142857142857142857142857142857142

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
        FeeSnap memory fees;

        liqTree.addMLiq(range(1, 2), 100, fees);
        liqTree.addTLiq(range(1, 2), 20, fees, 74e18, 21e6);
        liqTree.removeTLiq(range(1, 2), 20, fees, 2e18, 2e6);

        LiqNode storage oneOne = liqTree.nodes[LKey.wrap((1 << 24) | 1)];
        LiqNode storage twoTwo = liqTree.nodes[LKey.wrap((1 << 24) | 2)];

        // 1-1
        assertEq(oneOne.tokenX.borrow, 36000000000000000000); // 72e18/2*1 = 36000000000000000000
        assertEq(oneOne.tokenY.borrow, 9500000); // 19e6/2*1 = 9500000

        // 2-2
        assertEq(twoTwo.tokenX.borrow, 36000000000000000000);
        assertEq(twoTwo.tokenY.borrow, 9500000);
    }

    function testBorrowSplitAcrossSeveralNodesWalkingRightLeg() public {
        // 8-14 => Node: 8-11, 12-13, 14-14
        // 3rd traversal type, only right leg
        FeeSnap memory fees;

        liqTree.addMLiq(range(8, 14), 100, fees);
        liqTree.addTLiq(range(8, 14), 20, fees, 474e18, 220e6);
        liqTree.removeTLiq(range(8, 14), 20, fees, 2e18, 1e6);

        LiqNode storage eightEleven = liqTree.nodes[LKey.wrap((4 << 24) | 8)];
        LiqNode storage twelveThirteen = liqTree.nodes[LKey.wrap((2 << 24) | 12)];
        LiqNode storage fourteenFourteen = liqTree.nodes[LKey.wrap((1 << 24) | 14)];

        // 8-11
        // x: floor(472e18/7) = 67428571428571428571 * 4 = 269714285714285714284
        // y: floor(219e6/7) = 31285714 * 4 = 125142856
        assertEq(eightEleven.tokenX.borrow, 269714285714285714284); // 472e18/7*4 = 269714285714285714285.714285714285714285714285714285714285714 (1 wei lost)
        assertEq(eightEleven.tokenY.borrow, 125142856); // 219e6/7*4 = 125142857.142857142857142857142857142857142857142857142857142 (1 wei lost)

        // 12-13
        // x: floor(472e18/7) * 2 = 134857142857142857142
        // y: floor(219e6/7) * 2 = 62571428
        assertEq(twelveThirteen.tokenX.borrow, 134857142857142857142); // 472e18/7*2 = 134857142857142857142.857142857142857142857142857142857142857
        assertEq(twelveThirteen.tokenY.borrow, 62571428); // 219e6/7*2 = 62571428.5714285714285714285714285714285714285714285714285714

        // 14-14
        // x: floor(472e18/7) * 1 = 67428571428571428571
        // y: floor(219e6/7) * 1 = 31285714
        assertEq(fourteenFourteen.tokenX.borrow, 67428571428571428571); // 472e18/7*1 = 67428571428571428571.4285714285714285714285714285714285714285
        assertEq(fourteenFourteen.tokenY.borrow, 31285714); // 219e6/7*1 = 31285714.2857142857142857142857142857142857142857142857142857
    }

    function testBorrowSplitAcrossSeveralNodesWalkingBothLegsAtOrAbovePeak() public {
        // 8-15 => Node: 8-15
        // 4th traversal type, both legs at or above peak
        FeeSnap memory fees;

        liqTree.addMLiq(range(8, 15), 100, fees);
        liqTree.addTLiq(range(8, 15), 20, fees, 1473e18, 5220e6);
        liqTree.removeTLiq(range(8, 15), 20, fees, 1e18, 1e6);

        LiqNode storage eightFifteen = liqTree.nodes[LKey.wrap((8 << 24) | 8)];

        // 8-15
        // x: floor(1472e18/8) * 8 = 1472e18
        // y: floor(5219e6/8) * 8 = 5219e6
        assertEq(eightFifteen.tokenX.borrow, 1472e18);
        assertEq(eightFifteen.tokenY.borrow, 5219e6);
    }

    // Subtree Borrow

    function testSubtreeBorrowAtRootNode() public {
        FeeSnap memory fees;

        liqTree.addWideRangeMLiq(900, fees);
        liqTree.addWideRangeTLiq(200, fees, 57e18, 290e6);
        liqTree.removeWideRangeTLiq(50, fees, 10e18, 1e6);

        liqTree.addMLiq(range(4, 7), 100, fees);
        liqTree.addTLiq(range(4, 7), 10, fees, 200e18, 200e6);
        liqTree.removeTLiq(range(4, 7), 10, fees, 100e18, 100e6);

        LiqNode storage root = liqTree.nodes[liqTree.root];
        assertEq(root.tokenX.subtreeBorrow, 147e18);
        assertEq(root.tokenY.subtreeBorrow, 389e6);

        // (almost all other) borrows should be empty
    }

    function testSubtreeBorrowAtSingleNode() public {
        FeeSnap memory fees;

        liqTree.addMLiq(range(0, 3), 500, fees);
        liqTree.addTLiq(range(0, 3), 400, fees, 43e18, 12e6);
        liqTree.removeTLiq(range(0, 3), 20, fees, 20e18, 10e6);

        LiqNode storage zeroThree = liqTree.nodes[LKey.wrap((4 << 24) | 0)];
        assertEq(zeroThree.tokenX.subtreeBorrow, 23e18);
        assertEq(zeroThree.tokenY.subtreeBorrow, 2e6);

        // nodes above should include this amount

        // 0-7
        LiqNode storage zeroSeven = liqTree.nodes[LKey.wrap((8 << 24) | 0)];
        assertEq(zeroSeven.tokenX.subtreeBorrow, 23e18);
        assertEq(zeroSeven.tokenY.subtreeBorrow, 2e6);

        // 0-15
        LiqNode storage zeroFifteen = liqTree.nodes[liqTree.root];
        assertEq(zeroFifteen.tokenX.subtreeBorrow, 23e18);
        assertEq(zeroFifteen.tokenY.subtreeBorrow, 2e6);

        // other borrows should be empty
    }

    function testSubtreeBorrowAtLeafNode() public {
        FeeSnap memory fees;

        liqTree.addMLiq(range(3, 3), 100, fees);
        liqTree.addTLiq(range(3, 3), 20, fees, 22e18, 29e6);
        liqTree.removeTLiq(range(3, 3), 20, fees, 20e18, 20e6);

        LiqNode storage threeThree = liqTree.nodes[LKey.wrap((1 << 24) | 3)];
        assertEq(threeThree.tokenX.subtreeBorrow, 2e18);
        assertEq(threeThree.tokenY.subtreeBorrow, 9e6);

        // nodes above should include this amount

        // 2-3
        LiqNode storage twoThree = liqTree.nodes[LKey.wrap((2 << 24) | 2)];
        assertEq(twoThree.tokenX.subtreeBorrow, 2e18);
        assertEq(twoThree.tokenY.subtreeBorrow, 9e6);

        // 0-3
        LiqNode storage zeroThree = liqTree.nodes[LKey.wrap((4 << 24) | 0)];
        assertEq(zeroThree.tokenX.subtreeBorrow, 2e18);
        assertEq(zeroThree.tokenY.subtreeBorrow, 9e6);

        // 0-7
        LiqNode storage zeroSeven = liqTree.nodes[LKey.wrap((8 << 24) | 0)];
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
        FeeSnap memory fees;

        liqTree.addMLiq(range(1, 7), 100, fees);
        liqTree.addTLiq(range(1, 7), 20, fees, 12e18, 19e6);
        liqTree.removeTLiq(range(1, 7), 20, fees, 10e18, 10e6);

        LiqNode storage oneOne = liqTree.nodes[LKey.wrap((1 << 24) | 1)];
        LiqNode storage twoThree = liqTree.nodes[LKey.wrap((2 << 24) | 2)];
        LiqNode storage fourSeven = liqTree.nodes[LKey.wrap((4 << 24) | 4)];

        // 1-1
        assertEq(oneOne.tokenX.subtreeBorrow, 285714285714285714); // 2e18/7*1 = 285714285714285714.285714285714285714285714285714285714285714
        assertEq(oneOne.tokenY.subtreeBorrow, 1285714); // 9e6/7*1 = 1285714.2857142857142857142857142857142857142857142857142857142857142857142857142857142857142857142857142857142

        // 2-3
        assertEq(twoThree.tokenX.subtreeBorrow, 571428571428571428); // 2e18/7*2 = 571428571428571428.571428571428571428571428571428571428571428
        assertEq(twoThree.tokenY.subtreeBorrow, 2571428); // 9e6/7*2 = 2571428.57142857142857142857142857142857142857142857142857142

        // 4-7
        // x: 2e18/7 = 285714285714285714.285714285714285714285714285714285714285714
        //   floor() = 285714285714285714 * 4 = 1142857142857142856
        // y: 9e6/7  = 1285714.28571428571428571428571428571428571428571428571428571
        //   floor() = 1285714 * 4 = 5142856
        assertEq(fourSeven.tokenX.subtreeBorrow, 1142857142857142856); // 2e18/7*4 = 1142857142857142857.14285714285714285714285714285714285714285 (1 wei lost in rounding)
        assertEq(fourSeven.tokenY.subtreeBorrow, 5142856); // 9e6/7*4 = 5142857.14285714285714285714285714285714285714285714285714285 (1 wei lost in rounding)

        // nodes above should include this amount

        // 0-1 (from 1-1)
        LiqNode storage zeroOne = liqTree.nodes[LKey.wrap((2 << 24) | 0)];
        assertEq(zeroOne.tokenX.subtreeBorrow, 285714285714285714);
        assertEq(zeroOne.tokenY.subtreeBorrow, 1285714);

        // 0-3 (from 1-1 and 2-3)
        LiqNode storage zeroThree = liqTree.nodes[LKey.wrap((4 << 24) | 0)];
        assertEq(zeroThree.tokenX.subtreeBorrow, 857142857142857142); // 285714285714285714 + 571428571428571428 = 857142857142857142
        assertEq(zeroThree.tokenY.subtreeBorrow, 3857142); // 1285714 + 2571428 = 3857142

        // 0-7 (from 1-1, 2-3, and 4-7)
        LiqNode storage zeroSeven = liqTree.nodes[LKey.wrap((8 << 24) | 0)];
        assertEq(zeroSeven.tokenX.subtreeBorrow, 1999999999999999998); // 857142857142857142 + 1142857142857142856 = 1999999999999999998
        assertEq(zeroSeven.tokenY.subtreeBorrow, 8999998); // 3857142 + 5142856 = 8999998

        // 0-15 (from 1-1, 2-3, and 4-7)
        LiqNode storage zeroFifteen = liqTree.nodes[liqTree.root];
        assertEq(zeroFifteen.tokenX.subtreeBorrow, 1999999999999999998);
        assertEq(zeroFifteen.tokenY.subtreeBorrow, 8999998);

        // other borrows should be empty
    }

    function testSubtreeBorrowSplitAcrossSeveralNodesWalkingBothLegsBelowPeak() public {
        // 1-2 => Node: 1-1, 2-2
        // 1st traversal type, both legs below peak
        FeeSnap memory fees;

        liqTree.addMLiq(range(1, 2), 100, fees);
        liqTree.addTLiq(range(1, 2), 20, fees, 74e18, 21e6);
        liqTree.removeTLiq(range(1, 2), 20, fees, 2e18, 2e6);

        LiqNode storage oneOne = liqTree.nodes[LKey.wrap((1 << 24) | 1)];
        LiqNode storage twoTwo = liqTree.nodes[LKey.wrap((1 << 24) | 2)];

        // 1-1
        assertEq(oneOne.tokenX.subtreeBorrow, 36000000000000000000); // 72e18/2*1 = 36000000000000000000
        assertEq(oneOne.tokenY.subtreeBorrow, 9500000); // 19e6/2*1 = 9500000

        // 2-2
        assertEq(twoTwo.tokenX.subtreeBorrow, 36000000000000000000);
        assertEq(twoTwo.tokenY.subtreeBorrow, 9500000);

        // nodes above should include this amount

        // 0-1 (from 1-1)
        LiqNode storage zeroOne = liqTree.nodes[LKey.wrap((2 << 24) | 0)];
        assertEq(zeroOne.tokenX.subtreeBorrow, 36e18);
        assertEq(zeroOne.tokenY.subtreeBorrow, 9.5e6);

        // 2-3 (from 2-2)
        LiqNode storage twoThree = liqTree.nodes[LKey.wrap((2 << 24) | 2)];
        assertEq(twoThree.tokenX.subtreeBorrow, 36e18);
        assertEq(twoThree.tokenY.subtreeBorrow, 9.5e6);

        // 0-3 (from 1-1 and 2-2)
        LiqNode storage zeroThree = liqTree.nodes[LKey.wrap((4 << 24) | 0)];
        assertEq(zeroThree.tokenX.subtreeBorrow, 72e18);
        assertEq(zeroThree.tokenY.subtreeBorrow, 19e6);

        // 0-7 (from 1-1 and 2-2)
        LiqNode storage zeroSeven = liqTree.nodes[LKey.wrap((8 << 24) | 0)];
        assertEq(zeroSeven.tokenX.subtreeBorrow, 72e18);
        assertEq(zeroSeven.tokenY.subtreeBorrow, 19e6);

        // 0-15 (from 1-1 and 2-2)
        LiqNode storage zeroFifteen = liqTree.nodes[liqTree.root];
        assertEq(zeroFifteen.tokenX.subtreeBorrow, 72e18);
        assertEq(zeroFifteen.tokenY.subtreeBorrow, 19e6);

        // all other nodes should have 0
    }

    function testSubtreeBorrowSplitAcrossSeveralNodesWalkingRightLeg() public {
        // 8-14 => Node: 8-11, 12-13, 14-14
        // 3rd traversal type, only right leg
        FeeSnap memory fees;

        liqTree.addMLiq(range(8, 14), 100, fees);
        liqTree.addTLiq(range(8, 14), 20, fees, 474e18, 220e6);
        liqTree.removeTLiq(range(8, 14), 20, fees, 2e18, 1e6);

        LiqNode storage eightEleven = liqTree.nodes[LKey.wrap((4 << 24) | 8)];
        LiqNode storage twelveThirteen = liqTree.nodes[LKey.wrap((2 << 24) | 12)];
        LiqNode storage fourteenFourteen = liqTree.nodes[LKey.wrap((1 << 24) | 14)];

        // 8-11
        // x: floor(472e18/7) = 67428571428571428571 * 4 = 269714285714285714284
        // y: floor(219e6/7) = 31285714 * 4 = 125142856
        assertEq(eightEleven.tokenX.subtreeBorrow, 269714285714285714284); // 472e18/7*4 = 269714285714285714285.714285714285714285714285714285714285714 (1 wei lost)
        assertEq(eightEleven.tokenY.subtreeBorrow, 125142856); // 219e6/7*4 = 125142857.142857142857142857142857142857142857142857142857142 (1 wei lost)

        // 12-13
        // x: floor(472e18/7) * 2 = 134857142857142857142
        // y: floor(219e6/7) * 2 = 62571428
        assertEq(twelveThirteen.tokenX.subtreeBorrow, 134857142857142857142); // 472e18/7*2 = 134857142857142857142.857142857142857142857142857142857142857
        assertEq(twelveThirteen.tokenY.subtreeBorrow, 62571428); // 219e6/7*2 = 62571428.5714285714285714285714285714285714285714285714285714

        // 14-14
        // x: floor(472e18/7) * 1 = 67428571428571428571
        // y: floor(219e6/7) * 1 = 31285714
        assertEq(fourteenFourteen.tokenX.subtreeBorrow, 67428571428571428571); // 472e18/7*1 = 67428571428571428571.4285714285714285714285714285714285714285
        assertEq(fourteenFourteen.tokenY.subtreeBorrow, 31285714); // 219e6/7*1 = 31285714.2857142857142857142857142857142857142857142857142857

        // nodes above should include this amount

        // 14-15 (from 14-14)
        LiqNode storage fourteenFifteen = liqTree.nodes[LKey.wrap((2 << 24) | 14)];
        assertEq(fourteenFifteen.tokenX.subtreeBorrow, 67428571428571428571);
        assertEq(fourteenFifteen.tokenY.subtreeBorrow, 31285714);

        // 12-15 (from 12-13 and 14-14)
        LiqNode storage tweleveFifteen = liqTree.nodes[LKey.wrap((4 << 24) | 12)];
        assertEq(tweleveFifteen.tokenX.subtreeBorrow, 202285714285714285713); // 67428571428571428571 + 134857142857142857142 = 202285714285714285713
        assertEq(tweleveFifteen.tokenY.subtreeBorrow, 93857142); // 31285714 + 62571428 = 93857142

        // 8-15 (from 8-11, 12-13, and 14-14)
        LiqNode storage eightFifteen = liqTree.nodes[LKey.wrap((8 << 24) | 8)];
        assertEq(eightFifteen.tokenX.subtreeBorrow, 471999999999999999997); // 202285714285714285713 + 269714285714285714284 = 471999999999999999997
        assertEq(eightFifteen.tokenY.subtreeBorrow, 218999998); // 93857142 + 125142856 = 218999998

        // 0-15 (from 8-11, 12-13, and 14-14)
        LiqNode storage zeroFifteen = liqTree.nodes[liqTree.root];
        assertEq(zeroFifteen.tokenX.subtreeBorrow, 471999999999999999997);
        assertEq(zeroFifteen.tokenY.subtreeBorrow, 218999998);

        // all other nodes should have 0
    }

    function testSubtreeBorrowSplitAcrossSeveralNodesWalkingBothLegsAtOrAbovePeak() public {
        // 8-15 => Node: 8-15
        // 4th traversal type, both legs at or above peak
        FeeSnap memory fees;

        liqTree.addMLiq(range(8, 15), 100, fees);
        liqTree.addTLiq(range(8, 15), 20, fees, 1473e18, 5220e6);
        liqTree.removeTLiq(range(8, 15), 20, fees, 1e18, 1e6);

        LiqNode storage eightFifteen = liqTree.nodes[LKey.wrap((8 << 24) | 8)];

        // 8-15
        // x: floor(1472e18/8) * 8 = 1472e18
        // y: floor(5219e6/8) * 8 = 5219e6
        assertEq(eightFifteen.tokenX.borrow, 1472e18);
        assertEq(eightFifteen.tokenY.borrow, 5219e6);

        // nodes above should include this amount

        // 0-15
        LiqNode storage zeroFifteen = liqTree.nodes[liqTree.root];
        assertEq(zeroFifteen.tokenX.subtreeBorrow, 1472e18);
        assertEq(zeroFifteen.tokenY.subtreeBorrow, 5219e6);

        // all other nodes should have 0
    }

    // subtreeMLiq

    // note: different from subtreeMLiq on the node
    function _calculateSubtreeMLiqForNode(LKey key) internal returns (uint256 subtreeMLiq) {
        (uint24 width, ) = key.explode();

        LiqNode storage node = liqTree.nodes[key];
        uint256 subtreeMLiqForNode = node.mLiq * width;
        if (width == 1) {
            return subtreeMLiqForNode;
        }

        (LKey left, LKey right) = key.children();
        return subtreeMLiqForNode + _calculateSubtreeMLiqForNode(left) + _calculateSubtreeMLiqForNode(right);
    }

    function testSubtreeMLiqAtSingleNode() public {
        FeeSnap memory fees;

        liqTree.addMLiq(range(0, 3), 500, fees);

        LKey key = LKey.wrap((4 << 24) | 0); // 0-3
        assertEq(_calculateSubtreeMLiqForNode(key), 2000); // 500*4
    }

    function testSubtreeMLiqAtLeafNode() public {
        FeeSnap memory fees;
        liqTree.addMLiq(range(3, 3), 100, fees);

        LKey key = LKey.wrap((1 << 24) | 3); // 3-3
        assertEq(_calculateSubtreeMLiqForNode(key), 100);
    }

    function testSubtreeMLiqForMLiqSplitAcrossSeveralNodesWalkingLeftLeg() public {
        // 1-7 => Nodes: 1-1, 2-3, 4-7
        // 2nd traversal type, only left leg
        FeeSnap memory fees;

        liqTree.addMLiq(range(1, 7), 200, fees);

        assertEq(_calculateSubtreeMLiqForNode(LKey.wrap((1 << 24) | 1)), 200); // 1-1
        assertEq(_calculateSubtreeMLiqForNode(LKey.wrap((2 << 24) | 2)), 400); // 2-3
        assertEq(_calculateSubtreeMLiqForNode(LKey.wrap((4 << 24) | 4)), 800); // 4-7

        assertEq(_calculateSubtreeMLiqForNode(LKey.wrap((2 << 24) | 0)), 200); // 0-1
        assertEq(_calculateSubtreeMLiqForNode(LKey.wrap((4 << 24) | 0)), 600); // 0-3
        assertEq(_calculateSubtreeMLiqForNode(LKey.wrap((8 << 24) | 0)), 1400); // 0-7
        assertEq(_calculateSubtreeMLiqForNode(liqTree.root), 1400); // 0-15
    }

    function testSubtreeMLiqForMLiqSplitAcrossSeveralNodesWalkingBothLegsBelowPeak() public {
        // 1-2 => Node: 1-1, 2-2
        // 1st traversal type, both legs below peak
        FeeSnap memory fees;
        liqTree.addMLiq(range(1, 2), 70, fees);

        assertEq(_calculateSubtreeMLiqForNode(LKey.wrap((1 << 24) | 1)), 70); // 1-1
        assertEq(_calculateSubtreeMLiqForNode(LKey.wrap((1 << 24) | 2)), 70); // 2-2

        assertEq(_calculateSubtreeMLiqForNode(LKey.wrap((2 << 24) | 0)), 70); // 0-1
        assertEq(_calculateSubtreeMLiqForNode(LKey.wrap((2 << 24) | 2)), 70); // 2-3
        assertEq(_calculateSubtreeMLiqForNode(LKey.wrap((4 << 24) | 0)), 140); // 0-3
        assertEq(_calculateSubtreeMLiqForNode(LKey.wrap((8 << 24) | 0)), 140); // 0-7
        assertEq(_calculateSubtreeMLiqForNode(liqTree.root), 140); // 0-15
    }

    function testSubtreeMLiqForMLiqSplitAcrossSeveralNodesWalkingRightLeg() public {
        // 8-14 => Node: 8-11, 12-13, 14-14
        // 3rd traversal type, only right leg
        FeeSnap memory fees;
        liqTree.addMLiq(range(8, 14), 9, fees);

        assertEq(_calculateSubtreeMLiqForNode(LKey.wrap((4 << 24) | 8)), 36); // 8-11
        assertEq(_calculateSubtreeMLiqForNode(LKey.wrap((2 << 24) | 12)), 18); // 12-13
        assertEq(_calculateSubtreeMLiqForNode(LKey.wrap((1 << 24) | 14)), 9); // 14-14

        assertEq(_calculateSubtreeMLiqForNode(LKey.wrap((2 << 24) | 14)), 9); // 14-15
        assertEq(_calculateSubtreeMLiqForNode(LKey.wrap((4 << 24) | 12)), 27); // 12-15
        assertEq(_calculateSubtreeMLiqForNode(LKey.wrap((8 << 24) | 8)), 63); // 8-15
        assertEq(_calculateSubtreeMLiqForNode(liqTree.root), 63); // 0-15
    }

    function testSubtreeMLiqForMLiqSplitAcrossSeveralNodesWalkingBothLegsAtOrAbovePeak() public {
        // 8-15 => Node: 8-15
        // 4th traversal type, both legs at or above peak
        FeeSnap memory fees;
        liqTree.addMLiq(range(8, 15), 100, fees);

        assertEq(_calculateSubtreeMLiqForNode(LKey.wrap((8 << 24) | 8)), 800); // 8-15
        assertEq(_calculateSubtreeMLiqForNode(liqTree.root), 800); // 0-15
    }

    // A[]

    // NOTE: Below section of tests have the following in common
    //  1. borrow and subtreeBorrow values will be the same
    //  2. the equation to split the borrow across nodes
    //      borrow / borrowRange * nodeRange
    //     will have borrowRange and nodeRange as the same values. Meaning we borrow at a single node.
    //  3. we assert against 3 only to show the result is not a multiple of 2.
    //  4. borrow will equal the range tested. Anything lower will result in 0, as the equation to split with division first causes the first term to truncate to zero
    //  5. r will be adjusted to counter the totalMLiq in the nodeEarn and nodeSubtreeEarn equations

    function _allocateAuxillaryArrays(FeeSnap memory fees) internal {
        // Allocate mLiq to each node, such that any combination of sums can only be one distinct set of nodes.
        // This way, when testing for the sum X, we know it must only be this unique set.
        // Lets use 1024, then add 1 for each node
        uint128 mLiq = 16384;
        liqTree.addWideRangeMLiq(mLiq, fees);

        for (int24 j = 1; j < 16; j *= 2) {
            mLiq = 1024 * uint24(j);
            for (int24 i = 0; i < 16; ) {
                liqTree.addMLiq(range(i, i + j - 1), mLiq, fees);
                i += j;
                mLiq += 1;
            }
        }
    }

    function testAuxAllocation() public {
        FeeSnap memory fees;
        _allocateAuxillaryArrays(fees);

        assertEq(liqTree.nodes[LKey.wrap((16 << 24) | 0)].mLiq, 16384);

        assertEq(liqTree.nodes[LKey.wrap((8 << 24) | 0)].mLiq, 8192);
        assertEq(liqTree.nodes[LKey.wrap((8 << 24) | 8)].mLiq, 8193);

        assertEq(liqTree.nodes[LKey.wrap((4 << 24) | 0)].mLiq, 4096);
        assertEq(liqTree.nodes[LKey.wrap((4 << 24) | 4)].mLiq, 4097);
        assertEq(liqTree.nodes[LKey.wrap((4 << 24) | 8)].mLiq, 4098);
        assertEq(liqTree.nodes[LKey.wrap((4 << 24) | 12)].mLiq, 4099);

        assertEq(liqTree.nodes[LKey.wrap((2 << 24) | 0)].mLiq, 2048);
        assertEq(liqTree.nodes[LKey.wrap((2 << 24) | 2)].mLiq, 2049);
        assertEq(liqTree.nodes[LKey.wrap((2 << 24) | 4)].mLiq, 2050);
        assertEq(liqTree.nodes[LKey.wrap((2 << 24) | 6)].mLiq, 2051);
        assertEq(liqTree.nodes[LKey.wrap((2 << 24) | 8)].mLiq, 2052);
        assertEq(liqTree.nodes[LKey.wrap((2 << 24) | 10)].mLiq, 2053);
        assertEq(liqTree.nodes[LKey.wrap((2 << 24) | 12)].mLiq, 2054);
        assertEq(liqTree.nodes[LKey.wrap((2 << 24) | 14)].mLiq, 2055);

        assertEq(liqTree.nodes[LKey.wrap((1 << 24) | 0)].mLiq, 1024);
        assertEq(liqTree.nodes[LKey.wrap((1 << 24) | 1)].mLiq, 1025);
        assertEq(liqTree.nodes[LKey.wrap((1 << 24) | 2)].mLiq, 1026);
        assertEq(liqTree.nodes[LKey.wrap((1 << 24) | 3)].mLiq, 1027);
        assertEq(liqTree.nodes[LKey.wrap((1 << 24) | 4)].mLiq, 1028);
        assertEq(liqTree.nodes[LKey.wrap((1 << 24) | 5)].mLiq, 1029);
        assertEq(liqTree.nodes[LKey.wrap((1 << 24) | 6)].mLiq, 1030);
        assertEq(liqTree.nodes[LKey.wrap((1 << 24) | 7)].mLiq, 1031);
        assertEq(liqTree.nodes[LKey.wrap((1 << 24) | 8)].mLiq, 1032);
        assertEq(liqTree.nodes[LKey.wrap((1 << 24) | 9)].mLiq, 1033);
        assertEq(liqTree.nodes[LKey.wrap((1 << 24) | 10)].mLiq, 1034);
        assertEq(liqTree.nodes[LKey.wrap((1 << 24) | 11)].mLiq, 1035);
        assertEq(liqTree.nodes[LKey.wrap((1 << 24) | 12)].mLiq, 1036);
        assertEq(liqTree.nodes[LKey.wrap((1 << 24) | 13)].mLiq, 1037);
        assertEq(liqTree.nodes[LKey.wrap((1 << 24) | 14)].mLiq, 1038);
        assertEq(liqTree.nodes[LKey.wrap((1 << 24) | 15)].mLiq, 1039);
    }

    function testAuxAtNodeOfRangeOne() public {
        FeeSnap memory fees;
        _allocateAuxillaryArrays(fees);

        LiqNode storage zeroZero = liqTree.nodes[LKey.wrap((1 << 24) | 0)];

        liqTree.addTLiq(range(0, 0), 100, fees, 1, 1);

        // A[] = 0-1.mliq + 0-3.mLiq + 0-7.mLiq + 0-15.mLiq
        //     = 2048 + 4096 + 8192 + 16384 = 30720
        // totalMLiq = 1024*1 + 30720*1 = 31744
        fees.X += 1756720331627508019494912;
        fees.Y += 1756720331627508019494912;

        liqTree.removeTLiq(range(0, 0), 100, fees, 1, 1);

        assertEq(zeroZero.tokenX.cumulativeEarnedPerMLiq >> 64, 3);
        assertEq(zeroZero.tokenX.subtreeCumulativeEarnedPerMLiq >> 64, 3);
        assertEq(zeroZero.tokenY.cumulativeEarnedPerMLiq >> 64, 3);
        assertEq(zeroZero.tokenY.subtreeCumulativeEarnedPerMLiq >> 64, 3);
    }

    function testAuxAtNodeOfRangeTwo() public {
        FeeSnap memory fees;
        _allocateAuxillaryArrays(fees);

        LiqNode storage zeroOne = liqTree.nodes[LKey.wrap((2 << 24) | 0)];

        // using 2 so splitting the borrow results in 2 instead of 0 (x/2*2)
        liqTree.addTLiq(range(0, 1), 100, fees, 2, 2);

        // A[] = 0-3.mLiq + 0-7.mLiq + 0-15.mLiq
        //     = 4096 + 8192 + 16384 = 28672
        // subtreeMLiq = 1024 + 1025 = 2049
        // totalMLiq = 2049 + 2048*2 + 28672*2 = 63489
        fees.X += 1756748001743618583822336; // 63489 * 2**64
        fees.Y += 1756748001743618583822336;

        liqTree.removeTLiq(range(0, 1), 100, fees, 1, 1);

        assertEq(zeroOne.tokenX.cumulativeEarnedPerMLiq >> 64, 3);
        assertEq(zeroOne.tokenX.subtreeCumulativeEarnedPerMLiq >> 64, 3);
        assertEq(zeroOne.tokenY.cumulativeEarnedPerMLiq >> 64, 3);
        assertEq(zeroOne.tokenY.subtreeCumulativeEarnedPerMLiq >> 64, 3);
    }

    function testAuxAtNodeOfRangeFour() public {
        FeeSnap memory fees;
        _allocateAuxillaryArrays(fees);

        LiqNode storage zeroThree = liqTree.nodes[LKey.wrap((4 << 24) | 0)];

        // using 2 so splitting the borrow results in 2 instead of 0 (x/2*2)
        liqTree.addTLiq(range(0, 3), 100, fees, 4, 4);

        // A[] = 0-7.mLiq + 0-15.mLiq
        //     = 8192 + 16384 = 24576
        // subtreeMLiq = 4096*4 + 2*2048 + 2*2049 + 1*1024 + 1*1025 + 1*1026 + 1*1027 = 28680
        // totalMLiq = 28680 + 24576*4 = 126984
        fees.X += 1756831012091950276804608; // 126984 * 2**64 / 4 * 3
        fees.Y += 1756831012091950276804608;

        liqTree.removeTLiq(range(0, 3), 100, fees, 1, 1);

        assertEq(zeroThree.tokenX.cumulativeEarnedPerMLiq >> 64, 3);
        assertEq(zeroThree.tokenX.subtreeCumulativeEarnedPerMLiq >> 64, 3);
        assertEq(zeroThree.tokenY.cumulativeEarnedPerMLiq >> 64, 3);
        assertEq(zeroThree.tokenY.subtreeCumulativeEarnedPerMLiq >> 64, 3);
    }

    function testAuxAtNodeOfRangeEight() public {
        FeeSnap memory fees;
        _allocateAuxillaryArrays(fees);

        LiqNode storage zeroSeven = liqTree.nodes[LKey.wrap((8 << 24) | 0)];

        liqTree.addTLiq(range(0, 7), 100, fees, 8, 8);

        // A[] = 0-15.mLiq
        //     = 16384 = 16384
        // subtreeMLiq = 8192*8 + 4096*4 + 4097*4 + 2048*2 + 2049*2 + 2050*2 + 2051*2 + 1024*1 + 1025*1 + 1026*1 + 1027*1 + 1028*1 + 1029*1 + 1030*1 + 1031*1 = 57388
        // totalMLiq = 122924 + 16384*8 = 253996
        fees.X += 1757024702904724227096576; // 253996 * 2**64 / 8 * 3
        fees.Y += 1757024702904724227096576;

        liqTree.removeTLiq(range(0, 7), 100, fees, 1, 1);

        assertEq(zeroSeven.tokenX.cumulativeEarnedPerMLiq >> 64, 3);
        assertEq(zeroSeven.tokenX.subtreeCumulativeEarnedPerMLiq >> 64, 3);
        assertEq(zeroSeven.tokenY.cumulativeEarnedPerMLiq >> 64, 3);
        assertEq(zeroSeven.tokenY.subtreeCumulativeEarnedPerMLiq >> 64, 3);
    }

    // something strange about the console output in the fee handle method?
    function testAuxAtNodeOfRangeSixteen() public {
        FeeSnap memory fees;
        _allocateAuxillaryArrays(fees);

        LiqNode storage zeroFifteen = liqTree.nodes[liqTree.root];

        liqTree.addWideRangeTLiq(100, fees, 16, 16);

        // A[] = 0-15.mLiq = 0
        // subtreeMLiq =
        //      16384*16 + 8192*8 + 8193*8 + 4096*4 + 4097*4 + 4098*4 + 4099*4 +
        //      2048*2 + 2049*2 + 2050*2 + 2051*2 + 2052*2 + 2053*2 + 2054*2 + 2055*2 +
        //      1024*1 + 1025*1 + 1026*1 + 1027*1 + 1028*1 + 1029*1 + 1030*1 + 1031*1 + 1032*1 +
        //      1033*1 + 1034*1 + 1035*1 + 1036*1 + 1037*1 + 1038*1 + 1039*1
        //      = 458784 + 32824 + 9252 + 7252 = 508112
        // totalMLiq = 508112 + 0*8 = 508112
        fees.X += 1757439754646382692007936; // 508112 * 2**64 / 16 * 3
        fees.Y += 1757439754646382692007936;

        liqTree.removeWideRangeTLiq(100, fees, 16, 16);

        assertEq(zeroFifteen.tokenX.cumulativeEarnedPerMLiq >> 64, 3);
        assertEq(zeroFifteen.tokenX.subtreeCumulativeEarnedPerMLiq >> 64, 3);
        assertEq(zeroFifteen.tokenY.cumulativeEarnedPerMLiq >> 64, 3);
        assertEq(zeroFifteen.tokenY.subtreeCumulativeEarnedPerMLiq >> 64, 3);
    }

    // N.range

    function testNodeRangeOfOneInFeeCalculation() public {
        // TODO: revert on allocation of tLiq when there is not enough mLiq
        FeeSnap memory fees;
        LiqNode storage zeroZero = liqTree.nodes[LKey.wrap((1 << 24) | 0)];

        liqTree.addWideRangeMLiq(1, fees); // A[] = 1
        liqTree.addMLiq(range(0, 0), 5, fees);
        liqTree.addTLiq(range(0, 0), 1, fees, 18, 18);

        fees.X += 18446744073709551616; // 2**64
        fees.Y += 18446744073709551616;
        liqTree.removeTLiq(range(0, 0), 1, fees, 15, 15);

        // totalMLiq = 5 + 1*1 = 6
        // borrows = 18
        assertEq(zeroZero.tokenX.cumulativeEarnedPerMLiq >> 64, 3); // 15 * 1 / 5
        assertEq(zeroZero.tokenX.subtreeCumulativeEarnedPerMLiq >> 64, 3);
        assertEq(zeroZero.tokenY.cumulativeEarnedPerMLiq >> 64, 3);
        assertEq(zeroZero.tokenY.subtreeCumulativeEarnedPerMLiq >> 64, 3);
    }

    function testNodeRangeOfTwoInFeeCalculation() public {
        FeeSnap memory fees;
        LiqNode storage zeroOne = liqTree.nodes[LKey.wrap((2 << 24) | 0)];

        liqTree.addWideRangeMLiq(1, fees); // A[] = 1
        liqTree.addMLiq(range(0, 1), 4, fees);
        liqTree.addTLiq(range(0, 1), 1, fees, 31, 31);

        fees.X += 18446744073709551616; // 2**64
        fees.Y += 18446744073709551616;
        liqTree.removeTLiq(range(0, 1), 1, fees, 21, 21);

        // totalMLiq = 4*2 + 2*1 = 10
        // borrow = 31/2*2 = 20 (decimal truncation)
        assertEq(zeroOne.tokenX.cumulativeEarnedPerMLiq >> 64, 3);
        assertEq(zeroOne.tokenX.subtreeCumulativeEarnedPerMLiq >> 64, 3);
        assertEq(zeroOne.tokenY.cumulativeEarnedPerMLiq >> 64, 3);
        assertEq(zeroOne.tokenY.subtreeCumulativeEarnedPerMLiq >> 64, 3);
    }

    function testNodeRangeOfFourInFeeCalculation() public {
        FeeSnap memory fees;
        LiqNode storage zeroThree = liqTree.nodes[LKey.wrap((4 << 24) | 0)];

        liqTree.addWideRangeMLiq(1, fees); // A[] = 1
        liqTree.addMLiq(range(0, 3), 24, fees);
        liqTree.addTLiq(range(0, 3), 1, fees, 300, 300);

        fees.X += 18446744073709551616; // 2**64
        fees.Y += 18446744073709551616;
        liqTree.removeTLiq(range(0, 3), 1, fees, 300, 300);

        // totalMLiq = 24*4 + 4*1 = 100
        assertEq(zeroThree.tokenX.cumulativeEarnedPerMLiq >> 64, 3);
        assertEq(zeroThree.tokenX.subtreeCumulativeEarnedPerMLiq >> 64, 3);
        assertEq(zeroThree.tokenY.cumulativeEarnedPerMLiq >> 64, 3);
        assertEq(zeroThree.tokenY.subtreeCumulativeEarnedPerMLiq >> 64, 3);
    }

    function testNodeRangeOfEightInFeeCalculation() public {
        FeeSnap memory fees;
        LiqNode storage zeroSeven = liqTree.nodes[LKey.wrap((8 << 24) | 0)];

        liqTree.addWideRangeMLiq(1, fees); // A[] = 1
        liqTree.addMLiq(range(0, 7), 47, fees);
        liqTree.addTLiq(range(0, 7), 1, fees, 1152, 1152);

        fees.X += 18446744073709551616; // 2**64
        fees.Y += 18446744073709551616;
        liqTree.removeTLiq(range(0, 7), 1, fees, 1, 1);

        // totalMLiq = 47*8 + 8*1 = 384
        assertEq(zeroSeven.tokenX.cumulativeEarnedPerMLiq >> 64, 3);
        assertEq(zeroSeven.tokenX.subtreeCumulativeEarnedPerMLiq >> 64, 3);
        assertEq(zeroSeven.tokenY.cumulativeEarnedPerMLiq >> 64, 3);
        assertEq(zeroSeven.tokenY.subtreeCumulativeEarnedPerMLiq >> 64, 3);
    }

    function testNodeRangeOfSixteenInFeeCalculation() public {
        FeeSnap memory fees;
        LiqNode storage zeroSixteen = liqTree.nodes[liqTree.root];

        liqTree.addWideRangeMLiq(3, fees);
        liqTree.addWideRangeTLiq(1, fees, 144, 144);

        fees.X += 18446744073709551616; // 2**64
        fees.Y += 18446744073709551616;
        liqTree.removeWideRangeTLiq(1, fees, 1, 1);

        // totalMLiq = 3*16 + 16*0 = 48
        assertEq(zeroSixteen.tokenX.cumulativeEarnedPerMLiq >> 64, 3);
        assertEq(zeroSixteen.tokenX.subtreeCumulativeEarnedPerMLiq >> 64, 3);
        assertEq(zeroSixteen.tokenY.cumulativeEarnedPerMLiq >> 64, 3);
        assertEq(zeroSixteen.tokenY.subtreeCumulativeEarnedPerMLiq >> 64, 3);
    }

    // r

    function testNodeRateAccumulationAddingMLiq() public {
        FeeSnap memory fees;
        fees.X += 1;
        fees.Y += 1;

        liqTree.addMLiq(range(15, 15), 100, fees);

        LiqNode storage eightFifteen = liqTree.nodes[LKey.wrap((8 << 24) | 8)];
        assertEq(eightFifteen.tokenX.feeRateSnapshot, 1);
        assertEq(eightFifteen.tokenY.feeRateSnapshot, 1);
    }

    function testNodeMultiRateAccumulationAddingMLiq() public {
        FeeSnap memory fees;
        fees.X += 1;
        fees.Y += 1;

        fees.X += 8726349723049235689236;
        fees.Y += 827369027349823649072634587236582365;

        liqTree.addMLiq(range(15, 15), 100, fees);

        LiqNode storage eightFifteen = liqTree.nodes[LKey.wrap((8 << 24) | 8)];
        assertEq(eightFifteen.tokenX.feeRateSnapshot, 8726349723049235689237);
        assertEq(eightFifteen.tokenY.feeRateSnapshot, 827369027349823649072634587236582366);
    }

    function testNodeRateDoesNotAccumulateWhenAddingMLiqToOtherNodes() public {
        FeeSnap memory fees;
        fees.X += 1;
        fees.Y += 1;

        liqTree.addMLiq(range(0, 0), 100, fees);

        LiqNode storage eightFifteen = liqTree.nodes[LKey.wrap((8 << 24) | 8)];
        assertEq(eightFifteen.tokenX.feeRateSnapshot, 0);
        assertEq(eightFifteen.tokenY.feeRateSnapshot, 0);
    }

    function testNodeRateDoesNotAccumulateWhenAddingWideMLiq() public {
        FeeSnap memory fees;
        fees.X += 1;
        fees.Y += 1;

        liqTree.addWideRangeMLiq(100, fees);

        LiqNode storage eightFifteen = liqTree.nodes[LKey.wrap((8 << 24) | 8)];
        assertEq(eightFifteen.tokenX.feeRateSnapshot, 0);
        assertEq(eightFifteen.tokenY.feeRateSnapshot, 0);
    }

    function testNodeRateAccumulationRemovingMLiq() public {
        FeeSnap memory fees;
        liqTree.addMLiq(range(15, 15), 100, fees);
        fees.X += 1;
        fees.Y += 1;
        liqTree.removeMLiq(range(15, 15), 20, fees);

        LiqNode storage eightFifteen = liqTree.nodes[LKey.wrap((8 << 24) | 8)];
        assertEq(eightFifteen.tokenX.feeRateSnapshot, 1);
        assertEq(eightFifteen.tokenY.feeRateSnapshot, 1);
    }

    function testNodeMultiRateAccumulationRemovingMLiq() public {
        FeeSnap memory fees;
        fees.X += 1;
        fees.Y += 1;

        liqTree.addMLiq(range(15, 15), 100, fees);

        fees.X += 8726349723049235689236;
        fees.Y += 827369027349823649072634587236582365;

        liqTree.removeMLiq(range(15, 15), 20, fees);

        LiqNode storage eightFifteen = liqTree.nodes[LKey.wrap((8 << 24) | 8)];
        assertEq(eightFifteen.tokenX.feeRateSnapshot, 8726349723049235689237);
        assertEq(eightFifteen.tokenY.feeRateSnapshot, 827369027349823649072634587236582366);
    }

    function testNodeRateDoesNotAccumulateWhenRemovingMLiqFromOtherNodes() public {
        FeeSnap memory fees;
        liqTree.addMLiq(range(0, 0), 100, fees);
        fees.X += 1;
        fees.Y += 1;
        liqTree.removeMLiq(range(0, 0), 100, fees);

        LiqNode storage eightFifteen = liqTree.nodes[LKey.wrap((8 << 24) | 8)];
        assertEq(eightFifteen.tokenX.feeRateSnapshot, 0);
        assertEq(eightFifteen.tokenY.feeRateSnapshot, 0);
    }

    function testNodeRateDoesNotAccuulateWhenRemovingWideMLiq() public {
        FeeSnap memory fees;
        liqTree.addWideRangeMLiq(100, fees);
        fees.X += 1;
        fees.Y += 1;
        liqTree.removeWideRangeMLiq(100, fees);

        LiqNode storage eightFifteen = liqTree.nodes[LKey.wrap((8 << 24) | 8)];
        assertEq(eightFifteen.tokenX.feeRateSnapshot, 0);
        assertEq(eightFifteen.tokenY.feeRateSnapshot, 0);
    }

    function testNodeRateAccumulationAddingTLiq() public {
        FeeSnap memory fees;
        liqTree.addMLiq(range(15, 15), 100, fees);
        fees.X += 1;
        fees.Y += 1;
        liqTree.addTLiq(range(15, 15), 10, fees, 1, 1);

        LiqNode storage eightFifteen = liqTree.nodes[LKey.wrap((8 << 24) | 8)];
        assertEq(eightFifteen.tokenX.feeRateSnapshot, 1);
        assertEq(eightFifteen.tokenY.feeRateSnapshot, 1);
    }

    function testNodeMultiRateAccumulationAddingTLiq() public {
        FeeSnap memory fees;
        fees.X += 1;
        fees.Y += 1;

        liqTree.addMLiq(range(15, 15), 100, fees);

        fees.X += 8726349723049235689236;
        fees.Y += 827369027349823649072634587236582365;

        liqTree.addTLiq(range(15, 15), 10, fees, 1, 1);

        LiqNode storage eightFifteen = liqTree.nodes[LKey.wrap((8 << 24) | 8)];
        assertEq(eightFifteen.tokenX.feeRateSnapshot, 8726349723049235689237);
        assertEq(eightFifteen.tokenY.feeRateSnapshot, 827369027349823649072634587236582366);
    }

    function testNodeRateDoesNotAccumulateWhenAddingTLiqToOtherNodes() public {
        FeeSnap memory fees;
        liqTree.addMLiq(range(0, 0), 100, fees);
        fees.X += 1;
        fees.Y += 1;
        liqTree.addTLiq(range(0, 0), 10, fees, 1, 1);

        LiqNode storage eightFifteen = liqTree.nodes[LKey.wrap((8 << 24) | 8)];
        assertEq(eightFifteen.tokenX.feeRateSnapshot, 0);
        assertEq(eightFifteen.tokenY.feeRateSnapshot, 0);
    }

    function testNodeRateDoesNotAccumulateWhenAddingWideTLiq() public {
        FeeSnap memory fees;
        liqTree.addWideRangeMLiq(100, fees);
        fees.X += 1;
        fees.Y += 1;
        liqTree.addWideRangeTLiq(10, fees, 1, 1);

        LiqNode storage eightFifteen = liqTree.nodes[LKey.wrap((8 << 24) | 8)];
        assertEq(eightFifteen.tokenX.feeRateSnapshot, 0);
        assertEq(eightFifteen.tokenY.feeRateSnapshot, 0);
    }

    function testNodeRateAccumulationRemovingTLiq() public {
        FeeSnap memory fees;
        liqTree.addMLiq(range(15, 15), 100, fees);
        liqTree.addTLiq(range(15, 15), 10, fees, 1, 1);
        fees.X += 1;
        fees.Y += 1;
        liqTree.removeTLiq(range(15, 15), 10, fees, 1, 1);

        LiqNode storage eightFifteen = liqTree.nodes[LKey.wrap((8 << 24) | 8)];
        assertEq(eightFifteen.tokenX.feeRateSnapshot, 1);
        assertEq(eightFifteen.tokenY.feeRateSnapshot, 1);
    }

    function testNodeMultiRateAccumulationRemovingTLiq() public {
        FeeSnap memory fees;
        fees.X += 1;
        fees.Y += 1;

        liqTree.addMLiq(range(15, 15), 100, fees);
        liqTree.addTLiq(range(15, 15), 10, fees, 1, 1);

        fees.X += 8726349723049235689236;
        fees.Y += 827369027349823649072634587236582365;

        liqTree.removeTLiq(range(15, 15), 10, fees, 1, 1);

        LiqNode storage eightFifteen = liqTree.nodes[LKey.wrap((8 << 24) | 8)];
        assertEq(eightFifteen.tokenX.feeRateSnapshot, 8726349723049235689237);
        assertEq(eightFifteen.tokenY.feeRateSnapshot, 827369027349823649072634587236582366);
    }

    function testNodeRateDoesNotAccumulateWhenRemovingTLiqFromOtherNodes() public {
        FeeSnap memory fees;
        liqTree.addMLiq(range(0, 0), 100, fees);
        liqTree.addTLiq(range(0, 0), 10, fees, 1, 1);
        fees.X += 1;
        fees.Y += 1;
        liqTree.removeTLiq(range(0, 0), 10, fees, 1, 1);

        LiqNode storage eightFifteen = liqTree.nodes[LKey.wrap((8 << 24) | 8)];
        assertEq(eightFifteen.tokenX.feeRateSnapshot, 0);
        assertEq(eightFifteen.tokenY.feeRateSnapshot, 0);
    }

    function testNodeRateDoesNotAccumulateWhenRemovingWideTLiq() public {
        FeeSnap memory fees;
        liqTree.addWideRangeMLiq(100, fees);
        liqTree.addWideRangeTLiq(10, fees, 1, 1);
        fees.X += 1;
        fees.Y += 1;
        liqTree.removeWideRangeTLiq(10, fees, 1, 1);

        LiqNode storage eightFifteen = liqTree.nodes[LKey.wrap((8 << 24) | 8)];
        assertEq(eightFifteen.tokenX.feeRateSnapshot, 0);
        assertEq(eightFifteen.tokenY.feeRateSnapshot, 0);
    }
}
