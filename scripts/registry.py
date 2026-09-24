"""
The instance and solver registry shared by run_experiments.py and the
analysis scripts: which instances exist and how they are grouped, and every
solver name with the command it runs.
"""
import os
import re
from pathlib import Path
from typing import Dict, List, Tuple

INSTANCES = [
    # TSPLIB instances
    # "eil51.tsp",
    # "berlin52.tsp",
    # "pr76.tsp",
    # "rat99.tsp",
    # "kroA100.tsp",
    # "eil101.tsp",

    # "st70.tsp",
    # "rat99.tsp",
    # "kroD100.tsp",
    # "lin105.tsp",
    # "pr107.tsp",
    # "rat195.tsp",
    # "pr226.tsp",
    # "lin318.tsp",
    # "pr439.tsp",
    # "att532.tsp",

    "gr120.tsp",
]

def _n_of(name: str) -> int:
    """n from the trailing digits of a TSPLIB name (kroA150 -> 150)."""
    return int(re.search(r"(\d+)(?=\.tsp$)", name).group(1))


# The 77 TSPLIB instances
TSPLIB = [
    "dantzig42.tsp",         # 42  EXPLICIT
    "swiss42.tsp",           # 42  EXPLICIT
    "att48.tsp",             # 48  ATT
    "gr48.tsp",              # 48  EXPLICIT
    "hk48.tsp",              # 48  EXPLICIT
    "eil51.tsp",             # 51
    "berlin52.tsp",          # 52
    "brazil58.tsp",          # 58  EXPLICIT
    "st70.tsp",              # 70
    "eil76.tsp",             # 76
    "pr76.tsp",              # 76
    "gr96.tsp",              # 96  GEO
    "rat99.tsp",             # 99
    "kroA100.tsp",           # 100
    "kroB100.tsp",           # 100
    "kroC100.tsp",           # 100
    "kroD100.tsp",           # 100
    "kroE100.tsp",           # 100
    "rd100.tsp",             # 100
    "eil101.tsp",            # 101
    "lin105.tsp",            # 105
    "pr107.tsp",             # 107
    "gr120.tsp",             # 120  EXPLICIT
    "pr124.tsp",             # 124
    "bier127.tsp",           # 127
    "ch130.tsp",             # 130
    "pr136.tsp",             # 136
    "gr137.tsp",             # 137  GEO
    "pr144.tsp",             # 144
    "ch150.tsp",             # 150
    "kroA150.tsp",           # 150
    "kroB150.tsp",           # 150
    "pr152.tsp",             # 152
    "u159.tsp",              # 159
    "si175.tsp",             # 175  EXPLICIT
    "brg180.tsp",            # 180  EXPLICIT
    "rat195.tsp",            # 195
    "d198.tsp",              # 198
    "kroA200.tsp",           # 200
    "kroB200.tsp",           # 200
    "gr202.tsp",             # 202  GEO
    "ts225.tsp",             # 225
    "tsp225.tsp",            # 225
    "pr226.tsp",             # 226
    "gr229.tsp",             # 229  GEO
    "gil262.tsp",            # 262
    "pr264.tsp",             # 264
    "a280.tsp",              # 280
    "pr299.tsp",             # 299
    "lin318.tsp",            # 318
    "rd400.tsp",             # 400
    "fl417.tsp",             # 417
    "gr431.tsp",             # 431  GEO
    "pr439.tsp",             # 439
    "pcb442.tsp",            # 442
    "d493.tsp",              # 493
    "att532.tsp",            # 532  ATT
    "ali535.tsp",            # 535  GEO
    "si535.tsp",             # 535  EXPLICIT
    "pa561.tsp",             # 561  EXPLICIT
    "u574.tsp",              # 574
    "rat575.tsp",            # 575
    "p654.tsp",              # 654
    "d657.tsp",              # 657
    "gr666.tsp",             # 666  GEO
    "u724.tsp",              # 724
    "rat783.tsp",            # 783
    "dsj1000.tsp",           # 1000  CEIL_2D
    "pr1002.tsp",            # 1002
    "si1032.tsp",            # 1032  EXPLICIT
    "u1060.tsp",             # 1060
    "vm1084.tsp",            # 1084
    "pcb1173.tsp",           # 1173
    "d1291.tsp",             # 1291
    "rl1304.tsp",            # 1304
    "rl1323.tsp",            # 1323
    "nrw1379.tsp",           # 1379
]

