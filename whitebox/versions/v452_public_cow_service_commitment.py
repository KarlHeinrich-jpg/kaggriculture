"""V452: stabilize cow-dominant service routes at the late growth peak.

On day seventeen, a cow-dominant mature herd under stronger public milk demand
creates a dense daily feed, care, fertilizer, and harvest route.  This visible
certificate credits six movement turns for retaining a still-live target.
Sheep-dominant farms and all other days keep V448's existing route policy.
"""

from whitebox.versions import v448_public_unfunded_seed_cash as _v448


_c06 = _v448._c06
_base_unit_actions = _v448._v423._v422._base_unit_actions


def _own_animals(farm):
    counts = {animal: 0 for animal in _c06.ANIMALS}
    for row in farm.get("tiles", []) or []:
        for tile in row or ():
            if isinstance(tile, dict) and tile.get("animal") in counts:
                counts[tile["animal"]] += 1
    return counts


def _cow_service_peak(obs, farm):
    animals = _own_animals(farm)
    return (
        int((obs or {}).get("day", 0) or 0) == 17
        and animals["COW"] > animals["SHEEP"]
        and _c06._town_demand_per_day(obs, "MILK")
        > _c06._town_demand_per_day(obs, "WOOL")
    )


def _unit_actions(obs, config, farm, private, roles):
    day = int((obs or {}).get("day", 0) or 0)
    mature = (
        day >= 9
        and _c06._town_demand_per_day(obs, "MILK")
        > _c06._town_demand_per_day(obs, "WOOL")
    )
    previous = _c06.TARGET_STICKINESS_BONUS
    _c06.TARGET_STICKINESS_BONUS = (
        6.0 * _c06.TRAVEL_COST
        if _cow_service_peak(obs, farm)
        else _c06.TRAVEL_COST if mature else 0.0
    )
    try:
        return _base_unit_actions(obs, config, farm, private, roles)
    finally:
        _c06.TARGET_STICKINESS_BONUS = previous


_v448._unit_actions = _unit_actions


def whitebox_v452_public_cow_service_commitment(obs):
    return _v448.whitebox_v448_public_unfunded_seed_cash(obs)
