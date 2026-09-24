"""
Run batches of MLP solvers, pair the runs by seed and report means,
win/tie/loss and exact sign tests. `--help` explains the modes.

Run from the project root: python3 scripts/run_experiments.py --help
The solver and instance registry is in registry.py, running a solver and
the checkpoint in runner.py, and the paired statistics in stats.py.
"""
import argparse
import os
import shutil
import statistics
import subprocess
import sys
import threading
import time
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

import runner
from registry import (CLOSED_CAPABLE, FIXED_TIME_BINARIES, INSTANCE_GROUPS, INSTANCES,
                      INST_DIR, ROOT, SALEHIPOUR_DIR, SALEHIPOUR_SIZES, SOLUTIONS_DIR, SOLVERS,
                      SolverCmd, resolve_instances, salehipour_instances,
                      supports_fixed_time)
from control import CONTROL, BatchStopped
from runner import (Checkpoint, SolutionTracker, latest_checkpoint, run_cached,
                    solver_command)
from stats import compare_pairs, pair_runs


VISUALIZER = "uv run scripts/instance_visualizer.py"


class StatusLine:
    """
    The batch progress on one terminal line, rewritten in place: what is
    running, which instance of how many, how many runs of the batch are done,
    and dots that move while a solver runs (PAUSED after Ctrl+P). Anything
    printed through status.print() goes above it. Off when stdout is not a
    terminal or with --vb, which prints every run instead.
    """
    FRAMES = ["   ", ".  ", ".. ", "..."]

    def __init__(self, n_instances: int, n_runs: int, enabled: bool = True):
        self.enabled = enabled and sys.stdout.isatty()
        self.n_instances, self.n_runs = n_instances, n_runs
        self.instance, self.runs_done, self.label = 0, 0, ""
        self._frame = 0
        self._hidden = False
        self._lock = threading.Lock()
        self._stop = threading.Event()
        self._thread = None

    def __enter__(self):
        if self.enabled:
            CONTROL.printer = self.print
            self._thread = threading.Thread(target=self._animate, daemon=True)
            self._thread.start()
        return self

    def __exit__(self, *exc):
        if self.enabled:
            self._stop.set()
            self._thread.join()
            CONTROL.printer = None
            with self._lock:
                sys.stdout.write("\r\x1b[K")
                sys.stdout.flush()

    def _draw(self):
        if self._hidden:
            return
        state = "  PAUSED" if CONTROL.paused else self.FRAMES[self._frame % len(self.FRAMES)]
        line = (f"{self.label}  instance {self.instance}/{self.n_instances}"
                f"  run {self.runs_done}/{self.n_runs}{state}")
        width = shutil.get_terminal_size().columns - 1   # a wrapped line cannot be rewritten
        sys.stdout.write("\r\x1b[K" + line[:width])
        sys.stdout.flush()

    def _animate(self):
        while not self._stop.wait(0.12):
            with self._lock:
                self._frame += 1
                self._draw()

    def update(self, label: Optional[str] = None, instance: Optional[int] = None):
        if label is not None:
            self.label = label
        if instance is not None:
            self.instance = instance
        if self.enabled:
            with self._lock:
                self._draw()

    def advance(self):
        """One more run of the batch done (or found in the checkpoint)."""
        self.runs_done += 1
        self.update()

    def print(self, *args, **kwargs):
        if not self.enabled:
            print(*args, **kwargs)
            return
        with self._lock:
            sys.stdout.write("\r\x1b[K")
            print(*args, **{**kwargs, "flush": True})
            self._draw()

    @contextmanager
    def hidden(self):
        """Take the line off screen, e.g. for an input() prompt."""
        with self._lock:
            self._hidden = True
            if self.enabled:
                sys.stdout.write("\r\x1b[K")
                sys.stdout.flush()
        try:
            yield
        finally:
            self._hidden = False


