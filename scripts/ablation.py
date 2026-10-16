#!/usr/bin/env python3
"""
Ablation from GILS-RVND (as published) to the proposed gils_am_rvnd_dlb.

Two families of arms, run in the same batch so they share the pairing:

  chain  -- cumulative: each arm adds ONE component to the previous one,
            from ./bin/gils_rvnd up to gils_am_rvnd_dlb. Each step is
            compared against the step before it (marginal gain) and
            against the first arm (cumulative gain).
  loo    -- leave-one-out from the final method: each arm is
            gils_am_rvnd_dlb with one piece removed, compared against the
            full method.

Two suites (--suite):

  screen30     30 s, 3 concurrent jobs, 10 instances n = 200..1002; the loo
               family removes each neighborhood (--cand-drop).
  official100  100 s, sequential (the fixed-time protocol), 6 instances
               n >= 500; the chain adds pruning before the extra
               neighborhoods, and the loo family removes each component.

Scheduling follows scripts/screen_parallel.py: every arm of one
(instance, seed) cell runs before the next cell, in groups of exactly
--jobs concurrent processes (padded with a throwaway run), so every
measured run sees the same machine load. The arm order inside a cell is
shuffled with the seed, so which arms share a group is not systematic.

Every tour is checked independently -- a permutation of 0..n-1 from the
depot, latency recomputed from the instance file -- before it is saved.

    python3 scripts/ablation.py --out results/ablation/ablation_30s.json
    python3 scripts/ablation.py --suite official100 --out results/ablation/ablation_100s.json
    python3 scripts/ablation.py --out results/ablation/ablation_30s.json --report-only
"""
import argparse, json, os, random, subprocess, sys, time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from registry import BEST_SOLUTIONS_FILE, ROOT
from stats import compare_pairs
from verify_tour import dist, read_instance

R = "./bin/gils_rvnd"
AM = "./bin/gils_am_rvnd"
DLB = ["--rvnd-mode", "candidate-dlb", "--cand-k", "12"]

# (label, binary, args, description). Order is the order components are added.
CHAIN = [
    ("c0_gils_rvnd",  R,  ["--iils", "100"],
     "GILS-RVND: 5 vizinhancas, varredura O(n^2), I_ILS=100"),
    ("c1_oropt4-6",   R,  ["--rvnd-mode", "extended-oropt", "--iils", "100"],
     "+ or-opt de comprimento 4, 5 e 6 (8 vizinhancas)"),
    ("c2_rev2-6",     R,  ["--rvnd-mode", "extended-oropt-rev", "--iils", "100"],
     "+ or-opt invertido 2 a 6 (13 vizinhancas)"),
    ("c3_cand",       R,  ["--rvnd-mode", "candidate", "--cand-k", "12", "--iils", "100"],
     "+ lista de candidatos K=12 e varredura continua"),
    ("c4_dlb",        R,  DLB + ["--iils", "100"],
     "+ don't-look bits e aplicacao em O(span)"),
    ("c5_iils300",    R,  DLB + ["--iils", "300"],
     "+ I_ILS=300"),
    ("c6_rcl_thresh", AM, DLB + ["--iils", "300", "--lambda", "0"],
     "+ construcao com RCL por limiar (gils_am_rvnd, lambda=0)"),
    ("c7_am",         AM, DLB + ["--iils", "300"],
     "+ memoria adaptativa (lambda=0.5) = gils_am_rvnd_dlb"),
]
LOO_DROPS = (["swap", "2opt"] + [f"oropt{L}" for L in range(1, 7)]
             + [f"rev{L}" for L in range(2, 7)])
LOO_GROUPS = [
    ("oropt4-6", "oropt4,oropt5,oropt6"),
    ("rev2-6",   "rev2,rev3,rev4,rev5,rev6"),
    ("ext",      "oropt4,oropt5,oropt6,rev2,rev3,rev4,rev5,rev6"),
]
LOO = ([(f"d_{d}", AM, DLB + ["--iils", "300", "--cand-drop", d], f"sem {d}")
        for d in LOO_DROPS]
       + [(f"d_{g}", AM, DLB + ["--iils", "300", "--cand-drop", csv], f"sem {g}")
          for g, csv in LOO_GROUPS])

EXT = "oropt4,oropt5,oropt6,rev2,rev3,rev4,rev5,rev6"
CAND = ["--rvnd-mode", "candidate", "--cand-k", "12"]

