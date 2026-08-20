import math

# ---------------------------------------------------------------------------
# The engine's market constants, copied from kaggriculture.py.
#   base          = price at equilibrium inventory (10,000)
#   T             = the "throughput" scale - how many units of imbalance it takes
#                   to move the price by `target` x base
#   below_/above_ = the SHAPE of the curve on each side of equilibrium, and how
#                   far it travels. These differ wildly per product and that
#                   asymmetry is the single most important thing in the game.
# ---------------------------------------------------------------------------
MARKET_I0 = 10000
MARKET_PARAMS = {
    "WHEAT":      {"base":  25, "T": 400, "bf": "sqrt",   "bt": 0.80, "af": "log",    "at": 0.20},
    "CARROT":     {"base":  35, "T": 450, "bf": "log",    "bt": 0.20, "af": "sqrt",   "at": 0.70},
    "TOMATO":     {"base":  60, "T": 200, "bf": "linear", "bt": 0.40, "af": "sqrt",   "at": 0.60},
    "STRAWBERRY": {"base": 120, "T": 100, "bf": "sqrt",   "bt": 0.70, "af": "linear", "at": 1.60},
    "MELON":      {"base": 250, "T": 300, "bf": "log",    "bt": 0.20, "af": "sq",     "at": 3.60},
    "EGG":        {"base":  50, "T": 332, "bf": "linear", "bt": 0.40, "af": "log",    "at": 0.20},
    "MILK":       {"base": 160, "T": 122, "bf": "sqrt",   "bt": 0.60, "af": "linear", "at": 1.60},
    "WOOL":       {"base": 200, "T": 105, "bf": "log",    "bt": 0.20, "af": "sq",     "at": 3.20},
    "FERTILIZER": {"base": 100, "T": 200, "bf": "linear", "bt": 0.40, "af": "linear", "at": 0.40},
}

def _shape(f, x):
    """The four curve shapes the engine uses."""
    x = x if x > 0 else 0.0
    if f == "linear": return x
    if f == "sq":     return x * x
    if f == "sqrt":   return math.sqrt(x)
    if f == "log":    return math.log(1.0 + x)
    return x

def market_price(item, inv):
    """Price of the NEXT unit at this inventory level.

    Note this is a function of live inventory, not of the `market.prices` dict you
    are shown - that dict only refreshes at the end of each order slot. You are
    handed `market.inventory` in the observation, so you can compute the true
    marginal price of unit #1 vs unit #40 of a sale *before* you send the order.
    """
    p = MARKET_PARAMS[item]
    base, T = p["base"], p["T"]
    if inv < MARKET_I0:
        # scarcity side: price rises above base
        amp = p["bt"] * base / _shape(p["bf"], T)
        v = base + amp * _shape(p["bf"], MARKET_I0 - inv)
    else:
        # glut side: price falls below base, and this is where products differ
        amp = p["at"] * base / _shape(p["af"], T)
        v = base - amp * _shape(p["af"], inv - MARKET_I0)
    return max(1, int(round(v)))          # $1 is a hard floor


# --- verify against the real engine, if it's importable -------------------
try:
    from kaggle_environments.envs.kaggriculture.kaggriculture import (
        market_price as engine_price)
    bad = [(it, inv) for it in MARKET_PARAMS for inv in range(5000, 15000)
           if engine_price(it, inv) != market_price(it, inv)]
    print("checked {:,} points against the real engine - mismatches: {}".format(
        len(MARKET_PARAMS) * 10000, len(bad)))
except Exception as e:
    print("kaggle_environments not importable here ({});".format(type(e).__name__),
          "using the reference implementation above.")

ROWS = [9000, 9500, 9800, 9900, 9950, 10000, 10050, 10100, 10200, 10500]
COLS = ["STRAWBERRY", "MILK", "WOOL", "MELON", "FERTILIZER", "WHEAT", "EGG"]

print("inventory " + "".join("{:>12}".format(c[:10]) for c in COLS))
for inv in ROWS:
    mark = " <-- equilibrium" if inv == MARKET_I0 else ""
    print("{:>9,} ".format(inv) +
          "".join("{:>12}".format(market_price(c, inv)) for c in COLS) + mark)

# Plot it, because the table undersells how sharp the transition is.
import matplotlib.pyplot as plt

xs = list(range(9600, 10400))
fig, ax = plt.subplots(figsize=(10, 5))
for item in ["STRAWBERRY", "MILK", "WOOL", "MELON", "EGG", "WHEAT"]:
    ax.plot(xs, [market_price(item, x) for x in xs], label=item, linewidth=2)
ax.axvline(MARKET_I0, color="black", linestyle="--", linewidth=1, alpha=.6)
ax.annotate("equilibrium\n(10,000)", xy=(MARKET_I0, 380), ha="center", fontsize=9)
ax.set_xlabel("market inventory")
ax.set_ylabel("price of the next unit ($)")
ax.set_title("The glut side is a cliff for premium goods and nearly flat for staples")
ax.legend()
ax.grid(alpha=.25)
plt.tight_layout()
plt.show()

def sell_block(n_units, item="STRAWBERRY", start_inv=9900):
    """Simulate selling n_units one at a time, exactly as the engine's order loop does.

    Returns (revenue, final_inventory, unit_at_which_price_hit_the_floor).
    """
    inv, revenue, floored_at = start_inv, 0, None
    for n in range(1, n_units + 1):
        price = market_price(item, inv)
        revenue += price
        if price > 1:
            inv += 1                     # only non-floor sales add inventory
        elif floored_at is None:
            floored_at = n
    return revenue, inv, floored_at

print("selling STRAWBERRY starting from inventory 9,900\n")
print("{:>14} {:>12} {:>10} {:>16}".format(
    "units sold", "cumulative $", "avg $/u", "this block $/u"))

prev_units, prev_rev = 0, 0
for n in (50, 100, 150, 200, 300, 400):
    rev, inv, floor_at = sell_block(n)
    block_units = n - prev_units
    block_rate = (rev - prev_rev) / block_units      # what the LAST slice earned each
    print("{:>14} {:>12,} {:>10.0f} {:>16.0f}".format(n, rev, rev / n, block_rate))
    prev_units, prev_rev = n, rev

rev, inv, floor_at = sell_block(400)
print("\nprice hit the $1 floor at unit {} of 400.".format(floor_at))
print("the last {} units earned $1 each - ${} for a third of the harvest.".format(
    400 - floor_at, 400 - floor_at))

# What the ceiling actually looks like, and what a collection rate is worth.
ANIMALS_PER_FARM = 14          # a typical mid-game herd
PRODUCTIVE_DAYS  = 28
FERT_PRICE       = 60          # realistic realised price, well off the $100 base

ceiling = ANIMALS_PER_FARM * PRODUCTIVE_DAYS
print("season ceiling: {} animals x {} days = {} fertiliser".format(
    ANIMALS_PER_FARM, PRODUCTIVE_DAYS, ceiling))
print("\n{:>16} {:>10} {:>14}".format("collection rate", "units", "revenue"))
for rate in (0.40, 0.50, 0.60, 0.75, 0.90):
    units = int(ceiling * rate)
    print("{:>15.0f}% {:>10} {:>14,}".format(rate * 100, units, units * FERT_PRICE))
print("\nevery 10 points of collection rate is worth ~${:,} a season.".format(
    int(ceiling * 0.10 * FERT_PRICE)))

SHED_CAPACITY = 100

def drop_to_shed(shed, carried, capacity=SHED_CAPACITY):
    """Faithful copy of the engine's _drop_inventories_to_shed.

    Returns (new_shed, units_destroyed). Note the engine deletes the carried
    inventory whether or not it fitted - there is no 'leftover' state.
    """
    shed = dict(shed)
    destroyed = 0
    for item, n in carried.items():
        current = sum(shed.values())
        room = max(0, capacity - current)
        take = min(n, room)
        if take > 0:
            shed[item] = shed.get(item, 0) + take
        destroyed += n - take          # <-- silently gone
    return shed, destroyed

# Scenario: you are holding wool through a price crash, waiting for the recovery.
# Meanwhile the farm keeps producing, and everything has to fit in the same 100 slots.
print("{:<22} {:>10} {:>12} {:>14}".format(
    "wool held back", "free slots", "day's output", "units destroyed"))
for held in (0, 20, 40, 60, 80):
    shed = {"WOOL": held}
    days_output = {"MILK": 22, "STRAWBERRY": 24, "FERTILIZER": 14}   # a mid-game day
    after, lost = drop_to_shed(shed, days_output)
    print("{:<22} {:>10} {:>12} {:>14}".format(
        held, SHED_CAPACITY - held, sum(days_output.values()), lost))

print("\nThe engine does not warn, does not drop the excess on the ground, and does")
print("not keep it in the carrying inventory. It is deleted.")
print("\nThis is the constraint that makes holding expensive: the shed you are using")
print("as a warehouse is the same shed your production has to land in tonight.")

