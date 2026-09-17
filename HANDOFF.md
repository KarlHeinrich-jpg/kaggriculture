# Kaggriculture white-box handoff

## Recovery update — 2026-09-18

The resumed failure-driven campaign is complete for this foreground pass. The
current best audited package is `submission/whitebox_v454.py` (entry
`whitebox.versions.v454_public_weed_window_sale_cash`). On the fixed public
pool of 9 opponents × seeds `11,47,101` × both seats it scores **18/54 =
33.3%**, with all 54 episodes `DONE` and no runtime errors. It is the package
to preserve and upload; no candidate reached 100%. It was uploaded to Kaggle as
submission **56315014** on 2026-09-17 23:06 UTC; the current API status is
`PENDING`.

The measured failure pattern remains joint route throughput, not one isolated
threshold: against the hardest losses the candidate produced substantially
fewer `WATER`, `HARVEST`, `PLANT`, `DIG`, and `SELL` operations than the public
opponent, while often retaining a similar herd. The fixed evidence is in
`analysis/failure_pool_v454.csv`, `analysis/official_trace_v454_54.json`, and
`analysis/ab_v454_54.json`.

The following observation-only candidates were audited, packaged, and rejected
because they failed to beat V454 on the 12-game screen (results are recorded
under `analysis/`): V517 (0/12), V518 (3/12), V519 (4/12), V520 (3/12), V521
(0/12), V522 (2/12), V523 (0/12), V524 (2/12), V525 (1/12), V526 (1/12), V527
(0/12), V528 (0/12), V529 (1/12), V530 (2/12), and V531 (2/12). The best
looking route split still regressed on the balanced and multi-route opponents;
therefore none is promoted. All runtime checks use only the live observation,
public engine rules, and explicit seat-scoped certificates; no opponent name,
seed, seat mapping, replay tape, fitted policy, or private opponent inventory
is reachable from the submission bundle.

The next recovery seam is a jointly certified task-assignment/value repair
that increases productive route throughput without changing the opening
capital queue. Do not promote a single-task priority, unconditional 14-hand,
late-sale-cash, fourth-land, or late route-switch edit without a fresh 54-game
comparison against V454.

Updated: 2026-09-17. This is the only current recovery document. The former
long record is archived at `docs/HANDOFF_HISTORY_2026-09-02.md`; raw evidence
stays in `logs/`, and equations/architecture stay in `MODEL.md`, `STRATEGY.md`
and `WHITEBOX_ARCHITECTURE.md`.

## Non-negotiable contract

Build the strongest legal two-player agent, judged by absolute wins and paired
final-money margin against a declared opponent pool. The online policy must be
completely white-box:

- every state, candidate action, constraint, cost and value term is named and
  inspectable;
- use only the current observation, public engine rules and our own retained
  action certificates;
- never identify opponents or branch on names, source files, replay IDs or
  identities;
- never imitate/follow action tapes, fit hidden weights or import offline
  traces into runtime;
- never hard-code leader dates, coordinates, asset counts or compositions;
- leader/tape observations are offline falsification evidence only. Any lesson
  must be re-derived from public rules and expressed as a general mechanism;
- cash flow is a hard feasibility certificate, not the objective. Feasible
  actions are compared by robust paired margin against a finite set of
  resource-feasible, fully paid opponent responses;
- no lambda mixing own wealth with win probability. IDLE is an explicit action;
- `econ.MAX_OWNED_QUADRANTS = 3` is a user-required global invariant. No layer
  may buy, plan for or use the fourth quadrant.

Do not start a background campaign, server loop or watchdog. Work is
foreground-only unless the user explicitly reverses this decision.

## Current truth

