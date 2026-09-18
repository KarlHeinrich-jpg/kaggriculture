"""V623: public FARMERS_MARKET light route with six cows."""

from whitebox.versions import v608_public_sticky_low_wheat_route as _v608


_v545 = _v608._v545
_v454 = _v545._v454
_c06 = _v545._c06
_base_targets = _v545._base_herd_targets
_FULL = dict(_v545._base_slots)
_WHEAT = {"NW": 4, "NE": 5, "SW": 4, "SE": 0}


def _farmers_market(obs):
    shops = ((obs or {}).get("town", {}) or {}).get("unlocked_shops", []) or []
    return "FARMERS_MARKET" in shops


def _herd_targets(obs, farm, private, capacity):
    raw = _base_targets(obs, farm, private, capacity)
    player = int((obs or {}).get("player", 0) or 0)
    if _v545._MODE.get(player) != "light" or not _farmers_market(obs):
        return raw
    total = min(int(capacity), sum(raw.values()), 13)
    if total < 4:
        return raw
    cows = min(total, 6)
    return {"COW": cows, "SHEEP": max(0, total - cows)}


_c06._herd_targets = _herd_targets


def _route(obs):
    mode = _v545._update_mode(obs)
    old_slots, old_mix, old_hands = _c06.ANIMAL_SLOTS, _c06.CROP_MIX, _c06.MAX_HANDS
    if mode == "light":
        _c06.ANIMAL_SLOTS = {"NW": 4, "NE": 5, "SW": 4, "SE": 0}
        _c06.CROP_MIX = dict(_v545._base_crop_mix)
        _c06.MAX_HANDS = 14
    elif mode == "wheat":
        _c06.ANIMAL_SLOTS = dict(_WHEAT)
        _c06.CROP_MIX = dict(_v545._WHEAT30)
        _c06.MAX_HANDS = _v545._base_max_hands
    else:
        _c06.ANIMAL_SLOTS = dict(_FULL)
        _c06.CROP_MIX = dict(_v545._base_crop_mix)
        _c06.MAX_HANDS = _v545._base_max_hands
    try:
        return _v454.whitebox_v454_public_weed_window_sale_cash(obs)
    finally:
        _c06.ANIMAL_SLOTS, _c06.CROP_MIX, _c06.MAX_HANDS = old_slots, old_mix, old_hands


_v545.whitebox_v545_public_state_route_selector = _route


def whitebox_v623_public_light_farmers_cow6(obs):
    return _v608.whitebox_v608_public_sticky_low_wheat_route(obs)
