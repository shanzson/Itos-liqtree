// SPDX-License-Identifier: BSL-1.1
pragma solidity ^0.8.13;

/// The type we use for storing liquidity
type Liq is uint128;

library LiqImpl {
    function add(Liq self, int128 delta) internal pure returns (Liq) {
        if (delta < 0) {
            return Liq.wrap(Liq.unwrap(self) - uint128(-delta));
        } else {
            return Liq.wrap(Liq.unwrap(self) + uint128(delta));
        }
    }

    function sub(Liq self, int128 delta) internal pure returns (Liq) {
        if (delta < 0) {
            return Liq.wrap(Liq.unwrap(self) + uint128(-delta));
        } else {
            return Liq.wrap(Liq.unwrap(self) - uint128(delta));
        }
    }

    function isLT(Liq self, Liq other) internal pure returns (bool) {
        return Liq.unwrap(self) < Liq.unwrap(other);
    }

    function isEq(Liq self, uint256 other) internal pure returns (bool) {
        return Liq.unwrap(self) == other;
    }

    function isLTEq(Liq self, uint256 other) internal pure returns (bool) {
        return Liq.unwrap(self) <= other;
    }
}
