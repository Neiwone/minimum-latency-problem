"""
Running a solver binary and keeping what it produced: the parsed output of
one run, the checkpoint a batch is saved to, and the best known solutions
in instances/solutions/.
"""
import json
import os
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from control import CONTROL, RunInterrupted
from registry import (CLOSED_CAPABLE, DETERMINISTIC_BINARIES, SOLVERS, SolverCmd)

# Set from --closed by run_experiments.py: every run then counts the return
# to the depot.
CLOSED_TOUR = False


class SolutionTracker:
    """Manages best known solutions and TSPLIB tour files."""

    def __init__(self, solutions_dir: Path):
        self.solutions_dir = solutions_dir
        self.solutions_dir.mkdir(parents=True, exist_ok=True)
        self.best_solutions_file = solutions_dir / "best_solutions.json"
        self.best_solutions = self._load_best_solutions()

    def _load_best_solutions(self) -> Dict:
        """Load best known solutions from JSON file."""
        if self.best_solutions_file.exists():
            with open(self.best_solutions_file, 'r') as f:
                return json.load(f)
        return {}

    def _save_best_solutions(self):
        """Save best solutions to JSON file."""
        with open(self.best_solutions_file, 'w') as f:
            json.dump(self.best_solutions, indent=2, fp=f)

    def get_best_cost(self, instance: str) -> Optional[float]:
        """Get the best known cost for an instance."""
        if instance in self.best_solutions:
            return self.best_solutions[instance]["cost"]
        return None

    def is_better(self, instance: str, cost: float) -> bool:
        """Check if the given cost is better than the current best."""
        best_cost = self.get_best_cost(instance)
        if best_cost is None:
            return True
        return cost < best_cost

    def save_solution(self, instance: str, cost: float, route: str, solver: str,
                     nodes: int, force: bool = False):
        """
        Save a solution in TSPLIB format and update best solutions.

        Args:
            instance: Instance name (without .tsp extension)
            cost: Solution cost
            route: Space-separated node indices (1-indexed)
            solver: Name of the solver that found this solution
            nodes: Number of nodes in the instance
            force: If True, save without prompting
        """
        if not force and not self.is_better(instance, cost):
            print(f"  Cost {cost:.2f} is not better than current best "
                  f"{self.get_best_cost(instance):.2f}")
            return False

        # Prompt user if this is better
        if not force and instance in self.best_solutions:
            current_best = self.best_solutions[instance]["cost"]
            improvement = ((current_best - cost) / current_best) * 100
            response = input(
                f"\n  New best solution for {instance}!\n"
                f"  Current: {current_best:.2f} → New: {cost:.2f} "
                f"(improvement: {improvement:.2f}%)\n"
                f"  Save this solution? [Y/n]: "
            ).strip().lower()

            if response and response != 'y' and response != 'yes':
                print("  Solution not saved.")
                return False

        # Save TSPLIB tour file
        tour_file = self.solutions_dir / f"{instance}.tour"
        self._write_tsplib_tour(tour_file, instance, cost, route, nodes, solver)

        # Update best solutions JSON
        self.best_solutions[instance] = {
            "cost": cost,
            "solver": solver,
            "timestamp": datetime.now().isoformat(),
            "tour_file": str(tour_file.name)
        }
        self._save_best_solutions()

        print(f"  ✓ Saved solution to {tour_file.name}")
        return True

    def _write_tsplib_tour(self, filepath: Path, instance: str, cost: float,
                          route: str, nodes: int, solver: str):
        """Write solution in TSPLIB tour format."""
        route_nodes = route.split()

        with open(filepath, 'w') as f:
            f.write(f"NAME : {instance}.tour\n")
            f.write(f"COMMENT : MLP solution (cost={cost:.2f}, solver={solver})\n")
            f.write("TYPE : TOUR\n")
            f.write(f"DIMENSION : {nodes}\n")
            f.write("TOUR_SECTION\n")

            for node in route_nodes:
                f.write(f"{node}\n")

            f.write("-1\n")
            f.write("EOF\n")


