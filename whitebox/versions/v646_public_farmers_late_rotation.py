"""V646: late short-crop rotation in the public FARMERS_MARKET light state.

After a long-cycle role's public planting deadline, an empty or weeded tile
can no longer execute that role.  In the FARMERS_MARKET light state only,
rotate such tiles to wheat while wheat can still mature, then carrot while
carrot can still mature.  Existing plants and every non-matching public state
remain unchanged.
"""

from whitebox.versions import v645_public_farmers_carried_routes as _v645


_v629 = _v645._v629
_v623 = _v645._v623
_v545 = _v645._v545
_c06 = _v645._c06
_base_role_plan = _c06._role_plan


def _role_plan(obs, farm):
    roles = _base_role_plan(obs, farm)
    player = int((obs or {}).get("player", 0) or 0)
    if _v545._MODE.get(player) != "light" or not _v645._farmers_market(obs):
        return roles
    day = int((obs or {}).get("day", 0) or 0)
    tiles = farm.get("tiles", []) or []
    for position, role in tuple(roles.items()):
        kind, crop = role
        if kind != "CROP" or day <= _c06.CROPS[crop]["last_plant"]:
            continue
        x, y = position
        tile = tiles[y][x]
        if not (
            tile is None
            or (isinstance(tile, dict) and tile.get("kind") == "WEED")
        ):
            continue
        if day <= _c06.CROPS["WHEAT"]["last_plant"]:
            roles[position] = ("CROP", "WHEAT")
        elif day <= _c06.CROPS["CARROT"]["last_plant"]:
            roles[position] = ("CROP", "CARROT")
    return roles


_c06._role_plan = _role_plan


def whitebox_v646_public_farmers_late_rotation(obs):
    return _v629.whitebox_v629_public_shop_adaptive_hands(obs)