# Named groups usable with --instances in every mode, e.g. --instances tsplib-200
INSTANCE_GROUPS = {
    "tsplib":     TSPLIB,
    "tsplib-120": [i for i in TSPLIB if _n_of(i) >= 120],
    "tsplib-200": [i for i in TSPLIB if _n_of(i) >= 200],
    "tsplib-500": [i for i in TSPLIB if _n_of(i) >= 500],
}


def resolve_instances(names) -> List[str]:
    """Expand group names into .tsp filenames; other names are taken literally.
    None/empty means the tracked INSTANCES list."""
    if not names:
        return list(INSTANCES)
    out = [n if n.endswith(".tsp") else n + ".tsp"
           for name in names
           for n in INSTANCE_GROUPS.get(name, [name])]
    # Fail before launching the first solver, not after a typo burns the batch.
    missing = [n for n in out if not os.path.exists(os.path.join(INST_DIR, n))]
    if missing:
        raise SystemExit(f"Error: instances not found: {', '.join(missing)}\n"
                         f"Groups: {', '.join(INSTANCE_GROUPS)}")
    return out


# --closed only exists in these three; anywhere else it would be dropped and the
# run would silently report open-path costs.
CLOSED_CAPABLE = {"gils_am_rvnd", "mdm_gils_rvnd", "gils_rvnd"}
# Every path in the project (instances/, bin/, results/) is relative to
# this directory; run_experiments.py changes into it before doing anything.
ROOT = Path(__file__).resolve().parent.parent
INST_DIR = "instances"
SOLUTIONS_DIR = Path(INST_DIR) / "solutions"
BEST_SOLUTIONS_FILE = SOLUTIONS_DIR / "best_solutions.json"


SALEHIPOUR_DIR = Path(INST_DIR) / "salehipour"
SALEHIPOUR_SIZES = [10, 20, 50, 100, 200, 500, 1000]
SALEHIPOUR_INSTANCES_PER_SIZE = 20


def salehipour_instances(size: int) -> List[str]:
    """Paths (relative to project root) of the 20 instances for one size."""
    return [
        str(SALEHIPOUR_DIR / f"salehipour_n{size:04d}_i{i:02d}.tsp")
        for i in range(1, SALEHIPOUR_INSTANCES_PER_SIZE + 1)
    ]


