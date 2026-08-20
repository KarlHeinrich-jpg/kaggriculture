# Kaggriculture Autonomous Tournament Agent
import math
import sys
import os

# --- state_helper.py ---


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
                    # Don't plant on center shed adjacent tiles if needed
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

    def get_animals_needing_feed(self):
        unfed = []
        for y in range(self.grid_size):
            for x in range(self.grid_size):
                t = self.get_tile(x, y)
                if isinstance(t, dict) and t.get("kind") in ["COOP", "PASTURE"]:
                    if t.get("animal") and not t.get("fed_today", False):
                        unfed.append(((x, y), t))
        return unfed

    def get_animals_with_fertilizer(self):
        fert = []
        for y in range(self.grid_size):
            for x in range(self.grid_size):
                t = self.get_tile(x, y)
                if isinstance(t, dict) and t.get("kind") in ["COOP", "PASTURE"]:
                    if t.get("fertilizer_available", False):
                        fert.append(((x, y), t))
        return fert

    def get_unfertilized_high_value_crops(self):
        unfert = []
        for y in range(self.grid_size):
            for x in range(self.grid_size):
                t = self.get_tile(x, y)
                if isinstance(t, dict) and t.get("kind") == "PLANT":
                    if t.get("crop") in ["MELON", "STRAWBERRY"] and t.get("fertilized_until_day", -1) < self.day:
                        unfert.append(((x, y), t))
        return unfert

    def get_weeds(self):
        weeds = []
        for y in range(self.grid_size):
            for x in range(self.grid_size):
                t = self.get_tile(x, y)
                if isinstance(t, dict) and t.get("kind") == "WEED":
                    weeds.append((x, y))
        return weeds

    def total_shed_item_count(self):
        return sum(v for k, v in self.shed.items() if k != "seeds")


# --- market_engine.py ---


import math

# Competition Market Parameters Default Reference
MARKET_SPECS = {
    "WHEAT":      {"base": 25,  "I0": 10000, "T": 400, "below_func": "sqrt",   "below_target": 0.80, "above_func": "log",    "above_target": 0.20},
    "CARROT":     {"base": 35,  "I0": 10000, "T": 450, "below_func": "log",    "below_target": 0.20, "above_func": "sqrt",   "above_target": 0.70},
    "TOMATO":     {"base": 60,  "I0": 10000, "T": 200, "below_func": "linear", "below_target": 0.40, "above_func": "sqrt",   "above_target": 0.60},
    "STRAWBERRY": {"base": 120, "I0": 10000, "T": 100, "below_func": "sqrt",   "below_target": 0.70, "above_func": "linear font", "above_target": 1.60},
    "MELON":      {"base": 250, "I0": 10000, "T": 300, "below_func": "log",    "below_target": 0.20, "above_func": "sq",     "above_target": 3.60},
    "EGG":        {"base": 50,  "I0": 10000, "T": 332, "below_func": "linear", "below_target": 0.40, "above_func": "log",    "above_target": 0.20},
    "MILK":       {"base": 160, "I0": 10000, "T": 122, "below_func": "sqrt",   "below_target": 0.60, "above_func": "linear", "above_target": 1.60},
    "WOOL":       {"base": 200, "I0": 10000, "T": 105, "below_func": "log",    "below_target": 0.20, "above_func": "sq",     "above_target": 3.20},
    "FERTILIZER": {"base": 100, "I0": 10000, "T": 200, "below_func": "linear", "below_target": 0.40, "above_func": "linear", "above_target": 0.40},
}

CROP_SPECS = {
    "WHEAT":      {"seed_cost": 10,  "base_price": 25,  "first_yield_days": 2,  "max_yield_days": 4,  "yield_units": 6, "ongoing": False},
    "CARROT":     {"seed_cost": 20,  "base_price": 35,  "first_yield_days": 2,  "max_yield_days": 3,  "yield_units": 4, "ongoing": False},
    "TOMATO":     {"seed_cost": 50,  "base_price": 60,  "first_yield_days": 8,  "max_yield_days": 11, "yield_units": 4, "ongoing": True},
    "STRAWBERRY": {"seed_cost": 100, "base_price": 120, "first_yield_days": 10, "max_yield_days": 16, "yield_units": 4, "ongoing": True},
    "MELON":      {"seed_cost": 80,  "base_price": 250, "first_yield_days": 10, "max_yield_days": 10, "yield_units": 6, "ongoing": False},
}

