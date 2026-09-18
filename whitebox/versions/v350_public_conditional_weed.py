"""V350: service a severe visible weed backlog before it blocks crops.

Weed clearing stays at the base priority for ordinary noise.  Once the live
farm has a large backlog, clearing jobs receive a limited priority bump while
there is still time to plant; this uses no opponent identity or schedule.
"""

from whitebox.versions import v336_public_care_value25 as _v336

_c06 = _v336._c06
_base_jobs = _c06._field_jobs


def _field_jobs(obs, farm, private, roles, liquidation):
    jobs = _base_jobs(obs, farm, private, roles, liquidation)
    if liquidation:
        return jobs
    day = int((obs or {}).get("day", 0) or 0)
    weeds = sum(
        1
        for row in farm.get("tiles", []) or []
        for tile in row or ()
        if isinstance(tile, dict) and tile.get("kind") == "WEED"
    )
    if weeds < 9 or day > 21:
        return jobs
    # At this threshold the backlog itself is the evidence of lost land.
    # Priority 3 remains below feeding/watering/harvest, but outranks normal
    # planting and routine care.
    for job in jobs:
        if job.get("reason") == "dig_weed":
            job["priority"] = min(int(job.get("priority", 4)), 3)
            job["value"] = max(float(job.get("value", 0)), 160.0)
    return jobs


_c06._field_jobs = _field_jobs


def whitebox_v350_public_conditional_weed(obs):
    return _c06.agent(obs)
