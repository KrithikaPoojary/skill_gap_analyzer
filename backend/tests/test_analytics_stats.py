"""Unit tests for statistical calculation primitives."""

import pytest

from app.services.analytics.stats import (
    calculate_mean,
    calculate_median,
    calculate_percentile,
    calculate_std_dev,
    summarize_distribution,
)


class TestAnalyticsStats:
    """Test suite for mean, median, IQR, percentiles, and distribution summary."""

    SAMPLE_DATA = [10, 20, 30, 40, 50, 60, 70, 80, 90, 100]

    def test_calculate_mean(self) -> None:
        assert calculate_mean(self.SAMPLE_DATA) == 55.0
        assert calculate_mean([]) is None
        assert calculate_mean([42.5]) == 42.5

    def test_calculate_median(self) -> None:
        assert calculate_median(self.SAMPLE_DATA) == 55.0
        assert calculate_median([10, 20, 30]) == 20.0
        assert calculate_median([10, 20]) == 15.0
        assert calculate_median([]) is None

    def test_calculate_percentile(self) -> None:
        assert calculate_percentile(self.SAMPLE_DATA, 0) == 10.0
        assert calculate_percentile(self.SAMPLE_DATA, 100) == 100.0
        assert calculate_percentile(self.SAMPLE_DATA, 50) == 55.0
        assert calculate_percentile(self.SAMPLE_DATA, 25) == 32.5
        assert calculate_percentile(self.SAMPLE_DATA, 75) == 77.5

        with pytest.raises(ValueError):
            calculate_percentile(self.SAMPLE_DATA, -5)
        with pytest.raises(ValueError):
            calculate_percentile(self.SAMPLE_DATA, 105)

    def test_calculate_std_dev(self) -> None:
        std = calculate_std_dev(self.SAMPLE_DATA)
        assert std is not None
        assert round(std, 1) == 30.3
        assert calculate_std_dev([]) is None
        assert calculate_std_dev([100]) == 0.0

    def test_summarize_distribution_populated(self) -> None:
        summary = summarize_distribution(self.SAMPLE_DATA)
        assert summary.count == 10
        assert summary.mean == 55.0
        assert summary.min == 10.0
        assert summary.max == 100.0
        assert summary.median == 55.0
        assert summary.p25 == 32.5
        assert summary.p75 == 77.5
        assert summary.iqr == 45.0
        assert summary.to_dict()["count"] == 10

    def test_summarize_distribution_empty(self) -> None:
        summary = summarize_distribution([])
        assert summary.count == 0
        assert summary.mean is None
        assert summary.median is None
        assert summary.iqr is None