class ListSolversAction(argparse.Action):
    """--list-solvers: print every solver name with the command it runs, then exit."""

    def __init__(self, option_strings, dest, **kwargs):
        super().__init__(option_strings, dest, nargs=0, default=argparse.SUPPRESS, **kwargs)

    def __call__(self, parser, namespace, values, option_string=None):
        width = max(len(name) for name in SOLVERS)
        commands = {name: " ".join([binary] + extra) for name, (binary, extra) in SOLVERS.items()}
        cmd_width = max(len(c) for c in commands.values())
        print(f"{'solver':<{width}}  {'command':<{cmd_width}}  supports")
        for name, (binary, _) in SOLVERS.items():
            notes = []
            if binary in FIXED_TIME_BINARIES:
                notes.append("fixed-time")
            if os.path.basename(binary) in CLOSED_CAPABLE:
                notes.append("--closed")
            print(f"{name:<{width}}  {commands[name]:<{cmd_width}}  {', '.join(notes)}")
        parser.exit()


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description="""\
Run batches of MLP solvers, pair the runs by seed and report means, win/tie/loss
and exact sign tests.

Modes (--mode):
  fixed-time            every solver in --solvers gets the same wall-clock budget
                        per run (--time-limit); the first solver is the baseline.
                        The protocol behind every result in docs/.
  salehipour-benchmark  --solver, or two --solvers compared pairwise, over the
                        140-instance Salehipour set (instances/salehipour/),
                        reported per size. One run per instance.
  compare-best          --solver against the best known solutions in
                        instances/solutions/; offers to save any it beats.
  compare-solvers       two --solvers, average cost and time per instance.

Every run uses seed i for run i (1..--runs), so a batch is reproducible, and is
saved to a checkpoint as it finishes (see --checkpoint).""",
        epilog="""\
examples:
  # GILS-AM-RVND-DLB vs MDM-GILS-RVND, 100 s per run, 10 paired seeds
  python3 scripts/run_experiments.py --mode fixed-time --time-limit 100 --runs 10 \\
      --instances lin318 pr439 att532 --solvers mdm_gils_rvnd gils_am_rvnd_dlb

  # the same over every TSPLIB instance with n >= 200, resumable
  python3 scripts/run_experiments.py --mode fixed-time --time-limit 100 --runs 10 \\
      --instances tsplib-200 --solvers mdm_gils_rvnd gils_am_rvnd_dlb \\
      --checkpoint results/fixed-time/tsplib200.json

  # Salehipour benchmark
  python3 scripts/run_experiments.py --mode salehipour-benchmark --sizes 10 20 50 \\
      --solvers gils_rvnd gils_am_rvnd_dlb

  # look for new best known solutions
  python3 scripts/run_experiments.py --mode compare-best --solver gils_am_rvnd_dlb \\
      --instances eil51 st70 --runs 5 --auto-save

  # every solver name and the command it runs
  python3 scripts/run_experiments.py --list-solvers""",
    )

    parser.add_argument(
        "--mode",
        choices=["fixed-time", "salehipour-benchmark", "compare-best",
                 "compare-solvers"],
        required=True,
        help="what to run; see the list above",
    )
    parser.add_argument(
        "--list-solvers",
        action=ListSolversAction,
        help="print every solver name with the command it runs, and exit",
    )

    common = parser.add_argument_group("solvers and instances")
    common.add_argument(
        "--solver",
        choices=list(SOLVERS),
        metavar="NAME",
        help="the solver, for compare-best and salehipour-benchmark "
             "(names: --list-solvers)",
    )
    common.add_argument(
        "--solvers",
        nargs="+",
        choices=list(SOLVERS),
        metavar="NAME",
        help="the solvers to compare: two or more for fixed-time (the first is "
             "the baseline), exactly two for compare-solvers and "
             "salehipour-benchmark",
    )
    common.add_argument(
        "--instances",
        nargs="+",
        default=None,
        metavar="NAME",
        help=(
            "instances from instances/, with or without .tsp (e.g. lin318 att532), "
            "or a group: "
            + ", ".join(f"{k} ({len(v)} instances)" for k, v in INSTANCE_GROUPS.items())
            + f". Default: the INSTANCES list in this file ({', '.join(INSTANCES)}). "
            "Not used by salehipour-benchmark"
        ),
    )
    common.add_argument(
        "--runs",
        type=int,
        default=10,
        metavar="N",
        help="runs per instance and solver, with seeds 1..N (default: 10). "
             "Not used by salehipour-benchmark",
    )
    common.add_argument(
        "--closed",
        action="store_true",
        help=(
            "count the return to the depot in the latency (closed tour). Default "
            "is the MLP definition: a Hamiltonian path, no return. Only "
            + ", ".join(sorted(CLOSED_CAPABLE)) + " support it"
        ),
    )
    common.add_argument(
        "--checkpoint",
        metavar="FILE",
        help=(
            "JSON file every run is saved to as it finishes. If FILE exists the "
            "batch resumes from it: runs already there are reused, and a resume "
            "with a different configuration (--closed, a solver's flags, "
            "--time-limit, --iils) is refused. 'last' resumes the most recently "
            "written checkpoint of the mode under results/<mode>/. Default: a new "
            "timestamped file under results/<mode>/, printed at the start; no "
            "existing file is ever overwritten"
        ),
    )
    common.add_argument(
        "--vb",
        action="store_true",
        help="print a line for every run, with the step timings (construction, "
             "rvnd, tabu) that the solver reports, instead of the progress line",
    )

    fixed = parser.add_argument_group("fixed-time")
    fixed.add_argument(
        "--time-limit",
        type=float,
        default=None,
        metavar="SECONDS",
        help="wall-clock budget per run, the same for every solver (passed as "
             "--max-time). Required",
    )
    fixed.add_argument(
        "--iils",
        type=int,
        default=10,
        metavar="N",
        help=(
            "I_ILS for every solver that does not set its own (default: 10). Keep "
            "it small enough that several restarts fit in --time-limit: mining "
            "(mdm_gils_rvnd) and adaptive memory (gils_am_rvnd) only act at "
            "restarts, and with too few they degenerate to plain GILS-RVND. See "
            "docs/experiments/fixed-time-protocol.md"
        ),
    )
    fixed.add_argument(
        "--salehipour-sizes",
        type=int,
        nargs="+",
        choices=SALEHIPOUR_SIZES,
        default=None,
        metavar="N",
        help="also run these whole Salehipour tiers (20 instances each), e.g. "
             "--salehipour-sizes 500 1000. Given alone, replaces --instances",
    )

    saleh = parser.add_argument_group("salehipour-benchmark")
    saleh.add_argument(
        "--sizes",
        type=int,
        nargs="+",
        choices=SALEHIPOUR_SIZES,
        default=SALEHIPOUR_SIZES,
        metavar="N",
        help=f"instance sizes to run (default: all of {' '.join(map(str, SALEHIPOUR_SIZES))})",
    )

    best = parser.add_argument_group("compare-best")
    best.add_argument(
        "--auto-save",
        action="store_true",
        help="save a new best solution without asking",
    )
    best.add_argument(
        "--plot",
        action="store_true",
        help="plot the best route found on each instance",
    )

    return parser.parse_args()