# Pruning goes in before the extra neighborhoods: under a full O(n^2) scan
# every extra neighborhood costs iterations, which screen30 showed hides
# what the neighborhoods are worth once the scan is cheap.
CHAIN100 = [
    ("k0_gils_rvnd", R,  ["--iils", "100"],
     "GILS-RVND: 5 vizinhancas, varredura O(n^2), I_ILS=100"),
    ("k1_cand",      R,  CAND + ["--cand-drop", EXT, "--iils", "100"],
     "+ lista de candidatos K=12 e varredura continua (5 vizinhancas)"),
    ("k2_ext",       R,  CAND + ["--iils", "100"],
     "+ or-opt 4-6 e or-opt invertido 2-6 (13 vizinhancas)"),
    ("k3_dlb",       R,  DLB + ["--iils", "100"],
     "+ don't-look bits e aplicacao em O(span)"),
    ("k4_iils300",   R,  DLB + ["--iils", "300"],
     "+ I_ILS=300"),
    ("k5_rcl_thresh", AM, DLB + ["--iils", "300", "--lambda", "0"],
     "+ construcao com RCL por limiar (gils_am_rvnd, lambda=0)"),
    ("k6_am",        AM, DLB + ["--iils", "300"],
     "+ memoria adaptativa (lambda=0.5) = gils_am_rvnd_dlb"),
]
# A label already in the chain is reused, not run twice.
LOO100 = [
    ("x_cand", AM, ["--rvnd-mode", "extended-oropt-rev", "--iils", "300"],
     "sem lista de candidatos (varredura completa; o DLB sai junto)"),
    ("x_dlb",  AM, CAND + ["--iils", "300"],
     "sem don't-look bits"),
    ("x_iils", AM, DLB + ["--iils", "100"],
     "I_ILS=100 em vez de 300"),
    ("x_ext",  AM, DLB + ["--iils", "300", "--cand-drop", EXT],
     "sem as 8 vizinhancas extras (so as 5 do artigo)"),
    ("k5_rcl_thresh", AM, DLB + ["--iils", "300", "--lambda", "0"],
     "sem memoria adaptativa (lambda=0)"),
    ("k4_iils300", R, DLB + ["--iils", "300"],
     "sem memoria e com a construcao do GILS-RVND (gils_rvnd)"),
]

SUITES = {
    "screen30": dict(
        instances=["kroA200", "a280", "lin318", "rd400", "pr439",
                   "pcb442", "att532", "rat575", "rat783", "pr1002"],
        time_limit=30.0, jobs=3, chain=CHAIN, loo=LOO,
        loo_title="Leave-one-out das vizinhancas"),
    "official100": dict(
        instances=["att532", "rat783", "pr1002", "pcb1173", "d1291", "nrw1379"],
        time_limit=100.0, jobs=1, chain=CHAIN100, loo=LOO100,
        loo_title="Leave-one-out dos componentes"),
}


def suite_arms(suite):
    chain_labels = {lab for lab, *_ in suite["chain"]}
    return suite["chain"] + [a for a in suite["loo"] if a[0] not in chain_labels]


# ---------------------------------------------------------------- running

_inst_cache = {}


def recompute_latency(inst_path, route):
    if inst_path not in _inst_cache:
        _inst_cache[inst_path] = read_instance(inst_path)
    coords, etype, matrix = _inst_cache[inst_path]
    n = len(coords)
    if sorted(route) != list(range(n)) or route[0] != 0:
        return None
    acc = lat = 0
    for i in range(1, n):
        if matrix is not None:
            acc += matrix[route[i - 1]][route[i]]
        else:
            acc += dist(coords[route[i - 1] + 1], coords[route[i] + 1], etype)
        lat += acc
    return lat


def run_one(cmd, inst_path):
    out = subprocess.run(cmd, capture_output=True, text=True, timeout=3600)
    if out.returncode != 0:
        raise RuntimeError(out.stderr[:300])
    rec, route = {}, None
    for line in out.stdout.splitlines():
        p = line.split()
        if len(p) >= 2 and p[0] in ("COST", "TIME_MS", "RESTARTS", "ILS_ITERS"):
            rec[p[0].lower()] = float(p[1])
        elif p and p[0] == "ROUTE":
            route = [int(x) for x in line.split(None, 1)[1].split(",")]
    if route is None:
        raise RuntimeError("no ROUTE in output")
    lat = recompute_latency(inst_path, route)
    if lat is None or lat != int(rec["cost"]):
        raise RuntimeError(f"tour check failed: reported {rec['cost']}, recomputed {lat}")
    return rec


