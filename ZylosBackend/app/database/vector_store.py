# app/database/vector_store.py
import os
from ..core.config import settings

EMBED_PATH = "app/data/embeddings.faiss"

# Try to import heavy deps; if not present provide a dummy fallback.
try:
    from sentence_transformers import SentenceTransformer
    import faiss
    import numpy as np

    MODEL_NAME = "all-MiniLM-L6-v2"
    _model = SentenceTransformer(MODEL_NAME)

    if os.path.exists(EMBED_PATH):
        import pickle
        data = pickle.load(open(EMBED_PATH, "rb"))
        _index = data["index"]
        _docs = data["docs"]
    else:
        # create an L2 index for 384-dim embeddings
        _index = faiss.IndexFlatL2(384)
        _docs = []

    class VectorStore:
        def __init__(self, model=_model, index=_index, docs=_docs, path=EMBED_PATH):
            self.model = model
            self.index = index
            self.docs = docs
            self.path = path

        def save(self):
            import pickle
            pickle.dump({"index": self.index, "docs": self.docs}, open(self.path, "wb"))

        def add(self, texts):
            # texts: list[str]
            embs = self.model.encode(texts, convert_to_numpy=True).astype("float32")
            self.index.add(embs)
            self.docs.extend(texts)
            self.save()

        def search(self, query, k=5):
            emb = self.model.encode([query], convert_to_numpy=True).astype("float32")
            D, I = self.index.search(emb, k)
            res = []
            for i in I[0]:
                if i < len(self.docs):
                    res.append(self.docs[i])
            return res

    vector_store = VectorStore()

except Exception as exc:
    # Fallback dummy store (no embeddings). Keeps API consistent.
    print("[vector_store] Optional dependencies missing or failed:", exc)

    class DummyVectorStore:
        def add(self, texts):
            return None
        def search(self, query, k=5):
            return []
    vector_store = DummyVectorStore()