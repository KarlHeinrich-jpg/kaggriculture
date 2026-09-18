#!/usr/bin/env python3
"""Aggregate why V684 passes while public positive-value tasks remain.

This is an offline diagnostic. It records counts and feasibility certificates,
never observations, routes, replay actions, or opponent-private state.
"""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from kaggle_environments import make  # noqa: E402
from route.match import load_module  # noqa: E402
from search.evaluate import load_ref_agent  # noqa: E402


router = None


def _task_key(task):
    operations = "+".join(
        str(action[0]) for action in task.ops if action
    ) or str(task.kind)
    carry = "+".join(
        f"{item}:{int(quantity)}"
        for item, quantity in sorted(task.carry.items())
        if int(quantity) > 0
    )
    return f"{operations}|carry={carry or '-'}"


def _missing_carry(task, inventory):
    return {
        item: max(0, int(quantity) - int(inventory.get(item, 0) or 0))
        for item, quantity in task.carry.items()
        if int(quantity) > int(inventory.get(item, 0) or 0)
    }


def _single_task_cost(unit, task, inventory, missing, bank_outputs):
    position = tuple(unit.start)
    cost = 0
    if missing:
        anchor = min(
            router.SHED_TILES,
            key=lambda tile: (router.dist(position, tile), tile),
        )
        cost += router.dist(position, anchor) + len(missing)
        position = anchor
    cost += router.dist(position, tuple(task.pos)) + int(task.n_ops)
    if bank_outputs and router._route_banks_output([task]):
        cost += min(
            router.dist(tuple(task.pos), shed)
            for shed in router.SHED_TILES
        ) + 1
    return cost


