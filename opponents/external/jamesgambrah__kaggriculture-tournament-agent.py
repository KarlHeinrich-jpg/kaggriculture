# Kaggriculture Autonomous Tournament Agent - Version 20 Master Edition
import math
import sys
import os

# --- 1. STATE HELPER ---

class FarmState:
    def __init__(self, obs):
        self.raw_obs = obs
        self.player_index = obs.get("player", 0)
        self.farms = obs.get("farms", [])
        self.my_farm = self.farms[self.player_index] if self.farms and self.player_index < len(self.farms) else {}
        self.private = obs.get("private", {}) or {}
        
        # Grid & Money
        self.money = self.my_farm.get("money", 0)
        self.tiles = self.my_farm.get("tiles", [])
        self.grid_size = len(self.tiles) if self.tiles else 10
        self.unlocked_quadrants = set(self.my_farm.get("unlocked_quadrants", ["NW"]))
        
        # Positions
        self.farmer_pos = tuple(self.my_farm.get("farmer", [4, 4]))
        self.hands_pos = [tuple(h) for h in self.my_farm.get("hands", [])]
        self.hires_today = self.my_farm.get("hires_today", 0)

        # Inventory & Seeds
        self.shed = self.private.get("shed", {})
        self.seeds = self.private.get("seeds", {})
        self.inventories = self.private.get("inventories", [])

        # Time & Market
        self.day = obs.get("day", 0)
        self.hour = obs.get("hour", 0)
        self.market = obs.get("market", {})

    def get_tile(self, x, y):
        if 0 <= y < len(self.tiles) and 0 <= x < len(self.tiles[y]):
            return self.tiles[y][x]
        return None

    def is_tile_unlocked(self, x, y):
        half = self.grid_size // 2
        if x < half and y < half:
            return "NW" in self.unlocked_quadrants
        elif x >= half and y < half:
            return "NE" in self.unlocked_quadrants
        elif x < half and y >= half:
            return "SW" in self.unlocked_quadrants
        else:
            return "SE" in self.unlocked_quadrants

    def get_empty_unlocked_tiles(self):
        empty = []
        for y in range(self.grid_size):
            for x in range(self.grid_size):
                if self.is_tile_unlocked(x, y):
                    if self.get_tile(x, y) is None:
                        empty.append((x, y))
        return empty

    def get_plants_needing_water(self):
        unwatered = []
        for y in range(self.grid_size):
            for x in range(self.grid_size):
                t = self.get_tile(x, y)
                if isinstance(t, dict) and t.get("kind") == "PLANT":
                    if not t.get("watered_today", False):
                        unwatered.append(((x, y), t))
        return unwatered

    def get_plants_ready_to_harvest(self):
        harvestable = []
        for y in range(self.grid_size):
            for x in range(self.grid_size):
                t = self.get_tile(x, y)
                if isinstance(t, dict) and t.get("kind") == "PLANT":
                    if t.get("yield_units", 0) > 0:
                        harvestable.append(((x, y), t))
        return harvestable

    def get_empty_pastures_needing_animal(self):
        empty_pastures = []
        for y in range(self.grid_size):
            for x in range(self.grid_size):
                t = self.get_tile(x, y)
                if isinstance(t, dict) and t.get("kind") == "PASTURE" and t.get("animal") is None:
                    empty_pastures.append((x, y))
        return empty_pastures

    def get_weeds(self):
        weeds = []
        for y in range(self.grid_size):
            for x in range(self.grid_size):
                t = self.get_tile(x, y)
                if isinstance(t, dict) and t.get("kind") == "WEED":
                    weeds.append((x, y))
        return weeds

    def get_tiles_by_kind(self, kind):
        result = []
        for y in range(self.grid_size):
            for x in range(self.grid_size):
                t = self.get_tile(x, y)
                if isinstance(t, dict) and t.get("kind") == kind:
                    result.append(t)
        return result


# --- 2. PATHFINDING & OBSTACLE AVOIDANCE ---

DIRECTIONS = {
    "NORTH": (0, -1),
    "SOUTH": (0, 1),
    "EAST": (1, 0),
    "WEST": (-1, 0),
}

