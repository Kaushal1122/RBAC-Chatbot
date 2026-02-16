import chromadb

client = chromadb.PersistentClient(path="data/chroma_db")

collection = client.get_collection("chroma_db")

print("Count:", collection.count())