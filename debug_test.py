#!/usr/bin/env python3
import subprocess
import sys

# Run the test and capture all output
result = subprocess.run([sys.executable, 'tests/test_integration_rcon.py'], 
                       capture_output=True, text=True, cwd='/home/william/Programs/pz-admin-tool-release')

print("STDOUT:")
print(result.stdout)
print("\nSTDERR:")
print(result.stderr)
print(f"\nReturn code: {result.returncode}")
