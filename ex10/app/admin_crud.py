"""관리자 대시보드 CRUD 모듈."""

import datetime

DEPARTMENTS = ["영업부", "인사부", "개발부", "마케팅부"]
POSITIONS = ["사원", "주임", "대리", "선임", "과장", "팀장"]


def _execute_write(db, sql, params=()):
    """INSERT/UPDATE/DELETE를 실행하고 커밋한다."""
    cur = db._conn.cursor()
    cur.execute(sql, params)
    db._conn.commit()
    cur.close()


# ============================================================
# 직원 CRUD
# ============================================================


def generate_emp_no(db):
    """다음 사번을 자동 생성한다 (E001, E002, ...)."""
    rows = db.execute(
        "SELECT emp_no FROM employees ORDER BY emp_no DESC LIMIT 1"
    )
    if not rows:
        return "E001"
    last_no = int(rows[0]["emp_no"].replace("E", ""))
    return f"E{last_no + 1:03d}"


def get_all_employees(db, name=None, dept=None):
    """직원 목록을 조회한다 (이름/부서 검색 지원)."""
    sql = "SELECT emp_no, name, department, position, hire_date FROM employees"
    conditions = []
    params = []
    if name:
        conditions.append("name ILIKE %s")
        params.append(f"%{name}%")
    if dept:
        conditions.append("department ILIKE %s")
        params.append(f"%{dept}%")
    if conditions:
        sql += " WHERE " + " AND ".join(conditions)
    sql += " ORDER BY emp_no"
    return db.execute(sql, tuple(params))


def create_employee(db, name, department, position, hire_date):
    """직원을 등록하고 사번을 반환한다. 연차 레코드도 함께 생성한다."""
    emp_no = generate_emp_no(db)
    _execute_write(
        db,
        "INSERT INTO employees (emp_no, name, department, position, hire_date) "
        "VALUES (%s, %s, %s, %s, %s)",
        (emp_no, name, department, position, hire_date),
    )
    _execute_write(
        db,
        "INSERT INTO leave_balance (emp_no, total_days, used_days, year) "
        "VALUES (%s, 15, 0, %s) ON CONFLICT DO NOTHING",
        (emp_no, datetime.date.today().year),
    )
    return emp_no


def update_employee(db, emp_no, name=None, department=None, position=None, hire_date=None):
    """직원 정보를 수정한다 (None이 아닌 필드만 업데이트)."""
    sets = []
    params = []
    if name:
        sets.append("name = %s")
        params.append(name)
    if department:
        sets.append("department = %s")
        params.append(department)
    if position:
        sets.append("position = %s")
        params.append(position)
    if hire_date:
        sets.append("hire_date = %s")
        params.append(hire_date)
    if not sets:
        return
    params.append(emp_no)
    _execute_write(
        db,
        f"UPDATE employees SET {', '.join(sets)} WHERE emp_no = %s",
        tuple(params),
    )


def delete_employee(db, emp_no):
    """직원을 삭제한다 (연차·매출 데이터도 함께 삭제)."""
    _execute_write(db, "DELETE FROM sales WHERE emp_no = %s", (emp_no,))
    _execute_write(db, "DELETE FROM leave_balance WHERE emp_no = %s", (emp_no,))
    _execute_write(db, "DELETE FROM employees WHERE emp_no = %s", (emp_no,))
    return True


# ============================================================
# 연차 CRUD
# ============================================================


def get_all_leaves(db, employee_name=None):
    """연차 현황을 조회한다 (직원 이름 검색 지원). remaining을 계산한다."""
    sql = """
        SELECT e.emp_no, e.name, e.department, lb.year,
               lb.total_days, lb.used_days,
               (lb.total_days - lb.used_days) AS remaining
        FROM leave_balance lb
        JOIN employees e ON lb.emp_no = e.emp_no
    """
    params = []
    if employee_name:
        sql += " WHERE e.name ILIKE %s"
        params.append(f"%{employee_name}%")
    sql += " ORDER BY e.emp_no"
    return db.execute(sql, tuple(params))


