"""V608: sticky public low-wheat market route.

Once a route is selected from the public signal it remains fixed for the
episode, matching V545's certificate semantics.  The earlier challenger
incorrectly re-tested the low-wheat condition after later replanting.
"""

from whitebox.versions import v546_public_state_wheat_only as _v546


_v545 = _v546._v545
_base_public_selector = _v546._base_update_mode
_FULL = dict(_v545._base_slots)
_WHEAT_SLOTS = {"NW": 4, "NE": 5, "SW": 4, "SE": 0}


def _low_wheat_animals(obs):
    player = int((obs or {}).get("player", 0) or 0)
    for index, rival in enumerate((obs or {}).get("farms", []) or ()):
        if index == player:
            continue
        wheat = animals = 0
        for row in rival.get("tiles", []) or ():
            for tile in row or ():
                if not isinstance(tile, dict):
                    continue
                wheat += tile.get("crop") == "WHEAT"
                animals += bool(tile.get("animal"))
        if animals >= 8 and wheat <= 5:
            return True
    return False


def _wool_favorable(obs):
    prices = ((obs or {}).get("market", {}) or {}).get("prices", {}) or {}
    return float(prices.get("WOOL", 200) or 200) >= float(
        prices.get("MILK", 160) or 160
    )


def _update_mode(obs):
    player = int((obs or {}).get("player", 0) or 0)
    step = int((obs or {}).get("step", 0) or 0)
    if step == 0 or step < _v545._LAST_STEP.get(player, -1):
        _v545._MODE.pop(player, None)
    _v545._LAST_STEP[player] = step
    existing = _v545._MODE.get(player)
    if existing in {"light", "wheat", "default"}:
        mode = existing
    else:
        mode = _base_public_selector(obs)
        if mode == "light" and not (
            _low_wheat_animals(obs) and _wool_favorable(obs)
        ):
            _v545._MODE[player] = "default"
            mode = "default"
    _v545._base_slots = dict(_WHEAT_SLOTS if mode == "wheat" else _FULL)
    return mode


_v545._update_mode = _update_mode


def whitebox_v608_public_sticky_low_wheat_route(obs):
    return _v546.whitebox_v546_public_state_wheat_only(obs)
