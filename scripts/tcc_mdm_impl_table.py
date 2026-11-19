#!/usr/bin/env python3
"""
LaTeX table for the TCC: our MDM-GILS-RVND against the one published by
Santana, Plastino & Rosseti (2019), Table 1, on the circuit set: best /
average / time from the paper, then best / average / gap / time / time gap
of ours, gaps against the paper's average and time.

Ours comes from scripts/run_circuit_equal_time.sh (the paper's stopping rule,
I_max = 10, I_ILS = min(100, n), seeds 1..10). Only instances with all 10
runs are listed. Bold marks the better value of the two, both on a tie.

    PYTHONPATH=scripts python3 scripts/tcc_mdm_impl_table.py > ../tcc/Tabelas/comparacao_mdm_implementacao.tex
"""
from statistics import mean

from literature_compare import rel, wtl
from mdm_paper_compare import PAPER
from tcc_mdm_table import load, num


def main():
    ours = load("results/literature/circuit_mdm.json", 10)
    rows, gaps, t_gaps = [], [], []
    for inst in [i for i in PAPER if i in ours]:
        pb, pa, pt = PAPER[inst][4:]
        costs = [float(r["cost"]) for r in ours[inst]]
        ob, oa = min(costs), mean(costs)
        ot = mean(float(r["time_ms"]) for r in ours[inst]) / 1000
        bw, _, bl = wtl([(ob, pb)])
        aw, _, al = wtl([(oa, pa)])
        bold = {"ours": (not bl, not al), "paper": (not bw, not aw)}
        gaps.append(rel(oa, pa))
        t_gaps.append(rel(ot, pt))
        name = "dsj1000ceil" if inst == "dsj1000" else inst   # PAPER keeps the CEIL_2D row
        rows.append(" & ".join([
            name,
            num(pb, bold=bold["paper"][0]), num(pa, 1, bold=bold["paper"][1]), num(pt, 2),
            num(ob, bold=bold["ours"][0]), num(oa, 1, bold=bold["ours"][1]),
            num(gaps[-1], 3, sign=True), num(ot, 2), num(t_gaps[-1], 1, sign=True),
        ]) + " \\\\")

    head = ("\\toprule\n"
            "& \\multicolumn{3}{c}{MDM-GILS-RVND (paper)} "
            "& \\multicolumn{5}{c}{MDM-GILS-RVND (reimplementação)} \\\\\n"
            "\\cmidrule(lr){2-4}\\cmidrule(lr){5-9}\n"
            + " & ".join(f"\\multicolumn{{1}}{{l}}{{{h}}}" for h in   # left headers over right-aligned values
                         ["Instância", "Melhor", "Média", "Tempo (s)", "Melhor", "Média",
                          "Gap (\\%)", "Tempo (s)", "Gap Tempo (\\%)"]) + " \\\\\n"
            "\\midrule")
    print("% Gerado por scripts/tcc_mdm_impl_table.py (projeto minimum-latency-problem); não editar à mão.")
    print("\\begin{landscape}")
    print("\\footnotesize")
    print("\\setlength{\\tabcolsep}{3pt}")
    print("\\setlength{\\LTcapwidth}{\\linewidth}")
    print("\\begin{longtable}{lrrrrrrrr}")
    print("\\caption{Resultados do MDM-GILS-RVND reportados por \\cite{santana2019} "
          "e obtidos pela reimplementação deste trabalho.}")
    print("\\label{tab:comparacao-mdm-implementacao} \\\\")
    print(head)
    print("\\endfirsthead")
    print("\\multicolumn{9}{l}{\\textit{(continuação)}} \\\\")
    print(head)
    print("\\endhead")
    print("\\midrule\\multicolumn{9}{r}{\\textit{(continua)}} \\\\")
    print("\\endfoot")
    print("\\endlastfoot")
    print("\n".join(rows))
    print("\\midrule")
    if gaps:
        print(f"Média & & & & & & {num(mean(gaps), 3, sign=True)} & "
              f"& {num(mean(t_gaps), 1, sign=True)} \\\\")
    print("\\bottomrule")
    print("\\end{longtable}")
    print("\\end{landscape}")


if __name__ == "__main__":
    main()
