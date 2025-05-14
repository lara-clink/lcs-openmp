import random
import string

def generate_sequence(length):
    # Generate a random sequence of characters
    return ''.join(random.choices(string.ascii_letters, k=length))

def create_test_file(filename, length):
    with open(filename, 'w') as f:
        f.write(generate_sequence(length))

# Create test files with different sizes
create_test_file('20000.in', 20000)
create_test_file('20000.in2', 20000)
create_test_file('40000.in', 40000)
create_test_file('40000.in2', 40000)
create_test_file('80000.in', 80000)
create_test_file('80000.in2', 80000)

print("Test files generated successfully!") 
