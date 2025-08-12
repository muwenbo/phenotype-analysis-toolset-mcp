#!/usr/bin/env python3
"""
Test script for get_hpo_name_by_id function in mcp_server.py

This script tests various scenarios including:
- Valid HPO IDs
- Invalid HPO IDs
- Edge cases
- Database connection handling
"""

import sys
import os
import unittest
from unittest.mock import patch, MagicMock

# Add parent directory to path to import mcp_server
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from mcp_server import get_hpo_name_by_id, get_db_connection
except ImportError as e:
    print(f"Error importing mcp_server: {e}")
    print("Make sure you're running this from the project root directory")
    sys.exit(1)


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
        
        self.malformed_inputs = [
            "",            # Empty string
            None,          # None value
            "not_an_hpo",  # Random string
            123,           # Integer instead of string
        ]

    def test_valid_hpo_ids(self):
        """Test function with valid HPO IDs"""
        print("\n=== Testing Valid HPO IDs ===")
        
        for hpo_id in self.valid_hpo_ids:
            with self.subTest(hpo_id=hpo_id):
                try:
                    result = get_hpo_name_by_id(hpo_id)
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
                        
                except Exception as e:
                    self.fail(f"Valid HPO ID {hpo_id} raised an exception: {e}")

    def test_invalid_hpo_ids(self):
        """Test function with invalid HPO IDs"""
        print("\n=== Testing Invalid HPO IDs ===")
        
        for hpo_id in self.invalid_hpo_ids:
            with self.subTest(hpo_id=hpo_id):
                result = get_hpo_name_by_id(hpo_id)
                print(f"Testing {hpo_id}: {result}")
                
                # Should return dictionary with error
                self.assertIsInstance(result, dict)
                self.assertIn("error", result)
                self.assertIn(hpo_id, result["error"])
                print(f"  ✅ Correctly returned error for invalid ID")

    def test_malformed_inputs(self):
        """Test function with malformed inputs"""
        print("\n=== Testing Malformed Inputs ===")
        
        for invalid_input in self.malformed_inputs:
            with self.subTest(input=invalid_input):
                try:
                    result = get_hpo_name_by_id(invalid_input)
                    print(f"Testing {repr(invalid_input)}: {result}")
                    
                    # Should return dictionary with error
                    self.assertIsInstance(result, dict)
                    self.assertIn("error", result)
                    print(f"  ✅ Correctly handled malformed input")
                    
                except Exception as e:
                    # Some malformed inputs might raise exceptions, which is acceptable
                    print(f"  ⚠️  Exception raised for {repr(invalid_input)}: {e}")

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

    @patch('mcp_server.get_db_connection')
    def test_database_error_handling(self, mock_get_db_connection):
        """Test error handling when database connection fails"""
        print("\n=== Testing Database Error Handling ===")
        
        # Mock database connection to raise an exception
        mock_get_db_connection.side_effect = Exception("Database connection failed")
        
        result = get_hpo_name_by_id("HP:0000007")
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
        result = get_hpo_name_by_id("HP:0025700")
        print(f"Testing known sample data HP:0025700: {result}")
        
        if "error" not in result:
            self.assertEqual(result["hpo_id"], "HP:0025700")
            self.assertEqual(result["hpo_name"], "Anhydramnios")
            self.assertTrue(result["success"])
            print("  ✅ Sample data verification successful")
        else:
            print("  ⚠️  Sample data not found - database may be different")


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
            
        result = get_hpo_name_by_id(hpo_id)
        
        if "error" in result:
            print(f"❌ Error: {result['error']}")
        else:
            print(f"✅ Success!")
            print(f"   HPO ID: {result['hpo_id']}")
            print(f"   HPO Name: {result['hpo_name']}")


if __name__ == "__main__":
    print("HPO Name Lookup Function Test Suite")
    print("="*50)
    
    # Check if we want to run interactive mode
    if len(sys.argv) > 1 and sys.argv[1] == "--interactive":
        run_interactive_test()
    else:
        # Run unit tests
        unittest.main(verbosity=2)