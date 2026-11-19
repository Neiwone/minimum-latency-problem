#!/usr/bin/env python3
"""
The proposed method against the published results of GILS-RVND and
MDM-GILS-RVND, instance by instance, on every public instance the papers use.

Two suites, each in its paper's variant and rounding:

  circuit  Table 1 of Santana, Plastino & Rosseti (arXiv:1908.10705): 56 TSPLIB
           instances n = 120..1379, Hamiltonian circuit, TSPLIB nint. Published
           GILS-RVND and MDM-GILS-RVND (best, average of 10, time).
  path     Table 2 of Silva et al. (2012): the 10 TSPLIB instances of Salehipour
           et al. (2011), Hamiltonian path, truncated EUC_2D. Published
           GILS-RVND (best, average of 10, time); the BKS includes the att532
           value of Santana et al. (2019), Table 4.

Each run gets min(--cap, published time) seconds: the published time of
MDM-GILS-RVND (circuit) or GILS-RVND (path), so the proposal never gets more
wall-clock than the method it is compared with. circuit-long repeats the
n >= 500 instances with a 1000 s cap and 5 seeds, recording the best cost
over time, on a machine of similar
speed (both papers: single thread of a Core i7, 2.93-3.40 GHz). Seeds 1..10,
every tour verified from the coordinates.

    python3 scripts/literature_compare.py --suite circuit --out results/literature/circuit.json --jobs 4
    python3 scripts/literature_compare.py --suite path    --out results/literature/path.json
    python3 scripts/literature_compare.py --suite path --method gils_rvnd_paper --out results/literature/path_gils_rvnd.json --cores 2
    python3 scripts/literature_compare.py --suite path --cap 100000 --budget-from results/literature/path_gils_rvnd.json --out results/literature/path_gils_budget.json --cores 2
    python3 scripts/literature_compare.py --suite abeledo --out results/literature/abeledo.json
    python3 scripts/literature_compare.py --suite circuit-long --out results/literature/circuit_long.json --jobs 4
    python3 scripts/literature_compare.py --suite circuit --out results/literature/circuit.json --report-only
    python3 scripts/literature_compare.py --suite circuit --out results/literature/circuit.json --report-only --save-best
"""
import argparse, json, os, statistics, subprocess, threading, time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from am_study import latency as path_latency
from mdm_paper_compare import PAPER, closed_nint_latency
from registry import ROOT, SOLUTIONS_DIR
from runner import SolutionTracker
from stats import sign_test_p

PROPOSAL = ["./bin/gils_am_rvnd", "--rvnd-mode", "candidate-dlb", "--cand-k", "12",
            "--iils", "300"]
# our implementation of GILS-RVND, for comparing on the same machine and budget
# our GILS-RVND and MDM-GILS-RVND; the *_paper methods run under the paper's
# stopping rule (I_max = 10, I_ILS = min(100, n)) with no time limit, to measure
# their time here
METHODS = {"proposal": PROPOSAL, "gils_rvnd": ["./bin/gils_rvnd"],
           "gils_rvnd_paper": ["./bin/gils_rvnd", "--imax", "10"],
           "mdm_gils_rvnd_paper": ["./bin/mdm_gils_rvnd", "--imax", "10"],
           # restarts until the time limit; I_ILS = min(100, n) = 100 on the circuit set
           "mdm_gils_rvnd": ["./bin/mdm_gils_rvnd", "--iils", "100"]}

# Table 2 of Silva et al. (2012): instance -> (Salehipour best, GILS best,
# GILS avg, GILS time s). The BKS is the GILS best except att532.
SILVA_T2 = {
    "st70":    (19553, 19215, 19215.0, 1.51),
    "rat99":   (56994, 54984, 54984.0, 9.47),
    "kroD100": (976830, 949594, 949594.0, 6.90),
    "lin105":  (585823, 585823, 585823.0, 6.19),
    "pr107":   (1983475, 1980767, 1980767.0, 8.13),
    "rat195":  (213371, 210191, 210335.9, 75.56),
    "pr226":   (7226554, 7100308, 7100308.0, 59.05),
    "lin318":  (5876537, 5560679, 5569819.5, 220.59),
    "pr439":   (18567170, 17688561, 17734922.0, 553.74),
    "att532":  (18448435, 5581240, 5597866.8, 1792.61),
}
PATH_BKS = {"att532": 5572131}   # Santana et al. (2019), Table 4

