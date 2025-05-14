import os
import time
import json
import statistics
import subprocess
from datetime import datetime
from typing import Dict, List, Tuple
import pandas as pd
import matplotlib.pyplot as plt

# Configuration
THREAD_COUNTS = [1, 2, 4, 8]
INPUT_SIZES = [20000, 40000, 80000]
ITERATIONS = 20

# Function to calculate mean and standard deviation
def calc_stats(values):
    if not values:
        return "; ;"
    mean = statistics.mean(values)
    stddev = statistics.stdev(values) if len(values) > 1 else 0
    return f"{mean:.6f}; {stddev:.6f};"

# Function to parse stats string into mean and std
def parse_stats(stats_str: str) -> Tuple[float, float]:
    mean_str, std_str, _ = stats_str.split(';')
    return float(mean_str), float(std_str)

# Function to generate test files
def generate_test_files(input_size: int):
    import random
    import string
    def generate_sequence(length):
        return ''.join(random.choices(string.ascii_letters, k=length))
    def create_test_file(filename, length):
        with open(filename, 'w') as f:
            f.write(generate_sequence(length))
    create_test_file(f"{input_size}.in", input_size)
    create_test_file(f"{input_size}.in2", input_size)

# Function to run a single test
def run_single_test(input_size: int, thread_count: int) -> Tuple[float, float]:
    # Always (re)create input files before each run
    generate_test_files(input_size)
    input_file = f"{input_size}.in"
    try:
        result = subprocess.run(
            ['./lcs', input_file, f"{input_size}.in2", str(thread_count)],
            capture_output=True,
            text=True,
            check=True
        )
    except subprocess.CalledProcessError as e:
        print(f"LCS program failed with error code {e.returncode}")
        print(f"Error output: {e.stderr}")
        print(f"Command output: {e.stdout}")
        raise RuntimeError(f"LCS program failed: {e.stderr}")

    total_time = None
    parallel_time = None
    for line in result.stdout.splitlines():
        if "Total time:" in line:
            total_time = float(line.split(":")[1].strip().split()[0])
        elif "LCS computation time:" in line:
            parallel_time = float(line.split(":")[1].strip().split()[0])

    if total_time is None or parallel_time is None:
        print("Failed to parse LCS program output:")
        print(result.stdout)
        raise RuntimeError("Failed to parse LCS program output")

    return total_time, parallel_time

# Function to run all experiments
def run_experiments():
    results_dir = f"experiment_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    os.makedirs(results_dir, exist_ok=True)
    results_data = []
    sequential_times = {}  # Store sequential times for each input size

    for input_size in INPUT_SIZES:
        print(f"\nTesting with input size: {input_size}")
        # Run tests for all thread counts
        for thread_count in THREAD_COUNTS:
            print(f"  Threads: {thread_count}")
            times = []
            for i in range(ITERATIONS):
                try:
                    total_time, parallel_time = run_single_test(input_size, thread_count)
                    times.append(parallel_time)
                    print(f"    Iteration {i+1}: {parallel_time:.6f} seconds")
                except Exception as e:
                    print(f"    Error in iteration {i+1}: {str(e)}")
                    continue

            if times:
                stats_str = calc_stats(times)
                mean_time, std_time = parse_stats(stats_str)
                
                # For thread_count=1, store the sequential time
                if thread_count == 1:
                    sequential_times[input_size] = mean_time
                    speedup = 1.0
                    efficiency = 1.0
                else:
                    # Calculate speedup and efficiency using the stored sequential time
                    speedup = sequential_times[input_size] / mean_time
                    efficiency = speedup / thread_count

                results_data.append({
                    'input_size': input_size,
                    'thread_count': thread_count,
                    'mean_time': mean_time,
                    'std_time': std_time,
                    'speedup': speedup,
                    'efficiency': efficiency
                })

    # Save results
    df = pd.DataFrame(results_data)
    df.to_csv(os.path.join(results_dir, 'results.csv'), index=False)
    with open(os.path.join(results_dir, 'results.json'), 'w') as f:
        json.dump(results_data, f, indent=4)

    # Generate plots
    plots_dir = os.path.join(results_dir, 'plots')
    os.makedirs(plots_dir, exist_ok=True)

    # Plot execution time vs thread count
    plt.figure(figsize=(10, 6))
    for size in INPUT_SIZES:
        size_data = df[df['input_size'] == size]
        if not size_data.empty:
            plt.errorbar(
                size_data['thread_count'],
                size_data['mean_time'],
                yerr=size_data['std_time'],
                label=f'Input size {size}',
                marker='o'
            )
    plt.xlabel('Number of Threads')
    plt.ylabel('Execution Time (seconds)')
    plt.title('Execution Time vs Thread Count')
    plt.legend()
    plt.grid(True)
    plt.savefig(os.path.join(plots_dir, 'execution_time.png'))
    plt.close()

    # Plot speedup vs thread count
    plt.figure(figsize=(10, 6))
    for size in INPUT_SIZES:
        size_data = df[df['input_size'] == size]
        if not size_data.empty:
            plt.plot(
                size_data['thread_count'],
                size_data['speedup'],
                label=f'Input size {size}',
                marker='o'
            )
    plt.plot([1, max(THREAD_COUNTS)], [1, max(THREAD_COUNTS)], 'k--', label='Linear speedup')
    plt.xlabel('Number of Threads')
    plt.ylabel('Speedup')
    plt.title('Speedup vs Thread Count')
    plt.legend()
    plt.grid(True)
    plt.savefig(os.path.join(plots_dir, 'speedup.png'))
    plt.close()

    # Plot efficiency vs thread count
    plt.figure(figsize=(10, 6))
    for size in INPUT_SIZES:
        size_data = df[df['input_size'] == size]
        if not size_data.empty:
            plt.plot(
                size_data['thread_count'],
                size_data['efficiency'],
                label=f'Input size {size}',
                marker='o'
            )
    plt.xlabel('Number of Threads')
    plt.ylabel('Efficiency')
    plt.title('Efficiency vs Thread Count')
    plt.legend()
    plt.grid(True)
    plt.savefig(os.path.join(plots_dir, 'efficiency.png'))
    plt.close()

if __name__ == "__main__":
    run_experiments() 
