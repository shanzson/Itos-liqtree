// SPDX-License-Identifier: BSL-1.1
pragma solidity ^0.8.18;

struct FeeRateSnapshot {
    uint256 timestamp;
    uint256 cummulativeInterestX128;
}


library FeeRateSnapshotImpl {

    function diff(FeeRateSnapshot storage self, FeeRateSnapshot storage other) external view returns (uint256 cummulativeInterestDiff) {
        cummulativeInterestDiff = self.cummulativeInterestX128 - other.cummulativeInterestX128;
    }

    function add(FeeRateSnapshot storage self, uint256 interestX128) external {
        self.cummulativeInterestX128 += interestX128;
        self.timestamp = block.timestamp;
    }

}