def open_checkpoint(args, mode: str, stem: str, params: Dict,
                    solvers: Dict[str, SolverCmd]) -> Checkpoint:
    """--checkpoint resumes (or starts) that file, and --checkpoint last the
    newest checkpoint of this mode. Without it every batch gets a new
    timestamped file under results/<mode>/, so no batch ever overwrites
    another."""
    if args.checkpoint == "last":
        path = latest_checkpoint(mode)
        if path is None:
            raise SystemExit(f"Error: --checkpoint last: no checkpoint to resume in "
                             f"results/{mode}/")
        print(f"Latest {mode} checkpoint: {path}")
    elif args.checkpoint:
        path = Path(args.checkpoint)
    else:
        path = Path("results") / mode / f"{stem}_{datetime.now():%Y%m%d-%H%M%S}.json"
    ckpt = Checkpoint(path, mode, {**params, "closed": runner.CLOSED_TOUR},
                      {name: solver_command(s) for name, s in solvers.items()})
    if not args.checkpoint:
        print(f"  resume an interrupted run with: --checkpoint {path}")
    return ckpt


def run_solver_n_times(ckpt: Checkpoint, solver_name: str, inst_name: str,
                       instance_path: str, n_runs: int, verbose: bool = False,
                       display_label: Optional[str] = None,
                       keep_route: bool = False,
                       status: Optional[StatusLine] = None) -> Optional[Dict]:
    """
    Run a solver with seeds 1..n_runs, reusing the runs already in the
    checkpoint. Returns aggregated stats: best cost, avg cost, avg time, best
    route. After Ctrl+Q the stats cover the runs done so far, or are None if
    there are none.
    """
    records: List[Dict] = []
    if status is not None and status.enabled:
        status.update(label=f"{solver_name} on {inst_name}")
    elif (not verbose) and (display_label is not None):
        print(f"{display_label}...")

    try:
        for seed in range(1, n_runs + 1):
            rec, sol = run_cached(ckpt, inst_name, instance_path, solver_name, seed,
                                  verbose=verbose, keep_route=keep_route)
            records.append(rec)
            if status is not None:
                status.advance()

            if verbose:
                if sol is None:
                    print(f"  run {seed:>2}/{n_runs}: cost={rec['cost']:.2f}  "
                          f"time={rec['time_ms']:.1f}ms  (from checkpoint)")
                    continue
                step_info = ""
                if sol["construction_ms"] > 0 or sol["rvnd_ms"] > 0 or sol["tabu_ms"] > 0:
                    parts = []
                    if sol["construction_ms"] > 0:
                        parts.append(f"construction: {sol['construction_ms']:.1f}ms")
                    if sol["rvnd_ms"] > 0:
                        parts.append(f"rvnd: {sol['rvnd_ms']:.1f}ms")
                    if sol["tabu_ms"] > 0:
                        parts.append(f"tabu: {sol['tabu_ms']:.1f}ms")
                    parts.append(f"total: {sol['time']:.1f}ms")
                    step_info = f"  [{', '.join(parts)}]"
                best_iter_info = ""
                if sol["best_iter"] is not None:
                    best_iter_info = f" best_iter={sol['best_iter']}"
                ttfb_info = ""
                if sol["time_to_best_ms"] is not None:
                    ttfb_info = f" ttfb={sol['time_to_best_ms']:.1f}ms"
                print(
                    f"  run {seed:>2}/{n_runs}: "
                    f"cost={sol['cost']:.2f}  time={sol['time']:.1f}ms{step_info}{best_iter_info}{ttfb_info}"
                )
    except BatchStopped:
        pass

    if not records:
        return None
    costs = [r["cost"] for r in records]
    best = min(records, key=lambda r: r["cost"])
    best_cost = best["cost"]
    ttfb = [r["time_to_best_ms"] for r in records if "time_to_best_ms" in r]
    best_hit_count = sum(1 for c in costs if abs(c - best_cost) < 1e-9)

    return {
        "nodes": best["nodes"],
        "best_cost": best_cost,
        "avg_cost": statistics.mean(costs),
        "avg_time": statistics.mean(r["time_ms"] for r in records),
        "std_cost": statistics.pstdev(costs) if len(costs) > 1 else 0.0,
        "best_hit_rate": best_hit_count / len(records) * 100.0,
        "avg_time_to_best_ms": statistics.mean(ttfb) if ttfb else None,
        "best_route": best.get("route"),
        "all_costs": costs,
    }


