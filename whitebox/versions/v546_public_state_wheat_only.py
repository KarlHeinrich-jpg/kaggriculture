"""V546: retain the public wheat signal while rejecting the light footprint."""

from whitebox.versions import v545_public_state_route_selector as _v545


_base_update_mode = _v545._update_mode


def _update_mode(obs):
    mode = _base_update_mode(obs)
    if mode == "light":
        player = int((obs or {}).get("player", 0) or 0)
        _v545._MODE[player] = "default"
        return "default"
    return mode


_v545._update_mode = _update_mode


def whitebox_v546_public_state_wheat_only(obs):
    return _v545.whitebox_v545_public_state_route_selector(obs)
