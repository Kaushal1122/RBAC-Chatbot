import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer



VECTOR_DB_PATH = "data/chroma_db"
COLLECTION_NAME = "chroma_db"
MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"


def main():
    print("Loading embedding model...")
    model = SentenceTransformer(MODEL_NAME)

    print("Connecting to ChromaDB...")
    client = chromadb.PersistentClient(path=VECTOR_DB_PATH)
    collection = client.get_collection(COLLECTION_NAME)

    print("\nAvailable roles:")
    roles = ["Finance", "HR", "Marketing", "Engineering", "Employees", "C-Level"]
    for r in roles:
        print(f" - {r}")

    user_role = input("\nEnter your role: ").strip()
    query = input("Enter your query: ").strip()

    user_role_norm = user_role.lower()

    print("\nEmbedding query...")
    query_embedding = model.encode(query).tolist()

    print("Searching vector DB...")
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=10,
        include=["documents", "metadatas", "distances"]
    )

    print("\nApplying RBAC filtering...")

    allowed_results = []

    for doc, meta, dist in zip(
        results["documents"][0],
        results["metadatas"][0],
        results["distances"][0]
    ):
        roles_allowed = [r.strip().lower() for r in meta["accessible_roles"].split(",")]

        # C-Level override
        if user_role_norm == "c-level":
            allowed_results.append((doc, meta, dist))
            continue
        roles_allowed = [r.strip().lower() for r in meta["accessible_roles"].split(",")]
        user_role_norm = user_role.strip().lower()


        if user_role_norm in roles_allowed:
            allowed_results.append((doc, meta, dist))

    if not allowed_results:
        print("\nNo accessible results found for your role.")
        return

    

    print("\nTop accessible results:\n")

    for i, (doc, meta, dist) in enumerate(allowed_results, start=1):
        print(f"Result {i}")
        print(f"Source document : {meta['source_document']}")
        print(f"Department      : {meta['department']}")
        print(f"Token count     : {meta['token_count']}")
        print(f"Distance        : {dist:.4f}")
        print("Text:")
        print(doc[:500], "...\n")


if __name__ == "__main__":
    main()