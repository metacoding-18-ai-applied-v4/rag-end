"""
CRUD 함수 모듈.

직원(employee), 연차(leave_balance), 매출(sales) 테이블에 대한
Create / Read / Update / Delete 함수를 제공합니다.
모든 함수는 psycopg2 연결을 인자로 받아 트랜잭션을 공유합니다.
"""

from datetime import date
from typing import Optional

import psycopg2.extensions

from app.models import DeptSummary, Employee, LeaveBalance, Sale


# ============================================================
# 직원 CRUD
# ============================================================

def _generate_emp_no(conn: psycopg2.extensions.connection) -> str:
    """다음 사번을 자동 생성합니다 (EMP001, EMP002, ...).

    Args:
        conn: psycopg2 연결 객체

    Returns:
        새 사번 문자열 (예: "EMP006")
    """
    sql = "SELECT emp_no FROM employee ORDER BY id DESC LIMIT 1"
    with conn.cursor() as cur:
        cur.execute(sql)
        row = cur.fetchone()

    if row is None:
        return "EMP001"

    last_no = int(row["emp_no"].replace("EMP", ""))       # ① "EMP005" → 5
    return f"EMP{last_no + 1:03d}"                         # ② → "EMP006"


def create_employee(
    conn: psycopg2.extensions.connection,
    name: str,
    dept: str,
    position: str,
    hire_date: date,
) -> Employee:
    """직원을 데이터베이스에 등록합니다 (사번은 자동 생성).

    Args:
        conn:      psycopg2 연결 객체
        name:      직원 이름
        dept:      소속 부서
        position:  직급
        hire_date: 입사일

    Returns:
        등록된 Employee 객체
    """
    # [PROCESS] 사번 자동 생성 → INSERT
    emp_no = _generate_emp_no(conn)                                   # ①
    sql = """
        INSERT INTO employee (emp_no, name, dept, position, hire_date)
        VALUES (%s, %s, %s, %s, %s)
        RETURNING id, emp_no, name, dept, position, hire_date
    """
    with conn.cursor() as cur:
        cur.execute(sql, (emp_no, name, dept, position, hire_date))   # ②
        row = cur.fetchone()                                          # ③
    return _row_to_employee(row)


def get_all_employees(
    conn: psycopg2.extensions.connection,
    name_filter: Optional[str] = None,
    dept_filter: Optional[str] = None,
) -> list[Employee]:
    """직원 전체 목록을 조회합니다 (이름/부서 필터 지원).

    Args:
        conn:        psycopg2 연결 객체
        name_filter: 이름 부분 검색 (None이면 전체)
        dept_filter: 부서 부분 검색 (None이면 전체)

    Returns:
        Employee 객체 리스트 (id 오름차순)
    """
    # [PROCESS] 동적 WHERE 조건 구성
    conditions: list[str] = []
    params: list[str] = []

    if name_filter:
        conditions.append("name ILIKE %s")          # ① 대소문자 무시 검색
        params.append(f"%{name_filter}%")
    if dept_filter:
        conditions.append("dept ILIKE %s")          # ②
        params.append(f"%{dept_filter}%")

    where_clause = ("WHERE " + " AND ".join(conditions)) if conditions else ""
    sql = f"SELECT id, emp_no, name, dept, position, hire_date FROM employee {where_clause} ORDER BY id"

    with conn.cursor() as cur:
        cur.execute(sql, params)                    # ③
        rows = cur.fetchall()                       # ④

    return [_row_to_employee(r) for r in rows]


def get_employee_by_emp_no(
    conn: psycopg2.extensions.connection,
    emp_no: str,
) -> Optional[Employee]:
    """사번으로 직원 정보를 조회합니다.

    Args:
        conn:   psycopg2 연결 객체
        emp_no: 사번 (예: "EMP001")

    Returns:
        Employee 객체 또는 None
    """
    sql = "SELECT id, emp_no, name, dept, position, hire_date FROM employee WHERE emp_no = %s"
    with conn.cursor() as cur:
        cur.execute(sql, (emp_no,))
        row = cur.fetchone()
    return _row_to_employee(row) if row else None


