#!/usr/bin/env python3
"""
Run a solver and check its tour independently of the solver itself.

Verifies the route is a permutation of 0..n-1 starting at the depot, and
recomputes the latency straight from the instance coordinates with the
Evaluator's rounding convention (truncation for EUC_2D, ceiling for ATT).

    python3 scripts/verify_tour.py instances/att532.tsp \
        ./bin/gils_am_rvnd instances/att532.tsp --rvnd-mode candidate-dlb --max-time 5
"""
import math, subprocess, sys


def read_instance(path):
    coords, section, etype = {}, None, "EUC_2D"
    for line in open(path):
        line = line.strip()
        if line.startswith("EDGE_WEIGHT_TYPE"):
            etype = line.split(":")[1].strip()
        if line.startswith("NODE_COORD_SECTION"):
            section = "coords"; continue
        if line.startswith("EOF"):
            break
        if section == "coords" and line:
            p = line.split()
            coords[int(p[0])] = (float(p[1]), float(p[2]))
    return coords, etype


def dist(a, b, etype):
    dx, dy = a[0] - b[0], a[1] - b[1]
    if etype == "ATT":
        return int(math.ceil(math.sqrt((dx * dx + dy * dy) / 10.0)))
    return int(math.sqrt(dx * dx + dy * dy))


def main():
    instance, cmd = sys.argv[1], sys.argv[2:]
    out = subprocess.run(cmd, capture_output=True, text=True)
    route = cost = None
    for line in out.stdout.splitlines():
        if line.startswith("ROUTE"):
            route = [int(x) for x in line.split(None, 1)[1].split(",")]
        if line.startswith("COST"):
            cost = int(line.split()[1])
    if route is None:
        print(f"FAIL no ROUTE in output\n{out.stdout[-400:]}{out.stderr[-400:]}")
        return 1

    coords, etype = read_instance(instance)
    n = len(coords)
    if sorted(route) != list(range(n)) or route[0] != 0:
        print(f"FAIL not a tour of 0..{n-1} starting at the depot")
        return 1

    acc = latency = 0
    for i in range(1, n):
        acc += dist(coords[route[i - 1] + 1], coords[route[i] + 1], etype)
        latency += acc

    ok = latency == cost
    print(f"{'OK  ' if ok else 'FAIL'} n={n} reported={cost} recomputed={latency}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
