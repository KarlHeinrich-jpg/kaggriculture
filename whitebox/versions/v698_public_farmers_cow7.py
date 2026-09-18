"""V698: seven cows in the public FARMERS_MARKET light portfolio.

V684's live light route produces enough wool from its seven sheep but trails
the public milk route.  Preserve its thirteen livestock cells and every route,
crop, market, and hiring rule; only exchange one sheep role for one cow while
the current public certificate is light plus FARMERS_MARKET.
"""

from whitebox.versions import v684_public_recertified_nonfarmers_light as _v684


_v678 = _v684._v678
_v645 = _v678._v675._v659._v649._v646._v645
_v545 = _v645._v545
_c06 = _v645._c06
_base_targets = _c06._herd_targets


def _herd_targets(obs, farm, private, capacity):
    raw = _base_targets(obs, farm, private, capacity)
    player = int((obs or {}).get("player", 0) or 0)
    if (
        _v545._MODE.get(player) != "light"
        or not _v645._farmers_market(obs)
    ):
        return raw
    total = min(int(capacity), sum(raw.values()), 13)
    if total < 4:
        return raw
    cows = min(total, 7)
    return {"COW": cows, "SHEEP": max(0, total - cows)}


_c06._herd_targets = _herd_targets


def whitebox_v698_public_farmers_cow7(obs):
    return _v684.whitebox_v684_public_recertified_nonfarmers_light(obs)