class Diagnosis:
    def __init__(self):
        self.context = None
        self.live_call = None
        self.totals = Counter()
        self.by_operation = defaultdict(Counter)
        self.by_day = defaultdict(Counter)
        self.live_by_day = defaultdict(Counter)

    def wrap_plan_day(self, original):
        def wrapped(units, tasks, *args, **kwargs):
            units = list(units)
            tasks = list(tasks)
            stock = kwargs.get("shed_stock")
            if stock is None and args:
                stock = args[0]
            try:
                stock_before = {
                    str(item): max(0, int(quantity or 0))
                    for item, quantity in (stock or {}).items()
                }
            except Exception as exc:
                stock_before = {}
                self.totals[f"hook_stock_error:{type(exc).__name__}"] += 1
            tours, undone = original(units, tasks, *args, **kwargs)
            try:
                frame = sys._getframe(1)
                caller = (
                    f"{frame.f_globals.get('__name__', 'unknown')}:"
                    f"{frame.f_code.co_name}"
                )
                context = self.context or {}
                positions = [
                    tuple(value) for value in context.get("positions", ())
                ]
                is_live = (
                    len(units) == len(positions)
                    and all(
                        int(unit.idx) == index
                        and tuple(unit.start) == positions[index]
                        and int(unit.start_hour) == int(context.get("hour", -1))
                        for index, unit in enumerate(units)
                    )
                )
                if is_live:
                    day = int(context.get("day", -1))
                    hour = int(context.get("hour", -1))
                    selected_ids = {
                        id(task)
                        for tour in tours.values()
                        for task in ((tour or {}).get("tasks", ()) or ())
                    }
                    selected = [
                        task for task in tasks if id(task) in selected_ids
                    ]
                    positive_undone = [
                        task for task in undone
                        if task.ops and float(task.value) > 0.0
                    ]
                    daily = self.live_by_day[day]
                    daily["calls"] += 1
                    daily["unit_budgets"] += sum(
                        int(unit.budget) for unit in units
                    )
                    daily["tasks"] += len(tasks)
                    daily["task_ops"] += sum(
                        int(task.n_ops) for task in tasks
                    )
                    daily["selected_tasks"] += len(selected)
                    daily["selected_ops"] += sum(
                        int(task.n_ops) for task in selected
                    )
                    daily["positive_undone"] += len(positive_undone)
                    daily[f"hour_{hour}_tasks"] += len(tasks)
                    for task in tasks:
                        for action in task.ops:
                            if action:
                                daily[f"task_op:{action[0]}"] += 1
                    for task in selected:
                        for action in task.ops:
                            if action:
                                daily[f"selected_op:{action[0]}"] += 1
                    self.live_call = {
                        "caller": caller,
                        "units": units,
                        "stock": stock_before,
                        "tours": tours,
                        "undone": list(undone),
                        "bank_outputs": bool(
                            kwargs.get("bank_outputs", False)
                        ),
                    }
            except Exception as exc:
                self.totals[f"hook_record_error:{type(exc).__name__}"] += 1
            return tours, undone

        return wrapped

    def begin(self, observation):
        player = int(observation.get("player", 0) or 0)
        farm = observation["farms"][player]
        private = observation.get("private", {}) or {}
        self.context = {
            "day": int(observation.get("day", 0) or 0),
            "hour": int(observation.get("hour", 0) or 0),
            "positions": [
                tuple(farm["farmer"]),
                *(tuple(value) for value in (farm.get("hands", []) or [])),
            ],
            "inventories": [
                dict(value or {})
                for value in (private.get("inventories", []) or [])
            ],
        }
        self.live_call = None

    def finish(self, action):
        actions = [action.get("farmer", ["PASS"])]
        actions.extend(action.get("hands", ()) or ())
        pass_units = {
            index for index, value in enumerate(actions)
            if value == ["PASS"]
        }
        if not pass_units:
            return
        positions = list(self.context.get("positions", ()))
        inventories = list(self.context.get("inventories", ()))
        for primary_index, primary_action in enumerate(actions):
            if (
                primary_index >= len(positions)
                or not primary_action
                or primary_action[0] in {
                    "PASS", "NORTH", "SOUTH", "EAST", "WEST",
                    "PICKUP", "DROP",
                }
            ):
                continue
            colocated_idle = [
                index for index in pass_units
                if index < len(positions)
                and index > primary_index
                and tuple(positions[index]) == tuple(positions[primary_index])
            ]
            if not colocated_idle:
                continue
            self.totals["primary_ops_with_later_colocated_pass"] += 1
            self.totals["later_colocated_pass_units"] += len(colocated_idle)
        self.totals["pass_unit_turns"] += len(pass_units)
        self.totals["pass_turns_with_live_call"] += self.live_call is not None
        if self.live_call is None:
            return
        call = self.live_call
        self.totals[f"pass_live_caller:{call['caller']}"] += 1
        day = int(self.context["day"])
        inventories = self.context["inventories"]
        selected_ids = {
            id(task)
            for tour in call["tours"].values()
            for task in ((tour or {}).get("tasks", ()) or ())
        }
        positive = [
            task for task in call["undone"]
            if task.ops and float(task.value) > 0.0
        ]
        if positive:
            self.totals["pass_turns_with_positive_undone"] += 1
            self.totals["positive_undone_tasks"] += len(positive)
        for unit_index in sorted(pass_units):
            if unit_index >= len(call["units"]):
                continue
            unit = call["units"][unit_index]
            tour = call["tours"].get(unit_index) or {}
            tour_tasks = list(tour.get("tasks", ()) or ())
            tour_stops = list(tour.get("stops", ()) or ())
            inventory = (
                inventories[unit_index]
                if unit_index < len(inventories)
                else {}
            )
            if not tour_tasks:
                self.totals["pass_unit_empty_tour"] += 1
            elif not tour_stops:
                self.totals["pass_unit_tasks_without_stops"] += 1
            else:
                self.totals["pass_unit_nonempty_tour"] += 1
                for task in tour_tasks:
                    self.by_operation[_task_key(task)]["selected_for_pass"] += 1
                tour_missing = _missing_carry(
                    type("TourCarry", (), {"carry": tour.get("carry", {})})(),
                    inventory,
                )
                available_missing = {
                    item: quantity
                    for item, quantity in tour_missing.items()
                    if int(call["stock"].get(item, 0) or 0) > 0
                }
                executable = False
                for _position, operations in tour_stops:
                    for operation in operations:
                        if not operation:
                            continue
                        need = None
                        if operation[0] == "FEED":
                            need = "WHEAT"
                        elif operation[0] == "FERTILIZE":
                            need = "FERTILIZER"
                        elif operation[0] == "PLACE" and len(operation) > 1:
                            need = str(operation[1])
                        if need is None or int(inventory.get(need, 0) or 0) > 0:
                            executable = True
                            break
                    if executable:
                        break
                self.totals["pass_nonempty_available_missing"] += bool(
                    available_missing
                )
                self.totals["pass_nonempty_executable_stop"] += executable
                if not available_missing and not executable:
                    self.totals["pass_nonempty_input_blocked"] += 1
            feasible = []
            for task in positive:
                if id(task) in selected_ids:
                    continue
                missing = _missing_carry(task, inventory)
                stock_ok = all(
                    int(quantity) <= int(call["stock"].get(item, 0) or 0)
                    for item, quantity in missing.items()
                )
                cost = _single_task_cost(
                    unit,
                    task,
                    inventory,
                    missing,
                    call["bank_outputs"],
                )
                time_ok = cost <= int(unit.budget)
                key = _task_key(task)
                counter = self.by_operation[key]
                counter["seen"] += 1
                counter["stock_ok"] += stock_ok
                counter["time_ok"] += time_ok
                counter["strict_feasible"] += stock_ok and time_ok
                counter["already_carried"] += not missing
                if stock_ok and time_ok:
                    feasible.append((cost, -float(task.value), key))
            if feasible:
                best = min(feasible)
                self.totals["pass_units_with_strict_feasible_task"] += 1
                self.by_day[day]["pass_units_with_strict_feasible_task"] += 1
                self.by_operation[best[2]]["best_for_pass_unit"] += 1

    def payload(self, opponent, seed, seat, final_money, opponent_money, status):
        return {
            "opponent": opponent,
            "seed": int(seed),
            "seat": int(seat),
            "candidate_final": float(final_money),
            "opponent_final": float(opponent_money),
            "margin": float(final_money - opponent_money),
            "status": list(status),
            "totals": dict(sorted(self.totals.items())),
            "by_day": {
                str(day): dict(sorted(values.items()))
                for day, values in sorted(self.by_day.items())
            },
            "live_by_day": {
                str(day): dict(sorted(values.items()))
                for day, values in sorted(self.live_by_day.items())
            },
            "by_operation": {
                key: dict(sorted(values.items()))
                for key, values in sorted(self.by_operation.items())
            },
        }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--opponent", required=True)
    parser.add_argument("--seed", required=True, type=int)
    parser.add_argument("--seat", required=True, type=int, choices=(0, 1))
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()

    global router
    candidate_module = load_module(
        str(ROOT / "submission" / "whitebox_v684.py"),
        prefix="v684_router_diagnosis",
    )
    candidate_agent = candidate_module.kaggriculture_agent
    router = sys.modules["route.router"]
    diagnosis = Diagnosis()
    original_plan_day = router.plan_day
    router.plan_day = diagnosis.wrap_plan_day(original_plan_day)

    def candidate(observation, configuration=None):
        try:
            diagnosis.begin(observation)
        except Exception as exc:
            diagnosis.totals[f"hook_begin_error:{type(exc).__name__}"] += 1
        action = candidate_agent(observation, configuration)
        try:
            diagnosis.finish(action)
        except Exception as exc:
            diagnosis.totals[f"hook_finish_error:{type(exc).__name__}"] += 1
        return action

    opponent = load_ref_agent(args.opponent)
    pair = [candidate, opponent] if args.seat == 0 else [opponent, candidate]
    environment = make(
        "kaggriculture",
        configuration={"episodeSteps": 720, "seed": int(args.seed)},
        debug=False,
    )
    environment.run(pair)
    final = environment.steps[-1]
    candidate_money = final[args.seat].observation["farms"][args.seat]["money"]
    opponent_money = final[args.seat].observation["farms"][1 - args.seat]["money"]
    status = tuple(str(getattr(player, "status", "")) for player in final)
    payload = diagnosis.payload(
        args.opponent,
        args.seed,
        args.seat,
        candidate_money,
        opponent_money,
        status,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(json.dumps(payload["totals"], sort_keys=True))
    print(f"margin={payload['margin']:.0f} saved={args.output}")


if __name__ == "__main__":
    main()
