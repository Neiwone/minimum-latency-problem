#include <bits/stdc++.h>

using namespace std;
using Graph = vector<vector<double>>;

const double INF = 1e18;

Graph load_instance(const string& filename) {
    ifstream file(filename);
    if (!file.is_open()) {
        throw runtime_error("Could not open file");
    }

    string line;
    int n = 0;
    vector<pair<double, double>> coords;
    bool reading_coords = false;

    while (getline(file, line)) {
        if (line.find("DIMENSION") != string::npos) {
            n = stoi(line.substr(line.find(":") + 1));
            coords.resize(n);
        }
        else if (line == "NODE_COORD_SECTION") {
            reading_coords = true;
        }
        else if (line == "EOF") {
            break;
        }
        else if (reading_coords) {
            stringstream ss(line);
            int id;
            double x, y;
            ss >> id >> x >> y;

            coords[id - 1] = {x, y};
        }
    }

    Graph graph(n, vector<double>(n, 0.0));

    for (int i = 0; i < n; i++) {
        for (int j = 0; j < n; j++) {
            double dx = coords[i].first - coords[j].first;
            double dy = coords[i].second - coords[j].second;
            graph[i][j] = sqrt(dx * dx + dy * dy);
        }
    }

    return graph;
}

vector<int> nearest_neighbour(const Graph& graph, int depot = 0) {
    int n = graph.size();

    // Initialize all vertices as unvisited.
    vector<bool> visited(n, false);
    vector<int> route;

    // Select an arbitrary vertex, set it as the current vertex. Mark as visited.
    int current = depot;
    visited[current] = true;
    route.push_back(current);

    // If all the vertices in the domain are visited, then terminate.
    while (route.size() < n) {
        // Find out the shortest edge connecting the current vertex and an unvisited vertex v.
        int v = -1;
        for (int i = 0; i < n; i++)
        {
            if (i == current) continue;
            if (!visited[i] && (v == -1 || graph[current][i] < graph[current][v])) {
                v = i;
            }
        }

        // Set v as the current vertex. Mark v as visited.
        current = v;
        visited[current] = true;
        route.push_back(current);
    }

    return route;
}

double compute_cost(const Graph& graph, const vector<int>& route, int depot = 0) {
    int n = graph.size();

    double walked = 0.0;
    double cost = 0.0;

    int u, v;
    double w;

    for (int i = 0; i <= n; i++) {
        u = route[i];
        v = route[i + 1];
        w = graph[u][v];

        walked += w;
        cost += walked;
    }

    return cost;
}


int main(int argc, char** argv) {
    if (argc < 2) {
        cerr << "Usage: ./greedy <instance.tsp>\n";
        return 1;
    }

    string filename = argv[1];

    Graph graph = load_instance(filename);
    int n = graph.size();

    using Clock = chrono::high_resolution_clock;

    auto t0 = Clock::now();
    vector<int> route = nearest_neighbour(graph, 0);
    double cost = compute_cost(graph, route);
    auto t1 = Clock::now();

    double runtime_ms = chrono::duration<double, milli>(t1 - t0).count();

    cout << "INSTANCE " << filename << "\n";
    cout << "NODES " << n << "\n";
    cout << "COST " << fixed << setprecision(2) << cost << "\n";
    cout << "TIME_MS " << fixed << setprecision(3) << runtime_ms << "\n";
    cout << "ROUTE ";
    for (int i = 0; i < n; i++) {
        cout << route[i] << ",\n"[i + 1 == n];
    }

    return 0;
}
