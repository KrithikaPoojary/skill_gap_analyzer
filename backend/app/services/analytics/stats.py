"""Statistical calculation functions for market analysis.

Provides robust statistical primitives: mean, median, percentiles, IQR,
and comprehensive distribution summaries with empty-set safety.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
import math
from typing import Any, Sequence


@dataclass(frozen=True)
class DistributionSummary:
    """Standard statistical summary of a numerical sample distribution."""

    count: int
    mean: float | None
    std_dev: float | None
    min: float | None
    p25: float | None
    median: float | None
    p75: float | None
    p90: float | None
    max: float | None
    iqr: float | None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def calculate_mean(values: Sequence[float]) -> float | None:
    """Compute arithmetic mean of a sequence of numbers."""
    if not values:
        return None
    return round(sum(values) / len(values), 2)


def calculate_percentile(values: Sequence[float], p: float) -> float | None:
    """Compute the p-th percentile (0 <= p <= 100) using linear interpolation."""
    if not values:
        return None
    if p < 0 or p > 100:
        raise ValueError(f"Percentile must be between 0 and 100, got {p}")

    sorted_vals = sorted(values)
    n = len(sorted_vals)
    if n == 1:
        return round(float(sorted_vals[0]), 2)

    rank = (p / 100.0) * (n - 1)
    lower_idx = int(math.floor(rank))
    upper_idx = int(math.ceil(rank))
    fraction = rank - lower_idx

    if lower_idx == upper_idx:
        return round(float(sorted_vals[lower_idx]), 2)

    val = sorted_vals[lower_idx] + fraction * (sorted_vals[upper_idx] - sorted_vals[lower_idx])
    return round(val, 2)


def calculate_median(values: Sequence[float]) -> float | None:
    """Compute the 50th percentile (median)."""
    return calculate_percentile(values, 50.0)


def calculate_std_dev(values: Sequence[float], mean_val: float | None = None) -> float | None:
    """Compute sample standard deviation."""
    if not values or len(values) < 2:
        return 0.0 if values else None

    mean = mean_val if mean_val is not None else (sum(values) / len(values))
    variance = sum((x - mean) ** 2 for x in values) / (len(values) - 1)
    return round(math.sqrt(variance), 2)


def summarize_distribution(values: Sequence[float]) -> DistributionSummary:
    """Generate a comprehensive DistributionSummary for a dataset."""
    valid = [float(v) for v in values if v is not None and not math.isnan(v)]
    if not valid:
        return DistributionSummary(
            count=0,
            mean=None,
            std_dev=None,
            min=None,
            p25=None,
            median=None,
            p75=None,
            p90=None,
            max=None,
            iqr=None,
        )

    mean_val = calculate_mean(valid)
    std_dev_val = calculate_std_dev(valid, mean_val)
    min_val = round(min(valid), 2)
    max_val = round(max(valid), 2)
    p25 = calculate_percentile(valid, 25.0)
    p50 = calculate_percentile(valid, 50.0)
    p75 = calculate_percentile(valid, 75.0)
    p90 = calculate_percentile(valid, 90.0)

    iqr_val = round(p75 - p25, 2) if (p75 is not None and p25 is not None) else None

    return DistributionSummary(
        count=len(valid),
        mean=mean_val,
        std_dev=std_dev_val,
        min=min_val,
        p25=p25,
        median=p50,
        p75=p75,
        p90=p90,
        max=max_val,
        iqr=iqr_val,
    )
