import sqlite3
import json
import math

DB_PATH = "rag.db"


def get_connection():
    return sqlite3.connect(DB_PATH)


def init_db():
    conn = get_connection()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS chunks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            content TEXT NOT NULL,
            source TEXT NOT NULL,
            embedding TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()


def insert_chunk(content, source, embedding):
    conn = get_connection()
    conn.execute(
        "INSERT INTO chunks (content, source, embedding) VALUES (?, ?, ?)",
        (content, source, json.dumps(embedding)),
    )
    conn.commit()
    conn.close()


def cosine_similarity(a, b):
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(y * y for y in b))
    return dot / (norm_a * norm_b)


def get_top_chunks(query_embedding, top_k=3):
    conn = get_connection()
    rows = conn.execute("SELECT id, content, source, embedding FROM chunks").fetchall()
    conn.close()

    scored = []
    for row_id, content, source, embedding_json in rows:
        embedding = json.loads(embedding_json)
        score = cosine_similarity(query_embedding, embedding)
        scored.append((score, row_id, content, source))

    scored.sort(key=lambda x: -x[0])
    return scored[:top_k]