def run_compare_best_mode(args, tracker: SolutionTracker):
    """Compare solver results with best known solutions (multiple runs)."""
    if not args.solver:
        print("Error: --solver is required for compare-best mode")
        return

    n_runs = args.runs
    verbose = args.vb
    results = []
    ckpt = open_checkpoint(args, "compare-best", f"compare_best_{args.solver}", {},
                           {args.solver: SOLVERS[args.solver]})

    print(f"\n{'='*100}")
    print(f"Comparing {args.solver.upper()} with Best Known Solutions ({n_runs} runs per instance)")
    print(f"{'='*100}\n")

    instances = resolve_instances(args.instances)
    status = StatusLine(len(instances), len(instances) * n_runs, enabled=not verbose)
    with status:
        for i, inst in enumerate(instances, 1):
            path = os.path.join(INST_DIR, inst)
            name = inst.replace(".tsp", "")
            status.update(instance=i)

            if verbose:
                print(f"Running {args.solver} on {name} ({n_runs} runs)...")

            try:
                agg = run_solver_n_times(
                    ckpt, args.solver, name, path, n_runs,
                    verbose=verbose,
                    display_label=f"Running for {name} instance",
                    keep_route=True,
                    status=status,
                )
            except RuntimeError as e:
                status.print(f"  Error: {e}")
                continue
            if agg is None:
                break

            best_known = None if runner.CLOSED_TOUR else tracker.get_best_cost(name)
            best_gap = None
            avg_gap = None
            best_known_hit_rate = None

            if best_known is not None:
                best_gap = ((agg["best_cost"] - best_known) / best_known) * 100.0
                avg_gap = ((agg["avg_cost"] - best_known) / best_known) * 100.0
                known_hits = sum(1 for c in agg["all_costs"] if abs(c - best_known) < 1e-9)
                best_known_hit_rate = (known_hits / len(agg["all_costs"])) * 100.0

            # Check if this is a new best
            is_new_best = (not runner.CLOSED_TOUR) and tracker.is_better(name, agg["best_cost"])

            result_entry = {
                "instance": name,
                "nodes": agg["nodes"],
                "best_cost": agg["best_cost"],
                "avg_cost": agg["avg_cost"],
                "best_known": best_known,
                "best_gap": best_gap,
                "avg_gap": avg_gap,
                "avg_time": agg["avg_time"],
                "std_cost": agg["std_cost"],
                "best_hit_rate": agg["best_hit_rate"],
                "best_known_hit_rate": best_known_hit_rate,
                "avg_time_to_best_ms": agg["avg_time_to_best_ms"],
                "route": agg["best_route"],
                "is_new_best": is_new_best,
            }
            results.append(result_entry)

            # Save if better
            if is_new_best and agg["best_route"]:
                with status.hidden(), CONTROL.suspended():   # save_solution may ask with input()
                    tracker.save_solution(
                        name, agg["best_cost"], agg["best_route"],
                        args.solver, agg["nodes"], force=args.auto_save
                    )

            # Visualize if requested
            if args.plot and agg["best_route"]:
                subprocess.run(
                    f"{VISUALIZER} plot-route {inst} --route {agg['best_route']}",
                    shell=True,
                )

            if CONTROL.stopped:
                break

    # Print results table; instances that never ran (Ctrl+Q) get "-"
    w = 140
    print(f"\n{'='*w}")
    print(f"Results Summary ({n_runs} runs per instance)")
    print(f"{'='*w}")
    print(
        f"{'Instance':<12} {'Best Known':>12} {'Best Found':>12} {'Avg. Sol':>12} "
        f"{'Avg. Gap':>10} {'Avg. Time(s)':>12}"
    )
    print("-" * w)

    by_name = {r["instance"]: r for r in results}
    for inst in instances:
        r = by_name.get(inst.replace(".tsp", ""))
        if r is None:
            print(f"{inst.replace('.tsp', ''):<12} {'-':>12} {'-':>12} {'-':>12} "
                  f"{'-':>10} {'-':>12}")
            continue
        known_str = f"{r['best_known']:.0f}" if r['best_known'] is not None else "-"
        agap_str = f"{r['avg_gap']:.2f}%" if r['avg_gap'] is not None else "-"

        print(
            f"{r['instance']:<12} {known_str:>12} "
            f"{r['best_cost']:>12.0f} {r['avg_cost']:>12.2f} "
            f"{agap_str:>10} {r['avg_time']/1000:>12.3f}s"
        )

    print("=" * w)


