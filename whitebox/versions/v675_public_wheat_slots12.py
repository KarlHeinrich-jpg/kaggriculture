"""V675: reserve one extra crop tile only in the public wheat route.

V659's sticky selector exposes a named ``wheat`` mode when the live rival farm
has a wheat-heavy, non-strawberry public crop book.  In that mode only, use
twelve animal slots instead of thirteen so one more already-unlocked tile
remains a crop role.  Light and default routes are unchanged.
"""

from whitebox.versions import v659_public_idle_undone_refill as _v659


_v623 = _v659._v649._v646._v645._v623
_v623._WHEAT = {"NW": 4, "NE": 4, "SW": 4, "SE": 0}


def whitebox_v675_public_wheat_slots12(obs):
    return _v659.whitebox_v659_public_idle_undone_refill(obs)
