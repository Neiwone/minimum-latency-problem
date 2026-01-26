import subprocess
import os
import argparse

from best_known_mlp import BEST_KNOWN_MLP

INSTANCES = [
  "berlin52.tsp",
  "a280.tsp",
  "eil51.tsp",
  "pr76.tsp",
  "eil101.tsp",
  "rat99.tsp",
  "kroA100.tsp",
]
INST_DIR = "instances"
SOLVER = "./greedy"
VISUALIZER = "uv run instance_visualizer.py"

def parse_args():
    parser = argparse.ArgumentParser(
        description="Run experiments for Greedy NN (MLP)"
    )
    parser.add_argument(
        "--plot",
        action="store_true",
        help="Visualize route after each run",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    results = []

    for inst in INSTANCES:
        path = os.path.join(INST_DIR, inst)

        proc = subprocess.run(
            [SOLVER, path],
            capture_output=True,
            text=True,
        )

        if proc.returncode != 0:
            print(f"Error running {inst}")
            print(proc.stderr)
            continue

        output = proc.stdout.strip().splitlines()

        data = {}
        for line in output:
            key, *rest = line.split()
            data[key] = " ".join(rest)

        instance_name = inst.replace(".tsp", "")
        cost = float(data["COST"])
        time_ms = float(data["TIME_MS"])
        route = data.get("ROUTE")

        bks = BEST_KNOWN_MLP.get(instance_name)
        gap = None
        if bks is not None:
            gap = (cost - bks) / bks * 100.0

        results.append({
            "instance": instance_name,
            "nodes": int(data["NODES"]),
            "cost": cost,
            "bks": bks,
            "gap": gap,
            "time": time_ms,
            "route": route,
        })

        if args.plot and route is not None:
            print(f"\nPlotting route for {instance_name}...")
            subprocess.run(
                f"{VISUALIZER} plot-route {inst} --route {route}",
                shell=True,
            )

    print("\nGreedy Nearest Neighbor - Minimum Latency Problem")
    print("=" * 100)
    print(
        f"{'Instance':<12} {'N':>6} {'Cost':>18} "
        f"{'BKS':>12} {'Gap %':>8} {'Time (ms)':>12}"
    )
    print("-" * 100)

    for r in results:
        gap_str = f"{r['gap']:.2f}" if r["gap"] is not None else "-"
        bks_str = f"{r['bks']}" if r["bks"] is not None else "-"

        print(
            f"{r['instance']:<12} {r['nodes']:>6} "
            f"{r['cost']:>18.2f} {bks_str:>12} "
            f"{gap_str:>8} {r['time']:>12.3f}"
        )

    print("=" * 100)


if __name__ == "__main__":
    main()
