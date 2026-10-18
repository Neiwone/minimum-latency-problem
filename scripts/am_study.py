#!/usr/bin/env python3
"""
What the adaptive memory of gils_am_rvnd does beyond final quality.

Every comparison is lambda = 0 (no memory) against lambda = 0.5 (memory) in
the same binary, so construction and local search are identical and only the
memory differs. Two suites, both sequential (time is a measured outcome):

  fixed100  100 s per run, 6 TSPLIB instances n >= 500, I_ILS in {30, 300}:
            quality, cost over time, time to target, per-restart mechanism.
  iter      I_max = 10, I_ILS = 100 (no time limit), 5 instances n = 200..532,
            original RVND and candidate-dlb: wall time and quality at a fixed
            number of iterations, the protocol of grasp-am-large-scale.md.

Runs use --trace (TRACE_R per restart, TRACE_B per new global best); every
tour is verified from the coordinates.

    python3 scripts/am_study.py --suite fixed100 --out results/am-study/fixed100.json
    python3 scripts/am_study.py --suite iter     --out results/am-study/iter.json
    python3 scripts/am_study.py --suite fixed100 --out results/am-study/fixed100.json --report-only
"""
import argparse, json, os, random, statistics, subprocess, time
from pathlib import Path

from registry import BEST_SOLUTIONS_FILE, ROOT
from stats import compare_pairs, sign_test_p
from verify_tour import dist, read_instance

AM = "./bin/gils_am_rvnd"
DLB = ["--rvnd-mode", "candidate-dlb", "--cand-k", "12"]

SUITES = {
    "fixed100": dict(
        instances=["att532", "rat783", "pr1002", "pcb1173", "d1291", "nrw1379"],
        arms={f"i{i}_l{l}": DLB + ["--iils", str(i), "--lambda", l, "--max-time", "100"]
              for i in (30, 300) for l in ("0", "0.5")},
        pairs=[("i30_l0", "i30_l0.5"), ("i300_l0", "i300_l0.5")]),
    "iter": dict(
        instances=["kroA200", "a280", "lin318", "pr439", "att532"],
        arms={f"{ls}_l{l}": (DLB if ls == "dlb" else []) + ["--imax", "10", "--iils", "100",
                                                             "--lambda", l]
              for ls in ("single", "dlb") for l in ("0", "0.5")},
        pairs=[("single_l0", "single_l0.5"), ("dlb_l0", "dlb_l0.5")]),
}

mean = lambda xs: statistics.mean(xs) if xs else float("nan")


# ---------------------------------------------------------------- running

_inst = {}


def latency(path, route):
    if path not in _inst:
        _inst[path] = read_instance(path)
    coords, etype, m = _inst[path]
    if sorted(route) != list(range(len(coords))) or route[0] != 0:
        return None
    acc = tot = 0
    for a, b in zip(route, route[1:]):
        acc += m[a][b] if m is not None else dist(coords[a + 1], coords[b + 1], etype)
        tot += acc
    return tot


def run_one(cmd, path):
    out = subprocess.run(cmd, capture_output=True, text=True, timeout=6 * 3600)
    if out.returncode != 0:
        raise RuntimeError(out.stderr[:300])
    rec = {"restarts_trace": [], "best_trace": []}
    route = None
    for line in out.stdout.splitlines():
        p = line.split()
        if not p:
            continue
        if p[0] in ("COST", "TIME_MS", "RESTARTS", "ILS_ITERS"):
            rec[p[0].lower()] = float(p[1])
        elif p[0] == "ROUTE":
            route = [int(x) for x in line.split(None, 1)[1].split(",")]
        elif p[0] == "TRACE_B":
            rec["best_trace"].append([float(p[1]), int(p[2])])
        elif p[0] == "TRACE_R":
            # restart, t0 ms, pool size, alpha, construct cost, first-descent
            # cost, first-descent ms, restart best, ILS iters, restart ms, distance
            rec["restarts_trace"].append([int(p[1]), float(p[2]), int(p[3]), float(p[4]),
                                          int(p[5]), int(p[6]), float(p[7]), int(p[8]),
                                          int(p[9]), float(p[10]), int(p[11])])
    lat = latency(path, route or [])
    if lat is None or lat != int(rec["cost"]):
        raise RuntimeError(f"tour check failed: reported {rec.get('cost')}, recomputed {lat}")
    return rec