ANIMALS = {
    "GOOSE": {"first_yield_day": 4, "interval": 1, "max_held": 4, "product": "EGG"},
    "COW":   {"first_yield_day": 8, "interval": 2, "max_held": 6, "product": "MILK"},
    "SHEEP": {"first_yield_day": 6, "interval": 3, "max_held": 6, "product": "WOOL"},
}

def lifetime_output(animal, care, days=30):
    """Total units produced over a season, following the engine's end-of-day logic.

    Assumes the animal is fed every day (2 consecutive unfed days kills it) and that
    a unit harvests the yield each morning, so `max_held` never truncates.
    """
    a = ANIMALS[animal]
    yield_units = pending = collected = 0
    for day in range(days):
        dsf = day - a["first_yield_day"]
        if dsf >= 0 and dsf % a["interval"] == 0:
            yield_units = min(a["max_held"], yield_units + 1 + pending)
            pending = 0
        if care:                       # cared AND fed
            pending += 1
        collected += yield_units       # harvested next morning
        yield_units = 0
    return collected

print("{:<8} {:>10} {:>10} {:>10}   {}".format("animal", "no care", "cared", "multiple", "product"))
for an in ("SHEEP", "COW", "GOOSE"):
    no, yes = lifetime_output(an, False), lifetime_output(an, True)
    print("{:<8} {:>10} {:>10} {:>9.2f}x   {}".format(an, no, yes, yes / no, ANIMALS[an]["product"]))

# What one consumption tick is worth, at realistic operating inventories.
TICK_DRAIN = 8      # a mid-game tick with several shops unlocked

print("{:<12} {:>10} {:>14} {:>10}".format("item", "inventory", "gain per unit", "%"))
for item in ("STRAWBERRY", "MILK", "WOOL", "FERTILIZER"):
    for inv in (9500, 9800, 9950):
        before = market_price(item, inv)
        after  = market_price(item, inv - TICK_DRAIN)
        print("{:<12} {:>10,} {:>14} {:>9.2f}%".format(
            item, inv, "+${}".format(after - before), 100 * (after - before) / before))
    print()

# %%writefile main.py
"""Kaggriculture agent - task-scheduling farm manager.

Strategy
--------
* CARE on animals is the single biggest edge in the game (measured against the real
  engine: sheep 4.25x, cow 3.27x, goose 2.08x lifetime output vs. never caring).
  Cows and sheep therefore get the tiles closest to the shed, where feeding is cheap
  in walking distance, and every animal is fed + cared every single day.
* Melon is the best crop per tile-day: 6 units per 10-day cycle at a $250 base, and
  a 30-day season fits exactly three cycles (plant day 0/10/19 -> harvest 10/20/29).
* Ongoing crops double their output if fertilised on production days AND harvested
  between productions (strawberry 4 -> 8 units). Animals hand us free fertiliser.
* The real constraint is market absorption, not production. Premium goods
  (melon/milk/wool/strawberry) crash to the $1 floor on modest gluts, while egg and
  wheat absorb almost unlimited volume. We spread across curves and meter selling so
  no price is pushed below a floor.
* Feed wheat is bought, not grown - a tile of wheat only feeds 0.67 animals for a
  season, so growing feed is a terrible use of land.
* Hands are extremely cheap (the first 15 in a day cost $1596 total, ~$4.4/action)
  against $90-150/action production, so we hire hard once cash allows. Land is
  bought early: NE is not just 25 tiles, it also unblocks the hand spawn squares
  (with only NW unlocked a hand spawning on (5,5) is permanently trapped).

Numeric knobs live in PARAMS and are tuned by self-play (tune.py).
"""
import math
from collections import deque

CROPS = {
    "WHEAT":      {"seed": 10, "first_yield_day": 2, "max_yield_day": 4, "interval": 0, "max_yield": 6, "ongoing": False},
    "CARROT":     {"seed": 20, "first_yield_day": 2, "max_yield_day": 3, "interval": 0, "max_yield": 4, "ongoing": False},
    "TOMATO":     {"seed": 50, "first_yield_day": 8, "max_yield_day": 8, "interval": 1, "max_yield": 4, "ongoing": True},
    "STRAWBERRY": {"seed": 100, "first_yield_day": 10, "max_yield_day": 10, "interval": 2, "max_yield": 4, "ongoing": True},
    "MELON":      {"seed": 80, "first_yield_day": 10, "max_yield_day": 12, "interval": 0, "max_yield": 6, "ongoing": False},
}
ANIMALS = {
    "GOOSE": {"cost": 300, "structure": "COOP",    "first_yield_day": 4, "interval": 1, "max_held": 4, "product": "EGG"},
    "COW":   {"cost": 400, "structure": "PASTURE", "first_yield_day": 8, "interval": 2, "max_held": 6, "product": "MILK"},
    "SHEEP": {"cost": 500, "structure": "PASTURE", "first_yield_day": 6, "interval": 3, "max_held": 6, "product": "WOOL"},
}
PRODUCTS = ["WHEAT", "CARROT", "TOMATO", "STRAWBERRY", "MELON", "EGG", "MILK", "WOOL", "FERTILIZER"]
MARKET_I0 = 10000
LAND_PRICES = [1000, 2000, 4000]
DIRS = (("NORTH", 0, -1), ("SOUTH", 0, 1), ("EAST", 1, 0), ("WEST", -1, 0))
MARKET_PARAMS = {
    "WHEAT":      {"base":  25, "T": 400, "bf": "sqrt",   "bt": 0.80, "af": "log",    "at": 0.20},
    "CARROT":     {"base":  35, "T": 450, "bf": "log",    "bt": 0.20, "af": "sqrt",   "at": 0.70},
    "TOMATO":     {"base":  60, "T": 200, "bf": "linear", "bt": 0.40, "af": "sqrt",   "at": 0.60},
    "STRAWBERRY": {"base": 120, "T": 100, "bf": "sqrt",   "bt": 0.70, "af": "linear", "at": 1.60},
    "MELON":      {"base": 250, "T": 300, "bf": "log",    "bt": 0.20, "af": "sq",     "at": 3.60},
    "EGG":        {"base":  50, "T": 332, "bf": "linear", "bt": 0.40, "af": "log",    "at": 0.20},
    "MILK":       {"base": 160, "T": 122, "bf": "sqrt",   "bt": 0.60, "af": "linear", "at": 1.60},
    "WOOL":       {"base": 200, "T": 105, "bf": "log",    "bt": 0.20, "af": "sq",     "at": 3.20},
    "FERTILIZER": {"base": 100, "T": 200, "bf": "linear", "bt": 0.40, "af": "linear", "at": 0.40},
}


def _shape(f, x):
    x = x if x > 0 else 0.0
    if f == "linear": return x
    if f == "sq":     return x * x
    if f == "sqrt":   return math.sqrt(x)
    if f == "log":    return math.log(1.0 + x)
    return x


def market_price(item, inv):
    p = MARKET_PARAMS[item]
    base, T = p["base"], p["T"]
    if inv < MARKET_I0:
        amp = p["bt"] * base / _shape(p["bf"], T)
        v = base + amp * _shape(p["bf"], MARKET_I0 - inv)
    else:
        amp = p["at"] * base / _shape(p["af"], T)
        v = base - amp * _shape(p["af"], inv - MARKET_I0)
    return max(1, int(round(v)))


