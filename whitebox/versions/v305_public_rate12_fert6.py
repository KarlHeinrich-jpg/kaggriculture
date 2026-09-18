"""V305 candidate: V278 production-rate tilt plus a six-unit fertilizer
reserve, preventing free byproduct from displacing productive stock."""
from whitebox.versions import v278_public_rate_12_herd as _v278

_c06 = _v278._c06
_base_sell = _c06._sell_quantity


def _sell_quantity(item, have, inventory, day, shed_load, obs=None):
    quantity = _base_sell(item, have, inventory, day, shed_load, obs)
    if item == "FERTILIZER" and have > 6 and day < _c06.TOTAL_DAYS - 1:
        quantity = max(quantity, have - 6)
    return min(have, quantity)


_c06._sell_quantity = _sell_quantity


def whitebox_v305_public_rate12_fert6(obs):
    return _c06.agent(obs)