def update_employee(
    conn: psycopg2.extensions.connection,
    emp_no: str,
    name: Optional[str] = None,
    dept: Optional[str] = None,
    position: Optional[str] = None,
    hire_date: Optional[date] = None,
) -> Optional[Employee]:
    """직원 정보를 부분 수정합니다 (입력된 필드만 변경).

    Args:
        conn:      psycopg2 연결 객체
        emp_no:    대상 직원 사번
        name:      수정할 이름 (None이면 유지)
        dept:      수정할 부서 (None이면 유지)
        position:  수정할 직급 (None이면 유지)
        hire_date: 수정할 입사일 (None이면 유지)

    Returns:
        수정된 Employee 객체 또는 None (해당 사번 없음)
    """
    # [PROCESS] 변경할 컬럼만 SET 절에 포함
    set_parts: list[str] = []
    params: list = []

    if name is not None:
        set_parts.append("name = %s")       # ①
        params.append(name)
    if dept is not None:
        set_parts.append("dept = %s")
        params.append(dept)
    if position is not None:
        set_parts.append("position = %s")
        params.append(position)
    if hire_date is not None:
        set_parts.append("hire_date = %s")
        params.append(hire_date)

    if not set_parts:
        return get_employee_by_emp_no(conn, emp_no)

    params.append(emp_no)
    sql = f"""
        UPDATE employee SET {', '.join(set_parts)}
        WHERE emp_no = %s
        RETURNING id, emp_no, name, dept, position, hire_date
    """
    with conn.cursor() as cur:
        cur.execute(sql, params)            # ②
        row = cur.fetchone()               # ③
    return _row_to_employee(row) if row else None


def delete_employee(
    conn: psycopg2.extensions.connection,
    emp_no: str,
) -> bool:
    """직원을 삭제합니다.

    Args:
        conn:   psycopg2 연결 객체
        emp_no: 삭제할 직원 사번

    Returns:
        삭제 성공 시 True, 해당 사번 없으면 False
    """
    sql = "DELETE FROM employee WHERE emp_no = %s"
    with conn.cursor() as cur:
        cur.execute(sql, (emp_no,))
        return cur.rowcount > 0             # ① 삭제된 행 수로 성공 여부 판단


def _row_to_employee(row: dict) -> Employee:
    """DB 결과 딕셔너리를 Employee 객체로 변환합니다.

    Args:
        row: RealDictCursor 반환 딕셔너리

    Returns:
        Employee 객체
    """
    return Employee(
        id=row["id"],
        emp_no=row["emp_no"],
        name=row["name"],
        dept=row["dept"],
        position=row["position"],
        hire_date=row["hire_date"],
    )


# ============================================================
# 연차 CRUD
# ============================================================

def create_leave_balance(
    conn: psycopg2.extensions.connection,
    employee_id: int,
    year: int,
    total_days: float,
    used_days: float = 0.0,
) -> LeaveBalance:
    """연차 잔여량 레코드를 생성합니다.

    Args:
        conn:        psycopg2 연결 객체
        employee_id: 직원 ID
        year:        연도
        total_days:  총 연차 일수
        used_days:   사용 연차 일수 (기본 0)

    Returns:
        생성된 LeaveBalance 객체

    Raises:
        psycopg2.errors.UniqueViolation: 동일 직원/연도가 이미 존재할 때
    """
    sql = """
        INSERT INTO leave_balance (employee_id, year, total_days, used_days)
        VALUES (%s, %s, %s, %s)
        RETURNING id, employee_id, year, total_days, used_days, remaining_days
    """
    with conn.cursor() as cur:
        cur.execute(sql, (employee_id, year, total_days, used_days))
        row = cur.fetchone()
    return _row_to_leave(row)


def get_all_leaves(
    conn: psycopg2.extensions.connection,
    employee_name_filter: Optional[str] = None,
) -> list[LeaveBalance]:
    """연차 잔여량 전체 목록을 조회합니다 (직원 이름·사번 조인 포함).

    Args:
        conn:                 psycopg2 연결 객체
        employee_name_filter: 직원 이름 부분 검색 (None이면 전체)

    Returns:
        LeaveBalance 객체 리스트
    """
    # [PROCESS] employee 테이블과 JOIN하여 이름·사번 포함 조회
    base_sql = """
        SELECT lb.id, lb.employee_id, lb.year,
               lb.total_days, lb.used_days, lb.remaining_days,
               e.name, e.emp_no
        FROM leave_balance lb
        JOIN employee e ON lb.employee_id = e.id
    """
    params: list = []
    where_clause = ""

    if employee_name_filter:
        where_clause = "WHERE e.name ILIKE %s"          # ①
        params.append(f"%{employee_name_filter}%")

    sql = f"{base_sql} {where_clause} ORDER BY lb.id"

    with conn.cursor() as cur:
        cur.execute(sql, params)                         # ②
        rows = cur.fetchall()                            # ③

    return [_row_to_leave(r) for r in rows]


