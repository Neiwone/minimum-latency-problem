#include <bits/stdc++.h>
#include "construction.h"

using namespace std;

int main(int argc, char** argv) {
    if (argc < 2) {
        cerr << "Usage:\n";
        cerr << "  ./construction <instance.tsp> [--alpha 0.3]\n";
        return 1;
    }

    string instanceFile = argv[1];
    double alpha = 0.3;
    bool lookahead = false;
    int lookaheadK = 3;
    long seed = -1;

    for (int i = 2; i < argc; i++) {
        string a = argv[i];
        if (a == "--alpha" && i + 1 < argc) {
            alpha = stod(argv[++i]);
        }
        else if (a == "--construction-mode" && i + 1 < argc) {
            string m = argv[++i];
            if (m == "lookahead") lookahead = true;
            else if (m == "greedy") lookahead = false;
            else { cerr << "Unknown --construction-mode: " << m << "\n"; return 1; }
        }
        else if (a == "--lookahead-k" && i + 1 < argc) {
            lookaheadK = stoi(argv[++i]);
        }
        else if (a == "--seed" && i + 1 < argc) {
            seed = stol(argv[++i]);
        }
    }

    string filepath = instanceFile;
    if (instanceFile.find('/') == string::npos) {
        filepath = "instances/" + instanceFile;
    }

    Evaluator eval;
    eval.SetInstance((char*)filepath.c_str());

    Solution sol;

    mt19937 gen(seed >= 0 ? (unsigned long)seed : random_device{}());

    using Clock = chrono::high_resolution_clock;

    auto t0 = Clock::now();

    if (lookahead)
        construction_lookahead(sol, eval, alpha, lookaheadK, gen);
    else
        construction(sol, eval, alpha, gen);

    auto t1 = Clock::now();

    double runtime_ms = chrono::duration<double, milli>(t1 - t0).count();

    cout << "INSTANCE " << instanceFile << "\n";
    cout << "NODES " << sol.fN << "\n";
    cout << "COST " << sol.fEvaluationValue << "\n";
    cout << "ALPHA " << alpha << "\n";
    cout << "TIME_MS " << fixed << setprecision(3) << runtime_ms << "\n";
    cout << "ROUTE ";
    for (int i = 0; i < sol.fN; i++) {
        cout << sol.fTour[i] << ",\n"[i == sol.fN - 1];
    }

    return 0;
}
