#!/usr/bin/env python3
"""
LaTeX table for the TCC: the proposal against the published MDM-GILS-RVND,
laid out like Table 1 of Santana, Plastino & Rosseti (2019): proven optimum,
best / average / time of MDM-GILS-RVND, then best / average / gap / time of
the proposal, gap = proposal average against the MDM average.

Our numbers come from the literature_compare checkpoints, all with the MDM
time: n < 500 from the circuit suite (min(100 s, MDM time)), n >= 500 from
circuit-long (min(1000 s, MDM time)), and the instances where those caps bind
from scripts/run_circuit_paper_time.sh (MDM time, no cap). 10 runs each; a
circuit-long instance with only 5 so far is marked. Instances without an
uncapped run (n >= 1000) are left out. The optimum is the one proven by
Bulhoes et al. (2018) and marked alpha in the paper; the other instances have none.

    PYTHONPATH=scripts python3 scripts/tcc_mdm_table.py > ../tcc/Tabelas/comparacao_mdm_paper.tex
"""
import json
from pathlib import Path
from statistics import mean

from literature_compare import n_of, rel, wtl
from mdm_paper_compare import PAPER

OPTIMAL = list(PAPER)[:list(PAPER).index("rat195") + 1]   # alpha in Table 1


def load(path, runs):
    if not Path(path).exists():   # a batch that has not started yet
        return {}
    data = json.loads(Path(path).read_text())["runs"]
    out = {}
    for key, rec in data.items():
        inst, seed = key.split("|")
        if int(seed) <= runs:
            out.setdefault(inst, []).append(rec)
    return {i: r for i, r in out.items() if len(r) == runs}


def num(x, dec=0, bold=False, sign=False):
    """Brazilian style: thin-space thousands, decimal comma."""
    if round(x, dec) == 0:
        x, sign = 0.0, False   # no "-0,00" nor "+0,00"
    s = f"{x:{'+' if sign else ''},.{dec}f}".replace(",", " ").replace(".", "{,}").replace(" ", "\\,")
    return f"\\textbf{{{s}}}" if bold else s


def main():
    short = load("results/literature/circuit.json", 10)
    long10 = load("results/literature/circuit_long.json", 10)
    long5 = load("results/literature/circuit_long.json", 5)
    uncapped = load("results/literature/circuit_paper_time.json", 10)
    rows, gaps = [], []
    better = {"best": [0, 0], "avg": [0, 0]}
    for inst, (_, _, _, _, mb, ma, mt) in PAPER.items():
        big = n_of(inst) >= 500
        five = False
        if mt > (1000 if big else 100):   # capped there: not the MDM time
            if inst not in uncapped:
                continue
            recs = uncapped[inst]
        elif big:
            five = inst not in long10
            recs = long5[inst] if five else long10[inst]
        else:
            recs = short[inst]
        costs = [float(r["cost"]) for r in recs]
        ob, oa = min(costs), mean(costs)
        ot = mean(float(r["time_ms"]) for r in recs) / 1000
        assert abs(ot - mt) < 0.1, (inst, ot, mt)   # one time column: both ran the MDM time
        bw, _, bl = wtl([(ob, mb)])
        aw, _, al = wtl([(oa, ma)])
        better["best"][0] += bw
        better["best"][1] += bl
        better["avg"][0] += aw
        better["avg"][1] += al
        gaps.append(rel(oa, ma))
        name = "dsj1000ceil" if inst == "dsj1000" else inst   # PAPER keeps the CEIL_2D row
        rows.append(" & ".join([
            name + ("$^\\ddagger$" if five else ""), num(PAPER[inst][0]) if inst in OPTIMAL else "--",
            num(mt, 2), num(mb, bold=bl), num(ma, 1, bold=al),
            num(ob, bold=bw), num(oa, 1, bold=aw), num(gaps[-1], 3, sign=True),
        ]) + " \\\\")

    head = ("Instância & Ótimo & Tempo (s) & Melhor & Média "
            "& Melhor & Média & Gap (\\%) \\\\")
    cols = ("\\multicolumn{3}{c}{} & \\multicolumn{2}{c}{MDM-GILS-RVND} "
            "& \\multicolumn{3}{c}{Proposta} \\\\\n"
            "\\cmidrule(lr){4-5}\\cmidrule(lr){6-8}")
    print("% Gerado por scripts/tcc_mdm_table.py (projeto minimum-latency-problem); não editar à mão.")
    print("\\begingroup")   # keeps \footnotesize and \tabcolsep from leaking into the text after
    print("\\footnotesize")
    print("\\setlength{\\tabcolsep}{4pt}")
    print("\\setlength{\\LTcapwidth}{\\linewidth}")
    print("\\begin{longtable}{lrrrrrrr}")
    print("\\caption{Proposta contra o MDM-GILS-RVND publicado nas instâncias TSPLIB "
          "de \\cite{santana2019}.}\\label{tab:comparacao-mdm-paper} \\\\")
    for part in ("\\toprule", cols, head, "\\midrule"):
        print(part)
    print("\\endfirsthead")
    print("\\multicolumn{8}{l}{\\textit{(continuação)}} \\\\")
    for part in ("\\toprule", cols, head, "\\midrule"):
        print(part)
    print("\\endhead")
    print("\\midrule\\multicolumn{8}{r}{\\textit{(continua)}} \\\\")
    print("\\endfoot")
    print("\\endlastfoot")
    print("\n".join(rows))
    print("\\midrule")
    print(f"Média & & & & & & & {num(mean(gaps), 3, sign=True)} \\\\")
    print(f"Melhor em & & & {better['best'][1]} & {better['avg'][1]} "
          f"& {better['best'][0]} & {better['avg'][0]} & \\\\")
    print("\\bottomrule")
    print("\\end{longtable}")
    print("\\endgroup")


if __name__ == "__main__":
    main()
