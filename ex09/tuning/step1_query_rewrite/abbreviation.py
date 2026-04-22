"""약어/동의어 확장 -- ABBREVIATION_MAP, SYNONYM_MAP을 사용하여 쿼리를 풀어씁니다."""

from __future__ import annotations

from .data import ABBREVIATION_MAP, SYNONYM_MAP


def expand_abbreviations(query: str) -> dict:
    """쿼리의 약어와 동의어를 확장합니다.

    ABBREVIATION_MAP과 SYNONYM_MAP을 사용하여 쿼리 내 약어와 동의어를
    풀어씁니다.

    Returns:
        {"original": str, "expanded": str, "applied": list[str]}
    """
    # TODO: 쿼리의 약어와 동의어를 확장합니다.
    expanded = query
    applied: list[str] = []

    # 1. 약어 확장
    for abbrev, full_form in ABBREVIATION_MAP.items():
        if abbrev in expanded:
            expanded = expanded.replace(abbrev, full_form)
            applied.append(f"약어 '{abbrev}' -> '{full_form}'")

    # 2. 동의어 확장
    for term, synonym in SYNONYM_MAP.items():
        if term in expanded and synonym not in expanded:
            expanded = expanded.replace(term, synonym)
            applied.append(f"동의어 '{term}' -> '{synonym}'")

    return {"original": query, "expanded": expanded, "applied": applied}
