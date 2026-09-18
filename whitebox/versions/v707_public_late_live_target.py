"""V707: preserve late-day live targets against deadline thrashing.

Matcher diagnostics show that late public workers often become too far from
every current job before the job's same-day deadline.  A small current-state
continuity credit is enabled only during the mature service window.  The
existing live target certificate is still revalidated each observation; it is
not an action tape or future route.
"""

from whitebox.versions import v684_public_recertified_nonfarmers_light as _v684


_v678 = _v684._v678
_v659 = _v678._v675._v659
_v649 = _v659._v649
_v646 = _v649._v646
_v645 = _v646._v645
_v623 = _v645._v623
_v545 = _v623._v545
_v452 = _v545._v454._v452
_c06 = _v545._c06
_base_unit_actions = _v452._base_unit_actions


def _unit_actions(obs, config, farm, private, roles):
    day = int((obs or {}).get("day", 0) or 0)
    previous = _c06.TARGET_STICKINESS_BONUS
    enabled = 10 <= day <= 27
    _c06.TARGET_STICKINESS_BONUS = 16.0 if enabled else previous
    try:
        return _base_unit_actions(obs, config, farm, private, roles)
    finally:
        _c06.TARGET_STICKINESS_BONUS = previous


_v452._v448._unit_actions = _unit_actions


def whitebox_v707_public_late_live_target(obs):
    return _v684.whitebox_v684_public_recertified_nonfarmers_light(obs)
