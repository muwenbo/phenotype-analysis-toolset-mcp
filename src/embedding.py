import json
from langchain.docstore.document import Document
from langchain_voyageai import VoyageAIEmbeddings
from langchain_community.vectorstores import FAISS

def process_json_file(file_path):
    """Process JSON file and convert to Documents"""
    with open(file_path, 'r') as file:
        data = json.load(file)
    
    nodes = data['graphs'][0]['nodes']
    documents = []
    
    # If data is not a list, wrap it in a list
    if not isinstance(nodes, list):
        nodes = [nodes]
    
    for record in nodes:
        # Create content string
        content_parts = []
        
        # Add ID and label
        id = record.get('id', '').split('/')[-1].replace('_', ':')
        #content_parts.append(f"ID: {record.get('id', '')}")
        content_parts.append(f"ID: {id}")
        content_parts.append(f"Label: {record.get('lbl', '')}")
        
        # Add definition
        if "meta" in record and "definition" in record["meta"]:
            content_parts.append(f"Definition: {record['meta']['definition'].get('val', '')}")
        
        # Add synonyms
        if "meta" in record and "synonyms" in record["meta"]:
            synonyms = [s.get('val', '') for s in record["meta"]["synonyms"]]
            content_parts.append(f"Synonyms: {', '.join(synonyms)}")
        
        # Add comments
        if "meta" in record and "comments" in record["meta"]:
            content_parts.append(f"Comments: {' '.join(record['meta']['comments'])}")
        
        # Create metadata
        metadata = {
            "id": record.get("id", ""),
            "label": record.get("lbl", "")
        }
        
        # Create Document object
        doc = Document(
            page_content="\n".join(content_parts),
            metadata=metadata
        )
        documents.append(doc)
    
    return documents


def create_vectorstore(embeddings, embedding_store):
    # Create embeddings and vectorstore
    documents = process_json_file('../data/hp.json')
    vectorstore = FAISS.from_documents(documents=documents, embedding=embeddings)

    # Save the vectorstore
    vectorstore.save_local(folder_path=embedding_store)
    #return vectorstore

def main():
    from dotenv import load_dotenv
    load_dotenv()
    embeddings = VoyageAIEmbeddings(model="voyage-3")
    embedding_store = '../embeddings/voyage_3/'
    #create_vectorstore(embeddings,embedding_store)

    try:
        vectorstore = FAISS.load_local(
            folder_path=embedding_store,
            embeddings=embeddings,
            allow_dangerous_deserialization=True
        )
        print("Number of documents in vectorstore:", len(vectorstore.docstore._dict))
        results = vectorstore.similarity_search("Delayed speech", k=5)
        print("Search result:", results)
        print("Expected result: ", "Delayed speech and language development")
        print("✅ Vector store loaded successfully.")
    except Exception as e:
        print("❌ Failed to load vector store:", e)


if __name__ == "__main__":
    main()