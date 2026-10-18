#!/usr/bin/env python3
"""
Run a solver and check its tour independently of the solver itself.

Verifies the route is a permutation of 0..n-1 starting at the depot, and
recomputes the latency straight from the instance coordinates with the
Evaluator's rounding convention for the path (truncation for EUC_2D,
ceiling for ATT); a solver run with --nint is checked with nint.

    python3 scripts/verify_tour.py instances/att532.tsp \
        ./bin/gils_am_rvnd instances/att532.tsp --rvnd-mode candidate-dlb --max-time 5
"""
import math, subprocess, sys


def read_instance(path):
    coords, section, etype, fmt, n, nums = {}, None, "EUC_2D", None, 0, []
    for line in open(path):
        line = line.strip()
        if line.startswith("DIMENSION"):
            n = int(line.split(":")[1])
        if line.startswith("EDGE_WEIGHT_TYPE"):
            etype = line.split(":")[1].strip()
        if line.startswith("EDGE_WEIGHT_FORMAT"):
            fmt = line.split(":")[1].strip()
        if line.startswith("NODE_COORD_SECTION"):
            section = "coords"; continue
        if line.startswith("EDGE_WEIGHT_SECTION"):
            section = "weights"; continue
        if line.startswith("DISPLAY_DATA_SECTION") or line.startswith("EOF"):
            section = None; continue
        if not line:
            continue
        if section == "coords":
            p = line.split()
            coords[int(p[0])] = (float(p[1]), float(p[2]))
        elif section == "weights":
            nums += [int(float(v)) for v in line.split()]

    if etype != "EXPLICIT":
        return coords, etype, None

    # Each format lists a different triangle; read it then mirror.
    m = [[0] * n for _ in range(n)]
    it = iter(nums)
    for i in range(n):
        rng = {"FULL_MATRIX":    range(n),
               "UPPER_ROW":      range(i + 1, n),
               "UPPER_DIAG_ROW": range(i, n),
               "LOWER_ROW":      range(i),
               "LOWER_DIAG_ROW": range(i + 1)}[fmt]
        for j in rng:
            m[i][j] = m[j][i] = next(it)
    leftover = sum(1 for _ in it)
    if leftover:
        print(f"WARN {leftover} valores sobrando em EDGE_WEIGHT_SECTION")
    return {i + 1: None for i in range(n)}, etype, m


def geo_rad(v):
    deg = int(v)
    return 3.141592 * (deg + 5.0 * (v - deg) / 3.0) / 180.0  # TSPLIB uses this PI


def dist(a, b, etype, nint=False):
    if etype == "GEO":
        la, lo = geo_rad(a[0]), geo_rad(a[1])
        lb, lob = geo_rad(b[0]), geo_rad(b[1])
        q1, q2, q3 = math.cos(lo - lob), math.cos(la - lb), math.cos(la + lb)
        return int(6378.388 * math.acos(0.5 * ((1 + q1) * q2 - (1 - q1) * q3)) + 1.0)
    dx, dy = a[0] - b[0], a[1] - b[1]
    if etype == "ATT":
        return int(math.ceil(math.sqrt((dx * dx + dy * dy) / 10.0)))
    if etype == "CEIL_2D":
        return int(math.ceil(math.sqrt(dx * dx + dy * dy)))
    d = math.sqrt(dx * dx + dy * dy)
    return int(d + 0.5) if nint else int(d)


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

    coords, etype, matrix = read_instance(instance)
    nint = "--nint" in cmd
    n = len(coords)
    if sorted(route) != list(range(n)) or route[0] != 0:
        print(f"FAIL not a tour of 0..{n-1} starting at the depot")
        return 1

    acc = latency = 0
    for i in range(1, n):
        if matrix is not None:
            acc += matrix[route[i - 1]][route[i]]
        else:
            acc += dist(coords[route[i - 1] + 1], coords[route[i] + 1], etype, nint)
        latency += acc

    ok = latency == cost
    print(f"{'OK  ' if ok else 'FAIL'} n={n} reported={cost} recomputed={latency}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
