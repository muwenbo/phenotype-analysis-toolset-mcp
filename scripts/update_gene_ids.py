
import sqlite3

conn = sqlite3.connect('../hpo_annotations.db')
cursor = conn.cursor()

# Update the ncbi_gene_id column
cursor.execute("UPDATE genes_to_disease SET ncbi_gene_id = REPLACE(ncbi_gene_id, 'NCBIGene:', '') WHERE ncbi_gene_id LIKE 'NCBIGene:%'")

conn.commit()
conn.close()

print("Successfully updated ncbi_gene_id in the genes_to_disease table.")
