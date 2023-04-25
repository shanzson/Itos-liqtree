from dataclasses import dataclass

#  Liquidity Tree
#
#  Consider a tree with a depth of 4
#
#                                                               root
#                                                       ____----    ----____
#                                   __________----------                    ----------__________
#                                  L                                                            R
#                             __--  --__                                                    __--  --__
#                        __---          ---__                                          __---          ---__
#                      /                       \                                     /                       \
#                   LL                           LR                               RL                           RR
#                 /   \                         /   \                           /   \                         /   \
#               /       \                     /       \                       /       \                     /       \
#             /           \                 /           \                   /           \                 /           \
#           LLL            LLR            LRL            LRR              RLL            RLR            RRL            RRR
#          /   \          /   \          /   \          /   \            /   \          /   \          /   \          /   \
#         /     \        /     \        /     \        /     \          /     \        /     \        /     \        /     \
#      LLLL    LLLR    LLRL    LLRR   LRLL    LRLR   LRRL    LRRR      RLLL   RLLR   RLRL    RLRR   RRLL    RRLR   RRRL    RRRR


@dataclass
class LiqRange:
    low: int
    high: int


@dataclass
class LiqNode:
    m_liq: int = 0
    t_liq: int = 0
    subtree_m_liq: int = 0

    token_x_borrowed: int = 0
    token_x_subtree_borrowed: int = 0
    token_x_fee_rate_snapshot: int = 0
    token_x_cummulative_earned_per_m_liq: int = 0
    token_x_cummulative_earned_per_m_subtree_liq: int = 0

    token_y_borrowed: int = 0
    token_y_subtree_borrowed: int = 0
    token_y_fee_rate_snapshot: int = 0
    token_y_cummulative_earned_per_m_liq: int = 0
    token_y_cummulative_earned_per_m_subtree_liq: int = 0

    # Can think of node in a tree as the combination key of (value, base)
    # ex. R is (1, 1) while LRR is (3, 2)
    # value is the nodes binary value. If in the tree 0 is prepended for a left traversal, and a 1 for a right traversal
    value: int = 0
    depth: int = 0

    parent = None
    left = None
    right = None


class LiquidityTree:
    # region Initialization
    def __init__(self, depth: int):
        self.root = LiqNode()
        self.width = (1 << depth)
        self._init_tree(self.root, None, 0, 0, depth)

    def _init_tree(self, current: LiqNode, parent: LiqNode, value: int, depth: int, max_depth: int) -> None:
        current.parent = parent

        if depth > max_depth:
            return

        current.left = LiqNode()
        current.right = LiqNode()

        current.left.depth = depth
        current.left.value = (0 << depth) + value
        current.right.depth = depth
        current.right = (1 << depth) + value

        self._init_tree(current.left, current, depth + 1, max_depth)
        self._init_tree(current.right, current, depth + 1, max_depth)

    # endregion

    # region Liquidity Limited Range Methods

    def add_m_liq(self, liq_range: LiqRange, liq: int) -> None:
        pass

    def remove_m_liq(self, liq_range: LiqRange, liq: int) -> None:
        pass

    def add_t_liq(self, liq_range: LiqRange, liq: int, amount_x: int, amount_y: int) -> None:
        pass

    def remove_t_liq(self, liq_range: LiqRange, liq: int, amount_x: int, amount_y: int) -> None:
        pass

    # endregion

    # region Liquidity INF Range Methods

    def add_inf_range_m_liq(self, liq: int) -> None:
        # TODO: fee
        self.root.m_liq += liq
        self.root.subtree_m_liq += self.width * liq

    def remove_inf_range_m_liq(self, liq: int) -> None:
        # TODO: fee
        self.root.m_liq -= liq
        self.root.subtree_m_liq -= self.width * liq

    def add_inf_range_t_liq(self, liq: int, amount_x: int, amount_y: int) -> None:
        # TODO: fee
        self.root.t_liq += liq
        self.root.token_x_borrowed += amount_x
        self.root.token_x_subtree_borrowed += amount_x
        self.root.token_y_borrowed += amount_y
        self.root.token_x_subtree_borrowed += amount_y

    def remove_inf_range_t_liq(self, liq: int, amount_x: int, amount_y: int) -> None:
        # TODO: fee
        self.root.t_liq -= liq
        self.root.token_x_borrowed -= amount_x
        self.root.token_x_subtree_borrowed -= amount_x
        self.root.token_y_borrowed -= amount_y
        self.root.token_x_subtree_borrowed -= amount_y

    # endregion

    # region Sol

    def _l_key_by_index(self, depth: int, row: int) -> int:
        return self._l_key(depth, row)

    def _l_key(self, base: int, range: int) -> int:
        return base << 24 | range

    # endregion


