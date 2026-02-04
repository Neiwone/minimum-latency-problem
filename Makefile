CXX = g++
CXXFLAGS = -O2 -std=c++17 -Wall

# ---- shared objects ----
COMMON_OBJ = solution.o evaluator.o

# ---- executables ----
TARGETS = nearest_neighbour local_search backtracking

# ---- default target ----
all: $(TARGETS)

# ---- build rules ----
nearest_neighbour: nearest_neighbour.o $(COMMON_OBJ)
	$(CXX) $(CXXFLAGS) $^ -o $@

local_search: local_search.o $(COMMON_OBJ)
	$(CXX) $(CXXFLAGS) $^ -o $@

backtracking: backtracking.o $(COMMON_OBJ)
	$(CXX) $(CXXFLAGS) $^ -o $@

# ---- generic object rule ----
%.o: %.cpp
	$(CXX) $(CXXFLAGS) -c $<

# ---- cleanup ----
clean:
	rm -f *.o $(TARGETS)

# ---- rebuild everything ----
rebuild: clean all
