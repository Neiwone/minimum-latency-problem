"""
Roda o modo --pert-mode distance (controle homeostatico por distancia de
arestas, estilo AILS-PR) nas MESMAS instancias/seeds/orcamentos do
experimento anterior (scripts/h1_ab_results.json), para permitir comparacao
de 3 vias (fixed vs stagnation vs distance) sem re-rodar fixed/stagnation
(esses nao mudaram de comportamento -- so a interface de CLI mudou).
"""
import json
import re
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def run(instance, imax, iils, seed, pert_mode):
    cmd = ["./bin/gils_rvnd", f"instances/{instance}.tsp",
           "--imax", str(imax), "--iils", str(iils), "--seed", str(seed),
           "--pert-mode", pert_mode]
    out = subprocess.run(cmd, capture_output=True, text=True, cwd=PROJECT_ROOT, check=True).stdout
    cost = int(re.search(r"COST (\d+)", out).group(1))
    time_ms = float(re.search(r"TIME_MS ([\d.]+)", out).group(1))
    return cost, time_ms


def main():
    prior = json.load(open(PROJECT_ROOT / "scripts" / "h1_ab_results.json"))

    results = []
    for row in prior:
        instance, imax, iils, seed = row["instance"], row["imax"], row["iils"], row["seed"]
        cost_dist, t_dist = run(instance, imax, iils, seed, "distance")
        merged = dict(row)
        merged["cost_distance"] = cost_dist
        merged["time_distance_ms"] = t_dist
        results.append(merged)
        print(f"{instance} seed={seed}: fixed={row['cost_fixed']} stagnation={row['cost_adaptive']} "
              f"distance={cost_dist} ({t_dist:.0f}ms)", file=sys.stderr)

        out_path = PROJECT_ROOT / "scripts" / "h1_3way_results.json"
        with open(out_path, "w") as f:
            json.dump(results, f, indent=2)

    print(f"done, results written to {out_path}", file=sys.stderr)


if __name__ == "__main__":
    main()
