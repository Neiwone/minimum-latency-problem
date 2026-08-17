"""
Extensao do teste A/B (fixed vs distance) para ganhar poder estatistico nas
instancias maiores: mais seeds em lin318, e novas rodadas pareadas em
pr439/att532 (que nao estavam no experimento anterior). Roda tudo em
sequencia (nao em paralelo) para nao distorcer as medidas de tempo por
contencao de CPU.
"""
import json
import re
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

# (instance, imax, iils, seeds)
CONFIG = [
    ("lin318", 5, 100, list(range(5, 13))),   # extends seeds 1-4 already collected
    ("pr439", 1, 100, list(range(1, 6))),
    ("att532", 1, 100, list(range(1, 4))),
]


def run(instance, imax, iils, seed, pert_mode):
    cmd = ["./bin/gils_rvnd", f"instances/{instance}.tsp",
           "--imax", str(imax), "--iils", str(iils), "--seed", str(seed),
           "--pert-mode", pert_mode]
    out = subprocess.run(cmd, capture_output=True, text=True, cwd=PROJECT_ROOT, check=True).stdout
    cost = int(re.search(r"COST (\d+)", out).group(1))
    time_ms = float(re.search(r"TIME_MS ([\d.]+)", out).group(1))
    return cost, time_ms


def main():
    results = []
    for instance, imax, iils, seeds in CONFIG:
        for seed in seeds:
            cost_fixed, t_fixed = run(instance, imax, iils, seed, "fixed")
            cost_dist, t_dist = run(instance, imax, iils, seed, "distance")
            results.append({
                "instance": instance, "imax": imax, "iils": iils, "seed": seed,
                "cost_fixed": cost_fixed, "time_fixed_ms": t_fixed,
                "cost_distance": cost_dist, "time_distance_ms": t_dist,
            })
            print(f"{instance} seed={seed}: fixed={cost_fixed} ({t_fixed:.0f}ms) "
                  f"distance={cost_dist} ({t_dist:.0f}ms)", file=sys.stderr)

            out_path = PROJECT_ROOT / "scripts" / "h1_large_results.json"
            with open(out_path, "w") as f:
                json.dump(results, f, indent=2)

    print(f"done, results written to {out_path}", file=sys.stderr)


if __name__ == "__main__":
    main()
