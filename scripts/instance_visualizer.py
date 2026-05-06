import matplotlib.pyplot as plt
import argparse
import os


def load_instance(filename, inst_dir="instances"):
    coords = []
    reading_coords = False
    n = None

    path = os.path.join(inst_dir, filename)

    with open(path, "r") as f:
        for line in f:
            line = line.strip()

            if not line:
                continue

            if line.startswith("DIMENSION"):
                n = int(line.split(":")[1])

            elif line == "NODE_COORD_SECTION":
                reading_coords = True

            elif line == "EOF":
                break

            elif reading_coords:
                _, x, y = line.split()
                coords.append((float(x), float(y)))

    if n is None or len(coords) != n:
        raise ValueError("Invalid or corrupted instance file")

    return {
        "coords": coords,
        "depot": 0
    }


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

    # Calculate distances and cumulative cost (MLP style)
    total_distance = 0.0
    cumulative_cost = 0.0
    edge_distances = []
    
    for i in range(len(route) - 1):
        a = coords[route[i]]
        b = coords[route[i + 1]]
        
        # Euclidean distance
        dx = b[0] - a[0]
        dy = b[1] - a[1]
        dist = (dx*dx + dy*dy) ** 0.5
        
        total_distance += dist
        cumulative_cost += total_distance
        edge_distances.append((i, route[i], route[i+1], dist, total_distance, cumulative_cost))
        
        # Plot edge with distance label
        mid_x = (a[0] + b[0]) / 2
        mid_y = (a[1] + b[1]) / 2
        plt.plot([a[0], b[0]], [a[1], b[1]], 'b-', alpha=0.6)
        plt.text(mid_x, mid_y, f"{dist:.1f}", fontsize=8, bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))

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
    plt.title(f"Route Visualization\nTotal Distance: {total_distance:.2f}, MLP Cost: {cumulative_cost:.2f}")
    plt.legend()
    plt.grid(True, alpha=0.3)
    
    # Print edge details only if verbose
    if verbose:
        print("\n" + "="*80)
        print("ROUTE DETAILS")
        print("="*80)
        print(f"{'Step':<5} {'From':<6} {'To':<6} {'Edge Dist':<12} {'Walked':<12} {'MLP Cost':<12}")
        print("-"*80)
        
        walked = 0.0
        cost = 0.0
        for i in range(len(route) - 1):
            a = coords[route[i]]
            b = coords[route[i + 1]]
            dx = b[0] - a[0]
            dy = b[1] - a[1]
            dist = (dx*dx + dy*dy) ** 0.5
            walked += dist
            cost += walked
            print(f"{i:<5} {route[i]:<6} {route[i+1]:<6} {dist:<12.2f} {walked:<12.2f} {cost:<12.2f}")
        
        print("-"*80)
        print(f"{'TOTAL':<5} {'':<6} {'':<6} {walked:<12.2f} {'':<12} {cost:<12.2f}")
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
