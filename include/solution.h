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