// SPDX-License-Identifier: BSL-1.1
pragma solidity ^0.8.18;


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
 */

/// I would totally rewrite this differently.
/// Querying is not just using the break down.
/// Traversals are always done so I would have prioritize cheapening those.
/// But the change should not be insanely difficult.



import { console } from "forge-std/console.sol";


type LKey is uint48;
// Even if we use 1 as the tick spacing, we still won't have over 2^21 ticks.
uint8 constant MAX_TREE_DEPTH = 21; // We zero index depth, so this is 22 levels.

// This is okay as the NIL key because it can't possibly be used in any breakdowns since the depth portion of
// the lkey is one-hot.
LKey constant LKeyNIL = LKey.wrap(0xFFFFFFFFFFFF);

struct LiqRange {
    uint24 low;
    uint24 high;
}

/*
 * @notice A struct for querying the liquidity available in a given range. It's similar to a combination of a
 * segment tree and an augmented tree.
 * TODO: We can test a LGroupKey idea where we batch node storage to reduce lookups like a BTree
 * @author Terence An
 */
struct LiqTree {
    mapping(LKey => LiqNode) nodes;
    LKey root; // maxRange << 24 + maxRange;
    uint24 offset; // This is also the maximum range allowed in this tree.
    uint8 depth; // will is be cheaper gas to store this? Or calculate?
}

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



/// Encapsulation of the details nodes store in a LiqTree.
library LiqNodeImpl {

    function addMLiq(LiqNode storage self, int128 liq) internal {
        if (liq >= 0) {
            uint128 uliq = uint128(liq);
            self.mLiq += uliq;
            self.subtreeMinM += uliq;
            self.subtreeMaxM += uliq;
        } else {
            // We should never be removing liquidity we don't have in a node so it's okay
            // to do the subtraction here. We'll leave it checked for now though.
            uint128 uliq = uint128(-liq);
            self.mLiq -= uliq;
            self.subtreeMinM -= uliq;
            self.subtreeMaxM -= uliq;
        }
    }

    function addTLiq(LiqNode storage self, int128 liq) internal {
        if (liq >= 0) {
            uint128 uliq = uint128(liq);
            self.tLiq += uliq;
            self.subtreeMaxT += uliq;
        } else {
            // We should never be removing liquidity we don't have in a node so it's okay
            // to do the subtraction here. We'll leave it checked for now though.
            uint128 uliq = uint128(-liq);
            self.tLiq -= uliq;
            self.subtreeMaxT -= uliq;
        }
    }
}

