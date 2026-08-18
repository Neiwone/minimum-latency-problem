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

    int** T;    /* Duration */
    int** C;    /* Latency cost */
    int** Cr;   /* Reversed cost */
};

#endif