# ---- tuned by self-play cross-entropy optimisation (see tune.py, 40 generations) ----
PARAMS = {
    # tile budget per role, filled nearest-to-shed first
    # Herd mix is the single largest lever measured against the actual ladder.
    # Sweeping it against the top-10 tape (lab/sweep.py) rather than in self-play:
    #   n_sheep  6 (was)   win vs tape 25.0%
    #   n_sheep  8         win vs tape 50.0%   +$1,682  z=+4.4
    #   n_sheep  9         win vs tape 70.8%   +$3,764  z=+8.6   <- adopted
    #   n_sheep 10         win vs tape 20.8%   -$1,046  z=-2.0
    # Replicated on two independent 16- and 24-seed sets. The optimum is sharp:
    # a 10th sheep costs more watering/feeding labour than its wool repays.
    # More COWS measured strongly negative in the same sweep (n_cow=8 -$3,895,
    # n_cow=10 -$12,378, n_cow=12 -$22,408) - milk's glut curve is linear-1.6 and
    # both farms already saturate it, so extra cows crash the price they sell into.
    "n_cow": 5, "n_sheep": 9, "n_goose": 0,
    "n_melon": 9, "n_straw": 40, "n_tomato": 0, "n_carrot": 0,
    # hiring
    "hire_max": 13, "hire_early_max": 6, "hire_cash_frac": 0.1763,
    # land: buy when day >= d and cash >= c
    "land1_day": 3, "land1_cash": 1266.3838,
    "land2_day": 7, "land2_cash": 2000,
    "land3_day": 11, "land3_cash": 22361.8008,
    # capital discipline
    "animal_start_day": 0,      # grow wheat on animal tiles until here
    "animal_last_day": 21,      # after this an animal cannot repay its cost
    "animal_reserve": 173.0606,    # cash kept back when buying animals
    "seed_reserve": 127.682,
    "straw_start_day": 3,       # strawberry seeds are $100 - not an opening buy
    "straw_cash": 272.9836,
    "tiles_per_unit": 3.5417,   # crop tiles one farmhand can keep alive per day
    # market. The shed holds only 100 items and end-of-day overflow is DESTROYED,
    # so holding inventory is pure downside - money in the bank is never lost.
    "sell_floor_frac": 0.3873,
    "sell_min_price": {"MELON": 40, "MILK": 40, "WOOL": 40, "STRAWBERRY": 30,
                       "TOMATO": 15, "EGG": 18, "CARROT": 10, "WHEAT": 12,
                       "FERTILIZER": 35},
    # animal dung is free money: the engine accepts SELL FERTILIZER at a $100 base
    # Animals cap at max_held and everything past it is DESTROYED. A cared sheep
    # gains 1+interval = 4 units per production, so waiting until yield >= 5 (the
    # old rule) means the next production overflows and we bin 2-3 units. Measured
    # in one game: we extracted 118 wool from 6 sheep where the tape got 173, and
    # 149 fertilizer where it got 243 - a VOLUME gap, not a price gap. Our
    # realised $/unit is actually HIGHER than theirs on almost every product.
    # Animal acquisition: 0 = demand-driven (buy for whatever animal-role tile is
    # actually free), 1 = fixed headcount target. Demand-driven LOOKS like a bug -
    # it fields 6 cows + 7 sheep when configured for 5 + 6, because assign_roles
    # re-ranks tiles as land unlocks - but measured head-to-head on identical
    # seeds it beats every fixed-target variant tried (-$238 vs -$1,577 at best,
    # 41.4% vs 34.3% win). It adapts the herd to the farm the agent actually has.
    "animal_target_mode": 0,
    "animal_harvest_slack": 2,  # harvest at max_held - slack; measured +$5,135 vs slack=1
    "fert_pri": 69,             # priority of COLLECT_FERTILIZER
    "fert_keep": 0,            # units held back for our own FERTILIZE jobs
    "fert_cap": 15,             # stop collecting past this much unsold in the shed
    # opponent modelling: sell ahead of a flood we can see coming
    "opp_model": 1,
    "threat_units": 12,         # opponent units on the stalk that count as a flood
    "threat_relax": 0.4944,        # how far to drop our price floor when threatened
    "endgame_day": 29,
    "wheat_days_buffer": 2, "wheat_buy_max_price": 85,
    "feed_pickup": 3, "use_fertilizer": 1,
    "max_walk": 3,              # never send a unit further than this for one job
    "sticky": 0,                # bias toward finishing the job we started
    # optimal min-cost assignment instead of greedy nearest-free-unit.
    # Measured: greedy walks 31.3% further than optimal, worse on 68% of turns.
    # crash-hold: the clone-pack tape is open-loop and floors wool/melon on
    # predictable days; measured wool $227 -> $1 -> $141 in a single game.
    "hold_crash": 0,          # measured -$747 vs OFF: shed cap makes holding worse
    "hold_ratio": 0.45,         # sell only above this fraction of the running peak
    "hold_until_day": 26,       # after this, liquidate regardless - no time to recover
    "assign_opt": 1,
    "pri_weight": 0.05,          # tiles of walking one priority point is worth
    "assign_max_jobs": 40,      # cap the matrix so per-turn latency stays bounded
    # job commitment: hold a target until done, rather than re-deriving every turn
    "commit": 0,          # measured -$6,788: re-optimising each turn beats committing
    "commit_break": 12,         # priority gap that may still steal a committed unit
    "drop_load": 6,             # haul this much before walking back to the shed
    "land_labour_frac": 0.7945, # only buy land we have the hands to work
    # routing: walking is the dominant cost, so paths are tie-broken through
    # pending work and a unit standing on a job does it instead of walking away
    "route_bias": 1,
    "opportunist": 2,           # 0 off, 1 stop for anything, 2 stop only if worthwhile
    "opportunist_floor": 26,    # min job priority worth stopping for
    "opportunist_delta": 39,    # how much worse than your target you will settle for
    # DAY_SCHEDULE pins fert_pri/fert_cap on 25 of the 30 days and hire_max /
    # hire_cash_frac on 20, which means a parameter search physically cannot move
    # them - and the measured gap against the ladder tape is a dung and wool
    # VOLUME gap that lives in exactly those knobs. These switches let the search
    # decide whether the baked schedule or the global value wins. Default 0 is
    # the pre-existing behaviour, so they cost nothing until measured positive.
    "sched_free_fert": 0,
    "sched_free_hire": 0,
    # the schedule was beam-searched against a 6-sheep farm; if it no longer
    # pays on the 9-sheep farm this switches it off and hands the keys back to
    # the global search
    "use_day_schedule": 1,
}

