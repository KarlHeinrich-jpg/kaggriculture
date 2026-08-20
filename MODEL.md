# Kaggriculture — mathematical model

Everything here is derived from the engine source
(`kaggle_environments/envs/kaggriculture/kaggriculture.py`, v1.32.7), not from
the competition write-up. Where a quantity is verified against the engine the
verification is stated; where a coefficient is fitted, the calibration data is
given.

Implementation map:

| section | module |
|---|---|
| 2–4 market curve, marginal value | `dynamic/market_model.py` |
| 5 opponent state | `dynamic/opp_state.py` |
| 6 yields, opportunity cost | `dynamic/opportunity.py` |
| 7–9 ENPV, knapsack, shadow price | `dynamic/enpv.py` |
| 10 task value | `dynamic/task_value.py` |
| 12 sale timing, order queue | `dynamic/market_timing.py` |
| 13 fitted opponent supply | `dynamic/opp_predict.py` |
| 14 spatial feasibility | `dynamic/spatial.py` |

---

## 1. Notation and verified engine constants

$$
T = 30 \text{ days}, \qquad H = 24 \text{ turns/day}, \qquad
\text{Cap}_{\text{shed}} = 100, \qquad P_{\text{floor}} = \$1
$$

$$
I_0 = 10{,}000 \quad\text{(market baseline inventory, per product)}
$$

Hiring the $n$-th hand on a day costs $\mathrm{fib}(n)$ with $\mathrm{fib} = 1,1,2,3,5,8,\dots$

$$
C_{\text{hire}}(n) = \mathrm{fib}(n), \qquad
C_{\text{crew}}(k) = \sum_{n=0}^{k-1}\mathrm{fib}(n)
$$

Crop table (engine `CROPS`), where $f$ = `first_yield_day`, $m$ = `max_yield_day`,
$\iota$ = `interval`, $Y_{\max}$ = `max_yield`:

| crop | seed | $f$ | $m$ | $\iota$ | $Y_{\max}$ | ongoing |
|---|---|---|---|---|---|---|
| WHEAT | 10 | 2 | 4 | 0 | 6 | no |
| CARROT | 20 | 2 | 3 | 0 | 4 | no |
| TOMATO | 50 | 8 | 8 | 1 | 4 | yes |
| STRAWBERRY | 100 | 10 | 10 | 2 | 4 | yes |
| MELON | 80 | 10 | 12 | 0 | 6 | no |

Animal table (engine `ANIMALS`):

| animal | cost | $f$ | $\iota$ | product | structure |
|---|---|---|---|---|---|
| GOOSE | 300 | 4 | 1 | EGG | COOP |
| COW | 400 | 8 | 2 | MILK | PASTURE |
| SHEEP | 500 | 6 | 3 | WOOL | PASTURE |

Feeding costs exactly **1 WHEAT per animal per day** (engine line 510).

---

## 2. Market price

For product $i$ with base $b_i$, scale $T_i$, shape functions $f^-_i, f^+_i$ and
targets $\tau^-_i, \tau^+_i$:

$$
P_i(q) \;=\; \max\!\Big(P_{\text{floor}},\;
\operatorname{round}\big(\tilde P_i(q)\big)\Big)
$$

$$
\tilde P_i(q) \;=\;
\begin{cases}
b_i + A^-_i \, f^-_i(I_0 - q) & q < I_0 \\[4pt]
b_i & q = I_0 \\[4pt]
b_i - A^+_i \, f^+_i(q - I_0) & q > I_0
\end{cases}
$$

with amplitudes derived so that selling $T_i$ units moves the price by
$\tau_i \cdot b_i$:

$$
A^{\pm}_i \;=\; \frac{\tau^{\pm}_i \, b_i}{f^{\pm}_i(T_i)}
$$

Shape functions:

$$
f(x) \in \Big\{\, x,\;\; x^2,\;\; \sqrt{x},\;\; \ln(1+x),\;\; \log_{10}(1+x),\;\;
\underbrace{u + \gamma\max(0, u-1)^2}_{\text{hinge},\; u = x/T,\; \gamma = 8} \,\Big\}
$$

