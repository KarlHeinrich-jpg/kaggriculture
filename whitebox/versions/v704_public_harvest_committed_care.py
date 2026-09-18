"""V704: use idle route capacity for harvest-committed animal care.

The public task generator suppresses CARE while held output is at its capacity
boundary, even when the current route solver has already certified that the
same animal's HARVEST will complete before day end.  Preserve every selected
route and use only workers whose selected tour is empty: they may travel to one
such animal and CARE it.  HARVEST later releases the output capacity, so the
engine-defined care bonus can produce on a later fed tick.

The certificate is rebuilt from the current observation and current solver
output every turn.  It retains no target, action sequence, seed, seat, or
opponent identity.
"""

from whitebox.versions import v684_public_recertified_nonfarmers_light as _v684


_v678 = _v684._v678
_v659 = _v678._v675._v659
_v464 = _v659._v464
_v463 = _v464._v463
_v384 = _v464._v384
_c06 = _v659._c06


def _selected_harvest_care_targets(obs, farm, jobs, tours):
    day = int((obs or {}).get("day", 0) or 0)
    if day > 27:
        return []
    existing_care = {
        tuple(job.get("target", ()))
        for job in jobs
        if (job.get("action") or [""])[0] == "CARE"
    }
    selected_harvest = {
        tuple(task.pos)
        for tour in tours.values()
        for task in ((tour or {}).get("tasks", ()) or ())
        if any(action and action[0] == "HARVEST" for action in task.ops)
    }
    prices = ((obs or {}).get("market", {}) or {}).get("prices", {}) or {}
    tiles = farm.get("tiles", []) or []
    targets = []
    for target in sorted(selected_harvest - existing_care):
        x, y = target
        tile = tiles[y][x]
        if (
            not isinstance(tile, dict)
            or tile.get("animal") not in _c06.ANIMALS
            or tile.get("cared_today", False)
            or int(tile.get("yield_units", 0) or 0) <= 0
        ):
            continue
        rule = _c06.ANIMALS[tile["animal"]]
        price = float(
            prices.get(rule["product"], _c06.MARKET[rule["product"]][0])
            or _c06.MARKET[rule["product"]][0]
        )
        if price >= 20:
            targets.append(target)
    return targets


def _unit_actions(obs, config, farm, private, roles):
    day = int((obs or {}).get("day", 0) or 0)
    hour = int((obs or {}).get("hour", 0) or 0)
    step = int((obs or {}).get("step", day * 24 + hour) or 0)
    final_step = int(_c06._cfg(config, "episodeSteps", 720)) - 2
    actions_left = max(0, final_step - step + 1)
    liquidation = actions_left <= _c06.LIQUIDATION_TURNS
    jobs = _v384._live_jobs(obs, farm, private, roles, liquidation)
    positions = [farm["farmer"], *(farm.get("hands", []) or [])]
    inventories = list(private.get("inventories", []) or [])
    tasks, fixed_owner = _v464._reserve_carried_inputs(
        _v384._task_groups(jobs), positions, inventories
    )
    units = [
        _v464.router.Unit(index, tuple(position), hour)
        for index, position in enumerate(positions)
    ]
    shed_stock = {
        item: max(0, int(quantity or 0))
        for item, quantity in (private.get("shed", {}) or {}).items()
    }
    tours, undone = _v464.router.plan_day(
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

    targets = _selected_harvest_care_targets(obs, farm, jobs, tours)
    remaining_turns = max(0, 24 - hour)
    for index, action in enumerate(actions):
        if action != ["PASS"] or not targets:
            continue
        if list((tours.get(index) or {}).get("tasks", ()) or ()):
            continue
        position = tuple(positions[index])
        feasible = [
            target for target in targets
            if _c06._distance(position, target) + 1 <= remaining_turns
        ]
        if not feasible:
            continue
        target = min(
            feasible,
            key=lambda value: (
                _c06._distance(position, value), value[1], value[0]
            ),
        )
        targets.remove(target)
        actions[index] = (
            ["CARE"]
            if position == target
            else _c06._bfs_first_step(farm["tiles"], position, target)
        )

    available = [
        task for task in undone
        if not task.carry and task.ops and float(task.value) > 0.0
    ]
    for index, action in enumerate(actions):
        if action != ["PASS"] or not available:
            continue
        position = tuple(positions[index])
        feasible = [
            task for task in available
            if _c06._distance(position, task.pos) + task.n_ops
            <= remaining_turns
        ]
        if not feasible:
            continue
        task = min(
            feasible,
            key=lambda candidate: (
                _c06._distance(position, candidate.pos),
                -float(candidate.value),
                tuple(candidate.pos),
                tuple(tuple(op) for op in candidate.ops),
            ),
        )
        available.remove(task)
        actions[index] = (
            list(task.ops[0])
            if position == tuple(task.pos)
            else _c06._bfs_first_step(
                farm["tiles"], position, tuple(task.pos)
            )
        )
    return {
        "farmer": actions[0] if actions else ["PASS"],
        "hands": actions[1:],
        "liquidation": liquidation,
    }


_v464._unit_actions = _unit_actions


def whitebox_v704_public_harvest_committed_care(obs):
    return _v684.whitebox_v684_public_recertified_nonfarmers_light(obs)
