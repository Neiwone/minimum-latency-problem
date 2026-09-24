#!/usr/bin/env python3
"""
Draw the claim the don't-look bits rest on, on one small instance.

Reordering a window of the tour changes every arrival time after it -- and
changes nothing about how much a move somewhere else is worth. The figure shows
both facts at once, plus the boundary case where the claim stops holding.

    python3 scripts/plot_dlb_theorem.py [--out docs/img/dlb-theorem.png]
"""
import argparse
import math
import random

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

W_COLOR, M_COLOR = "#d62728", "#1f77b4"


def dist(a, b):
    return int(math.sqrt((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2))


def arrivals(tour, pts):
    out, walked = [0], 0
    for i in range(1, len(tour)):
        walked += dist(pts[tour[i - 1]], pts[tour[i]])
        out.append(walked)
    return out


def cost(tour, pts):
    return sum(arrivals(tour, pts))


def draw_map(ax, tour, pts, win, mov, title):
    xs = [pts[c][0] for c in tour]
    ys = [pts[c][1] for c in tour]
    ax.plot(xs, ys, "-", color="0.7", lw=1.4, zorder=1)
    for lo, hi, col in [(win[0], win[1], W_COLOR), (mov[0], mov[1], M_COLOR)]:
        ax.plot(xs[lo:hi + 1], ys[lo:hi + 1], "-", color=col, lw=3.2, zorder=2)
    ax.scatter(xs, ys, s=70, c="white", edgecolors="0.35", zorder=3)
    for k, c in enumerate(tour):
        ax.text(xs[k], ys[k], str(k), ha="center", va="center", fontsize=7, zorder=4)
    ax.scatter([xs[0]], [ys[0]], marker="s", s=120, c="black", zorder=5)
    ax.set_title(title, fontsize=10)
    ax.set_xticks([]); ax.set_yticks([])


def delay_curve(ax, pts, tour, mov, label, color, style):
    """How much later each client is served once the move is applied."""
    moved = tour[:]
    moved[mov[0]:mov[1] + 1] = list(reversed(moved[mov[0]:mov[1] + 1]))
    a0, a1 = arrivals(tour, pts), arrivals(moved, pts)
    d = [x - y for x, y in zip(a1, a0)]
    ax.step(range(len(d)), d, style, color=color, lw=2, where="mid", label=label)
    return sum(d)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="docs/img/dlb-theorem.png")
    ap.add_argument("--seed", type=int, default=11)
    args = ap.parse_args()

    rng = random.Random(args.seed)
    n = 16
    pts = [(rng.uniform(0, 100), rng.uniform(0, 100)) for _ in range(n)]
    tour = [0] + rng.sample(range(1, n), n - 1)

    win = (4, 6)          # a janela reordenada
    mov = (10, 13)        # o movimento, longe dela
    edge = (win[1] + 1, win[1] + 4)   # o caso de fronteira: encosta na janela

    shuffled = tour[:]
    blk = shuffled[win[0]:win[1] + 1]
    rng.shuffle(blk)
    shuffled[win[0]:win[1] + 1] = blk

    fig = plt.figure(figsize=(13, 10.5))
    gs = fig.add_gridspec(3, 2, height_ratios=[1.25, 1, 1], hspace=0.42, wspace=0.12)

    draw_map(fig.add_subplot(gs[0, 0]), tour, pts, win, mov,
             f"rota original — custo {cost(tour, pts)}")
    draw_map(fig.add_subplot(gs[0, 1]), shuffled, pts, win, mov,
             f"mesma rota, janela reordenada — custo {cost(shuffled, pts)}")

    ax = fig.add_subplot(gs[1, :])
    g1 = delay_curve(ax, pts, tour, mov, "na rota original", "#2ca02c", "-")
    g2 = delay_curve(ax, pts, shuffled, mov, "na rota com a janela reordenada",
                     "#ff7f0e", "--")
    ax.axvspan(win[0] - 0.5, win[1] + 0.5, color=W_COLOR, alpha=0.12)
    ax.axvspan(mov[0] - 0.5, mov[1] + 0.5, color=M_COLOR, alpha=0.12)
    ax.set_title(f"movimento LONGE da janela: as duas curvas coincidem — "
                 f"ganho {g1:+d} nos dois casos", fontsize=11, color="#2ca02c")
    ax.set_ylabel("quanto cada cliente\natrasa com o movimento")
    ax.legend(fontsize=9, loc="upper left"); ax.grid(alpha=0.25)

    ax = fig.add_subplot(gs[2, :])
    g3 = delay_curve(ax, pts, tour, edge, "na rota original", "#2ca02c", "-")
    g4 = delay_curve(ax, pts, shuffled, edge, "na rota com a janela reordenada",
                     "#ff7f0e", "--")
    ax.axvspan(win[0] - 0.5, win[1] + 0.5, color=W_COLOR, alpha=0.12)
    ax.axvspan(edge[0] - 0.5, edge[1] + 0.5, color=M_COLOR, alpha=0.12)
    ax.set_title(f"movimento ENCOSTANDO na janela: as curvas se separam — "
                 f"ganho {g3:+d} contra {g4:+d}", fontsize=11, color="#d62728")
    ax.set_xlabel("posição do cliente na rota")
    ax.set_ylabel("quanto cada cliente\natrasa com o movimento")
    ax.legend(fontsize=9, loc="upper left"); ax.grid(alpha=0.25)

    fig.suptitle("Reordenar a janela vermelha muda todos os tempos de chegada depois dela.\n"
                 "O quanto o movimento azul vale não muda — a menos que ele encoste na janela.",
                 fontsize=13, y=0.975)

    import os
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    fig.savefig(args.out, dpi=130, bbox_inches="tight")
    print(f"figura em {args.out}")
    print(f"  longe    : ganho {g1:+d} e {g2:+d}   {'iguais' if g1 == g2 else 'DIFERENTES'}")
    print(f"  encostado: ganho {g3:+d} e {g4:+d}   {'iguais' if g3 == g4 else 'diferentes'}")


if __name__ == "__main__":
    main()
