"""데이터베이스 연결 모듈."""

import os

# ---------------------------------------------------------------------------
# 1. 연결 설정
# ---------------------------------------------------------------------------

POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5432")
POSTGRES_DB = os.getenv("POSTGRES_DB", "rag_db")
POSTGRES_USER = os.getenv("POSTGRES_USER", "rag_user")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "rag_password")

DATABASE_URL = (
    f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}"
    f"@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"
)


# ---------------------------------------------------------------------------
# 2. 연결 래퍼 클래스
# ---------------------------------------------------------------------------

class _DbConnectionWrapper:
    """psycopg2 연결 객체를 DictCursor와 함께 래핑한다."""

    def __init__(self, conn):
        """연결 객체를 초기화한다."""
        self._conn = conn

    def execute(self, sql, params=()):
        """SQL을 실행하고 딕셔너리 리스트를 반환한다."""
        import psycopg2.extras
        cur = self._conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute(sql, params)
        rows = [dict(row) for row in cur.fetchall()]
        cur.close()
        return rows

    def close(self):
        """연결을 종료한다."""
        self._conn.close()


# ---------------------------------------------------------------------------
# 3. 연결 함수
# ---------------------------------------------------------------------------

def get_db_connection():
    """PostgreSQL 연결을 반환한다. 실패 시 SystemExit을 발생시킨다."""
    try:
        import psycopg2
        conn = psycopg2.connect(DATABASE_URL, connect_timeout=5)
        return _DbConnectionWrapper(conn)
    except Exception as e:
        raise SystemExit(f"PostgreSQL 연결 실패: {e}\n.env 파일의 POSTGRES_* 설정을 확인하세요.") from e


def get_db_connection_safe():
    """PostgreSQL 연결을 시도하고 실패 시 None을 반환한다."""
    try:
        import psycopg2
        conn = psycopg2.connect(DATABASE_URL, connect_timeout=3)  # ①
        return _DbConnectionWrapper(conn)
    except Exception:
        return None  # ② 연결 실패 → 인메모리 모드
