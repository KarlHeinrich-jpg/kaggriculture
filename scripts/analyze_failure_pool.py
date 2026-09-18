#!/usr/bin/env python3
"""Explain every loss of a white-box candidate against the public pool.

The report is deliberately trajectory based.  It consumes only the public
observations and the actions returned by both agents; it does not inspect
replays, opponent identities, private opponent inventory, or candidate
internals.  The classifier is a compact diagnostic heuristic, not a claim of
causal identification: every label is accompanied by measured evidence.
"""
from __future__ import annotations

import argparse
import csv
import json
import multiprocessing as mp
import os
import sys
from collections import Counter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from kaggle_environments import make  # noqa: E402
from route.match import load_module  # noqa: E402
from route.tournament import REFS  # noqa: E402
from search.evaluate import load_ref_agent  # noqa: E402


ANIMALS = ("COW", "SHEEP", "GOOSE")
UNIT_OPS = {
    "MOVE": {"NORTH", "SOUTH", "EAST", "WEST"},
    "PASS": {"PASS"},
    "BUILD": {"BUILD_PASTURE", "BUILD_COOP"},
    "PLACE": {"PLACE"},
    "PLANT": {"PLANT"},
    "SERVICE": {
        "WATER", "HARVEST", "FEED", "CARE", "FERTILIZE",
        "COLLECT_FERTILIZER", "CLEAR_WEED", "DIG", "PICKUP", "DROP",
    },
}


def _farm(obs, seat):
    farms = obs.get("farms") or []
    return farms[int(seat)] if 0 <= int(seat) < len(farms) else {}


def _tile_counts(obs, seat):
    farm = _farm(obs, seat)
    crops = Counter()
    animals = Counter()
    structures = Counter()
    weeds = 0
    for row in farm.get("tiles") or ():
        for tile in row or ():
            if not isinstance(tile, dict):
                continue
            kind = str(tile.get("kind") or "")
            if kind == "WEED":
                weeds += 1
            if tile.get("crop"):
                crops[str(tile["crop"])] += 1
            if tile.get("animal"):
                animals[str(tile["animal"])] += 1
            if kind in ("PASTURE", "COOP"):
                structures[kind] += 1
    return {
        "crops": dict(crops),
        "animals": {kind: int(animals.get(kind, 0)) for kind in ANIMALS},
        "structures": dict(structures),
        "weeds": int(weeds),
        "crop_total": int(sum(crops.values())),
        "animal_total": int(sum(animals.values())),
    }


def _shed_counts(obs, seat):
    # The candidate's own shed is public to the candidate.  We intentionally
    # do not use the opponent's private shed for diagnosis.
    if int(obs.get("player", -1)) != int(seat):
        return {}
    private = obs.get("private") or {}
    return {str(k): max(0, int(v or 0)) for k, v in
            (private.get("shed") or {}).items()}


def _action_ops(action):
    ops = []
    if not isinstance(action, dict):
        return ops
    orders = [action.get("farmer") or ["PASS"]]
    orders.extend(action.get("hands") or ())
    for order in orders:
        if isinstance(order, (list, tuple)) and order:
            ops.append(str(order[0]))
    return ops


def _market_counts(action):
    counts = Counter()
    quantities = Counter()
    if not isinstance(action, dict):
        return counts, quantities
    for order in action.get("market") or ():
        if not isinstance(order, (list, tuple)) or not order:
            continue
        op = str(order[0])
        counts[op] += 1
        if len(order) >= 3:
            quantities[(op, str(order[1]))] += max(0, int(order[2] or 0))
    return counts, quantities


def _asset_day(history, field, minimum=1):
    for row in history:
        if int(row.get(field, 0) or 0) >= int(minimum):
            return int(row.get("day", 0) or 0)
    return None


def _daily_max(history, field):
    return max((int(row.get(field, 0) or 0) for row in history), default=0)


def _first_unlock(history, count):
    for row in history:
        if len(row.get("unlocked", ()) or ()) >= int(count):
            return int(row.get("day", 0) or 0)
    return None


def _snapshot(obs, seat, action=None):
    farm = _farm(obs, seat)
    assets = _tile_counts(obs, seat)
    shed = _shed_counts(obs, seat)
    return {
        "step": int(obs.get("step", 0) or 0),
        "day": int(obs.get("day", 0) or 0),
        "hour": int(obs.get("hour", 0) or 0),
        "money": float(farm.get("money", 0.0) or 0.0),
        "unlocked": tuple(farm.get("unlocked_quadrants") or ()),
        "hands": len(farm.get("hands") or ()),
        "farmer": tuple(farm.get("farmer") or ()),
        "crop_total": assets["crop_total"],
        "animal_total": assets["animal_total"],
        "weeds": assets["weeds"],
        "animals": assets["animals"],
        "crops": assets["crops"],
        "shed": shed,
        "ops": _action_ops(action),
        # Keep the emitted public market queue in the trace.  This is useful
        # for diagnosing capital starvation/animal timing and contains no
        # private opponent state (the candidate's own queue is part of its
        # public action record).
        "market": [list(order) for order in (action or {}).get("market", ())]
        if isinstance(action, dict) else [],
    }


