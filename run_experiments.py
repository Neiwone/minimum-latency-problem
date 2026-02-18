import subprocess
import os
import argparse
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional

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
]

INST_DIR = "instances"
SOLUTIONS_DIR = Path(INST_DIR) / "solutions"
BEST_SOLUTIONS_FILE = SOLUTIONS_DIR / "best_solutions.json"

# Solvers
SOLVERS = {
    "nn": "./bin/nearest_neighbour",
    "backtracking": "./bin/backtracking",
    "local_search": "./bin/local_search",
    "construction": "./bin/construction",
    "gils_rvnd": "./bin/gils_rvnd",
}

VISUALIZER = "uv run instance_visualizer.py"


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
    
    return parser.parse_args()


def run_solver(solver_path: str, instance_path: str, route: Optional[str] = None) -> Dict:
    """
    Run a solver and parse its output.
    """

    # ---------- Warm start for Local Search ----------
    if "local_search" in solver_path and route is None:
        construction_path = SOLVERS["construction"]

        construction_solution = run_solver(construction_path, instance_path)

        route = construction_solution["route"]

    # ---------- Run solver ----------
    cmd = [solver_path, instance_path]

    if route is not None:
        cmd += ["--route", route]

    proc = subprocess.run(cmd, capture_output=True, text=True)

    if proc.returncode != 0:
        raise RuntimeError(f"Solver failed: {proc.stderr}")

    data = {}
    for line in proc.stdout.strip().splitlines():
        parts = line.split(maxsplit=1)
        if len(parts) == 2:
            key, value = parts
            data[key] = value

    return {
        "nodes": int(data.get("NODES", 0)),
        "cost": float(data.get("COST", 0)),
        "time": float(data.get("TIME_MS", 0)),
        "route": data.get("ROUTE"),
    }


def run_compare_best_mode(args, tracker: SolutionTracker):
    """Compare solver results with best known solutions."""
    if not args.solver:
        print("Error: --solver is required for compare-best mode")
        return
    
    solver_path = SOLVERS[args.solver]
    results = []
    
    print(f"\n{'='*80}")
    print(f"Comparing {args.solver.lower()} with Best Known Solutions")
    print(f"{'='*80}\n")
    
    for inst in INSTANCES:
        path = os.path.join(INST_DIR, inst)
        name = inst.replace(".tsp", "")
        
        print(f"Running {args.solver} on {name}...")
        
        try:
            solution = run_solver(solver_path, path)
        except RuntimeError as e:
            print(f"  Error: {e}")
            continue
        
        best_cost = tracker.get_best_cost(name)
        gap = None
        
        if best_cost is not None:
            gap = ((solution["cost"] - best_cost) / best_cost) * 100.0
        
        # Check if this is a new best
        is_new_best = tracker.is_better(name, solution["cost"])
        
        results.append({
            "instance": name,
            "nodes": solution["nodes"],
            "cost": solution["cost"],
            "best_cost": best_cost,
            "gap": gap,
            "time": solution["time"],
            "route": solution["route"],
            "is_new_best": is_new_best,
        })
        
        # Save if better
        if is_new_best and solution["route"]:
            tracker.save_solution(
                name, solution["cost"], solution["route"],
                args.solver, solution["nodes"], force=args.auto_save
            )
        
        # Visualize if requested
        if args.plot and solution["route"]:
            subprocess.run(
                f"{VISUALIZER} plot-route {inst} --route {solution['route']}",
                shell=True,
            )
    
    # Print results table
    print(f"\n{'='*80}")
    print("Results Summary")
    print(f"{'='*80}")
    print(
        f"{'Instance':<12} {'N':>5} "
        f"{'Cost':>12} {'Best':>12} {'Gap%':>8} {'Time(s)':>10} {'New?':>5}"
    )
    print("-" * 80)
    
    for r in results:
        best_str = f"{r['best_cost']:.2f}" if r['best_cost'] is not None else "-"
        gap_str = f"{r['gap']:.2f}" if r['gap'] is not None else "-"
        new_str = "✓" if r['is_new_best'] else ""
        
        print(
            f"{r['instance']:<12} {r['nodes']:>5} "
            f"{r['cost']:>12.2f} {best_str:>12} {gap_str:>8} "
            f"{r['time']/60:>10.3f} {new_str:>5}"
        )
    
    print("=" * 80)


