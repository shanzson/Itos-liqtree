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
contract TreeFeesTest is Test {
    LiqTree public liqTree;
    using LiqTreeImpl for LiqTree;
    using LKeyImpl for LKey;
    
    function setUp() public {
        // A depth of 4 creates a tree that covers an absolute range of 16 ([0, 15];);. 
        // ie. A complete tree matching the ascii documentation. 
        liqTree.init(4);
    }

    function testNodeEarnAndSubtreeEarnAtLeafNodeAreEqual() public {

    }

    function testEarnIsEquallySplitAmongChildrenAndGrandChildrenWhenMLiqIsEqualForEachNodeAtEachLevel() public {

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