def run_compare_solvers_mode(args, tracker: SolutionTracker):
    """Compare multiple solvers (multiple runs)."""
    if not args.solvers or len(args.solvers) != 2:
        print("Error: --solvers requires exactly 2 solvers for this summary")
        return

    n_runs = args.runs
    verbose = args.vb
    results = []
    solver_a = args.solvers[0]
    solver_b = args.solvers[1]
    ckpt = open_checkpoint(args, "compare-solvers", f"compare_{solver_a}_vs_{solver_b}", {},
                           {s: SOLVERS[s] for s in (solver_a, solver_b)})

    print(f"\n{'='*80}")
    print(f"Comparing Solvers: {solver_a.upper()} vs {solver_b.upper()} ({n_runs} runs each)")
    print(f"{'='*80}\n")

    instances = resolve_instances(args.instances)
    status = StatusLine(len(instances), len(instances) * 2 * n_runs, enabled=not verbose)
    with status:
        for i, inst in enumerate(instances, 1):
            path = os.path.join(INST_DIR, inst)
            name = inst.replace(".tsp", "")
            status.update(instance=i)

            if verbose:
                print(f"Running solvers on {name}...")

            inst_result = {"instance": name, "solvers": {}}

            for solver_name in (solver_a, solver_b):
                try:
                    if verbose:
                        print(f"  {solver_name}:")
                    agg = run_solver_n_times(
                        ckpt, solver_name, name, path, n_runs,
                        verbose=verbose,
                        display_label=f"Running for {name} instance",
                        status=status,
                    )
                    if agg is None:          # Ctrl+Q before any run of it
                        break
                    inst_result["solvers"][solver_name] = agg
                    if verbose:
                        ttfb_msg = "-"
                        if agg["avg_time_to_best_ms"] is not None:
                            ttfb_msg = f"{agg['avg_time_to_best_ms']:.1f}ms"
                        print(
                            f"    summary: best={agg['best_cost']:.2f} avg={agg['avg_cost']:.2f} "
                            f"std={agg['std_cost']:.2f} hit_run={agg['best_hit_rate']:.1f}% ttfb={ttfb_msg}"
                        )
                except RuntimeError as e:
                    status.print(f"  {solver_name} failed: {e}")
                    inst_result["solvers"][solver_name] = "FAILED"
                if CONTROL.stopped:
                    break

            results.append(inst_result)
            if CONTROL.stopped:
                break

    # Print table with only the requested 4 values (plus instance identifier)
    # per instance:
    # 1) AVG_ONE: solver_a average cost
    # 2) AVG_TWO: solver_b average cost
    # 3) AVG_TIME_PCT_DIFF: (solver_a avg_time vs solver_b avg_time)
    # 4) AVG_GAP_PCT_DIFF: (solver_a avg_cost vs solver_b avg_cost)
    w = 100
    print(f"\n{'='*w}")
    print(f"Results Summary ({n_runs} runs per instance)")
    print(f"{'='*w}")
    print(
        f"{'Instance':<12} {'First Avg':>14} {'Second Avg':>14} "
        f"{'Avg Time':>20} {'Avg Gap':>18}"
    )
    print("-" * w)

    # A solver that failed shows FAILED; one that never ran (Ctrl+Q) shows "-".
    by_name = {r["instance"]: r["solvers"] for r in results}
    for inst in instances:
        name = inst.replace(".tsp", "")
        a = by_name.get(name, {}).get(solver_a)
        b = by_name.get(name, {}).get(solver_b)

        if not isinstance(a, dict) or not isinstance(b, dict):
            def cell(agg):
                return agg if agg == "FAILED" else "-" if agg is None else f"{agg['avg_cost']:.2f}"
            print(
                f"{name:<12} {cell(a):>14} {cell(b):>14} "
                f"{'-':>20} {'-':>18}"
            )
            continue

        avg_one = a["avg_cost"]
        avg_two = b["avg_cost"]

        if b["avg_time"] > 0:
            avg_time_pct_diff = ((a["avg_time"] - b["avg_time"]) / b["avg_time"]) * 100.0
        else:
            avg_time_pct_diff = 0.0

        if b["avg_cost"] > 0:
            avg_gap_pct_diff = ((a["avg_cost"] - b["avg_cost"]) / b["avg_cost"]) * 100.0
        else:
            avg_gap_pct_diff = 0.0

        print(
            f"{name:<12} {avg_one:>14.2f} {avg_two:>14.2f} "
            f"{avg_time_pct_diff:>19.2f}% {avg_gap_pct_diff:>17.2f}%"
        )

    print("=" * w)


