import hashlib
from sentence_transformers import SentenceTransformer
from config import EMBED_MODEL_NAME
from .cache import get_embedding, save_embedding

model = SentenceTransformer(EMBED_MODEL_NAME)

def make_hash(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()

keyword_cache = {}

def embed_text(text):
    """
    Thread-safe, cached embedding fetch.
    """
    h = make_hash(text)
    vec = get_embedding(h)
    if vec is not None:
        return vec

    vec = model.encode(text, convert_to_numpy=True)
    save_embedding(h, vec)
    return vec

def embed_articles(articles, batch_size=16):
    texts, idxs = [], []

    for i, a in enumerate(articles):
        combined = a["title"] + "\n" + a["summary"]
        h = make_hash(combined)
        a["_hash"] = h

        cached = get_embedding(h)
        if cached is not None:
            a["embedding"] = cached
        else:
            texts.append(combined)
            idxs.append(i)

    if texts:
        vectors = model.encode(texts, batch_size=batch_size, convert_to_numpy=True)
        for article_i, vec in zip(idxs, vectors):
            articles[article_i]["embedding"] = vec
            save_embedding(articles[article_i]["_hash"], vec)

    return articles
