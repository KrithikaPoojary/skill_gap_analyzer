"""Salary standardization and currency normalization utility.

Converts diverse salary rates (hourly, monthly, annual) and international
currencies into standardized annualized figures for unified analytics.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import ClassVar


@dataclass(frozen=True)
class StandardizedSalary:
    """Standardized annual salary representation in target currency."""

    min_salary_annual: float | None
    max_salary_annual: float | None
    currency: str
    midpoint_annual: float | None

    @classmethod
    def from_range(
        cls,
        min_val: float | None,
        max_val: float | None,
        currency: str = "USD",
    ) -> StandardizedSalary:
        midpoint = None
        if min_val is not None and max_val is not None:
            midpoint = round((min_val + max_val) / 2.0, 2)
        elif min_val is not None:
            midpoint = min_val
        elif max_val is not None:
            midpoint = max_val

        return cls(
            min_salary_annual=min_val,
            max_salary_annual=max_val,
            currency=currency.upper(),
            midpoint_annual=midpoint,
        )


class SalaryStandardizer:
    """Standardizes disparate compensation formats to normalized annualized amounts."""

    # Approximate market parity exchange rates to USD base
    USD_EXCHANGE_RATES: ClassVar[dict[str, float]] = {
        "USD": 1.0,
        "EUR": 1.08,
        "GBP": 1.28,
        "CAD": 0.74,
        "AUD": 0.66,
        "INR": 0.012,  # ~83.5 INR per USD
    }

    # Working hours assumption for hourly rate conversion
    STANDARD_ANNUAL_HOURS: ClassVar[int] = 2080  # 40 hrs/wk * 52 wks
    MONTHS_PER_YEAR: ClassVar[int] = 12

    def to_annual(
        self,
        amount: float | None,
        period: str = "annual",
    ) -> float | None:
        """Convert hourly, monthly, or annual rates to an annualized amount.

        Args:
            amount: The monetary figure.
            period: 'hourly', 'monthly', or 'annual'.
        """
        if amount is None or amount <= 0:
            return None

        period_lower = period.strip().lower()
        if period_lower in ("hourly", "hour", "hr"):
            return round(amount * self.STANDARD_ANNUAL_HOURS, 2)
        elif period_lower in ("monthly", "month", "mo"):
            return round(amount * self.MONTHS_PER_YEAR, 2)
        elif period_lower in ("annual", "yearly", "year", "yr"):
            return round(amount, 2)
        else:
            return round(amount, 2)

    def convert_currency(
        self,
        amount: float | None,
        from_currency: str,
        to_currency: str = "USD",
    ) -> float | None:
        """Convert an amount from one currency to another using parity rates."""
        if amount is None:
            return None

        from_curr = from_currency.strip().upper()
        to_curr = to_currency.strip().upper()

        if from_curr == to_curr:
            return round(amount, 2)

        rate_from = self.USD_EXCHANGE_RATES.get(from_curr, 1.0)
        rate_to = self.USD_EXCHANGE_RATES.get(to_curr, 1.0)

        # Convert to USD first, then to target
        amount_usd = amount * rate_from
        target_amount = amount_usd / rate_to
        return round(target_amount, 2)

    def standardize(
        self,
        min_salary: float | None,
        max_salary: float | None,
        from_currency: str = "USD",
        to_currency: str = "USD",
        period: str = "annual",
    ) -> StandardizedSalary:
        """Fully normalize min and max salary into target currency and annualized rate."""
        ann_min = self.to_annual(min_salary, period)
        ann_max = self.to_annual(max_salary, period)

        conv_min = self.convert_currency(ann_min, from_currency, to_currency)
        conv_max = self.convert_currency(ann_max, from_currency, to_currency)

        # Swap if inverted
        if conv_min is not None and conv_max is not None and conv_min > conv_max:
            conv_min, conv_max = conv_max, conv_min

        return StandardizedSalary.from_range(conv_min, conv_max, to_currency)


salary_standardizer = SalaryStandardizer()
