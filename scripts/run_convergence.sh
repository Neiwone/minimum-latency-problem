#!/usr/bin/env bash
# Convergence and time-per-phase study for the TCC: GILS-RVND (original RVND,
# I_ILS = 100, restarting until the time runs out) and the proposal, 300 s each,
# on three large circuit instances, seeds 1-5. Each run writes its raw output
# (TRACE_B per new best, PROFILE time per phase) to results/convergence/;
# finished runs are skipped, so it can be killed (kill -- -PGID) and rerun.
#
#   nohup setsid scripts/run_convergence.sh >> results/convergence/run.log 2>&1 &
set -euo pipefail
cd "$(dirname "$0")/.."
CORE=${CORE:-2}
TIME=${TIME:-300}
OUT=${OUT:-results/convergence}
mkdir -p "$OUT"
COMMON=(--closed --nint --max-time "$TIME" --profile --trace)
for inst in att532 pr1002 nrw1379; do
    for seed in 1 2 3 4 5; do
        for method in gils_rvnd proposta; do
            f="$OUT/${method}_${inst}_${seed}.txt"
            [[ -s $f ]] && grep -q '^PROFILE' "$f" && continue
            echo "=== $method $inst seed $seed $(date '+%F %T')"
            case $method in
                gils_rvnd) cmd=(./bin/gils_rvnd "instances/$inst.tsp" --iils 100) ;;
                proposta)  cmd=(./bin/gils_am_rvnd "instances/$inst.tsp" --rvnd-mode candidate-dlb
                                --cand-k 12 --iils 300) ;;
            esac
            taskset -c "$CORE" "${cmd[@]}" "${COMMON[@]}" --seed "$seed" > "$f.tmp"
            mv "$f.tmp" "$f"
        done
    done
done
echo "=== done $(date '+%F %T')"
