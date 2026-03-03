"""
In-memory vector store abstraction used for local hybrid matching.

The interface is deliberately minimal and maps cleanly to pgvector/Qdrant later.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Any, Iterable


@dataclass
class VectorRecord:
    namespace: str
    record_id: str
    vector: List[float]
    metadata: Dict[str, Any]


class InMemoryVectorStore:
    def __init__(self):
        self._records: Dict[str, List[VectorRecord]] = {}

    def upsert(self, namespace: str, records: Iterable[VectorRecord]) -> None:
        bucket = self._records.setdefault(namespace, [])
        existing = {r.record_id: i for i, r in enumerate(bucket)}
        for rec in records:
            if rec.record_id in existing:
                bucket[existing[rec.record_id]] = rec
            else:
                bucket.append(rec)

    def query(self, namespace: str, vector: List[float], top_k: int = 50, metadata_filter: Dict[str, Any] | None = None) -> List[Dict[str, Any]]:
        recs = self._records.get(namespace, [])
        results = []
        for rec in recs:
            if metadata_filter and not _metadata_matches(rec.metadata, metadata_filter):
                continue
            score = _cosine(vector, rec.vector)
            results.append({"record_id": rec.record_id, "score": score, "metadata": rec.metadata})
        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:top_k]


def _cosine(a: List[float], b: List[float]) -> float:
    if not a or not b or len(a) != len(b):
        return 0.0
    return max(0.0, min(1.0, sum(x * y for x, y in zip(a, b))))


def _metadata_matches(metadata: Dict[str, Any], filt: Dict[str, Any]) -> bool:
    for key, val in filt.items():
        cur = metadata.get(key)
        if isinstance(val, list):
            if isinstance(cur, list):
                if not any(v in cur for v in val):
                    return False
            else:
                if cur not in val:
                    return False
        else:
            if cur != val:
                return False
    return True
