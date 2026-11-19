"""LaTeX table for the TCC: mean share (%) of the cost removed by each of the 13
neighborhoods over the 10 instances (descents after perturbations), from the
same --nb-stats data as docs/img/nb-contribution.png, split into the 5
neighborhoods of the GILS-RVND (Silva et al., 2012) and the 8 added by this
work, with a subtotal for each.

    PYTHONPATH=scripts python3 scripts/tcc_nb_table.py > ../tcc/Tabelas/contribuicao_vizinhancas.tex
"""
import json, statistics
from pathlib import Path

from nb_contrib import INSTANCES, NAMES, shares

RUNS = 3
LABELS = {"swap": "Swap", "2opt": "2-opt", "oropt1": "Reinserção",
          **{f"oropt{L}": f"Or-opt-{L}" for L in range(2, 7)},
          **{f"rev{L}": f"Or-opt-{L} invertido" for L in range(2, 7)}}
ORIGINS = [("Vizinhanças do GILS-RVND", ["swap", "2opt", "oropt1", "oropt2", "oropt3"]),
           ("Vizinhanças adicionadas neste trabalho",
            ["oropt4", "oropt5", "oropt6"] + [f"rev{L}" for L in range(2, 7)])]

data = json.loads(Path("results/nb-contrib/nb_100s.json").read_text())
sh = {i: shares(data, i, RUNS, "1") for i in INSTANCES}
mean = {n: statistics.mean(sh[i][n][0] for i in INSTANCES) for n in NAMES}
assert abs(sum(mean.values()) - 100) < 1e-6  # shares add up to 100% per instance


def pct(x):
    return f"{x:.1f}".replace(".", "{,}")


assert sorted(n for _, ms in ORIGINS for n in ms) == sorted(NAMES)
rows = []
for k, (origin, members) in enumerate(ORIGINS):
    if k:
        rows.append(r"\midrule")
    rows.append(rf"\multicolumn{{2}}{{l}}{{\textit{{{origin}}}}} \\")
    rows.append(r"\midrule")
    rows += [f"{LABELS[n]} & {pct(mean[n])} \\\\" for n in members]
    rows.append(rf"\textbf{{Subtotal}} & \textbf{{{pct(sum(mean[n] for n in members))}}} \\")
print(r"""% gerado por scripts/tcc_nb_table.py (minimum-latency-problem); não editar à mão
\begin{table}[htbp]
\centering
\caption{Participação média de cada estrutura de vizinhança no custo removido pela busca local, nas descidas após as perturbações (média de 10 instâncias, com 3 execuções de 100~s cada).}
\label{tab:contribuicao-vizinhancas}
\begin{tabular}{lr}
\toprule
Vizinhança & Custo removido (\%) \\
\midrule
""" + "\n".join(rows) + r"""
\bottomrule
\end{tabular}
\end{table}""")
