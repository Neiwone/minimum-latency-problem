"""
Extensao do H12a (docs/experiments/h12-extended-oropt.md) para n=2000
(instancia rand2000, gerada via
`uv run scripts/instance_generator.py --n 2000 --grid 1000 --seed 42`),
seguindo a recomendacao pos-n=1000: testar a combinacao GILS-AM-RVND +
extended-oropt (ja confirmada no agregado em n<=532, e agora que
extended-oropt sozinho mostrou +1.17% com 10W/10 em n=1000) contra o
gils_rvnd baseline puro, na maior escala testada nesta sessao.

Calibracao de 1 seed (--imax 1 --iils 10): baseline=30.621.341/448s,
gils_am_rvnd+extended-oropt=30.189.083/441s -- ja mais rapido E melhor
num unico ponto. Este lote fecha com N=10, pareado por seed.
"""
import json
import math
import re
import statistics
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
RESULTS_PATH = PROJECT_ROOT / "scripts" / "h12a_rand2000_results.json"

INSTANCE = "rand2000"
IMAX = 1
IILS = 10
N_SEEDS = 10


def run(cmd):
    out = subprocess.run(cmd, capture_output=True, text=True, cwd=PROJECT_ROOT, check=True).stdout
    cost = int(re.search(r"COST (\d+)", out).group(1))
    time_ms = float(re.search(r"TIME_MS ([\d.]+)", out).group(1))
    return cost, time_ms


def run_baseline(seed):
    cmd = ["./bin/gils_rvnd", f"instances/{INSTANCE}.tsp",
           "--imax", str(IMAX), "--iils", str(IILS), "--seed", str(seed),
           "--rvnd-mode", "single"]
    return run(cmd)


def run_combo(seed):
    cmd = ["./bin/gils_am_rvnd", f"instances/{INSTANCE}.tsp",
           "--imax", str(IMAX), "--iils", str(IILS), "--seed", str(seed),
           "--rvnd-mode", "extended-oropt"]
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

    for seed in range(1, N_SEEDS + 1):
        if any(r["seed"] == seed for r in results):
            continue

        cost_base, t_base = run_baseline(seed)
        cost_combo, t_combo = run_combo(seed)

        row = {
            "seed": seed,
            "cost_baseline": cost_base, "time_baseline_ms": t_base,
            "cost_combo": cost_combo, "time_combo_ms": t_combo,
        }
        results.append(row)
        print(f"seed={seed}: baseline={cost_base} ({t_base:.0f}ms) "
              f"combo={cost_combo} ({t_combo:.0f}ms)", file=sys.stderr)

        with open(RESULTS_PATH, "w") as f:
            json.dump(results, f, indent=2)

    print_summary(results)


def print_summary(results):
    diffs = [r["cost_baseline"] - r["cost_combo"] for r in results]
    rel = [d / r["cost_baseline"] * 100 for d, r in zip(diffs, results)]
    wins = sum(1 for d in diffs if d > 0)
    losses = sum(1 for d in diffs if d < 0)
    ties = len(results) - wins - losses
    p = sign_test_p(wins, losses)

    tb_vals = [r["time_baseline_ms"] for r in results]
    tc_vals = [r["time_combo_ms"] for r in results]
    med = statistics.median(tb_vals + tc_vals)
    tb_clean = [x for x in tb_vals if x < med * 10]
    tc_clean = [x for x in tc_vals if x < med * 10]
    tb = statistics.mean(tb_clean)
    tc = statistics.mean(tc_clean)
    time_pct = (tc - tb) / tb * 100

    print(f"\n{'instance':10} {'n':>4} {'mean_rel%':>10} {'w/t/l':>10} {'sign_p':>8} {'time+%':>8}")
    print(f"{INSTANCE:10} {len(results):4d} {statistics.mean(rel):10.4f} {wins}/{ties}/{losses:<6} {p:8.3f} {time_pct:8.1f}")


if __name__ == "__main__":
    main()
