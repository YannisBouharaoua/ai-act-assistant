"""Ligne de commande : ``ai-act ask``, ``ai-act corpus``, ``ai-act eval``, ``ai-act serve``."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .config import Settings
from .corpus import load_corpus
from .evaluate import evaluate_retrieval
from .retriever import Retriever
from .service import Assistant


def _print_result(result: dict) -> None:
    print(f"\n[{result['status']}] conversation {result['thread_id']}")
    if result["answer"]:
        print(result["answer"])
    for s in result["sources"]:
        print(f"  - {s['ref']} — {s['title']}")


def cmd_ask(args: argparse.Namespace) -> int:
    assistant = Assistant()
    result = assistant.ask(args.question)
    if result["status"] == "pending_review":
        pending = assistant.pending(result["thread_id"])
        print(f"\nRelecture humaine requise ({pending['reason']}). Brouillon :\n")
        print(pending["draft"])
        if not sys.stdin.isatty():
            print(f"\nEn attente. Reprendre avec : conversation {result['thread_id']}")
            return 0
        choice = input("\nValider ? [o]ui / [n]on : ").strip().lower()
        decision = "approve" if choice.startswith("o") else "reject"
        result = assistant.review(result["thread_id"], decision, reviewer="cli")
    _print_result(result)
    return 0


def cmd_corpus(args: argparse.Namespace) -> int:
    chunks = load_corpus(Settings().corpus_path)
    refs = sorted({c.ref for c in chunks})
    print(f"{len(chunks)} extraits, {len(refs)} articles et annexes.")
    for c in chunks[: args.limit]:
        print(f"  {c.id:<14} {c.title[:70]}")
    return 0


def cmd_eval(args: argparse.Namespace) -> int:
    settings = Settings()
    retriever = Retriever(load_corpus(settings.corpus_path))
    report = evaluate_retrieval(retriever, Path(args.golden), k=settings.top_k)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["hit_rate"] >= args.min_hit_rate else 1


def cmd_serve(args: argparse.Namespace) -> int:
    import uvicorn

    uvicorn.run("ai_act_assistant.api:app", host=args.host, port=args.port)
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="ai-act", description="Assistant de conformité AI Act")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("ask", help="poser une question")
    p.add_argument("question")
    p.set_defaults(func=cmd_ask)

    p = sub.add_parser("corpus", help="résumer le corpus chargé")
    p.add_argument("--limit", type=int, default=20)
    p.set_defaults(func=cmd_corpus)

    p = sub.add_parser("eval", help="mesurer la qualité de la recherche")
    p.add_argument("--golden", default="eval/golden.jsonl")
    p.add_argument("--min-hit-rate", type=float, default=0.8)
    p.set_defaults(func=cmd_eval)

    p = sub.add_parser("serve", help="lancer l'API")
    p.add_argument("--host", default="127.0.0.1")
    p.add_argument("--port", type=int, default=8000)
    p.set_defaults(func=cmd_serve)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
