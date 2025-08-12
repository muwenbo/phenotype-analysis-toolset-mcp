#!/usr/bin/env python3
"""
Test script for VOYAGE API key configuration
"""

import sys
import os
import tempfile

# Add parent directory to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

def test_api_key_config_without_key():
    """Test configuration status when no API key is set"""
    print("Testing API Key Configuration (No Key)")
    print("="*50)
    
    # Temporarily remove API key if it exists
    original_key = os.environ.get('VOYAGE_API_KEY')
    if 'VOYAGE_API_KEY' in os.environ:
        del os.environ['VOYAGE_API_KEY']
    
    try:
        # Import after removing the key
        if 'mcp_server' in sys.modules:
            del sys.modules['mcp_server']
        
        # Now import and test
        from mcp_server import VOYAGE_API_KEY
        
        print(f"API Key configured: {bool(VOYAGE_API_KEY)}")
        print(f"API Key value: {VOYAGE_API_KEY}")
        
        # Test the configuration function logic
        script_dir = os.path.dirname(os.path.abspath(os.path.join(project_root, 'mcp_server.py')))
        env_path = os.path.join(script_dir, '.env')
        env_template_path = os.path.join(script_dir, '.env.template')
        
        print(f"Script directory: {script_dir}")
        print(f".env file exists: {os.path.exists(env_path)}")
        print(f".env.template exists: {os.path.exists(env_template_path)}")
        
    finally:
        # Restore original key
        if original_key:
            os.environ['VOYAGE_API_KEY'] = original_key
        
def test_api_key_config_with_env_var():
    """Test configuration with environment variable"""
    print("\\nTesting API Key Configuration (Environment Variable)")
    print("="*50)
    
    # Set a test API key
    test_key = "voyage_test_key_12345678"
    os.environ['VOYAGE_API_KEY'] = test_key
    
    try:
        # Reload the module to pick up the new environment variable
        if 'mcp_server' in sys.modules:
            del sys.modules['mcp_server']
        
        from mcp_server import VOYAGE_API_KEY
        
        print(f"API Key configured: {bool(VOYAGE_API_KEY)}")
        print(f"API Key matches test: {VOYAGE_API_KEY == test_key}")
        
    finally:
        # Clean up
        if 'VOYAGE_API_KEY' in os.environ:
            del os.environ['VOYAGE_API_KEY']

def test_api_key_config_with_env_file():
    """Test configuration with .env file"""
    print("\\nTesting API Key Configuration (.env file)")
    print("="*50)
    
    # Remove environment variable if it exists
    original_key = os.environ.get('VOYAGE_API_KEY')
    if 'VOYAGE_API_KEY' in os.environ:
        del os.environ['VOYAGE_API_KEY']
    
    # Create a temporary .env file
    script_dir = os.path.dirname(os.path.abspath(os.path.join(project_root, 'mcp_server.py')))
    env_path = os.path.join(script_dir, '.env')
    env_backup_path = env_path + '.backup'
    
    # Backup existing .env if it exists
    if os.path.exists(env_path):
        os.rename(env_path, env_backup_path)
    
    try:
        # Create test .env file
        test_key = "voyage_env_file_key_87654321"
        with open(env_path, 'w') as f:
            f.write(f'VOYAGE_API_KEY={test_key}\\n')
        
        print(f"Created test .env file: {env_path}")
        
        # Reload the module to pick up the .env file
        if 'mcp_server' in sys.modules:
            del sys.modules['mcp_server']
        
        from mcp_server import VOYAGE_API_KEY
        
        print(f"API Key configured: {bool(VOYAGE_API_KEY)}")
        print(f"API Key matches test: {VOYAGE_API_KEY == test_key}")
        
    finally:
        # Clean up
        if os.path.exists(env_path):
            os.remove(env_path)
        
        # Restore backup if it existed
        if os.path.exists(env_backup_path):
            os.rename(env_backup_path, env_path)
        
        # Restore original environment variable
        if original_key:
            os.environ['VOYAGE_API_KEY'] = original_key

def test_server_hpo_vectorstore():
    """Test the ServerHPOVectorStore with different key configurations"""
    print("\\nTesting ServerHPOVectorStore")
    print("="*50)
    
    # Set a dummy API key for testing
    os.environ['VOYAGE_API_KEY'] = "test_key_for_vector_store"
    
    try:
        # Reload module
        if 'mcp_server' in sys.modules:
            del sys.modules['mcp_server']
        
        from mcp_server import ServerHPOVectorStore
        
        # Test initialization
        embeddings_path = os.path.join(project_root, 'embeddings', 'voyage_3')
        vectorstore = ServerHPOVectorStore(embeddings_path)
        
        print(f"Vector store initialized: {vectorstore is not None}")
        print(f"API key configured: {bool(vectorstore.api_key)}")
        print(f"Embeddings path exists: {os.path.exists(embeddings_path)}")
        
        # Test loading (this will likely fail without real API key, but should handle gracefully)
        try:
            success = vectorstore.load_vectorstore()
            print(f"Vector store load success: {success}")
        except Exception as e:
            print(f"Vector store load failed (expected): {str(e)[:100]}...")
        
    finally:
        # Clean up
        if 'VOYAGE_API_KEY' in os.environ:
            del os.environ['VOYAGE_API_KEY']

if __name__ == "__main__":
    print("VOYAGE API Key Configuration Test")
    print("="*60)
    
    try:
        test_api_key_config_without_key()
        test_api_key_config_with_env_var()
        test_api_key_config_with_env_file()
        test_server_hpo_vectorstore()
        
        print("\\n✅ Configuration tests completed!")
        print("\\nTo configure your API key:")
        print("1. Get API key from https://www.voyageai.com/")
        print("2. Set environment variable: export VOYAGE_API_KEY='your_key'")
        print("3. Or create .env file in project root with: VOYAGE_API_KEY=your_key")
        
    except Exception as e:
        print(f"\\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()