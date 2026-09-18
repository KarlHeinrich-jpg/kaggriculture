"""V454: use exact early sale cash during a visible rival weed delay.

On day two, a clean own field with open land can immediately deploy committed
seed.  Exact sale cash is released only while another public farm has a weed,
which certifies a competing service delay.  Without that delay, V452's
conservative buffer avoids entering a synchronized crop expansion race.
"""

from whitebox.versions import v452_public_cow_service_commitment as _v452


_c06 = _v452._c06


def _field_counts(farm):
    open_cells = 0
    weeds = 0
    for row in farm.get("tiles", []) or []:
        for tile in row or ():
            if tile is None:
                open_cells += 1
            elif isinstance(tile, dict) and tile.get("kind") == "WEED":
                weeds += 1
    return open_cells, weeds


def _weed_window(obs):
    farms = (obs or {}).get("farms", []) or []
    player = int((obs or {}).get("player", 0) or 0)
    if not (0 <= player < len(farms)):
        return False
    own_open, own_weeds = _field_counts(farms[player])
    rival_weeds = sum(
        _field_counts(farm)[1]
        for index, farm in enumerate(farms)
        if index != player
    )
    return (
        int((obs or {}).get("day", 0) or 0) == 2
        and own_open > 0
        and own_weeds == 0
        and rival_weeds > 0
    )


def whitebox_v454_public_weed_window_sale_cash(obs):
    previous = _c06.SALE_CASH_FACTOR
    _c06.SALE_CASH_FACTOR = 1.0 if _weed_window(obs) else 0.85
    try:
        return _v452.whitebox_v452_public_cow_service_commitment(obs)
    finally:
        _c06.SALE_CASH_FACTOR = previous
