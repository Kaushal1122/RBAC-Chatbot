import nltk
from nltk.tokenize import sent_tokenize
import tiktoken
import json

from metadata import load_role_mapping, infer_department, get_allowed_roles
import os

from io_utils import list_documents, read_markdown, read_csv
from cleaner import clean_text

nltk.download("punkt", quiet=True)
nltk.download("punkt_tab", quiet=True)

ENCODER = tiktoken.get_encoding("cl100k_base")
RAW_DATA_DIR = "data/raw"
ROLE_CONFIG_PATH = "config/role_mapping.yaml"
OUTPUT_PATH = "data/processed/chunks.jsonl"


def count_tokens(text: str) -> int:
    return len(ENCODER.encode(text))

def trim_to_last_tokens(text: str, max_tokens: int) -> str:
    tokens = ENCODER.encode(text)
    return ENCODER.decode(tokens[-max_tokens:])

def hard_trim_to_max(text: str, max_tokens: int) -> str:
    tokens = ENCODER.encode(text)
    if len(tokens) <= max_tokens:
        return text
    return ENCODER.decode(tokens[:max_tokens])

def chunk_text(
    text: str,
    min_tokens: int = 300,
    max_tokens: int = 512,
    overlap_tokens: int = 50
):
    sentences = sent_tokenize(text)
    chunks = []

    current_chunk = []
    current_tokens = 0

    for sentence in sentences:
        sentence_tokens = count_tokens(sentence)

        if sentence_tokens > max_tokens:
            words = sentence.split()
            temp_chunk = []
            temp_tokens = 0

            for word in words:
                word_tokens = count_tokens(word + " ")

                if temp_tokens + word_tokens > max_tokens:
                    chunk_text_str = hard_trim_to_max(" ".join(temp_chunk), max_tokens)
                    chunks.append(chunk_text_str)
                    temp_chunk = [word]
                    temp_tokens = word_tokens
                else:
                    temp_chunk.append(word)
                    temp_tokens += word_tokens

            if temp_chunk:
                chunk_text_str = hard_trim_to_max(" ".join(temp_chunk), max_tokens)
                chunks.append(chunk_text_str)

            continue

        if current_tokens + sentence_tokens > max_tokens:
            chunk_text_str = hard_trim_to_max(" ".join(current_chunk), max_tokens)
            chunks.append(chunk_text_str)

            overlap_text = trim_to_last_tokens(chunk_text_str, overlap_tokens)
            current_chunk = [overlap_text, sentence]
            current_tokens = count_tokens(overlap_text) + sentence_tokens
        else:
            current_chunk.append(sentence)
            current_tokens += sentence_tokens

    if current_chunk:
        chunk_text_str = hard_trim_to_max(" ".join(current_chunk), max_tokens)
        chunks.append(chunk_text_str)

    final_chunks = []

    for chunk in chunks:
        chunk = hard_trim_to_max(chunk, max_tokens)
        token_count = count_tokens(chunk)

        if token_count < min_tokens and final_chunks:
            merged = hard_trim_to_max(final_chunks[-1] + " " + chunk, max_tokens)
            if count_tokens(merged) <= max_tokens:
                final_chunks[-1] = merged
            else:
                final_chunks.append(chunk)
        else:
            final_chunks.append(chunk)

    return final_chunks



def main():
    print("Chunking documents...\n")

    documents = list_documents(RAW_DATA_DIR)
    role_config = load_role_mapping(ROLE_CONFIG_PATH)

    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)

    total_chunks = 0
    all_chunk_records = []

    for doc in documents:
        if doc.endswith(".md"):
            raw_content = read_markdown(doc)
        elif doc.endswith(".csv"):
            raw_content = read_csv(doc)
        else:
            continue

        cleaned_content = clean_text(raw_content)
        chunks = chunk_text(cleaned_content)

        department = infer_department(doc, role_config)
        allowed_roles = get_allowed_roles(department, role_config)

        print(f"Chunked: {doc} → {len(chunks)} chunks")
        print(f"  Department: {department}")
        print(f"  Allowed roles: {allowed_roles}")

        for i, chunk in enumerate(chunks, start=1):
            tokens = count_tokens(chunk)
            status = "OK" if 300 <= tokens <= 512 else "BAD"

            chunk_id = f"{os.path.basename(doc)}_{i:03d}"

            chunk_record = {
                "chunk_id": chunk_id,
                "text": chunk,
                "source_document": os.path.basename(doc),
                "department": department,
                "accessible_roles": allowed_roles,
                "token_count": tokens
            }

            all_chunk_records.append(chunk_record)

            print(f"  Chunk {i:02d}: {tokens} tokens [{status}] → {chunk_id}")

        total_chunks += len(chunks)

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        for record in all_chunk_records:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")

    print(f"\nTotal chunks created: {total_chunks}")
    print(f"Saved to: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()