from foundry_local_sdk import FoundryLocalManager, Configuration
import db

config = Configuration(app_name="local-rag-assistant")
FoundryLocalManager.initialize(config)
manager = FoundryLocalManager.instance
manager.start_web_service()

model = manager.catalog.get_model("qwen3-embedding-0.6b")
model.download()
model.load()
client = model.get_embedding_client()

db.init_db()

texts = [
    ("The cat sat on the mat.", "notes1.txt"),
    ("A dog is playing in the park.", "notes2.txt"),
    ("SQLite is a lightweight relational database.", "notes3.txt"),
]

for content, source in texts:
    response = client.generate_embedding(content)
    embedding = response.data[0].embedding
    db.insert_chunk(content, source, embedding)

query = "Where is the cat?"
query_embedding = client.generate_embedding(query).data[0].embedding

results = db.get_top_chunks(query_embedding, top_k=3)
for score, row_id, content, source in results:
    print(f"{score:.4f}  [{source}]  {content}")
