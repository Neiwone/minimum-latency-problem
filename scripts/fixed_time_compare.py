"""Paired comparison of fixed-time checkpoints written by
run_experiments.py --mode fixed-time.

Reads scripts/fixed_time_<T>s.json and reports, for every solver in the
file, its paired result against a chosen baseline over whichever
(instance, seed) pairs both of them completed. Unlike the report built
into run_experiments.py this works on a partial checkpoint, so a batch
can be read while it is still running.

  python3 scripts/fixed_time_compare.py 30 mdm_gils_rvnd
"""
import json
import math
import statistics
import sys
from collections import defaultdict
from pathlib import Path


def sign_test_p(wins: int, losses: int) -> float:
    n = wins + losses
    if n == 0:
        return 1.0
    k = min(wins, losses)
    return min(1.0, 2 * sum(math.comb(n, i) for i in range(k + 1)) / (2 ** n))


def load(path: Path):
    raw = json.loads(path.read_text())
    runs = defaultdict(dict)          # (instance, seed) -> solver -> record
    solvers, instances = [], []
    for key, rec in raw.items():
        inst, solver, seed = key.split("|")
        runs[(inst, int(seed))][solver] = rec
        if solver not in solvers:
            solvers.append(solver)
        if inst not in instances:
            instances.append(inst)
    return runs, solvers, instances


def compare(runs, instances, baseline, solver):
    """-> per-instance rows + aggregate, over pairs both solvers finished."""
    rows, agg_rel, agg = [], [], [0, 0, 0]
    for inst in instances:
        rel, w, t, l, tb, ts = [], 0, 0, 0, [], []
        for (i, seed), by_solver in sorted(runs.items()):
            if i != inst:
                continue
            if baseline not in by_solver or solver not in by_solver:
                continue
            cb = by_solver[baseline]["cost"]
            cs = by_solver[solver]["cost"]
            rel.append((cs - cb) / cb * 100.0)
            tb.append(by_solver[baseline]["time_ms"] / 1000.0)
            ts.append(by_solver[solver]["time_ms"] / 1000.0)
            if cs < cb:
                w += 1
            elif cs > cb:
                l += 1
            else:
                t += 1
        if not rel:
            continue
        rows.append((inst, len(rel), statistics.mean(rel), w, t, l,
                     sign_test_p(w, l), statistics.mean(tb), statistics.mean(ts)))
        agg_rel += rel
        agg[0] += w; agg[1] += t; agg[2] += l
    if not agg_rel:
        return rows, None
    return rows, (len(agg_rel), statistics.mean(agg_rel), agg[0], agg[1], agg[2],
                  sign_test_p(agg[0], agg[2]))


def main():
    arg = sys.argv[1] if len(sys.argv) > 1 else "30"
    baseline = sys.argv[2] if len(sys.argv) > 2 else "mdm_gils_rvnd"
    path = Path(arg) if arg.endswith(".json") else Path("scripts") / f"fixed_time_{arg}s.json"

    runs, solvers, instances = load(path)
    print(f"{path}  ({sum(len(v) for v in runs.values())} runs)  baseline: {baseline}\n")

    summary = []
    for solver in solvers:
        if solver == baseline:
            continue
        rows, aggregate = compare(runs, instances, baseline, solver)
        if not aggregate:
            continue
        print(f"--- {solver} vs {baseline} ---")
        print(f"{'instance':10s} {'N':>3s} {'mean_rel%':>10s} {'w/t/l':>9s} "
              f"{'p':>7s} {'t_base':>7s} {'t_sol':>7s}")
        for inst, n, mrel, w, t, l, p, tb, ts in rows:
            print(f"{inst:10s} {n:3d} {mrel:+10.3f} {f'{w}/{t}/{l}':>9s} "
                  f"{p:7.3f} {tb:7.1f} {ts:7.1f}")
        n, mrel, w, t, l, p = aggregate
        print(f"{'AGG':10s} {n:3d} {mrel:+10.3f} {f'{w}/{t}/{l}':>9s} {p:7.4f}\n")
        summary.append((mrel, p, solver, n, w, t, l))

    print("=" * 72)
    print(f"{'ranking (most negative mean_rel% = best)':45s} {'N':>3s} {'w/t/l':>9s} {'p':>7s}")
    for mrel, p, solver, n, w, t, l in sorted(summary):
        flag = " *" if p < 0.05 and mrel < 0 else ""
        print(f"{solver:38s} {mrel:+7.3f} {n:3d} {f'{w}/{t}/{l}':>9s} {p:7.4f}{flag}")


if __name__ == "__main__":
    main()
