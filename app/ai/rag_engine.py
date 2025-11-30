# app/ai/rag_engine.py
"""
RAG Engine for Zylos.
- Wraps the vector store to provide search and ranking capabilities.
- Provides `search` to find relevant documents for a user.
- Provides `rank_candidates` to score and sort texts based on relevance to a query.
"""

import logging
from typing import List, Dict, Any

# --- Dependencies --- #
# Attempt to import vector store and its dependencies. If they are not installed,
# the RAG engine will be disabled, and the application will fall back to simpler methods.
try:
    from app.database.vector_store import vector_store
    import numpy as np
    VECTOR_STORE_AVAILABLE = True
except ImportError as e:
    vector_store = None
    np = None
    VECTOR_STORE_AVAILABLE = False
    logging.warning(f"[rag_engine] Vector store dependencies not found. RAG features will be disabled. Error: {e}")

# --- Public Functions --- #

def search(user_id: str, query: str, k: int = 5) -> List[Dict[str, Any]]:
    """
    Searches the vector store for the top `k` documents relevant to the query,
    filtered for a specific user.

    Args:
        user_id: The ID of the user to filter memories for.
        query: The user's search query.
        k: The maximum number of results to return.

    Returns:
        A list of result dictionaries, each containing document text and metadata.
    """
    if not query or not VECTOR_STORE_AVAILABLE:
        return []

    try:
        # The vector store's search method must support filtering by metadata.
        results = vector_store.search(query, k=k, filter_metadata={"user_id": user_id})
        return results or []
    except Exception as e:
        logging.exception(f"RAG search failed for user '{user_id}': {e}")
        return []

def rank_candidates(query: str, candidates: List[str], k: int = 10) -> List[Dict[str, Any]]:
    """
    Ranks a list of candidate texts against a query for relevance.

    If the vector store is available, it uses cosine similarity for accurate ranking.
    Otherwise, it falls back to a simple keyword-based (Jaccard) similarity score.

    Args:
        query: The query to rank against.
        candidates: A list of texts to be ranked.
        k: The number of top candidates to return.

    Returns:
        A sorted list of dictionaries, each with 'text' and 'score' keys.
    """
    if not query or not candidates:
        return []

    # --- Vector-based Ranking (High Quality) ---
    if VECTOR_STORE_AVAILABLE:
        try:
            model = getattr(vector_store, "model", None)
            if model is None:
                raise RuntimeError("Vector store is missing the 'model' attribute required for encoding.")

            # Encode the query and candidate texts, normalizing them for cosine similarity.
            q_emb = model.encode([query], convert_to_numpy=True, normalize_embeddings=True)
            cand_embs = model.encode(candidates, convert_to_numpy=True, normalize_embeddings=True)

            # Calculate cosine similarity (dot product of normalized vectors).
            scores = np.dot(cand_embs, q_emb.T).flatten().tolist()

            ranked = [{"text": c, "score": s} for c, s in zip(candidates, scores)]
            ranked.sort(key=lambda x: x["score"], reverse=True) # Sort descending by score
            return ranked[:k]

        except Exception as e:
            logging.warning(f"Vector-based ranking failed, falling back to keyword method. Error: {e}")
            # Fall through to the keyword-based fallback method.

    # --- Keyword-based Ranking (Fallback) ---
    q_tokens = set(query.lower().split())
    if not q_tokens:
        return []

    scored_candidates = []
    for text in candidates:
        c_tokens = set(text.lower().split())
        if not c_tokens:
            score = 0.0
        else:
            # Jaccard similarity: intersection over union
            score = len(q_tokens.intersection(c_tokens)) / len(q_tokens.union(c_tokens))
        scored_candidates.append({"text": text, "score": score})

    scored_candidates.sort(key=lambda x: x["score"], reverse=True)
    return scored_candidates[:k]
