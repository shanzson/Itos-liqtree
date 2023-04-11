// SPDX-License-Identifier: BSL-1.1
pragma solidity ^0.8.18;

import { console } from "forge-std/console.sol";
import { Test } from "forge-std/Test.sol";

import { FeeRateSnapshot, FeeRateSnapshotImpl } from "src/FeeRateSnapshot.sol";
import { LiqTree, LiqTreeImpl, LiqRange, LKey, LKeyImpl, LiqNode } from "src/Tree.sol";

/**
 * In practice, the LiqTree will have many nodes. So many, that testing at that scale is intractable.
 * Thus the reason for this file. A smaller scale LiqTree, where we can more easily populate the values densely.
 */ 
contract DenseTreeTest is Test {
    LiqTree public liqTree;
    using LiqTreeImpl for LiqTree;
    using LKeyImpl for LKey;
    using FeeRateSnapshotImpl for FeeRateSnapshot;
    
    function setUp() public {
        // A depth of 4 creates a tree that covers an absolute range of 16 ([0, 15]). 
        // ie. A complete tree matching the ascii documentation. 
        liqTree.init(4);
    }

    function testWalkToRootForMLiq() public {
        liqTree.addInfRangeMLiq(140); // root
        liqTree.addMLiq(LiqRange(0, 7), 37); // L
        liqTree.addMLiq(LiqRange(4, 7), 901); // LR
        liqTree.addMLiq(LiqRange(4, 5), 72); // LRL

        // High key corresponds to LRL (low key is LR)
        (, LKey highKey,,) = liqTree.getKeys(4, 5); // LRL
        uint128[] memory mLiqs = liqTree.walkToRootForMLiq(highKey);
        assertEq(mLiqs[0], 72);
        assertEq(mLiqs[1], 901);
        assertEq(mLiqs[2], 37);
        assertEq(mLiqs[3], 140);
    }

    function testOutputRangeCombinations() public {
        uint24 range;
        uint24 base;

        // 16 is the offset
        for (uint24 i = 0; i < 16; i++) {
            for (uint24 j = i; j < 16; j++) {
                if (i == 0 && j == 15) {
                    continue;
                }

                console.log("\n\nOutputing (i, j)", i, j);
                (LKey low, LKey high, LKey peak, LKey stopRange) = liqTree.getKeys(i, j);

                (range, base) = peak.explode();
                console.log("Peak (r,b,v)", range, base, LKey.unwrap(peak));
                (range, base) = stopRange.explode();
                console.log("Stop (r,b,v)", range, base, LKey.unwrap(stopRange));
                (range, base) = low.explode();
                console.log("Low (r,b,v)", range, base, LKey.unwrap(low));
                (range, base) = high.explode();
                console.log("High (r,b,v)", range, base, LKey.unwrap(high));

            }
        }
    }

    function testRootNodeOnly() public {
        LKey root = liqTree.root;

        vm.warp(0); // T0
        liqTree.addInfRangeMLiq(8430); // Step 1
        liqTree.addInfRangeTLiq(4381, 832e18, 928e6); // Step 2

        vm.warp(60 * 60); // T3600 (1hr)
        liqTree.feeRateSnapshotTokenX.add(113712805933826); // 5.4% APR as Q192.64
        liqTree.feeRateSnapshotTokenY.add(113712805933826);

        // Verify root state is as expected
        assertEq(liqTree.nodes[root].mLiq, 8430);
        assertEq(liqTree.nodes[root].subtreeMLiq, 134880);
        assertEq(liqTree.nodes[root].tLiq, 4381);
        assertEq(liqTree.nodes[root].tokenX.borrowed, 832e18);
        assertEq(liqTree.nodes[root].tokenX.subtreeBorrowed, 832e18);
        assertEq(liqTree.nodes[root].tokenY.borrowed, 928e6);
        assertEq(liqTree.nodes[root].tokenY.subtreeBorrowed, 928e6);

        // Testing 4 methods addInfRangeMLiq, removeInfRangeMLiq, addInfRangeTLiq, removeInfRangeTLiq
        // Assert tree structure and fee calculations after each operation
        liqTree.addInfRangeMLiq(9287);

        assertEq(liqTree.nodes[root].tokenX.cummulativeEarnedPerMLiq, 38024667284);
        assertEq(liqTree.nodes[root].tokenX.subtreeCummulativeEarnedPerMLiq, 38024667284);
        assertEq(liqTree.nodes[root].tokenY.cummulativeEarnedPerMLiq, 0);
        assertEq(liqTree.nodes[root].tokenY.subtreeCummulativeEarnedPerMLiq, 0);

        assertEq(liqTree.nodes[root].mLiq, 17717);
        assertEq(liqTree.nodes[root].subtreeMLiq, 283472);
        assertEq(liqTree.nodes[root].tLiq, 4381);
        assertEq(liqTree.nodes[root].tokenX.borrowed, 832e18);
        assertEq(liqTree.nodes[root].tokenX.subtreeBorrowed, 832e18);
        assertEq(liqTree.nodes[root].tokenY.borrowed, 928e6);
        assertEq(liqTree.nodes[root].tokenY.subtreeBorrowed, 928e6);

        vm.warp(22000); // T22000
        liqTree.feeRateSnapshotTokenX.add(74672420010376264941568); // 693792000.0% APR as Q192.64 from T22000 - T3600
        liqTree.feeRateSnapshotTokenY.add(74672420010376264941568);

        liqTree.removeInfRangeMLiq(3682);

        /* 
                      1188101861132416784
            Expected: 11881018269102162284
              Actual: 11881018269102163474
      */

        // 11881018231077494784
        // 11881018269102162068

        // In code the rates are correct, both 74672420010376264941568
        // x num 62127453448633052431384576000000000000000000 (correct)
        // y num 69296005769629173865775104000000 (correct)
        // x earn as Q192.64 is 219166102643763942933991985099057402494 (off by +42933991985099057402494)
        // y earn as Q192.64 is 244454499102659782503298752 (ending 782503298752 should be 8e11)
        // x earn as token is 11881018231077496190 (real 1.18810182310774961900999040469605463678530107851649688655015 × 10^19)
        // y earn as token is 13251904 (real 1.32519049500479765197268160192844987932403455488383769989013 × 10^7)
        // X total 11881018269102163474 (off by 0)
        // Y total 13251904 (off by +1 if we round up)
        assertEq(liqTree.nodes[root].tokenX.cummulativeEarnedPerMLiq, 11881018269102163474);
        assertEq(liqTree.nodes[root].tokenX.subtreeCummulativeEarnedPerMLiq, 11881018269102163474);
        assertEq(liqTree.nodes[root].tokenY.cummulativeEarnedPerMLiq, 13251904);
        assertEq(liqTree.nodes[root].tokenY.subtreeCummulativeEarnedPerMLiq, 13251904);

        assertEq(liqTree.nodes[root].mLiq, 14035);
        assertEq(liqTree.nodes[root].subtreeMLiq, 224560);
        assertEq(liqTree.nodes[root].tLiq, 4381);
        assertEq(liqTree.nodes[root].tokenX.borrowed, 832e18);
        assertEq(liqTree.nodes[root].tokenX.subtreeBorrowed, 832e18);
        assertEq(liqTree.nodes[root].tokenY.borrowed, 928e6);
        assertEq(liqTree.nodes[root].tokenY.subtreeBorrowed, 928e6);

        vm.warp(37002); // T37002
        liqTree.feeRateSnapshotTokenX.add(6932491854677024); // 7.9% APR as Q192.64 T37002 - T22000
        liqTree.feeRateSnapshotTokenY.add(6932491854677024);

        liqTree.addInfRangeTLiq(7287, 9184e18, 7926920e6);

        assertEq(liqTree.nodes[root].tokenX.cummulativeEarnedPerMLiq, 11881019661491126559); // fix rounding, add 1
        assertEq(liqTree.nodes[root].tokenX.subtreeCummulativeEarnedPerMLiq, 11881019661491126559);
        assertEq(liqTree.nodes[root].tokenY.cummulativeEarnedPerMLiq, 13251905); // fix rounding, add 1
        assertEq(liqTree.nodes[root].tokenY.subtreeCummulativeEarnedPerMLiq, 13251905);

        assertEq(liqTree.nodes[root].mLiq, 14035);
        assertEq(liqTree.nodes[root].subtreeMLiq, 224560);
        assertEq(liqTree.nodes[root].tLiq, 11668);
        assertEq(liqTree.nodes[root].tokenX.borrowed, 10016e18);
        assertEq(liqTree.nodes[root].tokenX.subtreeBorrowed, 10016e18);
        assertEq(liqTree.nodes[root].tokenY.borrowed, 7927848e6);
        assertEq(liqTree.nodes[root].tokenY.subtreeBorrowed, 7927848e6);

        // liqTree.removeInfRangeMLiq(4923);

        /*
        assertEq(liqTree.nodes[root].mLiq, 0);
        assertEq(liqTree.nodes[root].subtreeMLiq, 0);
        assertEq(liqTree.nodes[root].tLiq, 0);
        assertEq(liqTree.nodes[root].tokenX.borrowed, 0);
        assertEq(liqTree.nodes[root].tokenX.sbutreeBorrowed, 0);
        assertEq(liqTree.nodes[root].tokenY.borrowed, 0);
        assertEq(liqTree.nodes[root].tokenY.sbutreeBorrowed, 0);
        */
    }

    function testExample2Fees() public {
        // Keys

        uint256 t0 = block.timestamp;

        LKey root = liqTree.root;
        LKey L = _nodeKey(1, 0, 16);
        LKey LL = _nodeKey(2, 0, 16);
        LKey LLL = _nodeKey(3, 0, 16);
        LKey LLR = _nodeKey(3, 1, 16);
        LKey LLLR = _nodeKey(4, 1, 16);
        LKey LLRL = _nodeKey(4, 2, 16);

        // Step 1) add maker liq ---------------------------------------------------
        vm.warp(t0);

        // 1.a) Add mLiq to LL ---------------------------------------------------
        liqTree.addMLiq(LiqRange(0, 3), 2);  // LL

        assertEq(liqTree.nodes[root].mLiq, 0);
        assertEq(liqTree.nodes[L].mLiq, 0);
        assertEq(liqTree.nodes[LL].mLiq, 2);

        assertEq(liqTree.nodes[root].subtreeMLiq, 8);
        assertEq(liqTree.nodes[L].subtreeMLiq, 8);
        assertEq(liqTree.nodes[LL].subtreeMLiq, 8);

        // 1.b) Add mLiq to LL ---------------------------------------------------
        liqTree.addMLiq(LiqRange(0, 2), 7);  // LLL, LLRL

        assertEq(liqTree.nodes[root].mLiq, 0);
        assertEq(liqTree.nodes[L].mLiq, 0);
        assertEq(liqTree.nodes[LL].mLiq, 2);
        assertEq(liqTree.nodes[LLL].mLiq, 7);
        assertEq(liqTree.nodes[LLR].mLiq, 0);
        assertEq(liqTree.nodes[LLRL].mLiq, 7);

        assertEq(liqTree.nodes[root].subtreeMLiq, 0 + 0 + 8 + 14 + 0 + 7); // 29
        assertEq(liqTree.nodes[L].subtreeMLiq, 0 + 8 + 14 + 0 + 7); // 29
        assertEq(liqTree.nodes[LL].subtreeMLiq, 8 + 14 + 0 + 7); // 29
        assertEq(liqTree.nodes[LLL].subtreeMLiq, 14);
        assertEq(liqTree.nodes[LLR].subtreeMLiq, 0 + 7);
        assertEq(liqTree.nodes[LLRL].subtreeMLiq, 7);

        // 1.c) Add mliq to L ---------------------------------------------------
        liqTree.addMLiq(LiqRange(0, 7), 20); // L

        assertEq(liqTree.nodes[root].mLiq, 0);
        assertEq(liqTree.nodes[L].mLiq, 20);
        assertEq(liqTree.nodes[LL].mLiq, 2);
        assertEq(liqTree.nodes[LLL].mLiq, 7);
        assertEq(liqTree.nodes[LLR].mLiq, 0);
        assertEq(liqTree.nodes[LLRL].mLiq, 7);

        assertEq(liqTree.nodes[root].subtreeMLiq, 0 + 160 + 8 + 14 + 0 + 7); // 189
        assertEq(liqTree.nodes[L].subtreeMLiq, 160 + 8 + 14 + 0 + 7); // 189
        assertEq(liqTree.nodes[LL].subtreeMLiq, 8 + 14 + 0 + 7); // 29
        assertEq(liqTree.nodes[LLL].subtreeMLiq, 14);
        assertEq(liqTree.nodes[LLR].subtreeMLiq, 0 + 7);
        assertEq(liqTree.nodes[LLRL].subtreeMLiq, 7);

        // Step 2) add taker liq
        vm.warp(t0 + 5);

        // 2.a) add tLiq to LLL
        liqTree.addTLiq(LiqRange(0, 1), 5, 12, 22); // LLL

        assertEq(liqTree.nodes[root].tLiq, 0);
        assertEq(liqTree.nodes[L].tLiq, 0);
        assertEq(liqTree.nodes[LL].tLiq, 0);
        assertEq(liqTree.nodes[LLL].tLiq, 5);
        assertEq(liqTree.nodes[LLR].tLiq, 0);
        assertEq(liqTree.nodes[LLRL].tLiq, 0);

        assertEq(liqTree.nodes[root].tokenX.borrowed, 0);
        assertEq(liqTree.nodes[L].tokenX.borrowed, 0);
        assertEq(liqTree.nodes[LL].tokenX.borrowed, 0);
        assertEq(liqTree.nodes[LLL].tokenX.borrowed, 12);
        assertEq(liqTree.nodes[LLR].tokenX.borrowed, 0);
        assertEq(liqTree.nodes[LLRL].tokenX.borrowed, 0);

        assertEq(liqTree.nodes[root].tokenX.subtreeBorrowed, 12);
        assertEq(liqTree.nodes[L].tokenX.subtreeBorrowed, 12);
        assertEq(liqTree.nodes[LL].tokenX.subtreeBorrowed, 12);
        assertEq(liqTree.nodes[LLL].tokenX.subtreeBorrowed, 12);
        assertEq(liqTree.nodes[LLR].tokenX.subtreeBorrowed, 0);
        assertEq(liqTree.nodes[LLRL].tokenX.subtreeBorrowed, 0);

        assertEq(liqTree.nodes[root].tokenY.borrowed, 0);
        assertEq(liqTree.nodes[L].tokenY.borrowed, 0);
        assertEq(liqTree.nodes[LL].tokenY.borrowed, 0);
        assertEq(liqTree.nodes[LLL].tokenY.borrowed, 22);
        assertEq(liqTree.nodes[LLR].tokenY.borrowed, 0);
        assertEq(liqTree.nodes[LLRL].tokenY.borrowed, 0);

        assertEq(liqTree.nodes[root].tokenY.subtreeBorrowed, 22);
        assertEq(liqTree.nodes[L].tokenY.subtreeBorrowed, 22);
        assertEq(liqTree.nodes[LL].tokenY.subtreeBorrowed, 22);
        assertEq(liqTree.nodes[LLL].tokenY.subtreeBorrowed, 22);
        assertEq(liqTree.nodes[LLR].tokenY.subtreeBorrowed, 0);
        assertEq(liqTree.nodes[LLRL].tokenY.subtreeBorrowed, 0);

        // 2.b) add tLiq to L
        liqTree.addTLiq(LiqRange(0, 7), 9, 3, 4); // L

        assertEq(liqTree.nodes[root].tLiq, 0);
        assertEq(liqTree.nodes[L].tLiq, 9);
        assertEq(liqTree.nodes[LL].tLiq, 0);
        assertEq(liqTree.nodes[LLL].tLiq, 5);
        assertEq(liqTree.nodes[LLR].tLiq, 0);
        assertEq(liqTree.nodes[LLRL].tLiq, 0);

        assertEq(liqTree.nodes[root].tokenX.borrowed, 0);
        assertEq(liqTree.nodes[L].tokenX.borrowed, 3);
        assertEq(liqTree.nodes[LL].tokenX.borrowed, 0);
        assertEq(liqTree.nodes[LLL].tokenX.borrowed, 12);
        assertEq(liqTree.nodes[LLR].tokenX.borrowed, 0);
        assertEq(liqTree.nodes[LLRL].tokenX.borrowed, 0);

        assertEq(liqTree.nodes[root].tokenX.subtreeBorrowed, 15);
        assertEq(liqTree.nodes[L].tokenX.subtreeBorrowed, 15);
        assertEq(liqTree.nodes[LL].tokenX.subtreeBorrowed, 12);
        assertEq(liqTree.nodes[LLL].tokenX.subtreeBorrowed, 12);
        assertEq(liqTree.nodes[LLR].tokenX.subtreeBorrowed, 0);
        assertEq(liqTree.nodes[LLRL].tokenX.subtreeBorrowed, 0);

        assertEq(liqTree.nodes[root].tokenY.borrowed, 0);
        assertEq(liqTree.nodes[L].tokenY.borrowed, 4);
        assertEq(liqTree.nodes[LL].tokenY.borrowed, 0);
        assertEq(liqTree.nodes[LLL].tokenY.borrowed, 22);
        assertEq(liqTree.nodes[LLR].tokenY.borrowed, 0);
        assertEq(liqTree.nodes[LLRL].tokenY.borrowed, 0);

        assertEq(liqTree.nodes[root].tokenY.subtreeBorrowed, 26);
        assertEq(liqTree.nodes[L].tokenY.subtreeBorrowed, 26);
        assertEq(liqTree.nodes[LL].tokenY.subtreeBorrowed, 22);
        assertEq(liqTree.nodes[LLL].tokenY.subtreeBorrowed, 22);
        assertEq(liqTree.nodes[LLR].tokenY.subtreeBorrowed, 0);
        assertEq(liqTree.nodes[LLRL].tokenY.subtreeBorrowed, 0);

        // Step 3) add new position that effects previous nodes, calculate fees
        vm.warp(t0 + 10);

        // Let's say the rate is a 128.128 number
        // With 0.000000007927 that has 8 zeros 
        // The first 128 bits should represent 000000007927
        // ?

        // OG math
        // (5 / (365 * 24 * 60 * 60)) = 0.000000007927
        // rate = (5 << 128) / ((365 * 24 * 60 * 60) << 128)
        liqTree.feeRateSnapshotTokenX.add(146227340272);
        liqTree.addMLiq(LiqRange(1, 3), 13); // LLLR, LLR

        assertEq(liqTree.nodes[root].tokenX.cummulativeEarnedPerMLiq, 0);
        assertEq(liqTree.nodes[L].tokenX.cummulativeEarnedPerMLiq, 0);
        assertEq(liqTree.nodes[LL].tokenX.cummulativeEarnedPerMLiq, 0);
        assertEq(liqTree.nodes[LLL].tokenX.cummulativeEarnedPerMLiq, 0);
        assertEq(liqTree.nodes[LLR].tokenX.cummulativeEarnedPerMLiq, 0);
        assertEq(liqTree.nodes[LLRL].tokenX.cummulativeEarnedPerMLiq, 0);

        assertEq(liqTree.nodes[root].tokenX.subtreeCummulativeEarnedPerMLiq, 0);
        assertEq(liqTree.nodes[L].tokenX.subtreeCummulativeEarnedPerMLiq, 0);
        assertEq(liqTree.nodes[LL].tokenX.subtreeCummulativeEarnedPerMLiq, 0);
        assertEq(liqTree.nodes[LLL].tokenX.subtreeCummulativeEarnedPerMLiq, 0);
        assertEq(liqTree.nodes[LLR].tokenX.subtreeCummulativeEarnedPerMLiq, 0);
        assertEq(liqTree.nodes[LLRL].tokenX.subtreeCummulativeEarnedPerMLiq, 0);

        // Step 4) verify

        // LLLR
        // 0, 0
        
        // LLL
        // 0, 0.00000000164

        // LL
        // 0.0000000010013052, 0

        // L
        // 
    }

    function _printTree() public {

    }

    function _printKey(LKey k) public {
        {
            (uint24 rootLow, uint24 rootBase) = k.explode();
            console.log("(range, base, num)", rootLow, rootBase, LKey.unwrap(k));
        }
    }

    function _nodeKey(uint24 depth, uint24 index, uint24 offset) public returns (LKey) {
        uint24 baseStep = uint24(offset / 2 ** depth);

        uint24 range = offset >> depth;
        uint24 base = offset + baseStep * index;
        return LKeyImpl.makeKey(range, base);
    }

    function _nodeDepthIndex(uint24 depth, uint24 index, LiqTree storage tree) internal returns (LiqNode storage) {
        return tree.nodes[_nodeKey(depth, index, tree.offset)];
    }
}

