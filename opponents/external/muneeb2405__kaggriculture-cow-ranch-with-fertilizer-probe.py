import warnings
warnings.filterwarnings("ignore")

import base64
import copy
import hashlib
import json
import math
import subprocess
import sys
import tarfile
import zlib
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

try:
    installed_ke = version("kaggle-environments")
except PackageNotFoundError:
    installed_ke = "0"

# Same load-bearing version floor the source notebook uses -- 1.32.4 changed
# BUY_PRODUCT/BUY_SEED behaviour when the shed is full, which matters for the
# terminal-liquidation logic reused below.
if tuple(map(int, installed_ke.split(".")[:3])) < (1, 32, 4):
    subprocess.check_call([sys.executable, "-m", "pip", "install", "-q", "-U", "kaggle-environments>=1.32.4"])

import kaggle_environments
print("kaggle-environments", kaggle_environments.__version__)
from kaggle_environments import make

WORK = Path("/kaggle/working")
if not WORK.exists():
    WORK = Path.cwd()


# Exact c68 source from the frozen final gate, compressed so the notebook stays
# readable. Copied byte-for-byte from "Kaggriculture: notes from replay
# hunting" (submission 55371099) -- this whole blob is public, competitor-
# derived replay + controller data, credited as such per that notebook's own
# provenance note in its section 12.
_AGENT_B64_PARTS = [
    "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"
    "dY8ZwNBrvx6h5YsJ0TTKiwFZ86xALlUJvOlE1X28eZE3L4ZWeUDhd2VrIDOuJP9bGycLrCb3R8PkPjm2BsInf9ZEzT//W5/2W32u"
    "kfTzBqazXX2gk3F7qOtU92+c9Cv7H+bohubGwtttb/wqKZ/cg6troeH+mnsGX26C9vGNTwPeF00D3xDsmtYF+0O1KlNizSqJhmqD"
    "HxEMI2t3o3VzfAXWTOznyEVv1EkwIzMmrz7VYryE9oFQFOmG6X2mr6A+4G08kmBZ7c46YHT6PJDx/ItRHu3mMZ7hrlPXblTjhjQB"
    "xq/rOMYXbeuoED8omha1D1cYs/NwHezhJ79PCYmjJdWXZFXDB5hF9dpiiOl7M4Nh779MHu/7XJVCzT39qfc0pN0M+hLdmVEbXW/b"
    "8ZcJ6XV/PGH9HaaX+PCK6h7s3oOQJ2H0GQb2SYNoF/BpPY9483MeEZP3hk5jyVV0VcRXpNpDzRnTCTZh1J8/6x0TDXrr1RXXNL4W"
    "NRlxtt4CGiMf7zMhWGbG4zrjgJuGekzsLgBfycjbi23Wg3ldgT7m8+AU+HFb2k+k649vM/1+Pd9MykxvUb3h+/iPjaE3/VB9LJqn"
    "gJ83sdHXGn/4IHe6PSZ84HUQg4af1/E13fR3wqjD//znhvvXL/PKGEjvEjRXTQhBktoLCGTmcFMxc4KdaqpQfWL5z38s/q93F6CD"
    "eTTrePuksld/an7yHfwzLPgi22psv9DJ12k02y6TYGoi8eUqX2MiZnO1bKadYDw0m9Mr8HW8p0BbVVT/mA2Irr+MHfQce+gazWhV"
    "V+ARCF6H0yoB6jSe4p0fmn8oA+DbI5a9eQpaTs685R5YTBCfJVgUZMZ44YgqKnpHjTkfdzWodlDn4VX1nMX1QH6F+bwrDLlZ84yC"
    "315kouL9Qol+mDToFfNv9KGOVWHYlzleydAbPk/NkFE982ISWW3P6B10WN81eNJjQZ6idx9m4rV1ofm1Sq9moc2zAp+cFL2n5p/o"
    "GaYbR/UBnppMK/ESLHyKUW5YVPLvCH/qyH6ZR9bykibLfgNVt4nGpQ/DOTRCXzNtmv7x/4EClRX7a+x76/ZTl4OnJ77nFCSg9QIN"
    "svjbCqiDP/Kn+6tSv66B5rjpz3fm5z/3v8A/ceiRnlZ33+823XebzbQaV86+7LKzeWZmsdCINn2/uaJ5VCsqvWQQdE7JOiOv9D5t"
    "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"
]
_AGENT_B64 = "".join(_AGENT_B64_PARTS)
EXPECTED_MAIN_SHA256 = "e5cbb6ed75e8582ed27dab18539f3b14e20f87d591181936c38cd1697ffbc248"
EXPECTED_MAIN_BYTES = 31149

