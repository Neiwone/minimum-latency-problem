"""Paired comparison of fixed-time checkpoints written by
run_experiments.py --mode fixed-time.

Reads results/fixed-time/fixed_time_<T>s.json and reports, for every solver in the
file, its paired result against a chosen baseline over whichever
(instance, seed) pairs both of them completed. Unlike the report built
into run_experiments.py this works on a partial checkpoint, so a batch
can be read while it is still running.

  python3 scripts/fixed_time_compare.py 30 mdm_gils_rvnd
"""
import statistics
import sys
from pathlib import Path

from runner import load_runs
from stats import compare_pairs, pair_runs, split_key


def compare(runs, instances, baseline, solver):
    """-> per-instance rows + aggregate, over pairs both solvers finished."""
    by_inst = pair_runs(runs, baseline, solver, instances=instances)
    rows = []
    for inst, pairs in by_inst.items():
        c = compare_pairs((b["cost"], s["cost"]) for b, s in pairs)
        rows.append((inst, c.n, c.mean_rel, c.wins, c.ties, c.losses, c.p,
                     statistics.mean(b["time_ms"] / 1000.0 for b, _ in pairs),
                     statistics.mean(s["time_ms"] / 1000.0 for _, s in pairs)))
    c = compare_pairs((b["cost"], s["cost"]) for pairs in by_inst.values() for b, s in pairs)
    return rows, (c and (c.n, c.mean_rel, c.wins, c.ties, c.losses, c.p))


def main():
    arg = sys.argv[1] if len(sys.argv) > 1 else "30"
    baseline = sys.argv[2] if len(sys.argv) > 2 else "mdm_gils_rvnd"
    path = Path(arg) if arg.endswith(".json") else Path("results") / "fixed-time" / f"fixed_time_{arg}s.json"

    runs = load_runs(path)
    solvers = list(dict.fromkeys(split_key(k)[1] for k in runs))
    instances = list(dict.fromkeys(split_key(k)[0] for k in runs))
    print(f"{path}  ({len(runs)} runs)  baseline: {baseline}\n")

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
