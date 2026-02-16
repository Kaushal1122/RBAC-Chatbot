import os
import pandas as pd

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