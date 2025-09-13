#!/usr/bin/env python3
"""
Simple test script to verify the VMware analysis fix.
This script will exit with code 1 to test the strace error handling.
"""

import sys
import time

print("Test script starting...")
print("This is a test file for VMware analysis")
print("Simulating some work...")

# Simulate some work
for i in range(3):
    print(f"Working... {i+1}/3")
    time.sleep(0.5)

print("Test script completed with exit code 1")
print("This should not cause the analysis to fail")

# Exit with non-zero code to test error handling
sys.exit(1)
