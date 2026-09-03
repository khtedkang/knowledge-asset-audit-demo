"""Tiny synthetic coverage calculation; not flight-control software."""

def coverage_ratio(observed: int, total: int) -> float:
    if total <= 0:
        raise ValueError("total must be positive")
    return max(0.0, min(1.0, observed / total))
