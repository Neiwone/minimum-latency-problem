"""pgfplots version of docs/img/nb-contribution.png for the TCC: per instance,
the share of the cost removed by each of the 13 neighborhoods (descents after
perturbations), stacked to 100%. Swap, 2-opt and reinsertion keep the colors of
nb_contrib.plot; or-opt 2-6 are shades of amber and reversed or-opt 2-6 shades
of purple, darker for shorter segments. * marks the neighborhoods added by
this work (not in the GILS-RVND).

    PYTHONPATH=scripts python3 scripts/tcc_nb_instance_figure.py > ../tcc/Figuras/contribuicao_vizinhancas_instancia.tex
"""
import json
from pathlib import Path

from nb_contrib import INSTANCES, NAMES, dimension, shares

RUNS = 3
BASES = {"swap": "2A78D6", "2opt": "EB6834", "oropt1": "1BAF7A", "oropt": "EDA100", "rev": "7B3FA0"}
SHADES = [100, 75, 55, 40, 28]  # % of the base color for segment lengths 2..6
# name -> (legend label, tikz color, label text color)
STYLE = {"swap": ("Swap", "nbswap", "white"), "2opt": ("2-opt", "nb2opt", "white"),
         "oropt1": ("Reinserção", "nboropt1", "black"),
         **{f"oropt{L}": (f"Or-opt-{L}" + ("*" if L >= 4 else ""), f"nboropt!{SHADES[L - 2]}!white", "black")
            for L in range(2, 7)},
         **{f"rev{L}": (f"Or-opt-{L} invertido*", f"nbrev!{SHADES[L - 2]}!white",
                        "white" if L <= 3 else "black") for L in range(2, 7)}}

data = json.loads(Path("results/nb-contrib/nb_100s.json").read_text())
sh = {i: shares(data, i, RUNS, "1") for i in INSTANCES}
vals = [[sh[i][n][0] for i in INSTANCES] for n in NAMES]
for k in range(len(INSTANCES)):
    assert abs(sum(v[k] for v in vals) - 100) < 1e-6

out = [r"% gerado por scripts/tcc_nb_instance_figure.py (minimum-latency-problem); não editar à mão",
       r"\begin{tikzpicture}"]
out += [rf"  \definecolor{{nb{k}}}{{HTML}}{{{c}}}" for k, c in BASES.items()]
out += [r"  \begin{axis}[",
        r"    width=0.9\textwidth, height=0.66\textwidth,",
        r"    ybar stacked, bar width=0.62, ymin=0, ymax=100,",
        r"    ymajorgrids, grid style={gray!25}, ylabel={Participação no custo removido (\%)},",
        rf"    xmin=-0.5, xmax={len(INSTANCES) - 0.5}, xtick={{0,...,{len(INSTANCES) - 1}}},",
        r"    xticklabels={" + ",".join(rf"{{{i}\\($n={dimension(i)}$)}}" for i in INSTANCES) + "},",
        r"    xticklabel style={font=\scriptsize, align=center}, yticklabel style={font=\small},",
        r"    legend style={at={(0.5,1.03)}, anchor=south, legend columns=5, font=\scriptsize, draw=none,",
        r"                  /tikz/every even column/.append style={column sep=0.8em}},",
        r"    legend cell align=left,",
        r"  ]"]
for n, v in zip(NAMES, vals):
    label, color, _ = STYLE[n]
    pts = " ".join(f"({k},{x:.2f})" for k, x in enumerate(v))
    out.append(rf"    \addplot[fill={color}, draw=white] coordinates {{{pts}}};")
    out.append(rf"    \addlegendentry{{{label}}}")
    if n == "oropt1":  # two blank cells, so each family starts a legend row
        out += [r"    \addlegendimage{empty legend}\addlegendentry{}"] * 2
bottom = [0.0] * len(INSTANCES)
labels = []  # drawn after the axis, otherwise the stacked bars cover them
for g, (n, v) in enumerate(zip(NAMES, vals)):
    text = STYLE[n][2]
    for k, x in enumerate(v):
        if x >= 6:
            out.append(rf"    \coordinate (l{g}-{k}) at (axis cs:{k},{bottom[k] + x / 2:.2f});")
            labels.append(rf"  \node[font=\scriptsize, text={text}] at (l{g}-{k}) {{{x:.0f}\%}};")
        bottom[k] += x
out += [r"  \end{axis}", *labels, r"\end{tikzpicture}"]
print("\n".join(out))
