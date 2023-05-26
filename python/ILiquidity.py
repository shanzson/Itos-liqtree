import abc
from dataclasses import dataclass

from UnsignedDecimal import UnsignedDecimal


TWO_POW_SIXTY_FOUR: UnsignedDecimal = UnsignedDecimal(2**64)


@dataclass
class LiqRange:
    low: int
    high: int

    def copy(self):
        return LiqRange(self.low, self.high)


class ILiquidity(metaclass=abc.ABCMeta):

    @abc.abstractmethod
    def add_m_liq(self, liq_range: LiqRange, liq: UnsignedDecimal) -> (UnsignedDecimal, UnsignedDecimal):
        """Adds mLiq to the provided range. Liquidity provided is per tick. Returns the min mLiq, and accumulated fee rates per mLiq for each token."""
        raise NotImplementedError

    @abc.abstractmethod
    def remove_m_liq(self, liq_range: LiqRange, liq: UnsignedDecimal) -> (UnsignedDecimal, UnsignedDecimal, UnsignedDecimal):
        """Removes mLiq from the provided range. Liquidity provided is per tick. Returns the min mLiq, and accumulated fee rates per mLiq for each token."""
        raise NotImplementedError

    @abc.abstractmethod
    def add_t_liq(self, liq_range: LiqRange, liq: UnsignedDecimal, amount_x: UnsignedDecimal, amount_y: UnsignedDecimal) -> UnsignedDecimal:
        """Adds tLiq to the provided range. Liquidity provided is per tick. Borrowing given amounts. Returns the max tLiq."""
        raise NotImplementedError

    @abc.abstractmethod
    def remove_t_liq(self, liq_range: LiqRange, liq: UnsignedDecimal, amount_x: UnsignedDecimal, amount_y: UnsignedDecimal) -> UnsignedDecimal:
        """Removes tLiq to the provided range. Liquidity provided is per tick. Repaying given amounts. Returns the max tLiq."""
        raise NotImplementedError

    @abc.abstractmethod
    def add_wide_m_liq(self, liq: UnsignedDecimal) -> (UnsignedDecimal, UnsignedDecimal, UnsignedDecimal):
        """Adds mLiq over the wide range. Returns the min mLiq, and accumulated fee rates per mLiq for each token."""
        raise NotImplementedError

    @abc.abstractmethod
    def remove_wide_m_liq(self, liq: UnsignedDecimal) -> (UnsignedDecimal, UnsignedDecimal, UnsignedDecimal):
        """Removes mLiq over the wide range. Returns the min mLiq, and accumulated fee rates per mLiq for each token."""
        raise NotImplementedError

    @abc.abstractmethod
    def add_wide_t_liq(self, liq: UnsignedDecimal, amount_x: UnsignedDecimal, amount_y: UnsignedDecimal) -> UnsignedDecimal:
        """Adds tLiq over the wide range. Borrowing given amounts. Returns the max tLiq."""
        raise NotImplementedError

    @abc.abstractmethod
    def remove_wide_t_liq(self, liq: UnsignedDecimal, amount_x: UnsignedDecimal, amount_y: UnsignedDecimal) -> UnsignedDecimal:
        """Removes tLiq over the wide range. Repaying given amounts. Returns the max tLiq."""
        raise NotImplementedError

    @abc.abstractmethod
    def query_min_m_liq_max_t_liq(self, liq_range: LiqRange) -> (UnsignedDecimal, UnsignedDecimal):
        """Returns the min mLiq, max tLiq over the wide range. Returned liquidity is per tick."""
        raise NotImplementedError

    @abc.abstractmethod
    def query_wide_min_m_liq_max_t_liq(self) -> (UnsignedDecimal, UnsignedDecimal):
        """Returns the min mLiq, max tLiq over the wide range. Returned liquidity is for all tick."""
        raise NotImplementedError

    @abc.abstractmethod
    def query_accumulated_fee_rates(self) -> (UnsignedDecimal, UnsignedDecimal):
        """Returns the accumulated fee rates per mLiq for each token over the provided range."""
        raise NotImplementedError

    @abc.abstractmethod
    def query_wide_accumulated_fee_rates_per_m_liq(self) -> (UnsignedDecimal, UnsignedDecimal):
        """Returns the accumulated fee rates per mLiq for each token over the wide range."""
        raise NotImplementedError
    