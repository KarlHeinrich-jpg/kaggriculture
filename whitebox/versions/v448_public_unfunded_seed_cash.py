"""V448: release exact sale cash only for an unfunded expansion seed plan.

On day eight, substantial open land certifies that the first expansion still
has crop work available.  The conservative V423 market plan is built first.
Only when that plan cannot fund any already named seed does the policy rebuild
the same public-state market plan with engine-exact same-turn sale cash.
Capital, field routing, and plans that already buy seed remain unchanged.
"""

from whitebox.versions import v423_public_mature_routes_cow_rotation as _v423


_c06 = _v423._c06
_unit_actions = _v423._v422._unit_actions


def _open_land(farm):
    return sum(
        tile is None or (
            isinstance(tile, dict) and tile.get("kind") == "WEED"
        )
        for row in farm.get("tiles", []) or []
        for tile in row or ()
    )


def _buys_seed(orders):
    return any(
        isinstance(order, list)
        and len(order) >= 2
        and order[0] == "BUY_SEED"
        and int(order[2] if len(order) >= 3 else 1) > 0
        for order in orders or ()
    )


def _decide(obs, config=None):
    farms = obs.get("farms", []) or []
    player = int(obs.get("player", 0) or 0)
    if not (0 <= player < len(farms)):
        return {"farmer": ["PASS"], "hands": [], "market": []}
    farm = farms[player]
    private = obs.get("private", {}) or {}
    roles = _c06._role_plan(obs, farm)
    field = _unit_actions(obs, config, farm, private, roles)
    market = _c06._market_actions(obs, config, farm, private, roles, field)
    certified = (
        int(obs.get("day", 0) or 0) == 8
        and len(farm.get("unlocked_quadrants", []) or []) == 2
        and _open_land(farm) >= 16
        and not _buys_seed(market)
    )
    if certified:
        previous = _c06.COMMITTED_WORK_SALE_CASH_FACTOR
        _c06.COMMITTED_WORK_SALE_CASH_FACTOR = 1.0
        try:
            market = _c06._market_actions(
                obs, config, farm, private, roles, field
            )
        finally:
            _c06.COMMITTED_WORK_SALE_CASH_FACTOR = previous
    return {
        "farmer": field["farmer"],
        "hands": field["hands"],
        "market": market,
    }


def whitebox_v448_public_unfunded_seed_cash(obs):
    try:
        return _decide(obs)
    except Exception:
        farms = obs.get("farms", []) if hasattr(obs, "get") else []
        player = int(obs.get("player", 0)) if hasattr(obs, "get") else 0
        hand_count = (
            len(farms[player].get("hands", []) or [])
            if 0 <= player < len(farms) else 0
        )
        return {
            "farmer": ["PASS"],
            "hands": [["PASS"] for _ in range(hand_count)],
            "market": [],
        }