class MarketEngine:
    def __init__(self, market_obs=None):
        self.market_prices = market_obs.get("prices", {}) if market_obs else {}
        self.market_inventory = market_obs.get("inventory", {}) if market_obs else {}

    def update(self, market_obs):
        self.market_prices = market_obs.get("prices", {})
        self.market_inventory = market_obs.get("inventory", {})

    def get_price(self, item):
        return self.market_prices.get(item, MARKET_SPECS.get(item, {}).get("base", 10))

    def evaluate_crop_roi(self, crop, current_day, max_season_days=30):
        
        spec = CROP_SPECS.get(crop)
        if not spec:
            return -999

        days_needed = spec["max_yield_days"]
        days_remaining = max_season_days - current_day
        
        # Will the crop yield before end of season?
        if days_remaining < spec["first_yield_days"]:
            return -999 # Waste of money!

        price = self.get_price(crop if crop != "WHEAT" else "WHEAT")
        expected_revenue = spec["yield_units"] * price
        net_profit = expected_revenue - spec["seed_cost"]
        
        # Profit per day occupied
        roi_per_day = net_profit / max(1, min(days_needed, days_remaining))
        return roi_per_day

    def select_best_crop(self, available_money, current_day, max_season_days=30):
        
        days_remaining = max_season_days - current_day

        # Phase 3 (Days 26-30): Stop planting entirely
        if days_remaining <= 2:
            return None

        # Short term phase (Days 20-25): Wheat or Carrot ONLY
        if days_remaining < 8:
            if available_money >= 20 and self.evaluate_crop_roi("CARROT", current_day) > 0:
                return "CARROT"
            elif available_money >= 10 and self.evaluate_crop_roi("WHEAT", current_day) > 0:
                return "WHEAT"
            return None

        # Medium to Long term (Days 0-19): High ROI crops
        candidates = ["MELON", "STRAWBERRY", "CARROT", "WHEAT", "TOMATO"]
        best_crop = None
        best_score = -999

        for crop in candidates:
            cost = CROP_SPECS[crop]["seed_cost"]
            if available_money >= cost:
                score = self.evaluate_crop_roi(crop, current_day)
                if score > best_score:
                    best_score = score
                    best_crop = crop

        return best_crop


# --- pathfinder.py ---


import heapq

DIRECTIONS = {
    "NORTH": (0, -1),
    "SOUTH": (0, 1),
    "EAST": (1, 0),
    "WEST": (-1, 0),
}

def manhattan_distance(pos1, pos2):
    return abs(pos1[0] - pos2[0]) + abs(pos1[1] - pos2[1])

def get_next_step(start_pos, target_pos, grid_size=10):
    
    if start_pos == target_pos:
        return "PASS"

    sx, sy = start_pos
    tx, ty = target_pos

    best_dir = "PASS"
    best_dist = manhattan_distance(start_pos, target_pos)

    for direction, (dx, dy) in DIRECTIONS.items():
        nx, ny = sx + dx, sy + dy
        if 0 <= nx < grid_size and 0 <= ny < grid_size:
            dist = manhattan_distance((nx, ny), target_pos)
            if dist < best_dist:
                best_dist = dist
                best_dir = direction

    return best_dir

def get_shed_adjacent_positions(grid_size=10):
    
    half = grid_size // 2
    return [(half - 1, half - 1), (half, half - 1), (half - 1, half), (half, half)]

def is_adjacent_to_shed(pos, grid_size=10):
    return pos in get_shed_adjacent_positions(grid_size)


# --- multi_tile_planner.py ---



MAX_YIELD_DAYS = {
    "CARROT": 3,
    "WHEAT": 4,
    "MELON": 10,
    "TOMATO": 11,
    "STRAWBERRY": 16
}

