# Kaggriculture white-box handoff

Updated: 2026-09-18. The campaign is paused for a new Codex window; the 100%
target is **not** complete.

## Current best

- Source entry: `whitebox/versions/v684_public_recertified_nonfarmers_light.py`
- Callable: `whitebox_v684_public_recertified_nonfarmers_light`
- Submission: `submission/whitebox_v684.py`
- SHA-256: `e91f993e23a0e952bb1dd8d428be7c9aafd3175115438ecf48cdb8fe059c08ec`
- Hard screen: **10/18** wins, zero errors (`analysis/ab_v684_screen18.json`)
- Full declared pool: **22/54** wins, mean margin **-$11,029.93**, zero errors
  (`analysis/ab_v684_54.json`)

V684 is the strongest verified checkpoint, not a 100% solution. Do not replace
it unless a new candidate exceeds 10/18 on the hard screen or keeps the same
wins with a materially better paired margin, then improves the full 54 games.

## Non-negotiable contract

- Runtime may use only the current observation, public engine rules, and our
  own explicit state/certificates.
- No opponent identity/name/source branch, seed or seat mapping, replay/action
  tape, compressed trajectory, hidden fitted parameter, or opponent private
  inventory.
- Every rule, value, state transition, constraint, and certificate must be
  inspectable Python source.
- Own at most **three total quadrants**; never buy or plan for the fourth.
- Preserve the dirty worktree. Never reset, checkout, delete, or overwrite
  unrelated user experiments.
- Run `scripts/audit_whitebox_runtime.py` before any formal evaluation.

## What V684 does

V684 inherits the V678 public-state portfolio. The `FARMERS_MARKET` light
route keeps its carried-input solver and late crop rotation. Other light
routes are re-certified from the live public economy: if the visible rival is
no longer low-wheat/animal-heavy or wool is no longer favorable to milk, the
episode returns to the ordinary default route. The certificate uses no stored
opponent identity or future action.

## Failure evidence

The main gap is **productive route throughput**, not simply asset count.

- Failure labels over 54 games: insufficient hired/service capacity 29,
  insufficient sales turnover 16, productive land lost to weeds 9.
- In multi-route seed 11 seat 0, V684 emitted about **2,743 PASS** actions
  versus the opponent's **553**, while both finished with nine workers.
- The same game had V684/opponent effective counts of CARE 192/318 and HARVEST
  279/397. V684 made 215 PICKUP actions versus 119, indicating excess return
  trips and weak unit-level continuity.
- In frontier seed 101 seat 0, V684/opponent effective counts were PLANT
  99/197, HARVEST 228/387, and CARE 190/286.
- Evidence files: `analysis/failure_pool_v684_54.csv`,
  `analysis/trace_effective_v684_multi11_s0.json`, and
  `analysis/trace_effective_v684_frontier101_s0.json`.

Historical complete 54-game candidates collectively won only 27 of the 54
cells. No prior white-box candidate beat any of the six multi-route cells, so
combining old wrappers cannot reach 100%.

## Rejected directions

- Same-tile CARE/completion bonuses, arrived-stop retention, task exchange,
  global matching, and whole-day/receding route certificates.
- Simple herd shrinkage or unconditional extra hires/hands.
- Unconditional immediate sales, wheat liquidity cycles, and buy/sell
  arbitrage; the public market locks unit quotes and round trips net zero.
- V690-V697 are failure evidence only. V691 also fails static audit because
  its reachable module name contains the forbidden token `opening`.
- High-scoring public opponents contain encoded/precomputed action sequences;
  they may be used only as offline falsification evidence, never imported or
  imitated by production code.

## Best next seam

Investigate a short-window **public look-ahead positioning certificate**.
V684 creates work only when it is currently due, so paid workers often PASS
instead of moving toward a tile whose next service/maturity is deterministically
known from the public engine. A legal candidate may predict the next public
task time from live crop/animal fields and move an otherwise-idle unit toward
that tile, but must revalidate every turn and must not retain an action tape.

Start with one multi-route game, then both seats/seeds, then the 18-game hard
screen. Stop early on capital-path regressions.

## Reproduction

```bash
/home/yilewang/kagg-env/bin/python scripts/audit_whitebox_runtime.py \
  --entry whitebox.versions.v684_public_recertified_nonfarmers_light \
  --callable whitebox_v684_public_recertified_nonfarmers_light

/home/yilewang/kagg-env/bin/python scripts/package_whitebox.py \
  --entry whitebox.versions.v684_public_recertified_nonfarmers_light \
  --callable whitebox_v684_public_recertified_nonfarmers_light \
  --output submission/whitebox_v684.py

/home/yilewang/kagg-env/bin/python scripts/evaluate_whitebox_pool.py \
  --candidate submission/whitebox_v684.py --seeds 11 47 101 \
  --output analysis/ab_v684_54.json
```

The fixed pool is the nine entries in `route/tournament.py::REFS`, with seeds
`11, 47, 101` and both seat orders (54 games). `No module named pyspiel` is a
harmless Kaggle Environments warning.
