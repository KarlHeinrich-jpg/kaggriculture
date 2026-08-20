# %%capture
# !pip install --upgrade "kaggle-environments>=1.32.2"

from kaggle_environments import make

env = make("kaggriculture", debug=True)
print(f"Environment: {env.name} v{env.version}")
print(f"Players: {env.specification.agents}")
print(f"Max steps: {env.configuration.episodeSteps}")

# Run a quick game to see what the observation looks like
env = make("kaggriculture", debug=True)
env.run(["random", "random"])

# Peek at the initial observation
obs = env.steps[1][0].observation  # step 1 = first action step
items = obs.market.prices.keys()
print(f"Player: {obs.player}")
print(f"Player {obs.player}'s Unlocked Farm Areas: {obs.farms[obs.player].unlocked_quadrants}")
for i in items:
    print(f"{i} Price: {obs.market.prices[i]}")

from kaggle_environments.envs.kaggriculture.kaggriculture import CROPS, ANIMALS

CROP_ORDER = ["MELON", "CARROT", "WHEAT", "TOMATO", "STRAWBERRY"]
BASE_PRICE = {
    "WHEAT": 25, "CARROT": 35, "TOMATO": 60,
    "STRAWBERRY": 120, "MELON": 250,
    "EGG": 50, "MILK": 160, "WOOL": 200, "FERTILIZER": 100,
}


def _step_toward(fx, fy, tx, ty):
    if fx < tx:
        return "EAST"
    if fx > tx:
        return "WEST"
    if fy < ty:
        return "SOUTH"
    if fy > ty:
        return "NORTH"
    return None


def _manhattan(a, b):
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def _tasks(obs, farm, private):
    tasks = []
    board = farm["tiles"]
    day = obs.get("day", 0)
    seeds = private.get("seeds", {})

    # Survival and production tasks.
    for y, row in enumerate(board):
        for x, tile in enumerate(row):
            if not isinstance(tile, dict):
                continue

            if tile.get("kind") == "WEED":
                tasks.append((80, x, y, "DIG"))

            elif tile.get("kind") == "PLANT":
                crop = tile.get("crop")

                # Fertilize high-value crops when a unit is carrying fertilizer.
                if crop in ("MELON", "STRAWBERRY", "TOMATO") and \
                        tile.get("fertilized_until_day", -1) < day:
                    tasks.append((86, x, y, "FERTILIZE"))

                # Watering is critical because two consecutive missed days
                # turn a plant into a weed.
                if not tile.get("watered_today"):
                    priority = 100 if tile.get("consecutive_unwatered", 0) >= 1 else 75
                    tasks.append((priority, x, y, "WATER"))

                # Harvest as soon as a mature yield exists.
                if tile.get("yield_units", 0) > 0 and \
                        day - tile.get("planted_day", day) >= CROPS[crop]["first_yield_day"]:
                    tasks.append((95, x, y, "HARVEST"))

            elif "animal" in tile:
                # Feeding is the highest animal priority.
                if not tile.get("fed_today"):
                    tasks.append((120, x, y, "FEED"))

                # Care + feeding creates a production bonus.
                if not tile.get("cared_today"):
                    tasks.append((70, x, y, "CARE"))

                if tile.get("fertilizer_available"):
                    tasks.append((60, x, y, "COLLECT_FERTILIZER"))

            elif tile.get("kind") in ("COOP", "PASTURE") and "animal" not in tile:
                # If an animal is waiting in the shed, place it in a matching
                # structure. The actual PLACE task is also generated below
                # for units that already carry the animal.
                for animal in ("GOOSE", "COW", "SHEEP"):
                    if private.get("shed", {}).get(animal, 0) > 0:
                        if ANIMALS[animal]["structure"] == tile.get("kind"):
                            tasks.append((90, x, y, ("PLACE", animal)))
                            break

    preferred = (
        "MELON"
        if seeds.get("MELON", 0)
        else next((c for c in CROP_ORDER if seeds.get(c, 0)), None)
    )

    wheat_on_field = sum(
        1
        for row in board
        for tile in row
        if isinstance(tile, dict)
        and tile.get("kind") == "PLANT"
        and tile.get("crop") == "WHEAT"
    )

    goose_total = sum(
        1
        for row in board
        for tile in row
        if isinstance(tile, dict) and tile.get("animal") == "GOOSE"
    ) + private.get("shed", {}).get("GOOSE", 0)

    # Build exactly one required animal structure at a time.
    waiting_structure = None
    for animal in ("GOOSE", "COW", "SHEEP"):
        if private.get("shed", {}).get(animal, 0) > 0:
            waiting_structure = ANIMALS[animal]["structure"]
            break

    empty_tiles = [
        (x, y)
        for y, row in enumerate(board)
        for x, tile in enumerate(row)
        if tile is None
    ]

    if waiting_structure and empty_tiles:
        x, y = empty_tiles[0]
        operation = "BUILD_COOP" if waiting_structure == "COOP" else "BUILD_PASTURE"
        tasks.append((65, x, y, operation))
    else:
        # Keep a small wheat area for animal feed, then use the remaining
        # production capacity for melons.
        for x, y in empty_tiles:
            if goose_total and wheat_on_field < 4 and seeds.get("WHEAT", 0) > 0:
                tasks.append((55, x, y, ("PLANT", "WHEAT")))
                wheat_on_field += 1
            elif preferred:
                tasks.append((45, x, y, ("PLANT", preferred)))

    # All units spawn near the shed each day. Use those access tiles to
    # collect fertilizer, wheat, or animals from the shed.
    half = len(board) // 2
    shed_access = {
        (half - 1, half - 1),
        (half, half - 1),
        (half - 1, half),
        (half, half),
    }

    animal_on_farm = any(
        isinstance(tile, dict) and "animal" in tile
        for row in board
        for tile in row
    )

    if animal_on_farm and private.get("shed", {}).get("WHEAT", 0) > 0:
        for x, y in shed_access:
            if 0 <= x < len(board) and 0 <= y < len(board):
                tasks.append((75, x, y, ("PICKUP", "WHEAT", 1)))

    if private.get("shed", {}).get("FERTILIZER", 0) > 0:
        for x, y in shed_access:
            if 0 <= x < len(board) and 0 <= y < len(board):
                tasks.append((58, x, y, ("PICKUP", "FERTILIZER", 1)))

    for animal in ("GOOSE", "COW", "SHEEP"):
        if private.get("shed", {}).get(animal, 0) > 0:
            for x, y in shed_access:
                if 0 <= x < len(board) and 0 <= y < len(board):
                    tasks.append((57, x, y, ("PICKUP", animal, 1)))

    return tasks


