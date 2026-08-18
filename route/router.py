"""Daily route solver.

The measured gap to the reference agents is throughput, not strategy: they land
52% useful actions to our 25% because their route was solved offline instead of
re-derived greedily every turn. This module solves that routing problem.

Once per day every unit starts on a shed-access tile with a 24-turn budget, so
one day is an independent multi-vehicle routing problem:

    partition the day's tile-tasks across units (angular sweep, packed to each
    unit's turn budget)  ->  order each unit's tiles (nearest-neighbour + 2-opt
    on Manhattan distance)  ->  emit the exact turn-by-turn action list.

Movement is unrestricted -- LOCKED tiles are passable -- so travel cost is plain
Manhattan distance and no path search is needed.
"""
import math

from route.geom import SHED_SET, dist, steps_between

TURNS_PER_DAY = 24


class Task:
    """One tile's work for one day. `ops` are engine action lists, already in
    the order they must run on the tile (FERTILIZE -> WATER -> HARVEST, since
    WATER checks the fertilizer flag and HARVEST clears the yield)."""

    __slots__ = ("pos", "ops", "carry", "value")

    def __init__(self, pos, ops, carry=None, value=1.0):
        self.pos = pos
        self.ops = ops
        # {item: n} that must be in hand before the ops run (feed wheat,
        # fertilizer, an animal to PLACE). Collected in one PICKUP per item.
        self.carry = carry or {}
        self.value = value

    @property
    def n_ops(self):
        return len(self.ops)

    def __repr__(self):
        return f"Task({self.pos}, {[o[0] for o in self.ops]}, v={self.value:.0f})"


class Unit:
    """A farmer/hand slot for one day. `start_hour` is when the unit first gets
    to act -- hands hired at hour h are appended by the market phase of that
    turn and so are first controllable at h+1."""

    __slots__ = ("idx", "start", "start_hour")

    def __init__(self, idx, start, start_hour=0):
        self.idx = idx
        self.start = start
        self.start_hour = start_hour

    @property
    def budget(self):
        return max(0, TURNS_PER_DAY - self.start_hour)


# ---------------------------------------------------------------- tour solving

def tour_length(start, order):
    if not order:
        return 0
    total = dist(start, order[0])
    for a, b in zip(order, order[1:]):
        total += dist(a, b)
    return total


def nearest_neighbour(start, tiles):
    remaining = list(tiles)
    order = []
    cur = start
    while remaining:
        nxt = min(remaining, key=lambda t: (dist(cur, t), t))
        remaining.remove(nxt)
        order.append(nxt)
        cur = nxt
    return order


def two_opt(start, order, max_passes=6):
    """2-opt on an open path with a fixed start. Reversing order[i:j+1] only
    changes the two edges entering and leaving that span, so each candidate is
    an O(1) delta; the tail edge is free because the path may end anywhere."""
    if len(order) < 3:
        return order
    order = list(order)
    n = len(order)
    for _ in range(max_passes):
        improved = False
        for i in range(n - 1):
            prev = order[i - 1] if i > 0 else start
            for j in range(i + 1, n):
                a, b = order[i], order[j]
                before = dist(prev, a)
                after = dist(prev, b)
                if j + 1 < n:
                    nxt = order[j + 1]
                    before += dist(b, nxt)
                    after += dist(a, nxt)
                if after < before:
                    order[i:j + 1] = reversed(order[i:j + 1])
                    improved = True
        if not improved:
            break
    return order


def solve_tour(start, tiles):
    return two_opt(start, nearest_neighbour(start, tiles))


# ------------------------------------------------------------------ partition

def _sweep_key(pos, centre):
    """Angle around the shed, then distance. Sorting by this walks the board in
    a spiral, so any contiguous slice of the list is a compact wedge -- which is
    what makes the greedy packing below produce sane, non-overlapping zones."""
    ang = math.atan2(pos[1] - centre[1], pos[0] - centre[0])
    return (ang, dist(pos, (round(centre[0]), round(centre[1]))))


