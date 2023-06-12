// SPDX-License-Identifier: BSL-1.1
pragma solidity ^0.8.18;

import { console } from "forge-std/console.sol";
import { Test } from "forge-std/Test.sol";

import { LiqTree, LiqTreeImpl, LiqRange, LKey, LKeyImpl, LiqNode } from "src/Tree.sol";


/**
 * NOTE: There are 4 ways to breakdown a query, that effect how the tree will be traversed.
 *          1. Simple case, walking both legs
 *          2. Left leg only
 *          3. Right leg only
 *          4. Both are at or higher than the peak
 *
 * This also effects how our code is executed. Usually following an approach, that checks
 *          a1. current node
 *          a2. propogate to node parrent
 *           b. optional flip to the adjacent node
 *           c. propogation to parent (flipped or not)
 *
 * For full coverage, we need to test these possible paths. For each low and high checks. 
 * This is simple enough using only 2. and 3. however, we will test all four cases for completeness
 */

 /**
 struct LiqNodeTokenData {
    uint256 borrow;
    uint256 subtreeBorrow;
    uint256 feeRateSnapshot;
    uint256 cumulativeEarnedPerMLiq;
    uint256 subtreeCumulativeEarnedPerMLiq;
}
  */
contract TreeFeesTest is Test {
    LiqTree public liqTree;
    using LiqTreeImpl for LiqTree;
    using LKeyImpl for LKey;
    
    function setUp() public {
        // A depth of 4 creates a tree that covers an absolute range of 16 ([0, 15]). 
        // ie. A complete tree matching the ascii documentation. 
        liqTree.init(4);
    }

    function testNodeEarnAndSubtreeEarnAtLeafNodeAreEqual() public {
        LiqNode storage threeThree = liqTree.nodes[LKey.wrap(1 << 24 | 19)];

        (uint256 accumulatedFeeRateX, uint256 accumulatedFeeRateY) = liqTree.addWideRangeMLiq(400);
        assertEq(accumulatedFeeRateX, 0);
        assertEq(accumulatedFeeRateY, 0);
        
        (accumulatedFeeRateX, accumulatedFeeRateY) = liqTree.addMLiq(LiqRange(3, 3), 130);
        assertEq(accumulatedFeeRateX, 0);
        assertEq(accumulatedFeeRateY, 0);

        liqTree.addTLiq(LiqRange(3, 3), 30, 44e18, 101e18);
        liqTree.feeRateSnapshotTokenX += 23947923;
        liqTree.feeRateSnapshotTokenY += 13542645834;
        (accumulatedFeeRateX, accumulatedFeeRateY) = liqTree.removeMLiq(LiqRange(3, 3), 20);

        // totalMLiq = 130*1 + 400*1 = 530
        // x:  44e18 * 23947923 / (130*1 + 400*1) / 2**64 = 107776.713
        // y:  101e18 * 13542645834 / (130*1 + 400*1) / 2**64 = 139903732.969517
        assertEq(threeThree.tokenX.cumulativeEarnedPerMLiq, 107776);
        assertEq(threeThree.tokenX.subtreeCumulativeEarnedPerMLiq, 107776);
        assertEq(threeThree.tokenY.cumulativeEarnedPerMLiq, 139903732);
        assertEq(threeThree.tokenY.subtreeCumulativeEarnedPerMLiq, 139903732);

        assertEq(accumulatedFeeRateX, 107776);
        assertEq(accumulatedFeeRateY, 139903732);
    }

    /*
    should be covered in param test 

            LiqNode storage threeThree = liqTree.nodes[LKey.wrap(1 << 24 | 19)];

        // initial state
        assertEq(threeThree.tokenX.borrow, 0);
        assertEq(threeThree.tokenX.subtreeBorrow, 0);
        assertEq(threeThree.tokenX.feeRateSnapshot, 0);
        assertEq(threeThree.tokenX.cumulativeEarnedPerMLiq, 0);
        assertEq(threeThree.tokenX.subtreeCumulativeEarnedPerMLiq, 0);

        assertEq(threeThree.tokenY.borrow, 0);
        assertEq(threeThree.tokenY.subtreeBorrow, 0);
        assertEq(threeThree.tokenY.feeRateSnapshot, 0);
        assertEq(threeThree.tokenY.cumulativeEarnedPerMLiq, 0);
        assertEq(threeThree.tokenY.subtreeCumulativeEarnedPerMLiq, 0);

        liqTree.feeRateSnapshotTokenX += 23947923;
        liqTree.feeRateSnapshotTokenY += 13542645834;

        // change in rate does nothing
        assertEq(threeThree.tokenX.borrow, 0);
        assertEq(threeThree.tokenX.subtreeBorrow, 0);
        assertEq(threeThree.tokenX.feeRateSnapshot, 0);
        assertEq(threeThree.tokenX.cumulativeEarnedPerMLiq, 0);
        assertEq(threeThree.tokenX.subtreeCumulativeEarnedPerMLiq, 0);

        assertEq(threeThree.tokenY.borrow, 0);
        assertEq(threeThree.tokenY.subtreeBorrow, 0);
        assertEq(threeThree.tokenY.feeRateSnapshot, 0);
        assertEq(threeThree.tokenY.cumulativeEarnedPerMLiq, 0);
        assertEq(threeThree.tokenY.subtreeCumulativeEarnedPerMLiq, 0);

        liqTree.addMLiq(LiqRange(3, 3), 789e18);

        // rate accumulates, but nothing earned w/o a borrow
        assertEq(threeThree.tokenX.borrow, 0);
        assertEq(threeThree.tokenX.subtreeBorrow, 0);
        assertEq(threeThree.tokenX.feeRateSnapshot, 23947923);
        assertEq(threeThree.tokenX.cumulativeEarnedPerMLiq, 0);
        assertEq(threeThree.tokenX.subtreeCumulativeEarnedPerMLiq, 0);

        assertEq(threeThree.tokenY.borrow, 0);
        assertEq(threeThree.tokenY.subtreeBorrow, 0);
        assertEq(threeThree.tokenY.feeRateSnapshot, 13542645834);
        assertEq(threeThree.tokenY.cumulativeEarnedPerMLiq, 0);
        assertEq(threeThree.tokenY.subtreeCumulativeEarnedPerMLiq, 0);

        liqTree.feeRateSnapshotTokenX += 1000;
        liqTree.feeRateSnapshotTokenY += 1000;
        liqTree.addTLiq(LiqRange(3, 3), 100e18, 70e18, 20e6);

        // fees are calculated prior to the update, so here there is still no borrow
        assertEq(threeThree.tokenX.borrow, 70e18);
        assertEq(threeThree.tokenX.subtreeBorrow, 70e18);
        assertEq(threeThree.tokenX.feeRateSnapshot, 23948923);
        assertEq(threeThree.tokenX.cumulativeEarnedPerMLiq, 0);
        assertEq(threeThree.tokenX.subtreeCumulativeEarnedPerMLiq, 0);

        assertEq(threeThree.tokenY.borrow, 20e6);
        assertEq(threeThree.tokenY.subtreeBorrow, 20e6);
        assertEq(threeThree.tokenY.feeRateSnapshot, 13542646834);
        assertEq(threeThree.tokenY.cumulativeEarnedPerMLiq, 0);
        assertEq(threeThree.tokenY.subtreeCumulativeEarnedPerMLiq, 0);

    */

    function testEarnIsEquallySplitAmongChildrenAndGrandChildrenWhenMLiqIsEqualForEachNodeAtEachLevel() public {
        /*        
        *                     /
        *                  0-3
        *                /   \
        *              /       \
        *            /           \
        *          0-1            2-3
        *         /   \          /   \
        *        /     \        /     \
        *       0       1      2       3
        */


    }

    function testSubtreeEarnIsLargelyConsummedByChildWithLargerSubtreeMLiq() public {

    }

    function testEarnIsLargelyConsummedByChildWithLargerMLiq() public {

    }

    function testEarnWhereTotalMLiqIsOnlyFromAuxArray() public {

    }

    function testEarnWhereTotalMLiqIsOnlyFromSubtreeMLiq() public {

    }

    function testEarnWhereTotalMLiqIsFromBothAuxArrayAndSubtreeMLiq() public {

    }


    // -- Not sure about these

    function testFeeCalculationWalkingLeftLegThatCoversAllBlocksWithinTheLowCodeBranch() public {
        // 0-4 | 4-4, 4-5, 4-7, 0-3, 0-7

        /*        
        *                                                              0-15
        *                                                      ____----
        *                                  __________----------
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
    }

    function testFeeCalculationWalkingRightLegThatCoversAllBlocksWithinTheHighCodeBranch() public {
        // 1-7 | 1-1, 0-1, 2-3, 0-3, 0-7

        /*        
        *                                                              0-15
        *                                                      ____----
        *                                  __________----------
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
    }

    function testFeeCalculationWalkingBothLegsThatCoversAllBlocksWithinBothTheLowAndHighBranches() public {
        // 1-12 |   1-1,   0-1,   2-3,   0-3,   4-7,   0-7
        //      | 12-12, 12-13,        12-15,  8-11,  8-15

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
    }

    function testFeeCalculationWalkingBothLegsAtOrHigherThanThePeak() public {
        // 2-3 | 2-3, 0-3

        /*        
        *                                                              0-15
        *                                                      ____----    ----____
        *                                  __________---------- 
        *                                0-7
        *                            __--  --__
        *                       __---        
        *                     / 
        *                  0-3
        *                /   \
        *              /       \
        *            /           \
        *          0-1            2-3
        *         /   \          /   \
        *        /     \        /     \
        *       0       1      2       3
        */
    }

 
}