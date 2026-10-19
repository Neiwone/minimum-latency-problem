#!/usr/bin/env python3
"""
How much each neighborhood improves the solution, per instance.

Runs the proposed method (gils_am_rvnd_dlb) with --nb-stats, which adds up
the cost removed by every move each neighborhood applies, split into the
descent from a fresh construction (phase 0) and the descents after a
perturbation (phase 1). Sequential, 100 s per run, every tour verified.
Draws docs/img/nb-contribution.png: one bar per instance, split by
neighborhood group, as a share of the cost removed after perturbations.

    python3 scripts/nb_contrib.py --out results/nb-contrib/nb_100s.json
    python3 scripts/nb_contrib.py --out results/nb-contrib/nb_100s.json --report-only
"""
import argparse, json, os, statistics, subprocess, time
from pathlib import Path

from registry import ROOT
from verify_tour import dist, read_instance

INSTANCES = ["kroA200", "a280", "lin318", "rd400", "pr439",
             "pcb442", "att532", "rat575", "rat783", "pr1002"]
CMD = ["./bin/gils_am_rvnd", "--rvnd-mode", "candidate-dlb", "--cand-k", "12",
       "--iils", "300", "--max-time", "100", "--nb-stats"]
NAMES = ["swap", "2opt"] + [f"oropt{L}" for L in range(1, 7)] + [f"rev{L}" for L in range(2, 7)]
GROUPS = [("swap", ["swap"]), ("2-opt", ["2opt"]), ("reinserção (or-opt 1)", ["oropt1"]),
          ("or-opt 2–3", ["oropt2", "oropt3"]), ("or-opt 4–6", ["oropt4", "oropt5", "oropt6"]),
          ("or-opt invertido 2–6", [f"rev{L}" for L in range(2, 7)])]
COLORS = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300"]


def dimension(inst):
    for line in open(f"instances/{inst}.tsp"):
        if line.startswith("DIMENSION"):
            return int(line.split(":")[1])


def run_one(inst, seed):
    path = f"instances/{inst}.tsp"
    out = subprocess.run([CMD[0], path, *CMD[1:], "--seed", str(seed)],
                         capture_output=True, text=True, timeout=3600)
    if out.returncode != 0:
        raise RuntimeError(out.stderr[:300])
    rec = {"stats": {"0": {}, "1": {}}}
    route = None
    for line in out.stdout.splitlines():
        p = line.split()
        if p and p[0] == "COST":
            rec["cost"] = int(p[1])
        elif p and p[0] == "ILS_ITERS":
            rec["ils_iters"] = int(p[1])
        elif p and p[0] == "NB_STATS":
            rec["stats"][p[1]][p[2]] = [int(p[3]), int(p[4])]
        elif p and p[0] == "ROUTE":
            route = [int(x) for x in line.split(None, 1)[1].split(",")]
    coords, etype, m = read_instance(path)
    ok = route and sorted(route) == list(range(len(coords))) and route[0] == 0
    acc = lat = 0
    for a, b in zip(route or [], (route or [])[1:]):
        acc += m[a][b] if m is not None else dist(coords[a + 1], coords[b + 1], etype)
        lat += acc
    if not ok or lat != rec.get("cost"):
        raise RuntimeError(f"tour check failed: reported {rec.get('cost')}, recomputed {lat}")
    return rec


def run(args):
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    data = json.loads(out.read_text()) if out.exists() else {"cmd": CMD, "runs": {}}
    if data["cmd"] != CMD:
        raise SystemExit("checkpoint has a different command; refusing to mix runs")
    todo = [(i, s) for i in args.instances for s in range(1, args.runs + 1)
            if f"{i}|{s}" not in data["runs"]]
    print(f"{len(todo)} runs to go", flush=True)
    t0 = time.time()
    for k, (i, s) in enumerate(todo, 1):
        try:
            rec = run_one(i, s)
        except Exception as e:
            print(f"  FAILED {i}|{s}: {e}", flush=True)
            continue
        data["runs"][f"{i}|{s}"] = rec
        out.write_text(json.dumps(data))
        print(f"[{k}/{len(todo)}] {i}|{s} cost={rec['cost']}", flush=True)
    print(f"\nfinished in {(time.time() - t0) / 60:.1f} min\n")


