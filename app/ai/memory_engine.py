
# app/ai/memory_engine.py
"""
Memory Engine for Zylos

Manages three tiers of memory:
- Short-term: Conversation-level ephemeral storage (fast, non-persistent).
- Mid-term: Per-user rolling summaries (persisted).
- Long-term: Per-user knowledge items (persisted + vectorized for RAG).

Also includes a simple knowledge graph for storing entity relationships.
"""

import json
import threading
import time
import os
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

from .rag_engine import search as rag_search, rank_candidates
from ..core.config import settings
from .summarizer import summarize_text

LOCK = threading.RLock()

DATA_DIR = "app/data"
LONG_PATH = os.path.join(DATA_DIR, "memory_long.json")
MID_PATH = os.path.join(DATA_DIR, "memory_mid.json")
KG_PATH = os.path.join(DATA_DIR, "memory_kg.json")

# --- In-memory & persisted data stores ---
_short_memory: Dict[str, List[Dict[str, Any]]] = {}  # {conv_id: [{text, ts, user_id, role}]}
_mid_cache: Dict[str, List[Dict[str, Any]]] = {}      # {user_id: [{summary, ts}]}
_long_cache: Dict[str, List[Dict[str, Any]]] = {}     # {user_id: [{id, type, text, meta, ts}]}
_kg: Dict[str, Dict[str, Any]] = {}                  # {node: {relations: {rel: [targets]}, meta: {}}}

# --- Initialization ---
def _load_json(path: str) -> Dict:
    if not os.path.exists(path):
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return {}

def _persist_json(path: str, obj: Dict) -> None:
    tmp_path = path + ".tmp"
    try:
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(obj, f, ensure_ascii=False, indent=2)
        os.replace(tmp_path, path)
    except IOError as e:
        print(f"Error persisting JSON to {path}: {e}")

def _initialize_stores():
    global _mid_cache, _long_cache, _kg
    os.makedirs(DATA_DIR, exist_ok=True)
    with LOCK:
        _mid_cache = _load_json(MID_PATH)
        _long_cache = _load_json(LONG_PATH)
        _kg = _load_json(KG_PATH)

# --- Persistence Helpers ---
def _persist_long():
    with LOCK:
        _persist_json(LONG_PATH, _long_cache)

def _persist_mid():
    with LOCK:
        _persist_json(MID_PATH, _mid_cache)

def _persist_kg():
    with LOCK:
        _persist_json(KG_PATH, _kg)

# --- Utility Helpers ---
def _now_ts() -> str:
    return datetime.utcnow().isoformat() + "Z"

# --------------------------------
# SHORT-TERM MEMORY (CONVERSATION)
# --------------------------------
def add_short_memory(conversation_id: str, item: Dict[str, Any]):
    """Adds an item to the ephemeral conversation history."""
    with LOCK:
        history = _short_memory.setdefault(conversation_id, [])
        history.append({
            "text": item.get("text"),
            "role": item.get("role", "user"),
            "user_id": item.get("user_id"),
            "ts": item.get("ts", _now_ts())
        })
        # Keep short-term memory bounded
        if len(history) > settings.SHORT_TERM_MEMORY_LIMIT:
            _short_memory[conversation_id] = history[-settings.SHORT_TERM_MEMORY_LIMIT:]

def retrieve_short(conversation_id: str, limit: int = 50) -> List[Dict[str, Any]]:
    """Retrieves the last N items from a conversation."""
    with LOCK:
        return _short_memory.get(conversation_id, [])[-limit:].copy()

# ---------------------------
# MID-TERM MEMORY (SUMMARIES)
# ---------------------------
def add_mid_memory(user_id: str, summary: str, ts: Optional[str] = None):
    """Adds a new summary to the user's mid-term memory."""
    with LOCK:
        summaries = _mid_cache.setdefault(user_id, [])
        summaries.append({"summary": summary, "ts": ts or _now_ts()})
        if len(summaries) > 200:
            summaries[:] = summaries[-200:]
    _persist_mid()

def get_mid_memory(user_id: str, limit: int = 10) -> List[str]:
    """Retrieves the last N summaries for a user."""
    with LOCK:
        summaries = _mid_cache.get(user_id, [])[-limit:]
        return [s["summary"] for s in summaries]

# ---------------------------
# LONG-TERM MEMORY (KNOWLEDGE)
# ---------------------------
def add_long_memory(user_id: str, item: Dict[str, Any]):
    """Adds a new knowledge item to the user's long-term memory and vector store."""
    from app.database.vector_store import vector_store  # Lazy import

    with LOCK:
        knowledge = _long_cache.setdefault(user_id, [])
        entry = {
            "id": f"mem_{int(time.time() * 1000)}_{len(knowledge)}",
            "type": item.get("type", "note"),
            "text": item.get("text"),
            "meta": item.get("meta", {}),
            "ts": item.get("ts", _now_ts())
        }
        knowledge.append(entry)
    _persist_long()

    # Add to vector store for retrieval
    if hasattr(vector_store, "add") and entry["text"]:
        try:
            metadata = {
                "user_id": user_id,
                "memory_id": entry["id"],
                "type": entry["type"],
                "created_at": entry["ts"]
            }
            vector_store.add([entry["text"]], [metadata])
        except Exception as e:
            print(f"Failed to add memory to vector store: {e}")

    return entry

