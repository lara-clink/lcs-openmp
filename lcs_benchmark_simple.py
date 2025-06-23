#!/usr/bin/env python3
"""
Simplified LCS MPI benchmark for Nomade cluster
No external dependencies (no pandas, matplotlib)
"""

import os
import time
import json
import statistics
import subprocess
from datetime import datetime
from typing import Dict, List, Tuple
import csv

# Configuration for Nomade cluster (AMD FX-6300)
# Memory limit: 15GB per node
# Otimizado para testes mais longos
INPUT_SIZES = [20000, 40000, 80000]  # Aumentado para testes mais longos
PROCESS_COUNTS = [1, 2, 4, 6, 12]    # Mantido
WEAK_SCALABILITY_BASE_SIZE = 8000    # Aumentado para testar escalabilidade fraca
ITERATIONS = 30                      # Mantido para estatística robusta

def generate_test_files(input_size: int):
    """Generate random test files of specified size"""
    import random
    import string
    
    def generate_sequence(length):
        return ''.join(random.choices(string.ascii_letters + string.digits, k=length))
    
    def create_test_file(filename, length):
        with open(filename, 'w') as f:
            f.write(generate_sequence(length))
    
    create_test_file(f"test_{input_size}_A.txt", input_size)
    create_test_file(f"test_{input_size}_B.txt", input_size)

def run_mpi_test(input_size: int, num_processes: int) -> Tuple[float, float, float, int]:
    """Run MPI test and return (total_time, io_time, computation_time, score)"""
    generate_test_files(input_size)
    
    # Determine node distribution for optimal performance
    if num_processes <= 6:
        mpi_cmd = ['mpirun', '-np', str(num_processes), '--map-by', 'core']
    else:
        processes_per_node = num_processes // 2
        mpi_cmd = ['mpirun', '-np', str(num_processes), 
                  '--map-by', f'ppr:{processes_per_node}:node']
    
    mpi_cmd.extend(['./lcs_mpi', f'test_{input_size}_A.txt', f'test_{input_size}_B.txt'])
    
    try:
        result = subprocess.run(mpi_cmd, capture_output=True, text=True, check=True)
    except subprocess.CalledProcessError as e:
        print(f"MPI program failed: {e.stderr}")
        raise RuntimeError(f"MPI program failed: {e.stderr}")

    # Parse output
    total_time = computation_time = score = None
    
    for line in result.stdout.splitlines():
        if "Total time:" in line:
            total_time = float(line.split(":")[1].strip().split()[0])
        elif "LCS computation time:" in line:
            computation_time = float(line.split(":")[1].strip().split()[0])
        elif "Score:" in line:
            score = int(line.split(":")[1].strip())

    if total_time is None or computation_time is None or score is None:
        print("Failed to parse output:")
        print(result.stdout)
        raise RuntimeError("Failed to parse program output")

    io_time = total_time - computation_time
    return total_time, io_time, computation_time, score

def calculate_amdahl_speedup(sequential_fraction: float, num_processes: int) -> float:
    """Calculate theoretical speedup using Amdahl's law"""
    if sequential_fraction >= 1.0:
        return 1.0
    return 1.0 / (sequential_fraction + (1.0 - sequential_fraction) / num_processes)

def measure_sequential_fraction(input_size: int) -> Tuple[float, Dict]:
    """Measure sequential vs parallel portions"""
    print(f"\n=== Measuring Sequential Fraction for Input Size {input_size} ===")
    
    measurements = []
    for i in range(ITERATIONS):
        print(f"  Iteration {i+1}/{ITERATIONS}")
        total_time, io_time, comp_time, score = run_mpi_test(input_size, 1)
        measurements.append({
            'total_time': total_time,
            'io_time': io_time,
            'computation_time': comp_time,
            'score': score
        })
    
    # Calculate averages
    avg_total = statistics.mean([m['total_time'] for m in measurements])
    avg_io = statistics.mean([m['io_time'] for m in measurements])
    avg_comp = statistics.mean([m['computation_time'] for m in measurements])
    avg_score = statistics.mean([m['score'] for m in measurements])
    
    sequential_fraction = avg_io / avg_total
    
    results = {
        'input_size': input_size,
        'avg_total_time': avg_total,
        'avg_io_time': avg_io,
        'avg_computation_time': avg_comp,
        'sequential_fraction': sequential_fraction,
        'parallel_fraction': 1.0 - sequential_fraction,
        'avg_score': avg_score,
        'measurements': measurements
    }
    
    return sequential_fraction, results