def run_salehipour_benchmark_mode(args):
    """
    Run --solver or --solvers over the Salehipour-protocol benchmark
    (instances/salehipour/, generated by
    scripts/generate_salehipour_benchmark.py), aggregated per instance
    size. This is the literature-comparable benchmark used by the
    GILS-RVND base paper and by DBMEA/GQPSO/MDM-GILS-RVND to report
    results at large n (see docs/experiments/h12-extended-oropt.md).

    With --solvers (exactly 2): pairs each solver on the SAME instance
    and reports win/tie/loss + exact sign test p-value per size, and
    aggregated across all requested sizes -- same rigor (paired
    comparison, sign test) used throughout this project's
    docs/experiments/ hypothesis testing. Every run is saved to the
    checkpoint as it finishes -- n=500/1000 runs take hours, and an
    interrupted run (session restart, killed process) should resume
    instead of losing that work (this happened once already, see
    docs/experiments/h-salehipour-grasp-vnd.md).

    With --solver (one): reports mean cost/time per size, no comparison.

    One run per instance, with seed 1.
    """
    verbose = args.vb

    if not SALEHIPOUR_DIR.exists():
        print(f"Error: {SALEHIPOUR_DIR} does not exist. Run "
              f"'uv run scripts/generate_salehipour_benchmark.py' first.")
        return

    if args.solvers and len(args.solvers) == 2:
        solver_a_name, solver_b_name = args.solvers
        ckpt = open_checkpoint(args, "salehipour-benchmark",
                               f"salehipour_{solver_a_name}_vs_{solver_b_name}", {},
                               {s: SOLVERS[s] for s in args.solvers})

        print(f"\n{'='*90}")
        print(f"Salehipour benchmark: {solver_a_name.upper()} vs {solver_b_name.upper()}")
        print(f"{'='*90}\n")
        print(f"{'n':>6} {'instances':>10} {'mean_rel%':>10} {'w/t/l':>10} {'sign_p':>8} {'time_b_vs_a%':>13}", flush=True)

        # After Ctrl+Q the sizes that got no run are listed with "-".
        n_inst = sum(len(salehipour_instances(s)) for s in args.sizes)
        status = StatusLine(n_inst, 2 * n_inst, enabled=not verbose)
        inst_i = 0
        with status:
            all_rows = []
            for size in args.sizes:
                rows = []
                try:
                    for inst_path in salehipour_instances(size):
                        if not Path(inst_path).exists():
                            status.print(f"  missing: {inst_path}", flush=True)
                            continue
                        name = Path(inst_path).stem
                        if verbose:
                            status.print(f"  {inst_path}...", flush=True)
                        inst_i += 1
                        status.update(label=f"{solver_a_name} on {name}", instance=inst_i)
                        try:
                            rec_a, _ = run_cached(ckpt, name, inst_path, solver_a_name, 1, verbose=verbose)
                            status.advance()
                            status.update(label=f"{solver_b_name} on {name}")
                            rec_b, _ = run_cached(ckpt, name, inst_path, solver_b_name, 1, verbose=verbose)
                            status.advance()
                        except RuntimeError as e:
                            status.print(f"  failed on {inst_path}: {e}", flush=True)
                            continue
                        rows.append({
                            "cost_a": rec_a["cost"], "time_a": rec_a["time_ms"],
                            "cost_b": rec_b["cost"], "time_b": rec_b["time_ms"],
                        })
                except BatchStopped:
                    pass

                if not rows:
                    status.print(f"{size:>6} {'-':>10} {'-':>10} {'-':>10} {'-':>8} {'-':>13}", flush=True)
                    continue
                all_rows += rows

                c = compare_pairs((r["cost_a"], r["cost_b"]) for r in rows)
                time_a = statistics.mean(r["time_a"] for r in rows)
                time_b = statistics.mean(r["time_b"] for r in rows)
                time_pct = (time_b - time_a) / time_a * 100 if time_a else 0.0

                status.print(f"{size:>6} {c.n:>10} {c.mean_rel:>10.4f} "
                             f"{f'{c.wins}/{c.ties}/{c.losses}':>10} {c.p:>8.3f} {time_pct:>+13.1f}", flush=True)

        if all_rows:
            c = compare_pairs((r["cost_a"], r["cost_b"]) for r in all_rows)
            print("-" * 90)
            print(f"{'ALL':>6} {c.n:>10} {c.mean_rel:>10.4f} "
                  f"{f'{c.wins}/{c.ties}/{c.losses}':>10} {c.p:>8.3f}", flush=True)

    elif args.solver:
        ckpt = open_checkpoint(args, "salehipour-benchmark", f"salehipour_{args.solver}", {},
                               {args.solver: SOLVERS[args.solver]})
        print(f"\n{'='*70}")
        print(f"Salehipour benchmark: {args.solver.upper()}")
        print(f"{'='*70}\n")
        print(f"{'n':>6} {'instances':>10} {'mean_cost':>16} {'mean_time(s)':>13}")

        n_inst = sum(len(salehipour_instances(s)) for s in args.sizes)
        status = StatusLine(n_inst, n_inst, enabled=not verbose)
        inst_i = 0
        with status:
            for size in args.sizes:
                costs, times = [], []
                try:
                    for inst_path in salehipour_instances(size):
                        if not Path(inst_path).exists():
                            status.print(f"  missing: {inst_path}")
                            continue
                        inst_i += 1
                        status.update(label=f"{args.solver} on {Path(inst_path).stem}", instance=inst_i)
                        try:
                            rec, _ = run_cached(ckpt, Path(inst_path).stem, inst_path,
                                                args.solver, 1, verbose=verbose)
                            status.advance()
                        except RuntimeError as e:
                            status.print(f"  failed on {inst_path}: {e}")
                            continue
                        costs.append(rec["cost"])
                        times.append(rec["time_ms"])
                except BatchStopped:
                    pass

                if not costs:
                    status.print(f"{size:>6} {'-':>10} {'-':>16} {'-':>13}")
                    continue
                status.print(f"{size:>6} {len(costs):>10} {statistics.mean(costs):>16.2f} "
                             f"{statistics.mean(times) / 1000:>13.3f}")

    else:
        print("Error: --solver, or --solvers with exactly 2 names, is required for salehipour-benchmark mode")