def manhattan_distance(pos1, pos2):
    return abs(pos1[0] - pos2[0]) + abs(pos1[1] - pos2[1])

def get_next_step(start_pos, target_pos, state):
    if start_pos == target_pos:
        return "PASS"

    sx, sy = start_pos
    best_dir = "PASS"
    best_dist = 9999

    for direction, (dx, dy) in DIRECTIONS.items():
        nx, ny = sx + dx, sy + dy
        if 0 <= nx < state.grid_size and 0 <= ny < state.grid_size:
            if not state.is_tile_unlocked(nx, ny):
                continue
            tile = state.get_tile(nx, ny)
            # Avoid walking through weeds unless weeding is the direct target
            if isinstance(tile, dict) and tile.get("kind") == "WEED" and (nx, ny) != target_pos:
                dist = manhattan_distance((nx, ny), target_pos) + 5
            else:
                dist = manhattan_distance((nx, ny), target_pos)

            if dist < best_dist:
                best_dist = dist
                best_dir = direction

    return best_dir


# --- 3. MULTI-TILE PLANNER & PRODUCTION ENGINE ---

MAX_YIELD_DAYS = {
    "CARROT": 3,
    "WHEAT": 4,
    "MELON": 10,
    "TOMATO": 11,
    "STRAWBERRY": 16
}

SEED_COSTS = {
    "WHEAT": 10,
    "CARROT": 20,
    "TOMATO": 50,
    "MELON": 80,
    "STRAWBERRY": 120
}

SHOP_MAP = {
    'BAKERY': ('EGG', 'WHEAT'),
    'PIZZA_SHOP': ('MILK', 'TOMATO', 'WHEAT'),
    'BRUNCH_SPOT': ('EGG', 'WHEAT', 'STRAWBERRY'),
    'YARN_STORE': ('WOOL',),
    'ICE_CREAM_SHOP': ('STRAWBERRY', 'MILK', 'WHEAT'),
    'PET_CAFE': ('CARROT',),
    'SMOOTHIE_SHOP': ('STRAWBERRY', 'MILK'),
    'FARMERS_MARKET': ('WHEAT', 'CARROT', 'TOMATO', 'STRAWBERRY')
}

SHED_ACCESS_TILES = {(4, 4), (5, 4), (4, 5), (5, 5)}
PRODUCE_TO_SELL = {"WHEAT", "CARROT", "TOMATO", "MELON", "STRAWBERRY", "EGG", "MILK", "WOOL", "FERTILIZER"}

