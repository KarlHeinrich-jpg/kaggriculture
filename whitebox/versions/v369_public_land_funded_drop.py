"""V369: bank carried goods once they can fund the second land purchase.

This isolates the only rule-derived part of V368: the value trigger is the
public 2,000 cost of the next expansion.  Unit, shed-pressure and emergency
cash thresholds stay exactly at V361 values.
"""

from whitebox.versions import v361_public_wheat_rotation22 as _v361


_c06 = _v361._c06
_c06.DROP_VALUE_THRESHOLD = _c06.LAND_PRICES[1]


def whitebox_v369_public_land_funded_drop(obs):
    return _c06.agent(obs)