def run_strong_scalability_test(input_size: int, sequential_fraction: float) -> List[Dict]:
    """Test strong scalability"""
    print(f"\n=== Strong Scalability Test - Input Size: {input_size} ===")
    
    results = []
    sequential_time = None
    
    for num_processes in PROCESS_COUNTS:
        print(f"  Testing with {num_processes} processes...")
        
        if num_processes == 3:
            print("    (1 process per physical core)")
        elif num_processes == 6:
            print("    (Full single node)")
        elif num_processes > 6:
            print("    (Multi-node execution)")
        
        times = []
        scores = []
        for i in range(ITERATIONS):
            total_time, io_time, comp_time, score = run_mpi_test(input_size, num_processes)
            times.append(comp_time)
            scores.append(score)
        
        avg_time = statistics.mean(times)
        std_time = statistics.stdev(times) if len(times) > 1 else 0
        avg_score = statistics.mean(scores)
        
        if num_processes == 1:
            sequential_time = avg_time
            speedup = 1.0
            efficiency = 1.0
        else:
            speedup = sequential_time / avg_time
            efficiency = speedup / num_processes
        
        theoretical_speedup = calculate_amdahl_speedup(sequential_fraction, num_processes)
        
        results.append({
            'input_size': input_size,
            'num_processes': num_processes,
            'avg_time': avg_time,
            'std_time': std_time,
            'speedup': speedup,
            'efficiency': efficiency,
            'theoretical_speedup': theoretical_speedup,
            'avg_score': avg_score
        })
    
    return results

def run_weak_scalability_test(base_size: int) -> List[Dict]:
    """Test weak scalability"""
    print(f"\n=== Weak Scalability Test - Base Size per Process: {base_size} ===")
    
    results = []
    baseline_time = None
    
    for num_processes in PROCESS_COUNTS:
        scaled_size = base_size * num_processes
        print(f"  Testing {num_processes} processes with input size {scaled_size}...")
        
        times = []
        scores = []
        for i in range(ITERATIONS):
            total_time, io_time, comp_time, score = run_mpi_test(scaled_size, num_processes)
            times.append(comp_time)
            scores.append(score)
        
        avg_time = statistics.mean(times)
        std_time = statistics.stdev(times) if len(times) > 1 else 0
        avg_score = statistics.mean(scores)
        
        if num_processes == 1:
            baseline_time = avg_time
            efficiency = 1.0
        else:
            efficiency = baseline_time / avg_time
        
        results.append({
            'num_processes': num_processes,
            'input_size': scaled_size,
            'size_per_process': base_size,
            'avg_time': avg_time,
            'std_time': std_time,
            'efficiency': efficiency,
            'avg_score': avg_score
        })
    
    return results

def save_csv_table(filename: str, data: List[Dict], headers: List[str]):
    """Save data as CSV table"""
    with open(filename, 'w', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=headers)
        writer.writeheader()
        writer.writerows(data)

def print_table(title: str, data: List[Dict], headers: List[str]):
    """Print formatted table"""
    print(f"\n{title}")
    print("-" * 60)
    
    # Print header
    header_line = " | ".join(f"{h:>12}" for h in headers)
    print(header_line)
    print("-" * len(header_line))
    
    # Print data
    for row in data:
        values = []
        for h in headers:
            val = row.get(h, '')
            if isinstance(val, float):
                values.append(f"{val:>12.4f}")
            else:
                values.append(f"{str(val):>12}")
        print(" | ".join(values))

