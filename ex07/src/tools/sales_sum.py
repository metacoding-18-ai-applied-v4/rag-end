"""ex07 매출 합계 조회 도구."""

import os
import logging

from langchain_core.tools import tool

logger = logging.getLogger(__name__)

_DB_ERROR_MSG = (
    "PostgreSQL에 연결할 수 없습니다. "
    "docker-compose up -d 로 DB를 시작한 후 다시 시도하십시오."
)


def _query_from_db(dept=None):
    """PostgreSQL에서 매출 합계를 조회합니다."""
    try:
        import psycopg2
        import psycopg2.extras

        db_url = os.getenv("DATABASE_URL", "")
        if not db_url:
            host = os.getenv("POSTGRES_HOST", "localhost")
            port = os.getenv("POSTGRES_PORT", "5432")
            db = os.getenv("POSTGRES_DB", "rag_db")
            user = os.getenv("POSTGRES_USER", "rag_user")
            password = os.getenv("POSTGRES_PASSWORD", "")
            db_url = f"postgresql://{user}:{password}@{host}:{port}/{db}"

        conn = psycopg2.connect(db_url, connect_timeout=3)
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

        if dept:
            # ① 부서별 매출 합계
            cursor.execute(
                """
                SELECT e.department, SUM(s.amount) AS total_amount, COUNT(*) AS count
                FROM sales s
                JOIN employees e ON s.emp_no = e.emp_no
                WHERE e.department LIKE %s
                GROUP BY e.department
                """,
                (f"%{dept}%",),
            )
            row = cursor.fetchone()
            cursor.execute(
                """
                SELECT s.*, e.name AS employee_name, e.department
                FROM sales s
                JOIN employees e ON s.emp_no = e.emp_no
                WHERE e.department LIKE %s
                ORDER BY s.sale_date DESC LIMIT 5
                """,
                (f"%{dept}%",),
            )
            recent_records = [dict(r) for r in cursor.fetchall()]
        else:
            # ② 전체 매출 합계
            cursor.execute(
                "SELECT SUM(amount) AS total_amount, COUNT(*) AS count FROM sales"
            )
            row = cursor.fetchone()
            cursor.execute(
                """
                SELECT s.*, e.name AS employee_name, e.department
                FROM sales s
                JOIN employees e ON s.emp_no = e.emp_no
                ORDER BY s.sale_date DESC LIMIT 5
                """
            )
            recent_records = [dict(r) for r in cursor.fetchall()]

        conn.close()

        if not row or row["total_amount"] is None:
            return {"dept": dept or "전체", "total_amount": 0, "count": 0, "recent_records": []}

        return {
            "dept": dept or "전체",
            "total_amount": int(row["total_amount"]),
            "count": int(row["count"]),
            "recent_records": recent_records,
        }

    except Exception as exc:
        logger.warning("PostgreSQL 연결 실패: %s", exc)
        return None


@tool
def get_sales_sum(dept=None):
    """부서별 또는 전체 매출 합계와 실적 정보를 조회합니다.

    부서명을 지정하면 해당 부서의 매출 합계를, 지정하지 않으면
    전체 부서의 합산 매출을 반환합니다.

    Args:
        dept: 조회할 부서명 (예: "영업부"). None이면 전체 매출 합계를 반환합니다.

    Returns:
        부서, 총 매출액, 거래 건수, 최근 거래 내역이 담긴 딕셔너리.
        DB 연결 실패 시 오류 딕셔너리를 반환합니다.
    """
    logger.info("[get_sales_sum] 조회 대상 부서: %s", dept or "전체")

    # DB 조회 시도
    result = _query_from_db(dept)
    if result is None:
        result = {"error": _DB_ERROR_MSG, "dept": dept or "전체"}

    logger.info("[get_sales_sum] 결과: %s", result)
    return result
