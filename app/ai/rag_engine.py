"""
RAG Engine wrapper.
- Uses app.database.vector_store.vector_store for embeddings + FAISS.
- Provides search(query, k) -> list[str] (relevant docs/snippets)
- Provides rank_by_relevance(query, candidates) -> list[(candidate, score)]
"""

from typing import List, Tuple
import logging

try:
    from app.database.vector_store import vector_store
except Exception as e:
    vector_store = None
    logging.warning("[rag_engine] vector_store import failed: %s", e)


def def search(query: str, k: int = 5) -> List[str]:
    """
    Return up to k relevant stored memory/documents for the query.
    If vector_store missing, returns empty list.
    """
    if not query:
        return []
    if vector_store is None:
        # no vector backend — return empty
        return []
    try:
        results = vector_store.search(query, k=k)
        # vector_store may return raw doc texts
        return results or []
    except Exception as e:
        logging.exception("RAG search failed: %s", e)
        return []


def rank_candidates(query: str, candidates: List[str]) -> List[Tuple[str, float]]:
    """
    Naive ranking wrapper: if vector_store available, use similarity ranking.
    Otherwise, fallback to heuristic keyword overlap scoring.
    Returns list of (candidate, score) descending.
    """
    if not candidates:
        return []

    if vector_store is not None:
        try:
            # Use internal encode -> cosine / L2 similarity if available.
            # vector_store.search returns docs; to rank a provided candidate list
            # we can add them temporarily or rely on model.encode and numpy.
            # For simplicity, implement a model-based ranking if model present.
            # NOTE: This function tries best-effort — vector_store.model should exist.
            model = getattr(vector_store, "model", None)
            index = getattr(vector_store, "index", None)
            docs = getattr(vector_store, "docs", None)
            if model is None or index is None:
                raise RuntimeError("vector_store missing model/index")
            import numpy as np
            # encode query and candidates
            q_emb = model.encode([query], convert_to_numpy=True).astype("float32")
            cand_embs = model.encode(candidates, convert_to_numpy=True).astype("float32")
            # compute cosine similarity
            def cosine(a, b):
                return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b) + 1e-10))
            scores = [cosine(q_emb[0], cand_embs[i]) for i in range(len(candidates))]
            ranked = sorted(zip(candidates, scores), key=lambda x: x[1], reverse=True)
            return ranked
        except Exception:
            # fall through to heuristic
            pass

    # Heuristic scoring: token overlap
    qtokens = set(query.lower().split())
    scored = []
    for c in candidates:
        ctokens = set(c.lower().split())
        score = len(qtokens.intersection(ctokens)) / (1 + len(ctokens))
        scored.append((c, float(score)))
    scored_sorted = sorted(scored, key=lambda x: x[1], reverse=True)
    return scored_sorted