- The current public-white-box reference is
  `whitebox/versions/v361_public_wheat_rotation22.py`, packaged as
  `submission/whitebox_v361.py`. It was uploaded at the user's explicit request
  on 2026-09-17 as Kaggle submission **56306983**; initial status was
  `PENDING`. Its declared evaluation is 13/54 absolute
  wins (24.1%, mean final-money margin about -$16,699), 18/144 wins on the
  screen block (12.5%), and 13/180 wins on the untouched holdout (7.2%). The
  holdout regression forbids promotion or upload; V361 remains a research
  reference only.
- V363--V369 tested three tempting scalar repairs and rejected all of them:
  exact same-turn sale cash (V363, 6/54, about -$20,352), exact sale cash only
  for seed/crew work (V364, 9/54, about -$18,136), cross-quadrant penalties of
  16 and 4 (V365, 10/54, about -$19,931; V366, 3/54, about -$20,037), earlier
  inventory banking (V368, 8/54, about -$16,449), and only lowering the banked
  value trigger to the public $2,000 land price (V369, 12/54, about -$16,900).
  Do not continue tuning sale-cash, quadrant-crossing or DROP thresholds.
- The public engine credits each successful SELL at 100% of its quoted price,
  but V363 showed that exposing all of that cash to the undifferentiated
  capital queue changes day-1 purchases from three wheat seeds toward commodity
  wheat and later collapses the wool path. Thus V361's 0.85 factor is an
  accidental risk buffer, not a rule value. The next mechanism must separate
  feed, seed, crew, sales and durable-capital obligations in a named committed-
  work ledger, constructed from one immutable public snapshot, before exact
  sale proceeds can be released safely. Shared-market opponent response must
  be represented by a finite public-rule certificate rather than another cash
  multiplier.
- Recovery verification on 2026-09-17 passed all 429/429 unit tests, Python
  compilation and `git diff --check`. The five focused sale-cash tests are in
  `whitebox/test_public_sale_cash.py`; causal traces are
  `analysis/trace_v361_cash_seed11.json` and
  `analysis/trace_v363_cash_seed11.json`. No Kaggle upload was made.
- A resumed failure-driven pass tested V370--V382 on the hardest measured
  seed-101 block (nine public opponents, both seats, 18 games). None qualified
  for the 54-game gate, so V361 remains the local reference. The tested seams
  were crop-work priority (V370), 14/12-animal service caps (V371/V376), 14
  hands (V372), optional cross-quadrant locality (V373), a visible crop-race
  guard (V374), clustered 14-animal layout (V375), combined crop/animal guards
  (V377), opening seed commitments (V378/V379), seed-before-feed queue ordering
  (V380), committed WATER (V381), and early PLANT priority (V382). The best of
  these small screens still won only 3/18; most materially reduced margin.
  V383 is an untested diagnostic and must not be packaged, uploaded or treated
  as evidence.
- The public trace on seed 101 explains why these local fixes failed. V361
  already reaches 53 live crops mid-season and then loses them through the
  ordinary harvest/decay cycle; it also executes hundreds of CARE, fertilizer,
  feed and movement actions. Promoting one task class changes the whole shared
  market path and often reduces early hiring or output. The next valid research
  step is therefore a single immutable `FlatSnapshot` plus a committed-work
  ledger that jointly prices seed, plant, water, feed, sale and crew obligations
  before emitting the queue. Do not resume isolated priority/count edits.

- Production entry: `whitebox/agent.py`; research wrappers:
  `whitebox/versions/`.
- Latest uploaded white-box bundle before the 2026-09-17 V361 handoff is
  `submission/whitebox_v292_public_weed_priority3.py`, Kaggle submission
  **56246208**, completed on 2026-09-15 with publicScore **767.6**. The older
  V204 submission **56007683** remains a historical architecture reference,
  not the latest upload.
  The latest local candidate is `submission/whitebox_v218_certified_shed_cluster.py`.
  V218 adds only a certified shed-access layout challenger: newly purchased
  animals may use a central access cell only when the unchanged current/future
  route and unified cash/value certificate accepts it. It does not open the
  broad central-tile action space or use replay coordinates.
  Kaggle accepted it as `COMPLETE` on 2026-09-04. After its first completed
  ladder episode its publicScore is **698.8**; the initial 600 was only the
  registration rating. V203 submission 55978231 completed at **744.6** and
  V199 submission 55972915 currently reports **825.0**.
