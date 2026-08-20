# Kaggriculture

Agent for the Kaggle **Kaggriculture** simulation competition (2-player,
720 turns, most money wins). Submission deadline 2026-09-30.

**New session? Read `HANDOFF.md` first** — section 0 carries the current state
and the three rules that override everything else.

**[`MODEL.md`](MODEL.md)** is the mathematical model: the engine's price curve
and its exact reproduction, the marginal value of a sale, opponent state
estimation, asset ENPV, and the global resource allocation. It renders on
GitHub. Every coefficient in it names its calibration data, and section 11
lists the refuted branches so they are not re-derived.

---

## What ships

`submission/main.py` — 155 KB, stdlib-only, entry `_submission_entry`.

It is the public `multi-route-farming-agent` ("kawa") 720-step tape, **unmodified**,
plus one appended layer of our own: `pbt/intervene.py`, which dumps 80% of held
stock three turns ahead of the opponent's predicted sale, on
MELON/MILK/STRAWBERRY/WOOL/FERTILIZER.

Rebuild it with:

```bash
/home/yilewang/kagg-env/bin/python -c "
import sys; sys.path.insert(0,'.')
from route.bake import bake
print(bake({'_PREEMPT_MIN_FUTURE_QUANTITY':0,'_PREEMPT_MAX_BATCH':30,
            'INTERVENE':1,'IV_DUMP_FRAC':0.8,'IV_LEAD':3,'IV_FERT':1}))"
```

## Results

### Ladder

| submission | what it is | score |
|---|---|---|
| 55600561 `v3` | kawa + our market layer | **2394** (37 games, 32-5, **86%**) |
| 55594505 | unmodified kawa | 2326 |
| 55597426 | unmodified kawa | 1970 |
| 55587826 | our own planner (all-crop GA) | 483 |

Both of the earlier user submissions were verified as unmodified kawa by
extracting their tape from replays and matching frame-for-frame.

### Local, paired margin (both seat orders per seed, summed)

Our build against the whole evaluation pool, 20 seeds:

| opponent | paired margin | paired wins |
|---|---|---|
| kawa (multi-route) | **+1,176** | 19/20 |
| frontier-the-soil-remembers-rain | +13,311 | 13/20 |
| v111 / V16-RC5 | +14,798 | 15/20 |
| breaking-the-tie-2883 | +17,284 | 15/20 |
| Kaito Fukami v25 | +27,512 | 20/20 |
| strong-barnyard-economist | +33,887 | 20/20 |
| pure-architecture-2600-elo | +39,589 | 20/20 |

kawa is in a class of its own — the next-hardest opponent is 11x further away.

### What each change was worth

| change | paired margin vs kawa |
|---|---|
| plain kawa | 0 (baseline) |
| `_PREEMPT_MIN_FUTURE_QUANTITY` 4→0, `_PREEMPT_MAX_BATCH` 12→30 | +464 |
| + market intervention, lead 1, dump 40% | +1,221 |
| + lead 3 and FERTILIZER | +1,428 |
| + dump 80% | **+1,611** |

Refinements tested and **rejected** (all measured, none shipped): exact
repayment/volume conservation, staged dumping, near-mirror gating, wheat
starvation squeeze, structural yield forecast, floor-price gate, sell-slot
reordering, and every attempt to touch the tape.

## Layout

```
submission/main.py      the file to submit
HANDOFF.md              full state, engine mechanics, measurement rules, pitfalls
opponents/              15 public agents, 10 loadable; 9 form the evaluation pool
replays/                downloaded ladder replays (git-ignored, ~30 MB each)

pbt/intervene.py        the market layer — the entire measured edge
pbt/extract_tape.py     replay -> 719-step tape -> runnable agent
pbt/agreement.py        is an opponent a replayable tape, or adaptive?
pbt/build_pool.py       ladder crawl: teamId -> submissions -> episodes
route/bake.py           assembles submission/main.py from base tape + layers
route/opponent.py       exact opponent-sales inference (validated to 0 error)
route/tournament.py     round-robin harness
route/batch.py          fixed-matchup batch scorer

route/agent.py|router.py|geom.py    our own planner — see "self-built" below
pbt/{tapesel,tape_edit,recover,features,cluster,adaptive,adversary}.py
                        experiments, each with its measured verdict in HANDOFF
```

## The self-built planner

`route/` is a complete agent of our own: an offline-searched plan (tile roles,
crew size, purchase timing) executed through a daily routing solver
(angular-sweep partition + nearest-neighbour/2-opt tour). It solves movement
well — 31% of turns against kawa's 43% — but loses on economy.

Best measured: **-8,192 paired margin** against the reference pool after 124
generations, improved from -34,720. Still negative; it does not beat kawa.
Checkpoints in `route/checkpoints/`.

It is kept because it is the only line that does not depend on anyone else's
tape, and because the ladder offers no better tape to copy — every strong player
is either running kawa's public tape already or is adaptive and cannot be
extracted (`pbt/agreement.py` measures which).

## Reproducing anything

```bash
kaggle competitions submissions kaggriculture
kaggle competitions episodes <SUBMISSION_ID>
kaggle competitions replay <EPISODE_ID> -p replays/
python -m pbt.extract_tape replays/<file>.json <seat> out.py
python -m route.tournament --workers 26 --include-tuned
```

Real seed is at `info.seed` in the replay, so any ladder game reproduces
locally. **Actions live at `steps[1:]`** — `steps[0]` is the initial state and
carries no action, which is why tapes are 719 long.
