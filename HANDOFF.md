# Kaggriculture White-Box Handoff

Updated: 2026-09-18. The 100% opponent-pool target is not complete.

## Best Version

- Source: `whitebox/versions/v684_public_recertified_nonfarmers_light.py`
- Submission: `submission/whitebox_v684.py`
- Callable: `whitebox_v684_public_recertified_nonfarmers_light`
- SHA-256: `e91f993e23a0e952bb1dd8d428be7c9aafd3175115438ecf48cdb8fe059c08ec`
- Hard-18: `10/18`, mean margin `-3,893.67`
- Full-54: `22/54`, mean margin `-11,029.93`, zero runtime errors
- Keep V684 unless a candidate first ties/beats hard-18 and then improves full-54.

Pool: `route/tournament.py::REFS` (9 public opponents, seeds `11/47/101`,
both seats = 54 games).

## White-Box Contract

Use only the current observation, public engine rules, and explicit inspectable
state/certificates. Do not use opponent identity, seed/seat routing,
replays/tapes, compressed trajectories, hidden fitting, imitation, or private
opponent inventory. Keep the total owned quadrants at most three.

Audit every formal candidate with:

```bash
/home/yilewang/kagg-env/bin/python scripts/audit_whitebox_runtime.py \
  --entry whitebox.versions.<module> --callable <callable>
```

Missing `pyspiel` is harmless. Preserve unrelated dirty work; never reset,
checkout, or clean the worktree.

## Current Diagnosis

Rejected V700-V707 action-level repairs changed public state/RNG paths and
regressed paired margins. V684's main loss is not same-tile contention or
carry-free filtering: the old matcher repeatedly assigns workers to targets
that cannot meet the current day's `latest_hour`, producing many PASS turns.
The public mode switch (`default` -> `light` -> `default`) is also a likely
source of herd/service discontinuity, especially around seed 47 day 10-11.

Diagnostics:

- `scripts/diagnose_v684_router_passes.py`
- `scripts/diagnose_v684_matcher_passes.py`
- `analysis/diag_v684_*json`

Next work should test a general public-state feasibility/deadline rule and
mode-transition certificate on hard-18 first, then full-54. Never branch on
opponent, seed, seat, or named scenario.

## Submission State

This backup extends GitHub checkpoint `22ea237`.
V684 passed real-engine file-path validation. A Kaggle upload was attempted on
2026-09-18 but the API TLS connection failed during token introspection; no
submission id was returned. Retry the same command when `api.kaggle.com` is
reachable:

```bash
/home/yilewang/kagg-env/bin/kaggle competitions submit \
  -c kaggriculture -f submission/whitebox_v684.py \
  -m 'V684 certified public-state white-box baseline'
```
