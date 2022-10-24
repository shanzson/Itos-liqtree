// SPDX-License-Identifier: BSL-1.1
pragma solidity ^0.8.13;

import { console } from "forge-std/console.sol";
import { PRBTest } from "@prb/test/PRBTest.sol";
import { LiqTree, LiqTreeImpl, LiqTreeIntLib } from "src/Tree.sol";
import { LKey, LKeyImpl } from "src/Tree.sol";

/// @dev See the "Writing Tests" section in the Foundry Book if this is your first time with Forge.
/// https://book.getfoundry.sh/forge/writing-tests
contract LiqTreeTest is PRBTest {
    function setUp() public {
        // solhint-disable-previous-line no-empty-blocks
    }
}

contract LiqTreeIntTest is PRBTest {
    using LiqTreeIntLib for uint24;
    using LKeyImpl for LKey;

    function testLSB() public {
        // We actually don't rely on this because it will never happen. But I'm curious if it does the natural thing.
        assertEq(0, uint24(0).lsb());
        assertEq(0x80, uint24(0x80).lsb());
        assertEq(0x80, uint24(0xFFCA80).lsb());
        assertEq(0x04, uint24(0x65432C).lsb());
    }

    function assertLCA(uint24 a, uint24 b, uint24 common, uint24 commonRange) public {
        LKey key = LiqTreeIntLib.lowestCommonAncestor(a, b);
        (uint24 base, uint24 range) = key.explode();
        assertEq(base, common);
        assertEq(range, commonRange);
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

}

contract LKeyTest is PRBTest {
    using LKeyImpl for LKey;

    function isOneHot(uint24 x) public pure returns (bool) {
        unchecked {
            return (x != 0) && ((x - 1) & x == 0);
        }
    }

    function testMakeKey(uint24 base, uint24 range) public {
        LKey key = LKeyImpl.makeKey(base, range);
        (uint24 eBase, uint24 eRange) = key.explode();
        assertEq(base, eBase);
        assertEq(range, eRange);
    }

    function testLKeyImpl(uint24 base, uint24 range) public {
        // Range must be one hot.
        vm.assume(isOneHot(range));

        LKey key = LKeyImpl.makeKey(base, range);
        LKey up;
        LKey left;
        LKey right;
        if (key.isLeft()) {
            (up, right) = key.leftUp();
            left = key;
        } else {
            (up, left) = key.rightUp();
            right = key;
        }
        assertTrue(right.isRight());
        assertTrue(left.isLeft());
        // Test children
        (LKey pLeft, LKey pRight) = up.children();
        assertTrue(left.isEq(pLeft));
        assertTrue(right.isEq(pRight));
        assertTrue(left.isNeq(pRight));
        assertTrue(right.isNeq(pLeft));
        // Test bases and ranges directly.
        (uint24 pbase, uint24 prange) = up.explode();
        (uint24 lbase, uint24 lrange) = left.explode();
        (uint24 rbase, uint24 rrange) = right.explode();
        assertEq(lrange, rrange);
        assertEq(lrange, prange >> 1);
        assertEq(lbase, pbase);
        assertEq(lbase, rbase ^ lrange);
        // Test generic up
        (LKey gUp, LKey gOther) = left.genericUp();
        assertTrue(gOther.isEq(right));
        assertTrue(gUp.isEq(up));
        (gUp, gOther) = right.genericUp();
        assertTrue(gOther.isEq(left));
        assertTrue(gUp.isEq(up));
        // Test sib functions
        assertTrue(right.isEq(left.rightSib()));
        assertTrue(left.isEq(right.leftSib()));
    }
}
