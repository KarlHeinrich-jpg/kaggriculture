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

### The two lines, as of 2026-08-20

Both are at local optima and the reason is now measured, not guessed.

- **tape+market (SHIPPED, ladder 2183.9)**: 600 mutants cleared nothing;
  five market-layer ideas refuted with controls. Section 20.
- **from-scratch planner (-57,830)**: its economy already MATCHES the tape's
  (own bank 86,386 vs 86,119). The entire gap is that the opponent banks ~$51k
  more against us, and the cause is price, not stolen volume -- they sell 1,446
  units against us and 1,447 against the tape, at $114.2 and $78.7 respectively.
  Ten levers refuted. Section 19.

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

---

## 19. The planner's deficit is PRICE SUPPRESSION, and ten levers were refuted (2026-08-20)

### The measurement that reframes everything

Every diagnostic before tonight measured OUR side -- revenue per work-turn,
$/unit, work fraction, build count, idle rate -- and all of them showed the
planner at or above the tape at 50 tiles. That is why nine experiments chased
the wrong quantity. **`paired margin` is us MINUS them, and the second term was
never measured on its own.**

Over 4 opponents x 3 seeds x both seats:

| we play | own bank | opponent bank | paired |
|---|---|---|---|
| dynamic, 50 tiles | 86,386 | **131,522** | -45,136 |
| the tape | 86,119 | **80,601** | **+5,518** |

**Our economy is already tape-equivalent -- 0.3% apart.** The whole gap is that
the opponent banks ~$51k more against us than against the tape.

### It is price, not volume. The opponent sells exactly as much either way.

| we play | opp units | opp $/unit | opp bank | our units | our $/unit |
|---|---|---|---|---|---|
| dynamic | **1,446** | **114.2** | 131,522 | 1,110 | 104.6 |
| tape | **1,447** | **78.7** | 80,601 | 1,603 | 80.5 |

The opponent sells 1,446 units against us and 1,447 against the tape -- the tape
takes not one unit from them. It wins by selling 1,603 units to our 1,110, which
drags the shared price level down 31% for everyone. **The tape suffers the low
prices too ($80.5/unit); it wins because at that price level the larger producer
comes out ahead.** Our high $/unit is a symptom of being small, not a strength.

So the requirement is precise: **produce profitably above ~50 tiles.**

### Ten levers, all refuted

| lever | result |
|---|---|
| proportional portfolio scale-up | -87,245 |
| crew floor (MIN_CREW) | -52,000 |
| crew + tiles together (schedule-driven) | -62,285 |
| cycling-crop portfolios (wheat-heavy) | -150,176 |
| geese (the uncapped book) | -183,427 |
| front-loaded purchases | -42,897 |
| SeasonPlan layout transplant | -86,211 |
| whole-tile triage scheduler | +/-2,700, i.e. noise |
| wheat flooding | -95,916, **and it makes the opponent RICHER** |
| capped-book flooding | -81,980, **opponent's volume does not move at all** |

Two of these are worth keeping as facts rather than scores:

- **Flooding wheat subsidises the opponent.** The engine allows `BUY_PRODUCT`
  only for WHEAT and FERTILIZER, so wheat is what they buy for feed. Pushing our
  wheat sales 285 -> 536 raised their bank 106,957 -> 112,248.
- **There is no headroom to steal.** Across every capped-book variant the
  opponent sold 753-755 units regardless of whether we sold 540 or 638. Town
  drain replenishes fast enough that both players sell what they produce. An
  earlier note in this document reasoned that capped products cannot be denied
  because both clear at $1; the real reason is simpler -- volume is not
  contested at all, only price is.

### Why buying to dump cannot work

`_commit_unit` quotes `BUY_PRODUCT` at `market_price(inv - 1)`, i.e. post-buy,
with the engine's own comment: "so a buy/sell round-trip against an unchanged
market nets zero". Price suppression has to be PRODUCED, never purchased.

### Status

Mechanism fully characterised, no usable lever found. This is not a parameter
problem: it needs a day scheduler that stays profitable past 50 tiles, and the
triage rewrite (`dynamic/router2.py`) did not deliver that. Do not re-run
portfolio or cash-flow searches -- `planner/role_gradient.py` measured all 24
single-role perturbations of the 50-tile optimum negative, and a 19-generation
cash-flow GA peaked at generation 1 (-57,830 from -78,027) and then went 17
generations without improvement.

