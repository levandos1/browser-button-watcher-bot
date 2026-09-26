from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class AppState(StrEnum):
    DISCONNECTED = "DISCONNECTED"
    CONNECTED = "CONNECTED"
    READY = "READY"
    MONITORING = "MONITORING"
    STOPPING = "STOPPING"
    ERROR = "ERROR"


class MatchMode(StrEnum):
    EXACT = "Exact(полное совпадение)"
    CONTAINS = "Contains(кнопка должна содержать указанную фразу)"
    CASE_INSENSITIVE_EXACT = "Case-insensitive exact(полное совпадение без учёта регистра)"
    CASE_INSENSITIVE_CONTAINS = "Case-insensitive contains(частичное совпадение без учёта регистра)"


@dataclass(slots=True)
class TabInfo:
    key: str
    title: str
    url: str


@dataclass(slots=True)
class MonitorSettings:
    target_text: str
    match_mode: MatchMode
    interval_ms: int
    cooldown_seconds: float


def normalize_text(value: str) -> str:
    """Collapse Unicode whitespace without changing meaningful characters."""
    return " ".join(value.split())


def text_matches(candidate: str, target: str, mode: MatchMode) -> bool:
    candidate_n = normalize_text(candidate)
    target_n = normalize_text(target)
    if mode == MatchMode.EXACT:
        return candidate_n == target_n
    if mode == MatchMode.CONTAINS:
        return target_n in candidate_n
    if mode == MatchMode.CASE_INSENSITIVE_EXACT:
        return candidate_n.casefold() == target_n.casefold()
    if mode == MatchMode.CASE_INSENSITIVE_CONTAINS:
        return target_n.casefold() in candidate_n.casefold()
    return False