# ---- per-day strategy schedule (beam-searched offline, see lab/plan.py) -------
# The agent used ONE parameter set for all 30 days. The season is not stationary:
# early days are capital-constrained, mid-season is labour-constrained, and the
# endgame is market-constrained, so the right land intensity / hiring rate / sell
# floor differ by day. A rolling-horizon beam search (beam 4, 8 candidates/day,
# scored by simulating to season end) found per-day overrides worth
#   +$1,717 +-$230, z=+7.5, 85% win over 100 held-out games.
# Days not listed fall back to PARAMS.
DAY_SCHEDULE = {
    0: {
        'drop_load': 5, 'fert_cap': 20, 'fert_pri': 78, 'hire_cash_frac': 0.261195,
        'hire_max': 10, 'max_walk': 3, 'opportunist_delta': 45, 'opportunist_floor': 13,
        'route_bias': 1, 'sell_floor_frac': 0.396203, 'tiles_per_unit': 2.330154,
        'wheat_days_buffer': 1
    },
    1: {
        'drop_load': 7, 'fert_cap': 6, 'fert_pri': 95, 'hire_cash_frac': 0.219373,
        'hire_max': 12, 'max_walk': 3, 'opportunist_delta': 43, 'opportunist_floor': 30,
        'route_bias': 1, 'sell_floor_frac': 0.213114, 'tiles_per_unit': 3.636771,
        'wheat_days_buffer': 2
    },
    2: {
        'drop_load': 6, 'fert_cap': 16, 'fert_pri': 74, 'hire_cash_frac': 0.101894,
        'hire_max': 9, 'max_walk': 5, 'opportunist_delta': 24, 'opportunist_floor': 36,
        'route_bias': 1, 'sell_floor_frac': 0.336244, 'tiles_per_unit': 4.071247,
        'wheat_days_buffer': 2
    },
    3: {
        'drop_load': 10, 'fert_cap': 9, 'fert_pri': 93, 'hire_cash_frac': 0.352118,
        'hire_max': 15, 'max_walk': 4, 'opportunist_delta': 19, 'opportunist_floor': 30,
        'route_bias': 1, 'sell_floor_frac': 0.425861, 'tiles_per_unit': 3.367878,
        'wheat_days_buffer': 2
    },
    4: {
        'drop_load': 5, 'fert_cap': 12, 'fert_pri': 68, 'hire_cash_frac': 0.166026,
        'hire_max': 12, 'max_walk': 2, 'opportunist_delta': 47, 'opportunist_floor': 37,
        'route_bias': 1, 'sell_floor_frac': 0.443822, 'tiles_per_unit': 3.370646,
        'wheat_days_buffer': 1
    },
    5: {
        'drop_load': 8, 'fert_cap': 12, 'fert_pri': 65, 'hire_cash_frac': 0.145216,
        'hire_max': 13, 'max_walk': 3, 'opportunist_delta': 34, 'opportunist_floor': 20,
        'route_bias': 1, 'sell_floor_frac': 0.361047, 'tiles_per_unit': 3.568063,
        'wheat_days_buffer': 1
    },
    6: {
        'drop_load': 7, 'fert_cap': 25, 'fert_pri': 66, 'hire_cash_frac': 0.259064,
        'hire_max': 15, 'max_walk': 2, 'opportunist_delta': 23, 'opportunist_floor': 20,
        'route_bias': 1, 'sell_floor_frac': 0.429879, 'tiles_per_unit': 3.235801,
        'wheat_days_buffer': 1
    },
    7: {
        'drop_load': 4, 'fert_cap': 19, 'fert_pri': 65, 'hire_cash_frac': 0.05,
        'hire_max': 9, 'max_walk': 2, 'opportunist_delta': 44, 'opportunist_floor': 26,
        'route_bias': 1, 'sell_floor_frac': 0.365325, 'tiles_per_unit': 4.786934,
        'wheat_days_buffer': 3
    },
    9: {
        'drop_load': 6, 'fert_cap': 15, 'fert_pri': 68, 'hire_cash_frac': 0.245524,
        'hire_max': 11, 'max_walk': 3, 'opportunist_delta': 37, 'opportunist_floor': 22,
        'route_bias': 1, 'sell_floor_frac': 0.388067, 'tiles_per_unit': 3.338662,
        'wheat_days_buffer': 2
    },
    10: {
        'drop_load': 6, 'fert_pri': 54, 'hire_cash_frac': 0.190097, 'max_walk': 2,
        'sell_floor_frac': 0.284804, 'tiles_per_unit': 2.137628
    },
    11: {
        'drop_load': 5, 'fert_cap': 13, 'fert_pri': 86, 'hire_cash_frac': 0.05,
        'hire_max': 14, 'max_walk': 3, 'opportunist_delta': 39, 'opportunist_floor': 20,
        'route_bias': 1, 'sell_floor_frac': 0.438602, 'tiles_per_unit': 4.358638,
        'wheat_days_buffer': 2
    },
    13: {
        'drop_load': 6, 'fert_cap': 23, 'fert_pri': 80, 'hire_cash_frac': 0.17926,
        'hire_max': 10, 'max_walk': 2, 'opportunist_delta': 42, 'opportunist_floor': 25,
        'route_bias': 1, 'sell_floor_frac': 0.282407, 'tiles_per_unit': 2.542352,
        'wheat_days_buffer': 2
    },
    14: {
        'drop_load': 8, 'fert_cap': 16, 'fert_pri': 69, 'hire_cash_frac': 0.199052,
        'hire_max': 8, 'max_walk': 3, 'opportunist_delta': 53, 'opportunist_floor': 23,
        'route_bias': 1, 'sell_floor_frac': 0.53966, 'tiles_per_unit': 4.145957,
        'wheat_days_buffer': 4
    },
    15: {
        'drop_load': 5, 'fert_cap': 24, 'fert_pri': 83, 'hire_cash_frac': 0.237464,
        'hire_max': 12, 'max_walk': 4, 'opportunist_delta': 45, 'opportunist_floor': 36,
        'route_bias': 1, 'sell_floor_frac': 0.489601, 'tiles_per_unit': 3.302522,
        'wheat_days_buffer': 1
    },
    16: {
        'drop_load': 6, 'fert_cap': 12, 'fert_pri': 70, 'hire_cash_frac': 0.120331,
        'hire_max': 11, 'max_walk': 4, 'opportunist_delta': 34, 'opportunist_floor': 22,
        'route_bias': 1, 'sell_floor_frac': 0.438901, 'tiles_per_unit': 4.127247,
        'wheat_days_buffer': 1
    },
    17: {
        'drop_load': 7, 'fert_pri': 61, 'hire_cash_frac': 0.087703, 'max_walk': 3,
        'sell_floor_frac': 0.382342, 'tiles_per_unit': 3.206709
    },
    18: {
        'drop_load': 3, 'fert_cap': 11, 'fert_pri': 72, 'hire_cash_frac': 0.155269,
        'hire_max': 14, 'max_walk': 2, 'opportunist_delta': 43, 'opportunist_floor': 28,
        'route_bias': 1, 'sell_floor_frac': 0.215148, 'tiles_per_unit': 2.081383,
        'wheat_days_buffer': 3
    },
    19: {
        'drop_load': 6, 'fert_cap': 14, 'fert_pri': 72, 'hire_cash_frac': 0.05,
        'hire_max': 12, 'max_walk': 3, 'opportunist_delta': 48, 'opportunist_floor': 16,
        'route_bias': 1, 'sell_floor_frac': 0.187006, 'tiles_per_unit': 4.051292,
        'wheat_days_buffer': 1
    },
    21: {
        'drop_load': 9, 'fert_cap': 16, 'fert_pri': 72, 'hire_cash_frac': 0.128108,
        'hire_max': 12, 'max_walk': 3, 'opportunist_delta': 38, 'opportunist_floor': 27,
        'route_bias': 1, 'sell_floor_frac': 0.305308, 'tiles_per_unit': 4.508708,
        'wheat_days_buffer': 2
    },
    22: {
        'drop_load': 6, 'fert_cap': 19, 'fert_pri': 70, 'hire_cash_frac': 0.185978,
        'hire_max': 11, 'max_walk': 3, 'opportunist_delta': 39, 'opportunist_floor': 28,
        'route_bias': 1, 'sell_floor_frac': 0.281957, 'tiles_per_unit': 3.335851,
        'wheat_days_buffer': 3
    },
    23: {
        'drop_load': 5, 'fert_pri': 48, 'hire_cash_frac': 0.141644, 'max_walk': 2,
        'sell_floor_frac': 0.354808, 'tiles_per_unit': 3.282099
    },
    25: {
        'drop_load': 5, 'fert_pri': 82, 'hire_cash_frac': 0.209097, 'max_walk': 2,
        'sell_floor_frac': 0.455768, 'tiles_per_unit': 2.11229
    },
    26: {
        'drop_load': 4, 'fert_cap': 17, 'fert_pri': 58, 'hire_cash_frac': 0.095041,
        'hire_max': 12, 'max_walk': 4, 'opportunist_delta': 50, 'opportunist_floor': 10,
        'route_bias': 1, 'sell_floor_frac': 0.559047, 'tiles_per_unit': 3.380601,
        'wheat_days_buffer': 1
    },
    27: {
        'drop_load': 6, 'fert_cap': 19, 'fert_pri': 80, 'hire_cash_frac': 0.140807,
        'hire_max': 9, 'max_walk': 3, 'opportunist_delta': 20, 'opportunist_floor': 32,
        'route_bias': 1, 'sell_floor_frac': 0.332525, 'tiles_per_unit': 3.140262,
        'wheat_days_buffer': 2
    },
    28: {
        'drop_load': 5, 'fert_cap': 13, 'fert_pri': 76, 'hire_cash_frac': 0.127736,
        'hire_max': 10, 'max_walk': 3, 'opportunist_delta': 51, 'opportunist_floor': 24,
        'route_bias': 1, 'sell_floor_frac': 0.405297, 'tiles_per_unit': 3.214423,
        'wheat_days_buffer': 3
    },
    29: {
        'drop_load': 4, 'fert_pri': 53, 'hire_cash_frac': 0.191441, 'max_walk': 2,
        'sell_floor_frac': 0.221859, 'tiles_per_unit': 4.063683
    },
}


def day_params(P, day):
    # `_sched_applied` lets the offline planner (lab/plan.py) merge the baked
    # schedule with its own candidate day-plans itself and then opt out here.
    # Without it, round-2 search candidates are silently overwritten by round-1's
    # baked values on exactly the 20 days that matter, and the search measures
    # nothing.
    if P.get("_sched_applied") or not P.get("use_day_schedule", 1):
        return P
    over = DAY_SCHEDULE.get(day)
    if not over:
        return P
    Q = dict(P)
    Q.update(over)
    # let the global value win back the keys the search needs to be able to move
    if P.get("sched_free_fert"):
        Q["fert_pri"], Q["fert_cap"] = P["fert_pri"], P["fert_cap"]
    if P.get("sched_free_hire"):
        Q["hire_max"], Q["hire_cash_frac"] = P["hire_max"], P["hire_cash_frac"]
    return Q


_MEM = {}


def bfs(sx, sy, tiles, n, jobset=None):
    """Shortest-path map from (sx, sy).

    With `jobset` ({(x, y): priority}), ties between equal-length paths are broken
    toward the route crossing the most *valuable* pending work. Walking is ~70% of
    all actions, so a unit that strolls over three thirsty tiles on its way to a
    harvest turns three separate round trips into one - the detour is free because
    the path length is identical, and the opportunistic pass below does the work it
    lands on. Weighting by priority rather than counting jobs matters: an unweighted
    version steered units into clusters of cheap work (weeds, fertiliser pickup) and
    cost ~$6k a game.
    """
    dist = [[-1] * n for _ in range(n)]
    first = [[None] * n for _ in range(n)]
    if not (0 <= sx < n and 0 <= sy < n):
        return dist, first
    dist[sy][sx] = 0
    q = deque(((sx, sy),))
    if jobset is None:
        while q:
            x, y = q.popleft()
            d = dist[y][x] + 1
            f0 = first[y][x]
            for name, dx, dy in DIRS:
                nx, ny = x + dx, y + dy
                if 0 <= nx < n and 0 <= ny < n and dist[ny][nx] < 0 and tiles[ny][nx] != "LOCKED":
                    dist[ny][nx] = d
                    first[ny][nx] = name if (x, y) == (sx, sy) else f0
                    q.append((nx, ny))
        return dist, first
    # BFS expands strictly level by level, so every level-(d-1) parent is popped
    # before any level-d node is itself popped: an equal-distance improvement is
    # therefore always final by the time the node expands its own children.
    gain = [[0] * n for _ in range(n)]
    while q:
        x, y = q.popleft()
        d = dist[y][x] + 1
        f0 = first[y][x]
        g0 = gain[y][x]
        for name, dx, dy in DIRS:
            nx, ny = x + dx, y + dy
            if not (0 <= nx < n and 0 <= ny < n) or tiles[ny][nx] == "LOCKED":
                continue
            cur = dist[ny][nx]
            if cur >= 0 and cur != d:
                continue
            g = g0 + jobset.get((nx, ny), 0)
            if cur < 0:
                dist[ny][nx] = d
                first[ny][nx] = name if (x, y) == (sx, sy) else f0
                gain[ny][nx] = g
                q.append((nx, ny))
            elif g > gain[ny][nx]:
                first[ny][nx] = name if (x, y) == (sx, sy) else f0
                gain[ny][nx] = g
    return dist, first