class MultiTilePlanner:
    def __init__(self):
        pass

    def plan_turn(self, obs):
        state = FarmState(obs)
        market_orders = []

        # ==========================================
        # 1. MARKET ORDERS (IMMEDIATE SELL, HIRING, SEEDS, EXPANSION)
        # ==========================================
        
        # A. Sell ALL produce sitting in shed immediately
        for item, qty in state.shed.items():
            if item != "seeds" and qty > 0:
                market_orders.append(["SELL", item, qty])

        # B. Farm Hand Hiring (Hire 2 farm hands daily for $2/day salary)
        if state.money >= 50 and state.hires_today < 2 and state.day <= 25:
            market_orders.append(["HIRE"])

        # C. Seed Purchasing Strategy
        days_remaining = 30 - state.day
        chosen_crop = "CARROT"
        seed_cost = 20

        if days_remaining >= 11 and state.money >= 350:
            chosen_crop = "MELON"
            seed_cost = 80
        elif days_remaining < 4:
            chosen_crop = None

        if chosen_crop:
            current_seeds = state.seeds.get(chosen_crop, 0)
            empty_count = len(state.get_empty_unlocked_tiles())
            num_workers = 1 + len(state.hands_pos)
            
            # Buy seed if seed count < worker count and empty space exists
            if current_seeds < num_workers and empty_count > 0 and state.money >= seed_cost:
                market_orders.append(["BUY_SEED", chosen_crop, 1])

        # D. Land Expansion Strategy (Buy NE at $1,000 when money >= $1,500)
        if len(state.unlocked_quadrants) == 1 and state.money >= 1500 and state.day <= 15:
            market_orders.append(["BUY_LAND"])

        # ==========================================
        # 2. WORKER ACTION ASSIGNMENTS
        # ==========================================
        all_workers = [state.farmer_pos] + state.hands_pos
        worker_actions = []
        assigned_targets = set()

        unwatered_plants = [pos for pos, _ in state.get_plants_needing_water()]
        harvestable_plants = [pos for pos, _ in state.get_plants_ready_to_harvest()]
        empty_tiles = state.get_empty_unlocked_tiles()
        weeds = state.get_weeds()

        for w_pos in all_workers:
            wx, wy = w_pos
            current_tile = state.get_tile(wx, wy)
            action = ["PASS"]

            # Priority 1: Action on current plant tile
            if isinstance(current_tile, dict) and current_tile.get("kind") == "PLANT":
                crop = current_tile.get("crop")
                planted_day = current_tile.get("planted_day", 0)
                crop_age = state.day - planted_day
                yield_units = current_tile.get("yield_units", 0)
                watered_today = current_tile.get("watered_today", False)
                max_age = MAX_YIELD_DAYS.get(crop, 3)

                if crop in ["CARROT", "WHEAT", "MELON"]:
                    if (crop_age >= max_age or state.day >= 27) and yield_units > 0:
                        action = ["HARVEST"]
                    elif not watered_today:
                        action = ["WATER"]
                    else:
                        action = self._assign_movement(w_pos, unwatered_plants, harvestable_plants, empty_tiles, weeds, assigned_targets, state)
                else:
                    if yield_units > 0:
                        action = ["HARVEST"]
                    elif not watered_today:
                        action = ["WATER"]
                    else:
                        action = self._assign_movement(w_pos, unwatered_plants, harvestable_plants, empty_tiles, weeds, assigned_targets, state)

            # Priority 2: Plant seed if standing on empty tile
            elif current_tile is None:
                planted = False
                allowed_crops = ["MELON", "CARROT", "WHEAT"] if (30 - state.day) >= 11 else ["CARROT", "WHEAT"]
                for crop in allowed_crops:
                    if state.seeds.get(crop, 0) > 0:
                        action = ["PLANT", crop]
                        planted = True
                        break
                if not planted:
                    action = self._assign_movement(w_pos, unwatered_plants, harvestable_plants, empty_tiles, weeds, assigned_targets, state)

            # Priority 3: Dig weed
            elif isinstance(current_tile, dict) and current_tile.get("kind") == "WEED":
                action = ["DIG"]

            else:
                action = self._assign_movement(w_pos, unwatered_plants, harvestable_plants, empty_tiles, weeds, assigned_targets, state)

            worker_actions.append(action)

        farmer_action = worker_actions[0] if worker_actions else ["PASS"]
        hands_actions = worker_actions[1:] if len(worker_actions) > 1 else []

        return {
            "farmer": farmer_action,
            "hands": hands_actions,
            "market": market_orders[:10]
        }

    def _assign_movement(self, w_pos, unwatered, harvestable, empty, weeds, assigned_targets, state):
        # 1. Unwatered Plants
        targets = [p for p in unwatered if p not in assigned_targets]
        if targets:
            best_target = min(targets, key=lambda p: manhattan_distance(w_pos, p))
            assigned_targets.add(best_target)
            step_dir = get_next_step(w_pos, best_target, state.grid_size)
            if step_dir != "PASS":
                return [step_dir]

        # 2. Harvestable Plants
        targets = [p for p in harvestable if p not in assigned_targets]
        if targets:
            best_target = min(targets, key=lambda p: manhattan_distance(w_pos, p))
            assigned_targets.add(best_target)
            step_dir = get_next_step(w_pos, best_target, state.grid_size)
            if step_dir != "PASS":
                return [step_dir]

        # 3. Empty tiles for planting
        if any(v > 0 for v in state.seeds.values()):
            targets = [p for p in empty if p not in assigned_targets]
            if targets:
                best_target = min(targets, key=lambda p: manhattan_distance(w_pos, p))
                assigned_targets.add(best_target)
                step_dir = get_next_step(w_pos, best_target, state.grid_size)
                if step_dir != "PASS":
                    return [step_dir]

        # 4. Weeds
        targets = [p for p in weeds if p not in assigned_targets]
        if targets:
            best_target = min(targets, key=lambda p: manhattan_distance(w_pos, p))
            assigned_targets.add(best_target)
            step_dir = get_next_step(w_pos, best_target, state.grid_size)
            if step_dir != "PASS":
                return [step_dir]

        return ["PASS"]



planner_instance = None

def agent(obs):
    global planner_instance
    if planner_instance is None:
        planner_instance = MultiTilePlanner()

    try:
        return planner_instance.plan_turn(obs)
    except Exception as e:
        return {"farmer": ["PASS"], "hands": [], "market": []}