def _classify(row):
    """Return (primary, secondary, evidence) from measured public metrics."""
    me = row["me"]
    opp = row["opp"]
    evidence = []
    unlock_gap = []
    for count, label in ((2, "second_land_day"), (3, "third_land_day")):
        md = me.get(label)
        od = opp.get(label)
        if md is None and od is not None:
            unlock_gap.append(f"{label}=never_vs_day_{od}")
        elif md is not None and od is not None and md > od:
            unlock_gap.append(f"{label}=day_{md}_vs_{od}")
    if unlock_gap:
        evidence.append("land " + ", ".join(unlock_gap))

    animal_gap = int(opp["final_animal_total"] - me["final_animal_total"])
    crop_gap = int(opp["final_crop_total"] - me["final_crop_total"])
    hand_gap = int(opp["max_hands"] - me["max_hands"])
    weed_gap = int(me["final_weeds"] - opp["final_weeds"])
    if animal_gap:
        evidence.append(f"animals={me['final_animal_total']} vs {opp['final_animal_total']}")
    if crop_gap:
        evidence.append(f"crops={me['final_crop_total']} vs {opp['final_crop_total']}")
    if hand_gap:
        evidence.append(f"max_hands={me['max_hands']} vs {opp['max_hands']}")
    if weed_gap:
        evidence.append(f"weeds={me['final_weeds']} vs {opp['final_weeds']}")
    if me["pass_rate"] > 0.35:
        evidence.append(f"pass_rate={me['pass_rate']:.1%}")
    if me["market_buys"] < opp["market_buys"]:
        evidence.append(f"buy_qty={me['market_buys']} vs {opp['market_buys']}")
    if me["market_sells"] < opp["market_sells"]:
        evidence.append(f"sell_qty={me['market_sells']} vs {opp['market_sells']}")

    # Priority is based on the earliest structural bottleneck visible in the
    # trace, then on the terminal asset gap.  The labels are deliberately
    # broad so they remain useful across different public opponents.
    if me["final_animal_total"] <= 1 and animal_gap >= 4:
        primary = "动物资产规模不足"
        secondary = "资本候选或动物服务证书未形成可执行组合"
    elif unlock_gap and crop_gap >= 5:
        primary = "土地扩张偏晚"
        secondary = "新增土地没有及时转成作物资产"
    elif me["max_hands"] <= 2 and hand_gap >= 2:
        primary = "雇工规模不足"
        secondary = "路线吞吐受限"
    elif me["final_weeds"] >= 20 and weed_gap >= 8:
        primary = "杂草占用有效土地"
        secondary = "清理路线吞吐不足"
    elif me["pass_rate"] > 0.50:
        primary = "后半程空转"
        secondary = "任务调度未把新增资产转成有效工作"
    elif animal_gap >= 4:
        primary = "动物资产规模不足"
        secondary = "动物购买或放置速度落后"
    elif crop_gap >= 8:
        primary = "作物资产规模不足"
        secondary = "资本候选偏少或种植吞吐不足"
    elif hand_gap >= 2:
        primary = "雇工规模不足"
        secondary = "路线吞吐不足"
    elif me["market_sells"] + 4 < opp["market_sells"]:
        primary = "销售周转不足"
        secondary = "有效产出没有及时变现"
    elif me["final_cash"] < opp["final_cash"] and me["market_buys"] + 3 < opp["market_buys"]:
        primary = "资本投入不足"
        secondary = "有效资产数量不足"
    else:
        primary = "综合经济差距"
        secondary = "需要查看逐日资本候选和路线证书"
    return primary, secondary, "; ".join(evidence)


