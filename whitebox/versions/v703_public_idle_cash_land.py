"""V703: buy already-affordable land during an otherwise idle market turn.

V684 can hold more cash than the next public land price while its market queue
is empty because the base capital rule also requires a fixed cash reserve.
When current cash already pays the full land price, the owned wheat stock
covers the existing herd for the engine-defined feed horizon, no animal is at
risk, and the ordinary queue has no competing order, spend that idle cash on
the next legal quadrant.  The rule never exceeds three total quadrants and
uses no future sale, opponent identity, seed, seat, or action tape.
"""

from whitebox.versions import v684_public_recertified_nonfarmers_light as _v684


_v678 = _v684._v678
_v659 = _v678._v675._v659
_c06 = _v659._c06
_base_market_actions = _c06._market_actions


def _market_actions(obs, config, farm, private, roles, field):
    orders = [
        list(order)
        for order in _base_market_actions(
            obs, config, farm, private, roles, field
        )
    ]
    if orders or field.get("liquidation", False):
        return orders

    day = int((obs or {}).get("day", 0) or 0)
    left = _c06.TOTAL_DAYS - day
    total_quadrants = len(farm.get("unlocked_quadrants", []) or ["NW"])
    extra_land = max(0, total_quadrants - 1)
    if (
        total_quadrants >= 3
        or extra_land >= _c06.MAX_EXTRA_LAND
        or day < int(_c06.LAND_OPEN_DAYS[extra_land])
        or left < 12
    ):
        return orders

    summary = _c06._survey(farm, private, roles, day)
    feed_cover = int(summary["animals"]) * int(_c06.FEED_STOCK_DAYS)
    land_cost = int(_c06.LAND_PRICES[extra_land])
    max_orders = int(
        _c06._cfg(config, "maxMarketOrdersPerTurn", _c06.MAX_MARKET_ORDERS)
    )
    if (
        float(farm.get("money", 0) or 0) >= land_cost
        and int(summary["wheat_stock"]) >= feed_cover
        and int(summary["at_risk_animals"]) == 0
        and len(orders) < max_orders
    ):
        orders.append(["BUY_LAND"])
    return orders


_c06._market_actions = _market_actions


def whitebox_v703_public_idle_cash_land(obs):
    return _v684.whitebox_v684_public_recertified_nonfarmers_light(obs)
