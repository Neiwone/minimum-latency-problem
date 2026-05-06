#include <bits/stdc++.h>
#include "solution.h"
#include "evaluator.h"

using namespace std;

void nearest_neighbour(Solution& sol, Evaluator& eval, int depot = 0) {
    int n = eval.Ncity;
    
    // Initialize all vertices as unvisited
    vector<bool> visited(n, false);
    vector<int> route;

    // Select depot as starting point
    int current = depot;
    visited[current] = true;
    route.push_back(current);

    // Build route by always visiting nearest unvisited city
    while ((int)route.size() < n) {
        // Find nearest unvisited city
        int next = -1;
        int min_dist = INT_MAX;
        
        for (int i = 0; i < n; i++) {
            if (!visited[i] && eval.fEdgeDis[current][i] < min_dist) {
                next = i;
                min_dist = eval.fEdgeDis[current][i];
            }
        }

        current = next;
        visited[current] = true;
        route.push_back(current);
    }

    // Store route in solution
    sol.Define(n);
    for (int i = 0; i < n; i++) {
        sol.fTour[i] = route[i];
    }
}


int main(int argc, char** argv) {
    if (argc < 2) {
        cerr << "Usage: ./nearest_neighbour <instance.tsp>\n";
        return 1;
    }

    string filename = argv[1];
    
    string filepath = filename;
    if (filename.find('/') == string::npos) {
        filepath = "instances/" + filename;
    }

    Evaluator eval;
    eval.SetInstance((char*)filepath.c_str());
    
    Solution sol;

    using Clock = chrono::high_resolution_clock;

    auto t0 = Clock::now();

    nearest_neighbour(sol, eval, 0);
    eval.DoIt(sol);

    auto t1 = Clock::now();

    double runtime_ms = chrono::duration<double, milli>(t1 - t0).count();

    cout << "INSTANCE " << filename << "\n";
    cout << "NODES " << sol.fN << "\n";
    cout << "COST " << sol.fEvaluationValue << "\n";
    cout << "TIME_MS " << fixed << setprecision(3) << runtime_ms << "\n";
    cout << "ROUTE ";
    for (int i = 0; i < sol.fN; i++) {
        cout << sol.fTour[i] << ",\n"[i == sol.fN - 1];
    }

    return 0;
}