---

## 20. The tape+market line is exhausted too (2026-08-20)

`evolution/` ran 600 mutants over 3 rounds -- tape-map recombination, cross-family
window splices, and jitter on the base tape's constants -- with **zero clearing a
+200 screen**, and stopped on its own plateau rule.

Market-layer ideas tested and refuted tonight, each with controls:

| idea | result |
|---|---|
| adaptive dump sizing from the exact price curve | 12 variants, all negative; best -34 |
| ...against fixed-fraction controls | no adaptive setting beat its fixed control |
| depth concentration (dump only MELON+FERTILIZER) | 8 variants, all negative, best -127 |
| day gate on late-game dumping | +22 (pool), +10 (ladder replays) |
| weighted / most-recent cadence predictor | 5 variants, -126..-181; median stands |

**The front-run audit is the useful artefact.** Over 144 games, tracking every
firing against the opponent's exactly recovered sales: we clear ahead on
**94-99%** of firings and same-step collisions are rare (the engine quotes both
players against the same pre-commit inventory, so a same-step sale is priced
identically for both -- beating them requires a strictly earlier step). Position
is not the problem. Realised price sorts by market DEPTH instead:

```
FERTILIZER  493 units to floor   +1.1 per unit
MELON       158                 +24.3
MILK         76                  -2.8
STRAWBERRY   62                  -2.1
WOOL         59                  -2.2
```

On three of five products we sell first and realise LESS: dumping into a shallow
book walks our own later units down, the town drains, and the opponent sells into
the recovery above our average. But the A/B refuted acting on it -- concentrating
on the deep books scored -127 -- so the audit signal is correlational, and does
not separate our dump's causal effect from the price path it shares with theirs.

---

## 21. Measurement rules added tonight

**Identical rows across variants means a parameter is inert, not that the idea
is neutral.** This cost three separate measurements:

- `TERMINAL_STEP` belongs to `route/agent.py` and does not exist in the tape
  build; nine terminal-timing variants returned byte-identical numbers.
- `PLAN_GATE_DAYS >= 0` is true for 0, so a SeasonPlan "off" control silently ran
  the tape's 73-tile layout with 50-tile parameters and scored -164,312 against
  its real -78,101.
- A sell-policy sweep produced seven identical rows because the reserve was
  never binding; a follow-up probe then mislabelled the cause as the reserve
  price when the actual hold is the FEED buffer.

`dynamic/agent2.py::configure()` now reports unknown keys and raises under
`STRICT_PARAMS`. **Apply the same guard before trusting any sweep.**

**Do not select games by outcome and then read their trajectory.** A per-day
margin trace of 7 losses against 7 wins appeared to show "endgame collapse" --
losses led at day 15 and bled out. That is circular: a loss is by definition a
game whose margin ends negative. Two interventions built on it (day gate,
adaptive sizing) found nothing, because the pattern was an artefact of the
selection. Compare at a FIXED point instead: of all games led at day 15, what
fraction converted?

**Behavioural cloning from a tape cannot work, and the control proves it.**
`planner/bc_data.py` + `bc_train.py` reach 92.8% action accuracy (96.2% on
non-move ops) from 2.7M samples. The resulting agent banks **$288** against the
tape's $89k. Letting the TAPE drive and merely asking the network what it would
do gives 92.6% agreement -- so the model is correct and the failure is covariate
shift. It is unfixable here: DAgger needs the expert to label the states the
learner reaches, and a fixed 719-step action list cannot be queried off its own
trajectory. Adding data does not help; more on-distribution samples say nothing
about off-distribution states.

---

## 22. The suppression math, and why neither half of the architecture can use it (2026-08-20)

Built to the plan of pricing every decision through the real market: an exact
market model, an opponent inventory tracker, and both wired into the market
controller and the day scheduler. **The math is right, both wiring points are
measured inert, and the reasons are structural rather than parametric.**

### The marginal value of a sale is not its price

