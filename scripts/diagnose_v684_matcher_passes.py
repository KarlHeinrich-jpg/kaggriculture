#!/usr/bin/env python3
"""Aggregate why V684's public one-step matcher emits PASS actions."""

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


class MatcherDiagnosis:
    def __init__(self, code):
        self.code = code
        self.totals = Counter()
        self.by_day = defaultdict(Counter)
        self.by_operation = defaultdict(Counter)

    @staticmethod
    def _target_key(mission, target, liquidation):
        if mission.get("kind") != "FIELD":
            return target
        operation = str((mission.get("action") or ["PASS"])[0])
        if (
            liquidation
            and operation in {"HARVEST", "COLLECT_FERTILIZER"}
        ) or operation == "FERTILIZE":
            return (target, operation)
        return target

    def profile(self, frame, event, result):
        if event != "return" or frame.f_code is not self.code:
            return
        try:
            self._record(frame.f_locals, result)
        except Exception as exc:
            self.totals[f"diagnostic_error:{type(exc).__name__}"] += 1

    def _record(self, local, result):
        obs = local.get("obs") or {}
        day = int(obs.get("day", 0) or 0)
        positions = list(local.get("positions") or ())
        missions = list(local.get("missions") or ())
        pairs = list(local.get("pairs") or ())
        used_missions = set(local.get("used_missions") or ())
        used_targets = set(local.get("used_targets") or ())
        liquidation = bool(local.get("liquidation", False))
        seed_budget = dict(local.get("seed_budget") or {})
        actions = [list((result or {}).get("farmer") or ["PASS"])]
        actions.extend(
            list(action or ["PASS"])
            for action in ((result or {}).get("hands") or ())
        )
        daily = self.by_day[day]
        daily["calls"] += 1
        daily["jobs"] += len(local.get("jobs") or ())
        daily["missions"] += len(missions)
        daily["pairs"] += len(pairs)
        daily["workers"] += len(positions)

        by_worker = defaultdict(list)
        for pair in pairs:
            by_worker[int(pair[2])].append(pair)

        for worker, action in enumerate(actions):
            if action != ["PASS"]:
                continue
            self.totals["pass_workers"] += 1
            daily["pass_workers"] += 1
            worker_pairs = by_worker.get(worker, ())
            if not worker_pairs:
                self.totals["pass_no_pair"] += 1
                daily["pass_no_pair"] += 1
                position = positions[worker]
                inventory = (local.get("inventories") or [{}])[worker]
                blocked = Counter()
                for mission_index, mission in enumerate(missions):
                    kind = mission.get("kind")
                    if kind == "DROP":
                        if mission.get("eligible") != worker:
                            blocked["drop_other_worker"] += 1
                        else:
                            blocked["drop_not_emittable"] += 1
                        continue
                    if kind == "FIELD":
                        need = mission.get("need")
                        if need is not None and int(
                            inventory.get(need, 0) or 0
                        ) <= 0:
                            blocked[f"missing_{need}"] += 1
                            continue
                        target = tuple(mission.get("target", ()))
                        distance = self.code and abs(
                            int(position[0]) - int(target[0])
                        ) + abs(int(position[1]) - int(target[1]))
                        if int(local.get("hour", 0)) + distance > int(
                            mission.get("latest_hour", 23)
                        ):
                            blocked["past_latest_hour"] += 1
                            continue
                        blocked["target_or_other"] += 1
                        continue
                    blocked[f"mission_{kind}"] += 1
                for reason, count in blocked.items():
                    self.totals[f"no_pair:{reason}"] += count
                    daily[f"no_pair:{reason}"] += count
                continue
            self.totals["pass_with_pair"] += 1
            daily["pass_with_pair"] += 1
            reasons = Counter()
            for pair in worker_pairs:
                mission_index = int(pair[3])
                mission = missions[mission_index]
                target = pair[6]
                operation = (
                    str((mission.get("action") or [mission.get("kind")])[0])
                    if mission.get("kind") == "FIELD"
                    else str(mission.get("kind"))
                )
                self.by_operation[operation]["pass_pairs"] += 1
                if mission_index in used_missions:
                    reasons["mission_used"] += 1
                    self.by_operation[operation]["mission_used"] += 1
                    continue
                target_key = self._target_key(
                    mission, target, liquidation
                )
                if mission.get("kind") == "FIELD" and target_key in used_targets:
                    reasons["target_conflict"] += 1
                    self.by_operation[operation]["target_conflict"] += 1
                    continue
                planned = mission.get("action") or ()
                if (
                    planned
                    and planned[0] == "PLANT"
                    and int(seed_budget.get(planned[1], 0) or 0) <= 0
                ):
                    reasons["seed_exhausted"] += 1
                    self.by_operation[operation]["seed_exhausted"] += 1
                    continue
                reasons["unexplained_available"] += 1
                self.by_operation[operation]["unexplained_available"] += 1
            for reason in reasons:
                self.totals[f"pass_has:{reason}"] += 1
                daily[f"pass_has:{reason}"] += 1
            if reasons and sum(reasons.values()) == reasons["mission_used"]:
                self.totals["pass_only_mission_used"] += 1
            elif reasons and sum(reasons.values()) == reasons["target_conflict"]:
                self.totals["pass_only_target_conflict"] += 1
            elif reasons and sum(reasons.values()) == reasons["seed_exhausted"]:
                self.totals["pass_only_seed_exhausted"] += 1

    def payload(self, opponent, seed, seat, final):
        observation = final[seat].observation
        candidate_money = float(observation["farms"][seat]["money"])
        opponent_money = float(observation["farms"][1 - seat]["money"])
        return {
            "opponent": opponent,
            "seed": int(seed),
            "seat": int(seat),
            "candidate_final": candidate_money,
            "opponent_final": opponent_money,
            "margin": candidate_money - opponent_money,
            "status": [str(getattr(player, "status", "")) for player in final],
            "totals": dict(sorted(self.totals.items())),
            "by_day": {
                str(day): dict(sorted(values.items()))
                for day, values in sorted(self.by_day.items())
            },
            "by_operation": {
                operation: dict(sorted(values.items()))
                for operation, values in sorted(self.by_operation.items())
            },
        }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--opponent", required=True)
    parser.add_argument("--seed", required=True, type=int)
    parser.add_argument("--seat", required=True, type=int, choices=(0, 1))
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()

    candidate_module = load_module(
        str(ROOT / "submission" / "whitebox_v684.py"),
        prefix="v684_matcher_diagnosis",
    )
    candidate_agent = candidate_module.kaggriculture_agent
    c06 = sys.modules["whitebox.versions.v239_public_scenario_c06"]
    diagnosis = MatcherDiagnosis(c06._unit_actions.__code__)

    def candidate(observation, configuration=None):
        sys.setprofile(diagnosis.profile)
        try:
            return candidate_agent(observation, configuration)
        finally:
            sys.setprofile(None)

    opponent = load_ref_agent(args.opponent)
    pair = [candidate, opponent] if args.seat == 0 else [opponent, candidate]
    environment = make(
        "kaggriculture",
        configuration={"episodeSteps": 720, "seed": int(args.seed)},
        debug=False,
    )
    environment.run(pair)
    payload = diagnosis.payload(
        args.opponent, args.seed, args.seat, environment.steps[-1]
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(json.dumps(payload["totals"], sort_keys=True))
    print(f"margin={payload['margin']:.0f} saved={args.output}")


if __name__ == "__main__":
    main()
