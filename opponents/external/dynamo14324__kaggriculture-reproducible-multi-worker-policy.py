"""Capacity-first Kaggriculture policy.

This original agent uses only the current observation.  Its strategy is a staged
farm: early melons/wheat for liquidity, then a cow/sheep herd on three
quadrants, a small strawberry block, daily animal care, and price-aware
small-batch selling.  It is intentionally self-contained for Kaggle submission.
"""
from __future__ import annotations

from collections import Counter

# (x, y, desired animal), chosen to keep the early herd close to the shed.
ANIMAL_PLAN = [
    (3, 4, "SHEEP"), (4, 3, "SHEEP"), (2, 4, "SHEEP"), (4, 2, "SHEEP"), (3, 3, "COW"),
    (5, 4, "COW"), (5, 3, "COW"), (6, 4, "COW"), (6, 3, "COW"), (7, 4, "COW"),
    (4, 5, "COW"), (3, 5, "COW"), (4, 6, "COW"),
]
CROP_PLAN = [
    (0, 0, "MELON"), (1, 0, "MELON"), (2, 0, "MELON"), (0, 1, "MELON"), (1, 1, "MELON"),
    (2, 1, "WHEAT"), (3, 1, "WHEAT"), (4, 1, "WHEAT"), (0, 2, "WHEAT"), (1, 2, "WHEAT"),
    (2, 2, "STRAWBERRY"), (0, 3, "STRAWBERRY"), (1, 3, "STRAWBERRY"),
    (2, 3, "STRAWBERRY"), (0, 4, "STRAWBERRY"), (1, 4, "STRAWBERRY"),
]
SHED_TILES = {(4, 4), (5, 4), (4, 5), (5, 5)}
PREMIUM_FLOORS = {"FERTILIZER": 45, "MELON": 110, "MILK": 85, "WOOL": 105, "STRAWBERRY": 65}
BATCH = {"FERTILIZER": 5, "MELON": 7, "MILK": 7, "WOOL": 8, "STRAWBERRY": 8, "WHEAT": 8}

# Kept as module constants so local ablations can alter only capital allocation
# while retaining exactly the same observation-driven field policy.
INITIAL_MELON_SEEDS = 5
INITIAL_WHEAT_SEEDS = 5
INITIAL_COWS = 1
INITIAL_SHEEP = 3
INITIAL_WHEAT_PRODUCT = 10
STRAWBERRY_PURCHASE_DAYS = (3, 4)
# Selling at hour 0 competes with hires for the 10-order cap.  Controlled
# isolated validation shows hour 1 liquidation is more robust and higher mean.
SELL_HOUR = 1


def _tile(obs, pos):
    x, y = pos
    tiles = obs["farms"][obs["player"]]["tiles"]
    if 0 <= y < len(tiles) and 0 <= x < len(tiles[y]):
        return tiles[y][x]
    return "LOCKED"


def _move(pos, target):
    x, y = pos
    tx, ty = target
    if x < tx:
        return ["EAST"]
    if x > tx:
        return ["WEST"]
    if y < ty:
        return ["SOUTH"]
    if y > ty:
        return ["NORTH"]
    return ["PASS"]


def _distance(a, b):
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def _at_shed(pos):
    return tuple(pos) in SHED_TILES


def _inventory_count(inventory, item):
    if not isinstance(inventory, dict):
        return 0
    return int(inventory.get(item, 0) or 0)


def _visible_counts(obs):
    me = obs["farms"][obs["player"]]
    animals, crops = Counter(), Counter()
    for row in me["tiles"]:
        for cell in row:
            if isinstance(cell, dict):
                if cell.get("kind") == "PLANT":
                    crops[cell.get("crop")] += 1
                elif cell.get("animal"):
                    animals[cell.get("animal")] += 1
    return animals, crops


def _quadrant_unlocked(obs, pos):
    x, y = pos
    want = "NW" if x < 5 and y < 5 else "NE" if x >= 5 and y < 5 else "SW" if x < 5 else "SE"
    return want in obs["farms"][obs["player"]].get("unlocked_quadrants", [])


