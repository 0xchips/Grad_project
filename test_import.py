#!/usr/bin/env python3

import sys
import os
print(f"Python version: {sys.version}")
print(f"Current directory: {os.getcwd()}")
print(f"Python path: {sys.path}")

# Try to import and check the function
try:
    import flaskkk
    print("Flask module imported successfully")
    
    # Check if we can find the test function
    if hasattr(flaskkk, 'test_subprocess'):
        func = getattr(flaskkk, 'test_subprocess')
        print(f"Function found: {func}")
        print(f"Function docstring: {func.__doc__}")
    else:
        print("test_subprocess function not found")
        
    # Check the file modification time
    import stat
    file_stat = os.stat('flaskkk.py')
    print(f"File modified time: {file_stat.st_mtime}")
    
except Exception as e:
    print(f"Error importing: {e}")
