// SPDX-License-Identifier: BSL-1.1
pragma solidity ^0.8.18;

import { Test, stdError } from "forge-std/Test.sol";

import { FeeRateSnapshot, FeeRateSnapshotImpl } from "../src/FeeRateSnapshot.sol";

contract FeeRateSnapshotTest is Test {
    using FeeRateSnapshotImpl for FeeRateSnapshot;

    FeeRateSnapshot public t0;
    FeeRateSnapshot public t1;

    function setUp() public {
        t0 = FeeRateSnapshot(0, 10);
        t1 = FeeRateSnapshot(1, 15);
    }

    function testDiff() public {
        assertEq(t1.diff(t0), 5);
    }

    function testDiffOfSelf() public {
        assertEq(t0.diff(t0), 0);
    }

    function testRevertOnDiffGoingBackInTime() public {
        vm.expectRevert(stdError.arithmeticError);
        t0.diff(t1);
    }

    function testAdd() public {
        vm.warp(10);
        t1.add(100);
        assertEq(t1.timestamp, 10);
        assertEq(t1.cummulativeInterestX128, 115);
    }

    function testAddZero() public {
        vm.warp(10);
        t1.add(0);
        assertEq(t1.timestamp, 10);
        assertEq(t1.cummulativeInterestX128, 15);
    }

}
