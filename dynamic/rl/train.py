"""PPO over the scheduler's decision points, against an opponent pool.

REWARD IS THE MATCH OUTCOME, not the margin. `publicScore` is a skill rating
driven by wins (HANDOFF section 7), and section 31 measured a change worth
win-rate t=12 whose mean margin was exactly zero -- the two objectives genuinely
disagree, and the ladder scores the first one. So terminal reward is +1 / -1 on
the paired result, with a small margin term only as a tie-breaker inside a
result, never large enough to trade a win for a bigger loss.

PAIRED EPISODES. Seat asymmetry is real here (HANDOFF rule 1: a byte-identical
mirror wins seat 0 only 15% of the time), so every rollout plays the SAME seed
from BOTH seats against the same opponent and the reward is the paired outcome.
That removes the seat term from the gradient instead of asking the network to
learn around it.

SELF-PLAY IS REQUIRED FOR THE SIGN TERM TO CARRY INFORMATION. Against the
reference pool alone the agent loses 100% of paired episodes, so sign(paired) is
a constant and only the margin term teaches anything. Playing a FROZEN SNAPSHOT
of the current policy puts the win rate at 50% by construction, which is where a
win/loss signal has the most information in it. The references stay in the mix
so the policy cannot drift into beating only itself -- that is the Lux AI
opponent-pool lesson, and it is also why the snapshot is frozen and refreshed on
a delay rather than being the live weights.

OPPONENT POOL, not pure self-play. Lux AI's lesson, and it matches the local
evidence: our pool of reference agents differs in style, and an agent tuned
against one family transfers badly. Snapshots of the training policy are added
to the pool as it improves, so it does not overfit to the newest version of
itself.

Rollouts are CPU (26 cores, ~37k games/hour); the GPU only does the update. The
nets are small enough that per-decision inference is ~1 ms, so batching them
onto a GPU would need a vectorised environment -- a rewrite with a fidelity risk
this project has repeatedly paid for.
"""
import json
import math
import multiprocessing as mp
import os
import random
import statistics
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:] = [p for p in sys.path if os.path.abspath(p or ".") not in
               (_HERE, os.path.join(ROOT, "dynamic"))]
sys.path.insert(0, ROOT)

import torch                                        # noqa: E402
import torch.nn.functional as F                     # noqa: E402

from dynamic.rl import policy_api as PA             # noqa: E402
from dynamic.rl.net import (DailyNet, SellNet, NumpyPolicy, export_numpy,     # noqa: E402
                            n_params, to_numpy_weights)

AGENT = os.path.join(ROOT, "dynamic", "rl", "agent_rl.py")
CKPT_DIR = os.path.join(ROOT, "logs", "rl")
POOL = ["kaggriculture-multi-route-farming-agent",
        "v111-8c4s-economic-core-premium-lead",
        "kaggriculture-frontier-the-soil-remembers-rain",
        "kaggriculture-3000-socre",
        "kaggriculture-rank-your-agent",
        "strong-barnyard-economist"]
_cache = {}


def _base_genome():
    from route.search import to_params
    g = json.load(open(os.path.join(ROOT, "dynamic", "best_genome3.json")))["genome"]
    p = to_params(dict(g))
    p["OPP_MODEL"] = 1
    p["SHED_PANIC_FRACTION"] = 0.40      # HANDOFF section 31
    return p


def _load_agent(genome, policy, tag):
    import importlib.util
    spec = importlib.util.spec_from_file_location(tag, AGENT)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    m.configure(genome)
    m.set_policy(policy)
    return m.agent


def _load_opp(name):
    if name not in _cache:
        import importlib.util
        p = os.path.join(ROOT, "opponents", f"{name}.py")
        spec = importlib.util.spec_from_file_location(f"opp_{name}", p)
        m = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(m)
        _cache[name] = getattr(m, "_submission_entry", None) or m.agent
    return _cache[name]


_W = {}


def _worker_init(weights, snapshot):
    # Workers run the NUMPY forward, not torch: measured 1,917 us against 25 us
    # for a SellNet call, because torch pays a Python dispatch and a kernel
    # launch per op on 128-element tensors. Over a game that is 2.72 s against
    # 1.87 s, and it is the same code path the submission has to use anyway.
    _W["weights"] = weights
    _W["snapshot"] = snapshot
    _W["genome"] = _base_genome()


