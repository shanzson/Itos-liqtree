// SPDX-License-Identifier: BSL-1.1
pragma solidity ^0.8.18;

import { console } from "forge-std/console.sol";
import { PRBTest } from "@prb/test/PRBTest.sol";
import { LiqTree, LiqTreeImpl, LiqTreeIntLib } from "src/Tree.sol";
import { LKey, LKeyImpl, LiqRange, FeeSnap } from "src/Tree.sol";

// solhint-disable

/// @dev See the "Writing Tests" section in the Foundry Book if this is your first time with Forge.
/// https://book.getfoundry.sh/forge/writing-tests
contract LiqTreeTest is PRBTest {
    using LiqTreeImpl for LiqTree;

    LiqTree public t;

    function setUp() public {
        t.init(0x13); // 19 gives 80000 as the offset.
    }

    function assertWideGap(int256 gap) private {
        int256 actualGap = t.queryWideLiqGap();
        assertEq(actualGap, gap);
    }

    function testWide() public {
        FeeSnap memory fees;

        assertWideGap(0);
        t.addWideRangeMLiq(10, fees);
        assertWideGap(10);
        t.addWideRangeMLiq(10, fees);
        assertWideGap(20);

        t.addWideRangeTLiq(10, fees, 0, 0);
        assertWideGap(10);

        // Going over won't happen in practice but we should still test.
        t.addWideRangeTLiq(20, fees, 0, 0);
        assertWideGap(-10);

        t.removeWideRangeMLiq(10, fees);
        assertWideGap(-20);

        t.removeWideRangeTLiq(30, fees, 0, 0);
        assertWideGap(10);

        // And adding mliq anywhere else won't change the wide min gap.
        t.addMLiq(LiqRange(100, 200), 10, fees);
        assertWideGap(10);

        // Adding tliq though, will lower the min gap.
        t.addTLiq(LiqRange(300, 400), 10, fees, 0, 0);
        assertWideGap(0);
    }

    function assertGap(
        int24 low,
        int24 high,
        int256 gap
    ) public {
        int256 actualGap = t.queryLiqGap(LiqRange(low, high));
        assertEq(actualGap, gap);
    }

    function testMLiq() public {
        FeeSnap memory fees;

        // Single-node tests
        t.addMLiq(LiqRange(0, 0), 10, fees);
        assertGap(0, 0, 10);
        assertWideGap(0);
        assertGap(0, 1, 0);
        assertGap(0, 100, 0);

        t.addMLiq(LiqRange(0, 1), 10, fees);
        // Now we have 0:20, 1:10
        assertGap(0, 0, 20);
        assertGap(1, 1, 10);
        assertGap(0, 1, 10);
        assertGap(0, 100, 0);
        assertGap(1, 2, 0);
        assertWideGap(0);

        t.addMLiq(LiqRange(0, 7), 10, fees);
        // 0:30, 1: 20, 2-7: 10
        assertGap(0, 0, 30);
        assertGap(1, 1, 20);
        assertGap(1, 2, 10);
        assertGap(3, 5, 10);
        assertGap(20, 30, 0);

        t.removeMLiq(LiqRange(0, 1), 10, fees);
        // 0:20, 1-7: 10
        assertGap(0, 0, 20);
        assertGap(1, 3, 10);
        assertGap(0, 7, 10);

        t.removeMLiq(LiqRange(0, 7), 3, fees);
        // 0:17, 1-7: 7
        assertGap(0, 0, 17);
        assertGap(0, 7, 7);
        assertGap(0, 8, 0);

        // Multi-node tests
        t.addMLiq(LiqRange(500, 800), 100, fees);
        assertWideGap(0);
        assertGap(500, 800, 100);
        assertGap(600, 700, 100);
        assertGap(400, 900, 0);

        t.addMLiq(LiqRange(0, 500), 200, fees);
        assertGap(0, 800, 100);
        assertGap(400, 700, 100);

        t.addMLiq(LiqRange(400, 600), 300, fees);
        assertGap(0, 800, 100);
        assertGap(400, 600, 400);
        assertGap(400, 500, 500);
        assertGap(500, 600, 400);

        // Undo the last one
        t.removeMLiq(LiqRange(400, 600), 300, fees);
        assertGap(0, 800, 100);
        assertGap(400, 600, 100);
        assertGap(400, 500, 200);
        assertGap(500, 600, 100);
    }

    function testAddMLiqGas(int24 low, uint8 _highOff) public {
        FeeSnap memory fees;
        int24 highOff = int24(uint24(_highOff));
        // Within range.
        vm.assume(-int24(t.width / 2) <= low);
        vm.assume(low < int24(t.width / 2 - _highOff));

        t.addMLiq(LiqRange(low, low + highOff), 10, fees);
    }

    function testTLiq() public {
        FeeSnap memory fees;
        t.addTLiq(LiqRange(6, 6), 10, fees, 0, 0);
        assertGap(6, 6, -10);
        assertWideGap(-10);
        assertGap(6, 7, -10);
        assertGap(0, 100, -10);
        assertGap(7, 10, 0);

        // Test consecutive nodes
        t.addTLiq(LiqRange(7, 7), 5, fees, 0, 0);
        assertGap(6, 7, -10);
        assertGap(7, 7, -5);
        assertGap(6, 6, -10);
        assertGap(0, 100, -10);
        assertGap(50, 100, 0);
        assertWideGap(-10);

        // Test larger ranges
        t.addTLiq(LiqRange(5, 100), 50, fees, 0, 0);
        assertWideGap(-60);
        assertGap(0, 4, 0);
        assertGap(0, 5, -50);
        assertGap(100, 500, -50);
        assertGap(101, 500, 0);
        assertGap(5, 100, -60);
    }

    // Test that the tree correctly reports the smallest gap anywhere.
    function testGaps() public {
        // We have 4 sections.
        // 1. One high mLiq area.
        // 2. One medium mLiq area.
        // 3. One low mLiq area.
        // 4. The ambient liquidity everywhere.
        FeeSnap memory fees;
        // 4.
        t.addWideRangeMLiq(100 gwei, fees);
        // 1.
        t.addMLiq(LiqRange(-100, -5), 10 ether, fees);
        assertWideGap(100 gwei);
        assertGap(-500, 0, 100 gwei);
        // 2.
        t.addMLiq(LiqRange(100, 500), 1 ether, fees);
        assertWideGap(100 gwei);
        // 3.
        t.addMLiq(LiqRange(1000, 5000), 10 gwei, fees);

        // We add tLiq to each section to make the gaps smaller
        // 1.
        t.addTLiq(LiqRange(-50, -50), 10 ether + 10 gwei, fees, 0, 0);
        assertWideGap(90 gwei);
        assertGap(-500, -51, 100 gwei);
        assertGap(-500, -50, 90 gwei);
        // 2.
        t.addTLiq(LiqRange(150, 200), 1 ether + 20 gwei, fees, 0, 0);
        assertWideGap(80 gwei);
        assertGap(0, 100, 100 gwei);
        assertGap(0, 150, 80 gwei);
        // 3.
        t.addTLiq(LiqRange(1500, 2000), 40 gwei, fees, 0, 0);
        assertWideGap(70 gwei);
        assertGap(0, 1000, 80 gwei);
        assertGap(1600, 6000, 70 gwei);
        // 1.
        t.addTLiq(LiqRange(-51, -45), 30 gwei, fees, 0, 0);
        assertWideGap(60 gwei);
        assertGap(-5000, -5, 60 gwei);
        // 4.
        t.addTLiq(LiqRange(-500, -400), 50 gwei, fees, 0, 0);
        assertWideGap(50 gwei);
        assertGap(-5000, -5, 50 gwei);
    }
}

