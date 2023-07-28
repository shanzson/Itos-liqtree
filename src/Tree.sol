// SPDX-License-Identifier: BSL-1.1
pragma solidity ^0.8.17;
// solhint-disable

// import { console2 } from "forge-std/console2.sol";
import { LiqNode, LiqNodeImpl } from "./LiqNode.sol";
import { Math } from "./Math.sol";

/**
 *  Liquidity Tree
 *
 *  Consider a tree with a depth of 4
 *
 *                                                              root
 *                                                      ____----    ----____
 *                                  __________----------                    ----------__________
 *                                 L                                                            R
 *                            __--  --__                                                    __--  --__
 *                       __---          ---__                                          __---          ---__
 *                     /                       \                                     /                       \
 *                  LL                           LR                               RL                           RR
 *                /   \                         /   \                           /   \                         /   \
 *              /       \                     /       \                       /       \                     /       \
 *            /           \                 /           \                   /           \                 /           \
 *          LLL            LLR            LRL            LRR              RLL            RLR            RRL            RRR
 *         /   \          /   \          /   \          /   \            /   \          /   \          /   \          /   \
 *        /     \        /     \        /     \        /     \          /     \        /     \        /     \        /     \
 *     LLLL    LLLR    LLRL    LLRR   LRLL    LRLR   LRRL    LRRR      RLLL   RLLR   RLRL    RLRR   RRLL    RRLR   RRRL    RRRR
 *
 *
 *
 *
 *                                                              0-15
 *                                                      ____----    ----____
 *                                  __________----------                    ----------__________
 *                                0-7                                                          8-15
 *                            __--  --__                                                    __--  --__
 *                       __---          ---__                                          __---          ---__
 *                     /                       \                                     /                       \
 *                  0-3                          4-7                             8-11                         12-15
 *                /   \                         /   \                           /   \                         /   \
 *              /       \                     /       \                       /       \                     /       \
 *            /           \                 /           \                   /           \                 /           \
 *          0-1            2-3            4-5            6-7              8-9           10-11          12-13          14-15
 *         /   \          /   \          /   \          /   \            /   \          /   \          /   \          /   \
 *        /     \        /     \        /     \        /     \          /     \        /     \        /     \        /     \
 *       0       1      2       3      4       5      6       7        8       9      10      11    12      13      14     15
 **/

/// I would totally rewrite this differently.
/// Querying is not just using the break down.
/// Traversals are always done so I would have prioritize cheapening those.
/// But the change should not be insanely difficult.

type LKey is uint48;
// Even if we use 1 as the tick spacing, we still won't have over 2^21 ticks, so 22 bits.
uint8 constant MAX_TREE_DEPTH = 22;

// This is okay as the NIL key because it can't possibly be used in any breakdowns since the depth portion of
// the lkey is one-hot.
LKey constant LKeyNIL = LKey.wrap(0xFFFFFFFFFFFF);

// This stay in memory so each have their own slots.
struct LiqRange {
    int24 low;
    int24 high;
}

/*
 * @notice A struct for querying the liquidity available in a given range. It's similar to a combination of a
 * segment tree and an augmented tree.
 * @author Terence An and Austin Urlaub
 */
struct LiqTree {
    mapping(LKey => LiqNode) nodes;
    LKey root; // maxRange << 24;
    uint24 width; // This is the range at root and double the offset.
}

// Single stack pointer for the fees from a user.
// The precision is left up to the user.
struct FeeSnap {
    uint256 X;
    uint256 Y;
}

// Helper for tracking state accross traversals.
struct State {
    FeeSnap rateSnap;
    FeeSnap accumulatedFees;
    uint256[MAX_TREE_DEPTH] auxMLiqs;
    uint8 auxIdx;
    // The liquidity change our operation is introducting.
    uint128 liqDiff;
    // The borrow changes.
    uint256 xDiff;
    uint256 yDiff;
    // Used for tracking liquidity bounds in removeMLiq and addTLiq.
    int256 gapTracker;
    // tracker backup. The Trackers are leg specific, so we have to save those results.
    // When switching to the other side.
    int256 gapBackup;

    // We waste a little space because xDiff and accumulatedFees are never used
    // together but IMO it's fine.
}

