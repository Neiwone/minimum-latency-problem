#!/usr/bin/env python3
"""Paired report over a screen_parallel.py checkpoint (works on partial data)."""
import json, math, sys
from collections import defaultdict

def sign_test(w, l):
    n = w + l
    if n == 0: return 1.0
    k = min(w, l)
    return min(1.0, 2 * sum(math.comb(n, i) for i in range(k + 1)) / 2 ** n)

path, base = sys.argv[1], sys.argv[2]
data = json.loads(open(path).read())
cells = defaultdict(dict)          # (inst, seed) -> label -> cost
restarts = defaultdict(list)
for k, v in data.items():
    inst, label, seed = k.split("|")
    cost = v["COST"] if "COST" in v else v["cost"]
    cells[(inst, seed)][label] = cost
    restarts[(inst, label)].append(v.get("RESTARTS", v.get("restarts", 0)))

labels = sorted({k.split("|")[1] for k in data})
insts = sorted({k.split("|")[0] for k in data})

for lab in labels:
    if lab == base: continue
    print(f"--- {lab} vs {base} ---")
    aw = al = 0; arel = []
    for inst in insts:
        rels, w, t, l = [], 0, 0, 0
        for (i, s), d in cells.items():
            if i != inst or base not in d or lab not in d: continue
            rels.append((d[lab] - d[base]) / d[base] * 100)
            if d[lab] < d[base]: w += 1
            elif d[lab] > d[base]: l += 1
            else: t += 1
        if not rels: continue
        aw += w; al += l; arel += rels
        rs = restarts[(inst, lab)]
        print(f"  {inst:10s} {sum(rels)/len(rels):+8.3f}%  {w}/{t}/{l:<3d} "
              f"p={sign_test(w,l):.4f}  restarts={sum(rs)/len(rs):.0f}")
    if arel:
        print(f"  {'TOTAL':10s} {sum(arel)/len(arel):+8.3f}%  {aw}/-/{al:<3d} "
              f"p={sign_test(aw,al):.4f}   (N={len(arel)})")
    print()