`dynamic/market_model.py` reproduces the engine's `market_price` bit for bit
(0 mismatches over 9 products x 4,001 inventories) and adds the analytic slope.
Market inventory is a pure accumulator -- `_town_consume` subtracts the same
amount whatever we do -- so an extra unit sold now clears every LATER sale by
BOTH players one slope lower, for the rest of the season. Differentiating the
margin gives

    MV = P(inv) + alpha * |P'(inv)| * (N_them - N_us)

The suppression term is **signed on the difference of the two remaining
supplies**. That single fact retro-explains three earlier negatives: flooding a
book we ourselves still have to sell into is self-harm, which is exactly what
wheat flooding (-95,916) and capped-book flooding (-81,980) were measuring.

**Section 20's front-run audit was reading the wrong cause.** It sorted
realised-price edge by market DEPTH; the real variable is NON-RECOVERY, and
depth only correlates with it. Season town demand against units-to-floor:

    MELON       30 demand / 158 to floor   ratio 0.19   audit +24.3
    FERTILIZER   0        / 493            ratio 0.00   audit  +1.1
    WOOL       246        /  59            ratio 4.2    audit  -2.2
    MILK       331        /  76            ratio 4.4    audit  -2.8
    STRAWBERRY 422        /  62            ratio 6.8    audit  -2.1

MELON is in **no shop's product list** -- only the town centre's 1-per-24-steps
touches it -- and FERTILIZER has no buyer at all. Those two are the only books
where being first is worth anything, and they are exactly the two the audit
scored positive. The three it scored negative are the three the town refills
4-7x over. Perfect ordering, and it is derivable without playing a game.

### The opponent's holdings are recoverable, and they are always small

`dynamic/opp_state.py`. Their tiles are fully public, including `yield_units`,
`pending_care_bonus` and `money`. Within a day `yield_units` can only fall, and
only HARVEST lowers it, so summing intra-day drops measures their harvests
**exactly** -- validated in `dynamic/opp_state_test.py`, where the residual
mirrors the sales side unit for unit.

Two corrections tame the sales side, which is blind only at the $1 floor:
floor reconciliation (a floored book cannot be suppressed anyway -- `slope()` is
0 there) and the shed cap. `_drop_inventories_to_shed` keeps **100 items TOTAL
across all products and discards the overflow**, so no estimate above ~100 is
physically possible; that alone cut MILK's drift from 267 units to 24.

The useful finding is what survives: **the opponent can never be sitting on a
hoard**, so `N_them` is dominated by what their tiles will still produce, not by
what they hold.

- The structural forecast under-reads the truth ~2.5x (72.8 strawberry against
  an actual 192.7) but has RANK: correlation 0.66-0.82 on the five products
  that matter. A scalar gain fixes a bias, so the bias was left to calibration.
- **Extrapolating their exact observed harvest rate instead is worse.** It
  halves the bias and takes strawberry's correlation from 0.66 to -0.00 and
  melon's from 0.80 to -0.04. Kept behind `blend`, defaulted off.

### Why the market controller cannot use any of it

Attributing every unit we offer to the branch that offered it (3 seeds, vs kawa):

    shed-panic dump 79%     terminal dump 19%     the price gate 2-3%

The reserve price, the front-run hold and the opponent's reserve scale together
govern **one sale in forty**. The agent's real sell policy is "the shed passed
20% -> dump everything", and that is also, by accident, why our realised $/unit
is HIGHER than the tape's: dumping in small frequent batches meters the book.

This is the true cause of the "identical rows" symptom in section 21. The gate
is not merely unbinding on some parameter settings; it is nearly dead code.
Every MV variant lands in noise -- MV ordering of the panic dump -34 (t=-0.0),
alpha 0/0.5/1/2 all within 200, `SHED_PANIC_FRACTION` 0.10 exactly +0.

Metering is worse than inert: -32,749 (t=-12.7). Holding stock fills the shed
and stalls production, the same mechanism section 17 round 6 measured.

### Why the scheduler cannot use it either

`dynamic/task_value.py` prices every task through the live market -- a melon
harvest and a wheat harvest score 900 apiece under `OP_VALUE`, though one is six
units at $250 and the other six at $25. It is correct and it is **exactly +0
over 144 paired games**, because:

