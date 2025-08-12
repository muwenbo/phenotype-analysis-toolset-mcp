#!/usr/bin/env python3
"""
Test script for get_server_status function in mcp_server.py

This script tests the server status functionality without the MCP wrapper.
"""

import sys
import os
import sqlite3
from datetime import datetime

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def get_db_connection():
    """Database connection function for testing"""
    conn = sqlite3.connect('hpo_annotations.db')
    conn.row_factory = sqlite3.Row
    return conn

def get_server_status_core():
    """Core logic of get_server_status function (without MCP decoration)"""
    try:
        timestamp = datetime.now().isoformat()
        status_info = {
            "status": "healthy",
            "timestamp": timestamp,
            "database": {},
            "embeddings": {},
            "tables": {},
            "server_info": {}
        }
        
        # Check database file existence
        db_path = 'hpo_annotations.db'
        if os.path.exists(db_path):
            db_size = os.path.getsize(db_path)
            db_modified = datetime.fromtimestamp(os.path.getmtime(db_path)).isoformat()
            
            status_info["database"] = {
                "exists": True,
                "path": db_path,
                "size_bytes": db_size,
                "size_mb": round(db_size / (1024 * 1024), 2),
                "last_modified": db_modified
            }
            
            # Test database connection and get table info
            try:
                conn = get_db_connection()
                cursor = conn.cursor()
                
                # Get all table names
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
                tables = [row[0] for row in cursor.fetchall()]
                
                # Get record counts for each table
                table_info = {}
                for table in tables:
                    try:
                        cursor.execute(f"SELECT COUNT(*) FROM {table}")
                        count = cursor.fetchone()[0]
                        table_info[table] = {
                            "record_count": count,
                            "status": "accessible"
                        }
                    except Exception as e:
                        table_info[table] = {
                            "record_count": 0,
                            "status": f"error: {str(e)}"
                        }
                
                status_info["tables"] = table_info
                
                # Test a simple query to verify database integrity
                cursor.execute("SELECT COUNT(*) FROM phenotype_to_genes WHERE hpo_id LIKE 'HP:%' LIMIT 1")
                hpo_count = cursor.fetchone()[0]
                
                status_info["database"]["connection"] = "successful"
                status_info["database"]["integrity_check"] = "passed"
                status_info["database"]["hpo_terms_count"] = hpo_count
                
                conn.close()
                
            except Exception as e:
                status_info["database"]["connection"] = f"failed: {str(e)}"
                status_info["database"]["integrity_check"] = "failed"
                status_info["status"] = "degraded"
                
        else:
            status_info["database"] = {
                "exists": False,
                "path": db_path,
                "error": f"Database file not found at {db_path}"
            }
            status_info["status"] = "error"
        
        # Check embeddings directory
        embeddings_path = './embeddings/voyage_3/'
        if os.path.exists(embeddings_path):
            try:
                # Check for key embedding files
                index_faiss = os.path.join(embeddings_path, 'index.faiss')
                index_pkl = os.path.join(embeddings_path, 'index.pkl')
                
                embeddings_info = {
                    "directory_exists": True,
                    "path": embeddings_path,
                    "files": {}
                }
                
                for file_name, file_path in [("index.faiss", index_faiss), ("index.pkl", index_pkl)]:
                    if os.path.exists(file_path):
                        file_size = os.path.getsize(file_path)
                        file_modified = datetime.fromtimestamp(os.path.getmtime(file_path)).isoformat()
                        embeddings_info["files"][file_name] = {
                            "exists": True,
                            "size_bytes": file_size,
                            "size_mb": round(file_size / (1024 * 1024), 2),
                            "last_modified": file_modified
                        }
                    else:
                        embeddings_info["files"][file_name] = {"exists": False}
                
                # Note: Skipping vector store loading test to avoid API key requirement
                embeddings_info["vector_store"] = "not tested (requires API key)"
                
                status_info["embeddings"] = embeddings_info
                
            except Exception as e:
                status_info["embeddings"] = {
                    "directory_exists": True,
                    "path": embeddings_path,
                    "error": f"Failed to check embeddings: {str(e)}"
                }
                if status_info["status"] == "healthy":
                    status_info["status"] = "degraded"
        else:
            status_info["embeddings"] = {
                "directory_exists": False,
                "path": embeddings_path,
                "error": "Embeddings directory not found"
            }
            if status_info["status"] == "healthy":
                status_info["status"] = "degraded"
        
        # Server info
        status_info["server_info"] = {
            "server_name": "Phenotype_Analysis_Toolset",
            "framework": "FastMCP",
            "python_version": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
            "working_directory": os.getcwd(),
        }
        
        return status_info
        
    except Exception as e:
        return {
            "status": "error",
            "timestamp": datetime.now().isoformat(),
            "error": f"Failed to get server status: {str(e)}",
            "database": {"exists": False, "error": "Unable to check"},
            "embeddings": {"directory_exists": False, "error": "Unable to check"}
        }

