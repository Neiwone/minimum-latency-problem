import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection
from matplotlib.widgets import Button
import numpy as np
import argparse
import json
import math
import os


def load_instance(filename, inst_dir="instances"):
    coords, weights = [], []
    section = None
    n = None
    edge_type, edge_format = "EUC_2D", None

    path = filename if os.path.sep in filename else os.path.join(inst_dir, filename)

    with open(path, "r") as f:
        for line in f:
            line = line.strip()

            if not line:
                continue

            if line.startswith("DIMENSION"):
                n = int(line.split(":")[1])

            elif line.startswith("EDGE_WEIGHT_TYPE"):
                edge_type = line.split(":")[1].strip()

            elif line.startswith("EDGE_WEIGHT_FORMAT"):
                edge_format = line.split(":")[1].strip()

            # DISPLAY_DATA only exists to draw the instance -- never to measure it.
            elif line in ("NODE_COORD_SECTION", "DISPLAY_DATA_SECTION"):
                section = "coords"

            elif line == "EDGE_WEIGHT_SECTION":
                section = "weights"

            elif line == "EOF":
                break

            elif section == "coords":
                _, x, y = line.split()[:3]
                coords.append((float(x), float(y)))

            elif section == "weights":
                weights += [int(float(v)) for v in line.split()]

    if n is None:
        raise ValueError(f"{os.path.basename(path)}: no DIMENSION")

    matrix = build_matrix(weights, n, edge_format) if edge_type == "EXPLICIT" else None

    if len(coords) != n:
        if edge_type == "EXPLICIT":
            raise ValueError(
                f"{os.path.basename(path)} is EXPLICIT and carries no "
                "DISPLAY_DATA_SECTION, so it has no coordinates to draw.")
        raise ValueError("Invalid or corrupted instance file")

    return {
        "coords": coords,
        "matrix": matrix,
        "depot": 0,
        "edge_type": edge_type,
        "name": os.path.basename(path),
    }


def build_matrix(weights, n, fmt):
    """Each EDGE_WEIGHT_FORMAT lists a different triangle; read it then mirror."""
    m = [[0] * n for _ in range(n)]
    it = iter(weights)
    for i in range(n):
        try:
            rng = {"FULL_MATRIX":    range(n),
                   "UPPER_ROW":      range(i + 1, n),
                   "UPPER_DIAG_ROW": range(i, n),
                   "LOWER_ROW":      range(i),
                   "LOWER_DIAG_ROW": range(i + 1)}[fmt]
        except KeyError:
            raise ValueError(f"Unsupported EDGE_WEIGHT_FORMAT: {fmt}")
        for j in rng:
            m[i][j] = m[j][i] = next(it)
    return m


