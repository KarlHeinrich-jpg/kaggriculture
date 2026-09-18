"""V702: due cow-capacity harvest only on the ordinary public route.

V701 showed that harvesting two held milk units before a due production tick
helps the ordinary public economy but competes with the specialized light and
wheat route portfolios.  Apply the same engine-derived capacity rule only
after V684's live public certificate has selected ``default``.  The mode is
derived from visible farms and prices, not an opponent, seed, or seat label.
"""

from whitebox.versions import v684_public_recertified_nonfarmers_light as _v684


_v678 = _v684._v678
_v659 = _v678._v675._v659
_c06 = _v659._c06
_v545 = _v684._v545
_base_field_jobs = _c06._field_jobs


def _field_jobs(obs, farm, private, roles, liquidation):
    jobs = _base_field_jobs(obs, farm, private, roles, liquidation)
    player = int((obs or {}).get("player", 0) or 0)
    day = int((obs or {}).get("day", 0) or 0)
    if liquidation or day >= 27 or _v545._MODE.get(player) != "default":
        return jobs

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
                reason="default_due_cow_capacity_harvest",
            )
    return jobs


_c06._field_jobs = _field_jobs


def whitebox_v702_public_default_due_cow_harvest(obs):
    return _v684.whitebox_v684_public_recertified_nonfarmers_light(obs)
