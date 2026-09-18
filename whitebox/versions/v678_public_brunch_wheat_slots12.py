"""V678: reserve the thirteenth wheat-route tile only for public brunch demand.

The wheat route benefits from one extra crop role when the live town has
unlocked BRUNCH_SPOT, whose public recipe consumes both wheat and strawberry.
Use V675's twelve animal slots only in that state; otherwise retain the
thirteen-slot wheat portfolio.  Light/default routes and every other decision
remain unchanged.
"""

from whitebox.versions import v675_public_wheat_slots12 as _v675


_v623 = _v675._v623
_WHEAT_12 = {"NW": 4, "NE": 4, "SW": 4, "SE": 0}
_WHEAT_13 = {"NW": 4, "NE": 5, "SW": 4, "SE": 0}


def whitebox_v678_public_brunch_wheat_slots12(obs):
    shops = ((obs or {}).get("town", {}) or {}).get(
        "unlocked_shops", []
    ) or []
    _v623._WHEAT = dict(
        _WHEAT_12 if "BRUNCH_SPOT" in shops else _WHEAT_13
    )
    return _v675.whitebox_v675_public_wheat_slots12(obs)
