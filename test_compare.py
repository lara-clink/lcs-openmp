import subprocess
import sys
import os
import re

def extract_lcs_value(output):
    # Try to find 'Score: <number>' or 'LCS length: <number>'
    match = re.search(r'Score: (\d+)', output)
    if match:
        return int(match.group(1))
    match = re.search(r'LCS length: (\d+)', output)
    if match:
        return int(match.group(1))
    raise ValueError('Could not find LCS value in output')

def run_test(input_file1, input_file2):
    # Run both implementations with 1 thread
    cmd1 = ['./lcs', input_file1, input_file2, '1']
    cmd2 = ['./lcs_original', input_file1, input_file2]
    
    print(f"\nTesting with {input_file1} and {input_file2}")
    print(f"Using 1 thread (sequential)")
    
    print("\nRunning optimized version:")
    result1 = subprocess.run(cmd1, capture_output=True, text=True)
    print(result1.stdout)
    
    print("\nRunning original version:")
    result2 = subprocess.run(cmd2, capture_output=True, text=True)
    print(result2.stdout)
    
    # Extract scores
    score1 = extract_lcs_value(result1.stdout)
    score2 = extract_lcs_value(result2.stdout)
    
    # Compare results
    if score1 == score2:
        print(f"\nResults match! Both implementations found LCS length: {score1}")
    else:
        print(f"\nResults differ!")
        print(f"Optimized version: {score1}")
        print(f"Original version: {score2}")

def main():
    # Test with specific input files
    input_file1 = "20000.in"
    input_file2 = "20000.in2"
    
    if not (os.path.exists(input_file1) and os.path.exists(input_file2)):
        print(f"Input files {input_file1} and {input_file2} not found. Skipping...")
        return
    
    run_test(input_file1, input_file2)

if __name__ == "__main__":
    main() 
