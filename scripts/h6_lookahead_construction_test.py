"""
Diagnostico barato para H6 (construcao com lookahead cumulativo): compara,
SEM RVND nenhum, o custo bruto da rota logo apos a construcao entre a
construcao gulosa atual (so olha dist(r,c)) e uma variante que pontua cada
candidato por um rollout guloso de k passos (custo cumulativo do segmento
hipotetico r->c->proximo->..., nao so o primeiro salto).

Replica exatamente a mecanica de construction_impl.cpp (mesma formula de
RCL/alpha), so troca o criterio de ordenacao do candidate list.
"""
import json
import statistics
import sys
from pathlib import Path

import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parent.parent

INSTANCES = ["eil51", "st70", "pr76", "kroA100", "lin105", "pr226", "lin318"]
N_TRIALS = 30
ALPHA = 0.15
K = 3  # lookahead depth: 1 real hop + (K-1) greedy probe hops


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
    return total


def greedy_construction(dist, n, alpha, rng):
    """Exact replica of construction_impl.cpp."""
    avail = np.ones(n, dtype=bool)
    avail[0] = False
    route = [0]
    r = 0
    big = np.iinfo(np.int64).max // 2

    for _ in range(n - 1):
        d_row = np.where(avail, dist[r], big)
        order = np.argsort(d_row, kind="stable")
        cl_sorted = order[: avail.sum()]
        rcl_size = max(1, int(alpha * len(cl_sorted)))
        idx = rng.integers(0, rcl_size)
        c = int(cl_sorted[idx])
        route.append(c)
        avail[c] = False
        r = c
    return route


def lookahead_score(dist, r, c, avail_after_c, k, big):
    """Cumulative cost of the hypothetical segment r -> c -> (k-1 greedy hops)."""
    running = int(dist[r, c])
    total = running
    cur = c
    avail = avail_after_c.copy()
    for _ in range(k - 1):
        if not avail.any():
            break
        d_row = np.where(avail, dist[cur], big)
        nxt = int(np.argmin(d_row))
        running += int(dist[cur, nxt])
        total += running
        avail[nxt] = False
        cur = nxt
    return total


def lookahead_construction(dist, n, alpha, k, rng):
    avail = np.ones(n, dtype=bool)
    avail[0] = False
    route = [0]
    r = 0
    big = np.iinfo(np.int64).max // 2

    for _ in range(n - 1):
        candidates = np.nonzero(avail)[0]
        scores = []
        for c in candidates:
            avail_after_c = avail.copy()
            avail_after_c[c] = False
            scores.append(lookahead_score(dist, r, int(c), avail_after_c, k, big))
        order = np.argsort(scores, kind="stable")
        cl_sorted = candidates[order]
        rcl_size = max(1, int(alpha * len(cl_sorted)))
        idx = rng.integers(0, rcl_size)
        c = int(cl_sorted[idx])
        route.append(c)
        avail[c] = False
        r = c
    return route


def main():
    results = []
    for instance in INSTANCES:
        coords, edge_type = parse_tsp(instance)
        dist = build_dist_matrix(coords, edge_type)
        n = len(coords)

        for trial in range(N_TRIALS):
            rng_g = np.random.default_rng((hash(instance) + trial) % (2**32))
            rng_l = np.random.default_rng((hash(instance) + trial) % (2**32))

            route_g = greedy_construction(dist, n, ALPHA, rng_g)
            route_l = lookahead_construction(dist, n, ALPHA, K, rng_l)

            cost_g = int(route_cost(route_g, dist))
            cost_l = int(route_cost(route_l, dist))

            results.append({
                "instance": instance, "n": n, "trial": trial,
                "cost_greedy": cost_g, "cost_lookahead": cost_l,
                "delta": cost_g - cost_l, "rel_delta_pct": (cost_g - cost_l) / cost_g * 100.0,
            })

        print(f"{instance} (n={n}) done", file=sys.stderr)
        out_path = PROJECT_ROOT / "scripts" / "h6_lookahead_results_k3.json"
        with open(out_path, "w") as f:
            json.dump(results, f, indent=2)

    print_summary(results)


def print_summary(results):
    by_inst = {}
    for r in results:
        by_inst.setdefault(r["instance"], []).append(r)

    print(f"\n{'instance':10} {'n':>5} {'win/tie/loss':>14} {'mean_rel%':>10} {'mean_cost_g':>14} {'mean_cost_l':>14}")
    for instance, rows in by_inst.items():
        wins = sum(1 for r in rows if r["delta"] > 0)
        losses = sum(1 for r in rows if r["delta"] < 0)
        ties = len(rows) - wins - losses
        mean_rel = statistics.mean(r["rel_delta_pct"] for r in rows)
        mean_g = statistics.mean(r["cost_greedy"] for r in rows)
        mean_l = statistics.mean(r["cost_lookahead"] for r in rows)
        n = rows[0]["n"]
        print(f"{instance:10} {n:5d} {wins}/{ties}/{losses:<9} {mean_rel:10.4f} {mean_g:14.1f} {mean_l:14.1f}")


if __name__ == "__main__":
    main()
