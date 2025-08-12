
import sqlite3
from sentence_transformers import SentenceTransformer
import numpy as np

def generate_embeddings():
    # Load a pre-trained model
    model = SentenceTransformer('all-MiniLM-L6-v2')

    # Connect to the database
    conn = sqlite3.connect('../hpo_annotations.db')
    cursor = conn.cursor()

    # Fetch HPO terms
    cursor.execute("SELECT DISTINCT hpo_id, hpo_name FROM phenotype_to_genes")
    hpo_terms = cursor.fetchall()

    # Generate embeddings
    hpo_names = [term[1] for term in hpo_terms]
    embeddings = model.encode(hpo_names)

    # Store embeddings in the database
    for i, term in enumerate(hpo_terms):
        hpo_id = term[0]
        embedding = embeddings[i].astype(np.float32).tobytes()
        cursor.execute("INSERT OR REPLACE INTO hpo_embeddings (hpo_id, embedding) VALUES (?, ?)", (hpo_id, embedding))

    conn.commit()
    conn.close()

if __name__ == "__main__":
    generate_embeddings()
    print("Embeddings generated and stored successfully.")
