"""V423: combine mature-demand continuity with cow-backed crop rotation.

Both mechanisms are independently public-state based.  Route continuity uses
only the current town demand after the third shop unlock; melon rotation uses
only our observed completed melon tiles, current herd composition, planting
legality, and current town demand.  No opponent identity or action sequence is
retained.
"""

from whitebox.versions import v416_public_cow_backed_melon_rotation as _v416
from whitebox.versions import v422_public_mature_demand_stickiness as _v422


_c06 = _v416._c06


def whitebox_v423_public_mature_routes_cow_rotation(obs):
    return _v422.whitebox_v422_public_mature_demand_stickiness(obs)
