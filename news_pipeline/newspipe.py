from fetchers.newsdata import fetch_newsdata
from fetchers.newsapi import fetch_newsapi
from fetchers.gnews import fetch_gnews

from processing.ranking import keyword_match, rank_articles
from processing.dedupe import dedupe_events_ai
from embeddings.embedder import embed_articles
from config import API_KEYS

import json, time

def get_all_news(keyword):
    print(f"\nSearching for: {keyword}\n")
    raw = []

    raw.extend(fetch_newsdata(keyword, API_KEYS["newsdata"]))
    raw.extend(fetch_newsapi(keyword, API_KEYS["newsapi"]))
    raw.extend(fetch_gnews(keyword, API_KEYS["gnews"]))

    print(f"Fetched {len(raw)} raw articles")

    filtered = [a for a in raw if keyword_match(a, keyword)]
    print(f"Relevant articles: {len(filtered)}")

    print("Generating semantic embeddings...")
    embedded = embed_articles(filtered)

    print("Removing duplicates...")
    unique = dedupe_events_ai(embedded)

    ranked = rank_articles(unique, keyword)
    print(f"Final results: {len(ranked)}")
    return ranked

if __name__ == "__main__":
    topic = "Fuel industry"
    results = get_all_news(topic)

    for article in results:
        print(f"[{article['source']}] (Score: {article['score']}) {article['title']}")
        print(f"Link: {article['link']}")
        print("-" * 80)

    # Remove embeddings — they are NumPy arrays, not JSON-serializable
    for article in results:
        article.pop("embedding", None)

    # Use a fixed filename
    filename = "resultsgen.json"

    with open(filename, "w") as f:
        json.dump(results, f, indent=2)

    print(f"\nSaved results to {filename}")
