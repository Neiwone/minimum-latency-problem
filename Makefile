CXX = g++
CXXFLAGS = -O2 -std=c++17 -Wall

# ---- folders ----
SRC_DIR = src
INC_DIR = include
BIN_DIR = bin
OBJ_DIR = obj

CXXFLAGS += -I$(INC_DIR)

# ---- executables ----
TARGETS = nearest_neighbour local_search backtracking construction gils_rvnd grasp grasp_am gils_am_rvnd mdm_gils_rvnd dbmea tabu_search gils_rvnd_tabu

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

grasp: $(OBJ_DIR)/grasp.o $(COMMON_OBJ) $(RVND_OBJ) $(CONSTRUCTION_OBJ)
	$(CXX) $(CXXFLAGS) $^ -o $(BIN_DIR)/$@

grasp_am: $(OBJ_DIR)/grasp_am.o $(COMMON_OBJ) $(RVND_OBJ)
	$(CXX) $(CXXFLAGS) $^ -o $(BIN_DIR)/$@

gils_am_rvnd: $(OBJ_DIR)/gils_am_rvnd.o $(COMMON_OBJ) $(RVND_OBJ)
	$(CXX) $(CXXFLAGS) $^ -o $(BIN_DIR)/$@

mdm_gils_rvnd: $(OBJ_DIR)/mdm_gils_rvnd.o $(COMMON_OBJ) $(RVND_OBJ) $(CONSTRUCTION_OBJ)
	$(CXX) $(CXXFLAGS) $^ -o $(BIN_DIR)/$@

dbmea: $(OBJ_DIR)/dbmea.o $(COMMON_OBJ) $(RVND_OBJ) $(CONSTRUCTION_OBJ)
	$(CXX) $(CXXFLAGS) $^ -o $(BIN_DIR)/$@

tabu_search: $(OBJ_DIR)/tabu_search.o $(COMMON_OBJ) $(CONSTRUCTION_OBJ)
	$(CXX) $(CXXFLAGS) $^ -o $(BIN_DIR)/$@

gils_rvnd_tabu: $(OBJ_DIR)/gils_rvnd_tabu.o $(COMMON_OBJ) $(RVND_OBJ) $(CONSTRUCTION_OBJ)
	$(CXX) $(CXXFLAGS) $^ -o $(BIN_DIR)/$@

# ---- generic object rule ----
$(OBJ_DIR)/%.o: $(SRC_DIR)/%.cpp | directories
	$(CXX) $(CXXFLAGS) -c $< -o $@

# ---- cleanup ----
clean:
	rm -rf $(OBJ_DIR) $(BIN_DIR)

# ---- rebuild everything ----
rebuild: clean all
