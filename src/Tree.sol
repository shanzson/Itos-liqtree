// SPDX-License-Identifier: BSL-1.1
pragma solidity ^0.8.13;

type LKey is int48;
uint8 constant MAX_TREE_DEPTH = 21;

// This is okay as the NIL key because it can't possibly be used in any breakdowns since the depth portion of the lkey is one-hot.
LKey constant LKeyNIL = LKey.wrap(-1);

/*
 * @notice A struct for querying the liquidity available in a given range. It's similar to a combination of a segment tree and an augmented tree.
 * @dev All ranges are left inclusive and right exclusive. The range portion of the key starts at 1 for leaf nodes.
 * TODO: We can test a LGroupKey idea where we batch node storage to reduce lookups.
 * @author Terence An
 */
struct LiqTree {
    mapping(LKey => LiqNode) nodes;
    LKey root; // max_range << 24;
    // TODO: Perhaps cheaper to not store this at all, let all loops technically terminate at MAX_TREE_DEPTH, but actually early term?
    int24 max_range; // Is 1 << (height - 1)
    int8 height; // The depth of the tree, 0 is an empty tree.
}

struct LiqNode {
    uint128 mLiq;
    uint128 tLiq;

    uint128 subtreeMinM;
    uint128 subtreeMaxM;

    uint128 subtreeMaxT;
    // uint128 feeTokens; // There may be extra accounting needed depending on how we calculate the fees.
}