def update_leave_usage(
    conn: psycopg2.extensions.connection,
    emp_no: str,
    days: float,
    year: int = 2025,
) -> Optional[LeaveBalance]:
    """사용 연차를 추가합니다 (누적 방식).

    Args:
        conn:   psycopg2 연결 객체
        emp_no: 직원 사번
        days:   추가로 사용할 일수
        year:   대상 연도 (기본 2025)

    Returns:
        갱신된 LeaveBalance 객체 또는 None (레코드 없음)

    Raises:
        ValueError: 잔여 연차 부족 시
    """
    # [PROCESS] 사번 → employee_id 서브쿼리로 연차 갱신
    emp_subquery = "(SELECT id FROM employee WHERE emp_no = %s)"
    check_sql = f"""
        SELECT remaining_days FROM leave_balance
        WHERE employee_id = {emp_subquery} AND year = %s
    """
    update_sql = f"""
        UPDATE leave_balance
        SET used_days = used_days + %s
        WHERE employee_id = {emp_subquery} AND year = %s
        RETURNING id, employee_id, year, total_days, used_days, remaining_days
    """
    with conn.cursor() as cur:
        cur.execute(check_sql, (emp_no, year))          # ① 잔여 확인
        check_row = cur.fetchone()

        if check_row is None:
            return None

        if check_row["remaining_days"] < days:           # ② 잔여 부족 검사
            raise ValueError(
                f"잔여 연차({check_row['remaining_days']}일)가 부족합니다. "
                f"요청 일수: {days}일"
            )

        cur.execute(update_sql, (days, emp_no, year))    # ③ 사용 일수 누적
        row = cur.fetchone()

    return _row_to_leave(row) if row else None


def update_leave_balance(
    conn: psycopg2.extensions.connection,
    emp_no: str,
    year: int,
    total_days: Optional[float] = None,
    used_days: Optional[float] = None,
) -> Optional[LeaveBalance]:
    """연차 잔여량을 직접 수정합니다.

    Args:
        conn:       psycopg2 연결 객체
        emp_no:     직원 사번
        year:       대상 연도
        total_days: 수정할 총 연차 일수
        used_days:  수정할 사용 연차 일수

    Returns:
        갱신된 LeaveBalance 객체 또는 None
    """
    set_parts: list[str] = []
    params: list = []

    if total_days is not None:
        set_parts.append("total_days = %s")
        params.append(total_days)
    if used_days is not None:
        set_parts.append("used_days = %s")
        params.append(used_days)

    if not set_parts:
        return None

    emp_subquery = "(SELECT id FROM employee WHERE emp_no = %s)"
    params.extend([emp_no, year])
    sql = f"""
        UPDATE leave_balance SET {', '.join(set_parts)}
        WHERE employee_id = {emp_subquery} AND year = %s
        RETURNING id, employee_id, year, total_days, used_days, remaining_days
    """
    with conn.cursor() as cur:
        cur.execute(sql, params)
        row = cur.fetchone()
    return _row_to_leave(row) if row else None


def _row_to_leave(row: dict) -> LeaveBalance:
    """DB 결과 딕셔너리를 LeaveBalance 객체로 변환합니다.

    Args:
        row: RealDictCursor 반환 딕셔너리

    Returns:
        LeaveBalance 객체
    """
    return LeaveBalance(
        id=row["id"],
        employee_id=row["employee_id"],
        year=row["year"],
        total_days=float(row["total_days"]),
        used_days=float(row["used_days"]),
        remaining_days=float(row["remaining_days"]),
        name=row.get("name"),
        emp_no=row.get("emp_no"),
    )


# ============================================================
# 매출 CRUD
# ============================================================

def create_sale(
    conn: psycopg2.extensions.connection,
    dept: str,
    sale_date: date,
    amount: int,
    item: str,
) -> Sale:
    """매출 기록을 등록합니다.

    Args:
        conn:      psycopg2 연결 객체
        dept:      매출 부서
        sale_date: 매출 일자
        amount:    금액 (원)
        item:      매출 항목

    Returns:
        등록된 Sale 객체
    """
    sql = """
        INSERT INTO sales (dept, sale_date, amount, item)
        VALUES (%s, %s, %s, %s)
        RETURNING id, dept, sale_date, amount, item
    """
    with conn.cursor() as cur:
        cur.execute(sql, (dept, sale_date, amount, item))   # ①
        row = cur.fetchone()                                 # ②
    return _row_to_sale(row)


