"""
Teste A/B pareado para H1: double-bridge de intensidade fixa vs. adaptativa
(intensidade cresce com o contador de estagnacao iterILS, reseta a 1 na
melhoria -- ver src/gils_rvnd.cpp).

Para cada instancia e cada seed, roda o mesmo binario ./bin/gils_rvnd duas
vezes com o MESMO --seed (RNG deterministico), uma vez sem --adaptive
(baseline) e uma vez com --adaptive, e registra custo final e tempo. Mesma
seed em ambos os modos = comparacao pareada (a diferenca isola o efeito da
politica de perturbacao, nao ruido de amostragem de outra fonte).
"""
import json
import re
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

# (instance, imax, iils, n_seeds)
CONFIG = [
    ("eil51", 10, 100, 20),
    ("st70", 10, 100, 20),
    ("pr76", 10, 100, 20),
    ("kroA100", 10, 100, 15),
    ("lin105", 10, 100, 15),
    ("pr226", 10, 100, 8),
    ("lin318", 5, 100, 4),
]


def run(instance, imax, iils, seed, adaptive):
    cmd = ["./bin/gils_rvnd", f"instances/{instance}.tsp",
           "--imax", str(imax), "--iils", str(iils), "--seed", str(seed)]
    if adaptive:
        cmd.append("--adaptive")
    out = subprocess.run(cmd, capture_output=True, text=True, cwd=PROJECT_ROOT, check=True).stdout
    cost = int(re.search(r"COST (\d+)", out).group(1))
    time_ms = float(re.search(r"TIME_MS ([\d.]+)", out).group(1))
    return cost, time_ms


def main():
    results = []
    for instance, imax, iils, n_seeds in CONFIG:
        for seed in range(1, n_seeds + 1):
            cost_fixed, t_fixed = run(instance, imax, iils, seed, adaptive=False)
            cost_adapt, t_adapt = run(instance, imax, iils, seed, adaptive=True)
            results.append({
                "instance": instance, "imax": imax, "iils": iils, "seed": seed,
                "cost_fixed": cost_fixed, "time_fixed_ms": t_fixed,
                "cost_adaptive": cost_adapt, "time_adaptive_ms": t_adapt,
            })
            print(f"{instance} seed={seed}: fixed={cost_fixed} ({t_fixed:.0f}ms) "
                  f"adaptive={cost_adapt} ({t_adapt:.0f}ms)", file=sys.stderr)

        out_path = PROJECT_ROOT / "scripts" / "h1_ab_results.json"
        with open(out_path, "w") as f:
            json.dump(results, f, indent=2)

    print(f"done, results written to {out_path}", file=sys.stderr)


if __name__ == "__main__":
    main()