def shares(data, inst, runs, phase):
    """Per neighborhood: (share % of the cost removed, share % of the moves),
    averaged over seeds."""
    per = {n: ([], []) for n in NAMES}
    for s in range(1, runs + 1):
        st = data["runs"][f"{inst}|{s}"]["stats"][phase]
        gain = sum(v[1] for v in st.values()) or 1
        moves = sum(v[0] for v in st.values()) or 1
        for n in NAMES:
            per[n][0].append(100.0 * st.get(n, [0, 0])[1] / gain)
            per[n][1].append(100.0 * st.get(n, [0, 0])[0] / moves)
    return {n: (statistics.mean(g), statistics.mean(m)) for n, (g, m) in per.items()}


def report(args):
    data = json.loads(Path(args.out).read_text())
    insts = [i for i in args.instances
             if all(f"{i}|{s}" in data["runs"] for s in range(1, args.runs + 1))]
    for phase, title in (("1", "após perturbações (o trabalho do ILS)"),
                         ("0", "1ª descida, a partir da construção")):
        print(f"\n## Participação no custo removido, {title} (% ; média de {args.runs} seeds)\n")
        print("| vizinhança | " + " | ".join(insts) + " | média |")
        print("|---|" + "---:|" * (len(insts) + 1))
        sh = {i: shares(data, i, args.runs, phase) for i in insts}
        for n in NAMES:
            vals = [sh[i][n][0] for i in insts]
            print(f"| {n} | " + " | ".join(f"{v:.1f}" for v in vals)
                  + f" | {statistics.mean(vals):.1f} |")
    print(f"\n## Participação nos movimentos aplicados após perturbações (%)\n")
    print("| vizinhança | " + " | ".join(insts) + " | média |")
    print("|---|" + "---:|" * (len(insts) + 1))
    sh = {i: shares(data, i, args.runs, "1") for i in insts}
    for n in NAMES:
        vals = [sh[i][n][1] for i in insts]
        print(f"| {n} | " + " | ".join(f"{v:.1f}" for v in vals)
              + f" | {statistics.mean(vals):.1f} |")
    plot(data, insts, args.runs)


def plot(data, insts, runs):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    SURFACE, INK, INK2, GRID = "#fcfcfb", "#0b0b0b", "#52514e", "#e4e3df"
    plt.rcParams.update({
        "figure.facecolor": SURFACE, "axes.facecolor": SURFACE, "savefig.facecolor": SURFACE,
        "axes.edgecolor": GRID, "axes.labelcolor": INK2, "xtick.color": INK2,
        "ytick.color": INK2, "text.color": INK, "font.size": 10, "axes.spines.top": False,
        "axes.spines.right": False, "axes.axisbelow": True})

    sh = {i: shares(data, i, runs, "1") for i in insts}
    fig, ax = plt.subplots(figsize=(9.2, 5.2), dpi=200)
    ax.grid(axis="y", color=GRID, linewidth=0.8)
    bottom = [0.0] * len(insts)
    for (label, members), color in zip(GROUPS, COLORS):
        vals = [sum(sh[i][n][0] for n in members) for i in insts]
        ax.bar(range(len(insts)), vals, bottom=bottom, width=0.68, color=color,
               label=label, edgecolor=SURFACE, linewidth=1.5)
        for x, (v, b) in enumerate(zip(vals, bottom)):
            if v >= 6:
                ax.text(x, b + v / 2, f"{v:.0f}%", ha="center", va="center",
                        fontsize=7.5, color="#ffffff" if color in ("#2a78d6", "#eb6834", "#008300")
                        else INK)
        bottom = [b + v for b, v in zip(bottom, vals)]
    ax.set_xticks(range(len(insts)))
    ax.set_xticklabels([f"{i}\n(n = {dimension(i)})" for i in insts], fontsize=8)
    ax.set_ylim(0, 100)
    ax.set_ylabel("participação no custo removido (%)")
    fig.text(0.012, 0.975, "Quanto cada vizinhança melhorou a solução, por instância",
             fontsize=11, color=INK, va="top")
    fig.text(0.012, 0.93, "gils_am_rvnd_dlb, 100 s; custo removido nas descidas após "
             f"perturbações; média de {runs} seeds", fontsize=8, color=INK2, va="top")
    ax.legend(frameon=False, loc="upper left", bbox_to_anchor=(1.0, 1.0), fontsize=8.5,
              reverse=True)
    fig.tight_layout(rect=(0, 0, 1, 0.9))
    fig.savefig(ROOT / "docs/img/nb-contribution.png")
    plt.close(fig)


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--out", required=True)
    ap.add_argument("--instances", nargs="+", default=INSTANCES)
    ap.add_argument("--runs", type=int, default=3)
    ap.add_argument("--report-only", action="store_true")
    args = ap.parse_args()
    os.chdir(ROOT)
    if not args.report_only:
        run(args)
    report(args)


if __name__ == "__main__":
    main()
