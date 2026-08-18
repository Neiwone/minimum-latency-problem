import subprocess
import os
import argparse
import json
import statistics
import sys
import threading
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple

INSTANCES = [
    # TSPLIB instances
    # "eil51.tsp",
    # "berlin52.tsp",
    # "pr76.tsp",
    # "rat99.tsp",
    # "kroA100.tsp",
    # "eil101.tsp",

    "st70.tsp",
    "rat99.tsp",
    "kroD100.tsp",
    "lin105.tsp",
    "pr107.tsp",
    "rat195.tsp",
    "pr226.tsp",
    "lin318.tsp",
    "pr439.tsp",
    "att532.tsp",
]

INST_DIR = "instances"
SOLUTIONS_DIR = Path(INST_DIR) / "solutions"
BEST_SOLUTIONS_FILE = SOLUTIONS_DIR / "best_solutions.json"

# Solvers. Value is either a bare binary path, or (path, extra_args) when the
# solver needs fixed flags appended after "<binary> <instance>" -- e.g. the
# grasp_am parent-mode variants (see src/grasp_am.cpp --parent-mode).
SOLVERS_RAW = {
    "nn": "./bin/nearest_neighbour",
    "backtracking": "./bin/backtracking",
    "local_search": "./bin/local_search",
    "construction": "./bin/construction",
    "grasp": "./bin/grasp",
    "grasp_am": "./bin/grasp_am",
    "grasp_am_pool": ("./bin/grasp_am", ["--parent-mode", "pool"]),
    "grasp_am_pair": ("./bin/grasp_am", ["--parent-mode", "pair"]),
    "gils_am_rvnd_pool": ("./bin/gils_am_rvnd", ["--parent-mode", "pool"]),
    "gils_am_rvnd_pair": ("./bin/gils_am_rvnd", ["--parent-mode", "pair"]),
    "gils_rvnd": "./bin/gils_rvnd",
    "gils_rvnd_extended_oropt": ("./bin/gils_rvnd", ["--rvnd-mode", "extended-oropt"]),
    "gils_rvnd_extended_oropt_wide": ("./bin/gils_rvnd", ["--rvnd-mode", "extended-oropt-wide"]),
    "mdm_gils_rvnd": "./bin/mdm_gils_rvnd",
    "tabu_search": "./bin/tabu_search",
    "gils_rvnd_tabu": "./bin/gils_rvnd_tabu",
}

SolverCmd = Tuple[str, List[str]]


def _normalize_solver(entry) -> SolverCmd:
    if isinstance(entry, tuple):
        path, extra_args = entry
        return (path, list(extra_args))
    return (entry, [])


SOLVERS: Dict[str, SolverCmd] = {
    name: _normalize_solver(entry) for name, entry in SOLVERS_RAW.items()
}

VISUALIZER = "uv run scripts/instance_visualizer.py"


class DotAnimator:
    """Simple animated dots for long-running terminal tasks."""

    def __init__(self, label: str):
        self.label = label
        self._stop = threading.Event()
        self._thread = threading.Thread(target=self._animate, daemon=True)
        self._frames = ["   ", ".  ", ".. ", "..."]

    def _animate(self):
        idx = 0
        while not self._stop.is_set():
            frame = self._frames[idx % len(self._frames)]
            print(f"\r{self.label}{frame}   ", end="", flush=True)
            idx += 1
            time.sleep(0.12)

    def start(self):
        self._thread.start()

    def stop(self, keep_final_line: bool = True):
        self._stop.set()
        self._thread.join()
        if keep_final_line:
            print(f"\r{self.label}...", flush=True)
        else:
            print("\r" + " " * (len(self.label) + 8) + "\r", end="", flush=True)


