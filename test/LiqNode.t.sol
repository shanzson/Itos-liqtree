// SPDX-License-Identifier: BSL-1.1
pragma solidity ^0.8.18;

import { Test, stdError } from "forge-std/Test.sol";

import { LiqNode, LiqNodeImpl } from "../src/LiqNode.sol";

contract LiqNodeTest is Test {
    using LiqNodeImpl for LiqNode;

    LiqNode public node;

    function testAddMLiq() public {
        node.addMLiq(483);
        assertEq(node.mLiq, 483);
        assertEq(node.subtreeMinM, 483);
        assertEq(node.subtreeMaxM, 483);
    }

    function testRemoveMLiq() public {
        node.addMLiq(483);
        node.removeMLiq(480);
        assertEq(node.mLiq, 3);
        assertEq(node.subtreeMinM, 3);
        assertEq(node.subtreeMaxM, 3);
    }

    function testRevertRemoveMLiqExceedingMLiqAdded() public {
        vm.expectRevert(stdError.arithmeticError);
        node.removeMLiq(100);
    }

    function testAddTLiq() public {
        node.addTLiq(928);
        assertEq(node.tLiq, 928);
        assertEq(node.subtreeMaxT, 928);
    }

    function testRemoveTLiq() public {
        node.addTLiq(928);
        node.removeTLiq(1);
        assertEq(node.tLiq, 927);
        assertEq(node.subtreeMaxT, 927);
    }

    function testRevertRemoveTLiqExceedingTLiqAdded() public {
        vm.expectRevert(stdError.arithmeticError);
        node.removeTLiq(100);
    }

    function testBorrow() public {
        node.borrow(220, 550);
        assertEq(node.borrowedX, 220);
        assertEq(node.subtreeBorrowedX, 220);
        assertEq(node.borrowedY, 550);
        assertEq(node.subtreeBorrowedY, 550);
    }

    function testRepay() public {
        node.borrow(220, 550);
        node.repay(100, 200);
        assertEq(node.borrowedX, 120);
        assertEq(node.subtreeBorrowedX, 120);
        assertEq(node.borrowedY, 350);
        assertEq(node.subtreeBorrowedY, 350);
    }

    function testRevertRepayingMoreThanBorrowed() public {
        vm.expectRevert(stdError.arithmeticError);
        node.repay(100, 200);
    }

}
