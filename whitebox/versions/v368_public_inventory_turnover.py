"""V368: bank a material worker load before it becomes route-dead stock.

The shed holds one hundred units.  A worker carrying at least one eighth of
that capacity, or goods worth the second land purchase, has a concrete capital
reason to return.  DROP remains a production-tier mission, so survival feed,
critical water and harvest deadlines retain priority.
"""

from whitebox.versions import v361_public_wheat_rotation22 as _v361


_c06 = _v361._c06
_c06.DROP_PRESSURE_THRESHOLD = 75
_c06.DROP_UNIT_THRESHOLD = max(1, _c06.SHED_CAPACITY // 8)
_c06.DROP_VALUE_THRESHOLD = _c06.LAND_PRICES[1]
_c06.CASH_DROP_VALUE_THRESHOLD = 300


def whitebox_v368_public_inventory_turnover(obs):
    return _c06.agent(obs)
