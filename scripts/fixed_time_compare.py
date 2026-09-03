"""
Equal-time comparison of the project's main algorithms.

Every algorithm gets the SAME wall-clock budget per run (--max-time, added
to gils_rvnd / gils_am_rvnd / mdm_gils_rvnd) instead of the same iteration
count, which is the only fair way to compare them: their per-iteration cost
differs a lot (extended-oropt scans more neighborhoods, mdm shells out to
FPMax*), so equal iterations means unequal compute. This mirrors the
"running time as stopping criterion" experiment of the MDM-GILS-RVND paper
(Santana, Plastino & Rosseti, arXiv:1908.10705, Section 5.3.3).

Two protocol requirements, both learned the hard way in this project:

  1. SEQUENTIAL EXECUTION. Timing comparisons are meaningless under CPU
     contention -- running 6 solvers at once on 6 cores inflated per-run
     times by 2-5x and with high variance (see
     docs/experiments/salehipour-tsplib-mdm-vs-am-extended.md section 2).
     This script therefore runs ONE process at a time, always.

  2. THE BUDGET MUST FIT SEVERAL RESTARTS. Both mdm_gils_rvnd (mining
     phase) and gils_am_rvnd (adaptive-memory construction) only do
     anything interesting at restart boundaries: mdm switches to the
     mining phase at half the budget and needs a later restart to use the
     patterns, and gils_am_rvnd's construction needs an elite pool that
     only fills after the first restart. With --iils 100 on lin318 and a
     20s budget, only 2 restarts fit and mining never fires
     (MINING_CALLS 0) -- the algorithms degenerate to plain GILS-RVND.
     So --iils must be small enough that several restarts fit in the
     budget. The script records RESTARTS / MINING_CALLS for every run and
     flags any run where the mechanism did not fire, instead of silently
     reporting a null result.

Usage examples:
  python3 scripts/fixed_time_compare.py --instances lin318 pr439 att532 \
      --time-limit 60 --iils 10 --seeds 10
  python3 scripts/fixed_time_compare.py --salehipour 500 --time-limit 120 \
      --iils 10 --seeds 5
"""
import argparse
import json
import math
import statistics
import subprocess
import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

# name -> (binary, extra args). Keep the keys stable: they end up in the
# checkpoint and in the generated tables.
SOLVERS = {
    "gils_rvnd": ("bin/gils_rvnd", []),
    "gils_am_rvnd": ("bin/gils_am_rvnd", []),
    "gils_am_rvnd_extended_oropt": ("bin/gils_am_rvnd", ["--rvnd-mode", "extended-oropt"]),
    "gils_am_rvnd_adaptive_oropt": ("bin/gils_am_rvnd", ["--rvnd-mode", "adaptive-oropt"]),
    "gils_rvnd_extended_oropt": ("bin/gils_rvnd", ["--rvnd-mode", "extended-oropt"]),
    "gils_rvnd_adaptive_oropt": ("bin/gils_rvnd", ["--rvnd-mode", "adaptive-oropt"]),
    "mdm_gils_rvnd": ("bin/mdm_gils_rvnd", []),
}

DEFAULT_SOLVERS = ["gils_rvnd", "gils_am_rvnd_extended_oropt", "mdm_gils_rvnd"]


def sign_test_p(wins: int, losses: int) -> float:
    n = wins + losses
    if n == 0:
        return 1.0
    k = min(wins, losses)
    p_le_k = sum(math.comb(n, i) for i in range(k + 1)) / (2 ** n)
    return min(1.0, 2 * p_le_k)


def parse_output(stdout: str) -> dict:
    data = {}
    for line in stdout.strip().splitlines():
        parts = line.split(maxsplit=1)
        if len(parts) == 2:
            data[parts[0]] = parts[1]
    return data


