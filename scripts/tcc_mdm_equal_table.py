#!/usr/bin/env python3
"""
LaTeX table for the TCC: the proposal against our MDM-GILS-RVND at equal time
on the circuit set of Santana et al. (2019), Table 1, laid out like the
Salehipour table: proven optimum, best / average / time of MDM-GILS-RVND, then
best / average / gap / time of the proposal, gap = proposal average against
the MDM average.

Both come from scripts/run_circuit_equal_time.sh: MDM-GILS-RVND under the
paper's stopping rule (I_max = 10, I_ILS = min(100, n)), then the proposal with
the MDM mean time on each instance. Only instances with all 10 runs of both
methods are listed, so the table can be built while the batch is running.
Bold marks the better value of the two, both on a tie.

    PYTHONPATH=scripts python3 scripts/tcc_mdm_equal_table.py > ../tcc/Tabelas/comparacao_mdm.tex
"""
from statistics import mean

from literature_compare import rel, wtl
from mdm_paper_compare import PAPER
from tcc_mdm_table import OPTIMAL, load, num


def main():
    mdm = load("results/literature/circuit_mdm.json", 10)
    ours = load("results/literature/circuit_mdm_budget.json", 10)
    rows, gaps = [], []
    best_or_tie = {"mdm": [0, 0], "ours": [0, 0]}   # [best, avg]
    insts = [i for i in PAPER if i in mdm and i in ours]
    for inst in insts:
        mcosts = [float(r["cost"]) for r in mdm[inst]]
        mb, ma = min(mcosts), mean(mcosts)
        mt = mean(float(r["time_ms"]) for r in mdm[inst]) / 1000
        costs = [float(r["cost"]) for r in ours[inst]]
        ob, oa = min(costs), mean(costs)
        ot = mean(float(r["time_ms"]) for r in ours[inst]) / 1000
        bw, _, bl = wtl([(ob, mb)])
        aw, _, al = wtl([(oa, ma)])
        bold = {"ours": (not bl, not al), "mdm": (not bw, not aw)}
        for k, (b, a) in bold.items():
            best_or_tie[k][0] += b
            best_or_tie[k][1] += a
        gaps.append(rel(oa, ma))
        name = "dsj1000ceil" if inst == "dsj1000" else inst   # PAPER keeps the CEIL_2D row
        rows.append(" & ".join([
            name, num(PAPER[inst][0]) if inst in OPTIMAL else "--",
            num(mb, bold=bold["mdm"][0]), num(ma, 1, bold=bold["mdm"][1]), num(mt, 2),
            num(ob, bold=bold["ours"][0]), num(oa, 1, bold=bold["ours"][1]),
            num(gaps[-1], 3, sign=True), num(ot, 2),
        ]) + " \\\\")

    head = ("\\toprule\n"
            "& & \\multicolumn{3}{c}{MDM-GILS-RVND} & \\multicolumn{4}{c}{Proposta} \\\\\n"
            "\\cmidrule(lr){3-5}\\cmidrule(lr){6-9}\n"
            "Instância & Ótimo & Melhor & Média & Tempo (s) & Melhor & Média & Gap (\\%) & Tempo (s) \\\\\n"
            "\\midrule")
    print("% Gerado por scripts/tcc_mdm_equal_table.py (projeto minimum-latency-problem); não editar à mão.")
    print("\\begin{landscape}")
    print("\\footnotesize")
    print("\\setlength{\\tabcolsep}{3pt}")
    print("\\setlength{\\LTcapwidth}{\\linewidth}")
    print("\\begin{longtable}{lrrrrrrrr}")
    print("\\caption{Resultados das instâncias TSPLIB de \\cite{santana2019}.}")
    print("\\label{tab:comparacao-mdm} \\\\")
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
        print(f"Média & & & & & & & {num(mean(gaps), 3, sign=True)} & \\\\")
    print(f"Melhor/Igual em & & {best_or_tie['mdm'][0]} & {best_or_tie['mdm'][1]} & "
          f"& {best_or_tie['ours'][0]} & {best_or_tie['ours'][1]} & & \\\\")
    print("\\bottomrule")
    print("\\end{longtable}")
    print("\\end{landscape}")


if __name__ == "__main__":
    main()
