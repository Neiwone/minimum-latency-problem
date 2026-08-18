"""
H12a em n=1000: extensao do achado principal da sessao
(docs/experiments/h12-extended-oropt.md) para a escala onde o efeito
mostrou o maior ganho de qualidade ate agora (1 seed, --imax 1 --iils 100:
extended-oropt deu -1.26% vs single, 10.462.530 vs 10.595.879) -- mas
sem poder estatistico. Este lote fecha isso com N>=10, pareado por seed,
mesmo --imax/--iils da calibracao original (mesma referencia de H8 pra
rand1000).
"""
import json
import math
import re
import statistics
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
RESULTS_PATH = PROJECT_ROOT / "scripts" / "h12a_rand1000_results.json"

INSTANCE = "rand1000"
IMAX = 1
IILS = 100
N_SEEDS = 10


def run(cmd):
    out = subprocess.run(cmd, capture_output=True, text=True, cwd=PROJECT_ROOT, check=True).stdout
    cost = int(re.search(r"COST (\d+)", out).group(1))
    time_ms = float(re.search(r"TIME_MS ([\d.]+)", out).group(1))
    return cost, time_ms


def run_gils(seed, rvnd_mode):
    cmd = ["./bin/gils_rvnd", f"instances/{INSTANCE}.tsp",
           "--imax", str(IMAX), "--iils", str(IILS), "--seed", str(seed),
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

    for seed in range(1, N_SEEDS + 1):
        if any(r["seed"] == seed for r in results):
            continue

        cost_single, t_single = run_gils(seed, "single")
        cost_extended, t_extended = run_gils(seed, "extended-oropt")

        row = {
            "seed": seed,
            "cost_single": cost_single, "time_single_ms": t_single,
            "cost_extended": cost_extended, "time_extended_ms": t_extended,
        }
        results.append(row)
        print(f"seed={seed}: single={cost_single} ({t_single:.0f}ms) "
              f"extended={cost_extended} ({t_extended:.0f}ms)", file=sys.stderr)

        with open(RESULTS_PATH, "w") as f:
            json.dump(results, f, indent=2)

    print_summary(results)


def print_summary(results):
    diffs = [r["cost_single"] - r["cost_extended"] for r in results]
    rel = [d / r["cost_single"] * 100 for d, r in zip(diffs, results)]
    wins = sum(1 for d in diffs if d > 0)
    losses = sum(1 for d in diffs if d < 0)
    ties = len(results) - wins - losses
    p = sign_test_p(wins, losses)

    ts_vals = [r["time_single_ms"] for r in results]
    te_vals = [r["time_extended_ms"] for r in results]
    med = statistics.median(ts_vals + te_vals)
    ts_clean = [x for x in ts_vals if x < med * 10]
    te_clean = [x for x in te_vals if x < med * 10]
    ts = statistics.mean(ts_clean)
    te = statistics.mean(te_clean)
    time_pct = (te - ts) / ts * 100

    print(f"\n{'instance':10} {'n':>4} {'mean_rel%':>10} {'w/t/l':>10} {'sign_p':>8} {'time+%':>8}")
    print(f"{INSTANCE:10} {len(results):4d} {statistics.mean(rel):10.4f} {wins}/{ties}/{losses:<6} {p:8.3f} {time_pct:8.1f}")


if __name__ == "__main__":
    main()
