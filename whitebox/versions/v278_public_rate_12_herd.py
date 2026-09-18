"""V278 diagnostic: public production frequency tilt at twelve percent."""
from whitebox.versions import v250_public_scenario_sale60 as _v250
_c06 = _v250._c06
_base_score = _c06._livestock_score
def _livestock_score(obs, animal, own_count, opponent_count):
    score = _base_score(obs, animal, own_count, opponent_count)
    interval = max(1, int(_c06.ANIMALS[animal].get("interval", 1)))
    return score * (1.0 + 0.12 * (2.0 / float(interval) - 1.0))
_c06._livestock_score = _livestock_score
def whitebox_v278_public_rate_12_herd(obs):
    return _c06.agent(obs)
