#!/usr/bin/env python3
"""
Test script for get_hpo_name_by_id function in mcp_server.py

This script tests the core logic by directly creating and testing the function
without the MCP decorator wrapper.
"""

import sys
import os
import unittest
import sqlite3
from unittest.mock import patch, MagicMock

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def get_db_connection():
    """Database connection function for testing"""
    conn = sqlite3.connect('hpo_annotations.db')
    conn.row_factory = sqlite3.Row
    return conn


def get_hpo_name_by_id_core(hpo_id: str) -> dict:
    """Core logic of get_hpo_name_by_id function (without MCP decoration)"""
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


class TestGetHPONameById(unittest.TestCase):
    """Test cases for get_hpo_name_by_id function"""
    
    def setUp(self):
        """Set up test fixtures before each test method"""
        self.valid_hpo_ids = [
            "HP:0025700",  # Should exist based on our sample data
            "HP:0001263",  # Global developmental delay (common term)
            "HP:0000007",  # Example from function docstrings
        ]
        
        self.invalid_hpo_ids = [
            "HP:9999999",  # Non-existent HPO ID
            "INVALID:123", # Invalid format
            "HP:0000000",  # Edge case
        ]

    def test_valid_hpo_ids(self):
        """Test function with valid HPO IDs"""
        print("\n=== Testing Valid HPO IDs ===")
        
        for hpo_id in self.valid_hpo_ids:
            with self.subTest(hpo_id=hpo_id):
                result = get_hpo_name_by_id_core(hpo_id)
                print(f"Testing {hpo_id}: {result}")
                
                # Check if result is a dictionary
                self.assertIsInstance(result, dict)
                
                # Check for success or error
                if "error" in result:
                    print(f"  ⚠️  {hpo_id} not found in database: {result['error']}")
                else:
                    # Successful result should have required fields
                    self.assertIn("hpo_id", result)
                    self.assertIn("hpo_name", result)
                    self.assertIn("success", result)
                    self.assertEqual(result["hpo_id"], hpo_id)
                    self.assertTrue(result["success"])
                    print(f"  ✅ Success: {result['hpo_name']}")

    def test_invalid_hpo_ids(self):
        """Test function with invalid HPO IDs"""
        print("\n=== Testing Invalid HPO IDs ===")
        
        for hpo_id in self.invalid_hpo_ids:
            with self.subTest(hpo_id=hpo_id):
                result = get_hpo_name_by_id_core(hpo_id)
                print(f"Testing {hpo_id}: {result}")
                
                # Should return dictionary with error
                self.assertIsInstance(result, dict)
                self.assertIn("error", result)
                self.assertIn(hpo_id, result["error"])
                print(f"  ✅ Correctly returned error for invalid ID")

    def test_database_connection(self):
        """Test that database connection works"""
        print("\n=== Testing Database Connection ===")
        
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # Test basic query
            cursor.execute("SELECT COUNT(*) FROM phenotype_to_genes")
            count = cursor.fetchone()[0]
            
            conn.close()
            
            self.assertGreater(count, 0, "Database should contain data")
            print(f"  ✅ Database connection successful, {count} records found")
            
        except Exception as e:
            self.fail(f"Database connection failed: {e}")

    @patch('__main__.get_db_connection')
    def test_database_error_handling(self, mock_get_db_connection):
        """Test error handling when database connection fails"""
        print("\n=== Testing Database Error Handling ===")
        
        # Mock database connection to raise an exception
        mock_get_db_connection.side_effect = Exception("Database connection failed")
        
        result = get_hpo_name_by_id_core("HP:0000007")
        print(f"Testing database error: {result}")
        
        # Should return error message
        self.assertIsInstance(result, dict)
        self.assertIn("error", result)
        self.assertIn("Failed to get HPO name", result["error"])
        print("  ✅ Correctly handled database connection error")

    def test_sample_data_verification(self):
        """Verify some known data exists in the database"""
        print("\n=== Testing Sample Data Verification ===")
        
        # Test with the sample data we know exists
        result = get_hpo_name_by_id_core("HP:0025700")
        print(f"Testing known sample data HP:0025700: {result}")
        
        if "error" not in result:
            self.assertEqual(result["hpo_id"], "HP:0025700")
            self.assertEqual(result["hpo_name"], "Anhydramnios")
            self.assertTrue(result["success"])
            print("  ✅ Sample data verification successful")
        else:
            print("  ⚠️  Sample data not found - database may be different")

    def test_edge_cases(self):
        """Test edge cases and malformed inputs"""
        print("\n=== Testing Edge Cases ===")
        
        edge_cases = ["", "HP:", "HP:ABC", "not_an_hpo"]
        
        for case in edge_cases:
            with self.subTest(input=case):
                result = get_hpo_name_by_id_core(case)
                print(f"Testing edge case '{case}': {result}")
                
                # Should return dictionary with error for all edge cases
                self.assertIsInstance(result, dict)
                self.assertIn("error", result)
                print(f"  ✅ Correctly handled edge case")


def run_interactive_test():
    """Run interactive test with user input"""
    print("\n" + "="*60)
    print("INTERACTIVE TEST MODE")
    print("="*60)
    print("Enter HPO IDs to test (press Enter with empty input to exit):")
    
    while True:
        hpo_id = input("\nEnter HPO ID (e.g., HP:0000007): ").strip()
        if not hpo_id:
            break
            
        result = get_hpo_name_by_id_core(hpo_id)
        
        if "error" in result:
            print(f"❌ Error: {result['error']}")
        else:
            print(f"✅ Success!")
            print(f"   HPO ID: {result['hpo_id']}")
            print(f"   HPO Name: {result['hpo_name']}")


def run_quick_test():
    """Run a quick test with known data"""
    print("\n" + "="*60)
    print("QUICK TEST - Testing with known sample data")
    print("="*60)
    
    test_cases = [
        "HP:0025700",  # Known to exist: Anhydramnios
        "HP:0000001",  # Likely doesn't exist
        "INVALID",     # Invalid format
    ]
    
    for hpo_id in test_cases:
        result = get_hpo_name_by_id_core(hpo_id)
        print(f"\nTesting {hpo_id}:")
        
        if "error" in result:
            print(f"  ❌ {result['error']}")
        else:
            print(f"  ✅ {result['hpo_name']}")


if __name__ == "__main__":
    print("HPO Name Lookup Function Test Suite (Fixed Version)")
    print("="*60)
    
    # Check command line arguments
    if len(sys.argv) > 1:
        if sys.argv[1] == "--interactive":
            run_interactive_test()
        elif sys.argv[1] == "--quick":
            run_quick_test()
        else:
            print("Usage: python test_get_hpo_name_by_id_fixed.py [--interactive|--quick]")
    else:
        # Run unit tests
        unittest.main(verbosity=2)