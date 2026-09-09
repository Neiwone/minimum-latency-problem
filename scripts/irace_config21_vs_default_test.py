"""
Validacao da configuracao vencedora do irace (config 21) contra o default
adotado do projeto, nas 10 instancias TSPLIB de reporte (mesmo conjunto de
run_experiments.py), pareado por seed -- ver irace/README.md secao 6 e
memoria feedback-experiment-rigor.

irace (6 instancias de treino, 2000 experimentos) elegeu, da melhor pra pior
soma de ranks:
  21  --pool 47 --lambda 0.1746 --parent-mode pool --rvnd-mode extended-oropt-wide
  31  --pool 15 --lambda 0.2371 --parent-mode pair --rvnd-mode extended-oropt-wide
  65  --pool 42 --lambda 0.4324 --parent-mode pair --rvnd-mode single
  113 --pool 47 --lambda 0.6107 --parent-mode pair --rvnd-mode extended-oropt

As duas melhores escolheram extended-oropt-wide, e nao o extended-oropt que
e' o achado atualmente adotado. Isso so vale nas instancias de treino; aqui
confirmamos (ou nao) o ganho nas instancias de reporte, pareado por seed.

  BASELINE (default adotado): --rvnd-mode extended-oropt
                              (pool 20, lambda 0.50, parent-mode pool -- defaults do binario)
  CONFIG 21 (vencedor irace): --pool 47 --lambda 0.1746 --parent-mode pool --rvnd-mode extended-oropt-wide

Orcamento cheio (imax=10/iils=100) em todas as 10, 20 seeds. Instancias
grandes (lin318/pr439/att532) sao lentas nesse orcamento -- checkpoint e'
gravado apos cada par (instancia, seed) e a run retoma do JSON se cair.
"""
import json
import math
import re
import statistics
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
RESULTS_PATH = PROJECT_ROOT / "scripts" / "irace_config21_vs_default_results.json"

# As 10 instancias TSPLIB de reporte (INSTANCES em run_experiments.py).
INSTANCES = [
    "st70", "rat99", "kroD100", "lin105", "pr107",
    "rat195", "pr226", "lin318", "pr439", "att532",
]
IMAX = 10
IILS = 100
N_SEEDS = 20

# Flags fixas de cada lado (alem de --seed). Baseline = default adotado;
# config21 = vencedor do irace.
BASELINE_ARGS = ["--rvnd-mode", "extended-oropt"]
CONFIG21_ARGS = ["--pool", "47", "--lambda", "0.1746",
                 "--parent-mode", "pool", "--rvnd-mode", "extended-oropt-wide"]


def run(cmd):
    out = subprocess.run(cmd, capture_output=True, text=True,
                         cwd=PROJECT_ROOT, check=True).stdout
    cost = int(re.search(r"COST (\d+)", out).group(1))
    time_ms = float(re.search(r"TIME_MS ([\d.]+)", out).group(1))
    return cost, time_ms


def run_variant(instance, seed, extra_args):
    cmd = ["./bin/gils_am_rvnd", f"instances/{instance}.tsp",
           "--imax", str(IMAX), "--iils", str(IILS), "--seed", str(seed),
           *extra_args]
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

    for instance in INSTANCES:
        for seed in range(1, N_SEEDS + 1):
            if any(r["instance"] == instance and r["seed"] == seed for r in results):
                continue

            cost_base, t_base = run_variant(instance, seed, BASELINE_ARGS)
            cost_c21, t_c21 = run_variant(instance, seed, CONFIG21_ARGS)

            row = {
                "instance": instance, "imax": IMAX, "iils": IILS, "seed": seed,
                "cost_baseline": cost_base, "time_baseline_ms": t_base,
                "cost_config21": cost_c21, "time_config21_ms": t_c21,
            }
            results.append(row)
            print(f"{instance} seed={seed}: baseline={cost_base} ({t_base:.0f}ms) "
                  f"config21={cost_c21} ({t_c21:.0f}ms)", file=sys.stderr)

            with open(RESULTS_PATH, "w") as f:
                json.dump(results, f, indent=2)

    print_summary(results)


def _summarize(rows):
    # diff > 0  =>  config21 melhor (custo menor que o baseline)
    diffs = [r["cost_baseline"] - r["cost_config21"] for r in rows]
    rel = [d / r["cost_baseline"] * 100 for d, r in zip(diffs, rows)]
    wins = sum(1 for d in diffs if d > 0)
    losses = sum(1 for d in diffs if d < 0)
    ties = len(rows) - wins - losses
    p = sign_test_p(wins, losses)
    tb = statistics.mean(r["time_baseline_ms"] for r in rows)
    tc = statistics.mean(r["time_config21_ms"] for r in rows)
    time_pct = (tc - tb) / tb * 100 if tb else 0.0
    return statistics.mean(rel), wins, ties, losses, p, time_pct


def print_summary(results):
    by_instance = {}
    for r in results:
        by_instance.setdefault(r["instance"], []).append(r)

    print("\nmean_rel% > 0 favorece config21 (custo menor); w/t/l conta vitorias da config21")
    print(f"time+% = quanto config21 e' mais lenta que o baseline\n")
    print(f"{'instance':10} {'n':>4} {'mean_rel%':>10} {'w/t/l':>10} {'sign_p':>8} {'time+%':>8}")

    # ordena pelas 10 instancias na ordem canonica, depois qualquer extra
    ordered = [i for i in INSTANCES if i in by_instance]
    ordered += [i for i in by_instance if i not in INSTANCES]
    for instance in ordered:
        rows = by_instance[instance]
        mean_rel, wins, ties, losses, p, time_pct = _summarize(rows)
        print(f"{instance:10} {len(rows):4d} {mean_rel:10.4f} "
              f"{f'{wins}/{ties}/{losses}':>10} {p:8.3f} {time_pct:8.1f}")

    all_rows = [r for rows in by_instance.values() for r in rows]
    if all_rows:
        mean_rel, wins, ties, losses, p, time_pct = _summarize(all_rows)
        print(f"{'AGREGADO':10} {len(all_rows):4d} {mean_rel:10.4f} "
              f"{f'{wins}/{ties}/{losses}':>10} {p:8.3f} {time_pct:8.1f}")


if __name__ == "__main__":
    main()
