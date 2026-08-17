#ifndef __CONSTRUCTION__
#define __CONSTRUCTION__

#include "solution.h"
#include "evaluator.h"
#include <random>

void construction(Solution& sol, Evaluator& eval, double alpha, std::mt19937& gen);

/* H6: same greedy-randomized RCL/alpha mechanism as construction(), but
   scores each candidate c by the cumulative cost of a hypothetical k-step
   greedy rollout r -> c -> (k-1 more nearest-unvisited hops), instead of
   just dist(r,c). See docs/experiments/h6-lookahead-construction.md. */
void construction_lookahead(Solution& sol, Evaluator& eval, double alpha, int k, std::mt19937& gen);

#endif
