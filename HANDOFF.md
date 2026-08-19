# Kaggriculture — handoff

**Goal:** gold in the Kaggle *Kaggriculture* simulation competition (2-player,
720 turns, most money wins). Submission deadline 2026-09-30.

---

## 0. READ THIS FIRST — state as of 2026-08-19 midday

**Ship this:** `submission/main.py` (162,800 bytes, stdlib-only, entry
`_submission_entry`). Live as Kaggle submission **55614625**. It is the public
`multi-route-farming-agent` ("kawa") tape plus three appended layers:
`pbt/intervene.py` (market intervention), `IV_STRUCT` (structural sale forecast),
and a one-bucket correction to kawa's tape-selection rule.

Rebuild:
```bash
cd /home/yilewang/kaggriculture && /home/yilewang/kagg-env/bin/python -c "
import sys; sys.path.insert(0,'.')
from route.bake import bake
print(bake({'_PREEMPT_MIN_FUTURE_QUANTITY':0,'_PREEMPT_MAX_BATCH':30,
            'INTERVENE':1,'IV_DUMP_FRAC':0.7,'IV_LEAD':3,'IV_FERT':1,
            'IV_STRUCT':1,'IV_MIN_PRICE':0.20,
            'TAPE_MAP':['6c12s_4q_second_yarn','6c12s_4q_second_yarn',
                        '6c8s_3q','10c4s_3q','8c6s_3q']}))"
```

### Submissions (Kaggle keeps only the latest 2 active)

| id | what | real-engine gain | ladder |
|---|---|---|---|
| **55614625** | + bucket-0 tape swap | **+858** vs 55612771 | active, converging |
| **55612771** | + IV_STRUCT, dump .70, price gate .20 | +670 vs 55600561 | active, 24/27 (89%) |
| 55600561 | kawa + intervene (2026-08-18) | — | inactive, peaked 2630.9, 65/84 (77%) |

### Three rules that override everything else

1. **Never score same-tape matchups by win rate.** An agent against a
   byte-identical copy of itself wins seat 0 only **15%** of the time, on a mean
   margin of **-$66**. Use **paired margin**: play both seat orders per seed and
   sum them. A true mirror then scores exactly 0. Section 5.
2. **The tape cannot be edited** — not farm actions, not hires, not even day 0's
   market line. Every probe collapsed the run. It can only be replaced wholesale,
   or *selected* differently (section 16). Market orders ARE editable; that is
   what the whole intervention layer is.
3. **Validate a submission by file path** (`env.run([path, opponent])`), never by
   import. Kaggle resolves a file agent with `get_last_callable`, which walks the
   namespace in **insertion order** — rebinding `agent` in an appended layer does
   *not* move it, so the last *newly defined* callable wins. Section 5.

### Rule 4, learned 2026-08-19 and now the most expensive one

**For a concentrated effect, sample size means FIRING games, not games played.**
The bucket-0 tape swap changes behaviour in only ~13% of games. Its first
real-engine gate ran 180 paired games — comfortably past section 5's "≥100
games" bar — but only ~28 of them fired, and it returned **-18** for something
worth **+858** at 630 paired. Nothing was broken: the simulator reproduces that
same -18 on that same sample. Always report how often a change actually fires
and its CONDITIONAL distribution, not just the mean.

Corollary: two "independent replications" that share an opponent set are not
independent. +1,889 and +1,966 on disjoint seeds looked conclusive and were both
drawing the same region; real independence came from changing distribution
entirely (the 80 real ladder traces).

### What was actually worth anything

| change | measured on | gain |
|---|---|---|
| ~10 generations of constant search, PBT, tape-selection search | — | **~0** |
| market intervention (lead 3, dump 80%, +FERTILIZER) | vs plain kawa | +1,611 |
| IV_STRUCT + dump .70 + price gate .20 | real engine | **+670** |
| bucket-0 tape swap | real engine | **+858** |
| ...the same, across our 80 real ladder games | ladder traces | +429, record 62/80 → 66/80 |

### Corrections to earlier sections of this document

- **Section 0's old "12 vs 14 hand slots" gap is NOT our deficit.** Measured
  from 23 replays (`planner/analyze_top.py`): we run 277 hires, 12 hands, 2,858
  useful ops — at or above every ladder leader, and the most ops of anyone. Only
  ReCurSiON runs 14 hands. The gap is price realisation, not labour.
- **Section 11's "tape-selection mapping already searched, default wins" is
  wrong for bucket 0.** Section 16.
- **Section 12's "IV_STRUCT is ambiguous" was under-sampling.** It is +420 at
  n=1,440 paired (t=16.3), and shipped.
