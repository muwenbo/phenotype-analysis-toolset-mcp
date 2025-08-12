import sqlite3

# Connect to the database (or create it if it doesn't exist)
conn = sqlite3.connect('../hpo_annotations.db')

# Create a cursor object
cursor = conn.cursor()

# Read the schema from the .sql file
with open('../src/schema.sql', 'r') as f:
    schema = f.read()

# Execute the schema
cursor.executescript(schema)

# Commit the changes and close the connection
conn.commit()
conn.close()
