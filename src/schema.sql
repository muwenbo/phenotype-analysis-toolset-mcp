
CREATE TABLE IF NOT EXISTS hpo_annotations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    DatabaseId TEXT,
    DB_Name TEXT,
    Qualifier TEXT,
    HPO_ID TEXT,
    DB_Reference TEXT,
    Evidence TEXT,
    Onset TEXT,
    Frequency TEXT,
    Sex TEXT,
    Modifier TEXT,
    Aspect TEXT,
    BiocurationBy TEXT
);

CREATE TABLE IF NOT EXISTS genes_to_disease (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ncbi_gene_id TEXT,
    gene_symbol TEXT,
    association_type TEXT,
    disease_id TEXT,
    source TEXT
);

CREATE TABLE IF NOT EXISTS genes_to_phenotype (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ncbi_gene_id TEXT,
    gene_symbol TEXT,
    hpo_id TEXT,
    hpo_name TEXT,
    frequency TEXT,
    disease_id TEXT
);

CREATE TABLE IF NOT EXISTS phenotype_to_genes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    hpo_id TEXT,
    hpo_name TEXT,
    ncbi_gene_id TEXT,
    gene_symbol TEXT
);

CREATE TABLE IF NOT EXISTS hpo_embeddings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    hpo_id TEXT UNIQUE,
    embedding BLOB
);