- Final local V202 production bundle: `submission/whitebox_v202.py`,
  SHA-256
  `6a22323649a03ae1794bd6d574596b452c80c5dc1f986cf06b900d2318d679fc`.
  Its packaged entry is `whitebox_v202_stable_repair`: V190's stable
  economic core with V199 spatial multistart and the unproved paid-turnover
  arm both explicitly disabled.
- V132 is the evidence-backed reference. V149 is the strongest directional
  land arm. V190 is the strongest recent economic arm. V204 is the latest
  uploaded research arm. None is promoted under the current protocol.
- V199's fresh 9-cell gain (+$6,037/cell, SE $6,387, W-L 6-3) is only a noisy
  screen and had zero absolute wins. The measured hard-pool absolute win rate
  remains 0%; there is no 100% or gold claim.
- V200 service-cluster placement was inert after fixing a cash-flow pickup-day
  crash. V201's repeatedly re-optimised land-turnover option could defer the
  same ownership state forever and was rejected. V202 closes the submitted
  regression by rolling back V199's noisy spatial-route second start to the
  evidence-backed V190 configuration. V203 adds the bounded early-land option
  and repaired late-land route reachability. V204 retains a deferred land
  obligation until its public eligibility day and bounds the online integer
  quantity frontier, as described below.
- Preserve the dirty worktree. Many `whitebox/` files are currently untracked;
  never reset, overwrite or delete unrelated work.

## V218 animal-layout repair

V204 excluded the four public `paths.SHED_TILES` from productive placement, so
even its distance-sorted animal columns could only stop on the outer ring. V218
keeps that ordinary proposal space unchanged and enables
`productive_shed_relocation=True` plus `service_cluster_layout=True`. The
challenger enumerates only current-observation empty cells, keeps existing
animals/structures fixed, preserves item counts and land orders, and accepts a
layout only after the existing current-route, future-service, cash and finite
public-response certificates pass. The relocation execution manifest applies
the retained item/tile map on the next observation. A 108-game local screen
against V204 was neutral (pool paired delta about **-$305**, no separable
difference); a direct simulator trace placed the first cow on `(4,4)` and the
next sheep on `(3,4)`, while V204's corresponding first animal was outside the
center tile. This is a geometry correction, not a claim of leaderboard gain.

## V202 diagnosis and production decision

The external-observation trace of submitted V199 on seed 37320 exposed a real
throughput symptom. It does not read planner internals.

| measure | V199 | opponent |
|---|---:|---:|
| final cash | $121,716 | $151,497 |
| PLANT / distinct used tiles | 103 / 51 = 2.02 | 199 / 63 = 3.16 |
| DIG | **0** | **40** |
| day-27 crops / weeds | 19 / 18 | 61 / 0 |

V199 opens quadrant 2 on day 2; the opponent opens it on day 6. Early land is
secondary. V199 never DIGs, productive area shrinks and service-heavy animals
consume the remaining labour. These are observed symptoms, not online targets.

The action-set bug was real:

- V179 uses `execution_variant="paid_weed_reinvestment_manifest"`, which makes
  a weed valuable even when no seed is already held and closes the circular
  deletion `no seed -> DIG value 0 -> no empty tile -> no seed purchase`;
- the capability is now an orthogonal plan boolean, threaded through projected
  plans, cache keys, capital and execution without replacing fertilizer;
- an empty/no-seed tile waits instead of losing its retained
  DIG -> BUY_SEED -> PLANT -> WATER certificate;
- the projected capital solve completes only the exact named missing seed,
  under live cash reserve and order slots;
