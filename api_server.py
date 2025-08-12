
from fastapi import FastAPI, HTTPException
import sqlite3
from pydantic import BaseModel
from typing import List, Optional

app = FastAPI()

# Database connection
def get_db_connection():
    conn = sqlite3.connect('hpo_annotations.db')
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

@app.get("/gene/hpo/{hpo_id}", response_model=HPOToGene)
def get_genes_by_hpo(hpo_id: str):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT hpo_name, ncbi_gene_id, gene_symbol FROM phenotype_to_genes WHERE hpo_id = ?", (hpo_id,))
    rows = cursor.fetchall()
    conn.close()
    if not rows:
        raise HTTPException(status_code=404, detail="HPO term not found")
    
    hpo_name = rows[0]['hpo_name']
    genes = [Gene(ncbi_gene_id=row['ncbi_gene_id'], gene_symbol=row['gene_symbol']) for row in rows]
    return HPOToGene(hpo_id=hpo_id, hpo_name=hpo_name, genes=genes)

@app.get("/hpo/gene/{gene_id}", response_model=GeneToHPO)
def get_hpo_by_gene(gene_id: str):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT gene_symbol, hpo_id, hpo_name FROM genes_to_phenotype WHERE ncbi_gene_id = ?", (gene_id,))
    rows = cursor.fetchall()
    conn.close()
    if not rows:
        raise HTTPException(status_code=404, detail="Gene not found")
    
    gene_symbol = rows[0]['gene_symbol']
    hpo_terms = [{"hpo_id": row['hpo_id'], "hpo_name": row['hpo_name']} for row in rows]
    return GeneToHPO(ncbi_gene_id=gene_id, gene_symbol=gene_symbol, hpo_terms=hpo_terms)

@app.get("/disease/gene/{gene_id}", response_model=GeneToDisease)
def get_diseases_by_gene(gene_id: str):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT gene_symbol, disease_id FROM genes_to_disease WHERE ncbi_gene_id = ?", (gene_id,))
    rows = cursor.fetchall()
    conn.close()
    if not rows:
        raise HTTPException(status_code=404, detail="Gene not found")
    
    gene_symbol = rows[0]['gene_symbol']
    diseases = [Disease(disease_id=row['disease_id']) for row in rows]
    return GeneToDisease(ncbi_gene_id=gene_id, gene_symbol=gene_symbol, diseases=diseases)

@app.get("/gene/disease/{disease_id}", response_model=DiseaseToGene)
def get_genes_by_disease(disease_id: str):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT ncbi_gene_id, gene_symbol FROM genes_to_disease WHERE disease_id = ?", (disease_id,))
    rows = cursor.fetchall()
    conn.close()
    if not rows:
        raise HTTPException(status_code=404, detail="Disease not found")
    
    genes = [Gene(ncbi_gene_id=row['ncbi_gene_id'], gene_symbol=row['gene_symbol']) for row in rows]
    return DiseaseToGene(disease_id=disease_id, genes=genes)

@app.get("/disease/hpo/{hpo_id}", response_model=HPOToDisease)
def get_diseases_by_hpo(hpo_id: str):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT DB_Name, DB_Reference FROM hpo_annotations WHERE HPO_ID = ?", (hpo_id,))
    rows = cursor.fetchall()
    conn.close()
    if not rows:
        raise HTTPException(status_code=404, detail="HPO term not found")
    
    hpo_name = ""
    diseases = [Disease(disease_id=row['DB_Reference'], disease_name=row['DB_Name']) for row in rows]
    return HPOToDisease(hpo_id=hpo_id, hpo_name=hpo_name, diseases=diseases)

@app.get("/hpo/disease/{disease_id}", response_model=DiseaseToHPO)
def get_hpo_by_disease(disease_id: str):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT HPO_ID FROM hpo_annotations WHERE DB_Reference = ?", (disease_id,))
    rows = cursor.fetchall()
    conn.close()
    if not rows:
        raise HTTPException(status_code=404, detail="Disease not found")
    
    hpo_terms = [{"hpo_id": row['HPO_ID']} for row in rows]
    return DiseaseToHPO(disease_id=disease_id, hpo_terms=hpo_terms)

