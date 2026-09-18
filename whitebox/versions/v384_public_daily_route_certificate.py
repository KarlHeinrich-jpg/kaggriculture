"""V384: retain a live, public-state route certificate for each farm day.

The C06 policy already chooses useful field jobs, but historically rematched
every worker to every job after every observation.  This version changes only
execution: public jobs are packed into multi-stop day routes, retained across
turns, and revalidated against the live tile state before every emitted action.
No opponent identity, replay, fitted schedule, or hidden state is retained.
"""

from route import router
from whitebox.versions import v361_public_wheat_rotation22 as _v361


_c06 = _v361._c06
_ROUTE_CERTIFICATES = {}

_OP_ORDER = {
    "FEED": 0,
    "FERTILIZE": 1,
    "WATER": 2,
    "CARE": 3,
    "HARVEST": 4,
    "COLLECT_FERTILIZER": 5,
    "DIG": 6,
    "BUILD_COOP": 7,
    "BUILD_PASTURE": 7,
    "PLACE": 8,
    "PLANT": 9,
}


def reset(seat=None):
    if seat is None:
        _ROUTE_CERTIFICATES.clear()
    else:
        _ROUTE_CERTIFICATES.pop(int(seat), None)


def _action_key(action):
    return tuple(action or ("PASS",))


def _job_key(job):
    return tuple(job["target"]), _action_key(job["action"])


def _need_for(action):
    operation = action[0] if action else "PASS"
    if operation == "FEED":
        return "WHEAT"
    if operation == "FERTILIZE":
        return "FERTILIZER"
    if operation == "PLACE" and len(action) >= 2 and action[1] in _c06.ANIMALS:
        return action[1]
    return None


def _all_shed_tiles(board_size):
    half = int(board_size) // 2
    return (
        (half - 1, half - 1),
        (half, half - 1),
        (half - 1, half),
        (half, half),
    )


def _nearest_shed(position, board_size):
    return min(
        _all_shed_tiles(board_size),
        key=lambda target: (_c06._distance(position, target), target[1], target[0]),
    )


def _step_toward(position, target):
    """One legal Manhattan step; locked tiles are publicly known passable."""
    x, y = int(position[0]), int(position[1])
    tx, ty = int(target[0]), int(target[1])
    if y < ty:
        return ["SOUTH"]
    if y > ty:
        return ["NORTH"]
    if x < tx:
        return ["EAST"]
    if x > tx:
        return ["WEST"]
    return ["PASS"]


def _live_jobs(obs, farm, private, roles, liquidation):
    hour = int(obs.get("hour", 0) or 0)
    return [
        job for job in _c06._field_jobs(obs, farm, private, roles, liquidation)
        if hour <= int(job.get("latest_hour", 23) or 23)
    ]


def _task_groups(jobs):
    grouped = {}
    for job in jobs:
        grouped.setdefault(tuple(job["target"]), []).append(job)

    tasks = []
    for target, target_jobs in sorted(grouped.items()):
        unique = {}
        for job in target_jobs:
            key = _action_key(job["action"])
            incumbent = unique.get(key)
            if incumbent is None or (
                int(job["priority"]), -float(job["value"])
            ) < (
                int(incumbent["priority"]), -float(incumbent["value"])
            ):
                unique[key] = job
        ordered = sorted(
            unique.values(),
            key=lambda job: (
                _OP_ORDER.get(job["action"][0], 50),
                int(job["priority"]),
                _action_key(job["action"]),
            ),
        )
        carry = {}
        for job in ordered:
            need = job.get("need") or _need_for(job["action"])
            if need is not None:
                carry[need] = carry.get(need, 0) + 1
        priority = min(int(job["priority"]) for job in ordered)
        value = sum(
            max(1.0, float(job["value"]))
            + float(_c06.PRIORITY_BONUS.get(int(job["priority"]), 0.0))
            for job in ordered
        )
        tasks.append(
            router.Task(
                target,
                [list(job["action"]) for job in ordered],
                carry=carry,
                value=value,
                mandatory=priority <= 0,
                kind="PUBLIC_ROUTE_" + "+".join(
                    str(job.get("reason") or job["action"][0])
                    for job in ordered
                ),
            )
        )
    return tasks


