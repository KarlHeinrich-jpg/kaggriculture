"""V422: admit minimal continuity only after a mature demand signal.

Town shops unlock every three public days.  Before the third unlock, a single
shop is not enough evidence to alter the route path.  From day nine onward the
one-travel-unit continuity credit is enabled only while public milk demand is
strictly above wool demand.  All live tasks are still rebuilt every turn.
"""

from whitebox.versions import v361_public_wheat_rotation22 as _v361


_c06 = _v361._c06
_base_unit_actions = _c06._unit_actions


def _unit_actions(obs, config, farm, private, roles):
    day = int((obs or {}).get("day", 0) or 0)
    enabled = (
        day >= 9
        and _c06._town_demand_per_day(obs, "MILK")
        > _c06._town_demand_per_day(obs, "WOOL")
    )
    previous = _c06.TARGET_STICKINESS_BONUS
    _c06.TARGET_STICKINESS_BONUS = _c06.TRAVEL_COST if enabled else 0.0
    try:
        return _base_unit_actions(obs, config, farm, private, roles)
    finally:
        _c06.TARGET_STICKINESS_BONUS = previous


def _decide(obs, config=None):
    farms = obs.get("farms", []) or []
    player = int(obs.get("player", 0) or 0)
    if not (0 <= player < len(farms)):
        return {"farmer": ["PASS"], "hands": [], "market": []}
    farm = farms[player]
    private = obs.get("private", {}) or {}
    roles = _c06._role_plan(obs, farm)
    field = _unit_actions(obs, config, farm, private, roles)
    return {
        "farmer": field["farmer"],
        "hands": field["hands"],
        "market": _c06._market_actions(
            obs, config, farm, private, roles, field
        ),
    }


def whitebox_v422_public_mature_demand_stickiness(obs):
    try:
        return _decide(obs)
    except Exception:
        farms = obs.get("farms", []) if hasattr(obs, "get") else []
        player = int(obs.get("player", 0)) if hasattr(obs, "get") else 0
        hands = (
            len(farms[player].get("hands", []) or [])
            if 0 <= player < len(farms) else 0
        )
        return {
            "farmer": ["PASS"],
            "hands": [["PASS"] for _ in range(hands)],
            "market": [],
        }
