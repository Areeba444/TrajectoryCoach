"""Pure Python statistics utilities. No numpy, no scipy."""
import math
import random


def rank(xs: list) -> list[float]:
    """Return ranks (1-indexed, average ties)."""
    n = len(xs)
    if n == 0:
        return []
    # Create (value, original_index) pairs and sort
    indexed = sorted(enumerate(xs), key=lambda t: t[1])
    ranks = [0.0] * n
    i = 0
    while i < n:
        j = i
        # Find the end of a run of equal values
        while j < n - 1 and indexed[j][1] == indexed[j + 1][1]:
            j += 1
        # Average rank for ties: positions i+1 .. j+1 (1-indexed)
        avg_rank = (i + 1 + j + 1) / 2.0
        for k in range(i, j + 1):
            ranks[indexed[k][0]] = avg_rank
        i = j + 1
    return ranks


def spearman_rho(xs: list, ys: list) -> float:
    """Spearman rank correlation between two lists of equal length."""
    n = len(xs)
    if n != len(ys):
        raise ValueError('Lists must have equal length')
    if n < 2:
        return float('nan')
    rx = rank(xs)
    ry = rank(ys)
    # Pearson correlation of ranks
    mean_rx = sum(rx) / n
    mean_ry = sum(ry) / n
    num = sum((rx[i] - mean_rx) * (ry[i] - mean_ry) for i in range(n))
    den_x = math.sqrt(sum((r - mean_rx) ** 2 for r in rx))
    den_y = math.sqrt(sum((r - mean_ry) ** 2 for r in ry))
    if den_x == 0 or den_y == 0:
        return float('nan')
    return num / (den_x * den_y)


def bootstrap_ci(
    data: list[float],
    stat_fn,
    n_boot: int = 1000,
    seed: int = 0,
    alpha: float = 0.05,
) -> tuple[float, float]:
    """
    Parametric bootstrap over a flat list. Returns (lower, upper) CI.
    Uses random.seed(seed) + random.choices for reproducibility.
    """
    rng = random.Random(seed)
    n = len(data)
    boot_stats = []
    for _ in range(n_boot):
        sample = rng.choices(data, k=n)
        boot_stats.append(stat_fn(sample))
    boot_stats.sort()
    lo_idx = int(math.floor(alpha / 2 * n_boot))
    hi_idx = int(math.floor((1 - alpha / 2) * n_boot)) - 1
    lo_idx = max(0, min(lo_idx, n_boot - 1))
    hi_idx = max(0, min(hi_idx, n_boot - 1))
    return (boot_stats[lo_idx], boot_stats[hi_idx])

