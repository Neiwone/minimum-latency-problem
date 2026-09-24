# Minimum Latency Problem (MLP) Solvers in C++

Implementations of exact and heuristic algorithms for the Minimum Latency Problem
(a.k.a. Traveling Repairman Problem) on TSPLIB-style instances. The depot is node 0
and the objective is the sum of arrival times along a Hamiltonian path.

The project is built around GILS-RVND (Silva, Subramanian, Vidal & Ochi, *EJOR* 221,
2012) and a line of experiments on top of it. The current best configuration beats
MDM-GILS-RVND at 100 s/run on every instance with n >= 200 (-1.249%, 60 wins / 10 ties
/ 0 losses over 70 paired seeds). Giving MDM-GILS-RVND the same local search makes the
two tie, so the gain is local search and calibration, not search strategy -- see
[docs/hypotheses/h19-dlb-fast-regime.md](docs/hypotheses/h19-dlb-fast-regime.md).

## Layout

| Path | What |
|---|---|
| `src/`, `include/` | solvers and core logic |
| `instances/` | TSPLIB instances; `salehipour/` is the 140-instance benchmark of Salehipour et al. (2011); `solutions/` holds the best tours found |
| `docs/` | how the method works and every experiment write-up; [docs/README.md](docs/README.md) is the index |
| `scripts/` | the batch runner (`run_experiments.py`), analysis and instance tools; `registry.py`, `runner.py` and `stats.py` are modules they share |
| `results/` | raw per-run data (checkpoints) behind every table in `docs/` |

## Build

	make                  # everything, into bin/
	make gils_am_rvnd     # one target
	make clean

Requires a C++17 compiler and make. The Python tooling needs Python 3.10+ and `uv`
(dependencies are declared in `pyproject.toml`).

## Running a solver

The best configuration in the project:

	./bin/gils_am_rvnd instances/att532.tsp \
	    --rvnd-mode candidate-dlb --cand-k 12 --iils 300 --max-time 100

`--max-time` is a wall-clock budget in seconds, and is what makes an equal-time
comparison between algorithms possible. Every solver prints `INSTANCE`, `NODES`,
`COST`, `TIME_MS` and `ROUTE`; the metaheuristics add their own counters
(`RESTARTS`, `MINING_CALLS`, ...). Run a binary with no arguments for its flags.

| Binary | What it is |
|---|---|
| `gils_am_rvnd` | GILS-RVND + adaptive memory; hosts the candidate-list and don't-look-bit local searches (`--rvnd-mode`). **The one to use.** |
| `gils_rvnd` | GILS-RVND as published, plus the flags of the rejected hypotheses |
| `mdm_gils_rvnd` | GILS-RVND with FPMax* pattern mining (Santana, Plastino & Rosseti) |
| `grasp_vnd` | GRASP+VND / GRASP+VNS of Salehipour et al. (2011) |
| `dbmea`, `tabu_search`, `gils_rvnd_tabu`, `grasp`, `grasp_am` | other metaheuristics compared along the way |
| `construction`, `local_search`, `nearest_neighbour` | single building blocks, runnable on their own |
| `backtracking` | exact solver; small instances only |

## Experiments

`scripts/run_experiments.py` runs batches, pairs them by seed, and reports means,
win/tie/loss and exact sign tests. Every mode saves each run as it finishes: without
`--checkpoint` a batch gets a new timestamped file under `results/<mode>/`, and
passing that file back with `--checkpoint` resumes it (`--checkpoint last` picks the
newest one of the mode). The checkpoint records the batch configuration, so a resume
with different flags is refused instead of mixing runs. Runs use seeds 1..`--runs`, so
a batch is reproducible.

	# equal-time comparison, the protocol used for every result in docs/
	python3 scripts/run_experiments.py --mode fixed-time --time-limit 100 --runs 10 \
	    --instances lin318 pr439 att532 \
	    --solvers mdm_gils_rvnd gils_am_rvnd_dlb

Other modes: `compare-solvers`, `compare-best` (against the tracked best solutions),
and `salehipour-benchmark`. `--help` lists the rest.

The fixed-time protocol has two rules that results depend on, both learned the hard
way: runs are **sequential** (timing comparisons do not survive CPU contention), and
the budget must fit several restarts, or the restart-boundary mechanisms silently
degenerate. See
[docs/benchmarks/fixed-time-protocol.md](docs/benchmarks/fixed-time-protocol.md).

## Docs

The docs are in Portuguese. Start with [docs/README.md](docs/README.md), the index: it
lists every doc and has a one-line verdict for each hypothesis.

- [docs/results-tables.md](docs/results-tables.md) — the final results, generated from
  the checkpoints by `scripts/make_result_tables.py`.
- [docs/concepts/](docs/concepts/) — how the method works: the problem, GILS-RVND, what
  the proposal changes, distance types, 64-bit costs, the `--closed` flag.
- [docs/hypotheses/](docs/hypotheses/) — one write-up per hypothesis, including the many
  that were refuted.
- [docs/benchmarks/](docs/benchmarks/) — the fixed-time protocol and the benchmark
  comparisons.

## Python scripts

	uv run scripts/instance_generator.py --n 50 --grid 100 --seed 42 --out rand50
	uv run scripts/instance_visualizer.py plot-route eil51.tsp --route 0,31,10,37
	uv run scripts/generate_salehipour_benchmark.py

`scripts/interactive_builder.py` opens a pygame canvas for drawing an instance by
hand, and `scripts/record_best.py` verifies a solver's tour from the raw coordinates
before saving it as a new best.
