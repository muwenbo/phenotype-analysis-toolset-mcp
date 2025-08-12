#!/usr/bin/env python3
"""
Test script to verify that MCP server tools work correctly when run from different directories.

This simulates the issue where an MCP client runs from a different working directory
than the server script location.
"""

import sys
import os
import tempfile
import shutil
from pathlib import Path

# Add parent directory to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

def test_from_different_directory():
    """Test server functions when running from a different directory"""
    print("Testing Path Independence")
    print("="*50)
    
    # Get the original directory
    original_dir = os.getcwd() 
    print(f"Original directory: {original_dir}")
    
    # Create a temporary directory to run from
    with tempfile.TemporaryDirectory() as temp_dir:
        try:
            # Change to the temporary directory
            os.chdir(temp_dir)
            print(f"Changed to temp directory: {temp_dir}")
            
            # Now test importing and using the MCP server functions
            print("\\nTesting imports...")
            
            # Import the database connection function
            from mcp_server import get_db_connection
            print("✅ Import successful")
            
            # Test database connection
            print("\\nTesting database connection...")
            try:
                conn = get_db_connection()
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM phenotype_to_genes LIMIT 1")
                count = cursor.fetchone()[0]
                conn.close()
                print(f"✅ Database connection successful: {count} records found")
            except Exception as e:
                print(f"❌ Database connection failed: {e}")
                return False
            
            # Test server status core logic (simplified)
            print("\\nTesting server status logic...")
            try:
                script_dir = os.path.dirname(os.path.abspath(os.path.join(project_root, 'mcp_server.py')))
                db_path = os.path.join(script_dir, 'hpo_annotations.db')
                embeddings_path = os.path.join(script_dir, 'embeddings', 'voyage_3')
                
                db_exists = os.path.exists(db_path)
                embeddings_exists = os.path.exists(embeddings_path)
                
                print(f"✅ Database path resolution: {db_exists} ({db_path})")
                print(f"✅ Embeddings path resolution: {embeddings_exists} ({embeddings_path})")
                
                if not db_exists:
                    print("❌ Database file not found with absolute path")
                    return False
                    
                if not embeddings_exists:
                    print("❌ Embeddings directory not found with absolute path") 
                    return False
                    
            except Exception as e:
                print(f"❌ Path resolution failed: {e}")
                return False
            
            print("\\n🎉 All tests passed! Server should work from any directory.")
            return True
            
        finally:
            # Always restore original directory
            os.chdir(original_dir)
            print(f"\\nRestored to original directory: {os.getcwd()}")

def test_relative_vs_absolute_paths():
    """Compare relative vs absolute path behavior"""
    print("\\nTesting Relative vs Absolute Paths")
    print("="*50)
    
    # Test from project root
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    os.chdir(project_root)
    print(f"Working from project root: {project_root}")
    
    # Relative paths (old behavior)
    rel_db = 'hpo_annotations.db'
    rel_embeddings = './embeddings/voyage_3/'
    
    # Absolute paths (new behavior) 
    script_path = os.path.join(project_root, 'mcp_server.py')
    script_dir = os.path.dirname(os.path.abspath(script_path))
    abs_db = os.path.join(script_dir, 'hpo_annotations.db')
    abs_embeddings = os.path.join(script_dir, 'embeddings', 'voyage_3')
    
    print(f"\\nRelative paths:")
    print(f"  Database: {rel_db} -> Exists: {os.path.exists(rel_db)}")
    print(f"  Embeddings: {rel_embeddings} -> Exists: {os.path.exists(rel_embeddings)}")
    
    print(f"\\nAbsolute paths:")
    print(f"  Database: {abs_db} -> Exists: {os.path.exists(abs_db)}")
    print(f"  Embeddings: {abs_embeddings} -> Exists: {os.path.exists(abs_embeddings)}")
    
    # Test from different directory
    home_dir = os.path.expanduser("~")
    os.chdir(home_dir)
    print(f"\\nNow working from: {home_dir}")
    
    print(f"\\nRelative paths (should fail):")
    print(f"  Database: {rel_db} -> Exists: {os.path.exists(rel_db)}")
    print(f"  Embeddings: {rel_embeddings} -> Exists: {os.path.exists(rel_embeddings)}")
    
    print(f"\\nAbsolute paths (should work):")
    print(f"  Database: {abs_db} -> Exists: {os.path.exists(abs_db)}")
    print(f"  Embeddings: {abs_embeddings} -> Exists: {os.path.exists(abs_embeddings)}")

if __name__ == "__main__":
    print("MCP Server Path Independence Test")
    print("="*60)
    
    try:
        # Test 1: Run functions from different directory
        success = test_from_different_directory()
        
        # Test 2: Compare path behaviors
        test_relative_vs_absolute_paths()
        
        if success:
            print("\\n✅ PATH INDEPENDENCE TEST PASSED")
            print("The server should now work correctly regardless of client working directory.")
        else:
            print("\\n❌ PATH INDEPENDENCE TEST FAILED") 
            print("There are still path-related issues to fix.")
            
    except Exception as e:
        print(f"\\n💥 Test failed with exception: {e}")
        import traceback
        traceback.print_exc()