CXX = g++
CXXFLAGS = -O2 -std=c++17 -Wall

# ---- folders ----
BIN_DIR = bin
OBJ_DIR = obj

# ---- executables ----
TARGETS = nearest_neighbour local_search backtracking construction gils_rvnd

# ---- shared objects ----
COMMON_OBJ = $(OBJ_DIR)/solution.o $(OBJ_DIR)/evaluator.o
NEIGHBORHOOD_OBJ = $(OBJ_DIR)/neighborhoods.o
RVND_OBJ = $(OBJ_DIR)/rvnd.o $(NEIGHBORHOOD_OBJ)
CONSTRUCTION_OBJ = $(OBJ_DIR)/construction_impl.o

# ---- default target ----
all: directories $(TARGETS)

# ---- create folders ----
directories:
	mkdir -p $(BIN_DIR)
	mkdir -p $(OBJ_DIR)

# ---- build rules ----
nearest_neighbour: $(OBJ_DIR)/nearest_neighbour.o $(COMMON_OBJ)
	$(CXX) $(CXXFLAGS) $^ -o $(BIN_DIR)/$@

local_search: $(OBJ_DIR)/local_search.o $(COMMON_OBJ) $(RVND_OBJ)
	$(CXX) $(CXXFLAGS) $^ -o $(BIN_DIR)/$@

backtracking: $(OBJ_DIR)/backtracking.o $(COMMON_OBJ)
	$(CXX) $(CXXFLAGS) $^ -o $(BIN_DIR)/$@

construction: $(OBJ_DIR)/construction.o $(COMMON_OBJ) $(CONSTRUCTION_OBJ)
	$(CXX) $(CXXFLAGS) $^ -o $(BIN_DIR)/$@

gils_rvnd: $(OBJ_DIR)/gils_rvnd.o $(COMMON_OBJ) $(RVND_OBJ) $(CONSTRUCTION_OBJ)
	$(CXX) $(CXXFLAGS) $^ -o $(BIN_DIR)/$@

# ---- generic object rule ----
$(OBJ_DIR)/%.o: %.cpp
	$(CXX) $(CXXFLAGS) -c $< -o $@

# ---- cleanup ----
clean:
	rm -rf $(OBJ_DIR) $(BIN_DIR)

# ---- rebuild everything ----
rebuild: clean all
