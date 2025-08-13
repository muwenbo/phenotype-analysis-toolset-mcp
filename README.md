# Phenotype Analysis Toolset

[![smithery badge](https://smithery.ai/badge/@muwenbo/phenotype-analysis-toolset-mcp)](https://smithery.ai/server/@muwenbo/phenotype-analysis-toolset-mcp)

A comprehensive AI-powered phenotype analysis system that provides advanced semantic search and structured workflows for mapping clinical symptoms to HPO (Human Phenotype Ontology) terms. Built with FastMCP framework, supporting both Chinese and English medical terminology with RAG-based analysis.

## Key Features

🔍 **Advanced Semantic Search**
- Vector-based HPO term matching using FAISS + VoyageAI embeddings
- High-accuracy similarity search (0.5-0.6 confidence scores)
- Support for both Chinese and English medical terminology

🧬 **Comprehensive Database Queries** 
- Bidirectional mappings between phenotypes, genes, and diseases
- 6 core relationship query functions with >100K annotations
- Real-time database health monitoring

🌐 **Multilingual Clinical Analysis**
- Chinese phenotype analysis with translation and standardization
- English phenotype analysis with streamlined processing  
- Structured 4-step workflows with confidence scoring

⚙️ **Robust Architecture**
- FastMCP-based server with path-independent operations
- SQLite database with comprehensive test suite
- Graceful error handling and API key management

## Project Structure

```
.
├── mcp_server.py              # Main FastMCP server with 11 tools
├── api_server.py              # Alternative FastAPI REST interface  
├── hpo_annotations.db         # SQLite database with phenotype data
├── embeddings/voyage_3/       # FAISS vector store for semantic search
├── data/                      # Raw HPO and gene-disease data files
│   ├── phenotype.hpoa         # HPO annotations (100K+ entries)
│   ├── hp.json                # HPO ontology structure
│   ├── genes_to_disease.txt   # Gene-disease mappings
│   └── phenotype_to_genes.txt # Phenotype-gene associations
├── src/                       # Core analysis modules
│   ├── phenotype_analysis_rag.py # RAG-based phenotype processing
│   ├── embedding.py           # Vector embedding utilities
│   └── utils.py              # Common utilities
├── scripts/                   # Database and embedding setup
│   ├── create_db.py          # Initialize SQLite database
│   ├── populate_db.py        # Load data into database
│   ├── generate_embeddings.py # Create FAISS vector store
│   └── update_gene_ids.py    # Update gene identifiers
├── tests/                     # Comprehensive test suite
│   ├── test_search_hpo_terms.py # Vector search validation
│   ├── test_voyage_api_key_config.py # API key configuration
│   └── test_path_independence.py # Cross-directory functionality
└── test_search_hpo_terms.py  # Main HPO search testing script
```

## Available MCP Tools

### 🔍 Core Database Queries
- `get_genes_by_hpo(hpo_id)` - Get genes associated with HPO term
- `get_hpo_by_gene(gene_id)` - Get HPO terms for specific gene  
- `get_diseases_by_gene(gene_id)` - Get diseases associated with gene
- `get_genes_by_disease(disease_id)` - Get genes linked to disease
- `get_diseases_by_hpo(hpo_id)` - Get diseases for HPO term
- `get_hpo_by_disease(disease_id)` - Get HPO terms for disease
- `get_hpo_name_by_id(hpo_id)` - Resolve HPO ID to human-readable name

### 🧠 Semantic Search & Analysis  
- `search_hpo_for_symptom(english_symptom, k=5)` - Vector-based HPO term matching
- `chinese_phenotype_anaylysis_workflow()` - 4-step Chinese clinical text analysis
- `english_phenotype_analysis_workflow()` - Streamlined English phenotype analysis

### ⚙️ System Management
- `get_server_status()` - Database health, embeddings status, table statistics
- `get_api_key_configuration()` - VOYAGE_API_KEY setup and validation

## Quick Start

### Installing via Smithery

To install phenotype-analysis-toolset-mcp for Claude Desktop automatically via [Smithery](https://smithery.ai/server/@muwenbo/phenotype-analysis-toolset-mcp):

```bash
npx -y @smithery/cli install @muwenbo/phenotype-analysis-toolset-mcp --client claude
```

### 1. Installation
```bash
git clone <repository-url>
cd phenotype_analysis_toolset
pip install -r requirements.txt
```

### 2. API Key Configuration
Get your VoyageAI API key from [voyage.ai](https://www.voyageai.com) and configure it:

**Option A: Environment Variable**
```bash
export VOYAGE_API_KEY='your_voyage_api_key_here'
```

**Option B: .env File**
```bash
echo "VOYAGE_API_KEY=your_voyage_api_key_here" > .env
```

### 3. Database Setup
```bash
# Create and populate database (one-time setup)
python3 scripts/create_db.py
python3 scripts/populate_db.py  
python3 scripts/update_gene_ids.py

# Generate semantic search embeddings (requires API key)
python3 scripts/generate_embeddings.py
```

### 4. Run the Server
```bash
# Start FastMCP server (primary interface)
python3 mcp_server.py

# OR start FastAPI server (REST interface)
uvicorn api_server:app --reload --port 8000
```

### 5. Test the Setup
```bash
# Validate vector search functionality
python3 test_search_hpo_terms.py

# Test from different directory (path independence)
cd /tmp && python3 /path/to/phenotype_analysis_toolset/test_search_hpo_terms.py
```

## Usage Examples

### Basic Database Queries
```python
# Get genes associated with developmental delay
result = get_genes_by_hpo("HP:0001263")  
# Returns: {"hpo_id": "HP:0001263", "hpo_name": "Global developmental delay", "genes": [...]}

# Get HPO terms for a specific gene  
result = get_hpo_by_gene("2260")
# Returns: {"ncbi_gene_id": "2260", "gene_symbol": "FGFR1", "hpo_terms": [...]}
```

### Semantic Search
```python
# Search for HPO terms matching English symptoms
result = search_hpo_for_symptom("developmental delay", k=5)
# Returns top 5 HPO candidates with similarity scores

# Example result:
{
  "symptom": "developmental delay",
  "candidates": [
    {
      "hpo_id": "http://purl.obolibrary.org/obo/HP_0001263",
      "hpo_name": "Global developmental delay", 
      "similarity_score": 0.534,
      "description": "..."
    }
  ]
}
```

### Clinical Text Analysis Workflows

**Chinese Phenotype Analysis:**
```python
workflow = chinese_phenotype_anaylysis_workflow()
# Returns 4-step workflow for Chinese clinical text:
# 1. Extract symptoms with Chinese → English translation
# 2. Vector search for each symptom  
# 3. LLM-based HPO term selection
# 4. Compile results with confidence scoring
```

**English Phenotype Analysis:**
```python  
workflow = english_phenotype_analysis_workflow()
# Returns streamlined 4-step workflow for English text:
# 1. Extract and standardize symptoms
# 2. Vector search for each symptom
# 3. Select best HPO matches
# 4. Compile results
```

### System Status Monitoring
```python
status = get_server_status()
# Returns comprehensive system health check:
{
  "status": "healthy",
  "database": {"exists": true, "size_mb": 45.2, "tables": {...}},
  "embeddings": {"vector_store": "loaded successfully", "api_key_status": "configured"},
  "server_info": {"framework": "FastMCP", "python_version": "3.12.7"}
}
```

## Data Sources & Statistics

- **HPO Annotations**: 100,000+ phenotype-disease associations from phenotype.hpoa
- **Gene-Disease Mappings**: Comprehensive OMIM and database cross-references  
- **Phenotype-Gene Links**: Curated associations with NCBI gene identifiers
- **Vector Embeddings**: 10,000+ HPO terms with VoyageAI semantic embeddings
- **Supported Languages**: English and Chinese medical terminology

## Architecture Details

### Vector Search Engine
- **Model**: VoyageAI Voyage-3 embeddings (1536 dimensions)
- **Index**: FAISS for high-performance similarity search
- **Performance**: Sub-second search across 10K+ HPO terms
- **Accuracy**: 0.5-0.6 similarity scores for clinically relevant matches

### Database Schema
```sql
-- Core tables with relationship mappings
hpo_annotations      -- HPO_ID → Disease mappings (100K+ rows)
genes_to_disease     -- Gene → Disease relationships  
genes_to_phenotype   -- Gene → HPO bidirectional mappings
phenotype_to_genes   -- HPO → Gene reverse mappings
```

### Workflow Processing
- **Chinese Pipeline**: Extract → Translate → Standardize → Search → Select → Map
- **English Pipeline**: Extract → Standardize → Search → Select → Map  
- **Confidence Thresholds**: 0.7+ for reliable clinical mappings
- **Error Handling**: Graceful degradation with detailed error reporting
