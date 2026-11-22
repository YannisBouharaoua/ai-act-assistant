"""Recherche des extraits pertinents.

Par défaut la recherche est lexicale (BM25) : sur un texte juridique, les mots exacts
(« déployeur », « notation sociale ») portent l'essentiel du sens. Un index dense peut
être ajouté ; les deux classements sont alors fusionnés par Reciprocal Rank Fusion.
"""

from __future__ import annotations

import re
import unicodedata
from collections.abc import Sequence
from typing import Protocol

import numpy as np
from rank_bm25 import BM25Okapi

from .corpus import Chunk

_STOPWORDS = frozenset(
    """a au aux avec ce ces cette dans de des du elle en est et il ils je la le les leur
    lui ma mais me mes mon ne nos notre nous on ou par pas pour qu que quel quelle quelles
    quels qui sa se ses son sur ta te tes ton tu un une vos votre vous y d l n s c j m t
    sont etre peut doit dois faut fait faire quoi comment""".split()
)
_TOKEN = re.compile(r"[a-z0-9]+")


def tokenize(text: str) -> list[str]:
    """Minuscules, sans accents, sans mots vides, pluriels simples ramenés au singulier."""
    folded = unicodedata.normalize("NFKD", text.lower())
    folded = "".join(c for c in folded if not unicodedata.combining(c))
    tokens = []
    for tok in _TOKEN.findall(folded):
        if tok in _STOPWORDS:
            continue
        if len(tok) > 3 and tok.endswith(("s", "x")):
            tok = tok[:-1]
        tokens.append(tok)
    return tokens


class Embedder(Protocol):
    def embed(self, texts: Sequence[str]) -> np.ndarray:
        """Renvoie une matrice (n_textes, dimension)."""


class SentenceTransformerEmbedder:
    """Embeddings locaux. Nécessite l'extra ``dense``."""

    def __init__(self, model_name: str) -> None:
        from sentence_transformers import SentenceTransformer

        self._model = SentenceTransformer(model_name)

    def embed(self, texts: Sequence[str]) -> np.ndarray:
        return np.asarray(self._model.encode(list(texts), normalize_embeddings=True))


def reciprocal_rank_fusion(rankings: Sequence[Sequence[int]], k: int = 60) -> list[int]:
    """Fusionne plusieurs classements d'indices en un seul."""
    scores: dict[int, float] = {}
    for ranking in rankings:
        for rank, idx in enumerate(ranking):
            scores[idx] = scores.get(idx, 0.0) + 1.0 / (k + rank + 1)
    return sorted(scores, key=lambda i: (-scores[i], i))


class Retriever:
    def __init__(self, chunks: Sequence[Chunk], embedder: Embedder | None = None) -> None:
        if not chunks:
            raise ValueError("Le corpus est vide.")
        self.chunks = list(chunks)
        docs = [tokenize(f"{c.ref} {c.title} {c.text}") for c in self.chunks]
        self._doc_terms = [set(d) for d in docs]
        self._bm25 = BM25Okapi(docs)
        self._embedder = embedder
        self._matrix = (
            self._normalize(embedder.embed([f"{c.title}\n{c.text}" for c in self.chunks]))
            if embedder
            else None
        )

    @staticmethod
    def _normalize(m: np.ndarray) -> np.ndarray:
        norms = np.linalg.norm(m, axis=1, keepdims=True)
        return m / np.where(norms == 0, 1.0, norms)

    def _lexical(self, query: str) -> list[int]:
        tokens = tokenize(query)
        if not tokens:
            return []
        scores = self._bm25.get_scores(tokens)
        # Un extrait qui ne partage aucun mot avec la question n'est pas un résultat.
        query_terms = set(tokens)
        order = np.argsort(-scores, kind="stable")
        return [int(i) for i in order if query_terms & self._doc_terms[int(i)]]

    def _dense(self, query: str) -> list[int]:
        assert self._embedder is not None and self._matrix is not None
        q = self._normalize(self._embedder.embed([query]))[0]
        return [int(i) for i in np.argsort(-(self._matrix @ q), kind="stable")]

    def search(self, query: str, k: int = 4) -> list[Chunk]:
        lexical = self._lexical(query)
        if self._embedder is None:
            ranked = lexical
        else:
            # Le dense classe tout le corpus : on ne garde que sa tête pour la fusion.
            ranked = reciprocal_rank_fusion([lexical, self._dense(query)[: max(k * 3, 10)]])
        return [self.chunks[i] for i in ranked[:k]]
