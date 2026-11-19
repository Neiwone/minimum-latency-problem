#!/usr/bin/env bash
# The proposal with the published MDM-GILS-RVND time (Santana et al., 2019) on
# the circuit instances where the 100 s / 1000 s caps cut it short,
# 10 runs each, plus seeds 6..10 of the n >= 500 instances that already ran
# uncapped with 5 runs. One instance at a time, smallest first, one core; each
# run is checkpointed, so it can be killed (kill -- -PGID) and rerun to resume.
#
#   nohup setsid scripts/run_circuit_paper_time.sh >> results/literature/circuit_paper_time.log 2>&1 &
set -euo pipefail
cd "$(dirname "$0")/.."
CORE=${CORE:-2}
for inst in rd400 fl417 gr431 pr439 pcb442 d493 att532 ali535 si535 pa561 u574 \
            rat575 p654 d657 gr666 u724 rat783 \
            si1032 pr1002 d1291 vm1084 u1060 dsj1000 rl1304 pcb1173 rl1323 nrw1379; do
    echo "=== $inst $(date '+%F %T')"
    case $inst in
        att532|ali535|si535|pa561|u574)
            python3 scripts/literature_compare.py --suite circuit-long --runs 10 \
                --instances "$inst" --out results/literature/circuit_long.json --cores "$CORE" --no-report ;;
        *)
            python3 scripts/literature_compare.py --suite circuit --cap 100000 \
                --instances "$inst" --out results/literature/circuit_paper_time.json --cores "$CORE" --no-report ;;
    esac
done
echo "=== done $(date '+%F %T')"
