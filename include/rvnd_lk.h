#ifndef __RVND_LK__
#define __RVND_LK__

#include "solution.h"
#include "evaluator.h"
#include <random>

/* Sequential Lin-Kernighan-style escape, on top of RVND_ExtendedOrOpt
   (H12a's best known local search). See docs/experiments/
   h-lk-escape.md and diag_lk.cpp for the diagnostic that motivated this:
   from an RVND_ExtendedOrOpt-converged tour, a bounded-depth chain of
   sequential 2-opt-style reversals (guided by Evaluator::fNearCity, cost
   tracked exactly via T/C/Cr at every step) occasionally reaches a
   strictly better tour than any single neighborhood move can -- rare
   (roughly 1-2.5% of random starts at depth<=15/candK<=20 on TSPLIB) but
   real and growing with depth/candidate width, unlike the always-zero
   result you'd see if RVND already covered everything a sequential
   search can reach.

   RVND_LKEscape converges with RVND_ExtendedOrOpt, then repeatedly
   fires a batch of random-start LK chains; if any chain finds a
   strictly better tour, adopts it and reconverges (since new moves may
   have opened up), otherwise stops. Needs Evaluator (not just Solution)
   because the candidate lists come from Evaluator::fNearCity -- unlike
   every other RVND_* variant in rvnd.h, which only touch Solution. */
void RVND_LKEscape(Solution& sol, Evaluator& eval, std::mt19937& gen);

#endif
