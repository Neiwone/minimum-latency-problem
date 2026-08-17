"""
Diagnostico barato para H5 (perturbacao guiada por "regret" de aresta):
antes de implementar qualquer coisa em C++, testa se cortar o double-bridge
em posicoes de alto regret (em vez de posicoes aleatorias) encontra
melhorias mais frequentes/maiores, a partir de otimos locais ja
convergidos por RVND.

regret(u, v) = dist(u, v) - dist(u, vizinho_mais_proximo_de_u)
  -- o quanto pior e' a aresta atual de u comparada a melhor alternativa
     geometrica disponivel (inspirado em GNN-GLS / Hudson et al. 2022).
peso por posicao: weighted_regret(p) = regret(tour[p-1], tour[p]) * (n - p)
  -- arestas cedo na rota pesam mais no MLP (mais clientes afetados a
     jusante), mesmo raciocinio do artigo-base para o avaliador O(1).

Para cada estrategia de escolha dos 3 cortes do double-bridge (random,
regret-biased, inverse-regret como controle), aplica o kick numa rota ja
convergida e reconverge via RVND (reaproveitando ./bin/local_search
--route), medindo se a nova convergencia melhora o custo original.
"""
import itertools
import json
import re
import subprocess
import sys
from pathlib import Path

import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parent.parent

INSTANCES = ["lin318", "pr439", "att532"]
N_BASE_OPTIMA = 5
TRIALS_PER_STRATEGY = 30
ALPHA = 0.15


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
    n = len(coords)
    xs = np.array([c[0] for c in coords])
    ys = np.array([c[1] for c in coords])
    dx = xs[:, None] - xs[None, :]
    dy = ys[:, None] - ys[None, :]
    d = np.sqrt(dx * dx + dy * dy)
    if edge_type == "ATT":
        rij = np.sqrt((dx * dx + dy * dy) / 10.0)
        tij = rij.astype(int)
        dist = np.where(tij < rij, tij + 1, tij)
    else:
        dist = d.astype(int)
    np.fill_diagonal(dist, np.iinfo(dist.dtype).max // 2)
    return dist


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


def random_local_optimum(instance, seed_offset):
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


def weighted_regret(route, dist):
    n = len(route)
    nearest = dist.min(axis=1)
    w = np.zeros(n)
    for p in range(1, n - 1):
        u, v = route[p - 1], route[p]
        regret = dist[u, v] - nearest[u]
        w[p] = max(regret, 0) * (n - p)
    return w


def sample_cuts(n, weights, rng, mode):
    positions = np.arange(1, n - 1)
    if mode == "random":
        p = np.ones(len(positions))
    elif mode == "regret":
        p = weights[1:n - 1]
    elif mode == "inverse_regret":
        w = weights[1:n - 1]
        maxw = w.max() if w.max() > 0 else 1.0
        p = (maxw - w) + 1e-6
    else:
        raise ValueError(mode)

    if p.sum() <= 0:
        p = np.ones(len(positions))
    p = p / p.sum()

    chosen = rng.choice(positions, size=3, replace=False, p=p)
    return sorted(int(x) for x in chosen)


def double_bridge(route, p1, p2, p3):
    return route[:p1] + route[p2:p3] + route[p1:p2] + route[p3:]


def main():
    rng = np.random.default_rng(42)
    results = []

    for instance in INSTANCES:
        coords, edge_type = parse_tsp(instance)
        dist = build_dist_matrix(coords, edge_type)
        n = len(coords)

        for base_i in range(N_BASE_OPTIMA):
            route, base_cost = random_local_optimum(instance, base_i)
            weights = weighted_regret(route, dist)

            for mode in ["random", "regret", "inverse_regret"]:
                for trial in range(TRIALS_PER_STRATEGY):
                    p1, p2, p3 = sample_cuts(n, weights, rng, mode)
                    perturbed = double_bridge(route, p1, p2, p3)
                    new_cost = local_search_cost(instance, perturbed)
                    delta = base_cost - new_cost
                    results.append({
                        "instance": instance, "base_i": base_i, "mode": mode,
                        "trial": trial, "base_cost": base_cost, "new_cost": new_cost,
                        "delta": delta, "rel_delta_pct": delta / base_cost * 100.0,
                    })

            print(f"{instance} base_optimum {base_i + 1}/{N_BASE_OPTIMA} done (cost={base_cost})",
                  file=sys.stderr)

        out_path = PROJECT_ROOT / "scripts" / "h5_regret_results.json"
        with open(out_path, "w") as f:
            json.dump(results, f, indent=2)

    print_summary(results)


def print_summary(results):
    import statistics
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