# Table 1 of Silva et al. (2012): the 23 TSPLIB instances of Abeledo et al.
# (2010), Hamiltonian circuit. instance -> (OPT or UB, GILS best, GILS avg,
# GILS time s); OPT is proven except where marked. pr76r (pr76 rescaled) has
# no instance file here and is left out.
ABELEDO = {
    "dantzig42": (12528, 12528, 12528.0, 0.16),
    "swiss42":   (22327, 22327, 22327.0, 0.16),
    "att48":     (209320, 209320, 209320.0, 0.32),
    "gr48":      (102378, 102378, 102378.0, 0.33),
    "hk48":      (247926, 247926, 247926.0, 0.30),
    "eil51":     (10178, 10178, 10178.0, 0.49),
    "berlin52":  (143721, 143721, 143721.0, 0.46),
    "brazil58":  (512361, 512361, 512361.0, 0.78),
    "st70":      (20557, 20557, 20557.0, 1.65),
    "eil76":     (17976, 17976, 17976.0, 2.64),
    "pr76":      (3455242, 3455242, 3455242.0, 2.31),
    "gr96":      (2097170, 2097170, 2097170.0, 6.19),
    "rat99":     (58288, 57986, 57986.0, 11.27),     # UB, not proven
    "kroA100":   (983128, 983128, 983128.0, 8.59),
    "kroB100":   (986008, 986008, 986008.0, 9.21),
    "kroC100":   (961324, 961324, 961324.0, 8.17),
    "kroD100":   (976965, 976965, 976965.0, 8.46),
    "kroE100":   (971266, 971266, 971266.0, 8.31),
    "rd100":     (340047, 340047, 340047.0, 8.52),
    "eil101":    (27519, 27513, 27513.0, 12.76),     # UB, not proven
    "lin105":    (603910, 603910, 603910.0, 8.42),
    "pr107":     (2026626, 2026626, 2026626.0, 10.89),
}

SUITES = {
    "circuit": dict(instances=list(PAPER), closed=True,
                    lit_time=lambda i: PAPER[i][6]),
    "abeledo": dict(instances=list(ABELEDO), closed=True,
                    lit_time=lambda i: ABELEDO[i][3]),
    "path":    dict(instances=list(SILVA_T2), closed=False,
                    lit_time=lambda i: SILVA_T2[i][3]),
    # n >= 500 with a longer cap, recording the best cost over time, so one
    # run gives the result at every budget up to the cap
    "circuit-long": dict(instances=list(PAPER)[list(PAPER).index("att532"):], closed=True,
                         lit_time=lambda i: PAPER[i][6], cap=1000.0, runs=5, trace=True),
}

mean = statistics.mean


def budget(suite, inst, cap):
    return round(min(cap, SUITES[suite]["lit_time"](inst)), 2)


# ---------------------------------------------------------------- running

def run_one(cmd, path, closed):
    out = subprocess.run(cmd, capture_output=True, text=True, timeout=48 * 3600)
    if out.returncode != 0:
        raise RuntimeError(out.stderr[:300])
    rec, route = {}, None
    for line in out.stdout.splitlines():
        p = line.split()
        if len(p) >= 2 and p[0] in ("COST", "TIME_MS", "RESTARTS", "ILS_ITERS", "CLOSED"):
            rec[p[0].lower()] = float(p[1])
        elif p and p[0] == "TRACE_B":
            rec.setdefault("best_trace", []).append([float(p[1]), int(p[2])])
        elif p and p[0] == "ROUTE":
            route = [int(x) for x in line.split(None, 1)[1].split(",")]
    if rec.get("closed") != (1 if closed else 0):
        raise RuntimeError("solver ran in the wrong variant")
    lat = (closed_nint_latency if closed else path_latency)(path, route or [])
    if lat is None or lat != int(rec["cost"]):
        raise RuntimeError(f"tour check failed: reported {rec['cost']}, recomputed {lat}")
    rec["route"] = route
    return rec


