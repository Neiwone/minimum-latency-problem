#!/usr/bin/env python3
"""Per-instance cost/gap table over a fixed-time checkpoint."""
import json, sys
from collections import defaultdict
from pathlib import Path

BKS = json.loads(Path("instances/solutions/best_solutions.json").read_text())

def bks_of(inst):
    v = BKS.get(inst)
    if isinstance(v, dict):
        return v.get("cost")
    return v

path = sys.argv[1]
d = json.loads(Path(path).read_text())
by = defaultdict(list)
rst = defaultdict(list)
for k, v in d.items():
    inst, solver, seed = k.split("|")
    by[(inst, solver)].append(v["cost"])
    rst[(inst, solver)].append(v.get("restarts", 0))

insts = sorted({k[0] for k in by})
solvers = sorted({k[1] for k in by})
print(f"{'instancia':14s} {'solver':26s} {'n runs':>6s} {'melhor':>14s} {'medio':>14s} "
      f"{'gap medio%':>10s} {'gap best%':>10s} {'restarts':>9s}")
for inst in insts:
    b = bks_of(inst)
    for s in solvers:
        v = by.get((inst, s))
        if not v:
            continue
        mean = sum(v) / len(v)
        gm = f"{100*(mean-b)/b:10.3f}" if b else f"{'-':>10s}"
        gb = f"{100*(min(v)-b)/b:10.3f}" if b else f"{'-':>10s}"
        print(f"{inst:14s} {s:26s} {len(v):6d} {min(v):14.0f} {mean:14.1f} {gm} {gb} "
              f"{sum(rst[(inst,s)])/len(v):9.0f}")