class SolutionTracker:
    """Manages best known solutions and TSPLIB tour files."""
    
    def __init__(self, solutions_dir: Path):
        self.solutions_dir = solutions_dir
        self.solutions_dir.mkdir(parents=True, exist_ok=True)
        self.best_solutions_file = solutions_dir / "best_solutions.json"
        self.best_solutions = self._load_best_solutions()
    
    def _load_best_solutions(self) -> Dict:
        """Load best known solutions from JSON file."""
        if self.best_solutions_file.exists():
            with open(self.best_solutions_file, 'r') as f:
                return json.load(f)
        return {}
    
    def _save_best_solutions(self):
        """Save best solutions to JSON file."""
        with open(self.best_solutions_file, 'w') as f:
            json.dump(self.best_solutions, indent=2, fp=f)
    
    def get_best_cost(self, instance: str) -> Optional[float]:
        """Get the best known cost for an instance."""
        if instance in self.best_solutions:
            return self.best_solutions[instance]["cost"]
        return None
    
    def is_better(self, instance: str, cost: float) -> bool:
        """Check if the given cost is better than the current best."""
        best_cost = self.get_best_cost(instance)
        if best_cost is None:
            return True
        return cost < best_cost
    
    def save_solution(self, instance: str, cost: float, route: str, solver: str, 
                     nodes: int, force: bool = False):
        """
        Save a solution in TSPLIB format and update best solutions.
        
        Args:
            instance: Instance name (without .tsp extension)
            cost: Solution cost
            route: Space-separated node indices (1-indexed)
            solver: Name of the solver that found this solution
            nodes: Number of nodes in the instance
            force: If True, save without prompting
        """
        if not force and not self.is_better(instance, cost):
            print(f"  Cost {cost:.2f} is not better than current best "
                  f"{self.get_best_cost(instance):.2f}")
            return False
        
        # Prompt user if this is better
        if not force and instance in self.best_solutions:
            current_best = self.best_solutions[instance]["cost"]
            improvement = ((current_best - cost) / current_best) * 100
            response = input(
                f"\n  New best solution for {instance}!\n"
                f"  Current: {current_best:.2f} → New: {cost:.2f} "
                f"(improvement: {improvement:.2f}%)\n"
                f"  Save this solution? [Y/n]: "
            ).strip().lower()
            
            if response and response != 'y' and response != 'yes':
                print("  Solution not saved.")
                return False
        
        # Save TSPLIB tour file
        tour_file = self.solutions_dir / f"{instance}.tour"
        self._write_tsplib_tour(tour_file, instance, cost, route, nodes, solver)
        
        # Update best solutions JSON
        self.best_solutions[instance] = {
            "cost": cost,
            "solver": solver,
            "timestamp": datetime.now().isoformat(),
            "tour_file": str(tour_file.name)
        }
        self._save_best_solutions()
        
        print(f"  ✓ Saved solution to {tour_file.name}")
        return True
    
    def _write_tsplib_tour(self, filepath: Path, instance: str, cost: float,
                          route: str, nodes: int, solver: str):
        """Write solution in TSPLIB tour format."""
        route_nodes = route.split()
        
        with open(filepath, 'w') as f:
            f.write(f"NAME : {instance}.tour\n")
            f.write(f"COMMENT : MLP solution (cost={cost:.2f}, solver={solver})\n")
            f.write("TYPE : TOUR\n")
            f.write(f"DIMENSION : {nodes}\n")
            f.write("TOUR_SECTION\n")
            
            for node in route_nodes:
                f.write(f"{node}\n")
            
            f.write("-1\n")
            f.write("EOF\n")


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Run MLP experiments and track best solutions",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Compare solver with best known solutions
  python run_experiments.py --mode compare-best --solver nn
  
  # Run exact comparison with backtracking
  python run_experiments.py --mode exact --solver nn
  
  # Compare multiple solvers
  python run_experiments.py --mode compare-solvers --solvers nn local_search
        """
    )
    
    parser.add_argument(
        "--mode",
        choices=["compare-best", "exact", "compare-solvers"],
        required=True,
        help=(
            "compare-best: Compare solver with tracked best solutions | "
            "exact: Compare solver with exact backtracking solver | "
            "compare-solvers: Compare multiple solvers"
        )
    )
    
    parser.add_argument(
        "--solver",
        choices=list(SOLVERS.keys()),
        help="Solver to use (required for compare-best and exact modes)"
    )
    
    parser.add_argument(
        "--solvers",
        nargs="+",
        choices=list(SOLVERS.keys()),
        help="List of solvers to compare (for compare-solvers mode)"
    )
    
    parser.add_argument(
        "--plot",
        action="store_true",
        help="Visualize routes"
    )
    
    parser.add_argument(
        "--auto-save",
        action="store_true",
        help="Automatically save better solutions without prompting"
    )
    
    parser.add_argument(
        "--runs",
        type=int,
        default=10,
        help="Number of runs per instance (default: 10)"
    )
    
    parser.add_argument(
        "--vb",
        action="store_true",
        help="Verbose: show step-level timing (construction, rvnd, tabu) when available"
    )
    
    return parser.parse_args()


def run_solver(solver: SolverCmd, instance_path: str, route: Optional[str] = None,
               verbose: bool = False) -> Dict:
    """
    Run a solver and parse its output.
    """
    solver_path, extra_args = solver

    # ---------- Warm start for Local Search ----------
    if "local_search" in solver_path and route is None:
        construction_solver = SOLVERS["construction"]

        construction_solution = run_solver(construction_solver, instance_path)

        route = construction_solution["route"]

    # ---------- Run solver ----------
    cmd = [solver_path, instance_path]

    if verbose and (
        "gils_rvnd" in solver_path
        or "grasp_rvnd" in solver_path
        or "grasp_am" in solver_path
        or "gils_rvnd_tabu" in solver_path
        or "tabu_search" in solver_path
        or solver_path.endswith("/grasp")
    ):
        cmd.append("-v")

    if route is not None:
        cmd += ["--route", route]

    cmd += extra_args

    proc = subprocess.run(cmd, capture_output=True, text=True)

    if proc.returncode != 0:
        raise RuntimeError(f"Solver failed: {proc.stderr}")

    data = {}
    for line in proc.stdout.strip().splitlines():
        parts = line.split(maxsplit=1)
        if len(parts) == 2:
            key, value = parts
            data[key] = value

    best_iter = None
    if proc.stderr:
        for line in proc.stderr.strip().splitlines():
            if line.startswith("best at iter"):
                parts = line.split()
                if len(parts) >= 4:
                    try:
                        best_iter = int(parts[3])
                    except ValueError:
                        best_iter = None

    outer_iters = 0
    if "IMAX" in data:
        try:
            outer_iters = int(data["IMAX"])
        except ValueError:
            outer_iters = 0
    elif "ITER" in data:
        try:
            outer_iters = int(data["ITER"])
        except ValueError:
            outer_iters = 0

    time_ms = float(data.get("TIME_MS", 0))
    time_to_best_ms = None
    if best_iter is not None and outer_iters > 0:
        bounded_iter = min(max(best_iter, 0), outer_iters - 1)
        time_to_best_ms = ((bounded_iter + 1) / outer_iters) * time_ms

    return {
        "nodes": int(data.get("NODES", 0)),
        "cost": float(data.get("COST", 0)),
        "time": time_ms,
        "construction_ms": float(data.get("CONSTRUCTION_MS", 0)),
        "rvnd_ms": float(data.get("RVND_MS", 0)),
        "tabu_ms": float(data.get("TABU_MS", 0)),
        "route": data.get("ROUTE"),
        "best_iter": best_iter,
        "time_to_best_ms": time_to_best_ms,
    }


def run_solver_n_times(solver: SolverCmd, instance_path: str, n_runs: int,
                       verbose: bool = False,
                       display_label: Optional[str] = None) -> Dict:
    """
    Run a solver n_runs times. Returns aggregated stats:
    best cost, avg cost, avg time, best route, and per-step timing.
    """
    costs: List[float] = []
    times: List[float] = []
    construction_times: List[float] = []
    rvnd_times: List[float] = []
    tabu_times: List[float] = []
    time_to_best_samples: List[float] = []
    best_cost = float('inf')
    best_route = None
    best_nodes = 0
    best_time = 0.0
    animate = (not verbose) and (display_label is not None) and sys.stdout.isatty()
    animator = None

    if (not verbose) and (display_label is not None):
        if animate:
            animator = DotAnimator(display_label)
            animator.start()
        else:
            print(f"{display_label}...")

    try:
        for run_i in range(n_runs):
            sol = run_solver(solver, instance_path, verbose=verbose)

            costs.append(sol["cost"])
            times.append(sol["time"])
            construction_times.append(sol["construction_ms"])
            rvnd_times.append(sol["rvnd_ms"])
            tabu_times.append(sol["tabu_ms"])
            if sol["time_to_best_ms"] is not None:
                time_to_best_samples.append(sol["time_to_best_ms"])

            if sol["cost"] < best_cost:
                best_cost = sol["cost"]
                best_route = sol["route"]
                best_nodes = sol["nodes"]
                best_time = sol["time"]

            if verbose:
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
                    f"  run {run_i+1:>2}/{n_runs}: "
                    f"cost={sol['cost']:.2f}  time={sol['time']:.1f}ms{step_info}{best_iter_info}{ttfb_info}"
                )
    finally:
        if animator is not None:
            animator.stop(keep_final_line=True)

    avg_cost = statistics.mean(costs)
    avg_time = statistics.mean(times)
    avg_construction = statistics.mean(construction_times)
    avg_rvnd = statistics.mean(rvnd_times)
    avg_tabu = statistics.mean(tabu_times)
    std_cost = statistics.pstdev(costs) if len(costs) > 1 else 0.0
    best_hit_count = sum(1 for c in costs if abs(c - best_cost) < 1e-9)
    best_hit_rate = (best_hit_count / n_runs) * 100.0 if n_runs > 0 else 0.0
    avg_time_to_best_ms = statistics.mean(time_to_best_samples) if time_to_best_samples else None

    return {
        "nodes": best_nodes,
        "best_cost": best_cost,
        "avg_cost": avg_cost,
        "avg_time": avg_time,
        "best_time": best_time,
        "avg_construction_ms": avg_construction,
        "avg_rvnd_ms": avg_rvnd,
        "avg_tabu_ms": avg_tabu,
        "std_cost": std_cost,
        "best_hit_rate": best_hit_rate,
        "avg_time_to_best_ms": avg_time_to_best_ms,
        "best_route": best_route,
        "all_costs": costs,
        "all_times": times,
    }


def run_compare_best_mode(args, tracker: SolutionTracker):
    """Compare solver results with best known solutions (multiple runs)."""
    if not args.solver:
        print("Error: --solver is required for compare-best mode")
        return
    
    solver = SOLVERS[args.solver]
    n_runs = args.runs
    verbose = args.vb
    results = []

    print(f"\n{'='*100}")
    print(f"Comparing {args.solver.upper()} with Best Known Solutions ({n_runs} runs per instance)")
    print(f"{'='*100}\n")

    for inst in INSTANCES:
        path = os.path.join(INST_DIR, inst)
        name = inst.replace(".tsp", "")

        if verbose:
            print(f"Running {args.solver} on {name} ({n_runs} runs)...")

        try:
            agg = run_solver_n_times(
                solver,
                path,
                n_runs,
                verbose=verbose,
                display_label=f"Running for {name} instance",
            )
        except RuntimeError as e:
            print(f"  Error: {e}")
            continue
        
        best_known = tracker.get_best_cost(name)
        best_gap = None
        avg_gap = None
        best_known_hit_rate = None
        
        if best_known is not None:
            best_gap = ((agg["best_cost"] - best_known) / best_known) * 100.0
            avg_gap = ((agg["avg_cost"] - best_known) / best_known) * 100.0
            known_hits = sum(1 for c in agg["all_costs"] if abs(c - best_known) < 1e-9)
            best_known_hit_rate = (known_hits / n_runs) * 100.0
        
        # Check if this is a new best
        is_new_best = tracker.is_better(name, agg["best_cost"])
        
        result_entry = {
            "instance": name,
            "nodes": agg["nodes"],
            "best_cost": agg["best_cost"],
            "avg_cost": agg["avg_cost"],
            "best_known": best_known,
            "best_gap": best_gap,
            "avg_gap": avg_gap,
            "avg_time": agg["avg_time"],
            "avg_construction_ms": agg["avg_construction_ms"],
            "avg_rvnd_ms": agg["avg_rvnd_ms"],
            "avg_tabu_ms": agg["avg_tabu_ms"],
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

    # Print results table
    w = 140
    print(f"\n{'='*w}")
    print(f"Results Summary ({n_runs} runs per instance)")
    print(f"{'='*w}")
    print(
        f"{'Instance':<12} {'Best Known':>12} {'Best Found':>12} {'Avg. Sol':>12} "
        f"{'Avg. Gap':>10} {'Avg. Time(s)':>12}"
    )
    print("-" * w)

    for r in results:
        known_str = f"{r['best_known']:.0f}" if r['best_known'] is not None else "-"
        agap_str = f"{r['avg_gap']:.2f}%" if r['avg_gap'] is not None else "-"

        print(
            f"{r['instance']:<12} {known_str:>12} "
            f"{r['best_cost']:>12.0f} {r['avg_cost']:>12.2f} "
            f"{agap_str:>10} {r['avg_time']/1000:>12.3f}s"
        )

    print("=" * w)


def run_exact_mode(args, tracker: SolutionTracker):
    """Compare solver with exact backtracking solver (multiple runs)."""
    if not args.solver:
        print("Error: --solver is required for exact mode")
        return
    
    solver = SOLVERS[args.solver]
    bt_solver = SOLVERS["backtracking"]
    n_runs = args.runs
    verbose = args.vb
    results = []

    print(f"\n{'='*110}")
    print(f"Comparing {args.solver.upper()} ({n_runs} runs) with Exact Solver (Backtracking)")
    print(f"{'='*110}\n")

    for inst in INSTANCES:
        path = os.path.join(INST_DIR, inst)
        name = inst.replace(".tsp", "")

        if verbose:
            print(f"Running on {name}...")

        try:
            agg = run_solver_n_times(
                solver,
                path,
                n_runs,
                verbose=verbose,
                display_label=f"Running for {name} instance",
            )
            bt_sol = run_solver(bt_solver, path)
        except RuntimeError as e:
            print(f"  Error: {e}")
            continue
        
        best_gap = ((agg["best_cost"] - bt_sol["cost"]) / bt_sol["cost"]) * 100.0
        avg_gap = ((agg["avg_cost"] - bt_sol["cost"]) / bt_sol["cost"]) * 100.0
        
        results.append({
            "instance": name,
            "nodes": agg["nodes"],
            "best_cost": agg["best_cost"],
            "avg_cost": agg["avg_cost"],
            "std_cost": agg["std_cost"],
            "best_hit_rate": agg["best_hit_rate"],
            "avg_time_to_best_ms": agg["avg_time_to_best_ms"],
            "optimal_cost": bt_sol["cost"],
            "best_gap": best_gap,
            "avg_gap": avg_gap,
            "avg_time": agg["avg_time"],
            "avg_construction_ms": agg["avg_construction_ms"],
            "avg_rvnd_ms": agg["avg_rvnd_ms"],
            "avg_tabu_ms": agg["avg_tabu_ms"],
            "bt_time": bt_sol["time"],
        })
    
    # Print results
    w = 130
    print(f"\n{'='*w}")
    print(f"Results Summary ({n_runs} runs per instance)")
    print(f"{'='*w}")
    print(
        f"{'Instance':<12} {'Optimal':>12} {'Best':>12} {'Avg. Sol':>12} {'Std':>10} "
        f"{'Avg. Gap':>10} {'Hit Run%':>9} {'TTFB(s)':>9} {'Avg. Time(s)':>12} {'BT Time(s)':>12}"
    )
    print("-" * w)
    
    for r in results:
        agap_str = f"{r['avg_gap']:.2f}%"
        hit_run_str = f"{r['best_hit_rate']:.1f}%"
        ttfb_str = f"{(r['avg_time_to_best_ms'] / 1000):.3f}s" if r['avg_time_to_best_ms'] is not None else "-"
        print(
            f"{r['instance']:<12} {r['optimal_cost']:>12.0f} "
            f"{r['best_cost']:>12.0f} {r['avg_cost']:>12.2f} {r['std_cost']:>10.2f} "
            f"{agap_str:>10} {hit_run_str:>9} {ttfb_str:>9} "
            f"{r['avg_time']/1000:>9.3f}s {r['bt_time']/1000:>9.3f}s"
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
    
    print(f"\n{'='*80}")
    print(f"Comparing Solvers: {solver_a.upper()} vs {solver_b.upper()} ({n_runs} runs each)")
    print(f"{'='*80}\n")
    
    for inst in INSTANCES:
        path = os.path.join(INST_DIR, inst)
        name = inst.replace(".tsp", "")
        
        if verbose:
            print(f"Running solvers on {name}...")
        
        inst_result = {"instance": name, "solvers": {}}
        
        for solver_name in (solver_a, solver_b):
            solver = SOLVERS[solver_name]
            try:
                if verbose:
                    print(f"  {solver_name}:")
                agg = run_solver_n_times(
                    solver,
                    path,
                    n_runs,
                    verbose=verbose,
                    display_label=f"Running for {name} instance",
                )
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
                print(f"  {solver_name} failed: {e}")
                inst_result["solvers"][solver_name] = None
        
        results.append(inst_result)
    
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

    for r in results:
        a = r["solvers"].get(solver_a)
        b = r["solvers"].get(solver_b)

        if a is None or b is None:
            print(
                f"{r['instance']:<12} {'FAILED':>14} {'FAILED':>14} "
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
            f"{r['instance']:<12} {avg_one:>14.2f} {avg_two:>14.2f} "
            f"{avg_time_pct_diff:>19.2f}% {avg_gap_pct_diff:>17.2f}%"
        )

    print("=" * w)


def main():
    """Main entry point."""
    args = parse_args()
    
    # Initialize solution tracker
    tracker = SolutionTracker(SOLUTIONS_DIR)
    
    # Run selected mode
    if args.mode == "compare-best":
        run_compare_best_mode(args, tracker)
    elif args.mode == "exact":
        run_exact_mode(args, tracker)
    elif args.mode == "compare-solvers":
        run_compare_solvers_mode(args, tracker)


if __name__ == "__main__":
    main()