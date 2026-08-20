# --- Load the shipped engine. Fail LOUDLY rather than quietly guessing. ---
import sys, math, inspect, subprocess

def _version():
    try:
        import importlib.metadata as _md
        return _md.version("kaggle-environments")
    except Exception:
        return "unknown"

def _load():
    for mod in [m for m in list(sys.modules) if m.startswith("kaggle_environments")]:
        del sys.modules[mod]
    from kaggle_environments.envs.kaggriculture import kaggriculture as K
    return K

# The Kaggle image ships kaggle-environments 1.29.3, which is PRE-REBALANCE: it still has
# the old town-centre demand schedule. Every number below would silently describe a game
# that no longer exists, so upgrade first and say so out loud.
BEFORE = _version()
subprocess.run([sys.executable, "-m", "pip", "install", "-q", "-U",
                "kaggle-environments"], check=False)
try:
    K = _load()
except Exception as e:
    sys.exit(f"FATAL: could not import the kaggriculture engine: {e!r}")
if BEFORE != _version():
    print(f"upgraded kaggle-environments {BEFORE} -> {_version()}")

for required in ("ANIMALS", "MARKET_PARAMS", "market_price",
                 "_new_animal", "_daily_refresh_animals"):
    if not hasattr(K, required):
        sys.exit(f"FATAL: engine is missing {required!r} — this notebook's "
                 f"assumptions do not hold on this version. Stopping.")

print(f"kaggle-environments == {_version()}")
print("The prose in this notebook was written against 1.32.6.")

# The prose quotes specific constants. If the engine has moved under us, say so
# in capital letters instead of letting the text and the tables disagree.
EXPECTED = {
    ("ANIMALS", "GOOSE", "interval"): 1, ("ANIMALS", "COW", "interval"): 2,
    ("ANIMALS", "SHEEP", "interval"): 3,
    ("MARKET_PARAMS", "EGG", "base"): 50, ("MARKET_PARAMS", "MILK", "base"): 160,
    ("MARKET_PARAMS", "WOOL", "base"): 200, ("MARKET_PARAMS", "WHEAT", "base"): 25,
}
drift = []
for (table, key, field), want in EXPECTED.items():
    got = getattr(K, table)[key].get(field)
    if got != want:
        drift.append(f"  {table}[{key}][{field}]: prose says {want}, engine says {got}")
if drift:
    print("\n*** WARNING: THE ENGINE HAS CHANGED SINCE THIS WAS WRITTEN ***")
    print("\n".join(drift))
    print("Trust the computed tables below, NOT the prose numbers.")
else:
    print("Constant check: OK — every number quoted in the prose still matches the engine.")


src = inspect.getsource(K._daily_refresh_animals)
# Print the production/care block itself — the ordering inside it is the finding.
marker = "a = ANIMALS[tile[\"animal\"]]"
print(src[src.index(marker):] if marker in src else src)


for name, a in K.ANIMALS.items():
    print(f"{name:6s} interval={a['interval']}  cost=${a['cost']:<4d} "
          f"first_yield_day={a['first_yield_day']:<2d} max_held={a['max_held']}  "
          f"product={a['product']:5s}  ->  steady state {1 + a['interval']} units/cycle")


SEASON_DAYS = 30       # episodeSteps 720 / turnsPerDay 24

def run_animal(animal, care=True, season=SEASON_DAYS, buy_day=0):
    """Drive the engine's own daily refresh. Returns total units produced."""
    tile = K._new_animal(animal, buy_day)
    farm = {"tiles": [[tile]]}
    produced = 0
    for day in range(buy_day, season):
        tile["fed_today"] = True            # FEED  (costs 1 wheat)
        tile["cared_today"] = bool(care)    # CARE  (free, one action)
        if tile["yield_units"] > 0:         # COLLECT
            produced += tile["yield_units"]
            tile["yield_units"] = 0
        K._daily_refresh_animals(farm, day)
    return produced + tile["yield_units"]

