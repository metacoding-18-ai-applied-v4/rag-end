"""ex06 — 대표 시나리오 테스트."""

import sys
import os
import unittest

# 프로젝트 루트를 sys.path에 추가
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from src.router import QueryRouter
from src.mcp_tools import (
    leave_balance,
    sales_sum,
    list_employees,
    search_documents,
)


# ---------------------------------------------------------------------------
# 1. QueryRouter 테스트
# ---------------------------------------------------------------------------

class TestQueryRouter(unittest.TestCase):
    """QueryRouter 3단계 라우팅 전략 테스트."""

    def setUp(self):
        """LLM 없이 라우터를 초기화한다."""
        self.router = QueryRouter(llm=None)

    def test_step1_structured_keyword(self):
        """Step 1: 정형 키워드(연차)를 올바르게 분류한다."""
        result = self.router.classify_query("김민준 연차 잔여일수 알려줘")
        self.assertEqual(result, "structured")

    def test_step1_unstructured_keyword(self):
        """Step 1: 비정형 키워드(온보딩)를 올바르게 분류한다."""
        result = self.router.classify_query("온보딩 절차가 어떻게 되나요?")
        self.assertEqual(result, "unstructured")

    def test_step1_hybrid_keyword(self):
        """Step 1: 정형 + 비정형 키워드가 모두 있으면 hybrid로 분류한다."""
        result = self.router.classify_query("매출 합계와 출장 규정 모두 알려줘")
        self.assertEqual(result, "hybrid")

    def test_step1_sales_keyword(self):
        """Step 1: 매출 키워드를 정형으로 분류한다."""
        result = self.router.classify_query("영업부 11월 매출 합계가 얼마야?")
        self.assertEqual(result, "structured")

    def test_step1_security_keyword(self):
        """Step 1: 보안 정책 키워드를 비정형으로 분류한다."""
        result = self.router.classify_query("보안 정책에 대해 설명해줘")
        self.assertEqual(result, "unstructured")

    def test_step2_schema_term(self):
        """Step 2: DB 컬럼명(remaining_days)을 정형으로 분류한다."""
        result = self.router.classify_query("remaining_days가 0인 직원은?")
        self.assertEqual(result, "structured")

    def test_explain_routing_format(self):
        """explain_routing 반환 형식이 올바른지 확인한다."""
        result = self.router.explain_routing("연차 잔여일수 조회")
        self.assertIn("query", result)
        self.assertIn("step1", result)
        self.assertIn("step2", result)
        self.assertIn("route", result)
        self.assertIn(result["route"], ("structured", "unstructured", "hybrid"))

    def test_default_unstructured(self):
        """키워드 없는 질문은 기본값 unstructured로 분류된다."""
        result = self.router.classify_query("안녕하세요")
        self.assertEqual(result, "unstructured")


# ---------------------------------------------------------------------------
# 2. 정형 시나리오 테스트 (DB 조회)
# ---------------------------------------------------------------------------

class TestStructuredScenarios(unittest.TestCase):
    """정형 데이터 MCP 도구 테스트 (PostgreSQL 연결 필요)."""

    def test_scenario_01_leave_balance_by_name(self):
        """시나리오 01: 이름으로 연차 잔여일수를 조회한다."""
        result = leave_balance.invoke({"emp_no": "김민준"})
        self.assertIsInstance(result, dict)
        self.assertIn("remaining_days", result)
        self.assertGreaterEqual(result["remaining_days"], 0)

    def test_scenario_02_sales_sum_dept(self):
        """시나리오 02: 영업부 매출 합계를 조회한다."""
        result = sales_sum.invoke({"dept": "영업부", "start_date": "", "end_date": ""})
        self.assertIsInstance(result, dict)
        self.assertIn("total_amount", result)
        self.assertGreater(result["total_amount"], 0)

    def test_scenario_03_list_employees_by_dept(self):
        """시나리오 03: 개발부 직원 목록을 조회한다."""
        result = list_employees.invoke({"dept": "개발부"})
        self.assertIsInstance(result, dict)
        self.assertIn("employees", result)
        self.assertGreater(result["count"], 0)
        for emp in result["employees"]:
            self.assertIn("개발부", emp["department"])

    def test_scenario_04_dept_stats(self):
        """시나리오 04: 전체 직원 목록과 부서별 통계를 확인한다."""
        result = list_employees.invoke({"dept": ""})
        self.assertIsInstance(result, dict)
        self.assertGreaterEqual(result["count"], 5)
        depts = {emp["department"] for emp in result["employees"]}
        self.assertGreaterEqual(len(depts), 3)  # 최소 3개 부서


# ---------------------------------------------------------------------------
# 3. 비정형 시나리오 테스트 (문서 검색)
# ---------------------------------------------------------------------------

