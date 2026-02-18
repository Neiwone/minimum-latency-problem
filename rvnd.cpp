#include "rvnd.h"
#include "neighborhoods.h"
#include <vector>

using namespace std;

void RVND(Solution& sol, mt19937& gen) {
    using NeighborhoodFn = void (*)(Solution&);
    vector<NeighborhoodFn> allNeighborhoods = {
        neighborhood_swap,
        neighborhood_2opt,
        neighborhood_reinsertion,
        neighborhood_oropt2,
        neighborhood_oropt3,
    };

    // Initialize the Neighborhood List NL;
    vector<int> NL;
    for (int i = 0; i < (int)allNeighborhoods.size(); i++)
        NL.push_back(i);

    while (!NL.empty()) {
        uniform_int_distribution<int> dist(0, (int)NL.size() - 1);
        int idx = dist(gen);

        // get a random neighborhood from the list
        int eta = NL[idx];

        int oldCost = sol.fEvaluationValue;

        // Find the best neighbor of s in neighborhood eta
        // apply the neighborhood move if better
        // update optimization data structures if better
        allNeighborhoods[eta](sol);

        // if the move was an improvement, reinitialize the neighborhood list
        if (sol.fEvaluationValue < oldCost) {
            NL.clear();
            for (int i = 0; i < (int)allNeighborhoods.size(); i++)
                NL.push_back(i);
        } else {
        // remove the neighborhood from the list
            NL.erase(NL.begin() + idx);
        }
    }
}
