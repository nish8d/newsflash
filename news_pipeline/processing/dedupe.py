from sklearn.cluster import DBSCAN
import numpy as np
from config import DBSCAN_EPS, DBSCAN_MIN_SAMPLES
from utils.similarity import cosine_similarity

def dedupe_events_ai(articles):
    """
    Cluster embeddings using DBSCAN over cosine distance.
    Returns one exemplar per cluster.
    """
    if not articles:
        return []

    X = np.array([a["embedding"] for a in articles])

    # cosine distance = 1 - cosine similarity
    def metric(x, y):
        return 1 - cosine_similarity(x, y)

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
        # pick the article with highest text length (as a heuristic proxy)
        best = max(group, key=lambda a: len(a["summary"]))
        exemplars.append(best)

    return exemplars