**Verified:** `market_model.price` reproduces the engine's `market_price`
exactly — 0 mismatches over 9 products $\times$ 4,001 inventory levels.

Parameters (engine `MARKET_PARAMS`):

| $i$ | $b_i$ | $T_i$ | $f^-_i$ | $\tau^-_i$ | $f^+_i$ | $\tau^+_i$ |
|---|---|---|---|---|---|---|
| WHEAT | 25 | 400 | sqrt | 0.80 | log | 0.20 |
| CARROT | 35 | 450 | hinge | 1.00 | sqrt | 0.70 |
| TOMATO | 60 | 200 | hinge | 0.40 | sqrt | 0.60 |
| STRAWBERRY | 120 | 100 | sqrt | 0.70 | linear | 1.60 |
| MELON | 250 | 300 | log | 0.20 | sq | 3.60 |
| EGG | 50 | 332 | hinge | 0.40 | log | 0.20 |
| MILK | 160 | 122 | sqrt | 0.60 | linear | 1.60 |
| WOOL | 200 | 105 | log | 0.20 | sq | 3.20 |
| FERTILIZER | 100 | 200 | linear | 0.40 | linear | 0.40 |

### 2.1 Slope

$$
\big|P_i'(q)\big| \;=\;
\begin{cases}
A^-_i \,\big(f^-_i\big)'(I_0 - q) & q < I_0 \\[4pt]
A^+_i \,\big(f^+_i\big)'(q - I_0) & q > I_0
\end{cases}
\qquad\text{and } 0 \text{ once } P_i(q) = P_{\text{floor}}
$$

A floored book records no sale (engine line 659), so it cannot be pushed lower.

### 2.2 Depth to the floor

$$
Q^{\text{cap}}_i \;=\; \min\{\, q \ge 0 : P_i(I_0 + q) = P_{\text{floor}} \,\}
$$

| $i$ | MELON | FERTILIZER | WOOL | MILK | STRAWBERRY | EGG | WHEAT |
|---|---|---|---|---|---|---|---|
| $Q^{\text{cap}}_i$ | 158 | 493 | 59 | 76 | 62 | $\infty$ | $\infty$ |

---

## 3. Town demand

A shop instance consumes each of its products every `SHOP_INTERVAL` $=4$ steps,
doubled if the shop sells a single product; the town centre consumes one of
every product except FERTILIZER every `CENTER_INTERVAL` $=24$ steps.

$$
d_i(\mathcal{S}) \;=\; \frac{H}{4}\sum_{s \in \mathcal{S}} \mathbb{1}[\,i \in \text{prod}(s)\,]\cdot
\big(2 - \mathbb{1}[\,|\text{prod}(s)| > 1\,]\big) \;+\; \mathbb{1}[\, i \ne \text{FERTILIZER} \,]
$$

in units per **day**, and remaining season demand

$$
D_i(t,\mathcal{S}) \;=\; d_i(\mathcal{S}) \cdot (T - t)
$$

### 3.1 The recovery ratio decides which books can be suppressed

$$
\rho_i \;=\; \frac{\text{season drain}_i}{Q^{\text{cap}}_i}
$$

| $i$ | drain | $Q^{\text{cap}}$ | $\rho$ | measured front-run edge $/$unit |
|---|---|---|---|---|
| MELON | 30 | 158 | **0.19** | **+24.3** |
| FERTILIZER | 0 | 493 | **0.00** | **+1.1** |
| WOOL | 246 | 59 | 4.2 | −2.2 |
| MILK | 331 | 76 | 4.4 | −2.8 |
| STRAWBERRY | 422 | 62 | 6.8 | −2.1 |

MELON appears in **no shop's product list** and FERTILIZER has no buyer at all,
so those two books never recover — and they are exactly the two where selling
first is measurably worth something. The ordering is **non-recovery**, not market
depth; depth is only correlated with it.

