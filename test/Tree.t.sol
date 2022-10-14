// SPDX-License-Identifier: BSL-1.1
pragma solidity ^0.8.13;

import { console } from "forge-std/console.sol";
import { PRBTest } from "@prb/test/PRBTest.sol";
import { LiqTreeLib} from "Tree.sol";


/// @dev See the "Writing Tests" section in the Foundry Book if this is your first time with Forge.
/// https://book.getfoundry.sh/forge/writing-tests
contract LiqTreeTest is PRBTest {
    function setUp() public {
        // solhint-disable-previous-line no-empty-blocks
    }
}

contract LiqTreeLibTest is PRBTest {

    function testRangeBreakdown() public {
        (LKey[MAX_TREE_DEPTH] memory upKeys, LKey[MAX_TREE_DEPTH] memory downKeys) = LiqTreeLib._rangeBreakdown(low, high);


    }

    function testLSB() public {
        // We actually don't rely on this because it will never happen. But I'm curious if it does the natural thing.
        assertEq(0, LiqTreeLib.lsb(0));
    }
}
