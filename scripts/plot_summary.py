#!/usr/bin/env python3
"""
Figures for docs/reports/resumo-resultados.md, straight from the ablation checkpoints.

  docs/img/gain-vs-n.png        gain of gils_am_rvnd_dlb over GILS-RVND per
                                instance, against n (screening at 30 s and the
                                official batch at 100 s)
  docs/img/component-loss.png   what removing each component from the
                                proposed method costs, per instance (100 s)

    python3 scripts/plot_summary.py
"""
import json, statistics
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from registry import ROOT

SURFACE, INK, INK2, GRID = "#fcfcfb", "#0b0b0b", "#52514e", "#e4e3df"
BLUE, ORANGE, AQUA, YELLOW = "#2a78d6", "#eb6834", "#1baf7a", "#eda100"

plt.rcParams.update({
    "figure.facecolor": SURFACE, "axes.facecolor": SURFACE, "savefig.facecolor": SURFACE,
    "axes.edgecolor": GRID, "axes.labelcolor": INK2, "xtick.color": INK2, "ytick.color": INK2,
    "text.color": INK, "font.size": 10, "axes.spines.top": False, "axes.spines.right": False,
    "axes.axisbelow": True,
})

# label offsets (points) where neighbouring instances would collide
LABEL_OFFSET = {"a280": (-14, 8), "lin318": (16, 8), "pr439": (0, 9), "pcb442": (0, -14)}


def titles(fig, title, subtitle):
    fig.text(0.012, 0.975, title, fontsize=11, color=INK, va="top")
    fig.text(0.012, 0.925, subtitle, fontsize=8, color=INK2, va="top")


def load(name):
    return json.loads((ROOT / "results/ablation" / name).read_text())["runs"]


def dim(inst):
    for line in open(ROOT / f"instances/{inst}.tsp"):
        if line.startswith("DIMENSION"):
            return int(line.split(":")[1])


def gains(runs, insts, base, final):
    """Per instance: gain % of `final` over `base` for each seed (positive = better)."""
    out = {}
    for i in insts:
        g = [(runs[f"{i}|{base}|{s}"]["cost"] - runs[f"{i}|{final}|{s}"]["cost"])
             / runs[f"{i}|{base}|{s}"]["cost"] * 100 for s in range(1, 6)]
        out[i] = g
    return out


def gain_vs_n():
    screen = gains(load("ablation_30s.json"),
                   ["kroA200", "a280", "lin318", "rd400", "pr439",
                    "pcb442", "att532", "rat575", "rat783", "pr1002"],
                   "c0_gils_rvnd", "c7_am")
    official = gains(load("ablation_100s.json"),
                     ["att532", "rat783", "pr1002", "pcb1173", "d1291", "nrw1379"],
                     "k0_gils_rvnd", "k6_am")

    fig, ax = plt.subplots(figsize=(8.2, 4.6), dpi=200)
    ax.grid(axis="y", color=GRID, linewidth=0.8)
    ax.axhline(0, color=INK2, linewidth=0.8)
    for data, color, label, dx, marker in (
            (screen, BLUE, "triagem: 30 s, 3 processos (10 instâncias)", -6, "o"),
            (official, ORANGE, "oficial: 100 s, sequencial (6 instâncias)", 6, "D")):
        xs = [dim(i) + dx for i in data]
        means = [statistics.mean(g) for g in data.values()]
        for x, g in zip(xs, data.values()):
            ax.plot([x, x], [min(g), max(g)], color=color, linewidth=2, alpha=0.35,
                    solid_capstyle="round", zorder=2)
        ax.plot(xs, means, linestyle="none", marker=marker, markersize=7, color=color,
                markeredgecolor=SURFACE, markeredgewidth=1.5, label=label, zorder=3)
    # direct labels: instance names, once per instance, above the higher mean
    names = {**{i: statistics.mean(g) for i, g in screen.items()}}
    for i, g in official.items():
        names[i] = max(names.get(i, -9), statistics.mean(g))
    for i, m in names.items():
        ax.annotate(i, (dim(i), m), textcoords="offset points",
                    xytext=LABEL_OFFSET.get(i, (0, 9)), ha="center", va="center",
                    fontsize=8, color=INK2)
    ax.set_xlabel("tamanho da instância (n)")
    ax.set_ylabel("ganho sobre o GILS-RVND (%)")
    titles(fig, "Ganho do gils_am_rvnd_dlb sobre o GILS-RVND, por instância",
           "ponto = média de 5 seeds; barra = mínimo a máximo entre seeds")
    ax.legend(frameon=False, loc="upper left", fontsize=8.5)
    ax.set_ylim(bottom=min(-0.3, ax.get_ylim()[0]))
    fig.tight_layout(rect=(0, 0, 1, 0.9))
    fig.savefig(ROOT / "docs/img/gain-vs-n.png")
    plt.close(fig)
    return screen, official


def component_loss():
    runs = load("ablation_100s.json")
    insts = ["att532", "rat783", "pr1002", "pcb1173", "d1291", "nrw1379"]
    comps = [("x_cand", "lista de candidatos", BLUE),
             ("x_ext", "8 vizinhanças extras", ORANGE),
             ("x_iils", "I_ILS = 300", AQUA),
             ("x_dlb", "don't-look bits", YELLOW)]
    loss = {c: [statistics.mean((runs[f"{i}|{c}|{s}"]["cost"] - runs[f"{i}|k6_am|{s}"]["cost"])
                                / runs[f"{i}|k6_am|{s}"]["cost"] * 100 for s in range(1, 6))
                for i in insts] for c, _, _ in comps}

    fig, ax = plt.subplots(figsize=(8.2, 4.4), dpi=200)
    ax.grid(axis="y", color=GRID, linewidth=0.8)
    w = 0.19
    for k, (c, label, color) in enumerate(comps):
        xs = [j + (k - 1.5) * (w + 0.01) for j in range(len(insts))]
        bars = ax.bar(xs, loss[c], width=w, color=color, label=label,
                      edgecolor=SURFACE, linewidth=1)
        for x, v in zip(xs, loss[c]):
            ax.annotate(f"{v:.2f}", (x, v), textcoords="offset points",
                        xytext=(0, 2), ha="center", fontsize=6.5, color=INK2)
    ax.axhline(0, color=INK2, linewidth=0.8)
    ax.set_xticks(range(len(insts)))
    ax.set_xticklabels([f"{i}\n(n = {dim(i)})" for i in insts], fontsize=8.5)
    ax.set_ylabel("perda ao retirar do método (%)")
    titles(fig, "Quanto cada componente vale no método proposto (100 s)",
           "média de 5 seeds; positivo = o método piora sem o componente")
    ax.legend(frameon=False, loc="upper left", fontsize=8.5)
    fig.tight_layout(rect=(0, 0, 1, 0.9))
    fig.savefig(ROOT / "docs/img/component-loss.png")
    plt.close(fig)
    return loss


if __name__ == "__main__":
    screen, official = gain_vs_n()
    loss = component_loss()
    for name, data in (("30 s", screen), ("100 s", official)):
        print(name, {i: round(statistics.mean(g), 3) for i, g in data.items()})
    print({c: [round(v, 3) for v in vals] for c, vals in loss.items()})