def run(args, insts):
    closed = SUITES[args.suite]["closed"]
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    data = (json.loads(out.read_text()) if out.exists()
            else {"suite": args.suite, "cap": args.cap, "cmd": METHODS[args.method],
                  "budget_from": args.budget_from, "runs": {}})
    if ((data["suite"], data["cap"], data["cmd"], data.get("budget_from"))
            != (args.suite, args.cap, METHODS[args.method], args.budget_from)):
        raise SystemExit("checkpoint has a different suite, cap, command or budget; refusing to mix")
    runs = data["runs"]
    # in parallel, largest first, so the long runs do not end up alone at the
    # tail; one at a time, smallest first, so a broken setup shows up early
    sign = -1 if args.jobs > 1 else 1
    todo = sorted(((i, s) for i in insts for s in range(1, args.runs + 1)
                   if f"{i}|{s}" not in runs),
                  key=lambda t: (sign * budget(args.suite, t[0], args.cap), t[0], t[1]))
    total = sum(budget(args.suite, i, args.cap) for i, _ in todo)
    print(f"{len(todo)} runs to go, {total / 3600:.1f} h of budget on {args.jobs} jobs", flush=True)

    lock = threading.Lock()
    free = list(args.cores or [])
    done = [0]
    t0 = time.time()

    def work(item):
        inst, seed = item
        with lock:
            core = free.pop(0) if free else None
        path = f"instances/{inst}.tsp"
        method = METHODS[args.method]
        if args.method.endswith("_paper"):
            limit = ["--iils", str(min(100, n_of(inst)))]
        else:
            limit = ["--max-time", str(budget(args.suite, inst, args.cap))]
        cmd = [*method[:1], path, *method[1:], *limit, "--seed", str(seed)]
        if closed:
            cmd += ["--closed", "--nint"]
        if SUITES[args.suite].get("trace"):
            cmd += ["--trace"]
        if core is not None:
            cmd = ["taskset", "-c", str(core)] + cmd
        try:
            rec = run_one(cmd, path, closed)
            err = None
        except Exception as e:
            rec, err = None, e
        with lock:
            if core is not None:
                free.append(core)
            done[0] += 1
            if err:
                print(f"  FAILED {inst}|{seed}: {err}", flush=True)
                return
            runs[f"{inst}|{seed}"] = rec
            tmp = out.with_suffix(".tmp")   # atomic, so a kill never corrupts the checkpoint
            tmp.write_text(json.dumps(data))
            tmp.replace(out)
            print(f"[{done[0]}/{len(todo)}] {inst}|{seed} cost={rec['cost']:.0f} "
                  f"t={rec['time_ms'] / 1000:.1f}s restarts={rec['restarts']:.0f}", flush=True)

    with ThreadPoolExecutor(max_workers=args.jobs) as ex:
        list(ex.map(work, todo))
    print(f"\nfinished in {(time.time() - t0) / 60:.1f} min\n")


# ---------------------------------------------------------------- report

def rel(a, b):
    return (a - b) / b * 100


def wtl(pairs, eps=0.05):
    """(ours, theirs) -> wins/ties/losses; the papers print one decimal."""
    w = sum(o < t - eps for o, t in pairs)
    l = sum(o > t + eps for o, t in pairs)
    return w, len(pairs) - w - l, l


def n_of(inst):
    for line in open(f"instances/{inst}.tsp"):
        if line.startswith("DIMENSION"):
            return int(line.split(":")[1])