---

## 4. The marginal value of a sale

Market inventory is a pure accumulator: `_town_consume` subtracts the same
amount whatever we do, and each sale above the floor adds exactly one. So a unit
sold at step $s$ raises inventory by 1 for the remainder of the season, and
every later sale by **either** player clears one slope lower.

Let $N^{\text{us}}_i$ and $N^{\text{them}}_i$ be the units of $i$ each player
still has to sell after $s$. Differentiating the margin (ours minus theirs):

$$
\boxed{\;
MV_i \;=\; P_i(q) \;+\; \alpha \, \big|P_i'(q)\big| \cdot
\big(N^{\text{them}}_i - N^{\text{us}}_i\big)
\;}
$$

The face price is only the first term. The suppression term is **signed on the
difference of the two remaining supplies**:

- $N^{\text{them}} > N^{\text{us}}$ — suppress. Every unit costs them more than us.
- $N^{\text{them}} < N^{\text{us}}$ — this book is ours to sell into later; flooding it is self-harm.

This is why flooding experiments that ignored the sign measured negative
(wheat flooding $-95{,}916$, capped-book flooding $-81{,}980$).

### 4.1 Endogenous realized price

A marginal quote prices *one* more unit. An asset produces many, and each lowers
the price of the next. For selling $n$ units evenly over $\Delta$ days against
the town's drain and the opponent's expected supply $n^{\text{opp}}$:

$$
\bar P_i(n) \;=\; \frac{1}{n}\sum_{k=0}^{\Delta-1}
\tilde P_i\!\left(q_k + \tfrac{n}{2\Delta}\right)\cdot \frac{n}{\Delta},
\qquad
q_{k+1} = q_k + \frac{n + n^{\text{opp}}}{\Delta} - d_i(\mathcal{S})
$$

This is $P_{\text{realized}}(Q) = f\big(Q_{\text{ours}} + \mathbb{E}[Q_{\text{opp}}]\big)$.
Sample (18 days, opponent selling the same amount):

| $i$ | $n{=}20$ | $n{=}50$ | $n{=}100$ | $n{=}200$ | $n{=}400$ |
|---|---|---|---|---|---|
| MELON | 248 | 228 | 148 | 73 | 38 |
| STRAWBERRY | 228 | 219 | 203 | 151 | 11 |
| EGG | 55 | 54 | 51 | 43 | 41 |

A genome storing a fixed count prices all its cows identically; this does not.

---

## 5. Opponent state

Their sales are recoverable exactly. Within a step the engine settles both
players' orders and then the town's consumption, so

$$
q_i(t+1) \;=\; q_i(t) + s^{\text{us}}_i(t) + s^{\text{them}}_i(t) - \text{take}_i(t)
$$

$$
\Rightarrow\quad
s^{\text{them}}_i(t) \;=\; q_i(t+1) - q_i(t) - s^{\text{us}}_i(t) + \text{take}_i(t)
$$

Their **harvests** are recoverable exactly too. Within a day a tile's
`yield_units` can only fall, and only HARVEST lowers it:

$$
h_i \;=\; \sum_{t}\;\sum_{\text{tiles } j \text{ of } i}
\max\big(0,\; y_j(t) - y_j(t{+}1)\big)
\quad\text{(same-day pairs, plus the carried yield of a vanished tile)}
$$

Holdings then close the balance sheet:

$$
\text{held}_i \;=\; \max\big(0,\; h_i - s^{\text{them}}_i\big)
$$

subject to two corrections, both necessary:

$$
P_i = P_{\text{floor}} \;\Rightarrow\; \text{held}_i := 0
\qquad\text{(floor sales are invisible; a floored book cannot be suppressed anyway)}
$$

$$
\sum_i \text{held}_i \;\le\; \text{Cap}_{\text{shed}} + 4(1 + n_{\text{hands}})
\qquad\text{(the shed holds 100 items TOTAL; overflow is discarded nightly)}
$$

