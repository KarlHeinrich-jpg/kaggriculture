# White-box V361 wheat-rotation candidate

V361 keeps the audited public-state C06 policy and changes only the transparent
crop role map. It reserves twenty-two repeatable WHEAT roles across the three
allowed quadrants while preserving the global maximum of three owned
quadrants. Runtime decisions use only the current observation, public engine
rules, and the policy's own visible state; no replay, action tape, opponent
identity, fitted weight, or hidden strategy is reachable from the bundle.

## Measurements

The fixed public opponent pool contains nine opponents. Both seat orders were
tested on seeds `11`, `47`, and `101` (54 games):

| candidate | wins | mean money margin |
| --- | ---: | ---: |
| V361 wheat rotation | 13/54 | -16,699 |

The larger screen won 18/144 games (12.5%). The untouched holdout won 13/180
games (7.2%), so V361 is not a statistically qualified promotion and is not a
claim of universal strength. It is nevertheless the strongest local public-
white-box reference measured in the current C06 branch; V363--V382 all failed
their corresponding mechanism screens.

## Negative evidence

Exact same-turn sale cash, partial committed-sale cash, scalar cross-quadrant
penalties, earlier inventory banking, extra hands, smaller herds, crop-priority
guards, opening seed commitments, queue reordering, and isolated WATER/PLANT
priority changes did not improve the declared screens. The next research seam
is a single immutable public snapshot with a joint committed-work ledger for
seed, plant, water, feed, sales, crew, and durable capital.

## Verification

The recovery pass completed 429/429 unit tests, Python compilation, static
white-box runtime audit, and `git diff --check`. The packaged entry is
`submission/whitebox_v361.py`.
