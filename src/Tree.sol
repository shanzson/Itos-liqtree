// SPDX-License-Identifier: BSL-1.1
pragma solidity ^0.8.13;

import { console } from "forge-std/console.sol";

type LKey is uint48;
uint8 constant MAX_TREE_DEPTH = 21;

// This is okay as the NIL key because it can't possibly be used in any breakdowns since the depth portion of
// the lkey is one-hot.
LKey constant LKeyNIL = LKey.wrap(0xFFFFFFFFFFFF);

/*
 * @notice A struct for querying the liquidity available in a given range. It's similar to a combination of a
 * segment tree and an augmented tree.
 * TODO: We can test a LGroupKey idea where we batch node storage to reduce lookups like a BTree
 * @author Terence An
 */
struct LiqTree {
    mapping(LKey => LiqNode) nodes;
    LKey root; // maxRange << 24;
    // TODO: Perhaps cheaper to not store this at all, let all loops technically terminate at MAX_TREE_DEPTH,
    // but actually early term?
    uint24 maxRange; // Is 1 << (height - 1)
    uint8 height; // The depth of the tree, 0 is an empty tree.
}

struct LiqNode {
    // The first four are for liquidity constraints
    uint128 mLiq;
    uint128 tLiq; // This is also used for fees.
    uint128 subtreeMinM;
    uint128 subtreeMaxT;
    // These are for fee calculation.
    uint128 subtreeMaxM;
    uint128 cumFlatFee; // The cumulative flat flee accrued to this range from now inactive tliq.
}

/// Encapsulation of the details nodes store in a LiqTree.
library LiqNodeImpl {

    function addMLiq(LiqNode storage self, uint128 liq) internal {
        self.mLiq += liq;
        self.subtreeMinM += liq;
        self.subtreeMaxM += liq;
    }

    function subMLiq(LiqNode storage self, uint128 liq) internal {
        self.mLiq -= liq;
        self.subtreeMinM -= liq;
        self.subtreeMaxM -= liq;
    }

    function addTLiq(LiqNode storage self, uint128 liq) internal {
        self.tLiq += liq;
        self.subtreeMaxT += liq;
    }

    function subTLiq(LiqNode storage self, uint128 liq) internal {
        self.tLiq -= liq;
        self.subtreeMaxT -= liq;
    }
}

