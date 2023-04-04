// SPDX-License-Identifier: BSL-1.1
pragma solidity ^0.8.18;

struct LiqNode {
    uint128 mLiq;
    uint128 tLiq;

    uint256 borrowedX;
    uint256 borrowedY;

    uint256 subtreeBorrowedX;
    uint256 subtreeBorrowedY;

    // --- above this line is used 100%

    // The first four are for liquidity constraints
    //uint128 mLiq;
    //uint128 tLiq; // This is also used for fees.
    uint128 subtreeMinM;
    uint128 subtreeMaxT;

    uint128 subtreeMLiq;

    // snapshot

    uint128 cummulativeXEarnedPerMLiq;
    uint128 cummulativeYEarnedPerMLiq;

    // DEPRECATED
    uint128 subtreeMaxM;
}

library LiqNodeImpl {

    function addMLiq(LiqNode storage self, uint128 liq) external {
         self.mLiq += liq;
         self.subtreeMinM += liq;
         self.subtreeMaxM += liq;
    }

    function removeMLiq(LiqNode storage self, uint128 liq) external {
         self.mLiq -= liq;
         self.subtreeMinM -= liq;
         self.subtreeMaxM -= liq;
    }

    function addTLiq(LiqNode storage self, uint128 liq) external {
        self.tLiq += liq;
        self.subtreeMaxT += liq;
    }

    function removeTLiq(LiqNode storage self, uint128 liq) external {
        self.tLiq -= liq;
        self.subtreeMaxT -= liq;
    }

    function borrow(LiqNode storage self, uint256 amountX, uint256 amountY) external {
        self.borrowedX += amountX;
        self.borrowedY += amountY;
        self.subtreeBorrowedX += amountX;
        self.subtreeBorrowedY += amountY;
    }

    function repay(LiqNode storage self, uint256 amountX, uint256 amountY) external {
        self.borrowedX -= amountX;
        self.borrowedY -= amountY;
        self.subtreeBorrowedX -= amountX;
        self.subtreeBorrowedY -= amountY;
    }

}