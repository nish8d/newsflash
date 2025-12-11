from typing import List, Dict, Any
from fetchers.newsdata import fetch_newsdata
from fetchers.newsapi import fetch_newsapi
from fetchers.gnews import fetch_gnews

from processing.ranking import keyword_match, rank_articles
from processing.dedupe import dedupe_events_ai
from embeddings.embedder import embed_articles
from config import API_KEYS

import json
import time
import logging
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def get_all_news(keyword: str) -> List[Dict[str, Any]]:
    """
    Fetch from configured sources, filter by keyword-match, embed, dedupe and rank.
    Returns a list of ranked article dicts (containing 'embedding' while in-memory).
    """
    logger.info("Searching for: %s", keyword)
    raw = []

    try:
        raw.extend(fetch_newsdata(keyword, API_KEYS.get("newsdata")))
    except Exception as e:
        logger.exception("newsdata fetch failed: %s", e)

    try:
        raw.extend(fetch_newsapi(keyword, API_KEYS.get("newsapi")))
    except Exception as e:
        logger.exception("newsapi fetch failed: %s", e)

    try:
        raw.extend(fetch_gnews(keyword, API_KEYS.get("gnews")))
    except Exception as e:
        logger.exception("gnews fetch failed: %s", e)

    logger.info("Fetched %d raw articles", len(raw))

    # filter using keyword_match (works off title/content)
    filtered = [a for a in raw if keyword_match(a, keyword)]
    logger.info("Relevant articles: %d", len(filtered))

    if not filtered:
        return []

    logger.info("Generating semantic embeddings...")
    embedded = embed_articles(filtered)  # expected to attach "embedding" to each article

    logger.info("Removing duplicates...")
    unique = dedupe_events_ai(embedded)

    logger.info("Ranking articles...")
    ranked = rank_articles(unique, keyword)
    logger.info("Final results: %d", len(ranked))

    return ranked


def save_results_json(articles: List[Dict[str, Any]], filename: str = "resultsgen.json") -> None:
    """
    Strip non-serializable fields (like embeddings) and write results to JSON.
    Overwrites filename. Does not persist embeddings.
    """
    serializable = []
    for a in articles:
        copy = dict(a)  # shallow copy
        copy.pop("embedding", None)  # remove embeddings (NumPy arrays)
        serializable.append(copy)

    # ensure directory exists if path includes directories
    os.makedirs(os.path.dirname(filename) or ".", exist_ok=True)

    with open(filename, "w", encoding="utf-8") as f:
        json.dump(serializable, f, indent=2, ensure_ascii=False)

    logger.info("Saved results to %s", filename)


if __name__ == "__main__":
    # Example usage
    topic = "English Premier League"
    results = get_all_news(topic)

    for article in results:
        src = article.get("source", "UNKNOWN")
        score = article.get("score", 0)
        print(f"[{src}] (Score: {score:.2f}) {article.get('title')}")
        print(f"Link: {article.get('link')}")
        print("-" * 80)

    save_results_json(results, filename="resultsgen.json")