raw = zlib.decompress(base64.b64decode(_AGENT_B64.encode("ascii")))
assert len(raw) == EXPECTED_MAIN_BYTES, (len(raw), EXPECTED_MAIN_BYTES)
digest = hashlib.sha256(raw).hexdigest()
print("decoded", len(raw), "bytes, sha256 matches source notebook:", digest == EXPECTED_MAIN_SHA256)

C68_MAIN_PATH = WORK / "c68_main.py"
C68_MAIN_PATH.write_bytes(raw)
compile(raw, str(C68_MAIN_PATH), "exec")

import importlib.util
spec = importlib.util.spec_from_file_location("main_c68", C68_MAIN_PATH)
main_c68 = importlib.util.module_from_spec(spec)
sys.modules["main_c68"] = main_c68  # so smart_wrapper's `import main_c68 as base` resolves to this
spec.loader.exec_module(main_c68)
print(main_c68.__version__)


env = make("kaggriculture", configuration={"episodeSteps": 720, "seed": 0}, debug=False)
env.run([main_c68.agent, "starter"])
final = env.steps[-1]
print("status:", [row["status"] for row in final])
print("reward:", [row["reward"] for row in final])


def market_price(base, equilibrium, scale, below_func, below_target, above_func, above_target, inventory):
    def shape(name, value):
        value = max(0.0, float(value))
        return {"linear": value, "sq": value * value, "sqrt": math.sqrt(value),
                "log": math.log1p(value), "log10": math.log10(1.0 + value)}[name]
    if inventory < equilibrium:
        amplitude = below_target * base / shape(below_func, scale)
        price = base + amplitude * shape(below_func, equilibrium - inventory)
    else:
        amplitude = above_target * base / shape(above_func, scale)
        price = base - amplitude * shape(above_func, inventory - equilibrium)
    return max(1, price)

inv = np.linspace(9700, 10300, 300)
fig, axes = plt.subplots(1, 2, figsize=(11, 4))
for ax, item in zip(axes, ["MELON", "WOOL"]):
    params = main_c68._MARKET_PARAMS[item]
    prices = [market_price(*params, i) for i in inv]
    ax.plot(inv, prices)
    ax.axvline(10000, color="gray", linestyle="--", linewidth=1, label="equilibrium (10,000)")
    ax.set_title(f"{item} price vs. market inventory")
    ax.set_xlabel("market inventory")
    ax.set_ylabel("price")
    ax.legend()
plt.tight_layout()
plt.show()
print("MELON decays fastest above equilibrium (above_target=3.6, sq) -- selling a big MELON batch")
print("at once is expensive. WOOL is nearly as steep. This is exactly why order-within-turn matters.")


