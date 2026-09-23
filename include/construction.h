#ifndef __CONSTRUCTION__
#define __CONSTRUCTION__

#include "solution.h"
#include "evaluator.h"
#include <random>

void construction(Solution& sol, Evaluator& eval, double alpha, std::mt19937& gen);

/* H6: same RCL/alpha, but scores a candidate by a k-step greedy rollout
   instead of just dist(r,c). */
void construction_lookahead(Solution& sol, Evaluator& eval, double alpha, int k, std::mt19937& gen);

#endif
