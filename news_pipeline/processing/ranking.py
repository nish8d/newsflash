from embeddings.embedder import embed_text
from utils.similarity import cosine_similarity

def relevance_score_keyword(article, keyword):
    title = article["title"].lower()
    summary = article["summary"].lower()
    words = keyword.lower().split()

    score = 0
    if keyword.lower() in title: score += 10
    if keyword.lower() in summary: score += 5

    for w in words:
        if w in title: score += 3
        elif w in summary: score += 1

    return score

def keyword_match(article, keyword):
    content = (article["title"] + " " + article["summary"]).lower()
    words = keyword.lower().split()
    matches = sum(w in content for w in words)
    return matches >= max(1, len(words) // 2)

# Cache keyword embeddings
_keyword_embeds = {}

def rank_articles(articles, keyword):
    # Embed keyword only once
    if keyword not in _keyword_embeds:
        _keyword_embeds[keyword] = embed_text(keyword)
    kw_vec = _keyword_embeds[keyword]

    ranked = []
    for a in articles:
        kw_score = relevance_score_keyword(a, keyword)
        sem_score = cosine_similarity(a["embedding"], kw_vec) * 100

        final = kw_score * 0.6 + sem_score * 0.4

        ranked.append({**a, "score": final})

    return sorted(ranked, key=lambda x: x["score"], reverse=True)
