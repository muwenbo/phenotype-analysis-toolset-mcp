#!/usr/bin/env python3
"""
Test server status tool from different working directory
"""

import sys
import os
import tempfile

# Save original directory
original_dir = os.getcwd()

try:
    # Create and change to a temporary directory
    temp_dir = tempfile.mkdtemp()
    os.chdir(temp_dir)
    print(f"Testing from temporary directory: {temp_dir}")
    print(f"Original project directory: {original_dir}")
    
    # Add the project directory to Python path
    sys.path.insert(0, original_dir)
    
    # Import and test the server status
    from tests.test_server_status import get_server_status_core, print_status_report
    
    print("\\n" + "="*60)
    print("TESTING SERVER STATUS FROM DIFFERENT DIRECTORY")
    print("="*60)
    
    # Run the server status check
    status = get_server_status_core()
    print_status_report(status)
    
    # Check if it worked
    if status['status'] == 'healthy':
        print("\\n🎉 SUCCESS: Server status works from different directory!")
    else:
        print(f"\\n⚠️  Status: {status['status']}")
        
finally:
    # Always restore original directory
    os.chdir(original_dir)
    # Clean up temp directory
    if 'temp_dir' in locals():
        import shutil
        shutil.rmtree(temp_dir, ignore_errors=True)
        print(f"\\nCleaned up temporary directory: {temp_dir}")
    print(f"Restored to original directory: {os.getcwd()}")