def run(args, suite):
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    data = json.loads(out.read_text()) if out.exists() else {"arms": suite["arms"], "runs": {}}
    if data["arms"] != suite["arms"]:
        raise SystemExit("checkpoint has different arms; refusing to mix runs")
    runs = data["runs"]
    todo = []
    for inst in suite["instances"]:
        for seed in range(1, args.runs + 1):
            cell = [(inst, a, seed) for a in suite["arms"] if f"{inst}|{a}|{seed}" not in runs]
            random.Random(seed * 7919 + len(inst)).shuffle(cell)
            todo += cell
    print(f"{len(todo)} runs to go", flush=True)
    t0 = time.time()
    for k, (inst, arm, seed) in enumerate(todo, 1):
        path = f"instances/{inst}.tsp"
        cmd = [AM, path, *suite["arms"][arm], "--seed", str(seed), "--trace"]
        try:
            rec = run_one(cmd, path)
        except Exception as e:
            print(f"  FAILED {inst}|{arm}|{seed}: {e}", flush=True)
            continue
        runs[f"{inst}|{arm}|{seed}"] = rec
        out.write_text(json.dumps(data))
        print(f"[{k}/{len(todo)}] {inst}|{arm}|{seed} cost={rec['cost']:.0f} "
              f"t={rec['time_ms'] / 1000:.1f}s restarts={rec['restarts']:.0f}", flush=True)
    print(f"\nfinished in {(time.time() - t0) / 60:.1f} min\n")


# ---------------------------------------------------------------- report

def best_at(rec, t_ms):
    """Best cost found up to t_ms (None if nothing yet)."""
    c = None
    for t, cost in rec["best_trace"]:
        if t > t_ms:
            break
        c = cost
    return c


def time_to(rec, target):
    """First time the best cost was <= target, or None if never."""
    for t, cost in rec["best_trace"]:
        if cost <= target:
            return t
    return None


def fmt_p(p):
    return "<0.0001" if p < 1e-4 else f"{p:.4f}"


