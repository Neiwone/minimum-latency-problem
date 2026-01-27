#include <bits/stdc++.h>
using namespace std;

using Graph = vector<vector<double>>;
const double INF = 1e18;

Graph load_instance(const string& filename) {
    ifstream file(filename);
    if (!file.is_open())
        throw runtime_error("Could not open file");

    string line;
    int n = 0;
    vector<pair<double,double>> coords;
    bool reading = false;

    while (getline(file, line)) {
        if (line.find("DIMENSION") != string::npos) {
            n = stoi(line.substr(line.find(":") + 1));
            coords.resize(n);
        }
        else if (line == "NODE_COORD_SECTION") {
            reading = true;
        }
        else if (line == "EOF") break;
        else if (reading) {
            int id; double x, y;
            stringstream ss(line);
            ss >> id >> x >> y;
            coords[id - 1] = {x, y};
        }
    }

    Graph g(n, vector<double>(n));
    for (int i = 0; i < n; i++)
        for (int j = 0; j < n; j++) {
            double dx = coords[i].first - coords[j].first;
            double dy = coords[i].second - coords[j].second;
            g[i][j] = sqrt(dx*dx + dy*dy);
        }

    return g;
}

double best_cost = INF;
vector<int> best_route;

void backtrack(
    const Graph& g,
    vector<bool>& visited,
    vector<int>& route,
    int current,
    double walked,
    double cost
) {
    int n = g.size();

    if ((int)route.size() == n) {
        if (cost < best_cost) {
            best_cost = cost;
            best_route = route;
        }
        return;
    }

    for (int v = 0; v < n; v++) {
        if (!visited[v]) {
            double d = g[current][v];
            double new_walked = walked + d;
            double new_cost = cost + new_walked;

            if (new_cost >= best_cost)
                continue;

            visited[v] = true;
            route.push_back(v);

            backtrack(g, visited, route, v, new_walked, new_cost);

            route.pop_back();
            visited[v] = false;
        }
    }
}

int main(int argc, char** argv) {
    if (argc < 2) {
        cerr << "Usage: ./backtracking <instance.tsp>\n";
        return 1;
    }

    Graph graph = load_instance(argv[1]);
    int n = graph.size();

    vector<bool> visited(n, false);
    vector<int> route;

    int depot = 0;
    visited[depot] = true;
    route.push_back(depot);

    using Clock = chrono::high_resolution_clock;

    auto t0 = Clock::now();
    backtrack(graph, visited, route, depot, 0.0, 0.0);
    auto t1 = Clock::now();

    double runtime_ms = chrono::duration<double, milli>(t1 - t0).count();

    cout << "INSTANCE " << argv[1] << "\n";
    cout << "NODES " << n << "\n";
    cout << "COST " << fixed << setprecision(2) << best_cost << "\n";
    cout << "TIME_MS " << fixed << setprecision(3) << runtime_ms << "\n";
    cout << "ROUTE ";
    for (int i = 0; i < n; i++) {
      cout << best_route[i] << ",\n"[i == n-1];
    }

    return 0;
}
