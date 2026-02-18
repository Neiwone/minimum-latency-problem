#include "construction.h"
#include <algorithm>

using namespace std;

void construction(Solution& sol, Evaluator& eval, double alpha, mt19937& gen) {
    int n = eval.Ncity;

    vector<int> CL;
    for (int i = 1; i < n; i++)
        CL.push_back(i);

    vector<int> route;
    route.push_back(0);

    int r = 0;

    while (!CL.empty()) {
        sort(CL.begin(), CL.end(), [&](int a, int b) {
            return eval.fEdgeDis[r][a] < eval.fEdgeDis[r][b];
        });

        int rclSize = max(1, (int)(alpha * CL.size()));
        uniform_int_distribution<int> dist(0, rclSize - 1);

        int idx = dist(gen);
        int c = CL[idx];

        route.push_back(c);
        r = c;

        CL.erase(CL.begin() + idx);
    }

    sol.Define(n);
    sol.fDist = eval.fEdgeDis;
    for (int i = 0; i < n; i++)
        sol.fTour[i] = route[i];

    sol.calculateStructures();
}
