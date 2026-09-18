#!/usr/bin/env python3
"""Play a self-contained white-box submission against the public pool.

Each job loads fresh candidate/opponent modules and uses both seat orders on
the same seed.  The script is diagnostic only; it is not reachable from a
Kaggriculture submission bundle and never loads a replay action tape.
"""
from __future__ import annotations

import argparse
import json
import multiprocessing as mp
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from route.match import load_module, run_episode  # noqa: E402
from route.tournament import REFS  # noqa: E402
from search.evaluate import load_ref_agent  # noqa: E402


def _play(job):
    candidate_path, opponent_name, seed, seat = job
    try:
        candidate_module = load_module(
            candidate_path, prefix="whitebox_pool_candidate",
        )
        candidate = getattr(candidate_module, "kaggriculture_agent", None)
        if candidate is None:
            candidate = getattr(candidate_module, "agent")
        opponent = load_ref_agent(opponent_name)
        result = run_episode(candidate, opponent, int(seed), seat=int(seat))
        return {
            "opponent": opponent_name,
            "seed": int(seed),
            "seat": int(seat),
            "me": float(result.me),
            "opp": float(result.opp),
            "win": bool(result.me > result.opp),
            "tie": bool(result.me == result.opp),
            "status": list(result.status),
            "error": None,
        }
    except Exception as exc:  # keep one bad public model from hiding others
        return {
            "opponent": opponent_name,
            "seed": int(seed),
            "seat": int(seat),
            "me": 0.0,
            "opp": 0.0,
            "win": False,
            "tie": False,
            "status": [],
            "error": repr(exc),
        }


def _summary(rows, opponents):
    print("\n" + "opponent".ljust(48) + "win%  W/G   mean margin   errors")
    total_wins = total_games = total_errors = 0
    for opponent in opponents:
        group = [row for row in rows if row["opponent"] == opponent]
        good = [row for row in group if row["error"] is None]
        wins = sum(int(row["win"]) for row in good)
        margin = sum(row["me"] - row["opp"] for row in good)
        errors = len(group) - len(good)
        games = len(good)
        print(
            opponent.ljust(48)
            + f"{wins / max(games, 1):5.0%}"
            + f" {wins:2d}/{games:<2d}"
            + f" {margin / max(games, 1):13,.0f}"
            + f" {errors:7d}"
        )
        total_wins += wins
        total_games += games
        total_errors += errors
    print(
        "TOTAL".ljust(48)
        + f"{total_wins / max(total_games, 1):5.0%}"
        + f" {total_wins:2d}/{total_games:<2d}"
        + f" {sum(r['me'] - r['opp'] for r in rows if not r['error']) / max(total_games, 1):13,.0f}"
        + f" {total_errors:7d}"
    )
    return {
        "wins": total_wins,
        "games": total_games,
        "errors": total_errors,
        "win_rate": total_wins / max(total_games, 1),
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--candidate",
        default=os.path.join(ROOT, "submission", "whitebox_v223_spatial_throughput.py"),
    )
    parser.add_argument("--seeds", type=int, nargs="*", default=[11, 47, 101])
    parser.add_argument("--workers", type=int, default=12)
    parser.add_argument("--output", default="")
    parser.add_argument("--opponents", nargs="*", default=REFS)
    args = parser.parse_args(argv)

    jobs = [
        (args.candidate, opponent, seed, seat)
        for opponent in args.opponents
        for seed in args.seeds
        for seat in (0, 1)
    ]
    print(
        f"candidate={args.candidate}\n"
        f"opponents={len(args.opponents)} seeds={list(args.seeds)} "
        f"seats=2 games={len(jobs)} workers={args.workers}",
        flush=True,
    )
    context = mp.get_context("forkserver")
    with context.Pool(processes=max(1, int(args.workers))) as pool:
        rows = pool.map(_play, jobs)
    overall = _summary(rows, args.opponents)
    payload = {
        "candidate": os.path.abspath(args.candidate),
        "opponents": list(args.opponents),
        "seeds": list(args.seeds),
        "rows": rows,
        "overall": overall,
    }
    if args.output:
        with open(args.output, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2, sort_keys=True)
        print(f"saved -> {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
