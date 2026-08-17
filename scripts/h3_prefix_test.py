"""
Testa H3: vizinhanca especifica de MLP no prefixo.

Para varias instancias de tamanhos crescentes, gera otimos locais (construction
aleatoria + RVND, via os binarios do projeto) e mede, para janelas de k
clientes consecutivos, quanto uma busca exaustiva por permutacao daquela
janela ainda melhora o custo -- comparando janela no prefixo (logo apos o
deposito) contra janelas de controle no meio e no fim da rota.

Se H3 for verdadeira: delta_prefixo > delta_meio > delta_fim, e delta_prefixo
cresce com n.
"""
import itertools
import json
import math
import statistics
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
INSTANCES = ["eil51", "st70", "pr76", "kroA100", "lin105", "pr226", "lin318", "pr439", "att532"]
TRIALS = 10
K_VALUES = [4, 6]
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


def edge_dist(coords, i, j, edge_type):
    dx = coords[i][0] - coords[j][0]
    dy = coords[i][1] - coords[j][1]
    if edge_type == "ATT":
        rij = math.sqrt((dx * dx + dy * dy) / 10.0)
        tij = int(rij)
        return tij + 1 if tij < rij else tij
    return int(math.sqrt(dx * dx + dy * dy))


def route_cost(route, coords, edge_type):
    t = 0
    total = 0
    for k in range(1, len(route)):
        t += edge_dist(coords, route[k - 1], route[k], edge_type)
        total += t
    return total


def parse_route_output(out):
    route = None
    cost = None
    for line in out.splitlines():
        if line.startswith("ROUTE "):
            route = [int(x) for x in line[len("ROUTE "):].strip().rstrip(",").split(",")]
        elif line.startswith("COST "):
            cost = int(line.split()[1])
    return route, cost


def run(cmd):
    return subprocess.run(cmd, capture_output=True, text=True, cwd=PROJECT_ROOT, check=True).stdout


def random_local_optimum(instance):
    out = run(["./bin/construction", f"instances/{instance}.tsp", "--alpha", str(ALPHA)])
    route0, _ = parse_route_output(out)
    route_str = ",".join(map(str, route0))
    out = run(["./bin/local_search", f"instances/{instance}.tsp", "--route", route_str])
    return parse_route_output(out)


def best_window_permutation(route, coords, edge_type, start, k, base_cost):
    prefix = route[:start]
    seg = route[start:start + k]
    suffix = route[start + k:]
    best_cost = base_cost
    for perm in itertools.permutations(seg):
        if perm == tuple(seg):
            continue
        candidate = prefix + list(perm) + suffix
        c = route_cost(candidate, coords, edge_type)
        if c < best_cost:
            best_cost = c
    return best_cost


def main():
    results = []
    for instance in INSTANCES:
        coords, edge_type = parse_tsp(instance)
        n = len(coords)
        for trial in range(TRIALS):
            route, cost = random_local_optimum(instance)
            assert route[0] == 0
            recomputed = route_cost(route, coords, edge_type)
            assert recomputed == cost, f"{instance}: cost mismatch {recomputed} != {cost}"

            for k in K_VALUES:
                if n < 3 * k + 4:
                    continue
                mid_start = n // 2 - k // 2
                regions = {"prefix": 1, "middle": mid_start, "suffix": n - k}
                for region_name, start in regions.items():
                    best_cost = best_window_permutation(route, coords, edge_type, start, k, cost)
                    delta = cost - best_cost
                    results.append({
                        "instance": instance, "n": n, "trial": trial, "k": k,
                        "region": region_name, "base_cost": cost,
                        "delta": delta, "rel_delta_pct": delta / cost * 100.0,
                    })
            print(f"{instance} (n={n}) trial {trial + 1}/{TRIALS} done", file=sys.stderr)

    out_path = PROJECT_ROOT / "scripts" / "h3_prefix_results.json"
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2)
    print(f"raw results written to {out_path}", file=sys.stderr)

    print_summary(results)


def print_summary(results):
    by_key = {}
    for r in results:
        key = (r["instance"], r["n"], r["k"], r["region"])
        by_key.setdefault(key, []).append(r)

    print(f"{'instance':10} {'n':>5} {'k':>2} {'region':7} {'hit%':>6} {'mean_delta':>11} {'mean_rel%':>10}")
    for key in sorted(by_key.keys(), key=lambda k: (k[2], k[1], k[3])):
        instance, n, k, region = key
        rows = by_key[key]
        hits = sum(1 for r in rows if r["delta"] > 0)
        hit_pct = 100.0 * hits / len(rows)
        mean_delta = statistics.mean(r["delta"] for r in rows)
        mean_rel = statistics.mean(r["rel_delta_pct"] for r in rows)
        print(f"{instance:10} {n:5d} {k:2d} {region:7} {hit_pct:6.1f} {mean_delta:11.2f} {mean_rel:10.4f}")


if __name__ == "__main__":
    main()