def partition(tasks, units, centre=(4.5, 4.5)):
    """Assign tasks to units by angular sweep, packing each unit to its turn
    budget. Returns (assignment, leftover)."""
    ordered = sorted(tasks, key=lambda t: _sweep_key(t.pos, centre))
    assignment = {u.idx: [] for u in units}
    leftover = []
    if not units:
        return assignment, ordered

    ui = 0
    cur_cost = 0
    cur_pos = None
    for task in ordered:
        while ui < len(units):
            u = units[ui]
            overhead = _carry_turns(assignment[u.idx] + [task])
            step = dist(cur_pos, task.pos) if cur_pos is not None else dist(u.start, task.pos)
            projected = cur_cost + step + task.n_ops + overhead
            if projected <= u.budget or not assignment[u.idx]:
                assignment[u.idx].append(task)
                cur_cost += step + task.n_ops
                cur_pos = task.pos
                break
            ui += 1
            cur_cost = 0
            cur_pos = None
        else:
            leftover.append(task)
    return assignment, leftover


def _carry_turns(tasks):
    """PICKUP turns needed before setting off: one per distinct carried item.
    PICKUP takes a count, so n wheat is still a single turn."""
    items = set()
    for t in tasks:
        items.update(k for k, v in t.carry.items() if v)
    return len(items)


def _carry_totals(tasks):
    totals = {}
    for t in tasks:
        for k, v in t.carry.items():
            if v:
                totals[k] = totals.get(k, 0) + v
    return totals


# ----------------------------------------------------------------------- emit

def build_tour(unit, tasks, shed_stock=None):
    """Turn one unit's task set into a *tour*: the pickups to make at the shed
    and the ordered (tile, ops) stops to work through.

    A tour is emitted rather than a baked move tape because a hand's real spawn
    tile is not knowable when the day is planned -- `_spawn_hand` picks the
    least-occupied shed-access tile, which depends on where the farmer happens
    to be standing. Following a tour re-derives each move from the unit's actual
    position, so a wrong guess costs a step, never a desync.

    Drops the lowest-value tasks first if the tour does not fit the budget, so
    an over-subscribed unit loses its cheapest work rather than whatever
    happened to fall at the end of the route.
    """
    tasks = list(tasks)
    budget = unit.budget
    if budget <= 0 or not tasks:
        return {"carry": {}, "stops": [], "tasks": []}

    while tasks:
        order = solve_tour(unit.start, [t.pos for t in tasks])
        cost = (_carry_turns(tasks) + tour_length(unit.start, order)
                + sum(t.n_ops for t in tasks))
        if cost <= budget:
            break
        worst = min(tasks, key=lambda t: (t.value, -t.n_ops))
        tasks.remove(worst)
    if not tasks:
        return {"carry": {}, "stops": [], "tasks": []}

    carry = _carry_totals(tasks)
    if shed_stock is not None:
        for item in list(carry):
            carry[item] = min(carry[item], int(shed_stock.get(item, 0)))
            if carry[item] <= 0:
                del carry[item]
            else:
                shed_stock[item] = shed_stock.get(item, 0) - carry[item]

    by_pos = {}
    for t in tasks:
        by_pos.setdefault(t.pos, []).append(t)
    stops = []
    for tile in order:
        ops = []
        for t in by_pos.get(tile, []):
            ops.extend(list(op) for op in t.ops)
        stops.append((tile, ops))
    return {"carry": carry, "stops": stops, "tasks": tasks}


def plan_day(units, tasks, shed_stock=None):
    """Full day plan: {unit_idx: tour}, plus the tasks nobody was given."""
    assignment, leftover = partition(tasks, units)
    tours = {}
    scheduled = set()
    for u in units:
        tour = build_tour(u, assignment[u.idx], shed_stock)
        tours[u.idx] = tour
        for t in tour["tasks"]:
            scheduled.add(id(t))
    undone = [t for t in tasks if id(t) not in scheduled]
    return tours, undone