library LiqTreeImpl {
    using LKeyImpl for LKey;
    using LiqNodeImpl for LiqNode;
    using LiqTreeIntLib for uint24;

    /****************************
     * Initialization Functions *
     ****************************/

    function init(LiqTree storage self, uint8 maxDepth) internal {
        require(maxDepth <= MAX_TREE_DEPTH, "MTD");
        // Note, NOT maxDepth - 1. The indexing from 0 or 1 is arbitrary so we go with the cheaper gas.
        uint24 maxRange = uint24(1 << maxDepth);

        self.root = LKeyImpl.makeKey(maxRange, maxRange);
        self.offset = maxRange;
        self.depth = maxDepth;
    }

    /***********************************
     * Updated Interface Methods (comment to be deleted after refactor)  *
     ***********************************/

    function addMLiq(LiqTree storage self, LiqRange memory range, uint128 liq) external {
        (LKey low, LKey high, , LKey stopRange) = getKeys(self, range.low, range.high);

        LKey current;
        LiqNode storage node;

        if (low.isLess(stopRange)) {
            current = low;
            node = self.nodes[current];
            node.addMLiq(int128(liq));
            (current, node) = rightPropogateM(self, current, node);

            while (current.isLess(stopRange)) {
                if (current.isLeft()) {
                    current = current.rightSib();
                    node = self.nodes[current];
                    node.addMLiq(int128(liq));
                }
                (current, node) = rightPropogateM(self, current, node);
            }
        }

        if (high.isLess(stopRange)) {
            current = high;
            node = self.nodes[current];
            node.addMLiq(int128(liq));
            (current, node) = leftPropogateM(self, current, node);

            while(current.isLess(stopRange)) {
                if (current.isRight()) {
                    current = current.leftSib();
                    node = self.nodes[current];
                    node.addMLiq(int128(liq));
                }
                (current, node) = leftPropogateM(self, current, node);
            }
        }

        // Both legs are handled. Touch up everything above where we left off.
        // Current must have already been propogated to.
        // Note. Peak propogating from peak could waste one propogation because sometimes
        // high or low is equal to peak, and we always propogate following an update.
        // So this is just a slight gas saving of one propogate.
        peakPropogateM(self, current, self.nodes[current]); // Is node, but compiler thinks might be unassigned.
    }

    function removeMLiq(LiqTree storage self, LiqRange memory range, uint128 liq) external {
        // TODO (urlaubaitos)
    }

    function addTLiq(LiqTree storage self, LiqRange memory range, uint128 liq) external {
        (LKey low, LKey high, , LKey stopRange) = getKeys(self, range.low, range.high);

        LKey current;
        LiqNode storage node;

        // Start with the left side of all right nodes.
        if (low.isLess(stopRange)) {
            current = low;
            node = self.nodes[current];
            node.addTLiq(int128(liq));
            (current, node) = rightPropogateT(self, current, node);

            while (current.isLess(stopRange)) {
                // TODO: This can be gas optimized by sharing the left key and node with rightPropogate
                if (current.isLeft()) {
                    current = current.rightSib();
                    node = self.nodes[current];
                    node.addTLiq(int128(liq));
                }
                (current, node) = rightPropogateT(self, current, node);
            }
        }

        if (high.isLess(stopRange)) {
            current = high;
            node = self.nodes[current];
            node.addTLiq(int128(liq));
            (current, node) = leftPropogateT(self, current, node);

            while(current.isLess(stopRange)) {
                // TODO: This can be gas optimized by sharing the right key and node with leftPropogate
                if (current.isRight()) {
                    current = current.leftSib();
                    node = self.nodes[current];
                    node.addTLiq(int128(liq));
                }
                (current, node) = leftPropogateT(self, current, node);
            }
        }

        // Both legs are handled. Touch up everything above.
        // Current has already been propogated to.
        peakPropogateT(self, current, self.nodes[current]); // Is node, but compiler thinks might be unassigned.
    }

    function removeTLiq(LiqTree storage self, LiqRange memory range, uint128 liq) external {
        // TODO (urlaubaitos)
    }

    function addInfRangeMLiq(LiqTree storage self, uint128 liq) external {
        // TODO (urlaubaitos) adjust for fee accounting
        LiqNode storage rootNode = self.nodes[self.root];
        rootNode.mLiq += liq;
        rootNode.subtreeMinM += liq;
    }

    function removeInfRangeMLiq(LiqTree storage self, uint128 liq) external {
        // TODO (urlaubaitos) adjust for fee accounting
        LiqNode storage rootNode = self.nodes[self.root];
        rootNode.mLiq -= liq;
        rootNode.subtreeMinM -= liq;
    }

    function addInfRangeTLiq(LiqTree storage self, uint128 liq) external {
        // TODO (urlaubaitos) adjust for fee accounting
        LiqNode storage rootNode = self.nodes[self.root];
        rootNode.tLiq += liq;
        rootNode.subtreeMaxT += liq;
    }

    function removeInfRangeTLiq(LiqTree storage self, uint128 liq) external {
        // TODO (urlaubaitos) adjust for fee accounting
        LiqNode storage rootNode = self.nodes[self.root];
        rootNode.tLiq -= liq;
        rootNode.subtreeMaxT -= liq;
    }

    function borrow(LiqTree storage self, LiqRange memory range, uint128 liq, uint128 amountX, uint128 amountY) internal  {
        // TODO (urlaubaitos)
    }

    function repay(LiqTree storage self, LiqRange memory range, uint128 liq, uint128 amountX, uint128 amountY) internal {
        // TODO (urlaubaitos)
    }

    // determine better way to keep private + support testing
    function walkToRootForMLiq(LiqTree storage self, LKey nodeKey) public view returns (uint128[] memory mLiqs) {
        mLiqs = new uint128[](self.depth);

        (uint24 rb, uint24 rr) = LKeyImpl.explode(self.root);
        console.log("root");
        console.log("root rb", rb, rr);

        uint8 index = 0;
        while (nodeKey.isNeq(self.root)) {
            console.log("next key");
            (uint24 r, uint24 b) = LKeyImpl.explode(nodeKey);
            console.log(r, b);
            LiqNode storage node = self.nodes[nodeKey];
            mLiqs[index] = node.mLiq;
            (nodeKey, ) = nodeKey.genericUp();
            ++index;
        }
    }

    /***********************************
     * Raw int range to LKey functions *
     ***********************************/

    /// A thin wrapper around LiqTreeIntLib that handles base value offsets.
    // Determine way to support testing + make private
    function getKeys(
        LiqTree storage self, uint24 rangeLow, uint24 rangeHigh
    ) public view returns (LKey low, LKey high, LKey peak, LKey stopRange) {
        require(rangeLow <= rangeHigh, "RLH");
        require(rangeHigh < self.offset, "RHO");
        // No one should be able to specifc the whole range. We rely on not having peak be equal to root
        // when we traverse the tree because stoprange can sometimes be one above the peak.
        require((rangeLow != 0) || (rangeHigh != (self.offset - 1)), "WR");
        rangeLow += self.offset;
        rangeHigh += self.offset;
        return LiqTreeIntLib.getRangeBounds(rangeLow, rangeHigh);
    }

    /**************************
     ** Wide Range Functions **
     **************************/

    /// Add whole range maker liquidity to the tree.
    function addWideMLiq(LiqTree storage self, uint128 liq) internal {
        LiqNode storage node = self.nodes[self.root];
        node.mLiq += liq;
        node.subtreeMinM += liq;
    }

    /// Subtract whole range maker liquidity from the tree.
    function subWideMLiq(LiqTree storage self, uint128 liq) internal {
        LiqNode storage node = self.nodes[self.root];
        node.mLiq -= liq;
        node.subtreeMinM -= liq;
    }

    /// Add whole range taker liquidity to the tree.
    function addWideTLiq(LiqTree storage self, uint128 liq) internal {
        LiqNode storage node = self.nodes[self.root];
        node.tLiq += liq;
        node.subtreeMaxT += liq;
    }

    /// Subtract whole range taker liquidity from the tree.
    function subWideTLiq(LiqTree storage self, uint128 liq) internal {
        LiqNode storage node = self.nodes[self.root];
        node.tLiq -= liq;
        node.subtreeMaxT -= liq;
    }

    /**************************
     ** Wide Query Functions **
     **************************/

    function queryWideMTBounds(LiqTree storage self) internal view returns (uint128 minMaker, uint128 maxTaker) {
        LiqNode storage node = self.nodes[self.root];
        return (node.subtreeMinM, node.subtreeMaxT);
    }

    /******************************
     ** Range specific functions **
     ******************************/

    /// Add or subtract maker liquidity to a range.
    /// @dev When subtracting liquidity, we are specifically subtracting from liquidity that already exists
    /// at a particular node. This is meant for removing existing positions, not add new negative ones.
    function addMLiq(
        LiqTree storage self,
        uint24 rawLow,
        uint24 rawHigh,
        int128 liq
    ) internal {
        (LKey low, LKey high, , LKey stopRange) = getKeys(self, rawLow, rawHigh);

        LKey current;
        LiqNode storage node;

        // console.log("add low", LKey.unwrap(low));
        // console.log("add high", LKey.unwrap(high));
        // console.log("add stop", LKey.unwrap(stopRange));

        // Start with the left side of all right nodes.
        // Only do this first add if we're actually a valid breakdown node!
        if (low.isLess(stopRange)) {
            current = low;
            node = self.nodes[current];
            // console.log("adding low", LKey.unwrap(low), liq);
            node.addMLiq(liq);
            (current, node) = rightPropogateM(self, current, node);

            while (current.isLess(stopRange)) {
                // TODO: This can be gas optimized by sharing the left key and node with rightPropogate
                if (current.isLeft()) {
                    current = current.rightSib();
                    // console.log("current add", LKey.unwrap(current));
                    node = self.nodes[current];
                    node.addMLiq(liq);
                }
                (current, node) = rightPropogateM(self, current, node);
            }
        }

        if (high.isLess(stopRange)) {
            current = high;
            node = self.nodes[current];
            // console.log("adding high", LKey.unwrap(high), liq);
            // // console.log("existing", node.subtreeMinM);
            node.addMLiq(liq);
            // console.log("after", node.subtreeMinM);
            (current, node) = leftPropogateM(self, current, node);
            // console.log("after2", self.nodes[high].subtreeMinM);

            while(current.isLess(stopRange)) {
                // TODO: This can be gas optimized by sharing the right key and node with leftPropogate
                if (current.isRight()) {
                    current = current.leftSib();
                    // console.log("current add", LKey.unwrap(current));
                    node = self.nodes[current];
                    node.addMLiq(liq);
                }
                (current, node) = leftPropogateM(self, current, node);
            }
        }

        // Both legs are handled. Touch up everything above where we left off.
        // Current must have already been propogated to.
        // Note. Peak propogating from peak could waste one propogation because sometimes
        // high or low is equal to peak, and we always propogate following an update.
        // So this is just a slight gas saving of one propogate.
        peakPropogateM(self, current, self.nodes[current]); // Is node, but compiler thinks might be unassigned.
    }

    /// Add maker liquidity to a range.
    function addTLiq(
        LiqTree storage self,
        uint24 rawLow,
        uint24 rawHigh,
        int128 liq
    ) internal {
        (LKey low, LKey high, , LKey stopRange) = getKeys(self, rawLow, rawHigh);

        LKey current;
        LiqNode storage node;

        // Start with the left side of all right nodes.
        if (low.isLess(stopRange)) {
            current = low;
            node = self.nodes[current];
            node.addTLiq(liq);
            (current, node) = rightPropogateT(self, current, node);

            while (current.isLess(stopRange)) {
                // TODO: This can be gas optimized by sharing the left key and node with rightPropogate
                if (current.isLeft()) {
                    current = current.rightSib();
                    node = self.nodes[current];
                    node.addTLiq(liq);
                }
                (current, node) = rightPropogateT(self, current, node);
            }
        }

        if (high.isLess(stopRange)) {
            current = high;
            node = self.nodes[current];
            node.addTLiq(liq);
            (current, node) = leftPropogateT(self, current, node);

            while(current.isLess(stopRange)) {
                // TODO: This can be gas optimized by sharing the right key and node with leftPropogate
                if (current.isRight()) {
                    current = current.leftSib();
                    node = self.nodes[current];
                    node.addTLiq(liq);
                }
                (current, node) = leftPropogateT(self, current, node);
            }
        }

        // Both legs are handled. Touch up everything above.
        // Current has already been propogated to.
        peakPropogateT(self, current, self.nodes[current]); // Is node, but compiler thinks might be unassigned.
    }

    /*******************
     ** Range Queries **
     *******************/

    /// Query the minimum Maker liquidity available and max Taker liquidity over all ticks in this range.
    function queryMTBounds(
        LiqTree storage self,
        uint24 rawLow,
        uint24 rawHigh
    ) internal view returns (uint128 minMaker, uint128 maxTaker) {
        (LKey low, LKey high, , LKey stopRange) = getKeys(self, rawLow, rawHigh);

        // console.log("query low", LKey.unwrap(low));
        // console.log("query high", LKey.unwrap(high));
        // console.log("query stop", LKey.unwrap(stopRange));

        LKey current;
        LiqNode storage node;

        minMaker = type(uint128).max;
        maxTaker = 0;

        // First handle the left side.
        if (low.isLess(stopRange)) {
            // Left side directly writes to minMaker and maxTaker to save stack space.

            current = low;
            node = self.nodes[current];
            // console.log("found low", LKey.unwrap(current), node.subtreeMinM);
            minMaker = min(node.subtreeMinM, minMaker);
            maxTaker = max(node.subtreeMaxT, maxTaker);
            (current,) = current.rightUp();

            LKey right;
            while(current.isLess(stopRange)) {
                node = self.nodes[current];
                // console.log("found current addition", LKey.unwrap(current), node.mLiq);
                minMaker += node.mLiq;
                maxTaker += node.tLiq;

                if (current.isLeft()) {
                    (current, right) = current.leftUp();
                    // console.log("minning low", LKey.unwrap(current), LKey.unwrap(right));
                    // console.log(minMaker, self.nodes[right].subtreeMinM);
                    minMaker = min(minMaker, self.nodes[right].subtreeMinM);
                    maxTaker = max(maxTaker, self.nodes[right].subtreeMaxT);
                } else {
                    (current,) = current.rightUp();
                }
            }
            // We the node at the stop range, so we don't have to specially handle
            // the two legged case later.
            node = self.nodes[current];
            minMaker += node.mLiq;
            maxTaker += node.tLiq;
        }

        if (high.isLess(stopRange)) {
            // We temporarily write here to avoid overwriting the left side.
            uint128 rightMaker = type(uint128).max;
            uint128 rightTaker = 0;

            current = high;
            node = self.nodes[current];
            // console.log("found high", LKey.unwrap(current), node.subtreeMinM);
            rightMaker = min(node.subtreeMinM, rightMaker);
            rightTaker = max(node.subtreeMaxT, rightTaker);
            (current,) = current.leftUp();

            LKey left;
            // console.log("stopRange", LKey.unwrap(stopRange));
            while(current.isLess(stopRange)) {
                node = self.nodes[current];
                // console.log("found current addition", LKey.unwrap(current), node.mLiq);
                rightMaker += node.mLiq;
                rightTaker += node.tLiq;

                if (current.isRight()) {
                    (current, left) = current.rightUp();
                    // console.log("minning high", LKey.unwrap(current), LKey.unwrap(left));
                    // console.log(rightMaker, self.nodes[left].subtreeMinM);
                    rightMaker = min(rightMaker, self.nodes[left].subtreeMinM);
                    rightTaker = max(rightTaker, self.nodes[left].subtreeMaxT);
                } else {
                    (current,) = current.leftUp();
                }
            }
            // We add the node at the stop range, so we don't have to specially handle
            // the two legged case later.
            node = self.nodes[current];
            rightMaker += node.mLiq;
            rightTaker += node.tLiq;

            // Merge with the other side
            minMaker = min(minMaker, rightMaker);
            maxTaker = max(maxTaker, rightTaker);
        }

        // console.log("PrePeak", minMaker, maxTaker);

        // At this moment, we've already added the liq at the node AT the stoprange.
        // To regardless if we're in the two legged case, the one legged case, or the single node case,
        // the node above current is new and incorporates both all nodes in our range breakdown.
        // Thus we just need to start adding.
        // NOTE: it's possible we've already added root in the single node case.
        while (current.isLess(self.root)) {
            (current,) = current.genericUp();
            node = self.nodes[current];
            // console.log("Found Peak Add", node.mLiq, node.tLiq);
            minMaker += node.mLiq;
            maxTaker += node.tLiq;
        }
        // console.log("PostPeak", minMaker, maxTaker);
    }

    /// Query the total amount of Taker liquidity over the entire range and the maximum maker liquidity.
    function queryMLiqMaxFeeTokenSum(
        LiqTree storage self,
        uint24 low,
        uint24 high
    ) internal view returns (uint128 maxMaker, uint128 sumTaker) {
        // TODO
    }

    /*************************
     ** Propogation helpers **
     *************************/

    /// Propogate the new mLiq value of the current node, who is a right node, up.
    function rightPropogateM(
        LiqTree storage self,
        LKey current,
        LiqNode storage node
    ) internal returns (LKey, LiqNode storage) {
        (LKey up, LKey left) = current.rightUp();
        LiqNode storage parent = self.nodes[up];
        parent.subtreeMinM = min(self.nodes[left].subtreeMinM, node.subtreeMinM) + parent.mLiq;
        return (up, parent);
    }

    /// Propogate the new tLiq value of the current node, who is a right node, up.
    function rightPropogateT(
        LiqTree storage self,
        LKey current,
        LiqNode storage node
    ) internal returns (LKey, LiqNode storage) {
        (LKey up, LKey left) = current.rightUp();
        LiqNode storage parent = self.nodes[up];
        parent.subtreeMaxT = max(self.nodes[left].subtreeMaxT, node.subtreeMaxT) + parent.tLiq;
        return (up, parent);
    }

    /// Propogate the new mLiq value of the current node, who is a left node, up.
    function leftPropogateM(
        LiqTree storage self,
        LKey current,
        LiqNode storage node
    ) internal returns (LKey, LiqNode storage) {
        (LKey up, LKey left) = current.leftUp();
        LiqNode storage parent = self.nodes[up];
        parent.subtreeMinM = min(self.nodes[left].subtreeMinM, node.subtreeMinM) + parent.mLiq;
        return (up, parent);
    }

    /// Propogate the new tLiq value of the current node, who is a left node, up.
    function leftPropogateT(
        LiqTree storage self,
        LKey current,
        LiqNode storage node
    ) internal returns (LKey, LiqNode storage) {
        (LKey up, LKey left) = current.leftUp();
        LiqNode storage parent = self.nodes[up];
        parent.subtreeMaxT = max(self.nodes[left].subtreeMaxT, node.subtreeMaxT) + parent.tLiq;
        return (up, parent);
    }

    /// Propogate the new mliq values of the current node all the way to root.
    function peakPropogateM(
        LiqTree storage self,
        LKey current,
        LiqNode storage node
    ) internal {
        // Is less works on root since root has the smallest possible base.
        while (current.isLess(self.root)) {
            (LKey up, LKey other) = current.genericUp();
            LiqNode storage parent = self.nodes[up];
            uint128 oldMin = parent.subtreeMinM;

            // We're just propogating the min, if our value doesn't change none of the parents need to.
            parent.subtreeMinM = min(self.nodes[other].subtreeMinM, node.subtreeMinM) + parent.mLiq;
            if (parent.subtreeMinM == oldMin) {
                return;
            }

            current = up;
            node = parent; // Store this to save one lookup..
        }
    }

    /// Propogate the new tliq values of the current node all the way to root.
    function peakPropogateT(
        LiqTree storage self,
        LKey current,
        LiqNode storage node
    ) internal {
        while (current.isNeq(self.root)) {
            (LKey up, LKey other) = current.genericUp();
            LiqNode storage parent = self.nodes[up];
            uint128 oldMax = parent.subtreeMaxT;
            parent.subtreeMaxT = max(self.nodes[other].subtreeMaxT, node.subtreeMaxT) + parent.tLiq;
            if (node.subtreeMaxT == oldMax) {
                return;
            }
            current = up;
            node = parent;
        }
    }

    /*********************
     * Traversal Helpers *
     *********************/

    /**********
     ** MISC **
     **********/

    /// Convenience function for minimum of uint128s
    function min(uint128 a, uint128 b) private pure returns (uint128) {
        return (a <= b) ? a : b;
    }

    /// Convenience function for maximum of uint128s
    function max(uint128 a, uint128 b) private pure returns (uint128) {
        return (a >= b) ? a : b;
    }
}

