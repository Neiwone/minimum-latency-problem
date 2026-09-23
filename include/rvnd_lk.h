#ifndef __RVND_LK__
#define __RVND_LK__

#include "solution.h"
#include "evaluator.h"
#include <random>

/* H14: converge with RVND_ExtendedOrOpt, then fire random-start chains of
   2-opt reversals, reconverging while any improves. Needs fNearCity. */
void RVND_LKEscape(Solution& sol, Evaluator& eval, std::mt19937& gen);

#endif
