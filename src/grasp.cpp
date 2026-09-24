#include <bits/stdc++.h>
#include "solution.h"
#include "evaluator.h"
#include "construction.h"
#include "rvnd.h"

using namespace std;

struct StepTimings {
    double construction_ms = 0;
    double rvnd_ms = 0;
    double total_ms = 0;
};

void grasp(
    Solution& bestSol,
    Evaluator& eval,
    int maxIter,
    optional<double> fixedAlpha,
    bool verbose,
    StepTimings* timings
) {
    random_device rd;
    mt19937 gen(rd());
    using Clock = chrono::high_resolution_clock;

    vector<double> R;
    for (double r = 0.00; r <= 0.25; r += 0.01)
        R.push_back(r);

    int bestIter = -1;
    Cost bestCost = LLONG_MAX;
    double totalConstructionMs = 0.0;
    double totalRvndMs = 0.0;

    for (int iter = 0; iter < maxIter; iter++) {
        double alpha = 0.0;
        if (!fixedAlpha.has_value() && iter == 0) {
            // First iteration is deterministic greedy to guarantee a strong baseline.
            alpha = 0.0;
        } else if (fixedAlpha.has_value()) {
            alpha = fixedAlpha.value();
        } else {
            uniform_int_distribution<int> rDist(0, (int)R.size() - 1);
            alpha = R[rDist(gen)];
        }

        auto tc0 = Clock::now();
        Solution s;
        construction(s, eval, alpha, gen);
        auto tc1 = Clock::now();
        double constructionMs = chrono::duration<double, milli>(tc1 - tc0).count();
        totalConstructionMs += constructionMs;

        auto tr0 = Clock::now();
        RVND(s, gen);
        auto tr1 = Clock::now();
        double rvndMs = chrono::duration<double, milli>(tr1 - tr0).count();
        totalRvndMs += rvndMs;

        if (verbose) {
            cerr << "  iter " << iter
                 << ": alpha=" << fixed << setprecision(2) << alpha
                 << "  constr=" << setprecision(1) << constructionMs << "ms"
                 << "  rvnd=" << rvndMs << "ms"
                 << "  cost=" << s.fEvaluationValue << "\n";
        }

        if (s.fEvaluationValue < bestCost) {
            bestCost = s.fEvaluationValue;
            bestSol = s;
            bestIter = iter;
        }
    }

    if (timings) {
        timings->construction_ms = totalConstructionMs;
        timings->rvnd_ms = totalRvndMs;
    }

    if (verbose) {
        cerr << "best at iter " << bestIter << " cost=" << bestCost << "\n";
    }
}

int main(int argc, char** argv) {
    if (argc < 2) {
        cerr << "Usage:\n";
        cerr << "  ./grasp <instance.tsp> [--iter 50] [--alpha 0.15] [-v]\n";
        return 1;
    }

    string instanceFile = argv[1];
    int maxIter = 50;
    optional<double> alpha;
    bool verbose = false;

    for (int i = 2; i < argc; i++) {
        string a = argv[i];
        if ((a == "--iter" || a == "--imax") && i + 1 < argc) {
            maxIter = stoi(argv[++i]);
        } else if (a == "--alpha" && i + 1 < argc) {
            alpha = stod(argv[++i]);
        } else if (a == "--verbose" || a == "-v") {
            verbose = true;
        }
    }

    string filepath = instanceFile;
    if (instanceFile.find('/') == string::npos)
        filepath = "instances/" + instanceFile;

    Evaluator eval;
    eval.SetInstance((char*)filepath.c_str());

    Solution bestSol;
    StepTimings timings;

    using Clock = chrono::high_resolution_clock;
    auto t0 = Clock::now();

    grasp(bestSol, eval, maxIter, alpha, verbose, &timings);

    auto t1 = Clock::now();
    double runtimeMs = chrono::duration<double, milli>(t1 - t0).count();
    timings.total_ms = runtimeMs;

    cout << "INSTANCE " << instanceFile << "\n";
    cout << "NODES " << bestSol.fN << "\n";
    cout << "COST " << bestSol.fEvaluationValue << "\n";
    cout << "ITER " << maxIter << "\n";
    if (alpha.has_value())
        cout << "ALPHA " << fixed << setprecision(2) << alpha.value() << "\n";
    else
        cout << "ALPHA randomized(0.00..0.25)\n";
    cout << "TIME_MS " << fixed << setprecision(3) << runtimeMs << "\n";
    cout << "CONSTRUCTION_MS " << fixed << setprecision(3) << timings.construction_ms << "\n";
    cout << "RVND_MS " << fixed << setprecision(3) << timings.rvnd_ms << "\n";
    cout << "ROUTE ";
    for (int i = 0; i < bestSol.fN; i++)
        cout << bestSol.fTour[i] << ",\n"[i == bestSol.fN - 1];

    return 0;
}