def report(args, insts):
    data = json.loads(Path(args.out).read_text())
    runs = data["runs"]
    seeds = range(1, args.runs + 1)
    insts = [i for i in insts if all(f"{i}|{s}" in runs for s in seeds)]
    ours = {i: [runs[f"{i}|{s}"] for s in seeds] for i in insts}
    best = {i: min(r["cost"] for r in ours[i]) for i in insts}
    avg = {i: mean(r["cost"] for r in ours[i]) for i in insts}
    t_used = {i: mean(r["time_ms"] for r in ours[i]) / 1000 for i in insts}
    print(f"# suite {args.suite}: {len(insts)} instancias, {args.runs} execucoes, "
          f"tempo = min({data['cap']:g} s, tempo publicado)\n")
    if args.suite == "circuit-long":
        report_long(insts, ours, best, data["cap"])
    elif args.suite == "circuit":
        report_circuit(insts, best, avg, t_used)
    elif args.suite == "abeledo":
        report_abeledo(insts, ours, best, avg, t_used)
    else:
        report_path(insts, best, avg, t_used)


def bands(insts):
    return [("n < 200", [i for i in insts if n_of(i) < 200]),
            ("200 <= n < 500", [i for i in insts if 200 <= n_of(i) < 500]),
            ("n >= 500", [i for i in insts if n_of(i) >= 500]),
            ("todas", insts)]


def report_circuit(insts, best, avg, t_used):
    lit_best = {i: min(PAPER[i][1], PAPER[i][4]) for i in insts}
    print("| instancia | n | melhor literatura | GILS media | MDM media | MDM tempo (s) "
          "| proposta melhor | proposta media | tempo (s) | media vs MDM % | melhor vs literatura % |")
    print("|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|")
    for i in insts:
        _, gb, ga, gt, mb, ma, mt = PAPER[i]
        print(f"| `{i}` | {n_of(i)} | {lit_best[i]:,} | {ga:,.1f} | {ma:,.1f} | {mt:,.0f} "
              f"| {best[i]:,.0f} | {avg[i]:,.1f} | {t_used[i]:.0f} "
              f"| {rel(avg[i], ma):+.3f} | {rel(best[i], lit_best[i]):+.3f} |")

    print("\n## Media da proposta contra a media publicada (por instancia)\n")
    print("| faixa | inst. | vs GILS: dif.% | V/E/D | p | vs MDM: dif.% | V/E/D | p "
          "| tempo: proposta / MDM publicado |")
    print("|---|---:|---:|---:|---:|---:|---:|---:|---:|")
    for name, sub in bands(insts):
        if not sub:
            continue
        g = wtl([(avg[i], PAPER[i][2]) for i in sub])
        m = wtl([(avg[i], PAPER[i][5]) for i in sub])
        print(f"| {name} | {len(sub)} | {mean(rel(avg[i], PAPER[i][2]) for i in sub):+.3f} "
              f"| {'/'.join(map(str, g))} | {sign_test_p(g[0], g[2]):.2g} "
              f"| {mean(rel(avg[i], PAPER[i][5]) for i in sub):+.3f} "
              f"| {'/'.join(map(str, m))} | {sign_test_p(m[0], m[2]):.2g} "
              f"| {sum(t_used[i] for i in sub) / sum(PAPER[i][6] for i in sub) * 100:.1f}% |")

    print("\n## Melhor solucao contra a melhor publicada (min de GILS e MDM)\n")
    print("| faixa | inst. | igual | proposta melhor | proposta pior | gap medio da media "
          "da proposta a melhor publicada % |")
    print("|---|---:|---:|---:|---:|---:|")
    for name, sub in bands(insts):
        if not sub:
            continue
        eq = sum(best[i] == lit_best[i] for i in sub)
        bt = sum(best[i] < lit_best[i] for i in sub)
        print(f"| {name} | {len(sub)} | {eq} | {bt} | {len(sub) - eq - bt} "
              f"| {mean(rel(avg[i], lit_best[i]) for i in sub):+.3f} |")

    new = [i for i in insts if best[i] < lit_best[i]]
    print(f"\nNovas melhores solucoes ({len(new)}): " +
          ", ".join(f"`{i}` {best[i]:,.0f} ({rel(best[i], lit_best[i]):+.3f}%)" for i in new))
    worse = [i for i in insts if best[i] > lit_best[i]]
    print(f"\nMelhor pior que a publicada ({len(worse)}): " +
          ", ".join(f"`{i}` ({rel(best[i], lit_best[i]):+.3f}%)" for i in worse))


