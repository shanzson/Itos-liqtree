// SPDX-License-Identifier: BSL-1.1
pragma solidity ^0.8.18;

import { console2 } from "forge-std/console2.sol";
import { Test } from "forge-std/Test.sol";

import { LiqTree, LiqTreeImpl, LiqRange, LKey, LKeyImpl, LiqNode, FeeSnap } from "src/Tree.sol";

contract TreeErrorTest is Test {
    using LiqTreeImpl for LiqTree;
    using LKeyImpl for LKey;

    LiqTree public liqTree;
    FeeSnap public fees;

    function setUp() public {
        // A depth of 5 creates a tree that covers an absolute range of 16 ([0, 15];);.
        // ie. A complete tree matching the ascii documentation.
        liqTree.init(5);
    }

    // Helper for creating a LiqRange from the given indices. The tree offsets the input values
    // because it expects them to be zero centered. For testing, it is more convenient to interpret
    // the indices from 0 to the max range. This we undo the offset here.
    function range(int24 low, int24 high) public view returns (LiqRange memory lr) {
        lr.low = low - int24(liqTree.width / 2);
        lr.high = high - int24(liqTree.width / 2);
    }

    // addMLiq errors ----------------------------------------------------------------------

    function testRevertIfAddMLiqWithFlippedLowAndHigh() public {
        vm.expectRevert(); // RLH
        liqTree.addMLiq(range(4, 2), 199, fees);
    }

    function testRevertIfAddMLiqWithRangeLargerThanMaxAllowed() public {
        vm.expectRevert(); // RHO
        liqTree.addMLiq(range(8, 1000), 100, fees);
    }

    function testRevertIfAddMLiqWithRangeMatchingWideRange() public {
        vm.expectRevert();
        liqTree.addMLiq(range(0, 15), 100, fees);
    }

    // removeMLiq errors ----------------------------------------------------------------------

    function testRevertIfRemoveMLiqWhereZeroHasBeenAllocated() public {
        vm.expectRevert();
        liqTree.removeMLiq(range(1, 2), 100, fees);
    }

    function testRevertIfRemoveMLiqLargerThanWhatExistsInThatRange() public {
        liqTree.addMLiq(range(1, 5), 100, fees);
        vm.expectRevert();
        liqTree.removeMLiq(range(1, 5), 101, fees);
    }

    // function testRevertIfRemoveMLiqThatViolatsAllowedTakerUtilization() public {

    // }

    // do we care?
    // function testRevertIfRemoveMLiqOfZero() public {
    //     liqTree.addMLiq(range(1, 2), 10);
    //     vm.expectRevert();
    //     liqTree.removeMLiq(range(1, 2), 0);
    // }

    function testRevertIfRemoveMLiqWithFlippedLowAndHigh() public {
        vm.expectRevert();
        liqTree.removeMLiq(range(6, 2), 50, fees);
    }

    function testRevertIfRemoveMLiqWithRangeLargerThanMaxAllowed() public {
        vm.expectRevert();
        liqTree.removeMLiq(range(1, 2000), 50, fees);
    }

    function testRevertIfRemoveMLiqWithRangeMatchingWideRange() public {
        liqTree.addWideRangeMLiq(200, fees);
        vm.expectRevert();
        liqTree.removeMLiq(range(0, 15), 100, fees);
    }

    // addTLiq errors ----------------------------------------------------------------------

    function testRevertIfAddTLiqWithFlippedLowAndHigh() public {
        liqTree.addMLiq(range(8, 10), 100, fees);
        vm.expectRevert();
        liqTree.addTLiq(range(10, 8), 10, fees, 10, 10);
    }

    function testRevertIfAddTLiqWithRangeLargerThanMaxAllowed() public {
        vm.expectRevert();
        liqTree.addTLiq(range(1, 10000), 10, fees, 10, 10);
    }

    function testRevertIfAddTLiqWithRangeMatchingWideRange() public {
        liqTree.addWideRangeMLiq(200, fees);
        vm.expectRevert();
        liqTree.addTLiq(range(0, 15), 100, fees, 10, 10);
    }

    // removeTLiq errors ----------------------------------------------------------------------

    function testRevertIfRemoveTLiqWhereZeroHasBeenAllocated() public {
        liqTree.addMLiq(range(1, 2), 100, fees);
        vm.expectRevert();
        liqTree.removeTLiq(range(1, 2), 10, fees, 10, 10);
    }

    function testRevertIfRemoveTLiqLargerThanWhatExistsInThatRange() public {
        liqTree.addMLiq(range(1, 2), 100, fees);
        liqTree.addTLiq(range(1, 2), 10, fees, 1, 1);
        vm.expectRevert();
        liqTree.removeTLiq(range(1, 2), 12, fees, 1, 1);
    }

    function testRevertIfRemoveTLiqWithRepaymentOfXTokenThatExceedsBorrow() public {
        liqTree.addMLiq(range(2, 7), 100, fees);
        liqTree.addTLiq(range(2, 7), 10, fees, 10, 10);
        vm.expectRevert();
        liqTree.removeTLiq(range(2, 7), 2, fees, 12, 5);
    }

    function testRevertIfRemoveTLiqWithRepaymentOfYTokenThatExceedsBorrow() public {
        liqTree.addMLiq(range(2, 7), 100, fees);
        liqTree.addTLiq(range(2, 7), 10, fees, 10, 10);
        vm.expectRevert();
        liqTree.removeTLiq(range(2, 7), 2, fees, 5, 12);
    }

    function testRevertIfRemoveTLiqWithFlippedLowAndHigh() public {
        liqTree.addMLiq(range(2, 7), 100, fees);
        liqTree.addTLiq(range(2, 7), 10, fees, 10, 10);
        vm.expectRevert();
        liqTree.removeTLiq(range(7, 2), 2, fees, 5, 5);
    }

    function testRevertIfRemoveTLiqWithRangeLargerThanMaxAllowed() public {
        liqTree.addMLiq(range(2, 7), 100, fees);
        liqTree.addTLiq(range(2, 7), 10, fees, 10, 10);
        vm.expectRevert();
        liqTree.removeTLiq(range(2, 700), 2, fees, 5, 5);
    }

    function testRevertIfRemoveTLiqWithRangeMatchingWideRange() public {
        liqTree.addWideRangeMLiq(200, fees);
        liqTree.addWideRangeTLiq(100, fees, 10, 10);
        vm.expectRevert();
        liqTree.removeTLiq(range(0, 15), 20, fees, 2, 2);
    }

    // removeWideRangeMLiq errors ----------------------------------------------------------------------

    function testRevertIfRemoveWideRangeMLiqWhereZeroHasBeenAllocated() public {
        vm.expectRevert();
        liqTree.removeWideRangeMLiq(1000, fees);
    }

    function testRevertIfRemoveWideRangeMLiqLargerThanWhatExistsInThatRange() public {
        liqTree.addWideRangeMLiq(100, fees);
        vm.expectRevert();
        liqTree.removeWideRangeMLiq(1000, fees);
    }
}
