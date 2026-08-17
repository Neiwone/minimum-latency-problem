"""Aggregate/analyze scripts/h1_3way_results.json (fixed vs stagnation vs distance)."""
import json
import math
import statistics
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def sign_test_p(wins, losses):
    n = wins + losses
    if n == 0:
        return 1.0
    k = min(wins, losses)
    p_le_k = sum(math.comb(n, i) for i in range(0, k + 1)) / (2 ** n)
    return min(1.0, 2 * p_le_k)


def summarize(rows, cost_key, time_key, label):
    cf = [r["cost_fixed"] for r in rows]
    cx = [r[cost_key] for r in rows]
    tf = [r["time_fixed_ms"] for r in rows]
    tx = [r[time_key] for r in rows]

    diffs = [f - x for f, x in zip(cf, cx)]
    rel_diffs = [d / f * 100 for d, f in zip(diffs, cf)]

    wins = sum(1 for d in diffs if d > 0)
    losses = sum(1 for d in diffs if d < 0)
    p = sign_test_p(wins, losses)

    mean_rel = statistics.mean(rel_diffs)
    mean_tf = statistics.mean(tf)
    mean_tx = statistics.mean(tx)
    time_overhead = (mean_tx - mean_tf) / mean_tf * 100

    return wins, len(rows) - wins - losses, losses, p, mean_rel, time_overhead


def main():
    path = PROJECT_ROOT / "scripts" / "h1_3way_results.json"
    results = json.load(open(path))

    by_instance = {}
    for r in results:
        by_instance.setdefault(r["instance"], []).append(r)

    print(f"{'instance':10} {'n':>3} | {'stagn diff%':>11} {'w/t/l':>7} {'p':>6} {'time+%':>7} | "
          f"{'dist diff%':>10} {'w/t/l':>7} {'p':>6} {'time+%':>7}")

    for instance, rows in by_instance.items():
        ws, ts, ls, ps, mrs, tos = summarize(rows, "cost_adaptive", "time_adaptive_ms", "stagnation")
        wd, td, ld, pd_, mrd, tod = summarize(rows, "cost_distance", "time_distance_ms", "distance")

        print(f"{instance:10} {len(rows):3d} | {mrs:11.3f} {ws}/{ts}/{ls:<4} {ps:6.3f} {tos:7.1f} | "
              f"{mrd:10.3f} {wd}/{td}/{ld:<4} {pd_:6.3f} {tod:7.1f}")


if __name__ == "__main__":
    main()