def best_at(rec, t_ms):
    c = None
    for t, cost in rec["best_trace"]:
        if t > t_ms:
            break
        c = cost
    return c


def report_long(insts, ours, best, cap):
    marks = [t for t in (100, 300) if t < cap] + [int(cap)]
    print("Media da proposta ao longo do tempo contra a media publicada. Em cada "
          "marca t, a proposta usou min(t, tempo do MDM publicado).\n")
    print("| instancia | n | MDM media | MDM tempo (s) | " +
          " | ".join(f"vs MDM % a {t} s" for t in marks) + " | vs GILS % ao fim |")
    print("|---|---:|---:|---:|" + "---:|" * (len(marks) + 1))
    at = {}
    for i in insts:
        mt = PAPER[i][6]
        at[i] = {t: mean(best_at(r, min(t, mt) * 1000) for r in ours[i]) for t in marks}
        print(f"| `{i}` | {n_of(i)} | {PAPER[i][5]:,.1f} | {mt:,.0f} | " +
              " | ".join(f"{rel(at[i][t], PAPER[i][5]):+.3f}" for t in marks) +
              f" | {rel(at[i][marks[-1]], PAPER[i][2]):+.3f} |")
    print("\n| marca | vs GILS: dif.% | V/E/D | p | vs MDM: dif.% | V/E/D | p "
          "| tempo: proposta / MDM publicado |")
    print("|---|---:|---:|---:|---:|---:|---:|---:|")
    for t in marks:
        g = wtl([(at[i][t], PAPER[i][2]) for i in insts])
        m = wtl([(at[i][t], PAPER[i][5]) for i in insts])
        print(f"| {t} s | {mean(rel(at[i][t], PAPER[i][2]) for i in insts):+.3f} "
              f"| {'/'.join(map(str, g))} | {sign_test_p(g[0], g[2]):.2g} "
              f"| {mean(rel(at[i][t], PAPER[i][5]) for i in insts):+.3f} "
              f"| {'/'.join(map(str, m))} | {sign_test_p(m[0], m[2]):.2g} "
              f"| {sum(min(t, PAPER[i][6]) for i in insts) / sum(PAPER[i][6] for i in insts) * 100:.1f}% |")
    lit_best = {i: min(PAPER[i][1], PAPER[i][4]) for i in insts}
    new = [i for i in insts if best[i] < lit_best[i]]
    print(f"\nNovas melhores solucoes ({len(new)}): " +
          ", ".join(f"`{i}` {best[i]:,.0f} ({rel(best[i], lit_best[i]):+.3f}%)" for i in new))


def report_abeledo(insts, ours, best, avg, t_used):
    print("| instancia | n | OPT/UB | GILS melhor | GILS media | GILS tempo (s) "
          "| proposta melhor | proposta media | execucoes no OPT | tempo (s) |")
    print("|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|")
    for i in insts:
        opt, gb, ga, gt = ABELEDO[i]
        ref = min(opt, gb)
        hits = sum(r["cost"] == ref for r in ours[i])
        print(f"| `{i}` | {n_of(i)} | {opt:,} | {gb:,} | {ga:,.1f} | {gt:.2f} "
              f"| {best[i]:,.0f} | {avg[i]:,.1f} | {hits}/{len(ours[i])} | {t_used[i]:.2f} |")
    ref = {i: min(ABELEDO[i][0], ABELEDO[i][1]) for i in insts}
    g = wtl([(avg[i], ABELEDO[i][2]) for i in insts])
    print(f"\nMedia vs GILS publicado: {mean(rel(avg[i], ABELEDO[i][2]) for i in insts):+.4f}%, "
          f"V/E/D {'/'.join(map(str, g))}; melhor = referencia em "
          f"{sum(best[i] == ref[i] for i in insts)}, abaixo em "
          f"{sum(best[i] < ref[i] for i in insts)}, de {len(insts)}; execucoes na referencia "
          f"{sum(r['cost'] == ref[i] for i in insts for r in ours[i])}/"
          f"{sum(len(ours[i]) for i in insts)}; tempo "
          f"{sum(t_used.values()) / sum(ABELEDO[i][3] for i in insts) * 100:.1f}% do publicado")