def price_state(mem, prices, day):
    """Track each product's running peak so we can tell a crash from a low base.

    The top of the leaderboard is ~7 copies of one hardcoded 720-turn tape. It is
    open-loop: it cannot see prices, so it dumps the same goods on the same turn
    into the same nonlinear curve. Measured in our own engine against it:

        WOOL   227 (day 14) -> 1 (day 24) -> 141 (day 26)
        MELON  277 (day 10) -> 81 (day 24) -> 169 (day 29)
        STRAW  137 -> 215 (day 20 peak) -> 64 (day 29, everyone liquidating)

    Selling wool on day 24 realises $1/unit for goods worth $141 two days later.
    Our own endgame_day=29 was liquidating strawberry at its seasonal LOW.

    Because the clone pack is deterministic, these crashes are predictable, and
    an agent that simply declines to sell into them collects the recovery. This
    is the one edge an open-loop tape structurally cannot take.
    """
    pk = mem.setdefault("pmax", {})
    for it, p in prices.items():
        if p > pk.get(it, 0):
            pk[it] = p
    return pk


def hungarian(cost, n, m):
    """Optimal min-cost assignment (Jonker-Volgenant shortest-path form), O(n^2 m).

    Our scheduler assigned each job to its NEAREST FREE UNIT, taking jobs in
    priority order. That is a greedy approximation to min-cost bipartite
    matching, and greedy matching can be arbitrarily bad: one unit grabbing the
    job nearest to it can force three others into long walks.

    Measured on a full game (160 sampled turns, ~11 units and ~9 jobs each):
    greedy walks 2,266 tiles where the optimal assignment walks 1,726 - a
    **31.3% excess**, and greedy is strictly worse on 68% of turns. Movement is
    ~60% of all unit-actions, so this is roughly a fifth of the entire action
    budget spent on a problem with an exact polynomial solution.

    Requires n <= m; callers pad with dummy columns of cost 0.
    Returns row -> column (or -1).
    """
    INF = float("inf")
    u = [0.0] * (n + 1)
    v = [0.0] * (m + 1)
    p = [0] * (m + 1)
    way = [0] * (m + 1)
    for i in range(1, n + 1):
        p[0] = i
        j0 = 0
        minv = [INF] * (m + 1)
        used = [False] * (m + 1)
        while True:
            used[j0] = True
            i0 = p[j0]
            delta = INF
            j1 = -1
            row = cost[i0 - 1]
            for j in range(1, m + 1):
                if not used[j]:
                    cur = row[j - 1] - u[i0] - v[j]
                    if cur < minv[j]:
                        minv[j] = cur
                        way[j] = j0
                    if minv[j] < delta:
                        delta = minv[j]
                        j1 = j
            if j1 < 0:
                break
            for j in range(m + 1):
                if used[j]:
                    u[p[j]] += delta
                    v[j] -= delta
                else:
                    minv[j] -= delta
            j0 = j1
            if p[j0] == 0:
                break
        while j0:
            j1 = way[j0]
            p[j0] = p[j1]
            j0 = j1
    out = [-1] * n
    for j in range(1, m + 1):
        if 0 < p[j] <= n:
            out[p[j] - 1] = j - 1
    return out


def shed_tiles(n):
    h = n // 2
    return ((h - 1, h - 1), (h, h - 1), (h - 1, h), (h, h))


def assign_roles(tiles, n, P):
    """Every unlocked tile gets a role; animals sit nearest the shed."""
    sx, sy = shed_tiles(n)[0]
    open_t = []
    for y in range(n):
        for x in range(n):
            if tiles[y][x] != "LOCKED":
                open_t.append((abs(x - sx) + abs(y - sy), y, x))
    open_t.sort()
    order = (("COW", P["n_cow"]), ("SHEEP", P["n_sheep"]), ("GOOSE", P["n_goose"]),
             ("MELON", P["n_melon"]), ("STRAWBERRY", P["n_straw"]),
             ("TOMATO", P["n_tomato"]), ("CARROT", P["n_carrot"]))
    roles, i = {}, 0
    for role, cnt in order:
        for _ in range(int(cnt)):
            if i >= len(open_t):
                break
            _, y, x = open_t[i]
            roles[(x, y)] = role
            i += 1
    while i < len(open_t):
        _, y, x = open_t[i]
        roles[(x, y)] = "WHEAT"
        i += 1
    return roles


def plan_sale(item, have, inv, floor_frac, min_price):
    if have <= 0:
        return 0
    now = market_price(item, inv)
    if now < min_price:
        return 0
    limit = max(min_price, now * floor_frac)
    sold, cur = 0, inv
    while sold < have:
        p = market_price(item, cur)
        if p < limit:
            break
        sold += 1
        if p > 1:
            cur += 1
    return sold


def _fib(k):
    a, b = 1, 1
    for _ in range(k):
        a, b = b, a + b
    return a