print(f"{'animal':7s} {'w/ CARE':>8s} {'no CARE':>8s} {'multiplier':>11s}")
care_units = {}
for name in K.ANIMALS:
    w, wo = run_animal(name, care=True), run_animal(name, care=False)
    care_units[name] = w
    print(f"{name:7s} {w:8d} {wo:8d} {w / wo:10.2f}x")


import matplotlib.pyplot as plt

names = list(K.ANIMALS)
w  = [run_animal(n, care=True)  for n in names]
wo = [run_animal(n, care=False) for n in names]

fig, ax = plt.subplots(figsize=(7, 3.6))
x = range(len(names))
ax.bar([i - 0.2 for i in x], wo, 0.4, label="fed only", color="#c9ccd1")
ax.bar([i + 0.2 for i in x], w,  0.4, label="fed + CARE", color="#2e7d32")
for i, (a, b) in enumerate(zip(wo, w)):
    ax.text(i + 0.2, b + 1, f"{b/a:.2f}x", ha="center", fontweight="bold")
ax.set_xticks(list(x)); ax.set_xticklabels(names)
ax.set_ylabel("units produced in a 30-day season")
ax.set_title("CARE pays more the slower the animal")
ax.legend(frameon=False); ax.spines[["top", "right"]].set_visible(False)
plt.tight_layout(); plt.show()


WHEAT_BASE = K.MARKET_PARAMS["WHEAT"]["base"]

print(f"feed cost = 1 WHEAT/animal/day = ${WHEAT_BASE}/day\n")
print(f"{'animal':7s} {'product':6s} {'base':>6s} {'units/cycle':>12s} "
      f"{'gross/day':>10s} {'net of feed':>12s}")
for name, a in K.ANIMALS.items():
    base = K.MARKET_PARAMS[a["product"]]["base"]
    per_cycle = 1 + a["interval"]
    gross = per_cycle * base / a["interval"]
    print(f"{name:7s} {a['product']:6s} ${base:5d} {per_cycle:12d} "
          f"${gross:9.2f} ${gross - WHEAT_BASE:11.2f}")


I0 = K.MARKET_I0
print(f"{'dumped':>7s} {'EGG':>6s} {'MILK':>6s} {'WOOL':>6s}")
for n in (0, 25, 50, 100, 200, 400, 800):
    row = "".join(f"{K.market_price(p, I0 + n):6d} " for p in ("EGG", "MILK", "WOOL"))
    print(f"{n:7d} {row}")

print()
for p in ("EGG", "MILK", "WOOL"):
    mp = K.MARKET_PARAMS[p]
    print(f"{p:5s} glut shape={mp['above_func']:6s} target={mp['above_target']:.2f} T={mp['T']}")


UNLOCK_INTERVAL, MAX_SHOPS, TICKS_PER_DAY = 3, 8, 6

def sink_on_day(product, day):
    """Expected units/day the town permanently removes."""
    n = min(MAX_SHOPS, day // UNLOCK_INTERVAL)
    rate = sum(n * (1.0 / len(K.SHOPS)) * (2 if len(ps) == 1 else 1)
               for s, ps in K.SHOPS.items() if product in ps)
    rate *= TICKS_PER_DAY
    return rate + (1.0 if product in K.TOWN_CENTER_PRODUCTS else 0.0)

def realized_revenue(animal, herd, season=SEASON_DAYS, opponent=True):
    """Sell the herd's output day by day into the live price curve. MODEL."""
    a = K.ANIMALS[animal]
    product = a["product"]
    per_animal = care_units[animal]
    start = a["first_yield_day"]
    per_day = per_animal / (season - start) * herd
    inv, total, mine, carry = float(I0), 0.0, 0, 0.0
    share = 2 if opponent else 1
    for day in range(season):
        if day >= start:
            carry += per_day * share
        k, carry = int(carry), carry - int(carry)
        for i in range(k):
            if i % share == 0:                      # our half of the flow
                total += K.market_price(product, int(round(inv)))
                mine += 1
            inv += 1
        inv = max(I0 - 500, inv - sink_on_day(product, day))
    return total, mine

print(f"{'herd':>5s} " + " ".join(f"{a:>14s}" for a in K.ANIMALS))
print(f"{'':5s} " + " ".join(f"{'$/animal':>14s}" for _ in K.ANIMALS))
for herd in (1, 2, 4, 6, 8, 12, 16):
    cells = []
    for animal in K.ANIMALS:
        rev, _ = realized_revenue(animal, herd)
        cells.append(f"{rev / herd:14,.0f}")
    print(f"{herd:5d} " + " ".join(cells))


fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, 3.8))

