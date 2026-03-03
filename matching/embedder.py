"""
Embedding abstraction with a deterministic local embedder.

This is intentionally simple and local-first so the matching pipeline can run
without external services. Replace `LocalHashEmbedder` with a real embedding
provider later without changing the matching service contract.
"""
from __future__ import annotations

import hashlib
import math
import re
from typing import List


class LocalHashEmbedder:
    def __init__(self, dim: int = 96):
        self.dim = dim

    def embed(self, text: str) -> List[float]:
        vec = [0.0] * self.dim
        tokens = re.findall(r"[a-zA-Z0-9_#+.-]+", (text or "").lower())
        if not tokens:
            return vec
        for tok in tokens:
            h = hashlib.sha256(tok.encode("utf-8")).hexdigest()
            idx = int(h[:8], 16) % self.dim
            sign = -1.0 if int(h[8:10], 16) % 2 else 1.0
            weight = 1.0 + (len(tok) / 20.0)
            vec[idx] += sign * weight
        norm = math.sqrt(sum(v * v for v in vec))
        if norm == 0:
            return vec
        return [v / norm for v in vec]

    @property
    def model_name(self) -> str:
        return f"local-hash-embedder-{self.dim}d"
