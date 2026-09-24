"""HISTORICO -- nao e mais chamado em runtime.

A mineracao do mdm_gils_rvnd passou a rodar em memoria via a lib C++
FPmax-LIB (external/fpmax/, ver docs/hypotheses/h13-mdm-gils-rvnd.md
secao 2.2). Este script fica no repo como registro da versao anterior e
para reproduzir a checagem de equivalencia entre as duas implementacoes.


Real FPMax* maximal frequent itemset mining, called by src/mdm_gils_rvnd.cpp
as a subprocess (mining happens only a handful of times per run -- whenever
the elite set changes during phase 2 -- so subprocess overhead is
negligible against total runtime). See docs/hypotheses/h13-mdm-gils-rvnd.md.

Input: one line per elite tour, arcs as whitespace-separated "u_v" tokens.
Output: one line per mined maximal frequent itemset, arcs as
whitespace-separated "u_v" tokens (empty file if none found).

Usage: uv run --with mlxtend --with pandas python3 scripts/fpmax_mine.py <in> <sup_min> <out>
"""
import sys

from mlxtend.frequent_patterns import fpmax
from mlxtend.preprocessing import TransactionEncoder
import pandas as pd


def main():
    input_path, sup_min_str, output_path = sys.argv[1], sys.argv[2], sys.argv[3]
    sup_min = float(sup_min_str)

    transactions = []
    with open(input_path) as f:
        for line in f:
            arcs = line.split()
            if arcs:
                transactions.append(arcs)

    if not transactions:
        open(output_path, "w").close()
        return

    te = TransactionEncoder()
    te_ary = te.fit(transactions).transform(transactions)
    df = pd.DataFrame(te_ary, columns=te.columns_)

    result = fpmax(df, min_support=sup_min, use_colnames=True)

    with open(output_path, "w") as f:
        for itemset in result["itemsets"]:
            f.write(" ".join(itemset) + "\n")


if __name__ == "__main__":
    main()
