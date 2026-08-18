"""
H12b: 3-opt genuino (reversao dupla independente de B e C, nao alcancavel
por nenhum movimento unico ja existente -- ver docs/experiments/
h12-extended-oropt.md secao 12) por cima do melhor baseline confirmado
ate agora (extended-oropt, H12a).

Diagnostico read-only (bin/diag_3opt) achou sinal real mas esparso: so
5 de 15 otimos locais testados tinham alguma melhoria de 3-opt disponivel,
mas quando havia, as vezes grande (pr439 trial 2: 122 movimentos
simultaneos melhorando, -0.94% no melhor sozinho).

Calibracao de tempo (1 seed, lin318 imax=5/iils=100): extended-oropt-3opt
levou 4.1x mais tempo que extended-oropt puro (343s vs 84s) e EMPATOU em
custo nesse seed -- sinal preocupante de custo, mas so 1 amostra. Usuario
decidiu rodar o lote completo mesmo assim.

Mesma escala de instancia/imax/iils do teste original de H12a
(scripts/night_batch.py): lin318 imax=5/N=20, pr439 imax=3/N=15,
att532 imax=2/N=10, pareado por seed.
"""
import json
import math
import re
import statistics
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
RESULTS_PATH = PROJECT_ROOT / "scripts" / "h12b_3opt_results.json"

# (instance, imax, iils, n_seeds) -- mesma escala do teste original de H12a
CONFIG = [
    ("lin318", 5, 100, 20),
    ("pr439", 3, 100, 15),
    ("att532", 2, 100, 10),
]


def run(cmd):
    out = subprocess.run(cmd, capture_output=True, text=True, cwd=PROJECT_ROOT, check=True).stdout
    cost = int(re.search(r"COST (\d+)", out).group(1))
    time_ms = float(re.search(r"TIME_MS ([\d.]+)", out).group(1))
    return cost, time_ms


def run_gils(instance, imax, iils, seed, rvnd_mode):
    cmd = ["./bin/gils_rvnd", f"instances/{instance}.tsp",
           "--imax", str(imax), "--iils", str(iils), "--seed", str(seed),
           "--rvnd-mode", rvnd_mode]
    return run(cmd)


def sign_test_p(wins, losses):
    n = wins + losses
    if n == 0:
        return 1.0
    k = min(wins, losses)
    p_le_k = sum(math.comb(n, i) for i in range(0, k + 1)) / (2 ** n)
    return min(1.0, 2 * p_le_k)


def main():
    results = []
    if RESULTS_PATH.exists():
        results = json.load(open(RESULTS_PATH))
        print(f"resumindo com {len(results)} resultados existentes", file=sys.stderr)

    for instance, imax, iils, n_seeds in CONFIG:
        for seed in range(1, n_seeds + 1):
            if any(r["instance"] == instance and r["seed"] == seed for r in results):
                continue

            cost_eo, t_eo = run_gils(instance, imax, iils, seed, "extended-oropt")
            cost_3opt, t_3opt = run_gils(instance, imax, iils, seed, "extended-oropt-3opt")

            row = {
                "instance": instance, "imax": imax, "iils": iils, "seed": seed,
                "cost_extended_oropt": cost_eo, "time_extended_oropt_ms": t_eo,
                "cost_3opt": cost_3opt, "time_3opt_ms": t_3opt,
            }
            results.append(row)
            print(f"{instance} seed={seed}: extended_oropt={cost_eo} ({t_eo:.0f}ms) "
                  f"3opt={cost_3opt} ({t_3opt:.0f}ms)", file=sys.stderr)

            with open(RESULTS_PATH, "w") as f:
                json.dump(results, f, indent=2)

    print_summary(results)


def print_summary(results):
    by_instance = {}
    for r in results:
        by_instance.setdefault(r["instance"], []).append(r)

    print(f"\n{'instance':10} {'n':>4} {'mean_rel%':>10} {'w/t/l':>10} {'sign_p':>8} {'time+%':>8}")
    all_rows = []
    for instance, rows in by_instance.items():
        diffs = [r["cost_extended_oropt"] - r["cost_3opt"] for r in rows]
        rel = [d / r["cost_extended_oropt"] * 100 for d, r in zip(diffs, rows)]
        wins = sum(1 for d in diffs if d > 0)
        losses = sum(1 for d in diffs if d < 0)
        ties = len(rows) - wins - losses
        p = sign_test_p(wins, losses)
        te = statistics.mean(r["time_extended_oropt_ms"] for r in rows)
        t3 = statistics.mean(r["time_3opt_ms"] for r in rows)
        time_pct = (t3 - te) / te * 100
        print(f"{instance:10} {len(rows):4d} {statistics.mean(rel):10.4f} {wins}/{ties}/{losses:<6} {p:8.3f} {time_pct:8.1f}")
        all_rows.extend(rows)

    if all_rows:
        diffs = [r["cost_extended_oropt"] - r["cost_3opt"] for r in all_rows]
        rel = [d / r["cost_extended_oropt"] * 100 for d, r in zip(diffs, all_rows)]
        wins = sum(1 for d in diffs if d > 0)
        losses = sum(1 for d in diffs if d < 0)
        ties = len(all_rows) - wins - losses
        p = sign_test_p(wins, losses)
        te = statistics.mean(r["time_extended_oropt_ms"] for r in all_rows)
        t3 = statistics.mean(r["time_3opt_ms"] for r in all_rows)
        time_pct = (t3 - te) / te * 100
        print(f"{'AGREGADO':10} {len(all_rows):4d} {statistics.mean(rel):10.4f} {wins}/{ties}/{losses:<6} {p:8.3f} {time_pct:8.1f}")


if __name__ == "__main__":
    main()
