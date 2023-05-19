from dataclasses import dataclass

from ILiquidity import ILiquidity, LiqRange
from UnsignedDecimal import UnsignedDecimal


@dataclass
class Bucket:
    m_liq: UnsignedDecimal = UnsignedDecimal(0)
    t_liq: UnsignedDecimal = UnsignedDecimal(0)

    token_x_borrowed: UnsignedDecimal = UnsignedDecimal(0)
    token_x_fee_rate_snapshot: UnsignedDecimal = UnsignedDecimal(0)
    token_x_cumulative_earned_per_m_liq: UnsignedDecimal = UnsignedDecimal(0)

    token_y_borrowed: UnsignedDecimal = UnsignedDecimal(0)
    token_y_fee_rate_snapshot: UnsignedDecimal = UnsignedDecimal(0)
    token_y_cumulative_earned_per_m_liq: UnsignedDecimal = UnsignedDecimal(0)


class LiquidityBucket(ILiquidity):
    def __init__(self, size, sol_truncation = True):
        self.sol_truncation = sol_truncation

        self._buckets = [Bucket()] * size
        self._wide_bucket = Bucket()

        self.token_x_fee_rate_snapshot: UnsignedDecimal = UnsignedDecimal(0)
        self.token_y_fee_rate_snapshot: UnsignedDecimal = UnsignedDecimal(0)

    def add_m_liq(self, liq_range: LiqRange, liq: UnsignedDecimal) -> None:
        """Adds mLiq to the provided range."""

        for i in range(liq_range.low, liq_range.high + 1):
            bucket: Bucket = self._buckets[i]
            self._handleFees(bucket)
            bucket.m_liq += liq

    def remove_m_liq(self, liq_range: LiqRange, liq: UnsignedDecimal) -> None:
        """Removes mLiq from the provided range."""

        for i in range(liq_range.low, liq_range.high + 1):
            bucket: Bucket = self._buckets[i]
            self._handleFees(bucket)
            bucket.m_liq -= liq

    def add_t_liq(self, liq_range: LiqRange, liq: UnsignedDecimal, amount_x: UnsignedDecimal, amount_y: UnsignedDecimal) -> None:
        """Adds tLiq to the provided range. Borrowing given amounts."""

        for i in range(liq_range.low, liq_range.high + 1):
            bucket: Bucket = self._buckets[i]
            self._handleFees(bucket)
            bucket.t_liq += liq
            bucket.token_x_borrowed += amount_x
            bucket.token_y_borrowed += amount_y

    def remove_t_liq(self, liq_range: LiqRange, liq: UnsignedDecimal, amount_x: UnsignedDecimal, amount_y: UnsignedDecimal) -> None:
        """Removes tLiq to the provided range. Repaying given amounts."""

        for i in range(liq_range.low, liq_range.high + 1):
            bucket: Bucket = self._buckets[i]
            self._handleFees(bucket)
            bucket.t_liq -= liq
            bucket.token_x_borrowed -= amount_x
            bucket.token_y_borrowed -= amount_y

    def add_inf_range_m_liq(self, liq: UnsignedDecimal) -> None:
        """Adds mLiq covering the entire data structure."""

        self._wide_bucket.m_liq += liq

    def remove_inf_range_m_liq(self, liq: UnsignedDecimal) -> None:
        """Removes mLiq covering the entire data structure."""

        self._wide_bucket.m_liq -= liq

    def add_inf_range_t_liq(self, liq: UnsignedDecimal, amount_x: UnsignedDecimal, amount_y: UnsignedDecimal) -> None:
        """Adds tLiq covering the entire data structure. Borrowing given amounts."""

        self._wide_bucket.m_liq += liq
        self._wide_bucket.token_x_borrowed += amount_x
        self._wide_bucket.token_y_borrowed += amount_y

    def remove_inf_range_t_liq(self, liq: UnsignedDecimal, amount_x: UnsignedDecimal, amount_y: UnsignedDecimal) -> None:
        """Removes tLiq covering the entire data structure. Repaying given amounts."""

        self._wide_bucket.m_liq -= liq
        self._wide_bucket.token_x_borrowed -= amount_x
        self._wide_bucket.token_y_borrowed -= amount_y

    def _handleFees(self, bucket: Bucket) -> None:
        rate_x: UnsignedDecimal = self.token_x_fee_rate_snapshot - bucket.token_x_fee_rate_snapshot
        bucket.token_x_fee_rate_snapshot = self.token_x_fee_rate_snapshot
        rate_y: UnsignedDecimal = self.token_y_fee_rate_snapshot - bucket.token_y_fee_rate_snapshot
        bucket.token_y_fee_rate_snapshot = self.token_y_fee_rate_snapshot

        if bucket.m_liq == UnsignedDecimal(0):
            return

        bucket.token_x_cumulative_earned_per_m_liq += rate_x * bucket.token_x_borrowed / bucket.m_liq / 2**64
        bucket.token_y_cumulative_earned_per_m_liq += rate_y * bucket.token_y_borrowed / bucket.m_liq / 2**64

        if self.sol_truncation:
            bucket.token_x_cumulative_earned_per_m_liq = UnsignedDecimal(int(bucket.token_x_cumulative_earned_per_m_liq))
            bucket.token_y_cumulative_earned_per_m_liq = UnsignedDecimal(int(bucket.token_y_cumulative_earned_per_m_liq))
            bucket.token_y_cumulative_earned_per_m_liq = UnsignedDecimal(int(bucket.token_y_cumulative_earned_per_m_liq))

    def query_mt_bounds(self, liq_range: LiqRange):
        last_bucket: Bucket = self._buckets[liq_range.high]
        (min_m, max_t) = (last_bucket.m_liq, last_bucket.t_liq)

        for i in range(liq_range.low, liq_range.high):
            bucket: Bucket = self._buckets[i]
            min_m = min(bucket.m_liq, min_m)
            max_t = max(bucket.t_liq, max_t)

        return min_m, max_t