xs = range(0, 401, 5)
for prod, colour in (("EGG", "#f9a825"), ("MILK", "#1e88e5"), ("WOOL", "#8e24aa")):
    ax1.plot(list(xs), [K.market_price(prod, I0 + n) for n in xs], label=prod, color=colour)
ax1.set_xlabel("units dumped into the market"); ax1.set_ylabel("price ($)")
ax1.set_title("The glut curve: wool falls off a cliff, egg barely moves")
ax1.legend(frameon=False); ax1.spines[["top", "right"]].set_visible(False)

herds = [1, 2, 4, 6, 8, 12, 16]
for animal, colour in (("GOOSE", "#f9a825"), ("COW", "#1e88e5"), ("SHEEP", "#8e24aa")):
    ys = [realized_revenue(animal, h)[0] / h for h in herds]
    ax2.plot(herds, ys, marker="o", label=animal, color=colour)
ax2.set_xlabel("herd size (one species)"); ax2.set_ylabel("revenue per animal ($)")
ax2.set_title("...so the value of the marginal animal collapses  [MODEL]")
ax2.legend(frameon=False); ax2.spines[["top", "right"]].set_visible(False)

plt.tight_layout(); plt.show()


# label -> (overall win %, W, L)  — W/L are DISCORDANT pairs vs baseline, n=288 each.
SWEEP = [
    ("baseline (cows 8, sheep 6, care 0.35)", 19.1, None, None),
    ("care_mult 0.35 -> 0.20  (care less)",   10.1,  4, 30),
    ("target_sheep 6 -> 8",                    8.7,  7, 37),
    ("target_sheep 6 -> 4",                    9.7,  6, 33),
    ("target_cows  8 -> 10",                  12.5,  5, 24),
    ("target_cows  8 -> 6",                   18.4, 17, 19),
]

print(f"{'change':40s} {'win%':>6s} {'W/L':>8s} {'z':>7s}  verdict")
for label, win, W, L in SWEEP:
    if W is None:
        print(f"{label:40s} {win:5.1f}% {'—':>8s} {'—':>7s}")
        continue
    z = (W - L) / math.sqrt(W + L)
    verdict = ("significantly WORSE" if z <= -1.96 else
               "significantly better" if z >= 1.96 else "no detectable effect")
    print(f"{label:40s} {win:5.1f}% {W:3d}/{L:<4d} {z:+7.2f}  {verdict}")


def animal_plan(budget, tiles, season=SEASON_DAYS, verbose=True):
    """Rank single-species herds you can afford. MODEL — see Part 3's assumptions."""
    rows = []
    for animal, a in K.ANIMALS.items():
        max_by_cash = budget // a["cost"]
        herd = int(min(tiles, max_by_cash))
        if herd < 1:
            continue
        rev, units = realized_revenue(animal, herd, season)
        feed = WHEAT_BASE * herd * (season - a["first_yield_day"])
        capital = a["cost"] * herd
        rows.append((rev - feed - capital, animal, herd, rev, units, feed, capital))
    rows.sort(reverse=True)
    if verbose:
        print(f"budget ${budget:,}  tiles {tiles}  season {season}d\n")
        print(f"{'animal':7s} {'herd':>5s} {'units':>7s} {'revenue':>10s} "
              f"{'feed':>8s} {'capital':>8s} {'PROFIT':>10s}")
        for profit, animal, herd, rev, units, feed, capital in rows:
            print(f"{animal:7s} {herd:5d} {units:7.0f} {rev:10,.0f} "
                  f"{feed:8,.0f} {capital:8,.0f} {profit:10,.0f}")
    return rows

