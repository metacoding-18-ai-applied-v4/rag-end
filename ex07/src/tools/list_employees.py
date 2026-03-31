"""ex07 직원 목록 조회 도구."""

import os
import logging

from langchain_core.tools import tool

logger = logging.getLogger(__name__)

_DB_ERROR_MSG = (
    "PostgreSQL에 연결할 수 없습니다. "
    "docker-compose up -d 로 DB를 시작한 후 다시 시도하십시오."
)


def _query_from_db(dept=None, name=None):
    """PostgreSQL에서 직원 목록을 조회합니다."""
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

        cursor.execute(sql, tuple(params))

        rows = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return rows

    except Exception as exc:
        logger.warning("PostgreSQL 연결 실패: %s", exc)
        return None


@tool
def list_employees(dept=None, name=None):
    """직원의 기초 정보(부서, 직급, 입사일 등) 범용 목록을 조회합니다.
    특정 직원의 입사일이나 기본 정보가 궁금할 때에는 name(이름)에 직원이름을 넣어 검색합니다.

    Args:
        dept: 조회할 부서명 (예: "영업부", "인사부"). None이면 부서 필터 없음.
        name: 조회할 직원 이름 (예: "홍길동"). None이면 이름 필터 없음.

    Returns:
        직원 정보 딕셔너리 목록. DB 연결 실패 시 오류 딕셔너리를 반환합니다.
    """
    logger.info("[list_employees] 조회 대상 부서: %s, 이름: %s", dept or "전체", name or "전체")

    # DB 조회 시도
    result = _query_from_db(dept, name)
    if result is None:
        return {"error": _DB_ERROR_MSG, "employees": [], "count": 0}

    count = len(result)
    logger.info("[list_employees] 조회된 직원 수: %d", count)
    return result
