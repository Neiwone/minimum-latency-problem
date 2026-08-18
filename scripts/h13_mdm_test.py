"""
H13: MDM-GILS-RVND (Santana, Plastino & Rosseti, arXiv:1908.10705) --
mineracao de segmentos consecutivos de arestas frequentes no elite set,
splicados como unidade atomica na construcao -- ver
docs/experiments/h13-mdm-gils-rvnd.md.

Diferente do nosso GRASP-AM/GILS-AM-RVND (frequencia de aresta isolada,
ja testado nesta sessao: empata em qualidade, ganha em velocidade), o
paper reporta ganho de qualidade E velocidade crescendo com n (ate
32.78% mais rapido e 19/20 melhores solucoes em n=1000).

Calibracao pequena (3 seeds lin318, 3 seeds att532, rodada concorrente
com outro lote pesado) deu sinal inconclusivo -- mas o proprio paper
reporta efeito modesto nessas escalas tambem (so fica forte a partir de
n~500-1000). Este lote fecha com N>=15-20, pareado por seed, mesma escala
de instancia/imax/iils do teste original de H12a.

mdm_gils_rvnd usa --pool 10 (nao 20) e --sup-min 0.70 --max-patterns 5,
os defaults do binario (== parametros do paper).
"""
import json
import math
import re
import statistics
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
RESULTS_PATH = PROJECT_ROOT / "scripts" / "h13_mdm_results.json"

# (instance, imax, iils, n_seeds) -- mesma escala do teste original de H12a
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


def run_baseline(instance, imax, iils, seed):
    cmd = ["./bin/gils_rvnd", f"instances/{instance}.tsp",
           "--imax", str(imax), "--iils", str(iils), "--seed", str(seed),
           "--rvnd-mode", "single"]
    return run(cmd)


def run_mdm(instance, imax, iils, seed):
    cmd = ["./bin/mdm_gils_rvnd", f"instances/{instance}.tsp",
           "--imax", str(imax), "--iils", str(iils), "--seed", str(seed)]
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

            cost_base, t_base = run_baseline(instance, imax, iils, seed)
            cost_mdm, t_mdm = run_mdm(instance, imax, iils, seed)

            row = {
                "instance": instance, "imax": imax, "iils": iils, "seed": seed,
                "cost_baseline": cost_base, "time_baseline_ms": t_base,
                "cost_mdm": cost_mdm, "time_mdm_ms": t_mdm,
            }
            results.append(row)
            print(f"{instance} seed={seed}: baseline={cost_base} ({t_base:.0f}ms) "
                  f"mdm={cost_mdm} ({t_mdm:.0f}ms)", file=sys.stderr)

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
        diffs = [r["cost_baseline"] - r["cost_mdm"] for r in rows]
        rel = [d / r["cost_baseline"] * 100 for d, r in zip(diffs, rows)]
        wins = sum(1 for d in diffs if d > 0)
        losses = sum(1 for d in diffs if d < 0)
        ties = len(rows) - wins - losses
        p = sign_test_p(wins, losses)
        tb = statistics.mean(r["time_baseline_ms"] for r in rows)
        tm = statistics.mean(r["time_mdm_ms"] for r in rows)
        time_pct = (tm - tb) / tb * 100
        print(f"{instance:10} {len(rows):4d} {statistics.mean(rel):10.4f} {wins}/{ties}/{losses:<6} {p:8.3f} {time_pct:8.1f}")
        all_rows.extend(rows)

    if all_rows:
        diffs = [r["cost_baseline"] - r["cost_mdm"] for r in all_rows]
        rel = [d / r["cost_baseline"] * 100 for d, r in zip(diffs, all_rows)]
        wins = sum(1 for d in diffs if d > 0)
        losses = sum(1 for d in diffs if d < 0)
        ties = len(all_rows) - wins - losses
        p = sign_test_p(wins, losses)
        tb = statistics.mean(r["time_baseline_ms"] for r in all_rows)
        tm = statistics.mean(r["time_mdm_ms"] for r in all_rows)
        time_pct = (tm - tb) / tb * 100
        print(f"{'AGREGADO':10} {len(all_rows):4d} {statistics.mean(rel):10.4f} {wins}/{ties}/{losses:<6} {p:8.3f} {time_pct:8.1f}")


if __name__ == "__main__":
    main()