def _play(job):
    candidate_path, opponent_name, seed, candidate_seat = job
    try:
        module = load_module(candidate_path, prefix="failure_pool")
        candidate = getattr(module, "kaggriculture_agent", None)
        if candidate is None:
            candidate = getattr(module, "agent")
        opponent = load_ref_agent(opponent_name)
        env = make("kaggriculture", configuration={
            "episodeSteps": 720, "seed": int(seed),
        }, debug=False)
        pair = [candidate, opponent] if int(candidate_seat) == 0 else [opponent, candidate]
        histories = [[], []]
        action_counts = [Counter(), Counter()]
        market_quantities = [Counter(), Counter()]
        daily = [{}, {}]

        # Use Environment.run so each callback receives the same shared-state
        # projection as a real Kaggle agent.  Calling env.step directly would
        # expose the raw player-1 state, whose shared step/day fields are None.
        def recording_agent(fn, seat):
            def wrapped(obs):
                action = fn(obs)
                snap = _snapshot(obs, seat, action)
                histories[seat].append(snap)
                action_counts[seat].update(snap["ops"])
                _counts, quantities = _market_counts(action)
                action_counts[seat].update("MKT_" + k for k in _counts.elements())
                market_quantities[seat].update(quantities)
                if snap["hour"] == 0:
                    daily[seat][snap["day"]] = snap
                return action
            return wrapped

        run_states = env.run([
            recording_agent(pair[0], 0),
            recording_agent(pair[1], 1),
        ])
        final_states = run_states[-1]
        final_obs = [final_states[i].observation for i in range(2)]
        finals = [_snapshot(final_obs[i], i) for i in range(2)]
        metrics = []
        for i in range(2):
            history = histories[i]
            final = finals[i]
            total_ops = max(1, sum(action_counts[i].values()))
            pass_rate = action_counts[i].get("PASS", 0) / total_ops
            buys = sum(q for (op, _item), q in market_quantities[i].items()
                       if op in ("BUY_SEED", "BUY_ANIMAL", "BUY_PRODUCT", "BUY_LAND"))
            sells = sum(q for (op, _item), q in market_quantities[i].items()
                        if op == "SELL")
            metrics.append({
                "final_cash": float(final["money"]),
                "final_animals": final["animals"],
                "final_animal_total": int(final["animal_total"]),
                "final_crops": final["crops"],
                "final_crop_total": int(final["crop_total"]),
                "final_weeds": int(final["weeds"]),
                "final_unlocked": list(final["unlocked"]),
                "max_hands": max((h["hands"] for h in history), default=0),
                "max_animals": max((h["animal_total"] for h in history), default=0),
                "max_crops": max((h["crop_total"] for h in history), default=0),
                "second_land_day": _first_unlock(history, 2),
                "third_land_day": _first_unlock(history, 3),
                "pass_rate": float(pass_rate),
                "ops": dict(action_counts[i]),
                "market_buys": int(buys),
                "market_sells": int(sells),
                "market_quantities": {
                    f"{op}:{item}": int(qty)
                    for (op, item), qty in sorted(market_quantities[i].items())
                },
                "history": history,
            })
        me_idx = int(candidate_seat)
        opp_idx = 1 - me_idx
        row = {
            "opponent": opponent_name,
            "seed": int(seed),
            "seat": int(candidate_seat),
            "status": [str(state.status) for state in final_states],
            "me": metrics[me_idx],
            "opp": metrics[opp_idx],
        }
        primary, secondary, evidence = _classify(row)
        row.update({"primary_reason": primary,
                    "secondary_reason": secondary,
                    "evidence": evidence,
                    "margin": row["me"]["final_cash"] - row["opp"]["final_cash"]})
        # Histories are useful for deep inspection but make the summary too
        # large. Keep them in JSON, while the CSV only receives the evidence.
        return row
    except Exception as exc:
        return {"opponent": opponent_name, "seed": int(seed),
                "seat": int(candidate_seat), "error": repr(exc)}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidate", default=os.path.join(
        ROOT, "submission", "whitebox_v223_spatial_throughput.py"))
    parser.add_argument("--seeds", type=int, nargs="*", default=[11, 47, 101])
    parser.add_argument("--opponents", nargs="*", default=REFS)
    parser.add_argument("--workers", type=int, default=8)
    parser.add_argument("--output", required=True)
    parser.add_argument("--csv", default="")
    args = parser.parse_args(argv)
    jobs = [(args.candidate, opponent, seed, seat)
            for opponent in args.opponents for seed in args.seeds
            for seat in (0, 1)]
    context = mp.get_context("forkserver")
    with context.Pool(processes=max(1, int(args.workers))) as pool:
        rows = pool.map(_play, jobs)
    rows.sort(key=lambda row: (row.get("opponent", ""), row.get("seed", 0), row.get("seat", 0)))
    with open(args.output, "w", encoding="utf-8") as handle:
        json.dump(rows, handle, indent=2, ensure_ascii=False, sort_keys=True)
    if args.csv:
        fields = ["opponent", "seed", "seat", "margin", "primary_reason",
                  "secondary_reason", "evidence", "status"]
        with open(args.csv, "w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=fields)
            writer.writeheader()
            for row in rows:
                writer.writerow({field: json.dumps(row.get(field), ensure_ascii=False)
                                 if field == "status" else row.get(field, "")
                                 for field in fields})
    good = [row for row in rows if "error" not in row]
    print(f"wrote {args.output}: {len(rows)} games, errors={len(rows)-len(good)}")
    counts = Counter(row.get("primary_reason") for row in good)
    for reason, count in counts.most_common():
        print(f"{reason}: {count}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
