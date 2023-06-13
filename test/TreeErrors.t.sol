// SPDX-License-Identifier: BSL-1.1
pragma solidity ^0.8.18;

import { Test } from "forge-std/Test.sol";

import { LiqTree, LiqTreeImpl, LiqRange, LKey, LKeyImpl, LiqNode } from "src/Tree.sol";

import { ONE_HUNDRED_PERCENT_UTILIZATION, EIGHTY_PERCENT_UTILIZATION } from "./UtilizationConstants.sol";

contract TreeErrorTest is Test {
    LiqTree public liqTree;
    using LiqTreeImpl for LiqTree;
    using LKeyImpl for LKey;
    
    function setUp() public {
        // A depth of 4 creates a tree that covers an absolute range of 16 ([0, 15];);. 
        // ie. A complete tree matching the ascii documentation. 
        liqTree.init(4);
    }

    // addMLiq errors ----------------------------------------------------------------------

    // do we care?
    // function testRevertIfAddMLiqOfZero() public {
    //     vm.expectRevert();
    //     liqTree.addMLiq(LiqRange(1, 9), 0);
    // }

    function testRevertIfAddMLiqWithFlippedLowAndHigh() public {
        vm.expectRevert(); // RLH
        liqTree.addMLiq(LiqRange(4, 2), 199);
    }

    function testRevertIfAddMLiqWithRangeLargerThanMaxAllowed() public {
        vm.expectRevert(); // RHO
        liqTree.addMLiq(LiqRange(8, 1000), 100);
    }

    function testRevertIfAddMLiqWithRangeMatchingWideRange() public {
        vm.expectRevert();
        liqTree.addMLiq(LiqRange(0, 15), 100);
    }

    // removeMLiq errors ----------------------------------------------------------------------

    function testRevertIfRemoveMLiqWhereZeroHasBeenAllocated() public {
        vm.expectRevert();
        liqTree.removeMLiq(LiqRange(1, 2), 100);
    }

    function testRevertIfRemoveMLiqLargerThanWhatExistsInThatRange() public {
        liqTree.addMLiq(LiqRange(1, 5), 100);
        vm.expectRevert();
        liqTree.removeMLiq(LiqRange(1, 5), 101);
    }

    // function testRevertIfRemoveMLiqThatViolatsAllowedTakerUtilization() public {

    // }

    // do we care?
    // function testRevertIfRemoveMLiqOfZero() public {
    //     liqTree.addMLiq(LiqRange(1, 2), 10);
    //     vm.expectRevert();
    //     liqTree.removeMLiq(LiqRange(1, 2), 0);
    // }

    function testRevertIfRemoveMLiqWithFlippedLowAndHigh() public {
        vm.expectRevert();
        liqTree.removeMLiq(LiqRange(6, 2), 50);
    }

    function testRevertIfRemoveMLiqWithRangeLargerThanMaxAllowed() public {
        vm.expectRevert();
        liqTree.removeMLiq(LiqRange(1, 2000), 50);
    }

    function testRevertIfRemoveMLiqWithRangeMatchingWideRange() public {
        liqTree.addWideRangeMLiq(200);
        vm.expectRevert();
        liqTree.removeMLiq(LiqRange(0, 15), 100);
    }

    // addTLiq errors ----------------------------------------------------------------------

    function testRevertIfAddTLiqWithoutMLiq() public {
        vm.expectRevert();
        liqTree.addTLiq(LiqRange(1, 2), 50, 20, 10, EIGHTY_PERCENT_UTILIZATION);
    }

    // left leg first checkpoint 

    function testRevertIfAddTLiqThatExceedsTakerUtilizationAlongLeftLegAtFirstCheckpoint() public {
        // (1-7) | (1-1), (2-3), (4-7)
        // target (1-1)
        liqTree.addMLiq(LiqRange(1, 7), 100);
        liqTree.addTLiq(LiqRange(1, 1), 70, 1, 1, EIGHTY_PERCENT_UTILIZATION);
        vm.expectRevert();
        liqTree.addTLiq(LiqRange(1, 7), 11, 20, 10, EIGHTY_PERCENT_UTILIZATION);
    }

    function testAddTLiqThatExactlyMatchesTheTakerUtilizationAlongLeftLegAtFirstCheckpoint() public {
        // (1-7) | (1-1), (2-3), (4-7)
        // target (1-1)        
        liqTree.addMLiq(LiqRange(1, 7), 100);
        liqTree.addTLiq(LiqRange(1, 1), 70, 1, 1, EIGHTY_PERCENT_UTILIZATION);
        liqTree.addTLiq(LiqRange(1, 7), 10, 20, 10, EIGHTY_PERCENT_UTILIZATION);
    }

    function testRevertIfAddTLiqThatExceedsMLiqRegardlessOfTakerUtilizationAlongLeftLegAtFirstCheckpoint() public {
        // (1-7) | (1-1), (2-3), (4-7)
        // target (1-1)
        liqTree.addMLiq(LiqRange(1, 7), 100);
        liqTree.addTLiq(LiqRange(1, 1), 70, 1, 1, EIGHTY_PERCENT_UTILIZATION);
        vm.expectRevert();
        liqTree.addTLiq(LiqRange(1, 7), 40, 20, 10, 100 << 128); // 100x
    }

    // left leg second (and last) checkpoint 

    function testRevertIfAddTLiqThatExceedsTakerUtilizationAlongLeftLegAtSecondAndLastCheckpoint() public {
        // (1-7) | (1-1), (2-3), (4-7)
        // target (2-3)        
        liqTree.addMLiq(LiqRange(1, 7), 100);
        liqTree.addTLiq(LiqRange(2, 3), 70, 1, 1, EIGHTY_PERCENT_UTILIZATION);
        vm.expectRevert();
        liqTree.addTLiq(LiqRange(1, 7), 11, 20, 10, EIGHTY_PERCENT_UTILIZATION);
    }

    function testAddTLiqThatExactlyMatchesTheTakerUtilizationAlongLeftLegAtSecondAndLastCheckpoint() public {
        // (1-7) | (1-1), (2-3), (4-7)
        // target (2-3)        
        liqTree.addMLiq(LiqRange(1, 7), 100);
        liqTree.addTLiq(LiqRange(2, 3), 70, 1, 1, EIGHTY_PERCENT_UTILIZATION);
        liqTree.addTLiq(LiqRange(1, 7), 10, 20, 10, EIGHTY_PERCENT_UTILIZATION);
    }

    function testRevertIfAddTLiqThatExceedsMLiqRegardlessOfTakerUtilizationAlongLeftLegAtSecondAndLastCheckpoint() public {
        // (1-7) | (1-1), (2-3), (4-7)
        // target (2-3)
        liqTree.addMLiq(LiqRange(1, 7), 100);
        liqTree.addTLiq(LiqRange(2, 3), 70, 1, 1, EIGHTY_PERCENT_UTILIZATION);
        vm.expectRevert();
        liqTree.addTLiq(LiqRange(1, 7), 40, 20, 10, 100 << 128); // 100x
    }

    // right leg first checkpoint 

    function testRevertIfAddTLiqThatExceedsTakerUtilizationAlongRightLegAtFirstCheckpoint() public {
        // (8-12) | (12-12), (12-13), (12-15), (8-11), (8-15)
        // target (12-12)
        liqTree.addMLiq(LiqRange(8, 12), 100);
        liqTree.addTLiq(LiqRange(12, 12), 70, 1, 1, EIGHTY_PERCENT_UTILIZATION);
        vm.expectRevert();
        liqTree.addTLiq(LiqRange(8, 12), 11, 20, 10, EIGHTY_PERCENT_UTILIZATION);
    }

    function testAddTLiqThatExactlyMatchesTheTakerUtilizationAlongRightLegAtFirstCheckpoint() public {
        // (8-12) | (12-12), (12-13), (12-15), (8-11), (8-15)
        // target (12-12)
        liqTree.addMLiq(LiqRange(8, 12), 100);
        liqTree.addTLiq(LiqRange(12, 12), 70, 1, 1, EIGHTY_PERCENT_UTILIZATION);
        liqTree.addTLiq(LiqRange(8, 12), 10, 20, 10, EIGHTY_PERCENT_UTILIZATION);
    }

    function testRevertIfAddTLiqThatExceedsMLiqRegardlessOfTakerUtilizationAlongRightLegAtFirstCheckpoint() public {
        // (8-12) | (12-12), (12-13), (12-15), (8-11), (8-15)
        // target (12-12)        
        liqTree.addMLiq(LiqRange(8, 12), 100);
        liqTree.addTLiq(LiqRange(12, 12), 70, 1, 1, EIGHTY_PERCENT_UTILIZATION);
        vm.expectRevert();
        liqTree.addTLiq(LiqRange(8, 12), 31, 20, 10, 100 << 128); // 100x
    }

    // right leg second (and last) checkpoint 

    function testRevertIfAddTLiqThatExceedsTakerUtilizationAlongRightLegAtSecondAndLastCheckpoint() public {
        // (8-12) | (12-12), (12-13), (12-15), (8-11), (8-15)
        // target (8-11)
        liqTree.addMLiq(LiqRange(8, 12), 100);
        liqTree.addTLiq(LiqRange(8, 11), 70, 1, 1, EIGHTY_PERCENT_UTILIZATION);
        vm.expectRevert();
        liqTree.addTLiq(LiqRange(8, 12), 11, 20, 10, EIGHTY_PERCENT_UTILIZATION);
    }

    function testAddTLiqThatExactlyMatchesTheTakerUtilizationAlongRightLegAtSecondAndLastCheckpoint() public {
        // (8-12) | (12-12), (12-13), (12-15), (8-11), (8-15)
        // target (8-11)
        liqTree.addMLiq(LiqRange(8, 12), 100);
        liqTree.addTLiq(LiqRange(8, 11), 70, 1, 1, EIGHTY_PERCENT_UTILIZATION);
        liqTree.addTLiq(LiqRange(8, 12), 10, 20, 10, EIGHTY_PERCENT_UTILIZATION);
    }

    function testRevertIfAddTLiqThatExceedsMLiqRegardlessOfTakerUtilizationAlongRightLegAtSecondAndLastCheckpoint() public {
        // (8-12) | (12-12), (12-13), (12-15), (8-11), (8-15)
        // target (8-11)
        liqTree.addMLiq(LiqRange(8, 12), 100);
        liqTree.addTLiq(LiqRange(8, 11), 70, 1, 1, EIGHTY_PERCENT_UTILIZATION);
        vm.expectRevert();
        liqTree.addTLiq(LiqRange(8, 12), 31, 20, 10, 100 << 128); // 100x
    }

    // do we care?
    // function testRevertIfAddTLiqOfZero() public {
    //     liqTree.addMLiq(LiqRange(1, 2), 100);
    //     vm.expectRevert();
    //     liqTree.removeTLiq(LiqRange(1, 2), 10, 10, 10, EIGHTY_PERCENT_UTILIZATION);
    // }

    function testRevertIfAddTLiqWithFlippedLowAndHigh() public {
        liqTree.addMLiq(LiqRange(8, 10), 100);
        vm.expectRevert();
        liqTree.addTLiq(LiqRange(10, 8), 10, 10, 10, EIGHTY_PERCENT_UTILIZATION);
    }

    function testRevertIfAddTLiqWithRangeLargerThanMaxAllowed() public {
        vm.expectRevert();
        liqTree.addTLiq(LiqRange(1, 10000), 10, 10, 10, EIGHTY_PERCENT_UTILIZATION);
    }

    function testRevertIfAddTLiqWithRangeMatchingWideRange() public {
        liqTree.addWideRangeMLiq(200);
        vm.expectRevert();
        liqTree.addTLiq(LiqRange(0, 15), 100, 10, 10, EIGHTY_PERCENT_UTILIZATION);
    }

    // removeTLiq errors ----------------------------------------------------------------------

    function testRevertIfRemoveTLiqWhereZeroHasBeenAllocated() public {
        liqTree.addMLiq(LiqRange(1, 2), 100);
        vm.expectRevert();
        liqTree.removeTLiq(LiqRange(1, 2), 10, 10, 10);
    }

    function testRevertIfRemoveTLiqLargerThanWhatExistsInThatRange() public {
        liqTree.addMLiq(LiqRange(1, 2), 100);
        liqTree.addTLiq(LiqRange(1, 2), 10, 1, 1, EIGHTY_PERCENT_UTILIZATION);
        vm.expectRevert();
        liqTree.removeTLiq(LiqRange(1, 2), 12, 1, 1);
    }

    function testRevertIfRemoveTLiqWithRepaymentOfXTokenThatExceedsBorrow() public {
        liqTree.addMLiq(LiqRange(2, 7), 100);
        liqTree.addTLiq(LiqRange(2, 7), 10, 10, 10, EIGHTY_PERCENT_UTILIZATION);
        vm.expectRevert();
        liqTree.removeTLiq(LiqRange(2, 7), 2, 12, 5);
    }

    function testRevertIfRemoveTLiqWithRepaymentOfYTokenThatExceedsBorrow() public {
        liqTree.addMLiq(LiqRange(2, 7), 100);
        liqTree.addTLiq(LiqRange(2, 7), 10, 10, 10, EIGHTY_PERCENT_UTILIZATION);
        vm.expectRevert();
        liqTree.removeTLiq(LiqRange(2, 7), 2, 5, 12);
    }

    // do we care?
    // function testRevertIfRemoveTLiqOfZero() public {
    //     liqTree.addMLiq(LiqRange(1, 2), 10);
    //     vm.expectRevert();
    //     liqTree.removeMLiq(LiqRange(1, 2), 0);
    // }

    function testRevertIfRemoveTLiqWithFlippedLowAndHigh() public {
        liqTree.addMLiq(LiqRange(2, 7), 100);
        liqTree.addTLiq(LiqRange(2, 7), 10, 10, 10, EIGHTY_PERCENT_UTILIZATION);
        vm.expectRevert();
        liqTree.removeTLiq(LiqRange(7, 2), 2, 5, 5);
    }

    function testRevertIfRemoveTLiqWithRangeLargerThanMaxAllowed() public {
        liqTree.addMLiq(LiqRange(2, 7), 100);
        liqTree.addTLiq(LiqRange(2, 7), 10, 10, 10, EIGHTY_PERCENT_UTILIZATION);
        vm.expectRevert();
        liqTree.removeTLiq(LiqRange(2, 700), 2, 5, 5);
    }

    function testRevertIfRemoveTLiqWithRangeMatchingWideRange() public {
        liqTree.addWideRangeMLiq(200);
        liqTree.addWideRangeTLiq(100, 10, 10, ONE_HUNDRED_PERCENT_UTILIZATION);
        vm.expectRevert();
        liqTree.removeTLiq(LiqRange(0, 15), 20, 2, 2);
    }

    // removeWideRangeMLiq errors ----------------------------------------------------------------------

    function testRevertIfRemoveWideRangeMLiqWhereZeroHasBeenAllocated() public {
        vm.expectRevert();
        liqTree.removeWideRangeMLiq(1000);
    }

    function testRevertIfRemoveWideRangeMLiqLargerThanWhatExistsInThatRange() public {
        liqTree.addWideRangeMLiq(100);
        vm.expectRevert();
        liqTree.removeWideRangeMLiq(1000);
    }

    // addWideRangeTLiq errors ----------------------------------------------------------------------

    function testRevertIfAddWideRangeTLiqWithoutMLiq() public {
        vm.expectRevert();
        liqTree.addWideRangeTLiq(20, 1, 1, ONE_HUNDRED_PERCENT_UTILIZATION);
    }

    function testRevertIfAddWideRangeTLiqThatExceedsTakerUtilization() public {
        liqTree.addWideRangeMLiq(100);
        vm.expectRevert();
        liqTree.addWideRangeTLiq(81, 1, 1, EIGHTY_PERCENT_UTILIZATION);
    }

    function testAddWideRangeTLiqThatExactlyMatchesTheTakerUtilization() public {
        liqTree.addWideRangeMLiq(100);
        liqTree.addWideRangeTLiq(80, 1, 1, EIGHTY_PERCENT_UTILIZATION);
    }

    function testRevertIfAddWideRangeTLiqExceedsMLiqRegardlessOfTakerUtilization() public {
        liqTree.addWideRangeMLiq(100);
        vm.expectRevert();
        liqTree.addWideRangeTLiq(200, 1, 1, 100 << 128); // 100x
    }

    // do we care?
    // function testRevertIfAddWideRangeTLiqOfZero() public {

    // }

    // removeWideRangeTLiq errors ----------------------------------------------------------------------

    function testRevertIfRemoveWideRangeTLiqWhereZeroHasBeenAllocated() public {
        vm.expectRevert();
        liqTree.removeWideRangeTLiq(100, 10, 10);
    }

    function testRevertIfRemoveWideRangeTLiqLargerThanWhatExistsInWideRange() public {
        liqTree.addWideRangeMLiq(1000);
        liqTree.addWideRangeTLiq(100, 10, 10, ONE_HUNDRED_PERCENT_UTILIZATION);
        vm.expectRevert();
        liqTree.removeWideRangeTLiq(200, 2, 2);
    }

    function testRevertIfRemoveWideRangeTLiqWithRepaymentOfTokenXThatExceedsBorrow() public {
        liqTree.addWideRangeMLiq(1000);
        liqTree.addWideRangeTLiq(100, 10, 10, ONE_HUNDRED_PERCENT_UTILIZATION);
        vm.expectRevert();
        liqTree.removeWideRangeTLiq(50, 12, 2);
    }

    function testRevertIfRemoveWideRangeTLiqWithRepaymentOfTokenYThatExceedsBorrow() public {
        liqTree.addWideRangeMLiq(1000);
        liqTree.addWideRangeTLiq(100, 10, 10, ONE_HUNDRED_PERCENT_UTILIZATION);
        vm.expectRevert();
        liqTree.removeWideRangeTLiq(50, 2, 12);
    }

    // do we care?
    // function testRevertIfRemoveWideRangeTLiqOfZero() public {

    // }

}