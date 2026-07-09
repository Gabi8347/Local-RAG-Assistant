import os
from pypdf import PdfReader
from foundry_local_sdk import FoundryLocalManager, Configuration
import db

DOCUMENTS_DIR = "documents"
CHUNK_SIZE = 800
CHUNK_OVERLAP = 100


def extract_text(pdf_path):
    reader = PdfReader(pdf_path)
    return "\n".join(page.extract_text() or "" for page in reader.pages)


def chunk_text(text, chunk_size=CHUNK_SIZE, overlap=CHUNK_OVERLAP):
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        start += chunk_size - overlap
    return chunks


def main():
    config = Configuration(app_name="local-rag-assistant")
    FoundryLocalManager.initialize(config)
    manager = FoundryLocalManager.instance
    manager.start_web_service()

    model = manager.catalog.get_model("qwen3-embedding-0.6b")
    model.download()
    model.load()
    client = model.get_embedding_client()

    db.init_db()

    pdf_files = [f for f in os.listdir(DOCUMENTS_DIR) if f.lower().endswith(".pdf")]
    total_chunks = 0

    for filename in pdf_files:
        path = os.path.join(DOCUMENTS_DIR, filename)
        print(f"Processing {filename}...")
        text = extract_text(path)
        chunks = chunk_text(text)

        for chunk in chunks:
            embedding = client.generate_embedding(chunk).data[0].embedding
            db.insert_chunk(chunk, filename, embedding)

        print(f"  -> {len(chunks)} chunks")
        total_chunks += len(chunks)

    print(f"Done. Inserted {total_chunks} chunks from {len(pdf_files)} files.")


if __name__ == "__main__":
    main()
