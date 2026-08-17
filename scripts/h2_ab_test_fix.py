"""
Correcao do teste de H2 para pr439/att532: a rodada anterior usou --imax 1,
o que faz o path relinking nunca executar de fato (pool de elite comeca
vazio e so ganha o primeiro membro depois do unico reinicio terminar -- nao
ha um segundo reinicio para relinkar contra ele). Aqui usamos imax>=2 para
dar ao mecanismo pelo menos uma chance real de rodar.
"""
import json
import re
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

# (instance, imax, iils, n_seeds)
CONFIG = [
    ("pr439", 3, 100, 6),
    ("att532", 2, 100, 4),
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

        out_path = PROJECT_ROOT / "scripts" / "h2_ab_results_fix.json"
        with open(out_path, "w") as f:
            json.dump(results, f, indent=2)

    print(f"done, results written to {out_path}", file=sys.stderr)


if __name__ == "__main__":
    main()
