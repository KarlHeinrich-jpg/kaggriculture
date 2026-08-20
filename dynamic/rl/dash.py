"""Live terminal dashboard for the RL run. Read-only; safe at any time.

    python dynamic/rl/dash.py            # refreshes every 20s
    python dynamic/rl/dash.py 60         # every 60s
    python dynamic/rl/dash.py 0          # print once and exit

WHY IT SPLITS SELF-PLAY FROM POOL. A blended win rate is unreadable here. A
policy frozen at the scheduler identity scores 0.6*50% + 0.4*0% = 30% overall,
and the self-play share of a 96-episode batch varies by about +-5 episodes
(sd = sqrt(96*0.6*0.4) = 4.8), so the blend alone swings several points. That
produced a spurious "win rate UP, t=+3.94" reading over 150 iterations in which
nothing was learned at all.

Split apart the question is direct:

    SELF   is the policy beating a frozen snapshot of itself? 50% means no.
    POOL   is it beating the reference agents? 0% is where it starts.
    p_id   how much probability still sits on "do what the scheduler would do".

The verdict line uses a t statistic, never an eyeball: one iteration's win rate
is 96 paired episodes, se about 5pp, so adjacent lines differing by 10pp are
noise.
"""
import os
import re
import statistics
import subprocess
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
LOGDIR = os.path.join(ROOT, "logs", "rl")
LOG = os.path.join(LOGDIR, "train.out")

LINE = re.compile(
    r"^iter\s+(\d+)\s+winrate\s+([\d.]+)%\s+paired\s+([-+,\d]+)\s+"
    r"reward\s+([-+.\d]+)\s+"
    r"(?:selfwr\s+([\d.nan]+)%\s+poolwr\s+([\d.nan]+)%\s+)?"
    r"p_id\s+([\d.]+)")

C = {"r": "\033[0m", "b": "\033[1m", "dim": "\033[2m", "g": "\033[32m",
     "y": "\033[33m", "red": "\033[31m", "cy": "\033[36m"}


def parse():
    rows = []
    if not os.path.exists(LOG):
        return rows
    with open(LOG, errors="ignore") as fh:
        for ln in fh:
            m = LINE.match(ln.strip())
            if not m:
                continue
            f = lambda s: float(s) if s and s != "nan" else float("nan")  # noqa: E731
            rows.append({"it": int(m.group(1)), "wr": float(m.group(2)),
                         "paired": float(m.group(3).replace(",", "")),
                         "reward": float(m.group(4)),
                         "self": f(m.group(5)), "pool": f(m.group(6)),
                         "pid": float(m.group(7))})
    return rows


def spark(vals, lo=None, hi=None, width=48):
    if not vals:
        return ""
    ch = "▁▂▃▄▅▆▇█"
    v = vals[-width:]
    lo = min(v) if lo is None else lo
    hi = max(v) if hi is None else hi
    if hi - lo < 1e-9:
        return ch[3] * len(v)
    return "".join(ch[min(7, int(7 * (x - lo) / (hi - lo)))] for x in v)


