from decimal import Decimal


class UnsignedDecimalIsSignedException(Exception):
    pass


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