def edge_dist(instance):
    """The Evaluator's rounding, so the latency shown matches what the solvers
       report. Takes city indices, because EXPLICIT has no coordinates."""
    etype = instance.get("edge_type", "EUC_2D")
    coords = instance["coords"]
    matrix = instance.get("matrix")

    if matrix is not None:
        return lambda i, j: matrix[i][j]

    def geo_rad(v):
        deg = int(v)
        return 3.141592 * (deg + 5.0 * (v - deg) / 3.0) / 180.0   # TSPLIB's PI

    if etype == "GEO":
        lat = [geo_rad(c[0]) for c in coords]
        lon = [geo_rad(c[1]) for c in coords]

        def geo(i, j):
            if i == j:
                return 0                      # the formula would give 1
            q1 = math.cos(lon[i] - lon[j])
            q2 = math.cos(lat[i] - lat[j])
            q3 = math.cos(lat[i] + lat[j])
            return int(6378.388 * math.acos(0.5 * ((1 + q1) * q2 - (1 - q1) * q3)) + 1.0)
        return geo

    def hypot(i, j):
        a, b = coords[i], coords[j]
        return math.sqrt((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2)

    if etype == "ATT":
        return lambda i, j: int(math.ceil(math.sqrt(
            ((coords[i][0] - coords[j][0]) ** 2
             + (coords[i][1] - coords[j][1]) ** 2) / 10.0)))
    if etype == "CEIL_2D":
        return lambda i, j: int(math.ceil(hypot(i, j)))
    return lambda i, j: int(hypot(i, j))


def arrival_times(instance, route, closed=False):
    """arrival[k] = when the client at route position k is served; the MLP cost
       is their sum. closed=True adds the return to the depot as a final term."""
    d = edge_dist(instance)
    arrival = [0]
    walked = 0
    for k in range(1, len(route)):
        walked += d(route[k - 1], route[k])
        arrival.append(walked)
    if closed and len(route) > 1:
        arrival.append(walked + d(route[-1], route[0]))
    return arrival, sum(arrival)


def load_route(instance, route_arg=None, tour_file=None, from_best=False):
    """A route from --route, from a TSPLIB .tour file, or from the tracked best
       solution of this instance."""
    n = len(instance["coords"])

    if route_arg:
        route = [int(x) for x in route_arg.replace(" ", "").split(",") if x != ""]
    elif tour_file:
        # Two layouts live in instances/solutions/: one node per line (1-based,
        # TSPLIB) and the whole route on one comma-separated line (0-based).
        tokens = []
        reading = False
        for line in open(tour_file):
            line = line.strip()
            if line == "TOUR_SECTION":
                reading = True
            elif reading:
                if line in ("-1", "EOF", ""):
                    break
                tokens += [t for t in line.split(",") if t.strip()]
        route = [int(t) for t in tokens]
        if min(route) == 1 and max(route) == n:
            route = [c - 1 for c in route]
    elif from_best:
        best = json.loads(open("instances/solutions/best_solutions.json").read())
        stem = os.path.splitext(instance["name"])[0]
        if stem not in best:
            raise SystemExit(f"no tracked solution for {stem}")
        return load_route(instance, tour_file=os.path.join(
            "instances", "solutions", best[stem]["tour_file"]))
    else:
        raise SystemExit("give one of --route, --tour or --best")

    if sorted(route) != list(range(n)):
        raise SystemExit(f"route is not a permutation of 0..{n-1}")
    if route[0] != instance["depot"]:
        raise SystemExit("route must start at the depot")
    return route


def plot_instance(instance):
    coords = instance["coords"]
    depot = instance["depot"]

    x = [c[0] for c in coords]
    y = [c[1] for c in coords]

    plt.figure()
    plt.scatter(x, y)

    plt.scatter(
        coords[depot][0],
        coords[depot][1],
        marker="s",
        s=100,
        label="Depot"
    )

    for i, (xi, yi) in enumerate(coords):
        plt.text(xi + 0.5, yi + 0.5, str(i), fontsize=9)

    plt.xlabel("X")
    plt.ylabel("Y")
    plt.title("DMP Instance")
    plt.legend()
    plt.show()


def plot_route(instance, route, verbose=False):
    coords = instance["coords"]
    depot = instance["depot"]

    plt.figure(figsize=(12, 8))

    # Same rounding as the Evaluator, so this matches what the solvers report
    dist_fn = edge_dist(instance)
    total_distance = 0
    cumulative_cost = 0
    edge_distances = []

    for i in range(len(route) - 1):
        a = coords[route[i]]
        b = coords[route[i + 1]]

        dist = dist_fn(route[i], route[i + 1])

        total_distance += dist
        cumulative_cost += total_distance
        edge_distances.append((i, route[i], route[i+1], dist, total_distance, cumulative_cost))
        
        # Plot edge with distance label
        mid_x = (a[0] + b[0]) / 2
        mid_y = (a[1] + b[1]) / 2
        plt.plot([a[0], b[0]], [a[1], b[1]], 'b-', alpha=0.6)
        plt.text(mid_x, mid_y, f"{dist}", fontsize=8, bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))

    x = [c[0] for c in coords]
    y = [c[1] for c in coords]
    plt.scatter(x, y, s=80, zorder=3)

    for i, (xi, yi) in enumerate(coords):
        plt.text(
            xi,
            yi,
            str(i),
            fontsize=8,
            ha="center",
            va="center",
            color="white",
            weight="bold",
            zorder=4
        )


    plt.scatter(
        coords[depot][0],
        coords[depot][1],
        marker="s",
        s=200,
        c='red',
        label="Depot",
        zorder=5
    )

    plt.xlabel("X")
    plt.ylabel("Y")
    plt.title(f"Route Visualization\nTotal Distance: {total_distance}, MLP Cost: {cumulative_cost}")
    plt.legend()
    plt.grid(True, alpha=0.3)
    
    # Print edge details only if verbose
    if verbose:
        print("\n" + "="*80)
        print("ROUTE DETAILS")
        print("="*80)
        print(f"{'Step':<5} {'From':<6} {'To':<6} {'Edge Dist':<12} {'Walked':<12} {'MLP Cost':<12}")
        print("-"*80)
        
        walked = 0
        cost = 0
        for i in range(len(route) - 1):
            dist = dist_fn(route[i], route[i + 1])
            walked += dist
            cost += walked
            print(f"{i:<5} {route[i]:<6} {route[i+1]:<6} {dist:<12} {walked:<12} {cost:<12}")

        print("-"*80)
        print(f"{'TOTAL':<5} {'':<6} {'':<6} {walked:<12} {'':<12} {cost:<12}")
        print("="*80 + "\n")
    
    plt.tight_layout()
    plt.show()