def get_long_memory(user_id: str, limit: int = 50) -> List[Dict[str, Any]]:
    """Retrieves the last N knowledge items for a user (not ranked)."""
    with LOCK:
        return (_long_cache.get(user_id, [])[-limit:]).copy()

# ---------------------------
# KNOWLEDGE GRAPH
# ---------------------------
def kg_add_relation(subject: str, relation: str, obj: str, meta: Optional[Dict[str, Any]] = None):
    """Adds a directed relation: Subject -> Relation -> Object."""
    with LOCK:
        node = _kg.setdefault(subject, {"relations": {}, "meta": {}})
        rels = node["relations"].setdefault(relation, [])
        if obj not in rels:
            rels.append(obj)
        if meta:
            node["meta"].update(meta)
    _persist_kg()
    return True

def kg_get_relations(subject: str) -> Dict[str, List[str]]:
    """Gets all outgoing relations from a subject."""
    with LOCK:
        return _kg.get(subject, {}).get("relations", {}).copy()

# ---------------------------
# HIGH-LEVEL BRAIN HELPERS
# ---------------------------
def add_memory_item(user_id: str, user_text: str, assistant_text: str, metadata: Optional[Dict[str, Any]] = None):
    """
    Called by the brain after a reply is generated.
    Stores the dialog turn in long-term memory and may trigger a summary update.
    """
    combined_text = f"User asked: {user_text}\nZylos replied: {assistant_text}"
    entry = add_long_memory(user_id, {
        "type": "dialog",
        "text": combined_text,
        "meta": metadata or {}
    })

    # Occasionally, update the mid-term summary.
    with LOCK:
        user_long_mem = _long_cache.get(user_id, [])
        if len(user_long_mem) % settings.SUMMARIZE_MEMORY_INTERVAL == 0:
            summarize_user_memory(user_id)

    return entry

def get_relevant_memory(user_id: str, query: str, conversation_id: str, k: int = 5) -> List[str]:
    """
    The main retrieval function used by the brain.
    Gathers candidates from all memory types and ranks them for relevance.
    """
    candidates = []

    # 1. Short-term conversation history
    short_term = retrieve_short(conversation_id, limit=20)
    candidates.extend([f'Conversation context: {item["role"]} said \'{item["text"]}\'' for item in short_term])

    # 2. Mid-term user summaries
    mid_term = get_mid_memory(user_id, limit=10)
    candidates.extend([f"Memory summary: {summary}" for summary in mid_term])

    # 3. Long-term vectorized search (RAG)
    try:
        # The RAG engine internally handles vector search
        rag_results = rag_search(user_id, query, k=k)
        candidates.extend([res['text'] for res in rag_results])
    except Exception as e:
        print(f"Could not perform RAG search for memory: {e}")

    if not candidates:
        return []

    # 4. Rank all candidates against the current query
    ranked_results = rank_candidates(query, candidates)
    return [res['text'] for res in ranked_results[:k]]

def summarize_user_memory(user_id: str):
    """Creates and stores a new summary of the user's recent long-term memories."""
    with LOCK:
        last_items = _long_cache.get(user_id, [])[-15:]

    if not last_items:
        return

    full_text = "\n\n".join([item["text"] for item in last_items])
    try:
        summary = summarize_text(full_text, max_tokens=150)
        if summary:
            add_mid_memory(user_id, summary)
            print(f"Successfully summarized memory for user {user_id}")
    except Exception as e:
        print(f"Could not summarize memory for user {user_id}: {e}")

def cleanup_aged_memory(max_age_days: int = 365):
    """
    Periodically cleans up old items from mid-term and long-term memory.
    Note: This does not currently remove items from the vector index.
    """
    cutoff_date = datetime.utcnow() - timedelta(days=max_age_days)
    with LOCK:
        for user_id in list(_long_cache.keys()):
            _long_cache[user_id] = [item for item in _long_cache[user_id] if datetime.fromisoformat(item['ts'].replace('Z','')) > cutoff_date]
            if not _long_cache[user_id]:
                del _long_cache[user_id]

        for user_id in list(_mid_cache.keys()):
            _mid_cache[user_id] = [item for item in _mid_cache[user_id] if datetime.fromisoformat(item['ts'].replace('Z','')) > cutoff_date]
            if not _mid_cache[user_id]:
                del _mid_cache[user_id]

    _persist_long()
    _persist_mid()
    print("Finished cleaning up aged memory.")

# --- Load data on module import ---
_initialize_stores()
