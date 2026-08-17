"""
Diagnostico barato para H9 (Large Neighborhood Search / ruin-and-recreate):
compara, a partir de otimos locais ja convergidos por RVND, se
remover-k-clientes + reinserir cada um na posicao mais barata (controlando
AMBAS as pontas do movimento) escapa de otimos locais com mais frequencia/
magnitude do que o double-bridge atual (que so controla onde cortar, nao
com o que reconectar -- ver docs/experiments/h5-regret-perturbation.md).

Ambas as estrategias, depois de perturbar, reconvergem via
./bin/local_search antes de medir o resultado -- e' uma comparacao justa
de "qual perturbacao, seguida do mesmo RVND, encontra melhor resultado".
"""
import itertools
import json
import re
import statistics
import subprocess
import sys
from pathlib import Path

import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parent.parent

INSTANCES = ["lin318", "pr439", "att532"]
N_BASE_OPTIMA = 5
TRIALS_PER_STRATEGY = 20
ALPHA = 0.15
RUIN_K = 8  # number of customers removed per ruin-and-recreate trial


def parse_tsp(name):
    coords = []
    edge_type = None
    reading = False
    with open(PROJECT_ROOT / "instances" / f"{name}.tsp") as f:
        for line in f:
            line = line.strip()
            if line.startswith("EDGE_WEIGHT_TYPE"):
                edge_type = line.split(":")[1].strip()
            elif line == "NODE_COORD_SECTION":
                reading = True
                continue
            elif line == "EOF":
                break
            elif reading and line:
                parts = line.split()
                coords.append((float(parts[1]), float(parts[2])))
    return coords, edge_type


def build_dist_matrix(coords, edge_type):
    xs = np.array([c[0] for c in coords])
    ys = np.array([c[1] for c in coords])
    dx = xs[:, None] - xs[None, :]
    dy = ys[:, None] - ys[None, :]
    d = np.sqrt(dx * dx + dy * dy)
    if edge_type == "ATT":
        rij = np.sqrt((dx * dx + dy * dy) / 10.0)
        tij = rij.astype(int)
        dist = np.where(tij < rij, tij + 1, tij).astype(np.int64)
    else:
        dist = d.astype(np.int64)
    return dist


def route_cost(route, dist):
    t = 0
    total = 0
    for i in range(1, len(route)):
        t += dist[route[i - 1], route[i]]
        total += t
    return int(total)


def run(cmd):
    return subprocess.run(cmd, capture_output=True, text=True, cwd=PROJECT_ROOT, check=True).stdout


def parse_route_output(out):
    route = None
    cost = None
    for line in out.splitlines():
        if line.startswith("ROUTE "):
            route = [int(x) for x in line[len("ROUTE "):].strip().rstrip(",").split(",")]
        elif line.startswith("COST "):
            cost = int(line.split()[1])
    return route, cost


def random_local_optimum(instance):
    out = run(["./bin/construction", f"instances/{instance}.tsp", "--alpha", str(ALPHA)])
    route0, _ = parse_route_output(out)
    route_str = ",".join(map(str, route0))
    out = run(["./bin/local_search", f"instances/{instance}.tsp", "--route", route_str])
    return parse_route_output(out)


def local_search_cost(instance, route):
    route_str = ",".join(map(str, route))
    out = run(["./bin/local_search", f"instances/{instance}.tsp", "--route", route_str])
    _, cost = parse_route_output(out)
    return cost


def double_bridge(route, rng):
    n = len(route)
    cuts = sorted(rng.choice(range(1, n - 1), size=3, replace=False))
    p1, p2, p3 = [int(x) for x in cuts]
    return route[:p1] + route[p2:p3] + route[p1:p2] + route[p3:]


def ruin_and_recreate(route, dist, k, rng):
    n = len(route)
    removable_positions = rng.choice(range(1, n), size=k, replace=False)
    removed_customers = [route[p] for p in removable_positions]
    partial = [c for c in route if c not in set(removed_customers)]

    # regret-2 insertion: repeatedly insert the customer whose gap between
    # best and 2nd-best insertion cost is largest (classic LNS "repair").
    to_insert = list(removed_customers)
    while to_insert:
        best_choice = None  # (regret, customer, best_pos, best_cost)
        for c in to_insert:
            costs = []
            for pos in range(1, len(partial) + 1):
                candidate = partial[:pos] + [c] + partial[pos:]
                costs.append((route_cost(candidate, dist), pos))
            costs.sort(key=lambda x: x[0])
            best_cost, best_pos = costs[0]
            regret = costs[1][0] - costs[0][0] if len(costs) > 1 else 0
            if best_choice is None or regret > best_choice[0]:
                best_choice = (regret, c, best_pos, best_cost)

        _, c, pos, _ = best_choice
        partial = partial[:pos] + [c] + partial[pos:]
        to_insert.remove(c)

    return partial


def main():
    rng = np.random.default_rng(42)
    results = []

    for instance in INSTANCES:
        coords, edge_type = parse_tsp(instance)
        dist = build_dist_matrix(coords, edge_type)

        for base_i in range(N_BASE_OPTIMA):
            route, base_cost = random_local_optimum(instance)

            for mode in ["double_bridge", "ruin_recreate"]:
                for trial in range(TRIALS_PER_STRATEGY):
                    if mode == "double_bridge":
                        perturbed = double_bridge(route, rng)
                    else:
                        perturbed = ruin_and_recreate(route, dist, RUIN_K, rng)

                    new_cost = local_search_cost(instance, perturbed)
                    delta = base_cost - new_cost
                    results.append({
                        "instance": instance, "base_i": base_i, "mode": mode,
                        "trial": trial, "base_cost": base_cost, "new_cost": new_cost,
                        "delta": delta, "rel_delta_pct": delta / base_cost * 100.0,
                    })

            print(f"{instance} base_optimum {base_i + 1}/{N_BASE_OPTIMA} done (cost={base_cost})",
                  file=sys.stderr)

        out_path = PROJECT_ROOT / "scripts" / "h9_ruin_recreate_results.json"
        with open(out_path, "w") as f:
            json.dump(results, f, indent=2)

    print_summary(results)


def print_summary(results):
    by_key = {}
    for r in results:
        by_key.setdefault((r["instance"], r["mode"]), []).append(r)

    print(f"\n{'instance':10} {'mode':16} {'n':>4} {'hit%':>7} {'mean_delta':>11} {'mean_rel%':>10}")
    for (instance, mode), rows in sorted(by_key.items()):
        hits = sum(1 for r in rows if r["delta"] > 0)
        hit_pct = 100.0 * hits / len(rows)
        mean_delta = statistics.mean(r["delta"] for r in rows)
        mean_rel = statistics.mean(r["rel_delta_pct"] for r in rows)
        print(f"{instance:10} {mode:16} {len(rows):4d} {hit_pct:7.1f} {mean_delta:11.2f} {mean_rel:10.4f}")


if __name__ == "__main__":
    main()