- **Section 14's "the market layer is at a local optimum" is now true and
  proven** — but it was true of the *parameters*, not of structural changes.
  Section 17.

---

## 1. Environment

| what | where |
|---|---|
| project root | `/home/yilewang/kaggriculture` |
| python | `/home/yilewang/kagg-env/bin/python` (venv, py3.14) |
| engine source (READ IT) | `/home/yilewang/kagg-env/lib/python3.14/site-packages/kaggle_environments/envs/kaggriculture/kaggriculture.py` |
| Kaggle CLI | `/home/yilewang/kagg-env/bin/kaggle`, token at `~/.kaggle/access_token` |

Machine: **26 physical cores** (52 logical), 187 GB RAM. GPUs unused — the
workload is single-threaded CPU-bound Python. **Always size pools to 26**;
48 workers on 26 cores took 6+ minutes to not finish what 26 do in 30s.

Rebuild the submission: see section 0 (the parameters changed 2026-08-19).

## 2. File map

```
STRATEGY.md                   game economics derived from engine source (still valid)
submission/main.py            THE FILE TO SUBMIT
opponents/                    6 loadable public reference agents + extractor
replays/                      downloaded ladder replays (~30MB each)

pbt/intervene.py              the market-intervention layer = the entire real edge
pbt/extract_tape.py           replay -> 719-step tape -> transplant into kawa
route/bake.py                 assembles submission/main.py (base tape + layers)
route/opponent.py             EXACT opponent-sales inference (used by the agent)
route/tournament.py           round-robin harness
route/batch.py                fixed-matchup batch scorer

route/geom.py|router.py|agent.py   own-plan architecture — still far behind, section 13
pbt/tapesel.py                tape-selection rule — bucket 0 IS mis-assigned, section 16

planner/simulate.py           FAST pure-Python engine port, ~1,200 steps/s (~9x env.step)
planner/tests/                test_sim_fidelity (56 replays) + test_agent_fidelity (live play)
planner/intervene_sweep.py    market-layer sweeps, rounds 1-6, paired margin with CRN
planner/tape_sweep.py         per-bucket tape argmax  |  tape_map_test.py  fresh-seed check
planner/ladder_sweep.py       tune against the 80 REAL ladder opponents, not the pool
planner/replay_counterfactual.py  "would the new agent have won the games we lost?"
planner/analyze_top.py        realised per-unit prices from replays, us vs the leaders
planner/decompile.py|spec_extract.py  tape -> explicit schedule spec, and the gap to it
planner/day_pipeline.py       gated submission (real-engine + file-path gates)
pbt/tape_edit.py              day-0 market editor (proved the tape is not editable)
pbt/features.py|cluster.py    6-dim opponent features + K-Means (no signal found)
pbt/adaptive.py|adversary.py  per-family counter params (tied with plain best)
pbt/pool.py|variants.py|train.py   population-based training (random walk, section 5)
agents/                       every baked variant from every experiment
```

## 3. Engine mechanics that matter

All verified against source, not the write-up.

- **Market-limited, not production-limited.** Price = f(inventory) around a
  10,000 baseline, per-product curves. MELON and WOOL are **quadratic** above
  baseline (crash hardest), MILK and STRAWBERRY linear, EGG/WHEAT log (never
  really crash). Selling at the $1 floor does **not** add to market inventory.