def run_fixed_time_mode(args):
    """
    Equal-time comparison: every solver gets the SAME wall-clock budget per
    run (--time-limit, passed through as --max-time), paired by seed.

    Comparing these algorithms at equal ITERATIONS is unfair -- their cost
    per iteration differs a lot (extended-oropt scans more neighborhoods,
    mdm runs FPMax* over the elite set) -- so equal iterations means unequal
    compute. This is the "running time as stopping criterion" comparison of
    the MDM-GILS-RVND paper (arXiv:1908.10705, Section 5.3.3).

    Two protocol rules, both learned the hard way in this project (see
    docs/experiments/fixed-time-protocol.md):

      1. Runs are SEQUENTIAL. Timing comparisons do not survive CPU
         contention -- running several solvers at once inflated per-run
         times 2-5x here, with huge variance.
      2. The budget must fit SEVERAL restarts, or mdm_gils_rvnd (mining)
         and gils_am_rvnd (adaptive memory) silently degenerate to plain
         GILS-RVND. RESTARTS / MINING_CALLS are recorded for every run and
         reported, so a null result caused by the protocol is visible
         instead of being mistaken for a null result about the algorithm.
    """
    if args.time_limit is None or args.time_limit <= 0:
        print("Error: --time-limit (seconds, > 0) is required for fixed-time mode")
        return
    if not args.solvers or len(args.solvers) < 2:
        print("Error: --solvers requires at least 2 solvers for fixed-time mode")
        return

    unsupported = [s for s in args.solvers if not supports_fixed_time(s)]
    if unsupported:
        print(f"Error: these solvers do not implement --max-time: {', '.join(unsupported)}")
        print(f"       fixed-time mode only accepts solvers whose binary is one of: "
              f"{', '.join(sorted(FIXED_TIME_BINARIES))}")
        return

    inst_paths = []

    if args.salehipour_sizes:
        for size in args.salehipour_sizes:
            for rel in salehipour_instances(size):
                inst_paths.append((Path(rel).stem, rel))

    if args.instances or not inst_paths:
        for inst in resolve_instances(args.instances):
            inst_paths.append((Path(inst).stem, os.path.join(INST_DIR, inst)))

    missing = [p for _, p in inst_paths if not os.path.exists(p)]
    if missing:
        print(f"Error: instances not found: {', '.join(missing)}")
        return

    n_runs = args.runs
    baseline = args.solvers[0]
    time_limit = args.time_limit

    # A solver that pins its own --iils keeps it: one value for everyone
    # compares each at someone else's tuning. The flags go into the
    # checkpoint as the solver's command, so a resume with a different
    # --time-limit or --iils is caught there.
    solvers = {}
    for solver_name in args.solvers:
        binary, extra = SOLVERS[solver_name]
        flags = ["--max-time", str(time_limit)]
        if "--iils" not in extra:
            flags += ["--iils", str(args.iils)]
        solvers[solver_name] = (binary, extra + flags)

    ckpt = open_checkpoint(args, "fixed-time", f"fixed_time_{int(time_limit)}s", {}, solvers)
    results = ckpt.runs

    print(f"\n{'='*104}")
    print(f"Fixed-time comparison: {time_limit:.0f}s per run, --iils {args.iils}, "
          f"{n_runs} seeds, sequential")
    print(f"Solvers: {', '.join(args.solvers)}   (baseline: {baseline})")
    print(f"Checkpoint: {ckpt.path}")
    print(f"{'='*104}\n", flush=True)

    total = len(inst_paths) * len(args.solvers) * n_runs
    done = 0
    t_start = time.time()

    status = StatusLine(len(inst_paths), total, enabled=not args.vb)
    with status:
        try:
            for inst_i, (inst_name, inst_path) in enumerate(inst_paths, 1):
                for solver_name in args.solvers:
                    for seed in range(1, n_runs + 1):
                        key = f"{inst_name}|{solver_name}|{seed}"
                        status.update(label=f"{solver_name} on {inst_name} seed={seed}",
                                      instance=inst_i)
                        try:
                            _, sol = run_cached(ckpt, inst_name, inst_path, solver_name, seed,
                                                solver=solvers[solver_name], verbose=args.vb)
                        except RuntimeError as e:
                            status.print(f"  FAILED {key}: {e}", flush=True)
                            continue
                        done += 1
                        status.advance()
                        if sol is None:
                            continue

                        flag = ""
                        if sol["mining_calls"] == 0:
                            flag = "  [!] mining never fired"
                        elif sol["restarts"] in (0, 1):
                            flag = f"  [!] only {sol['restarts']} restart(s)"
                        # In a terminal the status line is the progress; a line
                        # per run only with --vb, or when the run needs a look.
                        # Without a terminal (nohup, a log) it is the only progress.
                        if status.enabled and not flag:
                            continue
                        status.print(f"[{done}/{total}] {inst_name:14s} {solver_name:32s} seed={seed:<3d}"
                                     f" cost={sol['cost']:.0f} t={sol['time']/1000:6.1f}s"
                                     f" restarts={sol['restarts']}{flag}", flush=True)
        except BatchStopped:
            pass

    # Time spent paused (Ctrl+P) is not batch time.
    elapsed = time.time() - t_start - CONTROL.paused_seconds
    print(f"\nFinished in {elapsed/60:.1f} min\n")
    _fixed_time_report(results, inst_paths, args, baseline)