| day | tiles with work | op-turns wanted | crew turn cap | utilisation |
|---|---|---|---|---|
| 12 | 63 | 102 | 288 | 35% |
| 18 | 63 | 92 | 264 | 35% |
| 24 | 57 | 110 | 264 | 42% |

**Mean 35%, max 43%, and demand exceeds capacity on 0 days of 30.** Task value
only decides which work gets DROPPED, and nothing is ever dropped. `partition`
assigns by angular sweep; value reaches `build_tour` only on over-subscription.

So the whole objective `J = sum V_task - lambda*C_move` optimises an allocation
problem with 65% slack, and every coefficient in it (lambda, alpha, K, gamma,
beta) is unidentifiable by construction. This also explains `MIN_CREW` at -13k
to -52k: we already hire hands with nothing to do.

### What the audit says the gap actually is

`dynamic/revenue_audit.py` prices both players' sales through the commit hook.
Against kawa, 3 seeds:

| | our units | our $ | their units | their $ |
|---|---|---|---|---|
| dynamic scheduler | 1,132 | 89,008 | 1,521 | **137,382** |
| the tape | 1,704 | 91,889 | 1,704 | **91,734** |

**Our own economy is fine -- our bank is 77,614 against the tape's 71,544 in the
same matchup.** The entire gap is the second column. MILK is the clearest case:

    against us      we sell 156 @ $138, they sell 265 @ $141   margin  -15,789
    against the tape   248 @ $40,          249 @ $40           margin      -28

**The tape does not win milk. It neutralises it**, and that is worth +15,761
because the deficit it erases is larger than the revenue it gives up. Same shape
on strawberry (-23,625, crushable to about -6,480).

That is the mechanism, stated exactly, and it needs volume we do not have --
1,132 units against 1,704. Suppression cannot be bought (`BUY_PRODUCT` quotes
post-buy, so a round trip nets zero) and cannot be timed (we already dump
continuously). **It has to be PRODUCED.**

### Refuted tonight, with controls

| lever | result |
|---|---|
| MV ordering of the shed-panic dump | -34 (t=-0.0) |
| MV metering when we out-supply them | -32,749 (t=-12.7) |
| MV re-pricing the sell gate, alpha 0..2 | all exactly +0 (gate not binding) |
| economic task value in the scheduler | exactly +0 (capacity not binding) |
| economic task value + triage | -869 (t=-1.1) |
| WHEAT priority 0.014 -> 0.85 | **-75,378** (displaces melon/strawberry) |
| ...with 12 / 18 wheat tiles | -123,861 / -91,455 |
| 12 wheat tiles at current priority | -4,161 |
| 6 geese (EGG trades $89, nobody produces it) | -49,999 |
| feed buffer 1.0 -> 2.5 | -30,343 |

Also measured and NOT a defect: **shed-overflow discards are 15 units a game
against the tape's 21.** The nightly 100-item cap is not eating our output.

### Status

The suppression theory is sound and now has exact tooling behind it. Neither
the market controller nor the day scheduler is the place it can act, and both
were shown so by measurement rather than argument. The binding constraint is
unchanged from section 19 and is now quantified from a second direction:
**produce more units profitably.** Until that moves, this line stays at -90,650
paired against the 9-agent pool while the shipped tape+market build is +9,016.

### 22a. One thing that did work: refill dead tiles with wheat

`_last_plant_day` is 19 for STRAWBERRY and 17 for MELON, but **25 for WHEAT**.
After day 17 any tile that dies is dead for the season, because its own role can
no longer return anything before the buzzer -- and our board loses 10 tiles over
the last third (49 -> 39) where the tape holds ~70 flat. Replanting those with
wheat costs $10 and displaces nothing.

`NURSE_LATE=1, NURSE_CROP="WHEAT"`, paired margin against the 6-agent pool:

| seed set | n paired | vs base | se | t | paired wins |
|---|---|---|---|---|---|
| 90210 | 144 | **+1,768** | 373 | 4.7 | 96/144 (67%) |
| 4242 | 240 | **+1,893** | 286 | 6.6 | 166/240 (69%) |
| 777001 | 360 | **+2,049** | 221 | 9.3 | 259/360 (72%) |

