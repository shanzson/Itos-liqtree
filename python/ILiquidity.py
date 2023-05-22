import abc
from dataclasses import dataclass

from UnsignedDecimal import UnsignedDecimal


@dataclass
class LiqRange:
    low: int
    high: int

    def copy(self):
        return LiqRange(self.low, self.high)


class ILiquidity(metaclass=abc.ABCMeta):

    @abc.abstractmethod
    def add_m_liq(self, liq_range: LiqRange, liq: UnsignedDecimal) -> None:
        """Adds mLiq to the provided range."""
        raise NotImplementedError

    @abc.abstractmethod
    def remove_m_liq(self, liq_range: LiqRange, liq: UnsignedDecimal) -> None:
        """Removes mLiq from the provided range."""
        raise NotImplementedError

    @abc.abstractmethod
    def add_t_liq(self, liq_range: LiqRange, liq: UnsignedDecimal, amount_x: UnsignedDecimal, amount_y: UnsignedDecimal) -> None:
        """Adds tLiq to the provided range. Borrowing given amounts."""
        raise NotImplementedError

    @abc.abstractmethod
    def remove_t_liq(self, liq_range: LiqRange, liq: UnsignedDecimal, amount_x: UnsignedDecimal, amount_y: UnsignedDecimal) -> None:
        """Removes tLiq to the provided range. Repaying given amounts."""
        raise NotImplementedError

    @abc.abstractmethod
    def add_wide_m_liq(self, liq: UnsignedDecimal) -> None:
        """Adds mLiq covering the entire data structure."""
        raise NotImplementedError

    @abc.abstractmethod
    def remove_wide_m_liq(self, liq: UnsignedDecimal) -> None:
        """Removes mLiq covering the entire data structure."""
        raise NotImplementedError

    @abc.abstractmethod
    def add_wide_t_liq(self, liq: UnsignedDecimal, amount_x: UnsignedDecimal, amount_y: UnsignedDecimal) -> None:
        """Adds tLiq covering the entire data structure. Borrowing given amounts."""
        raise NotImplementedError

    @abc.abstractmethod
    def remove_wide_t_liq(self, liq: UnsignedDecimal, amount_x: UnsignedDecimal, amount_y: UnsignedDecimal) -> None:
        """Removes tLiq covering the entire data structure. Repaying given amounts."""
        raise NotImplementedError
