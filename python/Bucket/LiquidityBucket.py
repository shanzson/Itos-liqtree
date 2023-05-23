from dataclasses import dataclass, field
from typing import List

from ILiquidity import *
from LiquidityExceptions import *
from UnsignedDecimal import UnsignedDecimal, UnsignedDecimalIsSignedException


@dataclass
class Snapshot:
    range: LiqRange
    m_liq: UnsignedDecimal = UnsignedDecimal(0)
    t_liq: UnsignedDecimal = UnsignedDecimal(0)
    borrow_x: UnsignedDecimal = UnsignedDecimal(0)
    borrow_y: UnsignedDecimal = UnsignedDecimal(0)
    rate_x: UnsignedDecimal = UnsignedDecimal(0)
    rate_y: UnsignedDecimal = UnsignedDecimal(0)
    acc_x: UnsignedDecimal = UnsignedDecimal(0)
    acc_y: UnsignedDecimal = UnsignedDecimal(0)

    def copy(self):
        return Snapshot(
            range=LiqRange(self.range.low, self.range.high),
            m_liq=self.m_liq,
            t_liq=self.t_liq
        )

    def width(self):
        return UnsignedDecimal(self.range.high - self.range.low + 1)

    def total_m_liq(self):
        return self.m_liq * self.width()


@dataclass
class Bucket:
    snapshots: List[Snapshot] = field(default_factory=list)


class LiquidityBucket(ILiquidity):
    def __init__(self, size, sol_truncation = True):
        self.sol_truncation = sol_truncation

        self._buckets = [Bucket() for n in range(0, size)]

        self.token_x_fee_rate_snapshot: UnsignedDecimal = UnsignedDecimal(0)
        self.token_y_fee_rate_snapshot: UnsignedDecimal = UnsignedDecimal(0)

    def add_m_liq(self, liq_range: LiqRange, liq: UnsignedDecimal) -> None:
        """Adds mLiq to the provided range."""

        for tick in range(liq_range.low, liq_range.high + 1):
            bucket: Bucket = self._buckets[tick]
            snap = next(iter([snap for snap in bucket.snapshots if snap.range.low == liq_range.low and snap.range.high == liq_range.high]), None)

            if snap is None:
                snap = Snapshot(range=liq_range.copy(), m_liq=liq)

            bucket.snapshots.append(snap)

    def remove_m_liq(self, liq_range: LiqRange, liq: UnsignedDecimal) -> None:
        """Removes mLiq from the provided range."""

        for tick in range(liq_range.low, liq_range.high + 1):
            bucket: Bucket = self._buckets[tick]
            snap = next(iter([snap for snap in bucket.snapshots if snap.range.low == liq_range.low and snap.range.high == liq_range.high]), None)

            if snap is None:
                raise LiquidityExceptionRemovingMoreMLiqThanExists()

            try:
                snap.m_liq -= liq
            except UnsignedDecimalIsSignedException:
                raise LiquidityExceptionRemovingMoreMLiqThanExists()

    def add_t_liq(self, liq_range: LiqRange, liq: UnsignedDecimal, amount_x: UnsignedDecimal, amount_y: UnsignedDecimal) -> None:
        """Adds tLiq to the provided range. Borrowing given amounts."""

        for tick in range(liq_range.low, liq_range.high + 1):
            bucket: Bucket = self._buckets[tick]
            snap = next(iter([snap for snap in bucket.snapshots if snap.range.low == liq_range.low and snap.range.high == liq_range.high]), None)

            if snap is None:
                raise LiquidityExceptionTLiqExceedsMLiq()

            try:
                snap.t_liq += liq
                snap.borrow_x += amount_x
                snap.borrow_y += amount_y
            except UnsignedDecimalIsSignedException:
                raise LiquidityExceptionTLiqExceedsMLiq()

    def remove_t_liq(self, liq_range: LiqRange, liq: UnsignedDecimal, amount_x: UnsignedDecimal, amount_y: UnsignedDecimal) -> None:
        """Removes tLiq to the provided range. Repaying given amounts."""

        for tick in range(liq_range.low, liq_range.high + 1):
            bucket: Bucket = self._buckets[tick]
            snap = next(iter([snap for snap in bucket.snapshots if snap.range.low == liq_range.low and snap.range.high == liq_range.high]), None)

            if snap is None:
                raise LiquidityExceptionTLiqExceedsMLiq()

            try:
                snap.t_liq -= liq
                snap.borrow_x -= amount_x
                snap.borrow_y -= amount_y
            except UnsignedDecimalIsSignedException:
                raise LiquidityExceptionTLiqExceedsMLiq()

    def add_wide_m_liq(self, liq: UnsignedDecimal) -> None:
        """Adds mLiq covering the entire data structure."""
        pass

    def remove_wide_m_liq(self, liq: UnsignedDecimal) -> None:
        """Removes mLiq covering the entire data structure."""
        pass

    def add_wide_t_liq(self, liq: UnsignedDecimal, amount_x: UnsignedDecimal, amount_y: UnsignedDecimal) -> None:
        """Adds tLiq covering the entire data structure. Borrowing given amounts."""
        pass

    def remove_wide_t_liq(self, liq: UnsignedDecimal, amount_x: UnsignedDecimal, amount_y: UnsignedDecimal) -> None:
        """Removes tLiq covering the entire data structure. Repaying given amounts."""
        pass

    def query_m_liq(self, liq_range: LiqRange):
        m_liq = UnsignedDecimal(0)
        for tick in range(liq_range.low, liq_range.high + 1):
            for snapshot in self._buckets[tick].snapshots:
                m_liq += snapshot.m_liq / snapshot.width()

        if self.sol_truncation:
            m_liq = int(m_liq)

        return m_liq

    def query_t_liq(self, liq_range: LiqRange):
        t_liq = UnsignedDecimal(0)
        for tick in range(liq_range.low, liq_range.high + 1):
            for snapshot in self._buckets[tick].snapshots:
                t_liq += snapshot.t_liq / snapshot.width()

        if self.sol_truncation:
            t_liq = int(t_liq)

        return t_liq