Controls: `NURSE_LATE` with no `NURSE_CROP` is exactly +0, and
`NURSE_CROP="MELON"` is exactly +0 -- melon can never be the refill because its
own last plant day is 17. `SEED_BATCH_PER_TURN=16` on top adds ~+600 but its own
control is only +822 (t=1.6), so it is not established on its own.

**Mechanism confirmed, not assumed.** The two agents are byte-identical through
day 19 and then diverge exactly as predicted:

    day          15    17    19    21    23    25    27
    baseline     47    48    47    43    43    42    37
    late wheat   47    48    47    47    46    46    42     wheat 245 -> 282

Now on by default in `dynamic/agent2.py`. Note for future sweeps: the baseline
has moved, so an identity control has to set `NURSE_LATE=0`, not leave it unset.

### The same idea at the other end of the season does NOT work

Deferring expensive seed to follow the tape's cash-flow order is worse, and
consistently: STRAWBERRY held to day 8 is -10,029, day 11 -14,860, day 14
-32,276. Strawberry is an ongoing crop with a **4-yield lifetime cap**
(`production_count > max_yield` stops it, engine line 796), so every day it is
held back is a yield it never takes. Nursing wheat through the gap recovers
+4,000 to +6,000 of that but never the whole cost.

Also refuted with controls tonight, all on the opening ramp:

| lever | result |
|---|---|
| `BUY_ANIMALS_FIRST=0` (cheap seed before $400-500 animals) | **-17,719** |
| ...with batch 16 | -18,558 |
| `PLANT_MISS_TOLERANCE` 16 -> 0 / 2 / 4 | -1,214 / +1,311 / +183, all noise |
| the 73-tile season plan (85 tiles realised) | -62,148 |

The opening-order hypothesis was wrong in the direction it was proposed: animals
first is right. They produce fertilizer unconditionally from day 1 and milk/wool
for twenty-plus days, where a $100 strawberry seed returns nothing until day 12.

### Why the 85-tile plan still fails, measured

Crew capacity is NOT the reason, and the earlier reading of this was wrong on a
subtlety: `_size_crew` sizes the crew TO the task list, so utilisation is pinned
by construction at ~32% whatever the portfolio (50 tiles 35%, 85 tiles 32%,
0 days over 100% in either). It measures the crew-sizing ratio, not slack.

The real breakdown of where unit-turns go, against the tape on the same seed:

    us, 50 tiles   move 43%  enable 33%  idle 13%  produce 5%  build 2%   5,485 turns
    us, 85 tiles   move 47%  enable 30%  idle 12%  produce 4%  build 3%   5,330 turns
    the tape       move 52%  enable 28%  idle  8%  produce 6%  build 4%   6,914 turns

**Movement is not our problem -- we are better at it than the tape (43% vs 52%)
and it still banks twice as much.** It simply does 26% more unit-turns and 2.5x
more build ops. And under the 85-tile plan our cash sits at $0.3k from day 3 to
day 15 while the tape is at $10.3k by day 12, so the extra tiles are planted and
then die unwatered (19 tiles on day 3 down to 9 on day 6). More tiles without
the cash to crew them is strictly worse, which is the sixth independent
confirmation of that.

---

## 23. Opportunity cost as a module, so the windows find themselves (2026-08-20)

Section 22a's late-wheat refill was found by hand. It is one instance of a rule:

    V_task = V_self + V_suppress - V_opportunity
    V_opportunity(tile, t) = max over feasible c of E[Profit(c, tile, t)]

After day 19 nothing but WHEAT and CARROT can still be planted, so the feasible
set collapses to one useful element, `V_opportunity` goes to 0, and any
positive-profit crop should be planted automatically. `dynamic/opportunity.py`
computes the feasible set and each member's profit, so windows of that shape
fall out of the arithmetic instead of being noticed.

### E[Profit] is exact, and the two yield rules are different

Both had been misread earlier in this project, so they are now written down:

- **NON-ONGOING (WHEAT, CARROT, MELON).** `_new_plant` seeds `yield_units = 1`
  and the nightly refresh SKIPS them entirely. Yield comes from WATER, and only
  inside `[(max_yield_day+1)//2, max_yield_day]` (engine line 438-443). WHEAT
  therefore makes 1 + 3 = **4 units for 6 unit-turns**; MELON makes 6 by age 10.
  HARVEST then DELETES the plant, which is what lets it cycle a tile.
