"""ex07 휴가 잔여 조회 도구."""

import os
import logging

from langchain_core.tools import tool

logger = logging.getLogger(__name__)

_DB_ERROR_MSG = (
    "PostgreSQL에 연결할 수 없습니다. "
    "docker-compose up -d 로 DB를 시작한 후 다시 시도하십시오."
)


def _query_from_db(employee_name):
    """PostgreSQL에서 휴가 잔여 정보를 조회합니다."""
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

        # ① 직원 번호 또는 이름으로 조회
        cursor.execute(
            """
            SELECT e.emp_no, e.name, e.department,
                   l.total_days, l.used_days,
                   (l.total_days - l.used_days) AS remaining_days
            FROM employees e
            LEFT JOIN leave_balance l ON e.emp_no = l.emp_no
            WHERE e.name LIKE %s
            """,
            (f"%{employee_name}%",),
        )
        rows = [dict(row) for row in cursor.fetchall()]
        conn.close()

        if not rows:
            return f"직원 '{employee_name}'을(를) 찾을 수 없습니다."

        return {
            "employee_name": rows[0]["name"],
            "dept": rows[0]["department"],
            "total_leaves": float(rows[0]["total_days"]),
            "used_leaves": float(rows[0]["used_days"]),
            "remaining_leaves": float(rows[0]["remaining_days"]),
        }

    except Exception as exc:
        logger.warning("PostgreSQL 연결 실패: %s", exc)
        return None


@tool
def get_leave_balance(employee_name: str):
    """특정 직원의 휴가 잔여일 및 사용 내역을 조회합니다.

    직원 이름을 입력하면 해당 직원의 총 휴가 일수, 사용한 휴가 일수,
    남은 휴가 일수를 반환합니다.

    Args:
        employee_name: 조회할 직원의 이름 (예: "김민준")

    Returns:
        직원 이름, 부서, 총 휴가, 사용 휴가, 잔여 휴가가 담긴 딕셔너리.
        직원을 찾을 수 없으면 오류 메시지 문자열을 반환합니다.
    """
    logger.info("[get_leave_balance] 조회 대상: %s", employee_name)

    # DB 조회 시도
    result = _query_from_db(employee_name)
    if result is None:
        result = {"error": _DB_ERROR_MSG}

    logger.info("[get_leave_balance] 결과: %s", result)
    return result
