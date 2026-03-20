from __future__ import annotations

from dataclasses import dataclass, field

from modules.narrative_router.contracts import NarrativeFamilyContract


def _normalize_token(value: str | None) -> str:
    return (value or "").strip().lower().replace("_", "-")


@dataclass(frozen=True)
class NarrativeFamilyPlugin:
    key: str
    display_name: str
    description: str
    family_aliases: tuple[str, ...]
    genre_aliases: tuple[str, ...]
    integrated_order_path: str
    planning_path: str
    production_path: str
    bi_path: str
    contract: NarrativeFamilyContract
    extra_paths: dict[str, str] = field(default_factory=dict)

    def matches_family_hint(self, family_hint: str | None) -> bool:
        token = _normalize_token(family_hint)
        return bool(token) and token in {_normalize_token(item) for item in self.family_aliases}

    def matches_genre(self, genre: str | None) -> bool:
        token = _normalize_token(genre)
        return bool(token) and token in {_normalize_token(item) for item in self.genre_aliases}

    def document_paths(self) -> list[str]:
        return [
            self.integrated_order_path,
            self.planning_path,
            self.production_path,
            self.bi_path,
        ]
