#!/usr/bin/env bash
#
# Two fixed-time batches over the Salehipour benchmark, for the write-up.
# Resumable: if the machine reboots or you Ctrl-C, just run this again and it
# picks up where it stopped (the checkpoints live in scripts/).
#
#   nohup setsid bash scripts/run_advisor_batches.sh > scripts/advisor_run.log 2>&1 &
#
# Five arms in one batch, so the headline and the controls come from the same
# runs:
#   mdm_gils_rvnd            published baseline, its own protocol config
#   gils_am_rvnd_dlb         the proposal
#   mdm_gils_rvnd_dlb        the same local search given to mdm (is the gain
#                            the local search, or the strategy?)
#   mdm_gils_rvnd_dlb_i100   idem, at an I_ILS where mdm's mining runs with
#                            room to spare, so the control cannot be dismissed
#   gils_rvnd_dlb            the same local search with NO memory mechanism
#                            (does any memory mechanism matter at all?)
#
# RULES (results are void otherwise):
#   - nothing else heavy may run on this machine while the batch runs;
#   - do not start a second copy in parallel -- runs must be sequential;
#   - all four arms must come from THIS machine; never mix with another one's.

set -u
cd "$(dirname "$0")/.."

SOLVERS="mdm_gils_rvnd gils_am_rvnd_dlb mdm_gils_rvnd_dlb mdm_gils_rvnd_dlb_i100 gils_rvnd_dlb"

echo "=== build ==="
# `directories` first: bin/ and obj/ are gitignored, so on a fresh clone a
# parallel make could try to link before they exist.
make directories && make -j"$(nproc)" || { echo "BUILD FAILED"; exit 1; }

echo
echo "=== preflight: every arm runs and reports a cost ==="
for s in ./bin/mdm_gils_rvnd ./bin/gils_am_rvnd ./bin/gils_rvnd; do
    out=$("$s" instances/rat195.tsp --rvnd-mode candidate-dlb --cand-k 12 \
              --iils 300 --max-time 5 --seed 1 | grep -E "^COST")
    [ -n "$out" ] || { echo "PREFLIGHT FAILED: $s"; exit 1; }
    echo "  $s  $out"
done
python3 scripts/verify_tour.py instances/att532.tsp ./bin/gils_am_rvnd \
    instances/att532.tsp --rvnd-mode candidate-dlb --cand-k 12 --iils 300 \
    --max-time 5 --seed 1 || { echo "PREFLIGHT FAILED: invalid tour"; exit 1; }

echo
echo "=== batch 1/2: Salehipour n=1000, 20 instances x 5 solvers x 3 seeds ==="
echo "    300 runs at 100 s each, roughly 8.5 hours"
python3 run_experiments.py --mode fixed-time --time-limit 100 --runs 3 \
    --salehipour-sizes 1000 \
    --solvers $SOLVERS \
    --checkpoint scripts/advisor_n1000_100s.json

echo
echo "=== batch 2/2: Salehipour n=500, 20 instances x 5 solvers x 4 seeds ==="
echo "    400 runs at 100 s each, roughly 11.5 hours"
python3 run_experiments.py --mode fixed-time --time-limit 100 --runs 4 \
    --salehipour-sizes 500 \
    --solvers $SOLVERS \
    --checkpoint scripts/advisor_n500_100s.json

echo
echo "=== ALL DONE ==="
echo "Send back: scripts/advisor_n1000_100s.json, scripts/advisor_n500_100s.json,"
echo "           scripts/advisor_run.log"
