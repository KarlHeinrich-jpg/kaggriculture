"""V363: value same-turn sale cash exactly as the public engine does.

The engine credits every successful SELL unit at its quoted market price.  The
base C06 planner discounted that cash by 15 percent while constructing later
orders in the same queue, so it could reject purchases that the emitted sale
fully funds.  This version changes only that internal feasibility ledger; sale
quantities, prices and all field decisions remain unchanged.
"""

from whitebox.versions import v361_public_wheat_rotation22 as _v361


_c06 = _v361._c06
_c06.SALE_CASH_FACTOR = 1.0


def whitebox_v363_public_exact_sale_cash(obs):
    return _c06.agent(obs)
