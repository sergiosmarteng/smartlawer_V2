"""Comparação de artefatos por IDs estáveis (Onda 0 Task 15, §11.3).

Nunca muta o artefato publicado; a comparação é leitura pura sobre os
conteúdos versionados.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class ArtifactDiff:
    added: dict[str, list[str]] = field(default_factory=dict)
    removed: dict[str, list[str]] = field(default_factory=dict)
    changed: dict[str, list[str]] = field(default_factory=dict)


_DIFF_SECTIONS = ("claims", "facts", "evidence", "theses", "visuals")


def _by_id(items) -> dict[str, dict]:
    return {
        str(item.get("id")): item
        for item in (items or [])
        if isinstance(item, dict) and item.get("id")
    }


def compare_artifacts(before: dict, after: dict) -> ArtifactDiff:
    """Identifica adição, remoção e alteração por ID estável."""
    added: dict[str, list[str]] = {}
    removed: dict[str, list[str]] = {}
    changed: dict[str, list[str]] = {}
    for section in _DIFF_SECTIONS:
        old, new = _by_id((before or {}).get(section)), _by_id((after or {}).get(section))
        section_added = sorted(set(new) - set(old))
        section_removed = sorted(set(old) - set(new))
        section_changed = sorted(
            item_id for item_id in set(old) & set(new) if old[item_id] != new[item_id]
        )
        if section_added:
            added[section] = section_added
        if section_removed:
            removed[section] = section_removed
        if section_changed:
            changed[section] = section_changed
    return ArtifactDiff(added=added, removed=removed, changed=changed)
