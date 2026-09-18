"""V406: rotate a completed one-shot melon role into strawberry.

The certificate contains only our own publicly observed tile history. A base
MELON role must first be witnessed as a live melon plant and later become
empty or weeded. If strawberry has stronger current public town absorption and
is still legal to plant, that role becomes STRAWBERRY for the rest of the
episode. No opponent action, identity, replay date, or coordinate is retained.
"""

from whitebox.versions import v361_public_wheat_rotation22 as _v361


_c06 = _v361._c06
_base_role_plan = _c06._role_plan
_ROTATION_CERTIFICATES = {}
ROTATION_CAP = 10


def _certificate(obs):
    player = int((obs or {}).get("player", 0) or 0)
    step = int((obs or {}).get("step", 0) or 0)
    current = _ROTATION_CERTIFICATES.get(player)
    if current is None or step < int(current.get("step", -1)):
        current = {"step": step, "seen_melons": set(), "rotated": set()}
    current["step"] = step
    _ROTATION_CERTIFICATES[player] = current
    return current


def _role_plan(obs, farm):
    roles = _base_role_plan(obs, farm)
    day = int((obs or {}).get("day", 0) or 0)
    tiles = farm.get("tiles", []) or []
    certificate = _certificate(obs)
    seen_melons = certificate["seen_melons"]
    rotated = certificate["rotated"]

    for position, role in roles.items():
        if role != ("CROP", "MELON"):
            continue
        x, y = position
        tile = tiles[y][x]
        if (
            isinstance(tile, dict)
            and tile.get("kind") == "PLANT"
            and tile.get("crop") == "MELON"
        ):
            seen_melons.add(position)

    strawberry_open = day <= _c06.CROPS["STRAWBERRY"]["last_plant"]
    demand_favors_rotation = (
        _c06._town_demand_per_day(obs, "STRAWBERRY")
        > _c06._town_demand_per_day(obs, "MELON")
    )
    if strawberry_open and demand_favors_rotation:
        for position in sorted(seen_melons, key=lambda value: (value[1], value[0])):
            if len(rotated) >= ROTATION_CAP:
                break
            x, y = position
            tile = tiles[y][x]
            if tile is None or (
                isinstance(tile, dict) and tile.get("kind") == "WEED"
            ):
                rotated.add(position)

    for position in rotated:
        if roles.get(position) == ("CROP", "MELON"):
            roles[position] = ("CROP", "STRAWBERRY")
    return roles


_c06._role_plan = _role_plan


def whitebox_v406_public_one_shot_melon_rotation(obs):
    return _c06.agent(obs)
