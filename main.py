from foundry_local_sdk import FoundryLocalManager, Configuration
import db

CHAT_ALIAS = "phi-3.5-mini"
EMBEDDING_ALIAS = "qwen3-embedding-0.6b"
TOP_K = 3


def load_model(manager, alias):
    model = manager.catalog.get_model(alias)
    model.download()
    model.load()
    return model


def build_prompt(question, chunks):
    context = "\n\n".join(f"[{source}]\n{content}" for _, _, content, source in chunks)
    return [
        {
            "role": "system",
            "content": (
                "You are a helpful assistant. Answer the question using only the "
                "context below. If the answer is not in the context, say you don't know.\n\n"
                f"Context:\n{context}"
            ),
        },
        {"role": "user", "content": question},
    ]


def answer_query(question, embedding_client, chat_client):
    query_embedding = embedding_client.generate_embedding(question).data[0].embedding
    chunks = db.get_top_chunks(query_embedding, top_k=TOP_K)
    messages = build_prompt(question, chunks)
    response = chat_client.complete_chat(messages)
    return response.choices[0].message.content


def main():
    config = Configuration(app_name="local-rag-assistant")
    FoundryLocalManager.initialize(config)
    manager = FoundryLocalManager.instance
    manager.start_web_service()

    print("Loading chat model...")
    chat_model = load_model(manager, CHAT_ALIAS)
    chat_client = chat_model.get_chat_client()

    print("Loading embedding model...")
    embedding_model = load_model(manager, EMBEDDING_ALIAS)
    embedding_client = embedding_model.get_embedding_client()

    print("Ready. Ask a question (empty input to quit).")
    while True:
        question = input("\n> ").strip()
        if not question:
            break
        answer = answer_query(question, embedding_client, chat_client)
        print(answer)


if __name__ == "__main__":
    main()