class MultiTilePlanner:
    def __init__(self):
        pass

    def _calculate_town_demand(self, unlocked_shops, item):
        demand = 0
        for shop in unlocked_shops:
            products = SHOP_MAP.get(shop, ())
            if item in products:
                demand += 2 if len(products) == 1 else 1
        return demand

    def plan_turn(self, obs):
        state = FarmState(obs)
        market_orders = []
        days_remaining = 30 - state.day
        unlocked_shops = obs.get("town", {}).get("unlocked_shops", [])

        # ============================================================
        # 1. MARKET ORDERS & STRATEGIC CAPITAL ALLOCATION
        # ============================================================
        
        # A. LIQUIDATION & PRODUCE SELLING
        combined_inventory = dict(state.shed)
        all_workers = [state.farmer_pos] + state.hands_pos

        for w_idx, w_pos in enumerate(all_workers):
            pos_tuple = (w_pos[0], w_pos[1])
            w_inv = state.inventories[w_idx] if w_idx < len(state.inventories) else {}
            if pos_tuple in SHED_ACCESS_TILES:
                for item, qty in w_inv.items():
                    if item in PRODUCE_TO_SELL:
                        combined_inventory[item] = combined_inventory.get(item, 0) + qty

        # Day 29/30 GRAND LIQUIDATION: Sell 100% of everything in inventory!
        for item, qty in combined_inventory.items():
            if item in PRODUCE_TO_SELL and qty > 0:
                if state.day >= 28:
                    market_orders.append(["SELL", item, qty])  # <-- 100% Full Liquidation!
                else:
                    town_demand = self._calculate_town_demand(unlocked_shops, item)
                    base_batch = 5 if item in ["MILK", "WOOL", "MELON", "STRAWBERRY"] else 15
                    sell_batch = min(qty, base_batch + town_demand * 3)
                    market_orders.append(["SELL", item, sell_batch])

        # B. GUARANTEED WORKER HIRING (Maintain $300 Reserve)
        num_workers = len(all_workers)
        if state.money >= 40 and state.hires_today < 2 and state.day <= 26:
            market_orders.append(["HIRE"])

        # C. FEED PROTECTION (Always maintain feed for livestock)
        has_animals = len(state.get_tiles_by_kind("PASTURE")) > 0 or len(state.get_tiles_by_kind("COOP")) > 0
        if has_animals and state.shed.get("WHEAT", 0) < 6 and state.money >= 25:
            market_orders.append(["BUY_PRODUCT", "WHEAT", 6])

        # D. LAND EXPANSION ENGINE (Expands to Quads 2, 3, 4 whenever cash permits!)
        num_quads = len(state.unlocked_quadrants)
        if num_quads < 4 and state.day <= 20:
            expansion_cost = 1000 if num_quads == 1 else (1500 if num_quads == 2 else 2000)
            if state.money >= (expansion_cost + 400):  # Expand while preserving $400 cash floor
                market_orders.append(["BUY_LAND"])

        # E. LIVESTOCK PURCHASING (Strictly gated after Day 7 with pasture check)
        empty_pastures = state.get_empty_pastures_needing_animal()
        has_unplaced_cow = (state.shed.get("COW", 0) or 0) > 0 or any((inv.get("COW", 0) or 0) > 0 for inv in state.inventories)
        has_unplaced_sheep = (state.shed.get("SHEEP", 0) or 0) > 0 or any((inv.get("SHEEP", 0) or 0) > 0 for inv in state.inventories)

        if 8 <= state.day <= 20 and state.money >= 800 and empty_pastures:
            if not has_unplaced_cow and not has_unplaced_sheep:
                market_orders.append(["BUY_ANIMAL", "COW", 1])

        # F. PHASED SEED SELECTION & HARD HORIZON ENFORCEMENT
        chosen_crop = None
        
        # EARLY-GAME (Days 1–7): Fast compounding on Carrots & Wheat ONLY
        if state.day <= 7:
            chosen_crop = "CARROT" if state.money >= 200 else "WHEAT"
        
        # MID-GAME (Days 8–23): Safe horizon growth
        elif state.day <= 23:
            if days_remaining >= 18 and state.money >= 450:
                chosen_crop = "STRAWBERRY"
            elif days_remaining >= 12 and state.money >= 350:
                chosen_crop = "MELON"
            elif days_remaining >= 5:
                chosen_crop = "CARROT"
            elif days_remaining >= 3:
                chosen_crop = "WHEAT"
            else:
                chosen_crop = None

        # END-GAME (Days 24–30): Fast harvest / Stop planting
        else:
            if days_remaining >= 4:
                chosen_crop = "CARROT"
            elif days_remaining >= 3:
                chosen_crop = "WHEAT"
            else:
                chosen_crop = None  # Cease planting on Days 28-30

        # $300 LIQUIDITY RESERVE FLOOR: Never spend bank down to single digits!
        RESERVE_FLOOR = 300.0 if state.day < 24 else 80.0
        available_spend = max(0.0, state.money - RESERVE_FLOOR)
        empty_tiles = state.get_empty_unlocked_tiles()
        
        if chosen_crop and len(empty_tiles) > 0 and available_spend >= SEED_COSTS[chosen_crop]:
            current_seeds = state.seeds.get(chosen_crop, 0)
            target_seed_qty = min(len(empty_tiles), num_workers * 2)
            seeds_needed = max(0, target_seed_qty - current_seeds)
            
            if seeds_needed > 0:
                buy_qty = min(seeds_needed, int(available_spend // SEED_COSTS[chosen_crop]))
                if buy_qty > 0:
                    market_orders.append(["BUY_SEED", chosen_crop, buy_qty])

        # ============================================================
        # 2. WORKER ACTION ASSIGNMENTS & OPTIMIZED PRIORITY QUEUE
        # ============================================================
        worker_actions = []
        assigned_targets = set()

        unwatered_plants = [pos for pos, _ in state.get_plants_needing_water()]
        harvestable_plants = [pos for pos, _ in state.get_plants_ready_to_harvest()]
        empty_pastures = state.get_empty_pastures_needing_animal()
        weeds = state.get_weeds()

        for w_idx, w_pos in enumerate(all_workers):
            wx, wy = w_pos
            current_tile = state.get_tile(wx, wy)
            pos_tuple = (wx, wy)
            w_inv = state.inventories[w_idx] if w_idx < len(state.inventories) else {}

            # Rule 0: Move to unlocked land if on LOCKED tile
            if not state.is_tile_unlocked(wx, wy):
                action = self._assign_movement(w_pos, harvestable_plants, unwatered_plants, empty_pastures, empty_tiles, weeds, assigned_targets, state)

            # Rule 1: Same-turn Shed Drop if holding produce and at shed
            elif pos_tuple in SHED_ACCESS_TILES and any(k in PRODUCE_TO_SELL and v > 0 for k, v in w_inv.items()):
                action = ["DROP"]

            # Rule 2: PRIORITY 1 — HARVEST (Immediate Cash Generation!)
            elif isinstance(current_tile, dict) and current_tile.get("kind") == "PLANT" and current_tile.get("yield_units", 0) > 0:
                action = ["HARVEST"]

            # Rule 3: PRIORITY 2 — WATER (Prevent Growth Stalling)
            elif isinstance(current_tile, dict) and current_tile.get("kind") == "PLANT" and not current_tile.get("watered_today", False):
                action = ["WATER"]

            # Rule 4: PRIORITY 2.5 — LIVESTOCK CARE & ANIMAL PLACEMENT
            elif isinstance(current_tile, dict) and current_tile.get("kind") in ["PASTURE", "COOP"]:
                animal = current_tile.get("animal")
                fed_today = current_tile.get("fed_today", False)
                yield_units = current_tile.get("yield_units", 0)

                if animal is None:
                    placed_action = None
                    for animal_type in ["COW", "SHEEP", "GOOSE"]:
                        if (state.shed.get(animal_type, 0) or 0) > 0 or (w_inv.get(animal_type, 0) or 0) > 0:
                            placed_action = ["PLACE", animal_type]
                            break
                    if placed_action:
                        action = placed_action
                    else:
                        action = self._assign_movement(w_pos, harvestable_plants, unwatered_plants, empty_pastures, empty_tiles, weeds, assigned_targets, state)
                elif yield_units > 0:
                    action = ["HARVEST"]
                elif not fed_today and (state.shed.get("WHEAT", 0) > 0 or w_inv.get("WHEAT", 0) > 0):
                    action = ["FEED"]
                elif current_tile.get("fertilizer_available", False):
                    action = ["COLLECT_FERTILIZER"]
                else:
                    action = self._assign_movement(w_pos, harvestable_plants, unwatered_plants, empty_pastures, empty_tiles, weeds, assigned_targets, state)

            # Rule 5: PRIORITY 3 — PLANTING & PASTURE CONSTRUCTION
            elif current_tile is None:
                if len(unwatered_plants) == 0 and len(harvestable_plants) == 0:
                    # Construct Pasture after Day 8 if capital is high and quadrant unlocked
                    if 8 <= state.day <= 18 and state.money >= 1200 and len(empty_tiles) > 8 and len(state.get_tiles_by_kind("PASTURE")) < 2:
                        action = ["BUILD_PASTURE"]
                    else:
                        planted = False
                        crop_priority = ["STRAWBERRY", "MELON", "CARROT", "WHEAT"] if state.day < 24 else ["CARROT", "WHEAT"]
                        for crop in crop_priority:
                            if state.seeds.get(crop, 0) > 0:
                                action = ["PLANT", crop]
                                planted = True
                                break
                        if not planted:
                            action = self._assign_movement(w_pos, harvestable_plants, unwatered_plants, empty_pastures, empty_tiles, weeds, assigned_targets, state)
                else:
                    action = self._assign_movement(w_pos, harvestable_plants, unwatered_plants, empty_pastures, empty_tiles, weeds, assigned_targets, state)

            # Rule 6: PRIORITY 4 — WEED DIGGING
            elif isinstance(current_tile, dict) and current_tile.get("kind") == "WEED":
                action = ["DIG"]

            else:
                action = self._assign_movement(w_pos, harvestable_plants, unwatered_plants, empty_pastures, empty_tiles, weeds, assigned_targets, state)

            worker_actions.append(action)

        farmer_action = worker_actions[0] if worker_actions else ["PASS"]
        hands_actions = worker_actions[1:] if len(worker_actions) > 1 else []

        return {
            "farmer": farmer_action,
            "hands": hands_actions,
            "market": market_orders[:10]
        }

    def _assign_movement(self, w_pos, harvestable, unwatered, empty_pastures, empty_tiles, weeds, assigned_targets, state):
        # 1. HARVEST PRIORITY
        targets = [p for p in harvestable if p not in assigned_targets]
        if targets:
            best_target = min(targets, key=lambda p: manhattan_distance(w_pos, p))
            assigned_targets.add(best_target)
            step_dir = get_next_step(w_pos, best_target, state)
            return [step_dir] if step_dir != "PASS" else ["HARVEST"]

        # 2. WATERING PRIORITY
        targets = [p for p in unwatered if p not in assigned_targets]
        if targets:
            best_target = min(targets, key=lambda p: manhattan_distance(w_pos, p))
            assigned_targets.add(best_target)
            step_dir = get_next_step(w_pos, best_target, state)
            return [step_dir] if step_dir != "PASS" else ["WATER"]

        # 3. ANIMAL PLACEMENT PRIORITY (Directs worker to pasture if unplaced Cow exists)
        has_unplaced = (state.shed.get("COW", 0) or 0) > 0 or (state.shed.get("SHEEP", 0) or 0) > 0
        if has_unplaced and empty_pastures:
            targets = [p for p in empty_pastures if p not in assigned_targets]
            if targets:
                best_target = min(targets, key=lambda p: manhattan_distance(w_pos, p))
                assigned_targets.add(best_target)
                step_dir = get_next_step(w_pos, best_target, state)
                return [step_dir] if step_dir != "PASS" else ["PASS"]

        # 4. PLANTING PRIORITY (Move toward tilled empty land if seeds or cash available)
        if (any(v > 0 for v in state.seeds.values()) or state.money >= 50) and len(unwatered) == 0:
            targets = [p for p in empty_tiles if p not in assigned_targets]
            if targets:
                best_target = min(targets, key=lambda p: manhattan_distance(w_pos, p))
                assigned_targets.add(best_target)
                step_dir = get_next_step(w_pos, best_target, state)
                return [step_dir] if step_dir != "PASS" else ["PASS"]

        # 5. WEED CLEARANCE PRIORITY
        targets = [p for p in weeds if p not in assigned_targets]
        if targets:
            best_target = min(targets, key=lambda p: manhattan_distance(w_pos, p))
            assigned_targets.add(best_target)
            step_dir = get_next_step(w_pos, best_target, state)
            return [step_dir] if step_dir != "PASS" else ["DIG"]

        return ["PASS"]


# --- 4. KAGGLE AGENT HOOK ---

planner_instance = None

def agent(obs):
    global planner_instance
    if planner_instance is None:
        planner_instance = MultiTilePlanner()

    try:
        return planner_instance.plan_turn(obs)
    except Exception as e:
        return {"farmer": ["PASS"], "hands": [], "market": []}

if __name__ == "__main__":
    try:
        with open(__file__, "r", encoding="utf-8") as src:
            code = src.read()
        for fname in ["submission.py", "main.py"]:
            with open(fname, "w", encoding="utf-8") as out:
                out.write(code)
        print("Exported Version 20 submission.py and main.py successfully!")
    except Exception as ex:
        pass
