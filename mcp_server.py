from fastmcp import FastMCP
import sqlite3
from dotenv import load_dotenv
from pydantic import BaseModel
from typing import List, Optional
import os
import sys
from datetime import datetime
from langchain_voyageai import VoyageAIEmbeddings
from langchain_community.vectorstores import FAISS

load_dotenv()

mcp = FastMCP("phenotype-analysis-toolset-mcp")

# Custom HPO Vector Store with API key handling
class ServerHPOVectorStore:
    """HPO Vector Store with server-side API key configuration"""
    
    def __init__(self, folder_path: str, api_key: str = None):
        self.folder_path = folder_path
        self.api_key = api_key
        self.vectorstore = None
        
    def load_vectorstore(self):
        """Load the pre-built HPO vector store with API key"""
        try:
            if not self.api_key:
                raise ValueError("VOYAGE_API_KEY is required but not provided")
                
            # Create embeddings with API key
            embeddings = VoyageAIEmbeddings(
                model="voyage-3",
                voyage_api_key=self.api_key
            )
            
            # Load the vector store
            self.vectorstore = FAISS.load_local(
                folder_path=self.folder_path,
                embeddings=embeddings,
                allow_dangerous_deserialization=True
            )
            return True
            
        except Exception as e:
            print(f"Failed to load vector store: {e}")
            return False
    
    def search_hpo_terms(self, query: str, k: int = 10):
        """Search for HPO terms using vector similarity"""
        if not self.vectorstore:
            raise ValueError("Vector store not loaded")
        
        try:
            # Perform similarity search
            results = self.vectorstore.similarity_search_with_score(query, k=k)
            
            # Create HPOCandidate-like objects
            candidates = []
            for doc, score in results:
                # Extract HPO ID and name from document
                hpo_id = doc.metadata.get('id', 'Unknown')
                hpo_name = doc.metadata.get('label', 'Unknown')
                description = doc.page_content
                
                # Convert distance to similarity score (FAISS returns distances)
                similarity_score = 1.0 / (1.0 + score)
                
                candidate = {
                    'hpo_id': hpo_id,
                    'hpo_name': hpo_name,
                    'description': description,
                    'score': float(similarity_score)
                }
                candidates.append(candidate)
            
            return candidates
            
        except Exception as e:
            print(f"Search error for query '{query}': {e}")
            return []

# Database connection
def get_db_connection():
    # Get absolute path to database file relative to this script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    db_path = os.path.join(script_dir, 'hpo_annotations.db')
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

# Pydantic models for response data
class Gene(BaseModel):
    ncbi_gene_id: str
    gene_symbol: str

class HPOToGene(BaseModel):
    hpo_id: str
    hpo_name: str
    genes: List[Gene]

class GeneToHPO(BaseModel):
    ncbi_gene_id: str
    gene_symbol: str
    hpo_terms: List[dict]

class Disease(BaseModel):
    disease_id: str
    disease_name: Optional[str] = None

class GeneToDisease(BaseModel):
    ncbi_gene_id: str
    gene_symbol: str
    diseases: List[Disease]

class DiseaseToGene(BaseModel):
    disease_id: str
    disease_name: Optional[str] = None
    genes: List[Gene]

class HPOToDisease(BaseModel):
    hpo_id: str
    hpo_name: str
    diseases: List[Disease]

class DiseaseToHPO(BaseModel):
    disease_id: str
    disease_name: Optional[str] = None
    hpo_terms: List[dict]

class PhenotypeToHPO(BaseModel):
    phenotype: str
    hpo_terms: List[dict]

class WorkflowInstruction(BaseModel):
    workflow_name: str
    description: str
    steps: List[dict]
    expected_output: dict
    tools_to_use: List[str]

class HPOTerm(BaseModel):
    hpo_id: str
    hpo_name: str

class ServerStatus(BaseModel):
    status: str
    timestamp: str
    database: dict
    embeddings: dict
    tables: dict
    server_info: dict