def main():
    """Main benchmark execution"""
    print("LCS MPI BENCHMARK - NOMADE CLUSTER OPTIMIZED")
    print("="*60)
    print("Hardware: AMD FX-6300 (3 physical × 2 logical cores per node)")
    print("Cluster: 2 nodes × 6 cores = 12 processes maximum")
    print("="*60)
    
    # Create results directory
    results_dir = f"nomade_benchmark_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    os.makedirs(results_dir, exist_ok=True)
    
    # Step 1: Measure sequential fractions
    print("\nStep 1: Measuring sequential vs parallel portions...")
    sequential_results = {}
    avg_sequential_fraction = 0
    
    for size in INPUT_SIZES:
        seq_frac, results = measure_sequential_fraction(size)
        sequential_results[size] = results
        avg_sequential_fraction += seq_frac
    
    avg_sequential_fraction /= len(INPUT_SIZES)
    
    # Step 2: Create Amdahl's law table
    print(f"\nStep 2: Creating Amdahl's law table (avg sequential fraction: {avg_sequential_fraction:.4f})...")
    amdahl_data = []
    for p in [1, 2, 3, 4, 6, 8, 12, 16, 24, 32, "∞"]:
        if p == "∞":
            speedup = 1.0 / avg_sequential_fraction if avg_sequential_fraction > 0 else float('inf')
        else:
            speedup = calculate_amdahl_speedup(avg_sequential_fraction, p)
        amdahl_data.append({'processes': p, 'theoretical_speedup': speedup})
    
    # Step 3: Strong scalability tests
    print("\nStep 3: Running strong scalability tests...")
    all_strong_results = []
    for size in INPUT_SIZES:
        strong_results = run_strong_scalability_test(size, avg_sequential_fraction)
        all_strong_results.extend(strong_results)
    
    # Step 4: Weak scalability test
    print("\nStep 4: Running weak scalability test...")
    weak_results = run_weak_scalability_test(WEAK_SCALABILITY_BASE_SIZE)
    
    # Step 5: Save results
    print("\nStep 5: Saving results...")
    
    # Sequential analysis
    seq_table = []
    for size, data in sequential_results.items():
        seq_table.append({
            'Input_Size': size,
            'Total_Time': f"{data['avg_total_time']:.4f}",
            'IO_Time': f"{data['avg_io_time']:.4f}",
            'Computation_Time': f"{data['avg_computation_time']:.4f}",
            'Sequential_Fraction': f"{data['sequential_fraction']*100:.2f}%",
            'Parallel_Fraction': f"{data['parallel_fraction']*100:.2f}%"
        })
    
    save_csv_table(os.path.join(results_dir, 'sequential_analysis.csv'), 
                   seq_table, ['Input_Size', 'Total_Time', 'IO_Time', 'Computation_Time', 
                              'Sequential_Fraction', 'Parallel_Fraction'])
    
    # Amdahl's law
    save_csv_table(os.path.join(results_dir, 'amdahl_law.csv'), 
                   amdahl_data, ['processes', 'theoretical_speedup'])
    
    # Strong scalability
    save_csv_table(os.path.join(results_dir, 'strong_scalability.csv'), 
                   all_strong_results, ['input_size', 'num_processes', 'avg_time', 'std_time', 'speedup', 
                                       'efficiency', 'theoretical_speedup', 'avg_score'])
    
    # Weak scalability
    save_csv_table(os.path.join(results_dir, 'weak_scalability.csv'), 
                   weak_results, ['num_processes', 'input_size', 'size_per_process', 'avg_time', 'std_time', 'efficiency', 'avg_score'])
    
    # Print results
    print("\n" + "="*80)
    print("NOMADE CLUSTER BENCHMARK RESULTS")
    print("="*80)
    
    print_table("4. SEQUENTIAL vs PARALLEL ANALYSIS", seq_table, 
                ['Input_Size', 'Sequential_Fraction', 'Parallel_Fraction'])
    
    print_table("5. AMDAHL'S LAW - THEORETICAL SPEEDUP", amdahl_data, 
                ['processes', 'theoretical_speedup'])
    
    print_table("6. STRONG SCALABILITY", all_strong_results, 
                ['num_processes', 'speedup', 'efficiency', 'theoretical_speedup'])
    
    print_table("6. WEAK SCALABILITY", weak_results, 
                ['num_processes', 'input_size', 'size_per_process', 'efficiency'])
    
    print(f"\nAll results saved to: {results_dir}")
    print("Files generated:")
    for file in os.listdir(results_dir):
        print(f"  - {file}")

if __name__ == "__main__":
    main() 