def _plans(obs):
    """Return one best currently-actionable task per tile.

    Each tuple is (priority, position, operation, auxiliary_item).  Critical
    daily survival tasks dominate all expansion tasks.
    """
    me = obs["farms"][obs["player"]]
    private = obs["private"]
    seeds = private.get("seeds", {})
    shed = private.get("shed", {})
    carried = Counter()
    for inventory in private.get("inventories", []) or []:
        if isinstance(inventory, dict):
            carried.update({item: int(qty or 0) for item, qty in inventory.items()})
    tasks = []
    animal_by_pos = {(x, y): kind for x, y, kind in ANIMAL_PLAN}
    crop_by_pos = {(x, y): crop for x, y, crop in CROP_PLAN}

    for y, row in enumerate(me["tiles"]):
        for x, cell in enumerate(row):
            pos = (x, y)
            if cell == "LOCKED":
                continue
            if isinstance(cell, dict) and cell.get("kind") == "WEED":
                tasks.append((740, pos, "DIG", None))
                continue
            if isinstance(cell, dict) and cell.get("kind") == "PLANT":
                # New plants must be watered on their planting day, and all
                # established plants must receive daily service.
                if not cell.get("watered_today", False):
                    urgency = 1100 if int(cell.get("consecutive_unwatered", 0)) >= 1 else 1060
                    tasks.append((urgency, pos, "WATER", None))
                if int(cell.get("yield_units", 0) or 0) > 0:
                    tasks.append((820, pos, "HARVEST", None))
                continue
            if isinstance(cell, dict) and cell.get("kind") in {"COOP", "PASTURE"}:
                animal = cell.get("animal")
                if animal:
                    if not cell.get("fed_today", False):
                        urgency = 1090 if int(cell.get("consecutive_unfed", 0)) >= 1 else 1040
                        tasks.append((urgency, pos, "FEED", "WHEAT"))
                    elif not cell.get("cared_today", False):
                        tasks.append((900, pos, "CARE", None))
                    if cell.get("fertilizer_available", False):
                        tasks.append((780, pos, "COLLECT_FERTILIZER", None))
                    if int(cell.get("yield_units", 0) or 0) > 0:
                        tasks.append((835, pos, "HARVEST", None))
                else:
                    desired = animal_by_pos.get(pos)
                    if desired and (int(shed.get(desired, 0) or 0) > 0 or carried.get(desired, 0) > 0):
                        tasks.append((980, pos, "PLACE", desired))
                continue
            if cell is None:
                if pos in animal_by_pos:
                    tasks.append((960, pos, "BUILD_PASTURE", animal_by_pos[pos]))
                elif pos in crop_by_pos and int(seeds.get(crop_by_pos[pos], 0) or 0) > 0:
                    tasks.append((880, pos, "PLANT", crop_by_pos[pos]))
    return tasks


def _action_for_unit(obs, pos, inventory, tasks, claimed):
    """Choose one task then return exactly one legal-looking field action."""
    candidates = []
    for priority, target, operation, item in tasks:
        key = (target, operation)
        if key in claimed:
            continue
        # A modest travel penalty keeps nearby workers productive while
        # retaining strict precedence for water/feed.
        value = priority - 13 * _distance(pos, target)
        candidates.append((value, priority, target, operation, item, key))
    if not candidates:
        return ["PASS"]
    _, _, target, operation, item, key = max(candidates, key=lambda r: r[0])
    claimed.add(key)

    # Feed and animal placement require an inventory pickup before travel.
    if operation == "FEED" and _inventory_count(inventory, "WHEAT") <= 0:
        if _at_shed(pos):
            return ["PICKUP", "WHEAT", 5]
        return _move(pos, (4, 4))
    if operation == "PLACE" and _inventory_count(inventory, item) <= 0:
        if _at_shed(pos):
            return ["PICKUP", item, 1]
        return _move(pos, (4, 4))

    if tuple(pos) == target:
        if operation == "PLACE":
            return ["PLACE", item]
        if operation == "PLANT":
            return ["PLANT", item]
        return [operation]
    return _move(pos, target)


