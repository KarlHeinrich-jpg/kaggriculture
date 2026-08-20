"""Policy and value networks, and the numpy export path for a submission.

TWO NETWORKS, matching the two decision cadences in `policy_api.py`:

  DailyNet  4,286 -> strategic heads (crop preference, crew delta, buy land,
            animal) plus a value head. Runs 30 times a game.
  SellNet   86 -> one 4-way head per product (offer 0 / 25 / 50 / 100% of
            holdings) plus its own value head. Runs every turn, so it is kept
            deliberately tiny.

The board goes in as a flat vector rather than through convolutions. The farm is
10x10 and the decisions here are economic rather than spatial -- which crop,
how many hands, whether to sell -- and the spatial part of the problem (which
tile a unit walks to) is already solved by the router, which the policy does not
touch. A conv tower would spend parameters on structure the scheduler handles.

SIZE IS A SHIPPING CONSTRAINT, not a taste. The submission carries its weights,
so the target is single-digit MB: at the default widths this is ~1.4M
parameters, about 2.8 MB in fp16. `export_numpy` writes exactly the arrays the
stdlib/numpy inference path needs, so nothing torch-shaped reaches Kaggle.
"""
import math

import torch
import torch.nn as nn
import torch.nn.functional as F

from dynamic.rl import policy_api as PA


def _mlp(sizes, act=nn.GELU):
    layers = []
    for i in range(len(sizes) - 1):
        layers.append(nn.Linear(sizes[i], sizes[i + 1]))
        if i < len(sizes) - 2:
            layers.append(act())
    return nn.Sequential(*layers)


class DailyNet(nn.Module):
    """Strategic head: once a day, full observation."""

    def __init__(self, obs=PA.DAILY_OBS, width=256, depth=3):
        super().__init__()
        self.trunk = _mlp([obs] + [width] * depth)
        self.norm = nn.LayerNorm(width)
        self.heads = nn.ModuleDict({
            name: nn.Linear(width, n) for name, n in PA.DAILY_HEADS.items()})
        self.value = nn.Linear(width, 1)

    def forward(self, x):
        h = self.norm(F.gelu(self.trunk(x)))
        return {k: head(h) for k, head in self.heads.items()}, self.value(h).squeeze(-1)


class SellNet(nn.Module):
    """Sell head: every turn, market scalars only.

    This is the network that matters most. The branch it replaces offers 79% of
    all units we sell, and a single CONSTANT in it is worth 88.6% paired win
    rate (HANDOFF section 31) -- so a state-dependent policy here has the most
    headroom of any decision the scheduler makes.
    """

    def __init__(self, obs=PA.SELL_OBS, width=128, depth=2):
        super().__init__()
        self.trunk = _mlp([obs] + [width] * depth)
        self.norm = nn.LayerNorm(width)
        self.head = nn.Linear(width, len(PA.PRODUCTS) * len(PA.SELL_LEVELS))
        self.value = nn.Linear(width, 1)

    def forward(self, x):
        h = self.norm(F.gelu(self.trunk(x)))
        logits = self.head(h).view(*x.shape[:-1], len(PA.PRODUCTS),
                                   len(PA.SELL_LEVELS))
        return logits, self.value(h).squeeze(-1)


class TorchPolicy(PA.Policy):
    """Runs both nets on CPU inside a rollout worker.

    `explore=True` samples and records log-probs for PPO; `explore=False` takes
    the argmax, which is what an evaluation or a submission does.
    """

    def __init__(self, daily: DailyNet, sell: SellNet, explore=True, seed=0):
        self.dnet, self.snet = daily, sell
        self.explore = explore
        self.gen = torch.Generator().manual_seed(seed)
        self.traj = {"daily": [], "sell": []}

    def reset(self):
        self.traj = {"daily": [], "sell": []}

    @torch.no_grad()
    def daily(self, obs_vec):
        x = torch.tensor(obs_vec, dtype=torch.float32)
        logits, v = self.dnet(x)
        picks, logps = {}, 0.0
        for name, lg in logits.items():
            p = F.softmax(lg, dim=-1)
            if self.explore:
                i = int(torch.multinomial(p, 1, generator=self.gen).item())
            else:
                i = int(torch.argmax(p).item())
            picks[name] = i
            logps = logps + float(torch.log(p[i] + 1e-9))
        self.traj["daily"].append((obs_vec, picks, logps, float(v)))
        crop_logits = logits["crop_pref"]
        w = F.softmax(crop_logits, dim=-1)
        return PA.Decision(
            crop_pref={c: float(w[i]) * len(PA.CROPS) for i, c in enumerate(PA.CROPS)},
            crew_delta=PA.CREW_DELTAS[picks["crew_delta"]],
            buy_land=bool(picks["buy_land"]),
            animal=PA.ANIMAL_CHOICES[picks["animal"]],
        )

    @torch.no_grad()
    def sell(self, market_vec, holdings):
        x = torch.tensor(market_vec, dtype=torch.float32)
        logits, v = self.snet(x)
        p = F.softmax(logits, dim=-1)
        if self.explore:
            idx = torch.multinomial(p, 1, generator=self.gen).squeeze(-1)
        else:
            idx = torch.argmax(p, dim=-1)
        lp = float(torch.log(p[torch.arange(len(PA.PRODUCTS)), idx] + 1e-9).sum())
        self.traj["sell"].append((market_vec, idx.tolist(), lp, float(v)))
        return {item: PA.SELL_LEVELS[int(idx[i])]
                for i, item in enumerate(PA.PRODUCTS)}


