"""
Ranking utilities.

- No dependency on 'summary' field anymore.
- Uses a simple keyword/title heuristic + semantic similarity (embedding).
"""
from embeddings.embedder import embed_text
from utils.similarity import cosine_similarity
from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)

# Cache keyword embeddings to avoid repeated calls
_keyword_embeds = {}


def relevance_score_keyword(article: Dict[str, Any], keyword: str) -> float:
    """
    Heuristic binary/term match over the article title (case-insensitive).
    Returns a small integer-ish score; semantic score (below) will be on a different scale.
    """
    title = str(article.get("title", "")).lower()
    keyword_l = keyword.lower()
    words = keyword_l.split()

    score = 0.0
    if keyword_l in title:
        score += 10.0

    # reward presence of individual words
    for w in words:
        if w and w in title:
            score += 3.0

    return score


def keyword_match(article: Dict[str, Any], keyword: str) -> bool:
    """
    Quick filter used early in pipeline. Matches if at least half of the keyword words
    appear in the title OR the keyword as a whole appears in the title.
    """
    title = str(article.get("title", "")).lower()
    keyword_l = keyword.lower()
    words = [w for w in keyword_l.split() if w]

    if not words:
        return False

    if keyword_l in title:
        return True

    matches = sum(1 for w in words if w in title)
    return matches >= max(1, len(words) // 2)


def rank_articles(articles: List[Dict[str, Any]], keyword: str) -> List[Dict[str, Any]]:
    """
    Rank articles by combining a keyword heuristic and semantic similarity.
    Expects each article to have an 'embedding' vector.
    Returns a new list of dicts with a 'score' key (float).
    """
    if not articles:
        return []

    # ensure keyword embedding cached
    if keyword not in _keyword_embeds:
        _keyword_embeds[keyword] = embed_text(keyword)
    kw_vec = _keyword_embeds[keyword]

    ranked = []
    for a in articles:
        try:
            kw_score = relevance_score_keyword(a, keyword)
            sem_score = 0.0
            if "embedding" in a and a["embedding"] is not None:
                sem_score = float(cosine_similarity(a["embedding"], kw_vec)) * 100.0
            final = kw_score * 0.6 + sem_score * 0.4
        except Exception as e:
            logger.exception("Error scoring article %s: %s", a.get("title"), e)
            final = 0.0

        item = dict(a)
        item["score"] = final
        ranked.append(item)

    ranked_sorted = sorted(ranked, key=lambda x: x.get("score", 0.0), reverse=True)
    return ranked_sorted
