#ifndef __SOLUTION__
#define __SOLUTION__

#include <bits/stdc++.h>
using namespace std;

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
    int fEvaluationValue;

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

    inline int getT(int i, int j) const { return (int)(P[j] - P[i]); }

    inline int getC(int i, int j) const {
        return (int)((SP[j] - SP[i]) - (long long)(j - i) * P[i]);
    }

    inline int getCr(int i, int j) const {
        return (int)((long long)(j - i + 1) * P[j] - (SP[j] - SP[i] + P[i]));
    }
};

#endif