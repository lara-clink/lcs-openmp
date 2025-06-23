# Compiler settings
MPICC = mpicc
CC = gcc  # Changed from gcc-14 to gcc for cluster compatibility
CFLAGS = -Wall -Wextra -O3
LDFLAGS = 

# Source files
SRCS = lcs.c
OBJS = $(SRCS:.c=.o)

# Executables
TARGET = lcs_mpi
TARGET_ORIGINAL = lcs_original

# Python requirements
REQUIREMENTS = requirements.txt

# Default target
all: $(TARGET) $(TARGET_ORIGINAL) python-deps

# Compile the MPI LCS program
$(TARGET): $(OBJS)
	$(MPICC) $(CFLAGS) -o $@ $^ $(LDFLAGS)

# Compile the original LCS program (still using OpenMP)
$(TARGET_ORIGINAL): lcs_original.c
	$(CC) -Wall -Wextra -O3 -fopenmp -o $@ $< -fopenmp

# Compile source files
%.o: %.c
	$(MPICC) $(CFLAGS) -c $<

# Install Python dependencies
python-deps:
	@echo "Skipping pip install - using built-in Python libraries only"

# Clean up object files, executables, experiment results, and input files
clean:
	rm -f $(OBJS) $(TARGET) $(TARGET_ORIGINAL)
	rm -rf experiment_results_*
	# Remove all .in and .in2 files except fileA.in and fileB.in
	find . -maxdepth 1 -name "*.in" ! -name "fileA.in" ! -name "fileB.in" -delete
	find . -maxdepth 1 -name "*.in2" -delete

# Run tests
test: all
	./test_threads.sh

# Phony targets
.PHONY: all clean test python-deps 
