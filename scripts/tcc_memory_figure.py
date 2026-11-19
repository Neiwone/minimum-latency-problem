"""TikZ figure for the TCC (adaptive memory): two elite solutions with the arcs
they share, and a new solution under construction that follows those arcs.
Arcs are directed, as in gils_am_rvnd's EdgeFreq. Panel (c) shows the partial
route, the last inserted vertex r, and the common arcs not yet in the route.

    python3 scripts/tcc_memory_figure.py > ../tcc/Figuras/memoria_adaptativa.tex
"""
import math

PTS = {0: (0, 0), 1: (-0.2, 1.5), 2: (1.4, 1.6), 3: (2.4, 0.4), 4: (1.9, -1.1),
       5: (0.5, -1.7), 6: (-1.0, -1.0), 7: (-1.6, 0.3)}
ELITE = [(0, 1, 2, 3, 4, 5, 6, 7), (0, 1, 2, 3, 5, 4, 6, 7)]
PARTIAL = (0, 1, 2)  # route built so far; r = last vertex
SCALE, OFFSET = 0.95, 5.0


def arcs(tour):
    return set(zip(tour, tour[1:] + tour[:1]))


common = arcs(ELITE[0]) & arcs(ELITE[1])
built = set(zip(PARTIAL, PARTIAL[1:]))
assert built <= common  # the partial route follows the memory


def seg_dist(p, a, b):
    (px, py), (ax, ay), (bx, by) = p, a, b
    t = max(0, min(1, ((px - ax) * (bx - ax) + (py - ay) * (by - ay)) / ((bx - ax) ** 2 + (by - ay) ** 2)))
    return math.hypot(px - ax - t * (bx - ax), py - ay - t * (by - ay))


for a, b in arcs(ELITE[0]) | arcs(ELITE[1]):  # no arc grazes a vertex it does not touch
    assert all(seg_dist(PTS[v], PTS[a], PTS[b]) > 0.5 for v in PTS if v not in (a, b)), (a, b)

out = [r"% gerado por scripts/tcc_memory_figure.py (minimum-latency-problem); não editar à mão",
       r"\begin{tikzpicture}[",
       r"  v/.style={draw, circle, minimum size=6mm, inner sep=0pt, font=\small},",
       r"  dep/.style={draw, rectangle, minimum size=6mm, inner sep=0pt, font=\small, fill=gray!20},",
       r"  arc/.style={->, >=latex, gray!70},",
       r"  com/.style={->, >=latex, blue!70!black, very thick},",
       r"  built/.style={->, >=latex, very thick},",
       r"  hint/.style={->, >=latex, blue!70!black, thick, dashed},",
       r"]"]
panels = [(r"(a) solução elite $s_1$", ELITE[0]), (r"(b) solução elite $s_2$", ELITE[1]),
          (r"(c) nova solução em construção", None)]
r = PARTIAL[-1]
for p, (label, tour) in enumerate(panels):
    ox = p * OFFSET
    for v, (x, y) in PTS.items():
        style = "dep" if v == 0 else ("v, fill=blue!15" if tour is None and v == r else "v")
        out.append(rf"  \node[{style}] (p{p}n{v}) at ({ox + x * SCALE:.2f},{y * SCALE:.2f}) {{{v}}};")
    if tour is None:
        draw = [(a, b, "built") for a, b in sorted(built)] + \
               [(a, b, "hint") for a, b in sorted(common - built) if a not in PARTIAL[:-1]]
        out.append(rf"  \node[font=\footnotesize, anchor=south west, inner sep=0.5pt] at (p{p}n{r}.north east) {{$r$}};")
    else:
        draw = [(a, b, "com" if (a, b) in common else "arc") for a, b in sorted(arcs(tour))]
    for a, b, style in draw:
        out.append(rf"  \draw[{style}] (p{p}n{a}) -- (p{p}n{b});")
    out.append(rf"  \node[font=\small] at ({ox + 0.4 * SCALE:.2f},{-2.5 * SCALE:.2f}) {{{label}}};")
out.append(r"\end{tikzpicture}")
print("\n".join(out))