def inspect_instance(instance):
    coords = instance["coords"]
    depot = instance["depot"]

    fig, ax = plt.subplots(figsize=(10, 8))

    x = [c[0] for c in coords]
    y = [c[1] for c in coords]

    ax.scatter(x, y)

    # Highlight depot
    ax.scatter(
        coords[depot][0],
        coords[depot][1],
        marker="s",
        s=150,
        label="Depot"
    )

    for i, (xi, yi) in enumerate(coords):
        ax.text(xi + 0.5, yi + 0.5, str(i), fontsize=9)

    ax.set_title("Click a vertex to inspect edge weights")
    ax.set_xlabel("X")
    ax.set_ylabel("Y")
    ax.legend()
    ax.grid(True, alpha=0.3)

    highlighted_lines = []

    def euclidean(a, b):
        dx = b[0] - a[0]
        dy = b[1] - a[1]
        return (dx*dx + dy*dy) ** 0.5

    def onclick(event):
        if event.inaxes != ax:
            return

        # Find nearest vertex
        click = (event.xdata, event.ydata)

        best_i = None
        best_dist = float("inf")

        for i, c in enumerate(coords):
            d = euclidean(click, c)
            if d < best_dist:
                best_dist = d
                best_i = i

        if best_i is None:
            return

        # Remove previous lines
        for line in highlighted_lines:
            line.remove()
        highlighted_lines.clear()

        v = coords[best_i]

        # Highlight selected vertex
        ax.scatter(v[0], v[1], s=200, marker="o")

        # Draw edges to all vertices
        for j, u in enumerate(coords):
            if j == best_i:
                continue

            dist = euclidean(v, u)

            line, = ax.plot(
                [v[0], u[0]],
                [v[1], u[1]],
                linestyle="--",
                alpha=0.4
            )

            highlighted_lines.append(line)

            mid_x = (v[0] + u[0]) / 2
            mid_y = (v[1] + u[1]) / 2

            txt = ax.text(mid_x, mid_y, f"{dist:.1f}", fontsize=8)
            highlighted_lines.append(txt)

        fig.canvas.draw_idle()

    fig.canvas.mpl_connect("button_press_event", onclick)

    plt.show()