The cap alone cut MILK's drift from 267 units to 24. **The useful consequence:
the opponent can never be sitting on a hoard**, so $N^{\text{them}}$ is dominated
by what their tiles will still produce.

$$
N^{\text{them}}_i \;=\; \text{held}_i \;+\; g \cdot \Phi_i(\text{their tiles}, t)
$$

$\Phi$ is the structural forecast. Measured against their actual remaining
sales it under-reads by roughly $2.5\times$ but has **rank**: correlation
$0.66$–$0.82$ on the five products that matter, so the bias is left for the
gain $g$ to absorb. Substituting an extrapolation of their exact observed
harvest rate halves the bias and destroys the correlation (STRAWBERRY
$0.66 \to -0.00$, MELON $0.80 \to -0.04$) — kept, defaulted off.

---

## 6. Yields — exact, and the two rules are different

### 6.1 Non-ongoing (WHEAT, CARROT, MELON)

`_new_plant` seeds $y = 1$ and the nightly refresh **skips these crops
entirely**. Yield comes from WATER, and only inside a window (engine 438–443):

$$
w = \left\lceil \frac{m+1}{2} \right\rceil, \qquad
Y(t) \;=\; \min\Big(Y_{\max},\; 1 + \sigma \cdot \big|\{\,a : w \le a \le \min(m,\,T-1-t)\,\}\big|\Big)
$$

with $\sigma = 2$ if fertilized on that day, else 1. HARVEST then **deletes the
plant**, which is what lets a non-ongoing crop cycle a tile.

### 6.2 Ongoing (STRAWBERRY, TOMATO)

Yield accrues at the nightly refresh, once per $\iota$ days from $f$, and
`production_count > max_yield` stops it **permanently** (engine line 796) — so
$Y_{\max}$ is a **lifetime** cap, not merely a holding cap:

$$
N_{\text{harvest}}(t) \;=\; \min\!\left(
\left\lfloor \frac{\max(0,\; T - 1 - t - f)}{\iota} \right\rfloor + 1,\;\; Y_{\max}
\right)
$$

STRAWBERRY therefore produces exactly 4 units, at ages 10, 12, 14, 16. **Every
day a strawberry is deferred is a yield never taken, not a yield delayed** —
which is the arithmetic behind deferral measuring $-10{,}029$ to $-32{,}276$.

### 6.3 Labour

$$
H_{\text{req}}(c,t) \;=\; \underbrace{2}_{\text{PLANT}+\text{WATER}} +\;
\max(0,\; a_{\text{done}} - 1) \;+\; n_{\text{harvests}}
$$

| crop | units | unit-turns |
|---|---|---|
| WHEAT | 4 | 6 |
| CARROT | 3 | 5 |
| MELON | 6 | 14 |
| TOMATO | 4 | 16 |
| STRAWBERRY | 4 | 21 |

### 6.4 Latest useful planting day

HARVEST is gated on $f$, not on $m$ (engine line 457):

$$
t^{\text{last}}_c \;=\; T - 1 - f_c
$$

giving MELON 19 and WHEAT 27, against the agent's conservative $T-1-m$ of 17 and
25. **Both extra windows were tested and refuted** ($-1{,}546$, $t=-7.0$): they
have positive gross profit and negative net value, because a flat labour price
understates a late planting that waters daily against a shrinking crew and
finishes inside the terminal liquidation window.

---

## 7. Asset ENPV

### 7.1 Feed cost

$$
C^{\text{feed}}_i \;=\; \min\big(Q^{\text{need}}_i,\, Q^{\text{own}}_i\big)\cdot c_{\text{own}}
\;+\; \max\big(0,\; Q^{\text{need}}_i - Q^{\text{own}}_i\big)\cdot P_{\text{WHEAT}}
$$

### 7.2 Animals

An animal yields its product **and** one FERTILIZER per day unconditionally,
fed or not. `consecutive_unfed` $\ge 2$ kills; an unfed but living animal still
produces its base unit and loses only the CARE bonus. So both rations are
evaluated and the better taken:

