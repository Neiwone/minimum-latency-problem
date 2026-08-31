"""
Compares gils_rvnd, gils_am_rvnd --rvnd-mode extended-oropt, and mdm_gils_rvnd
on the Salehipour benchmark (instances/salehipour/), sizes 10..500, following
the exact protocol of the MDM-GILS-RVND paper (Santana, Plastino & Rosseti,
arXiv:1908.10705): Imax=10, Iils=min(100,n), R=0..0.25 (already this project's
defaults), 10 seeds per instance.

Checkpoint lives in this file's own directory (NOT /tmp) so a reboot or
session restart does not lose progress -- this batch is long-running
(the n=500 tier alone takes ~1200s per run on this machine).
"""
import json
import statistics
import subprocess
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
INST_DIR = PROJECT_ROOT / "instances" / "salehipour"
CHECKPOINT = Path(__file__).resolve().parent / "salehipour_mdm_vs_am_extended_checkpoint.json"
LOG = Path(__file__).resolve().parent / "salehipour_mdm_vs_am_extended.log"

SIZES = [10, 20, 50, 100, 200, 500]
N_PER_SIZE = 20
N_RUNS = 10  # seeds 1..10, matches paper protocol

SOLVERS = {
    "gils_rvnd": (str(PROJECT_ROOT / "bin/gils_rvnd"), []),
    "gils_am_rvnd_extended_oropt": (str(PROJECT_ROOT / "bin/gils_am_rvnd"), ["--rvnd-mode", "extended-oropt"]),
    "mdm_gils_rvnd": (str(PROJECT_ROOT / "bin/mdm_gils_rvnd"), []),
}


def parse_output(stdout: str):
    data = {}
    for line in stdout.strip().splitlines():
        parts = line.split(maxsplit=1)
        if len(parts) == 2:
            data[parts[0]] = parts[1]
    return data


def run_unit(size, index, solver_name):
    """Run N_RUNS seeds for one (size, index, solver) combo. Runs in a worker process."""
    binary, extra_args = SOLVERS[solver_name]
    inst_path = str(INST_DIR / f"salehipour_n{size:04d}_i{index:02d}.tsp")
    iils = min(100, size)
    costs = []
    times = []
    t0 = time.time()
    for seed in range(1, N_RUNS + 1):
        cmd = [binary, inst_path, "--iils", str(iils), "--seed", str(seed)] + extra_args
        proc = subprocess.run(cmd, capture_output=True, text=True)
        if proc.returncode != 0:
            raise RuntimeError(f"failed: {cmd} -> {proc.stderr}")
        data = parse_output(proc.stdout)
        costs.append(float(data["COST"]))
        times.append(float(data["TIME_MS"]))
    elapsed = time.time() - t0
    return {
        "size": size,
        "index": index,
        "solver": solver_name,
        "best_cost": min(costs),
        "avg_cost": statistics.mean(costs),
        "std_cost": statistics.pstdev(costs) if len(costs) > 1 else 0.0,
        "avg_time_ms": statistics.mean(times),
        "all_costs": costs,
        "all_times": times,
        "wall_s": elapsed,
    }


def main():
    results = {}
    if CHECKPOINT.exists():
        results = json.loads(CHECKPOINT.read_text())
        print(f"Resuming from checkpoint: {len(results)} units already done", flush=True)

    units = []
    for size in SIZES:
        for index in range(1, N_PER_SIZE + 1):
            for solver_name in SOLVERS:
                key = f"{size}_{index}_{solver_name}"
                if key not in results:
                    units.append((size, index, solver_name))

    total_count = len(SIZES) * N_PER_SIZE * len(SOLVERS)
    print(f"Total units to run: {len(units)} (of {total_count} total)", flush=True)

    done_count = len(results)

    with LOG.open("a") as logf:
        with ProcessPoolExecutor(max_workers=6) as ex:
            futures = {ex.submit(run_unit, size, index, solver_name): (size, index, solver_name)
                       for size, index, solver_name in units}
            for fut in as_completed(futures):
                size, index, solver_name = futures[fut]
                key = f"{size}_{index}_{solver_name}"
                try:
                    r = fut.result()
                except Exception as e:
                    line = f"FAILED {key}: {e}"
                    print(line, flush=True)
                    logf.write(line + "\n")
                    logf.flush()
                    continue
                results[key] = r
                done_count += 1
                line = (f"[{done_count}/{total_count}] TRP-S{size}-R{index:<3d} {solver_name:32s} "
                        f"best={r['best_cost']:.1f} avg={r['avg_cost']:.2f} "
                        f"avg_time={r['avg_time_ms']:.1f}ms wall={r['wall_s']:.1f}s")
                print(line, flush=True)
                logf.write(line + "\n")
                logf.flush()
                CHECKPOINT.write_text(json.dumps(results))

    print("ALL DONE", flush=True)
    with LOG.open("a") as logf_done:
        logf_done.write("ALL DONE\n")


if __name__ == "__main__":
    main()