animal_plan(budget=3000, tiles=6)
print()
animal_plan(budget=12000, tiles=16)


# %%writefile main.py
"""CARE-first animal husbandry agent.

A deliberately small agent that does one thing: keep a mixed herd fed, cared for and
harvested every single day. It grows no crops and runs no clever market model.
"""

SHED_TILES = [(4, 4), (5, 4), (4, 5), (5, 5)]
HERD = [("COW", 4), ("SHEEP", 3)]          # two species on purpose: two price curves
# NW is the only quadrant unlocked at the start, so every spot must satisfy x<5 and y<5.
# Ordered by walking distance from the shed-access tile (4,4).
PASTURE_SPOTS = [(4, 3), (3, 4), (3, 3), (4, 2), (2, 4), (2, 3), (3, 2), (4, 1)]
PRODUCTS = ("MILK", "WOOL", "EGG", "FERTILIZER")
CARE_ENABLED = True   # flip to False for the ablation


def _step(pos, target):
    x, y = pos
    tx, ty = target
    if x < tx: return "EAST"
    if x > tx: return "WEST"
    if y < ty: return "SOUTH"
    if y > ty: return "NORTH"
    return None


def _dist(a, b):
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def agent(obs):
    me = obs["farms"][obs["player"]]
    priv = obs["private"]
    tiles = me["tiles"]
    shed = priv["shed"]
    money = me["money"]
    invs = priv["inventories"]

    placed = {}
    empty_pastures = []
    animal_tiles = []
    free_spots = []
    for y, row in enumerate(tiles):
        for x, t in enumerate(row):
            if isinstance(t, dict) and "animal" in t:
                placed[t["animal"]] = placed.get(t["animal"], 0) + 1
                animal_tiles.append(((x, y), t))
            elif isinstance(t, dict) and t.get("kind") == "PASTURE":
                empty_pastures.append((x, y))
            elif t is None and (x, y) in PASTURE_SPOTS:
                free_spots.append((x, y))

    n_target = sum(n for _, n in HERD)
    n_structures = len(empty_pastures) + sum(placed.values())
    shed_animals = sum(shed.get(a, 0) for a, _ in HERD)

    # ---------------- market ----------------
    market = []
    carried_wheat = sum(i.get("WHEAT", 0) for i in invs)
    total_wheat = shed.get("WHEAT", 0) + carried_wheat
    n_alive = sum(placed.values())
    # keep roughly three days of feed in stock
    if total_wheat < max(8, n_alive * 3) and money > 600:
        market.append(["BUY_PRODUCT", "WHEAT", 12])

    for animal, target in HERD:
        if placed.get(animal, 0) + shed.get(animal, 0) < target and money > 1400:
            market.append(["BUY_ANIMAL", animal, 1])
            break

    for product in ("MILK", "WOOL"):
        held = shed.get(product, 0)
        if held > 0:
            market.append(["SELL", product, min(held, 4)])   # drip, never dump

    if obs["day"] >= 1 and me["hires_today"] < 3 and money > 2000:
        market.append(["HIRE"])

    # ---------------- workers ----------------
    workers = [tuple(me["farmer"])] + [tuple(p) for p in me["hands"]]
    claimed = set()
    ops = []

    for wi, pos in enumerate(workers):
        inv = invs[wi] if wi < len(invs) else {}
        x, y = pos
        here = tiles[y][x]
        carrying_animal = next((a for a, _ in HERD if inv.get(a, 0) > 0), None)
        job = None

        # --- act where we stand ---
        if isinstance(here, dict) and "animal" in here:
            if here.get("yield_units", 0) > 0:
                job = ["HARVEST"]
            elif not here.get("fed_today") and inv.get("WHEAT", 0) > 0:
                job = ["FEED"]
            elif CARE_ENABLED and not here.get("cared_today"):
                job = ["CARE"]
        elif carrying_animal and isinstance(here, dict) and here.get("kind") == "PASTURE":
            job = ["PLACE", carrying_animal, 1]
        elif here is None and (x, y) in PASTURE_SPOTS and n_structures < n_target:
            job = ["BUILD_PASTURE"]
        elif pos in SHED_TILES:
            if any(inv.get(p, 0) for p in PRODUCTS):
                job = ["DROP"]
            elif not carrying_animal and shed_animals > 0 and empty_pastures:
                for a, _ in HERD:
                    if shed.get(a, 0) > 0:
                        job = ["PICKUP", a, 1]
                        shed[a] -= 1
                        break
            elif inv.get("WHEAT", 0) < 3 and shed.get("WHEAT", 0) > 0:
                job = ["PICKUP", "WHEAT", 4]

        # --- otherwise, go somewhere useful ---
        if job is None:
            target = None
            if carrying_animal and empty_pastures:
                target = min((p for p in empty_pastures if p not in claimed),
                             key=lambda p: _dist(p, pos), default=None)
            if target is None and not carrying_animal and shed_animals > 0 and empty_pastures:
                target = min(SHED_TILES, key=lambda s: _dist(s, pos))
            if target is None and n_structures < n_target and free_spots:
                target = min((s for s in free_spots if s not in claimed),
                             key=lambda s: _dist(s, pos), default=None)
            if target is None and inv.get("WHEAT", 0) == 0 and shed.get("WHEAT", 0) > 0:
                target = min(SHED_TILES, key=lambda s: _dist(s, pos))
            if target is None:
                best, best_score = None, 0.0
                for (ax, ay), t in animal_tiles:
                    if (ax, ay) in claimed:
                        continue
                    score = 0.0
                    if t.get("yield_units", 0) > 0: score += 3
                    if not t.get("fed_today") and inv.get("WHEAT", 0) > 0: score += 2
                    if CARE_ENABLED and not t.get("cared_today"): score += 1
                    score -= 0.1 * _dist((ax, ay), pos)
                    if score > best_score:
                        best, best_score = (ax, ay), score
                target = best
            if target is None and any(inv.get(p, 0) for p in PRODUCTS):
                target = min(SHED_TILES, key=lambda s: _dist(s, pos))
            if target is not None:
                claimed.add(target)
                mv = _step(pos, target)
                job = [mv] if mv else ["PASS"]
            else:
                job = ["PASS"]

        ops.append(job)

    return {"farmer": ops[0], "hands": ops[1:], "market": market[:10]}


