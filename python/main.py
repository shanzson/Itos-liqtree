from LiqTree.LiquidityTree import LiquidityTree


def root_node_only():
    liq_tree = LiquidityTree(4)

    # T0
    # liq_tree.addInfRangeMLiq(1)

'''
    function testRootNodeOnly() public {
        LiqNode storage root = liqTree.nodes[liqTree.root];

        vm.warp(0); // T0
        liqTree.addInfRangeMLiq(8430); // Step 1
        liqTree.addInfRangeTLiq(4381, 832e18, 928e6); // Step 2

        vm.warp(60 * 60); // T3600 (1hr)
        liqTree.feeRateSnapshotTokenX.add(113712805933826); // 5.4% APR as Q192.64
        liqTree.feeRateSnapshotTokenY.add(113712805933826);

        // Verify root state is as expected
        assertEq(root.mLiq, 8430);
        assertEq(root.subtreeMLiq, 134880);
        assertEq(root.tLiq, 4381);
        assertEq(root.tokenX.borrowed, 832e18);
        assertEq(root.tokenX.subtreeBorrowed, 832e18);
        assertEq(root.tokenY.borrowed, 928e6);
        assertEq(root.tokenY.subtreeBorrowed, 928e6);

        // Testing 4 methods addInfRangeMLiq, removeInfRangeMLiq, addInfRangeTLiq, removeInfRangeTLiq
        // Assert tree structure and fee calculations after each operation
        liqTree.addInfRangeMLiq(9287);

        assertEq(root.tokenX.cummulativeEarnedPerMLiq, 38024667284);
        assertEq(root.tokenX.subtreeCummulativeEarnedPerMLiq, 38024667284);
        assertEq(root.tokenY.cummulativeEarnedPerMLiq, 0);
        assertEq(root.tokenY.subtreeCummulativeEarnedPerMLiq, 0);

        assertEq(root.mLiq, 17717);
        assertEq(root.subtreeMLiq, 283472);
        assertEq(root.tLiq, 4381);
        assertEq(root.tokenX.borrowed, 832e18);
        assertEq(root.tokenX.subtreeBorrowed, 832e18);
        assertEq(root.tokenY.borrowed, 928e6);
        assertEq(root.tokenY.subtreeBorrowed, 928e6);

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
        assertEq(root.tokenX.cummulativeEarnedPerMLiq, 11881018269102163474);
        assertEq(root.tokenX.subtreeCummulativeEarnedPerMLiq, 11881018269102163474);
        assertEq(root.tokenY.cummulativeEarnedPerMLiq, 13251904);
        assertEq(root.tokenY.subtreeCummulativeEarnedPerMLiq, 13251904);

        assertEq(root.mLiq, 14035);
        assertEq(root.subtreeMLiq, 224560);
        assertEq(root.tLiq, 4381);
        assertEq(root.tokenX.borrowed, 832e18);
        assertEq(root.tokenX.subtreeBorrowed, 832e18);
        assertEq(root.tokenY.borrowed, 928e6);
        assertEq(root.tokenY.subtreeBorrowed, 928e6);

        vm.warp(37002); // T37002
        liqTree.feeRateSnapshotTokenX.add(6932491854677024); // 7.9% APR as Q192.64 T37002 - T22000
        liqTree.feeRateSnapshotTokenY.add(6932491854677024);

        liqTree.addInfRangeTLiq(7287, 9184e18, 7926920e6);

        assertEq(root.tokenX.cummulativeEarnedPerMLiq, 11881019661491126559); // fix rounding, add 1
        assertEq(root.tokenX.subtreeCummulativeEarnedPerMLiq, 11881019661491126559);
        assertEq(root.tokenY.cummulativeEarnedPerMLiq, 13251905); // fix rounding, add 1
        assertEq(root.tokenY.subtreeCummulativeEarnedPerMLiq, 13251905);

        assertEq(root.mLiq, 14035);
        assertEq(root.subtreeMLiq, 224560);
        assertEq(root.tLiq, 11668);
        assertEq(root.tokenX.borrowed, 10016e18);
        assertEq(root.tokenX.subtreeBorrowed, 10016e18);
        assertEq(root.tokenY.borrowed, 7927848e6);
        assertEq(root.tokenY.subtreeBorrowed, 7927848e6);

        vm.warp(57212); // T57212
        liqTree.feeRateSnapshotTokenX.add(1055375100301031600000000); // 11.1% APR as Q192.64 TT57212 - T37002
        liqTree.feeRateSnapshotTokenY.add(1055375100301031600000000);
        
        liqTree.removeInfRangeTLiq(4923, 222e18, 786e6);

        /*
            x-rate 1055375100301031600000000 (correct)
            x num 10570637004615132505600000000000000000000000000 (correct)
            x Q.64 47072662115314982657641610260064125400783 (47072662115314980000000000000000000000000 is correct)
            x token 2551814126505030241953 (2.55181412650503024195387164028103035638433335980020216618053 × 10^21 is correct) // need to round up 1
            y-rate 1055375100301031600000000
            y num 8366853378171332767996800000000000000 (correct)
            y Q.64 37258876817649326540776629853936 (3.7258876817649324e+31 is correct)
            y token 2019807759503 (2.01980775950325988354767545683493270255599285721099372431609 × 10^12 is correct)
  */

        assertEq(root.tokenX.cummulativeEarnedPerMLiq, 2563695146166521368512);
        assertEq(root.tokenX.subtreeCummulativeEarnedPerMLiq, 2563695146166521368512);
        assertEq(root.tokenY.cummulativeEarnedPerMLiq, 2019821011408);
        assertEq(root.tokenY.subtreeCummulativeEarnedPerMLiq, 2019821011408);

        assertEq(root.mLiq, 14035);
        assertEq(root.subtreeMLiq, 224560);
        assertEq(root.tLiq, 6745);
        assertEq(root.tokenX.borrowed, 9794e18);
        assertEq(root.tokenX.subtreeBorrowed, 9794e18);
        assertEq(root.tokenY.borrowed, 7927062e6);
        assertEq(root.tokenY.subtreeBorrowed, 7927062e6);
    }
'''

def main():
    liq_tree = LiquidityTree()

    print("hello world")


if __name__ == "__main__":
    main()