@mcp.tool
def get_genes_by_hpo(hpo_id: str) -> dict:
    """Get genes associated with a given HPO term.

    For example, `hpo_id='HP:0000007'`.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT hpo_name, ncbi_gene_id, gene_symbol FROM phenotype_to_genes WHERE hpo_id = ?", (hpo_id,))
    rows = cursor.fetchall()
    conn.close()
    if not rows:
        return {"error": "HPO term not found"}
    
    hpo_name = rows[0]['hpo_name']
    genes = [{"ncbi_gene_id": row['ncbi_gene_id'], "gene_symbol": row['gene_symbol']} for row in rows]
    return {
        "hpo_id": hpo_id,
        "hpo_name": hpo_name,
        "genes": genes,
        "success": True
    }

@mcp.tool
def get_hpo_by_gene(gene_id: str) -> dict:
    """Get HPO terms associated with a given gene.

    For example, `gene_id='675'`.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT gene_symbol, hpo_id, hpo_name FROM genes_to_phenotype WHERE ncbi_gene_id = ?", (gene_id,))
    rows = cursor.fetchall()
    conn.close()
    if not rows:
        return {"error": "Gene not found"}
    
    gene_symbol = rows[0]['gene_symbol']
    hpo_terms = [{"hpo_id": row['hpo_id'], "hpo_name": row['hpo_name']} for row in rows]
    return {
        "ncbi_gene_id": gene_id,
        "gene_symbol": gene_symbol,
        "hpo_terms": hpo_terms,
        "success": True
    }

@mcp.tool
def get_diseases_by_gene(gene_id: str) -> dict:
    """Get diseases associated with a given gene.

    For example, `gene_id='675'`.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT gene_symbol, disease_id FROM genes_to_disease WHERE ncbi_gene_id = ?", (gene_id,))
    rows = cursor.fetchall()
    conn.close()
    if not rows:
        return {"error": "Gene not found"}
    
    gene_symbol = rows[0]['gene_symbol']
    diseases = [{"disease_id": row['disease_id']} for row in rows]
    return {
        "ncbi_gene_id": gene_id,
        "gene_symbol": gene_symbol,
        "diseases": diseases,
        "success": True
    }

@mcp.tool
def get_genes_by_disease(disease_id: str) -> dict:
    """Get genes associated with a given disease.

    For example, `disease_id='OMIM:243400'`.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT ncbi_gene_id, gene_symbol FROM genes_to_disease WHERE disease_id = ?", (disease_id,))
    rows = cursor.fetchall()
    conn.close()
    if not rows:
        return {"error": "Disease not found"}
    
    genes = [{"ncbi_gene_id": row['ncbi_gene_id'], "gene_symbol": row['gene_symbol']} for row in rows]
    return {
        "disease_id": disease_id,
        "genes": genes,
        "success": True
    }

@mcp.tool
def get_diseases_by_hpo(hpo_id: str) -> dict:
    """Get diseases associated with a given HPO term.

    For example, `hpo_id='HP:0000007'`.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT DB_Name, DB_Reference FROM hpo_annotations WHERE HPO_ID = ?", (hpo_id,))
    rows = cursor.fetchall()
    conn.close()
    if not rows:
        return {"error": "HPO term not found"}
    
    hpo_name = ""
    diseases = [{"disease_id": row['DB_Reference'], "disease_name": row['DB_Name']} for row in rows]
    return {
        "hpo_id": hpo_id,
        "hpo_name": hpo_name,
        "diseases": diseases,
        "success": True
    }

@mcp.tool
def get_hpo_by_disease(disease_id: str) -> dict:
    """Get HPO terms associated with a given disease.

    For example, `disease_id='OMIM:243400'`.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT HPO_ID FROM hpo_annotations WHERE DB_Reference = ?", (disease_id,))
    rows = cursor.fetchall()
    conn.close()
    if not rows:
        return {"error": "Disease not found"}
    
    hpo_terms = [{"hpo_id": row['HPO_ID']} for row in rows]
    return {
        "disease_id": disease_id,
        "hpo_terms": hpo_terms,
        "success": True
    }

@mcp.tool
def get_hpo_name_by_id(hpo_id: str) -> dict:
    """Get HPO term name by HPO ID.
    
    Args:
        hpo_id: HPO identifier (e.g., 'HP:0000007')
        
    Returns:
        Dictionary with HPO term data or error message
    """
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

