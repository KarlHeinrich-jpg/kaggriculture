# !pip install --quiet --upgrade "kaggle-environments>=1.32.2"

import math
from collections import Counter, defaultdict

import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np
import pandas as pd

from kaggle_environments.envs.kaggriculture.kaggriculture import (
    ANIMALS, CROPS, MARKET_I0, MARKET_PARAMS, PRODUCTS, SHOPS, market_price,
)

# Default game settings: 30 days of 24 turns.
DAYS, TURNS_PER_DAY = 30, 24
SHOP_UNLOCK_INTERVAL, SHOP_SELL_INTERVAL, TOWN_SELL_INTERVAL = 3, 4, 24
MAX_SHOP_INSTANCES = 8
I0 = MARKET_I0

# Blue/orange is the standard colour-blind-safe pair; purple and teal are added
# for a third and fourth series. Nothing is identified by colour alone -- every
# series is labelled directly on the plot as well.
BLUE, ORANGE, PURPLE, TEAL = "#1f6fb4", "#d1590f", "#7b52ab", "#0f8a6a"
GREY, GRID = "#6b6b66", "#dcdcd6"
plt.rcParams.update({
    "figure.dpi": 120, "axes.spines.top": False, "axes.spines.right": False,
    "axes.edgecolor": GREY, "axes.labelcolor": "#2c2c2a", "text.color": "#2c2c2a",
    "xtick.color": GREY, "ytick.color": GREY, "font.size": 9,
    "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.6,
    "axes.axisbelow": True, "figure.facecolor": "white",
})
print("engine loaded, products:", len(PRODUCTS))

rows = []
for item in PRODUCTS:
    p = MARKET_PARAMS[item]
    rows.append({
        "product": item, "base": p["base"], "T": p["T"],
        "scarcity shape": p["below_func"], "scarcity target": p["below_target"],
        "glut shape": p["above_func"], "glut target": p["above_target"],
        "price at I0−T": market_price(item, I0 - p["T"]),
        "price at I0+T": market_price(item, I0 + p["T"]),
    })
params = pd.DataFrame(rows).set_index("product")
params

show = ["STRAWBERRY", "MELON", "MILK", "WOOL", "WHEAT", "EGG"]
fig, axes = plt.subplots(2, 3, figsize=(11, 5.6), sharex=True)
span = np.arange(I0 - 600, I0 + 600, 5)
for ax, item in zip(axes.ravel(), show):
    y = [market_price(item, int(v)) for v in span]
    x = span - I0
    lo, hi = x < 0, x >= 0
    ax.plot(x[lo], np.array(y)[lo], color=BLUE, lw=2)
    ax.plot(x[hi], np.array(y)[hi], color=ORANGE, lw=2)
    ax.axvline(0, color=GREY, ls="--", lw=1)
    ax.axhline(MARKET_PARAMS[item]["base"], color=GRID, lw=1)
    ax.set_title(f"{item}   base ${MARKET_PARAMS[item]['base']}", fontsize=9.5)
    ax.set_ylim(0, max(y) * 1.08)
    ax.xaxis.set_major_formatter(mticker.FuncFormatter(
        lambda v, _: f"{v:+,.0f}".replace("+0", "I0")))
axes[0, 0].text(-560, 120, "town has eaten\n(scarcity)", color=BLUE,
                fontsize=8.5, va="top")
axes[0, 0].text(90, MARKET_PARAMS["STRAWBERRY"]["base"] * 0.55,
                "you have sold\n(glut)", color=ORANGE, fontsize=8.5)
for ax in axes[1]:
    ax.set_xlabel("market inventory, relative to I0")
for ax in axes[:, 0]:
    ax.set_ylabel("price, $")
fig.suptitle("Two branches, two different games — the dashed line is the "
             "starting inventory", y=0.99, fontsize=11)
fig.tight_layout()
plt.show()

def drain_by_day():
    '''Expected town consumption per day, units, for each product.'''
    p_type = 1.0 / len(SHOPS)
    per_day = {it: [] for it in PRODUCTS}
    for day in range(DAYS):
        n_inst = min(MAX_SHOP_INSTANCES, day // SHOP_UNLOCK_INTERVAL)
        today = Counter()
        for shop, items in SHOPS.items():
            mult = 2 if len(items) == 1 else 1
            copies = n_inst * p_type
            for it in items:
                today[it] += copies * (TURNS_PER_DAY / SHOP_SELL_INTERVAL) * mult
        for it in PRODUCTS:
            if it != "FERTILIZER":
                today[it] += TURNS_PER_DAY / TOWN_SELL_INTERVAL
        for it in PRODUCTS:
            per_day[it].append(today[it])
    return per_day

per_day = drain_by_day()
cum = {it: np.cumsum(v) for it, v in per_day.items()}
hole = {it: float(cum[it][-1]) for it in PRODUCTS}
pd.Series(hole, name="units eaten per season").sort_values(ascending=False).round(0).to_frame()

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, 4.1))
order = sorted(PRODUCTS, key=lambda i: -hole[i])
colours = {order[0]: BLUE, order[1]: ORANGE, order[2]: PURPLE, order[3]: TEAL}
placed = []
for it in order:
    c = colours.get(it, GRID)
    ax1.plot(range(DAYS), cum[it], color=c, lw=2 if it in colours else 1.2,
             zorder=3 if it in colours else 1)
    if it in colours:
        # CARROT and MILK have identical holes, so nudge the labels apart
        y = cum[it][-1]
        while any(abs(y - t) < 18 for t in placed):
            y -= 18
        placed.append(y)
        ax1.annotate(f" {it}  {hole[it]:,.0f}", (DAYS - 1, y),
                     color=c, fontsize=8.5, va="center")
