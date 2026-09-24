#!/usr/bin/env python3
"""
Run a solver a few times on an instance, verify each tour from the raw
coordinates, and report (optionally save) any tour that beats the tracked
best in instances/solutions/best_solutions.json.

Verification is independent of the solver: the route is checked to be a
permutation of 0..n-1 starting at the depot, and the latency is recomputed
with the Evaluator's rounding convention (truncation for EUC_2D, ceiling
for ATT).
"""
import argparse, json, math, subprocess, sys
from pathlib import Path

from runner import SolutionTracker

BEST = Path("instances/solutions/best_solutions.json")


def _tracker():
    """Reuse runner's SolutionTracker so the .tour file and the
    best_solutions.json entry keep exactly the project's format."""
    return SolutionTracker(Path("instances/solutions"))


def read_inst(path):
    coords, mode, etype = {}, None, "EUC_2D"
    for line in open(path):
        line = line.strip()
        if line.startswith("EDGE_WEIGHT_TYPE"):
            etype = line.split(":")[1].strip()
        if line.startswith("NODE_COORD_SECTION"):
            mode = "c"; continue
        if line.startswith("EOF"):
            break
        if mode == "c" and line:
            p = line.split()
            coords[int(p[0])] = (float(p[1]), float(p[2]))
    return coords, etype


def dist(a, b, etype):
    dx, dy = a[0] - b[0], a[1] - b[1]
    if etype == "ATT":
        return int(math.ceil(math.sqrt((dx * dx + dy * dy) / 10.0)))
    return int(math.sqrt(dx * dx + dy * dy))


def latency(route, coords, etype):
    acc = tot = 0
    for i in range(1, len(route)):
        acc += dist(coords[route[i - 1] + 1], coords[route[i] + 1], etype)
        tot += acc
    return tot


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("instance")
    ap.add_argument("--seeds", type=int, default=5)
    ap.add_argument("--max-time", type=float, default=300)
    ap.add_argument("--iils", type=int, default=300)
    ap.add_argument("--save", action="store_true")
    args = ap.parse_args()

    name = args.instance
    path = name if "/" in name else f"instances/{name}.tsp"
    stem = Path(path).stem
    coords, etype = read_inst(path)

    best = json.loads(BEST.read_text())
    tracked = best.get(stem)
    tracked_cost = tracked["cost"] if isinstance(tracked, dict) else tracked

    champion = None
    for seed in range(1, args.seeds + 1):
        cmd = ["./bin/gils_am_rvnd", path, "--rvnd-mode", "candidate-dlb",
               "--cand-k", "12", "--iils", str(args.iils),
               "--max-time", str(args.max_time), "--seed", str(seed)]
        out = subprocess.run(cmd, capture_output=True, text=True).stdout
        route = cost = None
        for line in out.splitlines():
            if line.startswith("ROUTE"):
                route = [int(x) for x in line.split(None, 1)[1].split(",")]
            if line.startswith("COST"):
                cost = int(line.split()[1])
        n = len(coords)
        assert sorted(route) == list(range(n)) and route[0] == 0, "invalid tour"
        rec = latency(route, coords, etype)
        assert rec == cost, f"cost mismatch: reported {cost} recomputed {rec}"
        print(f"seed {seed}: cost {cost} (verified)  tracked {tracked_cost}", flush=True)
        if champion is None or cost < champion[0]:
            champion = (cost, route)

    print(f"\nbest found {champion[0]}  tracked {tracked_cost}")
    if tracked_cost is None or champion[0] < tracked_cost:
        if tracked_cost is None:
            print("NEW ENTRY (nothing tracked for this instance yet)")
        else:
            print(f"IMPROVED by {tracked_cost - champion[0]} "
                  f"({100*(tracked_cost-champion[0])/tracked_cost:.4f}%)")
        if args.save:
            route_1based = " ".join(str(c + 1) for c in champion[1])
            _tracker().save_solution(
                stem, float(champion[0]), route_1based,
                f"gils_am_rvnd candidate-dlb k12 iils{args.iils} "
                f"maxtime{args.max_time:.0f}s",
                len(coords), force=True)
    else:
        print("no improvement")


if __name__ == "__main__":
    main()
