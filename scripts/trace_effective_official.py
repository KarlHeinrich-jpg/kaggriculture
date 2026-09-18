#!/usr/bin/env python3
"""Count successful actions and market fills in the official environment."""

from __future__ import annotations

import argparse
from collections import Counter
import copy
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from kaggle_environments import make  # noqa: E402
from kaggle_environments.envs.kaggriculture import kaggriculture as engine  # noqa: E402
from route.match import load_module  # noqa: E402
from search.evaluate import load_ref_agent  # noqa: E402


def _inventory_total(private):
    total = Counter(private.get("shed", {}) or {})
    for inventory in private.get("inventories", ()) or ():
        total.update(inventory or {})
    return total


def trace(candidate_path, opponent_name, seed, seat):
    module = load_module(str(candidate_path), prefix="effective_trace")
    candidate = getattr(module, "kaggriculture_agent")
    opponent = load_ref_agent(opponent_name)
    pair = [candidate, opponent] if seat == 0 else [opponent, candidate]
    farm_players = {}
    active_unit_player = {"value": 1}
    effective = [Counter(), Counter()]
    market_cash = [Counter(), Counter()]
    harvested = [Counter(), Counter()]

    def player_for(farm):
        return farm_players[id(farm)]

    original_unit = engine._apply_unit_action
    original_commit = engine._commit_unit
    original_hire = engine._do_hire
    original_land = engine._do_buy_land
    original_market = engine._process_market

    def process_market(state, env):
        farms = state[0].observation.farms
        farm_players.clear()
        farm_players.update({id(farm): index for index, farm in enumerate(farms)})
        return original_market(state, env)

    def unit(farm, private, idx, action, *args, **kwargs):
        if int(idx) == 0:
            active_unit_player["value"] = 1 - active_unit_player["value"]
        player = active_unit_player["value"]
        before_farm = copy.deepcopy(farm)
        before_private = copy.deepcopy(private)
        harvested_item = None
        harvested_quantity = 0
        if isinstance(action, list) and action and action[0] == "HARVEST":
            position = (
                farm.get("farmer")
                if int(idx) == 0
                else (farm.get("hands", ()) or ())[int(idx) - 1]
            )
            tile = farm["tiles"][int(position[1])][int(position[0])]
            if isinstance(tile, dict):
                harvested_quantity = max(0, int(tile.get("yield_units", 0) or 0))
                harvested_item = tile.get("crop")
                if "animal" in tile:
                    harvested_item = engine.ANIMALS[tile["animal"]]["product"]
        original_unit(farm, private, idx, action, *args, **kwargs)
        if farm != before_farm or private != before_private:
            op = str(action[0]) if isinstance(action, list) and action else ""
            effective[player][op] += 1
            if op == "HARVEST" and harvested_item and harvested_quantity > 0:
                harvested[player][str(harvested_item)] += harvested_quantity
            elif op == "COLLECT_FERTILIZER":
                harvested[player]["FERTILIZER"] += 1

    def commit(op, item, price, farm, private, market, *args, **kwargs):
        player = player_for(farm)
        before_money = float(farm.get("money", 0) or 0)
        ok = original_commit(
            op, item, price, farm, private, market, *args, **kwargs
        )
        if ok:
            effective[player][f"{op}:{item}"] += 1
            market_cash[player][f"{op}:{item}"] += abs(
                float(farm.get("money", 0) or 0) - before_money
            )
        return ok

    def hire(farm, private, *args, **kwargs):
        player = player_for(farm)
        before = len(farm.get("hands", ()) or ())
        original_hire(farm, private, *args, **kwargs)
        if len(farm.get("hands", ()) or ()) > before:
            effective[player]["HIRE"] += 1

    def land(farm, *args, **kwargs):
        player = player_for(farm)
        before = len(farm.get("unlocked_quadrants", ()) or ())
        original_land(farm, *args, **kwargs)
        if len(farm.get("unlocked_quadrants", ()) or ()) > before:
            effective[player]["BUY_LAND"] += 1

    engine._apply_unit_action = unit
    engine._commit_unit = commit
    engine._do_hire = hire
    engine._do_buy_land = land
    engine._process_market = process_market
    try:
        env = make(
            "kaggriculture",
            configuration={"episodeSteps": 720, "seed": int(seed)},
            debug=False,
        )
        env.run(pair)
    finally:
        engine._apply_unit_action = original_unit
        engine._commit_unit = original_commit
        engine._do_hire = original_hire
        engine._do_buy_land = original_land
        engine._process_market = original_market

    final = env.steps[-1][seat].observation
    return {
        "candidate": str(candidate_path),
        "opponent": opponent_name,
        "seed": int(seed),
        "seat": int(seat),
        "money": {
            "candidate": float(final["farms"][seat]["money"]),
            "opponent": float(final["farms"][1 - seat]["money"]),
        },
        "candidate_effective": dict(sorted(effective[seat].items())),
        "opponent_effective": dict(sorted(effective[1 - seat].items())),
        "candidate_market_cash": dict(sorted(market_cash[seat].items())),
        "opponent_market_cash": dict(sorted(market_cash[1 - seat].items())),
        "candidate_harvested": dict(sorted(harvested[seat].items())),
        "opponent_harvested": dict(sorted(harvested[1 - seat].items())),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("candidate", type=Path)
    parser.add_argument("--opponent", required=True)
    parser.add_argument("--seed", required=True, type=int)
    parser.add_argument("--seat", type=int, choices=(0, 1), default=0)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = trace(args.candidate, args.opponent, args.seed, args.seat)
    rendered = json.dumps(result, indent=2, sort_keys=True)
    if args.output:
        args.output.write_text(rendered + "\n", encoding="utf-8")
    print(rendered)


if __name__ == "__main__":
    main()
