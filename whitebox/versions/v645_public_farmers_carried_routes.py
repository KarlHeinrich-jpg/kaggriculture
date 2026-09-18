"""V645: carried-input routes for the public FARMERS_MARKET light state.

The receding route solver raises crop throughput on the light route when the
visible town opens with FARMERS_MARKET, but delays land and capital turnover
in the YARN_STORE opening.  This wrapper therefore enables the transparent
live-state route solver only for the former public state.  All other states
use V629 unchanged.
"""

from whitebox.versions import v629_public_shop_adaptive_hands as _v629
from whitebox.versions import v464_public_carried_input_routes as _v464


_v623 = _v629._v623
_v545 = _v623._v545
_c06 = _v545._c06
_base_selector = _v545.whitebox_v545_public_state_route_selector


def _farmers_market(obs):
    shops = ((obs or {}).get("town", {}) or {}).get("unlocked_shops", []) or []
    return "FARMERS_MARKET" in shops


def _selector(obs):
    mode = _v545._update_mode(obs)
    if mode != "light" or not _farmers_market(obs):
        return _base_selector(obs)
    farms = (obs or {}).get("farms", []) or []
    player = int((obs or {}).get("player", 0) or 0)
    if not (0 <= player < len(farms)):
        return {"farmer": ["PASS"], "hands": [], "market": []}
    farm = farms[player]
    private = (obs or {}).get("private", {}) or {}
    old_slots = _c06.ANIMAL_SLOTS
    old_mix = _c06.CROP_MIX
    old_hands = _c06.MAX_HANDS
    _c06.ANIMAL_SLOTS = {"NW": 4, "NE": 5, "SW": 4, "SE": 0}
    _c06.CROP_MIX = dict(_v545._base_crop_mix)
    _c06.MAX_HANDS = 12
    try:
        roles = _c06._role_plan(obs, farm)
        field = _v464._unit_actions(obs, None, farm, private, roles)
        return {
            "farmer": field["farmer"],
            "hands": field["hands"],
            "market": _c06._market_actions(obs, None, farm, private, roles, field),
        }
    finally:
        _c06.ANIMAL_SLOTS = old_slots
        _c06.CROP_MIX = old_mix
        _c06.MAX_HANDS = old_hands


_v545.whitebox_v545_public_state_route_selector = _selector


def whitebox_v645_public_farmers_carried_routes(obs):
    return _v629.whitebox_v629_public_shop_adaptive_hands(obs)