def print_status_report(status):
    """Print a formatted status report"""
    print("="*60)
    print("SERVER STATUS REPORT")
    print("="*60)
    
    print(f"Overall Status: {status['status'].upper()}")
    print(f"Timestamp: {status['timestamp']}")
    print()
    
    # Database status
    print("DATABASE:")
    db = status.get('database', {})
    if db.get('exists'):
        print(f"  ✅ File exists: {db['path']}")
        print(f"  📁 Size: {db['size_mb']} MB")
        print(f"  🔌 Connection: {db.get('connection', 'unknown')}")
        print(f"  ✔️  Integrity: {db.get('integrity_check', 'unknown')}")
        if 'hpo_terms_count' in db:
            print(f"  📊 HPO terms: {db['hpo_terms_count']}")
    else:
        print(f"  ❌ File missing: {db.get('path', 'unknown')}")
        if 'error' in db:
            print(f"  🚨 Error: {db['error']}")
    print()
    
    # Tables status
    print("TABLES:")
    tables = status.get('tables', {})
    for table_name, table_info in tables.items():
        count = table_info.get('record_count', 0)
        table_status = table_info.get('status', 'unknown')
        if table_status == 'accessible':
            print(f"  ✅ {table_name}: {count:,} records")
        else:
            print(f"  ❌ {table_name}: {table_status}")
    print()
    
    # Embeddings status
    print("EMBEDDINGS:")
    emb = status.get('embeddings', {})
    if emb.get('directory_exists'):
        print(f"  ✅ Directory exists: {emb['path']}")
        files = emb.get('files', {})
        for file_name, file_info in files.items():
            if file_info.get('exists'):
                size_mb = file_info.get('size_mb', 0)
                print(f"  ✅ {file_name}: {size_mb} MB")
            else:
                print(f"  ❌ {file_name}: missing")
        vs_status = emb.get('vector_store', 'unknown')
        print(f"  🔍 Vector store: {vs_status}")
    else:
        print(f"  ❌ Directory missing: {emb.get('path', 'unknown')}")
    print()
    
    # Server info
    print("SERVER INFO:")
    server = status.get('server_info', {})
    for key, value in server.items():
        print(f"  📋 {key.replace('_', ' ').title()}: {value}")


if __name__ == "__main__":
    print("Server Status Test")
    print("=" * 30)
    
    try:
        status = get_server_status_core()
        print_status_report(status)
        
        # Exit with appropriate code
        if status['status'] == 'healthy':
            print("\\n🎉 Server is healthy!")
            sys.exit(0)
        elif status['status'] == 'degraded':
            print("\\n⚠️  Server is degraded but functional")
            sys.exit(1)
        else:
            print("\\n🚨 Server has critical issues")
            sys.exit(2)
            
    except Exception as e:
        print(f"\\n💥 Failed to get server status: {e}")
        sys.exit(3)