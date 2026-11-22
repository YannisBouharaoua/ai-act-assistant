"""Télécharge le texte français de l'AI Act sur EUR-Lex et le met au format du corpus.

    pip install ".[fetch]"
    python scripts/fetch_corpus.py                 # téléchargement
    python scripts/fetch_corpus.py --from-file page.html   # page enregistrée à la main

EUR-Lex filtre parfois les téléchargements automatisés. Si le téléchargement échoue,
ouvrez l'URL dans un navigateur, enregistrez la page, puis utilisez --from-file.
Ensuite : CORPUS_PATH=data/corpus/ai_act_fr.txt
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

URL = "https://eur-lex.europa.eu/legal-content/FR/TXT/HTML/?uri=OJ:L_202401689"


def html_to_text(html: str) -> str:
    from bs4 import BeautifulSoup

    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style"]):
        tag.decompose()
    lines = (line.strip() for line in soup.get_text("\n").splitlines())
    return "\n".join(line for line in lines if line)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--from-file", type=Path, help="page HTML ou texte déjà enregistrée")
    parser.add_argument("--out", type=Path, default=Path("data/corpus/ai_act_fr.txt"))
    args = parser.parse_args()

    if args.from_file:
        raw = args.from_file.read_text(encoding="utf-8")
    else:
        import httpx

        resp = httpx.get(URL, follow_redirects=True, timeout=60)
        if resp.status_code != 200 or "Article" not in resp.text:
            print(
                f"Téléchargement refusé (HTTP {resp.status_code}). Enregistrez la page depuis "
                f"un navigateur puis relancez avec --from-file.\n{URL}",
                file=sys.stderr,
            )
            return 1
        raw = resp.text

    text = html_to_text(raw) if "<" in raw[:2000] else raw

    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
    from ai_act_assistant.corpus import parse_corpus

    chunks = parse_corpus(text)
    if not chunks:
        print("Aucun article reconnu dans ce fichier.", file=sys.stderr)
        return 1
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(text, encoding="utf-8")
    refs = {c.ref for c in chunks}
    print(f"{args.out} : {len(chunks)} extraits, {len(refs)} articles et annexes.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