class TestUnstructuredScenarios(unittest.TestCase):
    """비정형 문서 검색 MCP 도구 테스트."""

    def test_scenario_05_onboarding_procedure(self):
        """시나리오 05: 온보딩 절차 문서를 검색한다."""
        result = search_documents.invoke({"query": "온보딩 절차 신규 입사", "k": 3})
        self.assertIsInstance(result, dict)
        self.assertIn("results", result)
        self.assertGreater(len(result["results"]), 0)
        first = result["results"][0]
        self.assertIn("content", first)
        self.assertIn("source", first)

    def test_scenario_06_security_policy(self):
        """시나리오 06: 보안 정책 문서를 검색한다."""
        result = search_documents.invoke({"query": "보안 VPN 정책", "k": 3})
        self.assertIsInstance(result, dict)
        results = result.get("results", [])
        self.assertGreater(len(results), 0)
        # 보안 관련 내용이 포함되어야 함
        contents = " ".join(r["content"] for r in results)
        self.assertTrue("보안" in contents or "VPN" in contents)

    def test_scenario_07_workcation_info(self):
        """시나리오 07: 워케이션 제도 문서를 검색한다."""
        result = search_documents.invoke({"query": "워케이션 숙박 지원", "k": 3})
        self.assertIsInstance(result, dict)
        results = result.get("results", [])
        self.assertGreater(len(results), 0)

    def test_scenario_08_launch_strategy(self):
        """시나리오 08: 신규 서비스 런칭 전략 문서를 검색한다."""
        result = search_documents.invoke({"query": "런칭 전략 예산 로드맵", "k": 3})
        self.assertIsInstance(result, dict)
        results = result.get("results", [])
        self.assertGreater(len(results), 0)
        contents = " ".join(r["content"] for r in results)
        self.assertTrue("런칭" in contents or "전략" in contents or "예산" in contents)


# ---------------------------------------------------------------------------
# 4. 복합 시나리오 테스트 (정형 + 비정형 도구 동시 사용)
# ---------------------------------------------------------------------------

class TestHybridScenarios(unittest.TestCase):
    """복합 질문: 정형 DB 조회와 비정형 문서 검색을 병합하는 테스트."""

    def test_scenario_09_sales_dept_workcation(self):
        """시나리오 09: 매출 상위 부서 조회 + 워케이션 정책 검색을 병렬 실행한다."""
        # 정형: 전체 매출 집계
        sales_result = sales_sum.invoke({"dept": "", "start_date": "", "end_date": ""})
        self.assertIn("total_amount", sales_result)
        self.assertIn("top5", sales_result)

        # 비정형: 워케이션 정책 검색
        doc_result = search_documents.invoke({"query": "워케이션 병가 규정", "k": 3})
        self.assertIn("results", doc_result)

        # 두 결과를 합쳐 통합 응답을 구성할 수 있어야 함
        combined = {
            "sales": sales_result,
            "policy_docs": doc_result["results"],
        }
        self.assertIn("sales", combined)
        self.assertIn("policy_docs", combined)
        self.assertGreater(len(combined["policy_docs"]), 0)

    def test_scenario_10_employee_leave_policy(self):
        """시나리오 10: 직원 연차 현황 조회 + 연차 사용 규정 검색을 병렬 실행한다."""
        # 정형: 직원 연차 조회
        leave_result = leave_balance.invoke({"emp_no": "정시우"})
        self.assertIn("remaining_days", leave_result)

        # 비정형: 연차 규정 문서 검색
        doc_result = search_documents.invoke({"query": "연차 사용 규정 신청", "k": 3})
        self.assertIn("results", doc_result)

        # 복합 응답 구성 검증
        combined = {
            "employee": leave_result,
            "policy_docs": doc_result["results"],
        }
        self.assertEqual(combined["employee"]["name"], "정시우")
        self.assertGreater(len(combined["policy_docs"]), 0)


# ---------------------------------------------------------------------------
# 5. 추가 단위 테스트
# ---------------------------------------------------------------------------

class TestMcpToolsUnit(unittest.TestCase):
    """MCP 도구 단위 테스트."""

    def test_leave_balance_by_emp_no(self):
        """사원 번호로 연차 조회가 동작한다."""
        result = leave_balance.invoke({"emp_no": "E001"})
        self.assertIn("emp_no", result)
        self.assertEqual(result["emp_no"], "E001")

    def test_leave_balance_not_found(self):
        """존재하지 않는 직원 조회 시 error 키를 반환한다."""
        result = leave_balance.invoke({"emp_no": "존재안함"})
        self.assertIn("error", result)

    def test_sales_sum_total(self):
        """전체 매출 합계가 0보다 크다."""
        result = sales_sum.invoke({"dept": "", "start_date": "", "end_date": ""})
        self.assertGreater(result["total_amount"], 0)

    def test_search_documents_keyword_match(self):
        """문서 검색이 키워드 기반으로 결과를 반환한다."""
        result = search_documents.invoke({"query": "온보딩 입사", "k": 3})
        self.assertIsInstance(result, dict)
        self.assertIn("results", result)
        if result["results"]:
            self.assertIn("content", result["results"][0])
            self.assertIn("source", result["results"][0])

    def test_list_employees_all(self):
        """전체 직원 목록 조회가 5명 이상을 반환한다."""
        result = list_employees.invoke({"dept": ""})
        self.assertGreaterEqual(result["count"], 5)


# ---------------------------------------------------------------------------
# 6. 실행 진입점
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    suite.addTests(loader.loadTestsFromTestCase(TestQueryRouter))
    suite.addTests(loader.loadTestsFromTestCase(TestStructuredScenarios))
    suite.addTests(loader.loadTestsFromTestCase(TestUnstructuredScenarios))
    suite.addTests(loader.loadTestsFromTestCase(TestHybridScenarios))
    suite.addTests(loader.loadTestsFromTestCase(TestMcpToolsUnit))

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    sys.exit(0 if result.wasSuccessful() else 1)
