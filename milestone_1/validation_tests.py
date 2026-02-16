import json
import os
from collections import defaultdict

CHUNKS_PATH = "data/processed/chunks.jsonl"


def load_chunks(path: str):
    chunks = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            chunks.append(json.loads(line))
    return chunks


def fail(msg: str):
    print(f" FAIL: {msg}")
    exit(1)


def pass_test(msg: str):
    print(f" PASS: {msg}")


def main():
    if not os.path.exists(CHUNKS_PATH):
        fail(f"Missing file: {CHUNKS_PATH}")

    print("Loading chunks...")
    chunks = load_chunks(CHUNKS_PATH)

    if not chunks:
        fail("No chunks loaded")

    pass_test("Chunks loaded")

    required_fields = {
        "chunk_id",
        "text",
        "source_document",
        "department",
        "accessible_roles",
        "token_count"
    }

    for i, chunk in enumerate(chunks):
        missing = required_fields - set(chunk.keys())
        if missing:
            fail(f"Chunk {i} missing fields: {missing}")

    pass_test("All chunks have required fields")

    for i, chunk in enumerate(chunks):
        tokens = chunk["token_count"]
        if tokens < 300 or tokens > 512:
            fail(f"Chunk {chunk['chunk_id']} token_count out of range: {tokens}")

    pass_test("All chunks have token_count within 300–512")

    for i, chunk in enumerate(chunks):
        if not chunk["text"].strip():
            fail(f"Chunk {chunk['chunk_id']} is empty")

    pass_test("No empty chunks")

    docs = set()
    for chunk in chunks:
        docs.add(chunk["source_document"])

    if len(docs) == 0:
        fail("No source documents represented")

    pass_test("All source documents represented")

    for chunk in chunks:
        roles = chunk["accessible_roles"]
        if not roles:
            fail(f"Chunk {chunk['chunk_id']} has no accessible_roles")

    pass_test("All chunks have accessible_roles")

    
    finance_chunks = [
        c for c in chunks if c["department"].lower() == "finance"
    ]

    general_chunks = [
        c for c in chunks if c["department"].lower() == "general"
    ]

    for c in finance_chunks:
        roles = [r.lower() for r in c["accessible_roles"]]
        if "employees" in roles:
            fail(f"Employees should not access Finance chunk {c['chunk_id']}")

    pass_test("Employees cannot access Finance")

    for c in general_chunks:
        roles = [r.lower() for r in c["accessible_roles"]]
        if "employees" not in roles:
            fail(f"Employees missing access to General chunk {c['chunk_id']}")

    pass_test("Employees can access General")

    print("\n ALL VALIDATION TESTS PASSED ")


if __name__ == "__main__":
    main()