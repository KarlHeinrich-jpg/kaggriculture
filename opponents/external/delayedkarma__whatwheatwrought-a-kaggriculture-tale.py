# %%capture
# !pip install --upgrade "kaggle-environments>=1.32.2"

from kaggle_environments import make

def agent(obs):
    obs = dict(obs)
    player = obs["player"]
    farm = obs["farms"][player]
    private = obs["private"]
    
    day = obs["day"]
    hour = obs["hour"]
    fx, fy = farm["farmer"]
    seeds = private["seeds"]
    shed = private["shed"]
    money = farm["money"]
    prices = obs["market"]["prices"]
    hands = farm.get("hands", [])
    unlocked = farm.get("unlocked_quadrants", [])
    hires_today = farm.get("hires_today", 0)
    market = []

    # Sell wheat every turn, not just end of day — wheat sitting in shed is money sitting idle
    if shed.get("WHEAT", 0) > 0 and prices.get("WHEAT", 0) >= 20:
        market.append(["SELL", "WHEAT", shed["WHEAT"]])

    # Top up to 5 seeds
    if seeds.get("WHEAT", 0) < 5 and money >= 10:
        market.append(["BUY_SEED", "WHEAT", 5 - seeds.get("WHEAT", 0)])

    # Hire up to 2 hands — both orders go in the same market list, 
    # game processes them sequentially so hires_today increments correctly
    if hires_today < 2 and money >= 200:
        for _ in range(2 - hires_today):
            market.append(["HIRE"])

    # Buy land conservatively — only when well past the threshold
    # and not too late in the game to recoup the investment
    if "NE" not in unlocked and money >= 2000 and day < 20:
        market.append(["BUY_LAND"])
    elif "NE" in unlocked and "SW" not in unlocked and money >= 4000 and day < 15:
        market.append(["BUY_LAND"])
    elif "SW" in unlocked and "SE" not in unlocked and money >= 7000 and day < 10:
        market.append(["BUY_LAND"])

    # Collect all tiles that need work
    harvestable = []
    unwatered = []
    weeds = []
    empty = []
    for y in range(10):
        for x in range(10):
            t = farm["tiles"][y][x]
            if t == "LOCKED":
                continue
            if isinstance(t, dict):
                if t.get("kind") == "PLANT":
                    age = day - t["planted_day"]
                    if age >= 2 and t["yield_units"] > 0:
                        harvestable.append((x, y))
                    if not t["watered_today"]:
                        unwatered.append((x, y))
                elif t.get("kind") == "WEED":
                    weeds.append((x, y))
            elif t is None:
                empty.append((x, y))

    # Priority: harvest > water > dig weeds > plant
    if harvestable:
        work = harvestable
    elif unwatered:
        work = unwatered
    elif weeds:
        work = weeds
    else:
        work = empty

    # All units — farmer first, then hands
    units = [(fx, fy)] + [(hx, hy) for hx, hy in hands]

    # Greedily assign each unit to its closest unassigned task
    assignments = {}
    assigned_tiles = set()

    for i, (ux, uy) in enumerate(units):
        tile = farm["tiles"][uy][ux]
        if isinstance(tile, dict) and tile.get("kind") == "PLANT":
            age = day - tile["planted_day"]
            if age >= 2 and tile["yield_units"] > 0:
                assignments[i] = "HARVEST"
                continue
            if not tile["watered_today"]:
                assignments[i] = "WATER"
                continue
        if isinstance(tile, dict) and tile.get("kind") == "WEED":
            assignments[i] = "DIG"
            continue
        if tile is None and seeds.get("WHEAT", 0) > 0:
            assignments[i] = ("PLANT", "WHEAT")
            continue

        available = [(x, y) for x, y in work if (x, y) not in assigned_tiles]
        if available:
            tx, ty = min(available, key=lambda p: abs(p[0] - ux) + abs(p[1] - uy))
            assignments[i] = (tx, ty)
            assigned_tiles.add((tx, ty))

    def move_toward(ux, uy, tx, ty):
        if tx != ux:
            return ["EAST" if tx > ux else "WEST"]
        if ty != uy:
            return ["SOUTH" if ty > uy else "NORTH"]
        return ["PASS"]

    def resolve_action(i, ux, uy):
        assignment = assignments.get(i)
        if assignment is None:
            return ["PASS"]
        if assignment == "HARVEST":
            return ["HARVEST"]
        if assignment == "WATER":
            return ["WATER"]
        if assignment == "DIG":
            return ["DIG"]
        if isinstance(assignment, tuple) and assignment[0] == "PLANT":
            return ["PLANT", "WHEAT"]
        tx, ty = assignment
        return move_toward(ux, uy, tx, ty)

    farmer_action = resolve_action(0, fx, fy)

    hand_actions = []
    for i, (hx, hy) in enumerate(hands):
        hand_actions.append(resolve_action(i + 1, hx, hy))

    return {
        "farmer": farmer_action,
        "hands": hand_actions,
        "market": market,
    }

env = make("kaggriculture", debug=True)
env.run([agent, "random"])

final = env.steps[-1]
print(f"Our agent: {final[0].reward}")
print(f"Opponent:  {final[1].reward}")

for seed in [1, 21, 42, 84, 168]:
    env = make("kaggriculture", configuration={"seed": seed})
    env.run([agent, "starter"])
    final = env.steps[-1]
    p0, p1 = final[0].reward, final[1].reward
    result = "WIN" if p0 > p1 else ("TIE" if p0 == p1 else "LOSE")
    print(f"seed={seed}  us={p0:.0f}  starter={p1:.0f}  {result}")

