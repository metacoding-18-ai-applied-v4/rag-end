"""ex06 — MCP 도구 모듈."""

# LangChain 도구 데코레이터
from langchain_core.tools import tool

from src.db_helper import run_query, DB_ERROR_MSG, get_vectorstore, parse_and_chunk_docs


# ---------------------------------------------------------------------------
# MCP 도구 정의
# ---------------------------------------------------------------------------

@tool
def leave_balance(emp_no: str) -> dict:
    """직원의 연차 잔여 일수를 조회한다."""
    # TODO: emp_no가 "E"로 시작하는 사번이면 emp_no로 조회, 아니면 이름으로 LIKE 조회한다
    # ① DB 조회 시도 (이름 또는 번호)
    if emp_no.startswith("E") and emp_no[1:].isdigit():
        rows = run_query(
            """
            SELECT e.emp_no, e.name, e.department,
                   l.total_days, l.used_days,
                   (l.total_days - l.used_days) AS remaining_days
            FROM employees e
            LEFT JOIN leave_balance l ON e.emp_no = l.emp_no
            WHERE e.emp_no = %s
            """,
            (emp_no,),
        )
    else:
        rows = run_query(
            """
            SELECT e.emp_no, e.name, e.department,
                   l.total_days, l.used_days,
                   (l.total_days - l.used_days) AS remaining_days
            FROM employees e
            LEFT JOIN leave_balance l ON e.emp_no = l.emp_no
            WHERE e.name LIKE %s
            """,
            (f"%{emp_no}%",),
        )

    # TODO: DB 결과가 있으면 첫 번째 행을 반환한다
    # ② DB 결과가 있으면 반환
    if rows:
        return rows[0]

    # TODO: 결과가 없으면 에러 딕셔너리를 반환한다
    # ③ DB 연결 실패 시 에러 반환
    return {"error": f"직원 '{emp_no}'을(를) 찾을 수 없습니다. {DB_ERROR_MSG}"}


@tool
def sales_sum(dept: str = "", start_date: str = "", end_date: str = "") -> dict:
    """부서별 또는 전체 매출 합계를 조회한다."""
    # TODO: 파라미터 기본값 처리 (start_date 기본 "2024-11-01", end_date 기본 "2024-12-31")
    # ① 파라미터 기본값 처리
    start = start_date or "2024-11-01"  # ①
    end = end_date or "2024-12-31"

    # TODO: dept가 있으면 부서 필터를 SQL에 추가한다
    # ② DB 조회 시도
    dept_filter = f"AND e.department LIKE '%{dept}%'" if dept else ""
    rows = run_query(
        f"""
        SELECT e.department, e.name AS employee_name,
               SUM(s.amount) AS total_amount, COUNT(*) AS record_count
        FROM sales s
        JOIN employees e ON s.emp_no = e.emp_no
        WHERE s.sale_date BETWEEN %s AND %s {dept_filter}
        GROUP BY e.department, e.name
        ORDER BY total_amount DESC
        """,
        (start, end),
    )

    # TODO: DB 조회 후 결과가 있으면 grand_total, record_count, top5 등으로 가공하여 반환한다
    # ③ DB 결과 가공
    if rows:
        grand_total = sum(int(r.get("total_amount") or 0) for r in rows)
        return {
            "total_amount": grand_total,
            "record_count": len(rows),
            "dept_filter": dept or "전체",
            "period": f"{start} ~ {end}",
            "top5": rows[:5],
        }

    # TODO: 결과가 없으면 에러 딕셔너리를 반환한다
    # ④ DB 연결 실패 시 에러 반환
    return {"error": DB_ERROR_MSG, "dept_filter": dept or "전체", "period": f"{start} ~ {end}"}


@tool
def list_employees(dept: str = "", name: str = "") -> dict:
    """직원의 기초 정보(부서, 직급, 입사일 등) 범용 목록을 조회한다.
    특정 직원의 입사일이나 기본 정보가 궁금할 때에는 name(이름)에 직원이름을 넣어 검색한다."""
    # TODO: dept, name 조건이 있으면 WHERE절에 LIKE 조건을 추가한다
    # ① DB 조회 시도
    conditions = []
    params = []
    sql_base = "SELECT emp_no, name, department, position, hire_date FROM employees "
    
    if dept:
        conditions.append("department LIKE %s")
        params.append(f"%{dept}%")
    if name:
        conditions.append("name LIKE %s")
        params.append(f"%{name}%")
        
    if conditions:
        sql = sql_base + " WHERE " + " AND ".join(conditions) + " ORDER BY name"
    else:
        sql = sql_base + " ORDER BY department, name"

    rows = run_query(sql, tuple(params))

    # TODO: DB 조회 후 결과가 있으면 employees 리스트와 count를 반환한다
    # ② DB 결과 반환
    if rows:
        return {"employees": rows, "count": len(rows), "filter": {"dept": dept, "name": name}}

    # TODO: 결과가 없으면 에러 딕셔너리를 반환한다
    # ③ DB 연결 실패 시 에러 반환
    return {"error": DB_ERROR_MSG, "employees": [], "count": 0, "dept_filter": dept or "전체"}


@tool
def search_documents(query: str, k: int = 3) -> dict:
    """사내 문서에서 관련 내용을 벡터 검색한다."""
    # TODO: get_vectorstore()로 컬렉션을 가져온다
    collection = get_vectorstore()
    if collection is not None:
        try:
            # TODO: collection.query()로 벡터 검색을 수행한다
            results = collection.query(query_texts=[query], n_results=k)

            # TODO: 결과를 content, source, score 형태로 가공하여 반환한다
            docs = []
            for i, doc in enumerate(results["documents"][0]):
                docs.append({
                    "content": doc,
                    "source": results["metadatas"][0][i].get("source", "unknown"),
                    "score": round(1 - results["distances"][0][i], 4),
                })
            return {"results": docs, "total_found": len(docs)}
        except Exception:
            pass

    # TODO: 실패 시 빈 결과를 반환한다
    return {"results": [], "total_found": 0}


# ---------------------------------------------------------------------------
# 도구 목록 (에이전트에 전달)
# ---------------------------------------------------------------------------

ALL_TOOLS = [leave_balance, sales_sum, list_employees, search_documents]
