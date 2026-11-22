"""Journal d'audit : une ligne JSON par étape de l'agent.

Le fichier est en ajout seul. Il permet de reconstituer, pour une question donnée,
quels extraits ont été lus, ce que le modèle a répondu, qui a validé et quand.
"""

from __future__ import annotations

import json
import threading
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


class AuditLog:
    def __init__(self, path: Path) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()

    def record(self, thread_id: str, event: str, **data: Any) -> None:
        entry = {
            "ts": datetime.now(UTC).isoformat(timespec="milliseconds"),
            "thread_id": thread_id,
            "event": event,
            **data,
        }
        line = json.dumps(entry, ensure_ascii=False)
        with self._lock, self.path.open("a", encoding="utf-8") as f:
            f.write(line + "\n")

    def read(self, thread_id: str | None = None) -> list[dict[str, Any]]:
        if not self.path.exists():
            return []
        entries = []
        with self.path.open(encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                entry = json.loads(line)
                if thread_id is None or entry.get("thread_id") == thread_id:
                    entries.append(entry)
        return entries