import importlib, statistics, sys, os
sys.path.insert(0, os.getcwd())
import main as care_bot
from kaggle_environments import make

SEEDS = list(range(101, 113))

def play(seeds, care):
    care_bot.CARE_ENABLED = care
    banks = []
    for seed in seeds:
        env = make("kaggriculture", configuration={"seed": seed}, debug=False)
        env.run([care_bot.agent, "starter"])
        banks.append(env.state[0].reward)
    return banks

on  = play(SEEDS, True)
off = play(SEEDS, False)

wins = sum(1 for a, b in zip(on, off) if a > b)
losses = sum(1 for a, b in zip(on, off) if a < b)
z = (wins - losses) / math.sqrt(wins + losses) if wins + losses else 0.0

print(f"{'seed':>6s} {'CARE on':>12s} {'CARE off':>12s}")
for s, a, b in zip(SEEDS, on, off):
    print(f"{s:6d} {a:12,.0f} {b:12,.0f}")
print("-" * 34)
print(f"{'mean':>6s} {statistics.mean(on):12,.0f} {statistics.mean(off):12,.0f}")
print(f"\nCARE on wins {wins}/{len(SEEDS)} paired seeds "
      f"(losses {losses}), McNemar z = {z:+.2f}")
print(f"ratio of mean final bank: {statistics.mean(on)/statistics.mean(off):.2f}x")