def report(args, suite):
    runs = json.loads(Path(args.out).read_text())["runs"]
    insts = [i for i in suite["instances"] if any(k.startswith(i + "|") for k in runs)]
    seeds = range(1, args.runs + 1)
    best = json.loads((ROOT / BEST_SOLUTIONS_FILE).read_text())
    ref = {i: min([r["cost"] for k, r in runs.items() if k.startswith(i + "|")]
                  + ([best[i]["cost"]] if i in best else [])) for i in insts}
    get = lambda i, a, s: runs.get(f"{i}|{a}|{s}")

    def paired(base, arm, f):
        pr = [(f(get(i, base, s), i), f(get(i, arm, s), i)) for i in insts for s in seeds
              if get(i, base, s) and get(i, arm, s)]
        return [(x, y) for x, y in pr if x is not None and y is not None]

    print(f"# suite {args.suite}: {', '.join(insts)}; seeds 1..{args.runs}\n")
    for base, arm in suite["pairs"]:
        print(f"## {arm} (memoria) vs {base} (sem memoria)\n")

        # quality and robustness
        c = compare_pairs(paired(base, arm, lambda r, i: r["cost"]))
        print("### Qualidade final\n")
        print(f"rel% {c.mean_rel:+.3f}, V/E/D {c.wins}/{c.ties}/{c.losses}, p {fmt_p(c.p)} (N={c.n})\n")
        print("| instancia | gap% sem | gap% com | dp gap% sem | dp gap% com | pior gap% sem | pior gap% com |")
        print("|---|---:|---:|---:|---:|---:|---:|")
        for i in insts:
            g = {a: [(get(i, a, s)["cost"] - ref[i]) / ref[i] * 100 for s in seeds if get(i, a, s)]
                 for a in (base, arm)}
            if len(g[base]) < 2 or len(g[arm]) < 2:
                continue
            print(f"| {i} | {mean(g[base]):.3f} | {mean(g[arm]):.3f} | "
                  f"{statistics.stdev(g[base]):.3f} | {statistics.stdev(g[arm]):.3f} | "
                  f"{max(g[base]):.3f} | {max(g[arm]):.3f} |")

        # time
        c = compare_pairs(paired(base, arm, lambda r, i: r["time_ms"]))
        print(f"\n### Tempo de parede\n\nrel% {c.mean_rel:+.2f}, mais rapido/igual/mais lento "
              f"{c.wins}/{c.ties}/{c.losses}, p {fmt_p(c.p)}; "
              f"medio {mean([x for x, _ in paired(base, arm, lambda r, i: r['time_ms'])]) / 1000:.1f} s sem, "
              f"{mean([y for _, y in paired(base, arm, lambda r, i: r['time_ms'])]) / 1000:.1f} s com\n")

        # anytime
        if args.suite == "fixed100":
            print("### Custo ao longo do tempo (melhor ate t)\n")
            print("| t | rel% | V/E/D | p |")
            print("|---:|---:|---:|---:|")
            for t in (5, 10, 25, 50, 75, 100):
                c = compare_pairs(paired(base, arm, lambda r, i, t=t: best_at(r, t * 1000)))
                if c:
                    print(f"| {t} s | {c.mean_rel:+.3f} | {c.wins}/{c.ties}/{c.losses} | {fmt_p(c.p)} |")
            print("\n### Tempo ate o alvo (ref = melhor custo conhecido)\n")
            print("| alvo | atinge sem | atinge com | t mediano sem (s) | t mediano com (s) "
                  "| com chega antes/empate/depois | p |")
            print("|---|---:|---:|---:|---:|---:|---:|")
            for x in (2.0, 1.0, 0.5):
                w = l = e = 0
                hit = {base: [], arm: []}
                for i in insts:
                    tgt = ref[i] * (1 + x / 100)
                    for s in seeds:
                        ra, rb = get(i, base, s), get(i, arm, s)
                        if not ra or not rb:
                            continue
                        ta, tb = time_to(ra, tgt), time_to(rb, tgt)
                        hit[base].append(ta)
                        hit[arm].append(tb)
                        ta_, tb_ = ta if ta is not None else 1e18, tb if tb is not None else 1e18
                        if tb_ < ta_: w += 1
                        elif tb_ > ta_: l += 1
                        else: e += 1
                med = lambda xs: statistics.median([t / 1000 for t in xs if t is not None]) \
                    if any(t is not None for t in xs) else float("nan")
                n = len(hit[base])
                print(f"| +{x}% | {sum(t is not None for t in hit[base])}/{n} | "
                      f"{sum(t is not None for t in hit[arm])}/{n} | {med(hit[base]):.1f} | "
                      f"{med(hit[arm]):.1f} | {w}/{e}/{l} | {fmt_p(sign_test_p(w, l))} |")

        # mechanism, per restart (restart 0 never sees a memory)
        print("\n### Mecanismo, por reinicio (exceto o primeiro)\n")
        print("| metrica | sem memoria | com memoria |")
        print("|---|---:|---:|")
        rows = {}
        for a in (base, arm):
            R = [(i, r) for i in insts for s in seeds if get(i, a, s)
                 for r in get(i, a, s)["restarts_trace"] if r[0] > 0]
            n_of = lambda i: len(_inst[f"instances/{i}.tsp"][0]) if f"instances/{i}.tsp" in _inst \
                else len(read_instance(f"instances/{i}.tsp")[0])
            rows[a] = {
                "reinicios por execucao": mean([len(get(i, a, s)["restarts_trace"]) for i in insts
                                                for s in seeds if get(i, a, s)]),
                "gap% da solucao construida": mean([(r[4] - ref[i]) / ref[i] * 100 for i, r in R]),
                "gap% apos a 1a descida": mean([(r[5] - ref[i]) / ref[i] * 100 for i, r in R]),
                "duracao da 1a descida (ms)": mean([r[6] for i, r in R]),
                "gap% do otimo do reinicio": mean([(r[7] - ref[i]) / ref[i] * 100 for i, r in R]),
                "iteracoes de ILS por reinicio": mean([r[8] for i, r in R]),
                "duracao do reinicio (ms)": mean([r[9] for i, r in R]),
                "distancia ao melhor global (% dos nos)": mean([r[10] / n_of(i) * 100 for i, r in R]),
                "% de reinicios que voltam ao mesmo otimo (distancia 0)":
                    mean([100.0 * (r[10] == 0) for i, r in R]),
                "% de reinicios que melhoram o melhor global": None,
            }
            # restarts that improved the global best: restart best < best before it
            imp = []
            for i in insts:
                for s in seeds:
                    rec = get(i, a, s)
                    if not rec:
                        continue
                    cur = None
                    for r in rec["restarts_trace"]:
                        if cur is not None and r[0] > 0:
                            imp.append(100.0 * (r[7] < cur))
                        cur = r[7] if cur is None else min(cur, r[7])
            rows[a]["% de reinicios que melhoram o melhor global"] = mean(imp)
        for k in rows[base]:
            print(f"| {k} | {rows[base][k]:.2f} | {rows[arm][k]:.2f} |")
        print()


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--suite", choices=SUITES, required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--runs", type=int, default=5)
    ap.add_argument("--instances", nargs="+", help="default: the suite's")
    ap.add_argument("--report-only", action="store_true")
    args = ap.parse_args()
    os.chdir(ROOT)
    suite = dict(SUITES[args.suite])
    if args.instances:
        suite["instances"] = args.instances
    if not args.report_only:
        run(args, suite)
    report(args, suite)


if __name__ == "__main__":
    main()
