// SPDX-License-Identifier: BSL-1.1
pragma solidity ^0.8.18;

import { Test } from "forge-std/Test.sol";

import { FeeRateSnapshot, FeeRateSnapshotImpl } from "src/FeeRateSnapshot.sol";
import { LiqTree, LiqTreeImpl, LiqRange, LKey, LKeyImpl, LiqNode } from "src/Tree.sol";


contract SparseTreeGasTest is Test {
    LiqTree public liqTree;
    using LiqTreeImpl for LiqTree;
    using LKeyImpl for LKey;
    using FeeRateSnapshotImpl for FeeRateSnapshot;
    
    function setUp() public {
        liqTree.init(21); // max depth (0 - 2097152)
    }

    function testAddMLiq() public {
        // TODO: call testAddMLiq a lot (similar below)
    }

    function testRemoveMLiq() public {

    }

    function testAddTLiq() public {

    }

    function testRemoveTLiq() public {

    }

    function testAddInfRangeMLiq() public {

    }

    function testRemoveInfRangeMLiq() public {

    }

    function testAddInfRangeTLiq() public {

    }

    function testRemoveInfRangeTLiq() public {

    }

}