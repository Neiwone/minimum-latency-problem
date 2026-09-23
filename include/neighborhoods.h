#ifndef __NEIGHBORHOODS__
#define __NEIGHBORHOODS__

#include "solution.h"

void neighborhood_swap(Solution& sol);
void neighborhood_reinsertion(Solution& sol);
void neighborhood_2opt(Solution& sol);
void neighborhood_oropt2(Solution& sol);
void neighborhood_oropt3(Solution& sol);

/* H12a: or-opt past the paper's length 3. Improving moves of length 4-10
   do survive standard RVND convergence. */
void neighborhood_oropt4(Solution& sol);
void neighborhood_oropt5(Solution& sol);
void neighborhood_oropt6(Solution& sol);
void neighborhood_oropt8(Solution& sol);
void neighborhood_oropt10(Solution& sol);

/* Same scan with the length chosen at runtime (>=2), for the adaptive
   RVND that learns which lengths to scan. */
void neighborhood_oropt_len(Solution& sol, int segLen);

/* H16: or-opt inserting the segment REVERSED (segLen >= 2) -- standard in
   vehicle routing, absent from the MLP papers this follows. */
void neighborhood_oropt_rev_len(Solution& sol, int segLen);
void neighborhood_oropt_rev2(Solution& sol);
void neighborhood_oropt_rev3(Solution& sol);
void neighborhood_oropt_rev4(Solution& sol);
void neighborhood_oropt_rev5(Solution& sol);
void neighborhood_oropt_rev6(Solution& sol);

/* H12b: genuine 3-opt (reverse two disjoint segments independently,
   keeping their order -- see Solution::evaluateThreeOptDoubleReversal). */
void neighborhood_3opt_double_reversal(Solution& sol);

/* H4: scan the whole neighborhood first, then apply every improving move
   whose positions do not overlap another's, recomputing once per batch. */
void neighborhood_swap_multi(Solution& sol);
void neighborhood_reinsertion_multi(Solution& sol);
void neighborhood_2opt_multi(Solution& sol);
void neighborhood_oropt2_multi(Solution& sol);
void neighborhood_oropt3_multi(Solution& sol);

#endif