def n_params(*mods):
    return sum(p.numel() for m in mods for p in m.parameters())


def export_numpy(daily: DailyNet, sell: SellNet, path):
    """Write fp16 weights for the stdlib/numpy inference path.

    Kaggle runs the submission without torch, so the shipped agent reimplements
    the forward pass in numpy against exactly these arrays.
    """
    import numpy as np
    out = {}
    for tag, mod in (("d", daily), ("s", sell)):
        for k, v in mod.state_dict().items():
            out[f"{tag}.{k}"] = v.detach().cpu().numpy().astype(np.float16)
    np.savez_compressed(path, **out)
    return sum(a.nbytes for a in out.values())


# --------------------------------------------------------------- numpy path

class NumpyPolicy(PA.Policy):
    """The same forward pass in raw numpy, for rollouts AND for the submission.

    Measured: a SellNet forward costs 1,917 us under torch and 25 us here -- 77x
    -- because torch pays a Python dispatch and a kernel launch per op and these
    tensors are 128 elements wide. Over a game that is 1.409 s of policy
    overhead against 0.044 s, which roughly halves the cost of every rollout.

    It is also the path Kaggle needs: the submission runs without torch, so the
    shipped agent must reimplement the forward against exported arrays anyway.
    Using it in training too means the thing being trained is the thing being
    shipped, with no second implementation to diverge.
    """

    def __init__(self, weights, explore=True, seed=0):
        import numpy as np
        self.np = np
        self.W = {k: np.asarray(v, dtype=np.float32) for k, v in weights.items()}
        self.explore = explore
        self.rng = np.random.default_rng(seed)
        self.traj = {"daily": [], "sell": []}

    def reset(self):
        self.traj = {"daily": [], "sell": []}

    def _gelu(self, h):
        return h * 0.5 * (1.0 + self.np.tanh(0.7978845608 * (h + 0.044715 * h ** 3)))

    def _layernorm(self, h, tag):
        m, v = h.mean(-1, keepdims=True), h.var(-1, keepdims=True)
        return (h - m) / self.np.sqrt(v + 1e-5) * self.W[f"{tag}.norm.weight"] \
            + self.W[f"{tag}.norm.bias"]

    def _trunk(self, x, tag, depth):
        h = x
        for i in range(depth):
            li = 2 * i
            h = h @ self.W[f"{tag}.trunk.{li}.weight"].T + self.W[f"{tag}.trunk.{li}.bias"]
            if i < depth - 1:
                h = self._gelu(h)
        return self._layernorm(self._gelu(h), tag)

    def _softmax(self, z):
        z = z - z.max(-1, keepdims=True)
        e = self.np.exp(z)
        return e / e.sum(-1, keepdims=True)

    def _pick(self, p):
        if not self.explore:
            return int(p.argmax())
        return int(self.rng.choice(len(p), p=p / p.sum()))

    def daily(self, obs_vec):
        x = self.np.asarray(obs_vec, dtype=self.np.float32)
        h = self._trunk(x, "d", 3)
        picks, logp = {}, 0.0
        for name in PA.DAILY_HEADS:
            z = h @ self.W[f"d.heads.{name}.weight"].T + self.W[f"d.heads.{name}.bias"]
            p = self._softmax(z)
            i = self._pick(p)
            picks[name] = i
            logp += float(self.np.log(p[i] + 1e-9))
        v = float((h @ self.W["d.value.weight"].T + self.W["d.value.bias"])[0])
        self.traj["daily"].append((obs_vec, picks, logp, v))
        zc = h @ self.W["d.heads.crop_pref.weight"].T + self.W["d.heads.crop_pref.bias"]
        w = self._softmax(zc)
        return PA.Decision(
            crop_pref={c: float(w[i]) * len(PA.CROPS) for i, c in enumerate(PA.CROPS)},
            crew_delta=PA.CREW_DELTAS[picks["crew_delta"]],
            buy_land=bool(picks["buy_land"]),
            animal=PA.ANIMAL_CHOICES[picks["animal"]],
        )

    def sell(self, market_vec, holdings):
        x = self.np.asarray(market_vec, dtype=self.np.float32)
        h = self._trunk(x, "s", 2)
        z = (h @ self.W["s.head.weight"].T + self.W["s.head.bias"]).reshape(
            len(PA.PRODUCTS), len(PA.SELL_LEVELS))
        p = self._softmax(z)
        idx, logp = [], 0.0
        for i in range(len(PA.PRODUCTS)):
            j = self._pick(p[i])
            idx.append(j)
            logp += float(self.np.log(p[i, j] + 1e-9))
        v = float((h @ self.W["s.value.weight"].T + self.W["s.value.bias"])[0])
        self.traj["sell"].append((market_vec, idx, logp, v))
        return {item: PA.SELL_LEVELS[idx[i]] for i, item in enumerate(PA.PRODUCTS)}


def to_numpy_weights(daily, sell):
    """state_dicts -> the flat float32 dict NumpyPolicy expects."""
    out = {}
    for tag, mod in (("d", daily), ("s", sell)):
        for k, v in mod.state_dict().items():
            out[f"{tag}.{k}"] = v.detach().cpu().numpy()
    return out
