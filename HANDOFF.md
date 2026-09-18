# Kaggriculture white-box handoff

Updated: 2026-09-18. Paused for a new Codex window. The 100% target is **not complete**.

## Current best: V684

- Source: `whitebox/versions/v684_public_recertified_nonfarmers_light.py`
- Callable: `whitebox_v684_public_recertified_nonfarmers_light`
- Submission: `submission/whitebox_v684.py`
- SHA-256: `e91f993e23a0e952bb1dd8d428be7c9aafd3175115438ecf48cdb8fe059c08ec`
- Hard-18: **10/18**; full-54: **22/54**, mean margin **-$11,029.93**; zero errors.
- Evidence: `analysis/ab_v684_screen18.json`, `analysis/ab_v684_54.json`.

Do not replace V684 unless a candidate beats 10/18 (or ties with a materially
better paired margin) and then improves the full 54 games.

## Hard constraints

- Runtime may use only the current observation, public engine rules, and our
  own explicit, inspectable state/certificates.
- No opponent identity/source, seed/seat routing, replay/tape, compressed
  trajectory, hidden fitted parameters, private inventory, or imitation.
- Own at most **three total quadrants**.
- Audit every formal candidate with `scripts/audit_whitebox_runtime.py`.
- Preserve the dirty worktree: never reset, checkout, delete, or overwrite
  unrelated experiments.

## Latest diagnosis

- Multi-route seed 11: V684 hired 323 times for about 4,808 cost; the opponent
  hired 277 times for about 3,683. Earlier hire trimming regressed, so the gap
  is not simply too many workers.
- The engine resets all workers to the warehouse each day, and maturity/output
  does not advance within a day. This falsifies the prior cross-day
  pre-positioning direction.
- V684/opponent effective animal work in that matchup: cow FEED 147/187, CARE
  54/186, HARVEST 36/71, milk 108/237; wool was 174/164. The key gap is the
  cow/milk service chain, not sheep count.
- CARE was capacity-blocked 271 times for cows (22 also had HARVEST) and 395
  times for sheep (all 395 also had HARVEST). The public-rule closure is
  `FEED -> HARVEST -> CARE`: harvest frees capacity, then care builds the next
  production bonus.

## Latest candidates

- V698: FARMERS light herd changed to 7 cows. Audit/package passed; multi-route
  0/6, mean margin -16,525. Rejected.
- V699: same test with 8 cows. Audit/package passed; multi-route 0/6, mean
  margin -17,209. Rejected.
- V700: **not yet audited, packaged, or evaluated**. Source:
  `whitebox/versions/v700_public_post_harvest_animal_care.py`. In FARMERS light,
  day <= 27, it adds public-state CARE work when current jobs already contain
  animal HARVEST, and orders same-tile work as
  `FEED -> HARVEST -> CARE -> COLLECT_FERTILIZER`. It rebuilds from the current
  observation every turn and stores no future route/action tape.

## Resume here

```bash
/home/yilewang/kagg-env/bin/python scripts/audit_whitebox_runtime.py \
  --entry whitebox.versions.v700_public_post_harvest_animal_care \
  --callable whitebox_v700_public_post_harvest_animal_care

/home/yilewang/kagg-env/bin/python scripts/package_whitebox.py \
  --entry whitebox.versions.v700_public_post_harvest_animal_care \
  --callable whitebox_v700_public_post_harvest_animal_care \
  --output submission/whitebox_v700.py

/home/yilewang/kagg-env/bin/python scripts/evaluate_whitebox_pool.py \
  --candidate submission/whitebox_v700.py \
  --opponents kaggriculture-multi-route-farming-agent \
  --seeds 11 47 101 --workers 6 --output analysis/ab_v700_multi6.json
```

If V700 does not improve all three seeds, inspect the public mechanisms in
V460 (multi seed 11 margins -1,060/-1,303) and V665 (seed 101 margins
-11,890/-7,888); never route by seed or opponent identity.

The declared pool is `route/tournament.py::REFS`: nine opponents, seeds
11/47/101, both seats (54 games). `No module named pyspiel` is harmless.
