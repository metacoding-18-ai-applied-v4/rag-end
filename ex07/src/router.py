"""질문 라우팅 모듈."""

import json
import os
import re

# ---------------------------------------------------------------------------
# 1. 라우팅 판단 기준 키워드 정의
# ---------------------------------------------------------------------------

# 정형 데이터(DB) 관련 키워드 — 숫자/통계/명단 조회
STRUCTURED_KEYWORDS = [
    "잔여", "잔량", "연차", "휴가", "남은", "몇 일", "며칠",
    "매출", "합계", "총액", "금액", "얼마", "실적",
    "목록", "명단", "직원", "사원", "리스트", "조회",
    "통계", "평균", "부서별", "합산", "입사일", "날짜"
]

# 비정형 데이터(문서) 관련 키워드 — 절차/정책/안내
# 주의: "알려줘", "뭐야" 같은 범용 요청 접미사는 제외한다.
#       이런 표현은 모든 질문에 붙을 수 있어 판별력이 없다.
UNSTRUCTURED_KEYWORDS = [
    "절차", "방법", "어떻게", "규정", "정책", "기준",
    "온보딩", "입사", "안내", "가이드", "매뉴얼",
    "복지", "혜택", "보안", "출장", "비용",
    "설명해", "무엇인가", "어떤가",
]

# DB 스키마 컬럼/테이블명 — Step 2 매칭 대상
SCHEMA_TERMS = {
    # leave_balance 테이블
    "remaining_days": "structured",
    "used_days": "structured",
    "total_days": "structured",
    # sales 테이블
    "amount": "structured",
    "total_amount": "structured",
    "revenue": "structured",
    # employees 테이블
    "emp_no": "structured",
    "department": "structured",
    "hire_date": "structured",
}


class QueryRouter:
    """질문 유형 분류기."""

    def __init__(self, llm=None):
        """라우터를 초기화한다."""
        self._llm = llm

    # ------------------------------------------------------------------
    # 2. 공개 인터페이스
    # ------------------------------------------------------------------

    def classify_query(self, query):
        """질문을 분석하여 처리 경로를 반환한다."""
        # ① Step 1: 규칙 기반 키워드 매칭
        step1_result = self._step1_rule_based(query)  # ①
        if step1_result is not None:
            return step1_result

        # ② Step 2: DB 스키마 컬럼명 매칭
        step2_result = self._step2_schema_based(query)  # ②
        if step2_result is not None:
            return step2_result

        # ③ Step 3: LLM 판단 (폴백)
        if self._llm is not None:
            step3_result = self._step3_llm_based(query)  # ③
            if step3_result is not None:
                return step3_result

        # ④ 기본값: 비정형으로 처리
        return "unstructured"  # ④

    def explain_routing(self, query):
        """라우팅 결과와 각 단계별 판단 근거를 반환한다."""
        step1 = self._step1_rule_based(query)
        step2 = self._step2_schema_based(query)
        final = self.classify_query(query)

        return {
            "query": query,
            "step1": step1,
            "step2": step2,
            "route": final,
        }

    # ------------------------------------------------------------------
    # 3. 내부 구현 메서드
    # ------------------------------------------------------------------

    def _step1_rule_based(self, query):
        """규칙 기반 키워드 매칭으로 경로를 결정한다."""
        query_lower = query.lower()

        structured_hits = sum(
            1 for kw in STRUCTURED_KEYWORDS if kw in query_lower
        )
        unstructured_hits = sum(
            1 for kw in UNSTRUCTURED_KEYWORDS if kw in query_lower
        )

        # 두 쪽 모두 히트 → hybrid (단, 한 쪽이 2배 초과 우세하면 그 쪽으로 분류)
        if structured_hits > 0 and unstructured_hits > 0:
            if structured_hits > unstructured_hits * 2:
                return "structured"
            if unstructured_hits > structured_hits * 2:
                return "unstructured"
            return "hybrid"

        if structured_hits > 0:
            return "structured"
        if unstructured_hits > 0:
            return "unstructured"
        return None

    def _step2_schema_based(self, query):
        """DB 스키마 컬럼명 매칭으로 경로를 결정한다."""
        query_lower = query.lower()
        for term in SCHEMA_TERMS:
            if term in query_lower:
                return SCHEMA_TERMS[term]
        return None

    def _step3_llm_based(self, query):
        """LLM에게 질문 분류를 위임한다."""
        prompt = f"""다음 질문을 아래 세 가지 유형 중 하나로 분류하세요.

질문: {query}

유형:
- structured: 숫자, 통계, 목록 등 데이터베이스 조회가 필요한 질문
- unstructured: 절차, 정책, 설명 등 문서 검색이 필요한 질문
- hybrid: 두 가지가 모두 필요한 복합 질문

반드시 JSON 형식으로만 답하세요:
{{"route": "structured|unstructured|hybrid", "reason": "한 줄 근거"}}"""

        try:
            response = self._llm.invoke(prompt)
            content = (
                response.content
                if hasattr(response, "content")
                else str(response)
            )
            # <think> 태그 제거 (DeepSeek-R1 등)
            content = re.sub(r"<think>.*?</think>", "", content, flags=re.DOTALL).strip()
            # JSON 추출
            json_match = re.search(r"\{.*\}", content, re.DOTALL)
            if json_match:
                parsed = json.loads(json_match.group())
                route = parsed.get("route", "unstructured")
                if route in ("structured", "unstructured", "hybrid"):
                    return route
        except Exception:
            pass
        return None