$$
ENPV_{\text{animal}} \;=\; \max_{r \in \{\text{full},\,\text{half}\}}
\Big[\, Y^r \bar P_{\text{main}}(Y^r) + F \bar P_{\text{fert}}(F)
- C_{\text{buy}} - C^{\text{feed}}(r) - c_L H \,\Big]
$$

$$
Y^r = \frac{\sigma_r}{\iota}\,\max(0,\, T - 1 - t - f), \qquad
\sigma_{\text{full}} = 2,\;\; \sigma_{\text{half}} = 1, \qquad
F = T - 1 - t
$$

The prices $\bar P$ are the endogenous ones of §4.1, evaluated with the existing
herd's output as *prior*, so the marginal animal is charged for the book its
predecessors already filled. At 6 sheep owned the 7th scores $-118$.

### 7.3 Crops

$$
ENPV_{\text{crop}} \;=\; Y(t)\,\bar P_c\big(Y(t)\big) \;-\; C^{\text{seed}}_c \;-\; c_L H_{\text{req}}(c,t)
$$

### 7.4 Land

$$
ENPV_{\text{land}} \;=\; n_{\text{usable}} \cdot \max_c ENPV_{\text{crop}}(c,t) \;-\; C_{\text{land}}
$$

$n_{\text{usable}}$ is the tiles the crew can actually *serve*, not the 25 the
quadrant contains — the six refuted scaling experiments all assumed 25.

### 7.5 Labour

$$
ENPV_{\text{hand}} \;=\; H \cdot v_{\text{turn}} \;-\; C_{\text{hire}}(n)
$$

---

## 8. Global resource allocation

$$
V(C, L, P, t) \;=\; \max_{a \in A_{\text{feasible}}}
\Big[\, ENPV(a) \;+\; V\big(C - c_a,\; L - l_a,\; P - p_a,\; t\big) \Big]
$$

$$
ROI(a) \;=\; \frac{ENPV(a)}{Cost_{\text{upfront}}(a)}
$$

### 8.1 Ranking must follow the bottleneck, not ROI

A WHEAT tile is $ROI = 12.5$ against MELON's $11.5$ — but they consume the same
**one tile** and return \$125 against \$923, and we end seasons with \$97k
unspent. Cash has never been the binding resource. So each action is charged for
the fraction it consumes of every resource and scored per unit of that:

$$
\text{density}(a) \;=\; ENPV(a) \Big/
\left( \frac{c_a}{C} + \frac{p_a}{P} + \frac{l_a}{L} \right)
$$

Whichever resource is genuinely scarce dominates the denominator on its own, so
the ranking follows the bottleneck as it moves through the season instead of
being fixed in a genome. Greedy selection re-sorts after each pick.

### 8.2 Labour shadow price

$$
ENPV_{\text{labor}} \;=\;
\frac{V_{\text{knap}}(C,\, L + \Delta L) - V_{\text{knap}}(C,\, L) - \Delta L \cdot c_{\text{wage}}}{\Delta L}
$$

Measured behaviour: $+\$1{,}220$/day when unit-turns are the binding constraint,
and exactly $-c_{\text{wage}}$ when they are not. This is the honest replacement
for a fixed hire-budget fraction, and for the `MIN_CREW` floor that measured
$-13$k to $-52$k by hiring against work that did not exist.

### 8.3 Bundle ROI

$$
ROI_{\text{bundle}}(B) \;=\; \frac{ENPV(B)}{\sum_{a \in B} Cost_{\text{upfront}}(a)},
\qquad
ENPV(B) \;=\; \sum_{a\in B} ENPV(a) \;+\; \Delta_{\text{internal}}
$$

The one real internal trade is wheat: a wheat tile in the bundle feeds an animal
in the same bundle at no market cost.

$$
\Delta_{\text{internal}} \;=\; \min\big(Q^{\text{wheat}}_B,\; \text{animal-days}_B\big)\cdot P_{\text{WHEAT}}
$$

