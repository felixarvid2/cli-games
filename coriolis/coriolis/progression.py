"""Trading and exploration ranks, kept apart from the combat rank."""

TRADE_RANKS = (
    (0, "Penniless"), (250, "Peddler"), (1000, "Dealer"),
    (4000, "Merchant"), (15000, "Tycoon"), (40000, "Magnate"),
)

EXPLORE_RANKS = (
    (0, "Lost"), (3, "Scout"), (10, "Pathfinder"),
    (30, "Trailblazer"), (80, "Explorer"), (200, "Cartographer"),
)


def _rank(table, value):
    name = table[0][1]
    for need, title in table:
        if value >= need:
            name = title
    return name


def _next(table, value):
    for need, title in table:
        if value < need:
            return title, need - value
    return table[-1][1], 0


def trade_rank(profit):
    return _rank(TRADE_RANKS, max(0.0, profit))


def explore_rank(visited):
    return _rank(EXPLORE_RANKS, visited)


def next_trade(profit):
    """(next title, profit still needed)."""
    return _next(TRADE_RANKS, max(0.0, profit))


def next_explore(visited):
    return _next(EXPLORE_RANKS, visited)


def progress_line(profit):
    title, left = next_trade(profit)
    if left <= 0:
        return "trade rank maxed"
    return f"{left:.0f} CR to {title}"


def explore_line(visited):
    title, left = next_explore(visited)
    if left <= 0:
        return "every chart explored"
    return f"{left} more systems to {title}"
