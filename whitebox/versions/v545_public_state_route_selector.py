"""V545: select a public-state route family from the first expansion signal.

The selector has three generic modes: a wheat-heavy public crop book, a
lighter animal footprint when the visible book is animal-heavy but not
strawberry-heavy, and the audited V454 default.  It stores only the current
seat's mode and resets it when the episode step rewinds; no opponent label,
seed, seat pairing, or future action is referenced.
"""

from whitebox.versions import v454_public_weed_window_sale_cash as _v454


_c06 = _v454._c06
_base_herd_targets = _c06._herd_targets
_base_slots = dict(_c06.ANIMAL_SLOTS)
_base_crop_mix = dict(_c06.CROP_MIX)
_base_max_hands = _c06.MAX_HANDS
_MODE = {}
_LAST_STEP = {}

_WHEAT30 = {
    "NW": {"MELON": 10, "WHEAT": 10, "CARROT": 2},
    "NE": {"WHEAT": 10, "CARROT": 1},
    "SW": {"WHEAT": 10, "CARROT": 1},
    "SE": {"WHEAT": 10, "CARROT": 2},
}


def _counts(farm):
    crops = {"STRAWBERRY": 0, "WHEAT": 0, "MELON": 0}
    animals = {"COW": 0, "SHEEP": 0}
    for row in farm.get("tiles", []) or ():
        for tile in row or ():
            if not isinstance(tile, dict):
                continue
            if tile.get("crop") in crops:
                crops[tile["crop"]] += 1
            if tile.get("animal") in animals:
                animals[tile["animal"]] += 1
    return crops, animals


def _update_mode(obs):
    player = int((obs or {}).get("player", 0) or 0)
    step = int((obs or {}).get("step", 0) or 0)
    if step == 0 or step < _LAST_STEP.get(player, -1):
        _MODE.pop(player, None)
    _LAST_STEP[player] = step
    day = int((obs or {}).get("day", 0) or 0)
    farms = (obs or {}).get("farms", []) or []
    if player in _MODE or not (6 <= day <= 12):
        return _MODE.get(player, "default")
    for index, rival in enumerate(farms):
        if index == player:
            continue
        crops, animals = _counts(rival)
        if crops["WHEAT"] >= 9 and crops["STRAWBERRY"] < 15:
            _MODE[player] = "wheat"
            return "wheat"
        if sum(animals.values()) >= 8 and crops["STRAWBERRY"] < 15:
            _MODE[player] = "light"
            return "light"
    return "default"


def _herd_targets(obs, farm, private, capacity):
    raw = _base_herd_targets(obs, farm, private, capacity)
    player = int((obs or {}).get("player", 0) or 0)
    if _MODE.get(player) != "light":
        return raw
    total = sum(raw.values())
    target = min(13, max(total, 4))
    if total <= target:
        return raw
    cows = min(raw.get("COW", 0), target - 1)
    return {"COW": cows, "SHEEP": max(1, target - cows)}


_c06._herd_targets = _herd_targets


def whitebox_v545_public_state_route_selector(obs):
    mode = _update_mode(obs)
    old_slots = _c06.ANIMAL_SLOTS
    old_mix = _c06.CROP_MIX
    old_hands = _c06.MAX_HANDS
    if mode == "light":
        _c06.ANIMAL_SLOTS = {"NW": 4, "NE": 5, "SW": 4, "SE": 0}
        _c06.CROP_MIX = dict(_base_crop_mix)
        _c06.MAX_HANDS = 14
    elif mode == "wheat":
        _c06.ANIMAL_SLOTS = dict(_base_slots)
        _c06.CROP_MIX = dict(_WHEAT30)
        _c06.MAX_HANDS = _base_max_hands
    else:
        _c06.ANIMAL_SLOTS = dict(_base_slots)
        _c06.CROP_MIX = dict(_base_crop_mix)
        _c06.MAX_HANDS = _base_max_hands
    try:
        return _v454.whitebox_v454_public_weed_window_sale_cash(obs)
    finally:
        _c06.ANIMAL_SLOTS = old_slots
        _c06.CROP_MIX = old_mix
        _c06.MAX_HANDS = old_hands