def run(args):
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    config = {"time_limit": args.time_limit, "jobs": args.jobs,
              "arms": {lab: " ".join([b, *a]) for lab, b, a, _ in args.arms}}
    if out_path.exists():
        data = json.loads(out_path.read_text())
        if data["config"] != config:
            sys.exit("checkpoint has a different configuration; refusing to mix runs")
    else:
        data = {"config": config, "runs": {}}
    runs = data["runs"]

    total = len(args.instances) * args.runs * len(args.arms)
    done = len(runs)
    t0 = time.time()
    for inst in args.instances:
        inst_path = f"instances/{inst}.tsp"
        for seed in range(1, args.runs + 1):
            cells = [(f"{inst}|{lab}|{seed}",
                      [b, inst_path, *a, "--max-time", str(args.time_limit),
                       "--seed", str(seed)])
                     for lab, b, a, _ in args.arms if f"{inst}|{lab}|{seed}" not in runs]
            if not cells:
                continue
            random.Random(seed * 1000 + len(inst)).shuffle(cells)
            pad = (-len(cells)) % args.jobs
            batch = cells + [(None, cells[0][1])] * pad
            for g in range(0, len(batch), args.jobs):
                group = batch[g:g + args.jobs]
                with ThreadPoolExecutor(max_workers=args.jobs) as ex:
                    futs = [(k, ex.submit(run_one, c, inst_path)) for k, c in group]
                    for k, f in futs:
                        try:
                            rec = f.result()
                        except Exception as e:
                            print(f"  FAILED {k}: {e}", flush=True)
                            continue
                        if k is None:
                            continue
                        runs[k] = rec
                        done += 1
                        print(f"[{done}/{total}] {k:34s} cost={rec['cost']:.0f} "
                              f"restarts={rec.get('restarts', -1):.0f} "
                              f"ils={rec.get('ils_iters', -1):.0f}", flush=True)
                out_path.write_text(json.dumps(data))
    print(f"\nfinished in {(time.time() - t0) / 60:.1f} min\n")


# ---------------------------------------------------------------- report

def holm(pvals):
    """Holm-adjusted p-values, same order as the input."""
    m = len(pvals)
    order = sorted(range(m), key=lambda i: pvals[i])
    adj, running = [0.0] * m, 0.0
    for rank, i in enumerate(order):
        running = max(running, min(1.0, (m - rank) * pvals[i]))
        adj[i] = running
    return adj


def pairs(runs, insts, seeds, base, arm):
    return [(runs[f"{i}|{base}|{s}"]["cost"], runs[f"{i}|{arm}|{s}"]["cost"])
            for i in insts for s in seeds
            if f"{i}|{base}|{s}" in runs and f"{i}|{arm}|{s}" in runs]


def fmt_p(p):
    return "<0.0001" if p < 1e-4 else f"{p:.4f}"


