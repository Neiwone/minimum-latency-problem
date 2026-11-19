#!/usr/bin/env bash
# Circuit set of Santana et al. (2019), Table 1, at equal time: our MDM-GILS-RVND
# under the paper's stopping rule (I_max = 10, I_ILS = min(100, n)), then the
# proposal with the MDM mean time on that instance as its limit. Instance by
# instance, smallest first, one run at a time on one core, so the table fills in
# as it goes. Every finished run is saved; rerunning resumes, and stopping loses
# only the run in progress.
#
#   nohup setsid scripts/run_circuit_equal_time.sh >> results/literature/circuit_equal_time.log 2>&1 &
set -euo pipefail
cd "$(dirname "$0")/.."
CORE=${CORE:-2}
MDM=results/literature/circuit_mdm.json
PROP=results/literature/circuit_mdm_budget.json
for inst in $(PYTHONPATH=scripts python3 -c "from mdm_paper_compare import PAPER; print(*PAPER)"); do
    echo "=== $inst $(date '+%F %T')"
    python3 scripts/literature_compare.py --suite circuit --method mdm_gils_rvnd_paper \
        --instances "$inst" --out "$MDM" --cores "$CORE" --no-report
    python3 scripts/literature_compare.py --suite circuit --cap 100000 --budget-from "$MDM" \
        --instances "$inst" --out "$PROP" --cores "$CORE" --no-report
done
echo "=== done $(date '+%F %T')"