/**
 * Re-writing example 2 using Q192.64 numbers

 Time Premium Calculation (Example 2)

 
                                                                root [0, 15]
                                                        ____----    ----____
                                          __________----------                    ----------__________
                                        L [0, 7]                                                      
                                   __--  --__                  
                         __---                   ---__              
                     /                                   \                           
                  LL [0, 3]                                 LR [4, 7]                
                /           \                            /       \                           
              /               \                        /           \                                         
            /                   \                    /               \                            
          LLL [0, 1]            LLR [2, 3]         LRL [4, 5]            LRR [6, 7]       
         /     \              /     \            /     \                /     \              
        /       \            /       \          /       \              /       \          
     LLLL[0]   LLLR[1]   LLRL[2]    LLRR[3]   LRLL[4]  LRLR[5]      LRRL[6]     LRRR[7] 


make(low, high, liq, tokenX, tokenY)
take(low, high, liq, tokenX, tokenY)

Adding Q192.64 numbers in ()

Step 1) add maker Liq -------------------------------------------------------------------

make(low=0, high=3, liq=2, tokenX=2, tokenY=7)  // LL

root [0, 15] mLiq: 0
L    [0, 7]  mLiq: 0
LL   [0, 3]  mLiq: 2

-

make(low=0, high=2, liq=7, tokenX=5, tokenY=8)  // LLL, LLRL

root [0, 15] mLiq: 0
L    [0, 7]  mLiq: 0
LL   [0, 3]  mLiq: 2
LLL  [0, 1]  mLiq: 7
LLR  [2, 3]  mLiq: 0
LLRL [2]     mLiq: 7

-

make(low=0, high=7, liq=20, tokenX=9, tokenY=12) // L


root [0, 15] mLiq: 0
L    [0, 7]  mLiq: 20
LL   [0, 3]  mLiq: 2
LLL  [0, 1]  mLiq: 7
LLR  [2, 3]  mLiq: 0
LLRL [2]     mLiq: 7




Step 2) add taker liq --------------------------------------------------------------------
t = 5s

take(low=0, high=1, liq=5, tokenX=12, tokenY=22) // LLL

root [0, 15] mLiq: 0,  tLiq: 0, borrowX: 0
L    [0, 7]  mLiq: 20, tLiq: 0, borrowX: 0
LL   [0, 3]  mLiq: 2,  tLiq: 0, borrowX: 0
LLL  [0, 1]  mLiq: 7,  tLiq: 5, borrowX: 12
LLR  [2, 3]  mLiq: 0,  tLiq: 0, borrowX: 0
LLRL [2]     mLiq: 7,  tLiq: 0, borrowX: 0

- 

take(low=0, high=7, liq=9, tokenX=3, tokenY=4) // L

root [0, 15] mLiq: 0,  tLiq: 0, borrowX: 0
L    [0, 7]  mLiq: 20, tLiq: 9, borrowX: 3
LL   [0, 3]  mLiq: 2,  tLiq: 0, borrowX: 0
LLL  [0, 1]  mLiq: 7,  tLiq: 5, borrowX: 12
LLR  [2, 3]  mLiq: 0,  tLiq: 0, borrowX: 0
LLRL [2]     mLiq: 7,  tLiq: 0, borrowX: 0





Step 3) calculate fees --------------------------------------------------------------------
t=10s

make(low=1, high=3, liq=13, tokenX=19, tokenY=1) // LLLR, LLR

3.a) calculate earned fees before adding new maker position

Update LLLR first

Rate will be a Q192.64 number
Round rate down? 


LLLR
	// 1) Compute Fees
	rate 5%
	rateDiff = t10 - t5 = 0.05 * (5 / (365 * 24 * 60 * 60)) = 0.000000007927 (146227340272)
	subtreeFees = 0 * rateDiff = 0
	nodeFees = 0 * rateDiff = 0
	snapshot = t10

	// 2) Compute total maker liq
	A[level] = LLL.mLiq + LL.mLiq + L.mLiq + root.mLiq = 7 + 2 + 20 + 0 = 29
	perTickMLiq = 0 + 29 = 29
	totalMLiq = 0 + 29 * 1 = 29

	// 3) Accumulate fee
	subtreeCummulativeEarnPerMLiq += 0 / 29 = 0
	nodeCummulativeEarnPerMLiq += 0 / 29 = 0

LLL

	subtreeFees = 0
	nodeFees = 12 * 146227340272 = 1754728083264 (X64)

	A[level] = LL + L + root = 2 + 20 + 0 = 22
	perTickMLiq = 7 + 22 = 29
	totalMLiq = 0 + 29 * 2 = 58

	subtreeCummulativeEarnPerMLiq += 0
	nodeCummulativeEarnPerMLiq += 1754728083264 / 58 = 30253932470 (X64) or 1.6400689655101872e-09

LL
// 30253932470.068966
	subtreeFees = 12 * 0.000000007927 = 9.5124e-8 (1754728083264)
	nodeFees = 0

	A[level] = 20
	perTickMLiq = 2 + 20 = 22
	totalMLiq = 7 + 22 * 4 = 95 

	subtreeCummulativeEarnPerMLiq += 9.5124e-8 / 95 ~= 0.0000000010013052 (would also truncate to 0)
	nodeCummulativeEarnPerMLiq += 0

L

	subtreeFees = 12 * rateDiff = 9.5124e-8 (1754728083264)
	nodeFees = 3 * rateDiff = 2.3781e-8 (438682020816)

	A[level] = 0
	perTickMLiq = 20 + 0 = 20
	totalMLiq = 16 + 20 * 8 = 176 (3246626956972881084416)

	subtree..Earn... += 9.5124e-8 / 176 = ... lol 0
	node...Earn... += 2.3781e-8 / 176 = ... 0

--

Update LLR

LLR
	subtreeFees = 0
	nodeFees = 0

	...

LL
	
	// will no-op because the snapshot was just updated to t10 
	...

L

	// will no-op because the snapshot was just updated to t10 
	subtreeFees = 	

 */