- **ONGOING (STRAWBERRY, TOMATO).** `production_count > max_yield` stops accrual
  permanently (engine line 796), so `max_yield` is a **LIFETIME cap**.
  STRAWBERRY produces exactly 4 units, at ages 10/12/14/16. That is the
  arithmetic behind deferral measuring -10,029 to -32,276 in section 22a: every
  day held back is a yield never taken, not a yield delayed.

### It reproduces the hand-found window and beats it

`ALLOC_MODE=1` keeps a tile's searched role while that role is feasible and
profitable, and otherwise plants the best thing that still is. Paired margin
against the 6-agent pool, four disjoint seed sets, all against the same static
base (`NURSE_LATE=0, ALLOC_MODE=0`):

| seeds | n | hand-coded late wheat | alloc1 L13 | alloc1 L15 |
|---|---|---|---|---|
| 31337 | 240 | +2,311 (t=8.9) | — | **+2,938** (t=8.4) |
| 606060 | 288 | +2,363 (t=8.7) | **+3,020** (t=10.7) | +2,872 (t=10.5) |
| 818181 | 288 | +1,863 (t=7.6) | — | **+2,545** (t=7.6) |
| 246810 | 288 | +2,229 (t=9.4) | **+2,631** (t=8.7) | +2,449 (t=8.0) |

The allocator beats the hand-written rule by +500 to +680 on every set, at
82% paired wins on the largest. `ALLOC_LABOR` is a **plateau over 13-17**, not a
spike, with a cliff at 20 (-11,684) where strawberry's profit turns negative and
the fallback abandons it everywhere. Shipped at 13.

**`ALLOC_MODE=2` (always plant the argmax) is -53,163.** The searched static
layout carries real information about WHERE a role belongs that a per-tile
profit comparison does not have; the allocator is only allowed to act where the
static answer has expired.

### What it found on its own

Instrumented over 3 seeds, substitutions of (searched role -> chosen crop):

    MELON      -> WHEAT   days 20-27      the hand-found window
    STRAWBERRY -> WHEAT   days 20-25      the same window, other tiles
    STRAWBERRY -> MELON   days 18-19      NEW -- nobody had looked here
    anything   -> None    days 28-29      correctly stops planting

### A candidate the formula proposed and the engine rejected

`_last_plant_day` keys on `max_yield_day`, but HARVEST is gated on
`first_yield_day` (engine line 457) -- `max_yield_day` only bounds accrual. The
true bound is later: **MELON 17 -> 19** (still its full 6 units, since the
accrual window shuts at age 10 anyway) and **WHEAT 25 -> 27** (2 units, ~$100,
on a $10 seed). Both have positive gross profit, and the STRAWBERRY -> MELON
window above needs them.

Measured: **-1,546 (t=-7.0) on its own, -1,656 with the allocator, -2,085 with
the hand-coded refill.** So the flat $/unit-turn labour price understates a LATE
planting: it waters every day until harvest against a crew that is winding down,
and it finishes inside the terminal liquidation window where the turns are
wanted for selling. Kept reachable as `TRUE_LAST_PLANT_DAY`, defaulted off.

This is the formula-and-experiment loop behaving correctly. The module proposed
three windows; the engine kept one, and the one it kept is worth more than the
hand-written version of it.

### Shipped defaults in `dynamic/agent2.py`

    ALLOC_MODE = 1        ALLOC_LABOR = 13.0        TRUE_LAST_PLANT_DAY = 0
    NURSE_LATE = 1        NURSE_CROP = "WHEAT"      (both bypassed while ALLOC_MODE is on,
                                                     and worth +2,229 if it is turned off)

`ECON_VALUE` remains exactly inert alongside all of this (+2,449 with and
without), as section 22 predicted: nothing is ever dropped, so the thing that
decides what to drop cannot matter.

---

## 24. Global resource valuation: the veto works, the replacement does not (2026-08-20)

`dynamic/enpv.py` implements the full framework -- ENPV per asset with an
endogenous price, dynamic feed costing, a multi-dimensional knapsack, the labour
shadow price, bundle ROI and a burn-rate cash reserve. Two wirings of the same
correct valuation, and they differ by 95,000 paired margin.