Everything else nets to zero, because `BUY_PRODUCT` is quoted at
$P(q-1)$ — post-buy — so a buy/sell round trip against an unchanged market
returns exactly zero. **Price suppression must be produced, never purchased.**

### 8.4 Cash reserve

$$
\text{Reserve} \;=\; \max\Big(\text{floor},\;\;
\Delta_{\text{dry}}\cdot\big[\, n_{\text{animals}}P_{\text{WHEAT}} + C_{\text{crew}}(k^{*}) \,\big]\Big),
\qquad
k^{*} = \max\!\left(k_{\text{now}},\; \left\lceil \frac{n_{\text{tiles}}}{5} \right\rceil\right)
$$

Two properties that were learned by getting them wrong:

- $k^{*}$ must be the crew the farm **will** need. Crew is sized to the current
  task list, so on day 0 it is 1 and a burn-rate reserve built from it is ~\$2.
  Spending against that buys 20 tiles by day 3 and cannot afford one hand to
  water them — the board went 20 tiles on day 3 to 8 on day 9.
- The floor is required. The agent refuses to hire while
  $\text{money} - \text{cost} < \text{SPEND\_RESERVE}$, so a reserve below that
  does not under-save, it silently disables hiring.

$5$ tiles per hand is measured, not assumed: at 63 tiles the board wants ~102
op-turns a day and the crew covering it is 12 hands of 24 turns — most of a hand
goes to travel.

---

## 9. Task value and opportunity cost

$$
V_{\text{task}} \;=\; V_{\text{self}} + V_{\text{suppress}} - V_{\text{opportunity}}
$$

$V_{\text{self}} + V_{\text{suppress}}$ are quoted together by pricing units
through $MV$ of §4 — the suppression term rides along with the correct sign.

$$
V_{\text{opportunity}}(\text{tile}, t) \;=\;
\max_{c \,\in\, \mathcal{C}_{\text{feasible}}(\text{tile},\,t)}
\mathbb{E}\big[\text{Profit}(c, \text{tile}, t)\big]
$$

$$
\mathcal{C}_{\text{feasible}}(\text{tile}, t) = \{\text{wheat}\}
\;\wedge\; \mathbb{E}[\text{Profit}(\text{wheat})] > 0
\;\;\Longrightarrow\;\;
V_{\text{opportunity}} = 0,\quad V_{\text{task}} = V^{\text{wheat}}_{\text{self}} > 0
$$

After day 19 nothing but WHEAT and CARROT can still be planted, so the feasible
set collapses, the opportunity cost vanishes, and any positive-profit crop
should be planted automatically. Windows of this shape are then found by
arithmetic rather than by hand. Instrumented, the allocator discovered:

```
MELON      -> WHEAT   days 20-27
STRAWBERRY -> WHEAT   days 20-25
STRAWBERRY -> MELON   days 18-19     (not found by hand)
anything   -> None    days 28-29
```

Survival dominates revenue absolutely — two consecutive unwatered nights make a
weed, two unfed nights and the animal escapes — so

$$
V_{\text{task}} \;=\; \Lambda + R_{\text{tile}}
\quad\text{when the task is the last thing between an asset and that threshold,}
\quad \Lambda = 10^6
$$

---

## 10. Calibration

| symbol | meaning | value | evidence |
|---|---|---|---|
| $\alpha$ | suppression trust in $MV$ | 1.0 | market layer measured inert; see §11 |
| $g$ | gain on $N^{\text{them}}$ | 1.0 | bias absorbed, rank preserved |
| $c_L$ (crops) | \$/unit-turn, allocator | **13** | flat plateau 13–17, cliff at 20 |
| $c_L$ (veto) | \$/unit-turn, ENPV veto | **8** | most stable of 8/10/13 across 3 seed sets |
| $\Delta_{\text{dry}}$ | dry-spell days | 2 | insensitive over 1–4 |
| tiles/hand | crew sizing | 5 | measured at 63 tiles |

