import sqlite3
import csv

# Connect to the database
conn = sqlite3.connect('hpo_annotations.db')
cursor = conn.cursor()

# Clear existing data from tables to avoid duplicates if script is run multiple times
cursor.execute("DELETE FROM hpo_annotations")
cursor.execute("DELETE FROM genes_to_disease")
cursor.execute("DELETE FROM genes_to_phenotype")
cursor.execute("DELETE FROM phenotype_to_genes")
conn.commit()

# Populate the hpo_annotations table
with open('data/phenotype.hpoa', 'r') as f:
    reader = csv.reader(f, delimiter='	')
    data_to_insert = []
    for row in reader:
        if not row[0].startswith('#'):
            data_to_insert.append(row)
    # The first row after comments is the header, so skip it.
    if data_to_insert:
        cursor.executemany('INSERT INTO hpo_annotations (DatabaseId, DB_Name, Qualifier, HPO_ID, DB_Reference, Evidence, Onset, Frequency, Sex, Modifier, Aspect, BiocurationBy) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)', data_to_insert[1:])

# Populate the genes_to_disease table
with open('data/genes_to_disease.txt', 'r') as f:
    reader = csv.reader(f, delimiter='	')
    next(reader)  # Skip header
    cursor.executemany('INSERT INTO genes_to_disease (ncbi_gene_id, gene_symbol, association_type, disease_id, source) VALUES (?, ?, ?, ?, ?)', reader)

# Populate the genes_to_phenotype table
with open('data/genes_to_phenotype.txt', 'r') as f:
    reader = csv.reader(f, delimiter='	')
    next(reader)  # Skip header
    cursor.executemany('INSERT INTO genes_to_phenotype (ncbi_gene_id, gene_symbol, hpo_id, hpo_name, frequency, disease_id) VALUES (?, ?, ?, ?, ?, ?)', reader)

# Populate the phenotype_to_genes table
with open('data/phenotype_to_genes.txt', 'r') as f:
    reader = csv.reader(f, delimiter='	')
    next(reader)  # Skip header
    # Taking only the first 4 columns to avoid errors with malformed rows
    data_to_insert = [row[:4] for row in reader]
    cursor.executemany('INSERT INTO phenotype_to_genes (hpo_id, hpo_name, ncbi_gene_id, gene_symbol) VALUES (?, ?, ?, ?)', data_to_insert)

# Commit the changes and close the connection
conn.commit()
conn.close()

print("Database populated successfully.")