library LiqTreeImpl {
    using LKeyImpl for LKey;
    using LiqNodeImpl for LiqNode;
    using LiqTreeIntLib for uint24;

    error RangeBoundsInverted(int24 rangeLow, int24 rangeHigh);
    error RangeHighOutOfBounds(int24 rangeHigh, uint24 maxRange);
    error ConcentratedWideRangeUsed(int24 rangeLow, int24 rangeHigh);

    /****************************
     * Initialization Functions *
     ****************************/

    function init(LiqTree storage self, uint8 maxDepth) internal {
        require(maxDepth <= MAX_TREE_DEPTH, "MTD");
        uint24 maxRange = uint24(1 << (maxDepth - 1));

        self.root = LKeyImpl.makeKey(maxRange, 0);
        self.width = maxRange;
    }

    /*********************
     * Interface Methods *
     *********************/

    function addMLiq(
        LiqTree storage self,
        LiqRange memory range,
        uint128 liq,
        FeeSnap memory rates
    ) public returns (uint256 accumulatedFeeRateX, uint256 accumulatedFeeRateY) {
        State memory state;
        state.liqDiff = liq;
        state.rateSnap = rates;

        _traverse(self, range, addMLiqVisit, addMLiqPropogate, state);

        accumulatedFeeRateX = state.accumulatedFees.X;
        accumulatedFeeRateY = state.accumulatedFees.Y;
    }

    function removeMLiq(
        LiqTree storage self,
        LiqRange memory range,
        uint128 liq,
        FeeSnap memory rates
    )
        public
        returns (
            uint256 accumulatedFeeRateX,
            uint256 accumulatedFeeRateY,
            int256 liqGap
        )
    {
        State memory state;
        state.liqDiff = liq;
        state.rateSnap = rates;

        state.gapTracker = type(int256).max;
        state.gapBackup = type(int256).max;

        _traverse(self, range, removeMLiqVisit, removeMLiqPropogate, state);

        accumulatedFeeRateX = state.accumulatedFees.X;
        accumulatedFeeRateY = state.accumulatedFees.Y;

        liqGap = state.gapTracker;
    }

    function addTLiq(
        LiqTree storage self,
        LiqRange memory range,
        uint128 liq,
        FeeSnap memory rates,
        uint256 borrowedX,
        uint256 borrowedY
    ) public returns (int256 liqGap) {
        State memory state;
        state.liqDiff = liq;
        state.rateSnap = rates;

        state.gapTracker = type(int256).max;
        state.gapBackup = type(int256).max;

        // TODO: Test replacing this with the actual per node borrow calculation.
        uint256 width = uint24(range.high - range.low + 1);
        state.xDiff = borrowedX / width;
        state.yDiff = borrowedY / width;

        _traverse(self, range, addTLiqVisit, addTLiqPropogate, state);

        liqGap = state.gapTracker;
    }

    function removeTLiq(
        LiqTree storage self,
        LiqRange memory range,
        uint128 liq,
        FeeSnap memory rates,
        uint256 borrowedX,
        uint256 borrowedY
    ) public {
        State memory state;
        state.liqDiff = liq;
        state.rateSnap = rates;
        // TODO: Test replacing this with the actual per node borrow calculation.
        uint256 width = uint24(range.high - range.low + 1);
        state.xDiff = borrowedX / width;
        state.yDiff = borrowedY / width;

        _traverse(self, range, removeTLiqVisit, removeTLiqPropogate, state);
    }

    function addWideRangeMLiq(
        LiqTree storage self,
        uint128 liq,
        FeeSnap memory rates
    ) external returns (uint256 accumulatedFeeRateX, uint256 accumulatedFeeRateY) {
        LiqNode storage rootNode = self.nodes[self.root];

        _handleFee(rootNode, rates, 0);
        accumulatedFeeRateX = rootNode.tokenX.subtreeCumulativeEarnedPerMLiq;
        accumulatedFeeRateY = rootNode.tokenY.subtreeCumulativeEarnedPerMLiq;

        rootNode.mLiq += liq;
        rootNode.subtreeMLiq += self.width * liq;
        rootNode.subtreeMinGap += int256(uint256(liq));
    }

    function removeWideRangeMLiq(
        LiqTree storage self,
        uint128 liq,
        FeeSnap memory rates
    )
        external
        returns (
            uint256 accumulatedFeeRateX,
            uint256 accumulatedFeeRateY,
            int256 liqGap
        )
    {
        LiqNode storage rootNode = self.nodes[self.root];

        _handleFee(rootNode, rates, 0);
        accumulatedFeeRateX = rootNode.tokenX.subtreeCumulativeEarnedPerMLiq;
        accumulatedFeeRateY = rootNode.tokenY.subtreeCumulativeEarnedPerMLiq;

        rootNode.mLiq -= liq;
        rootNode.subtreeMLiq -= self.width * liq;

        liqGap = rootNode.subtreeMinGap - int256(uint256(liq));
        rootNode.subtreeMinGap = liqGap;
    }

    function addWideRangeTLiq(
        LiqTree storage self,
        uint128 liq,
        FeeSnap memory rates,
        uint256 amountX,
        uint256 amountY
    ) external returns (int256 liqGap) {
        LiqNode storage rootNode = self.nodes[self.root];

        _handleFee(rootNode, rates, 0);

        rootNode.tLiq += liq;
        rootNode.tokenX.borrow += amountX;
        rootNode.tokenX.subtreeBorrow += amountX;
        rootNode.tokenY.borrow += amountY;
        rootNode.tokenY.subtreeBorrow += amountY;

        liqGap = rootNode.subtreeMinGap - int256(uint256(liq));
        rootNode.subtreeMinGap = liqGap;
    }

    function removeWideRangeTLiq(
        LiqTree storage self,
        uint128 liq,
        FeeSnap memory rates,
        uint256 amountX,
        uint256 amountY
    ) external {
        LiqNode storage rootNode = self.nodes[self.root];

        _handleFee(rootNode, rates, 0);

        rootNode.tLiq -= liq;
        rootNode.tokenX.borrow -= amountX;
        rootNode.tokenX.subtreeBorrow -= amountX;
        rootNode.tokenY.borrow -= amountY;
        rootNode.tokenY.subtreeBorrow -= amountY;

        rootNode.subtreeMinGap += int256(uint256(liq));
    }

    /*******************
     ** Range Queries **
     *******************/

    function queryEarnRates(
        LiqTree storage self,
        LiqRange memory range,
        FeeSnap memory rates
    ) public view returns (uint256 accumulatedFeeRateX, uint256 accumulatedFeeRateY) {
        State memory state;
        state.rateSnap = rates;

        _traverseView(self, range, queryEarnVisit, queryEarnPropogate, state);

        accumulatedFeeRateX = state.accumulatedFees.X;
        accumulatedFeeRateY = state.accumulatedFees.Y;
    }

    function queryWideEarnRates(LiqTree storage self, FeeSnap memory rates)
        public
        view
        returns (uint256 accumulatedFeeRateX, uint256 accumulatedFeeRateY)
    {
        LiqNode storage rootNode = self.nodes[self.root];
        (accumulatedFeeRateX, accumulatedFeeRateY) = _viewSubtreeFee(rootNode, rates, 0);
    }

    function queryLiqGap(LiqTree storage self, LiqRange memory range) public view returns (int256 liqGap) {
        State memory state;
        state.gapTracker = type(int256).max;
        state.gapBackup = type(int256).max;
        _traverseView(self, range, queryLiqGapVisit, queryLiqGapPropogate, state);
        liqGap = state.gapTracker;
    }

    function queryWideLiqGap(LiqTree storage self) public view returns (int256 liqGap) {
        LiqNode storage rootNode = self.nodes[self.root];
        liqGap = rootNode.subtreeMinGap;
    }

    /*********************************
     * Visit and Propogate functions *
     *********************************/

    function addMLiqVisit(
        LKey key,
        LiqNode storage node,
        State memory state
    ) internal {
        (uint24 rangeWidth, ) = key.explode();

        uint256 aboveMLiq = state.auxMLiqs[state.auxIdx] * rangeWidth;
        _handleFee(node, state.rateSnap, aboveMLiq);

        // Update the subtreeMLiq after collecting fees.
        node.mLiq += state.liqDiff;
        node.subtreeMLiq += state.liqDiff * rangeWidth;
        node.subtreeMinGap += int256(uint256(state.liqDiff));

        state.accumulatedFees.X += node.tokenX.subtreeCumulativeEarnedPerMLiq;
        state.accumulatedFees.Y += node.tokenY.subtreeCumulativeEarnedPerMLiq;
    }

    function addMLiqPropogate(
        LiqNode storage a,
        LiqNode storage b,
        LKey up,
        LiqNode storage parent,
        State memory state
    ) internal {
        (uint24 rangeWidth, ) = up.explode();

        // Move up in the aux array since we're moving up a level.
        uint256 aboveMLiq = state.auxMLiqs[++state.auxIdx] * rangeWidth;
        _handleFee(parent, state.rateSnap, aboveMLiq);

        parent.subtreeMLiq = a.subtreeMLiq + b.subtreeMLiq + parent.mLiq * rangeWidth;
        parent.subtreeMinGap = min(a.subtreeMinGap, b.subtreeMinGap) + parent.gap();

        state.accumulatedFees.X += parent.tokenX.cumulativeEarnedPerMLiq;
        state.accumulatedFees.Y += parent.tokenY.cumulativeEarnedPerMLiq;
    }

    function removeMLiqVisit(
        LKey key,
        LiqNode storage node,
        State memory state
    ) internal {
        (uint24 rangeWidth, ) = key.explode();

        uint256 aboveMLiq = state.auxMLiqs[state.auxIdx] * rangeWidth;
        _handleFee(node, state.rateSnap, aboveMLiq);

        // Update the subtreeMLiq after fees have been collected
        node.mLiq -= state.liqDiff;
        node.subtreeMLiq -= state.liqDiff * rangeWidth;
        node.subtreeMinGap -= int256(uint256(state.liqDiff));

        // Track gap
        state.gapTracker = min(state.gapTracker, node.subtreeMinGap);

        state.accumulatedFees.X += node.tokenX.subtreeCumulativeEarnedPerMLiq;
        state.accumulatedFees.Y += node.tokenY.subtreeCumulativeEarnedPerMLiq;
    }

    function removeMLiqPropogate(
        LiqNode storage a,
        LiqNode storage b,
        LKey up,
        LiqNode storage parent,
        State memory state
    ) internal {
        (uint24 rangeWidth, ) = up.explode();
        // Move up in the aux array since we're moving up a level.
        uint256 aboveMLiq = state.auxMLiqs[++state.auxIdx] * rangeWidth;
        _handleFee(parent, state.rateSnap, aboveMLiq);

        parent.subtreeMLiq = a.subtreeMLiq + b.subtreeMLiq + parent.mLiq * rangeWidth;
        parent.subtreeMinGap = min(a.subtreeMinGap, b.subtreeMinGap) + parent.gap();

        state.gapTracker += parent.gap();

        state.accumulatedFees.X += parent.tokenX.cumulativeEarnedPerMLiq;
        state.accumulatedFees.Y += parent.tokenY.cumulativeEarnedPerMLiq;
    }

    function addTLiqVisit(
        LKey key,
        LiqNode storage node,
        State memory state
    ) internal {
        (uint24 rangeWidth, ) = key.explode();

        // Handle fees first
        uint256 aboveMLiq = state.auxMLiqs[state.auxIdx] * rangeWidth;
        _handleFee(node, state.rateSnap, aboveMLiq);

        node.tLiq += state.liqDiff;
        node.tokenX.borrow += state.xDiff * rangeWidth;
        node.tokenX.subtreeBorrow += state.xDiff * rangeWidth;
        node.tokenY.borrow += state.yDiff * rangeWidth;
        node.tokenY.subtreeBorrow += state.yDiff * rangeWidth;

        int256 gap = node.subtreeMinGap - int256(uint256(state.liqDiff));
        state.gapTracker = min(state.gapTracker, gap);
        node.subtreeMinGap = gap;
    }

    function addTLiqPropogate(
        LiqNode storage a,
        LiqNode storage b,
        LKey up,
        LiqNode storage parent,
        State memory state
    ) internal {
        (uint24 rangeWidth, ) = up.explode();

        // Move up in the aux array since we're moving up a level.
        uint256 aboveMLiq = state.auxMLiqs[++state.auxIdx] * rangeWidth;
        _handleFee(parent, state.rateSnap, aboveMLiq);

        state.gapTracker += parent.gap();

        parent.tokenX.subtreeBorrow = a.tokenX.subtreeBorrow + b.tokenX.subtreeBorrow + parent.tokenX.borrow;
        parent.tokenY.subtreeBorrow = a.tokenY.subtreeBorrow + b.tokenY.subtreeBorrow + parent.tokenY.borrow;
        parent.subtreeMinGap = min(a.subtreeMinGap, b.subtreeMinGap) + parent.gap();
    }

    function removeTLiqVisit(
        LKey key,
        LiqNode storage node,
        State memory state
    ) internal {
        (uint24 rangeWidth, ) = key.explode();

        // Handle fees first
        uint256 aboveMLiq = state.auxMLiqs[state.auxIdx] * rangeWidth;
        _handleFee(node, state.rateSnap, aboveMLiq);

        node.tLiq -= state.liqDiff;
        node.tokenX.borrow -= state.xDiff * rangeWidth;
        node.tokenX.subtreeBorrow -= state.xDiff * rangeWidth;
        node.tokenY.borrow -= state.yDiff * rangeWidth;
        node.tokenY.subtreeBorrow -= state.yDiff * rangeWidth;
        node.subtreeMinGap += int256(uint256(state.liqDiff));
    }

    function removeTLiqPropogate(
        LiqNode storage a,
        LiqNode storage b,
        LKey up,
        LiqNode storage parent,
        State memory state
    ) internal {
        (uint24 rangeWidth, ) = up.explode();

        // Move up in the aux array since we're moving up a level.
        uint256 aboveMLiq = state.auxMLiqs[++state.auxIdx] * rangeWidth;
        _handleFee(parent, state.rateSnap, aboveMLiq);

        parent.subtreeMinGap = min(a.subtreeMinGap, b.subtreeMinGap) + parent.gap();
        parent.tokenX.subtreeBorrow = a.tokenX.subtreeBorrow + b.tokenX.subtreeBorrow + parent.tokenX.borrow;
        parent.tokenY.subtreeBorrow = a.tokenY.subtreeBorrow + b.tokenY.subtreeBorrow + parent.tokenY.borrow;
    }

    function queryEarnVisit(
        LKey key,
        LiqNode storage node,
        State memory state
    ) internal view {
        (uint24 rangeWidth, ) = key.explode();
        uint256 aboveMLiq = state.auxMLiqs[state.auxIdx] * rangeWidth;
        (uint256 subtreeX, uint256 subtreeY) = _viewSubtreeFee(node, state.rateSnap, aboveMLiq);

        state.accumulatedFees.X += subtreeX;
        state.accumulatedFees.Y += subtreeY;
    }

    function queryEarnPropogate(
        LiqNode storage,
        LiqNode storage,
        LKey up,
        LiqNode storage parent,
        State memory state
    ) internal view {
        (uint24 rangeWidth, ) = up.explode();
        uint256 aboveMLiq = state.auxMLiqs[++state.auxIdx] * rangeWidth;
        (uint256 x, uint256 y) = _viewFee(parent, state.rateSnap, aboveMLiq);

        state.accumulatedFees.X += x;
        state.accumulatedFees.Y += y;
    }

    // @dev Not really used outside of testing
    function queryLiqGapVisit(
        LKey,
        LiqNode storage node,
        State memory state
    ) internal view {
        state.gapTracker = min(state.gapTracker, node.subtreeMinGap);
    }

    function queryLiqGapPropogate(
        LiqNode storage,
        LiqNode storage,
        LKey,
        LiqNode storage parent,
        State memory state
    ) internal view {
        state.gapTracker += parent.gap();
    }

    /***********/
    /* Helpers */
    /***********/

    function _traverse(
        LiqTree storage self,
        LiqRange memory range,
        function(LKey, LiqNode storage, State memory) internal visit,
        function(LiqNode storage, LiqNode storage, LKey, LiqNode storage, State memory) internal propogate,
        State memory state
    ) internal {
        (LKey low, LKey high, , LKey stopRange) = getKeys(self, range.low, range.high);

        LKey current;
        LiqNode storage node;

        if (low.isLess(stopRange)) {
            computeAuxArray(self, low, state.auxMLiqs);
            // Reset height index.
            state.auxIdx = 0;
            current = _traverseLeft(self, low, stopRange, visit, propogate, state);
        }

        if (high.isLess(stopRange)) {
            // Now we're on the other leg so we swap the tracker.
            (state.gapTracker, state.gapBackup) = (state.gapBackup, state.gapTracker);

            computeAuxArray(self, high, state.auxMLiqs);
            // Reset height index.
            state.auxIdx = 0;
            current = _traverseRight(self, high, stopRange, visit, propogate, state);
        }
        // We could return the node to save this lookup hash, but the compiler doesn't know
        // we are guaranteed to go through one of the above two branches, so it'll complain
        // node is unassigned before use.
        node = self.nodes[current];

        // Both legs are handled. Touch up everything above where we left off.
        // For visits using liquidity tracking, at this point they'll need to merge their results.
        // We do it for them to avoid using more stack pointers.
        state.gapTracker = min(state.gapTracker, state.gapBackup);

        // We are guaranteed to have visited the left or the right side, so our node and
        // current are already prefilled and current has already been propogated to.
        // Peak propogate.
        LKey up;
        LiqNode storage sib;
        while (current.isLess(self.root)) {
            {
                LKey other;
                (up, other) = current.genericUp();
                sib = self.nodes[other];
            }
            LiqNode storage parent = self.nodes[up];
            propogate(sib, node, up, parent, state);
            (current, node) = (up, parent);
        }
    }

    function _traverseLeft(
        LiqTree storage self,
        LKey current,
        LKey stopRange,
        function(LKey, LiqNode storage, State memory) internal visit,
        function(LiqNode storage, LiqNode storage, LKey, LiqNode storage, State memory) internal propogate,
        State memory state
    ) internal returns (LKey last) {
        LiqNode storage node = self.nodes[current];

        visit(current, node, state);
        // A propogate always follows a visit.
        LKey up;
        LiqNode storage sib;
        {
            LKey left;
            (up, left) = current.rightUp();
            sib = self.nodes[left];
        }
        LiqNode storage parent = self.nodes[up];
        propogate(sib, node, up, parent, state);
        (current, node) = (up, parent);

        while (current.isLess(stopRange)) {
            if (current.isLeft()) {
                current = current.rightSib();
                node = self.nodes[current];

                visit(current, node, state);
            }
            {
                LKey left;
                (up, left) = current.rightUp();
                sib = self.nodes[left];
            }
            parent = self.nodes[up];
            propogate(sib, node, up, parent, state);
            (current, node) = (up, parent);
        }
        last = current;
    }

    function _traverseRight(
        LiqTree storage self,
        LKey current,
        LKey stopRange,
        function(LKey, LiqNode storage, State memory) internal visit,
        function(LiqNode storage, LiqNode storage, LKey, LiqNode storage, State memory) internal propogate,
        State memory state
    ) internal returns (LKey last) {
        LiqNode storage node = self.nodes[current];

        visit(current, node, state);
        // A propogate always follows
        (LKey up, LKey right) = current.leftUp();
        LiqNode storage parent = self.nodes[up];
        LiqNode storage sib = self.nodes[right];
        propogate(node, sib, up, parent, state);

        (current, node) = (up, parent);

        while (current.isLess(stopRange)) {
            if (current.isRight()) {
                current = current.leftSib();
                node = self.nodes[current];

                visit(current, node, state);
            }
            (up, right) = current.leftUp();
            parent = self.nodes[up];
            sib = self.nodes[right];
            propogate(node, sib, up, parent, state);

            (current, node) = (up, parent);
        }
        last = current;
    }

    function _traverseView(
        LiqTree storage self,
        LiqRange memory range,
        function(LKey, LiqNode storage, State memory) internal view visit,
        function(LiqNode storage, LiqNode storage, LKey, LiqNode storage, State memory) internal view propogate,
        State memory state
    ) internal view {
        (LKey low, LKey high, , LKey stopRange) = getKeys(self, range.low, range.high);

        LKey current;
        LiqNode storage node;

        if (low.isLess(stopRange)) {
            computeAuxArray(self, low, state.auxMLiqs);
            // Reset height index.
            state.auxIdx = 0;
            current = _traverseLeftView(self, low, stopRange, visit, propogate, state);
        }
        if (high.isLess(stopRange)) {
            // Now we're on the other leg so we swap the liq trackers.
            (state.gapTracker, state.gapBackup) = (state.gapBackup, state.gapTracker);

            computeAuxArray(self, low, state.auxMLiqs);
            // Reset height index.
            state.auxIdx = 0;
            current = _traverseRightView(self, high, stopRange, visit, propogate, state);
        }
        // We could return the node to save this lookup hash, but the compiler doesn't know
        // we are guaranteed to go through one of the above two branches, so it'll complain
        // node is unassigned before use.
        node = self.nodes[current];

        // Both legs are handled. Touch up everything above where we left off.
        // For visits using liquidity tracking, at this point they'll need to merge their results.
        // We do it for them to avoid using more stack pointers.
        state.gapTracker = min(state.gapTracker, state.gapBackup);

        // We are guaranteed to have visited the left or the right side, so our node and
        // current are already prefilled and current has already been propogated to.
        // Peak propogate.
        LKey up;
        LiqNode storage sib;
        while (current.isLess(self.root)) {
            {
                LKey other;
                (up, other) = current.genericUp();
                sib = self.nodes[other];
            }
            LiqNode storage parent = self.nodes[up];
            propogate(sib, node, up, parent, state);
            (current, node) = (up, parent);
        }
    }

    function _traverseLeftView(
        LiqTree storage self,
        LKey current,
        LKey stopRange,
        function(LKey, LiqNode storage, State memory) internal view visit,
        function(LiqNode storage, LiqNode storage, LKey, LiqNode storage, State memory) internal view propogate,
        State memory state
    ) internal view returns (LKey last) {
        LiqNode storage node = self.nodes[current];

        visit(current, node, state);
        // A propogate always follows a visit.
        LKey up;
        LiqNode storage sib;
        {
            LKey left;
            (up, left) = current.rightUp();
            sib = self.nodes[left];
        }
        LiqNode storage parent = self.nodes[up];
        propogate(sib, node, up, parent, state);
        (current, node) = (up, parent);

        while (current.isLess(stopRange)) {
            if (current.isLeft()) {
                current = current.rightSib();
                node = self.nodes[current];

                visit(current, node, state);
            }
            {
                LKey left;
                (up, left) = current.rightUp();
                sib = self.nodes[left];
            }
            parent = self.nodes[up];
            propogate(sib, node, up, parent, state);
            (current, node) = (up, parent);
        }
        last = current;
    }

    function _traverseRightView(
        LiqTree storage self,
        LKey current,
        LKey stopRange,
        function(LKey, LiqNode storage, State memory) internal view visit,
        function(LiqNode storage, LiqNode storage, LKey, LiqNode storage, State memory) internal view propogate,
        State memory state
    ) internal view returns (LKey last) {
        LiqNode storage node = self.nodes[current];

        visit(current, node, state);
        // A propogate always follows
        (LKey up, LKey right) = current.leftUp();
        LiqNode storage parent = self.nodes[up];
        LiqNode storage sib = self.nodes[right];
        propogate(node, sib, up, parent, state);

        (current, node) = (up, parent);

        while (current.isLess(stopRange)) {
            if (current.isRight()) {
                current = current.leftSib();
                node = self.nodes[current];

                visit(current, node, state);
            }
            (up, right) = current.leftUp();
            parent = self.nodes[up];
            sib = self.nodes[right];
            propogate(node, sib, up, parent, state);

            (current, node) = (up, parent);
        }
        last = current;
    }

    function _handleFee(
        LiqNode storage node,
        FeeSnap memory fees,
        uint256 aboveMLiq
    ) internal {
        uint256 rateDiffX = fees.X - node.tokenX.feeRateSnapshot;
        node.tokenX.feeRateSnapshot = fees.X;
        uint256 rateDiffY = fees.Y - node.tokenY.feeRateSnapshot;
        node.tokenY.feeRateSnapshot = fees.Y;

        uint256 totalMLiq = node.subtreeMLiq + aboveMLiq; // At most 24 + 132 = 156 bits

        if (totalMLiq > 0) {
            node.tokenX.cumulativeEarnedPerMLiq += Math.shortMulDiv(node.tokenX.borrow, rateDiffX, totalMLiq);
            node.tokenX.subtreeCumulativeEarnedPerMLiq += Math.shortMulDiv(
                node.tokenX.subtreeBorrow,
                rateDiffX,
                totalMLiq
            );

            node.tokenY.cumulativeEarnedPerMLiq += Math.shortMulDiv(node.tokenY.borrow, rateDiffY, totalMLiq);
            node.tokenY.subtreeCumulativeEarnedPerMLiq += Math.shortMulDiv(
                node.tokenY.subtreeBorrow,
                rateDiffY,
                totalMLiq
            );
        }
    }

    function _viewFee(
        LiqNode storage node,
        FeeSnap memory snap,
        uint256 aboveMLiq
    ) internal view returns (uint256 earnedX, uint256 earnedY) {
        uint256 rateDiffX = snap.X - node.tokenX.feeRateSnapshot;
        uint256 rateDiffY = snap.Y - node.tokenY.feeRateSnapshot;
        uint256 totalMLiq = node.subtreeMLiq + aboveMLiq; // At most 24 + 132 = 156 bits
        if (totalMLiq > 0) {
            earnedX = Math.shortMulDiv(node.tokenX.borrow, rateDiffX, totalMLiq);
            earnedY = Math.shortMulDiv(node.tokenY.borrow, rateDiffY, totalMLiq);
        }
    }

    function _viewSubtreeFee(
        LiqNode storage node,
        FeeSnap memory snap,
        uint256 aboveMLiq
    ) internal view returns (uint256 subtreeEarnedX, uint256 subtreeEarnedY) {
        uint256 rateDiffX = snap.X - node.tokenX.feeRateSnapshot;
        uint256 rateDiffY = snap.Y - node.tokenY.feeRateSnapshot;
        uint256 totalMLiq = node.subtreeMLiq + aboveMLiq; // At most 24 + 132 = 156 bits
        if (totalMLiq > 0) {
            subtreeEarnedX = Math.shortMulDiv(node.tokenX.subtreeBorrow, rateDiffX, totalMLiq);
            subtreeEarnedY = Math.shortMulDiv(node.tokenY.subtreeBorrow, rateDiffY, totalMLiq);
        }
    }

    /// Precompute the auxilliary liquidities for a starting LKey (low or high leg).
    function computeAuxArray(
        LiqTree storage self,
        LKey start,
        uint256[MAX_TREE_DEPTH] memory auxMLiqs
    ) internal view {
        // Fill the array with the mLiq from its parent.
        uint8 idx = 0;
        (uint24 range, uint24 base) = start.explode();
        while (!start.isEq(self.root)) {
            (start, ) = start.genericUp();
            (range, base) = start.explode();
            auxMLiqs[idx++] = self.nodes[start].mLiq;
        }
        // We reuse this array between the two legs so ensure the root has an aux MLiq of 0.
        auxMLiqs[idx] = 0;

        // Iterate backwards collecting the previous MLiq into the partial suffix sums.
        uint256 suffixSum = 0;
        while (idx > 0) {
            suffixSum += auxMLiqs[--idx];
            auxMLiqs[idx] = suffixSum;
        }
    }

    /***********************************
     * Raw int range to LKey functions *
     ***********************************/

    /// Preprocessing to convert the user's zero centered, MAX_DEPTH bound int indices into
    /// our uint indices, the LKey's we use to work with. This also tells us where traversals should stop.
    function getKeys(
        LiqTree storage self,
        int24 rangeLow, // inclusive
        int24 rangeHigh // inclusive
    )
        public
        view
        returns (
            LKey low,
            LKey high,
            LKey peak,
            LKey stopRange
        )
    {
        // The offset specifies the whole range the indices can span centered around 0.
        // We can make everything positive by shifting half the range.
        rangeLow += int24(self.width / 2);
        rangeHigh += int24(self.width / 2);

        require(rangeLow >= 0, "NL");

        if (rangeLow > rangeHigh) revert RangeBoundsInverted(rangeLow, rangeHigh);
        if (rangeHigh >= int24(self.width)) revert RangeHighOutOfBounds(rangeHigh, self.width);
        // No one should be able to specifc the whole range. We rely on not having peak be equal to root
        // when we traverse the tree because stoprange can sometimes be one above the peak.
        if (rangeLow == 0 && (rangeHigh == int24(self.width - 1)))
            revert ConcentratedWideRangeUsed(rangeLow, rangeHigh);

        return getRangeBounds(self, uint24(rangeLow), uint24(rangeHigh));
    }

    /// The work-horse for get keys and finds the stop range for us.
    /// Here we coerce the range keys to the ones we expect in our proofs.
    /// I.e. A one-sided trapezoid has one key equal to the peak.
    function getRangeBounds(
        LiqTree storage self,
        uint24 rangeLow,
        uint24 rangeHigh
    )
        public
        view
        returns (
            LKey low,
            LKey high,
            LKey peak,
            LKey limitRange
        )
    {
        LKey peakRange;
        (peak, peakRange) = LiqTreeIntLib.lowestCommonAncestor(rangeLow, rangeHigh);

        low = LiqTreeIntLib.lowKey(rangeLow);
        high = LiqTreeIntLib.highKey(rangeHigh);
        // There is a special case where low is 0 which means it has no left nodes on its path to root
        // and has no LSB. We make sure to test that a lowKey(0) == 0;
        // Here we need to put that 0 back in the context of the tree and make it the root node.
        if (LKey.unwrap(low) == 0) low = self.root;

        bool lowBelow = low.isLess(peakRange);
        bool highBelow = high.isLess(peakRange);

        // Case on whether left and right are below the peak range or not.
        if (lowBelow && highBelow) {
            // The simple case where we can just walk up both legs.
            // Each individual leg will stop at the children of the peak,
            // so our limit range is one below peak range.
            limitRange = LKey.wrap(LKey.unwrap(peakRange) >> 1);
            // Note this ONLY works because we can't possibly want to visit
            // the nodes one below the peak. We only ever want to propogate into it.
        } else if (lowBelow && !highBelow) {
            // We only have the left leg to worry about.
            // So our limit range will be at the peak, because we can propogate into the peak
            // but we'll never want to visit it.
            limitRange = peakRange;
        } else if (!lowBelow && highBelow) {
            // Just the right leg. Same idea as the case above.
            limitRange = peakRange;
        } else {
            // One of the starts is the peak!
            // We don't modify our keys and limit at one above the peak.
            limitRange = LKey.wrap(LKey.unwrap(peakRange) << 1);
        }
    }

    /**********
     ** MISC **
     **********/

    /// Convenience function for minimum of uint128s
    function min(uint128 a, uint128 b) private pure returns (uint128) {
        return (a <= b) ? a : b;
    }

    /// Convenience function for minimum of int256s
    function min(int256 a, int256 b) private pure returns (int256) {
        return (a <= b) ? a : b;
    }

    // /// Convenience function for maximum of uint128s
    // function max(uint128 a, uint128 b) private pure returns (uint128) {
    //     return (a >= b) ? a : b;
    // }
}

