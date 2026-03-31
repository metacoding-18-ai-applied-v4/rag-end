"""
데이터베이스 연결 모듈.

psycopg2를 사용하여 PostgreSQL에 연결하고,
연결 풀(connection context)을 제공합니다.
"""

import os
import sys
from contextlib import contextmanager
from typing import Generator

import psycopg2
import psycopg2.extras
from dotenv import load_dotenv

# ------------------------------------------------------------------
# [INPUT] 환경 변수 로드
# ------------------------------------------------------------------
load_dotenv()

POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
POSTGRES_PORT = int(os.getenv("POSTGRES_PORT", "5432"))
POSTGRES_DB   = os.getenv("POSTGRES_DB",   "metacoding_db")
POSTGRES_USER = os.getenv("POSTGRES_USER", "metacoding")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "metacoding_pass")


def get_dsn() -> str:
    """PostgreSQL DSN(Data Source Name) 문자열을 반환합니다.

    Returns:
        psycopg2가 사용할 DSN 문자열
    """
    return (
        f"host={POSTGRES_HOST} port={POSTGRES_PORT} "
        f"dbname={POSTGRES_DB} user={POSTGRES_USER} "
        f"password={POSTGRES_PASSWORD}"
    )


# ------------------------------------------------------------------
# [PROCESS] 연결 컨텍스트 매니저
# ------------------------------------------------------------------
@contextmanager
def get_connection() -> Generator[psycopg2.extensions.connection, None, None]:
    """PostgreSQL 연결을 컨텍스트 매니저로 제공합니다.

    사용 예시:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1")

    Yields:
        psycopg2 연결 객체

    Raises:
        SystemExit: PostgreSQL 서버에 연결할 수 없을 때
    """
    conn = None
    try:
        conn = psycopg2.connect(                            # ①
            get_dsn(),
            cursor_factory=psycopg2.extras.RealDictCursor  # ② 결과를 dict로 반환
        )
        yield conn                                          # ③
        conn.commit()                                       # ④
    except psycopg2.OperationalError as exc:
        if conn:
            conn.rollback()
        print(
            "PostgreSQL 서버에 연결할 수 없습니다.\n"
            f"  호스트: {POSTGRES_HOST}:{POSTGRES_PORT}\n"
            "  'docker-compose up -d' 명령으로 DB를 먼저 실행하십시오."
        )
        raise RuntimeError("DB 연결 실패") from exc
    except Exception as exc:
        if conn:
            conn.rollback()
        raise exc
    finally:
        if conn:
            conn.close()                                    # ⑤


def verify_connection() -> bool:
    """DB 연결 상태를 확인합니다.

    Returns:
        연결 성공 시 True, 실패 시 False
    """
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1")
        return True
    except Exception:
        return False
