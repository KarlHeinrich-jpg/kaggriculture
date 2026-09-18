# Kaggriculture white-box handoff

Updated: 2026-09-18. The 100% pool target is **not complete**.

## Best verified model

- **V684**: `whitebox/versions/v684_public_recertified_nonfarmers_light.py`
- Callable: `whitebox_v684_public_recertified_nonfarmers_light`
- Submission: `submission/whitebox_v684.py`
- SHA-256: `e91f993e23a0e952bb1dd8d428be7c9aafd3175115438ecf48cdb8fe059c08ec`
- Hard-18: **10/18**, mean margin **-$3,893.67**.
- Full-54: **22/54**, mean margin **-$11,029.93**, zero errors.
- Evidence: `analysis/ab_v684_screen18.json`, `analysis/ab_v684_54.json`.

Keep V684 unless a candidate first beats/ties its hard-18 result and then
improves the full 54 games.

## Runtime constraints

- Use only the current observation, public engine rules, and our own explicit,
  inspectable state/certificates.
- No opponent identity/source, seed/seat routing, replay/tape, compressed
  trajectory, hidden fitting, imitation, or opponent-private inventory.
- Own at most **three total quadrants**.
- Audit formal candidates with `scripts/audit_whitebox_runtime.py`.
- Preserve the dirty worktree; do not reset, checkout, or clean unrelated work.
- Python: `/home/yilewang/kagg-env/bin/python`; missing `pyspiel` is harmless.

## Latest rejected candidates

- **V700**: post-HARVEST CARE. Multi-route **0/6**, mean **-$14,952.83**.
  CARE/milk improved, but displaced higher-value crop work.
- **V701**: early HARVEST when two cow outputs are held. Multi-route **0/6**;
  hard-18 **8/18**. Invalid premise: cow capacity is six, so two is not urgent.
- **V702**: V701 only in public `default` mode. Hard-18 **10/18**, mean
  **-$3,839.11**; full-54 **22/54**, mean **-$11,386.00**. Rejected because its
  full-pool margin is worse than V684.
- **V703**: idle-cash early land purchase. Multi-route **0/6**; hard-18
  **8/18**. The 300/500 land reserve is needed for the later capital chain.

All four candidates passed audit/package checks. Evidence is in
`analysis/ab_v700_multi6.json` through `analysis/ab_v703_screen18.json`, plus
`analysis/ab_v702_54.json`.

## Resume direction

Diagnose why V684's route solver still emits many PASS actions while public,
positive-value work exists. Start with multi-route seeds 11/47/101 and
frontier seed 101 using `analysis/official_trace_v684_structural18.json`.

Instrument `_v464.router.plan_day` to compare live/selected/undone tasks,
undone reasons and carry ownership, worker route costs/budgets, PASS actions,
and repeated PICKUP/DROP. Check same-tile FEED/CARE/HARVEST costing, shared
stock constraints, carry-blocked idle refills, and duplicated pickup/bank-tail
costs. Any repair must be a general current-task feasibility rule, never a
scenario, seed, opponent, or action-sequence route.

The declared pool is `route/tournament.py::REFS`: nine opponents, seeds
11/47/101, both seats (54 games).
