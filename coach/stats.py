"""Small statistics helpers. Standard library only, so results reproduce anywhere."""
import math, random, statistics


def rank(values):
    """Average ranks, so ties do not bias the correlation."""
    order = sorted(range(len(values)), key=lambda i: values[i])
    ranks = [0.0] * len(values)
    i = 0
    while i < len(order):
        j = i
        while j + 1 < len(order) and values[order[j + 1]] == values[order[i]]:
            j += 1
        shared = (i + j) / 2 + 1
        for k in range(i, j + 1):
            ranks[order[k]] = shared
        i = j + 1
    return ranks


def pearson(x, y):
    n = len(x)
    if n < 2:
        return None
    mx, my = statistics.fmean(x), statistics.fmean(y)
    num = sum((a - mx) * (b - my) for a, b in zip(x, y))
    dx = math.sqrt(sum((a - mx) ** 2 for a in x))
    dy = math.sqrt(sum((b - my) ** 2 for b in y))
    return None if dx == 0 or dy == 0 else num / (dx * dy)


def spearman(x, y):
    return pearson(rank(x), rank(y))


def bootstrap_ci(x, y, fn=spearman, reps=1000, seed=0):
    rng, draws = random.Random(seed), []
    n = len(x)
    for _ in range(reps):
        idx = [rng.randrange(n) for _ in range(n)]
        v = fn([x[i] for i in idx], [y[i] for i in idx])
        if v is not None:
            draws.append(v)
    if not draws:
        return None, None
    draws.sort()
    return draws[int(0.025 * len(draws))], draws[int(0.975 * len(draws)) - 1]


def mean_sd(values):
    vals = [v for v in values if v is not None]
    if not vals:
        return None, None
    return statistics.fmean(vals), (statistics.stdev(vals) if len(vals) > 1 else 0.0)
