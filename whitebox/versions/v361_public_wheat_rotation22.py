"""V361: reserve twenty-two crop slots for repeatable wheat rotation."""
from whitebox.versions import v350_public_conditional_weed as _v350
_c06 = _v350._c06
_c06.CROP_MIX = {
    "NW": {"MELON": 10, "WHEAT": 6, "CARROT": 2},
    "NE": {"WHEAT": 8, "CARROT": 1},
    "SW": {"WHEAT": 8, "CARROT": 1},
    "SE": {"WHEAT": 8, "CARROT": 2},
}
def whitebox_v361_public_wheat_rotation22(obs): return _c06.agent(obs)