# A minimal synthetic "clone" opponent: identical field/hand tape to c68 (so
# the clone-distance gate stays low, matching the real "converged field,
# different market timing" scenario the source notebook describes in its own
# section 4.7), but premium SELL orders are shifted a few turns later. This
# lets us count how many inference-worthy events a real game actually
# produces, without needing a second real leaderboard bot to test against.
def make_shifted_opponent(shift):
    def agent(obs):
        try:
            step = min(max(0, int(main_c68._get(obs, "step", 0) or 0)), len(main_c68._ACTIONS) - 1)
            tape_step = min(max(0, step - shift), len(main_c68._ACTIONS) - 1)
            raw_action = main_c68._copy_action(main_c68._ACTIONS[step])
            tape_market = main_c68._ACTIONS[tape_step].get("market") or []
            new_market = [o for o in raw_action.get("market", [])
                          if not (main_c68._is_sell(o) and o[1] in main_c68._PREMIUM)]
            for order in tape_market:
                if main_c68._is_sell(order) and order[1] in main_c68._PREMIUM:
                    new_market.append(["SELL", order[1], max(0, int(order[2]))])
            raw_action["market"] = new_market[:10]
            action = main_c68._weed_repair_action(obs, raw_action, step)
            action = main_c68._terminal_liquidation(obs, action, step)
            return main_c68._align_hands(action, obs)
        except Exception:
            farm = main_c68._farm(obs, main_c68._seat(obs))
            return {"farmer": ["PASS"], "hands": [["PASS"] for _ in (main_c68._get(farm, "hands", []) or [])], "market": []}
    return agent

opponent = make_shifted_opponent(shift=3)

event_log = []
orig_observe = main_c68._observe_opponent_market
def traced_observe(obs, step):
    result = orig_observe(obs, step)
    seat = main_c68._seat(obs)
    event_log.append(main_c68._RACE_STATE[seat]["events"])
    return result
main_c68._observe_opponent_market = traced_observe

env = make("kaggriculture", configuration={"episodeSteps": 720, "seed": 0}, debug=False)
env.run([main_c68.agent, opponent])
main_c68._observe_opponent_market = orig_observe  # restore

print("total inference-worthy events C68 saw in a full 720-turn game:", event_log[-1])


"""C69: SmartMarketController wrapping the C68 chassis.

Reuses c68's field tape, weed repair and terminal liquidation untouched.
Replaces the opponent-inference / preemption / sell-ordering trio with:
  1. an EWMA-smoothed opponent quantity estimate (decoupled from "assume
     they sell exactly what my own tape sells at the matched horizon"),
  2. a bounded, Dirichlet-style horizon confidence score -- calibrated
     against how sparse real premium-sale events turn out to be, not
     against the round "80%" number a naive gate would use (see Part 2
     of the tutorial for why a literal 80% threshold never fires),
  3. a value-gap check that only front-runs when doing so actually beats
     waiting for the price to recover, and allows pulling an extra turn
     earlier when both confidence and the value gap are large, and
  4. sell-slot ordering that prices in the *same-turn* opponent quantity
     estimate, not just our own order size.
"""
import main_c68 as base

_PREMIUM = base._PREMIUM
_MARKET_PARAMS = base._MARKET_PARAMS
_ADAPT_MAX_OPP_HORIZON = base._ADAPT_MAX_OPP_HORIZON
_PREEMPT_MAX_CLONE_DISTANCE = base._PREEMPT_MAX_CLONE_DISTANCE
_PREEMPT_MIN_FUTURE_QUANTITY = base._PREEMPT_MIN_FUTURE_QUANTITY
_PREEMPT_START = base._PREEMPT_START
_PREEMPT_STOP = base._PREEMPT_STOP
_PREEMPT_MAX_BATCH = base._PREEMPT_MAX_BATCH

# --- tunables introduced by C69 -------------------------------------------------
# Premium sale events are lumpy -- a whole game typically yields only a
# handful of them -- so the horizon posterior below is a small-prior
# Dirichlet-style accumulator (evidence adds up across events; it does not
# reset to a fresh EWMA that a single quiet stretch would erase) rather than
# a fast-decaying moving average. A gentle per-event decay still lets it
# adapt if the opponent genuinely changes their clock mid-game.
_ALPHA_PRIOR = 0.3         # weak uniform prior mass per horizon
_ALPHA_EVENT_WEIGHT = 2.0  # evidence weight contributed by a single event
_ALPHA_DECAY = 0.97        # gentle forgetting so old evidence isn't permanent
_QTY_BETA = 0.30           # weight on each new opponent-quantity observation
_CONFIDENCE_GATE = 0.55    # see the "does 80% ever fire?" note in the tutorial
_MIN_EVENTS_FOR_GATE = 2   # need at least a couple of events before acting
_EXTRA_PULL_CONFIDENCE = 0.92   # confidence needed to reach one turn earlier
_EXTRA_PULL_VALUE_RATIO = 1.15  # value(h+1) must beat value(h) by this ratio
_MAX_EXTRA_PULL = 1             # cap: at most one extra turn earlier than c68's horizon

