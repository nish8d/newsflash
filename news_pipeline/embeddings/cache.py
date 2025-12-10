import sqlite3
import threading
import numpy as np
import time
from config import EMBED_CACHE_DB, EMBED_CACHE_MAX_ITEMS

_lock = threading.Lock()

def _connect():
    conn = sqlite3.connect(EMBED_CACHE_DB, check_same_thread=False)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS cache (
            hash TEXT PRIMARY KEY,
            vector BLOB NOT NULL,
            created_at REAL
        )
    """)
    return conn

_conn = _connect()

def get_embedding(h):
    with _lock:
        cur = _conn.execute("SELECT vector FROM cache WHERE hash=?", (h,))
        row = cur.fetchone()
        if not row:
            return None
        vec = np.frombuffer(row[0], dtype=np.float32)
        return vec

def save_embedding(h, vector):
    blob = vector.astype(np.float32).tobytes()
    ts = time.time()

    with _lock:
        _conn.execute(
            "REPLACE INTO cache (hash, vector, created_at) VALUES (?, ?, ?)",
            (h, blob, ts)
        )
        _conn.commit()

        # Enforce LRU eviction
        cur = _conn.execute("SELECT COUNT(*) FROM cache")
        count = cur.fetchone()[0]

        if count > EMBED_CACHE_MAX_ITEMS:
            to_remove = count - EMBED_CACHE_MAX_ITEMS
            _conn.execute(
                """
                DELETE FROM cache WHERE hash IN (
                    SELECT hash FROM cache
                    ORDER BY created_at ASC
                    LIMIT ?
                )
                """,
                (to_remove,)
            )
            _conn.commit()