class RouteEditor:
    """Show a route, edit it by clicking, and recompute the latency live.

       Hovering a client shows when it is served; the route is coloured by
       visiting order, which is what makes an MLP solution readable."""

    HELP = ("clique: pegar/soltar   |   m mover  s trocar  r inverter trecho\n"
            "u desfazer   z voltar ao original   w salvar   p imprimir   q sair")

    def __init__(self, instance, route):
        self.inst = instance
        self.coords = instance["coords"]
        self.route = list(route)
        self.original = list(route)
        self.history = []
        self.mode = "m"          # m = mover, s = trocar, r = inverter
        self.picked = None       # first city of a pending edit
        self.closed = False      # count the return to the depot in the latency
        self.dist = edge_dist(instance)

        self.fig, self.ax = plt.subplots(figsize=(12, 9))
        xs = [c[0] for c in self.coords]
        ys = [c[1] for c in self.coords]

        self.edges = LineCollection([], cmap="viridis", linewidths=1.6, alpha=0.85)
        self.ax.add_collection(self.edges)
        self.nodes = self.ax.scatter(xs, ys, s=26, c="#3b3b3b", zorder=3)
        self.mark = self.ax.scatter([], [], s=220, facecolors="none",
                                    edgecolors="crimson", linewidths=2.2, zorder=5)
        d = self.coords[instance["depot"]]
        self.ax.scatter([d[0]], [d[1]], marker="s", s=160, c="crimson",
                        zorder=6, label="depósito")

        self.tip = self.ax.annotate(
            "", xy=(0, 0), xytext=(14, 14), textcoords="offset points",
            bbox=dict(boxstyle="round", fc="lightyellow", ec="0.4"),
            arrowprops=dict(arrowstyle="->"), fontsize=9, zorder=10)
        self.tip.set_visible(False)

        # Hover redraws only the tooltip over a cached background. A full redraw
        # costs ~54 ms at n=532 and ~116 ms at n=1000, which the mouse outruns.
        self.tip.set_animated(True)
        self.mark.set_animated(True)
        self.bg = None

        self.ax.legend(loc="upper right", fontsize=8)
        self.ax.grid(True, alpha=0.2)

        # Its own axes, so its clicks never reach the route-editing handler.
        self.fig.subplots_adjust(bottom=0.12)
        self.button = Button(self.fig.add_axes([0.13, 0.02, 0.26, 0.05]), "")
        self.button.on_clicked(self.toggle_closed)
        self.label_button()

        # Drop matplotlib's own key bindings for this figure: 's' saves a png,
        # 'r' resets the view and 'p' enters pan mode, which would swallow the
        # clicks. 'q' is handled below instead.
        mgr = getattr(self.fig.canvas, "manager", None)
        if mgr is not None and getattr(mgr, "key_press_handler_id", None) is not None:
            self.fig.canvas.mpl_disconnect(mgr.key_press_handler_id)

        self.fig.canvas.mpl_connect("draw_event", self.on_draw)
        self.fig.canvas.mpl_connect("motion_notify_event", self.on_hover)
        self.fig.canvas.mpl_connect("button_press_event", self.on_click)
        self.fig.canvas.mpl_connect("key_press_event", self.on_key)
        self.redraw()

    # ---------------- state ----------------

    def pos_of(self, city):
        return self.route.index(city)

    def push(self):
        self.history.append(list(self.route))
        if len(self.history) > 200:
            self.history.pop(0)

    def apply(self, a, b):
        """Edit joining the two picked cities, per the current mode."""
        pa, pb = self.pos_of(a), self.pos_of(b)
        if pa == 0 or pb == 0:
            print("o depósito não pode ser movido")
            return
        self.push()
        if self.mode == "s":
            self.route[pa], self.route[pb] = self.route[pb], self.route[pa]
        elif self.mode == "r":
            lo, hi = sorted((pa, pb))
            self.route[lo:hi + 1] = reversed(self.route[lo:hi + 1])
        else:
            city = self.route.pop(pa)
            self.route.insert(self.pos_of(b) + 1, city)

    # ---------------- drawing ----------------

    def redraw(self):
        arrival, total = arrival_times(self.inst, self.route, self.closed)
        self.arrival = arrival
        pts = [self.coords[c] for c in self.route]
        if self.closed:
            pts = pts + [pts[0]]
        self.edges.set_segments([[pts[i], pts[i + 1]] for i in range(len(pts) - 1)])
        self.edges.set_array(range(len(pts) - 1))

        base = arrival_times(self.inst, self.original, self.closed)[1]
        delta = total - base
        head = f"{self.inst['name']}   latência = {total:,}".replace(",", " ")
        if delta:
            head += f"   ({delta:+,} vs original)".replace(",", " ")
        modes = {"m": "mover", "s": "trocar", "r": "inverter trecho"}
        picked = f"   [segurando {self.picked}]" if self.picked is not None else ""
        self.ax.set_title(f"{head}\nmodo: {modes[self.mode]}{picked}\n{self.HELP}",
                          fontsize=9, loc="left")
        self.mark.set_offsets(np.array([self.coords[self.picked]]) if self.picked
                              is not None else np.empty((0, 2)))
        self.ax.relim(); self.ax.autoscale_view()
        self.bg = None
        self.fig.canvas.draw_idle()

    def label_button(self):
        self.button.label.set_text(
            "volta ao depósito: SIM" if self.closed else "volta ao depósito: NÃO")

    def toggle_closed(self, _event):
        self.closed = not self.closed
        self.label_button()
        self.redraw()

    # ---------------- events ----------------

    def on_draw(self, _event):
        """Cache everything but the tooltip, so hovering can blit over it."""
        self.bg = self.fig.canvas.copy_from_bbox(self.ax.bbox)
        self.ax.draw_artist(self.mark)
        self.ax.draw_artist(self.tip)

    def blit(self):
        if self.bg is None:
            self.fig.canvas.draw()
            return
        self.fig.canvas.restore_region(self.bg)
        self.ax.draw_artist(self.mark)
        self.ax.draw_artist(self.tip)
        self.fig.canvas.blit(self.ax.bbox)

    def nearest(self, event):
        if event.inaxes != self.ax or event.xdata is None:
            return None
        best, bd = None, float("inf")
        for i, c in enumerate(self.coords):
            d = (c[0] - event.xdata) ** 2 + (c[1] - event.ydata) ** 2
            if d < bd:
                bd, best = d, i
        span = max(self.ax.get_xlim()[1] - self.ax.get_xlim()[0], 1e-9)
        return best if bd ** 0.5 < span * 0.02 else None

    def on_hover(self, event):
        city = self.nearest(event)
        if city is None:
            if self.tip.get_visible():
                self.tip.set_visible(False)
                self.blit()
            return
        k = self.pos_of(city)
        total = self.arrival[-1] and sum(self.arrival)
        share = 100 * self.arrival[k] / sum(self.arrival) if sum(self.arrival) else 0
        self.tip.xy = self.coords[city]
        self.tip.set_text(
            f"cidade {city}\n"
            f"posição {k} de {len(self.route) - 1}\n"
            f"atendida em {self.arrival[k]:,}".replace(",", " ") +
            f"\n{share:.2f}% da latência total")
        self.tip.set_visible(True)
        self.blit()

    def on_click(self, event):
        city = self.nearest(event)
        if city is None:
            return
        if self.picked is None:
            self.picked = city
        elif city == self.picked:
            self.picked = None
        else:
            self.apply(self.picked, city)
            self.picked = None
        self.redraw()

    def on_key(self, event):
        if event.key in ("m", "s", "r"):
            self.mode = event.key
        elif event.key == "u" and self.history:
            self.route = self.history.pop()
        elif event.key == "z":
            self.push()
            self.route = list(self.original)
        elif event.key == "p":
            print(",".join(map(str, self.route)))
        elif event.key == "w":
            self.save()
        elif event.key == "q":
            plt.close(self.fig)
            return
        else:
            return
        self.picked = None
        self.redraw()

    def save(self):
        stem = os.path.splitext(self.inst["name"])[0]
        out = f"{stem}_edited.tour"
        total = arrival_times(self.inst, self.route, self.closed)[1]
        kind = "closed tour" if self.closed else "open path"
        with open(out, "w") as f:
            f.write(f"NAME : {out}\n")
            f.write(f"COMMENT : MLP solution (cost={total}, {kind}, edited by hand)\n")
            f.write("TYPE : TOUR\n")
            f.write(f"DIMENSION : {len(self.route)}\n")
            f.write("TOUR_SECTION\n")
            for c in self.route:
                f.write(f"{c + 1}\n")
            f.write("-1\nEOF\n")
        print(f"gravado em {out}  (latência {total}, {kind})")


