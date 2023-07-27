// SPDX-License-Identifier: BSL-1.1
pragma solidity ^0.8.18;

import { Test, stdError } from "forge-std/Test.sol";

import { LiqNode, LiqNodeImpl } from "../src/LiqNode.sol";

contract LiqNodeTest is Test {
    using LiqNodeImpl for LiqNode;

    LiqNode public node;

    function testBorrow() public {
        node.borrow(220, 550);
        assertEq(node.tokenX.borrow, 220);
        assertEq(node.tokenX.subtreeBorrow, 220);
        assertEq(node.tokenY.borrow, 550);
        assertEq(node.tokenY.subtreeBorrow, 550);
    }

    function testRepay() public {
        node.borrow(220, 550);
        node.repay(100, 200);
        assertEq(node.tokenX.borrow, 120);
        assertEq(node.tokenX.subtreeBorrow, 120);
        assertEq(node.tokenY.borrow, 350);
        assertEq(node.tokenY.subtreeBorrow, 350);
    }

    function testRevertRepayingMoreThanborrow() public {
        vm.expectRevert(stdError.arithmeticError);
        node.repay(100, 200);
    }

    function testGap() public {
        node.mLiq = 100;
        node.tLiq = 50;
        assertEq(node.gap(), 50);
        node.tLiq = 150;
        assertEq(node.gap(), -50);
    }
}
