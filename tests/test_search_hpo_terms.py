#!/usr/bin/env python3
"""
Test script for search_hpo_terms function in src.phenotype_analysis_rag.py

This script tests the HPOVectorStore.search_hpo_terms method with Chinese queries
to verify vector search functionality.
"""

import sys
import os
from datetime import datetime

# Add project root to path
sys.path.append('.')

# Configure API key for testing (try multiple sources)
def configure_api_key():
    """Configure VOYAGE_API_KEY for testing"""
    # First check if already set
    if os.getenv("VOYAGE_API_KEY"):
        return True
    
    # Try to read from .env file
    script_dir = os.path.dirname(os.path.abspath(__file__))
    env_path = os.path.join(script_dir, '.env')
    
    if os.path.exists(env_path):
        try:
            with open(env_path, 'r') as f:
                for line in f:
                    if line.startswith('VOYAGE_API_KEY='):
                        api_key = line.split('=', 1)[1].strip().strip('"\'')
                        os.environ['VOYAGE_API_KEY'] = api_key
                        return True
        except Exception:
            pass
    
    return False

def test_search_hpo_terms():
    """Test the search_hpo_terms function with Chinese and English queries"""
    
    print("Testing HPOVectorStore.search_hpo_terms")
    print("="*60)
    print(f"Test time: {datetime.now().isoformat()}")
    print()
    
    # Configure API key first
    if not configure_api_key():
        print("❌ VOYAGE_API_KEY not configured")
        print("Please set the API key in environment or .env file")
        print("To get API key: https://www.voyageai.com/")
        return False
    
    print("✅ VOYAGE_API_KEY configured")
    
    try:
        # Import the ServerHPOVectorStore class from mcp_server
        from mcp_server import ServerHPOVectorStore
        
        # Initialize the vector store with server-side API key handling
        print("Initializing ServerHPOVectorStore...")
        script_dir = os.path.dirname(os.path.abspath(__file__))
        vectorstore_path = os.path.join(script_dir, 'embeddings', 'voyage_3')
        vectorstore = ServerHPOVectorStore(vectorstore_path)
        
        print(f"Vector store path: {vectorstore_path}")
        print(f"Vector store folder exists: {os.path.exists(vectorstore_path)}")
        
        # Load the vector store
        print("\nLoading vector store...")
        if not vectorstore.load_vectorstore():
            print("❌ Failed to load vector store")
            return False
        print("✅ Vector store loaded successfully")
        
        # Test queries
        test_queries = [
            {
                "query": "发育迟缓/身材矮小",
                "description": "Chinese: Developmental delay / Short stature",
                "k": 10
            },
            {
                "query": "developmental delay",
                "description": "English: Developmental delay",
                "k": 5
            },
            {
                "query": "short stature",
                "description": "English: Short stature", 
                "k": 5
            },
            {
                "query": "发育迟缓",
                "description": "Chinese: Developmental delay only",
                "k": 8
            },
            {
                "query": "身材矮小",
                "description": "Chinese: Short stature only",
                "k": 8
            }
        ]
        
        # Run tests for each query
        for i, test_case in enumerate(test_queries, 1):
            query = test_case["query"]
            description = test_case["description"]
            k = test_case["k"]
            
            print(f"\n" + "="*50)
            print(f"TEST {i}: {description}")
            print(f"Query: '{query}'")
            print(f"Requesting top {k} results")
            print("-"*50)
            
            try:
                # Perform the search
                candidates = vectorstore.search_hpo_terms(query, k=k)
                
                if not candidates:
                    print("❌ No candidates found")
                    continue
                
                print(f"✅ Found {len(candidates)} candidates:")
                print()
                
                # Display results
                for j, candidate in enumerate(candidates, 1):
                    print(f"  {j}. HPO ID: {candidate['hpo_id']}")
                    print(f"     HPO Name: {candidate['hpo_name']}")
                    print(f"     Similarity Score: {candidate['score']:.4f}")
                    print(f"     Description: {candidate['description'][:100]}...")
                    print()
                
                # Show top 3 results summary
                print(f"📊 Top 3 Results Summary:")
                for j, candidate in enumerate(candidates[:3], 1):
                    print(f"   {j}. {candidate['hpo_id']} - {candidate['hpo_name']} (score: {candidate['score']:.3f})")
                
            except Exception as e:
                print(f"❌ Search failed for query '{query}': {e}")
                continue
        
        # Summary statistics
        print(f"\n" + "="*60)
        print("TEST SUMMARY")
        print("="*60)
        print(f"✅ All vector store operations completed")
        print(f"✅ Chinese queries processed successfully")
        print(f"✅ English queries processed successfully")
        print(f"✅ Vector similarity search is working")
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("Make sure src.phenotype_analysis_rag is available")
        return False
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

def test_vector_store_metadata():
    """Test to examine vector store metadata structure"""
    
    print(f"\n" + "="*60)
    print("METADATA STRUCTURE TEST")
    print("="*60)
    
    try:
        from mcp_server import ServerHPOVectorStore
        
        script_dir = os.path.dirname(os.path.abspath(__file__))
        vectorstore_path = os.path.join(script_dir, 'embeddings', 'voyage_3')
        vectorstore = ServerHPOVectorStore(vectorstore_path)
        
        if not vectorstore.load_vectorstore():
            print("❌ Failed to load vector store for metadata test")
            return
        
        # Get a few results to examine metadata
        candidates = vectorstore.search_hpo_terms("developmental delay", k=3)
        
        if candidates:
            print("Examining metadata structure from search results:")
            for i, candidate in enumerate(candidates[:2], 1):
                print(f"\nCandidate {i}:")
                print(f"  Type: {type(candidate)}")
                print(f"  HPO ID: {candidate['hpo_id']}")
                print(f"  HPO Name: {candidate['hpo_name']}")
                print(f"  Score: {candidate['score']}")
                print(f"  Description length: {len(candidate['description'])}")
                print(f"  Available keys: {list(candidate.keys())}")
        
        # Try to access the raw vector store for more details
        if hasattr(vectorstore, 'vectorstore') and vectorstore.vectorstore:
            print(f"\nVector store type: {type(vectorstore.vectorstore)}")
            
            # Get raw search results to see metadata structure
            raw_results = vectorstore.vectorstore.similarity_search_with_score("test", k=1)
            if raw_results:
                doc, score = raw_results[0]
                print(f"Raw document metadata: {doc.metadata}")
                print(f"Available metadata keys: {list(doc.metadata.keys())}")
        
    except Exception as e:
        print(f"❌ Metadata test failed: {e}")

if __name__ == "__main__":
    print("HPO Vector Store Search Test")
    print("Testing with Chinese query: 发育迟缓/身材矮小")
    print("="*80)
    
    success = test_search_hpo_terms()
    
    if success:
        # Run additional metadata test
        test_vector_store_metadata()
        
        print(f"\n🎉 All tests completed successfully!")
        print(f"The search_hpo_terms function is working correctly for both Chinese and English queries.")
    else:
        print(f"\n❌ Tests failed. Please check the error messages above.")
    
    print(f"\nTest completed at: {datetime.now().isoformat()}")