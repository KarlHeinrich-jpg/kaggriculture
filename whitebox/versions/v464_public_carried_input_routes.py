"""V464: receding public routes with exact carried-input ownership.

The public route solver prices shared shed stock, while live workers may
already carry feed, fertilizer, or an animal.  Treating that carried input as
unowned made the selected task migrate to another worker every turn and forced
repeated pickups.  This layer assigns each worker with a relevant carried item
to its nearest matching live task, removes exactly one unit of that task's
shed requirement, and jointly routes the remaining work.  The reservation is
rebuilt from the current private inventory and live tasks every observation.
"""

from route import router
from whitebox.versions import v463_public_receding_routes as _v463


_v384 = _v463._v384
_c06 = _v463._c06


def _copy_task(task, carry):
    return router.Task(
        task.pos,
        [list(action) for action in task.ops],
        carry=carry,
        value=task.value,
        mandatory=task.mandatory,
        kind=task.kind,
        cash_cost=task.cash_cost,
        order_key=task.order_key,
        activations=task.activations,
        exclusive_key=task.exclusive_key,
    )


def _reserve_carried_inputs(tasks, positions, inventories):
    tasks = list(tasks)
    fixed_owner = {}
    reserved = set()
    for worker, raw_position in enumerate(positions):
        inventory = (
            dict(inventories[worker] or {})
            if worker < len(inventories)
            else {}
        )
        candidates = []
        for index, task in enumerate(tasks):
            if index in reserved:
                continue
            usable = [
                item
                for item, quantity in task.carry.items()
                if int(quantity) > 0
                and int(inventory.get(item, 0) or 0) > 0
            ]
            if not usable:
                continue
            candidates.append((
                _c06._distance(raw_position, task.pos),
                0 if task.mandatory else 1,
                tuple(task.pos),
                index,
                sorted(usable, key=lambda item: (item != "WHEAT", item))[0],
            ))
        if not candidates:
            continue
        _distance, _optional, target, index, item = min(candidates)
        carry = dict(tasks[index].carry)
        carry[item] = max(0, int(carry.get(item, 0) or 0) - 1)
        if carry[item] == 0:
            del carry[item]
        tasks[index] = _copy_task(tasks[index], carry)
        fixed_owner[target] = worker
        reserved.add(index)
    return tasks, fixed_owner


def _unit_actions(obs, config, farm, private, roles):
    day = int(obs.get("day", 0) or 0)
    hour = int(obs.get("hour", 0) or 0)
    step = int(obs.get("step", day * 24 + hour) or 0)
    final_step = int(_c06._cfg(config, "episodeSteps", 720)) - 2
    actions_left = max(0, final_step - step + 1)
    liquidation = actions_left <= _c06.LIQUIDATION_TURNS
    jobs = _v384._live_jobs(obs, farm, private, roles, liquidation)
    positions = [farm["farmer"], *(farm.get("hands", []) or [])]
    inventories = list(private.get("inventories", []) or [])
    tasks, fixed_owner = _reserve_carried_inputs(
        _v384._task_groups(jobs), positions, inventories
    )
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
        tasks,
        shed_stock=shed_stock,
        fixed_owner=fixed_owner,
        bank_outputs=liquidation,
        deterministic_primal=True,
    )
    actions = [
        _v463._route_action(farm, private, tours.get(index), index)
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


def whitebox_v464_public_carried_input_routes(obs, config=None):
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
