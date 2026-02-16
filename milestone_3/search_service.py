import chromadb
from sentence_transformers import SentenceTransformer

VECTOR_DB_PATH = "data/chroma_db"
COLLECTION_NAME = "chroma_db"
MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"

model = SentenceTransformer(MODEL_NAME)
client = chromadb.PersistentClient(path=VECTOR_DB_PATH)
collection = client.get_collection(COLLECTION_NAME)


def search_with_rbac(query: str, user_role: str, k: int = 5):
    user_role_norm = user_role.lower()
    query_embedding = model.encode(query).tolist()

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=10,
        include=["documents", "metadatas", "distances"]
    )

    allowed = []

    for doc, meta, dist in zip(
        results["documents"][0],
        results["metadatas"][0],
        results["distances"][0]
    ):
        roles_allowed = [
            r.strip().lower()
            for r in meta["accessible_roles"].split(",")
        ]

        if user_role_norm == "c-level" or user_role_norm in roles_allowed:
            allowed.append({
                "text": doc,
                "source": meta["source_document"],
                "department": meta["department"],
                "distance": dist
            })

    return allowed[:k]



# what is the financial summary?