def run_exact_mode(args, tracker: SolutionTracker):
    """Compare solver with exact backtracking solver."""
    if not args.solver:
        print("Error: --solver is required for exact mode")
        return
    
    solver_path = SOLVERS[args.solver]
    bt_solver = SOLVERS["backtracking"]
    results = []
    
    print(f"\n{'='*80}")
    print(f"Comparing {args.solver.upper()} with Exact Solver (Backtracking)")
    print(f"{'='*80}\n")
    
    for inst in INSTANCES:
        path = os.path.join(INST_DIR, inst)
        name = inst.replace(".tsp", "")
        
        print(f"Running on {name}...")
        
        try:
            solver_sol = run_solver(solver_path, path)
            bt_sol = run_solver(bt_solver, path)
        except RuntimeError as e:
            print(f"  Error: {e}")
            continue
        
        gap = ((solver_sol["cost"] - bt_sol["cost"]) / bt_sol["cost"]) * 100.0
        
        results.append({
            "instance": name,
            "nodes": solver_sol["nodes"],
            "solver_cost": solver_sol["cost"],
            "optimal_cost": bt_sol["cost"],
            "gap": gap,
            "solver_time": solver_sol["time"],
            "bt_time": bt_sol["time"],
            "solver_route": solver_sol["route"],
            "bt_route": bt_sol["route"],
        })
        
        # Visualize optimal solution if requested
        if args.plot and bt_sol["route"]:
            subprocess.run(
                f"{VISUALIZER} plot-route {inst} --route {bt_sol['route']}",
                shell=True,
            )
    
    # Print results
    print(f"\n{'='*90}")
    print("Results Summary")
    print(f"{'='*90}")
    print(
        f"{'Instance':<12} {'N':>5} "
        f"{args.solver.upper()+' Cost':>15} {'Optimal':>15} {'Gap%':>8} "
        f"{'S Time':>10} {'BT Time':>10}"
    )
    print("-" * 90)
    
    for r in results:
        print(
            f"{r['instance']:<12} {r['nodes']:>5} "
            f"{r['solver_cost']:>15.2f} {r['optimal_cost']:>15.2f} "
            f"{r['gap']:>8.2f} "
            f"{r['solver_time']:>10.3f} {r['bt_time']:>10.3f}"
        )
    
    print("=" * 90)


def run_compare_solvers_mode(args, tracker: SolutionTracker):
    """Compare multiple solvers."""
    if not args.solvers or len(args.solvers) < 2:
        print("Error: --solvers requires at least 2 solvers for comparison")
        return
    
    results = []
    
    print(f"\n{'='*80}")
    print(f"Comparing Solvers: {', '.join(s.upper() for s in args.solvers)}")
    print(f"{'='*80}\n")
    
    for inst in INSTANCES:
        path = os.path.join(INST_DIR, inst)
        name = inst.replace(".tsp", "")
        
        print(f"Running solvers on {name}...")
        
        inst_result = {"instance": name, "solvers": {}}
        
        for solver_name in args.solvers:
            solver_path = SOLVERS[solver_name]
            try:
                sol = run_solver(solver_path, path)
                inst_result["solvers"][solver_name] = sol
            except RuntimeError as e:
                print(f"  {solver_name} failed: {e}")
                inst_result["solvers"][solver_name] = None
        
        results.append(inst_result)
    
    # Print comparison table
    print(f"\n{'='*80}")
    print("Results Summary")
    print(f"{'='*80}")
    
    # Build header
    header = f"{'Instance':<12} {'N':>5} "
    for solver in args.solvers:
        header += f"{solver.upper()+' Cost':>15} {solver.upper()+' Time':>10} "
    print(header)
    print("-" * len(header))
    
    for r in results:
        nodes = next((s["nodes"] for s in r["solvers"].values() if s), 0)
        row = f"{r['instance']:<12} {nodes:>5} "
        
        for solver in args.solvers:
            sol = r["solvers"].get(solver)
            if sol:
                row += f"{sol['cost']:>15.2f} {sol['time']:>10.3f} "
            else:
                row += f"{'FAILED':>15} {'-':>10} "
        
        print(row)
    
    print("=" * len(header))


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