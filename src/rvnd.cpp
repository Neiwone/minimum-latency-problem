#include "rvnd.h"
#include "neighborhoods.h"
#include <vector>
#include <algorithm>

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

void RVND_Multi(Solution& sol, mt19937& gen) {
    using NeighborhoodFn = void (*)(Solution&);
    vector<NeighborhoodFn> allNeighborhoods = {
        neighborhood_swap_multi,
        neighborhood_2opt_multi,
        neighborhood_reinsertion_multi,
        neighborhood_oropt2_multi,
        neighborhood_oropt3_multi,
    };

    vector<int> NL;
    for (int i = 0; i < (int)allNeighborhoods.size(); i++)
        NL.push_back(i);

    while (!NL.empty()) {
        uniform_int_distribution<int> dist(0, (int)NL.size() - 1);
        int idx = dist(gen);
        int eta = NL[idx];

        int oldCost = sol.fEvaluationValue;
        allNeighborhoods[eta](sol);

        if (sol.fEvaluationValue < oldCost) {
            NL.clear();
            for (int i = 0; i < (int)allNeighborhoods.size(); i++)
                NL.push_back(i);
        } else {
            NL.erase(NL.begin() + idx);
        }
    }
}

void RVND_ExtendedOrOpt(Solution& sol, mt19937& gen) {
    using NeighborhoodFn = void (*)(Solution&);
    vector<NeighborhoodFn> allNeighborhoods = {
        neighborhood_swap,
        neighborhood_2opt,
        neighborhood_reinsertion,
        neighborhood_oropt2,
        neighborhood_oropt3,
        neighborhood_oropt4,
        neighborhood_oropt5,
        neighborhood_oropt6,
    };

    vector<int> NL;
    for (int i = 0; i < (int)allNeighborhoods.size(); i++)
        NL.push_back(i);

    while (!NL.empty()) {
        uniform_int_distribution<int> dist(0, (int)NL.size() - 1);
        int idx = dist(gen);
        int eta = NL[idx];

        int oldCost = sol.fEvaluationValue;
        allNeighborhoods[eta](sol);

        if (sol.fEvaluationValue < oldCost) {
            NL.clear();
            for (int i = 0; i < (int)allNeighborhoods.size(); i++)
                NL.push_back(i);
        } else {
            NL.erase(NL.begin() + idx);
        }
    }
}

void RVND_ExtendedOrOptWide(Solution& sol, mt19937& gen) {
    using NeighborhoodFn = void (*)(Solution&);
    vector<NeighborhoodFn> allNeighborhoods = {
        neighborhood_swap,
        neighborhood_2opt,
        neighborhood_reinsertion,
        neighborhood_oropt2,
        neighborhood_oropt3,
        neighborhood_oropt4,
        neighborhood_oropt5,
        neighborhood_oropt6,
        neighborhood_oropt8,
        neighborhood_oropt10,
    };

    vector<int> NL;
    for (int i = 0; i < (int)allNeighborhoods.size(); i++)
        NL.push_back(i);

    while (!NL.empty()) {
        uniform_int_distribution<int> dist(0, (int)NL.size() - 1);
        int idx = dist(gen);
        int eta = NL[idx];

        int oldCost = sol.fEvaluationValue;
        allNeighborhoods[eta](sol);

        if (sol.fEvaluationValue < oldCost) {
            NL.clear();
            for (int i = 0; i < (int)allNeighborhoods.size(); i++)
                NL.push_back(i);
        } else {
            NL.erase(NL.begin() + idx);
        }
    }
}

void RVND_Tabu(Solution& sol, mt19937& gen, int tenure) {
    // RVND_Tabu is currently not optimized and we just fix it to compile
    using NeighborhoodFn = void (*)(Solution&);
    vector<NeighborhoodFn> allNeighborhoods = {
        neighborhood_swap,
        neighborhood_2opt,
        neighborhood_reinsertion,
        neighborhood_oropt2,
        neighborhood_oropt3,
    };

    vector<int> NL;
    for (int i = 0; i < (int)allNeighborhoods.size(); i++)
        NL.push_back(i);

    while (!NL.empty()) {
        uniform_int_distribution<int> dist(0, (int)NL.size() - 1);
        int idx = dist(gen);
        int eta = NL[idx];

        int oldCost = sol.fEvaluationValue;
        allNeighborhoods[eta](sol);

        if (sol.fEvaluationValue < oldCost) {
            NL.clear();
            for (int i = 0; i < (int)allNeighborhoods.size(); i++)
                NL.push_back(i);
        } else {
            NL.erase(NL.begin() + idx);
        }
    }
}
