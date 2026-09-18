"""V463: re-solve current public work as receding day routes every turn.

Each observation exposes the complete currently live task set, current worker
positions and carried inputs.  This layer groups same-tile operations, solves
an open multi-worker route over the remaining hours of the current day, and
emits only the first action of each route.  The solve is repeated from the next
live observation, so newly appearing feed, harvest, weed, and capital tasks
enter immediately and stale work disappears without a retained action tape.
"""

from route import router
from whitebox.versions import v384_public_daily_route_certificate as _v384
from whitebox.versions import v454_public_weed_window_sale_cash as _v454


_c06 = _v454._c06


def _route_action(farm, private, tour, index):
    positions = [farm["farmer"], *(farm.get("hands", []) or [])]
    if index >= len(positions):
        return ["PASS"]
    position = tuple(positions[index])
    inventories = list(private.get("inventories", []) or [])
    inventory = (
        dict(inventories[index] or {})
        if index < len(inventories)
        else {}
    )
    carry = dict((tour or {}).get("carry", {}) or {})
    missing = {
        item: max(0, int(quantity) - int(inventory.get(item, 0) or 0))
        for item, quantity in carry.items()
        if int(quantity) > int(inventory.get(item, 0) or 0)
    }
    shed = private.get("shed", {}) or {}
    available = [
        item
        for item in sorted(missing, key=lambda name: (name != "WHEAT", name))
        if int(shed.get(item, 0) or 0) > 0
    ]
    if available:
        target = _c06._nearest_shed(
            position, len(farm["tiles"]), farm["tiles"]
        )
        if position in _c06._shed_tiles(len(farm["tiles"]), farm["tiles"]):
            item = available[0]
            return [
                "PICKUP",
                item,
                min(missing[item], int(shed.get(item, 0) or 0)),
            ]
        return _c06._bfs_first_step(farm["tiles"], position, target)

    for target, operations in (tour or {}).get("stops", ()) or ():
        if not operations:
            continue
        action = list(operations[0])
        need = _v384._need_for(action)
        if need is not None and int(inventory.get(need, 0) or 0) <= 0:
            continue
        target = tuple(target)
        return (
            action
            if position == target
            else _c06._bfs_first_step(farm["tiles"], position, target)
        )
    return ["PASS"]


def _unit_actions(obs, config, farm, private, roles):
    day = int(obs.get("day", 0) or 0)
    hour = int(obs.get("hour", 0) or 0)
    step = int(obs.get("step", day * 24 + hour) or 0)
    final_step = int(_c06._cfg(config, "episodeSteps", 720)) - 2
    actions_left = max(0, final_step - step + 1)
    liquidation = actions_left <= _c06.LIQUIDATION_TURNS
    jobs = _v384._live_jobs(obs, farm, private, roles, liquidation)
    positions = [farm["farmer"], *(farm.get("hands", []) or [])]
    units = [
        router.Unit(index, tuple(position), hour)
        for index, position in enumerate(positions)
    ]
    shed_stock = {
        item: max(0, int(quantity or 0))
        for item, quantity in (private.get("shed", {}) or {}).items()
    }
    tours, _undone = router.plan_day(
        units,
        _v384._task_groups(jobs),
        shed_stock=shed_stock,
        bank_outputs=liquidation,
        deterministic_primal=True,
    )
    actions = [
        _route_action(farm, private, tours.get(index), index)
        for index in range(len(positions))
    ]
    return {
        "farmer": actions[0] if actions else ["PASS"],
        "hands": actions[1:],
        "liquidation": liquidation,
    }


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


def whitebox_v463_public_receding_routes(obs, config=None):
    try:
        return _decide(obs, config)
    except Exception:
        farms = obs.get("farms", []) if hasattr(obs, "get") else []
        player = int(obs.get("player", 0)) if hasattr(obs, "get") else 0
        hands = (
            len(farms[player].get("hands", []) or [])
            if 0 <= player < len(farms)
            else 0
        )
        return {
            "farmer": ["PASS"],
            "hands": [["PASS"] for _ in range(hands)],
            "market": [],
        }