def _desired_hires(day):
    if day <= 2:
        return 4
    if day <= 4:
        return 5
    if day == 5:
        return 7
    if day == 6:
        return 8
    return 10


def _market_actions(obs, animal_counts, crop_counts):
    me = obs["farms"][obs["player"]]
    private = obs["private"]
    shed = private.get("shed", {})
    inventories = private.get("inventories", [])
    day, hour = int(obs["day"]), int(obs["hour"])
    money = float(me.get("money", 0) or 0)
    orders = []
    sale_orders = []

    # Controlled liquidation: one small order per product per turn and only
    # above a floor protects against self-inflicted premium-goods gluts.
    available_wheat = int(shed.get("WHEAT", 0) or 0) + sum(_inventory_count(v, "WHEAT") for v in inventories)
    live_animals = sum(animal_counts.values())
    for item in ("FERTILIZER", "WOOL", "MILK", "MELON", "STRAWBERRY"):
        qty = int(shed.get(item, 0) or 0)
        if qty and int(obs["market"]["prices"].get(item, 0) or 0) >= PREMIUM_FLOORS[item]:
            sale_orders.append(["SELL", item, min(BATCH[item], qty)])
    if available_wheat > max(14, live_animals * 2 + 4) and int(obs["market"]["prices"].get("WHEAT", 0) or 0) >= 19:
        sale_orders.append(["SELL", "WHEAT", min(BATCH["WHEAT"], available_wheat - max(14, live_animals * 2 + 4))])

    # Sale timing is a deliberately isolated experimental lever. When sales
    # move to hour 1, hour 0 can devote its full order budget to expansion and
    # hires, after which the same controlled batches are offered.
    if hour != 0:
        if hour != SELL_HOUR:
            return []
        # Terminal bank, not inventory, decides the match.  Once only two days
        # remain, preserve no premium product beyond this fixed horizon: sell
        # the observed shed quantity in a single ordered transaction per item.
        # Wheat remains reserved as an operating input for the daily feed loop.
        if day >= 28:
            terminal_orders = []
            for item in ("FERTILIZER", "WOOL", "MILK", "MELON", "STRAWBERRY"):
                qty = int(shed.get(item, 0) or 0)
                if qty > 0:
                    terminal_orders.append(["SELL", item, qty])
            if terminal_orders:
                return terminal_orders[:10]
        return sale_orders[:10]

    # Day-zero capital allocation mirrors only the high-level asset mix: it is
    # not a replayed trace. Purchases are intentionally bounded to remain valid
    # if a price or previous sale differs.
    if day == 0:
        orders.extend([
            ["BUY_SEED", "MELON", INITIAL_MELON_SEEDS],
            ["BUY_SEED", "WHEAT", INITIAL_WHEAT_SEEDS],
            ["BUY_ANIMAL", "COW", INITIAL_COWS],
            ["BUY_ANIMAL", "SHEEP", INITIAL_SHEEP],
            ["BUY_PRODUCT", "WHEAT", INITIAL_WHEAT_PRODUCT],
        ])
    else:
        if day in STRAWBERRY_PURCHASE_DAYS and crop_counts.get("STRAWBERRY", 0) + int(private.get("seeds", {}).get("STRAWBERRY", 0) or 0) < 6:
            orders.append(["BUY_SEED", "STRAWBERRY", 3])
        # Buy the first two additional quadrants as soon as the current cash
        # balance can fund them with a modest feed/worker reserve.  Using the
        # observed unlocked-count avoids missing expansion when early sales
        # arrive a day later than expected.
        unlocked = len(me.get("unlocked_quadrants", []) or [])
        land_cost = (1000, 2000, 4000)[unlocked - 1] if 1 <= unlocked <= 3 else None
        if day >= 6 and unlocked < 3 and land_cost is not None and money >= land_cost + 400:
            orders.append(["BUY_LAND"])
        # Purchase cows progressively, rather than committing all working
        # capital before structures, feed, and hand capacity exist.
        carried_cows = sum(_inventory_count(v, "COW") for v in inventories)
        total_cows = animal_counts.get("COW", 0) + int(shed.get("COW", 0) or 0) + carried_cows
        if day >= 5 and day <= 17 and total_cows < 9 and money >= 650:
            orders.append(["BUY_ANIMAL", "COW", 1])
        carried_sheep = sum(_inventory_count(v, "SHEEP") for v in inventories)
        total_sheep = animal_counts.get("SHEEP", 0) + int(shed.get("SHEEP", 0) or 0) + carried_sheep
        if day >= 12 and day <= 17 and total_sheep < 4 and money >= 750:
            orders.append(["BUY_ANIMAL", "SHEEP", 1])
        total_wheat = available_wheat
        early_feed_need = live_animals + 2
        if day <= 2 and live_animals and total_wheat < early_feed_need:
            wheat_price = int(obs["market"]["prices"].get("WHEAT", 0) or 0)
            early_qty = early_feed_need - total_wheat
            if wheat_price > 0 and money >= early_qty * wheat_price + 20:
                orders.append(["BUY_PRODUCT", "WHEAT", early_qty])
        elif day >= 3 and total_wheat < max(10, live_animals + 4) and money >= 500:
            orders.append(["BUY_PRODUCT", "WHEAT", max(6, live_animals + 4)])

    # Hire capacity after essential strategic orders. Failures are harmless
    # no-ops if cash is temporarily unavailable.
    current_hires = int(me.get("hires_today", 0) or 0)
    for _ in range(max(0, _desired_hires(day) - current_hires)):
        if len(orders) >= 10:
            break
        orders.append(["HIRE"])
    if SELL_HOUR == 0:
        return (sale_orders + orders)[:10]
    return orders[:10]


