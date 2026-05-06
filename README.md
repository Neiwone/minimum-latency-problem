# Minimum Latency Problem (MLP) Solvers in C++

This project implements and compares several exact and heuristic algorithms for the Minimum Latency Problem (MLP) on TSPLIB-style Euclidean instances.

The depot is fixed at node 0 and the objective is to minimize the sum of arrival times (latencies) along a Hamiltonian path.

## Project Structure

- src/: C++ implementations of solvers and core logic
- include/: headers
- instances/: TSPLIB instances used in experiments
- instances/solutions/: saved best tours and metadata
- scripts/: Python utilities (generation, visualization, interactive builder)
- run_experiments.py: batch experiment runner and result tracker
- Makefile: build rules

## Requirements

- C++17 compiler (g++)
- make
- Python 3.10+
- uv (recommended) or pip for Python dependencies

Python dependencies are declared in pyproject.toml:

- matplotlib
- pygame

## Build

Build all binaries:

	make

Build a specific target:

	make gils_rvnd_tabu

Clean artifacts:

	make clean

Generated binaries are placed in bin/.

## Solvers

### 1) nearest_neighbour

Greedy constructive heuristic. Starts at depot (0) and repeatedly visits the nearest unvisited node.

Pros:
- Very fast

Cons:
- Usually lower quality solutions

Run:

	./bin/nearest_neighbour instances/eil51.tsp

### 2) construction

Greedy randomized construction controlled by alpha. Used standalone and also as a warm start for metaheuristics.

Run:

	./bin/construction instances/eil51.tsp --alpha 0.15

### 3) local_search

Applies RVND local search using neighborhoods (swap, 2-opt, reinsertion/or-opt variants).

You can pass an initial route, otherwise it starts from the identity route 0,1,2,...

Run (default initial route):

	./bin/local_search instances/eil51.tsp

Run (custom route):

	./bin/local_search instances/eil51.tsp --route 0,3,2,5,1,4

### 4) gils_rvnd

GILS-RVND metaheuristic:

- Multi-start with randomized construction
- RVND local search
- ILS loop with double-bridge perturbation

Run:

	./bin/gils_rvnd instances/eil51.tsp --imax 10 --iils 50 -v

### 5) tabu_search

Tabu Search with full neighborhood scan and aspiration criterion.

Run:

	./bin/tabu_search instances/eil51.tsp --imax 10 --iter 500 --tenure 7 -v

### 6) gils_rvnd_tabu

Hybrid metaheuristic that combines GILS-RVND and Tabu Search:

- Construction + RVND in an ILS framework
- Controlled Tabu intensification on stagnation
- Double-bridge perturbation for diversification

Key controls:

- --tabu-iter: per-call tabu effort
- --tabu-every: cadence of tabu calls inside ILS
- --tenure: tabu tenure

Run (balanced defaults):

	./bin/gils_rvnd_tabu instances/eil51.tsp --imax 10 --iils 50 -v

Run (stronger intensification):

	./bin/gils_rvnd_tabu instances/eil51.tsp --imax 10 --iils 50 --tabu-iter 25 --tabu-every 2 --tenure 7 -v

### 7) backtracking

Exact solver (branch-and-bound style backtracking). Useful as baseline for small instances only.

Important: this binary expects the input path exactly as provided (it does not auto-prefix instances/).

Run:

	./bin/backtracking instances/eil51.tsp

## Experiment Runner

run_experiments.py automates multi-run comparisons, computes aggregated statistics, and can save improved best-known solutions.

Main modes:

- compare-best: compare one solver against tracked best solutions
- exact: compare one solver against backtracking
- compare-solvers: compare multiple solvers side by side

Examples:

Compare hybrid solver with best-known solutions:

	python3 run_experiments.py --mode compare-best --solver gils_rvnd_tabu --runs 10 --vb

Compare GILS-RVND vs hybrid:

	python3 run_experiments.py --mode compare-solvers --solvers gils_rvnd gils_rvnd_tabu --runs 10 --vb

Compare tabu_search to exact baseline:

	python3 run_experiments.py --mode exact --solver tabu_search --runs 5

Auto-save improved solutions without prompt:

	python3 run_experiments.py --mode compare-best --solver gils_rvnd_tabu --runs 10 --auto-save

## Python Scripts

You can run scripts with uv (recommended):

	uv run scripts/<script>.py ...

or with Python directly:

	python3 scripts/<script>.py ...

### 1) Instance Generator

Creates random Euclidean TSPLIB instances.

Run:

	uv run scripts/instance_generator.py --n 50 --grid 100 --seed 42 --out rand50

Output file:

- instances/rand50.tsp

### 2) Instance Visualizer

Subcommands:

- plot-instance: scatter plot of vertices
- plot-route: draw route and edge distances
- inspect-instance: click a vertex and inspect distances to all others

Run:

	uv run scripts/instance_visualizer.py plot-instance eil51.tsp

	uv run scripts/instance_visualizer.py plot-route eil51.tsp --route 0,31,10,37,4,48,8,49

	uv run scripts/instance_visualizer.py plot-route eil51.tsp --route 0,31,10,37,4,48,8,49 -v

	uv run scripts/instance_visualizer.py inspect-instance eil51.tsp

### 3) Interactive Builder

Opens a pygame interface to create custom instances manually.

Run:

	uv run scripts/interactive_builder.py

Notes:

- Left click empty area: add node
- Left click and drag node: move node
- SAVE button writes custom_instance.tsp in the current directory

## Typical Workflow

1) Build binaries:

	make

2) Run a baseline:

	./bin/gils_rvnd instances/eil51.tsp --imax 10 --iils 50

3) Run hybrid:

	./bin/gils_rvnd_tabu instances/eil51.tsp --imax 10 --iils 50

4) Compare in batch:

	python3 run_experiments.py --mode compare-solvers --solvers gils_rvnd gils_rvnd_tabu --runs 10

## Output Format (Most Solvers)

Solvers print key-value lines such as:

- INSTANCE
- NODES
- COST
- TIME_MS
- ROUTE

Metaheuristics may also print step timings like CONSTRUCTION_MS, RVND_MS, and TABU_MS.