- **Hands are cleared every night** and must be re-hired daily. Cost is
  `fib(hires_today)` — so hiring *before* the tape's own hires reprices them
  (4 hires first moves the tape's 5 from $7 to $81, and it goes crewless).
- **A crop must be watered the day it is planted.** `_new_plant` starts at
  `consecutive_unwatered = 1`; unwatered at the nightly refresh it is a weed by
  morning. PLANT and WATER must ride in the same tile visit.
- **CARE banks a multiplier** consumed on the next fed production day: goose
  1→2 eggs/day, cow 1→3 milk/2 days, sheep 1→4 wool/3 days. Feed and care every
  animal every day.
- **Animals produce fertilizer unconditionally**, fed or not. Nobody in town
  consumes it, so its price only falls — but it must still be sold, because the
  shed holds only 100 items and hoarding it freezes all commerce (measured:
  bank $62).
- **Atomic PLANT validation:** if PLANT requests for one crop in a turn exceed
  seeds held, *all* of them are dropped.
- **`max_lifespan_step` is an absolute step index, not a duration.** MELON
  planted day 0 gets 312 = decay starts **day 13**; it first yields **day 10**.
  Reading it as "312 steps of locked capital" is wrong and has misled analyses.
- **Within a step the engine runs `_process_market` before `_town_consume`.** A
  sale placed on a step the town drains enters an undrained market; the same
  sale one step later enters after the tick lifted the price. This is what the
  front-run/dump timing exploits.

## 4. The tape is immutable

Day 0 is the most isolated possible edit — a market line that moves no unit.
Paired margins after editing it:

| day-0 change | vs kawa | vs v111 | overall |
|---|---|---|---|
| none (baseline) | +1,579 | +16,708 | **+12,101** |
| feed 6 → 14 | +1,579 | +16,708 | +12,101 (**no effect** — no cash to fill it) |
| melon 12 → 6 | -11,211 | -6,213 | -7,467 |
| hire 4 + feed 14 | -63,945 | -50,846 | -54,541 |
| 1 COW / 4 SHEEP | -111,355 | -106,791 | **-107,714** |
| v111's whole day-0 line | -99,442 | -158,985 | **-138,558** |

Every downstream PLACE/PLANT assumes exactly the shed the tape bought. Grafting
another agent's opening onto this tape destroys it — its parameters only work
with its own 720-step continuation.

The same rigidity killed the day-1 fix. **All five tapes leave day 1 empty** —
0 hand slots, 0 actions, 0 HIRE, so the farm runs that day on the farmer alone
despite four hires costing $7 against $23 on hand. Overlay results, 40 games vs
kawa each: baseline 62%, hire-only-day-1 62% (bodies idle — the tape has no work
for them), hire every day **0%**, hire + assign work **0-5%**. A tape `PASS` is a
hand *holding station*; moving it desynchronises the rest of its schedule.

## 5. Measurement rules paid for the hard way

- **Seat asymmetry decides same-tape games.** `_end_of_day` rolls player 0's
  weeds first and `_process_market` resolves atomic HIRE/BUY_LAND in player
  order. Identical agent vs itself: seat 0 wins 6/40, mean margin -$66. Use
  paired margin; a byte-identical mirror then scores +0/+0, 0 wins, 0 losses.
- **A screening panel ranks against a *field*; only pairwise ranks against an
  *opponent*.** Three times a panel rated variants equal-or-better while the
  direct 100-game pairing showed one clearly worse (once 26% vs the config it
  had "beaten"). Screen broadly, decide pairwise.
- **A variant needs ≥100 games before its rank means anything.** Real
  differences here are 1-3 points; PBT scored variants on 12 games, so noise
  dominated, `v8 random noise` kept "winning", and 10 rounds of optimisation
  moved *backwards* (its champion then lost 22-78 to the earlier build).
- **Never attribute engine callbacks using objects from `obs`.**
  `kaggle_environments` structifies the observation, so `farm is obs["farms"][0]`
  inside a patched `_commit_unit` is always false and every commit lands on one
  player. Hook `_process_market(state, env)` — it gets the live state — and
  identify players by `private` identity.
- **A validation whose ground truth shares the broken step with the thing being
  validated proves nothing.** The opponent-sales inference first "validated" at
  near-zero error only because both sides were computing *combined* sales.
- **Cross-opponent comparisons are confounded.** Weeds roll only on empty tiles,
  so our tile count shifts the RNG before `rng.choice(SHOPS)` — the town's shop
  mix changes with the opponent, and "agent X scores more against Y than Z"
  supports no strategy claim.
- **Seed range is *not* a confound** (hypothesis tested and rejected). Ladder
  seeds are 32-bit; local work used 1-50. Over 40 of each: ours vs naru +11,374
  / +8,860; kawa vs v111 +13,862 / +12,232; ours vs kawa +1,428 / +1,611. The
  populations agree.
- **`pkill -f <pattern>` matches your own shell.** Use `pkill -f '[g]a_search'`,
  and beware that regex `.` matches `/` — `route.search` also matched the literal
  text `route/search.py` in a heredoc and killed the shell running it.

## 6. Opponent modelling — the one thing that paid

**Their sales are exactly recoverable, not guessed.** Within a step the engine
settles both players' orders and then the town's consumption, so

    inv[t+1] = inv[t] + my_sales[t] + their_sales[t] - town_take[t]

and every term but theirs is known: inventory is public, `town_take` is
computable from the unlocked shop list, and our own sales are what we issued.
Validated against engine ground truth over a full season: **zero error** on
STRAWBERRY, MELON, MILK, WOOL and EGG; total absolute error 9, confined to
WHEAT and FERTILIZER — the only products whose price reaches the $1 floor, where
the engine deliberately does not record the sale.

`pbt/intervene.py` measures each product's sale cadence from that inference and
pushes stock into the book ahead of the predicted sale. Tuning by paired margin:

| dump fraction (lead 3, +FERTILIZER) | vs kawa | mirror vs dump-40% |
|---|---|---|
| 40% | +1,221 | — |
| 60% | +1,358 | +297 (37/3) |
| **80%** | **+1,428** | **+467 (39/1)** |
| 100% | +1,209 | +29 (29/11) |

**Cost of running it:** observation must happen every turn (a running inventory
delta — a skipped turn breaks the arithmetic), but the *action* fires only
**9% of turns**, never before day 6 (needs ≥3 observations to fit a period),
concentrated in days 23-27. FERTILIZER alone is half of all firings.

**Ideas tested and rejected**, all from the published Market Relay write-up:
exact repayment / volume conservation (**-3 to -5 points**: our dump is an
aggressive extra sale, not a retimed one, so repaying hands the advantage back),
near-mirror gating (**-2**, it only reduces how often we act), and buying wheat
to squeeze an animal-heavy opponent (**2% win rate** — it spends cash the tape
needs downstream).

**We were exploitable and this is how it was found.** kawa does not model us —
its `_future_sells(obs, step)` reads its *own* tape. But `_clone_distance` does
read our farm, and ours is **0** against kawa (same tape), so its preemption is
fully armed; denying it is worth +$784, and unreachable, because raising the
distance past 6 needs 7 extra hands, 7 changed tiles, or a different tape.
Turning our own layer around — equipping opponents with it — produced three
predators that beat us, which is exactly how the dump fraction was found to be
set too low.

## 7. Reference agents and the ladder

`opponents/` holds 6 loadable public agents, all stdlib-only and audited.
Round-robin by paired margin (3,120 games): our build +9,016, kawa +8,103,
ref_B/ref_D +1,608, v111 -13,338, rank-your-agent -13,624, pipeline -43,120.

- **V16-RC5 is v111**, byte-identical (`sha256 f029fa0c…`, 18,946 bytes). Its
  notebook's "60/60" is against its own reconstructed baselines, never against
  kawa. Do not submit it.
- **The ladder meta has converged on 8c4s.** Three different opponents
  (Naru041104, Igor V, StopPlantingStartGameTheorying) open identically —
  4-5 HIRE, **1 COW / 4 SHEEP**, 5 wheat seed, 5 melon seed, 5-14 wheat product —
  and all reach 14 hands. We beat that family ~70% of paired seeds; the three
  losses that prompted this investigation were a bad draw, not a systematic
  defeat.

### Submissions

`publicScore` is a **skill rating, not money**, and converges with games played —
two copies of the same agent can sit hundreds of points apart on match history
alone.

| id | file | score | what it actually is |
|---|---|---|---|
| 55594505 | submission.py | **2326.3** | **unmodified kawa** |
| 55597426 | submission8.18.v2.py | 1898.5 | **unmodified kawa** |
| 55576209 | Kaggriculture.py | 1848.1 | earlier user agent |
| 55587826 | main.py | 482.6 | our GA route agent (all-crop) |

Only the latest 2 are active; 5/day. **Nothing built on 2026-08-18 has been
submitted** — every gain since is unvalidated on the ladder.

### Replays are the only honest feedback

```bash
/home/yilewang/kagg-env/bin/kaggle competitions submissions kaggriculture
/home/yilewang/kagg-env/bin/kaggle competitions episodes <SUBMISSION_ID>
/home/yilewang/kagg-env/bin/kaggle competitions replay <EPISODE_ID> -p replays/
/home/yilewang/kagg-env/bin/python -m pbt.extract_tape replays/<f>.json <seat> out.py
```

The real seed is at `info.seed` (32-bit) — any ladder game reproduces locally
with it. **Off-by-one:** replay `steps[0]` is the initial state and carries no
action; actions live at `steps[1:]`, which is why tapes are 719 long. Taking
`steps[0]` silently discards the opening turn.

Transplant fidelity is verified: replaying both extracted tapes at the episode's
real seed reproduced 107,064 v 135,395 against an actual 108,217 v 135,557.

## 8. Ground rules with the user

The competition permits reusing published notebooks; the user has confirmed they
want that. The shipped agent is a public tape plus our own market layer, and
that is understood and intended.

## 9. Next (superseded by sections 16-18; see section 0)

1. **Submit and get a real score.** Every local avenue is exhausted; the one
   number we do not have is what the intervention layer is worth on the ladder.
2. **The 12→14 hand-slot gap** is the only quantified structural deficit left,
   and it needs a different tape, not a tuned one. Extraction tooling is ready.
3. Do not re-run constant searches. They were run to exhaustion and measured
   zero once paired margin replaced win rate.

## 10. The sparring pool cannot be grown by copying the ladder

Six reference agents is a small pool and the overfitting risk is real. Copying
the top of the ladder does **not** fix it.

Access is not the problem — it is fully solved. `pbt/build_pool.py` walks
leaderboard `teamId` -> that team's submissions -> that submission's episodes,
and episode *metadata* already carries `team_id`, `submission_id`, `reward` and
seat index. **2,616 real ladder games were mapped without downloading a byte.**
Real head-to-head records for the top 20 (>=25 games):

| team | ladder score | W-L | win% |
|---|---|---|---|
| tetsuya | 3048 | 83-11 | **88%** |
| mandgeee | 2910 | 82-17 | 83% |
| VanKoha | 2888 | 58-13 | 82% |
| カワシギ | **3196** | 143-34 | 81% |
| 我的AI是GPT | 2899 | 69-21 | 77% |
| Utkarsh #2 | 2904 | 137-134 | 51% |

Note score and strength disagree: tetsuya wins 88% but ranks 3rd on rating.

**The blocker is that these agents are adaptive, not tape-replay.**
`pbt/agreement.py` compares three of an agent's own games step by step:

| team | farmer agreement | hands | market |
|---|---|---|---|
| tetsuya | 49.1% | 19.1% | 76.5% |
| カワシギ | 37.4% | 26.1% | 43.4% |
| 我的AI是GPT | 39.9% | 27.7% | 45.1% |
| mandgeee | 65.2% | 33.0% | 52.6% |

V16-RC5 reconstructed Nikita's submission at **99.91%** market agreement — that
one was a tape. The current top of the ladder is not. A single episode is a
*trace*, not a policy; replayed blindly it degrades badly (the extracted files
lost to our submission by up to -106,857, implausible for a 77%-win opponent).
They are quarantined in `pool_invalid/`.

**Always run `pbt/agreement.py` before trusting an extracted opponent.**

This also reframes the ladder: the "two schools" split by day-0 opening is only
an opening similarity. The continuations are adaptive and diverge.

## 11. The behavioural-cloning critique, tested point by point

A review argued the agent is brittle behavioural cloning and proposed
parameterising quantities, adding a fallback policy, auto-selecting sequences,
and training a network. Measured against this codebase:

| proposal | verdict |
|---|---|
| parameterise absolute quantities into formulas | **refuted** — day-0 quantity edits cost -107k to -138k (section 4) |
| auto-select the sequence from opponent features | **already present and already optimal** — `_kawa_route_label`; the whole 5-bucket mapping was searched, default wins (section 23 of the archive) |
| submission size near a 20MB limit | **wrong** — the file is 155KB |
| weed/exception recovery | **already present** — `_weed_repair_action`, `_align_hands` |
| market intervention | **already shipped** — and confirmed firing on the ladder |
| "zero generalisation, catastrophic drift" | **overstated but has a kernel** — see below |
| add a fallback policy for drifted states | **refuted, decisively** — see below |

### How much does the tape actually misfire?

`pbt/noop_probe.py` checks every tile op against the engine's own preconditions
before submission, over 96 games:

- wasted tile ops: **2.0% mean** (median 1.5%, worst 15.3%)
- wins 1.7% vs losses **3.5%**; correlation with margin **r = -0.32**

So drift is real and does correlate with losing, but at 2% it is not
"catastrophic", and it explains ~10% of variance.

### Why no fallback can exploit it

`pbt/recover.py` substitutes a valid op **on the tile the unit already occupies**
whenever the tape's op would no-op — never moving, so position stays in sync,
and only touching turns the tape was wasting anyway. It looks free. It is not:

| opponent | recovery off | recovery on |
|---|---|---|
| kawa | +1,168 | **-140,858** |
| v111 | +11,560 | -130,748 |
| 3000-socre | +11,845 | -150,193 |
| rank-your-agent | +13,504 | -127,066 |

Head to head: **0 paired wins in 32**.

Position invariance is not enough — the tape needs **state** invariance, and
there is no useful action that leaves state unchanged. HARVEST takes the yield
and, on a non-ongoing crop, *deletes the plant*; WATER sets `watered_today` and
changes yield accrual; CARE and COLLECT_FERTILIZER consume their flags.

**Even the wasted 2% of turns cannot be reclaimed.** This is the third
independent confirmation that the tape admits no edits, and the strongest.

## 12. Structural yield forecast and staged dumping — tested, both marginal

A review proposed replacing the dump trigger's observed-cadence predictor with
one that reads the opponent's *visible board* (animal `placed_day + first_yield
+ k*interval`, crop growth tables), and splitting the dump into tranches.

The first idea was a genuine gap: `route/opponent.py::forecast_supply` had been
built and validated but was never wired into the intervention trigger, which
used only the median observed sale interval. Both were implemented
(`IV_STRUCT`, `IV_STAGED`) and measured over 32 paired 32-bit seeds:

| variant | kawa | v111 | 3000 | rank | field mean | direct vs base |
|---|---|---|---|---|---|---|
| base | +1,149 | +15,354 | +10,942 | +17,478 | +11,231 | — |
| **struct** | **+1,469** | +15,556 | +11,754 | +17,175 | **+11,489** | -29 (8/32) |
| staged | +1,124 | +15,539 | +11,056 | +17,583 | +11,325 | **-386 (1/32)** |
| both | +1,417 | +15,629 | +11,769 | +17,250 | +11,516 | **-824 (2/32)** |

- **Staged dumping is refuted** (-386, 1 paired win in 32). Splitting the block
  gives the opponent a turn to sell into the gap.
- **The structural forecast is ambiguous**: +258 on the field mean (+320 against
  kawa specifically, a 28% relative gain on that matchup) but -29 and 8/32 in
  the direct mirror. A -29 mean on a ~$90k bank is 0.03% — the mirror is
  effectively a tie decided by noise.

Not shipped. The effect is inside the band where today's measurements have
repeatedly inverted, and a live submission was already performing on the ladder;
swapping it for a ~2% local signal is not justified. Kept behind `IV_STRUCT` for
a future run with a larger sample.

### Proposals refuted before implementation, from measurements already on file
micro-task/transaction restructuring of the trace, A* pathfinding with a
reservation table, worker-driven early shed clearing (discards measured at
**0** — the problem does not exist), per-shop-combination dedicated traces
(we cannot author tapes; the ladder top is adaptive), and offline GA
perturbation of the trace. All require editing the tape. See sections 4 and 11.

## 13. Self-built planner: restarted 2026-08-18 evening

The tape is a hard ceiling and the ladder offers no better one to copy — every
strong agent is either running kawa's public tape already (HKmgikao matches
`_ACTIONS_6C12S_4Q_FIRST_YARN` at 100% farmer / 94.9% market) or is adaptive and
cannot be extracted (VanKoha 56.7%, Galaxantic 50.1%, Eddy Despradel 64.5%,
Michael Timbs 59.0%, plus the four in section 10). So the only way past it is to
author a schedule, which means `route/`.

### Honest baseline, paired margin, 32-bit seeds

| genome | vs kawa | vs v111 | vs 3000 | own bank |
|---|---|---|---|---|
| best_route2 | **-101,239** | -83,164 | -109,886 | $68,655 |
| best_route6 | -104,431 | -106,251 | -111,069 | $62,879 |
| defaults | -137,842 | -144,963 | -149,372 | $48,571 |

We bank ~$68k where kawa banks ~$170k in the same game. **The gap is 2.5x**, not
the 1.3x an earlier note implied — that note compared numbers measured under
different matchups and was wrong.

### Three fitness defects fixed before restarting

The earlier searches optimised the wrong thing:

1. **`starter` was in the matchup set.** Pitfall #3 exactly — a champion tuned
   with it won every local game and scored 485 on the ladder. Removed.
2. **Fitness was mean *own bank*.** That rewards a genome for drawing a rich
   seed, not for beating the opponent. Now mean **paired margin**.
3. **One seat only, and seeds from 1..10^6.** Now every reference is played from
   **both seats on the same seed**, with seeds drawn from the ladder's own 32-bit
   range.

### Result: 124 generations, stopped 2026-08-18

| | gen 0 | best (gen 116) |
|---|---|---|
| paired margin vs the reference pool | -34,720 | **-8,192** |
| win rate | 0.00 | 0.17-0.33 (noisy) |

The gap closed **76%** and then flattened. Best genome: 5 COW / 6 SHEEP /
6 MELON / 24 STRAWBERRY / 4 WHEAT, `MAX_HANDS=16`, `HIRE_BUDGET_FRACTION=0.61`
— and the search turned **`FRONT_RUN` and `OPP_MODEL` off**, which is the
opposite of what helps the tape build.

Still negative: it does not beat kawa. The line is kept because it is the only
one that depends on nobody else's tape, but on this evidence a parameter search
over the existing planner will not close the remaining gap — the shortfall is in
the economy (revenue per unit and product mix), not the routing, which already
runs 31% movement against kawa's 43%.

**Do not edit `route/agent.py` or `route/router.py` while a search runs** —
workers re-exec the agent per episode and the fitness signal is silently
corrupted.

## 15. Evaluation pool, expanded 2026-08-18

Six agents was too small a pool. Twelve high-vote public notebooks were pulled
with `kaggle kernels pull`; after dedup **five were genuinely new and usable**,
taking the pool to **nine**. Measured against our build (paired margin, 20 seeds,
both seats):

| pool member | paired margin | paired wins |
|---|---|---|
| kawa (multi-route) | **+1,176** | 19/20 |
| frontier-the-soil-remembers-rain | +13,311 | **13/20** |
| v111 / V16-RC5 | +14,798 | 15/20 |
| breaking-the-tie-2883 | +17,284 | 15/20 |
| Kaito Fukami v25 | +27,512 | 20/20 |
| strong-barnyard-economist | +33,887 | 20/20 |
| pure-architecture-2600-elo | +39,589 | 20/20 |

**No public notebook is worth copying** — every one is weaker than what we
already run, including the public v25 of the player who was ranked #1 (3220) at
the time. Public notebooks lag well behind what the top players actually submit.
They are useful only as sparring partners, and `frontier` is the valuable
addition: it takes 7 of 20 seeds off us, so it exercises the agent differently
from the kawa family.

Dedup saved three redundant matchups: `rank-top10-read-the-market` =
`3000-socre` = `ttv1`, and **boatlee's "V20-Adaptive-R1" is kawa itself**.

Four notebooks (adaptive-farming-strategy, findings-from-zero-to-top-meta,
structured-economic-policy, ultimate-mega-ensemble-3000) extract to analysis
code rather than a standalone agent and are not usable.

## 14. v3 ladder losses: no bug, and the market layer is at a local optimum

37 games, **32-5 (86%)**. All five losses are narrow — the worst is -5,341 on a
$121k bank (4.4%) and the smallest is -139. There is no collapse to fix.

**Four of the five are at seat 0**: seat 0 goes 17/21 (81%), seat 1 goes 15/16
(94%). That is the structural asymmetry from section 5 showing up on the ladder,
and it is not fixable from the agent side.

The largest loss did suggest a real mechanism. We sold **2,738 FERTILIZER to the
opponent's 1,697** while its price ran 43 -> 26 -> 10 -> **1**, and the game
turned in exactly that window (d22 +414 -> d24 -5,097). Front-running only pays
while there is a price to win; at the floor both players clear at the same few
dollars. kawa ships this idea as `_PREEMPT_MIN_PRICE_RATIO` but leaves it at 0.0.

Implemented as `IV_MIN_PRICE` and measured over 24 paired seeds:

| gate | field mean | direct vs gate-off |
|---|---|---|
| off | +8,137 | — |
| 0.05 | +8,186 | +65 (9/24) |
| **0.10** | **+8,280** | **+100 (12/24)** |
| 0.20 | +8,320 | -12 (8/24) |
| 0.35 | +8,277 | -178 (7/24) |

**Not shipped.** The best variant wins its direct matchup 12 of 24 — exactly
chance — and +100 on an +8,137 margin is 1.5%.

That is the third refinement of the market layer to land in the noise
(structural forecast, staged dumping, price gate). **The layer is at a local
optimum; stop tuning it.** Remaining gains have to come from the schedule, which
is what `route/` is for.

---

## 16. The tape-selection rule: bucket 0 IS mis-assigned (2026-08-19)

Section 11 recorded the 5-bucket mapping as "already present and already
optimal — the whole 5-bucket mapping was searched, default wins". That is right
for four of the five buckets and **wrong for bucket 0**.

`_kawa_route_label` maps the town's shop draw onto one of five tapes. The space
is 5^5 = 3,125 mappings, which is the wrong way to attack it. Buckets are
mutually exclusive, so force each tape, record which bucket each game fell into,
and take the argmax **per bucket** — 5 measurements, not 3,125
(`planner/tape_sweep.py`).

That naive answer proposed changing three buckets and was wrong on two counts:

1. The argmax is selected on the data it is scored on.
2. **The bucketing is post-hoc.** `_kawa_route_label` reads the shops unlocked
   *so far*, so the bucket starts at 4 and moves as shops unlock — the agent
   switches tapes mid-episode. The tell was in the data: the default agent's
   bucket-1 mean (21,379) did not equal the mean of the tape the default map
   assigns to bucket 1 (15,847), which it would have to if the map were static.

Tested properly, as real `TAPE_MAP` variants on seeds disjoint from the
derivation (`planner/tape_map_test.py`):

| change | vs live | t |
|---|---|---|
| **bucket 0 only** | **+1,841** | **13.7** |
| all three buckets | +1,041 | 3.2 |
| bucket 1 only | -111 | -0.8 |
| bucket 2 only | -814 | -6.1 |

Bucket 0 fires when YARN_STORE is the first shop unlocked. The default sends it
to `6c12s_4q_first_yarn`; `6c12s_4q_second_yarn` is much better there.

**The conditional distribution is the part that matters**, because a tape swap
replaces the whole 30-day schedule — it either does nothing or changes
everything:

```
fires on 12.6% of games (452 of 3,600 paired)
conditional mean +14,662 (se 853, t=17.2), positive in 365/452 = 81%
conditional sd 18,145   min -33,940   median +12,618   max +72,456
```

Confirmed on the distribution that actually matters — replayed against the 80
real ladder opponents we have faced: **+429, record 62/80 → 66/80**.

Shipped as 55614625. Real-engine gate +858 (se 242) over 630 paired games.

**The remaining four buckets have now been checked properly and the default is
right for them. Do not re-search this.**

---

## 17. The market layer is exhausted — proven, not assumed (2026-08-19)

Section 14 concluded "the layer is at a local optimum; stop tuning it" from
three refinements landing in noise at n=24-32. That conclusion was correct for
*parameters* and wrong for *structural* changes — `IV_STRUCT` was structural and
worth +670 on the real engine.

With `planner/simulate.py` the parameter question is now settled at ~1,300
paired games per variant, with common random numbers:

| round | what | verdict |
|---|---|---|
| 1-2 | IV_STRUCT / dump / price gate / lead / slot | **+490 shipped**; slot_first -327 (t=-10.8); lead 2 and 4 both worse than 3 |
| 3 | dump ITEM SET (drop STRAWBERRY, MILK, etc.) | refuted: no_strawberry +496 vs unchanged +495 |
| 4 | base tape `_PREEMPT_*` constants | **all noise** |
| 5 | seat-conditional play | refuted, and backwards from the hypothesis |
| 6 | sell SUPPRESSION (hold stock for price) | **catastrophic**, -7,905 to -14,731 |
| — | tuned against the 80 real ladder opponents | live config already optimal (best +23) |

Two findings inside those negatives are worth keeping:

- **kawa's own preempt layer is inert under our configuration.**
  `_PREEMPT_MAX_BATCH` 30→40, `_PREEMPT_FRACTION` 1.0→2.0 and `_PREEMPT_START`
  120→0 each produce an **exact 0.0** paired delta. Our layer has taken over its
  role entirely. This retroactively explains section 5's note that PBT "moved
  backwards" over 10 rounds on these constants — it was optimising dead
  parameters.
- **Our high-volume/low-price selling is structural, not a defect.**
  `planner/analyze_top.py` shows us selling the most units (1,813) at the lowest
  price ($80.4) against ReCurSiON's 1,404 at $129.6, which looks like an obvious
  target. It is not: withholding sales at ANY threshold is catastrophic, because
  the tape's economy depends on continuous liquidation — held stock fills the
  100-item shed, stalls production and starves downstream purchases.

**Also corrected:** section 0's old "12 vs 14 hand slots, ~22% less labour" gap
is not real. Measured over 23 replays we run 277 hires / 12 hands / 2,858 useful
ops — the most ops of anyone on the ladder. Only ReCurSiON runs 14 hands.

---

## 18. The from-scratch planner, 2026-08-19: still far behind

`route/agent.py` under the current best genome is **~-34,000 paired margin vs
the 9-agent pool at ~0% win rate**. Note the honest baseline: gen116's recorded
fitness of -8,192 was measured on a much easier matchup mix (kawa + one rotating
reference + self-play); under the full uniform pool the same genome is -47,787.

Tried and refuted today:

- 10 hand-picked portfolio variants (more GOOSE/EGG, less STRAWBERRY, 8c4s-style
  mix): **all worse than baseline**, some much worse.
- `MIN_CREW` floor in `_size_crew` (`planner/route_v2.py`): **-13k to -52k**.
  The idea was that sizing the crew to *today's* tasks is circular — tasks come
  from planted tiles, which come from yesterday's crew — so a floor should
  bootstrap it. Instead it burns fib-priced cash on idle hands, matching section
  4's finding for the tape. The identity check (MIN_CREW=0 reproduces the
  unmodified agent at exactly +0) confirms the measurement was sound.

`planner/spec_extract.py` turns the tape into an explicit target list. The gap
is **scale, not efficiency**: our realised price per unit is BETTER than the
tape's ($89.7 vs $79.6) and our useful-op rate is higher (44.5% vs 40.1%), but
we hire 188 to its 277 and land 67 PLANT / 13 PLACE to its 186 / 53. We run a
farm about two thirds the size, well.

**Do not edit `route/agent.py` while a search runs** — workers re-exec it per
episode. Copy it (as `planner/route_v2.py`) and edit the copy.
