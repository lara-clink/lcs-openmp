# Compiler and flags for macOS
CC = gcc-14
CFLAGS = -Wall -Wextra -O3 -fopenmp
LDFLAGS = -fopenmp

# Source files
SRCS = lcs.c
OBJS = $(SRCS:.c=.o)

# Executables
TARGET = lcs
TARGET_ORIGINAL = lcs_original

# Python requirements
REQUIREMENTS = requirements.txt

# Default target
all: $(TARGET) $(TARGET_ORIGINAL) python-deps

# Compile the LCS program
$(TARGET): $(OBJS)
	$(CC) $(CFLAGS) -o $@ $^ $(LDFLAGS)

# Compile the original LCS program
$(TARGET_ORIGINAL): lcs_original.c
	$(CC) $(CFLAGS) -o $@ $< $(LDFLAGS)

# Compile source files
%.o: %.c
	$(CC) $(CFLAGS) -c $<

# Install Python dependencies
python-deps:
	pip install -r $(REQUIREMENTS)

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
