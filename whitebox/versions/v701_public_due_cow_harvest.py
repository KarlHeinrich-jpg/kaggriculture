"""V701: harvest two held milk units before a due production tick.

V684 normally waits for three animal outputs or a capacity boundary.  A cow
with two held units that will produce again tonight can instead bank those
units now, freeing public capacity before the next milk tick.  The rule is
derived only from the current cow state and the engine production interval;
it adds no opponent, seed, route, or future-action memory.
"""

from whitebox.versions import v684_public_recertified_nonfarmers_light as _v684


_v678 = _v684._v678
_v659 = _v678._v675._v659
_c06 = _v659._c06
_base_field_jobs = _c06._field_jobs


def _field_jobs(obs, farm, private, roles, liquidation):
    jobs = _base_field_jobs(obs, farm, private, roles, liquidation)
    if liquidation or int((obs or {}).get("day", 0) or 0) >= 27:
        return jobs

    day = int((obs or {}).get("day", 0) or 0)
    prices = ((obs or {}).get("market", {}) or {}).get("prices", {}) or {}
    emitted = {
        (tuple(job.get("target", ())), (job.get("action") or [""])[0])
        for job in jobs
    }
    for y, row in enumerate(farm.get("tiles", []) or []):
        for x, tile in enumerate(row or []):
            if (
                not isinstance(tile, dict)
                or tile.get("animal") != "COW"
                or int(tile.get("yield_units", 0) or 0) != 2
                or ((x, y), "HARVEST") in emitted
                or not _c06._animal_produces_tonight(
                    tile, _c06.ANIMALS["COW"], day
                )
            ):
                continue
            price = float(
                prices.get("MILK", _c06.MARKET["MILK"][0])
                or _c06.MARKET["MILK"][0]
            )
            _c06._add_job(
                jobs,
                2,
                2.0 * price,
                (x, y),
                ("HARVEST",),
                reason="due_cow_capacity_harvest",
            )
    return jobs


_c06._field_jobs = _field_jobs


def whitebox_v701_public_due_cow_harvest(obs):
    return _v684.whitebox_v684_public_recertified_nonfarmers_light(obs)
