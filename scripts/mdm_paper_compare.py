#!/usr/bin/env python3
"""
Our GILS-RVND and MDM-GILS-RVND against Table 1 of Santana, Plastino &
Rosseti (arXiv:1908.10705): 56 TSPLIB instances, Hamiltonian-circuit
variant, TSPLIB nint distances.

The paper's protocol: I_max = 10, I_ILS = min(100, n), R = {0.00..0.25},
10 runs per instance; MDM with sup_min = 0.70, d = 10, MaxP = 5 (the
binaries' defaults). Here: --closed --nint --imax 10 --iils min(100, n),
seeds 1..10, sequential, every tour verified from the coordinates.

    python3 scripts/mdm_paper_compare.py --out results/mdm-paper/table1.json --max-n 318
    python3 scripts/mdm_paper_compare.py --out results/mdm-paper/table1.json --report-only
"""
import argparse, json, math, os, statistics, subprocess, time
from pathlib import Path

from registry import ROOT
from stats import sign_test_p
from verify_tour import dist, read_instance

# Table 1 of the paper: instance -> (BKS or None, GILS best, avg, time s,
#                                    MDM best, avg, time s)
PAPER = {
    "gr120":   (363454, 363454, 363569.5, 9.54, 363454, 363454.0, 8.10),
    "pr124":   (3154346, 3154346, 3154346.0, 5.39, 3154346, 3154346.0, 5.15),
    "bier127": (4545005, 4545005, 4546378.8, 9.25, 4545005, 4545691.9, 7.73),
    "ch130":   (349874, 349874, 349891.7, 9.23, 349874, 349903.5, 8.88),
    "pr136":   (6199268, 6199268, 6199805.4, 17.30, 6199268, 6200041.6, 14.82),
    "gr137":   (4061498, 4061498, 4061498.0, 8.11, 4061498, 4061498.0, 7.16),
    "pr144":   (3846137, 3846137, 3846137.0, 9.11, 3846137, 3846137.0, 8.80),
    "ch150":   (444424, 444424, 444424.0, 13.06, 444424, 444424.0, 10.67),
    "kroA150": (1825769, 1825769, 1825769.0, 19.84, 1825769, 1825769.0, 15.68),
    "kroB150": (1786546, 1786546, 1786546.0, 16.27, 1786546, 1786546.0, 14.49),
    "pr152":   (5064566, 5064566, 5064566.0, 11.23, 5064566, 5064566.0, 10.20),
    "u159":    (2972030, 2972030, 2972204.2, 14.21, 2972030, 2972204.2, 12.92),
    "si175":   (1808532, 1808532, 1808532.0, 19.14, 1808532, 1808532.0, 14.85),
    "brg180":  (174750, 174750, 174750.0, 16.79, 174750, 174750.0, 16.18),
    "rat195":  (218632, 218632, 218763.2, 44.69, 218632, 218736.6, 35.57),
    "d198":    (1186049, 1186049, 1186098.6, 38.28, 1186049, 1186273.3, 31.95),
    "kroA200": (2672437, 2672437, 2672444.2, 42.23, 2672437, 2672444.2, 33.73),
    "kroB200": (2669515, 2669515, 2674486.0, 42.00, 2669515, 2675993.6, 36.17),
    "gr202":   (None, 2909247, 2914644.2, 35.95, 2909247, 2913368.4, 29.68),
    "ts225":   (None, 13240046, 13240046.0, 26.60, 13240046, 13240046.0, 27.10),
    "tsp225":  (None, 402783, 403080.2, 53.89, 402783, 402933.3, 43.43),
    "pr226":   (None, 7196869, 7196869.0, 34.29, 7196869, 7196869.0, 28.85),
    "gr229":   (None, 10725914, 10729883.8, 53.66, 10725914, 10731249.9, 41.12),
    "gil262":  (None, 285060, 285527.1, 96.12, 285060, 285312.6, 74.72),
    "pr264":   (None, 5471615, 5471615.0, 47.02, 5471615, 5471615.0, 38.68),
    "a280":    (None, 346989, 347125.9, 107.18, 346989, 347106.9, 79.05),
    "pr299":   (None, 6556628, 6557983.4, 104.92, 6556628, 6559030.8, 75.93),
    "lin318":  (None, 5619810, 5629995.9, 117.98, 5619810, 5630590.5, 90.74),
    "rd400":   (None, 2768830, 2776672.7, 350.84, 2762532, 2775707.0, 247.61),
    "fl417":   (None, 1874242, 1874242.8, 382.64, 1874242, 1874242.0, 250.61),
    "gr431":   (None, 21159702, 21239150.9, 336.98, 21180562, 21214270.9, 245.10),
    "pr439":   (None, 17829541, 17887107.0, 285.56, 17829541, 17868632.7, 200.02),
    "pcb442":  (None, 10301705, 10323539.7, 413.41, 10301705, 10321465.7, 291.64),
    "d493":    (None, 6684190, 6691057.1, 608.47, 6677458, 6687268.2, 390.16),
    "att532":  (None, 5613010, 5632753.5, 988.04, 5617783, 5628346.4, 760.49),
    "ali535":  (None, 31870389, 31904676.6, 880.76, 31860679, 31910477.9, 570.79),
    "si535":   (None, 12247211, 12250679.7, 498.76, 12248066, 12251841.0, 319.01),
    "pa561":   (None, 658870, 661211.6, 1155.32, 660590, 661790.6, 873.20),
    "u574":    (None, 9314596, 9344178.4, 1234.19, 9308820, 9333295.3, 854.63),
    "rat575":  (None, 1848869, 1859221.1, 1739.46, 1847272, 1856335.1, 1234.05),
    "p654":    (None, 7827273, 7827639.2, 1755.28, 7827273, 7827867.8, 1239.21),
    "d657":    (None, 14159477, 14220133.3, 2615.66, 14112540, 14195797.6, 1779.16),
    "gr666":   (None, 63571693, 63731966.5, 2296.23, 63500984, 63612943.5, 1609.15),
    "u724":    (None, 13506660, 13558605.3, 4651.76, 13504408, 13537514.7, 3132.70),
    "rat783":  (None, 3282794, 3296069.6, 7044.52, 3275858, 3293606.1, 4475.85),
    "dsj1000": (None, 7646018508, 7685887300.0, 18068.70, 7642715113, 7664531851.0, 12233.54),
    "pr1002":  (None, 115550770, 116178260.2, 11963.29, 115420846, 115874237.0, 8029.58),
    "si1032":  (None, 46896355, 46897662.4, 2402.72, 46896355, 46896783.6, 1926.99),
    "u1060":   (None, 102508056, 102759766.0, 15680.50, 102539819, 102759493.6, 9910.02),
    "vm1084":  (None, 94760440, 95053081.2, 13894.43, 94670122, 94960603.3, 9468.85),
    "pcb1173": (None, 30926325, 31032128.8, 20508.89, 30890385, 30957008.7, 14037.76),
    "d1291":   (None, 29383346, 29477239.4, 12171.21, 29389729, 29515210.4, 8072.84),
    "rl1304":  (None, 144886001, 145596878.7, 18617.53, 144592447, 145398549.2, 12407.04),
    "rl1323":  (None, 155697857, 156360364.3, 22758.06, 155719283, 156273365.5, 15115.63),
    "nrw1379": (None, 35360407, 35519379.7, 49624.72, 35291795, 35456093.0, 32038.65),
}
# dsj1000ceil (Table 1) is dsj1000 with CEIL_2D; not in instances/, left out.