ax1.set_xlim(0, DAYS + 7)
ax1.set_xlabel("day"); ax1.set_ylabel("units eaten, cumulative")
ax1.set_title("The hole the town digs for you", fontsize=10.5)

# the same hole, expressed as a price premium
depth = [market_price(it, int(I0 - hole[it])) / MARKET_PARAMS[it]["base"]
         for it in order]
bars = ax2.barh(range(len(order)), depth, color=[colours.get(i, GRID) for i in order],
                height=0.62)
ax2.set_yticks(range(len(order)), order, fontsize=8.5)
ax2.invert_yaxis()
ax2.axvline(1, color=GREY, ls="--", lw=1)
for i, (d, it) in enumerate(zip(depth, order)):
    ax2.text(d + 0.03, i, f"×{d:.2f}", va="center", fontsize=8.5, color=GREY)
ax2.set_xlabel("price at the bottom of the hole, relative to base")
ax2.set_title("What that hole is worth per unit", fontsize=10.5)
fig.tight_layout(); plt.show()

def sell_run(item, start_inv, n):
    '''Revenue from selling n units in a row. Mirrors the engine's
    _commit_unit: the price is quoted at the current inventory, then
    inventory rises by one (except at the price floor).'''
    inv, total, path = int(start_inv), 0.0, []
    for _ in range(int(n)):
        p = market_price(item, inv)
        total += p
        path.append(p)
        if p > 1:
            inv += 1
    return total, path

value = []
for it in PRODUCTS:
    n = hole[it]
    if n < 1:
        continue
    into_hole, path_hole = sell_run(it, I0 - n, n)
    into_flat, path_flat = sell_run(it, I0, n)
    value.append({
        "product": it, "base": MARKET_PARAMS[it]["base"], "hole": round(n),
        "into the hole": round(into_hole), "into a flat market": round(into_flat),
        "ratio": round(into_hole / max(into_flat, 1), 1),
        "first price": path_hole[0], "last price": path_hole[-1],
    })
value = pd.DataFrame(value).set_index("product").sort_values("into the hole",
                                                             ascending=False)
value

fig, ax = plt.subplots(figsize=(9.6, 4.4))
v = value.sort_values("into the hole")
y = np.arange(len(v))
ax.barh(y + 0.19, v["into the hole"], height=0.36, color=BLUE,
        label="sold into the hole the town dug")
ax.barh(y - 0.19, v["into a flat market"], height=0.36, color=ORANGE,
        label="same goods dumped into an untouched market")
ax.set_yticks(y, v.index, fontsize=9)
ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"${x/1000:,.0f}k"))
for i, (a, b) in enumerate(zip(v["into the hole"], v["into a flat market"])):
    ax.text(a + 2000, i + 0.19, f"${a:,.0f}", va="center", fontsize=8.5, color=BLUE)
    if a / max(b, 1) > 2:
        ax.text(a + 2000, i - 0.19, f"×{a/max(b,1):.0f}", va="center",
                fontsize=8.5, color=ORANGE)
ax.legend(frameon=False, loc="lower right", fontsize=9)
ax.set_xlabel("revenue from one season's worth of that product")
ax.set_title("The same crop, sold at two different times", fontsize=11)
fig.tight_layout(); plt.show()

fig, ax = plt.subplots(figsize=(9.6, 3.9))
for it, c in (("MELON", ORANGE), ("STRAWBERRY", BLUE), ("WHEAT", TEAL)):
    _, path = sell_run(it, I0 - hole[it], 400)
    ax.plot(np.arange(1, len(path) + 1), path, color=c, lw=2)
    ax.annotate(f" {it}", (len(path) - 1, path[-1]), color=c, fontsize=9,
                va="center")
    n_floor = next((i for i, p in enumerate(path, 1) if p <= 1), None)
    if n_floor:
        ax.plot([n_floor], [1], "o", color=c, ms=6)
        ax.annotate(f"  floor at {n_floor}", (n_floor, 1), color=c, fontsize=8.5,
                    va="bottom")
ax.set_xlim(0, 460)
ax.set_xlabel("units sold this season, starting from the bottom of the hole")
ax.set_ylabel("price of the next unit, $")
ax.set_title("How fast each market fills up", fontsize=11)
fig.tight_layout(); plt.show()

SOURCES = {
    "STRAWBERRY": dict(item="STRAWBERRY", per_tile=4 * (DAYS - 10) / 17, cost=100, lag=10),
    "MELON":      dict(item="MELON",      per_tile=6 * DAYS / 12,        cost=80,  lag=10),
    "TOMATO":     dict(item="TOMATO",     per_tile=4 * DAYS / 12,        cost=50,  lag=8),
    "WHEAT":      dict(item="WHEAT",      per_tile=4 * DAYS / 4,         cost=10,  lag=2),
    "CARROT":     dict(item="CARROT",     per_tile=3 * DAYS / 3,         cost=20,  lag=2),
    "COW":        dict(item="MILK",       per_tile=1.5 * (DAYS - 9),     cost=400, lag=8),
    "SHEEP":      dict(item="WOOL",       per_tile=4 / 3 * (DAYS - 7),   cost=500, lag=6),
    "GOOSE":      dict(item="EGG",        per_tile=2 * (DAYS - 5),       cost=300, lag=4),
}
LIVESTOCK = {"COW", "SHEEP", "GOOSE"}
WHEAT_OVERHEAD = 0.75      # wheat tiles needed per head of livestock