def report_path(insts, best, avg, t_used):
    bks = {i: min(PATH_BKS.get(i, SILVA_T2[i][1]), SILVA_T2[i][1]) for i in insts}
    print("| instancia | n | BKS | GILS melhor | GILS media | GILS tempo (s) "
          "| proposta melhor | proposta media | tempo (s) | media vs GILS % | melhor vs BKS % |")
    print("|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|")
    for i in insts:
        _, gb, ga, gt = SILVA_T2[i]
        print(f"| `{i}` | {n_of(i)} | {bks[i]:,} | {gb:,} | {ga:,.1f} | {gt:,.1f} "
              f"| {best[i]:,.0f} | {avg[i]:,.1f} | {t_used[i]:.1f} "
              f"| {rel(avg[i], ga):+.3f} | {rel(best[i], bks[i]):+.3f} |")
    g = wtl([(avg[i], SILVA_T2[i][2]) for i in insts])
    print(f"\nMedia vs GILS publicado: {mean(rel(avg[i], SILVA_T2[i][2]) for i in insts):+.3f}%, "
          f"V/E/D {'/'.join(map(str, g))}; melhor = BKS em "
          f"{sum(best[i] == bks[i] for i in insts)}, abaixo em "
          f"{sum(best[i] < bks[i] for i in insts)}, de {len(insts)}; tempo "
          f"{sum(t_used.values()) / sum(SILVA_T2[i][3] for i in insts) * 100:.1f}% do publicado")


def save_best(args, insts):
    """Keep the best verified circuit tour per instance in
    instances/solutions/closed/, apart from the path BKS."""
    tracker = SolutionTracker(SOLUTIONS_DIR / "closed")
    runs = json.loads(Path(args.out).read_text())["runs"]
    for inst in insts:
        recs = [r for k, r in runs.items() if k.split("|")[0] == inst]
        if not recs:
            continue
        r = min(recs, key=lambda r: r["cost"])
        if tracker.is_better(inst, r["cost"]):
            tracker.save_solution(inst, r["cost"], " ".join(str(v + 1) for v in r["route"]),
                                  "gils_am_rvnd_dlb", len(r["route"]), force=True)


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--suite", choices=SUITES, required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--method", choices=METHODS, default="proposal")
    ap.add_argument("--budget-from", help="checkpoint whose mean time per instance replaces "
                                          "the published time (e.g. a gils_rvnd_paper run)")
    ap.add_argument("--cap", type=float, help="seconds (default: 100, or the suite's)")
    ap.add_argument("--runs", type=int, help="default: 10, or the suite's")
    ap.add_argument("--jobs", type=int, default=1)
    ap.add_argument("--cores", type=int, nargs="+", help="pin each job to one of these CPUs")
    ap.add_argument("--instances", nargs="+", help="default: the suite's")
    ap.add_argument("--report-only", action="store_true")
    ap.add_argument("--no-report", action="store_true", help="run only (e.g. one instance at a time)")
    ap.add_argument("--save-best", action="store_true",
                    help="circuit suites: record the best tour per instance in "
                         "instances/solutions/closed/")
    args = ap.parse_args()
    os.chdir(ROOT)
    args.cap = args.cap or SUITES[args.suite].get("cap", 100.0)
    args.runs = args.runs or SUITES[args.suite].get("runs", 10)
    insts = args.instances or SUITES[args.suite]["instances"]
    if args.budget_from:
        ref = json.loads(Path(args.budget_from).read_text())["runs"]
        t_ref = {i: mean(r["time_ms"] for k, r in ref.items() if k.split("|")[0] == i) / 1000
                 for i in insts}
        SUITES[args.suite]["lit_time"] = t_ref.__getitem__
    if not args.report_only:
        run(args, insts)
    if not args.no_report:
        report(args, insts)
    if args.save_best:
        if not SUITES[args.suite]["closed"]:
            raise SystemExit("--save-best is for the circuit suites")
        save_best(args, insts)


if __name__ == "__main__":
    main()