_STATE = {0: {}, 1: {}}


def _new_state():
    return {
        "last_step": -1,
        "inventory": {},
        "own_sells": {},
        "shops": (),
        # Dirichlet-style pseudo-counts over "true horizon offset == h".
        # horizon_prob() below normalizes these into a genuine, calibrated
        # confidence instead of the unbounded score c68 uses internally.
        "horizon_alpha": {h: _ALPHA_PRIOR for h in range(1, _ADAPT_MAX_OPP_HORIZON + 1)},
        "events": 0,
        "opp_qty_ewma": {item: None for item in _PREMIUM},
        "opp_qty_events": {item: 0 for item in _PREMIUM},
        "debts": {},
    }


def _state(obs, step):
    seat = base._seat(obs)
    state = _STATE[seat]
    if step == 0 or step < int(state.get("last_step", -1)):
        state = _new_state()
        _STATE[seat] = state
    return state


def _best_horizon_and_confidence(state):
    alpha = state["horizon_alpha"]
    total = sum(alpha.values()) or 1.0
    probs = {h: v / total for h, v in alpha.items()}
    best_h = max(probs, key=lambda h: (probs[h], -h))
    return best_h, probs[best_h]


def _update_market_estimates(obs, step):
    """Refresh the EWMA horizon-fit scores and per-item quantity estimate.

    Mirrors c68's own delta-inference (own sale + town drain removed from the
    raw market-inventory delta) but feeds the result into bounded EWMAs
    instead of an unbounded cumulative score, so (a) the signal can be turned
    into a genuine probability via softmax and (b) stale evidence decays
    instead of permanently anchoring the estimate.
    """
    state = _state(obs, step)
    current = dict(base._get(base._get(obs, "market", {}) or {}, "inventory", {}) or {})
    previous = dict(state.get("inventory", {}) or {})
    prev_step = int(state.get("last_step", -1))

    if previous and prev_step == step - 1 and base._clone_distance(obs) <= _PREEMPT_MAX_CLONE_DISTANCE:
        own = dict(state.get("own_sells", {}) or {})
        shops = tuple(state.get("shops", ()) or ())
        for item in _PREMIUM:
            delta = int(current.get(item, 0) or 0) - int(previous.get(item, 0) or 0)
            inferred = delta + base._town_drain(prev_step, shops, item) - int(own.get(item, 0) or 0)
            inferred -= base._planned_premium(prev_step, item)
            if inferred < _PREEMPT_MIN_FUTURE_QUANTITY:
                continue

            state["events"] += 1

            # (1) EWMA the observed magnitude directly -- this is the estimate
            # we will actually sell against, instead of blindly trusting that
            # the opponent's batch equals whatever our own tape does later.
            prior = state["opp_qty_ewma"][item]
            state["opp_qty_ewma"][item] = inferred if prior is None else (
                (1 - _QTY_BETA) * prior + _QTY_BETA * inferred
            )
            state["opp_qty_events"][item] += 1

            # (2) Turn this single event into a *soft vote* over candidate
            # horizons (similarity in [0, 1], zero where the tape has no
            # planned sale to compare against), then EWMA that vote into a
            # genuine, bounded, sums-to-1 confidence distribution -- so the
            # 80% gate means what it says instead of depending on how long
            # the game has run.
            similarity = {}
            for horizon in range(1, _ADAPT_MAX_OPP_HORIZON + 1):
                expected = base._planned_premium(prev_step + horizon, item)
                similarity[horizon] = (
                    min(inferred, expected) / float(max(inferred, expected)) if expected > 0 else 0.0
                )
            total_similarity = sum(similarity.values())
            if total_similarity > 0:
                vote = {h: s / total_similarity for h, s in similarity.items()}
                alpha = state["horizon_alpha"]
                state["horizon_alpha"] = {
                    h: alpha[h] * _ALPHA_DECAY + _ALPHA_EVENT_WEIGHT * vote[h]
                    for h in alpha
                }

    state["last_step"] = step
    state["inventory"] = current
    state["shops"] = tuple(base._get(base._get(obs, "town", {}) or {}, "unlocked_shops", []) or [])
    return state


