#ifndef __NEIGHBORHOODS_CAND__
#define __NEIGHBORHOODS_CAND__

#include "solution.h"
#include "evaluator.h"
#include <random>

/* Candidate-list ("neighbor list") variants of the RVND neighborhoods.

   Every neighborhood in src/neighborhoods.cpp scans its full O(n^2)
   position space. That is what the MLP papers this project follows
   describe, but it is not what fast TSP/VRP local searches do: they only
   consider moves that create at least one edge between geometrically
   close cities, using a precomputed list of each city's K nearest
   neighbours. Evaluator already builds exactly such a list
   (fNearCity/fNearNumMax) -- until now only the Lin-Kernighan experiment
   used it.

   The pruning rule per neighborhood, in each case "the move must create
   an edge to one of the K nearest cities of the endpoint that gains a
   new neighbour":

     or-opt (forward and reversed, any segment length): the relocated
       block [i..j] must land next to a near neighbour of tour[i] or of
       tour[j].
     2-opt: reversing [i..j] creates the edge (tour[i-1], tour[j]), so
       tour[j] must be a near neighbour of tour[i-1].
     swap: tour[j] moves in between tour[i-1] and tour[i+1], so tour[j]
       must be a near neighbour of tour[i-1].

   This makes each scan O(n*K) instead of O(n^2). It is a heuristic
   restriction -- improving moves whose new edges are all long are no
   longer seen -- so it trades local-optimum depth for iteration count,
   which is the trade a fixed-time budget actually rewards. K = 0
   disables the pruning and is not the code path used here (use the
   plain neighborhoods for that). */

struct CandList {
    int   K;      /* neighbours considered per city */
    int** near;   /* near[city][t] = t-th nearest city (Evaluator::fNearCity) */
};

CandList make_candidate_list(const Evaluator& eval, int K);

/* RVND over the candidate-pruned neighborhoods: swap, 2-opt, or-opt
   forward with segment lengths 1..maxLen, and or-opt reversed with
   lengths 2..maxLen. */
void RVND_Candidate(Solution& sol, const CandList& cl, int maxLen,
                    bool useReversed, std::mt19937& gen);

#endif
