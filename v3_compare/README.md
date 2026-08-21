# v3: tape vs decision tree, side by side

Two files that are the same agent. One stores its 720-turn route as ten arrays
and indexes them; the other stores the identical route as a perfect-fit CART and
walks it. **Same moves, same money, to the dollar.** Built and verified
2026-08-21.

| file | bytes | what it is |
|---|---|---|
| `v3_tape.py` | 155,305 | the submitted v3, unmodified |
| `v3_tree.py` | 196,410 | `v3_tape.py` + one appended block |
| `tree_block.py` | 41,105 | that block alone, as shipped |
| `tree_block_readable.py` | 3,190 | the same block with the blob folded — **read this one** |

## The diff is an append and nothing else

The first 155,305 bytes of `v3_tree.py` are byte-identical to `v3_tape.py`:

```bash
head -c 155305 v3_tree.py | cmp - v3_tape.py     # silent = identical
```

Nothing in the original was edited. Not the guards, not the market layer, not
the tables — the ten arrays are still there and the tree still reads its actions
out of them. That is deliberate: baking a fresh file from `route/bake.py` would
have regenerated every layer from today's generators, and v3's market layer came
from an older `pbt/intervene.py` (no `_IV_STRUCT`, no `_IV_MIN_PRICE`, no
`_IV_STAGED`), so a rebuild would have silently swapped it. `pbt/treeify.py`
copies the file and appends.

## What changed, in one line

```python
actions = _kawa_actions(obs)          # was: a list.  now: a _TrRoute proxy
```

That is the whole substitution. The eleven guards below it are untouched:

```python
step   = min(max(0, int(_get(obs, "step", 0) or 0)), len(actions) - 1)
action = _weed_repair_action(obs, _copy_action(actions[step]), step)
action = _v17_feed_guard(obs, action, step)
action = _v17_room_evac(obs, action, step)
action = _repay_shift(obs, action, step)
action = _rank_sell_slots(obs, action, None)
action = _preempt_shift(obs, action, step)
action = _v17_r5_counter(obs, action, step)
action = _v17_md_counter(obs, action, step)
action = _v17_room_guard(obs, action, step)
action = _terminal_liquidation(obs, action, step)
return _align_hands(action, obs)
```

`len(actions)` and `actions[step]` are the only two operations performed on it,
so an object with `__len__` and `__getitem__` drops straight in.

## Why a proxy and not a lookup function

Three places read the table, and replacing only the obvious one leaves the other
two planning against the route the tape *used to* have:

| site | index | who depends on it |
|---|---|---|
| `agent` | `step` | the base action |
| `_trace_actor_action` | `step` (current) | `_weed_repair_action` replays a deferred op for up to `_WEED_REPLAY_STEPS` = 8 steps |
| `_future_sells` | `step + 1` | `_preempt_shift` borrows tomorrow's premium sells into today and books the amount in `_SHIFT_STATE["due"]` for `_repay_shift` to subtract next turn |

A proxy makes all three resolve through the same tree, so an edit is coherent
everywhere *by construction* rather than by remembering to patch three places.

## Structure

Leaves hold `(table index, step)`, not actions — the ~3,000 distinct actions stay
in the ten arrays already in the file and are not duplicated. The blob is only
the branch structure, zlib+base64, decoded once on first use (a Kaggle agent has
an init budget, so the CART is fitted at build time, never at import).

Two of the ten tables are duplicates in v3 — `_ACTIONS_6C12S_4Q_FIRST_YARN` and
`_LEGACY_ACTIONS_6C12S_4Q_FIRST_YARN` carry identical blobs, likewise the
SECOND_YARN pair — so leaves merge more heavily here than in kawa.

## Evidence

Two drivers, on purpose. `planner.simulate` is ours and is fast enough for a
336-episode sweep; `kaggle_environments` is what actually scores the
competition, so only it can answer "is this submittable".

| check | tool | result |
|---|---|---|
| all route keys | — | **7,190/7,190** exact |
| pool games, per-seed final banks | `v3_bench.py` | **120/120** identical |
| self-play `tree_vs_base`, paired margin | `v3_bench.py` | **+0**, 0/16 nonzero seeds |
| self-play `base_vs_base` (identity control) | `v3_bench.py` | **+0**, 0/16 nonzero |
| real engine, by file path | `v3_submit_check.py` | **30/30** DONE/DONE, banks identical |
| episode wall time | `v3_submit_check.py` | 4.98s vs 4.97s, **+0.3%** |
| Kaggle entry point | `treeify.py --check` | `_treeroute_entry`, 1 required arg |

Self-play is scored by **paired margin** — both seat orders per seed, summed —
never win rate. An agent against a byte-identical copy of itself wins seat 0 only
15% of the time, so a win-rate reading of a mirror is noise wearing a number.

### The check that actually matters

Identical output has an innocent explanation: the appended block could be dead
code, and then every row above is vacuous. So the block was sabotaged on purpose
— one `_TR_EDITS` entry forcing PASS at step 30:

```
base 76,829 | tree 76,829 | tree+edit 55,293
```

The tree is in the execution path. Without this line the equivalence table proves
nothing.

## What this buys, and what it does not

**It is worth exactly zero points.** A perfect tree scores what the array scored;
shipping it alone adds risk and no reward. What it buys is a surface:

```python
_TR_EDITS[(legacy, label, step)] = action    # override one key, coherently
```

The tape was previously immutable (HANDOFF section 4). It no longer is — per key,
at all three read sites. But section 4's *measurement* still stands: edits are
mostly catastrophic. A single-step PASS at steps 0–20 costs between −6k and
−299k, and only 2,133 of the 7,190 keys are even reachable (29.7%; 4 of 10 tables
ever get selected). Steps beyond 100 are the untested region and the only place a
"soft" step is likely to exist.

Editability is a substrate, not a gain.

## Reproduce

```bash
python pbt/treeify.py submission/v3_base.py submission/v3_tree.py --check
python dynamic/tape/v3_bench.py            # sweep: keys, mirrors, pool identity
python dynamic/tape/v3_submit_check.py     # kaggle_environments, by file path
```

Equivalence is a property of a **build**, not of the generator. Rerun both after
regenerating; never trust a number in a comment.