def _record_own_sells(obs, action, step):
    state = _state(obs, step)
    sold = {}
    for order in action.get("market", []) or []:
        if len(order) >= 3 and order[0] == "SELL" and order[1] in _PREMIUM:
            sold[order[1]] = sold.get(order[1], 0) + max(0, int(order[2]))
    state["own_sells"] = sold


def _opponent_qty_estimate(state, item, step, horizon):
    """Blend the EWMA-observed magnitude with c68's tape-mirroring prior.

    Small-sample shrinkage: with few observed events we lean on the tape
    (c68's original assumption); as evidence accumulates we trust the
    directly observed EWMA more.
    """
    tape_guess = base._planned_premium(step + horizon, item)
    ewma = state["opp_qty_ewma"].get(item)
    events = state["opp_qty_events"].get(item, 0)
    if ewma is None:
        return tape_guess
    weight = min(1.0, events / 4.0)
    return weight * ewma + (1 - weight) * tape_guess


def _value_gap(obs, item, qty, opp_qty_at_target):
    """Value of selling `qty` now vs. leaving it to be sold alongside the
    opponent's estimated same-turn batch `opp_qty_at_target` turns later.
    """
    if qty <= 0:
        return 0.0
    market = base._get(obs, "market", {}) or {}
    inventory = base._get(market, "inventory", {}) or {}
    prices = base._get(market, "prices", {}) or {}
    current_inventory = int(base._get(inventory, item, 10000) or 0)
    price_now = float(base._get(prices, item, base._market_price(item, current_inventory)) or 0)
    price_if_wait = float(base._market_price(item, current_inventory + qty + max(0, opp_qty_at_target)))
    return qty * (price_now - price_if_wait)


def _predict_and_frontrun(obs, action, step):
    if not (_PREEMPT_START <= step < _PREEMPT_STOP):
        return action
    state = _state(obs, step)
    if base._clone_distance(obs) > _PREEMPT_MAX_CLONE_DISTANCE:
        return action

    best_h, confidence = _best_horizon_and_confidence(state)
    if state["events"] < _MIN_EVENTS_FOR_GATE or confidence < _CONFIDENCE_GATE:
        return action

    horizon = best_h
    # Optionally reach one extra turn earlier when both the horizon call and
    # the extra pull's value gap are strongly favourable ("front-run by two
    # turns if prices are optimal").
    if (
        _MAX_EXTRA_PULL > 0
        and horizon + 1 <= _ADAPT_MAX_OPP_HORIZON
        and confidence >= _EXTRA_PULL_CONFIDENCE
    ):
        base_value = sum(
            _value_gap(
                obs, item,
                min(_PREEMPT_MAX_BATCH, max(0, int(_opponent_qty_estimate(state, item, step, horizon)))),
                _opponent_qty_estimate(state, item, step, horizon),
            )
            for item in _PREMIUM
        )
        extra_value = sum(
            _value_gap(
                obs, item,
                min(_PREEMPT_MAX_BATCH, max(0, int(_opponent_qty_estimate(state, item, step, horizon + 1)))),
                _opponent_qty_estimate(state, item, step, horizon + 1),
            )
            for item in _PREMIUM
        )
        if base_value > 0 and extra_value >= base_value * _EXTRA_PULL_VALUE_RATIO:
            horizon = horizon + 1

    market = list(action.get("market") or [])
    if len(market) >= 10:
        return action
    remaining = base._projected_shed(obs, action)
    for raw in market:
        if len(raw) >= 3 and raw[0] == "SELL":
            item = raw[1]
            remaining[item] = max(0, int(remaining.get(item, 0) or 0) - max(0, int(raw[2])))

    shifted = {}
    shift_state = state.setdefault("debts", {})
    for item in _PREMIUM:
        opp_qty = _opponent_qty_estimate(state, item, step, horizon)
        if opp_qty < _PREEMPT_MIN_FUTURE_QUANTITY:
            continue
        target = min(
            max(0, int(remaining.get(item, 0) or 0)),
            _PREEMPT_MAX_BATCH,
            max(1, int(round(opp_qty))),
        )
        if target <= 0 or len(market) >= 10:
            continue
        gap = _value_gap(obs, item, target, opp_qty)
        if gap <= 0:
            continue  # selling now would not beat waiting -- skip
        market.append(["SELL", item, target])
        remaining[item] = max(0, int(remaining.get(item, 0) or 0) - target)
        shifted[item] = target

    if shifted:
        action["market"] = market[:10]
        due_step = step + horizon
        due = shift_state.setdefault(due_step, {})
        for item, quantity in shifted.items():
            due[item] = due.get(item, 0) + quantity
    return action