contract LiqTreeIntTest is PRBTest {
    using LiqTreeIntLib for uint24;
    using LKeyImpl for LKey;

    uint24 fauxMinKeyBase = 0x200000;
    uint24 fauxMaxKeyBase = 0x3fffff;

    function testLSB() public {
        // We actually don't rely on this because it will never happen. But I'm curious if it does the natural thing.
        assertEq(0, uint24(0).lsb());
        assertEq(0x80, uint24(0x80).lsb());
        assertEq(0x80, uint24(0xFFCA80).lsb());
        assertEq(0x04, uint24(0x65432C).lsb());
    }

    function assertLCA(
        uint24 a,
        uint24 b,
        uint24 common,
        uint24 commonRange
    ) public {
        (LKey peak, LKey peakRange) = LiqTreeIntLib.lowestCommonAncestor(a, b);
        (uint24 range, uint24 base) = peak.explode();
        assertEq(base, common);
        assertEq(range, commonRange);
        assertEq(range, LKey.unwrap(peakRange) >> 24);
    }

    function testLowestCommonAncestor() public {
        assertLCA(0xAB1234, 0xAB0234, 0xAB0000, 0x002000);
        assertLCA(0x123456, 0x123456, 0x123456, 0x000001);
        assertLCA(0xFEDCB8, 0xFEDCBA, 0xFEDCB8, 0x000004);
        // Range of 0 for totally different values (meaning the whole range).
        assertLCA(0x800000, 0x700000, 0x000000, 0x000000);
        // Just the first two bits are in common.
        assertLCA(0x800000, 0xA00000, 0x800000, 0x400000);
    }

    function testLowKey(uint24 low) public {
        vm.assume(fauxMinKeyBase <= low);
        vm.assume(low <= fauxMaxKeyBase);
        LKey l = low.lowKey();
        assertTrue(l.isRight());
        (, uint24 base) = l.explode();
        assertEq(base, low);
    }

    function testHighKey(uint24 high) public {
        vm.assume(fauxMinKeyBase <= high);
        vm.assume(high <= fauxMaxKeyBase);
        LKey h = high.highKey();
        assertTrue(h.isLeft());
        (uint24 range, uint24 base) = h.explode();
        // The last element in our key range should be the high value.
        assertEq(base + range - 1, high);
    }

    // function testRangeBounds()
    // TODO
}

