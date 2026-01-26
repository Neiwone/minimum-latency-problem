import random
import math
import argparse
import os


def generate_dmp_instance(
    n_nodes: int,
    grid_size: int = 100,
    seed: int | None = None,
    distance_type: str = "euclidean",
):
    if seed is not None:
        random.seed(seed)

    coords = [
        (random.randint(0, grid_size), random.randint(0, grid_size))
        for _ in range(n_nodes)
    ]

    depot = 0

    def distance(a, b):
        if distance_type == "euclidean":
            return math.hypot(a[0] - b[0], a[1] - b[1])
        elif distance_type == "manhattan":
            return abs(a[0] - b[0]) + abs(a[1] - b[1])
        else:
            raise ValueError("Invalid distance type")

    dist = [
        [distance(coords[i], coords[j]) for j in range(n_nodes)]
        for i in range(n_nodes)
    ]

    return {
        "coords": coords,
        "depot": depot,
        "dist": dist,
    }


def save_as_tsplib(instance, filename: str, out_dir="instances"):
    os.makedirs(out_dir, exist_ok=True)
    coords = instance["coords"]

    path = os.path.join(out_dir, filename + ".tsp")
    with open(path, "w") as f:
        f.write(f"NAME: {filename}\n")
        f.write("TYPE: TSP\n")
        f.write(f"DIMENSION: {len(coords)}\n")
        f.write("EDGE_WEIGHT_TYPE: EUC_2D\n")
        f.write("NODE_COORD_SECTION\n")

        for i, (x, y) in enumerate(coords, start=1):
            f.write(f"{i} {x} {y}\n")

        f.write("EOF\n")

    return path


def parse_args():
    parser = argparse.ArgumentParser(
        description="Random DMP / TSP instance generator"
    )

    parser.add_argument("--n", type=int, required=True, help="Number of nodes")
    parser.add_argument("--grid", type=int, default=50, help="Grid size")
    parser.add_argument("--seed", type=int, default=None, help="Random seed")
    parser.add_argument("--out", type=str, required=True, help="Output instance name")

    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()

    instance = generate_dmp_instance(
        n_nodes=args.n,
        grid_size=args.grid,
        seed=args.seed,
    )

    path = save_as_tsplib(instance, args.out)
    print(f"Instance saved to {path}")