def _repay_shift(obs, action, step):
    state = _state(obs, step)
    debts = state.setdefault("debts", {})
    due = {item: max(0, int(q)) for item, q in dict(debts.pop(step, {}) or {}).items()}
    if not due:
        return action
    market = []
    for raw in action.get("market", []) or []:
        order = list(raw)
        if len(order) >= 3 and order[0] == "SELL" and due.get(order[1], 0) > 0:
            item = order[1]
            requested = max(0, int(order[2]))
            reduction = min(requested, due[item])
            requested -= reduction
            due[item] -= reduction
            if requested <= 0:
                continue
            order[2] = requested
        market.append(order)
    action["market"] = market
    return action


def _joint_order_score(obs, state, order):
    score = base._impact_score(obs, order)
    if score <= 0 or not base._is_sell(order):
        return score
    item = str(order[1])
    quantity = max(0, int(order[2]))
    if item in _PREMIUM:
        opp_qty = state["opp_qty_ewma"].get(item)
        if opp_qty is not None and opp_qty > 0:
            # Re-price the "later" side of the impact score assuming the
            # opponent's estimated same-turn batch lands alongside ours,
            # instead of pretending we are the only seller this turn.
            market = base._get(obs, "market", {}) or {}
            inventory = base._get(market, "inventory", {}) or {}
            prices = base._get(market, "prices", {}) or {}
            current_inventory = int(base._get(inventory, item, 10000) or 0)
            current_quote = float(base._get(prices, item, base._market_price(item, current_inventory)) or 0)
            later_quote = float(base._market_price(item, current_inventory + quantity + int(round(opp_qty))))
            score = float(quantity) * max(0.0, current_quote - later_quote)
    market = base._get(obs, "market", {}) or {}
    inventory = base._get(market, "inventory", {}) or {}
    current_inventory = int(base._get(inventory, item, 10000) or 0)
    demand = max(0.25, base._demand_per_day(obs, None, item))
    excess = max(0.0, current_inventory + quantity - 10000)
    urgency = min(1.0, (excess / demand) / 10.0)
    return score * (1.0 + base._DEMAND_ALPHA * urgency)


def _rank_sell_slots(obs, action, state):
    action = base._copy_action(action)
    market = list(action.get("market") or [])
    rows = [
        (_joint_order_score(obs, state, order), -index, list(order))
        for index, order in enumerate(market)
        if base._is_sell(order)
    ]
    if len(rows) < 2:
        return action
    rows.sort(reverse=True)
    ranked = iter(row[2] for row in rows)
    action["market"] = [next(ranked) if base._is_sell(order) else order for order in market]
    return action


def agent(obs):
    try:
        step = min(max(0, int(base._get(obs, "step", 0) or 0)), len(base._ACTIONS) - 1)
        state = _update_market_estimates(obs, step)
        action = base._weed_repair_action(obs, base._copy_action(base._ACTIONS[step]), step)
        action = _repay_shift(obs, action, step)
        action = _rank_sell_slots(obs, action, state)
        action = _predict_and_frontrun(obs, action, step)
        action = base._terminal_liquidation(obs, action, step)
        action = base._align_hands(action, obs)
        _record_own_sells(obs, action, step)
        return action
    except Exception:
        farm = base._farm(obs, base._seat(obs))
        return {
            "farmer": ["PASS"],
            "hands": [["PASS"] for _ in (base._get(farm, "hands", []) or [])],
            "market": [],
        }