contract LKeyTest is PRBTest {
    using LKeyImpl for LKey;

    uint24 fauxMinKeyBase = 0x200000;
    uint24 fauxMaxKeyBase = 0x3fffff;

    function testMakeKey(uint24 range, uint24 base) public {
        LKey key = LKeyImpl.makeKey(range, base);
        (uint24 eRange, uint24 eBase) = key.explode();
        assertEq(base, eBase);
        assertEq(range, eRange);
    }

    function subtestAdjacency(
        LKey up,
        LKey left,
        LKey right
    ) public {
        (uint24 prange, ) = up.explode();
        (, uint24 lbase) = left.explode();
        (uint24 rrange, uint24 rbase) = right.explode();

        LKey lAdj = right.getNextLeftAdjacent();
        LKey rAdj = left.getNextRightAdjacent();
        (uint24 lAdjRange, uint24 lAdjBase) = lAdj.explode();
        // One of the adjacent nodes must be at our parents level.
        if (lAdjRange == prange) {
            {
                // The other should be at a higher level
                (uint24 rAdjRange, ) = rAdj.explode();
                assertTrue(rAdjRange > prange);
                assertTrue((rrange + rbase) == lAdjBase);
            }
            {
                assertTrue(LKey.unwrap(up.rightSib()) == LKey.unwrap(lAdj));
            }
        } else {
            {
                (uint24 rAdjRange, uint24 rAdjBase) = rAdj.explode();
                assertTrue(rAdjRange == prange);
                assertTrue(lAdjRange > prange);
                assertTrue((rAdjRange + rAdjBase) == lbase);
            }
            {
                assertTrue(LKey.unwrap(up.leftSib()) == LKey.unwrap(rAdj));
            }
        }
    }

    function testLKeyImpl(uint8 rangeNum, uint24 base) public {
        unchecked {
            base += fauxMinKeyBase;
            // Don't need the modulo since we're in uint24
            // base %= fauxMaxKeyBase;
        }
        uint24 range = uint24(1 << (rangeNum % 16));
        // We can only work with bases that are 0 beyond the range. Otherwise not a node.
        vm.assume(base % range == 0);

        LKey up;
        LKey left;
        LKey right;
        {
            LKey key = LKeyImpl.makeKey(range, base);
            if (key.isLeft()) {
                (up, right) = key.leftUp();
                left = key;
            } else {
                (up, left) = key.rightUp();
                right = key;
            }
            assertTrue(right.isRight());
            assertTrue(left.isLeft());
        }

        // Test children
        {
            (LKey pLeft, LKey pRight) = up.children();
            assertTrue(left.isEq(pLeft));
            assertTrue(right.isEq(pRight));
            assertTrue(left.isNeq(pRight));
            assertTrue(right.isNeq(pLeft));
        }

        // Test bases and ranges directly.
        (uint24 prange, uint24 pbase) = up.explode();
        (uint24 lrange, uint24 lbase) = left.explode();
        (uint24 rrange, uint24 rbase) = right.explode();
        assertEq(lrange, rrange);
        assertEq(lrange, prange >> 1);
        assertEq(lbase, pbase);
        assertEq(lbase, rbase ^ lrange);

        // Test generic up
        {
            (LKey gUp, LKey gOther) = left.genericUp();
            assertTrue(gOther.isEq(right));
            assertTrue(gUp.isEq(up));
            (gUp, gOther) = right.genericUp();
            assertTrue(gOther.isEq(left));
            assertTrue(gUp.isEq(up));
        }

        // Test sib functions
        {
            assertTrue(right.isEq(left.rightSib()));
            assertTrue(left.isEq(right.leftSib()));
        }

        // Test Adjacency.
        subtestAdjacency(up, left, right);
    }
}