def agent(obs):
    farms = obs.get("farms", [])
    player = obs.get("player", 0)
    private = obs.get("private", {}) or {}

    if not farms or player >= len(farms):
        return {"farmer": ["PASS"], "hands": [], "market": []}

    farm = farms[player]
    money = farm.get("money", 0)
    day = obs.get("day", 0)
    board = farm["tiles"]

    seeds = private.get("seeds", {}) or {}
    shed = private.get("shed", {}) or {}
    market_prices = (obs.get("market", {}) or {}).get("prices", {}) or {}

    # Market orders are processed in list order. Sell first so the proceeds
    # can fund hiring, land expansion, and seed purchases in the same turn.
    market = []

    final = day >= 27

    # Small sales reduce market-price crashes. In the final days we liquidate
    # more aggressively because only banked money matters at the end.
    for item in (
        "MELON", "STRAWBERRY", "TOMATO", "MILK",
        "WOOL", "EGG", "CARROT", "WHEAT"
    ):
        qty = shed.get(item, 0)
        if qty <= 0:
            continue

        price = market_prices.get(item, BASE_PRICE.get(item, 0))
        threshold = BASE_PRICE.get(item, price) * (
            0.88 if item == "MELON" else 0.82
        )

        if final or price >= threshold:
            market.append([
                "SELL",
                item,
                min(qty, 10 if final else 3),
            ])

        if len(market) >= 10:
            break

    # Farm hands are intentionally cheap early in the day. More hands allow
    # watering/feed/harvest work to happen in parallel.
    n_hands = len(farm.get("hands", []))
    target_hands = 6 if money >= 1200 else 4 if money >= 600 else 2

    if n_hands < target_hands:
        for _ in range(min(2, target_hands - n_hands)):
            market.append(["HIRE"])
            if len(market) >= 10:
                break

    # Buy the first expansion when there is still a cash buffer.
    if (
        len(market) < 10
        and len(farm.get("unlocked_quadrants", [])) == 1
        and money >= 1800
        and day < 18
    ):
        market.append(["BUY_LAND"])

    # Geese provide early recurring cash flow and require wheat feed.
    animals_on_farm = [
        tile.get("animal")
        for row in board
        for tile in row
        if isinstance(tile, dict) and "animal" in tile
    ]

    geese_total = (
        animals_on_farm.count("GOOSE") + shed.get("GOOSE", 0)
    )

    if (
        len(market) < 10
        and day >= 2
        and money >= 1000
        and geese_total < 2
    ):
        market.append(["BUY_ANIMAL", "GOOSE", 1])

    # Keep a small wheat reserve for animal feed.
    wheat_on_field = sum(
        1
        for row in board
        for tile in row
        if isinstance(tile, dict)
        and tile.get("kind") == "PLANT"
        and tile.get("crop") == "WHEAT"
    )

    if (
        len(market) < 10
        and geese_total
        and wheat_on_field + seeds.get("WHEAT", 0) < 4
    ):
        buy_n = min(
            6,
            4 - wheat_on_field - seeds.get("WHEAT", 0)
        )
        if buy_n > 0:
            market.append(["BUY_SEED", "WHEAT", buy_n])

    # Melon is the main profit crop in the reference environment.
    melon_on_field = sum(
        1
        for row in board
        for tile in row
        if isinstance(tile, dict)
        and tile.get("kind") == "PLANT"
        and tile.get("crop") == "MELON"
    )

    target_melon = min(12, 8 + max(0, n_hands - 2))

    if len(market) < 10:
        required = target_melon - melon_on_field - seeds.get("MELON", 0)
        if required > 0:
            market.append(["BUY_SEED", "MELON", min(10, required)])

    # Build a common task pool, then let the main farmer and each hired hand
    # claim different targets in the same turn.
    tasks = _tasks(obs, farm, private)
    claimed = set()

    def choose_action(pos, inventory):
        candidates = list(tasks)

        # A unit carrying an animal should go to a matching structure.
        for animal in ("GOOSE", "COW", "SHEEP"):
            if inventory.get(animal, 0) <= 0:
                continue

            structure = ANIMALS[animal]["structure"]

            for y, row in enumerate(board):
                for x, tile in enumerate(row):
                    if (
                        isinstance(tile, dict)
                        and tile.get("kind") == structure
                        and "animal" not in tile
                    ):
                        candidates.append((92, x, y, ("PLACE", animal)))

        filtered = []

        for priority, x, y, action in candidates:
            if (x, y) in claimed:
                continue

            if action == "FERTILIZE" and inventory.get("FERTILIZER", 0) <= 0:
                continue

            if (
                isinstance(action, tuple)
                and action[0] == "PICKUP"
                and inventory.get(action[1], 0) > 0
            ):
                continue

            score = priority - _manhattan(pos, (x, y)) * 2
            filtered.append((score, priority, x, y, action))

        # If a unit is already carrying fertilizer, spend it on a high-value
        # crop before doing lower-value work.
        if inventory.get("FERTILIZER", 0) > 0:
            fertilizer_tasks = [
                c for c in filtered if c[-1] == "FERTILIZE"
            ]
            if fertilizer_tasks:
                filtered = fertilizer_tasks

        if not filtered:
            return ["PASS"]

        filtered.sort(reverse=True)
        _, _, target_x, target_y, action = filtered[0]

        if (target_x, target_y) == tuple(pos):
            claimed.add((target_x, target_y))

            if isinstance(action, tuple):
                return list(action)

            return [action]

        step = _step_toward(
            pos[0], pos[1], target_x, target_y
        )

        return [step] if step else ["PASS"]

    positions = [farm["farmer"]] + list(farm.get("hands", []))
    inventories = private.get("inventories", []) or []

    actions = []

    for idx, pos in enumerate(positions):
        inventory = inventories[idx] if idx < len(inventories) else {}
        actions.append(choose_action(pos, inventory))

    return {
        "farmer": actions[0],
        "hands": actions[1:],
        "market": market[:10],
    }

from kaggle_environments import make

env = make("kaggriculture", debug=True)

env.run([agent, "random"])

for i, s in enumerate(env.steps[-1]):
    print(f"Player {i}: reward={s.reward}, status={s.status}")