env = make("kaggriculture", configuration={"episodeSteps": 720, "seed": 0}, debug=False)
env.run([agent, "starter"])
final = env.steps[-1]
print("status:", [row["status"] for row in final])
print("reward:", [row["reward"] for row in final])
# Expect this to match C68's own smoke-test reward exactly: against an
# opponent this different, C69's extra machinery has no clone to react to,
# so it should degrade gracefully to C68's behaviour.


def run_game(agent_a, agent_b, seed, steps=720):
    env = make("kaggriculture", configuration={"episodeSteps": steps, "seed": seed}, debug=False)
    env.run([agent_a, agent_b])
    final = env.steps[-1]
    return [row["status"] for row in final], [row["reward"] for row in final]

wins_c69 = wins_c68 = ties = errors = 0
for seed in range(5):
    for c69_seat in (0, 1):
        agents = [agent, main_c68.agent] if c69_seat == 0 else [main_c68.agent, agent]
        status, reward = run_game(*agents, seed)
        if any(s != "DONE" for s in status):
            errors += 1
            continue
        r69, r68 = (reward[0], reward[1]) if c69_seat == 0 else (reward[1], reward[0])
        if r69 > r68:
            wins_c69 += 1
        elif r68 > r69:
            wins_c68 += 1
        else:
            ties += 1

print(f"C69 better: {wins_c69}  C68 better: {wins_c68}  ties: {ties}  errors: {errors}")
print("Expectation: near-total ties, since an exact clone gives C69's opponent-quantity")
print("estimator nothing to disagree with C68's tape-mirroring assumption about.")


def evaluate_against(opponent_factory_agent, label, seeds=range(3)):
    wins_c69 = wins_c68 = ties = errors = 0
    for seed in seeds:
        for order in ("c_first", "opp_first"):
            if order == "c_first":
                s69, r69_pair = run_game(agent, opponent_factory_agent, seed)
                s68, r68_pair = run_game(main_c68.agent, opponent_factory_agent, seed)
                r69, r68 = r69_pair[0], r68_pair[0]
            else:
                s69, r69_pair = run_game(opponent_factory_agent, agent, seed)
                s68, r68_pair = run_game(opponent_factory_agent, main_c68.agent, seed)
                r69, r68 = r69_pair[1], r68_pair[1]
            if any(x != "DONE" for x in s69 + s68):
                errors += 1
                continue
            if r69 > r68:
                wins_c69 += 1
            elif r68 > r69:
                wins_c68 += 1
            else:
                ties += 1
    n = len(seeds) * 2
    print(f"{label}: C69 better {wins_c69}/{n}, C68 better {wins_c68}/{n}, tie {ties}/{n}, errors {errors}")

evaluate_against(make_shifted_opponent(shift=3), "timing-shifted clone (shift=+3 turns)")


def h2h(agent_a, agent_b, seeds=range(10), both_seats=True):
    """Same shape as the source notebook's own h2h helper (section 8).
    Run this with many more seeds, and against real downloaded replay tapes
    (not just the synthetic shifted-clone above) before trusting a result."""
    seats = (0, 1) if both_seats else (0,)
    rows = []
    for seed in seeds:
        for seat in seats:
            pair = (agent_a, agent_b) if seat == 0 else (agent_b, agent_a)
            status, reward = run_game(*pair, seed)
            a_reward, b_reward = (reward[0], reward[1]) if seat == 0 else (reward[1], reward[0])
            rows.append({"seed": seed, "seat": seat, "a": a_reward, "b": b_reward,
                         "a_win": a_reward > b_reward, "errors": any(s != "DONE" for s in status)})
    return pd.DataFrame(rows)