def allocate(n_tiles):
    inv0 = {it: I0 - hole.get(it, 0) for it in PRODUCTS}
    sold = {it: 0.0 for it in PRODUCTS}
    alloc, log, used = Counter(), [], 0.0
    while used < n_tiles:
        best, best_gain = None, 0.0
        for name, s in SOURCES.items():
            gain, _ = sell_run(s["item"], inv0[s["item"]] + sold[s["item"]],
                               s["per_tile"])
            gain -= s["cost"]
            if name in LIVESTOCK:
                f, _ = sell_run("FERTILIZER",
                                inv0["FERTILIZER"] + sold["FERTILIZER"],
                                DAYS - s["lag"])
                gain += f
                gain /= (1 + WHEAT_OVERHEAD)     # per tile, feed included
            if gain > best_gain:
                best, best_gain = name, gain
        if best is None:
            break
        s = SOURCES[best]
        step = 1 + (WHEAT_OVERHEAD if best in LIVESTOCK else 0)
        used += step
        alloc[best] += 1
        sold[s["item"]] += s["per_tile"]
        if best in LIVESTOCK:
            alloc["WHEAT"] += WHEAT_OVERHEAD
            sold["FERTILIZER"] += DAYS - s["lag"]
        log.append((used, best, best_gain))
    return alloc, sold, log

alloc, sold, log = allocate(100)
pd.Series({k: round(v, 1) for k, v in alloc.items()},
          name="tiles").sort_values(ascending=False).to_frame()

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, 4.2),
                               gridspec_kw={"width_ratios": [1.35, 1]})
cmap = {"COW": BLUE, "SHEEP": ORANGE, "GOOSE": PURPLE, "MELON": TEAL,
        "WHEAT": GREY, "STRAWBERRY": "#b02d6b", "CARROT": GRID, "TOMATO": GRID}
seen = set()
for used, name, gain in log:
    ax1.bar(used, gain, width=1.0, color=cmap.get(name, GRID),
            label=name if name not in seen else None)
    seen.add(name)
ax1.set_xlabel("tiles allocated so far")
ax1.set_ylabel("marginal revenue of the next tile, $")
ax1.set_title("Every tile, in the order it is worth buying", fontsize=10.5)
ax1.legend(frameon=False, fontsize=8, ncol=2)

first = [name for _, name, _ in log[:26]]
ax2.axis("off")
ax2.set_title("the first 25 tiles", fontsize=10.5, loc="left")
for i, name in enumerate(first[:25]):
    r, c = divmod(i, 5)
    ax2.add_patch(plt.Rectangle((c, -r), 0.92, 0.92,
                                color=cmap.get(name, GRID)))
    ax2.text(c + 0.46, -r + 0.46, name[:3], ha="center", va="center",
             color="white", fontsize=8, fontweight="bold")
ax2.set_xlim(-0.2, 5.2); ax2.set_ylim(-5.0, 1.2)
ax2.text(0, -4.55, "one 5×5 quadrant is all you start with",
         fontsize=8.5, color=GREY)
fig.tight_layout(); plt.show()

fib = [1, 1]
while len(fib) < 20:
    fib.append(fib[-1] + fib[-2])
cum_cost = np.cumsum(fib)
actions = np.arange(1, 21) * (TURNS_PER_DAY - 1)

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, 3.8))
ax1.plot(range(1, 21), cum_cost, color=BLUE, lw=2, marker="o", ms=3.5)
ax1.set_yscale("log")
ax1.set_xlabel("hands hired in one day"); ax1.set_ylabel("total cost, $ (log)")
ax1.set_title("Hiring cost is fibonacci and resets daily", fontsize=10.5)
for k in (5, 10, 15):
    ax1.annotate(f"  {k} hands = ${cum_cost[k-1]:,.0f}", (k, cum_cost[k - 1]),
                 fontsize=8.5, color=GREY)

ax2.plot(range(1, 21), cum_cost / actions, color=ORANGE, lw=2, marker="o", ms=3.5)
ax2.set_xlabel("hands hired in one day")
ax2.set_ylabel("$ per extra action")
ax2.set_title("Cost per action stays trivial until about 13 hands", fontsize=10.5)
ax2.axhline(1, color=GRID, lw=1)
ax2.annotate(" $1 / action", (1, 1), fontsize=8.5, color=GREY, va="bottom")
fig.tight_layout(); plt.show()

before = {"walking": 83.2, "animal care": 9.4, "shed trips": 3.0,
          "planting & building": 1.1, "idle": 1.4, "other": 1.9}
after = {"walking": 55.4, "animal care": 29.3, "shed trips": 6.9,
         "planting & building": 1.2, "idle": 5.3, "other": 1.9}
