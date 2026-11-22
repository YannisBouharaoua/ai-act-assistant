"""Découpage du règlement en extraits citables.

Le texte est découpé par article (et par annexe), jamais au milieu d'une unité
juridique sans en garder la référence : chaque extrait porte « Article N » ou
« Annexe N », ce qui permet de vérifier ensuite les citations du modèle.
"""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass
from pathlib import Path

_HEADING = re.compile(r"^\s*(?:(Article)\s+(\d+|premier)|(ANNEXE)\s+([IVXLC]+))\s*$", re.IGNORECASE)
_CITATION = re.compile(r"\[\s*(?:(Article)\s+(\d+)|(Annexe)\s+([IVXLC]+))\s*\]", re.IGNORECASE)


@dataclass(frozen=True)
class Chunk:
    id: str
    ref: str
    title: str
    text: str

    def to_dict(self) -> dict[str, str]:
        return asdict(self)


def normalize_ref(kind: str, number: str) -> str:
    """Forme canonique d'une référence : « Article 5 » ou « Annexe III »."""
    if kind.lower() == "article":
        return f"Article {1 if number.lower() == 'premier' else int(number)}"
    return f"Annexe {number.upper()}"


def extract_citations(text: str) -> list[str]:
    """Références citées entre crochets dans une réponse, sans doublon, dans l'ordre."""
    refs: list[str] = []
    for m in _CITATION.finditer(text):
        ref = normalize_ref(m.group(1) or m.group(3), m.group(2) or m.group(4))
        if ref not in refs:
            refs.append(ref)
    return refs


def _split_long(paragraphs: list[str], max_chars: int) -> list[str]:
    parts: list[str] = []
    current: list[str] = []
    size = 0
    for p in paragraphs:
        if current and size + len(p) > max_chars:
            parts.append("\n".join(current))
            current, size = [], 0
        current.append(p)
        size += len(p) + 1
    if current:
        parts.append("\n".join(current))
    return parts


def parse_corpus(text: str, max_chars: int = 1800) -> list[Chunk]:
    """Découpe un texte dont les articles commencent par une ligne « Article N ».

    La ligne qui suit le titre d'article est prise comme intitulé. Un article plus long
    que ``max_chars`` est découpé par paragraphes ; chaque morceau garde la référence.
    """
    sections: list[tuple[str, list[str]]] = []
    for raw in text.splitlines():
        line = raw.strip()
        m = _HEADING.match(line)
        if m:
            ref = normalize_ref(m.group(1) or m.group(3), m.group(2) or m.group(4))
            sections.append((ref, []))
        elif sections and line:
            sections[-1][1].append(line)

    chunks: list[Chunk] = []
    seen: dict[str, int] = {}
    for ref, lines in sections:
        if not lines:
            continue
        title, body = lines[0], lines[1:] or lines[:1]
        for part in _split_long(body, max_chars):
            n = seen.get(ref, 0)
            seen[ref] = n + 1
            slug = ref.lower().replace(" ", "-")
            chunks.append(
                Chunk(id=slug if n == 0 else f"{slug}#{n + 1}", ref=ref, title=title, text=part)
            )
    return chunks


def load_corpus(path: Path, max_chars: int = 1800) -> list[Chunk]:
    chunks = parse_corpus(Path(path).read_text(encoding="utf-8"), max_chars=max_chars)
    if not chunks:
        raise ValueError(
            f"Aucun article trouvé dans {path} : chaque article doit commencer "
            "par une ligne « Article N »."
        )
    return chunks
