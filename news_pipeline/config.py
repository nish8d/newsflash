from dotenv import load_dotenv
import os

load_dotenv()

API_KEYS = {
    "newsdata": os.getenv("NEWSDATA_KEY"),
    "newsapi": os.getenv("NEWSAPI_KEY"),
    "gnews": os.getenv("GNEWS_KEY")
}

EMBED_MODEL_NAME = "all-mpnet-base-v2"
EMBED_CACHE_DB = "embedding_cache.sqlite"

# Cache settings
EMBED_CACHE_MAX_ITEMS = 50_000  # LRU eviction

# Deduplication clustering
DBSCAN_EPS = 0.20     # 1 - cosine similarity threshold (~0.8)
DBSCAN_MIN_SAMPLES = 1
