from decimal import Decimal

import pytest

from apps.core.money import CurrencyMismatchError, Money, UnknownCurrencyError


def eur(amount: str) -> Money:
    return Money(Decimal(amount), "EUR")


class TestConstruction:
    def test_money_from_float_raises_type_error(self):
        with pytest.raises(TypeError):
            Money(1.10, "EUR")  # type: ignore[arg-type]  # the point of the test

    @pytest.mark.parametrize("amount", [5, True, "5"])
    def test_money_from_non_decimal_raises_type_error(self, amount):
        with pytest.raises(TypeError):
            Money(amount, "EUR")

    @pytest.mark.parametrize("amount", ["NaN", "Infinity", "-Infinity"])
    def test_money_non_finite_amount_raises(self, amount):
        with pytest.raises(ValueError):
            Money(Decimal(amount), "EUR")

    @pytest.mark.parametrize("currency", ["XYZ", "eur", "", "EURO"])
    def test_money_unknown_currency_raises(self, currency):
        with pytest.raises(UnknownCurrencyError):
            Money(Decimal(1), currency)

    def test_money_zero_has_currency(self):
        assert Money.zero("GBP") == Money(Decimal(0), "GBP")

    def test_money_is_immutable(self):
        money = eur("1")

        with pytest.raises(AttributeError):
            money.amount = Decimal(2)  # type: ignore[misc]  # the point of the test


class TestArithmetic:
    def test_money_add_same_currency(self):
        assert eur("0.10") + eur("0.20") == eur("0.30")

    def test_money_subtract_same_currency(self):
        assert eur("1.00") - eur("0.01") == eur("0.99")

    def test_money_negate(self):
        assert -eur("2.50") == eur("-2.50")

    @pytest.mark.parametrize("other", [1, Decimal("1")])
    def test_money_add_or_subtract_plain_number_raises(self, other):
        with pytest.raises(TypeError):
            eur("1") + other
        with pytest.raises(TypeError):
            eur("1") - other

    def test_money_add_different_currency_raises(self):
        with pytest.raises(CurrencyMismatchError):
            eur("1") + Money(Decimal(1), "GBP")

    @pytest.mark.parametrize("factor", [Decimal("3"), 3])
    def test_money_multiply_by_quantity(self, factor):
        assert eur("1.25") * factor == eur("3.75")
        assert factor * eur("1.25") == eur("3.75")

    def test_money_multiply_keeps_precision_until_rounded(self):
        assert eur("10.00") * Decimal("0.055") == eur("0.55000")

    def test_money_multiply_by_float_raises(self):
        with pytest.raises(TypeError):
            eur("1") * 1.5  # type: ignore[operator]  # the point of the test

    def test_money_multiply_by_money_raises(self):
        with pytest.raises(TypeError):
            eur("1") * eur("2")  # type: ignore[operator]  # the point of the test

    def test_money_sum_with_zero_start(self):
        total = sum([eur("1.10"), eur("2.20")], Money.zero("EUR"))

        assert total == eur("3.30")


class TestComparison:
    def test_money_compare_same_currency(self):
        assert eur("1") < eur("2")
        assert eur("1") <= eur("1.00")
        assert eur("3") > eur("2")
        assert eur("2") >= eur("2.00")

    def test_money_compare_different_currency_raises(self):
        with pytest.raises(CurrencyMismatchError):
            eur("1") < Money(Decimal(2), "GBP")  # noqa: B015  # comparison is the test

    def test_money_equal_amounts_different_currency_are_not_equal(self):
        assert eur("1") != Money(Decimal(1), "GBP")


class TestRounding:
    @pytest.mark.parametrize(
        ("amount", "expected"),
        [
            ("0.125", "0.13"),  # half up, not banker's rounding
            ("0.135", "0.14"),
            ("0.124", "0.12"),
            ("-0.125", "-0.13"),  # away from zero for negatives
            ("2", "2.00"),
        ],
    )
    def test_money_round_half_up_to_minor_unit(self, amount, expected):
        rounded = eur(amount).round()

        assert rounded.amount == Decimal(expected)
        assert str(rounded.amount) == expected

    def test_money_round_returns_same_currency(self):
        assert Money(Decimal("1.005"), "GBP").round() == Money(Decimal("1.01"), "GBP")