library LiqTreeIntLib {
    // LiqTreeInts are uint24 values that don't have a range. Their assumed range is 1.
    // They are used to specify the range [low, high].
    using LKeyImpl for LKey;

    /// Get the key for the node that represents the lowest bound of our range.
    /// This works by finding the first right sided node that contains this value.
    /// @dev Only to be used by getRangeBounds
    function lowKey(uint24 low) internal pure returns (LKey) {
        return LKeyImpl.makeKey(lsb(low), low);
    }

    /// Get the key for the node that is the inclusive high of our exclusive range.
    /// This works by finding the first left sided node that contains this value.
    /// @dev Only to be used by getRangeBounds
    function highKey(uint24 high) internal pure returns (LKey) {
        // Add one to propogate past any trailing ones
        // Then use lsb to find the range before zero-ing it out to get our left sided node.
        unchecked {
            high += 1;
            uint24 range = lsb(high);
            return LKeyImpl.makeKey(range, high ^ range);
        }
    }

    /// Get the node that is the lowest common ancestor of both the low and high nodes.
    /// This is the peak of our range breakdown which does not modify its liq.
    function lowestCommonAncestor(uint24 low, uint24 high) internal pure returns (LKey peak, LKey peakRange) {
        // Find the bitwise common prefix by finding the bits not in a common prefix.
        // This way uses less gas than directly finding the common prefix.
        uint32 diffMask = 0x00FFFFFF;
        uint256 diffBits = uint256(low ^ high);

        if (diffBits & 0xFFF000 == 0) {
            diffMask >>= 12;
            diffBits <<= 12;
        }

        if (diffBits & 0xFC0000 == 0) {
            diffMask >>= 6;
            diffBits <<= 6;
        }

        if (diffBits & 0xE00000 == 0) {
            diffMask >>= 3;
            diffBits <<= 3;
        }

        if (diffBits & 0xC00000 == 0) {
            diffMask >>= 2;
            diffBits <<= 2;
        }

        if (diffBits & 0x800000 == 0) {
            diffMask >>= 1;
            // we don't need diffBits anymore
        }

        uint24 commonMask = uint24(~diffMask);
        uint24 base = commonMask & low;
        uint24 range = lsb(commonMask);

        return (LKeyImpl.makeKey(range, base), LKeyImpl.makeKey(range, 0));
    }

    /// @dev this returns 0 for 0
    function lsb(uint24 x) internal pure returns (uint24) {
        unchecked {
            return x & (~x + 1);
        }
    }
}

