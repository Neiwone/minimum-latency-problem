"""Aggregate/analyze scripts/h1_ab_results.json (paired fixed vs adaptive runs)."""
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


def main():
    path = PROJECT_ROOT / "scripts" / "h1_ab_results.json"
    results = json.load(open(path))

    by_instance = {}
    for r in results:
        by_instance.setdefault(r["instance"], []).append(r)

    print(f"{'instance':10} {'n':>3} {'mean_fixed':>12} {'mean_adapt':>12} {'diff%':>7} "
          f"{'win/tie/loss':>13} {'sign_p':>8} {'time_fixed_ms':>14} {'time_adapt_ms':>14} {'time+%':>7}")

    all_rel_diffs = []
    for instance, rows in by_instance.items():
        cf = [r["cost_fixed"] for r in rows]
        ca = [r["cost_adaptive"] for r in rows]
        tf = [r["time_fixed_ms"] for r in rows]
        ta = [r["time_adaptive_ms"] for r in rows]

        diffs = [f - a for f, a in zip(cf, ca)]
        rel_diffs = [d / f * 100 for d, f in zip(diffs, cf)]
        all_rel_diffs.extend(rel_diffs)

        wins = sum(1 for d in diffs if d > 0)
        losses = sum(1 for d in diffs if d < 0)
        ties = sum(1 for d in diffs if d == 0)
        p = sign_test_p(wins, losses)

        mean_fixed = statistics.mean(cf)
        mean_adapt = statistics.mean(ca)
        mean_rel = statistics.mean(rel_diffs)
        mean_tf = statistics.mean(tf)
        mean_ta = statistics.mean(ta)
        time_overhead = (mean_ta - mean_tf) / mean_tf * 100

        print(f"{instance:10} {len(rows):3d} {mean_fixed:12.1f} {mean_adapt:12.1f} {mean_rel:7.3f} "
              f"{wins:4d}/{ties:1d}/{losses:<4d} {p:8.4f} {mean_tf:14.1f} {mean_ta:14.1f} {time_overhead:7.1f}")

    print()
    print(f"overall mean relative improvement (adaptive over fixed): {statistics.mean(all_rel_diffs):.4f}%")


if __name__ == "__main__":
    main()
