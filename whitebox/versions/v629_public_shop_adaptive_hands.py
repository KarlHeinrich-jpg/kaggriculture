"""V629: public-shop adaptive light-route hand capacity.

The light route keeps fourteen hands for the yarn-led opening, where crop
service is the binding capacity, and caps at twelve hands after a public
farmers-market opening, where early capital is tighter.  The branch uses only
the current town observation and the retained generic light certificate.
"""

from whitebox.versions import v623_public_light_farmers_cow6 as _v623


_v545 = _v623._v545
_c06 = _v545._c06
_base_target_hands = _c06._target_hands


def _target_hands(obs, farm, private, roles):
    value = _base_target_hands(obs, farm, private, roles)
    player = int((obs or {}).get("player", 0) or 0)
    if _v545._MODE.get(player) != "light":
        return value
    shops = ((obs or {}).get("town", {}) or {}).get("unlocked_shops", []) or []
    cap = 12 if "FARMERS_MARKET" in shops else 14
    return min(int(value), cap)


_c06._target_hands = _target_hands


def whitebox_v629_public_shop_adaptive_hands(obs):
    return _v623.whitebox_v623_public_light_farmers_cow6(obs)