labels = list(before)
fig, ax = plt.subplots(figsize=(9.6, 2.6))
left_b = left_a = 0
cols = [GRID, BLUE, ORANGE, TEAL, "#e8e8e2", PURPLE]
for lab, c in zip(labels, cols):
    ax.barh(1, before[lab], left=left_b, color=c, height=0.55)
    ax.barh(0, after[lab], left=left_a, color=c, height=0.55)
    if before[lab] > 6:
        ax.text(left_b + before[lab] / 2, 1, f"{lab}\n{before[lab]:.0f}%",
                ha="center", va="center", fontsize=8,
                color="white" if c != GRID else "#2c2c2a")
    if after[lab] > 6:
        ax.text(left_a + after[lab] / 2, 0, f"{lab}\n{after[lab]:.0f}%",
                ha="center", va="center", fontsize=8,
                color="white" if c != GRID else "#2c2c2a")
    left_b += before[lab]; left_a += after[lab]
ax.set_yticks([1, 0], ["greedy\nretargeting", "finish the tile\nyou stand on"],
              fontsize=9)
ax.set_xlim(0, 100); ax.set_xlabel("share of all unit-turns in a season, %")
ax.grid(False); ax.spines["left"].set_visible(False)
ax.set_title("Where 720 turns per unit actually go", fontsize=11)
fig.tight_layout(); plt.show()

# %%writefile main.py
"""Kaggriculture: sell into the hole, not into the market.

The whole game turns on a sign. Market inventory starts at I0 = 10,000 and moves
both ways: players selling push it up, the town eating pulls it down. Price is a
function of the *distance* from I0, and for most products the lower branch is far
steeper than the upper one. So what a product is worth is set not by its base
price but by how much the town has already eaten out of it, and by the shape of
that lower curve.

Computed from the engine's own market_price, accounting for shops unlocking
gradually (days 3, 6, 9, ... up to 8 instances, drawn with replacement):

    product       town eats     fill the hole     dump into a flat market
    STRAWBERRY        426          $100,445           $4,173     (x24)
    MILK              327          $ 86,662           $6,432     (x13.5)
    WOOL              228          $ 54,340
    WHEAT             525          $ 21,152
    TOMATO            228          $ 16,812
    CARROT            327          $ 13,246
    EGG               228          $ 12,972
    MELON              30          $  8,184

Per tile per season, after seed or livestock cost:

    cow $8,333    sheep $7,343    melon $4,092    goose $2,820
    strawberry $1,674    wheat $1,209    tomato $737

Hence the layout: pastures with cows and sheep first, then melon, then geese,
with wheat pulled in behind them as feed. Strawberry is the most valuable thing
to *sell* and a mediocre thing to *grow* -- a plant yields four units in
seventeen days.

The trading rule: sell only while the price is above base, because once
inventory reaches I0 the hole is full and the next unit goes up the shallow
branch, where the same strawberry is worth a tenth as much. The agent
re-implements market_price to work out exactly how many units it can sell before
crossing that threshold, and holds the rest. Two corrections make it survive
contact with an opponent:

  * the threshold decays through the season, because the hole is shared and
    holding out for a price that never comes leaves you with a full shed;
  * liquidity beats price -- below two days of running costs it sells whatever
    it has at whatever it fetches.

On the last days it dumps everything: unsold goods do not count.
"""


P = {
    # Target layout, from allocating tiles greedily by marginal revenue: while
    # the next cow tile pays more than the next sheep tile, take the cow. The
    # order comes out cows -> sheep -> melon -> geese, with wheat pulled in as
    # feed. These caps were then trimmed by the sweep: fewer head than the
    # static optimum, because servicing an animal costs four actions a day.
    "cows": 8,
    "sheep": 9,
    "melons": 16,
    "geese": 10,
    "wheat_per_animal": 0.5,   # one wheat tile feeds about one head
    "buy_animal_until": 22,     # later than this a cow never pays back: first milk on day 8
    "plant_until": {"MELON": 16, "WHEAT": 26},
    # --- trading
    # The hole is shared with the opponent: whoever sells first takes the
    # premium. So the threshold decays through the season -- holding is only
    # worth it while there are days left for the town to eat more.
    "floor_start": 1.15,   # early on, sell only above base
    "floor_end": 0.8,      # by the end, at almost any price
    # Holding stock is a luxury for the solvent. The market is shared: if the
    # opponent is filling the hole, the price never recovers, and a farm with
    # no cash does nothing. Below this many days of running costs, sell
    # everything at whatever it fetches.
    "cash_floor_days": 2,
    "dump_day": 28,        # from this day, dump everything: leftovers score nothing
    "wheat_days": 2,       # days of feed kept in the shed
    # --- labour and money
    "hands": 10,
    "hire_max": 250,
    "carry": 6,
    "shed_cap": 55,
    "hold_until": 30,     # below this shed load, holding is free
    "drop_load": 3,
    "evening": 17,
    "hunger": 4,
    "runway": 3,
    "hire_day_cost": 200,
    "land_day_min": 1,
    "land_free_left": 8,
}

