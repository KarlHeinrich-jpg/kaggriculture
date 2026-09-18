"""V706: execute live input-free work under genuinely idle workers.

After V684 chooses its ordinary action, a worker that would PASS may execute
one distinct current public operation on the tile it already occupies.  The
rule admits only input-free work and never moves a worker, spends seed, changes
market orders, or displaces a selected action.  Same-tile conflicts are removed
from the current action set, and all work is rebuilt from the observation.
"""

from whitebox.versions import v684_public_recertified_nonfarmers_light as _v684


_v678 = _v684._v678
_v659 = _v678._v675._v659
_c06 = _v659._c06

_ORDER = {
    "WATER": 0,
    "HARVEST": 1,
    "CARE": 2,
    "COLLECT_FERTILIZER": 3,
    "DIG": 4,
}


def _idle_colocated_work(obs, action):
    farms = (obs or {}).get("farms", []) or []
    player = int((obs or {}).get("player", 0) or 0)
    if not (0 <= player < len(farms)):
        return action
    farm = farms[player]
    private = (obs or {}).get("private", {}) or {}
    day = int((obs or {}).get("day", 0) or 0)
    step = int((obs or {}).get("step", 0) or 0)
    liquidation = max(0, 718 - step + 1) <= _c06.LIQUIDATION_TURNS
    roles = _c06._role_plan(obs, farm)
    jobs = _c06._field_jobs(obs, farm, private, roles, liquidation)
    positions = [farm.get("farmer"), *(farm.get("hands", []) or [])]
    actions = [list(action.get("farmer") or ["PASS"])]
    actions.extend(
        list(value or ["PASS"])
        for value in (action.get("hands", []) or [])
    )
    while len(actions) < len(positions):
        actions.append(["PASS"])

    claimed = {
        (tuple(positions[index]), tuple(value))
        for index, value in enumerate(actions)
        if index < len(positions) and value and value[0] != "PASS"
    }
    by_target = {}
    for job in jobs:
        planned = list(job.get("action") or [])
        target = tuple(job.get("target", ()))
        if (
            not planned
            or planned[0] not in _ORDER
            or job.get("need") is not None
            or planned[0] == "DIG" and day >= 27
        ):
            continue
        by_target.setdefault(target, []).append(job)

    for index, value in enumerate(actions):
        if index >= len(positions) or value != ["PASS"]:
            continue
        target = tuple(positions[index])
        candidates = [
            job for job in by_target.get(target, ())
            if (target, tuple(job["action"])) not in claimed
        ]
        if not candidates:
            continue
        job = min(
            candidates,
            key=lambda candidate: (
                int(candidate.get("priority", 9)),
                _ORDER[candidate["action"][0]],
                -float(candidate.get("value", 0.0)),
                tuple(candidate["action"]),
            ),
        )
        replacement = list(job["action"])
        actions[index] = replacement
        claimed.add((target, tuple(replacement)))

    result = dict(action)
    result["farmer"] = actions[0] if actions else ["PASS"]
    result["hands"] = actions[1:]
    return result


def whitebox_v706_public_idle_colocated_work(obs):
    action = _v684.whitebox_v684_public_recertified_nonfarmers_light(obs)
    return _idle_colocated_work(obs, action)
