"""Small statistics helpers."""
import numpy as np


def wilson(k, n, z=1.96):
    """Wilson score interval for a proportion k/n (95 % by default). Returns (low, high)."""
    if n == 0:
        return float("nan"), float("nan")
    p = k / n
    d = 1 + z * z / n
    center = (p + z * z / (2 * n)) / d
    half = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    lo = 0.0 if k == 0 else max(0.0, center - half)             # exact bounds at the edges (no 1e-18 rounding)
    hi = 1.0 if k == n else min(1.0, center + half)
    return float(lo), float(hi)


def rate(flags):
    """{'k','n','rate','ci95'} for a boolean array."""
    flags = np.asarray(flags, bool)
    k, n = int(flags.sum()), int(flags.size)
    lo, hi = wilson(k, n)
    return {"k": k, "n": n, "rate": k / n if n else float("nan"), "ci95": [lo, hi]}


def wasserstein1(a, b, n=200):
    """1-D Wasserstein distance between two samples (mean absolute difference of the quantile functions)."""
    q = np.linspace(0.005, 0.995, n)
    return float(np.mean(np.abs(np.quantile(a, q) - np.quantile(b, q))))