def get_all_sales(
    conn: psycopg2.extensions.connection,
    dept_filter: Optional[str] = None,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    limit: int = 50,
) -> list[Sale]:
    """매출 목록을 조회합니다 (부서/기간 필터 지원).

    Args:
        conn:        psycopg2 연결 객체
        dept_filter: 부서 부분 검색
        date_from:   조회 시작일
        date_to:     조회 종료일
        limit:       최대 반환 건수 (기본 50)

    Returns:
        Sale 객체 리스트 (sale_date 내림차순)
    """
    conditions: list[str] = []
    params: list = []

    if dept_filter:
        conditions.append("dept ILIKE %s")          # ①
        params.append(f"%{dept_filter}%")
    if date_from:
        conditions.append("sale_date >= %s")        # ②
        params.append(date_from)
    if date_to:
        conditions.append("sale_date <= %s")        # ③
        params.append(date_to)

    where_clause = ("WHERE " + " AND ".join(conditions)) if conditions else ""
    params.append(limit)
    sql = f"""
        SELECT id, dept, sale_date, amount, item FROM sales
        {where_clause} ORDER BY sale_date DESC LIMIT %s
    """
    with conn.cursor() as cur:
        cur.execute(sql, params)                    # ④
        rows = cur.fetchall()

    return [_row_to_sale(r) for r in rows]


def get_dept_summary(
    conn: psycopg2.extensions.connection,
    dept: str,
) -> Optional[DeptSummary]:
    """특정 부서의 누적 매출 합계를 조회합니다.

    Args:
        conn: psycopg2 연결 객체
        dept: 부서명

    Returns:
        DeptSummary 객체 또는 None (매출 없음)
    """
    sql = """
        SELECT dept, SUM(amount) AS total_amount
        FROM sales
        WHERE dept ILIKE %s
        GROUP BY dept
    """
    with conn.cursor() as cur:
        cur.execute(sql, (f"%{dept}%",))
        row = cur.fetchone()

    if row is None:
        return None
    return DeptSummary(dept=row["dept"], total_amount=int(row["total_amount"]))


def get_dashboard_stats(conn: psycopg2.extensions.connection) -> dict:
    """대시보드 통계 (직원 수, 연차 수, 매출 건수 및 합계)를 조회합니다.

    Args:
        conn: psycopg2 연결 객체

    Returns:
        통계 딕셔너리 {employees_count, leaves_count, sales_count, sales_total}
    """
    # [PROCESS] 4개 집계 쿼리 한 번에 실행
    with conn.cursor() as cur:
        cur.execute("SELECT COUNT(*) AS cnt FROM employee")          # ①
        emp_cnt = cur.fetchone()["cnt"]

        cur.execute("SELECT COUNT(*) AS cnt FROM leave_balance")     # ②
        leave_cnt = cur.fetchone()["cnt"]

        cur.execute("SELECT COUNT(*) AS cnt FROM sales")             # ③
        sales_cnt = cur.fetchone()["cnt"]

        cur.execute("SELECT COALESCE(SUM(amount), 0) AS total FROM sales")  # ④
        sales_total = cur.fetchone()["total"]

    return {
        "employees_count": emp_cnt,
        "leaves_count": leave_cnt,
        "sales_count": sales_cnt,
        "sales_total": int(sales_total),
    }


def get_recent_sales(
    conn: psycopg2.extensions.connection,
    limit: int = 5,
) -> list[Sale]:
    """최근 매출 N건을 조회합니다.

    Args:
        conn:  psycopg2 연결 객체
        limit: 반환 건수 (기본 5)

    Returns:
        Sale 객체 리스트 (sale_date 내림차순)
    """
    sql = """
        SELECT id, dept, sale_date, amount, item
        FROM sales ORDER BY sale_date DESC LIMIT %s
    """
    with conn.cursor() as cur:
        cur.execute(sql, (limit,))
        rows = cur.fetchall()
    return [_row_to_sale(r) for r in rows]


def _row_to_sale(row: dict) -> Sale:
    """DB 결과 딕셔너리를 Sale 객체로 변환합니다.

    Args:
        row: RealDictCursor 반환 딕셔너리

    Returns:
        Sale 객체
    """
    return Sale(
        id=row["id"],
        dept=row["dept"],
        sale_date=row["sale_date"],
        amount=int(row["amount"]),
        item=row["item"],
    )
