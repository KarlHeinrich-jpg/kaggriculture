"""V416: rotate completed melon roles only under cow-backed service capacity.

The one-shot crop rotation is admitted only when the current visible own herd
contains strictly more cows than sheep. Milk has a linear oversupply penalty,
while wool has a quadratic penalty in the public market curve; the guard keeps
extra perennial crop service from disturbing a sheep-dominant sale schedule.
All other states retain V361's role map exactly.
"""

from whitebox.versions import v406_public_one_shot_melon_rotation as _v406


_c06 = _v406._c06
_base_role_plan = _v406._base_role_plan
_ROTATION_CERTIFICATES = {}


def _own_animals(farm):
    counts = {animal: 0 for animal in _c06.ANIMALS}
    for row in farm.get("tiles", []) or []:
        for tile in row or ():
            if isinstance(tile, dict) and tile.get("animal") in counts:
                counts[tile["animal"]] += 1
    return counts


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
    certificate = _certificate(obs)
    seen_melons = certificate["seen_melons"]
    rotated = certificate["rotated"]
    tiles = farm.get("tiles", []) or []
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

    animals = _own_animals(farm)
    day = int((obs or {}).get("day", 0) or 0)
    rotation_open = (
        animals["COW"] > animals["SHEEP"]
        and day <= _c06.CROPS["STRAWBERRY"]["last_plant"]
        and _c06._town_demand_per_day(obs, "STRAWBERRY")
        > _c06._town_demand_per_day(obs, "MELON")
    )
    if rotation_open:
        for position in sorted(seen_melons, key=lambda value: (value[1], value[0])):
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


def whitebox_v416_public_cow_backed_melon_rotation(obs):
    return _c06.agent(obs)