CROPS = {
    "WHEAT":      {"seed": 10, "first": 2, "max_day": 4,  "ongoing": False},
    "CARROT":     {"seed": 20, "first": 2, "max_day": 3,  "ongoing": False},
    "TOMATO":     {"seed": 50, "first": 8, "max_day": 8,  "ongoing": True, "interval": 1, "n": 4},
    "STRAWBERRY": {"seed": 100, "first": 10, "max_day": 10, "ongoing": True, "interval": 2, "n": 4},
    "MELON":      {"seed": 80, "first": 10, "max_day": 12, "ongoing": False},
}
ANIMALS = {
    "GOOSE": {"cost": 300, "struct": "COOP",    "product": "EGG"},
    "COW":   {"cost": 400, "struct": "PASTURE", "product": "MILK"},
    "SHEEP": {"cost": 500, "struct": "PASTURE", "product": "WOOL"},
}
# from the engine's MARKET_PARAMS; needed to work out how much can be sold
MP = {
    "WHEAT":      (25, 400, "sqrt", 0.80, "log", 0.20),
    "CARROT":     (35, 450, "log", 0.20, "sqrt", 0.70),
    "TOMATO":     (60, 200, "linear", 0.40, "sqrt", 0.60),
    "STRAWBERRY": (120, 100, "sqrt", 0.70, "linear", 1.60),
    "MELON":      (250, 300, "log", 0.20, "sq", 3.60),
    "EGG":        (50, 332, "linear", 0.40, "log", 0.20),
    "MILK":       (160, 122, "sqrt", 0.60, "linear", 1.60),
    "WOOL":       (200, 105, "log", 0.20, "sq", 3.20),
    "FERTILIZER": (100, 200, "linear", 0.40, "linear", 0.40),
}
I0 = 10000
PRODUCTS = list(MP)
SELLABLE = ["MILK", "WOOL", "STRAWBERRY", "MELON", "EGG", "TOMATO",
            "CARROT", "FERTILIZER", "WHEAT"]


def _shape(f, x):
    import math
    x = max(0.0, x)
    if f == "linear":
        return x
    if f == "sq":
        return x * x
    if f == "sqrt":
        return math.sqrt(x)
    if f == "log":
        return math.log(1.0 + x)
    return x


def price_of(item, inv):
    base, T, bf, bt, af, at = MP[item]
    if inv < I0:
        amp = bt * base / _shape(bf, T)
        p = base + amp * _shape(bf, I0 - inv)
    else:
        amp = at * base / _shape(af, T)
        p = base - amp * _shape(af, inv - I0)
    return max(1, int(round(p)))


def sellable_units(item, inv, floor_price):
    """How many units go before the price drops below floor_price.

    Each sale raises inventory by one, so the price falls as the order fills.
    This walks the curve exactly the way the engine does.
    """
    n = 0
    while n < 200:
        if price_of(item, inv + n) < floor_price:
            break
        n += 1
    return n


def _get(d, key, default=None):
    if isinstance(d, dict):
        return d.get(key, default)
    return getattr(d, key, default)


def _shed_tiles(n):
    h = n // 2
    return [(h - 1, h - 1), (h, h - 1), (h - 1, h), (h, h)]


def _step(fx, fy, tx, ty):
    if fx < tx:
        return "EAST"
    if fx > tx:
        return "WEST"
    if fy < ty:
        return "SOUTH"
    if fy > ty:
        return "NORTH"
    return None