def _service_job(job):
    reason = str(job.get("reason", ""))
    operation = str((job.get("action") or ["PASS"])[0])
    return (
        reason.startswith(("build_", "place_"))
        or reason in {
            "critical_feed", "feed", "care", "animal_harvest",
            "fertilizer", "terminal_animal", "terminal_fertilizer",
            "clear_animal_slot", "replace_incompatible_structure",
        }
        or operation in {"BUILD_COOP", "BUILD_PASTURE"}
        or (operation == "PLACE" and len(job.get("action") or ()) >= 2
            and job["action"][1] in _c06.ANIMALS)
    )


def _certificate_from_tour(tour):
    return {
        "carry": dict((tour or {}).get("carry", {}) or {}),
        "stops": [
            {
                "target": tuple(target),
                "ops": [list(action) for action in (actions or ())],
            }
            for target, actions in ((tour or {}).get("stops", ()) or ())
        ],
        "turn_cost": int((tour or {}).get("turn_cost", 0) or 0),
    }


def _next_target(certificate):
    for stop in (certificate or {}).get("stops", ()):
        if stop.get("ops"):
            return tuple(stop["target"])
    return None


def _plan_routes(
    obs, farm, private, jobs, previous=None, unit_indexes=None,
    liquidation=False,
):
    hour = int(obs.get("hour", 0) or 0)
    positions = [farm["farmer"], *(farm.get("hands", []) or [])]
    if unit_indexes is None:
        unit_indexes = list(range(len(positions)))
    units = [
        router.Unit(index, tuple(positions[index]), hour)
        for index in unit_indexes
        if index < len(positions)
    ]
    shed_stock = {
        item: max(0, int(quantity or 0))
        for item, quantity in (private.get("shed", {}) or {}).items()
    }
    service_jobs = [job for job in jobs if _service_job(job)]
    field_jobs = [job for job in jobs if not _service_job(job)]
    service_targets = len({tuple(job["target"]) for job in service_jobs})
    service_count = min(
        len(units),
        max(1, int((service_targets + 3) // 4)) if service_jobs else 0,
    )
    if field_jobs and service_count >= len(units) and len(units) > 1:
        service_count = len(units) - 1
    service_units = units[:service_count]
    field_units = units[service_count:]
    if not service_jobs:
        field_units = units
    if not field_jobs:
        service_units = units

    def solve(selected_units, selected_jobs):
        if not selected_units or not selected_jobs:
            return {}, _task_groups(selected_jobs)
        fixed_owner = {}
        if previous is not None:
            selected_indexes = {unit.idx for unit in selected_units}
            for index in selected_indexes:
                target = _next_target(
                    (previous.get("routes", {}) or {}).get(index)
                )
                if target is not None:
                    fixed_owner[target] = index
        return router.plan_day(
            selected_units,
            _task_groups(selected_jobs),
            shed_stock=shed_stock,
            fixed_owner=fixed_owner,
            bank_outputs=liquidation,
            deterministic_primal=True,
        )

    service_tours, service_undone = solve(service_units, service_jobs)
    field_tours, field_undone = solve(field_units, field_jobs)
    tours = dict(service_tours)
    tours.update(field_tours)
    undone = list(service_undone) + list(field_undone)
    return {
        unit.idx: _certificate_from_tour(tours.get(unit.idx))
        for unit in units
    }, undone


def _prune_routes(cache, live_keys):
    for certificate in (cache.get("routes", {}) or {}).values():
        retained = []
        for stop in certificate.get("stops", ()):
            target = tuple(stop["target"])
            operations = [
                list(action) for action in stop.get("ops", ())
                if (target, _action_key(action)) in live_keys
            ]
            if operations:
                retained.append({"target": target, "ops": operations})
        certificate["stops"] = retained


def _covered_keys(cache):
    return {
        (tuple(stop["target"]), _action_key(action))
        for certificate in (cache.get("routes", {}) or {}).values()
        for stop in certificate.get("stops", ())
        for action in stop.get("ops", ())
    }


def _empty_units(cache, unit_count):
    routes = cache.get("routes", {}) or {}
    return [
        index for index in range(unit_count)
        if _next_target(routes.get(index)) is None
    ]


def _live_signature(jobs):
    return tuple(sorted(_job_key(job) for job in jobs))


def _ensure_routes(obs, farm, private, jobs, liquidation):
    seat = int(obs.get("player", 0) or 0)
    day = int(obs.get("day", 0) or 0)
    step = int(obs.get("step", day * 24 + int(obs.get("hour", 0) or 0)) or 0)
    unit_count = 1 + len(farm.get("hands", []) or [])
    cache = _ROUTE_CERTIFICATES.get(seat)
    quadrant_signature = tuple(sorted(
        farm.get("unlocked_quadrants", []) or ["NW"]
    ))
    if step == 0 or (cache is not None and step < int(cache.get("step", -1))):
        cache = None

    live_keys = {_job_key(job) for job in jobs}
    full_replan = (
        cache is None
        or int(cache.get("day", -1)) != day
        or unit_count < int(cache.get("units", -1))
        or bool(cache.get("liquidation", False)) != bool(liquidation)
        or tuple(cache.get("quadrants", ())) != quadrant_signature
    )
    if cache is not None:
        _prune_routes(cache, live_keys)
        covered = _covered_keys(cache)
        critical = {
            _job_key(job) for job in jobs if int(job.get("priority", 9)) <= 0
        }
        service_event = any(
            _job_key(job) not in covered
            and _service_job(job)
            and str((job.get("action") or ["PASS"])[0])
            in {"BUILD_COOP", "BUILD_PASTURE", "PLACE", "FEED"}
            for job in jobs
        )
        if critical - covered or service_event:
            full_replan = True

    if full_replan:
        previous = cache
        seed_cache = {
            "day": day,
            "step": step,
            "units": unit_count,
            "liquidation": bool(liquidation),
            "quadrants": quadrant_signature,
            "routes": {},
        }
        routes, undone = _plan_routes(
            obs, farm, private, jobs, previous=previous,
            liquidation=liquidation,
        )
        seed_cache["routes"] = routes
        seed_cache["undone"] = len(undone)
        cache = seed_cache
        _ROUTE_CERTIFICATES[seat] = cache
    else:
        old_units = int(cache.get("units", 0) or 0)
        for index in range(old_units, unit_count):
            cache.setdefault("routes", {})[index] = {
                "carry": {}, "stops": [], "turn_cost": 0,
            }
        cache["units"] = unit_count
        covered = _covered_keys(cache)
        missing_jobs = [job for job in jobs if _job_key(job) not in covered]
        idle = _empty_units(cache, unit_count)
        should_extend = bool(idle) and bool(missing_jobs)
        if should_extend:
            routes, undone = _plan_routes(
                obs, farm, private, missing_jobs, unit_indexes=idle,
                liquidation=liquidation,
            )
            cache["routes"].update(routes)
            cache["undone"] = len(undone)

    cache["step"] = step
    return cache


def _remaining_requirements(certificate):
    required = {}
    for stop in (certificate or {}).get("stops", ()):
        for action in stop.get("ops", ()):
            need = _need_for(action)
            if need is not None:
                required[need] = required.get(need, 0) + 1
    return required


def _drop_action(obs, config, farm, private, jobs, certificate, index, liquidation):
    inventories = list(private.get("inventories", []) or [])
    inventory = dict(inventories[index] or {}) if index < len(inventories) else {}
    products = {
        item: max(0, int(inventory.get(item, 0) or 0))
        for item in _c06.PRODUCTS
        if int(inventory.get(item, 0) or 0) > 0
    }
    if not products:
        return None
    required = _remaining_requirements(certificate)
    if not liquidation and any(
        int(inventory.get(item, 0) or 0) > 0 and quantity > 0
        for item, quantity in required.items()
    ):
        return None

    prices = ((obs.get("market", {}) or {}).get("prices", {}) or {})
    cash_units = sum(products.values())
    cash_value = sum(
        quantity * float(prices.get(item, _c06.MARKET[item][0]) or _c06.MARKET[item][0])
        for item, quantity in products.items()
    )
    summary = _c06._survey(farm, private, None, int(obs.get("day", 0) or 0))
    pressure = summary["shed_load"] + summary["carried_load"]
    cash_needed = (
        int(obs.get("day", 0) or 0) < 22
        and float(farm.get("money", 0) or 0) < 500
    )
    should_drop = (
        liquidation
        or pressure >= _c06.DROP_PRESSURE_THRESHOLD
        or cash_units >= _c06.DROP_UNIT_THRESHOLD
        or cash_value >= _c06.DROP_VALUE_THRESHOLD
        or (cash_needed and cash_value >= _c06.CASH_DROP_VALUE_THRESHOLD)
    )
    if not should_drop:
        return None

    capacity = int(_c06._cfg(config, "shedCapacity", _c06.SHED_CAPACITY))
    shed = private.get("shed", {}) or {}
    room = max(0, capacity - sum(max(0, int(value or 0)) for value in shed.values()))
    if room <= 0:
        return None
    positions = [farm["farmer"], *(farm.get("hands", []) or [])]
    if index >= len(positions):
        return None
    position = tuple(positions[index])
    sheds = _all_shed_tiles(len(farm["tiles"]))
    if position not in sheds:
        return _step_toward(position, _nearest_shed(position, len(farm["tiles"])))

    nonproducts = sum(
        max(0, int(quantity or 0))
        for item, quantity in inventory.items()
        if item not in _c06.PRODUCTS
    )
    if nonproducts <= 0 and cash_units <= room:
        return ["DROP"]
    item = max(
        products,
        key=lambda name: (
            float(prices.get(name, _c06.MARKET[name][0]) or _c06.MARKET[name][0]),
            name,
        ),
    )
    quantity = min(products[item], room)
    return ["PLACE", item, quantity] if quantity > 0 else None


def _route_action(obs, farm, private, certificate, index):
    positions = [farm["farmer"], *(farm.get("hands", []) or [])]
    if index >= len(positions):
        return ["PASS"]
    position = tuple(positions[index])
    inventories = list(private.get("inventories", []) or [])
    inventory = dict(inventories[index] or {}) if index < len(inventories) else {}
    requirements = _remaining_requirements(certificate)
    missing = {
        item: max(0, quantity - int(inventory.get(item, 0) or 0))
        for item, quantity in requirements.items()
        if quantity > int(inventory.get(item, 0) or 0)
    }
    shed = private.get("shed", {}) or {}
    available = [
        item for item in sorted(missing, key=lambda name: (name != "WHEAT", name))
        if int(shed.get(item, 0) or 0) > 0
    ]
    if available:
        target = _nearest_shed(position, len(farm["tiles"]))
        if position in _all_shed_tiles(len(farm["tiles"])):
            item = available[0]
            return ["PICKUP", item, min(missing[item], int(shed.get(item, 0) or 0))]
        return _step_toward(position, target)

    for stop in (certificate or {}).get("stops", ()):
        if not stop.get("ops"):
            continue
        action = list(stop["ops"][0])
        need = _need_for(action)
        if need is not None and int(inventory.get(need, 0) or 0) <= 0:
            continue
        target = tuple(stop["target"])
        return action if position == target else _step_toward(position, target)
    if missing:
        target = _nearest_shed(position, len(farm["tiles"]))
        return ["PASS"] if position in _all_shed_tiles(len(farm["tiles"])) else _step_toward(position, target)
    return ["PASS"]


def _unit_actions(obs, config, farm, private, roles):
    day = int(obs.get("day", 0) or 0)
    hour = int(obs.get("hour", 0) or 0)
    step = int(obs.get("step", day * 24 + hour) or 0)
    final_step = int(_c06._cfg(config, "episodeSteps", 720)) - 2
    liquidation = max(0, final_step - step + 1) <= _c06.LIQUIDATION_TURNS
    jobs = _live_jobs(obs, farm, private, roles, liquidation)
    cache = _ensure_routes(obs, farm, private, jobs, liquidation)
    positions = [farm["farmer"], *(farm.get("hands", []) or [])]
    actions = []
    for index in range(len(positions)):
        certificate = (cache.get("routes", {}) or {}).get(index, {"stops": []})
        action = _drop_action(
            obs, config, farm, private, jobs, certificate, index, liquidation,
        )
        actions.append(action or _route_action(obs, farm, private, certificate, index))
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
        "market": _c06._market_actions(obs, config, farm, private, roles, field),
    }


def whitebox_v384_public_daily_route_certificate(obs, config=None):
    try:
        return _decide(obs, config)
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
