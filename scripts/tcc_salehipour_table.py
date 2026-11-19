#!/usr/bin/env python3
"""
LaTeX table for the TCC: the proposal against our GILS-RVND on the 10 TSPLIB
instances selected by Salehipour et al. (2011) (Table 2 of Silva et al., 2012):
best / average / time of each method, plus the gap of the proposal's average
to the GILS-RVND average. Hamiltonian path, truncated EUC_2D.

Both methods ran on this machine with seeds 1..10: GILS-RVND under the
paper's stopping rule (I_max = 10, I_ILS = min(100, n)), then the proposal with
the GILS-RVND mean time on each instance as its time limit.
Bold marks the better value of the two, both on a tie.

    python3 scripts/literature_compare.py --suite path --method gils_rvnd_paper --out results/literature/path_gils_rvnd.json --cores 2
    python3 scripts/literature_compare.py --suite path --cap 100000 --budget-from results/literature/path_gils_rvnd.json --out results/literature/path_gils_budget.json --cores 2
    PYTHONPATH=scripts python3 scripts/tcc_salehipour_table.py > ../tcc/Tabelas/comparacao_salehipour.tex
"""
from statistics import mean

from literature_compare import SILVA_T2, rel, wtl
from tcc_mdm_table import load, num


def main():
    ours = load("results/literature/path_gils_budget.json", 10)
    gils = load("results/literature/path_gils_rvnd.json", 10)
    rows, gaps = [], []
    best_or_tie = {"ours": [0, 0], "gils": [0, 0]}   # [best, avg]
    for inst in SILVA_T2:
        gcosts = [float(r["cost"]) for r in gils[inst]]
        gb, ga = min(gcosts), mean(gcosts)
        gt = mean(float(r["time_ms"]) for r in gils[inst]) / 1000
        costs = [float(r["cost"]) for r in ours[inst]]
        ob, oa = min(costs), mean(costs)
        ot = mean(float(r["time_ms"]) for r in ours[inst]) / 1000
        bw, _, bl = wtl([(ob, gb)])
        aw, _, al = wtl([(oa, ga)])
        bold = {"ours": (not bl, not al), "gils": (not bw, not aw)}
        for k, (b, a) in bold.items():
            best_or_tie[k][0] += b
            best_or_tie[k][1] += a
        gaps.append(rel(oa, ga))
        rows.append(" & ".join([
            inst,
            num(gb, bold=bold["gils"][0]), num(ga, 1, bold=bold["gils"][1]), num(gt, 2),
            num(ob, bold=bold["ours"][0]), num(oa, 1, bold=bold["ours"][1]),
            num(gaps[-1], 3, sign=True), num(ot, 2),
        ]) + " \\\\")

    print("% Gerado por scripts/tcc_salehipour_table.py (projeto minimum-latency-problem); não editar à mão.")
    print("\\begin{table}[htbp]")
    print("\\centering")
    print("\\footnotesize")
    print("\\setlength{\\tabcolsep}{3pt}")
    print("\\caption{Resultados das instâncias TSPLIB selecionadas por \\cite{salehipour2011}.}")
    print("\\label{tab:comparacao-salehipour}")
    print("\\begin{tabular}{lrrrrrrr}")
    print("\\toprule")
    print("& \\multicolumn{3}{c}{GILS-RVND} & \\multicolumn{4}{c}{Proposta} \\\\")
    print("\\cmidrule(lr){2-4}\\cmidrule(lr){5-8}")
    print("Instância & Melhor & Média & Tempo (s) & Melhor & Média & Gap (\\%) & Tempo (s) \\\\")
    print("\\midrule")
    print("\n".join(rows))
    print("\\midrule")
    print(f"Média & & & & & & {num(mean(gaps), 3, sign=True)} & \\\\")
    print(f"Melhor/Igual em & {best_or_tie['gils'][0]} & {best_or_tie['gils'][1]} & "
          f"& {best_or_tie['ours'][0]} & {best_or_tie['ours'][1]} & & \\\\")
    print("\\bottomrule")
    print("\\end{tabular}")
    print("\\end{table}")

if __name__ == "__main__":
    main()
