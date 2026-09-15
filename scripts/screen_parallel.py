#!/usr/bin/env python3
"""
Triage harness for fixed-time variant screening.

run_experiments.py --mode fixed-time is the official protocol and runs
strictly sequentially (a timing comparison does not survive CPU
contention). That is right for a verdict, but it makes a screening sweep
over many variants cost hours of wall clock.

This script buys back the wall clock without breaking the pairing: it
runs the variants for ONE (instance, seed) cell CONCURRENTLY, in groups
of exactly `--jobs` processes, padding the last group with a throwaway
process so the machine load is identical for every measured run. Every
run in a comparison therefore sees the same contention, and the pairing
is per (instance, seed) as usual.

Measured contention on this machine (lin318, 20 s, same seed):
  sequential 112 restarts | 2 procs 91 | 3 procs 82 | 6 procs 59
so 3 concurrent processes cost ~27% of the throughput -- uniformly. Use
this to RANK variants, never to report a final number: the official
100 s verdict runs come from run_experiments.py.
"""
import argparse, json, math, os, subprocess, sys, time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path


def sign_test(wins, losses):
    n = wins + losses
    if n == 0:
        return 1.0
    k = min(wins, losses)
    p = sum(math.comb(n, i) for i in range(k + 1)) / (2 ** n)
    return min(1.0, 2 * p)


def run_one(cmd):
    out = subprocess.run(cmd, capture_output=True, text=True, timeout=3600)
    if out.returncode != 0:
        raise RuntimeError(out.stderr[:300])
    d = {}
    for line in out.stdout.splitlines():
        parts = line.split()
        if len(parts) >= 2 and parts[0] in ("COST", "TIME_MS", "RESTARTS", "MINING_CALLS"):
            d[parts[0]] = float(parts[1])
    return d


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--variants", nargs="+", required=True,
                    help="label=binary[,arg,arg,...]")
    ap.add_argument("--instances", nargs="+", required=True)
    ap.add_argument("--time-limit", type=float, required=True)
    ap.add_argument("--runs", type=int, default=6)
    ap.add_argument("--iils", type=int, default=10)
    ap.add_argument("--jobs", type=int, default=3)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    variants = []
    for v in args.variants:
        label, spec = v.split("=", 1)
        parts = spec.split(",")
        variants.append((label, parts[0], parts[1:]))

    out_path = Path(args.out)
    results = json.loads(out_path.read_text()) if out_path.exists() else {}

    inst_paths = []
    for name in args.instances:
        p = name if "/" in name else f"instances/{name}.tsp"
        if not os.path.exists(p):
            sys.exit(f"missing instance {p}")
        inst_paths.append((Path(p).stem, p))

    pad = (-len(variants)) % args.jobs
    t0 = time.time()
    total = len(inst_paths) * len(variants) * args.runs
    done = 0

    for inst_name, inst_path in inst_paths:
        for seed in range(1, args.runs + 1):
            cells = []
            for label, binary, extra in variants:
                key = f"{inst_name}|{label}|{seed}"
                cmd = [binary, inst_path, *extra,
                       "--max-time", str(args.time_limit),
                       "--seed", str(seed)]
                # a per-variant --iils in the spec wins over the batch default
                if "--iils" not in extra:
                    cmd += ["--iils", str(args.iils)]
                cells.append((key, cmd))
            # keep the machine load identical for the measured runs
            filler = [(None, cells[0][1]) for _ in range(pad)]
            batch = cells + filler
            if all(k in results for k, _ in cells):
                done += len(cells)
                continue
            for g in range(0, len(batch), args.jobs):
                group = batch[g:g + args.jobs]
                with ThreadPoolExecutor(max_workers=args.jobs) as ex:
                    futs = [(k, ex.submit(run_one, c)) for k, c in group]
                    for k, f in futs:
                        try:
                            d = f.result()
                        except Exception as e:
                            print(f"  FAILED {k}: {e}", flush=True)
                            continue
                        if k is None:
                            continue
                        results[k] = d
                        done += 1
                        print(f"[{done}/{total}] {k:44s} cost={d['COST']:.0f} "
                              f"restarts={d.get('RESTARTS', -1):.0f}", flush=True)
            out_path.write_text(json.dumps(results))

    print(f"\nfinished in {(time.time()-t0)/60:.1f} min\n")
    report(results, inst_paths, variants, args)


def report(results, inst_paths, variants, args):
    base_label = variants[0][0]
    print(f"baseline: {base_label}\n")
    for label, _, _ in variants[1:]:
        print(f"--- {label} vs {base_label} ---")
        print(f"{'instancia':16s} {'mean_rel%':>10s} {'W/T/L':>10s} {'p':>8s} "
              f"{'restarts':>9s}")
        agg_w = agg_t = agg_l = 0
        agg_rel = []
        for inst_name, _ in inst_paths:
            rels, w, t, l, rs = [], 0, 0, 0, []
            for seed in range(1, args.runs + 1):
                a = results.get(f"{inst_name}|{base_label}|{seed}")
                b = results.get(f"{inst_name}|{label}|{seed}")
                if not a or not b:
                    continue
                rels.append((b["COST"] - a["COST"]) / a["COST"] * 100)
                rs.append(b.get("RESTARTS", 0))
                if b["COST"] < a["COST"]: w += 1
                elif b["COST"] > a["COST"]: l += 1
                else: t += 1
            if not rels:
                continue
            agg_w += w; agg_t += t; agg_l += l; agg_rel += rels
            print(f"{inst_name:16s} {sum(rels)/len(rels):+10.3f} "
                  f"{f'{w}/{t}/{l}':>10s} {sign_test(w, l):8.4f} "
                  f"{sum(rs)/len(rs):9.0f}")
        if agg_rel:
            print(f"{'AGREGADO':16s} {sum(agg_rel)/len(agg_rel):+10.3f} "
                  f"{f'{agg_w}/{agg_t}/{agg_l}':>10s} "
                  f"{sign_test(agg_w, agg_l):8.4f}")
        print()


if __name__ == "__main__":
    main()
