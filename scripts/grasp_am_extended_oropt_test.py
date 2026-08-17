"""
Follow-up de H12a: grasp_am usa exatamente 1 convergencia de RVND por
construcao (sem laco de ILS/escape) -- fraqueza ja diagnosticada em
docs/experiments/grasp-am-large-scale.md (perde ~1-2% do gils_rvnd
baseline por falta de intensificacao, nao pela memoria adaptativa em si).
Testamos se usar --rvnd-mode extended-oropt (or-opt com segmentos 4-6,
H12a) nessa unica convergencia fecha parte dessa lacuna sem precisar da
reestruturacao completa que o GILS-AM-RVND fez.

Calibracao rapida (5 seeds, lin318, iter=200) deu sinal positivo mas
misto (3W/2L, alguns ganhos grandes de ~1-1.8%) -- maior que o
+0.33%/+0.39% visto no gils_rvnd puro (H12a), plausivelmente porque
grasp_am tem mais a ganhar de uma vizinhanca mais forte, ja que nunca
tem chance de reescapar via double-bridge. Este lote fecha com N>=15-20,
pareado por seed, mesma config de instancia/iter do doc de
grasp-am-large-scale.md (--parent-mode pool, o modo original).
"""
import json
import math
import re
import statistics
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
RESULTS_PATH = PROJECT_ROOT / "scripts" / "grasp_am_extended_oropt_results.json"

# (instance, iter, n_seeds) -- mesma escala de grasp-am-large-scale.md
CONFIG = [
    ("lin318", 800, 20),
    ("pr439", 500, 15),
    ("att532", 300, 10),
]


def run(cmd):
    out = subprocess.run(cmd, capture_output=True, text=True, cwd=PROJECT_ROOT, check=True).stdout
    cost = int(re.search(r"COST (\d+)", out).group(1))
    time_ms = float(re.search(r"TIME_MS ([\d.]+)", out).group(1))
    return cost, time_ms


def run_grasp_am(instance, n_iter, seed, rvnd_mode):
    cmd = ["./bin/grasp_am", f"instances/{instance}.tsp",
           "--iter", str(n_iter), "--seed", str(seed),
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

    for instance, n_iter, n_seeds in CONFIG:
        for seed in range(1, n_seeds + 1):
            if any(r["instance"] == instance and r["seed"] == seed for r in results):
                continue

            cost_single, t_single = run_grasp_am(instance, n_iter, seed, "single")
            cost_extended, t_extended = run_grasp_am(instance, n_iter, seed, "extended-oropt")

            row = {
                "instance": instance, "iter": n_iter, "seed": seed,
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
