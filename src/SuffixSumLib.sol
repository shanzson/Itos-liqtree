// SPDX-License-Identifier: BSL-1.1
pragma solidity ^0.8.18;

library SuffixSumLib {

    function suffixSum(uint256[] memory self) external returns (uint256[] memory suffixSum) {
        uint256 length = self.length;
        if (length == 0 || length == 1) {
            return self;
        }

        suffixSum = new uint256[](length);

        --length;
        suffixSum[length] = self[length];
        --length;

        while (length >= 0) {
            suffixSum[length] = self[length] + suffixSum[length + 1];

            if (length == 0) {
                break;
            }

            --length;
        }
    }

}
