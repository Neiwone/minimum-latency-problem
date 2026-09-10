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

    /* Same relocation as evaluateOrOpt, but the segment [i..j] is
       inserted REVERSED. The five neighborhoods of Silva et al. (2012)
       -- and every MLP paper this project reproduces -- only ever
       reinsert a segment in its original orientation, while joint
       relocate+reverse is standard in the vehicle-routing local-search
       literature. For a latency objective the two are genuinely
       different moves: reversing a relocated block changes the arrival
       time of every customer inside it, not just the two junctions, so
       this is not reachable by any composition of the existing five. */
    bool evaluateOrOptReversed(int i, int j, int k);

    /* H12b: genuine 3-opt reconnection not reachable by any single
       existing move. 3 cuts (i<j<k) split the tour into A=[0,i],
       B=[i+1,j], C=[j+1,k], D=[k+1,n-1]; this reverses B and C
       INDEPENDENTLY, keeping their order (A + rev(B) + rev(C) + D).
       Reversing the merged B+C span (which swaps their order too, giving
       rev(C)+rev(B)) is already reachable via evaluate2Opt -- this move
       is the one classic "type-7" 3-opt reconnection that isn't. See
       docs/experiments/h12-extended-oropt.md section 12. */
    bool evaluateThreeOptDoubleReversal(int i, int j, int k);
    
    int fN;
    int* fTour;
    int fEvaluationValue;

    double* x;
    double* y; 
    int** fDist;

    /* Subsequence data. The three O(n^2) matrices T/C/Cr this class used
       to materialize (rebuilt from scratch on every applied move) are
       redundant: every one of their entries is an O(1) expression on two
       O(n) prefix arrays over the tour's edge lengths. With
         P[j]  = sum of edge lengths up to position j   (P[0] = 0)
         SP[j] = P[0] + ... + P[j]
       we get, for i <= j,
         T(i,j)  = P[j] - P[i]                                (duration)
         C(i,j)  = (SP[j]-SP[i]) - (j-i)*P[i]                 (latency)
         Cr(i,j) = (j-i+1)*P[j] - (SP[j]-SP[i]+P[i])          (reversed)
       which reproduces the old matrices exactly (same recurrences:
       C(i,j)=C(i,j-1)+T(i,j), Cr(i,j)=Cr(i+1,j)+T(i,j)). This turns
       calculateStructures() from O(n^2) into O(n) and the per-Solution
       footprint from 3n^2 ints into 2n int64s -- at n=532 that is 3.4 MB
       of cache-thrashing tables replaced by 8 KB. Accessors below keep
       the old call sites honest. */
    long long* P;
    long long* SP;

    /* posOf[city] = position of that city in fTour, refreshed by
       calculateStructures(). Candidate-list scans need to go from "city
       c is geometrically near city d" to "where is d in the tour". */
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