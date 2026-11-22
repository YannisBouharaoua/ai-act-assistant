"""Mesure de la recherche sur un jeu de questions de référence.

Pour chaque question, on connaît l'article attendu. On mesure :
- ``hit_rate`` : la part des questions dont l'article attendu figure dans les k extraits ;
- ``mrr`` : la moyenne de 1/rang de cet article (1.0 s'il est toujours premier).

Cette mesure ne dit rien de la qualité des réponses rédigées : elle isole la recherche,
qui est la première cause d'erreur d'un RAG.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .retriever import Retriever


def load_golden(path: Path) -> list[dict[str, str]]:
    with Path(path).open(encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def evaluate_retrieval(retriever: Retriever, golden_path: Path, k: int = 4) -> dict[str, Any]:
    cases = load_golden(golden_path)
    hits, reciprocal, misses = 0, 0.0, []
    for case in cases:
        refs = [c.ref for c in retriever.search(case["question"], k=k)]
        if case["expected_ref"] in refs:
            hits += 1
            reciprocal += 1.0 / (refs.index(case["expected_ref"]) + 1)
        else:
            misses.append({**case, "retrieved": refs})
    n = len(cases)
    return {
        "cases": n,
        "k": k,
        "hit_rate": round(hits / n, 3) if n else 0.0,
        "mrr": round(reciprocal / n, 3) if n else 0.0,
        "misses": misses,
    }
