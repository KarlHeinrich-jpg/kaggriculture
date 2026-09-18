"""V705: use only zero-travel idle capacity for harvest-committed care.

V704 showed that sending an otherwise idle worker toward a HARVEST-committed
animal perturbs the next public replan.  Retain the same current-state
certificate, but act only when an empty-tour worker is already standing on the
animal tile.  No selected route, worker position, input allocation, or future
target changes.
"""

from whitebox.versions import v704_public_harvest_committed_care as _v704


_v684 = _v704._v684
_v659 = _v704._v659
_v464 = _v704._v464
_v463 = _v704._v463
_v384 = _v704._v384
_c06 = _v704._c06


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

    targets = set(_v704._selected_harvest_care_targets(
        obs, farm, jobs, tours
    ))
    for index, action in enumerate(actions):
        position = tuple(positions[index])
        if (
            action == ["PASS"]
            and position in targets
            and not list((tours.get(index) or {}).get("tasks", ()) or ())
        ):
            actions[index] = ["CARE"]
            targets.remove(position)

    available = [
        task for task in undone
        if not task.carry and task.ops and float(task.value) > 0.0
    ]
    remaining_turns = max(0, 24 - hour)
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


def whitebox_v705_public_colocated_harvest_care(obs):
    return _v684.whitebox_v684_public_recertified_nonfarmers_light(obs)
