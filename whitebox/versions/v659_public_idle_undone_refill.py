"""V659: refill genuinely idle workers from live undone public tasks.

V649's receding solver may leave positive-value work unassigned while some
units emit PASS.  Reuse only the solver's explicit ``undone`` set: each idle
unit takes the nearest distinct task that needs no carried input and whose
travel plus operations fit the remaining public day budget.  Assigned routes,
capital, market orders, and every input-constrained task remain unchanged.
"""

from whitebox.versions import v649_public_farmers_immediate_sales as _v649


_v464 = _v649._v646._v645._v464
_v463 = _v464._v463
_v384 = _v464._v384
_c06 = _v649._c06


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


def whitebox_v659_public_idle_undone_refill(obs):
    return _v649.whitebox_v649_public_farmers_immediate_sales(obs)
