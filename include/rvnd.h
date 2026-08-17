#ifndef __RVND__
#define __RVND__

#include "solution.h"
#include <random>

void RVND(Solution& sol, std::mt19937& gen);
void RVND_Tabu(Solution& sol, std::mt19937& gen, int tenure);

/* H4: same RVND control flow, but calls the neighborhood_*_multi variants
   (multi-improvement per scan instead of first-improvement). */
void RVND_Multi(Solution& sol, std::mt19937& gen);

/* H12a: same RVND control flow as RVND(), plus oropt4/5/6 in the
   neighborhood list (segment lengths beyond the paper's original 3). */
void RVND_ExtendedOrOpt(Solution& sol, std::mt19937& gen);

/* H12a follow-up: same idea, wider -- adds oropt8/oropt10 on top of
   ExtendedOrOpt's oropt4/5/6 (10 neighborhoods total). Tests whether the
   real quality gain found with lengths up to 6 keeps growing with longer
   segments, or plateaus/stops paying for its extra time cost. */
void RVND_ExtendedOrOptWide(Solution& sol, std::mt19937& gen);

#endif
