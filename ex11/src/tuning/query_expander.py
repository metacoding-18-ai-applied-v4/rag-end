"""챕터 9 — 약어 사전으로 질문을 확장하는 도메인 객체.

`WFH` 같은 사내 약어를 `WFH(재택근무)`로 풀어 붙여 검색 재현율을 높인다.
사전은 생성자 주입으로 교체할 수 있어 부서별·언어별 맞춤이 가능하다.
"""

from __future__ import annotations


DEFAULT_ABBREVIATIONS: dict[str, str] = {
    "WFH": "재택근무",
    "OT": "초과근무",
    "연차": "연차 휴가",
    "병가": "병가 유급휴가",
    "DLP": "데이터 유출 방지",
    "VPN": "가상사설망",
    "USB": "USB 외부저장장치",
}


class QueryExpander:
    """사내 약어·동의어 확장기."""

    def __init__(self, dictionary: dict[str, str] | None = None) -> None:
        self.dictionary = dictionary if dictionary is not None else DEFAULT_ABBREVIATIONS

    def expand(self, query: str) -> str:
        expanded = query
        for abbr, full in self.dictionary.items():
            if abbr in expanded and full not in expanded:
                expanded = expanded.replace(abbr, f"{abbr}({full})")
        return expanded
