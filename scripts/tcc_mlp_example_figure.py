"""TikZ figure for the TCC (formal definition of the MLP): two solutions of a
4-customer instance, with the travel time on each arc and the latency next to
each customer. s1 has the shorter total time (it is TSP-optimal) but the larger
total latency, so the figure also shows that the two objectives disagree.
Times are the rounded Euclidean distances of the drawn coordinates; the
latencies and totals are computed here, as in eq. (eq:mlp) with the return arc.

    python3 scripts/tcc_mlp_example_figure.py > ../tcc/Figuras/exemplo_mlp.tex
"""
import itertools
import math

PTS = {0: (0, 0), 1: (1, 2), 2: (-1, 3), 3: (-5, -1), 4: (5, -3)}
SCALE = 0.65  # cm per unit
SOLUTIONS = [("s_1", (0, 3, 2, 1, 4)), ("s_2", (0, 1, 2, 3, 4))]


def t(a, b):
    return round(math.dist(PTS[a], PTS[b]))


def evaluate(route):
    """(total time, latency of each visited vertex incl. the return, f)"""
    acc, lat = 0, []
    for a, b in zip(route, route[1:] + (0,)):
        acc += t(a, b)
        lat.append(acc)
    return acc, lat, sum(lat)


tours = [(0,) + p for p in itertools.permutations(range(1, 5))]
assert min(evaluate(r)[0] for r in tours) == evaluate(SOLUTIONS[0][1])[0]  # s1 is TSP-optimal
assert min(evaluate(r)[2] for r in tours) == evaluate(SOLUTIONS[1][1])[2]  # s2 is MLP-optimal

out = [r"% gerado por scripts/tcc_mlp_example_figure.py (minimum-latency-problem); não editar à mão",
       r"\begin{tikzpicture}[",
       r"  cli/.style={circle, draw, minimum size=6mm, inner sep=0pt, font=\small},",
       r"  dep/.style={rectangle, draw, minimum size=6mm, inner sep=0pt, font=\small, fill=gray!20},",
       r"  arc/.style={->, >=latex, thick},",
       r"  ret/.style={->, >=latex, thick, dashed},",
       r"  tt/.style={font=\scriptsize, fill=white, inner sep=1pt},",
       r"  lat/.style={font=\scriptsize, text=blue!70!black},",
       r"]"]
for p, (name, route) in enumerate(SOLUTIONS):
    total, lat, f = evaluate(route)
    ox = p * 7.6
    tag = 'ab'[p]  # tikz node prefix
    pos = {v: (ox + x * SCALE, y * SCALE) for v, (x, y) in PTS.items()}
    for v, (x, y) in pos.items():
        out.append(rf"  \node[{'dep' if v == 0 else 'cli'}] (n{tag}{v}) at ({x:.2f},{y:.2f}) {{{v}}};")
    for k, (a, b) in enumerate(zip(route, route[1:] + (0,))):
        style = "ret" if b == 0 else "arc"
        out.append(rf"  \draw[{style}] (n{tag}{a}) -- node[tt] {{{t(a, b)}}} (n{tag}{b});")
    for v, l in zip(route[1:], lat):
        x, y = PTS[v]
        ang = round(math.degrees(math.atan2(y, x)))  # label on the side away from the depot
        out.append(rf"  \node[lat, anchor={ang + 180}, inner sep=1pt] at (n{tag}{v}.{ang}) {{$\ell={l}$}};")
    out.append(rf"  \node[font=\small, align=center, anchor=north] at ({ox:.2f},{-3 * SCALE - 0.6:.2f}) "
               rf"{{({tag}) ${name} = ({', '.join(map(str, route))}, 0)$\\"
               rf"tempo total ${total}$\\ $f({name}) = {' + '.join(map(str, lat))} = {f}$}};")
out.append(r"\end{tikzpicture}")
print("\n".join(out))