# Why isnt the rendering working?
# env = make("kaggriculture", debug=True)
# env.run([agent, "starter"])
# env.render(mode="ipython", width=1200, height=800)

# Test it against the random agent
env = make("kaggriculture", debug=True)
env.run([agent, "random"])

final = env.steps[-1]
for i, s in enumerate(final):
    print(f"Player {i}: reward={s.reward}, status={s.status}")

# env.render(mode="ipython", width=800, height=600)

# %%writefile submission.py

def agent(obs):
    obs = dict(obs)
    player = obs["player"]
    farm = obs["farms"][player]
    private = obs["private"]
    
    day = obs["day"]
    hour = obs["hour"]
    fx, fy = farm["farmer"]
    seeds = private["seeds"]
    shed = private["shed"]
    money = farm["money"]
    prices = obs["market"]["prices"]
    hands = farm.get("hands", [])
    unlocked = farm.get("unlocked_quadrants", [])
    hires_today = farm.get("hires_today", 0)
    market = []

    # Sell wheat every turn, not just end of day — wheat sitting in shed is money sitting idle
    if shed.get("WHEAT", 0) > 0 and prices.get("WHEAT", 0) >= 20:
        market.append(["SELL", "WHEAT", shed["WHEAT"]])

    # Top up to 5 seeds
    if seeds.get("WHEAT", 0) < 5 and money >= 10:
        market.append(["BUY_SEED", "WHEAT", 5 - seeds.get("WHEAT", 0)])

    # Hire up to 2 hands — both orders go in the same market list, 
    # game processes them sequentially so hires_today increments correctly
    if hires_today < 2 and money >= 200:
        for _ in range(2 - hires_today):
            market.append(["HIRE"])

    # Buy land conservatively — only when well past the threshold
    # and not too late in the game to recoup the investment
    if "NE" not in unlocked and money >= 2000 and day < 20:
        market.append(["BUY_LAND"])
    elif "NE" in unlocked and "SW" not in unlocked and money >= 4000 and day < 15:
        market.append(["BUY_LAND"])
    elif "SW" in unlocked and "SE" not in unlocked and money >= 7000 and day < 10:
        market.append(["BUY_LAND"])

    # Collect all tiles that need work
    harvestable = []
    unwatered = []
    weeds = []
    empty = []
    for y in range(10):
        for x in range(10):
            t = farm["tiles"][y][x]
            if t == "LOCKED":
                continue
            if isinstance(t, dict):
                if t.get("kind") == "PLANT":
                    age = day - t["planted_day"]
                    if age >= 2 and t["yield_units"] > 0:
                        harvestable.append((x, y))
                    if not t["watered_today"]:
                        unwatered.append((x, y))
                elif t.get("kind") == "WEED":
                    weeds.append((x, y))
            elif t is None:
                empty.append((x, y))

    # Priority: harvest > water > dig weeds > plant
    if harvestable:
        work = harvestable
    elif unwatered:
        work = unwatered
    elif weeds:
        work = weeds
    else:
        work = empty

    # All units — farmer first, then hands
    units = [(fx, fy)] + [(hx, hy) for hx, hy in hands]

    # Greedily assign each unit to its closest unassigned task
    assignments = {}
    assigned_tiles = set()

    for i, (ux, uy) in enumerate(units):
        tile = farm["tiles"][uy][ux]
        if isinstance(tile, dict) and tile.get("kind") == "PLANT":
            age = day - tile["planted_day"]
            if age >= 2 and tile["yield_units"] > 0:
                assignments[i] = "HARVEST"
                continue
            if not tile["watered_today"]:
                assignments[i] = "WATER"
                continue
        if isinstance(tile, dict) and tile.get("kind") == "WEED":
            assignments[i] = "DIG"
            continue
        if tile is None and seeds.get("WHEAT", 0) > 0:
            assignments[i] = ("PLANT", "WHEAT")
            continue

        available = [(x, y) for x, y in work if (x, y) not in assigned_tiles]
        if available:
            tx, ty = min(available, key=lambda p: abs(p[0] - ux) + abs(p[1] - uy))
            assignments[i] = (tx, ty)
            assigned_tiles.add((tx, ty))

    def move_toward(ux, uy, tx, ty):
        if tx != ux:
            return ["EAST" if tx > ux else "WEST"]
        if ty != uy:
            return ["SOUTH" if ty > uy else "NORTH"]
        return ["PASS"]

    def resolve_action(i, ux, uy):
        assignment = assignments.get(i)
        if assignment is None:
            return ["PASS"]
        if assignment == "HARVEST":
            return ["HARVEST"]
        if assignment == "WATER":
            return ["WATER"]
        if assignment == "DIG":
            return ["DIG"]
        if isinstance(assignment, tuple) and assignment[0] == "PLANT":
            return ["PLANT", "WHEAT"]
        tx, ty = assignment
        return move_toward(ux, uy, tx, ty)

    farmer_action = resolve_action(0, fx, fy)

    hand_actions = []
    for i, (hx, hy) in enumerate(hands):
        hand_actions.append(resolve_action(i + 1, hx, hy))

    return {
        "farmer": farmer_action,
        "hands": hand_actions,
        "market": market,
    }

