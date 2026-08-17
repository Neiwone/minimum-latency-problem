"""
Teste A/B pareado para H2: GILS-RVND puro vs. GILS-RVND + path relinking
entre um pool de elite (ver src/gils_rvnd.cpp: --path-relinking).

Mesmo desenho do teste de H1 (scripts/h1_ab_test.py): mesma seed em ambos os
modos, --pert-mode fixed em ambos (isola o efeito do path relinking sem
misturar com o mecanismo de H1). Path relinking so' roda uma vez por
reinicio externo (I_max vezes), nao dentro do loop ILS -- overhead esperado
e' baixo mesmo em instancias grandes (confirmado manualmente antes deste
script: lin318 imax=5 teve overhead <1%).
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
    ("pr226", 10, 100, 10),
    ("lin318", 5, 100, 10),
    ("pr439", 1, 100, 6),
    ("att532", 1, 100, 5),
]


def run(instance, imax, iils, seed, path_relinking):
    cmd = ["./bin/gils_rvnd", f"instances/{instance}.tsp",
           "--imax", str(imax), "--iils", str(iils), "--seed", str(seed),
           "--pert-mode", "fixed"]
    if path_relinking:
        cmd.append("--path-relinking")
    out = subprocess.run(cmd, capture_output=True, text=True, cwd=PROJECT_ROOT, check=True).stdout
    cost = int(re.search(r"COST (\d+)", out).group(1))
    time_ms = float(re.search(r"TIME_MS ([\d.]+)", out).group(1))
    return cost, time_ms


def main():
    results = []
    for instance, imax, iils, n_seeds in CONFIG:
        for seed in range(1, n_seeds + 1):
            cost_base, t_base = run(instance, imax, iils, seed, path_relinking=False)
            cost_pr, t_pr = run(instance, imax, iils, seed, path_relinking=True)
            results.append({
                "instance": instance, "imax": imax, "iils": iils, "seed": seed,
                "cost_base": cost_base, "time_base_ms": t_base,
                "cost_pr": cost_pr, "time_pr_ms": t_pr,
            })
            print(f"{instance} seed={seed}: base={cost_base} ({t_base:.0f}ms) "
                  f"pr={cost_pr} ({t_pr:.0f}ms)", file=sys.stderr)

        out_path = PROJECT_ROOT / "scripts" / "h2_ab_results.json"
        with open(out_path, "w") as f:
            json.dump(results, f, indent=2)

    print(f"done, results written to {out_path}", file=sys.stderr)


if __name__ == "__main__":
    main()
