import decimal
from decimal import Decimal, getcontext


class UnsignedDecimalIsSignedException(Exception):
    pass


# By default Decimal has a limit of 28 places for precision.
# Which is too small for our calculations.
# Setting precision to the max allowed,
# decimal.MAX_PREC (999999999999999999 on a 64-bit machine) causes out of memory errors.
# Because we're limited to 256 bits in Solidity (well the liquidity tree anyway),
# we can safely use the max precision for a 256 bit number
# without worrying about precision errors later. That being 78.
getcontext().prec = 78


class UnsignedDecimal(Decimal):
    def __new__(cls, value, context=None):
        self = Decimal.__new__(cls, value, context)
        if self < Decimal(0):
            raise UnsignedDecimalIsSignedException()
        return self

    def __add__(self, other):
        result = Decimal.__add__(self, other)
        if result < Decimal(0):
            raise UnsignedDecimalIsSignedException()
        return result

    def __radd__(self, other):
        result = Decimal.__radd__(self, other)
        if result < Decimal(0):
            raise UnsignedDecimalIsSignedException()
        return result

    def __sub__(self, other):
        result = Decimal.__sub__(self, other)
        if result < Decimal(0):
            raise UnsignedDecimalIsSignedException()
        return result

    def __rsub__(self, other):
        result = Decimal.__rsub__(self, other)
        if result < Decimal(0):
            raise UnsignedDecimalIsSignedException()
        return result

    def __mul__(self, other):
        result = Decimal.__mul__(self, other)
        if result < Decimal(0):
            raise UnsignedDecimalIsSignedException()
        return result

    def __rmul__(self, other):
        result = Decimal.__rmul__(self, other)
        if result < Decimal(0):
            raise UnsignedDecimalIsSignedException()
        return result

    def __truediv__(self, other):
        result = Decimal.__truediv__(self, other)
        if result < Decimal(0):
            raise UnsignedDecimalIsSignedException()
        return result

    def __rtruediv__(self, other):
        result = Decimal.__rtruediv__(self, other)
        if result < Decimal(0):
            raise UnsignedDecimalIsSignedException()
        return result