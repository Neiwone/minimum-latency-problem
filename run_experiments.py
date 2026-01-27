import subprocess
import os
import argparse

from best_known_mlp import BEST_KNOWN_MLP

INSTANCES = [
    "rand1.tsp",
    "rand2.tsp",
    "rand3.tsp",
    "rand4.tsp",
    "rand5.tsp",
    # TSPLIB (use only with --mode bks)
    # "eil51.tsp",
    # "berlin52.tsp",
    # "pr76.tsp",
    # "rat99.tsp",
    # "kroA100.tsp",
    # "eil101.tsp",
    # "a280.tsp",
]

INST_DIR = "instances"
SOLVER = "./nearest_neighbour" # "./greedy"
BT_SOLVER = "./backtracking"

VISUALIZER = "uv run instance_visualizer.py"


def parse_args():
    parser = argparse.ArgumentParser(
        description="Run experiments for the Minimum Latency Problem"
    )

    parser.add_argument(
        "--mode",
        choices=["exact", "bks"],
        required=True,
        help="exact: solver vs exact solver | bks: solver vs best known solutions",
    )

    parser.add_argument(
        "--plot",
        action="store_true",
        help="Visualize routes",
    )

    return parser.parse_args()


def run_solver(solver, instance_path):
    proc = subprocess.run(
        [solver, instance_path],
        capture_output=True,
        text=True,
    )

    if proc.returncode != 0:
        raise RuntimeError(proc.stderr)

    data = {}
    for line in proc.stdout.strip().splitlines():
        key, *rest = line.split()
        data[key] = " ".join(rest)

    return {
        "nodes": int(data["NODES"]),
        "cost": float(data["COST"]),
        "time": float(data["TIME_MS"]),
        "route": data.get("ROUTE"),
    }


def run_exact_mode(args):
    results = []

    for inst in INSTANCES:
        path = os.path.join(INST_DIR, inst)
        name = inst.replace(".tsp", "")

        print(f"Running solvers for {name}...")

        solver = run_solver(SOLVER, path)
        bt = run_solver(BT_SOLVER, path)

        gap = (solver["cost"] - bt["cost"]) / bt["cost"] * 100.0

        results.append({
            "instance": name,
            "nodes": solver["nodes"],
            "solver_cost": solver["cost"],
            "best_cost": bt["cost"],
            "gap": gap,
            "solver_time": solver["time"],
            "bt_time": bt["time"],
            "solver_route": solver["route"],
            "bt_route": bt["route"],
        })

        if args.plot:
            subprocess.run(
                f"{VISUALIZER} plot-route {inst} --route {bt['route']}",
                shell=True,
            )

    print("\nSolver Solver vs Exact Solver (Backtracking)")
    print("=" * 110)
    print(
        f"{'Instance':<12} {'N':>5} "
        f"{'Solver':>15} {'Optimal':>15} {'Gap %':>8} "
        f"{'S Time':>10} {'BT Time':>10}"
    )
    print("-" * 110)

    for r in results:
        print(
            f"{r['instance']:<12} {r['nodes']:>5} "
            f"{r['solver_cost']:>15.2f} {r['best_cost']:>15.2f} "
            f"{r['gap']:>8.2f} "
            f"{r['solver_time']:>10.3f} {r['bt_time']:>10.3f}"
        )

    print("=" * 110)


def run_bks_mode(args):
    results = []

    for inst in INSTANCES:
        path = os.path.join(INST_DIR, inst)
        name = inst.replace(".tsp", "")

        print(f"Running solver for {name}...")

        solver = run_solver(SOLVER, path)
        bks = BEST_KNOWN_MLP.get(name)

        gap = None
        if bks is not None:
            gap = (solver["cost"] - bks) / bks * 100.0

        results.append({
            "instance": name,
            "nodes": solver["nodes"],
            "cost": solver["cost"],
            "bks": bks,
            "gap": gap,
            "time": solver["time"],
            "route": solver["route"],
        })

        if args.plot and solver["route"] is not None:
            subprocess.run(
                f"{VISUALIZER} plot-route {inst} --route {solver['route']}",
                shell=True,
            )

    print("\nSolver vs Best Known Solutions")
    print("=" * 95)
    print(
        f"{'Instance':<12} {'N':>5} "
        f"{'Cost':>15} {'BKS':>15} {'Gap %':>8} {'Time':>10}"
    )
    print("-" * 95)

    for r in results:
        gap_str = f"{r['gap']:.2f}" if r["gap"] is not None else "-"
        bks_str = f"{r['bks']}" if r["bks"] is not None else "-"

        print(
            f"{r['instance']:<12} {r['nodes']:>5} "
            f"{r['cost']:>15.2f} {bks_str:>15} "
            f"{gap_str:>8} {r['time']:>10.3f}"
        )

    print("=" * 95)


def main():
    args = parse_args()

    if args.mode == "exact":
        run_exact_mode(args)
    elif args.mode == "bks":
        run_bks_mode(args)


if __name__ == "__main__":
    main()
