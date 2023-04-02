// SPDX-License-Identifier: BSL-1.1
pragma solidity ^0.8.18;

struct LiqNode {
    // The first four are for liquidity constraints
    uint128 mLiq;
    uint128 tLiq; // This is also used for fees.
    uint128 subtreeMinM;
    uint128 subtreeMaxT;

    uint128 subtreeMLiq;
    
    uint128 borrowedX;
    uint128 borrowedY;

    uint128 subtreeBorrowedX;
    uint128 subtreeBorrowedY;

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

}