def _fixed_time_report(results, inst_paths, args, baseline):
    """Protocol sanity block + paired comparison of each solver vs baseline."""
    n_runs = args.runs

    print("Protocol sanity (mechanisms that live at restart boundaries):")
    for solver_name in args.solvers:
        restarts, mining_zero, seen = [], 0, 0
        for inst_name, _ in inst_paths:
            for seed in range(1, n_runs + 1):
                r = results.get(f"{inst_name}|{solver_name}|{seed}")
                if not r:
                    continue
                seen += 1
                restarts.append(r["restarts"])
                if r["mining_calls"] == 0:
                    mining_zero += 1
        if not seen:
            continue
        line = (f"  {solver_name:32s} restarts avg={statistics.mean(restarts):6.1f} "
                f"min={min(restarts)}")
        minings = [results[f"{i}|{solver_name}|{sd}"]["mining_calls"]
                   for i, _ in inst_paths for sd in range(1, n_runs + 1)
                   if f"{i}|{solver_name}|{sd}" in results
                   and results[f"{i}|{solver_name}|{sd}"]["mining_calls"] >= 0]
        if minings:
            line += f"  mining_calls avg={statistics.mean(minings):5.1f} min={min(minings)}"
        if mining_zero:
            line += (f"  runs with NO mining={mining_zero}/{seen}"
                     f"  <== not interpretable for those runs")
        print(line)
    print()

    w = 104
    for solver_name in args.solvers:
        if solver_name == baseline:
            continue
        print(f"--- {solver_name} vs {baseline} ---")
        print(f"{'Instance':14s} {'mean_rel%':>10s} {'w/t/l':>10s} {'sign_p':>8s} "
              f"{'base_cost':>14s} {'solver_cost':>14s} {'base_t(s)':>10s} {'solver_t(s)':>11s}")
        print("-" * w)

        by_inst = pair_runs(results, baseline, solver_name,
                            instances=[name for name, _ in inst_paths],
                            seeds=range(1, n_runs + 1))
        for inst_name, _ in inst_paths:
            pairs = by_inst.get(inst_name)
            if not pairs:            # never ran, e.g. after Ctrl+Q
                print(f"{inst_name:14s} {'-':>10s} {'-':>10s} {'-':>8s} {'-':>14s} "
                      f"{'-':>14s} {'-':>10s} {'-':>11s}")
                continue
            c = compare_pairs((rb["cost"], rs["cost"]) for rb, rs in pairs)
            print(f"{inst_name:14s} {c.mean_rel:+10.3f} "
                  f"{f'{c.wins}/{c.ties}/{c.losses}':>10s} {c.p:8.4f} "
                  f"{statistics.mean(rb['cost'] for rb, _ in pairs):14.1f} "
                  f"{statistics.mean(rs['cost'] for _, rs in pairs):14.1f} "
                  f"{statistics.mean(rb['time_ms'] / 1000.0 for rb, _ in pairs):10.1f} "
                  f"{statistics.mean(rs['time_ms'] / 1000.0 for _, rs in pairs):11.1f}")

        c = compare_pairs((rb["cost"], rs["cost"]) for pairs in by_inst.values() for rb, rs in pairs)
        if c:
            print("-" * w)
            print(f"{'AGGREGATE':14s} {c.mean_rel:+10.3f} "
                  f"{f'{c.wins}/{c.ties}/{c.losses}':>10s} {c.p:8.4f}")
        print()


def main():
    """Main entry point."""
    args = parse_args()

    # The paths the batch uses are relative to the project root, so work from
    # there whatever directory this was started in. --checkpoint is the one
    # path the user gives, so it is resolved against where they are first.
    if args.checkpoint and args.checkpoint != "last":
        path = Path(args.checkpoint).resolve()
        args.checkpoint = str(path.relative_to(ROOT) if path.is_relative_to(ROOT) else path)
    os.chdir(ROOT)

    runner.CLOSED_TOUR = args.closed
    if args.closed:
        print("Latency counts the return to the depot (closed tour). "
              "The tracked bests are open-path costs, so gaps against them are "
              "suppressed and nothing is written to them.")

    # Initialize solution tracker
    tracker = SolutionTracker(SOLUTIONS_DIR)

    # Run selected mode; Ctrl+P / Ctrl+Q control it (control.py)
    with CONTROL.listening():
        if args.mode == "compare-best":
            run_compare_best_mode(args, tracker)
        elif args.mode == "compare-solvers":
            run_compare_solvers_mode(args, tracker)
        elif args.mode == "salehipour-benchmark":
            run_salehipour_benchmark_mode(args)
        elif args.mode == "fixed-time":
            run_fixed_time_mode(args)


if __name__ == "__main__":
    main()
