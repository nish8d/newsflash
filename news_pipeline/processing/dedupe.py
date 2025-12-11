"""
Dedupe pipeline using DBSCAN over embedding vectors.

Exemplar selection no longer relies on 'summary' (removed).
We use title length as a simple heuristic; noise points (label -1)
are treated as their own clusters (i.e., included).
"""
from sklearn.cluster import DBSCAN
import numpy as np
from config import DBSCAN_EPS, DBSCAN_MIN_SAMPLES
from utils.similarity import cosine_similarity
from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)


def dedupe_events_ai(articles: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Cluster articles by their embeddings and return one exemplar per cluster.
    Each article is expected to contain an 'embedding' key (1D array-like).
    We choose the exemplar in a cluster by the longest title (fallback to first).
    """
    if not articles:
        return []

    # Ensure embeddings are convertible to numpy
    try:
        X = np.array([np.asarray(a["embedding"]) for a in articles])
    except Exception as e:
        logger.exception("Failed to build embedding matrix: %s", e)
        # If embeddings are missing or invalid, return unique articles as-is
        return articles

    # cosine distance = 1 - cosine_similarity
    def metric(x, y):
        # x, y are 1D arrays
        return 1.0 - float(cosine_similarity(x, y))

    clustering = DBSCAN(
        eps=DBSCAN_EPS,
        min_samples=DBSCAN_MIN_SAMPLES,
        metric=metric
    ).fit(X)

    labels = clustering.labels_
    clusters = {}
    for idx, lbl in enumerate(labels):
        clusters.setdefault(lbl, []).append(articles[idx])

    exemplars = []
    for lbl, group in clusters.items():
        # Choose article with longest title, fallback to first
        best = max(group, key=lambda a: len(str(a.get("title", "") or "")))
        exemplars.append(best)

    logger.info("Dedupe reduced %d -> %d", len(articles), len(exemplars))
    return exemplars
