// SPDX-License-Identifier: BSL-1.1
pragma solidity ^0.8.18;

import { Test } from "forge-std/Test.sol";

import { LiqTree } from "src/Tree.sol";

/**
 * In practice, the LiqTree will have many nodes. So many, that testing at that scale is intractable.
 * Thus the reason for this file. A smaller scale LiqTree, where we can more easily populate the values densely.
 */ 
contract DenseTreeTest is Test {
    LiqTree public liqTree;
    
    function setUp() public {
        // A depth of 4 creates a tree that covers an absolute range of 16 ([0, 15]). 
        // ie. A complete tree matching the ascii documentation. 
        liqTree.init(4);
    }
}
