#ifndef __FPMAX_MINING__
#define __FPMAX_MINING__

#include <vector>

/* Wrapper around vendored FPmax* (external/fpmax/): its fp_tree.h clashes
   with <stack>, so only fpmax_mining.cpp may include "fpmax.h", first. */

/* Maximal frequent arc itemsets over `tours`, reassembled into node paths
   of length >= 2, deduplicated, longest first. */
std::vector<std::vector<int>> fpmax_mine_arc_paths(
    const std::vector<std::vector<int>>& tours,
    int n,                  /* node count; an arc (u,v) is encoded u*n + v */
    double supMinFrac,      /* min support as a FRACTION of tours.size() */
    int maxPatterns);       /* cap on patterns returned */

#endif
