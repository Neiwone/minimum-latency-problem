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

    for (int i = 2; i < argc; i++) {
        string a = argv[i];
        if (a == "--alpha" && i + 1 < argc) {
            alpha = stod(argv[++i]);
        }
    }

    string filepath = instanceFile;
    if (instanceFile.find('/') == string::npos) {
        filepath = "instances/" + instanceFile;
    }

    Evaluator eval;
    eval.SetInstance((char*)filepath.c_str());

    Solution sol;

    random_device rd;
    mt19937 gen(rd());

    using Clock = chrono::high_resolution_clock;

    auto t0 = Clock::now();

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