library LiqTreeImpl {
    using LKeyImpl for LKey;
    using LiqTreeIntLib for int24;

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
    function addMLiq(LiqTree storage self, int24 low, int24 high, uint128 liq) internal {
        LKey peak = LiqTreeIntLib.lowestCommonAncestor(low, high);
        // A low key and high key will be equal to the peak if one leg is not present.

        // Start with the left side of all right nodes.
        LKey current = low.lowKey();
        if (current.isNeq(peak)) {
            while (true) {
                LiqNode storage node = self.nodes[current];
                // First add the liquidity
                node.mLiq += liq;
                node.subtreeMinM += liq;
                while (current.isRight()) {
                    (current, node) = rightPropogateM(self, current, node);
                }
                // We are on the left, our rightSib is the next node, but we need to check if the parent is the peak.
                (LKey up, LKey right) = current.leftUp();
                if(up.isEq(peak)) {
                    break;
                }
                current = right;
            }
        }
        // Handle the right side of all left nodes.
        current = high.highKey();
        if (current.isNeq(peak)) {
            while (true) {
                LiqNode storage node = self.nodes[current];
                node.mLiq += liq;
                node.subtreeMinM += liq;
                while (current.isLeft()) {
                    (current, node) = leftPropogateM(self, current, node);
                }
                // On the right now, if the parent is peak we're done.
                (LKey up, LKey left) = current.rightUp();
                if (up.isEq(peak)) {
                    break;
                }
                current = left;
            }
        }

        // Both legs are handled. Touch up the peak and above.
        peakPropogateM(self, peak, self.nodes[peak]);
    }

    /// Subtract maker liquidity from a range.
    function subMLiq(LiqTree storage self, int24 low, int24 high, uint128 liq) internal {
        LKey peak = LiqTreeIntLib.lowestCommonAncestor(low, high);
        // A low key and high key will be equal to the peak if one leg is not present.

        // Start with the left side of all right nodes.
        LKey current = low.lowKey();
        if (current.isNeq(peak)) {
            while (true) {
                LiqNode storage node = self.nodes[current];
                // First sub the liquidity
                node.mLiq -= liq;
                node.subtreeMinM -= liq;
                while (current.isRight()) {
                    (current, node) = rightPropogateM(self, current, node);
                }
                // We are on the left, our rightSib is the next node, but we need to check if the parent is the peak.
                (LKey up, LKey right) = current.leftUp();
                if(up.isEq(peak)) {
                    break;
                }
                current = right;
            }
        }
        // Handle the right side of all left nodes.
        current = high.highKey();
        if (current.isNeq(peak)) {
            while (true) {
                LiqNode storage node = self.nodes[current];
                node.mLiq -= liq;
                node.subtreeMinM -= liq;
                while (current.isLeft()) {
                    (current, node) = leftPropogateM(self, current, node);
                }
                // On the right now, if the parent is peak we're done.
                (LKey up, LKey left) = current.rightUp();
                if (up.isEq(peak)) {
                    break;
                }
                current = left;
            }
        }

        // Both legs are handled. Touch up the peak and above.
        peakPropogateM(self, peak, self.nodes[peak]);
    }

    /// Add taker liquidity to a range.
    function addTLiq(LiqTree storage self, int24 low, int24 high, uint128 liq) internal {
        LKey peak = LiqTreeIntLib.lowestCommonAncestor(low, high);
        // A low key and high key will be equal to the peak if one leg is not present.

        // Start with the left side of all right nodes.
        LKey current = low.lowKey();
        if (current.isNeq(peak)) {
            while (true) {
                LiqNode storage node = self.nodes[current];
                // First add the liquidity
                node.tLiq += liq;
                node.subtreeMaxT += liq;
                while (current.isRight()) {
                    (current, node) = rightPropogateT(self, current, node);
                }
                // We are on the left, our rightSib is the next node, but we need to check if the parent is the peak.
                (LKey up, LKey right) = current.leftUp();
                if(up.isEq(peak)) {
                    break;
                }
                current = right;
            }
        }
        // Handle the right side of all left nodes.
        current = high.highKey();
        if (current.isNeq(peak)) {
            while (true) {
                LiqNode storage node = self.nodes[current];
                node.tLiq += liq;
                node.subtreeMaxT += liq;
                while (current.isLeft()) {
                    (current, node) = leftPropogateT(self, current, node);
                }
                // On the right now, if the parent is peak we're done.
                (LKey up, LKey left) = current.rightUp();
                if (up.isEq(peak)) {
                    break;
                }
                current = left;
            }
        }

        // Both legs are handled. Touch up the peak and above.
        peakPropogateT(self, peak, self.nodes[peak]);
    }

    /// Subtract taker liquidity from a range.
    function subTLiq(LiqTree storage self, int24 low, int24 high, uint128 liq) internal {
        LKey peak = LiqTreeIntLib.lowestCommonAncestor(low, high);
        // A low key and high key will be equal to the peak if one leg is not present.

        // Start with the left side of all right nodes.
        LKey current = low.lowKey();
        if (current.isNeq(peak)) {
            while (true) {
                LiqNode storage node = self.nodes[current];
                // First sub the liquidity
                node.tLiq -= liq;
                node.subtreeMaxT -= liq;
                while (current.isRight()) {
                    (current, node) = rightPropogateT(self, current, node);
                }
                // We are on the left, our rightSib is the next node, but we need to check if the parent is the peak.
                (LKey up, LKey right) = current.leftUp();
                if(up.isEq(peak)) {
                    break;
                }
                current = right;
            }
        }
        // Handle the right side of all left nodes.
        current = high.highKey();
        if (current.isNeq(peak)) {
            while (true) {
                LiqNode storage node = self.nodes[current];
                node.tLiq -= liq;
                node.subtreeMaxT -= liq;
                while (current.isLeft()) {
                    (current, node) = leftPropogateT(self, current, node);
                }
                // On the right now, if the parent is peak we're done.
                (LKey up, LKey left) = current.rightUp();
                if (up.isEq(peak)) {
                    break;
                }
                current = left;
            }
        }

        // Both legs are handled. Touch up the peak and above.
        peakPropogateT(self, peak, self.nodes[peak]);
    }

    /*******************
     ** Range Queries **
     *******************/

    /// Query the minimum Maker liquidity available and max Taker liquidity over all ticks in this range.
    function queryMTBounds(LiqTree storage self, int24 low, int24 high) internal view returns (uint128 minMaker, uint128 maxTaker) {
        LKey peak = LiqTreeIntLib.lowestCommonAncestor(low, high);
        (, int24 peakRange) = peak.explode();
        int24 stopRange = peakRange >> 1;

        LKey current;
        minMaker = type(uint128).max;
        // maxTaker = 0 // True by default

        // We use raw numbers to be gas optimal, so we need to be really careful here.

        // First handle the left side.
        int24 lowRange = low.lsb();
        while (lowRange < stopRange) {
            current = LKeyImpl.makeKey(low, lowRange);
            minMaker = min(minMaker, self.nodes[current].subtreeMinM);
            maxTaker = max(maxTaker, self.nodes[current].subtreeMaxT);
            // WARNING
            // We don't try to handle the base part overflowing into the range portion because we should not be taking up the full range.
            // But it's important to add a test for this. Beware this is a potential source of error.
            low += lowRange;
            lowRange = low.lsb();
        }

        // Handle the right side.
        int24 highRange = high.lsb();
        high = high ^ highRange;
        while (highRange < stopRange) {
            current = LKeyImpl.makeKey(high, highRange);
            minMaker = min(minMaker, self.nodes[current].subtreeMinM);
            maxTaker = max(maxTaker, self.nodes[current].subtreeMaxT);
            // The order here is super important. We look ahead to find the next one bit tell us our next range.
            highRange = high.lsb();
            // Subtract and AND to get the parent node of our next high and that'll be the same base as the 0 child which is our next high.
            high = high ^ highRange;
        }
    }

    /// Query the total amount of Taker liquidity over the entire range and the maximum maker liquidity.
    function queryMLiqMaxFeeTokenSum(LiqTree storage self, int24 low, int24 high) internal view returns (uint128 maxMaker, uint128 sumTaker) {

        // TODO
    }

    /*************************
     ** Propogation helpers **
     *************************/

    /// Propogate the new mLiq value of the current node, who is a right node, up.
    function rightPropogateM(LiqTree storage self, LKey current, LiqNode storage node) internal returns (LKey, LiqNode storage) {
        (LKey up, LKey left) = current.rightUp();
        LiqNode storage parent = self.nodes[up];
        parent.subtreeMinM = min(self.nodes[left].subtreeMinM, node.subtreeMinM) + parent.mLiq;
        return (up, parent);
    }
    /// Propogate the new tLiq value of the current node, who is a right node, up.
    function rightPropogateT(LiqTree storage self, LKey current, LiqNode storage node) internal returns (LKey, LiqNode storage) {
        (LKey up, LKey left) = current.rightUp();
        LiqNode storage parent = self.nodes[up];
        parent.subtreeMaxT = max(self.nodes[left].subtreeMaxT, node.subtreeMaxT) + parent.tLiq;
        return (up, parent);
    }

    /// Propogate the new mLiq value of the current node, who is a left node, up.
    function leftPropogateM(LiqTree storage self, LKey current, LiqNode storage node) internal returns (LKey, LiqNode storage) {
        (LKey up, LKey left) = current.leftUp();
        LiqNode storage parent = self.nodes[up];
        parent.subtreeMinM = min(self.nodes[left].subtreeMinM, node.subtreeMinM) + parent.mLiq;
        return (up, parent);
    }
    /// Propogate the new tLiq value of the current node, who is a left node, up.
    function leftPropogateT(LiqTree storage self, LKey current, LiqNode storage node) internal returns (LKey, LiqNode storage) {
        (LKey up, LKey left) = current.leftUp();
        LiqNode storage parent = self.nodes[up];
        parent.subtreeMaxT = max(self.nodes[left].subtreeMaxT, node.subtreeMaxT) + parent.tLiq;
        return (up, parent);
    }

    /// Propogate the new mliq values of the current node all the way to root.
    function peakPropogateM(LiqTree storage self, LKey current, LiqNode storage node) internal {
        (LKey left, LKey right) = current.children();
        node.subtreeMinM = min(self.nodes[left].subtreeMinM, self.nodes[right].subtreeMinM) + node.mLiq;

        while(current.isNeq(self.root)) {
            (LKey up, LKey other) = current.genericUp();
            LiqNode storage parent = self.nodes[up];
            parent.subtreeMinM = min(self.nodes[other].subtreeMinM, node.subtreeMinM) + parent.mLiq;
            current = up;
            node = parent;
        }
    }
    /// Propogate the new tliq values of the current node all the way to root.
    function peakPropogateT(LiqTree storage self, LKey current, LiqNode storage node) internal {
        (LKey left, LKey right) = current.children();
        node.subtreeMaxT = max(self.nodes[left].subtreeMaxT, self.nodes[right].subtreeMaxT) + node.tLiq;

        while(current.isNeq(self.root)) {
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
    function min(uint128 a, uint128 b) private pure returns(uint128) {
        return (a <= b) ? a : b;
    }

    /// Convenience function for maximum of uint128s
    function max(uint128 a, uint128 b) private pure returns(uint128) {
        return (a >= b) ? a : b;
    }
}


library LiqTreeIntLib {

    /// @notice Get the keys to the nodes we'll need for a given range.
    /// @dev This is actually just used for comparison with the low, high, and peak keys.
    /// This creates the explicit range breakdown, but this breakdown can be inferred when traversing the tree according
    /// to the properties proven in the Liquidity Tree documentation.
    /// @return up A list of node keys representing the left chain of nodes used.
    /// @return down A list of node keys representing the right chain of nodes used.
    function _rangeBreakdown(int24 low, int24 high) internal pure returns(LKey[MAX_TREE_DEPTH] memory up, LKey[MAX_TREE_DEPTH] memory down) {
        uint8 idx = 0;

        int24 current = low;
        int24 range;
        // Climbing up the tree
        while(current == 0 || current <= high) {
            // Add ranges until we go over.
            range = lsb(current);
            // When climbing up, we attempt to add powers of two to get to our high.
            up[idx++] = LKeyImpl.makeKey(current, range);
            // WARNING
            // We don't try to handle the base part overflowing into the range portion because we should not be taking up the full range.
            // But it's important to add a test for this. Beware this is a potential source of error.
            current = current + range;
        }
        // Sometimes we can end the climb at there.
        if (current == high)
            return (up, down);
        // Climb down the tree
        up[idx] = LKeyNIL;
        idx = 0;
        while (current != high) {
            // In theory we go down levels (bits) until we're back below the high,
            // but we actually go in the reverse order for efficiency.
            // This works by subtracting powers of two until we hit our high.
            // Here, the fact that high is EXCLUSIVE IS IMPORTANT.
            range = lsb(high);
            // Since it's exclusive we want to xor first, then insert to list.
            high = high ^ range;
            down[idx++] = LKeyImpl.makeKey(high, range);
        }
    }

    /// Get the key for the node that represents the lowest bound of our range.
    /// @dev CANNOT use this method for the whole range. Instead use the optimized method. This will be incorrect.
    function lowKey(int24 low) internal pure returns(LKey) {
        return LKeyImpl.makeKey(low, lsb(low));
    }

    /// Get the key for the node that is the inclusive high of our exclusive range.
    /// @dev CANNOT use this method for the whole range. Instead use the optimized method. This will be incorrect.
    function highKey(int24 high) internal pure returns(LKey) {
        int24 range = lsb(high);
        return LKeyImpl.makeKey(high ^ range, range);
    }

    /// Get the node that is the lowest common ancestor of both the low and high nodes.
    /// This is the peak of our range breakdown which does not modify its liq.
    function lowestCommonAncestor(int24 low, int24 high) internal pure returns (LKey) {
        // Find the bitwise common prefix by finding the bits not in a common prefix.
        // This way uses less gas than directly finding the common prefix.
        int32 diff_mask = 0x00FFFFFF;
        int diff_bits = int(low ^ high);

        if (diff_bits & 0xFFF000 == 0) {
            diff_mask >> 12;
            diff_bits << 12;
        }

        if (diff_bits & 0xFC0000 == 0) {
            diff_mask >> 6;
            diff_bits << 6;
        }

        if (diff_bits & 0xE00000 == 0) {
            diff_mask >> 3;
            diff_bits << 3;
        }

        if (diff_bits & 0xC00000 == 0) {
            diff_mask >> 2;
            diff_bits << 2;
        }

        if (diff_bits & 0x800000 == 0) {
            diff_mask >> 1;
            // we don't need diff_bits anymore
        }

        int24 common_mask = int24(~diff_mask);
        int24 base = common_mask & low;
        int24 range = lsb(common_mask);
        return LKeyImpl.makeKey(base, range);
    }

    /// @dev this returns 0 for
    function lsb(int24 x) internal pure returns(int24) {
        return x & -x;
    }
}


library LKeyImpl {
    function makeKey(int24 base, int24 range) internal pure returns(LKey) {
        return LKey.wrap(int48(range) << 24 | int48(base));
    }

    function explode(LKey self) internal pure returns(int24 base, int24 range) {
        int48 all = LKey.unwrap(self);
        base = int24(all);
        range = int24(all >> 24);
    }

    function isEq(LKey self, LKey other) internal pure returns(bool) {
        return LKey.unwrap(self) == LKey.unwrap(other);
    }

    function isNeq(LKey self, LKey other) internal pure returns(bool) {
        return !isEq(self, other);
    }

    /// Go up to the parent from the right child.
    function rightUp(LKey self) internal pure returns(LKey up, LKey left) {
        int48 pair = LKey.unwrap(self);
        int48 range = pair >> 24;
        int48 leftRaw = pair ^ range;
        left = LKey.wrap(leftRaw);
        up = LKey.wrap(leftRaw + (range << 24));
    }

    /// Go up to the parent from the left child.
    function leftUp(LKey self) internal pure returns(LKey up, LKey right) {
        int48 pair = LKey.unwrap(self);
        int48 range = pair >> 24;
        right = LKey.wrap(pair ^ range);
        up = LKey.wrap(pair + (range << 24));
    }

    /// Go up without knowing which side we are on originally.
    function genericUp(LKey self) internal pure returns (LKey up, LKey other) {
        int48 pair = LKey.unwrap(self);
        int48 range = pair >> 24;
        int48 rawOther = range ^ pair;
        other = LKey.wrap(rawOther);
        up = LKey.wrap((rawOther < pair ? rawOther : pair) + (range << 24));
    }

    /// Test if the node is a right node or not.
    function isRight(LKey self) internal pure returns(bool) {
        int48 pair = LKey.unwrap(self);
        return ((pair >> 24) & pair) != 0;
    }

    /// Test if the node is a left node or not.
    function isLeft(LKey self) internal pure returns(bool) {
        int48 pair = LKey.unwrap(self);
        return ((pair >> 24) & pair) == 0;
    }

    /// Get the key of the right sibling of this key
    function rightSib(LKey self) internal pure returns(LKey right) {
        int48 pair = LKey.unwrap(self);
        return LKey.wrap(pair | (pair >> 24));
    }

    /// Get the key of the left sibling of this key
    function leftSib(LKey self) internal pure returns(LKey left) {
        int48 pair = LKey.unwrap(self);
        return LKey.wrap(pair & ~(pair >> 24));
    }

    /// Get the children of a key.
    function children(LKey self) internal pure returns(LKey left, LKey right) {
        int48 pair = LKey.unwrap(self);
        int48 childRange = pair >> 25;
        int48 rawLeft = pair - (childRange << 24);
        int48 rawRight = rawLeft + childRange;
        return (LKey.wrap(rawLeft), LKey.wrap(rawRight));
    }

    // Un-used, un-tested version of going up.
    // function up(LKey self) internal pure returns(LKey) {
    //     int48 pair = LKey.unwrap(self);
    //     int48 topRange = pair & int48(uint48(0xFFFFFF000000)); // Solidity won't allow direct cast to int48
    //     return LKey.wrap((pair & ~(topRange >> 24)) + topRange);
    // }
}