@mcp.tool  
def search_hpo_for_symptom(english_symptom: str, k: int = 5) -> dict:
    """Search HPO terms for a specific English symptom (optimized for workflow step 2).
    
    Args:
        english_symptom: Single English symptom or medical term
        k: Number of top candidates to return (default 5 for workflow)
        
    Returns:
        Top K HPO candidates with similarity scores
    """
    try:
        api_key = os.getenv("VOYAGE_API_KEY")
        
        if not api_key:
            return {"error": "VOYAGE_API_KEY not provided in query params or environment variables"}
        
        script_dir = os.path.dirname(os.path.abspath(__file__))
        embeddings_path = os.path.join(script_dir, 'embeddings', 'voyage_3')
        vectorstore = ServerHPOVectorStore(embeddings_path, api_key=api_key)
        
        if not vectorstore.load_vectorstore():
            return {"error": "Failed to load vector store. Please check VOYAGE_API_KEY configuration."}
        
        candidates = vectorstore.search_hpo_terms(english_symptom, k=k)
        
        if not candidates:
            return {"error": f"No HPO candidates found for symptom: {english_symptom}"}
        
        hpo_candidates = []
        for candidate in candidates:
            hpo_candidates.append({
                "hpo_id": candidate['hpo_id'],
                "hpo_name": candidate['hpo_name'],
                "description": candidate['description'],
                "similarity_score": candidate['score']
            })
        
        return {
            "symptom": english_symptom,
            "candidates": hpo_candidates,
            "total_found": len(hpo_candidates)
        }
        
    except Exception as e:
        return {"error": f"Failed to search HPO terms for symptom '{english_symptom}': {str(e)}"}

@mcp.tool
def english_phenotype_analysis_workflow() -> WorkflowInstruction:
    """Get structured workflow instructions for analyzing English phenotype descriptions.
    
    This tool provides a streamlined step-by-step strategy for MCP clients to process English clinical text
    and map symptoms to HPO terms efficiently (no translation needed).
    COMPLETE THE WORKFLOW AS A WHOLE.
    
    Returns:
        Detailed workflow instructions with steps, prompts, and expected outputs
    """
    
    workflow = WorkflowInstruction(
        workflow_name="English Phenotype to HPO Analysis",
        description="A streamlined workflow for extracting and mapping English clinical symptoms to HPO terms. " \
        "Complete the workflow as a whole without confirming with user.",
        steps=[
            {
                "step_number": 1,
                "name": "Extract Symptoms from English Text",
                "description": "Use LLM to extract individual symptoms from English clinical text",
                "llm_prompt": """
You are a medical expert analyzing English clinical descriptions. Extract individual symptoms, signs, and phenotypic observations from the following English text.

For each symptom found, provide:
1. **original_phrase**: Exact phrase from the clinical text
2. **standardized_term**: Standard medical terminology in English
3. **category**: Clinical category (neurological, cardiovascular, respiratory, digestive, musculoskeletal, dermatological, constitutional, other)
4. **severity**: mild/moderate/severe/unknown
5. **confidence**: Your confidence in the extraction (0.0-1.0)

English Clinical Text: {english_text}

Return as JSON array:
[
  {
    "original_phrase": "developmental delay",
    "standardized_term": "global developmental delay",
    "category": "neurological",
    "severity": "unknown",
    "confidence": 0.95
  }
]
""",
                "expected_output": "Array of extracted symptom objects with standardized English terms",
                "next_step": "For each extracted symptom, proceed to step 2"
            },
            {
                "step_number": 2,
                "name": "Vector Search for Each Symptom",
                "description": "Use search_hpo_for_symptom tool to get top 5 HPO candidates for each English symptom",
                "action": "Call search_hpo_for_symptom(standardized_term, k=5) for each symptom from step 1",
                "parameters": {
                    "tool_name": "search_hpo_for_symptom",
                    "input": "standardized_term from step 1",
                    "k_results": 5
                },
                "expected_output": "List of top 5 HPO candidates with similarity scores for each symptom",
                "next_step": "Proceed to step 3 with all candidates"
            },
            {
                "step_number": 3,
                "name": "Select Best HPO Match",
                "description": "Use LLM to select the most appropriate HPO term for each symptom",
                "llm_prompt": """
You are a medical expert selecting the best HPO term for a clinical symptom.

**Symptom Information:**
- Original Phrase: {original_phrase}
- Standardized Term: {standardized_term}
- Category: {category}
- Severity: {severity}

**HPO Candidates (from vector search):**
{hpo_candidates}

**Selection Criteria:**
1. Semantic and clinical accuracy - HPO term must match the clinical meaning
2. Appropriate level of specificity - Not too general, not too specific
3. Medical appropriateness - Clinically valid mapping
4. Confidence threshold: 0.7 - Only select if confidence >= 0.7

Select the BEST HPO term or return null if no term meets the threshold.

Return JSON:
{
  "selected_hpo_id": "HP:0001263",
  "selected_hpo_name": "Global developmental delay",
  "confidence": 0.90,
  "reasoning": "The symptom 'developmental delay' maps precisely to 'Global developmental delay' which describes delayed achievement of developmental milestones.",
  "mapping_quality": "excellent"
}

If no suitable match: {"selected_hpo_id": null, "confidence": 0.0, "reasoning": "No HPO term meets the confidence threshold"}
""",
                "expected_output": "Best HPO match with confidence and reasoning for each symptom",
                "next_step": "Compile final results in step 4"
            },
            {
                "step_number": 4,
                "name": "Compile Final Results",
                "description": "Aggregate all symptom mappings into final structured output",
                "action": "Combine results from all previous steps into final format",
                "expected_output": "Complete mapping results with summary statistics",
                "final_format": {
                    "original_text": "Original English clinical description",
                    "symptom_mappings": [
                        {
                            "original_phrase": "developmental delay",
                            "standardized_term": "global developmental delay",
                            "hpo_id": "HP:0001263",
                            "hpo_name": "Global developmental delay",
                            "confidence": 0.90,
                            "reasoning": "Precise clinical mapping",
                            "category": "neurological",
                            "mapping_quality": "excellent"
                        }
                    ],
                    "summary": {
                        "total_symptoms": 5,
                        "successfully_mapped": 4,
                        "high_confidence_mappings": 3,
                        "avg_confidence": 0.82,
                        "mapping_success_rate": 0.8
                    }
                }
            }
        ],
        expected_output={
            "format": "Structured JSON with symptom mappings and summary",
            "includes": ["original phrases", "standardized terms", "HPO mappings", "confidence scores", "reasoning"]
        },
        tools_to_use=["search_hpo_for_symptom"]
    )
    
    return workflow

