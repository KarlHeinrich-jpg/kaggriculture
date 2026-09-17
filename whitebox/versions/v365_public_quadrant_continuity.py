"""V365: price one lost local round trip on cross-quadrant field work.

Manhattan distance prices the current trip but not the next task displaced when
a worker abandons its local quadrant.  For otherwise comparable field jobs we
charge exactly two movement turns, one to cross the boundary and one to restore
local service continuity.  Survival priorities still dominate this tie-break.
"""

from whitebox.versions import v361_public_wheat_rotation22 as _v361


_c06 = _v361._c06
_c06.QUADRANT_CROSS_COST = 2.0 * _c06.TRAVEL_COST


def whitebox_v365_public_quadrant_continuity(obs):
    return _c06.agent(obs)