- turnover output credits only the earliest unfertilized engine yield;
- additive insertion preserves the ordinary task set and exact route order,
  and cannot precede an incumbent output-banking tail.

Those mechanical fixes are tested, but the economic hypothesis was falsified.
The candidate still lacks a retained future-day harvest/service witness. The
unsafe current-clear hire arm lost `-$10,785/cell` on the seed-37320
three-opponent screen. After durable-capital and terminal-cohort gates, the
two-seed hard screen still lost `-$2,456/cell`; order-preserving suffixes
lost `-$2,494/cell`, with every firing pair negative. Therefore the paid
turnover arm is retained only as `submission/whitebox_v202_experimental.py`
and is **off** in production.

The submitted V199 result also falsifies its own last addition. V199 differs
from V190 only by a spatial route multistart that had a noisy nine-cell
`+$6,037` screen (SE `$6,387`, t `0.95`) and then scored 822.4 live.
V190 had the stronger recent evidence: `+$8,019/cell`, t `3.74`, W-L
`14-4` against V149 on 18 fresh cells. A new two-seed direct comparison of
V190 versus V199 was mixed (`-$1,250/cell`, W-L `4-2`) and not separated.
V202 therefore makes the conservative, inspectable rollback: exact V190
economics, no spatial second start, no paid turnover. On seed 37320 it is
action-equivalent to V190 for all three hard opponents.

## V203 adaptive land certificate

Terminology matters. The farm begins with one quadrant. The first
`BUY_LAND` opens the **second total quadrant**; this was occurring too early.
The second `BUY_LAND` opens the **third total quadrant**; submitted V199 never
issued it in the diagnosed Enrico Ambrosio replay.

Two independent action-set bugs were repaired without putting that identity,
replay ID, seed or action sequence into production:

- Before the first paid expansion, the immediate land bundle must pay its
  named assets and current crew while preserving the standing service bridge.
  It is deferred only if both finite immediate endpoints fail and a concrete
  standing one-shot crop supplies a cash/route/order-certified released-tile
  alternative. This finite option may be exercised once per own ownership
  state; it cannot recursively replace every later land decision and create
  V201's endless rolling wait. A feasible immediate endpoint is never blocked
  by a predicted date.
- After two quadrants are public, `_late_crop_land_challenger` had already
  selected a positive robust crop ray, but `joint_assign` re-ranked its new
  capital columns by old standalone task values and could choose `n0`. The
  selected ray is now routed as one mandatory candidate. Every route may still
  reject it; displaced ordinary task value is charged, and the actually routed
  positions are recertified before `BUY_LAND` is emitted.

The external-observation trace on seed 38520 against the frontier reference
shows the intended two-sided correction. V202 bought the first paid quadrant
on day 2 and ended with two total quadrants. V203 bought on days 4 and 11 and
ended with three. Against the fixed public action sequence from the diagnosed
Enrico replay, the packaged V203 bought on days 8 and 14 and also ended with
three. This fixed-sequence run is causal falsification only, not a win-rate
estimate or an online dependency.

Small hard-pool screens are mixed and remain screens: the known adverse
three-cell block was `-$18,956/cell`, W-L 1-2; a fresh six-cell block was
`+$9,152/cell`, W-L 4-2. They neither prove a regression nor qualify a
promotion. Evidence is in
`logs/arena/v203_one_exercise_vs_v202_diag_38550.json`,
`logs/arena/v203_one_exercise_vs_v202_fresh6_38560.json`, and
`logs/arena/v203_one_exercise_frontier_trace_38520_s0.json`.

## V204 retained land commitment and bounded certificate frontier