def _act(obs, P, _MEM):
    P = day_params(P, obs["day"])
    me = obs["farms"][obs["player"]]
    priv = obs["private"]
    tiles = me["tiles"]
    n = len(tiles)
    day, hour = obs["day"], obs["hour"]
    money = me["money"]
    shed = dict(priv["shed"])                 # local copies: never mutate the observation
    seeds = dict(priv["seeds"])
    invs = priv["inventories"]
    mkt_inv = obs["market"]["inventory"]
    prices = obs["market"]["prices"]
    endgame = day >= P["endgame_day"]
    pmax = price_state(_MEM.setdefault("_px", {}), prices, day)
    last_day = 29


    roles = assign_roles(tiles, n, P)
    units = [tuple(me["farmer"])] + [tuple(h) for h in me["hands"]]
    sheds = set(shed_tiles(n))

    # Only farm as much land as we have hands to keep watered. Overextending is how
    # a farm turns into a field of weeds: an unwatered plant dies in two days.
    labour = max(1, len(units))
    if hour <= 1:
        labour = max(labour, min(P["hire_max"], int(money * P["hire_cash_frac"] / 8) + 1))
    crop_budget = int(P["tiles_per_unit"] * labour)
    sx0, sy0 = shed_tiles(n)[0]
    crop_rank = {}
    _r = 0
    for _d, _y, _x in sorted((abs(x - sx0) + abs(y - sy0), y, x)
                             for y in range(n) for x in range(n)
                             if tiles[y][x] != "LOCKED" and roles.get((x, y)) not in ANIMALS):
        crop_rank[(_x, _y)] = _r
        _r += 1

    def may_plant(x, y):
        return crop_rank.get((x, y), 0) < crop_budget

    # ------------------------------------------------------------------ jobs
    jobs = []
    n_animals = unfed = 0
    have_animal = {a: shed.get(a, 0) for a in ANIMALS}
    for inv in invs:
        for a in ANIMALS:
            have_animal[a] += inv.get(a, 0)

    for y in range(n):
        row = tiles[y]
        for x in range(n):
            t = row[x]
            if t == "LOCKED":
                continue
            role = roles.get((x, y), "WHEAT")
            if t is None:
                if role in ANIMALS:
                    if have_animal.get(role, 0) > 0:
                        jobs.append((72, x, y, "BUILD_" + ANIMALS[role]["structure"], None))
                    else:                       # earn from the tile until we can afford the animal
                        if day + CROPS["WHEAT"]["max_yield_day"] <= last_day and seeds.get("WHEAT", 0) > 0:
                            jobs.append((60, x, y, "PLANT", "WHEAT"))
                elif role in CROPS and not endgame and may_plant(x, y):
                    crop = role
                    if day + CROPS[crop]["first_yield_day"] > last_day:   # too late for this crop
                        crop = "WHEAT"
                    if crop != "WHEAT" and seeds.get(crop, 0) <= 0 and seeds.get("WHEAT", 0) > 0 \
                            and day + CROPS["WHEAT"]["max_yield_day"] <= last_day:
                        crop = "WHEAT"          # fall back to the cash crop rather than idle
                    if seeds.get(crop, 0) > 0 and day + CROPS[crop]["first_yield_day"] <= last_day:
                        jobs.append((62, x, y, "PLANT", crop))
                continue
            if not isinstance(t, dict):
                continue
            kind = t.get("kind")

            if kind == "WEED":
                jobs.append((28 if not endgame else 0, x, y, "DIG", None))

            elif kind == "PLANT":
                cd = CROPS[t["crop"]]
                age = day - t["planted_day"]
                if not t["watered_today"]:
                    if t["consecutive_unwatered"] >= 1:
                        jobs.append((98, x, y, "WATER", None))       # dies tonight otherwise
                    elif not cd["ongoing"]:
                        ws = (cd["max_yield_day"] + 1) // 2
                        if ws <= age <= cd["max_yield_day"] and t["yield_units"] < cd["max_yield"]:
                            jobs.append((66, x, y, "WATER", None))
                    elif t.get("fertilized_until_day", -1) >= day:
                        jobs.append((66, x, y, "WATER", None))
                ready = age >= cd["first_yield_day"] and t["yield_units"] > 0
                if ready:
                    if not cd["ongoing"]:
                        if t["yield_units"] >= cd["max_yield"] or age >= cd["max_yield_day"] or endgame:
                            jobs.append((86, x, y, "HARVEST", None))
                    elif t["yield_units"] >= 2 or endgame:
                        jobs.append((86, x, y, "HARVEST", None))     # clear the cap before next production
                if P["use_fertilizer"] and not endgame and t.get("fertilized_until_day", -1) < day:
                    if cd["ongoing"] and age >= cd["first_yield_day"] - 1:
                        jobs.append((44, x, y, "FERTILIZE", None))
                    elif t["crop"] in ("WHEAT", "CARROT") and age == (cd["max_yield_day"] + 1) // 2 - 1:
                        jobs.append((38, x, y, "FERTILIZE", None))

            elif "animal" in t:
                n_animals += 1
                a = ANIMALS[t["animal"]]
                if not t["fed_today"]:
                    unfed += 1
                    jobs.append((99, x, y, "FEED", None))
                if t["yield_units"] >= max(1, a["max_held"] - P["animal_harvest_slack"]) or (endgame and t["yield_units"] > 0):
                    jobs.append((88, x, y, "HARVEST", None))
                if not t["cared_today"] and not endgame:
                    jobs.append((82, x, y, "CARE", None))
                # Fertiliser is worth collecting even when we never spread any: the
                # engine accepts SELL FERTILIZER (the rules text says otherwise, but
                # PRODUCTS includes it and the order commits) at a $100 base, and
                # animals produce it free. Worth more per action than a wheat harvest.
                # The cap is the safety net: if the live engine turns out to refuse
                # the sale, fertiliser stalls here instead of filling the 100-item
                # shed and silently destroying the produce we actually live on.
                if t.get("fertilizer_available") and shed.get("FERTILIZER", 0) < P["fert_cap"]:
                    jobs.append((P["fert_pri"], x, y, "COLLECT_FERTILIZER", None))

            elif kind in ("COOP", "PASTURE"):
                want = None
                r = roles.get((x, y))
                if r in ANIMALS and ANIMALS[r]["structure"] == kind:
                    want = r
                else:
                    for an, ad in ANIMALS.items():
                        if ad["structure"] == kind and have_animal.get(an, 0) > 0:
                            want = an
                            break
                if want:
                    jobs.append((76, x, y, "PLACE", want))

    # A FEED job is only doable by a unit already carrying wheat, so fetching feed
    # has to be a scheduled job in its own right - otherwise every unit is busy
    # watering, nobody ever walks to the shed, and the whole herd starves.
    carried_wheat = sum((invs[i] if i < len(invs) else {}).get("WHEAT", 0)
                        for i in range(len(units)))
    shed_wheat = shed.get("WHEAT", 0)
    open_shed = [(sx1, sy1) for (sx1, sy1) in shed_tiles(n) if tiles[sy1][sx1] != "LOCKED"]
    if unfed > carried_wheat and shed_wheat > 0:
        runs = min(len(open_shed), -(-(unfed - carried_wheat) // max(1, P["feed_pickup"])))
        for (sx1, sy1) in open_shed[:runs]:
            jobs.append((97, sx1, sy1, "GET_FEED", None))

    # Same story for livestock: an animal sitting in the shed earns nothing, and
    # only a unit standing at the shed can pick it up. Make that a real job too.
    waiting = [j for j in jobs if j[3] == "PLACE"]
    carried_animals = sum((invs[i] if i < len(invs) else {}).get(a, 0)
                          for i in range(len(units)) for a in ANIMALS)
    fetch = min(len(open_shed), len(waiting) - carried_animals)
    if fetch > 0:
        wanted = [j[4] for j in waiting][carried_animals:]
        for k, (sx1, sy1) in enumerate(open_shed[:fetch]):
            if k < len(wanted) and shed.get(wanted[k], 0) > 0:
                jobs.append((94, sx1, sy1, "GET_ANIMAL", wanted[k]))

    jobs.sort(key=lambda j: -j[0])

    # ------------------------------------------------------- assign jobs to units
    # Assign each job to its NEAREST free unit (not: let each unit pick its
    # favourite job). Letting units choose sends everyone chasing the same urgent
    # tile across the farm; in an early build that burned 80% of all actions on
    # walking. Nearest-unit assignment keeps every worker in its own neighbourhood.
    n_units = len(units)
    actions = [None] * n_units
    inv_of = [invs[i] if i < len(invs) else {} for i in range(n_units)]

    def can_do(ui, op, extra):
        inv = inv_of[ui]
        if op == "FEED":
            return inv.get("WHEAT", 0) > 0
        if op == "GET_FEED":
            return inv.get("WHEAT", 0) == 0
        if op == "GET_ANIMAL":
            return not any(inv.get(a, 0) for a in ANIMALS)
        if op == "PLACE":
            return inv.get(extra, 0) > 0
        if op == "FERTILIZE":
            return inv.get("FERTILIZER", 0) > 0
        return True

    # Each unit is routed through the work *it personally* can do. This is what
    # makes livestock pay: a unit that picks up several wheat now walks the row of
    # hungry animals and feeds each one it steps on, instead of making a separate
    # round trip to the shed per animal.
    if P["route_bias"]:
        maps = []
        for ui, (ux, uy) in enumerate(units):
            js = {}
            for pri, jx, jy, op, extra in jobs:      # jobs are already priority-sorted
                if (jx, jy) not in js and pri >= P["opportunist_floor"] \
                        and can_do(ui, op, extra):
                    js[(jx, jy)] = pri
            maps.append(bfs(ux, uy, tiles, n, js))
    else:
        maps = [bfs(ux, uy, tiles, n) for (ux, uy) in units]
    free = set(range(n_units))
    plan = {}

    mem = _MEM.get(obs["player"])
    if not mem or mem.get("t") != (day, hour - 1) and mem.get("t") != (day - 1, 23):
        mem = {"assign": {}}
    prev = mem.get("assign", {})

    # units hauling a full load go bank it first - unsold produce in a hand is
    # destroyed at end of day once the shed is full. A unit carrying feed wheat
    # uses PLACE so it does not dump the herd's dinner into the shed as well.
    for ui in list(free):
        inv = inv_of[ui]
        prod = {k: v for k, v in inv.items() if k in PRODUCTS and k not in ("WHEAT", "FERTILIZER")}
        load = sum(prod.values())
        if load >= P["drop_load"] or (endgame and load > 0):
            ux, uy = units[ui]
            dist, first = maps[ui]
            if (ux, uy) in sheds:
                if inv.get("WHEAT", 0) > 0 and unfed > 0:
                    item = max(prod, key=prod.get)
                    actions[ui] = ["PLACE", item, prod[item]]
                else:
                    actions[ui] = ["DROP"]
                free.discard(ui)
            else:
                mv = None
                for (tx, ty) in shed_tiles(n):
                    if dist[ty][tx] >= 0 and first[ty][tx]:
                        mv = first[ty][tx]
                        break
                if mv:
                    actions[ui] = [mv]
                    free.discard(ui)

    done_jobs = set()

    # Work under your feet is free: it costs the one turn the op takes, where any
    # other unit would pay walking distance on top. Strict priority ordering used
    # to walk a unit off the tile it was standing on to chase a job worth a few
    # points more, leaving the tile it abandoned for someone else to walk to.
    if P["opportunist"] == 1:
        floor = P["opportunist_floor"]
        for job in jobs:
            pri, jx, jy, op, extra = job
            if pri < floor or (jx, jy, op) in done_jobs:
                continue
            here = next((ui for ui in sorted(free)
                         if units[ui] == (jx, jy) and can_do(ui, op, extra)), None)
            if here is not None:
                plan[here] = job
                done_jobs.add((jx, jy, op))
                free.discard(here)

    # ---- JOB COMMITMENT ------------------------------------------------------
    # Measured on a full game: of every turn where a unit's target changed, 43.3%
    # were ABANDONED before the unit ever arrived, burning 4,046 unit-turns -
    # most of the entire movement budget - walking toward work someone else took
    # or that simply got re-ranked. Re-deriving every assignment from scratch each
    # turn is what causes it: a job list that shifts by one priority point yanks a
    # unit off a walk it was two thirds through.
    #
    # So a unit now KEEPS its target until the job is done or genuinely dead. The
    # `sticky` tiebreak was meant to do this but only subtracted one tile from the
    # distance comparison, which is far too weak - the optimiser correctly tuned it
    # to 0 because it never changed an outcome.
    #
    # Preemption is still allowed, but only for something materially better
    # (commit_break priority points), so a starving animal can still steal a unit
    # that is strolling to a watering job.
    live_jobs = {(jx, jy, op): (pri, extra) for (pri, jx, jy, op, extra) in jobs}
    if P["commit"]:
        for ui in sorted(free):
            key = prev.get(ui)
            if not key:
                continue
            info = live_jobs.get(key)
            if info is None:                 # job finished or no longer needed
                continue
            pri, extra = info
            if key in done_jobs or not can_do(ui, key[2], extra):
                continue
            d = maps[ui][0][key[1]][key[0]]
            if d < 0:
                continue
            # would a materially better job pull this unit away right now?
            steal = False
            for (bp, bx, by, bop, bex) in jobs:
                if bp <= pri + P["commit_break"]:
                    break                    # jobs are priority-sorted
                if (bx, by, bop) in done_jobs or not can_do(ui, bop, bex):
                    continue
                bd = maps[ui][0][by][bx]
                if 0 <= bd <= d:             # better AND no further away
                    steal = True
                    break
            if steal:
                continue
            plan[ui] = (pri, key[0], key[1], key[2], extra)
            done_jobs.add(key)
            free.discard(ui)

    # ---- OPTIMAL ASSIGNMENT --------------------------------------------------
    # Solve units-to-jobs exactly instead of greedily. Cost is travel distance
    # minus the job's priority scaled by `pri_weight` (how many tiles of walking
    # one priority point is worth), so the matching trades off "how urgent" and
    # "how far" globally rather than letting whichever job comes first in the
    # priority order claim the nearest unit.
    if P["assign_opt"] and free and jobs:
        cand_jobs = []
        seen_j = set()
        for (pri, jx, jy, op, extra) in jobs:
            if (jx, jy, op) in done_jobs or (jx, jy, op) in seen_j:
                continue
            seen_j.add((jx, jy, op))
            cand_jobs.append((pri, jx, jy, op, extra))
            if len(cand_jobs) >= P["assign_max_jobs"]:
                break
        rows = sorted(free)
        if rows and cand_jobs:
            W = float(P["pri_weight"])
            BIG = 1e6
            nrow, ncol = len(rows), len(cand_jobs)
            wide = max(ncol, nrow)              # pad so every unit has an out
            cost = []
            for ui in rows:
                dmap = maps[ui][0]
                r = []
                for (pri, jx, jy, op, extra) in cand_jobs:
                    d = dmap[jy][jx]
                    if d < 0 or not can_do(ui, op, extra):
                        r.append(BIG)
                    else:
                        r.append(float(d) - W * float(pri))
                r.extend([0.0] * (wide - ncol))  # dummy = stay unassigned, cost 0
                cost.append(r)
            match = hungarian(cost, nrow, wide)
            for ri, cj in enumerate(match):
                if cj < 0 or cj >= ncol:
                    continue
                if cost[ri][cj] >= BIG:
                    continue                    # unreachable / cannot do
                ui = rows[ri]
                job = cand_jobs[cj]
                plan[ui] = job
                done_jobs.add((job[1], job[2], job[3]))
                free.discard(ui)

    # First pass keeps everyone local (max_walk); a second, unbounded pass hands
    # whatever is left to units that would otherwise stand around doing nothing.
    for reach in (P["max_walk"], 2 * n):
        for job in jobs:
            if not free:
                break
            pri, jx, jy, op, extra = job
            if (jx, jy, op) in done_jobs:
                continue
            best_ui, best_d = None, None
            for ui in free:
                d = maps[ui][0][jy][jx]
                if d < 0 or d > reach:
                    continue
                if not can_do(ui, op, extra):
                    continue
                eff = d - (P["sticky"] if prev.get(ui) == (jx, jy, op) else 0)
                if best_d is None or eff < best_d:
                    best_d, best_ui = eff, ui
            if best_ui is not None:
                plan[best_ui] = job
                done_jobs.add((jx, jy, op))
                free.discard(best_ui)
        if not free:
            break

    # Mode 2 decides the same thing after assignment, when the alternative is
    # actually known: stop for the job under your feet only if it is worth nearly
    # as much as the one you were walking to. Stopping unconditionally delays the
    # expensive jobs (a melon harvest) behind a string of cheap ones.
    if P["opportunist"] == 2:
        floor, delta = P["opportunist_floor"], P["opportunist_delta"]
        for ui, job in list(plan.items()):
            pri, jx, jy, op, extra = job
            ux, uy = units[ui]
            if (jx, jy) == (ux, uy):
                continue
            for cand in jobs:                        # priority-sorted: best first
                cp, cx, cy, cop, cex = cand
                if cp < floor or cp < pri - delta:
                    break
                if (cx, cy) != (ux, uy) or (cx, cy, cop) in done_jobs:
                    continue
                if not can_do(ui, cop, cex):
                    continue
                plan[ui] = cand
                done_jobs.add((cx, cy, cop))
                done_jobs.discard((jx, jy, op))      # release it for next turn
                break
        for ui in sorted(free):
            ux, uy = units[ui]
            for cand in jobs:
                cp, cx, cy, cop, cex = cand
                if cp < floor:
                    break
                if (cx, cy) != (ux, uy) or (cx, cy, cop) in done_jobs:
                    continue
                if not can_do(ui, cop, cex):
                    continue
                plan[ui] = cand
                done_jobs.add((cx, cy, cop))
                free.discard(ui)
                break

    new_assign = {}
    feed_left = shed.get("WHEAT", 0)
    for ui, job in plan.items():
        pri, jx, jy, op, extra = job
        ux, uy = units[ui]
        new_assign[ui] = (jx, jy, op)
        if (jx, jy) == (ux, uy):
            if op == "PLANT":
                actions[ui] = ["PLANT", extra]
            elif op == "PLACE":
                actions[ui] = ["PLACE", extra]
            elif op == "GET_FEED":
                take = max(1, min(P["feed_pickup"], feed_left, unfed))
                feed_left -= take
                actions[ui] = ["PICKUP", "WHEAT", take]
            elif op == "GET_ANIMAL":
                actions[ui] = ["PICKUP", extra, 1]
            else:
                actions[ui] = [op]
        else:
            mv = maps[ui][1][jy][jx]
            actions[ui] = [mv] if mv else ["PASS"]

    # idle units: fetch feed wheat / carry an animal / park at the shed
    wheat_free = shed.get("WHEAT", 0)
    carry_claim = dict(shed)
    need_carry = [j for j in jobs if j[3] == "PLACE"]
    for ui in sorted(free):
        ux, uy = units[ui]
        dist, first = maps[ui]
        inv = inv_of[ui]
        at_shed = (ux, uy) in sheds
        if at_shed:
            if unfed > 0 and inv.get("WHEAT", 0) == 0 and wheat_free > 0:
                take = min(P["feed_pickup"], wheat_free)
                wheat_free -= take
                actions[ui] = ["PICKUP", "WHEAT", take]
                continue
            grabbed = False
            for (pri, jx, jy, op, extra) in need_carry:
                if carry_claim.get(extra, 0) > 0:
                    carry_claim[extra] -= 1
                    actions[ui] = ["PICKUP", extra, 1]
                    grabbed = True
                    break
            if grabbed:
                continue
            actions[ui] = ["DROP"] if inv else ["PASS"]
        else:
            mv = None
            for (tx, ty) in shed_tiles(n):
                if dist[ty][tx] >= 0 and first[ty][tx]:
                    mv = first[ty][tx]
                    break
            actions[ui] = [mv] if mv else ["PASS"]

    _MEM[obs["player"]] = {"t": (day, hour), "assign": new_assign}

    for i in range(n_units):
        if actions[i] is None:
            actions[i] = ["PASS"]

    # ------------------------------------------------------------------ market
    market = []
    add = market.append

    # Opponent modelling. Both farms are public, so we can count the produce the
    # other player is holding on the stalk. The market is shared and prices fall as
    # inventory rises, so whoever sells first gets the high price - if they are
    # sitting on 40 melons we would rather take a mediocre price now than a floored
    # one after they dump. Only their tiles are visible, not their shed, so this
    # under-counts; that is the safe direction to be wrong in.
    threat = {}
    if P["opp_model"] and len(obs["farms"]) > 1:
        for row in obs["farms"][1 - obs["player"]]["tiles"]:
            for t in row:
                if not isinstance(t, dict):
                    continue
                q = t.get("yield_units", 0)
                if q <= 0:
                    continue
                if t.get("kind") == "PLANT":
                    threat[t["crop"]] = threat.get(t["crop"], 0) + q
                elif "animal" in t:
                    pr = ANIMALS[t["animal"]]["product"]
                    threat[pr] = threat.get(pr, 0) + q

    # 1. SELL FIRST - orders resolve in list order, so this funds the buys below
    shed_total = sum(shed.values())
    sellable = [(prices.get(it, 0) * shed.get(it, 0), it) for it in PRODUCTS
                if shed.get(it, 0) > 0]
    sellable.sort(reverse=True)
    # The wheat we hold back must be >= the wheat we top up to, otherwise we sell
    # feed on one turn and buy it straight back on the next (an earlier build
    # churned 2,263 wheat through the market for nothing).
    livestock_now = n_animals + sum(have_animal.values())
    feed_target = livestock_now * P["wheat_days_buffer"] + 4 if livestock_now else 0
    feed_keep = 0 if endgame else min(45, feed_target + 6)
    tight = shed_total >= 70          # close to the cap: clear space at any price
    slots = 9 if tight else 7
    for _, item in sellable:
        if len(market) >= slots:
            break
        have = shed.get(item, 0)
        if item == "WHEAT":
            have = max(0, have - feed_keep)
        elif item == "FERTILIZER":
            # keep back only what we can actually spread; the rest is dead weight
            # in a 100-item shed that silently destroys the overflow
            have = max(0, have - (0 if endgame else P["fert_keep"]))
        if have <= 0:
            continue
        if endgame:
            add(["SELL", item, have])
            money += have * prices.get(item, 0)
            continue
        # CRASH HOLD: refuse to sell into a price the clone pack has floored.
        # Only while there is still time to recover, only if the shed is not
        # about to overflow (overflow is destroyed, so a full shed beats any
        # price theory), and never for wheat, which is feed rather than produce.
        if P["hold_crash"] and not tight and item != "WHEAT" and day <= P["hold_until_day"]:
            pk = pmax.get(item, 0)
            if pk > 0 and prices.get(item, 0) < P["hold_ratio"] * pk:
                continue
        ff, mp = P["sell_floor_frac"], P["sell_min_price"].get(item, 10)
        if threat.get(item, 0) >= P["threat_units"]:
            ff *= P["threat_relax"]          # undercut them rather than be undercut
            mp *= P["threat_relax"]
        qty = plan_sale(item, have, mkt_inv.get(item, MARKET_I0), ff, mp)
        if tight:
            qty = have                # never let production be destroyed by overflow
        if qty > 0:
            add(["SELL", item, qty])
            money += qty * prices.get(item, 0)

    if endgame:
        return {"farmer": actions[0], "hands": actions[1:], "market": market[:10]}

    # 2. hire early - hands are the cheapest thing in the game and they multiply
    #    everything else, so they are funded before any expensive seed
    n_extra = len(me["unlocked_quadrants"]) - 1
    if hour <= 1 and len(market) < 10:
        cap = P["hire_max"] if n_extra >= 1 else P["hire_early_max"]
        budget = money * P["hire_cash_frac"]
        h, spent = me["hires_today"], 0
        while h < cap and len(market) < 10:
            c = _fib(h)
            if spent + c > budget:
                break
            add(["HIRE"])
            spent += c
            h += 1
        money -= spent

    # 3. land - only worth buying if we have the hands to actually work it.
    #    Unworked land is not free: it grows weeds and spreads our units thin.
    if n_extra < 3 and len(market) < 10:
        open_now = sum(1 for yy in range(n) for xx in range(n) if tiles[yy][xx] != "LOCKED")
        if (day >= P["land%d_day" % (n_extra + 1)]
                and money >= P["land%d_cash" % (n_extra + 1)]
                and crop_budget >= P["land_labour_frac"] * open_now):
            add(["BUY_LAND"])
            money -= LAND_PRICES[n_extra]

    # 4. seeds, cheapest-and-most-urgent first (melon is time-critical: three
    #    10-day cycles only fit if the first one goes in on day 0)
    want_s = {}
    for (x, y), role in roles.items():
        if tiles[y][x] is not None:
            continue
        if role in ANIMALS:
            crop = None if have_animal.get(role, 0) > 0 else "WHEAT"
        else:
            crop = role if role in CROPS else "WHEAT"
            if not may_plant(x, y):
                continue
            if crop == "STRAWBERRY" and (day < P["straw_start_day"] or money < P["straw_cash"]):
                crop = "WHEAT"
        if not crop:
            continue
        cd = CROPS[crop]
        horizon = cd["max_yield_day"] if not cd["ongoing"] else cd["first_yield_day"]
        if day + horizon <= last_day:
            want_s[crop] = want_s.get(crop, 0) + 1
    seed_order = {"MELON": 0, "WHEAT": 1, "CARROT": 2, "TOMATO": 3, "STRAWBERRY": 4}
    for crop in sorted(want_s, key=lambda c: seed_order.get(c, 9)):
        if len(market) >= 9:
            break
        need = want_s[crop] - seeds.get(crop, 0)
        cost = CROPS[crop]["seed"]
        if need > 0 and money - P["seed_reserve"] >= cost:
            buy = min(need, int((money - P["seed_reserve"]) // cost))
            if buy > 0:
                add(["BUY_SEED", crop, buy])
                money -= buy * cost

    # 5. feed wheat BEFORE buying animals, so a new animal always has food waiting
    livestock = livestock_now
    if livestock > 0 and len(market) < 10:
        target = feed_target
        have = shed.get("WHEAT", 0)
        wp = market_price("WHEAT", mkt_inv.get("WHEAT", MARKET_I0) - 1)
        if have < target and wp <= P["wheat_buy_max_price"]:
            buy = min(target - have, int(max(0, money - 100) // max(1, wp)))
            if buy > 0:
                add(["BUY_PRODUCT", "WHEAT", buy])
                money -= buy * wp
                shed["WHEAT"] = have + buy

    # 6. animals - the highest-value asset in the game once CARE is applied.
    #    Reserve covers the feed bill for the animals we already own.
    if P["animal_start_day"] <= day <= P["animal_last_day"]:
        # Count against the TARGET headcount, not against empty role tiles.
        #
        # `assign_roles` ranks *unlocked* tiles by distance to the shed, so every
        # BUY_LAND reshuffles which squares are animal squares. Animals already
        # placed then sit on tiles that are no longer animal-role, the newly
        # promoted role tiles read as empty, and we buy replacements for livestock
        # we already own. Measured on the shipping config: intended 5 cows + 6
        # sheep, actually fielded 6 + 7; with geese enabled it ran to 7 geese from
        # n_goose=4, and a coop sat empty from day 16 to the end.
        if not P["animal_target_mode"]:
            want_a = {}
            for (x, y), role in roles.items():
                if role not in ANIMALS:
                    continue
                t = tiles[y][x]
                if t is None or (isinstance(t, dict)
                                 and t.get("kind") == ANIMALS[role]["structure"]
                                 and "animal" not in t):
                    want_a[role] = want_a.get(role, 0) + 1
        placed = {a: 0 for a in ANIMALS}
        for row in tiles:
            for t in row:
                if isinstance(t, dict) and "animal" in t:
                    placed[t["animal"]] = placed.get(t["animal"], 0) + 1
        target = {"COW": int(P["n_cow"]), "SHEEP": int(P["n_sheep"]),
                  "GOOSE": int(P["n_goose"])}
        if P["animal_target_mode"]:
            want_a = {a: max(0, target.get(a, 0) - placed.get(a, 0)) for a in ANIMALS}
        reserve = P["animal_reserve"] + livestock * 25
        for an in ("COW", "SHEEP", "GOOSE"):
            need = want_a.get(an, 0) - have_animal.get(an, 0)
            cost = ANIMALS[an]["cost"]
            if need > 0 and money - reserve >= cost and len(market) < 10:
                buy = min(need, int((money - reserve) // cost))
                if buy > 0:
                    add(["BUY_ANIMAL", an, buy])
                    money -= buy * cost

    return {"farmer": actions[0], "hands": actions[1:], "market": market[:10]}


SAFE = {"farmer": ["PASS"], "hands": [], "market": []}


def _safe(obs, P, mem):
    """A crash on one turn must never forfeit a ladder game - fall back to a
    legal no-op and keep playing."""
    try:
        return _act(obs, P, mem)
    except Exception:
        try:
            n_hands = len(obs["farms"][obs["player"]]["hands"])
        except Exception:
            n_hands = 0
        return {"farmer": ["PASS"], "hands": [["PASS"]] * n_hands, "market": []}


def make_agent(params=None):
    """Build an independent agent closure - lets two parameter sets play each other."""
    P = dict(PARAMS)
    if params:
        P.update(params)
    mem = {}
    return lambda obs, config=None: _safe(obs, P, mem)


_DEFAULT_MEM = {}


def agent(obs, config=None):
    return _safe(obs, PARAMS, _DEFAULT_MEM)

# Sanity-check the submission the way the grader will: import it, run a real episode.
try:
    from kaggle_environments import make
    env = make("kaggriculture", debug=True)
    env.run(["main.py", "main.py"])          # self-play is the validation episode
    banks = [s.observation.farms[i]["money"] for i, s in enumerate(env.state)] \
        if hasattr(env.state[0].observation, "farms") else None
    statuses = [s.status for s in env.state]
    print("episode finished. agent statuses:", statuses)
    print("final banks:", [f["money"] for f in env.state[0].observation["farms"]])
except Exception as e:
    print("could not run here ({}: {}).".format(type(e).__name__, e))
    print("On Kaggle with the competition environment available this plays a full episode.")