"""V700: close the public animal HARVEST -> CARE capacity cycle.

V684 decides whether CARE fits before executing a same-tile HARVEST.  A full
animal can therefore expose a live harvest while CARE is suppressed by the
pre-harvest held-output cap.  When the current public jobs already contain
that HARVEST, add its CARE suffix and execute FEED -> HARVEST -> CARE ->
COLLECT.  HARVEST releases capacity; CARE then creates only the engine-defined
pending bonus for a later fed production tick.  Every suffix is rebuilt from
the current tile and current jobs, with no retained route or future action.
"""

from whitebox.versions import v684_public_recertified_nonfarmers_light as _v684


_v678 = _v684._v678
_v659 = _v678._v675._v659
_v645 = _v659._v649._v646._v645
_v545 = _v645._v545
_c06 = _v659._c06
_v384 = _v659._v464._v384
_base_field_jobs = _c06._field_jobs
_base_task_groups = _v384._task_groups


def _field_jobs(obs, farm, private, roles, liquidation):
    jobs = _base_field_jobs(obs, farm, private, roles, liquidation)
    player = int((obs or {}).get("player", 0) or 0)
    day = int((obs or {}).get("day", 0) or 0)
    if (
        liquidation
        or day > 27
        or _v545._MODE.get(player) != "light"
        or not _v645._farmers_market(obs)
    ):
        return jobs

    harvested = {
        tuple(job.get("target", ()))
        for job in jobs
        if (job.get("action") or [""])[0] == "HARVEST"
        and str(job.get("reason", "")) == "animal_harvest"
    }
    cared = {
        tuple(job.get("target", ()))
        for job in jobs
        if (job.get("action") or [""])[0] == "CARE"
    }
    prices = ((obs or {}).get("market", {}) or {}).get("prices", {}) or {}
    tiles = farm.get("tiles", []) or []
    for target in sorted(harvested - cared, key=lambda pos: (pos[1], pos[0])):
        x, y = target
        tile = tiles[y][x]
        if not isinstance(tile, dict) or tile.get("cared_today", False):
            continue
        rule = _c06.ANIMALS.get(tile.get("animal"))
        if rule is None:
            continue
        price = float(
            prices.get(rule["product"], _c06.MARKET[rule["product"]][0])
            or _c06.MARKET[rule["product"]][0]
        )
        if price < 20:
            continue
        _c06._add_job(
            jobs,
            3,
            price,
            target,
            ("CARE",),
            reason="post_harvest_capacity_care",
        )
    return jobs


def _task_groups(jobs):
    tasks = _base_task_groups(jobs)
    order = {
        "FEED": 0,
        "HARVEST": 1,
        "CARE": 2,
        "COLLECT_FERTILIZER": 3,
    }
    for task in tasks:
        operations = {action[0] for action in task.ops if action}
        if "HARVEST" in operations and "CARE" in operations:
            task.ops.sort(
                key=lambda action: (order.get(action[0], 10), tuple(action))
            )
    return tasks


_c06._field_jobs = _field_jobs
_v384._task_groups = _task_groups


def whitebox_v700_public_post_harvest_animal_care(obs):
    return _v684.whitebox_v684_public_recertified_nonfarmers_light(obs)
