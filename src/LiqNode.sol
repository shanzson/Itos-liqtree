// SPDX-License-Identifier: BSL-1.1
pragma solidity ^0.8.17;

// solhint-disable

struct LiqNodeTokenData {
    uint256 borrow;
    uint256 subtreeBorrow;
    uint256 feeRateSnapshot;
    uint256 cumulativeEarnedPerMLiq;
    uint256 subtreeCumulativeEarnedPerMLiq;
}

struct LiqNode {
    uint128 mLiq;
    uint128 tLiq;

    uint128 subtreeMLiq;
    int256 subtreeMinGap;

    LiqNodeTokenData tokenX;
    LiqNodeTokenData tokenY;
}

library LiqNodeImpl {
    function gap(LiqNode storage self) internal view returns (int256) {
        return int256(uint256(self.mLiq)) - int256(uint256(self.tLiq));
    }

    function borrow(
        LiqNode storage self,
        uint256 amountX,
        uint256 amountY
    ) external {
        self.tokenX.borrow += amountX;
        self.tokenY.borrow += amountY;
        self.tokenX.subtreeBorrow += amountX;
        self.tokenY.subtreeBorrow += amountY;
    }

    function repay(
        LiqNode storage self,
        uint256 amountX,
        uint256 amountY
    ) external {
        self.tokenX.borrow -= amountX;
        self.tokenY.borrow -= amountY;
        self.tokenX.subtreeBorrow -= amountX;
        self.tokenY.subtreeBorrow -= amountY;
    }
}
