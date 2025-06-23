#!/bin/bash
#SBATCH --job-name=lcs_mpi_fixed
#SBATCH --nodes=2
#SBATCH --ntasks=12
#SBATCH --time=10:00:00
#SBATCH --output=lcs_nomade_fixed_%j.out
#SBATCH --error=lcs_nomade_fixed_%j.err

echo "=========================================="
echo "LCS MPI BENCHMARK - NOMADE CLUSTER FIXED"
echo "=========================================="
echo "Job ID: $SLURM_JOB_ID"
echo "Nodes allocated: $SLURM_JOB_NUM_NODES"
echo "Tasks per node: $SLURM_NTASKS_PER_NODE"
echo "Total tasks: $SLURM_NTASKS"
echo "Start time: $(date)"
echo ""

echo "=== HARDWARE INFORMATION ==="
echo "Node: $(hostname)"
echo "CPU Info: $(cat /proc/cpuinfo | grep 'model name' | head -1 | cut -d':' -f2 | xargs)"
echo "Cores: $(nproc)"
echo "Memory: $(free -h | grep Mem | awk '{print $2}')"
echo "Cache L3: $(lscpu | grep 'L3 cache' | awk '{print $3, $4}')"
echo ""

echo "=== NODE ALLOCATION ==="
echo "Nodes: $SLURM_JOB_NODELIST"
scontrol show hostnames $SLURM_JOB_NODELIST | while read node; do
    echo "      $SLURM_NTASKS_PER_NODE $node"
done
echo ""

echo "=== COMPILATION ==="
make clean
make all
echo ""

echo "=== STARTING BENCHMARK ==="
echo "Configuration:"
echo "  - Input sizes: 20k, 40k, 80k characters"
echo "  - Process counts: 1, 2, 4, 6, 12 (optimized selection)"
echo "  - Iterations: 30 per test (reduced for time efficiency)"
echo "  - Weak scalability: base 8k chars (max 12k for 12 processes)"
echo "  - Expected runtime: 5 hours (10h time limit)"
echo ""

# Run the benchmark
python3 lcs_benchmark_simple.py

echo ""
echo "=== BENCHMARK COMPLETED ==="
echo "End time: $(date)"
echo ""

echo "=== RESULTS SUMMARY ==="
RESULTS_DIR=$(ls -td nomade_benchmark_* 2>/dev/null | head -1)
if [ -n "$RESULTS_DIR" ]; then
    echo "Results directory: $RESULTS_DIR"
    echo "Files generated:"
    ls -la "$RESULTS_DIR"
    echo ""
    echo "=== CSV FILES CONTENT ==="
    for csv_file in "$RESULTS_DIR"/*.csv; do
        if [ -f "$csv_file" ]; then
            echo "--- $(basename "$csv_file") ---"
            head -10 "$csv_file"
            echo ""
        fi
    done
else
    echo "No results directory found"
fi 