def _d(a, b):
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def agent(obs):
    player = _get(obs, "player", 0)
    farms = _get(obs, "farms", [])
    if not farms or player >= len(farms):
        return {"farmer": ["PASS"], "hands": [], "market": []}

    farm = farms[player]
    private = _get(obs, "private", {}) or {}
    shed = dict(_get(private, "shed", {}) or {})
    seeds = dict(_get(private, "seeds", {}) or {})
    invs = [dict(i) if i else {} for i in (_get(private, "inventories", [{}]) or [{}])]
    tiles = farm["tiles"]
    n = len(tiles)
    day, hour = _get(obs, "day", 0), _get(obs, "hour", 0)
    money = farm["money"]
    mkt = _get(obs, "market", {}) or {}
    inv_mkt = _get(mkt, "inventory", {}) or {}
    prices = _get(mkt, "prices", {}) or {}
    wheat_price = max(1, prices.get("WHEAT", 25))

    units = [tuple(farm["farmer"])] + [tuple(p) for p in farm.get("hands", [])]
    n_units = len(units)
    while len(invs) < n_units:
        invs.append({})
    shed_access = _shed_tiles(n)
    centre = shed_access[0]

    # -------------------------------------------------------- read the farm
    animals, structs, free, weeds, plants = [], [], [], [], []
    for y in range(n):
        for x in range(n):
            t = tiles[y][x]
            if t is None:
                free.append((x, y))
            elif t == "LOCKED":
                continue
            elif isinstance(t, dict):
                k = t.get("kind")
                if k == "WEED":
                    weeds.append((x, y))
                elif k == "PLANT":
                    plants.append((x, y, t))
                elif "animal" in t:
                    animals.append((x, y, t))
                else:
                    structs.append((x, y, k))       # empty coop or pasture
    free.sort(key=lambda p: _d(p, centre))
    structs.sort(key=lambda s: _d((s[0], s[1]), centre))

    have = {"COW": 0, "SHEEP": 0, "GOOSE": 0}
    unfed = []
    for (x, y, t) in animals:
        have[t["animal"]] += 1
        if not t.get("fed_today"):
            unfed.append((x, y))
    for a in ANIMALS:
        have[a] += shed.get(a, 0) + sum(i.get(a, 0) for i in invs)

    crop_count = {}
    for (x, y, t) in plants:
        crop_count[t["crop"]] = crop_count.get(t["crop"], 0) + 1

    n_animals = sum(have.values())
    wheat_carried = sum(i.get("WHEAT", 0) for i in invs)
    wheat_have = shed.get("WHEAT", 0) + wheat_carried
    shed_total = sum(shed.values())
    day_cost = P["hire_day_cost"] + n_animals * wheat_price
    reserve = P["runway"] * day_cost

    # ------------------------------------------------------------ the market
    # Only 10 orders per turn are accepted and the rest are silently dropped,
    # so the queue is built by priority rather than in the order the code
    # happens to be written. Feed goes first: a shed full of unsold milk once
    # blocked a wheat purchase and the whole herd walked off in two days.
    market = []
    dumping = day >= P["dump_day"]

    # feed: one wheat per head per day; two missed days and it is gone for good
    wheat_target = max(2, int(n_animals * P["wheat_days"]))
    if wheat_have < wheat_target and shed_total < 95 and money > wheat_price:
        want = min(wheat_target - wheat_have, 95 - shed_total,
                   int(money // wheat_price))
        if want > 0:
            market.append(["BUY_PRODUCT", "WHEAT", want])

    # Sell into the hole: below I0 every unit fetches a premium, above it the
    # same strawberry is worth a tenth as much. But holding only works while
    # there is somewhere to put things -- the shed holds 100 and whatever does
    # not fit at nightfall is simply discarded. So the fuller the shed, the
    # lower the price we are willing to accept.
    t = min(1.0, day / max(1, P["dump_day"]))
    floor_day = P["floor_start"] + (P["floor_end"] - P["floor_start"]) * t
    if money < P["cash_floor_days"] * day_cost:
        floor_day = 0.0        # liquidity beats price
    slack = max(0.0, min(1.0, (shed_total - P["hold_until"]) /
                         max(1, 95 - P["hold_until"])))
    floor_mult = floor_day * (1.0 - slack)
    order = sorted((i for i in SELLABLE if shed.get(i, 0) > 0),
                   key=lambda i: -prices.get(i, 0) * shed.get(i, 0))
    for item in order:
        n_have = shed.get(item, 0)
        if item == "WHEAT":
            n_have -= wheat_target
            if n_have <= 0:
                continue
        if dumping:
            market.append(["SELL", item, n_have])
            continue
        base = MP[item][0]
        allow = sellable_units(item, inv_mkt.get(item, I0), base * floor_mult)
        k = min(n_have, allow)
        if k > 0:
            market.append(["SELL", item, k])

    # Hands: the fib(n) price resets every morning, so ten cost $143. Hired
    # across two turns so the hires do not eat the whole order queue at once.
    if hour in (0, 1) and len(market) < 9:
        a, b = 1, 1
        for _ in range(farm.get("hires_today", 0)):
            a, b = b, a + b
        budget = money - n_animals * wheat_price * 2
        while len(market) < 9 and farm.get("hires_today", 0) + \
                sum(1 for o in market if o[0] == "HIRE") < P["hands"]:
            if a > P["hire_max"] or a > budget:
                break
            market.append(["HIRE"])
            budget -= a
            a, b = b, a + b

    # Feed wheat comes before any investment. A herd you cannot feed walks off
    # in two days, and that is the only irreversible loss in the game.
    wheat_want = int(round(n_animals * P["wheat_per_animal"])) + 2
    wheat_planted = crop_count.get("WHEAT", 0) + seeds.get("WHEAT", 0)
    if wheat_planted < wheat_want and day <= P["plant_until"]["WHEAT"] and free:
        k = min(wheat_want - wheat_planted, len(free), 10,
                int(money // CROPS["WHEAT"]["seed"]))
        if k > 0:
            market.append(["BUY_SEED", "WHEAT", k])
            money -= k * 10

    # Animals pay best per tile and per dollar; bought strictly in marginal-
    # revenue order, and only once there is feed growing for them.
    room = len(free) + len(structs)
    # the herd never grows faster than the feed under it
    feed_ok = wheat_planted >= n_animals * P["wheat_per_animal"]
    if room > 0 and shed_total < 90 and day <= P["buy_animal_until"]:
        for kind, cap in (("COW", P["cows"]), ("SHEEP", P["sheep"]),
                          ("GOOSE", P["geese"])):
            if have[kind] >= cap or (kind == "GOOSE" and not feed_ok):
                continue
            cost = ANIMALS[kind]["cost"]
            afford = int((money - reserve) // (cost + P["runway"] * wheat_price))
            k = max(0, min(afford, cap - have[kind], room, 4))
            if k > 0:
                market.append(["BUY_ANIMAL", kind, k])
                money -= k * cost
                room -= k
                break

    # Melon: its hole is only 30 units, but the glut curve starts from $250,
    # so the first hundred still sell dear. A handful of tiles is right.
    melon_planted = crop_count.get("MELON", 0) + seeds.get("MELON", 0)
    if (melon_planted < P["melons"] and day <= P["plant_until"]["MELON"]
            and len(free) > 2 and money - reserve > 400):
        k = min(P["melons"] - melon_planted, len(free) - 2, 4,
                int((money - reserve) // CROPS["MELON"]["seed"]))
        if k > 0:
            market.append(["BUY_SEED", "MELON", k])
            money -= k * 80

    # Land: the 25 NW tiles hold neither the herd nor the feed for it.
    n_extra = len(farm.get("unlocked_quadrants", ["NW"])) - 1
    land_price = [1000, 2000, 4000][n_extra] if n_extra < 3 else None
    if (land_price and day >= P["land_day_min"] and day <= 22
            and len(free) <= P["land_free_left"]
            and money - land_price >= reserve + 600):
        market.append(["BUY_LAND"])

    market = market[:10]

    # ------------------------------------------------------------- the tasks
    # Every job at an animal is done from its own square: arrive, feed, care,
    # harvest, collect. So tasks are grouped by tile, and a unit already
    # standing on one finishes it before moving. Without this rule 83% of all
    # unit-turns went into walking, because units retargeted every turn.
    pending = {}

    def add(p, op):
        pending.setdefault(p, []).append(op)

    for (x, y, t) in animals:
        p = (x, y)
        if not t.get("fed_today"):
            add(p, ["FEED"])
        if t.get("yield_units", 0) > 0:
            add(p, ["HARVEST"])
        if not t.get("cared_today"):
            add(p, ["CARE"])          # +1 on the next scheduled yield
        if t.get("fertilizer_available"):
            add(p, ["COLLECT_FERTILIZER"])
    for (x, y, t) in plants:
        p = (x, y)
        cd = CROPS[t["crop"]]
        age = day - t["planted_day"]
        if not t.get("watered_today"):
            add(p, ["WATER"])
        if t.get("yield_units", 0) > 0:
            ripe = age >= cd["max_day"] if not cd["ongoing"] else age >= cd["first"]
            if ripe:
                add(p, ["HARVEST"])
    for (x, y) in weeds:
        add((x, y), ["DIG"])

    # what to build on the free tiles
    need_struct = {"PASTURE": max(0, shed.get("COW", 0) + shed.get("SHEEP", 0)
                                  + sum(i.get("COW", 0) + i.get("SHEEP", 0) for i in invs)
                                  - sum(1 for s in structs if s[2] == "PASTURE")),
                   "COOP": max(0, shed.get("GOOSE", 0)
                               + sum(i.get("GOOSE", 0) for i in invs)
                               - sum(1 for s in structs if s[2] == "COOP"))}
    plantable = []
    bi = 0
    for (x, y) in free:
        if need_struct["PASTURE"] > 0:
            add((x, y), ["BUILD_PASTURE"])
            need_struct["PASTURE"] -= 1
        elif need_struct["COOP"] > 0:
            add((x, y), ["BUILD_COOP"])
            need_struct["COOP"] -= 1
        else:
            plantable.append((x, y))
        bi += 1

    # --------------------------------------------------- assigning the units
    actions = [None] * n_units
    order = sorted(range(n_units), key=lambda i: _d(units[i], centre))
    unfed_left = set(unfed)
    targeted = set()
    seeds_left = dict(seeds)
    struct_free = {"COOP": [(x, y) for (x, y, k) in structs if k == "COOP"],
                   "PASTURE": [(x, y) for (x, y, k) in structs if k == "PASTURE"]}
    plant_left = list(plantable)
    wheat_shed = shed.get("WHEAT", 0)
    wheat_en_route = wheat_carried
    animals_shed = {a: shed.get(a, 0) for a in ANIMALS}

    def crop_for_tile():
        """What to plant on the next free tile."""
        for crop in ("WHEAT", "MELON"):
            if seeds_left.get(crop, 0) > 0:
                return crop
        return None

    for idx in order:
        pos, inv = units[idx], invs[idx]
        has_wheat = inv.get("WHEAT", 0) > 0
        carried_animal = next((a for a in ANIMALS if inv.get(a, 0) > 0), None)
        load = sum(v for k, v in inv.items()
                   if k not in ("WHEAT",) and k not in ANIMALS)
        at_shed = pos in shed_access

        # 1. finish the tile we are standing on
        here = pending.get(pos)
        if here:
            op = None
            for cand in here:
                if cand[0] == "FEED" and not has_wheat:
                    continue
                op = cand
                break
            if op is not None:
                here.remove(op)
                if op[0] == "FEED":
                    inv["WHEAT"] = inv.get("WHEAT", 0) - 1
                    unfed_left.discard(pos)
                actions[idx] = list(op)
                continue
        if carried_animal:
            st = ANIMALS[carried_animal]["struct"]
            if pos in struct_free[st]:
                struct_free[st].remove(pos)
                inv[carried_animal] = inv.get(carried_animal, 0) - 1
                actions[idx] = ["PLACE", carried_animal]
                continue
        if pos in plant_left:
            crop = crop_for_tile()
            if crop:
                plant_left.remove(pos)
                seeds_left[crop] -= 1
                crop_count[crop] = crop_count.get(crop, 0) + 1
                actions[idx] = ["PLANT", crop]
                continue

        # 2. a trip to the shed
        want = None
        pending_animal = next((a for a, k in animals_shed.items() if k > 0
                               and struct_free[ANIMALS[a]["struct"]]), None)
        if unfed_left and not has_wheat and wheat_shed > 0:
            want = "WHEAT"
        elif pending_animal and not carried_animal and not has_wheat:
            want = pending_animal
        elif load >= P["drop_load"] or (hour >= P["evening"] and load > 0):
            want = "DROP"
        if want:
            if at_shed:
                if want == "WHEAT":
                    take = min(P["carry"], wheat_shed)
                    actions[idx] = ["PICKUP", "WHEAT", take]
                    wheat_shed -= take
                    wheat_en_route += take
                elif want == "DROP":
                    actions[idx] = ["DROP"]
                else:
                    actions[idx] = ["PICKUP", want, 1]
                    animals_shed[want] -= 1
            else:
                tgt = min(shed_access, key=lambda p: _d(pos, p))
                actions[idx] = [_step(*pos, *tgt)]
            continue

        # 3. from mid-morning, the unfed outrank everything else
        if has_wheat and unfed_left and hour >= P["hunger"]:
            tgt = min(unfed_left, key=lambda p: _d(pos, p))
            unfed_left.discard(tgt)
            mv = _step(*pos, *tgt)
            actions[idx] = [mv] if mv else ["FEED"]
            continue

        # 4. head for the densest nearby tile
        best, best_key = None, None
        for p, ops in pending.items():
            if not ops or p in targeted:
                continue
            if all(o[0] == "FEED" for o in ops) and not has_wheat:
                continue
            d = _d(pos, p)
            key = (-len(ops) / (d + 1), d)
            if best_key is None or key < best_key:
                best, best_key = p, key
        if best is None and carried_animal:
            st = struct_free[ANIMALS[carried_animal]["struct"]]
            if st:
                best = min(st, key=lambda p: _d(pos, p))
        if best is None and plant_left and crop_for_tile():
            best = min(plant_left, key=lambda p: _d(pos, p))
        if best is None:
            if load:
                tgt = min(shed_access, key=lambda p: _d(pos, p))
                mv = _step(*pos, *tgt)
                actions[idx] = [mv] if mv else ["DROP"]
            else:
                actions[idx] = ["PASS"]
            continue
        targeted.add(best)
        mv = _step(*pos, *best)
        actions[idx] = [mv] if mv else ["PASS"]

    for i in range(n_units):
        if not actions[i] or actions[i][0] is None:
            actions[i] = ["PASS"]

    return {"farmer": actions[0], "hands": actions[1:], "market": market}


from kaggle_environments import make
import statistics, time

def play(a, b, seed):
    env = make("kaggriculture", configuration={"seed": seed}, debug=False)
    env.run([a, b])
    f = env.steps[-1]
    return float(f[0].reward or 0), float(f[1].reward or 0)

t0 = time.time()
results = []
for seed in range(6):
    mine, theirs = play("main.py", "starter", seed)
    results.append({"seed": seed, "agent": mine, "built-in starter": theirs})
    mine, theirs = play("main.py", "random", seed + 100)
    results.append({"seed": seed + 100, "agent": mine, "built-in random": theirs})
res = pd.DataFrame(results)
print(f"{len(results)} games in {time.time()-t0:.0f}s")
res.describe().loc[["mean", "50%", "min", "max"]].round(0)

env = make("kaggriculture", configuration={"seed": 0}, debug=False)
env.run(["main.py", "starter"])
money = [[s[p].observation.farms[p]["money"] if p == 0 else
          s[0].observation.farms[1]["money"] for p in (0,)][0]
         for s in env.steps]
mine = [s[0].observation.farms[0]["money"] for s in env.steps]
opp = [s[0].observation.farms[1]["money"] for s in env.steps]
days = np.arange(len(mine)) / TURNS_PER_DAY

fig, ax = plt.subplots(figsize=(9.6, 3.8))
ax.plot(days, mine, color=BLUE, lw=2)
ax.plot(days, opp, color=ORANGE, lw=2)
ax.annotate(f"  this agent  ${mine[-1]:,.0f}", (days[-1], mine[-1]), color=BLUE,
            fontsize=9, va="center")
ax.annotate(f"  built-in starter  ${opp[-1]:,.0f}", (days[-1], opp[-1]),
            color=ORANGE, fontsize=9, va="center")
ax.set_xlim(0, DAYS + 8)
ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f"${v/1000:,.0f}k"))
ax.set_xlabel("day"); ax.set_ylabel("bank")
ax.set_title("One season. Nothing happens until the hole opens.", fontsize=11)
fig.tight_layout(); plt.show()

# The comparison against the strong public agent was measured offline -- its
# code is not copied into this notebook, only the result of 12 swapped games.
bench = pd.DataFrame({
    "opponent": ["built-in\\n\"random\"", "built-in\\n\"starter\"",
                 "tetsutani\\nadaptive farming"],
    "this agent": [res["agent"].median(), res["agent"].median(), 27427],
    "opponent scored": [0, 3505, 120316],
})
fig, ax = plt.subplots(figsize=(8.4, 3.6))
y = np.arange(len(bench))
ax.barh(y + 0.19, bench["this agent"], height=0.36, color=BLUE, label="this agent")
ax.barh(y - 0.19, bench["opponent scored"], height=0.36, color=ORANGE,
        label="the opponent")
ax.set_yticks(y, bench["opponent"], fontsize=8.5)
ax.invert_yaxis()
ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f"${v/1000:,.0f}k"))
for i, (a, b) in enumerate(zip(bench["this agent"], bench["opponent scored"])):
    ax.text(a + 2500, i + 0.19, f"${a:,.0f}", va="center", fontsize=8.5, color=BLUE)
    ax.text(b + 2500, i - 0.19, f"${b:,.0f}", va="center", fontsize=8.5, color=ORANGE)
ax.legend(frameon=False, fontsize=9, loc="lower right")
ax.set_xlabel("median final bank")
ax.set_title("Beats the built-ins comfortably; loses to the state of the art by 4×",
             fontsize=10.5)
fig.tight_layout(); plt.show()