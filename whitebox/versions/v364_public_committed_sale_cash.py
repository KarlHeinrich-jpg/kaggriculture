"""V364: release exact sale cash only to committed seed and crew work.

V363 exposed full sale proceeds to every preceding capital choice and changed
the first divergence from planned seed into extra feed inventory.  This layer
keeps the evidence-backed conservative buffer for animals, feed and land, then
uses the engine's exact cash credit only for visible missing seeds and the crew
that services those already named crop roles.
"""

from whitebox.versions import v361_public_wheat_rotation22 as _v361


_c06 = _v361._c06
_c06.COMMITTED_WORK_SALE_CASH_FACTOR = 1.0


def whitebox_v364_public_committed_sale_cash(obs):
    return _c06.agent(obs)