### The endogenous price is the piece a fixed-count portfolio cannot have

`market_model.realized_price(item, inv, n, shops, days, opp_units)` returns the
AVERAGE $/unit for selling n units over `days`, against the town's drain and the
opponent's expected supply. A marginal quote prices one more unit; an asset
produces many, and each lowers the price of the next:

    n units sold over 18 days, opponent selling the same
    item          n=20   n=50  n=100  n=200  n=400      drain/day
    MELON          248    228    148     73     38          1
    STRAWBERRY     228    219    203    151     11         25
    EGG             55     54     51     43     41         13

A genome storing TC_COW=5 prices all five cows identically. With the feedback
in, the marginal animal is valued against the book the existing herd has already
filled, and the numbers are decisive: at 6 sheep owned the seventh is worth
**-118**, and the searched genome buys seven.

### Wholesale replacement: -90,059

`ENPV_BUY` replaces the searched purchase throttle with the knapsack. It starts
BETTER -- 20 producing tiles by day 3 against the base's 8, which is the ramp
this project has been chasing since section 19 -- and then collapses to 8 tiles
by day 9 with cash pinned at $0.00. It spends every dollar on seed and cannot
afford a single hand to water it.

Two bugs found and fixed on the way, both worth keeping:

- **The reserve must be sized to the crew the farm WILL need**, not the one it
  has. Crew is sized to the current task list, so on day 0 it is 1 and a burn-
  rate reserve built from it is about $2. (-115,067 -> -90,059 when fixed.)
- **It needs a floor at SPEND_RESERVE.** The rest of the agent refuses to hire
  while `money - cost < SPEND_RESERVE`, so a reserve below that number does not
  under-save, it silently disables hiring.

Even fixed it is -90,059, and insensitive to every parameter (L8 -88,718,
L20 -115,359, dry-days 1/2/4 all within 600). That is a behavioural break, not
a mis-valuation.

### Subtractive: +4,208 mean over three seed sets

`ENPV_VETO` keeps the searched purchase order exactly and only DECLINES a
purchase whose ENPV has gone negative. It can remove spending, never redirect it.

| ENPV_LABOR | 135791 (n=240) | 515151 (n=288) | 929292 (n=288) |
|---|---|---|---|
| **8** | **+3,626** (t=3.4) | **+4,619** (t=5.1) | **+4,378** (t=4.6) |
| 10 | — | +4,876 (t=4.8) | +2,126 (t=2.0) |
| 13 | +1,598 (t=1.4) | +4,681 (t=4.5) | +2,946 (t=2.8) |
| 20 | -3,279 | — | — |
| 30 | -27,650 | — | — |

Shipped at 8, the stable point. Above ~20 the veto starts refusing purchases
that pay.

**The veto is inert while ALLOC_MODE=0** -- it needs `S["econ"]`, which is only
built when the allocator or ECON_VALUE is on. Measured as two byte-identical
rows, which is exactly section 21's symptom.

### THE PATTERN, now established across five attempts

| change | shape | result |
|---|---|---|
| opportunity allocator (ALLOC_MODE=1) | **additive** -- acts only where the static role has expired | **+2,865** |
| ENPV veto | **subtractive** -- only removes negative-ENPV spending | **+4,208** |
| ALLOC_MODE=2, free argmax layout | replacement | -53,163 |
| ENPV_BUY, knapsack purchasing | replacement | -90,059 |
| MV metering in the market layer | replacement | -32,749 |

**The searched genome's parameters are co-adapted.** A principled subsystem
dropped in on top of them breaks that co-adaptation faster than its own
correctness repays. Every gain this session came from a change that acts only
where the existing policy does nothing, or that only declines. Design new work
to that shape.

### Cumulative, one fresh seed set (n=336 paired)

| build | paired margin | vs session start | t |
|---|---|---|---|
| session start | -80,909 | — | — |
| + late wheat (hand-coded) | -78,605 | +2,304 | 9.3 |
| + opportunity allocator | -78,044 | +2,865 | 10.7 |
| **+ ENPV veto (SHIPPED)** | **-73,390** | **+7,519** | **8.5** |
