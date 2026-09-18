"""V318: retain the full three-day feed certificate on day 28.

V308 retained two days but the base market routine still computed a
three-day purchase target, so it could sell 15 wheat and immediately buy 15.
The reserve is now exactly the same certificate used by the purchase branch,
which makes the day-28 transaction set idempotent.  Day 29 terminal
liquidation sells the certificate normally.
"""

from whitebox.versions import v305_public_rate12_fert6 as _v305

_c06 = _v305._c06
_base_sell_quantity = _c06._sell_quantity


def _farm_animals(obs):
    player = int((obs or {}).get("player", 0) or 0)
    farms = (obs or {}).get("farms", []) or []
    if not (0 <= player < len(farms)):
        return 0
    return sum(
        1
        for row in farms[player].get("tiles", []) or []
        for tile in row or ()
        if isinstance(tile, dict) and tile.get("animal") in _c06.ANIMALS
    )


def _sell_quantity(item, have, inventory, day, shed_load, obs=None):
    quantity = _base_sell_quantity(item, have, inventory, day, shed_load, obs)
    if item == "WHEAT" and int(day) == _c06.TOTAL_DAYS - 2:
        reserve = _farm_animals(obs) * int(_c06.FEED_STOCK_DAYS)
        quantity = min(quantity, max(0, int(have) - reserve))
    return min(int(have), max(0, int(quantity)))


_c06._sell_quantity = _sell_quantity


def whitebox_v318_public_wheat_certificate3(obs):
    return _c06.agent(obs)
