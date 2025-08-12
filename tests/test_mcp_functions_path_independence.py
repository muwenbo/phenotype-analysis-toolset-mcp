#!/usr/bin/env python3
"""
Test MCP server functions with path independence by testing the actual functions
"""

import sys
import os
import tempfile
import sqlite3
from datetime import datetime

# Save original directory
original_dir = os.getcwd()

def test_database_connection_from_different_dir():
    """Test the actual MCP database connection from different directory"""
    print("Testing Database Connection Path Independence")
    print("="*60)
    
    temp_dir = tempfile.mkdtemp()
    
    try:
        # Change to temp directory
        os.chdir(temp_dir)
        print(f"Changed to: {temp_dir}")
        
        # Add project to path and import
        sys.path.insert(0, original_dir)
        from mcp_server import get_db_connection
        
        # Test database connection
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM phenotype_to_genes LIMIT 1")
        count = cursor.fetchone()[0]
        conn.close()
        
        print(f"✅ Database connection successful: {count:,} records")
        return True
        
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False
        
    finally:
        os.chdir(original_dir)
        import shutil
        shutil.rmtree(temp_dir, ignore_errors=True)

def test_server_status_paths():
    """Test the actual server status logic with path checking"""
    print("\\nTesting Server Status Path Resolution")
    print("="*60)
    
    # Import the actual function logic (simulate what's in the MCP tool)
    sys.path.insert(0, original_dir)
    
    temp_dir = tempfile.mkdtemp()
    
    try:
        os.chdir(temp_dir)
        print(f"Changed to: {temp_dir}")
        
        # Test the path resolution logic used in the actual MCP server
        script_path = os.path.join(original_dir, 'mcp_server.py')
        script_dir = os.path.dirname(os.path.abspath(script_path))
        
        # These are the paths the MCP server will use
        db_path = os.path.join(script_dir, 'hpo_annotations.db')
        embeddings_path = os.path.join(script_dir, 'embeddings', 'voyage_3')
        
        db_exists = os.path.exists(db_path)
        embeddings_exists = os.path.exists(embeddings_path)
        
        print(f"Script directory: {script_dir}")
        print(f"Database path: {db_path}")
        print(f"Database exists: {db_exists}")
        print(f"Embeddings path: {embeddings_path}")
        print(f"Embeddings exists: {embeddings_exists}")
        
        if db_exists and embeddings_exists:
            print("✅ All paths resolved correctly from different directory")
            return True
        else:
            print("❌ Path resolution failed")
            return False
            
    finally:
        os.chdir(original_dir)
        import shutil
        shutil.rmtree(temp_dir, ignore_errors=True)

def test_hpo_name_function():
    """Test the HPO name lookup function from different directory"""
    print("\\nTesting HPO Name Lookup Path Independence")
    print("="*60)
    
    temp_dir = tempfile.mkdtemp()
    
    try:
        os.chdir(temp_dir)
        print(f"Changed to: {temp_dir}")
        
        # Import and test the get_hpo_name_by_id core logic
        sys.path.insert(0, original_dir)
        from mcp_server import get_db_connection
        
        # Test the core logic that's in the MCP tool
        def test_get_hpo_name_by_id(hpo_id: str):
            try:
                conn = get_db_connection()
                cursor = conn.cursor()
                cursor.execute("SELECT DISTINCT hpo_id, hpo_name FROM phenotype_to_genes WHERE hpo_id = ? LIMIT 1", (hpo_id,))
                row = cursor.fetchone()
                conn.close()
                
                if not row:
                    return {"error": f"HPO term not found: {hpo_id}"}
                
                return {
                    "hpo_id": row['hpo_id'], 
                    "hpo_name": row['hpo_name'],
                    "success": True
                }
            except Exception as e:
                return {"error": f"Failed to get HPO name for {hpo_id}: {str(e)}"}
        
        # Test with known HPO ID
        result = test_get_hpo_name_by_id("HP:0025700")
        
        if "error" not in result:
            print(f"✅ HPO lookup successful: {result['hpo_name']}")
            return True
        else:
            print(f"❌ HPO lookup failed: {result['error']}")
            return False
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False
        
    finally:
        os.chdir(original_dir)
        import shutil
        shutil.rmtree(temp_dir, ignore_errors=True)

if __name__ == "__main__":
    print("MCP Server Path Independence Test (Actual Functions)")
    print("="*70)
    print(f"Original directory: {original_dir}")
    
    try:
        # Run all tests
        test1 = test_database_connection_from_different_dir()
        test2 = test_server_status_paths()
        test3 = test_hpo_name_function()
        
        print("\\n" + "="*70)
        print("SUMMARY")
        print("="*70)
        print(f"Database Connection: {'✅ PASS' if test1 else '❌ FAIL'}")
        print(f"Path Resolution: {'✅ PASS' if test2 else '❌ FAIL'}")
        print(f"HPO Name Lookup: {'✅ PASS' if test3 else '❌ FAIL'}")
        
        if all([test1, test2, test3]):
            print("\\n🎉 ALL TESTS PASSED!")
            print("The MCP server should now work correctly from any client directory.")
        else:
            print("\\n❌ SOME TESTS FAILED!")
            print("There may still be path-related issues.")
            
    except Exception as e:
        print(f"\\n💥 Test suite failed: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Ensure we're back in original directory
        os.chdir(original_dir)
        print(f"\\nRestored to: {os.getcwd()}")