SOLVERS = {"gils": "./bin/gils_rvnd", "mdm": "./bin/mdm_gils_rvnd"}


_dims = {}


def _dimension(inst):
    if inst not in _dims:
        for line in open(f"instances/{inst}.tsp"):
            if line.startswith("DIMENSION"):
                _dims[inst] = int(line.split(":")[1])
                break
    return _dims[inst]


# ---------------------------------------------------------------- running

_cache = {}


def closed_nint_latency(inst_path, route):
    """Circuit latency with TSPLIB nint for EUC_2D; None if not a tour."""
    if inst_path not in _cache:
        _cache[inst_path] = read_instance(inst_path)
    coords, etype, matrix = _cache[inst_path]
    n = len(coords)
    if sorted(route) != list(range(n)) or route[0] != 0:
        return None

    def d(a, b):
        if matrix is not None:
            return matrix[a][b]
        if etype == "EUC_2D":
            pa, pb = coords[a + 1], coords[b + 1]
            return int(math.hypot(pa[0] - pb[0], pa[1] - pb[1]) + 0.5)
        return dist(coords[a + 1], coords[b + 1], etype)

    acc = lat = 0
    for a, b in zip(route, route[1:] + [0]):
        acc += d(a, b)
        lat += acc
    return lat


def run_one(cmd, inst_path):
    out = subprocess.run(cmd, capture_output=True, text=True, timeout=24 * 3600)
    if out.returncode != 0:
        raise RuntimeError(out.stderr[:300])
    rec, route = {}, None
    for line in out.stdout.splitlines():
        p = line.split()
        if len(p) >= 2 and p[0] in ("COST", "TIME_MS", "RESTARTS", "MINING_CALLS",
                                    "CLOSED", "NINT"):
            rec[p[0].lower()] = float(p[1])
        elif p and p[0] == "ROUTE":
            route = [int(x) for x in line.split(None, 1)[1].split(",")]
    if rec.get("closed") != 1 or rec.get("nint") != 1:
        raise RuntimeError("solver did not run in closed+nint mode")
    lat = closed_nint_latency(inst_path, route or [])
    if lat is None or lat != int(rec["cost"]):
        raise RuntimeError(f"tour check failed: reported {rec['cost']}, recomputed {lat}")
    return rec


