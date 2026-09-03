/* NOTE: "fpmax.h" must be the FIRST include here. fp_tree.h (pulled in by
   it) declares a global `class stack` and also does `using namespace std;`,
   so if <stack> has already been included (which <bits/stdc++.h> does),
   the unqualified `stack` in fpmax.h becomes ambiguous and the build
   fails. Including it first, in this isolated translation unit, keeps the
   vendored sources unmodified and the collision contained. */
#include "fpmax.h"

#include "fpmax_mining.h"

#include <algorithm>
#include <list>
#include <set>

std::vector<std::vector<int>> fpmax_mine_arc_paths(
    const std::vector<std::vector<int>>& tours,
    int n,
    double supMinFrac,
    int maxPatterns) {

    std::vector<std::vector<int>> result;

    const int d = (int)tours.size();
    if (d == 0 || n <= 0) return result;

    /* Each tour becomes a transaction of its arcs, an arc (u,v) being the
       item u*n + v (convention of the reference integration, so decoding
       is u = item / n, v = item % n). */
    Dataset dataset;
    for (const std::vector<int>& tour : tours) {
        std::set<int> transaction;
        for (size_t i = 0; i + 1 < tour.size(); i++)
            transaction.insert(tour[i] * n + tour[i + 1]);
        if (!transaction.empty()) dataset.push_back(transaction);
    }

    /* The library takes an ABSOLUTE minimum support. */
    int minsup = std::max(2, (int)(supMinFrac * (double)d));
    if ((int)dataset.size() < minsup) return result;

    FISet* itemsets = fpmax(&dataset, (unsigned int)minsup,
                            (unsigned int)std::max(0, maxPatterns));
    if (!itemsets) return result;

    std::set<std::vector<int>> seen;

    for (FISet::iterator it = itemsets->begin(); it != itemsets->end(); ++it) {
        /* Chain the itemset's arcs into maximal paths: each new arc (u,v)
           either extends one end of an open path, bridges two of them, or
           starts a new one. */
        std::list<std::vector<int>*> paths;

        for (std::set<int>::iterator a = it->begin(); a != it->end(); ++a) {
            const int u = *a / n;
            const int v = *a % n;

            std::vector<int>* lhs = nullptr; /* path ending at u */
            std::vector<int>* rhs = nullptr; /* path starting at v */
            for (std::vector<int>* p : paths) {
                if (p->back() == u) lhs = p;
                else if (p->front() == v) rhs = p;
            }

            if (lhs && rhs && lhs != rhs) {
                lhs->insert(lhs->end(), rhs->begin(), rhs->end());
                paths.remove(rhs);
                delete rhs;
            } else if (lhs) {
                lhs->push_back(v);
            } else if (rhs) {
                rhs->insert(rhs->begin(), u);
            } else {
                paths.push_back(new std::vector<int>{u, v});
            }
        }

        for (std::vector<int>* p : paths) {
            if (p->size() >= 2 && seen.insert(*p).second)
                result.push_back(*p);
            delete p;
        }
    }

    delete itemsets;

    std::sort(result.begin(), result.end(),
              [](const std::vector<int>& a, const std::vector<int>& b) {
                  return a.size() > b.size();
              });
    if (maxPatterns > 0 && (int)result.size() > maxPatterns)
        result.resize(maxPatterns);

    return result;
}
