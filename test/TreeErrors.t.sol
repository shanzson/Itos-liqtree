
// SPDX-License-Identifier: BSL-1.1
pragma solidity ^0.8.18;

import { console } from "forge-std/console.sol";
import { Test } from "forge-std/Test.sol";

import { LiqTree, LiqTreeImpl, LiqRange, LKey, LKeyImpl, LiqNode } from "src/Tree.sol";

contract TreeErrorsTest is Test {
    LiqTree public liqTree;
    using LiqTreeImpl for LiqTree;
    using LKeyImpl for LKey;
    
    function setUp() public {
        // A depth of 4 creates a tree that covers an absolute range of 16 ([0, 15]). 
        // ie. A complete tree matching the ascii documentation. 
        liqTree.init(4);
    }

    function testA() public {
        for (uint24 i = 0; i < 16; i++) {
            for (uint24 j = i; j < 16; j++) {
                if (i == 0 && j == 15) {
                    continue;
                }
                liqTree.addMLiq(LiqRange(i, j), 100);
            }
        }
    }

}