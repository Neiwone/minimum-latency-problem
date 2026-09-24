#ifndef __SOLUTION__
#define __SOLUTION__

#include <bits/stdc++.h>
using namespace std;

// Latency overflows int32 around n=4500 (fnl4461 reported INT_MIN), and the
// wrap is silent: the search then hunts tours that wrap most negative.
typedef long long Cost;

// MLP is a Hamiltonian path: the return to the depot is not paid. Turning this
// on adds the arrival back at the depot as one more term of the sum.
void set_closed_tour(bool on);
bool closed_tour();

class Solution {
public:
    Solution();
    ~Solution();
    void Define(int N);
    Solution(const Solution& src);
    Solution& operator = (const Solution& src);
    bool operator == (const Solution& other);

    void calculateStructures();

    /* Same, from position `lo` on: nothing below the first position a
       move disturbed changes. lo <= 0 rebuilds everything. */
    void calculateStructuresFrom(int lo);

    /* W(i,j) = number of customers in subsequence [i..j].
       Depot is always at position 0 */
    inline int getW(int i, int j) const {
        return (i == 0) ? j : (j - i + 1);
    }

    void printAllSubsequences();

    bool evaluateSwap(int i, int j);
    bool evaluate2Opt(int i, int j);
    bool evaluateReinsertion(int i, int j);
    bool evaluateOrOpt(int i, int j, int k);

    /* Same as evaluateOrOpt with [i..j] REVERSED -- under a latency
       objective a different move */
    bool evaluateOrOptReversed(int i, int j, int k);

    /* H12b: cuts i<j<k give A|B|C|D -> A + rev(B) + rev(C) + D. The one
       3-opt reconnection no single existing move reaches. */
    bool evaluateThreeOptDoubleReversal(int i, int j, int k);
    
    int fN;
    int* fTour;
    Cost fEvaluationValue;

    double* x;
    double* y; 
    int** fDist;

    /* P[j] = edge lengths up to position j, SP = prefix sum of P. Every
       entry of the old O(n^2) T/C/Cr tables is O(1) on them (see below). */
    long long* P;
    long long* SP;

    /* posOf[city] = its position in fTour. Candidate-list scans need to
       go from "c is geometrically near d" to "where is d in the tour". */
    int* posOf;

    /* Cost of closing the tour, given a candidate walk and its last city. */
    inline Cost closingTerm(Cost walk, int lastCity) const {
        return walk + fDist[lastCity][fTour[0]];
    }

    inline Cost getT(int i, int j) const { return P[j] - P[i]; }

    inline Cost getC(int i, int j) const {
        return (SP[j] - SP[i]) - (Cost)(j - i) * P[i];
    }

    inline Cost getCr(int i, int j) const {
        return (Cost)(j - i + 1) * P[j] - (SP[j] - SP[i] + P[i]);
    }
};

#endif