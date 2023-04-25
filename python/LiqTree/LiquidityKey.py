from typing import Tuple


class LiquidityKey:

    @staticmethod
    def right_up(key: int) -> Tuple[int, int]:  # up_key, left_key
        range_: int = key >> 24;
        left_raw: int = key ^ range_
        return left_raw + (range_ << 24), left_raw

    @staticmethod
    def left_up(key: int) -> Tuple[int, int]:  # up_key, right_key
        range_ = key >> 24
        return key + (range_ << 24), key ^ range_

    @staticmethod
    def generic_up(key: int) -> Tuple[int, int]:  # up_key, other_key
        range_ = key >> 24
        raw_other: int = range_ ^ key
        return (raw_other if raw_other < key else key) + (range_ << 24), raw_other

    @staticmethod
    def is_right(key: int) -> bool:
        return (key >> 24) & key != 0

    @staticmethod
    def is_left(key: int) -> bool:
        return (key >> 24) & key == 0

    @staticmethod
    def right_sibling(key: int) -> int:
        return key | key >> 24

    @staticmethod
    def left_sibling(key: int) -> int:
        return key & ~(key >> 24)

    # input is raw low, high
    @staticmethod
    def keys(low: int, high: int, offset: int) -> Tuple[int, int, int, int]:  # low, high, peak, stop_range
        return LiquidityKey.range_bounds(low + offset, high + offset)

    # input is raw low, high with offset
    @staticmethod
    def range_bounds(range_low: int, range_high: int) -> Tuple[int, int, int, int]:  # low, high, peak, limit_range
        peak, peak_range = LiquidityKey.lowest_common_ancestor(range_low, range_high)

        low: int = LiquidityKey.low_key(range_low)
        high: int = LiquidityKey.high_key(range_high)

        is_low_below: bool = low < peak_range
        is_high_below: bool = high < peak_range

        # Case on whether left and right are below the peak range or not.
        if is_low_below and is_high_below:
            # The simple case where we can just walk up both legs.
            # Each individual leg will stop at the children of the peak,
            # so our limit range is one below peak range.
            return low, high, peak, peak_range >> 1
        elif is_low_below and not is_high_below:
            # We only have the left leg to worry about.
            # So our limit range will be at the peak, because we want to include
            # the right child of the peak.
            return low, high, peak, peak_range
        elif not is_low_below and is_high_below:
            # Just the right leg. So include the left child of peak.
            return low, high, peak, peak_range
        else:
            # Both are at or higher than the peak! So our range breakdown is just the peak.
            # You can prove that one of the keys must be the peak itself trivially.
            # Thus we don't modify our keys and just stop at one above the peak.
            return low, high, peak, peak_range << 1

    @staticmethod
    def low_key(low: int) -> int:
        return LiquidityKey.lsb(low) << 24 | low

    @staticmethod
    def high_key(high: int) -> int:
        high += 1
        range_: int = LiquidityKey.lsb(high)
        return range_ << 24 | high ^ range_

    @staticmethod
    def lowest_common_ancestor(low: int, high: int) -> Tuple[int, int]:  # (peak, peak_range)
        # Same implementation as Solidity

        diff_mask: int = 0x00FFFFFF
        diff_bits: int = low ^ high

        if diff_bits & 0xFFF000 == 0:
            diff_mask >>= 12
            diff_bits <<= 12

        if diff_bits & 0xFC0000 == 0:
            diff_mask >>= 6
            diff_bits <<= 6

        if diff_bits & 0xE00000 == 0:
            diff_mask >>= 3
            diff_bits <<= 3

        if diff_bits & 0xC00000 == 0:
            diff_mask >>= 2
            diff_bits <<= 2

        if diff_bits & 0x800000 == 0:
            diff_mask >>= 1

        common_mask: int = ~diff_mask
        base: int = common_mask & low
        range_: int = LiquidityKey.lsb(common_mask)

        return range_ << 24 | base, range_ << 24

    @staticmethod
    def lsb(x: int) -> int:
        return x & (~x + 1)
