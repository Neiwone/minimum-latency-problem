#ifndef __RVND__
#define __RVND__

#include "solution.h"
#include <random>

void RVND(Solution& sol, std::mt19937& gen);
void RVND_Tabu(Solution& sol, std::mt19937& gen, int tenure);

#endif
