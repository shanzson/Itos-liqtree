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
