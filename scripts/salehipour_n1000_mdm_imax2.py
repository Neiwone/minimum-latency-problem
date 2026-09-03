"""
Re-runs ONLY mdm_gils_rvnd on the n=1000 Salehipour tier, with --imax 2
instead of --imax 1.

Why: mdm_gils_rvnd.cpp splits I_max into phase1Iters = max(1, I_max/2)
plain-GILS-RVND iterations followed by mining-guided iterations. With
--imax 1, phase1Iters = max(1, 0) = 1, and the single iteration (i=0) never
satisfies `i >= phase1Iters`, so the mining phase NEVER runs -- the n=1000
mdm_gils_rvnd results gathered under --imax 1 (see
salehipour_n1000_mdm_vs_am_extended_checkpoint.json) are byte-identical to
gils_rvnd, because they never actually exercised MDM's mining mechanism.
Same class of footgun already documented in the project's
feedback-experiment-rigor memory for H2's path relinking under --imax 1.

--imax 2 is the minimum value that gives phase1Iters = max(1, 1) = 1, so
the 2-iteration loop (i=0,1) runs exactly one plain-GILS-RVND iteration
(i=0) and one real mining-guided iteration (i=1) -- the smallest budget
that actually tests the mechanism.

gils_rvnd and gils_am_rvnd_extended_oropt are NOT re-run here -- their
--imax 1 results are unaffected by this bug (they don't have a phase split)
and stay valid as already gathered.

Checkpoint lives in this file's own directory (NOT /tmp) -- see
feedback-experiment-rigor memory: a previous batch lost progress to a
machine reboot because its checkpoint was in the session scratchpad.
"""
import json
import statistics
import subprocess
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
INST_DIR = PROJECT_ROOT / "instances" / "salehipour"
CHECKPOINT = Path(__file__).resolve().parent / "salehipour_n1000_mdm_imax2_checkpoint.json"
LOG = Path(__file__).resolve().parent / "salehipour_n1000_mdm_imax2.log"

SIZE = 1000
N_PER_SIZE = 20
N_RUNS = 10  # seeds 1..10
I_MAX = 2    # minimum value that actually exercises the mining phase -- see module docstring
I_ILS = 100

BINARY = str(PROJECT_ROOT / "bin/mdm_gils_rvnd")


def parse_output(stdout: str):
    data = {}
    for line in stdout.strip().splitlines():
        parts = line.split(maxsplit=1)
        if len(parts) == 2:
            data[parts[0]] = parts[1]
    return data


def run_unit(index):
    inst_path = str(INST_DIR / f"salehipour_n{SIZE:04d}_i{index:02d}.tsp")
    costs = []
    times = []
    t0 = time.time()
    for seed in range(1, N_RUNS + 1):
        cmd = [BINARY, inst_path, "--imax", str(I_MAX), "--iils", str(I_ILS), "--seed", str(seed)]
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
        "solver": "mdm_gils_rvnd_imax2",
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

    units = [idx for idx in range(1, N_PER_SIZE + 1) if str(idx) not in results]
    total_count = N_PER_SIZE
    print(f"Total units to run: {len(units)} (of {total_count} total)", flush=True)

    done_count = len(results)

    with LOG.open("a") as logf:
        with ProcessPoolExecutor(max_workers=6) as ex:
            futures = {ex.submit(run_unit, idx): idx for idx in units}
            for fut in as_completed(futures):
                idx = futures[fut]
                try:
                    r = fut.result()
                except Exception as e:
                    line = f"FAILED {idx}: {e}"
                    print(line, flush=True)
                    logf.write(line + "\n")
                    logf.flush()
                    continue
                results[str(idx)] = r
                done_count += 1
                line = (f"[{done_count}/{total_count}] TRP-S1000-R{idx:<3d} mdm_gils_rvnd_imax2 "
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
