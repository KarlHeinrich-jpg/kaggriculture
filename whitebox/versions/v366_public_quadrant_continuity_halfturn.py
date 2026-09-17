"""V366: half-turn shadow price for otherwise comparable cross-quadrant work."""

from whitebox.versions import v361_public_wheat_rotation22 as _v361


_c06 = _v361._c06
_c06.QUADRANT_CROSS_COST = 0.5 * _c06.TRAVEL_COST


def whitebox_v366_public_quadrant_continuity_halfturn(obs):
    return _c06.agent(obs)
