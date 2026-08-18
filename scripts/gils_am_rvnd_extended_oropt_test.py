"""
Follow-up de H12a: GILS-AM-RVND ja empata em qualidade com o gils_rvnd
baseline mas e' 20-26% mais rapido (grasp-am-large-scale.md) -- diferente
do grasp_am (sem laco de ILS), ele tem a mesma profundidade de
perturbacao+RVND do baseline, entao nao compartilha o mecanismo que fez o
extended-oropt virar ruido la (h12-extended-oropt.md secao 11).

Pergunta: os dois ganhos independentes (velocidade aqui, qualidade em
H12a) se compoem? Ou seja, --rvnd-mode extended-oropt no GILS-AM-RVND da'
algo mais rapido E melhor que o gils_rvnd puro?

Calibracao de 1 seed em lin318 (imax=10/iils=100): single=5578900/50.2s,
extended=5560679/109.5s -- direcao favoravel mas so 1 seed. Lote pareado
com N>=15-20, mesma escala do teste original de GILS-AM-RVND.
"""
import json
import math
import re
import statistics
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
RESULTS_PATH = PROJECT_ROOT / "scripts" / "gils_am_rvnd_extended_oropt_results.json"

# (instance, imax, iils, n_seeds) -- mesma escala de grasp-am-large-scale.md secao 5
CONFIG = [
    ("lin318", 10, 100, 20),
    ("pr439", 5, 100, 15),
    ("att532", 3, 100, 10),
]


def run(cmd):
    out = subprocess.run(cmd, capture_output=True, text=True, cwd=PROJECT_ROOT, check=True).stdout
    cost = int(re.search(r"COST (\d+)", out).group(1))
    time_ms = float(re.search(r"TIME_MS ([\d.]+)", out).group(1))
    return cost, time_ms


def run_gils_am(instance, imax, iils, seed, rvnd_mode):
    cmd = ["./bin/gils_am_rvnd", f"instances/{instance}.tsp",
           "--imax", str(imax), "--iils", str(iils), "--seed", str(seed),
           "--parent-mode", "pool", "--rvnd-mode", rvnd_mode]
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

            cost_single, t_single = run_gils_am(instance, imax, iils, seed, "single")
            cost_extended, t_extended = run_gils_am(instance, imax, iils, seed, "extended-oropt")

            row = {
                "instance": instance, "imax": imax, "iils": iils, "seed": seed,
                "cost_single": cost_single, "time_single_ms": t_single,
                "cost_extended": cost_extended, "time_extended_ms": t_extended,
            }
            results.append(row)
            print(f"{instance} seed={seed}: single={cost_single} ({t_single:.0f}ms) "
                  f"extended={cost_extended} ({t_extended:.0f}ms)", file=sys.stderr)

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
        diffs = [r["cost_single"] - r["cost_extended"] for r in rows]
        rel = [d / r["cost_single"] * 100 for d, r in zip(diffs, rows)]
        wins = sum(1 for d in diffs if d > 0)
        losses = sum(1 for d in diffs if d < 0)
        ties = len(rows) - wins - losses
        p = sign_test_p(wins, losses)
        ts = statistics.mean(r["time_single_ms"] for r in rows)
        te = statistics.mean(r["time_extended_ms"] for r in rows)
        time_pct = (te - ts) / ts * 100
        print(f"{instance:10} {len(rows):4d} {statistics.mean(rel):10.4f} {wins}/{ties}/{losses:<6} {p:8.3f} {time_pct:8.1f}")
        all_rows.extend(rows)

    if all_rows:
        diffs = [r["cost_single"] - r["cost_extended"] for r in all_rows]
        rel = [d / r["cost_single"] * 100 for d, r in zip(diffs, all_rows)]
        wins = sum(1 for d in diffs if d > 0)
        losses = sum(1 for d in diffs if d < 0)
        ties = len(all_rows) - wins - losses
        p = sign_test_p(wins, losses)
        ts = statistics.mean(r["time_single_ms"] for r in all_rows)
        te = statistics.mean(r["time_extended_ms"] for r in all_rows)
        time_pct = (te - ts) / ts * 100
        print(f"{'AGREGADO':10} {len(all_rows):4d} {statistics.mean(rel):10.4f} {wins}/{ties}/{losses:<6} {p:8.3f} {time_pct:8.1f}")


if __name__ == "__main__":
    main()
