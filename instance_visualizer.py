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


def plot_route(instance, route):
    coords = instance["coords"]
    depot = instance["depot"]

    plt.figure()

    for i in range(len(route) - 1):
        a = coords[route[i]]
        b = coords[route[i + 1]]
        plt.plot([a[0], b[0]], [a[1], b[1]])

    x = [c[0] for c in coords]
    y = [c[1] for c in coords]
    plt.scatter(x, y)

    plt.scatter(
        coords[depot][0],
        coords[depot][1],
        marker="s",
        s=100,
        label="Depot"
    )

    plt.xlabel("X")
    plt.ylabel("Y")
    plt.title("Route Visualization")
    plt.legend()
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

    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()

    if args.command == "plot-instance":
        instance = load_instance(args.file)
        plot_instance(instance)

    elif args.command == "plot-route":
        instance = load_instance(args.file)
        route = list(map(int, args.route.split(",")))
        plot_route(instance, route)