library LiqTreeIntLib {
    // LiqTreeInts are uint24 values that don't have a range. Their assumed range is 1.
    // They are used to specify the range [low, high].
    using LKeyImpl for LKey;

    /// Convenience for fetching the bounds of our range.
    /// Here we coerce the range keys to the ones we expect in our proofs.
    /// I.e. A one-sided trapezoid has one key equal to the peak.
    function getRangeBounds(
        uint24 rangeLow,
        uint24 rangeHigh
    ) public pure returns (LKey low, LKey high, LKey peak, LKey limitRange) {
        LKey peakRange;
        (peak, peakRange) = lowestCommonAncestor(rangeLow, rangeHigh);

        low = lowKey(rangeLow);
        high = highKey(rangeHigh);

        bool lowBelow = low.isLess(peakRange);
        bool highBelow = high.isLess(peakRange);

        // Case on whether left and right are below the peak range or not.
        if (lowBelow && highBelow) {
            // The simple case where we can just walk up both legs.
            // Each individual leg will stop at the children of the peak,
            // so our limit range is one below peak range.
            limitRange = LKey.wrap(LKey.unwrap(peakRange) >> 1);
        } else if (lowBelow && !highBelow) {
            // We only have the left leg to worry about.
            // So our limit range will be at the peak, because we want to include
            // the right child of the peak.
            limitRange = peakRange;
        } else if (!lowBelow && highBelow) {
            // Just the right leg. So include the left child of peak.
            limitRange = peakRange;
        } else {
            // Both are at or higher than the peak! So our range breakdown is just
            // the peak.
            // You can prove that one of the keys must be the peak itself trivially.
            // Thus we don't modify our keys and just stop at one above the peak.
            limitRange = LKey.wrap(LKey.unwrap(peakRange) << 1);
        }
    }

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
        uint48 lsb_bit = lsb(raw);
        return LKey.wrap(((raw ^ lsb_bit) & 0x000000FFFFFF) ^ (lsb_bit << 24));
    }

    /********
     * MISC *
     ********/

    function lsb(uint48 x) private pure returns (uint48) {
        unchecked {
            return x & (~x + 1);
        }
    }


    // Un-used, un-tested version of going up.
    // function up(LKey self) internal pure returns (LKey) {
    //     uint48 pair = LKey.unwrap(self);
    //     uint48 topRange = pair & uint48(0xFFFFFF000000); // Solidity won't allow direct cast to int48
    //     return LKey.wrap((pair & ~(topRange >> 24)) + topRange);
    // }
}