def run_solver(solver: SolverCmd, instance_path: str, route: Optional[str] = None,
               verbose: bool = False, seed: Optional[int] = None) -> Dict:
    """
    Run a solver and parse its output. `seed` is passed as --seed to every
    binary that has randomness, so the same seed reproduces the same run.
    """
    solver_path, extra_args = solver

    # ---------- Warm start for Local Search ----------
    if "local_search" in solver_path and route is None:
        construction_solver = SOLVERS["construction"]

        construction_solution = run_solver(construction_solver, instance_path, seed=seed)

        route = construction_solution["route"]

    # ---------- Run solver ----------
    cmd = [solver_path, instance_path]

    if verbose and (
        "gils_rvnd" in solver_path
        or "grasp_rvnd" in solver_path
        or "grasp_am" in solver_path
        or "gils_rvnd_tabu" in solver_path
        or "tabu_search" in solver_path
        or solver_path.endswith("/grasp")
    ):
        cmd.append("-v")

    if route is not None:
        cmd += ["--route", route]

    cmd += extra_args

    if seed is not None and solver_path not in DETERMINISTIC_BINARIES:
        cmd += ["--seed", str(seed)]

    if CLOSED_TOUR:
        if os.path.basename(solver_path) not in CLOSED_CAPABLE:
            raise RuntimeError(
                f"{os.path.basename(solver_path)} has no --closed and would report "
                f"open-path costs. Supported: {', '.join(sorted(CLOSED_CAPABLE))}")
        cmd.append("--closed")

    # Waited on in short slices so Ctrl+P / Ctrl+Q (control.py) can kill it;
    # communicate() returns as soon as the solver exits, so no time is added.
    proc = subprocess.Popen(cmd, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE, text=True)
    while True:
        try:
            stdout, stderr = proc.communicate(timeout=0.2)
            break
        except subprocess.TimeoutExpired:
            if CONTROL.interrupt.is_set():
                proc.kill()
                proc.communicate()
                raise RunInterrupted()

    if proc.returncode != 0:
        raise RuntimeError(f"Solver failed: {stderr}")

    data = {}
    for line in stdout.strip().splitlines():
        parts = line.split(maxsplit=1)
        if len(parts) == 2:
            key, value = parts
            data[key] = value

    best_iter = None
    if stderr:
        for line in stderr.strip().splitlines():
            if line.startswith("best at iter"):
                parts = line.split()
                if len(parts) >= 4:
                    try:
                        best_iter = int(parts[3])
                    except ValueError:
                        best_iter = None

    outer_iters = 0
    if "IMAX" in data:
        try:
            outer_iters = int(data["IMAX"])
        except ValueError:
            outer_iters = 0
    elif "ITER" in data:
        try:
            outer_iters = int(data["ITER"])
        except ValueError:
            outer_iters = 0

    time_ms = float(data.get("TIME_MS", 0))
    time_to_best_ms = None
    if best_iter is not None and outer_iters > 0:
        bounded_iter = min(max(best_iter, 0), outer_iters - 1)
        time_to_best_ms = ((bounded_iter + 1) / outer_iters) * time_ms

    return {
        "nodes": int(data.get("NODES", 0)),
        "cost": float(data.get("COST", 0)),
        "closed": data.get("CLOSED") == "1",
        "time": time_ms,
        # Restart-boundary mechanism counters (see fixed-time mode): -1 when
        # the solver does not report them.
        "restarts": int(data.get("RESTARTS", -1)),
        "mining_calls": int(data.get("MINING_CALLS", -1)),
        "pattern_restarts": int(data.get("PATTERN_RESTARTS", -1)),
        "construction_ms": float(data.get("CONSTRUCTION_MS", 0)),
        "rvnd_ms": float(data.get("RVND_MS", 0)),
        "tabu_ms": float(data.get("TABU_MS", 0)),
        "route": data.get("ROUTE"),
        "best_iter": best_iter,
        "time_to_best_ms": time_to_best_ms,
    }


