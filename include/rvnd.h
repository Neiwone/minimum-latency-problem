#ifndef __RVND__
#define __RVND__

#include "solution.h"
#include <random>

void RVND(Solution& sol, std::mt19937& gen);
void RVND_Tabu(Solution& sol, std::mt19937& gen, int tenure);

/* H4: same control flow over the *_multi neighborhoods. */
void RVND_Multi(Solution& sol, std::mt19937& gen);

/* H12a: RVND() plus oropt4/5/6 (lengths past the paper's 3). */
void RVND_ExtendedOrOpt(Solution& sol, std::mt19937& gen);

/* Wider still: adds oropt8/oropt10 (10 neighborhoods). Tests whether the
   gain up to length 6 keeps growing or stops paying for its time. */
void RVND_ExtendedOrOptWide(Solution& sol, std::mt19937& gen);

/* H16: ExtendedOrOpt plus reversed or-opt, lengths 2-6 (13 total). */
void RVND_ExtendedOrOptRev(Solution& sol, std::mt19937& gen);

/* H12b: ExtendedOrOpt plus the 3-opt double independent reversal. */
void RVND_ExtendedOrOpt3Opt(Solution& sol, std::mt19937& gen);

#endif
