import sqlite3
import os

# Get the directory of this script and project root
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)

# Connect to the database (or create it if it doesn't exist)
db_path = os.path.join(project_root, 'hpo_annotations.db')
conn = sqlite3.connect(db_path)

# Create a cursor object
cursor = conn.cursor()

# Read the schema from the .sql file
schema_path = os.path.join(project_root, 'src', 'schema.sql')
with open(schema_path, 'r') as f:
    schema = f.read()

# Execute the schema
cursor.executescript(schema)

# Commit the changes and close the connection
conn.commit()
conn.close()