def run_once(solver_name: str, inst_path: Path, seed: int, time_limit: float,
             iils: int) -> dict:
    binary, extra = SOLVERS[solver_name]
    cmd = [str(PROJECT_ROOT / binary), str(inst_path),
           "--max-time", str(time_limit), "--iils", str(iils), "--seed", str(seed)] + extra

    wall0 = time.time()
    proc = subprocess.run(cmd, capture_output=True, text=True)
    wall = time.time() - wall0

    if proc.returncode != 0:
        raise RuntimeError(f"{' '.join(cmd)} -> rc={proc.returncode}: {proc.stderr[:400]}")

    d = parse_output(proc.stdout)
    return {
        "cost": float(d["COST"]),
        "time_ms": float(d.get("TIME_MS", 0.0)),
        "wall_s": wall,
        "restarts": int(d.get("RESTARTS", -1)),
        "mining_calls": int(d.get("MINING_CALLS", -1)),
        "pattern_restarts": int(d.get("PATTERN_RESTARTS", -1)),
        "adapt_kmax_final": int(d.get("ADAPT_KMAX_FINAL", -1)),
        "adapt_kmax_range": d.get("ADAPT_KMAX_RANGE", ""),
    }


def instance_paths(args) -> list:
    paths = []
    if args.salehipour:
        for size in args.salehipour:
            for i in range(1, args.salehipour_count + 1):
                paths.append(PROJECT_ROOT / "instances" / "salehipour"
                             / f"salehipour_n{size:04d}_i{i:02d}.tsp")
    for name in args.instances or []:
        p = PROJECT_ROOT / "instances" / (name if name.endswith(".tsp") else name + ".tsp")
        paths.append(p)
    missing = [p for p in paths if not p.exists()]
    if missing:
        sys.exit(f"instancias inexistentes: {', '.join(str(m) for m in missing)}")
    if not paths:
        sys.exit("nenhuma instancia selecionada (use --instances e/ou --salehipour)")
    return paths


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--instances", nargs="*", help="nomes em instances/ (ex: lin318 att532)")
    ap.add_argument("--salehipour", nargs="*", type=int, default=[],
                    help="tamanhos do benchmark Salehipour (ex: 500 1000)")
    ap.add_argument("--salehipour-count", type=int, default=20,
                    help="quantas instancias por tamanho (default 20)")
    ap.add_argument("--time-limit", type=float, required=True,
                    help="orcamento de tempo por execucao, em segundos (igual pra todos)")
    ap.add_argument("--iils", type=int, default=10,
                    help="I_ILS: menor => restarts mais curtos => mais restarts cabem no "
                         "orcamento (necessario pro mdm minerar e pro AM ter memoria). "
                         "Default 10.")
    ap.add_argument("--seeds", type=int, default=10, help="seeds por instancia (1..N)")
    ap.add_argument("--solvers", nargs="*", default=DEFAULT_SOLVERS,
                    help=f"default: {' '.join(DEFAULT_SOLVERS)}")
    ap.add_argument("--baseline", default="gils_rvnd",
                    help="solver de referencia nas comparacoes pareadas")
    ap.add_argument("--checkpoint", default=None,
                    help="arquivo de checkpoint (default: scripts/fixed_time_<T>s.json)")
    args = ap.parse_args()

    for s in args.solvers + [args.baseline]:
        if s not in SOLVERS:
            sys.exit(f"solver desconhecido: {s}\ndisponiveis: {', '.join(SOLVERS)}")

    paths = instance_paths(args)
    ckpt = Path(args.checkpoint) if args.checkpoint else \
        Path(__file__).resolve().parent / f"fixed_time_{int(args.time_limit)}s.json"

    results = json.loads(ckpt.read_text()) if ckpt.exists() else {}
    if results:
        print(f"retomando de {ckpt} ({len(results)} runs ja feitos)", flush=True)

    total = len(paths) * len(args.solvers) * args.seeds
    done = 0
    t0 = time.time()

    # Sequential on purpose: see module docstring, requirement 1.
    for inst in paths:
        for solver in args.solvers:
            for seed in range(1, args.seeds + 1):
                key = f"{inst.stem}|{solver}|{seed}"
                if key in results:
                    done += 1
                    continue
                try:
                    r = run_once(solver, inst, seed, args.time_limit, args.iils)
                except RuntimeError as e:
                    print(f"FALHOU {key}: {e}", flush=True)
                    continue
                results[key] = r
                ckpt.write_text(json.dumps(results))
                done += 1
                flag = ""
                if solver == "mdm_gils_rvnd" and r["mining_calls"] == 0:
                    flag = "  [!] mineracao NAO disparou"
                elif r["restarts"] in (0, 1):
                    flag = f"  [!] apenas {r['restarts']} restart(s)"
                print(f"[{done}/{total}] {inst.stem:22s} {solver:30s} seed={seed:<3d}"
                      f" cost={r['cost']:.0f} t={r['time_ms']/1000:.1f}s"
                      f" restarts={r['restarts']} mining={r['mining_calls']}{flag}",
                      flush=True)

    print(f"\nconcluido em {(time.time()-t0)/60:.1f} min; checkpoint: {ckpt}\n", flush=True)
    report(results, paths, args)


