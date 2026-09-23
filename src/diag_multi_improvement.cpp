#include <bits/stdc++.h>
#include "solution.h"
#include "evaluator.h"
#include "construction.h"
#include "rvnd.h"

using namespace std;

/* Read-only probe for H4: how many improving moves of one scan have disjoint
   footprints, i.e. could be batched into a single pass? */

void double_bridge_once(Solution& sol, mt19937& gen) {
    int n = sol.fN;
    if (n < 8) return;

    vector<int> cuts;
    uniform_int_distribution<int> dist(1, n - 2);
    while ((int)cuts.size() < 3) {
        int c = dist(gen);
        bool dup = false;
        for (int x : cuts) if (x == c) { dup = true; break; }
        if (!dup) cuts.push_back(c);
    }
    sort(cuts.begin(), cuts.end());
    int p1 = cuts[0], p2 = cuts[1], p3 = cuts[2];

    vector<int> newTour;
    newTour.reserve(n);
    for (int i = 0;  i < p1; i++) newTour.push_back(sol.fTour[i]);
    for (int i = p2; i < p3; i++) newTour.push_back(sol.fTour[i]);
    for (int i = p1; i < p2; i++) newTour.push_back(sol.fTour[i]);
    for (int i = p3; i < n;  i++) newTour.push_back(sol.fTour[i]);
    for (int i = 0; i < n; i++) sol.fTour[i] = newTour[i];
    sol.calculateStructures();
}

struct Interval { int lo, hi; };

/* Greedy activity selection. The 1-position buffer is required: evaluate*()
   prices a boundary edge just outside its own footprint. */
int max_disjoint_count(vector<Interval> ivs) {
    sort(ivs.begin(), ivs.end(), [](const Interval& a, const Interval& b) {
        return a.hi < b.hi;
    });
    int count = 0;
    int lastEnd = -2; // so an interval starting at position 0 is still accepted first
    for (const auto& iv : ivs) {
        if (iv.lo > lastEnd + 1) {
            count++;
            lastEnd = iv.hi;
        }
    }
    return count;
}

struct ScanResult { int total; int maxDisjoint; };

ScanResult scan_swap(Solution& sol) {
    vector<Interval> ivs;
    for (int i = 1; i < sol.fN; i++)
        for (int j = i + 1; j < sol.fN; j++)
            if (sol.evaluateSwap(i, j)) ivs.push_back({i, j});
    return {(int)ivs.size(), max_disjoint_count(ivs)};
}

ScanResult scan_2opt(Solution& sol) {
    vector<Interval> ivs;
    for (int i = 1; i < sol.fN; i++)
        for (int j = i + 1; j < sol.fN; j++)
            if (sol.evaluate2Opt(i, j)) ivs.push_back({i, j});
    return {(int)ivs.size(), max_disjoint_count(ivs)};
}

ScanResult scan_reinsertion(Solution& sol) {
    vector<Interval> ivs;
    for (int i = 1; i < sol.fN; i++)
        for (int j = 1; j < sol.fN; j++) {
            if (i == j) continue;
            if (sol.evaluateReinsertion(i, j))
                ivs.push_back({min(i, j), max(i, j)});
        }
    return {(int)ivs.size(), max_disjoint_count(ivs)};
}

ScanResult scan_oropt2(Solution& sol) {
    vector<Interval> ivs;
    for (int i = 1; i < sol.fN - 1; i++)
        for (int k = 0; k < sol.fN; k++) {
            if (k >= i && k <= i + 1) continue;
            if (sol.evaluateOrOpt(i, i + 1, k))
                ivs.push_back({min(i, k), max(i + 1, k)});
        }
    return {(int)ivs.size(), max_disjoint_count(ivs)};
}

ScanResult scan_oropt3(Solution& sol) {
    vector<Interval> ivs;
    for (int i = 1; i < sol.fN - 2; i++)
        for (int k = 0; k < sol.fN; k++) {
            if (k >= i && k <= i + 2) continue;
            if (sol.evaluateOrOpt(i, i + 2, k))
                ivs.push_back({min(i, k), max(i + 2, k)});
        }
    return {(int)ivs.size(), max_disjoint_count(ivs)};
}

void report(const string& label, const string& neigh, const ScanResult& r) {
    cout << label << " " << neigh << " total=" << r.total
         << " max_disjoint=" << r.maxDisjoint << "\n";
}

void scan_all(const string& label, Solution& sol) {
    // Each scan_* call only reads T/C/Cr and fTour -- no mutation.
    report(label, "swap", scan_swap(sol));
    report(label, "2opt", scan_2opt(sol));
    report(label, "reinsertion", scan_reinsertion(sol));
    report(label, "oropt2", scan_oropt2(sol));
    report(label, "oropt3", scan_oropt3(sol));
}

int main(int argc, char** argv) {
    if (argc < 2) {
        cerr << "Usage: ./diag_multi_improvement <instance.tsp> [--seed N] [--trials T]\n";
        return 1;
    }

    string instanceFile = argv[1];
    long seed = -1;
    int trials = 3;

    for (int i = 2; i < argc; i++) {
        string a = argv[i];
        if (a == "--seed" && i + 1 < argc) seed = stol(argv[++i]);
        else if (a == "--trials" && i + 1 < argc) trials = stoi(argv[++i]);
    }

    string filepath = instanceFile;
    if (instanceFile.find('/') == string::npos)
        filepath = "instances/" + instanceFile;

    Evaluator eval;
    eval.SetInstance((char*)filepath.c_str());

    mt19937 gen(seed >= 0 ? (unsigned long)seed : random_device{}());

    for (int t = 0; t < trials; t++) {
        Solution fresh;
        construction(fresh, eval, 0.15, gen);
        scan_all("FRESH", fresh);

        Solution converged(fresh);
        RVND(converged, gen);

        Solution perturbed(converged);
        double_bridge_once(perturbed, gen);
        scan_all("PERTURBED", perturbed);
    }

    return 0;
}