def run(args, insts):
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    data = json.loads(out.read_text()) if out.exists() else {"runs": {}}
    runs = data["runs"]
    todo = [(i, s, k) for i in insts for s in range(1, args.runs + 1) for k in SOLVERS
            if f"{i}|{k}|{s}" not in runs]
    print(f"{len(todo)} runs to go", flush=True)
    t0 = time.time()
    for idx, (inst, seed, key) in enumerate(todo, 1):
        path = f"instances/{inst}.tsp"
        cmd = [SOLVERS[key], path, "--closed", "--nint", "--imax", "10",
               "--iils", str(min(100, _dimension(inst))), "--seed", str(seed)]
        try:
            rec = run_one(cmd, path)
        except Exception as e:
            print(f"  FAILED {inst}|{key}|{seed}: {e}", flush=True)
            continue
        runs[f"{inst}|{key}|{seed}"] = rec
        out.write_text(json.dumps(data))
        print(f"[{idx}/{len(todo)}] {inst}|{key}|{seed} cost={rec['cost']:.0f} "
              f"time={rec['time_ms'] / 1000:.1f}s", flush=True)
    print(f"\nfinished in {(time.time() - t0) / 60:.1f} min\n")


# ---------------------------------------------------------------- report

def report(args, insts):
    runs = json.loads(Path(args.out).read_text())["runs"]
    insts = [i for i in insts
             if all(f"{i}|{k}|{s}" in runs for k in SOLVERS for s in range(1, args.runs + 1))]
    mean = statistics.mean

    def ours(i, k):
        recs = [runs[f"{i}|{k}|{s}"] for s in range(1, args.runs + 1)]
        costs = [r["cost"] for r in recs]
        return min(costs), mean(costs), mean(r["time_ms"] for r in recs) / 1000

    print(f"# {len(insts)} instancias, {args.runs} execucoes cada, circuito + nint\n")
    print("| instancia | n | BKS | GILS paper melhor | GILS nosso melhor | GILS paper media "
          "| GILS nosso media | dif.% | MDM paper melhor | MDM nosso melhor | MDM paper media "
          "| MDM nosso media | dif.% |")
    print("|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|")
    agg = {k: {"rel": [], "w": 0, "t": 0, "l": 0, "best_eq": 0, "best_w": 0, "best_l": 0}
           for k in SOLVERS}
    times = []
    for i in insts:
        bks, gb, ga, gt, mb, ma, mt = PAPER[i]
        row = [i, str(_dimension(i)), f"{bks:,}" if bks else "—"]
        for k, (pb, pa) in (("gils", (gb, ga)), ("mdm", (mb, ma))):
            ob, oa, _ = ours(i, k)
            rel = (oa - pa) / pa * 100
            a = agg[k]
            a["rel"].append(rel)
            if abs(oa - pa) < 0.05:   # the paper prints one decimal
                a["t"] += 1
            elif oa < pa:
                a["w"] += 1
            else:
                a["l"] += 1
            if ob == pb:
                a["best_eq"] += 1
            elif ob < pb:
                a["best_w"] += 1
            else:
                a["best_l"] += 1
            row += [f"{pb:,}", f"{ob:,.0f}", f"{pa:,.1f}", f"{oa:,.1f}", f"{rel:+.3f}"]
        _, _, ogt = ours(i, "gils")
        _, _, omt = ours(i, "mdm")
        times.append((i, gt, mt, ogt, omt))
        print("| " + " | ".join(row) + " |")

    print("\n## Agregado: nossa media vs media do paper\n")
    print("| algoritmo | dif. media% | nossa media melhor / igual / pior | p (sinais) "
          "| melhor solucao: igual / nossa melhor / nossa pior |")
    print("|---|---:|---:|---:|---:|")
    for k, name in (("gils", "GILS-RVND"), ("mdm", "MDM-GILS-RVND")):
        a = agg[k]
        print(f"| {name} | {mean(a['rel']):+.4f} | {a['w']}/{a['t']}/{a['l']} | "
              f"{sign_test_p(a['w'], a['l']):.3f} | "
              f"{a['best_eq']}/{a['best_w']}/{a['best_l']} |")

    print("\n## MDM vs GILS: o efeito, no paper e aqui\n")
    rel_paper = [(PAPER[i][5] - PAPER[i][2]) / PAPER[i][2] * 100 for i in insts]
    rel_ours = [(ours(i, "mdm")[1] - ours(i, "gils")[1]) / ours(i, "gils")[1] * 100 for i in insts]
    tg_paper = [(mt - gt) / gt * 100 for _, gt, mt, _, _ in times]
    tg_ours = [(omt - ogt) / ogt * 100 for _, _, _, ogt, omt in times]
    cnt = lambda xs: (sum(x < -1e-9 for x in xs), sum(abs(x) <= 1e-9 for x in xs),
                      sum(x > 1e-9 for x in xs))
    print("| | paper | nosso |")
    print("|---|---:|---:|")
    print(f"| media: MDM vs GILS, dif. media% | {mean(rel_paper):+.4f} | {mean(rel_ours):+.4f} |")
    print(f"| media: MDM melhor / igual / pior | {'/'.join(map(str, cnt(rel_paper)))} "
          f"| {'/'.join(map(str, cnt(rel_ours)))} |")
    print(f"| tempo: MDM vs GILS, dif. media% | {mean(tg_paper):+.2f} | {mean(tg_ours):+.2f} |")
    print(f"| tempo medio GILS (s) | {mean(t[1] for t in times):.2f} | {mean(t[3] for t in times):.2f} |")

    print("\n### Tempo por instancia (s)\n")
    print("| instancia | GILS paper | GILS nosso | MDM paper | MDM nosso | dif. tempo paper% | dif. tempo nosso% |")
    print("|---|---:|---:|---:|---:|---:|---:|")
    for (i, gt, mt, ogt, omt), a, b in zip(times, tg_paper, tg_ours):
        print(f"| {i} | {gt:.2f} | {ogt:.2f} | {mt:.2f} | {omt:.2f} | {a:+.2f} | {b:+.2f} |")


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--out", required=True)
    ap.add_argument("--max-n", type=int, default=318)
    ap.add_argument("--instances", nargs="+", help="default: every Table 1 instance with n <= --max-n")
    ap.add_argument("--runs", type=int, default=10)
    ap.add_argument("--report-only", action="store_true")
    args = ap.parse_args()

    os.chdir(ROOT)
    insts = args.instances or [i for i in PAPER if _dimension(i) <= args.max_n]
    if not args.report_only:
        run(args, insts)
    report(args, insts)


if __name__ == "__main__":
    main()
