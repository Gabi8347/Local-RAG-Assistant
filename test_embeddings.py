from foundry_local_sdk import FoundryLocalManager, Configuration
from db import cosine_similarity

embedding_alias = "qwen3-embedding-0.6b"

config = Configuration(app_name="local-rag-assistant")
FoundryLocalManager.initialize(config)
manager = FoundryLocalManager.instance
manager.start_web_service()

model = manager.catalog.get_model(embedding_alias)

print("Model downloading (it might take a while on the first run)...")
model.download()

print("Model loading...")
model.load()

client = model.get_embedding_client()

texts = [
    "The cat sat on the mat.",
    "A dog is playing in the park.",
    "SQLite is a lightweight relational database.",
]
query = "Where is the cat?"

response = client.generate_embeddings(texts + [query])
vectors = [item.embedding for item in response.data]
*doc_vectors, query_vector = vectors

scores = [cosine_similarity(query_vector, v) for v in doc_vectors]

for text, score in sorted(zip(texts, scores), key=lambda x: -x[1]):
    print(f"{score:.4f}  {text}")
