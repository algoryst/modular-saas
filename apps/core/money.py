"""Money as Decimal plus an ISO 4217 currency. The only place amounts are rounded."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal
from typing import Final, Self

# Minor-unit digits per supported currency. Add a currency here before using it.
MINOR_UNITS: Final[Mapping[str, int]] = {"EUR": 2, "GBP": 2, "USD": 2}


class UnknownCurrencyError(ValueError):
    pass


class CurrencyMismatchError(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class Money:
    amount: Decimal
    currency: str

    def __post_init__(self) -> None:
        amount: object = self.amount
        if not isinstance(amount, Decimal):
            raise TypeError(f"Money amount must be Decimal, not {type(amount)}")
        if not self.amount.is_finite():
            raise ValueError("Money amount must be finite")
        if self.currency not in MINOR_UNITS:
            raise UnknownCurrencyError(self.currency)

    @classmethod
    def zero(cls, currency: str) -> Self:
        return cls(Decimal(0), currency)

    def round(self) -> Money:
        """Round half up (away from zero) to the currency's minor unit."""
        exponent = Decimal(1).scaleb(-MINOR_UNITS[self.currency])
        return Money(
            self.amount.quantize(exponent, rounding=ROUND_HALF_UP), self.currency
        )

    def _same_currency(self, other: Money) -> None:
        if other.currency != self.currency:
            raise CurrencyMismatchError(f"{self.currency} vs {other.currency}")

    def __add__(self, other: Money) -> Money:
        if not isinstance(other, Money):
            return NotImplemented
        self._same_currency(other)
        return Money(self.amount + other.amount, self.currency)

    def __sub__(self, other: Money) -> Money:
        if not isinstance(other, Money):
            return NotImplemented
        self._same_currency(other)
        return Money(self.amount - other.amount, self.currency)

    def __neg__(self) -> Money:
        return Money(-self.amount, self.currency)

    def __mul__(self, factor: Decimal | int) -> Money:
        if isinstance(factor, bool) or not isinstance(factor, Decimal | int):
            return NotImplemented
        return Money(self.amount * factor, self.currency)

    __rmul__ = __mul__

    def __lt__(self, other: Money) -> bool:
        self._same_currency(other)
        return self.amount < other.amount

    def __le__(self, other: Money) -> bool:
        self._same_currency(other)
        return self.amount <= other.amount

    def __gt__(self, other: Money) -> bool:
        self._same_currency(other)
        return self.amount > other.amount

    def __ge__(self, other: Money) -> bool:
        self._same_currency(other)
        return self.amount >= other.amount
