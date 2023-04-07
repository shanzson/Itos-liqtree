// SPDX-License-Identifier: BSL-1.1
pragma solidity ^0.8.18;

struct FeeRateSnapshot {
    uint256 timestamp;
    uint256 cummulativeInterestX64;
}


library FeeRateSnapshotImpl {

    function diff(FeeRateSnapshot storage self, FeeRateSnapshot storage other) external view returns (uint256 cummulativeInterestDiff) {
        cummulativeInterestDiff = self.cummulativeInterestX64 - other.cummulativeInterestX64;
    }

    function add(FeeRateSnapshot storage self, uint256 interestX128) external {
        self.cummulativeInterestX64 += interestX128;
        self.timestamp = block.timestamp;
    }

}
