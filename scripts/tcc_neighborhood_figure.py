"""TikZ figure for the TCC: one panel per neighborhood, the route before and after
the move (rows s and s'). Arcs that leave the route are dashed red in s, arcs
that enter it are thick blue in s', and the customers the move acts on are shaded.
The diff is computed from the two sequences, so the drawing cannot disagree with
the move.

    python3 scripts/tcc_neighborhood_figure.py > ../tcc/Figuras/vizinhancas.tex
"""
BEFORE = list(range(8))
MOVES = [  # (label, route after the move, customers the move acts on)
    (r"\textit{Swap}: troca os clientes 2 e 5", [0, 1, 5, 3, 4, 2, 6, 7], {2, 5}),
    (r"2-opt: inverte o trecho de 2 a 5", [0, 1, 5, 4, 3, 2, 6, 7], {2, 3, 4, 5}),
    (r"Reinserção: move o cliente 2 para depois do 5", [0, 1, 3, 4, 5, 2, 6, 7], {2}),
    (r"Or-opt-2: move o bloco (2, 3) para depois do 5", [0, 1, 4, 5, 2, 3, 6, 7], {2, 3}),
]
DX, ROW, PANEL = 1.15, 1.0, 2.9  # node spacing, before/after gap, panel height (cm)


def arcs(route):
    return {frozenset(p) for p in zip(route, route[1:])}


def row(route, y, name, other, style, moved):
    out = []
    for k, v in enumerate(route):
        shape = "dep" if v == 0 else ("mov" if v in moved else "cli")
        out.append(rf"  \node[{shape}] ({name}{k}) at ({k * DX:.2f},{-y:.2f}) {{{v}}};")
    for k, (a, b) in enumerate(zip(route, route[1:])):
        changed = frozenset((a, b)) not in other
        out.append(rf"  \draw[{style if changed else 'arc'}] ({name}{k}) -- ({name}{k + 1});")
    return out


out = [r"% gerado por scripts/tcc_neighborhood_figure.py (minimum-latency-problem); não editar à mão",
       r"\begin{tikzpicture}[",
       r"  cli/.style={circle, draw, minimum size=6mm, inner sep=0pt, font=\small},",
       r"  dep/.style={rectangle, draw, minimum size=6mm, inner sep=0pt, font=\small, fill=gray!20},",
       r"  mov/.style={circle, draw, minimum size=6mm, inner sep=0pt, font=\small, fill=blue!15},",
       r"  arc/.style={->, >=latex, gray!70},",
       r"  arcout/.style={->, >=latex, red!75!black, dashed, thick},",
       r"  arcin/.style={->, >=latex, blue!70!black, very thick},",
       r"]"]
for p, (label, after, moved) in enumerate(MOVES):
    assert sorted(after) == BEFORE and after[0] == 0
    y0 = p * PANEL
    out.append(rf"  \node[anchor=west, font=\small] at ({-0.3:.2f},{-y0 + 0.65:.2f}) {{({'abcd'[p]}) {label}}};")
    out.append(rf"  \node[anchor=east, font=\footnotesize] at ({-0.45:.2f},{-y0:.2f}) {{$s$}};")
    out.append(rf"  \node[anchor=east, font=\footnotesize] at ({-0.45:.2f},{-y0 - ROW:.2f}) {{$s'$}};")
    out += row(BEFORE, y0, f"b{p}n", arcs(after), "arcout", moved)
    out += row(after, y0 + ROW, f"a{p}n", arcs(BEFORE), "arcin", moved)
out.append(r"\end{tikzpicture}")
print("\n".join(out))