library LiqTreeImpl {
    using LKeyImpl for LKey;
    using LiqNodeImpl for LiqNode;
    using LiqTreeIntLib for uint24;

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

    /// Add maker liquidity to a range.
    function addMLiq(
        LiqTree storage self,
        uint24 rawLow,
        uint24 rawHigh,
        uint128 liq
    ) internal {
        (LKey low, LKey high, LKey peak, LKey stopRange) = LiqTreeIntLib.getRangeBounds(rawLow, rawHigh);

        // Start with the left side of all right nodes.
        LKey current = low;
        LiqNode storage node = self.nodes[current];
        node.addMLiq(liq);

        while (current.isLess(stopRange)) {
            // TODO: This can be gas optimized by sharing the left key and node with rightPropogate
            if (current.isLeft()) {
                current = current.rightSib();
                node = self.nodes[current];
                node.addMLiq(liq);
            }
            (current, node) = rightPropogateM(self, current, node);
        }

        current = high;
        node = self.nodes[current];
        node.addMLiq(liq);

        while(current.isLess(stopRange)) {
            // TODO: This can be gas optimized by sharing the right key and node with leftPropogate
            if (current.isRight()) {
                current = current.leftSib();
                node = self.nodes[current];
                node.addMLiq(liq);
            }
            (current, node) = leftPropogateM(self, current, node);
        }

        // Both legs are handled. Touch up the peak and above.
        peakPropogateM(self, peak, self.nodes[peak]);
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
        (LKey low, LKey high, , LKey stopRange) = LiqTreeIntLib.getRangeBounds(rawLow, rawHigh);

        minMaker = self.nodes[low].subtreeMinM;
        maxTaker = self.nodes[high].subtreeMaxT;

        // First handle the left side.
        LKey current = low.getNextLeftAdjacent();
        while (current.isLess(stopRange)) {
            minMaker = min(minMaker, self.nodes[current].subtreeMinM);
            maxTaker = max(maxTaker, self.nodes[current].subtreeMaxT);
            current = current.getNextLeftAdjacent();
        }

        // Now the right side.
        current = high.getNextRightAdjacent();
        while (current.isLess(stopRange)) {
            minMaker = min(minMaker, self.nodes[current].subtreeMinM);
            maxTaker = max(maxTaker, self.nodes[current].subtreeMaxT);
            current = current.getNextRightAdjacent();
        }
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
        (LKey left, LKey right) = current.children();
        node.subtreeMinM = min(self.nodes[left].subtreeMinM, self.nodes[right].subtreeMinM) + node.mLiq;

        while (current.isNeq(self.root)) {
            (LKey up, LKey other) = current.genericUp();
            LiqNode storage parent = self.nodes[up];
            parent.subtreeMinM = min(self.nodes[other].subtreeMinM, node.subtreeMinM) + parent.mLiq;
            current = up;
            node = parent;
        }
    }

    /// Propogate the new tliq values of the current node all the way to root.
    function peakPropogateT(
        LiqTree storage self,
        LKey current,
        LiqNode storage node
    ) internal {
        (LKey left, LKey right) = current.children();
        node.subtreeMaxT = max(self.nodes[left].subtreeMaxT, self.nodes[right].subtreeMaxT) + node.tLiq;

        while (current.isNeq(self.root)) {
            (LKey up, LKey other) = current.genericUp();
            LiqNode storage parent = self.nodes[up];
            parent.subtreeMaxT = max(self.nodes[other].subtreeMaxT, node.subtreeMaxT) + parent.tLiq;
            current = up;
            node = parent;
        }
    }

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
        (peak, peakRange)  = lowestCommonAncestor(rangeLow, rangeHigh);

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
    function lowKey(uint24 low) private pure returns (LKey) {
        return LKeyImpl.makeKey(lsb(low), low);
    }

    /// Get the key for the node that is the inclusive high of our exclusive range.
    /// This works by finding the first left sided node that contains this value.
    /// @dev Only to be used by getRangeBounds
    function highKey(uint24 high) private pure returns (LKey) {
        // Add one to propogate past any trailing ones
        // Then use lsb to find the range before zero-ing it out to get our left sided node.
        high += 1;
        uint24 range = lsb(high);
        return LKeyImpl.makeKey(range, high ^ range);
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
        return x & uint24(-int24(x));
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
    function isLess(LKey self, LKey other) internal pure returns (bool) {
        // Since the range bits come first, a smaller key means it's below the ancestor's range.
        // We expect other to be a raw range, meaning its base is 0.
        return LKey.unwrap(self) < LKey.unwrap(other);
    }

    /// Go up to the parent from the right child.
    function rightUp(LKey self) internal pure returns (LKey up, LKey left) {
        uint48 pair = LKey.unwrap(self);
        uint48 range = pair >> 24;
        uint48 leftRaw = pair ^ range;
        left = LKey.wrap(leftRaw);
        up = LKey.wrap(leftRaw + (range << 24));
    }

    /// Go up to the parent from the left child.
    function leftUp(LKey self) internal pure returns (LKey up, LKey right) {
        uint48 pair = LKey.unwrap(self);
        uint48 range = pair >> 24;
        right = LKey.wrap(pair ^ range);
        up = LKey.wrap(pair + (range << 24));
    }

    /// Go up without knowing which side we are on originally.
    function genericUp(LKey self) internal pure returns (LKey up, LKey other) {
        uint48 pair = LKey.unwrap(self);
        uint48 range = pair >> 24;
        uint48 rawOther = range ^ pair;
        other = LKey.wrap(rawOther);
        up = LKey.wrap((rawOther < pair ? rawOther : pair) + (range << 24));
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
        uint48 rawLeft = pair - (childRange << 24);
        uint48 rawRight = rawLeft + childRange;
        return (LKey.wrap(rawLeft), LKey.wrap(rawRight));
    }

    /// Get the left adjacent node to this node that is at a higher range.
    /// @dev We use the raw int values to save gas. This keeps us to 8 binary options. And avoids explodes/makeKeys
    function getNextLeftAdjacent(LKey key) internal pure returns (LKey) {
        uint48 raw = LKey.unwrap(key);
        raw = (raw >> 24) + raw;
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
        return x & uint48(-int48(x));
    }


    // Un-used, un-tested version of going up.
    // function up(LKey self) internal pure returns (LKey) {
    //     uint48 pair = LKey.unwrap(self);
    //     uint48 topRange = pair & uint48(0xFFFFFF000000); // Solidity won't allow direct cast to int48
    //     return LKey.wrap((pair & ~(topRange >> 24)) + topRange);
    // }
}