### Measured results — paired margin vs the 6-agent pool

Both seat orders per seed, summed; a byte-identical mirror scores exactly 0.

| build | paired margin | vs session start | $t$ |
|---|---|---|---|
| session start | −80,909 | — | — |
| + late wheat (hand-coded) | −78,605 | +2,304 | 9.3 |
| + opportunity allocator | −78,044 | +2,865 | 10.7 |
| **+ ENPV veto (shipped)** | **−73,390** | **+7,519** | **8.5** |

$n = 336$ paired games, seed set disjoint from every calibration set.

---

## 11. Refuted branches

Kept so they are not re-derived. All measured with identity controls.

| change | shape | result |
|---|---|---|
| opportunity allocator | **additive** | **+2,865** |
| ENPV veto | **subtractive** | **+4,208** mean of 3 sets |
| free-argmax layout (`ALLOC_MODE=2`) | replacement | −53,163 |
| knapsack purchasing (`ENPV_BUY`) | replacement | −90,059 |
| $MV$ metering in the sell policy | replacement | −32,749 |
| true $t^{\text{last}}$ from $f$ | extension | −1,546 |
| deferring strawberry to days 8/11/14 | reordering | −10,029 / −14,860 / −32,276 |
| economic task value in the scheduler | replacement | **exactly 0** |
| raising WHEAT role priority to 0.85 | replacement | −75,378 |
| 73-tile season plan | replacement | −62,148 |

### Two structural facts behind the zeros

**The sell policy is not where selling is decided.** Attributing every unit
offered to the branch that offered it: shed-panic dump 79%, terminal dump 19%,
the price gate 2–3%. The reserve price, the front-run hold and the opponent
reserve scale together govern one sale in forty.

**Crew capacity is not a constraint, and the metric that says otherwise is
circular.** Crew is sized *to* the task list, so utilisation is pinned near 32%
whatever the portfolio (50 tiles → 35%, 85 tiles → 32%, 0 days over 100% in
either). Task value only decides what gets dropped, and nothing is dropped —
hence exactly 0. Movement is not the deficit either: we run 43% movement against
the tape's 52% and still bank half as much.

### The pattern

$$
\textbf{additive or subtractive} \;\Rightarrow\; \text{holds}
\qquad\qquad
\textbf{wholesale replacement} \;\Rightarrow\; \text{breaks}
$$

The searched genome's parameters are co-adapted. A principled subsystem dropped
in on top of them breaks that co-adaptation faster than its own correctness
repays. Every gain came from a change that acts only where the existing policy
does nothing, or that only declines. **Design new work to that shape.**

---

## 12. Sale timing and the order queue

`_process_market` runs before `_town_consume` within a step, so a sale placed at
step $s$ is quoted against the inventory *before* that step's drain and the same
sale one step later is quoted after it:

$$
q_{s+1} \;=\; q_s \;+\; (\text{our sale}) \;-\; d_{\text{tick}}(i)\cdot\mathbb{1}[\,s \bmod 4 = 0\,]
$$

Holding across a tick is therefore worth exactly the inventory that tick
removed, priced at the local slope:

$$
\text{gain}_i \;=\; \big|P_i'(q)\big| \cdot d_{\text{tick}}(i)
$$

| $i$ | $\lvert P_i' \rvert$ | $d_{\text{tick}}$ | \$/unit held | in `FRONT_RUN_ITEMS`? |
|---|---|---|---|---|
| MILK | 2.098 | 3 | 6.30 | yes |
| WOOL | 2.322 | 2 | 4.64 | yes |
| STRAWBERRY | 0.343 | 4 | 1.37 | yes |
| **MELON** | 1.200 | **0** | **0.00** | **yes — and worth nothing** |

**This ranks the books the opposite way from suppression.** Suppression wants
the books the town cannot refill ($\rho_i \to 0$); timing wants the ones it
refills hardest, because those have the large ticks. MELON is $\rho = 0.19$ —
the best book to *dump* into and the worst to *hold*, and both follow from the
same $d_{\text{tick}}(\text{MELON}) = 0$.

