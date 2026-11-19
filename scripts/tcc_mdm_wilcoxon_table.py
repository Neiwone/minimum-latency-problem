#!/usr/bin/env python3
"""
LaTeX table for the TCC: does the published MDM-GILS-RVND (Santana et al.,
2019, Table 1) or our reimplementation dominate, at equal time?

Ours ran with the paper's mean time per instance as its limit (method
mdm_gils_rvnd of literature_compare, I_ILS = 100, seeds 1..10). The paper only
gives the mean of its 10 runs, so per instance the test is a one-sample
Wilcoxon signed-rank of our 10 costs against that mean; across instances, a
paired Wilcoxon of the two means (as relative gaps). Differences up to 0.05
count as ties, like the bold rule of the other tables. Only instances with all
10 runs are listed.

    PYTHONPATH=scripts python3 scripts/tcc_mdm_wilcoxon_table.py > ../tcc/Tabelas/comparacao_mdm_wilcoxon.tex
"""
from statistics import mean, stdev

from literature_compare import rel
from mdm_paper_compare import PAPER
from stats import wilcoxon_p
from tcc_mdm_table import load, num

ALPHA = 0.05


def diff(x, ref):
    return 0 if abs(x - ref) <= 0.05 else x - ref


def pval(p):
    return "$<$\\,0{,}001" if p < 0.001 else num(p, 3)


def main():
    ours = load("results/literature/circuit_mdm_paper_time.json", 10)
    rows, gaps, wins = [], [], {"Artigo": 0, "Reimpl.": 0, "--": 0}
    for inst in [i for i in PAPER if i in ours]:
        pa, pt = PAPER[inst][5], PAPER[inst][6]
        costs = [float(r["cost"]) for r in ours[inst]]
        oa = mean(costs)
        p = wilcoxon_p([diff(c, pa) for c in costs])
        dom = "--" if p >= ALPHA else ("Reimpl." if oa < pa else "Artigo")
        wins[dom] += 1
        gaps.append(rel(oa, pa) if diff(oa, pa) else 0.0)
        name = "dsj1000ceil" if inst == "dsj1000" else inst   # PAPER keeps the CEIL_2D row
        rows.append(" & ".join([
            name, num(pt, 2), num(pa, 1),
            num(min(costs)), num(oa, 1), num(stdev(costs), 1),
            num(gaps[-1], 3, sign=True), pval(p), dom,
        ]) + " \\\\")

    head = ("\\toprule\n"
            "& & \\multicolumn{1}{c}{Artigo} & \\multicolumn{3}{c}{Reimplementação} "
            "& & \\multicolumn{2}{c}{Wilcoxon} \\\\\n"
            "\\cmidrule(lr){3-3}\\cmidrule(lr){4-6}\\cmidrule(lr){8-9}\n"
            + " & ".join(f"\\multicolumn{{1}}{{l}}{{{h}}}" for h in   # left headers over right-aligned values
                         ["Instância", "Tempo (s)", "Média", "Melhor", "Média", "Desvio",
                          "Gap (\\%)", "$p$", "Domina"]) + " \\\\\n"
            "\\midrule")
    print("% Gerado por scripts/tcc_mdm_wilcoxon_table.py (projeto minimum-latency-problem); não editar à mão.")
    print("\\begin{landscape}")
    print("\\footnotesize")
    print("\\setlength{\\tabcolsep}{4pt}")
    print("\\setlength{\\LTcapwidth}{\\linewidth}")
    print("\\begin{longtable}{lrrrrrrrl}")
    print("\\caption{Teste de Wilcoxon entre o MDM-GILS-RVND reportado por \\cite{santana2019} "
          "e a reimplementação deste trabalho, com o mesmo tempo.}")
    print("\\label{tab:comparacao-mdm-wilcoxon} \\\\")
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
        better, worse = sum(g < 0 for g in gaps), sum(g > 0 for g in gaps)
        print(f"Média & & & & & & {num(mean(gaps), 3, sign=True)} & & \\\\")
        print(f"Domina em & \\multicolumn{{8}}{{l}}{{Artigo: {wins['Artigo']}; "
              f"reimplementação: {wins['Reimpl.']}; sem diferença: {wins['--']}}} \\\\")
        print(f"Todas & \\multicolumn{{8}}{{l}}{{Wilcoxon pareado das médias ({len(gaps)} instâncias; "
              f"reimplementação melhor em {better}, pior em {worse}): "
              f"$p$ = {pval(wilcoxon_p(gaps))}}} \\\\")
    print("\\bottomrule")
    print("\\end{longtable}")
    # below the table, not a \\multicolumn inside it: a wide p{} cell stretches the last column
    print("\\vspace{-1.5ex}{\\scriptsize "
          "Reimplementação: 10 execuções com o tempo médio do artigo na instância. "
          "O artigo publica só a média das suas 10 execuções, então o teste por instância é o de "
          "Wilcoxon de uma amostra (as 10 execuções da reimplementação contra a média do artigo, bilateral, exato); "
          "``Domina'' indica o método melhor quando $p < 0{,}05$. "
          "Gap: média da reimplementação em relação à média do artigo (negativo = reimplementação melhor). "
          "Diferenças de até 0{,}05 contam como empate.\\par}")
    print("\\end{landscape}")


if __name__ == "__main__":
    main()
