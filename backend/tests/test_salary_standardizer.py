"""Unit tests for the SalaryStandardizer service."""

import pytest

from app.services.salary_standardizer import SalaryStandardizer, StandardizedSalary, salary_standardizer


class TestSalaryStandardizer:
    """Test suite for rate conversion, currency parity, and standardization."""

    def test_to_annual_hourly_conversion(self) -> None:
        # $50/hour * 2080 hours = $104,000
        annual = salary_standardizer.to_annual(50.0, period="hourly")
        assert annual == 104000.0

    def test_to_annual_monthly_conversion(self) -> None:
        # $8,000/month * 12 months = $96,000
        annual = salary_standardizer.to_annual(8000.0, period="monthly")
        assert annual == 96000.0

    def test_to_annual_already_annual(self) -> None:
        annual = salary_standardizer.to_annual(125000.0, period="annual")
        assert annual == 125000.0

    def test_to_annual_none_and_negative(self) -> None:
        assert salary_standardizer.to_annual(None) is None
        assert salary_standardizer.to_annual(-50.0) is None
        assert salary_standardizer.to_annual(0.0) is None

    def test_convert_currency_same_currency(self) -> None:
        assert salary_standardizer.convert_currency(100000.0, "USD", "USD") == 100000.0

    def test_convert_currency_eur_to_usd(self) -> None:
        # 100,000 EUR * 1.08 = 108,000 USD
        usd = salary_standardizer.convert_currency(100000.0, "EUR", "USD")
        assert usd == 108000.0

    def test_convert_currency_inr_to_usd(self) -> None:
        # 1,200,000 INR (~12 LPA) * 0.012 = ~14,400 USD
        usd = salary_standardizer.convert_currency(1200000.0, "INR", "USD")
        assert usd == 14400.0

    def test_standardize_full_range_with_midpoint(self) -> None:
        res = salary_standardizer.standardize(
            min_salary=100000.0,
            max_salary=150000.0,
            from_currency="USD",
            to_currency="USD",
        )
        assert res.min_salary_annual == 100000.0
        assert res.max_salary_annual == 150000.0
        assert res.midpoint_annual == 125000.0
        assert res.currency == "USD"

    def test_standardize_inversion_swap(self) -> None:
        res = salary_standardizer.standardize(
            min_salary=180000.0,
            max_salary=120000.0,
        )
        assert res.min_salary_annual == 120000.0
        assert res.max_salary_annual == 180000.0
        assert res.midpoint_annual == 150000.0
