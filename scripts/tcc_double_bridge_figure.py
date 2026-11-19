"""TikZ figure for the TCC (GILS-RVND perturbation): the double-bridge on an
8-vertex circuit. Top: the circuit before (s) and after (s'), vertices on the
same positions, the two swapped segments (B, C) shaded, removed arcs dashed red, inserted arcs
(the "bridges") thick blue. Bottom: the two sequences with framed segments.
Removed/inserted arcs come from the arc diff of the two tours.

    python3 scripts/tcc_double_bridge_figure.py > ../tcc/Figuras/double_bridge.tex
"""
import math

N = 8
SEGS = [("A", [0, 1]), ("B", [2, 3]), ("C", [4, 5]), ("D", [6, 7])]
MOVED = {"B", "C"}
ORDER_AFTER = "ACBD"
R, CX = 2.0, (2.6, 9.0)          # circle radius, centres of the two circles (cm)
DX, Y_S, Y_S2 = 1.15, -4.3, -5.9  # spacing and rows of the linear sequences

seg_of = {v: name for name, vs in SEGS for v in vs}
before = [v for _, vs in SEGS for v in vs]
after = [v for name in ORDER_AFTER for s, vs in SEGS if s == name for v in vs]
assert sorted(after) == before and after[0] == 0


def arcs(tour):  # circuit arcs, including the return to the depot
    return {(a, b) for a, b in zip(tour, tour[1:] + tour[:1])}


A0, A1 = arcs(before), arcs(after)
removed, inserted = A0 - A1, A1 - A0
assert len(removed) == len(inserted) == 3


def node(name, v, x, y):
    shape = "rectangle, fill=gray!20" if v == 0 else "circle" + (", fill=blue!15" if seg_of[v] in MOVED else "")
    return rf"  \node[v, {shape}] ({name}) at ({x:.2f},{y:.2f}) {{{v}}};"


out = [r"% gerado por scripts/tcc_double_bridge_figure.py (minimum-latency-problem); não editar à mão",
       r"\begin{tikzpicture}[",
       r"  v/.style={draw, minimum size=6mm, inner sep=0pt, font=\small},",
       r"  arc/.style={->, >=latex, gray!70},",
       r"  arcout/.style={->, >=latex, red!75!black, dashed, thick},",
       r"  arcin/.style={->, >=latex, blue!70!black, very thick},",
       r"  seg/.style={font=\small},",
       r"]"]

# circuits
for p, (tour, label, style, changed) in enumerate([(before, "$s$", "arcout", removed),
                                                    (after, "$s'$", "arcin", inserted)]):
    cx = CX[p]
    pos = {}
    for k, v in enumerate(before):  # same positions in both panels
        ang = math.radians(90 - k * 360 / N)
        pos[v] = (cx + R * math.cos(ang), R * math.sin(ang))
        out.append(node(f"c{p}n{v}", v, *pos[v]))
    for name, vs in SEGS:
        k = before.index(vs[0]) + 0.5  # between the segment's two vertices
        ang = math.radians(90 - k * 360 / N)
        out.append(rf"  \node[seg] at ({cx + (R + 0.75) * math.cos(ang):.2f},"
                   rf"{(R + 0.75) * math.sin(ang):.2f}) {{${name}$}};")
    for a, b in sorted(arcs(tour)):
        out.append(rf"  \draw[{style if (a, b) in changed else 'arc'}] (c{p}n{a}) -- (c{p}n{b});")
    out.append(rf"  \node[font=\small] at ({cx:.2f},{-R - 0.9:.2f}) {{{label}}};")

# sequences
for p, (tour, label, y, other, style) in enumerate([(before, "$s$", Y_S, A1, "arcout"),
                                                     (after, "$s'$", Y_S2, A0, "arcin")]):
    x0 = 1.9
    out.append(rf"  \node[anchor=east, font=\small] at ({x0 - 0.5:.2f},{y:.2f}) {{{label}}};")
    k = 0
    for name in (ORDER_AFTER if p else "ABCD"):
        vs = next(vs for s, vs in SEGS if s == name)
        xa, xb = x0 + k * DX, x0 + (k + len(vs) - 1) * DX
        out.append(rf"  \draw[gray!60, rounded corners=3pt] ({xa - 0.42:.2f},{y - 0.42:.2f}) "
                   rf"rectangle ({xb + 0.42:.2f},{y + 0.42:.2f});")
        out.append(rf"  \node[seg] at ({(xa + xb) / 2:.2f},{y + 0.65:.2f}) {{${name}$}};")
        k += len(vs)
    for k, v in enumerate(tour):
        out.append(node(f"l{p}n{k}", v, x0 + k * DX, y))
    for k, (a, b) in enumerate(zip(tour, tour[1:])):
        out.append(rf"  \draw[{style if (a, b) not in other else 'arc'}] (l{p}n{k}) -- (l{p}n{k + 1});")
out.append(r"\end{tikzpicture}")
print("\n".join(out))