def trend(rows, key):
    """(delta, se, t) comparing the opening third against the closing third."""
    vals = [r[key] for r in rows if r[key] == r[key]]
    if len(vals) < 12:
        return None
    k = min(len(vals) // 3, 80)
    a, b = vals[:k], vals[-k:]
    d = statistics.mean(b) - statistics.mean(a)
    se = ((statistics.pstdev(a) / len(a) ** 0.5) ** 2
          + (statistics.pstdev(b) / len(b) ** 0.5) ** 2) ** 0.5
    return d, se, (d / se if se > 1e-9 else 0.0)


def verdict(t):
    if t is None:
        return f"{C['dim']}not enough data{C['r']}"
    d, se, tv = t
    if tv > 2:
        return f"{C['g']}UP   {d:+8.1f}  t {tv:+5.2f}{C['r']}"
    if tv < -2:
        return f"{C['red']}DOWN {d:+8.1f}  t {tv:+5.2f}{C['r']}"
    return f"{C['y']}flat {d:+8.1f}  t {tv:+5.2f}{C['r']}"


def render():
    rows = parse()
    out = []
    A = out.append
    A(f"{C['b']}RL training — Kaggriculture{C['r']}    "
      f"{C['dim']}{time.strftime('%Y-%m-%d %H:%M:%S')}{C['r']}")
    A("")
    alive = subprocess.run(["pgrep", "-f", "dynamic.rl.tr" + "ain"],
                           capture_output=True, text=True).stdout.split()
    state = (f"{C['g']}RUNNING{C['r']} ({len(alive)} procs)" if alive
             else f"{C['red']}NOT RUNNING{C['r']}")
    A(f"  status   {state}")
    if not rows:
        A(f"  {C['dim']}no iterations logged yet{C['r']}")
        return "\n".join(out)

    last = rows[-1]
    A(f"  iters    {len(rows)}   latest {last['it']}")
    A("")
    # 'now' is ONE iteration -- 96 paired episodes, se ~5pp on a win rate. It
    # swung 12% to 100% on consecutive iterations while the 50-iteration mean
    # sat near 50, and reading the single value as the state of the run is
    # exactly the mistake this dashboard exists to prevent. mean50 is the column
    # to read; 'now' is kept only to show the run is alive.
    A(f"  {C['b']}{'':<10}{C['dim']}{'now*':>8}{C['r']}{C['b']}{'mean50':>9}   "
      f"last 48 iterations{C['r']}")

    def line(label, key, fmt="{:.1f}%"):
        vals = [r[key] for r in rows if r[key] == r[key]]
        if not vals:
            return
        m50 = statistics.mean(vals[-50:])
        A(f"  {label:<10}{C['dim']}{fmt.format(vals[-1]):>8}{C['r']}"
          f"{fmt.format(m50):>9}   {C['cy']}{spark(vals)}{C['r']}")

    line("SELF wr", "self")
    line("POOL wr", "pool")
    line("paired", "paired", "{:+,.0f}")
    line("p_id", "pid", "{:.3f}")
    A("")
    A(f"  {C['b']}trend (first third vs last third){C['r']}")
    for label, key in (("self-play wr", "self"), ("pool wr", "pool"),
                       ("paired margin", "paired")):
        A(f"    {label:<16}{verdict(trend(rows, key))}")
    A("")

    # --- the two failure modes, stated plainly
    pid = last["pid"]
    sw = [r["self"] for r in rows if r["self"] == r["self"]]
    A(f"  {C['b']}diagnosis{C['r']}")
    if pid > 0.985 and len(rows) > 120:
        A(f"    {C['y']}p_id {pid:.3f} after {len(rows)} iters: the policy has not "
          f"moved.{C['r']}")
        A(f"    {C['dim']}The KL leash is holding it at the scheduler identity. "
          f"Nothing is being learned.{C['r']}")
    elif sw and statistics.mean(sw[-30:]) < 45:
        A(f"    {C['red']}self-play win rate {statistics.mean(sw[-30:]):.1f}% — the "
          f"policy is LOSING to a frozen copy of itself.{C['r']}")
        A(f"    {C['dim']}It is moving in a harmful direction: the leash is too "
          f"loose, or the advantage is noise.{C['r']}")
    elif sw and statistics.mean(sw[-30:]) > 55:
        A(f"    {C['g']}self-play win rate {statistics.mean(sw[-30:]):.1f}% — "
          f"beating its own snapshot. This is real improvement.{C['r']}")
    else:
        A(f"    {C['dim']}self-play near 50% and p_id {pid:.3f}: drifting without a "
          f"clear direction yet.{C['r']}")
    A("")
    A(f"  {C['dim']}* 'now' is a single 96-episode iteration (se ~5pp) -- read "
      f"mean50, not now.{C['r']}")
    A(f"  {C['dim']}baseline to beat: SHIPPED tape+market is +80,210 paired above "
      f"the RL start point.{C['r']}")
    A(f"  {C['dim']}final scores land in logs/rl/RESULTS.md when the run ends.{C['r']}")
    return "\n".join(out)


def main():
    every = float(sys.argv[1]) if len(sys.argv) > 1 else 20.0
    if every <= 0:
        print(render())
        return
    try:
        while True:
            sys.stdout.write("\033[H\033[J" + render() + "\n")
            sys.stdout.flush()
            time.sleep(every)
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
