from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class KillSwitch:
    tripped: bool = False
    reason: str | None = None
    book: str | None = None
    history: list[str] = field(default_factory=list)

    def trip(self, reason: str, book: str) -> None:
        self.tripped = True
        self.reason = reason
        self.book = book
        self.history.append(f"{book}:{reason}")

    def reset(self) -> None:
        self.tripped = False
        self.reason = None
        self.book = None
