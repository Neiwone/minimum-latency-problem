"""
Lote noturno: H12a (Or-opt estendido a segmentos 4/5/6, ver
docs/experiments/h12-extended-oropt.md) -- o diagnostico read-only mostrou
sinal real (12/15 otimos locais de RVND padrao tinham pelo menos 1 movimento
de or-opt4/5/6 melhorando, diferente do quase-zero de H9/H10), e uma
calibracao rapida (1 seed, imax/iils pequenos) em lin318 deu resultado
melhor em qualidade E mais rapido que o --rvnd-mode single. Este lote fecha
isso com poder estatistico real (N>=15-20, pareado por seed).

Para cada instancia/seed, roda 2 vezes com a MESMA seed:
  1. single         -- gils_rvnd baseline (--rvnd-mode single, as 5
                        vizinhancas originais do artigo)
  2. extended-oropt  -- gils_rvnd --rvnd-mode extended-oropt (+ oropt4/5/6)

Uso:
  python3 scripts/night_batch.py                  # config default abaixo
  python3 scripts/night_batch.py --resume          # continua um results.json existente

Ajuste CONFIG antes de rodar se quiser mais/menos seeds ou outras instancias.
"""
import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
RESULTS_PATH = PROJECT_ROOT / "scripts" / "night_batch_results.json"

# (instance, imax, iils, n_seeds)
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


def already_done(results, instance, seed):
    return any(r["instance"] == instance and r["seed"] == seed for r in results)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--resume", action="store_true",
                         help="Continua a partir de scripts/night_batch_results.json existente")
    args = parser.parse_args()

    results = []
    if args.resume and RESULTS_PATH.exists():
        results = json.load(open(RESULTS_PATH))
        print(f"resumindo com {len(results)} resultados existentes", file=sys.stderr)

    for instance, imax, iils, n_seeds in CONFIG:
        for seed in range(1, n_seeds + 1):
            if already_done(results, instance, seed):
                continue

            cost_single, t_single = run_gils(instance, imax, iils, seed, "single")
            cost_extended, t_extended = run_gils(instance, imax, iils, seed, "extended-oropt")

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

    print(f"done, results written to {RESULTS_PATH}", file=sys.stderr)


if __name__ == "__main__":
    main()