def report(args):
    data = json.loads(Path(args.out).read_text())
    runs = data["runs"]
    CHAIN, LOO = args.suite["chain"], args.suite["loo"]
    FINAL, FIRST = CHAIN[-1][0], CHAIN[0][0]
    insts = [i for i in args.instances if any(k.startswith(i + "|") for k in runs)]
    seeds = range(1, args.runs + 1)
    best = json.loads((ROOT / BEST_SOLUTIONS_FILE).read_text())
    mean = lambda xs: sum(xs) / len(xs) if xs else float("nan")

    # reference per instance: best of the tracked BKS and anything found here
    ref = {}
    for i in insts:
        found = [r["cost"] for k, r in runs.items() if k.startswith(i + "|")]
        ref[i] = min(found + ([best[i]["cost"]] if i in best else []))

    def arm_stats(lab):
        recs = [runs[f"{i}|{lab}|{s}"] for i in insts for s in seeds if f"{i}|{lab}|{s}" in runs]
        gaps = [(runs[f"{i}|{lab}|{s}"]["cost"] - ref[i]) / ref[i] * 100
                for i in insts for s in seeds if f"{i}|{lab}|{s}" in runs]
        return len(recs), mean(gaps), mean([r.get("ils_iters", 0) for r in recs]), \
            mean([r.get("restarts", 0) for r in recs])

    print(f"# instancias: {', '.join(insts)}; seeds 1..{args.runs}; "
          f"{data['config']['time_limit']:g} s/execucao; jobs={data['config']['jobs']}\n")

    # ---- chain
    print("## Cadeia cumulativa\n")
    print("| passo | componente adicionado | N | gap medio% | iter. ILS | reinicios "
          f"| vs passo anterior: rel% | V/E/D | p | p Holm | vs {FIRST}: rel% |")
    print("|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|")
    steps = []
    for k, (lab, _, _, desc) in enumerate(CHAIN):
        n, gap, it, rs = arm_stats(lab)
        prev = compare_pairs(pairs(runs, insts, seeds, CHAIN[k - 1][0], lab)) if k else None
        cum = compare_pairs(pairs(runs, insts, seeds, CHAIN[0][0], lab)) if k else None
        steps.append((lab, desc, n, gap, it, rs, prev, cum))
    adj = holm([s[6].p for s in steps[1:]])
    for k, (lab, desc, n, gap, it, rs, prev, cum) in enumerate(steps):
        if prev is None:
            print(f"| {lab} | {desc} | {n} | {gap:.3f} | {it:.0f} | {rs:.1f} | — | — | — | — | — |")
        else:
            print(f"| {lab} | {desc} | {n} | {gap:.3f} | {it:.0f} | {rs:.1f} | "
                  f"{prev.mean_rel:+.3f} | {prev.wins}/{prev.ties}/{prev.losses} | "
                  f"{fmt_p(prev.p)} | {fmt_p(adj[k - 1])} | {cum.mean_rel:+.3f} |")

    print("\n### Ganho marginal por instancia (rel% vs passo anterior)\n")
    print("| instancia | " + " | ".join(l for l, *_ in CHAIN[1:]) + f" | total vs {FIRST} |")
    print("|---|" + "---:|" * len(CHAIN))
    for i in insts:
        cells = []
        for k in range(1, len(CHAIN)):
            c = compare_pairs(pairs(runs, [i], seeds, CHAIN[k - 1][0], CHAIN[k][0]))
            cells.append(f"{c.mean_rel:+.3f}" if c else "—")
        c = compare_pairs(pairs(runs, [i], seeds, CHAIN[0][0], FINAL))
        total = f"{c.mean_rel:+.3f}" if c else "—"
        print(f"| {i} | " + " | ".join(cells) + f" | {total} |")

    print("\n### Gap medio% para a referencia, por instancia e passo\n")
    print("| instancia | n ref | " + " | ".join(l for l, *_ in CHAIN) + " |")
    print("|---|---:|" + "---:|" * len(CHAIN))
    for i in insts:
        cells = []
        for lab, *_ in CHAIN:
            g = [(runs[f"{i}|{lab}|{s}"]["cost"] - ref[i]) / ref[i] * 100
                 for s in seeds if f"{i}|{lab}|{s}" in runs]
            cells.append(f"{mean(g):.3f}" if g else "—")
        print(f"| {i} | {ref[i]:.0f} | " + " | ".join(cells) + " |")

    # ---- leave-one-out
    print(f"\n## {args.suite['loo_title']} (vs metodo completo)\n")
    print("| removido | N | gap medio% | iter. ILS | rel% | V/E/D | p | p Holm |")
    print("|---|---:|---:|---:|---:|---:|---:|---:|")
    n, gap, it, _ = arm_stats(FINAL)
    print(f"| (nada: {FINAL}) | {n} | {gap:.3f} | {it:.0f} | — | — | — | — |")
    rows = []
    for lab, _, _, desc in LOO:
        c = compare_pairs(pairs(runs, insts, seeds, FINAL, lab))
        if c:
            rows.append((desc, c, arm_stats(lab)))
    adj = holm([c.p for _, c, _ in rows])
    for (desc, c, (n, gap, it, _)), pa in zip(rows, adj):
        print(f"| {desc} | {n} | {gap:.3f} | {it:.0f} | {c.mean_rel:+.3f} | "
              f"{c.wins}/{c.ties}/{c.losses} | {fmt_p(c.p)} | {fmt_p(pa)} |")

    print("\n### Leave-one-out por instancia (rel% vs metodo completo)\n")
    print("| removido | " + " | ".join(insts) + " |")
    print("|---|" + "---:|" * len(insts))
    for lab, _, _, desc in LOO:
        cells = []
        for i in insts:
            c = compare_pairs(pairs(runs, [i], seeds, FINAL, lab))
            cells.append(f"{c.mean_rel:+.3f}" if c else "—")
        print(f"| {desc} | " + " | ".join(cells) + " |")


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--out", required=True, help="checkpoint JSON (resumed if it exists)")
    ap.add_argument("--suite", choices=SUITES, default="screen30")
    ap.add_argument("--instances", nargs="+", help="default: the suite's")
    ap.add_argument("--time-limit", type=float, help="default: the suite's")
    ap.add_argument("--runs", type=int, default=5, help="seeds 1..N")
    ap.add_argument("--jobs", type=int, help="concurrent runs (default: the suite's)")
    ap.add_argument("--report-only", action="store_true")
    args = ap.parse_args()

    args.suite = SUITES[args.suite]
    args.arms = suite_arms(args.suite)
    args.instances = args.instances or args.suite["instances"]
    if args.time_limit is None:
        args.time_limit = args.suite["time_limit"]
    if args.jobs is None:
        args.jobs = args.suite["jobs"]

    os.chdir(ROOT)
    if not args.report_only:
        run(args)
    report(args)


if __name__ == "__main__":
    main()
