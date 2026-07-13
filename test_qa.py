import time
from foundry_local_sdk import FoundryLocalManager, Configuration
from main import load_model, answer_query, CHAT_ALIAS, EMBEDDING_ALIAS

TEST_CASES = [
    ("What is the divide and conquer technique?", "answerable"),
    ("What is a greedy algorithm?", "answerable"),
    ("What is mathematical induction used for?", "answerable"),
    ("What is the capital of France?", "unanswerable"),
    ("How do I bake a chocolate cake?", "unanswerable"),
    ("", "edge_case_empty"),
    ("Tell me everything.", "edge_case_vague"),
]


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

    print("\n=== Running test cases ===\n")
    for question, kind in TEST_CASES:
        print(f"[{kind}] Q: {question!r}")
        if not question.strip():
            print("  -> SKIPPED (empty input should be handled by the CLI loop, not answer_query)\n")
            continue
        start = time.time()
        answer = answer_query(question, embedding_client, chat_client)
        elapsed = time.time() - start
        print(f"  -> ({elapsed:.1f}s) {answer}\n")


if __name__ == "__main__":
    main()