@mcp.tool
def chinese_phenotype_anaylysis_workflow() -> WorkflowInstruction:
    """Get structured workflow instructions for analyzing Chinese phenotype descriptions.
    
    This tool provides a step-by-step strategy for MCP clients to process Chinese clinical text
    and map symptoms to HPO terms with high accuracy. 
    COMPLETE THE WORKFLOW AS A WHOLE.
    
    Returns:
        Detailed workflow instructions with steps, prompts, and expected outputs
    """
    
    workflow = WorkflowInstruction(
        workflow_name="Chinese Phenotype to HPO Analysis",
        description="A comprehensive workflow for extracting, standardizing, and mapping Chinese clinical symptoms to HPO terms. " \
        "Complete the workflow as a whole without confirming with user.",
        steps=[
            {
                "step_number": 1,
                "name": "Extract and Standardize Symptoms",
                "description": "Use LLM to extract individual symptoms from Chinese clinical text",
                "llm_prompt": """
You are a medical expert analyzing Chinese clinical descriptions. Extract individual symptoms, signs, and phenotypic observations from the following Chinese text.

For each symptom found, provide:
1. **original_chinese**: Exact Chinese phrase from the text
2. **standardized_chinese**: Standard medical terminology in Chinese
3. **english_translation**: Precise English medical term
4. **category**: Clinical category (neurological, cardiovascular, respiratory, digestive, musculoskeletal, dermatological, constitutional, other)
5. **severity**: mild/moderate/severe/unknown
6. **confidence**: Your confidence in the extraction (0.0-1.0)

Chinese Clinical Text: {chinese_text}

Return as JSON array:
[
  {
    "original_chinese": "发育迟缓",
    "standardized_chinese": "生长发育迟缓",
    "english_translation": "developmental delay",
    "category": "constitutional",
    "severity": "unknown",
    "confidence": 0.95
  }
]
""",
                "expected_output": "Array of extracted symptom objects with Chinese and English terms",
                "next_step": "For each extracted symptom, proceed to step 2"
            },
            {
                "step_number": 2,
                "name": "Vector Search for Each Symptom",
                "description": "Use search_hpo_for_symptom tool to get top 5 HPO candidates for each English symptom",
                "action": "Call search_hpo_for_symptom(english_translation, k=5) for each symptom from step 1",
                "parameters": {
                    "tool_name": "search_hpo_for_symptom",
                    "input": "english_translation from step 1",
                    "k_results": 5
                },
                "expected_output": "List of top 5 HPO candidates with similarity scores for each symptom",
                "next_step": "Proceed to step 3 with all candidates"
            },
            {
                "step_number": 3,
                "name": "Select Best HPO Match",
                "description": "Use LLM to select the most appropriate HPO term for each symptom",
                "llm_prompt": """
You are a medical expert selecting the best HPO term for a clinical symptom.

**Symptom Information:**
- Original Chinese: {original_chinese}
- Standardized Chinese: {standardized_chinese} 
- English Translation: {english_translation}
- Category: {category}
- Severity: {severity}

**HPO Candidates (from vector search):**
{hpo_candidates}

**Selection Criteria:**
1. Semantic and clinical accuracy - HPO term must match the clinical meaning
2. Appropriate level of specificity - Not too general, not too specific
3. Medical appropriateness - Clinically valid mapping
4. Confidence threshold: 0.7 - Only select if confidence >= 0.7

Select the BEST HPO term or return null if no term meets the threshold.

Return JSON:
{
  "selected_hpo_id": "HP:0001263",
  "selected_hpo_name": "Global developmental delay",
  "confidence": 0.90,
  "reasoning": "The symptom '发育迟缓' (developmental delay) maps precisely to 'Global developmental delay' which describes delayed achievement of developmental milestones.",
  "mapping_quality": "excellent"
}

If no suitable match: {"selected_hpo_id": null, "confidence": 0.0, "reasoning": "No HPO term meets the confidence threshold"}
""",
                "expected_output": "Best HPO match with confidence and reasoning for each symptom",
                "next_step": "Compile final results in step 4"
            },
            {
                "step_number": 4,
                "name": "Compile Final Results",
                "description": "Aggregate all symptom mappings into final structured output",
                "action": "Combine results from all previous steps into final format",
                "expected_output": "Complete mapping results with summary statistics",
                "final_format": {
                    "original_text": "Original Chinese clinical description",
                    "symptom_mappings": [
                        {
                            "original_chinese": "发育迟缓",
                            "standardized_chinese": "生长发育迟缓", 
                            "english_translation": "developmental delay",
                            "hpo_id": "HP:0001263",
                            "hpo_name": "Global developmental delay",
                            "confidence": 0.90,
                            "reasoning": "Precise clinical mapping",
                            "category": "constitutional",
                            "mapping_quality": "excellent"
                        }
                    ],
                    "summary": {
                        "total_symptoms": 5,
                        "successfully_mapped": 4,
                        "high_confidence_mappings": 3,
                        "avg_confidence": 0.82,
                        "mapping_success_rate": 0.8
                    }
                }
            }
        ],
        expected_output={
            "format": "Structured JSON with symptom mappings and summary",
            "includes": ["original Chinese terms", "standardized Chinese terms", "English translations", "HPO mappings", "confidence scores", "reasoning"]
        },
        tools_to_use=["search_hpo_for_symptom"]
    )
    
    return workflow