def update_leave_usage(db, emp_no, days):
    """연차 사용을 등록한다 (used_days 누적)."""
    rows = db.execute(
        "SELECT total_days, used_days FROM leave_balance WHERE emp_no = %s",
        (emp_no,),
    )
    if not rows:
        raise ValueError(f"사번 {emp_no}의 연차 정보가 없습니다.")
    remaining = rows[0]["total_days"] - rows[0]["used_days"]
    if days > remaining:
        raise ValueError(
            f"잔여 연차({remaining}일)보다 많은 {days}일을 사용할 수 없습니다."
        )
    _execute_write(
        db,
        "UPDATE leave_balance SET used_days = used_days + %s WHERE emp_no = %s",
        (days, emp_no),
    )


def update_leave_balance(db, emp_no, year, total, used):
    """연차 정보를 직접 수정한다 (총량/사용량/연도)."""
    _execute_write(
        db,
        "INSERT INTO leave_balance (emp_no, total_days, used_days, year) "
        "VALUES (%s, %s, %s, %s) "
        "ON CONFLICT (emp_no) DO UPDATE SET total_days = %s, used_days = %s, year = %s",
        (emp_no, total, used, year, total, used, year),
    )


# ============================================================
# 매출 CRUD
# ============================================================


def get_all_sales(db, limit=50, date_from=None, date_to=None):
    """매출 목록을 조회한다 (직원 이름/부서 포함)."""
    sql = """
        SELECT s.emp_no, e.name, e.department, s.amount,
               s.sale_date, s.description
        FROM sales s
        JOIN employees e ON s.emp_no = e.emp_no
    """
    conditions = []
    params = []
    if date_from:
        conditions.append("s.sale_date >= %s")
        params.append(date_from)
    if date_to:
        conditions.append("s.sale_date <= %s")
        params.append(date_to)
    if conditions:
        sql += " WHERE " + " AND ".join(conditions)
    sql += " ORDER BY s.sale_date DESC"
    if limit:
        sql += f" LIMIT {limit}"
    return db.execute(sql, tuple(params))


def create_sale(db, emp_no, amount, sale_date, description=""):
    """매출을 등록한다."""
    _execute_write(
        db,
        "INSERT INTO sales (emp_no, amount, sale_date, description) "
        "VALUES (%s, %s, %s, %s)",
        (emp_no, amount, sale_date, description),
    )


def get_dept_summary(db, department):
    """특정 부서의 매출 합계를 반환한다."""
    rows = db.execute(
        """
        SELECT e.department, SUM(s.amount) AS total_amount
        FROM sales s
        JOIN employees e ON s.emp_no = e.emp_no
        WHERE e.department = %s
        GROUP BY e.department
        """,
        (department,),
    )
    return rows[0] if rows else None


# ============================================================
# 대시보드
# ============================================================


def get_dashboard_stats(db):
    """대시보드 통계를 반환한다."""
    emp_rows = db.execute("SELECT COUNT(*) AS cnt FROM employees")
    leave_rows = db.execute("SELECT COUNT(*) AS cnt FROM leave_balance")
    sales_rows = db.execute(
        "SELECT COUNT(*) AS cnt, COALESCE(SUM(amount), 0) AS total FROM sales"
    )
    return {
        "employees_count": emp_rows[0]["cnt"] if emp_rows else 0,
        "leaves_count": leave_rows[0]["cnt"] if leave_rows else 0,
        "sales_count": sales_rows[0]["cnt"] if sales_rows else 0,
        "sales_total": sales_rows[0]["total"] if sales_rows else 0,
    }


def get_recent_sales(db, limit=5):
    """최근 매출을 조회한다."""
    return db.execute(
        """
        SELECT s.emp_no, e.name, e.department, s.amount,
               s.sale_date, s.description
        FROM sales s
        JOIN employees e ON s.emp_no = e.emp_no
        ORDER BY s.sale_date DESC
        LIMIT %s
        """,
        (limit,),
    )
