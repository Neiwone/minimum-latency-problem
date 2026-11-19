"""LaTeX ablation table for the TCC, from results/ablation/ablation_100s.json
(official100 suite of scripts/ablation.py: 6 TSPLIB instances, n >= 500, 100 s,
seeds 1-5). Laid out like the sensitivity analysis of Haddad et al. (2018,
arXiv:1802.06318, Tables 9-10): one row for the full method and one per
component removed, mean gap (%) per instance and overall, and the p-value of a
paired Wilcoxon test against the full method (30 pairs, relative differences).

The gap is against the reference of ablation.report: the best of the tracked
best-known solution and every cost found in the batch.

    PYTHONPATH=scripts python3 scripts/tcc_ablation_table.py > ../tcc/Tabelas/ablacao.tex
"""
import json
import statistics

from ablation import CHAIN100, pairs
from registry import BEST_SOLUTIONS_FILE, ROOT
from stats import wilcoxon_p

INSTS = ["att532", "rat783", "pr1002", "pcb1173", "d1291", "nrw1379"]
SEEDS = range(1, 6)
FULL = CHAIN100[-1][0]
ROWS = [("Método completo", FULL),
        ("Sem lista de candidatos", "x_cand"),
        ("Sem vizinhanças adicionais", "x_ext"),
        (r"Sem \textit{don't-look bits}", "x_dlb"),
        (r"Com $I_{ILS} = 100$", "x_iils"),
        ("Sem memória adaptativa", "k5_rcl_thresh")]

runs = json.loads((ROOT / "results/ablation/ablation_100s.json").read_text())["runs"]
best = json.loads((ROOT / BEST_SOLUTIONS_FILE).read_text())
ref = {i: min([r["cost"] for k, r in runs.items() if k.startswith(i + "|")]
              + ([best[i]["cost"]] if i in best else [])) for i in INSTS}


def gap(i, arm):
    g = [(runs[f"{i}|{arm}|{s}"]["cost"] - ref[i]) / ref[i] * 100 for s in SEEDS]
    assert len(g) == len(SEEDS)
    return statistics.mean(g)


def num(x):
    return f"{x:.3f}".replace(".", "{,}")


def pval(p):
    if p < 1e-3:
        m, e = f"{p:.1e}".split("e")
        return rf"${m.replace('.', '{,}')} \times 10^{{{int(e)}}}$"
    return f"{p:.3f}".replace(".", "{,}")


lines = []
for name, arm in ROWS:
    gaps = [gap(i, arm) for i in INSTS]
    if arm == FULL:
        p = "--"
    else:
        pr = pairs(runs, INSTS, SEEDS, FULL, arm)
        assert len(pr) == 30, (arm, len(pr))
        p = pval(wilcoxon_p([(a - b) / b * 100 for b, a in pr]))
    lines.append(f"{name} & " + " & ".join(num(g) for g in gaps)
                 + f" & {num(statistics.mean(gaps))} & {p} \\\\")
    if arm == FULL:
        lines.append(r"\midrule")

print(r"""% gerado por scripts/tcc_ablation_table.py (minimum-latency-problem); não editar à mão
\begin{table}[htbp]
\centering
\footnotesize
\setlength{\tabcolsep}{4pt}
\caption{Gap médio (\%) de cada configuração do método proposto em relação à melhor solução conhecida e $p$-valor do teste de Wilcoxon pareado contra o método completo.}
\label{tab:ablacao}
\begin{tabular}{l""" + "r" * (len(INSTS) + 2) + r"""}
\toprule
Configuração & """ + " & ".join(INSTS) + r""" & Média & $p$-valor \\
\midrule
""" + "\n".join(lines) + r"""
\bottomrule
\end{tabular}
\end{table}""")
