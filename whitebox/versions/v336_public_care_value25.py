"""V336: retain CARE's original priority, but price its multiplier at 2.5x."""
from whitebox.versions import v318_public_wheat_certificate3 as _v318
_c06 = _v318._c06
_base_jobs = _c06._field_jobs
def _field_jobs(obs, farm, private, roles, liquidation):
    jobs = _base_jobs(obs, farm, private, roles, liquidation)
    if not liquidation:
        prices = ((obs or {}).get("market", {}) or {}).get("prices", {}) or {}
        for job in jobs:
            if job.get("reason") != "care": continue
            t = job.get("target", (0, 0)); tile = farm.get("tiles", [])[int(t[1])][int(t[0])]
            animal = tile.get("animal") if isinstance(tile, dict) else None; rule = _c06.ANIMALS.get(animal)
            if rule:
                p = float(prices.get(rule["product"], _c06.MARKET[rule["product"]][0]) or _c06.MARKET[rule["product"]][0])
                job["value"] = max(float(job.get("value", 0)), 2.5 * p)
    return jobs
_c06._field_jobs = _field_jobs
def whitebox_v336_public_care_value25(obs): return _c06.agent(obs)