def rollout(job):
    """One PAIRED episode: the same seed from both seats. Returns the two
    trajectories and the paired outcome."""
    seed, opp_name, wid = job
    from planner.simulate import Simulator
    out = []
    margins = []
    try:
        for seat in (0, 1):
            pol = NumpyPolicy(_W["weights"], explore=True,
                              seed=(seed * 7 + seat * 13 + wid) & 0x7fffffff)
            me = _load_agent(_W["genome"], pol, f"rl_{os.getpid()}_{seat}")
            if opp_name == "__self__":
                opp_pol = NumpyPolicy(_W["snapshot"], explore=True,
                                      seed=(seed * 11 + seat * 17 + wid) & 0x7fffffff)
                op = _load_agent(_W["genome"], opp_pol, f"rlopp_{os.getpid()}_{seat}")
            else:
                op = _load_opp(opp_name)
            pair = [me, op] if seat == 0 else [op, me]
            sim = Simulator.new_episode(configuration={"episodeSteps": 720}, seed=seed)
            m0, m1 = sim.run_episode(pair[0], pair[1])
            us, them = (m0, m1) if seat == 0 else (m1, m0)
            margins.append(us - them)
            out.append(pol.traj)
    except Exception:
        import traceback
        return None, traceback.format_exc()[-200:]
    paired = margins[0] + margins[1]
    # THE REWARD MUST HAVE VARIANCE, and the first version did not. It was
    #     r = sign(paired) + 0.25 * clamp(paired / 60000)
    # and against this opponent pool the agent loses every paired episode while
    # margins run near -76,000, so BOTH terms pinned: the sign at -1 and the
    # clamp at -1. Every episode returned exactly -1.25, advantages normalised
    # to zero, and PPO learned nothing -- 0.0% win rate over three iterations
    # was not a hard problem, it was no gradient at all.
    #
    # tanh keeps the margin term informative at any scale, and the divisor is
    # taken from the spread actually observed rather than guessed.
    r = (1.0 if paired > 0 else -1.0 if paired < 0 else 0.0)
    r += 0.75 * math.tanh(paired / 120000.0)
    return (out, r, paired), None


def _flatten(trajs, reward, gamma=0.999, lam=0.95):
    """GAE over each head's own sequence. The two heads act at different
    cadences, so they are advantaged separately rather than interleaved."""
    batches = {"daily": [], "sell": []}
    for traj in trajs:
        for key in ("daily", "sell"):
            seq = traj[key]
            if not seq:
                continue
            vals = [t[3] for t in seq] + [0.0]
            adv, gae = [0.0] * len(seq), 0.0
            for i in reversed(range(len(seq))):
                r = reward if i == len(seq) - 1 else 0.0
                delta = r + gamma * vals[i + 1] - vals[i]
                gae = delta + gamma * lam * gae
                adv[i] = gae
            for i, t in enumerate(seq):
                batches[key].append((t[0], t[1], t[2], adv[i], adv[i] + vals[i]))
    return batches


def ppo_update(dnet, snet, opt, batches, device, clip=0.2, epochs=3,
               vf=0.5, ent=0.01, mb=4096):
    stats = {"d_loss": 0.0, "s_loss": 0.0, "n": 0}
    for key, net in (("daily", dnet), ("sell", snet)):
        data = batches[key]
        if not data:
            continue
        obs = torch.tensor([d[0] for d in data], dtype=torch.float32, device=device)
        oldlp = torch.tensor([d[2] for d in data], dtype=torch.float32, device=device)
        adv = torch.tensor([d[3] for d in data], dtype=torch.float32, device=device)
        ret = torch.tensor([d[4] for d in data], dtype=torch.float32, device=device)
        adv = (adv - adv.mean()) / (adv.std() + 1e-6)
        if key == "daily":
            acts = {k: torch.tensor([d[1][k] for d in data], device=device)
                    for k in PA.DAILY_HEADS}
        else:
            acts = torch.tensor([d[1] for d in data], device=device)
        n = len(data)
        for _ in range(epochs):
            perm = torch.randperm(n, device=device)
            for i in range(0, n, mb):
                idx = perm[i:i + mb]
                if key == "daily":
                    logits, v = net(obs[idx])
                    lp = 0.0
                    entropy = 0.0
                    for k in PA.DAILY_HEADS:
                        ls = F.log_softmax(logits[k], dim=-1)
                        lp = lp + ls.gather(1, acts[k][idx, None]).squeeze(1)
                        entropy = entropy + -(ls.exp() * ls).sum(-1).mean()
                else:
                    logits, v = net(obs[idx])
                    ls = F.log_softmax(logits, dim=-1)
                    lp = ls.gather(2, acts[idx].unsqueeze(-1)).squeeze(-1).sum(-1)
                    entropy = -(ls.exp() * ls).sum(-1).mean()
                ratio = (lp - oldlp[idx]).exp()
                a = adv[idx]
                pl = -torch.min(ratio * a,
                                ratio.clamp(1 - clip, 1 + clip) * a).mean()
                vl = F.mse_loss(v, ret[idx])
                loss = pl + vf * vl - ent * entropy
                opt.zero_grad(set_to_none=True)
                loss.backward()
                torch.nn.utils.clip_grad_norm_(net.parameters(), 0.5)
                opt.step()
                stats[f"{key[0]}_loss"] += float(loss)
                stats["n"] += 1
    return stats


