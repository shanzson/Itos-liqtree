// SPDX-License-Identifier: BSL-1.1
pragma solidity ^0.8.18;

import { Test } from "forge-std/Test.sol";

import { LiqTree, LiqTreeImpl, LiqRange, LKey, LKeyImpl, LiqNode, FeeSnap } from "src/Tree.sol";

// solhint-disable

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
        // A depth of 5 creates a tree that covers an absolute range of 16 ([0, 15]).
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

    function testNodeEarnAndSubtreeEarnAtLeafNodeAreEqual() public {
        FeeSnap memory fees;
        LiqNode storage threeThree = liqTree.nodes[LKey.wrap((1 << 24) | 3)];

        (uint256 accumulatedFeeRateX, uint256 accumulatedFeeRateY) = liqTree.addWideRangeMLiq(400, fees);
        assertEq(accumulatedFeeRateX, 0);
        assertEq(accumulatedFeeRateY, 0);

        (accumulatedFeeRateX, accumulatedFeeRateY) = liqTree.addMLiq(range(3, 3), 130, fees);
        assertEq(accumulatedFeeRateX, 0);
        assertEq(accumulatedFeeRateY, 0);

        liqTree.addTLiq(range(3, 3), 30, fees, 44e18, 101e18);
        fees.X += 23947923;
        fees.Y += 13542645834;
        (accumulatedFeeRateX, accumulatedFeeRateY, ) = liqTree.removeMLiq(range(3, 3), 20, fees);

        // totalMLiq = 130*1 + 400*1 = 530
        // x:  44e18 * 23947923 / (130*1 + 400*1) / 2**64 = 107776.713
        // y:  101e18 * 13542645834 / (130*1 + 400*1) / 2**64 = 139903732.969517
        assertEq(threeThree.tokenX.cumulativeEarnedPerMLiq >> 64, 107776);
        assertEq(threeThree.tokenX.subtreeCumulativeEarnedPerMLiq >> 64, 107776);
        assertEq(threeThree.tokenY.cumulativeEarnedPerMLiq >> 64, 139903732);
        assertEq(threeThree.tokenY.subtreeCumulativeEarnedPerMLiq >> 64, 139903732);

        assertEq(accumulatedFeeRateX >> 64, 107776);
        assertEq(accumulatedFeeRateY >> 64, 139903732);
    }

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
        FeeSnap memory fees;

        // mLiq
        liqTree.addMLiq(range(0, 3), 1900e18, fees);

        liqTree.addMLiq(range(0, 1), 100, fees);
        liqTree.addMLiq(range(2, 3), 100, fees);

        liqTree.addMLiq(range(0, 0), 20, fees);
        liqTree.addMLiq(range(1, 1), 20, fees);
        liqTree.addMLiq(range(2, 2), 20, fees);
        liqTree.addMLiq(range(3, 3), 20, fees);

        // borrows
        liqTree.addTLiq(range(0, 3), 1, fees, 700e18, 2400e6);

        liqTree.addTLiq(range(0, 1), 1, fees, 700e18, 2400e6);
        liqTree.addTLiq(range(2, 3), 1, fees, 700e18, 2400e6);

        liqTree.addTLiq(range(0, 0), 1, fees, 700e18, 2400e6);
        liqTree.addTLiq(range(1, 1), 1, fees, 700e18, 2400e6);
        liqTree.addTLiq(range(2, 2), 1, fees, 700e18, 2400e6);
        liqTree.addTLiq(range(3, 3), 1, fees, 700e18, 2400e6);

        // trigger fees
        fees.X += 55769907879546549697897755;
        fees.Y += 445692368876987602531346364605670;

        liqTree.removeTLiq(range(0, 0), 1, fees, 700e18, 2400e6);
        liqTree.removeTLiq(range(1, 1), 1, fees, 700e18, 2400e6);
        liqTree.removeTLiq(range(2, 2), 1, fees, 700e18, 2400e6);
        liqTree.removeTLiq(range(3, 3), 1, fees, 700e18, 2400e6);

        // calculate fees

        // 0-0, 1-1, 2-2, 3-3
        // A[] = 100 + 1900e18
        // totalMLiq = 20 + (100 + 1900e18)*1 = 1900000000000000000120
        // x: 700e18 * 55769907879546549697897755 / 1900000000000000000120 / 2**64 = 1113844.702569
        // y: 2400e6 * 445692368876987602531346364605670 / 1900000000000000000120 / 2**64 = 30.51919797452468088

        LiqNode storage zeroZero = liqTree.nodes[LKey.wrap((1 << 24) | 0)];
        assertEq(zeroZero.tokenX.cumulativeEarnedPerMLiq >> 64, 1113844);
        assertEq(zeroZero.tokenX.subtreeCumulativeEarnedPerMLiq >> 64, 1113844);
        assertEq(zeroZero.tokenY.cumulativeEarnedPerMLiq >> 64, 30);
        assertEq(zeroZero.tokenY.subtreeCumulativeEarnedPerMLiq >> 64, 30);

        LiqNode storage oneOne = liqTree.nodes[LKey.wrap((1 << 24) | 1)];
        assertEq(oneOne.tokenX.cumulativeEarnedPerMLiq >> 64, 1113844);
        assertEq(oneOne.tokenX.subtreeCumulativeEarnedPerMLiq >> 64, 1113844);
        assertEq(oneOne.tokenY.cumulativeEarnedPerMLiq >> 64, 30);
        assertEq(oneOne.tokenY.subtreeCumulativeEarnedPerMLiq >> 64, 30);

        LiqNode storage twoTwo = liqTree.nodes[LKey.wrap((1 << 24) | 2)];
        assertEq(twoTwo.tokenX.cumulativeEarnedPerMLiq >> 64, 1113844);
        assertEq(twoTwo.tokenX.subtreeCumulativeEarnedPerMLiq >> 64, 1113844);
        assertEq(twoTwo.tokenY.cumulativeEarnedPerMLiq >> 64, 30);
        assertEq(twoTwo.tokenY.subtreeCumulativeEarnedPerMLiq >> 64, 30);

        LiqNode storage threeThree = liqTree.nodes[LKey.wrap((1 << 24) | 3)];
        assertEq(threeThree.tokenX.cumulativeEarnedPerMLiq >> 64, 1113844);
        assertEq(threeThree.tokenX.subtreeCumulativeEarnedPerMLiq >> 64, 1113844);
        assertEq(threeThree.tokenY.cumulativeEarnedPerMLiq >> 64, 30);
        assertEq(threeThree.tokenY.subtreeCumulativeEarnedPerMLiq >> 64, 30);

        // 0-1, 2-3
        // A[] = 1900e18
        // totalMLiq = 220 + 1900e18*2 = 3800000000000000000220
        //  x: 700e18 * 55769907879546549697897755 / 3800000000000000000220 / 2**64 = 556922.351284
        // sx: (3*700e18) * 55769907879546549697897755 / 3800000000000000000220 / 2**64 = 1670767.05385360
        //  y: 2400e6 * 445692368876987602531346364605670 / 3800000000000000000220 / 2**64 = 15.25959
        // sy: (3*2400e6) * 445692368876987602531346364605670 / 3800000000000000000220 / 2**64 = 45.778

        LiqNode storage zeroOne = liqTree.nodes[LKey.wrap((2 << 24) | 0)];
        assertEq(zeroOne.tokenX.cumulativeEarnedPerMLiq >> 64, 556922); // 556922
        assertEq(zeroOne.tokenX.subtreeCumulativeEarnedPerMLiq >> 64, 1670767); // 556922 + 1113844 = 1670766 (notice this would have lost 1 wei)
        assertEq(zeroOne.tokenY.cumulativeEarnedPerMLiq >> 64, 15);
        assertEq(zeroOne.tokenY.subtreeCumulativeEarnedPerMLiq >> 64, 45);

        LiqNode storage twoThree = liqTree.nodes[LKey.wrap((2 << 24) | 2)];
        assertEq(twoThree.tokenX.cumulativeEarnedPerMLiq >> 64, 556922);
        assertEq(twoThree.tokenX.subtreeCumulativeEarnedPerMLiq >> 64, 1670767);
        assertEq(twoThree.tokenY.cumulativeEarnedPerMLiq >> 64, 15);
        assertEq(twoThree.tokenY.subtreeCumulativeEarnedPerMLiq >> 64, 45);

        // 0-3
        // A[] = 0
        // totalMLiq = 1900e18*4 + 100*2*2 + 20*1*4 = 7600000000000000000480
        //  x: 700e18 * 55769907879546549697897755 / 7600000000000000000480 / 2**64 = 278461.17564
        // xs: (700e18*7) * 55769907879546549697897755 / 7600000000000000000480 / 2**64 = 1949228.22949
        //  y: 2400e6 * 445692368876987602531346364605670 / 7600000000000000000480 / 2**64 = 7.6297
        // sy: (2400e6*7) * 445692368876987602531346364605670 / 7600000000000000000480 / 2**64 = 53.4085

        LiqNode storage zeroThree = liqTree.nodes[LKey.wrap((4 << 24) | 0)];
        assertEq(zeroThree.tokenX.cumulativeEarnedPerMLiq >> 64, 278461);
        assertEq(zeroThree.tokenX.subtreeCumulativeEarnedPerMLiq >> 64, 1949228);
        assertEq(zeroThree.tokenY.cumulativeEarnedPerMLiq >> 64, 7);
        assertEq(zeroThree.tokenY.subtreeCumulativeEarnedPerMLiq >> 64, 53);
    }

    function testSubtreeEarnIsLargelyConsummedByChildWithLargerMLiq() public {
        /*
         *            /
         *          0-1
         *         /   \
         *        /     \
         *       0       1
         */
        FeeSnap memory fees;

        // mLiq
        liqTree.addMLiq(range(0, 1), 4000, fees);

        liqTree.addMLiq(range(0, 0), 4000000, fees);
        liqTree.addMLiq(range(1, 1), 20, fees);

        // borrows
        liqTree.addTLiq(range(0, 1), 1, fees, 700e18, 2400e6);

        liqTree.addTLiq(range(0, 0), 1, fees, 700e18, 2400e6);
        liqTree.addTLiq(range(1, 1), 1, fees, 700e18, 2400e6);

        // trigger fees
        fees.X += 55769907879546549697897755;
        fees.Y += 445692368876987602531346364605670;

        liqTree.removeTLiq(range(0, 0), 1, fees, 700e18, 2400e6);
        liqTree.removeTLiq(range(1, 1), 1, fees, 700e18, 2400e6);

        // calculate fees

        // 0-0
        // A[] = 4000
        // totalMLiq = 4000000 + (4000)*1 = 4004000
        // x: 700e18 * 55769907879546549697897755 / 4004000 / 2**64 = 528547686034272911864.280765
        // y: 2400e6 * 445692368876987602531346364605670 / 4004000 / 2**64 = 14482136900998225.1980

        LiqNode storage zeroZero = liqTree.nodes[LKey.wrap((1 << 24) | 0)];
        assertEq(zeroZero.tokenX.cumulativeEarnedPerMLiq >> 64, 528547686034272911864);
        assertEq(zeroZero.tokenX.subtreeCumulativeEarnedPerMLiq >> 64, 528547686034272911864);
        assertEq(zeroZero.tokenY.cumulativeEarnedPerMLiq >> 64, 14482136900998225);
        assertEq(zeroZero.tokenY.subtreeCumulativeEarnedPerMLiq >> 64, 14482136900998225);

        // 1-1
        // A[] = 4000
        // totalMLiq = 20 + (4000)*1 = 4020
        // x: 700e18 * 55769907879546549697897755 / 4020 / 2**64 = 526444013652046950026014.971734
        // y: 2400e6 * 445692368876987602531346364605670 / 4020 / 2**64 = 14424496555123605396.257

        LiqNode storage oneOne = liqTree.nodes[LKey.wrap((1 << 24) | 1)];
        assertEq(oneOne.tokenX.cumulativeEarnedPerMLiq >> 64, 526444013652046950026014);
        assertEq(oneOne.tokenX.subtreeCumulativeEarnedPerMLiq >> 64, 526444013652046950026014);
        assertEq(oneOne.tokenY.cumulativeEarnedPerMLiq >> 64, 14424496555123605396);
        assertEq(oneOne.tokenY.subtreeCumulativeEarnedPerMLiq >> 64, 14424496555123605396);

        // 0-1
        // A[] = 0
        // totalMLiq = 4000*2 + (4000000 + 20) + (0)*2 = 4008020
        //  x: 700e18 * 55769907879546549697897755 / 4008020 / 2**64 = 528017558515483640077.789079
        // sx: 3*700e18 * 55769907879546549697897755 / 4008020 / 2**64 = 1584052675546450920233.367238
        //  y: 2400e6 * 445692368876987602531346364605670 / 4008020 / 2**64 = 14467611476888062.857209
        // sy: 3*2400e6 * 445692368876987602531346364605670 / 4008020 / 2**64 = 43402834430664188.5716297

        LiqNode storage zeroOne = liqTree.nodes[LKey.wrap((2 << 24) | 0)];
        assertEq(zeroOne.tokenX.cumulativeEarnedPerMLiq >> 64, 528017558515483640077);
        assertEq(zeroOne.tokenX.subtreeCumulativeEarnedPerMLiq >> 64, 1584052675546450920233);
        assertEq(zeroOne.tokenY.cumulativeEarnedPerMLiq >> 64, 14467611476888062);
        assertEq(zeroOne.tokenY.subtreeCumulativeEarnedPerMLiq >> 64, 43402834430664188);
    }

    function testEarnIsLargelyConsummedByChildWithLargerSubtreeMLiq() public {
        /*
         *                     /
         *                  0-3
         *                /   \
         *                      \
         *                        \
         *                         2-3
         *                        /   \
         *                       /     \
         *                      2       3
         */
        FeeSnap memory fees;

        // mLiq
        liqTree.addMLiq(range(0, 3), 4000, fees);
        liqTree.addMLiq(range(3, 3), 4000000000, fees);

        // borrows
        liqTree.addTLiq(range(0, 3), 1, fees, 700e18, 2400e6);
        liqTree.addTLiq(range(3, 3), 1, fees, 700e18, 2400e6);

        // trigger fees
        fees.X += 55769907879546549697897755;
        fees.Y += 445692368876987602531346364605670;

        liqTree.removeTLiq(range(3, 3), 1, fees, 700e18, 2400e6);

        // calculate fees

        // 3-3
        // A[] = 4000
        // totalMLiq = 4000000 + (4000)*1 = 4000004000
        // x: 700e18 * 55769907879546549697897755 / 4000004000 / 2**64 = 529075704644602540.173604872
        // y: 2400e6 * 445692368876987602531346364605670 / 4000004000 / 2**64 = 14496604541294.6821285

        LiqNode storage threeThree = liqTree.nodes[LKey.wrap((1 << 24) | 3)];
        assertEq(threeThree.tokenX.cumulativeEarnedPerMLiq >> 64, 529075704644602540);
        assertEq(threeThree.tokenX.subtreeCumulativeEarnedPerMLiq >> 64, 529075704644602540);
        assertEq(threeThree.tokenY.cumulativeEarnedPerMLiq >> 64, 14496604541294);
        assertEq(threeThree.tokenY.subtreeCumulativeEarnedPerMLiq >> 64, 14496604541294);

        // 2-3
        // A[] = 4000
        // totalMLiq = 4000000000 + (4000)*2 = 4000008000
        //  x: 0
        // sx: 700e18 * 55769907879546549697897755 / 4000008000 / 2**64 = 529075175569956044.8640553
        //  y: 0
        // sy: 2400e6 * 445692368876987602531346364605670 / 4000008000 / 2**64 = 14496590044719.13398

        LiqNode storage twoThree = liqTree.nodes[LKey.wrap((2 << 24) | 2)];
        assertEq(twoThree.tokenX.cumulativeEarnedPerMLiq >> 64, 0);
        assertEq(twoThree.tokenX.subtreeCumulativeEarnedPerMLiq >> 64, 529075175569956044);
        assertEq(twoThree.tokenY.cumulativeEarnedPerMLiq >> 64, 0);
        assertEq(twoThree.tokenY.subtreeCumulativeEarnedPerMLiq >> 64, 14496590044719);

        // 0-3
        // A[] = 0
        // totalMLiq = 4000*4 + 4000000*1 + (0)*4 = 4000016000
        //  x: 700e18 * 55769907879546549697897755 / 4000016000 / 2**64 = 529074117423837489.426187
        // sx: 2*700e18 * 55769907879546549697897755 / 4000016000 / 2**64 = 1058148234847674978.8523746
        //  y: 2400e6 * 445692368876987602531346364605670 / 4000016000 / 2**64 = 14496561051655.01680
        // sy: 2*2400e6 * 445692368876987602531346364605670 / 4000016000 / 2**64 = 28993122103310.03360

        LiqNode storage zeroThree = liqTree.nodes[LKey.wrap((4 << 24) | 0)];
        assertEq(zeroThree.tokenX.cumulativeEarnedPerMLiq >> 64, 529074117423837489);
        assertEq(zeroThree.tokenX.subtreeCumulativeEarnedPerMLiq >> 64, 1058148234847674978);
        assertEq(zeroThree.tokenY.cumulativeEarnedPerMLiq >> 64, 14496561051655);
        assertEq(zeroThree.tokenY.subtreeCumulativeEarnedPerMLiq >> 64, 28993122103310);
    }

    function testEarnWhereTotalMLiqIsMostlyFromAuxArray() public {
        // note: it's not possible to only be from A[]

        /*
         *                                        0-15
         *                                ____----
         *            __________----------
         *        0-7
         *    __--  --__
         *                ---__
         *                        \
         *                       4-7
         *                      /   \
         *                     /     \
         *                    /
         *                4-5
         *               /   \
         *              /     \
         *             4       5
         */
        FeeSnap memory fees;

        // mLiq
        liqTree.addWideRangeMLiq(554000, fees);
        liqTree.addMLiq(range(0, 7), 2000, fees);
        liqTree.addMLiq(range(4, 7), 7000000000, fees);
        liqTree.addMLiq(range(4, 5), 1, fees);

        // borrows
        liqTree.addTLiq(range(4, 5), 1, fees, 9241e18, 16732e6);

        // trigger fees
        fees.X += 55769907879546549697897755;
        fees.Y += 445692368876987602531346364605670;

        liqTree.addMLiq(range(5, 5), 100, fees);

        // calculate fees

        // 4-5
        // A[] = 554000 + 2000 + 7000000000
        // totalMLiq = 1*2 + (554000 + 2000 + 7000000000)*2 = 14001112002
        //  x: 9241e18 * 55769907879546549697897755 / 14001112002 / 2**64 = 1995430679306434663.0912
        //  y: 16732e6 * 445692368876987602531346364605670 / 14001112002 / 2**64 = 28873591100892.7358765

        LiqNode storage fourFive = liqTree.nodes[LKey.wrap((2 << 24) | 4)];
        assertEq(fourFive.tokenX.cumulativeEarnedPerMLiq >> 64, 1995430679306434663);
        assertEq(fourFive.tokenX.subtreeCumulativeEarnedPerMLiq >> 64, 1995430679306434663);
        assertEq(fourFive.tokenY.cumulativeEarnedPerMLiq >> 64, 28873591100892);
        assertEq(fourFive.tokenY.subtreeCumulativeEarnedPerMLiq >> 64, 28873591100892);
    }

    function testEarnWhereTotalMLiqIsOnlyFromAuxArray() public {
        /*
         *                                        0-15
         *                                ____----
         *            __________----------
         *        0-7
         *    __--  --__
         *                ---__
         *                        \
         *                       4-7
         *                      /   \
         *                     /     \
         *                    /
         *                4-5
         *               /   \
         *              /     \
         *             4       5
         */
        FeeSnap memory fees;

        // mLiq
        liqTree.addWideRangeMLiq(554000, fees);
        liqTree.addMLiq(range(0, 7), 2000, fees);
        liqTree.addMLiq(range(4, 7), 7000000000, fees);

        // borrows
        liqTree.addTLiq(range(4, 7), 100, fees, 9241e18, 16732e6);

        // trigger fees
        fees.X += 55769907879546549697897755;
        fees.Y += 445692368876987602531346364605670;

        liqTree.addMLiq(range(5, 5), 100, fees);

        // calculate fees

        LiqNode storage fourFive = liqTree.nodes[LKey.wrap((2 << 24) | 4)];
        assertEq(fourFive.tokenX.cumulativeEarnedPerMLiq >> 64, 0);
        assertEq(fourFive.tokenX.subtreeCumulativeEarnedPerMLiq >> 64, 0);
        assertEq(fourFive.tokenY.cumulativeEarnedPerMLiq >> 64, 0);
        assertEq(fourFive.tokenY.subtreeCumulativeEarnedPerMLiq >> 64, 0);
    }

    function testEarnWhereTotalMLiqIsMostlyFromSubtreeMLiq() public {
        /*
         *                    /
         *                4-5
         *               /   \
         *              /     \
         *             4       5
         */
        FeeSnap memory fees;

        // mLiq
        liqTree.addMLiq(range(5, 5), 7000000000, fees);
        liqTree.addMLiq(range(4, 5), 1, fees);

        // borrows
        liqTree.addTLiq(range(5, 5), 1, fees, 9241e18, 16732e6);
        liqTree.addTLiq(range(4, 5), 1, fees, 1241e18, 26732e6);

        // trigger fees
        fees.X += 55769907879546549697897755;
        fees.Y += 445692368876987602531346364605670;

        liqTree.addMLiq(range(5, 5), 100, fees);

        // calculate fees

        // 5-5
        // A[] = 1
        // totalMLiq = 7000000000 + 1 = 7000000001
        // x: 9241e18 * 55769907879546549697897755 / 7000000001 / 2**64 = 3991178347029308150.029573
        // y: 16732e6 * 445692368876987602531346364605670 / 7000000001 / 2**64 = 57751768977971.1297454

        LiqNode storage fiveFive = liqTree.nodes[LKey.wrap((1 << 24) | 5)];
        assertEq(fiveFive.tokenX.cumulativeEarnedPerMLiq >> 64, 3991178347029308150);
        assertEq(fiveFive.tokenX.subtreeCumulativeEarnedPerMLiq >> 64, 3991178347029308150);
        assertEq(fiveFive.tokenY.cumulativeEarnedPerMLiq >> 64, 57751768977971);
        assertEq(fiveFive.tokenY.subtreeCumulativeEarnedPerMLiq >> 64, 57751768977971);

        // 4-5
        // A[] = 0
        // totalMLiq = 7000000000 + 2 = 7000000002
        //  x: 1241e18 * 55769907879546549697897755 / 7000000002 / 2**64 = 535986617028004816.610117
        // sx: (9241e18 + 1241e18) * 55769907879546549697897755 / 7000000002 / 2**64 = 4527164963487144631.5126
        //  y: 26732e6 * 445692368876987602531346364605670 / 7000000002 / 2**64 = 92267528573905.001490
        // sy: (16732e6 + 26732e6) * 445692368876987602531346364605670 / 7000000002 / 2**64 = 150019297543625.878527450

        LiqNode storage fourFive = liqTree.nodes[LKey.wrap((2 << 24) | 4)];
        assertEq(fourFive.tokenX.cumulativeEarnedPerMLiq >> 64, 535986617028004816);
        assertEq(fourFive.tokenX.subtreeCumulativeEarnedPerMLiq >> 64, 4527164963487144631);
        assertEq(fourFive.tokenY.cumulativeEarnedPerMLiq >> 64, 92267528573905);
        assertEq(fourFive.tokenY.subtreeCumulativeEarnedPerMLiq >> 64, 150019297543625);
    }

    function testEarnWhereTotalMLiqIsOnlyFromSubtreeMLiq() public {
        /*
         *                    /
         *                4-5
         *               /   \
         *              /     \
         *             4       5
         */
        FeeSnap memory fees;

        // mLiq
        liqTree.addMLiq(range(5, 5), 7000000000, fees);

        // borrows
        liqTree.addTLiq(range(5, 5), 1, fees, 9241e18, 16732e6);

        // trigger fees
        fees.X += 55769907879546549697897755;
        fees.Y += 445692368876987602531346364605670;

        liqTree.addMLiq(range(5, 5), 100, fees);

        // calculate fees

        // 5-5
        // A[] = 0
        // totalMLiq = 7000000000 = 7000000000
        // x: 9241e18 * 55769907879546549697897755 / 7000000000 / 2**64 = 3991178347599476485.319
        // y: 16732e6 * 445692368876987602531346364605670 / 7000000000 / 2**64 = 57751768986221.3824565

        LiqNode storage fiveFive = liqTree.nodes[LKey.wrap((1 << 24) | 5)];
        assertEq(fiveFive.tokenX.cumulativeEarnedPerMLiq >> 64, 3991178347599476485);
        assertEq(fiveFive.tokenX.subtreeCumulativeEarnedPerMLiq >> 64, 3991178347599476485);
        assertEq(fiveFive.tokenY.cumulativeEarnedPerMLiq >> 64, 57751768986221);
        assertEq(fiveFive.tokenY.subtreeCumulativeEarnedPerMLiq >> 64, 57751768986221);

        // 4-5
        LiqNode storage fourFive = liqTree.nodes[LKey.wrap((2 << 24) | 4)];
        assertEq(fourFive.tokenX.cumulativeEarnedPerMLiq >> 64, 0);
        assertEq(fourFive.tokenX.subtreeCumulativeEarnedPerMLiq >> 64, 3991178347599476485);
        assertEq(fourFive.tokenY.cumulativeEarnedPerMLiq >> 64, 0);
        assertEq(fourFive.tokenY.subtreeCumulativeEarnedPerMLiq >> 64, 57751768986221);
    }

    function testEarnWhereTotalMLiqIsFromBothAuxArrayAndSubtreeMLiq() public {
        /*
         *                        \
         *                       4-7
         *                      /   \
         *                     /     \
         *                    /
         *                4-5
         *               /   \
         *              /     \
         *             4       5
         */
        FeeSnap memory fees;

        // mLiq
        liqTree.addMLiq(range(4, 7), 7000000000, fees);
        liqTree.addMLiq(range(4, 5), 100, fees);
        liqTree.addMLiq(range(5, 5), 7000000000, fees);

        // borrows
        liqTree.addTLiq(range(4, 7), 1, fees, 9241e18, 16732e6);
        liqTree.addTLiq(range(4, 5), 1, fees, 9241e18, 16732e6);
        liqTree.addTLiq(range(5, 5), 1, fees, 9241e18, 16732e6);

        // trigger fees
        fees.X += 55769907879546549697897755;
        fees.Y += 445692368876987602531346364605670;

        liqTree.addMLiq(range(5, 5), 100, fees);

        // calculate fees

        // 4-5 (focus of test)
        // A[] = 7000000000
        // totalMLiq = 7000000000 + 100*2 + 7000000000*2 = 21000000200
        //  x: 9241e18 * 55769907879546549697897755 / 21000000200 / 2**64 = 1330392769862751496.413620
        // sx: (2*9241e18) * 55769907879546549697897755 / 21000000200 / 2**64 = 2660785539725502992.8272402727
        //  y: 16732e6 * 445692368876987602531346364605670 / 21000000200 / 2**64 = 19250589478734.8467
        // sy: (2*16732e6) * 445692368876987602531346364605670 / 21000000200 / 2**64 = 38501178957469.693471

        LiqNode storage fourFive = liqTree.nodes[LKey.wrap((2 << 24) | 4)];
        assertEq(fourFive.tokenX.cumulativeEarnedPerMLiq >> 64, 1330392769862751496);
        assertEq(fourFive.tokenX.subtreeCumulativeEarnedPerMLiq >> 64, 2660785539725502992);
        assertEq(fourFive.tokenY.cumulativeEarnedPerMLiq >> 64, 19250589478734);
        assertEq(fourFive.tokenY.subtreeCumulativeEarnedPerMLiq >> 64, 38501178957469);

        // 5-5
        // A[] = 7000000000 + 100 = 7000000100
        // totalMLiq = 7000000000 + (7000000000 + 100)*1 = 14000000100
        //  x: 9241e18 * 55769907879546549697897755 / 14000000100 / 2**64 = 1995589159545529960.191
        //  y: 16732e6 * 445692368876987602531346364605670 / 14000000100 / 2**64 = 28875884286854.374

        LiqNode storage fiveFive = liqTree.nodes[LKey.wrap((1 << 24) | 5)];
        assertEq(fiveFive.tokenX.cumulativeEarnedPerMLiq >> 64, 1995589159545529960);
        assertEq(fiveFive.tokenX.subtreeCumulativeEarnedPerMLiq >> 64, 1995589159545529960);
        assertEq(fiveFive.tokenY.cumulativeEarnedPerMLiq >> 64, 28875884286854);
        assertEq(fiveFive.tokenY.subtreeCumulativeEarnedPerMLiq >> 64, 28875884286854);

        // 4-7
        // A[] = 0
        // totalMLiq = 7000000000*4 + 100*2 + 7000000000 = 35000000200
        //   x: 9241e18 * 55769907879546549697897755 / 35000000200 / 2**64 = 798235664958548640.15790268
        //  sx: 3*9241e18 * 55769907879546549697897755 / 35000000200 / 2**64 = 2394706994875645920.47370
        //   y: 16732e6 * 445692368876987602531346364605670 / 35000000200 / 2**64 = 11550353731242.2551699
        //  sy: 3*16732e6 * 445692368876987602531346364605670 / 35000000200 / 2**64 = 34651061193726.76550

        LiqNode storage fourSeven = liqTree.nodes[LKey.wrap((4 << 24) | 4)];
        assertEq(fourSeven.tokenX.cumulativeEarnedPerMLiq >> 64, 798235664958548640);
        assertEq(fourSeven.tokenX.subtreeCumulativeEarnedPerMLiq >> 64, 2394706994875645920);
        assertEq(fourSeven.tokenY.cumulativeEarnedPerMLiq >> 64, 11550353731242);
        assertEq(fourSeven.tokenY.subtreeCumulativeEarnedPerMLiq >> 64, 34651061193726);
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