library LKeyImpl {
    function makeKey(uint24 range, uint24 base) internal pure returns (LKey) {
        return LKey.wrap((uint48(range) << 24) | uint48(base));
    }

    function explode(LKey self) internal pure returns (uint24 range, uint24 base) {
        uint48 all = LKey.unwrap(self);
        base = uint24(all);
        range = uint24(all >> 24);
    }

    function isEq(LKey self, LKey other) internal pure returns (bool) {
        return LKey.unwrap(self) == LKey.unwrap(other);
    }

    function isNeq(LKey self, LKey other) internal pure returns (bool) {
        return !isEq(self, other);
    }

    /// Used for comparing an Lkey to the peak's range to stop at.
    /// @dev Only use on stopRanges and roots. Less can be ill-defined otherwise.
    function isLess(LKey self, LKey other) internal pure returns (bool) {
        // Since the range bits come first, a smaller key means it's below the ancestor's range.
        // We expect other to be a raw range, meaning its base is 0.
        return LKey.unwrap(self) < LKey.unwrap(other);
    }

    /// Go up to the parent from the right child.
    function rightUp(LKey self) internal pure returns (LKey up, LKey left) {
        unchecked {
            uint48 pair = LKey.unwrap(self);
            uint48 range = pair >> 24;
            uint48 leftRaw = pair ^ range;
            left = LKey.wrap(leftRaw);
            up = LKey.wrap(leftRaw + (range << 24));
        }
    }

    /// Go up to the parent from the left child.
    function leftUp(LKey self) internal pure returns (LKey up, LKey right) {
        unchecked {
            uint48 pair = LKey.unwrap(self);
            uint48 range = pair >> 24;
            right = LKey.wrap(pair ^ range);
            up = LKey.wrap(pair + (range << 24));
        }
    }

    /// Go up without knowing which side we are on originally.
    function genericUp(LKey self) internal pure returns (LKey up, LKey other) {
        uint48 pair = LKey.unwrap(self);
        uint48 range = pair >> 24;
        uint48 rawOther = range ^ pair;
        other = LKey.wrap(rawOther);
        unchecked {
            up = LKey.wrap((rawOther < pair ? rawOther : pair) + (range << 24));
        }
    }

    /// Test if the node is a right node or not.
    function isRight(LKey self) internal pure returns (bool) {
        uint48 pair = LKey.unwrap(self);
        return ((pair >> 24) & pair) != 0;
    }

    /// Test if the node is a left node or not.
    function isLeft(LKey self) internal pure returns (bool) {
        uint48 pair = LKey.unwrap(self);
        return ((pair >> 24) & pair) == 0;
    }

    /// Get the key of the right sibling of this key
    function rightSib(LKey self) internal pure returns (LKey right) {
        uint48 pair = LKey.unwrap(self);
        return LKey.wrap(pair | (pair >> 24));
    }

    /// Get the key of the left sibling of this key
    function leftSib(LKey self) internal pure returns (LKey left) {
        uint48 pair = LKey.unwrap(self);
        return LKey.wrap(pair & ~(pair >> 24));
    }

    /// Get the children of a key.
    function children(LKey self) internal pure returns (LKey left, LKey right) {
        uint48 pair = LKey.unwrap(self);
        uint48 childRange = pair >> 25;
        unchecked {
            uint48 rawLeft = pair - (childRange << 24);
            uint48 rawRight = rawLeft + childRange;
            return (LKey.wrap(rawLeft), LKey.wrap(rawRight));
        }
    }

    /// Get the left adjacent node to this node that is at a higher range.
    /// @dev We use the raw int values to save gas. This keeps us to 8 binary options. And avoids explodes/makeKeys
    function getNextLeftAdjacent(LKey key) internal pure returns (LKey) {
        uint48 raw = LKey.unwrap(key);
        unchecked {
            raw = (raw >> 24) + raw;
        }
        return LKey.wrap((lsb(raw) << 24) ^ (0x000000FFFFFF & raw));
    }

    /// Get the right adjacent node to this node that is at a higher range.
    /// @dev We use the raw int values to save gas. TODO we don't really need range here.
    function getNextRightAdjacent(LKey key) internal pure returns (LKey) {
        uint48 raw = LKey.unwrap(key);
        uint48 lsbBit = lsb(raw);
        return LKey.wrap(((raw ^ lsbBit) & 0x000000FFFFFF) ^ (lsbBit << 24));
    }

    /********
     * MISC *
     ********/

    function lsb(uint48 x) private pure returns (uint48) {
        unchecked {
            return x & (~x + 1);
        }
    }

    // function log(LKey key) internal view {
    //     (uint24 range, uint24 base) = explode(key);
    //     console2.log("key", range, base);
    // }

    // function log(LKey key, string memory _msg) internal view {
    //     (uint24 range, uint24 base) = explode(key);
    //     console2.log(_msg, range, base);
    // }
}
