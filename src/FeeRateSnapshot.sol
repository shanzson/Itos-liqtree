// SPDX-License-Identifier: BSL-1.1
pragma solidity ^0.8.18;

struct FeeRateSnapshot {
    uint256 timestamp;
    uint256 cummulativeInterest; // should this be 256?
}


library FeeRateSnapshotImpl {

    function diff(FeeRateSnapshot storage self, FeeRateSnapshot storage other) external view returns (uint256 cummulativeInterestDiff) {
        cummulativeInterestDiff = self.cummulativeInterest - other.cummulativeInterest;
    }

    function add(FeeRateSnapshot storage self, uint256 interest) external {
        self.cummulativeInterest += interest;
        self.timestamp = block.timestamp;
    }

}
