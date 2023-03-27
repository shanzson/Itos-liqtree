// SPDX-License-Identifier: BSL-1.1
pragma solidity ^0.8.18;

import { Test } from "forge-std/Test.sol";

import { SuffixSumLib } from "../src/SuffixSumLib.sol";

contract SuffixSumLibTest is Test {
    using SuffixSumLib for uint256[];

    function testSuffixSumOfEmptyArray() public {
        uint256[] memory arr;
        assertEq(arr.suffixSum().length, 0);
    }

    function testSuffixSumOfSingleItemArray() public {
        uint256[] memory arr = new uint256[](1);
        arr[0] = 1;

        uint256[] memory suffixSum = arr.suffixSum();
        assertEq(suffixSum.length, 1);
        assertEq(suffixSum[0], 1);
    }

    function testSuffixSumOfMultiItemArray() public {
        uint256[] memory arr = new uint256[](4);
        arr[0] = arr[1] = arr[2] = arr[3] = 2;

        uint256[] memory suffixSum = arr.suffixSum();
        assertEq(suffixSum.length, 4);
        assertEq(suffixSum[0], 8);
        assertEq(suffixSum[1], 6);
        assertEq(suffixSum[2], 4);
        assertEq(suffixSum[3], 2);
    }

}
