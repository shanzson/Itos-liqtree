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
    uint128 subtreeMinM;
    uint128 subtreeMaxT;
    // Note! Not updated by the liq functions below.
    uint128 subtreeMLiq;
    LiqNodeTokenData tokenX;
    LiqNodeTokenData tokenY;
}

library LiqNodeImpl {
    function addMLiq(LiqNode storage self, uint128 liq) external {
        self.mLiq += liq;
        self.subtreeMinM += liq;
    }

    function removeMLiq(LiqNode storage self, uint128 liq) external {
        self.mLiq -= liq;
        self.subtreeMinM -= liq;
    }

    function addTLiq(LiqNode storage self, uint128 liq) external {
        self.tLiq += liq;
        self.subtreeMaxT += liq;
    }

    function removeTLiq(LiqNode storage self, uint128 liq) external {
        self.tLiq -= liq;
        self.subtreeMaxT -= liq;
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