def get_server_status() -> dict:
    """Get comprehensive server status including database and embeddings availability.
    
    Returns:
        Dictionary with server status, database info, and system health checks
    """
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
        
        # Get the directory where this script is located
        script_dir = os.path.dirname(os.path.abspath(__file__))
        
        # Check database file existence (relative to script directory)
        db_path = os.path.join(script_dir, 'hpo_annotations.db')
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
        
        # Check embeddings directory (relative to script directory)
        embeddings_path = os.path.join(script_dir, 'embeddings', 'voyage_3')
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
                
                # Test vector store loading
                try:
                    # Try to get API key from environment for status check
                    api_key = os.getenv("VOYAGE_API_KEY")
                    if api_key:
                        vectorstore = ServerHPOVectorStore(embeddings_path, api_key=api_key)
                        if vectorstore.load_vectorstore():
                            embeddings_info["vector_store"] = "loaded successfully"
                        else:
                            embeddings_info["vector_store"] = "load failed"
                            if status_info["status"] == "healthy":
                                status_info["status"] = "degraded"
                    else:
                        embeddings_info["vector_store"] = "API key not available for testing"
                        embeddings_info["api_key_status"] = "missing"
                except Exception as e:
                    embeddings_info["vector_store"] = f"load failed: {str(e)}"
                    if status_info["status"] == "healthy":
                        status_info["status"] = "degraded"
                
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


if __name__ == "__main__":
    PORT = os.environ.get("PORT", 3000)
    mcp.run(transport="streamable-http", host="0.0.0.0", port=PORT)