def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--iters", type=int, default=10000)
    ap.add_argument("--episodes", type=int, default=192)   # paired episodes/iter
    ap.add_argument("--workers", type=int, default=26)
    ap.add_argument("--lr", type=float, default=3e-4)
    ap.add_argument("--hours", type=float, default=48.0)
    ap.add_argument("--self_play", type=float, default=0.6,
                    help="fraction of episodes played against a frozen self")
    ap.add_argument("--snapshot_every", type=int, default=10)
    ap.add_argument("--snapshot_keep", type=int, default=5)
    args = ap.parse_args()

    os.makedirs(CKPT_DIR, exist_ok=True)
    device = "cuda" if torch.cuda.is_available() else "cpu"
    dnet, snet = DailyNet().to(device), SellNet().to(device)
    opt = torch.optim.Adam(list(dnet.parameters()) + list(snet.parameters()),
                           lr=args.lr)
    print(f"params {n_params(dnet, snet):,}  device {device}  "
          f"{args.episodes} paired episodes/iter x {args.workers} workers",
          flush=True)

    rng = random.Random(20260820)
    t0 = time.time()
    log = open(os.path.join(CKPT_DIR, "train.log"), "a")
    best = -9e9
    snapshots = []
    for it in range(args.iters):
        if time.time() - t0 > args.hours * 3600:
            print("time budget reached", flush=True)
            break
        weights = to_numpy_weights(dnet, snet)
        # A frozen self from a few iterations back. Refreshed on a delay so the
        # opponent is a fixed target within an iteration rather than a moving
        # one, which is what keeps self-play from chasing its own tail.
        if it % args.snapshot_every == 0 or not snapshots:
            snapshots.append({k: v.copy() for k, v in weights.items()})
            del snapshots[:-args.snapshot_keep]
        snapshot = snapshots[rng.randrange(len(snapshots))]
        def _pick_opp():
            return "__self__" if rng.random() < args.self_play else rng.choice(POOL)
        jobs = [(rng.randrange(10 ** 6, 2 ** 31 - 1), _pick_opp(), w)
                for w in range(args.episodes)]
        with mp.get_context("forkserver").Pool(
                args.workers, initializer=_worker_init,
                initargs=(weights, snapshot)) as pool:
            res = pool.map(rollout, jobs, chunksize=1)
        errs = [e for _, e in res if e]
        good = [r for r, e in res if e is None]
        if not good:
            print(f"iter {it}: all rollouts failed; first {errs[0]}", flush=True)
            break
        batches = {"daily": [], "sell": []}
        rewards, paireds = [], []
        for trajs, r, paired in good:
            b = _flatten(trajs, r)
            batches["daily"] += b["daily"]
            batches["sell"] += b["sell"]
            rewards.append(r)
            paireds.append(paired)
        stats = ppo_update(dnet, snet, opt, batches, device)
        wins = sum(1 for p in paireds if p > 0)
        wr = 100.0 * wins / len(paireds)
        line = (f"iter {it:>5} winrate {wr:>5.1f}%  paired {statistics.mean(paireds):>+9,.0f}  "
                f"reward {statistics.mean(rewards):>+5.2f}  "
                f"samples d{len(batches['daily']):,}/s{len(batches['sell']):,}  "
                f"{len(errs)} err  {time.time()-t0:.0f}s")
        print(line, flush=True)
        log.write(line + "\n")
        log.flush()
        if wr > best:
            best = wr
            torch.save({"daily": dnet.state_dict(), "sell": snet.state_dict(),
                        "iter": it, "winrate": wr},
                       os.path.join(CKPT_DIR, "best.pt"))
            export_numpy(dnet.cpu(), snet.cpu(), os.path.join(CKPT_DIR, "best.npz"))
            dnet.to(device)
            snet.to(device)


if __name__ == "__main__":
    main()
