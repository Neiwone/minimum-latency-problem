"""
Same comparison as scripts/salehipour_mdm_vs_am_extended.py (gils_rvnd vs
gils_am_rvnd --rvnd-mode extended-oropt vs mdm_gils_rvnd), but for the
n=1000 Salehipour tier specifically, with --imax 1 instead of the paper's
--imax 10 -- the full paper protocol at this n was estimated (from the
n=50/100/200/500 data already measured in this project) at ~3.2h per single
run, which would make N=10 seeds x 20 instances x 3 solvers take ~13-14 days
even with 6-way parallelism. --imax 1 matches the precedent already
established and validated in docs/experiments/h12-extended-oropt.md
(section 9.1, "n=1000 (rand1000) -- CONFIRMADO") for testing at this scale.

Checkpoint lives in this file's own directory (NOT /tmp) so a reboot or
session restart does not lose progress (see feedback-experiment-rigor
memory -- a previous n<=500 batch lost 306/360 completed units to an
accidental machine shutdown because its checkpoint was in /tmp).
"""
import json
import statistics
import subprocess
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
INST_DIR = PROJECT_ROOT / "instances" / "salehipour"
CHECKPOINT = Path(__file__).resolve().parent / "salehipour_n1000_mdm_vs_am_extended_checkpoint.json"
LOG = Path(__file__).resolve().parent / "salehipour_n1000_mdm_vs_am_extended.log"

SIZE = 1000
N_PER_SIZE = 20
N_RUNS = 10  # seeds 1..10
I_MAX = 1    # reduced from the paper's 10 -- see module docstring
I_ILS = 100  # min(100, n) = 100 for n=1000

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


def run_unit(index, solver_name):
    """Run N_RUNS seeds for one (index, solver) combo. Runs in a worker process."""
    binary, extra_args = SOLVERS[solver_name]
    inst_path = str(INST_DIR / f"salehipour_n{SIZE:04d}_i{index:02d}.tsp")
    costs = []
    times = []
    t0 = time.time()
    for seed in range(1, N_RUNS + 1):
        cmd = [binary, inst_path, "--imax", str(I_MAX), "--iils", str(I_ILS),
               "--seed", str(seed)] + extra_args
        proc = subprocess.run(cmd, capture_output=True, text=True)
        if proc.returncode != 0:
            raise RuntimeError(f"failed: {cmd} -> {proc.stderr}")
        data = parse_output(proc.stdout)
        costs.append(float(data["COST"]))
        times.append(float(data["TIME_MS"]))
    elapsed = time.time() - t0
    return {
        "size": SIZE,
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
    for index in range(1, N_PER_SIZE + 1):
        for solver_name in SOLVERS:
            key = f"{index}_{solver_name}"
            if key not in results:
                units.append((index, solver_name))

    total_count = N_PER_SIZE * len(SOLVERS)
    print(f"Total units to run: {len(units)} (of {total_count} total)", flush=True)

    done_count = len(results)

    with LOG.open("a") as logf:
        with ProcessPoolExecutor(max_workers=6) as ex:
            futures = {ex.submit(run_unit, index, solver_name): (index, solver_name)
                       for index, solver_name in units}
            for fut in as_completed(futures):
                index, solver_name = futures[fut]
                key = f"{index}_{solver_name}"
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
                line = (f"[{done_count}/{total_count}] TRP-S1000-R{index:<3d} {solver_name:32s} "
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
