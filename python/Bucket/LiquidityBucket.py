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
        self._wide_snapshot = Snapshot(range=LiqRange(0, size - 1))
        for bucket in self._buckets:
            bucket.snapshots.append(self._wide_snapshot.copy())

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
            else:
                self._accumulate_fees(snap)

    def remove_m_liq(self, liq_range: LiqRange, liq: UnsignedDecimal) -> None:
        """Removes mLiq from the provided range."""

        for tick in range(liq_range.low, liq_range.high + 1):
            bucket: Bucket = self._buckets[tick]
            snap = next(iter([snap for snap in bucket.snapshots if snap.range.low == liq_range.low and snap.range.high == liq_range.high]), None)

            if snap is None:
                raise LiquidityExceptionRemovingMoreMLiqThanExists()

            self._accumulate_fees(snap)

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

            self._accumulate_fees(snap)

            # check tLiq does not exceed mLiq

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
                # TODO: add more detailed exceptions
                raise Exception()

            self._accumulate_fees(snap)

            # try:
            # TODO: add more detailed exceptions
            snap.t_liq -= liq
            snap.borrow_x -= amount_x
            snap.borrow_y -= amount_y
            # except UnsignedDecimalIsSignedException:
            #     raise LiquidityExceptionTLiqExceedsMLiq()

    def add_wide_m_liq(self, liq: UnsignedDecimal) -> None:
        """Adds mLiq covering the entire data structure."""

        self._accumulate_fees(self._wide_snapshot)
        self._wide_snapshot.m_liq += liq

        range: LiqRange = self._wide_snapshot.range
        for bucket in self._buckets:
            snap = next(iter([snap for snap in bucket.snapshots if snap.range.low == range.low and snap.range.high == range.high]), None)
            self._accumulate_fees(snap)
            snap.m_liq += liq

    def remove_wide_m_liq(self, liq: UnsignedDecimal) -> None:
        """Removes mLiq covering the entire data structure."""

        self._accumulate_fees(self._wide_snapshot)
        self._wide_snapshot.m_liq -= liq

        range: LiqRange = self._wide_snapshot.range
        for bucket in self._buckets:
            snap = next(iter([snap for snap in bucket.snapshots if snap.range.low == range.low and snap.range.high == range.high]), None)
            self._accumulate_fees(snap)
            snap.m_liq -= liq

    def add_wide_t_liq(self, liq: UnsignedDecimal, amount_x: UnsignedDecimal, amount_y: UnsignedDecimal) -> None:
        """Adds tLiq covering the entire data structure. Borrowing given amounts."""

        self._accumulate_fees(self._wide_snapshot)
        self._wide_snapshot.t_liq += liq
        self._wide_snapshot.borrow_x += amount_x
        self._wide_snapshot.borrow_y += amount_y

        range: LiqRange = self._wide_snapshot.range
        for bucket in self._buckets:
            snap = next(iter([snap for snap in bucket.snapshots if snap.range.low == range.low and snap.range.high == range.high]), None)
            self._accumulate_fees(snap)
            # check tLiq does not exceed mLiq
            snap.t_liq += liq
            snap.borrow_x += amount_x
            snap.borrow_y += amount_y

    def remove_wide_t_liq(self, liq: UnsignedDecimal, amount_x: UnsignedDecimal, amount_y: UnsignedDecimal) -> None:
        """Removes tLiq covering the entire data structure. Repaying given amounts."""

        self._accumulate_fees(self._wide_snapshot)
        self._wide_snapshot.t_liq -= liq
        self._wide_snapshot.borrow_x -= amount_x
        self._wide_snapshot.borrow_y -= amount_y

        range: LiqRange = self._wide_snapshot.range
        for bucket in self._buckets:
            snap = next(iter([snap for snap in bucket.snapshots if snap.range.low == range.low and snap.range.high == range.high]), None)
            self._accumulate_fees(snap)
            # check tLiq does not exceed mLiq
            snap.t_liq -= liq
            snap.borrow_x -= amount_x
            snap.borrow_y -= amount_y

    def _accumulate_fees(self, snapshot: Snapshot):
        rate_x = self.token_x_fee_rate_snapshot - snapshot.rate_x
        snapshot.rate_x = self.token_x_fee_rate_snapshot

        rate_y = self.token_y_fee_rate_snapshot - snapshot.rate_y
        snapshot.rate_y = self.token_y_fee_rate_snapshot

        snapshot.acc_x += rate_x * snapshot.borrow_x / snapshot.total_m_liq() / 2**64 / snapshot.width()
        snapshot.acc_y += rate_y * snapshot.borrow_y / snapshot.total_m_liq() / 2**64 / snapshot.width()

        if self.sol_truncation:
            snapshot.acc_x = int(snapshot.acc_x)
            snapshot.acc_y = int(snapshot.acc_y)

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

    def query_wide_m_liq(self):
        return self._wide_snapshot.m_liq

    def query_wide_t_liq(self):
        return self._wide_snapshot.t_liq

    def query_fees_in_range(self, liq_range: LiqRange):
        acc_x = acc_y = UnsignedDecimal(0)

        for tick in range(liq_range.low, liq_range.high + 1):
            for snapshot in self._buckets[tick].snapshots:
                acc_x += snapshot.acc_x
                acc_y += snapshot.acc_y

                if self.sol_truncation:
                    acc_x = int(acc_x)
                    acc_y = int(acc_y)

        return acc_x, acc_y