class Checkpoint:
    """
    The runs of one batch, keyed "<instance>|<solver>|<seed>" and written to
    disk after every run, so an interrupted batch resumes where it stopped.

    The file also records the batch configuration, and resuming under a
    different one is refused: the keys say nothing about --time-limit,
    --iils, --closed or a solver's flags, so a mismatched resume would reuse
    runs made under the old settings as if they were made under the new
    ones. Adding solvers, instances or seeds to a batch is fine.
    """

    def __init__(self, path: Path, mode: str, params: Dict,
                 solvers: Dict[str, List[str]]):
        self.path = path
        if not path.exists():
            self.meta = {
                "mode": mode,
                "created": datetime.now().isoformat(timespec="seconds"),
                "params": params,
                "solvers": dict(solvers),
            }
            self.runs: Dict[str, Dict] = {}
            print(f"New checkpoint: {path}")
            return

        data = json.loads(path.read_text())
        if "meta" not in data:
            raise SystemExit(
                f"Error: {path} predates checkpoints that record their batch "
                f"configuration, so resuming it cannot be checked against this "
                f"run. Start a new checkpoint instead.")
        meta = data["meta"]
        problems = []
        if meta["mode"] != mode:
            problems.append(f"mode: {meta['mode']} -> {mode}")
        for k in sorted(set(meta["params"]) | set(params)):
            if meta["params"].get(k) != params.get(k):
                problems.append(f"{k}: {meta['params'].get(k)} -> {params.get(k)}")
        for name, cmd in solvers.items():
            old = meta["solvers"].get(name)
            if old is not None and old != cmd:
                problems.append(f"{name}: '{' '.join(old)}' -> '{' '.join(cmd)}'")
        if problems:
            raise SystemExit(
                f"Error: {path} was made with a different configuration:\n  "
                + "\n  ".join(problems)
                + "\nResuming would mix the two. Start a new checkpoint instead.")

        meta["solvers"].update(solvers)
        self.meta = meta
        self.runs = data["runs"]
        print(f"Resuming from {path} ({len(self.runs)} runs already done)")

    def save(self):
        # Write-then-rename: a kill mid-write leaves the previous file intact
        # instead of a truncated JSON that cannot be resumed.
        self.path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.path.with_name(self.path.name + ".tmp")
        tmp.write_text(json.dumps({"meta": self.meta, "runs": self.runs}))
        os.replace(tmp, self.path)


def solver_command(solver: SolverCmd) -> List[str]:
    """How a solver is recorded in a checkpoint: binary + flags, no instance/seed."""
    binary, extra = solver
    return [binary] + list(extra)


def run_cached(ckpt: Checkpoint, inst_name: str, inst_path: str, solver_name: str,
               seed: int, solver: Optional[SolverCmd] = None, verbose: bool = False,
               keep_route: bool = False) -> Tuple[Dict, Optional[Dict]]:
    """One run, taken from the checkpoint when it is already there.
    Returns (record, raw solver output or None when it came from the checkpoint)."""
    key = f"{inst_name}|{solver_name}|{seed}"
    if key in ckpt.runs:
        return ckpt.runs[key], None

    # A run killed by Ctrl+P is redone once the batch resumes; after Ctrl+Q,
    # wait_to_run raises BatchStopped instead.
    while True:
        CONTROL.wait_to_run()
        try:
            sol = run_solver(solver or SOLVERS[solver_name], inst_path,
                             verbose=verbose, seed=seed)
            break
        except RunInterrupted:
            continue
    rec = {
        "cost": sol["cost"],
        "time_ms": sol["time"],
        "nodes": sol["nodes"],
        "restarts": sol["restarts"],
        "mining_calls": sol["mining_calls"],
    }
    if sol["time_to_best_ms"] is not None:
        rec["time_to_best_ms"] = sol["time_to_best_ms"]
    if keep_route:
        rec["route"] = sol["route"]
    ckpt.runs[key] = rec
    ckpt.save()
    return rec, sol


def latest_checkpoint(mode: str) -> Optional[Path]:
    """The most recently written checkpoint under results/<mode>/, skipping
    files from before checkpoints had a meta header (they cannot be resumed)."""
    found = []
    for f in (Path("results") / mode).glob("*.json"):
        try:
            data = json.loads(f.read_text())
        except (OSError, ValueError):
            continue
        if isinstance(data, dict) and "meta" in data:
            found.append(f)
    return max(found, key=lambda f: f.stat().st_mtime, default=None)


def load_runs(path) -> Dict[str, Dict]:
    """The runs of a checkpoint, keyed "<instance>|<solver>|<seed>". Reads
    both the current format and the older one without a meta header."""
    data = json.loads(Path(path).read_text())
    return data["runs"] if "meta" in data else data
