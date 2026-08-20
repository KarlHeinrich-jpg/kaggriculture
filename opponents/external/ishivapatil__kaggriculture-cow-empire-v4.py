# %%writefile submission.py
import collections

def agent(obs):
    player = obs["player"]
    me = obs["farms"][player]
    private = obs["private"]
    day = obs["day"]
    step = obs["step"]
    money = me["money"]
    market_queue = []
    
    board_size = len(me["tiles"])
    half = board_size // 2
    shed = private["shed"]
    seeds = private["seeds"]
    market = obs["market"]
    prices = market["prices"]
    
    shed_tiles = set([(half - 1, half - 1), (half, half - 1), (half - 1, half), (half, half)])
    units = [tuple(me["farmer"])] + [tuple(h) for h in me["hands"]]
    n_units = len(units)
    
    # =========================================================================
    # SCAN THE FARM
    # =========================================================================
    num_animals = 0
    num_cows = 0
    num_sheep = 0
    empty_tiles = 0
    empty_structures = 0  # empty PASTURE/COOP without animal
    plants = []
    weeds = 0
    
    for row in me["tiles"]:
        for t in row:
            if t is None:
                empty_tiles += 1
            elif isinstance(t, dict):
                if t.get("animal"):
                    num_animals += 1
                    if t["animal"] == "COW": num_cows += 1
                    elif t["animal"] == "SHEEP": num_sheep += 1
                elif t.get("kind") in ["COOP", "PASTURE"]:
                    empty_structures += 1
                elif t.get("kind") == "PLANT":
                    plants.append(t)
                elif t.get("kind") == "WEED":
                    weeds += 1
    
    shed_cows = shed.get("COW", 0) + sum(inv.get("COW", 0) for inv in private["inventories"])
    shed_sheep = shed.get("SHEEP", 0) + sum(inv.get("SHEEP", 0) for inv in private["inventories"])
    unplaced_animals = shed_cows + shed_sheep
    total_animals = num_animals + unplaced_animals
    
    n_unlocked = len(me.get("unlocked_quadrants", ["NW"]))
    total_tiles = (board_size // 2) ** 2 * n_unlocked  # approx unlocked tiles
    
    # =========================================================================
    # MARKET ORDERS (max 10 per turn)
    # =========================================================================
    
    # --- 1. SELL intelligently based on Marginal Revenue Thresholds ---
    sell_thresholds = {
        "MILK": 10, "WOOL": 50, "EGG": 10, 
        "FERTILIZER": 50, # Stop selling if < 50; use to double crop yields instead
        "MELON": 100, "STRAWBERRY": 50, "TOMATO": 30, "CARROT": 15, "WHEAT": 10
    }
    sell_order = ["MILK", "WOOL", "EGG", "FERTILIZER", "MELON", "STRAWBERRY", "TOMATO", "CARROT", "WHEAT"]
    for item in sell_order:
        qty = shed.get(item, 0)
        if qty > 0:
            current_price = prices.get(item, 0)
            threshold = sell_thresholds.get(item, 1)
            
            # Don't sell wheat if we have animals that need feeding
            if item == "WHEAT" and total_animals > 0:
                # Only sell excess wheat beyond what animals need
                wheat_reserve = total_animals * 2  # keep 2 days buffer
                sell_qty = max(0, qty - wheat_reserve)
                if sell_qty > 0 and current_price >= threshold:
                    market_queue.append(["SELL", item, sell_qty])
            else:
                if current_price >= threshold:
                    market_queue.append(["SELL", item, qty])
    
    # --- 2. HIRE aggressively but smartly (Self-Reliance) ---
    def fib(n):
        a, b = 1, 1
        for _ in range(n): a, b = b, a + b
        return a
    
    # Calculate estimated daily workload
    # Plants need watering (1) or harvesting (1) + walk.
    # Animals need feed (1) + care (1) + collect (1) + multiple walks to shed.
    estimated_workload = len(plants) + (total_animals * 5) + (empty_tiles * 2)
    
    if day == 0:
        # Day 0 Perfect Expansion Math:
        # 1 farmer + 1 hire (2 total workers) can perfectly plant exactly 46 tiles.
        target_workers = 2
    else:
        target_workers = max(1, min(10, estimated_workload // 10))  # A worker does ~10 tasks/day with walking
    
    hire_budget = money * 0.4  # spend up to 40% of money on workers
    hires_done = me.get("hires_today", 0)
    
    # Hire dynamically if workload exceeds capacity
    if step < 650:
        while n_units + hires_done < target_workers:
            cost = fib(hires_done)
            if cost > hire_budget or cost > money:
                break
            market_queue.append(["HIRE"])
            money -= cost
            hire_budget -= cost
            hires_done += 1
            if hires_done >= 6:  # cap at 6 hires per step
                break
    
    # --- 3. BUY_LAND early but aggressively if we have excess resources ---
    LAND_PRICES = [1000, 2000, 4000]
    if n_unlocked - 1 < len(LAND_PRICES) and step < 400:
        land_cost = LAND_PRICES[n_unlocked - 1]
        # Buy land if we can afford it PLUS enough seeds to plant the new tiles ($500)
        if money >= land_cost + 500:
            market_queue.append(["BUY_LAND"])
            money -= land_cost
    
    # --- 4. BUY_ANIMAL COW (the money machine) ---
    # With Math Optimization, we can scale to the absolute maximum limit of the map
    # 22 Cows + 5 Sheep is the mathematical ceiling before space runs out
    target_cows = 22
    target_sheep = 5
    
    if step >= 48 and step < 350 and num_cows + shed_cows < target_cows:
        cow_cost = 400
        # Buy as many as we can afford (1 at a time through market)
        if money > cow_cost + 200 and empty_structures + empty_tiles > unplaced_animals:
            market_queue.append(["BUY_ANIMAL", "COW", 1])
            money -= cow_cost
    
    if step >= 48 and step < 250 and num_sheep + shed_sheep < target_sheep:
        sheep_cost = 500
        if money > sheep_cost + 200 and empty_structures + empty_tiles > unplaced_animals + 1:
            market_queue.append(["BUY_ANIMAL", "SHEEP", 1])
            money -= sheep_cost
    
    # --- 5. BUY WHEAT for animal feed ---
    # Animals need 1 wheat each per day. Buy enough for 2 days buffer.
    wheat_in_system = shed.get("WHEAT", 0) + sum(inv.get("WHEAT", 0) for inv in private["inventories"])
    wheat_needed = total_animals * 2  # 2-day buffer
    wheat_deficit = max(0, wheat_needed - wheat_in_system)
    if wheat_deficit > 0 and money >= 25 and step < 680:
        buy_wheat = min(wheat_deficit, int(money // 25))
        if buy_wheat > 0:
            market_queue.append(["BUY_PRODUCT", "WHEAT", buy_wheat])
            money -= buy_wheat * 25
    
    # --- 6. BUY SEEDS for cash crops (early game + fill gaps) ---
    total_plants = len(plants)
    # In early game, plant crops for quick cash to maximize profit. Later, reserve space for animals.
    if step < 100:
        max_crop_tiles = empty_tiles  # Maximize profit: plant EVERYTHING initially
    else:
        # Reserve tiles only when we are in the animal phase
        max_crop_tiles = max(0, empty_tiles - (target_cows + target_sheep - total_animals))
    
    if step < 100:
        # Early game: plant CARROT for fast cash (3-day cycle)
        # Ensure we buy exactly what we need to completely utilize the land
        needed_seeds = max(0, max_crop_tiles - seeds.get("CARROT", 0))
        if money > 20 and needed_seeds > 0:
            buy_amt = min(needed_seeds, int(money // 20))
            if buy_amt > 0:
                market_queue.append(["BUY_SEED", "CARROT", buy_amt])
                money -= buy_amt * 20
    elif step < 300:
        # Mid game: plant WHEAT (cheap, fast, useful as feed AND sellable)
        if money > 10 and seeds.get("WHEAT", 0) < max(5, max_crop_tiles // 2):
            buy_amt = min(10, int(money // 10))
            if buy_amt > 0:
                market_queue.append(["BUY_SEED", "WHEAT", buy_amt])
                money -= buy_amt * 10
    # Late game: plant MELON on remaining tiles if enough time
    if step < 500 and step > 200 and empty_tiles > 5:
        if money > 80 and seeds.get("MELON", 0) < 5:
            buy_amt = min(5, int(money // 80))
            if buy_amt > 0:
                market_queue.append(["BUY_SEED", "MELON", buy_amt])
                money -= buy_amt * 80
    
    # =========================================================================
    # GENERATE TASKS
    # =========================================================================
    # Priority: lower = more urgent
    # 1: FEED (animals die!)
    # 2: HARVEST (get money!)
    # 3: CARE (bonus animal yield)
    # 4: WATER (plants die without it!)
    # 5: COLLECT_FERTILIZER (free money)
    # 6: BUILD_PASTURE / PLACE / PLANT
    # 7: FERTILIZE (crop boost)
    # 8: DIG (clear weeds)
    
    tasks = []  # (priority, x, y, action, arg)
    
    for y, row in enumerate(me["tiles"]):
        for x, tile in enumerate(row):
            if tile == "LOCKED":
                continue
            
            if tile is None:
                # Empty tile: build pasture if we need more animal space
                if unplaced_animals > empty_structures:
                    tasks.append((6, x, y, "BUILD_PASTURE", None))
                else:
                    # Plant a crop
                    for c in ["CARROT", "WHEAT", "MELON", "TOMATO", "STRAWBERRY"]:
                        if seeds.get(c, 0) > 0:
                            tasks.append((6, x, y, "PLANT", c))
                            seeds[c] -= 1
                            break
                continue
            
            if not isinstance(tile, dict):
                continue
                
            kind = tile.get("kind")
            
            if kind == "WEED":
                tasks.append((9, x, y, "DIG", None))
                
            elif kind == "PLANT":
                # Harvest check: does it have yield_units > 0?
                crop = tile.get("crop", "")
                has_yield = tile.get("yield_units", 0) > 0
                
                if has_yield:
                    # Check if it's mature enough to harvest
                    # Non-ongoing: harvest when yield_units > 0 and past first_yield_day
                    CROP_FIRST_YIELD = {"WHEAT": 2, "CARROT": 2, "TOMATO": 8, "STRAWBERRY": 10, "MELON": 10}
                    first_yield = CROP_FIRST_YIELD.get(crop, 2)
                    if (day - tile.get("planted_day", 0)) >= first_yield:
                        tasks.append((2, x, y, "HARVEST", None))
                    else:
                        # Not mature yet, just water
                        if not tile.get("watered_today"):
                            tasks.append((4, x, y, "WATER", None))
                else:
                    # No yield yet, water it to keep alive and build yield
                    if not tile.get("watered_today"):
                        tasks.append((4, x, y, "WATER", None))
                    # Fertilize for bonus (only if we have some)
                    if tile.get("fertilized_until_day", -1) < day:
                        # Boost priority if it's MELON
                        fert_prio = 2.5 if crop == "MELON" else 4.5
                        tasks.append((fert_prio, x, y, "FERTILIZE", None))
                        
            elif kind in ["COOP", "PASTURE"]:
                if tile.get("animal"):
                    # Animal tile: FEED > HARVEST > CARE > COLLECT_FERTILIZER
                    if not tile.get("fed_today"):
                        tasks.append((1, x, y, "FEED", None))
                    if tile.get("yield_units", 0) > 0:
                        tasks.append((2, x, y, "HARVEST", None))
                    if not tile.get("cared_today"):
                        tasks.append((3, x, y, "CARE", None))
                    if tile.get("fertilizer_available"):
                        tasks.append((5, x, y, "COLLECT_FERTILIZER", None))
                else:
                    # Empty structure: place an animal
                    tasks.append((6, x, y, "PLACE", "COW"))
    
    tasks.sort(key=lambda t: t[0])
    
    # =========================================================================
    # BFS PATHFINDING
    # =========================================================================
    def bfs_path(sx, sy, tx, ty):
        if sx == tx and sy == ty:
            return []
        q = collections.deque([(sx, sy, [])])
        visited = {(sx, sy)}
        while q:
            cx, cy, path = q.popleft()
            for dx, dy, d in [(0, -1, "NORTH"), (0, 1, "SOUTH"), (-1, 0, "WEST"), (1, 0, "EAST")]:
                nx, ny = cx + dx, cy + dy
                if 0 <= nx < board_size and 0 <= ny < board_size and (nx, ny) not in visited:
                    new_path = path + [d]
                    if nx == tx and ny == ty:
                        return new_path
                    visited.add((nx, ny))
                    q.append((nx, ny, new_path))
        return []
    
    def nearest_shed_path(ux, uy):
        best_path = None
        for sx, sy in shed_tiles:
            p = bfs_path(ux, uy, sx, sy)
            if p is not None and (best_path is None or len(p) < len(best_path)):
                best_path = p
        return best_path if best_path else []
    
    # =========================================================================
    # ASSIGN TASKS TO UNITS
    # =========================================================================
    unit_actions = [["PASS"] for _ in units]
    assigned_tasks = set()
    
    for i, (ux, uy) in enumerate(units):
        inv = private["inventories"][i]
        my_wheat = inv.get("WHEAT", 0)
        my_cows = inv.get("COW", 0)
        my_sheep = inv.get("SHEEP", 0)
        my_fert = inv.get("FERTILIZER", 0)
        
        # Check what we're carrying that should go to shed
        valuable_items = sum(inv.get(item, 0) for item in ["MILK", "WOOL", "EGG", "MELON", "CARROT", "TOMATO", "STRAWBERRY"])
        excess_wheat = max(0, my_wheat - 5) if total_animals > 0 else my_wheat
        excess_fert = max(0, my_fert - 3)
        need_to_drop = valuable_items > 0 or excess_fert > 2
        
        # Step 1: PICKUP from shed if needed for tasks
        has_feed_task = any(t[3] == "FEED" for idx, t in enumerate(tasks) if idx not in assigned_tasks)
        has_place_task = any(t[3] == "PLACE" for idx, t in enumerate(tasks) if idx not in assigned_tasks)
        has_fert_task = any(t[3] == "FERTILIZE" for idx, t in enumerate(tasks) if idx not in assigned_tasks)
        
        need_pickup = None
        if has_feed_task and my_wheat == 0 and shed.get("WHEAT", 0) > 0:
            need_pickup = "WHEAT"
        elif has_fert_task and my_fert == 0 and shed.get("FERTILIZER", 0) > 0:
            need_pickup = "FERTILIZER"
        elif has_place_task and my_cows == 0 and my_sheep == 0:
            if shed.get("COW", 0) > 0:
                need_pickup = "COW"
            elif shed.get("SHEEP", 0) > 0:
                need_pickup = "SHEEP"
        
        if need_pickup:
            if (ux, uy) in shed_tiles:
                amt = min(5, shed.get(need_pickup, 0)) if need_pickup in ["WHEAT", "FERTILIZER"] else 1
                if amt > 0:
                    unit_actions[i] = ["PICKUP", need_pickup, amt]
                    continue
            else:
                path = nearest_shed_path(ux, uy)
                if path:
                    unit_actions[i] = [path[0]]
                    continue
        
        # Step 2: DROP valuable items at shed
        if need_to_drop:
            if (ux, uy) in shed_tiles:
                # Find what to drop
                for item in ["MILK", "WOOL", "EGG", "MELON", "CARROT", "TOMATO", "STRAWBERRY"]:
                    if inv.get(item, 0) > 0:
                        unit_actions[i] = ["DROP", item, inv[item]]
                        break
                else:
                    if excess_fert > 0:
                        unit_actions[i] = ["DROP", "FERTILIZER", excess_fert]
                    elif excess_wheat > 0:
                        unit_actions[i] = ["DROP", "WHEAT", excess_wheat]
                continue
            else:
                path = nearest_shed_path(ux, uy)
                if path:
                    unit_actions[i] = [path[0]]
                    continue
        
        # Step 3: Find nearest task this unit can do
        best_task = None
        best_dist = 999
        best_path = []
        
        for idx, (prio, tx, ty, act, arg) in enumerate(tasks):
            if idx in assigned_tasks:
                continue
            
            # Capability checks
            if act == "FEED" and my_wheat == 0:
                continue
            if act == "FERTILIZE" and my_fert == 0:
                continue
            if act == "PLACE":
                if my_cows > 0:
                    arg = "COW"
                elif my_sheep > 0:
                    arg = "SHEEP"
                else:
                    continue
            
            dist = abs(ux - tx) + abs(uy - ty)
            if dist == 0:
                best_task = idx
                best_dist = 0
                best_path = []
                if act == "PLACE":
                    tasks[idx] = (prio, tx, ty, act, arg)
                break
            elif dist < best_dist:
                path = bfs_path(ux, uy, tx, ty)
                if path:
                    best_dist = len(path)
                    best_task = idx
                    best_path = path
                    if act == "PLACE":
                        tasks[idx] = (prio, tx, ty, act, arg)
        
        if best_task is not None:
            assigned_tasks.add(best_task)
            if best_dist == 0:
                _, _, _, act, arg = tasks[best_task]
                unit_actions[i] = [act, arg] if arg else [act]
            else:
                unit_actions[i] = [best_path[0]]
    
    return {
        "farmer": unit_actions[0],
        "hands": unit_actions[1:],
        "market": market_queue[:10]
    }

