"""V699: eight cows in the public FARMERS_MARKET light portfolio.

This is V698's second transparent composition point.  It keeps V684's fixed
thirteen-cell public light capacity and exchanges two sheep roles for cows;
all task generation, routing, capital, market, and re-certification rules stay
unchanged.
"""

from whitebox.versions import v698_public_farmers_cow7 as _v698


def _herd_targets(obs, farm, private, capacity):
    raw = _v698._base_targets(obs, farm, private, capacity)
    player = int((obs or {}).get("player", 0) or 0)
    if (
        _v698._v545._MODE.get(player) != "light"
        or not _v698._v645._farmers_market(obs)
    ):
        return raw
    total = min(int(capacity), sum(raw.values()), 13)
    if total < 4:
        return raw
    cows = min(total, 8)
    return {"COW": cows, "SHEEP": max(0, total - cows)}


_v698._c06._herd_targets = _herd_targets


def whitebox_v699_public_farmers_cow8(obs):
    return _v698.whitebox_v698_public_farmers_cow7(obs)