def report(results: dict, paths: list, args) -> None:
    base = args.baseline
    others = [s for s in args.solvers if s != base]

    print(f"{'='*100}")
    print(f"Comparacao com tempo fixo de {args.time_limit:.0f}s por execucao "
          f"(--iils {args.iils}, {args.seeds} seeds, execucao sequencial)")
    print(f"{'='*100}\n")

    # Per-instance sanity: were the restart-boundary mechanisms exercised?
    print("Sanidade do protocolo (mecanismos que vivem em fronteira de restart):")
    for solver in args.solvers:
        rs, mining_zero = [], 0
        for inst in paths:
            for seed in range(1, args.seeds + 1):
                r = results.get(f"{inst.stem}|{solver}|{seed}")
                if not r:
                    continue
                rs.append(r["restarts"])
                if solver == "mdm_gils_rvnd" and r["mining_calls"] == 0:
                    mining_zero += 1
        if not rs:
            continue
        msg = f"  {solver:30s} restarts medio={statistics.mean(rs):6.1f} min={min(rs)}"
        if solver == "mdm_gils_rvnd":
            msg += f"  runs sem mineracao={mining_zero}/{len(rs)}"
            if mining_zero:
                msg += "  <== resultado NAO interpretavel pra esses runs"
        print(msg)
    print()

    for solver in others:
        print(f"--- {solver} vs {base} ---")
        print(f"{'instancia':22s} {'mean_rel%':>10s} {'w/t/l':>10s} {'sign_p':>8s} "
              f"{'custo_base':>13s} {'custo_solver':>13s}")
        agg_w = agg_t = agg_l = 0
        agg_rel = []
        for inst in paths:
            rels, w, t, l = [], 0, 0, 0
            cb_all, cs_all = [], []
            for seed in range(1, args.seeds + 1):
                rb = results.get(f"{inst.stem}|{base}|{seed}")
                rs_ = results.get(f"{inst.stem}|{solver}|{seed}")
                if not rb or not rs_:
                    continue
                cb, cs = rb["cost"], rs_["cost"]
                cb_all.append(cb)
                cs_all.append(cs)
                rels.append((cs - cb) / cb * 100.0)
                if cs < cb:
                    w += 1
                elif cs > cb:
                    l += 1
                else:
                    t += 1
            if not rels:
                continue
            agg_w += w; agg_t += t; agg_l += l
            agg_rel += rels
            print(f"{inst.stem:22s} {statistics.mean(rels):+10.3f} {f'{w}/{t}/{l}':>10s} "
                  f"{sign_test_p(w, l):8.4f} {statistics.mean(cb_all):13.1f} "
                  f"{statistics.mean(cs_all):13.1f}")
        if agg_rel:
            print(f"{'AGREGADO':22s} {statistics.mean(agg_rel):+10.3f} "
                  f"{f'{agg_w}/{agg_t}/{agg_l}':>10s} {sign_test_p(agg_w, agg_l):8.4f}")
        print()


if __name__ == "__main__":
    main()