V203 fixed the value comparison but left two implementation failures in live
play. First, after a certified decision to wait for a named standing crop to
release its tile, the ordinary proposal could disappear on the eligible day;
the policy remembered that waiting had been exercised but not the obligation
to retry the land action. V204 stores only the public seat, current unlocked
count and certified eligibility day. Before that day it suppresses only the
same pure next-land ray. At and after that day it reopens
`_late_crop_land_challenger` even when the ordinary capital master no longer
proposes land, and emits `BUY_LAND` only after a fresh full cash, service,
route and paid-response certificate. An ownership change clears the retained
obligation. This repairs both premature first paid expansion and missed later
expansion without a date, opponent or replay branch.

Second, V203 certified every integer crop quantity. One live day generated
141 expensive unified certificates; accumulated Kaggle overage caused the two
deterministic timeout collapses seen in episodes 105129270 and 105201896. V204
keeps every public crop direction but cheaply enumerates rule-derived endpoint
feasibility first. Because Fibonacci hiring can make feasibility non-monotone,
feasible quantities are partitioned into maximal contiguous regimes. Each
regime retains its first and last quantity, its exact standalone-surplus
maximizer, and that maximizer's feasible predecessor. Only this finite frontier
receives the expensive adversarial certificate. This is a candidate-screening
bound, never an acceptance shortcut: every emitted action still receives the
unchanged unified certificate and exact routed-position recertification.

The final package passed all **358/358** unit tests, compilation, forbidden
runtime-token scan, and source/bundle identity. On the actual public-observation
prefix of the diagnosed Enrico Ambrosio episode 105308430, V204 buys the third
total quadrant on day 13 with `BUY_SEED WHEAT 4 + BUY_LAND`; source and packaged
bundle agree through step 312. The two earlier missing-second-total-quadrant
cases reopen on day 8 (WHEAT 16 in episode 105091929 and CARROT 17 in episode
105104124). These replay identifiers are offline test labels only and do not
occur in the runtime bundle.

The full 720-step timeout replay 105129270 takes 22.10 s locally with a 3.402 s
maximum call, versus V203's 13.1 s worst day and timeout from step 360. A second
720-step timeout witness takes 16.85 s with a 2.904 s maximum call. The valid
fresh six-cell hard-pool screen versus the immutable V203 bundle is
`+$6,245/cell`, conditional `+$7,494`, W-L `3-2`, with 5/6 firing; this is a
small neutral research screen, not promotion evidence. Source/package identity
is exact in `logs/arena/v204_bundle_identity_38640.json`; the valid A/B screen
is `logs/arena/v204_bounded_vs_v203_fresh6_38630.json`.

The first real V204 ladder game is episode 105399683, seat 1 versus ipefix.
Both agents finished `DONE` over all 720 steps. V204 won `$108,563` to
`$59,301` (margin `+$49,262`), opened the second total quadrant on day 4 and
the third on day 12, and emitted exactly two `BUY_LAND` orders. This is direct
evidence that both land bugs are reachable in the submitted package, but one
game is not a stable win-rate estimate. The public replay summary is
`logs/planner/v204_live_56007683_initial.json`.

## Next model seam

Do not reopen paid turnover with another date/count threshold. Its value may
be positive only when the same selected action retains a dated future manifest
through harvest, or charges the robust displacement of every future standing
task it cannot guarantee. Until that multi-day witness exists, production must
keep the arm closed.

The deeper planner seam remains joint labour displacement. An animal's missing
white-box cost is not a fitted `2 * days * operation_price`; it is

`L_animal(d) = V*_d(B_d) - V*_d(B_d - DeltaRouteTurns_animal(d))`,

where the same executable task solve values the best excluded DIG, PLANT,
WATER, harvest and sale tasks. Existing feed, route and wage charges must not
be double-counted. Implement this only after the DIG loop is causally closed.

## Other confirmed facts, kept concise

- V201 moved first expansion from day 2 to day 6 on seed 38400 versus v111,
  after 33 PLANT and 18 HARVEST rather than 22/0, but own final cash fell from
  $103,644 to $58,911. Waiting has value, but a land-only timing repair is not
  sufficient. Evidence: `logs/arena/v201_vs_v199_land_diag_38400.json`.
