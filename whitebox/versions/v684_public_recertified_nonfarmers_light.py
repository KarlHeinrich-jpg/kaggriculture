"""V684: recertify non-FARMERS light routes from the live public economy.

V678's FARMERS_MARKET light route has a dedicated carried-input solver and
late crop rotation, so its initial public certificate remains stable.  Other
light routes use the ordinary matcher: if the visible rival later ceases to
be low-wheat, or the public wool price falls below milk, the original reason
for the reduced livestock footprint no longer holds.  Permanently return
that episode to the default route using only the current farms and market.
"""

from whitebox.versions import v678_public_brunch_wheat_slots12 as _v678
from whitebox.versions import v608_public_sticky_low_wheat_route as _v608


_v545 = _v608._v545
_sticky_update_mode = _v545._update_mode


def _farmers_market(obs):
    shops = ((obs or {}).get("town", {}) or {}).get(
        "unlocked_shops", []
    ) or []
    return "FARMERS_MARKET" in shops


def _update_mode(obs):
    mode = _sticky_update_mode(obs)
    if mode != "light" or _farmers_market(obs):
        return mode
    if _v608._low_wheat_animals(obs) and _v608._wool_favorable(obs):
        return mode
    player = int((obs or {}).get("player", 0) or 0)
    _v545._MODE[player] = "default"
    return "default"


_v545._update_mode = _update_mode


def whitebox_v684_public_recertified_nonfarmers_light(obs):
    return _v678.whitebox_v678_public_brunch_wheat_slots12(obs)