def edit_route(instance, route):
    # The canvas keeps only a WEAK reference to the callbacks, so the editor has
    # to stay referenced or the garbage collector silently kills every handler.
    editor = RouteEditor(instance, route)
    plt.show()
    return editor


def parse_args():
    parser = argparse.ArgumentParser(
        description="DMP / TSP instance visualizer"
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    pi = subparsers.add_parser("plot-instance", help="Plot instance nodes")
    pi.add_argument("file", type=str, help=".tsp file")

    pr = subparsers.add_parser("plot-route", help="Plot a route")
    pr.add_argument("file", type=str, help=".tsp file")
    pr.add_argument(
        "--route",
        type=str,
        required=True,
        help="Route as comma-separated list, e.g. 0,3,2,5,0"
    )
    pr.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Print detailed route information (edge distances, cumulative costs)"
    )

    inspect = subparsers.add_parser(
        "inspect-instance",
        help="Click vertices and inspect all edge weights"
    )
    inspect.add_argument("file", type=str, help=".tsp file")

    ed = subparsers.add_parser(
        "edit-route",
        help="View a solution, edit it by clicking, and see the latency update"
    )
    ed.add_argument("file", type=str, help=".tsp file")
    ed.add_argument("--route", type=str, help="route as a comma-separated list")
    ed.add_argument("--tour", type=str, help="TSPLIB .tour file")
    ed.add_argument("--best", action="store_true",
                    help="load the tracked best solution for this instance")

    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()

    if args.command == "plot-instance":
        instance = load_instance(args.file)
        plot_instance(instance)

    elif args.command == "plot-route":
        instance = load_instance(args.file)
        route = list(map(int, args.route.split(",")))
        plot_route(instance, route, verbose=args.verbose)
        
    elif args.command == "inspect-instance":
        instance = load_instance(args.file)
        inspect_instance(instance)

    elif args.command == "edit-route":
        instance = load_instance(args.file)
        route = load_route(instance, args.route, args.tour, args.best)
        edit_route(instance, route)
