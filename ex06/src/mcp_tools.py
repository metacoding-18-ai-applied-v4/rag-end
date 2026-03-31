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

    # ② DB 결과가 있으면 반환
    if rows:
        return rows[0]

    # ③ DB 연결 실패 시 에러 반환
    return {"error": f"직원 '{emp_no}'을(를) 찾을 수 없습니다. {DB_ERROR_MSG}"}


@tool
def sales_sum(dept: str = "", start_date: str = "", end_date: str = "") -> dict:
    """부서별 또는 전체 매출 합계를 조회한다."""
    # ① 파라미터 기본값 처리
    start = start_date or "2024-11-01"  # ①
    end = end_date or "2024-12-31"

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

    # ④ DB 연결 실패 시 에러 반환
    return {"error": DB_ERROR_MSG, "dept_filter": dept or "전체", "period": f"{start} ~ {end}"}


@tool
def list_employees(dept: str = "", name: str = "") -> dict:
    """직원의 기초 정보(부서, 직급, 입사일 등) 범용 목록을 조회한다. 
    특정 직원의 입사일이나 기본 정보가 궁금할 때에는 name(이름)에 직원이름을 넣어 검색한다."""
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

    # ② DB 결과 반환
    if rows:
        return {"employees": rows, "count": len(rows), "filter": {"dept": dept, "name": name}}

    # ③ DB 연결 실패 시 에러 반환
    return {"error": DB_ERROR_MSG, "employees": [], "count": 0, "dept_filter": dept or "전체"}


@tool
def search_documents(query: str, k: int = 3) -> dict:
    """사내 문서에서 관련 내용을 벡터 검색한다."""
    collection = get_vectorstore()
    if collection is not None:
        try:
            results = collection.query(query_texts=[query], n_results=k)

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

    return {"results": [], "total_found": 0}


# ---------------------------------------------------------------------------
# 도구 목록 (에이전트에 전달)
# ---------------------------------------------------------------------------

ALL_TOOLS = [leave_balance, sales_sum, list_employees, search_documents]
