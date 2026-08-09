from __future__ import annotations

from pathlib import Path
import re
import sys


def replace_method(
    text: str,
    method_name: str,
    replacement: str,
) -> str:
    pattern = re.compile(
        rf"^    def {re.escape(method_name)}\("
        rf".*?(?=^    def |\Z)",
        re.MULTILINE | re.DOTALL,
    )
    match = pattern.search(text)
    if not match:
        raise RuntimeError(f"Could not locate method: {method_name}")
    return (
        text[:match.start()]
        + replacement.rstrip()
        + "\n\n"
        + text[match.end():]
    )


def main() -> int:
    root = Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()
    path = root / "core/executive/timeline/repository.py"
    text = path.read_text(encoding="utf-8")

    helper = """    def _read_disk_events_unlocked(
        self,
    ) -> tuple[TimelineEvent, ...]:
        return tuple(
            TimelineEventSerializer.loads(line)
            for line in self._storage.iter_lines()
        )
"""

    if "_read_disk_events_unlocked" not in text:
        marker = "    def reload("
        index = text.find(marker)
        if index < 0:
            raise RuntimeError("Could not locate repository reload method.")
        text = text[:index] + helper + "\n" + text[index:]

    reload_method = """    def reload(self) -> tuple[TimelineEvent, ...]:
        with self._lock:
            with self._storage.exclusive():
                events = self._read_disk_events_unlocked()
                self._certify_candidate(events)
                self._events = events
                self._indexes = TimelineRepositoryIndexes.build(events)
                return events
"""

    append_many_method = """    def append_many(
        self,
        events: Iterable[TimelineEvent],
    ) -> tuple[TimelineEvent, ...]:
        incoming = tuple(events)
        if not incoming:
            return ()

        with self._lock:
            with self._storage.exclusive():
                disk_events = self._read_disk_events_unlocked()
                self._certify_candidate(disk_events)
                candidate = disk_events + incoming

                try:
                    self._certify_candidate(candidate)
                except TimelineRepositoryIntegrityError as exc:
                    self._events = disk_events
                    self._indexes = TimelineRepositoryIndexes.build(
                        disk_events
                    )
                    raise TimelineRepositoryConflictError(
                        str(exc)
                    ) from exc

                self._storage.append_many_unlocked(
                    TimelineEventSerializer.dump_line(event)
                    for event in incoming
                )
                self._events = candidate
                self._indexes = TimelineRepositoryIndexes.build(candidate)
                return incoming
"""

    text = replace_method(text, "reload", reload_method)
    text = replace_method(text, "append_many", append_many_method)
    path.write_text(text, encoding="utf-8")
    print("[PASS] ExecutiveTimelineRepository transaction patch applied")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