'''
contract DenseTreeTreeStructureTest is Test {
    LiqTree public liqTree;
    using LiqTreeImpl for LiqTree;
    using LKeyImpl for LKey;
    using FeeRateSnapshotImpl for FeeRateSnapshot;
    
    function setUp() public {
        // A depth of 4 creates a tree that covers an absolute range of 16 ([0, 15]). 
        // ie. A complete tree matching the ascii documentation. 
        liqTree.init(4);
    }

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

    function testLeafNodeOnly() public {

    }

    function testSingleNodeOnly() public {

    }

    function testLeftLegOnly() public {
        LiqNode storage root = liqTree.nodes[liqTree.root];
        LiqNode storage L = liqTree.nodes[_nodeKey(1, 0, liqTree.offset)];
        LiqNode storage LL = liqTree.nodes[_nodeKey(2, 0, liqTree.offset)];
        LiqNode storage LR = liqTree.nodes[_nodeKey(2, 1, liqTree.offset)];
        LiqNode storage LLR = liqTree.nodes[_nodeKey(3, 1, liqTree.offset)];
        LiqNode storage LLRR = liqTree.nodes[_nodeKey(4, 3, liqTree.offset)];

        // Step 1) Allocate different mLiq + tLiq values for each node
        vm.warp(0); // T0

        liqTree.addInfRangeMLiq(8430);              // root (INF)
        liqTree.addMLiq(LiqRange(0, 7), 377);       // L    (0-7)
        liqTree.addMLiq(LiqRange(0, 3), 9082734);   // LL   (0-3)
        liqTree.addMLiq(LiqRange(4, 7), 1111);      // LR   (4-7)
        liqTree.addMLiq(LiqRange(2, 3), 45346);     // LLR  (2-3)
        liqTree.addMLiq(LiqRange(3, 3), 287634865); // LLRR   (3)

        liqTree.addInfRangeTLiq(4430, 492e18, 254858e6);            // root
        liqTree.addTLiq(LiqRange(0, 7), 77, 998e18, 353e6);         // L 
        liqTree.addTLiq(LiqRange(0, 3), 82734, 765e18, 99763e6);    // LL
        liqTree.addTLiq(LiqRange(4, 7), 111, 24e18, 552e6);         // LR
        liqTree.addTLiq(LiqRange(2, 3), 5346, 53e18, 8765e6);       // LLR
        liqTree.addTLiq(LiqRange(3, 3), 7634865, 701e18, 779531e6); // LLRR

        // mLiq
        assertEq(root.mLiq, 8430);
        assertEq(L.mLiq, 377);
        assertEq(LL.mLiq, 9082734);
        assertEq(LR.mLiq, 1111);
        assertEq(LLR.mLiq, 45346);
        assertEq(LLRR.mLiq, 287634865);

        // tLiq
        assertEq(root.tLiq, 4430);
        assertEq(L.tLiq, 77);
        assertEq(LL.tLiq, 82734);
        assertEq(LR.tLiq, 111);
        assertEq(LLR.tLiq, 5346);
        assertEq(LLRR.tLiq, 7634865);

        // subtreeMLiq
        assertEq(root.subtreeMLiq, 324198833); // 8430*16 + 377*8 + 9082734*4 + 1111*4 + 45346*2 + 287634865*1
        assertEq(L.subtreeMLiq, 324063953);    // 377*8 + 9082734*4 + 1111*4 + 45346*2 + 287634865*1
        assertEq(LL.subtreeMLiq, 324056493);   // 9082734*4 + 45346*2 + 287634865*1
        assertEq(LR.subtreeMLiq, 4444);        // 1111*4
        assertEq(LLR.subtreeMLiq, 287725557);  // 45346*2 + 287634865*1
        assertEq(LLRR.subtreeMLiq, 287634865); // 287634865*1

        // borrowedX
        assertEq(root.tokenX.borrowed, 492e18);
        assertEq(L.tokenX.borrowed, 998e18);
        assertEq(LL.tokenX.borrowed, 765e18);
        assertEq(LR.tokenX.borrowed, 24e18);
        assertEq(LLR.tokenX.borrowed, 53e18);
        assertEq(LLRR.tokenX.borrowed, 701e18);
 
        // borrowedY
        assertEq(root.tokenY.borrowed, 254858e6);
        assertEq(L.tokenY.borrowed, 353e6);
        assertEq(LL.tokenY.borrowed, 99763e6);
        assertEq(LR.tokenY.borrowed, 552e6);
        assertEq(LLR.tokenY.borrowed, 8765e6);
        assertEq(LLRR.tokenY.borrowed, 779531e6);

        // subtreeBorrowedX
        assertEq(root.tokenX.subtreeBorrowed, 3033e18); // 492e18 + 998e18 + 765e18 + 53e18 + 701e18 + 24e18
        assertEq(L.tokenX.subtreeBorrowed, 2541e18);    // 998e18 + 765e18 + 53e18 + 701e18 + 24e18
        assertEq(LL.tokenX.subtreeBorrowed, 1519e18);   // 765e18 + 53e18 + 701e18
        assertEq(LR.tokenX.subtreeBorrowed, 24e18);
        assertEq(LLR.tokenX.subtreeBorrowed, 754e18);   // 53e18 + 701e18
        assertEq(LLRR.tokenX.subtreeBorrowed, 701e18);  // 701e18

        // subtreeBorrowedY
        assertEq(root.tokenY.subtreeBorrowed, 1143822e6); // 254858e6 + 353e6 + 99763e6 + 8765e6 + 779531e6 + 552e6
        assertEq(L.tokenY.subtreeBorrowed, 888964e6);     // 353e6 + 99763e6 + 8765e6 + 779531e6 + 552e6
        assertEq(LL.tokenY.subtreeBorrowed, 888059e6);    // 99763e6 + 8765e6 + 779531e6
        assertEq(LR.tokenY.subtreeBorrowed, 552e6);
        assertEq(LLR.tokenY.subtreeBorrowed, 788296e6);   // 8765e6 + 779531e6
        assertEq(LLRR.tokenY.subtreeBorrowed, 779531e6);  // 779531e6

        // Step 2) Assign different rates for X & Y
        vm.warp(98273); // T98273
        liqTree.feeRateSnapshotTokenX.add(4541239648278065);  // 7.9% APR as Q192.64 T98273 - T0
        liqTree.feeRateSnapshotTokenY.add(13278814667749784); // 23.1% APR as Q192.64 T98273 - T0

        // Step 3) Apply change that effects the entire tree, to calculate the fees at each node
        // 3.1) addMLiq
        liqTree.addMLiq(LiqRange(3, 7), 2734); // LLRR, LR

        // root
        assertEq(root.tokenX.cummulativeEarnedPerMLiq, 373601278);
        assertEq(root.tokenX.subtreeCummulativeEarnedPerMLiq, 2303115199);
        assertEq(root.tokenY.cummulativeEarnedPerMLiq, 0);
        assertEq(root.tokenY.subtreeCummulativeEarnedPerMLiq, 2);

        // L
        assertEq(L.tokenX.cummulativeEarnedPerMLiq, 757991165);
        assertEq(L.tokenX.subtreeCummulativeEarnedPerMLiq, 1929915382);
        assertEq(L.tokenY.cummulativeEarnedPerMLiq, 0);
        assertEq(L.tokenY.subtreeCummulativeEarnedPerMLiq, 1);

        // LL
        assertEq(LL.tokenX.cummulativeEarnedPerMLiq, 581096415);
        assertEq(LL.tokenX.subtreeCummulativeEarnedPerMLiq, 1153837196);
        assertEq(LL.tokenY.cummulativeEarnedPerMLiq, 0);
        assertEq(LL.tokenY.subtreeCummulativeEarnedPerMLiq, 1);

        // LR
        assertEq(LR.tokenX.cummulativeEarnedPerMLiq, 148929881804);
        assertEq(LR.tokenX.subtreeCummulativeEarnedPerMLiq, 148929881804);
        assertEq(LR.tokenY.cummulativeEarnedPerMLiq, 10);
        assertEq(LR.tokenY.subtreeCummulativeEarnedPerMLiq, 10);

        // LLR
        assertEq(LLR.tokenX.cummulativeEarnedPerMLiq, 42651943);
        assertEq(LLR.tokenX.subtreeCummulativeEarnedPerMLiq, 606784254);
        assertEq(LLR.tokenY.cummulativeEarnedPerMLiq, 0);
        assertEq(LLR.tokenY.subtreeCummulativeEarnedPerMLiq, 1);

        // LLRR
        assertEq(LLRR.tokenX.cummulativeEarnedPerMLiq, 581500584);
        assertEq(LLRR.tokenX.subtreeCummulativeEarnedPerMLiq, 581500584);
        assertEq(LLRR.tokenY.cummulativeEarnedPerMLiq, 1);
        assertEq(LLRR.tokenY.subtreeCummulativeEarnedPerMLiq, 1);

        // mLiq
        assertEq(root.mLiq, 8430);
        assertEq(L.mLiq, 377);
        assertEq(LL.mLiq, 9082734);
        assertEq(LR.mLiq, 3845);
        assertEq(LLR.mLiq, 45346);
        assertEq(LLRR.mLiq, 287637599);

        // subtreeMLiq
        assertEq(root.subtreeMLiq, 324212503); // 8430*16 + 377*8 + 9082734*4 + 3845*4 + 45346*2 + 287637599*1
        assertEq(L.subtreeMLiq, 324077623);    // 377*8 + 9082734*4 + 3845*4 + 45346*2 + 287637599*1
        assertEq(LL.subtreeMLiq, 324059227);   // 9082734*4 + 45346*2 + 287637599*1
        assertEq(LR.subtreeMLiq, 15380);       // 3845*4
        assertEq(LLR.subtreeMLiq, 287728291);  // 45346*2 + 287637599*1
        assertEq(LLRR.subtreeMLiq, 287637599); // 287637599*1

        // 3.2) removeMLiq
        vm.warp(2876298273); // T2876298273
        liqTree.feeRateSnapshotTokenX.add(16463537718422861220174597);   // 978567.9% APR as Q192.64 T2876298273 - T98273
        liqTree.feeRateSnapshotTokenY.add(3715979586694123491881712207); // 220872233.1% APR as Q192.64 T2876298273 - T98273

        liqTree.removeMLiq(LiqRange(3, 7), 2734); // LLRR, LR

        // root
        assertEq(root.tokenX.cummulativeEarnedPerMLiq, 373601278 + 1354374549470516050);         // 1354374549844117328
        assertEq(root.tokenX.subtreeCummulativeEarnedPerMLiq, 2303115199 + 8349223594601778821); // 8349223596904894020
        assertEq(root.tokenY.cummulativeEarnedPerMLiq, 0 + 158351473403);                        // 158351473403
        assertEq(root.tokenY.subtreeCummulativeEarnedPerMLiq, 2 + 710693401861);                 // 710693401863

        // L
        assertEq(L.tokenX.cummulativeEarnedPerMLiq, 757991165 + 2747859799177149412);         // 2747859799935140577
        assertEq(L.tokenX.subtreeCummulativeEarnedPerMLiq, 1929915382 + 6996304358425988634); // 6996304360355904016
        assertEq(L.tokenY.cummulativeEarnedPerMLiq, 0 + 219375887);                           // 219375887
        assertEq(L.tokenY.subtreeCummulativeEarnedPerMLiq, 1 + 552456845955);                 // 552456845956

        // LL
        assertEq(LL.tokenX.cummulativeEarnedPerMLiq, 581096415 + 2106654304105573173);         // 2106654304686669588
        assertEq(LL.tokenX.subtreeCummulativeEarnedPerMLiq, 1153837196 + 4183016846975641372); // 4183016848129478568
        assertEq(LL.tokenY.cummulativeEarnedPerMLiq, 0 + 62008538706);                         // 62008538706
        assertEq(LL.tokenY.subtreeCummulativeEarnedPerMLiq, 1 + 551980602776);                 // 551980602777

        // LR
        assertEq(LR.tokenX.cummulativeEarnedPerMLiq, 148929881804 + 423248577958689008325);        // 423248578107618890129
        assertEq(LR.tokenX.subtreeCummulativeEarnedPerMLiq, 148929881804 + 423248577958689008325); // 423248578107618890129
        assertEq(LR.tokenY.cummulativeEarnedPerMLiq, 10 + 2197219781185);                          // 2197219781195
        assertEq(LR.tokenY.subtreeCummulativeEarnedPerMLiq, 10 + 2197219781185);                   // 2197219781195

        // LLR
        assertEq(LLR.tokenX.cummulativeEarnedPerMLiq, 42651943 + 154626414974589533);          // 154626415017241476
        assertEq(LLR.tokenX.subtreeCummulativeEarnedPerMLiq, 606784254 + 2199779563978122803); // 2199779564584907057
        assertEq(LLR.tokenY.cummulativeEarnedPerMLiq, 0 + 5771781665);                         // 5771781665
        assertEq(LLR.tokenY.subtreeCummulativeEarnedPerMLiq, 1 + 519095539054);                // 519095539055

        // LLRR
        assertEq(LLRR.tokenX.cummulativeEarnedPerMLiq, 581500584 + 2108117905415037748);         // 2108117905996538332
        assertEq(LLRR.tokenX.subtreeCummulativeEarnedPerMLiq, 581500584 + 2108117905415037748);  // 2108117905996538332
        assertEq(LLRR.tokenY.cummulativeEarnedPerMLiq, 1 + 529127613134);                        // 529127613135
        assertEq(LLRR.tokenY.subtreeCummulativeEarnedPerMLiq, 1 + 529127613134);                 // 529127613135
        
        // mLiq
        assertEq(root.mLiq, 8430);
        assertEq(L.mLiq, 377);
        assertEq(LL.mLiq, 9082734);
        assertEq(LR.mLiq, 1111);
        assertEq(LLR.mLiq, 45346);
        assertEq(LLRR.mLiq, 287634865);

        // subtreeMLiq
        assertEq(root.subtreeMLiq, 324198833); // 8430*16 + 377*8 + 9082734*4 + 1111*4 + 45346*2 + 287634865*1
        assertEq(L.subtreeMLiq, 324063953);    // 377*8 + 9082734*4 + 1111*4 + 45346*2 + 287634865*1
        assertEq(LL.subtreeMLiq, 324056493);   // 9082734*4 + 45346*2 + 287634865*1
        assertEq(LR.subtreeMLiq, 4444);        // 1111*4
        assertEq(LLR.subtreeMLiq, 287725557);  // 45346*2 + 287634865*1
        assertEq(LLRR.subtreeMLiq, 287634865); // 287634865*1

        // 3.3) addTLiq
        vm.warp(9214298113); // T2876298273
        liqTree.feeRateSnapshotTokenX.add(11381610389149375791104);   // 307% APR as Q192.64 T9214298113 - T2876298273
        liqTree.feeRateSnapshotTokenY.add(185394198934916215865344);  // 5000.7% APR as Q192.64 T9214298113 - T2876298273

        liqTree.addTLiq(LiqRange(3, 7), 1000, 1000e18, 1000e6); // LLRR, LR

        // root
        assertEq(root.tokenX.cummulativeEarnedPerMLiq, 1354374549844117328 + 936348777891386);         // 1355310898622008714
        assertEq(root.tokenX.subtreeCummulativeEarnedPerMLiq, 8349223596904894020 + 5772247649074341); // 8354995844553968361
        assertEq(root.tokenY.cummulativeEarnedPerMLiq, 158351473403 + 7900657);                        // 158359374060
        assertEq(root.tokenY.subtreeCummulativeEarnedPerMLiq, 710693401863 + 35458749);                // 710728860612

        // L
        assertEq(L.tokenX.cummulativeEarnedPerMLiq, 2747859799935140577 + 1899736810880077);        // 2749759536746020654
        assertEq(L.tokenX.subtreeCummulativeEarnedPerMLiq, 6996304360355904016 + 4836905046539355); // 7001141265402443371
        assertEq(L.tokenY.cummulativeEarnedPerMLiq, 219375887 + 10945);                             // 219386832
        assertEq(L.tokenY.subtreeCummulativeEarnedPerMLiq, 552456845956 + 27563825);                // 552484409781

        // LL
        assertEq(LL.tokenX.cummulativeEarnedPerMLiq, 2106654304686669588 + 1456389336983247);        // 2108110694023652835
        assertEq(LL.tokenX.subtreeCummulativeEarnedPerMLiq, 4183016848129478568 + 2891837127944514); // 4185908685257423082
        assertEq(LL.tokenY.cummulativeEarnedPerMLiq, 62008538706 + 3093698);                         // 62011632404
        assertEq(LL.tokenY.subtreeCummulativeEarnedPerMLiq, 551980602777 + 27539135);                // 552008141912

        // LR
        assertEq(LR.tokenX.cummulativeEarnedPerMLiq, 423248578107618890129 + 373259731104033296);        // 423621837838722923425
        assertEq(LR.tokenX.subtreeCummulativeEarnedPerMLiq, 423248578107618890129 + 373259731104033296); // 423621837838722923425
        assertEq(LR.tokenY.cummulativeEarnedPerMLiq, 2197219781195 + 139839995);                         // 2197359621190
        assertEq(LR.tokenY.subtreeCummulativeEarnedPerMLiq, 2197219781195 + 139839995);                  // 2197359621190

        // LLR
        assertEq(LLR.tokenX.cummulativeEarnedPerMLiq, 154626415017241476 + 106897640711262);          // 154733312657952738
        assertEq(LLR.tokenX.subtreeCummulativeEarnedPerMLiq, 2199779564584907057 + 1520770209363996); // 2201300334794271053
        assertEq(LLR.tokenY.cummulativeEarnedPerMLiq, 5771781665 + 287962);                           // 5772069627
        assertEq(LLR.tokenY.subtreeCummulativeEarnedPerMLiq, 519095539055 + 25898463);                // 519121437518

        // LLRR
        assertEq(LLRR.tokenX.cummulativeEarnedPerMLiq, 2108117905996538332 + 1457402297493569);        // 2109575308294031901
        assertEq(LLRR.tokenX.subtreeCummulativeEarnedPerMLiq, 2108117905996538332 + 1457402297493569); // 2109575308294031901
        assertEq(LLRR.tokenY.cummulativeEarnedPerMLiq, 529127613135 + 26398986);                       // 529154012121
        assertEq(LLRR.tokenY.subtreeCummulativeEarnedPerMLiq, 529127613135 + 26398986);                // 529154012121

        // tLiq
        assertEq(root.tLiq, 4430);
        assertEq(L.tLiq, 77);
        assertEq(LL.tLiq, 82734);
        assertEq(LR.tLiq, 1111);
        assertEq(LLR.tLiq, 5346);
        assertEq(LLRR.tLiq, 7635865);

        // borrowedX
        assertEq(root.tokenX.borrowed, 492e18);
        assertEq(L.tokenX.borrowed, 998e18);
        assertEq(LL.tokenX.borrowed, 765e18);
        assertEq(LR.tokenX.borrowed, 1024e18);
        assertEq(LLR.tokenX.borrowed, 53e18);
        assertEq(LLRR.tokenX.borrowed, 1701e18);

        // borrowedY
        assertEq(root.tokenY.borrowed, 254858e6);
        assertEq(L.tokenY.borrowed, 353e6);
        assertEq(LL.tokenY.borrowed, 99763e6);
        assertEq(LR.tokenY.borrowed, 1552e6);
        assertEq(LLR.tokenY.borrowed, 8765e6);
        assertEq(LLRR.tokenY.borrowed, 780531e6);

        // subtreeBorrowedX
        assertEq(root.tokenX.subtreeBorrowed, 5033e18);  // 492e18 + 998e18 + 765e18 + 53e18 + 701e18 + 24e18
        assertEq(L.tokenX.subtreeBorrowed, 4541e18);     // 998e18 + 765e18 + 53e18 + 701e18 + 24e18
        assertEq(LL.tokenX.subtreeBorrowed, 2519e18);    // 765e18 + 53e18 + 701e18
        assertEq(LR.tokenX.subtreeBorrowed, 1024e18);
        assertEq(LLR.tokenX.subtreeBorrowed, 1754e18);   // 53e18 + 701e18
        assertEq(LLRR.tokenX.subtreeBorrowed, 1701e18);  // 701e18

        // subtreeBorrowedY
        assertEq(root.tokenY.subtreeBorrowed, 1145822e6); // 254858e6 + 353e6 + 99763e6 + 8765e6 + 779531e6 + 552e6
        assertEq(L.tokenY.subtreeBorrowed, 890964e6);     // 353e6 + 99763e6 + 8765e6 + 779531e6 + 552e6
        assertEq(LL.tokenY.subtreeBorrowed, 889059e6);    // 99763e6 + 8765e6 + 779531e6
        assertEq(LR.tokenY.subtreeBorrowed, 1552e6);
        assertEq(LLR.tokenY.subtreeBorrowed, 789296e6);   // 8765e6 + 779531e6
        assertEq(LLRR.tokenY.subtreeBorrowed, 780531e6);  // 779531e6

        // 3.4) removeTLiq
        // 3.3) addTLiq
        vm.warp(32876298273); // T32876298273
        liqTree.feeRateSnapshotTokenX.add(2352954287417905205553); // 17% APR as Q192.64 T32876298273 - T9214298113
        liqTree.feeRateSnapshotTokenY.add(6117681147286553534438); // 44.2% APR as Q192.64 T32876298273 - T9214298113

        liqTree.removeTLiq(LiqRange(3, 7), 1000, 1000e18, 1000e6); // LLRR, LR

        // root
        // A = 0
        // m = 324198833
        //     x: 492e18 * 2352954287417905205553 / 324198833 / 2**64
        // x sub: 5033e18 * 2352954287417905205553 / 324198833 / 2**64
        //     y: 254858e6 * 6117681147286553534438 / 324198833 / 2**64
        // y sub: 1145822e6 * 6117681147286553534438 / 324198833 / 2**64
        assertEq(root.tokenX.cummulativeEarnedPerMLiq, 1355310898622008714 + 193574177654021);
        assertEq(root.tokenX.subtreeCummulativeEarnedPerMLiq, 8354995844553968361 + 1980200886448553);
        assertEq(root.tokenY.cummulativeEarnedPerMLiq, 158359374060 + 260707);
        assertEq(root.tokenY.subtreeCummulativeEarnedPerMLiq, 710728860612 + 1172122);

        // L
        // 998e18 * 2352954287417905205553 / 324131393 / 2**64
        // 4541e18 * 2352954287417905205553 / 324131393 / 2**64
        // 353e6 * 6117681147286553534438 / 324131393 / 2**64
        // 890964e6 * 6117681147286553534438 / 324131393 / 2**64
        assertEq(L.tokenX.cummulativeEarnedPerMLiq, 2749759536746020654 + 392738261220692);
        assertEq(L.tokenX.subtreeCummulativeEarnedPerMLiq, 7001141265402443371 + 1786998441085335);
        assertEq(L.tokenY.cummulativeEarnedPerMLiq, 219386832 + 361);
        assertEq(L.tokenY.subtreeCummulativeEarnedPerMLiq, 552484409781 + 911603);

        // LL
        // 765e18 * 2352954287417905205553 / 324091721 / 2**64
        // 2519e18 * 2352954287417905205553 / 324091721 / 2**64
        // 99763e6 * 6117681147286553534438 / 324091721 / 2**64
        // 889059e6 * 6117681147286553534438 / 324091721 / 2**64
        assertEq(LL.tokenX.cummulativeEarnedPerMLiq, 2108110694023652835 + 301083714644757);
        assertEq(LL.tokenX.subtreeCummulativeEarnedPerMLiq, 4185908685257423082 + 991411604170121);
        assertEq(LL.tokenY.cummulativeEarnedPerMLiq, 62011632404 + 102086);
        assertEq(LL.tokenY.subtreeCummulativeEarnedPerMLiq, 552008141912 + 909766);

        // LR
        // 1024e18 * 2352954287417905205553 / 39672 / 2**64
        // 1024e18 * 2352954287417905205553 / 39672 / 2**64
        // 1552e6 * 6117681147286553534438 / 39672 / 2**64
        // 1552e6 * 6117681147286553534438 / 39672 / 2**64
        assertEq(LR.tokenX.cummulativeEarnedPerMLiq, 423621837838722923425 + 3292377527956539412);
        assertEq(LR.tokenX.subtreeCummulativeEarnedPerMLiq, 423621837838722923425 + 3292377527956539412);
        assertEq(LR.tokenY.cummulativeEarnedPerMLiq, 2197359621190 + 12974025);
        assertEq(LR.tokenY.subtreeCummulativeEarnedPerMLiq, 2197359621190 + 12974025);

        // LLR
        // 53e18 * 2352954287417905205553 / 305908639 / 2**64
        // 1754e18 * 2352954287417905205553 / 305908639 / 2**64
        // 8765e6 * 6117681147286553534438 / 305908639 / 2**64
        // 789296e6 * 6117681147286553534438 / 305908639 / 2**64
        assertEq(LLR.tokenX.cummulativeEarnedPerMLiq, 154733312657952738 + 22099268330799);
        assertEq(LLR.tokenX.subtreeCummulativeEarnedPerMLiq, 2201300334794271053 + 731360691551353);
        assertEq(LLR.tokenY.cummulativeEarnedPerMLiq, 5772069627 + 9502);
        assertEq(LLR.tokenY.subtreeCummulativeEarnedPerMLiq, 519121437518 + 855687);

        // LLRR
        // 1701e18 * 2352954287417905205553 / 296771752 / 2**64
        // 1701e18 * 2352954287417905205553 / 296771752 / 2**64
        // 780531e6 * 6117681147286553534438 / 296771752 / 2**64
        // 780531e6 * 6117681147286553534438 / 296771752 / 2**64
        assertEq(LLRR.tokenX.cummulativeEarnedPerMLiq, 2109575308294031901 + 731097873063750);
        assertEq(LLRR.tokenX.subtreeCummulativeEarnedPerMLiq, 2109575308294031901 + 731097873063750);
        assertEq(LLRR.tokenY.cummulativeEarnedPerMLiq, 529154012121 + 872237);
        assertEq(LLRR.tokenY.subtreeCummulativeEarnedPerMLiq, 529154012121 + 872237);

        // tLiq
        assertEq(root.tLiq, 4430);
        assertEq(L.tLiq, 77);
        assertEq(LL.tLiq, 82734);
        assertEq(LR.tLiq, 111);
        assertEq(LLR.tLiq, 5346);
        assertEq(LLRR.tLiq, 7634865);

        // subtreeMLiq
        assertEq(root.subtreeMLiq, 324198833); // 8430*16 + 377*8 + 9082734*4 + 1111*4 + 45346*2 + 287634865*1
        assertEq(L.subtreeMLiq, 324063953);    // 377*8 + 9082734*4 + 1111*4 + 45346*2 + 287634865*1
        assertEq(LL.subtreeMLiq, 324056493);   // 9082734*4 + 45346*2 + 287634865*1
        assertEq(LR.subtreeMLiq, 4444);        // 1111*4
        assertEq(LLR.subtreeMLiq, 287725557);  // 45346*2 + 287634865*1
        assertEq(LLRR.subtreeMLiq, 287634865); // 287634865*1

        // borrowedX
        assertEq(root.tokenX.borrowed, 492e18);
        assertEq(L.tokenX.borrowed, 998e18);
        assertEq(LL.tokenX.borrowed, 765e18);
        assertEq(LR.tokenX.borrowed, 24e18);
        assertEq(LLR.tokenX.borrowed, 53e18);
        assertEq(LLRR.tokenX.borrowed, 701e18);

        // borrowedY
        assertEq(root.tokenY.borrowed, 254858e6);
        assertEq(L.tokenY.borrowed, 353e6);
        assertEq(LL.tokenY.borrowed, 99763e6);
        assertEq(LR.tokenY.borrowed, 552e6);
        assertEq(LLR.tokenY.borrowed, 8765e6);
        assertEq(LLRR.tokenY.borrowed, 779531e6);

        // subtreeBorrowedX
        assertEq(root.tokenX.subtreeBorrowed, 3033e18); // 492e18 + 998e18 + 765e18 + 53e18 + 701e18 + 24e18
        assertEq(L.tokenX.subtreeBorrowed, 2541e18);    // 998e18 + 765e18 + 53e18 + 701e18 + 24e18
        assertEq(LL.tokenX.subtreeBorrowed, 1519e18);   // 765e18 + 53e18 + 701e18
        assertEq(LR.tokenX.subtreeBorrowed, 24e18);
        assertEq(LLR.tokenX.subtreeBorrowed, 754e18);   // 53e18 + 701e18
        assertEq(LLRR.tokenX.subtreeBorrowed, 701e18);  // 701e18

        // subtreeBorrowedY
        assertEq(root.tokenY.subtreeBorrowed, 1143822e6); // 254858e6 + 353e6 + 99763e6 + 8765e6 + 779531e6 + 552e6
        assertEq(L.tokenY.subtreeBorrowed, 888964e6);     // 353e6 + 99763e6 + 8765e6 + 779531e6 + 552e6
        assertEq(LL.tokenY.subtreeBorrowed, 888059e6);    // 99763e6 + 8765e6 + 779531e6
        assertEq(LR.tokenY.subtreeBorrowed, 552e6);
        assertEq(LLR.tokenY.subtreeBorrowed, 788296e6);   // 8765e6 + 779531e6
        assertEq(LLRR.tokenY.subtreeBorrowed, 779531e6);  // 779531e6
    }


    function testRightLegOnly() public {
        LiqNode storage root = liqTree.nodes[liqTree.root];
        LiqNode storage R = liqTree.nodes[_nodeKey(1, 1, liqTree.offset)];
        LiqNode storage RR = liqTree.nodes[_nodeKey(2, 3, liqTree.offset)];
        LiqNode storage RL = liqTree.nodes[_nodeKey(2, 2, liqTree.offset)];
        LiqNode storage RRL = liqTree.nodes[_nodeKey(3, 6, liqTree.offset)];
        LiqNode storage RRLL = liqTree.nodes[_nodeKey(4, 12, liqTree.offset)];

        // Step 1) Allocate different mLiq + tLiq values for each node
        vm.warp(0); // T0

        liqTree.addInfRangeMLiq(8430);                // root   (INF)
        liqTree.addMLiq(LiqRange(8, 15), 377);        // R     (8-15)
        liqTree.addMLiq(LiqRange(12, 15), 9082734);   // RR   (12-15)
        liqTree.addMLiq(LiqRange(8, 11), 1111);       // RL    (8-11)
        liqTree.addMLiq(LiqRange(12, 13), 45346);     // RRL  (12-13)
        liqTree.addMLiq(LiqRange(12, 12), 287634865); // RRLL    (12)

        liqTree.addInfRangeTLiq(4430, 492e18, 254858e6);              // root
        liqTree.addTLiq(LiqRange(8, 15), 77, 998e18, 353e6);          // R 
        liqTree.addTLiq(LiqRange(12, 15), 82734, 765e18, 99763e6);    // RR
        liqTree.addTLiq(LiqRange(8, 11), 111, 24e18, 552e6);          // RL
        liqTree.addTLiq(LiqRange(12, 13), 5346, 53e18, 8765e6);       // RRL
        liqTree.addTLiq(LiqRange(12, 12), 7634865, 701e18, 779531e6); // RRLL

        // mLiq
        assertEq(root.mLiq, 8430);
        assertEq(R.mLiq, 377);
        assertEq(RR.mLiq, 9082734);
        assertEq(RL.mLiq, 1111);
        assertEq(RRL.mLiq, 45346);
        assertEq(RRLL.mLiq, 287634865);

        // tLiq
        assertEq(root.tLiq, 4430);
        assertEq(R.tLiq, 77);
        assertEq(RR.tLiq, 82734);
        assertEq(RL.tLiq, 111);
        assertEq(RRL.tLiq, 5346);
        assertEq(RRLL.tLiq, 7634865);

        // subtreeMLiq
        assertEq(root.subtreeMLiq, 324198833); // 8430*16 + 377*8 + 9082734*4 + 1111*4 + 45346*2 + 287634865*1
        assertEq(R.subtreeMLiq, 324063953);    // 377*8 + 9082734*4 + 1111*4 + 45346*2 + 287634865*1
        assertEq(RR.subtreeMLiq, 324056493);   // 9082734*4 + 45346*2 + 287634865*1
        assertEq(RL.subtreeMLiq, 4444);        // 1111*4
        assertEq(RRL.subtreeMLiq, 287725557);  // 45346*2 + 287634865*1
        assertEq(RRLL.subtreeMLiq, 287634865); // 287634865*1

        // borrowedX
        assertEq(root.tokenX.borrowed, 492e18);
        assertEq(R.tokenX.borrowed, 998e18);
        assertEq(RR.tokenX.borrowed, 765e18);
        assertEq(RL.tokenX.borrowed, 24e18);
        assertEq(RRL.tokenX.borrowed, 53e18);
        assertEq(RRLL.tokenX.borrowed, 701e18);
 
        // borrowedY
        assertEq(root.tokenY.borrowed, 254858e6);
        assertEq(R.tokenY.borrowed, 353e6);
        assertEq(RR.tokenY.borrowed, 99763e6);
        assertEq(RL.tokenY.borrowed, 552e6);
        assertEq(RRL.tokenY.borrowed, 8765e6);
        assertEq(RRLL.tokenY.borrowed, 779531e6);

        // subtreeBorrowedX
        assertEq(root.tokenX.subtreeBorrowed, 3033e18); // 492e18 + 998e18 + 765e18 + 53e18 + 701e18 + 24e18
        assertEq(R.tokenX.subtreeBorrowed, 2541e18);    // 998e18 + 765e18 + 53e18 + 701e18 + 24e18
        assertEq(RR.tokenX.subtreeBorrowed, 1519e18);   // 765e18 + 53e18 + 701e18
        assertEq(RL.tokenX.subtreeBorrowed, 24e18);
        assertEq(RRL.tokenX.subtreeBorrowed, 754e18);   // 53e18 + 701e18
        assertEq(RRLL.tokenX.subtreeBorrowed, 701e18);  // 701e18

        // subtreeBorrowedY
        assertEq(root.tokenY.subtreeBorrowed, 1143822e6); // 254858e6 + 353e6 + 99763e6 + 8765e6 + 779531e6 + 552e6
        assertEq(R.tokenY.subtreeBorrowed, 888964e6);     // 353e6 + 99763e6 + 8765e6 + 779531e6 + 552e6
        assertEq(RR.tokenY.subtreeBorrowed, 888059e6);    // 99763e6 + 8765e6 + 779531e6
        assertEq(RL.tokenY.subtreeBorrowed, 552e6);
        assertEq(RRL.tokenY.subtreeBorrowed, 788296e6);   // 8765e6 + 779531e6
        assertEq(RRLL.tokenY.subtreeBorrowed, 779531e6);  // 779531e6

        // Step 2) Assign different rates for X & Y
        vm.warp(98273); // T98273
        liqTree.feeRateSnapshotTokenX.add(4541239648278065);  // 7.9% APR as Q192.64 T98273 - T0
        liqTree.feeRateSnapshotTokenY.add(13278814667749784); // 23.1% APR as Q192.64 T98273 - T0

        // Step 3) Apply change that effects the entire tree, to calculate the fees at each node
        // 3.1) addMLiq
        liqTree.addMLiq(LiqRange(8, 12), 2734); // RRLL, RL

        // root
        assertEq(root.tokenX.cummulativeEarnedPerMLiq, 373601278);
        assertEq(root.tokenX.subtreeCummulativeEarnedPerMLiq, 2303115199);
        assertEq(root.tokenY.cummulativeEarnedPerMLiq, 0);
        assertEq(root.tokenY.subtreeCummulativeEarnedPerMLiq, 2);

        // R
        assertEq(R.tokenX.cummulativeEarnedPerMLiq, 757991165);
        assertEq(R.tokenX.subtreeCummulativeEarnedPerMLiq, 1929915382);
        assertEq(R.tokenY.cummulativeEarnedPerMLiq, 0);
        assertEq(R.tokenY.subtreeCummulativeEarnedPerMLiq, 1);

        // RR
        assertEq(RR.tokenX.cummulativeEarnedPerMLiq, 581096415);
        assertEq(RR.tokenX.subtreeCummulativeEarnedPerMLiq, 1153837196);
        assertEq(RR.tokenY.cummulativeEarnedPerMLiq, 0);
        assertEq(RR.tokenY.subtreeCummulativeEarnedPerMLiq, 1);

        // RL
        assertEq(RL.tokenX.cummulativeEarnedPerMLiq, 148929881804);
        assertEq(RL.tokenX.subtreeCummulativeEarnedPerMLiq, 148929881804);
        assertEq(RL.tokenY.cummulativeEarnedPerMLiq, 10);
        assertEq(RL.tokenY.subtreeCummulativeEarnedPerMLiq, 10);

        // RRL
        assertEq(RRL.tokenX.cummulativeEarnedPerMLiq, 42651943);
        assertEq(RRL.tokenX.subtreeCummulativeEarnedPerMLiq, 606784254);
        assertEq(RRL.tokenY.cummulativeEarnedPerMLiq, 0);
        assertEq(RRL.tokenY.subtreeCummulativeEarnedPerMLiq, 1);

        // RRLL
        assertEq(RRLL.tokenX.cummulativeEarnedPerMLiq, 581500584);
        assertEq(RRLL.tokenX.subtreeCummulativeEarnedPerMLiq, 581500584);
        assertEq(RRLL.tokenY.cummulativeEarnedPerMLiq, 1);
        assertEq(RRLL.tokenY.subtreeCummulativeEarnedPerMLiq, 1);

        // mLiq
        assertEq(root.mLiq, 8430);
        assertEq(R.mLiq, 377);
        assertEq(RR.mLiq, 9082734);
        assertEq(RL.mLiq, 3845);
        assertEq(RRL.mLiq, 45346);
        assertEq(RRLL.mLiq, 287637599);

        // subtreeMLiq
        assertEq(root.subtreeMLiq, 324212503); // 8430*16 + 377*8 + 9082734*4 + 3845*4 + 45346*2 + 287637599*1
        assertEq(R.subtreeMLiq, 324077623);    // 377*8 + 9082734*4 + 3845*4 + 45346*2 + 287637599*1
        assertEq(RR.subtreeMLiq, 324059227);   // 9082734*4 + 45346*2 + 287637599*1
        assertEq(RL.subtreeMLiq, 15380);       // 3845*4
        assertEq(RRL.subtreeMLiq, 287728291);  // 45346*2 + 287637599*1
        assertEq(RRLL.subtreeMLiq, 287637599); // 287637599*1

        // 3.2) removeMLiq
        vm.warp(2876298273); // T2876298273
        liqTree.feeRateSnapshotTokenX.add(16463537718422861220174597);   // 978567.9% APR as Q192.64 T2876298273 - T98273
        liqTree.feeRateSnapshotTokenY.add(3715979586694123491881712207); // 220872233.1% APR as Q192.64 T2876298273 - T98273

        liqTree.removeMLiq(LiqRange(8, 12), 2734); // RRLL, RL

        // root
        assertEq(root.tokenX.cummulativeEarnedPerMLiq, 373601278 + 1354374549470516050);         // 1354374549844117328
        assertEq(root.tokenX.subtreeCummulativeEarnedPerMLiq, 2303115199 + 8349223594601778821); // 8349223596904894020
        assertEq(root.tokenY.cummulativeEarnedPerMLiq, 0 + 158351473403);                        // 158351473403
        assertEq(root.tokenY.subtreeCummulativeEarnedPerMLiq, 2 + 710693401861);                 // 710693401863

        // R
        assertEq(R.tokenX.cummulativeEarnedPerMLiq, 757991165 + 2747859799177149412);         // 2747859799935140577
        assertEq(R.tokenX.subtreeCummulativeEarnedPerMLiq, 1929915382 + 6996304358425988634); // 6996304360355904016
        assertEq(R.tokenY.cummulativeEarnedPerMLiq, 0 + 219375887);                           // 219375887
        assertEq(R.tokenY.subtreeCummulativeEarnedPerMLiq, 1 + 552456845955);                 // 552456845956

        // RR
        assertEq(RR.tokenX.cummulativeEarnedPerMLiq, 581096415 + 2106654304105573173);         // 2106654304686669588
        assertEq(RR.tokenX.subtreeCummulativeEarnedPerMLiq, 1153837196 + 4183016846975641372); // 4183016848129478568
        assertEq(RR.tokenY.cummulativeEarnedPerMLiq, 0 + 62008538706);                         // 62008538706
        assertEq(RR.tokenY.subtreeCummulativeEarnedPerMLiq, 1 + 551980602776);                 // 551980602777

        // RL
        assertEq(RL.tokenX.cummulativeEarnedPerMLiq, 148929881804 + 423248577958689008325);        // 423248578107618890129
        assertEq(RL.tokenX.subtreeCummulativeEarnedPerMLiq, 148929881804 + 423248577958689008325); // 423248578107618890129
        assertEq(RL.tokenY.cummulativeEarnedPerMLiq, 10 + 2197219781185);                          // 2197219781195
        assertEq(RL.tokenY.subtreeCummulativeEarnedPerMLiq, 10 + 2197219781185);                   // 2197219781195

        // RRL
        assertEq(RRL.tokenX.cummulativeEarnedPerMLiq, 42651943 + 154626414974589533);          // 154626415017241476
        assertEq(RRL.tokenX.subtreeCummulativeEarnedPerMLiq, 606784254 + 2199779563978122803); // 2199779564584907057
        assertEq(RRL.tokenY.cummulativeEarnedPerMLiq, 0 + 5771781665);                         // 5771781665
        assertEq(RRL.tokenY.subtreeCummulativeEarnedPerMLiq, 1 + 519095539054);                // 519095539055

        // RRLL
        assertEq(RRLL.tokenX.cummulativeEarnedPerMLiq, 581500584 + 2108117905415037748);         // 2108117905996538332
        assertEq(RRLL.tokenX.subtreeCummulativeEarnedPerMLiq, 581500584 + 2108117905415037748);  // 2108117905996538332
        assertEq(RRLL.tokenY.cummulativeEarnedPerMLiq, 1 + 529127613134);                        // 529127613135
        assertEq(RRLL.tokenY.subtreeCummulativeEarnedPerMLiq, 1 + 529127613134);                 // 529127613135
        
        // mLiq
        assertEq(root.mLiq, 8430);
        assertEq(R.mLiq, 377);
        assertEq(RR.mLiq, 9082734);
        assertEq(RL.mLiq, 1111);
        assertEq(RRL.mLiq, 45346);
        assertEq(RRLL.mLiq, 287634865);

        // subtreeMLiq
        assertEq(root.subtreeMLiq, 324198833); // 8430*16 + 377*8 + 9082734*4 + 1111*4 + 45346*2 + 287634865*1
        assertEq(R.subtreeMLiq, 324063953);    // 377*8 + 9082734*4 + 1111*4 + 45346*2 + 287634865*1
        assertEq(RR.subtreeMLiq, 324056493);   // 9082734*4 + 45346*2 + 287634865*1
        assertEq(RL.subtreeMLiq, 4444);        // 1111*4
        assertEq(RRL.subtreeMLiq, 287725557);  // 45346*2 + 287634865*1
        assertEq(RRLL.subtreeMLiq, 287634865); // 287634865*1

        // 3.3) addTLiq
        vm.warp(9214298113); // T2876298273
        liqTree.feeRateSnapshotTokenX.add(11381610389149375791104);   // 307% APR as Q192.64 T9214298113 - T2876298273
        liqTree.feeRateSnapshotTokenY.add(185394198934916215865344);  // 5000.7% APR as Q192.64 T9214298113 - T2876298273

        liqTree.addTLiq(LiqRange(8, 12), 1000, 1000e18, 1000e6); // RRLL, RL

        // root
        assertEq(root.tokenX.cummulativeEarnedPerMLiq, 1354374549844117328 + 936348777891386);         // 1355310898622008714
        assertEq(root.tokenX.subtreeCummulativeEarnedPerMLiq, 8349223596904894020 + 5772247649074341); // 8354995844553968361
        assertEq(root.tokenY.cummulativeEarnedPerMLiq, 158351473403 + 7900657);                        // 158359374060
        assertEq(root.tokenY.subtreeCummulativeEarnedPerMLiq, 710693401863 + 35458749);                // 710728860612

        // R
        assertEq(R.tokenX.cummulativeEarnedPerMLiq, 2747859799935140577 + 1899736810880077);        // 2749759536746020654
        assertEq(R.tokenX.subtreeCummulativeEarnedPerMLiq, 6996304360355904016 + 4836905046539355); // 7001141265402443371
        assertEq(R.tokenY.cummulativeEarnedPerMLiq, 219375887 + 10945);                             // 219386832
        assertEq(R.tokenY.subtreeCummulativeEarnedPerMLiq, 552456845956 + 27563825);                // 552484409781

        // RR
        assertEq(RR.tokenX.cummulativeEarnedPerMLiq, 2106654304686669588 + 1456389336983247);        // 2108110694023652835
        assertEq(RR.tokenX.subtreeCummulativeEarnedPerMLiq, 4183016848129478568 + 2891837127944514); // 4185908685257423082
        assertEq(RR.tokenY.cummulativeEarnedPerMLiq, 62008538706 + 3093698);                         // 62011632404
        assertEq(RR.tokenY.subtreeCummulativeEarnedPerMLiq, 551980602777 + 27539135);                // 552008141912

        // RL
        assertEq(RL.tokenX.cummulativeEarnedPerMLiq, 423248578107618890129 + 373259731104033296);        // 423621837838722923425
        assertEq(RL.tokenX.subtreeCummulativeEarnedPerMLiq, 423248578107618890129 + 373259731104033296); // 423621837838722923425
        assertEq(RL.tokenY.cummulativeEarnedPerMLiq, 2197219781195 + 139839995);                         // 2197359621190
        assertEq(RL.tokenY.subtreeCummulativeEarnedPerMLiq, 2197219781195 + 139839995);                  // 2197359621190

        // RRL
        assertEq(RRL.tokenX.cummulativeEarnedPerMLiq, 154626415017241476 + 106897640711262);          // 154733312657952738
        assertEq(RRL.tokenX.subtreeCummulativeEarnedPerMLiq, 2199779564584907057 + 1520770209363996); // 2201300334794271053
        assertEq(RRL.tokenY.cummulativeEarnedPerMLiq, 5771781665 + 287962);                           // 5772069627
        assertEq(RRL.tokenY.subtreeCummulativeEarnedPerMLiq, 519095539055 + 25898463);                // 519121437518

        // RRLL
        assertEq(RRLL.tokenX.cummulativeEarnedPerMLiq, 2108117905996538332 + 1457402297493569);        // 2109575308294031901
        assertEq(RRLL.tokenX.subtreeCummulativeEarnedPerMLiq, 2108117905996538332 + 1457402297493569); // 2109575308294031901
        assertEq(RRLL.tokenY.cummulativeEarnedPerMLiq, 529127613135 + 26398986);                       // 529154012121
        assertEq(RRLL.tokenY.subtreeCummulativeEarnedPerMLiq, 529127613135 + 26398986);                // 529154012121

        // tLiq
        assertEq(root.tLiq, 4430);
        assertEq(R.tLiq, 77);
        assertEq(RR.tLiq, 82734);
        assertEq(RL.tLiq, 1111);
        assertEq(RRL.tLiq, 5346);
        assertEq(RRLL.tLiq, 7635865);

        // borrowedX
        assertEq(root.tokenX.borrowed, 492e18);
        assertEq(R.tokenX.borrowed, 998e18);
        assertEq(RR.tokenX.borrowed, 765e18);
        assertEq(RL.tokenX.borrowed, 1024e18);
        assertEq(RRL.tokenX.borrowed, 53e18);
        assertEq(RRLL.tokenX.borrowed, 1701e18);

        // borrowedY
        assertEq(root.tokenY.borrowed, 254858e6);
        assertEq(R.tokenY.borrowed, 353e6);
        assertEq(RR.tokenY.borrowed, 99763e6);
        assertEq(RL.tokenY.borrowed, 1552e6);
        assertEq(RRL.tokenY.borrowed, 8765e6);
        assertEq(RRLL.tokenY.borrowed, 780531e6);

        // subtreeBorrowedX
        assertEq(root.tokenX.subtreeBorrowed, 5033e18);  // 492e18 + 998e18 + 765e18 + 53e18 + 701e18 + 24e18
        assertEq(R.tokenX.subtreeBorrowed, 4541e18);     // 998e18 + 765e18 + 53e18 + 701e18 + 24e18
        assertEq(RR.tokenX.subtreeBorrowed, 2519e18);    // 765e18 + 53e18 + 701e18
        assertEq(RL.tokenX.subtreeBorrowed, 1024e18);
        assertEq(RRL.tokenX.subtreeBorrowed, 1754e18);   // 53e18 + 701e18
        assertEq(RRLL.tokenX.subtreeBorrowed, 1701e18);  // 701e18

        // subtreeBorrowedY
        assertEq(root.tokenY.subtreeBorrowed, 1145822e6); // 254858e6 + 353e6 + 99763e6 + 8765e6 + 779531e6 + 552e6
        assertEq(R.tokenY.subtreeBorrowed, 890964e6);     // 353e6 + 99763e6 + 8765e6 + 779531e6 + 552e6
        assertEq(RR.tokenY.subtreeBorrowed, 889059e6);    // 99763e6 + 8765e6 + 779531e6
        assertEq(RL.tokenY.subtreeBorrowed, 1552e6);
        assertEq(RRL.tokenY.subtreeBorrowed, 789296e6);   // 8765e6 + 779531e6
        assertEq(RRLL.tokenY.subtreeBorrowed, 780531e6);  // 779531e6

        // 3.4) removeTLiq
        // 3.3) addTLiq
        vm.warp(32876298273); // T32876298273
        liqTree.feeRateSnapshotTokenX.add(2352954287417905205553); // 17% APR as Q192.64 T32876298273 - T9214298113
        liqTree.feeRateSnapshotTokenY.add(6117681147286553534438); // 44.2% APR as Q192.64 T32876298273 - T9214298113

        liqTree.removeTLiq(LiqRange(8, 12), 1000, 1000e18, 1000e6); // RRLL, RL

        // root
        // A = 0
        // m = 324198833
        //     x: 492e18 * 2352954287417905205553 / 324198833 / 2**64
        // x sub: 5033e18 * 2352954287417905205553 / 324198833 / 2**64
        //     y: 254858e6 * 6117681147286553534438 / 324198833 / 2**64
        // y sub: 1145822e6 * 6117681147286553534438 / 324198833 / 2**64
        assertEq(root.tokenX.cummulativeEarnedPerMLiq, 1355310898622008714 + 193574177654021);
        assertEq(root.tokenX.subtreeCummulativeEarnedPerMLiq, 8354995844553968361 + 1980200886448553);
        assertEq(root.tokenY.cummulativeEarnedPerMLiq, 158359374060 + 260707);
        assertEq(root.tokenY.subtreeCummulativeEarnedPerMLiq, 710728860612 + 1172122);

        // R
        // 998e18 * 2352954287417905205553 / 324131393 / 2**64
        // 4541e18 * 2352954287417905205553 / 324131393 / 2**64
        // 353e6 * 6117681147286553534438 / 324131393 / 2**64
        // 890964e6 * 6117681147286553534438 / 324131393 / 2**64
        assertEq(R.tokenX.cummulativeEarnedPerMLiq, 2749759536746020654 + 392738261220692);
        assertEq(R.tokenX.subtreeCummulativeEarnedPerMLiq, 7001141265402443371 + 1786998441085335);
        assertEq(R.tokenY.cummulativeEarnedPerMLiq, 219386832 + 361);
        assertEq(R.tokenY.subtreeCummulativeEarnedPerMLiq, 552484409781 + 911603);

        // RR
        // 765e18 * 2352954287417905205553 / 324091721 / 2**64
        // 2519e18 * 2352954287417905205553 / 324091721 / 2**64
        // 99763e6 * 6117681147286553534438 / 324091721 / 2**64
        // 889059e6 * 6117681147286553534438 / 324091721 / 2**64
        assertEq(RR.tokenX.cummulativeEarnedPerMLiq, 2108110694023652835 + 301083714644757);
        assertEq(RR.tokenX.subtreeCummulativeEarnedPerMLiq, 4185908685257423082 + 991411604170121);
        assertEq(RR.tokenY.cummulativeEarnedPerMLiq, 62011632404 + 102086);
        assertEq(RR.tokenY.subtreeCummulativeEarnedPerMLiq, 552008141912 + 909766);

        // RL
        // 1024e18 * 2352954287417905205553 / 39672 / 2**64
        // 1024e18 * 2352954287417905205553 / 39672 / 2**64
        // 1552e6 * 6117681147286553534438 / 39672 / 2**64
        // 1552e6 * 6117681147286553534438 / 39672 / 2**64
        assertEq(RL.tokenX.cummulativeEarnedPerMLiq, 423621837838722923425 + 3292377527956539412);
        assertEq(RL.tokenX.subtreeCummulativeEarnedPerMLiq, 423621837838722923425 + 3292377527956539412);
        assertEq(RL.tokenY.cummulativeEarnedPerMLiq, 2197359621190 + 12974025);
        assertEq(RL.tokenY.subtreeCummulativeEarnedPerMLiq, 2197359621190 + 12974025);

        // RRL
        // 53e18 * 2352954287417905205553 / 305908639 / 2**64
        // 1754e18 * 2352954287417905205553 / 305908639 / 2**64
        // 8765e6 * 6117681147286553534438 / 305908639 / 2**64
        // 789296e6 * 6117681147286553534438 / 305908639 / 2**64
        assertEq(RRL.tokenX.cummulativeEarnedPerMLiq, 154733312657952738 + 22099268330799);
        assertEq(RRL.tokenX.subtreeCummulativeEarnedPerMLiq, 2201300334794271053 + 731360691551353);
        assertEq(RRL.tokenY.cummulativeEarnedPerMLiq, 5772069627 + 9502);
        assertEq(RRL.tokenY.subtreeCummulativeEarnedPerMLiq, 519121437518 + 855687);

        // RRLL
        // 1701e18 * 2352954287417905205553 / 296771752 / 2**64
        // 1701e18 * 2352954287417905205553 / 296771752 / 2**64
        // 780531e6 * 6117681147286553534438 / 296771752 / 2**64
        // 780531e6 * 6117681147286553534438 / 296771752 / 2**64
        assertEq(RRLL.tokenX.cummulativeEarnedPerMLiq, 2109575308294031901 + 731097873063750);
        assertEq(RRLL.tokenX.subtreeCummulativeEarnedPerMLiq, 2109575308294031901 + 731097873063750);
        assertEq(RRLL.tokenY.cummulativeEarnedPerMLiq, 529154012121 + 872237);
        assertEq(RRLL.tokenY.subtreeCummulativeEarnedPerMLiq, 529154012121 + 872237);

        // tLiq
        assertEq(root.tLiq, 4430);
        assertEq(R.tLiq, 77);
        assertEq(RR.tLiq, 82734);
        assertEq(RL.tLiq, 111);
        assertEq(RRL.tLiq, 5346);
        assertEq(RRLL.tLiq, 7634865);

        // subtreeMLiq
        assertEq(root.subtreeMLiq, 324198833); // 8430*16 + 377*8 + 9082734*4 + 1111*4 + 45346*2 + 287634865*1
        assertEq(R.subtreeMLiq, 324063953);    // 377*8 + 9082734*4 + 1111*4 + 45346*2 + 287634865*1
        assertEq(RR.subtreeMLiq, 324056493);   // 9082734*4 + 45346*2 + 287634865*1
        assertEq(RL.subtreeMLiq, 4444);        // 1111*4
        assertEq(RRL.subtreeMLiq, 287725557);  // 45346*2 + 287634865*1
        assertEq(RRLL.subtreeMLiq, 287634865); // 287634865*1

        // borrowedX
        assertEq(root.tokenX.borrowed, 492e18);
        assertEq(R.tokenX.borrowed, 998e18);
        assertEq(RR.tokenX.borrowed, 765e18);
        assertEq(RL.tokenX.borrowed, 24e18);
        assertEq(RRL.tokenX.borrowed, 53e18);
        assertEq(RRLL.tokenX.borrowed, 701e18);

        // borrowedY
        assertEq(root.tokenY.borrowed, 254858e6);
        assertEq(R.tokenY.borrowed, 353e6);
        assertEq(RR.tokenY.borrowed, 99763e6);
        assertEq(RL.tokenY.borrowed, 552e6);
        assertEq(RRL.tokenY.borrowed, 8765e6);
        assertEq(RRLL.tokenY.borrowed, 779531e6);

        // subtreeBorrowedX
        assertEq(root.tokenX.subtreeBorrowed, 3033e18); // 492e18 + 998e18 + 765e18 + 53e18 + 701e18 + 24e18
        assertEq(R.tokenX.subtreeBorrowed, 2541e18);    // 998e18 + 765e18 + 53e18 + 701e18 + 24e18
        assertEq(RR.tokenX.subtreeBorrowed, 1519e18);   // 765e18 + 53e18 + 701e18
        assertEq(RL.tokenX.subtreeBorrowed, 24e18);
        assertEq(RRL.tokenX.subtreeBorrowed, 754e18);   // 53e18 + 701e18
        assertEq(RRLL.tokenX.subtreeBorrowed, 701e18);  // 701e18

        // subtreeBorrowedY
        assertEq(root.tokenY.subtreeBorrowed, 1143822e6); // 254858e6 + 353e6 + 99763e6 + 8765e6 + 779531e6 + 552e6
        assertEq(R.tokenY.subtreeBorrowed, 888964e6);     // 353e6 + 99763e6 + 8765e6 + 779531e6 + 552e6
        assertEq(RR.tokenY.subtreeBorrowed, 888059e6);    // 99763e6 + 8765e6 + 779531e6
        assertEq(RL.tokenY.subtreeBorrowed, 552e6);
        assertEq(RRL.tokenY.subtreeBorrowed, 788296e6);   // 8765e6 + 779531e6
        assertEq(RRLL.tokenY.subtreeBorrowed, 779531e6);  // 779531e6
    }

    function testLeftAndRightLegBelowPeak() public {

    }

    function testLeftAndRightLegAtOrHigherThanPeak() public {

    }

    function testLeftAndRightLegSameDistanceToStop() public {

    }

    function testLeftLegLowerThanRightLeg() public {

    }

    function testRightLegLowerThanLeftLeg() public {

    }

    function _nodeKey(uint24 depth, uint24 index, uint24 offset) public returns (LKey) {
        uint24 baseStep = uint24(offset / 2 ** depth);

        uint24 range = offset >> depth;
        uint24 base = offset + baseStep * index;
        return LKeyImpl.makeKey(range, base);
    }
}


contract DenseTreeCodeStructureTest is Test {
    LiqTree public liqTree;
    using LiqTreeImpl for LiqTree;
    using LKeyImpl for LKey;
    using FeeRateSnapshotImpl for FeeRateSnapshot;
    
    function setUp() public {
        // A depth of 4 creates a tree that covers an absolute range of 16 ([0, 15]). 
        // ie. A complete tree matching the ascii documentation. 
        liqTree.init(4);
    }

    // NOTE: Technically all these cases are already covered by leftLegOnly + rightLegOnly
    //       I'm not yet sure if this is necessary or not.
    //       Leaning toward no.

    function testLowOutterIfStatementOnly() public {

    }

    function testLowInnerWhileWithoutInnerIf() public {

    }

    function testLowInnerWhileWithInnerIf() public {

    }

    function testHighOutterIfStatementOnly() public {

    }

    function testHighInnerWhileWithoutInnerIf() public {

    }

    function testHighInnerWhileWithInnerIf() public {

    }

}


contract DenseTreeMathmaticalLimitationsTest is Test {
    LiqTree public liqTree;
    using LiqTreeImpl for LiqTree;
    using LKeyImpl for LKey;
    using FeeRateSnapshotImpl for FeeRateSnapshot;
    
    function setUp() public {
        // A depth of 4 creates a tree that covers an absolute range of 16 ([0, 15]). 
        // ie. A complete tree matching the ascii documentation. 
        liqTree.init(4);
    }

    function testNoFeeAccumulationWithoutRate() public {

    }

    function testFeeAccumulationDoesNotRoundUp() public {

    }

    function testNodeTraversedTwiceWithoutRateUpdateDoesNotAccumulateAdditionalFees() public {

    }

    function testFeeAccumulationDoesNotOverflowUint256() public {

    }

    function testFeeAccumulationAccuracyWithRidiculousRates() public {

    }
}



type LKey is uint48;
// Even if we use 1 as the tick spacing, we still won't have over 2^21 ticks.
uint8 constant MAX_TREE_DEPTH = 21; // We zero index depth, so this is 22 levels.
uint256 constant TWO_POW_64 = 18446744073709551616;

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
    FeeRateSnapshot feeRateSnapshotTokenX;
    FeeRateSnapshot feeRateSnapshotTokenY;
}


library LiqTreeImpl {
    using LKeyImpl for LKey;
    using LiqNodeImpl for LiqNode;
    using LiqTreeIntLib for uint24;
    using FeeRateSnapshotImpl for FeeRateSnapshot;

    /****************************
     * Initialization Functions *
     ****************************/

    function init(LiqTree storage self, uint8 maxDepth) internal {
        require(maxDepth <= MAX_TREE_DEPTH, "MTD");
        // Note, NOT maxDepth - 1. The indexing from 0 or 1 is arbitrary so we go with the cheaper gas.
        uint24 maxRange = uint24(1 << maxDepth);

        self.root = LKeyImpl.makeKey(maxRange, maxRange);
        self.offset = maxRange;
    }

    /***********************************
     * Updated Interface Methods (comment to be deleted after refactor)  *
     ***********************************/

    function addMLiq(LiqTree storage self, LiqRange memory range, uint128 liq) external {
        (LKey low, LKey high, , LKey stopRange) = getKeys(self, range.low, range.high);

        LKey current;
        LiqNode storage node;
        uint24 rangeWidth;

        if (low.isLess(stopRange)) {
            current = low;
            node = self.nodes[current];

            (rangeWidth,) = current.explode();

            _handleFee(self, current, node);

            uint128 totalLiq = rangeWidth * liq; // better name

            node.addMLiq(liq);
            node.subtreeMLiq += totalLiq;

            // Right Propogate M
            (LKey up, LKey left) = current.rightUp();
            LiqNode storage parent = self.nodes[up];

            _handleFee(self, up, parent);

            parent.subtreeMinM = min(self.nodes[left].subtreeMinM, node.subtreeMinM) + parent.mLiq;
            parent.subtreeMLiq += totalLiq;
            (current, node) = (up, parent);

            while (current.isLess(stopRange)) {
                if (current.isLeft()) {
                    current = current.rightSib();
                    node = self.nodes[current];

                    (rangeWidth,) = current.explode();
                    totalLiq = rangeWidth * liq; // better name

                    _handleFee(self, current, node);

                    node.addMLiq(liq);
                    node.subtreeMLiq += totalLiq;
                }

                // In the next section, we need to calculate the subtreeMLiq
                // Because if we flipped over to the adjacent node, the side we flipped from, was not propogated. 

                // Right Propogate M
                (up, left) = current.rightUp();
                (rangeWidth,) = up.explode();
                parent = self.nodes[up];

                _handleFee(self, up, parent);

                parent.subtreeMinM = min(self.nodes[left].subtreeMinM, node.subtreeMinM) + parent.mLiq;
                parent.subtreeMLiq = self.nodes[left].subtreeMLiq + node.subtreeMLiq + parent.mLiq * rangeWidth;
                (current, node) = (up, parent);
            }
        }

        if (high.isLess(stopRange)) {
            current = high;
            node = self.nodes[current];

            (rangeWidth,) = current.explode();
            uint128 totalLiq = rangeWidth * liq; // better name

            _handleFee(self, current, node);

            node.addMLiq(liq);
            node.subtreeMLiq += totalLiq;

            // Left Propogate M
            (LKey up, LKey left) = current.leftUp();
            LiqNode storage parent = self.nodes[up];

            _handleFee(self, up, parent);

            parent.subtreeMinM = min(self.nodes[left].subtreeMinM, node.subtreeMinM) + parent.mLiq;
            parent.subtreeMLiq += totalLiq;
            (current, node) = (up, parent);

            while(current.isLess(stopRange)) {
                if (current.isRight()) {
                    current = current.leftSib();
                    node = self.nodes[current];

                    (rangeWidth,) = current.explode();
                    totalLiq = rangeWidth * liq; // better name

                    _handleFee(self, current, node);

                    node.addMLiq(liq);
                    node.subtreeMLiq += totalLiq;
                }

                // In the next section, we need to calculate the subtreeMLiq
                // Because if we flipped over to the adjacent node, the side we flipped from, was not propogated. 

                // Left Propogate M
                (up, left) = current.leftUp();
                (rangeWidth,) = up.explode();
                parent = self.nodes[up];

                _handleFee(self, up, parent);

                parent.subtreeMinM = min(self.nodes[left].subtreeMinM, node.subtreeMinM) + parent.mLiq;
                parent.subtreeMLiq = self.nodes[left].subtreeMLiq + node.subtreeMLiq + parent.mLiq * rangeWidth;
                (current, node) = (up, parent);
            }
        }

        // Both legs are handled. Touch up everything above where we left off.
        // Current must have already been propogated to.
        // Note. Peak propogating from peak could waste one propogation because sometimes
        // high or low is equal to peak, and we always propogate following an update.
        // So this is just a slight gas saving of one propogate.

        // Peak Propogate M

        node = self.nodes[current];

        // Is less works on root since root has the largest possible base.
        while (current.isLess(self.root)) {
            (LKey up, LKey other) = current.genericUp();
            LiqNode storage parent = self.nodes[up];
            uint128 oldMin = parent.subtreeMinM;

            (rangeWidth,) = up.explode();

            _handleFee(self, up, parent);

            // We're just propogating the min, if our value doesn't change none of the parents need to.
            parent.subtreeMinM = min(self.nodes[other].subtreeMinM, node.subtreeMinM) + parent.mLiq;
            parent.subtreeMLiq = self.nodes[other].subtreeMLiq + node.subtreeMLiq + parent.mLiq * rangeWidth;

            current = up;
            node = parent; // Store this to save one lookup..
        }
    }

    function removeMLiq(LiqTree storage self, LiqRange memory range, uint128 liq) external {
        (LKey low, LKey high, , LKey stopRange) = getKeys(self, range.low, range.high);

        LKey current;
        LiqNode storage node;
        uint24 rangeWidth;

        if (low.isLess(stopRange)) {
            current = low;
            node = self.nodes[current];

            (rangeWidth,) = current.explode();

            _handleFee(self, current, node);

            uint128 totalLiq = rangeWidth * liq; // better name

            node.removeMLiq(liq);
            node.subtreeMLiq -= totalLiq;

            // Right Propogate M
            (LKey up, LKey left) = current.rightUp();
            LiqNode storage parent = self.nodes[up];

            _handleFee(self, up, parent);

            parent.subtreeMinM = min(self.nodes[left].subtreeMinM, node.subtreeMinM) + parent.mLiq;
            parent.subtreeMLiq -= totalLiq;
            (current, node) = (up, parent);

            while (current.isLess(stopRange)) {
                if (current.isLeft()) {
                    current = current.rightSib();
                    node = self.nodes[current];

                    (rangeWidth,) = current.explode();
                    totalLiq = rangeWidth * liq; // better name

                    _handleFee(self, current, node);


                    node.removeMLiq(liq);
                    node.subtreeMLiq -= totalLiq;
                }

                // In the next section, we need to calculate the subtreeMLiq
                // Because if we flipped over to the adjacent node, the side we flipped from, was not propogated. 

                // Right Propogate M
                (up, left) = current.rightUp();
                (rangeWidth,) = up.explode();
                parent = self.nodes[up];

                _handleFee(self, up, parent);

                parent.subtreeMinM = min(self.nodes[left].subtreeMinM, node.subtreeMinM) + parent.mLiq;
                parent.subtreeMLiq = self.nodes[left].subtreeMLiq + node.subtreeMLiq + parent.mLiq * rangeWidth;
                (current, node) = (up, parent);
            }
        }

        if (high.isLess(stopRange)) {
            current = high;
            node = self.nodes[current];

            (rangeWidth,) = current.explode();
            uint128 totalLiq = rangeWidth * liq; // better name

            _handleFee(self, current, node);

            node.removeMLiq(liq);
            node.subtreeMLiq -= totalLiq;

            // Left Propogate M
            (LKey up, LKey left) = current.leftUp();
            LiqNode storage parent = self.nodes[up];

            _handleFee(self, up, parent);

            parent.subtreeMinM = min(self.nodes[left].subtreeMinM, node.subtreeMinM) + parent.mLiq;
            parent.subtreeMLiq -= totalLiq;
            (current, node) = (up, parent);

            while(current.isLess(stopRange)) {
                if (current.isRight()) {
                    current = current.leftSib();
                    node = self.nodes[current];

                    (rangeWidth,) = current.explode();
                    totalLiq = rangeWidth * liq; // better name

                    _handleFee(self, current, node);

                    node.removeMLiq(liq);
                    node.subtreeMLiq -= totalLiq;
                }

                // In the next section, we need to calculate the subtreeMLiq
                // Because if we flipped over to the adjacent node, the side we flipped from, was not propogated. 

                // Left Propogate M
                (up, left) = current.leftUp();
                (rangeWidth,) = up.explode();
                parent = self.nodes[up];

                _handleFee(self, up, parent);

                parent.subtreeMinM = min(self.nodes[left].subtreeMinM, node.subtreeMinM) + parent.mLiq;
                parent.subtreeMLiq = self.nodes[left].subtreeMLiq + node.subtreeMLiq + parent.mLiq * rangeWidth;
                (current, node) = (up, parent);
            }
        }

        // Both legs are handled. Touch up everything above where we left off.
        // Current must have already been propogated to.
        // Note. Peak propogating from peak could waste one propogation because sometimes
        // high or low is equal to peak, and we always propogate following an update.
        // So this is just a slight gas saving of one propogate.

        // Peak Propogate M

        node = self.nodes[current];

        // Is less works on root since root has the largest possible base.
        while (current.isLess(self.root)) {
            (LKey up, LKey other) = current.genericUp();
            LiqNode storage parent = self.nodes[up];
            uint128 oldMin = parent.subtreeMinM;

            (rangeWidth,) = up.explode();

            _handleFee(self, up, parent);

            // We're just propogating the min, if our value doesn't change none of the parents need to.
            parent.subtreeMinM = min(self.nodes[other].subtreeMinM, node.subtreeMinM) + parent.mLiq;
            parent.subtreeMLiq = self.nodes[other].subtreeMLiq + node.subtreeMLiq + parent.mLiq * rangeWidth;

            current = up;
            node = parent; // Store this to save one lookup..
        }
    }

    function addTLiq(LiqTree storage self, LiqRange memory range, uint128 liq, uint256 amountX, uint256 amountY) public {
        (LKey low, LKey high, , LKey stopRange) = getKeys(self, range.low, range.high);

        LKey current;
        LiqNode storage node;

        // Start with the left side of all right nodes.
        if (low.isLess(stopRange)) {
            current = low;
            node = self.nodes[current];

            _handleFee(self, current, node);

            node.addTLiq(liq);

            node.tokenX.borrowed += amountX;
            node.tokenY.borrowed += amountY;
            node.tokenX.subtreeBorrowed += amountX;
            node.tokenY.subtreeBorrowed += amountY;

            // Right Propogate T
            (LKey up, LKey left) = current.rightUp();
            LiqNode storage parent = self.nodes[up];
            _handleFee(self, up, parent);

            parent.subtreeMaxT = max(self.nodes[left].subtreeMaxT, node.subtreeMaxT) + parent.tLiq;
            parent.tokenX.subtreeBorrowed += amountX;
            parent.tokenY.subtreeBorrowed += amountY;
            (current, node) = (up, parent);

            while (current.isLess(stopRange)) {
                // TODO: This can be gas optimized by sharing the left key and node with rightPropogate
                if (current.isLeft()) {
                    current = current.rightSib();
                    node = self.nodes[current];

                    _handleFee(self, current, node);

                    node.addTLiq(liq);

                    node.tokenX.borrowed += amountX;
                    node.tokenY.borrowed += amountY;
                    node.tokenX.subtreeBorrowed += amountX;
                    node.tokenY.subtreeBorrowed += amountY;
                }

                // Right Propogate T
                (up, left) = current.rightUp();
                parent = self.nodes[up];
                _handleFee(self, up, parent);
                parent.subtreeMaxT = max(self.nodes[left].subtreeMaxT, node.subtreeMaxT) + parent.tLiq;
                parent.tokenX.subtreeBorrowed = self.nodes[left].tokenX.subtreeBorrowed + node.tokenX.subtreeBorrowed + parent.tokenX.borrowed;
                parent.tokenY.subtreeBorrowed = self.nodes[left].tokenY.subtreeBorrowed + node.tokenY.subtreeBorrowed + parent.tokenY.borrowed;
                (current, node) = (up, parent);
            }
        }

        if (high.isLess(stopRange)) {
            current = high;
            node = self.nodes[current];

            _handleFee(self, current, node);

            node.addTLiq(liq);

            node.tokenX.borrowed += amountX;
            node.tokenY.borrowed += amountY;
            node.tokenX.subtreeBorrowed += amountX;
            node.tokenY.subtreeBorrowed += amountY;

            // Left Propogate T
            (LKey up, LKey left) = current.leftUp();
            LiqNode storage parent = self.nodes[up];
            _handleFee(self, up, parent);
            parent.subtreeMaxT = max(self.nodes[left].subtreeMaxT, node.subtreeMaxT) + parent.tLiq;
            parent.tokenX.subtreeBorrowed += amountX;
            parent.tokenY.subtreeBorrowed += amountY;
            (current, node) = (up, parent);

            while(current.isLess(stopRange)) {
                // TODO: This can be gas optimized by sharing the right key and node with leftPropogate
                if (current.isRight()) {
                    current = current.leftSib();
                    node = self.nodes[current];

                    _handleFee(self, current, node);

                    node.addTLiq(liq);

                    node.tokenX.borrowed += amountX;
                    node.tokenY.borrowed += amountY;
                    node.tokenX.subtreeBorrowed += amountX;
                    node.tokenY.subtreeBorrowed += amountY;
                }

                // Left Propogate T
                (up, left) = current.leftUp();
                parent = self.nodes[up];
                _handleFee(self, up, parent);
                parent.subtreeMaxT = max(self.nodes[left].subtreeMaxT, node.subtreeMaxT) + parent.tLiq;
                parent.tokenX.subtreeBorrowed = self.nodes[left].tokenX.subtreeBorrowed + node.tokenX.subtreeBorrowed + parent.tokenX.borrowed;
                parent.tokenY.subtreeBorrowed = self.nodes[left].tokenY.subtreeBorrowed + node.tokenY.subtreeBorrowed + parent.tokenY.borrowed;
                (current, node) = (up, parent);
            }
        }

        // Both legs are handled. Touch up everything above.
        // Current has already been propogated to.

        // Peak Propogate T

        node = self.nodes[current];

        while (current.isNeq(self.root)) {
            (LKey up, LKey other) = current.genericUp();
            LiqNode storage parent = self.nodes[up];
            _handleFee(self, up, parent);
            uint128 oldMax = parent.subtreeMaxT;
            parent.subtreeMaxT = max(self.nodes[other].subtreeMaxT, node.subtreeMaxT) + parent.tLiq;
            parent.tokenX.subtreeBorrowed = self.nodes[other].tokenX.subtreeBorrowed + node.tokenX.subtreeBorrowed + parent.tokenX.borrowed;
            parent.tokenY.subtreeBorrowed = self.nodes[other].tokenY.subtreeBorrowed + node.tokenY.subtreeBorrowed + parent.tokenY.borrowed;

            if (node.subtreeMaxT == oldMax) {
            // Don't think we can early return anymore
            //    return;
            }
            current = up;
            node = parent;
        }
    }

    function removeTLiq(LiqTree storage self, LiqRange memory range, uint128 liq, uint256 amountX, uint256 amountY) external {
        (LKey low, LKey high, , LKey stopRange) = getKeys(self, range.low, range.high);

        LKey current;
        LiqNode storage node;

        // Start with the left side of all right nodes.
        if (low.isLess(stopRange)) {
            current = low;
            node = self.nodes[current];

            _handleFee(self, current, node);

            node.removeTLiq(liq);

            node.tokenX.borrowed -= amountX;
            node.tokenY.borrowed -= amountY;
            node.tokenX.subtreeBorrowed -= amountX;
            node.tokenY.subtreeBorrowed -= amountY;

            // Right Propogate T
            (LKey up, LKey left) = current.rightUp();
            LiqNode storage parent = self.nodes[up];
            _handleFee(self, up, parent);

            parent.subtreeMaxT = max(self.nodes[left].subtreeMaxT, node.subtreeMaxT) + parent.tLiq;
            parent.tokenX.subtreeBorrowed -= amountX;
            parent.tokenY.subtreeBorrowed -= amountY;
            (current, node) = (up, parent);

            while (current.isLess(stopRange)) {
                // TODO: This can be gas optimized by sharing the left key and node with rightPropogate
                if (current.isLeft()) {
                    current = current.rightSib();
                    node = self.nodes[current];

                    _handleFee(self, current, node);

                    node.removeTLiq(liq);

                    node.tokenX.borrowed -= amountX;
                    node.tokenY.borrowed -= amountY;
                    node.tokenX.subtreeBorrowed -= amountX;
                    node.tokenY.subtreeBorrowed -= amountY;
                }

                // neeed to calculate because blah blah blah

                // Right Propogate T
                (up, left) = current.rightUp();
                parent = self.nodes[up];
                _handleFee(self, up, parent);
                parent.subtreeMaxT = max(self.nodes[left].subtreeMaxT, node.subtreeMaxT) + parent.tLiq;
                parent.tokenX.subtreeBorrowed = self.nodes[left].tokenX.subtreeBorrowed + node.tokenX.subtreeBorrowed + parent.tokenX.borrowed;
                parent.tokenY.subtreeBorrowed = self.nodes[left].tokenY.subtreeBorrowed + node.tokenY.subtreeBorrowed + parent.tokenY.borrowed;
                (current, node) = (up, parent);
            }
        }

        if (high.isLess(stopRange)) {
            current = high;
            node = self.nodes[current];

            _handleFee(self, current, node);

            node.removeTLiq(liq);

            node.tokenX.borrowed -= amountX;
            node.tokenY.borrowed -= amountY;
            node.tokenX.subtreeBorrowed -= amountX;
            node.tokenY.subtreeBorrowed -= amountY;

            // Left Propogate T
            (LKey up, LKey left) = current.leftUp();
            LiqNode storage parent = self.nodes[up];
            _handleFee(self, up, parent);
            parent.subtreeMaxT = max(self.nodes[left].subtreeMaxT, node.subtreeMaxT) + parent.tLiq;
            parent.tokenX.subtreeBorrowed -= amountX;
            parent.tokenY.subtreeBorrowed -= amountY;
            (current, node) = (up, parent);

            while(current.isLess(stopRange)) {
                // TODO: This can be gas optimized by sharing the right key and node with leftPropogate
                if (current.isRight()) {
                    current = current.leftSib();
                    node = self.nodes[current];

                    _handleFee(self, current, node);

                    node.removeTLiq(liq);

                    node.tokenX.borrowed -= amountX;
                    node.tokenY.borrowed -= amountY;
                    node.tokenX.subtreeBorrowed -= amountX;
                    node.tokenY.subtreeBorrowed -= amountY;
                }

                // neeed to calculate because blah blah blah

                // Left Propogate T
                (up, left) = current.leftUp();
                parent = self.nodes[up];
                _handleFee(self, up, parent);
                parent.subtreeMaxT = max(self.nodes[left].subtreeMaxT, node.subtreeMaxT) + parent.tLiq;
                parent.tokenX.subtreeBorrowed = self.nodes[left].tokenX.subtreeBorrowed + node.tokenX.subtreeBorrowed + parent.tokenX.borrowed;
                parent.tokenY.subtreeBorrowed = self.nodes[left].tokenY.subtreeBorrowed + node.tokenY.subtreeBorrowed + parent.tokenY.borrowed;
                (current, node) = (up, parent);
            }
        }

        // Both legs are handled. Touch up everything above.
        // Current has already been propogated to.

        // Peak Propogate T

        node = self.nodes[current];

        while (current.isNeq(self.root)) {
            (LKey up, LKey other) = current.genericUp();
            LiqNode storage parent = self.nodes[up];
            _handleFee(self, up, parent);
            uint128 oldMax = parent.subtreeMaxT;
            parent.subtreeMaxT = max(self.nodes[other].subtreeMaxT, node.subtreeMaxT) + parent.tLiq;
            parent.tokenX.subtreeBorrowed = self.nodes[other].tokenX.subtreeBorrowed + node.tokenX.subtreeBorrowed + parent.tokenX.borrowed;
            parent.tokenY.subtreeBorrowed = self.nodes[other].tokenY.subtreeBorrowed + node.tokenY.subtreeBorrowed + parent.tokenY.borrowed;

            if (node.subtreeMaxT == oldMax) {
            // Don't think we can early return anymore
            //    return;
            }
            current = up;
            node = parent;
        }
    }

    function addInfRangeMLiq(LiqTree storage self, uint128 liq) external {
        LiqNode storage rootNode = self.nodes[self.root];

        uint256 tokenXRateDiffX64 = self.feeRateSnapshotTokenX.diff(rootNode.tokenX.feeRateSnapshot);
        rootNode.tokenX.feeRateSnapshot = self.feeRateSnapshotTokenX;
        uint256 tokenYRateDiffX64 = self.feeRateSnapshotTokenY.diff(rootNode.tokenY.feeRateSnapshot);
        rootNode.tokenY.feeRateSnapshot = self.feeRateSnapshotTokenY;

        // TODO: determine if we need to check for overflow
        // TODO: round earned fees up
        uint256 totalMLiq = rootNode.subtreeMLiq;
        if (totalMLiq > 0) {
            rootNode.tokenX.cummulativeEarnedPerMLiq += rootNode.tokenX.borrowed * tokenXRateDiffX64 / totalMLiq / TWO_POW_64;
            rootNode.tokenX.subtreeCummulativeEarnedPerMLiq += rootNode.tokenX.subtreeBorrowed * tokenXRateDiffX64 / totalMLiq / TWO_POW_64;

            rootNode.tokenY.cummulativeEarnedPerMLiq += rootNode.tokenY.borrowed * tokenYRateDiffX64 / totalMLiq / TWO_POW_64;
            rootNode.tokenY.subtreeCummulativeEarnedPerMLiq += rootNode.tokenY.subtreeBorrowed * tokenYRateDiffX64 / totalMLiq / TWO_POW_64;
        }

        rootNode.mLiq += liq;
        rootNode.subtreeMinM += liq;
        rootNode.subtreeMLiq += self.offset * liq;
    }

    function removeInfRangeMLiq(LiqTree storage self, uint128 liq) external {
        LiqNode storage rootNode = self.nodes[self.root];

        uint256 tokenXRateDiffX64 = self.feeRateSnapshotTokenX.diff(rootNode.tokenX.feeRateSnapshot);
        rootNode.tokenX.feeRateSnapshot = self.feeRateSnapshotTokenX;
        uint256 tokenYRateDiffX64 = self.feeRateSnapshotTokenY.diff(rootNode.tokenY.feeRateSnapshot);
        rootNode.tokenY.feeRateSnapshot = self.feeRateSnapshotTokenY;

        // TODO: determine if we need to check for overflow
        // TODO: round earned fees up
        uint256 totalMLiq = rootNode.subtreeMLiq;
        if (totalMLiq > 0) {
            rootNode.tokenX.cummulativeEarnedPerMLiq += rootNode.tokenX.borrowed * tokenXRateDiffX64 / totalMLiq / TWO_POW_64;
            rootNode.tokenX.subtreeCummulativeEarnedPerMLiq += rootNode.tokenX.subtreeBorrowed * tokenXRateDiffX64 / totalMLiq / TWO_POW_64;

            rootNode.tokenY.cummulativeEarnedPerMLiq += rootNode.tokenY.borrowed * tokenYRateDiffX64 / totalMLiq / TWO_POW_64;
            rootNode.tokenY.subtreeCummulativeEarnedPerMLiq += rootNode.tokenY.subtreeBorrowed * tokenYRateDiffX64 / totalMLiq / TWO_POW_64;
        }

        rootNode.mLiq -= liq;
        rootNode.subtreeMinM -= liq;
        rootNode.subtreeMLiq -= self.offset * liq;
    }

    function addInfRangeTLiq(LiqTree storage self, uint128 liq, uint256 amountX, uint256 amountY) external {
        LiqNode storage rootNode = self.nodes[self.root];

        // TODO (urlaubaitos) adjust for fee accounting

        uint256 tokenXRateDiffX64 = self.feeRateSnapshotTokenX.diff(rootNode.tokenX.feeRateSnapshot);
        rootNode.tokenX.feeRateSnapshot = self.feeRateSnapshotTokenX;
        uint256 tokenYRateDiffX64 = self.feeRateSnapshotTokenY.diff(rootNode.tokenY.feeRateSnapshot);
        rootNode.tokenY.feeRateSnapshot = self.feeRateSnapshotTokenY;

        // TODO: determine if we need to check for overflow
        // TODO: round earned fees up
        uint256 totalMLiq = rootNode.subtreeMLiq;
        if (totalMLiq > 0) {
            rootNode.tokenX.cummulativeEarnedPerMLiq += rootNode.tokenX.borrowed * tokenXRateDiffX64 / totalMLiq / TWO_POW_64;
            rootNode.tokenX.subtreeCummulativeEarnedPerMLiq += rootNode.tokenX.subtreeBorrowed * tokenXRateDiffX64 / totalMLiq / TWO_POW_64;

            rootNode.tokenY.cummulativeEarnedPerMLiq += rootNode.tokenY.borrowed * tokenYRateDiffX64 / totalMLiq / TWO_POW_64;
            rootNode.tokenY.subtreeCummulativeEarnedPerMLiq += rootNode.tokenY.subtreeBorrowed * tokenYRateDiffX64 / totalMLiq / TWO_POW_64;
        }

        rootNode.tLiq += liq;
        rootNode.subtreeMaxT += liq;
        rootNode.tokenX.borrowed += amountX;
        rootNode.tokenX.subtreeBorrowed += amountX;
        rootNode.tokenY.borrowed += amountY;
        rootNode.tokenY.subtreeBorrowed += amountY;
    }

    function removeInfRangeTLiq(LiqTree storage self, uint128 liq, uint256 amountX, uint256 amountY) external {
        LiqNode storage rootNode = self.nodes[self.root];

        uint256 tokenXRateDiffX64 = self.feeRateSnapshotTokenX.diff(rootNode.tokenX.feeRateSnapshot);
        rootNode.tokenX.feeRateSnapshot = self.feeRateSnapshotTokenX;
        uint256 tokenYRateDiffX64 = self.feeRateSnapshotTokenY.diff(rootNode.tokenY.feeRateSnapshot);
        rootNode.tokenY.feeRateSnapshot = self.feeRateSnapshotTokenY;

        // TODO: determine if we need to check for overflow
        // TODO: round earned fees up
        uint256 totalMLiq = rootNode.subtreeMLiq;
        if (totalMLiq > 0) {
            rootNode.tokenX.cummulativeEarnedPerMLiq += rootNode.tokenX.borrowed * tokenXRateDiffX64 / totalMLiq / TWO_POW_64;
            rootNode.tokenX.subtreeCummulativeEarnedPerMLiq += rootNode.tokenX.subtreeBorrowed * tokenXRateDiffX64 / totalMLiq / TWO_POW_64;

            rootNode.tokenY.cummulativeEarnedPerMLiq += rootNode.tokenY.borrowed * tokenYRateDiffX64 / totalMLiq / TWO_POW_64;
            rootNode.tokenY.subtreeCummulativeEarnedPerMLiq += rootNode.tokenY.subtreeBorrowed * tokenYRateDiffX64 / totalMLiq / TWO_POW_64;
        }

        rootNode.tLiq -= liq;
        rootNode.subtreeMaxT -= liq;
        rootNode.tokenX.borrowed -= amountX;
        rootNode.tokenX.subtreeBorrowed -= amountX;
        rootNode.tokenY.borrowed -= amountY;
        rootNode.tokenY.subtreeBorrowed -= amountY;
    }

    function _handleFee(LiqTree storage self, LKey current, LiqNode storage node) internal {
        (uint24 rangeWidth,) = current.explode();

        uint256 tokenXRateDiffX64 = self.feeRateSnapshotTokenX.diff(node.tokenX.feeRateSnapshot);
        node.tokenX.feeRateSnapshot = self.feeRateSnapshotTokenX;
        uint256 tokenYRateDiffX64 = self.feeRateSnapshotTokenY.diff(node.tokenY.feeRateSnapshot);
        node.tokenY.feeRateSnapshot = self.feeRateSnapshotTokenY;

        // TODO: determine if we need to check for overflow
        uint256 auxLevel = auxilliaryLevelMLiq(self, current);
        uint256 totalMLiq = node.subtreeMLiq + auxLevel * rangeWidth;

        if (totalMLiq > 0) {
            node.tokenX.cummulativeEarnedPerMLiq += node.tokenX.borrowed * tokenXRateDiffX64 / totalMLiq / TWO_POW_64;
            node.tokenX.subtreeCummulativeEarnedPerMLiq += node.tokenX.subtreeBorrowed * tokenXRateDiffX64 / totalMLiq / TWO_POW_64;

            node.tokenY.cummulativeEarnedPerMLiq += node.tokenY.borrowed * tokenYRateDiffX64 / totalMLiq / TWO_POW_64;
            node.tokenY.subtreeCummulativeEarnedPerMLiq += node.tokenY.subtreeBorrowed * tokenYRateDiffX64 / totalMLiq / TWO_POW_64;
        }
    }

    function auxilliaryLevelMLiq(LiqTree storage self, LKey nodeKey) internal view returns (uint256 mLiq) {
        if (nodeKey.isEq(self.root)) {
            return 0;
        }

        (nodeKey, ) = nodeKey.genericUp();
        while (nodeKey.isLess(self.root)) {
            mLiq += self.nodes[nodeKey].mLiq;
            (nodeKey, ) = nodeKey.genericUp();
        }
        mLiq += self.nodes[self.root].mLiq;
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
     ** Wide Query Functions **
     **************************/

    function queryWideMTBounds(LiqTree storage self) internal view returns (uint128 minMaker, uint128 maxTaker) {
        LiqNode storage node = self.nodes[self.root];
        return (node.subtreeMinM, node.subtreeMaxT);
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

        LKey current;
        LiqNode storage node;

        minMaker = type(uint128).max;
        maxTaker = 0;

        // First handle the left side.
        if (low.isLess(stopRange)) {
            // Left side directly writes to minMaker and maxTaker to save stack space.

            current = low;
            node = self.nodes[current];
            minMaker = min(node.subtreeMinM, minMaker);
            maxTaker = max(node.subtreeMaxT, maxTaker);
            (current,) = current.rightUp();

            LKey right;
            while(current.isLess(stopRange)) {
                node = self.nodes[current];
                minMaker += node.mLiq;
                maxTaker += node.tLiq;

                if (current.isLeft()) {
                    (current, right) = current.leftUp();
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
            rightMaker = min(node.subtreeMinM, rightMaker);
            rightTaker = max(node.subtreeMaxT, rightTaker);
            (current,) = current.leftUp();

            LKey left;
            while(current.isLess(stopRange)) {
                node = self.nodes[current];
                rightMaker += node.mLiq;
                rightTaker += node.tLiq;

                if (current.isRight()) {
                    (current, left) = current.rightUp();
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

        // At this moment, we've already added the liq at the node AT the stoprange.
        // To regardless if we're in the two legged case, the one legged case, or the single node case,
        // the node above current is new and incorporates both all nodes in our range breakdown.
        // Thus we just need to start adding.
        // NOTE: it's possible we've already added root in the single node case.
        while (current.isLess(self.root)) {
            (current,) = current.genericUp();
            node = self.nodes[current];
            minMaker += node.mLiq;
            maxTaker += node.tLiq;
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
    ) public view returns (LKey low, LKey high, LKey peak, LKey limitRange) {
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

}


'''