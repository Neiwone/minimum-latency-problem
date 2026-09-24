#include <bits/stdc++.h>
#include "solution.h"
#include "evaluator.h"
#include "rvnd.h"

using namespace std;

bool parse_route_string(const string& s, Solution& sol) {
    vector<int> vals;
    string token;
    stringstream ss(s);

    while (getline(ss, token, ',')) {
        if (token.empty()) continue;
        vals.push_back(stoi(token));
    }

    if ((int)vals.size() != sol.fN) {
        cerr << "Route size mismatch\n";
        return false;
    }

    vector<bool> used(sol.fN, false);
    for (int i = 0; i < sol.fN; i++) {
        int v = vals[i];
        if (v < 0 || v >= sol.fN || used[v]) {
            cerr << "Invalid route value\n";
            return false;
        }
        sol.fTour[i] = v;
        used[v] = true;
    }

    return true;
}


int main(int argc, char** argv) {
    if (argc < 2) {
        cerr << "Usage:\n";
        cerr << "  ./local_search <instance.tsp>\n";
        cerr << "  ./local_search <instance.tsp> --route 0,3,2,5,...\n";
        cerr << "    [--rvnd-mode MODE] [--seed N]\n";
        return 1;
    }

    string instanceFile = argv[1];
    string routeArg = "";
    string rvndMode = "single";
    long seed = -1;

    for (int i = 2; i < argc; i++) {
        string a = argv[i];
        if (a == "--route" && i + 1 < argc) {
            routeArg = argv[++i];
        }
        else if (a == "--seed" && i + 1 < argc) {
            seed = stol(argv[++i]);
        }
        else if (a == "--rvnd-mode" && i + 1 < argc) {
            rvndMode = argv[++i];
            if (rvndMode != "single" && rvndMode != "multi" && rvndMode != "extended-oropt"
                && rvndMode != "extended-oropt-wide" && rvndMode != "extended-oropt-3opt") {
                cerr << "Unknown --rvnd-mode: " << rvndMode << "\n";
                return 1;
            }
        }
    }

    string filepath = instanceFile;
    if (instanceFile.find('/') == string::npos) {
        filepath = "instances/" + instanceFile;
    }

    Evaluator eval;
    eval.SetInstance((char*)filepath.c_str());

    Solution sol;
    sol.Define(eval.Ncity);
    sol.fDist = eval.fEdgeDis;

    if (!routeArg.empty()) {
        if (!parse_route_string(routeArg, sol)) {
            return 1;
        }
    }
    else {
        for (int i = 0; i < sol.fN; ++i)
            sol.fTour[i] = i;
    }

    sol.calculateStructures();

    mt19937 gen(seed >= 0 ? (unsigned long)seed : random_device{}());

    using Clock = chrono::high_resolution_clock;

    auto t0 = Clock::now();

    if (rvndMode == "multi") RVND_Multi(sol, gen);
    else if (rvndMode == "extended-oropt") RVND_ExtendedOrOpt(sol, gen);
    else if (rvndMode == "extended-oropt-wide") RVND_ExtendedOrOptWide(sol, gen);
    else if (rvndMode == "extended-oropt-3opt") RVND_ExtendedOrOpt3Opt(sol, gen);
    else RVND(sol, gen);

    auto t1 = Clock::now();

    double runtime_ms = chrono::duration<double, milli>(t1 - t0).count();

    cout << "INSTANCE " << instanceFile << "\n";
    cout << "NODES " << sol.fN << "\n";
    cout << "COST " << sol.fEvaluationValue << "\n";
    cout << "TIME_MS " << fixed << setprecision(3) << runtime_ms << "\n";
    cout << "ROUTE ";
    for (int i = 0; i < sol.fN; i++) {
        cout << sol.fTour[i] << ",\n"[i == sol.fN - 1];
    }

    return 0;
}