Holding is capped at 3 steps by the 4-step tick, so it can never become the
open-ended metering that measured $-32{,}749$.

**Measured: exactly $+0$**, at every threshold, and the order queue likewise.
The sell gate governs 2–3% of units (79% shed-panic, 19% terminal), panic
bypasses the hold, and 7 products never exhaust 10 order slots.

---

## 13. Fitted opponent supply

$$
\theta^{*} \;=\; \arg\min_{\theta}\ \sum_{(obs,\,Q)\,\in\,\mathcal{D}} \mathcal{L}\big(Q,\; g(obs;\theta)\big)
$$

Ridge least squares, solved in closed form, on eight public features: the
structural forecast, tracked holdings, the exact harvest rate, the exact sales
rate, days left, their tiles of this item, and their herd size.

$$
\hat\theta \;=\; \big(X^{\top}X + \lambda I'\big)^{-1} X^{\top} y,
\qquad I'_{00} = 0 \ \text{(the bias is not penalised)}
$$

Held out **by game**, never by row — rows from one game share its board, shop
draw and opponent:

| $i$ | model bias / $\lvert$err$\rvert$ / corr | structural bias / $\lvert$err$\rvert$ / corr |
|---|---|---|
| STRAWBERRY | −0.9 / 11.3 / **0.99** | −136.4 / 136.4 / 0.54 |
| MELON | −0.9 / 9.0 / **0.96** | −24.3 / 24.3 / 0.75 |
| MILK | 1.3 / 11.6 / **0.97** | −75.7 / 75.7 / 0.65 |
| WOOL | 0.5 / 12.5 / **0.92** | −47.7 / 48.0 / 0.80 |
| WHEAT | 16.1 / 75.1 / **0.75** | −308.1 / 308.1 / **−0.48** |

The $2.5\times$ bias is gone and correlation goes $0.54$–$0.80 \to 0.92$–$0.99$.

**And it measures $-18{,}611$ in play.** A strictly better input to a consumer
calibrated against the biased one: correcting the bias raises
$\mathbb{E}[Q_{\text{opp}}]$, which lowers $\bar P$, which lowers ENPV, which
makes the veto decline purchases it used to allow.

---

## 14. Spatial feasibility

$$
G = (V, E), \qquad D(u,v) = |u_x - v_x| + |u_y - v_y|
$$

Manhattan, because movement is unrestricted and LOCKED tiles are passable —
there is no path search anywhere in the codebase and none is needed.

$$
L'_{\text{req}}(a,w) = L_{\text{req}}(a) + D(pos_w,\, loc(a)),
\qquad
ENPV_{\text{adj}}(a,w) = ENPV(a) - D(pos_w,\, loc(a))\cdot c_{\text{step}}
$$

The anti-collapse constraint, per worker:

$$
\sum_{a \in S_w} L_{\text{req}}(a) \;+\; \text{TravelTime}(S_w) \;\le\; L_{\max},
\qquad \bigcup_w S_w = A_{\text{selected}},\quad S_i \cap S_j = \varnothing
$$

**Evaluated with the real `partition` and `build_tour`, it never binds:**

```
73 tiles, 12 workers:  served 73,  dropped 0
50 tiles, 12 workers:  served 50,  dropped 0
```

| workers | crop tiles servable | animal tiles servable |
|---|---|---|
| 8 | 65 | 37 |
| 12 | 80 | 52 |
| 16 | 100 | 67 |

So the 73-tile collapse is not a routing failure. It is the cash chain: more
tiles → more crew → crew costs cash → no cash on days 3–15 → tiles die unwatered.

The useful by-product is honest crew sizing. Counting travel, 73 tiles needs 10
workers where op-turn sizing says 4 — roughly a factor of two, which is what
`enpv.crew_needed` applies via `TILES_PER_HAND`.
