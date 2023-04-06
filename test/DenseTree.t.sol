// SPDX-License-Identifier: BSL-1.1
pragma solidity ^0.8.18;

import { console } from "forge-std/console.sol";
import { Test } from "forge-std/Test.sol";

import { LiqTree, LiqTreeImpl, LiqRange, LKey, LKeyImpl, LiqNode } from "src/Tree.sol";

/**
 * In practice, the LiqTree will have many nodes. So many, that testing at that scale is intractable.
 * Thus the reason for this file. A smaller scale LiqTree, where we can more easily populate the values densely.
 */ 
contract DenseTreeTest is Test {
    LiqTree public liqTree;
    using LiqTreeImpl for LiqTree;
    using LKeyImpl for LKey;
    
    function setUp() public {
        // A depth of 4 creates a tree that covers an absolute range of 16 ([0, 15]). 
        // ie. A complete tree matching the ascii documentation. 
        liqTree.init(4);
    }

    function testWalkToRootForMLiq() public {
        liqTree.addInfRangeMLiq(140); // root
        liqTree.addMLiq(LiqRange(0, 7), 37); // L
        liqTree.addMLiq(LiqRange(4, 7), 901); // LR
        liqTree.addMLiq(LiqRange(4, 5), 72); // LRL

        // High key corresponds to LRL (low key is LR)
        (, LKey highKey,,) = liqTree.getKeys(4, 5); // LRL
        uint128[] memory mLiqs = liqTree.walkToRootForMLiq(highKey);
        assertEq(mLiqs[0], 72);
        assertEq(mLiqs[1], 901);
        assertEq(mLiqs[2], 37);
        assertEq(mLiqs[3], 140);
    }

    function testExample2Fees() public {
        // Keys

        uint256 t0 = block.timestamp;

        LKey root = liqTree.root;
        LKey L = _nodeKey(1, 0, 16);
        LKey LL = _nodeKey(2, 0, 16);
        LKey LLL = _nodeKey(3, 0, 16);
        LKey LLR = _nodeKey(3, 1, 16);
        LKey LLLR = _nodeKey(4, 1, 16);
        LKey LLRL = _nodeKey(4, 2, 16);

        // Step 1) add maker liq ---------------------------------------------------
        vm.warp(t0);

        // 1.a) Add mLiq to LL ---------------------------------------------------
        liqTree.addMLiq(LiqRange(0, 3), 2);  // LL

        assertEq(liqTree.nodes[root].mLiq, 0);
        assertEq(liqTree.nodes[L].mLiq, 0);
        assertEq(liqTree.nodes[LL].mLiq, 2);

        assertEq(liqTree.nodes[root].subtreeMLiq, 8);
        assertEq(liqTree.nodes[L].subtreeMLiq, 8);
        assertEq(liqTree.nodes[LL].subtreeMLiq, 8);

        // 1.b) Add mLiq to LL ---------------------------------------------------
        liqTree.addMLiq(LiqRange(0, 2), 7);  // LLL, LLRL

        assertEq(liqTree.nodes[root].mLiq, 0);
        assertEq(liqTree.nodes[L].mLiq, 0);
        assertEq(liqTree.nodes[LL].mLiq, 2);
        assertEq(liqTree.nodes[LLL].mLiq, 7);
        assertEq(liqTree.nodes[LLR].mLiq, 0);
        assertEq(liqTree.nodes[LLRL].mLiq, 7);

        assertEq(liqTree.nodes[root].subtreeMLiq, 0 + 0 + 8 + 14 + 0 + 7); // 29
        assertEq(liqTree.nodes[L].subtreeMLiq, 0 + 8 + 14 + 0 + 7); // 29
        assertEq(liqTree.nodes[LL].subtreeMLiq, 8 + 14 + 0 + 7); // 29
        assertEq(liqTree.nodes[LLL].subtreeMLiq, 14);
        assertEq(liqTree.nodes[LLR].subtreeMLiq, 0 + 7);
        assertEq(liqTree.nodes[LLRL].subtreeMLiq, 7);

        // 1.c) Add mliq to L ---------------------------------------------------
        liqTree.addMLiq(LiqRange(0, 7), 20); // L

        assertEq(liqTree.nodes[root].mLiq, 0);
        assertEq(liqTree.nodes[L].mLiq, 20);
        assertEq(liqTree.nodes[LL].mLiq, 2);
        assertEq(liqTree.nodes[LLL].mLiq, 7);
        assertEq(liqTree.nodes[LLR].mLiq, 0);
        assertEq(liqTree.nodes[LLRL].mLiq, 7);

        assertEq(liqTree.nodes[root].subtreeMLiq, 0 + 160 + 8 + 14 + 0 + 7); // 189
        assertEq(liqTree.nodes[L].subtreeMLiq, 160 + 8 + 14 + 0 + 7); // 189
        assertEq(liqTree.nodes[LL].subtreeMLiq, 8 + 14 + 0 + 7); // 29
        assertEq(liqTree.nodes[LLL].subtreeMLiq, 14);
        assertEq(liqTree.nodes[LLR].subtreeMLiq, 0 + 7);
        assertEq(liqTree.nodes[LLRL].subtreeMLiq, 7);

        // Step 2) add taker liq
        vm.warp(t0 + 5);

        // 2.a) add tLiq to LLL
        liqTree.addTLiq(LiqRange(0, 1), 5, 12, 22); // LLL

        assertEq(liqTree.nodes[root].tLiq, 0);
        assertEq(liqTree.nodes[L].tLiq, 0);
        assertEq(liqTree.nodes[LL].tLiq, 0);
        assertEq(liqTree.nodes[LLL].tLiq, 5);
        assertEq(liqTree.nodes[LLR].tLiq, 0);
        assertEq(liqTree.nodes[LLRL].tLiq, 0);

        assertEq(liqTree.nodes[root].borrowedX, 0);
        assertEq(liqTree.nodes[L].borrowedX, 0);
        assertEq(liqTree.nodes[LL].borrowedX, 0);
        assertEq(liqTree.nodes[LLL].borrowedX, 12);
        assertEq(liqTree.nodes[LLR].borrowedX, 0);
        assertEq(liqTree.nodes[LLRL].borrowedX, 0);

        assertEq(liqTree.nodes[root].subtreeBorrowedX, 12);
        assertEq(liqTree.nodes[L].subtreeBorrowedX, 12);
        assertEq(liqTree.nodes[LL].subtreeBorrowedX, 12);
        assertEq(liqTree.nodes[LLL].subtreeBorrowedX, 12);
        assertEq(liqTree.nodes[LLR].subtreeBorrowedX, 0);
        assertEq(liqTree.nodes[LLRL].subtreeBorrowedX, 0);

        assertEq(liqTree.nodes[root].borrowedY, 0);
        assertEq(liqTree.nodes[L].borrowedY, 0);
        assertEq(liqTree.nodes[LL].borrowedY, 0);
        assertEq(liqTree.nodes[LLL].borrowedY, 22);
        assertEq(liqTree.nodes[LLR].borrowedY, 0);
        assertEq(liqTree.nodes[LLRL].borrowedY, 0);

        assertEq(liqTree.nodes[root].subtreeBorrowedY, 22);
        assertEq(liqTree.nodes[L].subtreeBorrowedY, 22);
        assertEq(liqTree.nodes[LL].subtreeBorrowedY, 22);
        assertEq(liqTree.nodes[LLL].subtreeBorrowedY, 22);
        assertEq(liqTree.nodes[LLR].subtreeBorrowedY, 0);
        assertEq(liqTree.nodes[LLRL].subtreeBorrowedY, 0);

        // 2.b) add tLiq to L
        liqTree.addTLiq(LiqRange(0, 7), 9, 3, 4); // L

        assertEq(liqTree.nodes[root].tLiq, 0);
        assertEq(liqTree.nodes[L].tLiq, 9);
        assertEq(liqTree.nodes[LL].tLiq, 0);
        assertEq(liqTree.nodes[LLL].tLiq, 5);
        assertEq(liqTree.nodes[LLR].tLiq, 0);
        assertEq(liqTree.nodes[LLRL].tLiq, 0);

        assertEq(liqTree.nodes[root].borrowedX, 0);
        assertEq(liqTree.nodes[L].borrowedX, 3);
        assertEq(liqTree.nodes[LL].borrowedX, 0);
        assertEq(liqTree.nodes[LLL].borrowedX, 12);
        assertEq(liqTree.nodes[LLR].borrowedX, 0);
        assertEq(liqTree.nodes[LLRL].borrowedX, 0);

        assertEq(liqTree.nodes[root].subtreeBorrowedX, 15);
        assertEq(liqTree.nodes[L].subtreeBorrowedX, 15);
        assertEq(liqTree.nodes[LL].subtreeBorrowedX, 12);
        assertEq(liqTree.nodes[LLL].subtreeBorrowedX, 12);
        assertEq(liqTree.nodes[LLR].subtreeBorrowedX, 0);
        assertEq(liqTree.nodes[LLRL].subtreeBorrowedX, 0);

        assertEq(liqTree.nodes[root].borrowedY, 0);
        assertEq(liqTree.nodes[L].borrowedY, 4);
        assertEq(liqTree.nodes[LL].borrowedY, 0);
        assertEq(liqTree.nodes[LLL].borrowedY, 22);
        assertEq(liqTree.nodes[LLR].borrowedY, 0);
        assertEq(liqTree.nodes[LLRL].borrowedY, 0);

        assertEq(liqTree.nodes[root].subtreeBorrowedY, 26);
        assertEq(liqTree.nodes[L].subtreeBorrowedY, 26);
        assertEq(liqTree.nodes[LL].subtreeBorrowedY, 22);
        assertEq(liqTree.nodes[LLL].subtreeBorrowedY, 22);
        assertEq(liqTree.nodes[LLR].subtreeBorrowedY, 0);
        assertEq(liqTree.nodes[LLRL].subtreeBorrowedY, 0);


        return;

        // Step 3) add new position that effects previous nodes, calculate fees
        vm.warp(t0 + 10);

        liqTree.addMLiq(LiqRange(1, 3), 13); // LLLR, LLR

        // Step 4) verify

        // LLLR
        // 0, 0
        
        // LLL
        // 0, 0.00000000164

        // LL
        // 0.0000000010013052, 0

        // L
        // 
    }

    function _printTree() public {

    }

    function _printKey(LKey k) public {
        {
            (uint24 rootLow, uint24 rootBase) = k.explode();
            console.log("(range, base, num)", rootLow, rootBase, LKey.unwrap(k));
        }
    }

    function _nodeKey(uint24 depth, uint24 index, uint24 offset) public returns (LKey) {
        uint24 baseStep = uint24(offset / 2 ** depth);

        uint24 range = offset >> depth;
        uint24 base = offset + baseStep * index;
        return LKeyImpl.makeKey(range, base);
    }

    function _nodeDepthIndex(uint24 depth, uint24 index, LiqTree storage tree) internal returns (LiqNode storage) {
        return tree.nodes[_nodeKey(depth, index, tree.offset)];
    }
}
