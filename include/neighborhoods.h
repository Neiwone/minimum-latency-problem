#ifndef __NEIGHBORHOODS__
#define __NEIGHBORHOODS__

#include "solution.h"

void neighborhood_swap(Solution& sol);
void neighborhood_reinsertion(Solution& sol);
void neighborhood_2opt(Solution& sol);
void neighborhood_oropt2(Solution& sol);
void neighborhood_oropt3(Solution& sol);

/* H12a: Or-opt generalized to segment lengths beyond 3 -- the paper's 5
   neighborhoods only relocate segments of length 1 (reinsertion), 2
   (oropt2) and 3 (oropt3). A read-only diagnostic (docs/experiments/
   h12-extended-oropt.md) found real, non-trivial improving moves of
   length 4-10 surviving standard RVND convergence in most trials, unlike
   H9/H10 which found near-zero opportunity. evaluateOrOpt(i,j,k) already
   supports any segment length; these just call it with longer segments. */
void neighborhood_oropt4(Solution& sol);
void neighborhood_oropt5(Solution& sol);
void neighborhood_oropt6(Solution& sol);
void neighborhood_oropt8(Solution& sol);
void neighborhood_oropt10(Solution& sol);

/* H12b: genuine 3-opt (reverse two disjoint segments independently,
   keeping their order -- see Solution::evaluateThreeOptDoubleReversal). */
void neighborhood_3opt_double_reversal(Solution& sol);

/* Multi-improvement variants (H4): same evaluate*() calls and same final
   local-optimum semantics as the functions above, but instead of applying
   the first improving move found and recomputing T/C/Cr immediately, scan
   the whole neighborhood first, then apply every move whose position
   footprint doesn't overlap another chosen move's, and recompute once per
   batch. See docs/experiments/h4-multi-improvement.md. */
void neighborhood_swap_multi(Solution& sol);
void neighborhood_reinsertion_multi(Solution& sol);
void neighborhood_2opt_multi(Solution& sol);
void neighborhood_oropt2_multi(Solution& sol);
void neighborhood_oropt3_multi(Solution& sol);

#endif