- Animal service and weeds are one labour mechanism. On the same trace, cutting
  peak animals 18 -> 6 released 168 FEED/CARE operations and added 77 WATER,
  yet PLANT rose only 128 -> 132 and weeds worsened 23 -> 41. The task planner
  did not convert free capacity into DIG -> PLANT -> WATER.
- End-of-day auto-bank is capped by `shedCapacity=100`; all carried overflow is
  deleted. Feed, standing shed stock and overnight goods require one joint
  capacity certificate. V183's global binary auto-bank was strongly negative;
  any future repair must be per-item and preserve same-day sale/reinvestment.
- V199 runtime on one seed-38400 trace: median 2.24 ms, P99 172.76 ms, maximum
  4.44 s, 7/719 calls above 180 ms. Structural finiteness is not a latency
  bound; any promotion needs multi-state tail-latency evidence.
- Offline leader audits support route locality, same-tile bundles, staged land
  use and pricing service-heavy assets near access. They do not justify copied
  coordinates, fixed 8-sheep/4-cow targets or any identity branch.

## Architecture map

1. `state.py`: visible state extraction.
2. `opponent_model.py`, `horizon.py`: public opponent bounds/timing, no identity.
3. `strategy.py`: transparent economic plan.
4. `tasks.py`, `value.py`: exact tasks and explainable bundle values.
5. `route/router.py`: workers, carried inputs and closed Manhattan tours.
6. `capital.py`: hires, positioned assets, land and staged reinvestment.
7. `cashflow.py`: dated cash/feed/order/shed/route feasibility certificate.
8. `stackelberg.py`: worst-case margin over finite paid responses.
9. `market.py`: prerequisite buys, hires, assets and nonlinear sales.
10. `terminal.py`: constructive liquidation versus ordinary work.

The intended value model must jointly contain early-cash reinvestment value,
standing assets plus new capital's labour burden, and finite paid opponent best
responses. It must remain a concrete robust/Stackelberg action comparison, not
a prediction model or an own-cash heuristic.

## Evaluation boundary

`arena.py` has two stages:

- `--stage screen` can falsify a mechanism but can never print `IMPROVEMENT` or
  promote it;
- `--stage promotion --holdout-id ID` requires at least 288 paired cells, at
  least 100 firing cells, all episodes DONE/no errors, an unused seed block and
  unused holdout ID. Repeated formal attempts use
  `alpha_k = .05/[k(k+1)]` and record the required paired-win z value.

Promotion also requires no absolute-win regression. A 100% pool win rate means
winning every absolute game in a fresh declared block; candidate-versus-
baseline W-L-T is not the pool win rate.

```bash
cd /home/yilewang/kaggriculture
/home/yilewang/kagg-env/bin/python arena.py CANDIDATE.py \
  --baseline BASELINE.py --stage screen --seeds 6 --seed0 S \
  --pool hard --engine sim --json logs/arena/NAME.json
```

Required order: targeted tests; full unit/compile checks; isolation fingerprint;
one causal seed; fresh 18-cell screen; fresh 102-cell gate if warranted; only
then a formal unused 288-cell promotion holdout and larger real-engine checks.

## Verification and hygiene

```bash
cd /home/yilewang/kaggriculture
/home/yilewang/kagg-env/bin/python -m unittest discover -s whitebox -p 'test_*.py'
/home/yilewang/kagg-env/bin/python -m compileall -q whitebox route planner arena.py
git diff --check
rg -n 'incoming|submission|decomp|trace|opponent.*(name|file|id)' \
  whitebox --glob '!test_*' --glob '!versions/*'
```

The final pre-upload V204 full suite is 358/358 passing. Keep
formal arena JSON and causal logs. Keep tapes/opponent sources under `incoming/`
as offline witnesses only. Put new derivations in `MODEL.md`, raw measurements
in `logs/`, and update this handoff only with decisions and the next executable
seam.