# @dataclass
# class BorrowSnapshot:
#     range: LiqRange
#     m_liq: UnsignedDecimal = UnsignedDecimal(0)
#     amount_x: UnsignedDecimal = UnsignedDecimal(0)
#     amount_y: UnsignedDecimal = UnsignedDecimal(0)
#     rate_x: UnsignedDecimal = UnsignedDecimal(0)
#     rate_y: UnsignedDecimal = UnsignedDecimal(0)
#     acc_x: UnsignedDecimal = UnsignedDecimal(0)
#     acc_y: UnsignedDecimal = UnsignedDecimal(0)
#
#
# @dataclass
# class Bucket:
#     m_liq: UnsignedDecimal = UnsignedDecimal(0)
#     t_liq: UnsignedDecimal = UnsignedDecimal(0)
#     borrow_snapshots: [BorrowSnapshot] = field(default_factory=list)
#
#
# class LiquidityBucket(ILiquidity):
#     def __init__(self, size, sol_truncation = True):
#         self.sol_truncation = sol_truncation
#
#         self._buckets = [Bucket()] * size
#         self._wide_bucket = Bucket()
#
#         self.token_x_fee_rate_snapshot: UnsignedDecimal = UnsignedDecimal(0)
#         self.token_y_fee_rate_snapshot: UnsignedDecimal = UnsignedDecimal(0)
#
#     def add_m_liq(self, liq_range: LiqRange, liq: UnsignedDecimal) -> None:
#         """Adds mLiq to the provided range."""
#
#         for i in range(liq_range.low, liq_range.high + 1):
#             bucket: Bucket = self._buckets[i]
#             self._handleFees(bucket)
#             bucket.m_liq += liq
#
#     def remove_m_liq(self, liq_range: LiqRange, liq: UnsignedDecimal) -> None:
#         """Removes mLiq from the provided range."""
#
#         for i in range(liq_range.low, liq_range.high + 1):
#             bucket: Bucket = self._buckets[i]
#             self._handleFees(bucket)
#             bucket.m_liq -= liq
#
#     def add_t_liq(self, liq_range: LiqRange, liq: UnsignedDecimal, amount_x: UnsignedDecimal, amount_y: UnsignedDecimal) -> None:
#         """Adds tLiq to the provided range. Borrowing given amounts."""
#
#         total_m_liq: UnsignedDecimal = UnsignedDecimal(0)
#         for i in range(liq_range.low, liq_range.high + 1):
#             total_m_liq += self._buckets[i].m_liq
#         total_m_liq *= (liq_range.high - liq_range.low + 1)  # 11-8+1 = 4
#
#         borrow_snapshot: BorrowSnapshot = BorrowSnapshot(
#             range=liq_range,    # 8-11
#             m_liq=total_m_liq,  # 4444
#             amount_x=amount_x,   # 24e18
#             amount_y=amount_y,    # 7e6
#             rate_x=self.token_x_fee_rate_snapshot,
#             rate_y=self.token_y_fee_rate_snapshot,
#         )
#
#         for i in range(liq_range.low, liq_range.high + 1):
#             bucket: Bucket = self._buckets[i]
#             self._accumulateFees(bucket)
#             bucket.t_liq += liq
#
#             snapshot = next([snap for snap in bucket.borrow_snapshots if snap.range.low == liq_range.low and snap.range.high == liq_range.high])
#             if snapshot is not None:
#                 rate_x = self.token_x_fee_rate_snapshot - snapshot.rate_x
#                 snapshot.acc_x += rate_x * snapshot.token_x / snapshot.m_liq / 2**64
#
#             else:
#                 bucket.borrow_snapshots.append(borrow_snapshot)
#
#     def remove_t_liq(self, liq_range: LiqRange, liq: UnsignedDecimal, amount_x: UnsignedDecimal, amount_y: UnsignedDecimal) -> None:
#         """Removes tLiq to the provided range. Repaying given amounts."""
#
#         for i in range(liq_range.low, liq_range.high + 1):
#             bucket: Bucket = self._buckets[i]
#             self._accumulateFees(bucket)
#             bucket.t_liq -= liq
#             bucket.token_x_borrowed -= amount_x
#             bucket.token_y_borrowed -= amount_y
#
#     def add_wide_m_liq(self, liq: UnsignedDecimal) -> None:
#         """Adds mLiq covering the entire data structure."""
#
#         self._wide_bucket.m_liq += liq
#
#     def remove_wide_m_liq(self, liq: UnsignedDecimal) -> None:
#         """Removes mLiq covering the entire data structure."""
#
#         self._wide_bucket.m_liq -= liq
#
#     def add_wide_t_liq(self, liq: UnsignedDecimal, amount_x: UnsignedDecimal, amount_y: UnsignedDecimal) -> None:
#         """Adds tLiq covering the entire data structure. Borrowing given amounts."""
#
#         self._wide_bucket.m_liq += liq
#         self._wide_bucket.token_x_borrowed += amount_x
#         self._wide_bucket.token_y_borrowed += amount_y
#
#     def remove_wide_t_liq(self, liq: UnsignedDecimal, amount_x: UnsignedDecimal, amount_y: UnsignedDecimal) -> None:
#         """Removes tLiq covering the entire data structure. Repaying given amounts."""
#
#         self._wide_bucket.m_liq -= liq
#         self._wide_bucket.token_x_borrowed -= amount_x
#         self._wide_bucket.token_y_borrowed -= amount_y
#
#     def _accumulate_fees(self, bucket: Bucket):
#         for snapshot in bucket.borrow_snapshots:
#             width = snapshot.range.high - snapshot.range.low
#
#             rate_x = self.token_x_fee_rate_snapshot - snapshot.rate_x
#             snapshot.acc_x += rate_x * snapshot.amount_x / snapshot.m_liq / 2**64 / width
#             snapshot.rate_x = self.token_x_fee_rate_snapshot
#
#             rate_y = self.token_y_fee_rate_snapshot - snapshot.rate_y
#             snapshot.acc_y += rate_y * snapshot.amount_y / snapshot.m_liq / 2**64 / width
#             snapshot.rate_y = self.token_y_fee_rate_snapshot
#
#     def query_mt_bounds(self, liq_range: LiqRange):
#         last_bucket: Bucket = self._buckets[liq_range.high]
#         (min_m, max_t) = (last_bucket.m_liq, last_bucket.t_liq)
#         self._accumulateFees(last_bucket)
#         acc_x = sum([snap.acc_x for snap in last_bucket.borrow_snapshots])
#         acc_y = sum([snap.acc_y for snap in last_bucket.borrow_snapshots])
#
#         for i in range(liq_range.low, liq_range.high):
#             bucket: Bucket = self._buckets[i]
#             min_m = min(bucket.m_liq, min_m)
#             max_t = max(bucket.t_liq, max_t)
#             self._accumulateFees(bucket)
#             acc_x += sum([snap.acc_x for snap in last_bucket.borrow_snapshots])
#             acc_y += sum([snap.acc_y for snap in last_bucket.borrow_snapshots])
#
#         return min_m, max_t, 0, 0
