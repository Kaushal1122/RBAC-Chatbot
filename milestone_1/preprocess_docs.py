import os
import pandas as pd

RAW_DATA_DIR = "data/raw"

def list_documents(raw_dir):
    docs = []
    for root, dirs, files in os.walk(raw_dir):
        for file in files:
            if file.endswith(".md") or file.endswith(".csv"):
                docs.append(os.path.join(root, file))
    return docs

def read_markdown(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        return f.read()

def read_csv(file_path):
    df = pd.read_csv(file_path)
    return df.to_string(index=False)

def main():
    print("Listing documents...")
    documents = list_documents(RAW_DATA_DIR)

    print(f"Found {len(documents)} documents\n")

    for doc in documents:
        if doc.endswith(".md"):
            content = read_markdown(doc)
        elif doc.endswith(".csv"):
            content = read_csv(doc)
        else:
            continue

        print(f"Loaded: {doc}")
        print(f"Character length: {len(content)}\n")

if __name__ == "__main__":
    main()