# Example: h2h(agent, main_c68.agent, seeds=range(20))
print("Harness ready -- see the docstring for what a real promotion gate needs.")


# Assemble a self-contained main.py: c68's decoded source, followed by the
# SmartMarketController cell's own source with `base.` attribute access
# rewritten to plain names, since both pieces will share one module
# namespace once concatenated (the notebook cell above keeps them as two
# modules -- `import main_c68 as base` -- purely so Part 3 can be read and
# tested against the untouched c68 module side by side).
import inspect

# The wrapper functions were all defined in this notebook's global namespace
# (the Part 3 cell ran at top level), so main.py is rebuilt straight from the
# live function objects -- equivalent to the cell's own source, without
# depending on notebook-internal cell text.
def _source_of(names):
    return "\n\n\n".join(inspect.getsource(globals()[n]) for n in names)

_SMART_WRAPPER_FUNCS = [
    "_new_state", "_state", "_best_horizon_and_confidence", "_update_market_estimates",
    "_record_own_sells", "_opponent_qty_estimate", "_value_gap", "_predict_and_frontrun",
    "_repay_shift", "_joint_order_score", "_rank_sell_slots", "agent",
]
_SMART_WRAPPER_CONSTANTS = r"""
_PREMIUM = base._PREMIUM
_MARKET_PARAMS = base._MARKET_PARAMS
_ADAPT_MAX_OPP_HORIZON = base._ADAPT_MAX_OPP_HORIZON
_PREEMPT_MAX_CLONE_DISTANCE = base._PREEMPT_MAX_CLONE_DISTANCE
_PREEMPT_MIN_FUTURE_QUANTITY = base._PREEMPT_MIN_FUTURE_QUANTITY
_PREEMPT_START = base._PREEMPT_START
_PREEMPT_STOP = base._PREEMPT_STOP
_PREEMPT_MAX_BATCH = base._PREEMPT_MAX_BATCH
_ALPHA_PRIOR = 0.3
_ALPHA_EVENT_WEIGHT = 2.0
_ALPHA_DECAY = 0.97
_QTY_BETA = 0.30
_CONFIDENCE_GATE = 0.55
_MIN_EVENTS_FOR_GATE = 2
_EXTRA_PULL_CONFIDENCE = 0.92
_EXTRA_PULL_VALUE_RATIO = 1.15
_MAX_EXTRA_PULL = 1
_STATE = {0: {}, 1: {}}
"""

smart_source = _SMART_WRAPPER_CONSTANTS + "\n\n" + _source_of(_SMART_WRAPPER_FUNCS)
smart_source = smart_source.replace("base.", "")  # both pieces share one namespace once concatenated

c69_source = C68_MAIN_PATH.read_text() + "\n\n# --- SmartMarketController (C69) ---\n" + smart_source

C69_MAIN_PATH = WORK / "main.py"
ARCHIVE_PATH = WORK / "submission.tar.gz"
C69_MAIN_PATH.write_text(c69_source)
compile(c69_source, str(C69_MAIN_PATH), "exec")

with tarfile.open(ARCHIVE_PATH, "w:gz") as archive:
    archive.add(C69_MAIN_PATH, arcname="main.py")
with tarfile.open(ARCHIVE_PATH, "r:gz") as archive:
    members = archive.getnames()

spec2 = importlib.util.spec_from_file_location("c69_standalone", C69_MAIN_PATH)
c69_standalone = importlib.util.module_from_spec(spec2)
spec2.loader.exec_module(c69_standalone)

env = make("kaggriculture", configuration={"episodeSteps": 720, "seed": 0}, debug=False)
env.run([c69_standalone.agent, "starter"])
final = env.steps[-1]
print({
    "main_py": str(C69_MAIN_PATH),
    "main_bytes": C69_MAIN_PATH.stat().st_size,
    "submission": str(ARCHIVE_PATH),
    "archive_members": members,
    "smoke_vs_starter_status": [row["status"] for row in final],
    "smoke_vs_starter_rewards": [row["reward"] for row in final],
    "note": "This cell only builds files. It does not submit them.",
})
