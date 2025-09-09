# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a comprehensive phenotype analysis toolset that provides a FastMCP-based server for querying relationships between phenotypes, genes, and diseases. The system features advanced semantic search capabilities, multilingual phenotype analysis workflows, and robust HPO (Human Phenotype Ontology) term mapping using RAG (Retrieval-Augmented Generation) approaches.

## Architecture

The project uses a FastMCP server as the primary interface:
- **FastMCP Server** (`mcp_server.py`): Main server implementation with comprehensive MCP tools
- **Alternative FastAPI Server** (`api_server.py`): REST API interface for web applications

### Core Components:
- **Database Layer**: SQLite database (`hpo_annotations.db`) with comprehensive phenotype-gene-disease relationships
- **Vector Search System**: FAISS vector store with VoyageAI embeddings for semantic HPO term matching (`embeddings/voyage_3/`)
- **RAG Pipeline**: Advanced phenotype analysis supporting Chinese and English clinical text (`src/phenotype_analysis_rag.py`)
- **Workflow Engines**: Structured analysis workflows for both Chinese and English phenotype descriptions
- **Data Processing Scripts**: Automated database setup and embedding generation (`scripts/`)

## Development Commands

### Initial Setup
```bash
# Install dependencies
pip install -r requirements.txt

# Configure API keys (choose one method)
export VOYAGE_API_KEY='your_voyage_api_key'
# OR create .env file with: VOYAGE_API_KEY=your_voyage_api_key

# Create and populate database
python3 scripts/create_db.py
python3 scripts/populate_db.py
python3 scripts/update_gene_ids.py

# Generate embeddings for semantic search (requires VOYAGE_API_KEY)
python3 scripts/generate_embeddings.py
```

### Running Servers
```bash
# Run FastMCP server (primary)
python3 mcp_server.py

# Run FastAPI server (alternative)
uvicorn api_server:app --reload
```

### Data Management
```bash
# Recreate database from scratch
python3 scripts/create_db.py
python3 scripts/populate_db.py
python3 scripts/update_gene_ids.py

# Regenerate embeddings after data updates
python3 scripts/generate_embeddings.py
```

## Key Features

### Core Database Queries
The system provides 6 main relationship query functions:
- HPO term → genes (`get_genes_by_hpo`)
- Gene → HPO terms (`get_hpo_by_gene`) 
- Gene → diseases (`get_diseases_by_gene`)
- Disease → genes (`get_genes_by_disease`)
- HPO term → diseases (`get_diseases_by_hpo`)
- Disease → HPO terms (`get_hpo_by_disease`)
- HPO ID → HPO name (`get_hpo_name_by_id`)

### Advanced Semantic Search
- **Vector-based HPO search** (`search_hpo_for_symptom`): Semantic matching of English symptoms to HPO terms
- **Multilingual support**: Handles both Chinese and English medical terminology
- **FAISS + VoyageAI embeddings**: High-performance similarity search with 0.5-0.6 accuracy scores

### Structured Analysis Workflows
- **Chinese Phenotype Analysis** (`chinese_phenotype_analysis_workflow`): 4-step workflow with extraction, translation, vector search, and HPO mapping
- **English Phenotype Analysis** (`english_phenotype_analysis_workflow`): Streamlined 4-step workflow for English clinical text
- **Confidence scoring**: 0.7+ threshold for reliable mappings
- **Clinical categorization**: Neurological, cardiovascular, respiratory, etc.

### System Management
- **Server status monitoring** (`get_server_status`): Database health, embeddings availability, table statistics
- **API key configuration** (`get_api_key_configuration`): VOYAGE_API_KEY setup instructions and status
- **Path independence**: Works correctly regardless of client working directory

## Data Sources

- **HPO Data**: Human Phenotype Ontology annotations (`data/phenotype.hpoa`, `data/hp.json`)
- **Gene-Disease Mappings**: OMIM and other disease databases (`data/genes_to_disease.txt`)
- **Gene-Phenotype Mappings**: Curated associations (`data/genes_to_phenotype.txt`, `data/phenotype_to_genes.txt`)

## Database Schema

The SQLite database contains tables for:
- `hpo_annotations`: HPO to disease mappings
- `genes_to_disease`: Gene to disease relationships  
- `genes_to_phenotype`: Gene to phenotype associations
- `phenotype_to_genes`: Reverse phenotype to gene mappings

## Development Notes

### File Paths and Configuration
- **Database**: Uses absolute paths for cross-directory compatibility (`hpo_annotations.db` in project root)
- **Embeddings**: Stored in `embeddings/voyage_3/` with FAISS index files (`index.faiss`, `index.pkl`)
- **API Key**: Server-side configuration with fallback to `.env` file for VOYAGE_API_KEY
- **Path Independence**: All file operations use absolute paths relative to script location

### API and Data Handling
- **MCP Tools**: Return dictionaries for consistent validation (not Pydantic models)
- **Metadata Extraction**: Uses `'id'` and `'label'` keys from FAISS vector store metadata
- **Error Handling**: Graceful degradation with informative error messages
- **Multilingual Support**: Chinese clinical text processing with translation and standardization

### Testing and Validation
- **Comprehensive Test Suite**: Located in `tests/` directory
- **Vector Search Testing**: `test_search_hpo_terms.py` validates semantic search functionality
- **API Key Testing**: Validates multiple configuration methods
- **Path Independence Testing**: Ensures functionality across different working directories

### Performance and Scalability
- **Vector Search**: FAISS-based similarity search with VoyageAI embeddings (voyage-3 model)
- **Confidence Scoring**: Similarity scores typically range 0.5-0.6 for relevant matches
- **Batch Processing**: Supports multiple phenotype descriptions in single workflow execution