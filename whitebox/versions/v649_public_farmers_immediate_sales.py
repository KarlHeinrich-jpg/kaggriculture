"""V649: immediately sell banked outputs in the FARMERS_MARKET light state.

Current shed output is an exposed position on the shared public price curve.
For the FARMERS_MARKET light route, sell all already banked non-input output
at the current quote while retaining V646's wheat and fertilizer reserves.
Production, land, crew, and routing decisions are unchanged.
"""

from whitebox.versions import v646_public_farmers_late_rotation as _v646


_v645 = _v646._v645
_v545 = _v646._v545
_c06 = _v646._c06
_base_market_actions = _c06._market_actions
_OUTPUTS = tuple(
    item for item in _c06.PRODUCTS if item not in {"WHEAT", "FERTILIZER"}
)


def _market_actions(obs, config, farm, private, roles, field):
    orders = [list(order) for order in _base_market_actions(
        obs, config, farm, private, roles, field
    )]
    player = int((obs or {}).get("player", 0) or 0)
    if _v545._MODE.get(player) != "light" or not _v645._farmers_market(obs):
        return orders
    capacity = int(_c06._cfg(config, "shedCapacity", _c06.SHED_CAPACITY))
    shed, _inventories = _c06._post_field_storage(private, field, capacity)
    by_item = {
        order[1]: index
        for index, order in enumerate(orders)
        if len(order) >= 3 and order[0] == "SELL"
    }
    max_orders = int(_c06._cfg(
        config, "maxMarketOrdersPerTurn", _c06.MAX_MARKET_ORDERS
    ))
    for item in _OUTPUTS:
        quantity = max(0, int(shed.get(item, 0) or 0))
        if quantity <= 0:
            continue
        if item in by_item:
            orders[by_item[item]][2] = quantity
        elif len(orders) < max_orders:
            by_item[item] = len(orders)
            orders.append(["SELL", item, quantity])
    return orders[:max_orders]


_c06._market_actions = _market_actions


def whitebox_v649_public_farmers_immediate_sales(obs):
    return _v646.whitebox_v646_public_farmers_late_rotation(obs)
