#ifndef __FPMAX_MINING__
#define __FPMAX_MINING__

#include <vector>

/* Thin wrapper around the vendored FPmax* library (external/fpmax/).

   It exists to keep the library's headers out of the rest of the project:
   fp_tree.h declares a global `class stack` AND does `using namespace
   std;`, so including "fpmax.h" in any translation unit that already
   pulled in <stack> (e.g. via <bits/stdc++.h>) makes the name `stack`
   ambiguous and fails to compile. src/fpmax_mining.cpp therefore includes
   "fpmax.h" first and in isolation, and exposes only plain STL types
   here. The vendored sources are unmodified.

   Mines maximal frequent itemsets of arcs from a set of tours and returns
   them already reassembled into node paths ("Consecutive Arc Lists"):

     tours       -- one entry per elite solution, each a full node sequence
     n           -- number of nodes (an arc (u,v) is encoded as u*n + v,
                    the same convention as the reference integration
                    MDM-HGS-CVRP)
     supMinFrac  -- minimum support as a FRACTION of the number of tours;
                    converted internally to the absolute count the library
                    expects, as max(2, supMinFrac * tours.size())
     maxPatterns -- cap on how many patterns to return (passed to the
                    library as `nlargest`, and re-applied after
                    reassembly)

   Returns node paths of length >= 2, deduplicated, longest first. */
std::vector<std::vector<int>> fpmax_mine_arc_paths(
    const std::vector<std::vector<int>>& tours,
    int n,
    double supMinFrac,
    int maxPatterns);

#endif