# Solvers. Value is either a bare binary path, or (path, extra_args) when the
# solver needs fixed flags appended after "<binary> <instance>".
# `--list-solvers` prints them all with their commands.
SOLVERS_RAW = {
    # ---- Building blocks and other metaheuristics, as published ----
    "nn": "./bin/nearest_neighbour",
    "backtracking": "./bin/backtracking",
    "local_search": "./bin/local_search",
    "construction": "./bin/construction",
    "grasp": "./bin/grasp",
    "grasp_am": "./bin/grasp_am",
    "tabu_search": "./bin/tabu_search",
    "gils_rvnd_tabu": "./bin/gils_rvnd_tabu",
    "grasp_vnd": ("./bin/grasp_vnd", ["--local-search", "vnd"]),
    "grasp_vns": ("./bin/grasp_vnd", ["--local-search", "vns"]),

    # ---- The two baselines ----
    "gils_rvnd": "./bin/gils_rvnd",
    "mdm_gils_rvnd": "./bin/mdm_gils_rvnd",

    # ---- The proposed method ----
    # GILS-AM-RVND with the candidate-list RVND, don't-look bits and I_ILS
    # retuned. Beats mdm_gils_rvnd at 100s/run for n >= 200: -1.249%,
    # 60/10/0 of 70 pairs. See docs/experiments/h19-dlb-fast-regime.md.
    "gils_am_rvnd_dlb": ("./bin/gils_am_rvnd",
                         ["--rvnd-mode", "candidate-dlb", "--cand-k", "12", "--iils", "300"]),

    # ---- H19 fairness controls ----
    # The same local search as the proposed method, so what is left between
    # the three is only the memory strategy -- pattern mining (mdm), adaptive
    # memory (gils_am), or none at all (gils_rvnd).
    "mdm_gils_rvnd_dlb": ("./bin/mdm_gils_rvnd",
                          ["--rvnd-mode", "candidate-dlb", "--cand-k", "12", "--iils", "300"]),
    "gils_rvnd_dlb": ("./bin/gils_rvnd",
                      ["--rvnd-mode", "candidate-dlb", "--cand-k", "12", "--iils", "300"]),
    # Same, at the I_ILS where mdm's mining is exercised with room to spare
    # (~4x the calls of --iils 300), so the control cannot be dismissed as
    # "their mechanism barely ran".
    "mdm_gils_rvnd_dlb_i100": ("./bin/mdm_gils_rvnd",
                               ["--rvnd-mode", "candidate-dlb", "--cand-k", "12", "--iils", "100"]),
    # The baseline at its own best I_ILS, so it is best config vs best config.
    "mdm_gils_rvnd_i300": ("./bin/mdm_gils_rvnd", ["--iils", "300"]),

    # ---- H16: candidate-list neighborhoods (K nearest neighbours) ----
    # Kept to reproduce the results and screening tables of
    # docs/experiments/h16-candidate-neighborhoods.md. gils_am_rvnd_cand and
    # gils_am_rvnd_cand12 are the same configuration under the two names the
    # checkpoints use.
    "gils_am_rvnd_cand": ("./bin/gils_am_rvnd", ["--rvnd-mode", "candidate", "--cand-k", "12"]),
    "gils_am_rvnd_cand12": ("./bin/gils_am_rvnd", ["--rvnd-mode", "candidate", "--cand-k", "12"]),
    "gils_am_rvnd_cand20": ("./bin/gils_am_rvnd", ["--rvnd-mode", "candidate", "--cand-k", "20"]),
    "gils_am_rvnd_cand12_db10": ("./bin/gils_am_rvnd", ["--rvnd-mode", "candidate", "--cand-k", "12", "--db-maxseg-div", "10"]),
    "gils_am_rvnd_oropt_rev": ("./bin/gils_am_rvnd", ["--rvnd-mode", "extended-oropt-rev"]),
    "gils_am_rvnd_ext_db10": ("./bin/gils_am_rvnd", ["--rvnd-mode", "extended-oropt", "--db-maxseg-div", "10"]),
    "gils_am_rvnd_rev_db10": ("./bin/gils_am_rvnd", ["--rvnd-mode", "extended-oropt-rev", "--db-maxseg-div", "10"]),

    # ---- H12: extended or-opt (segments up to 6) ----
    "gils_am_rvnd_extended_oropt": ("./bin/gils_am_rvnd", ["--rvnd-mode", "extended-oropt"]),
    "grasp_vnd_extended_oropt": ("./bin/grasp_vnd", ["--local-search", "vnd", "--or-opt-max-len", "6"]),
    # --imax 1: the binaries' own default (--imax 10) takes hours per
    # instance at n=500/1000 (docs/experiments/h12-extended-oropt.md
    # section 9); used for the large sizes of the salehipour-benchmark.
    "gils_rvnd_imax1": ("./bin/gils_rvnd", ["--imax", "1"]),
    "gils_am_rvnd_extended_oropt_imax1": ("./bin/gils_am_rvnd", ["--rvnd-mode", "extended-oropt", "--imax", "1"]),

    # ---- Adaptive-memory parent selection (src/grasp_am.cpp --parent-mode) ----
    # See docs/experiments/grasp-am-large-scale.md.
    "gils_am_rvnd_pool": ("./bin/gils_am_rvnd", ["--parent-mode", "pool"]),
    "gils_am_rvnd_pair": ("./bin/gils_am_rvnd", ["--parent-mode", "pair"]),
}

SolverCmd = Tuple[str, List[str]]


def _normalize_solver(entry) -> SolverCmd:
    if isinstance(entry, tuple):
        path, extra_args = entry
        return (path, list(extra_args))
    return (entry, [])


SOLVERS: Dict[str, SolverCmd] = {
    name: _normalize_solver(entry) for name, entry in SOLVERS_RAW.items()
}

FIXED_TIME_BINARIES = {"./bin/gils_rvnd", "./bin/gils_am_rvnd", "./bin/mdm_gils_rvnd"}

# No randomness in these; every other binary takes --seed.
DETERMINISTIC_BINARIES = {"./bin/nearest_neighbour", "./bin/backtracking"}


def supports_fixed_time(solver_name: str) -> bool:
    return SOLVERS[solver_name][0] in FIXED_TIME_BINARIES