def agent(obs):
    """Kaggle competition entry point."""
    me = obs["farms"][obs["player"]]
    animals, crops = _visible_counts(obs)
    tasks = _plans(obs)
    positions = [me["farmer"]] + list(me.get("hands", []) or [])
    inventories = list(obs["private"].get("inventories", []) or [])
    while len(inventories) < len(positions):
        inventories.append({})

    claimed = set()
    actions = [_action_for_unit(obs, positions[i], inventories[i], tasks, claimed) for i in range(len(positions))]
    return {
        "farmer": actions[0] if actions else ["PASS"],
        "hands": actions[1:],
        "market": _market_actions(obs, animals, crops),
    }


from kaggle_environments import make

EPISODE_STEPS = 720


def run_match(opponent="starter", seed=606):
    env = make(
        "kaggriculture",
        configuration={"episodeSteps": EPISODE_STEPS, "seed": seed},
        debug=True,
    )
    env.run([agent, opponent])
    final = env.steps[-1]
    return {
        "seed": seed,
        "ours": float(final[0].reward or 0.0),
        "opponent": float(final[1].reward or 0.0),
        "margin": float((final[0].reward or 0.0) - (final[1].reward or 0.0)),
        "our_status": str(final[0].status),
        "opponent_status": str(final[1].status),
    }

run_match()


# A compact, reproducible seed sweep. Keep the opponent, simulator version,
# and policy revision fixed when comparing alternatives.
SEEDS = [606, 707, 808, 909, 1001, 1102, 1203, 1304, 1405, 1506]
results = [run_match("starter", seed) for seed in SEEDS]
for row in results:
    print(row)

mean_final_bank = sum(row["ours"] for row in results) / len(results)
win_count = sum(row["margin"] > 0 for row in results)
all_done = all(row["our_status"] == "DONE" for row in results)
{"mean_final_bank": mean_final_bank, "wins": win_count, "games": len(results), "all_done": all_done}
