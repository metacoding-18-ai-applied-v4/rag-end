"""ex06 — 관리자 대시보드 뷰 라우터."""

import datetime
import os

from fastapi import APIRouter, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from app import admin_crud
from app.admin_crud import DEPARTMENTS, POSITIONS
from app.database import get_db_connection_safe

router = APIRouter(prefix="/admin")

_BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
templates = Jinja2Templates(directory=os.path.join(_BASE_DIR, "templates"))


# ============================================================
# 대시보드
# ============================================================


@router.get("/dashboard", response_class=HTMLResponse)
def view_dashboard(request: Request):
    """대시보드 페이지 — 직원/연차/매출 통계 카드를 렌더링한다."""
    db = get_db_connection_safe()
    if db is None:
        return templates.TemplateResponse(
            "dashboard.html",
            {
                "request": request,
                "active_page": "dashboard",
                "db_path": "PostgreSQL 연결 실패",
                "employees_count": 0,
                "leaves_count": 0,
                "sales_count": 0,
                "sales_total": 0,
                "recent_sales": [],
            },
        )
    try:
        stats = admin_crud.get_dashboard_stats(db)
        recent_sales = admin_crud.get_recent_sales(db, 5)
    finally:
        db.close()

    return templates.TemplateResponse(
        "dashboard.html",
        {
            "request": request,
            "active_page": "dashboard",
            "db_path": "PostgreSQL (rag_db)",
            **stats,
            "recent_sales": [
                {
                    "department": s["department"],
                    "name": s["name"],
                    "amount": f"{s['amount']:,}원",
                    "date": (
                        s["sale_date"].strftime("%Y-%m-%d")
                        if hasattr(s["sale_date"], "strftime")
                        else str(s["sale_date"])
                    ),
                    "description": s["description"] or "",
                }
                for s in recent_sales
            ],
        },
    )


@router.get("/", response_class=HTMLResponse)
def view_admin_root(request: Request):
    """관리자 루트를 대시보드로 리다이렉트한다."""
    return RedirectResponse(url="/admin/dashboard")


# ============================================================
# 직원 관리
# ============================================================


@router.get("/employees", response_class=HTMLResponse)
def view_employees(request: Request, name=None, dept=None):
    """직원 목록 페이지를 렌더링한다 (이름/부서 검색 지원)."""
    db = get_db_connection_safe()
    employees = []
    if db:
        try:
            employees = admin_crud.get_all_employees(db, name, dept)
        finally:
            db.close()

    for e in employees:
        if hasattr(e.get("hire_date"), "strftime"):
            e["hire_date"] = e["hire_date"].strftime("%Y-%m-%d")

    return templates.TemplateResponse(
        "employees.html",
        {
            "request": request,
            "active_page": "employees",
            "employees": employees,
            "departments": DEPARTMENTS,
            "positions": POSITIONS,
            "search_name": name or "",
            "search_dept": dept or "",
        },
    )


@router.post("/employees/create")
def create_employee_view(
    request: Request,
    name: str = Form(...),
    department: str = Form(...),
    position: str = Form(...),
    hire_date: str = Form(...),
):
    """직원 등록 폼을 처리한다."""
    parsed_date = datetime.date.fromisoformat(hire_date)
    db = get_db_connection_safe()
    if db:
        try:
            admin_crud.create_employee(
                db, name, department, position, parsed_date
            )
        except Exception as exc:
            print(f"직원 등록 실패: {exc}")
        finally:
            db.close()
    return RedirectResponse(url="/admin/employees", status_code=303)


@router.post("/employees/update")
def update_employee_view(
    request: Request,
    emp_no: str = Form(...),
    name=Form(None),
    department=Form(None),
    position=Form(None),
    hire_date=Form(None),
):
    """직원 수정 폼을 처리한다."""
    parsed_date = (
        datetime.date.fromisoformat(hire_date) if hire_date else None
    )
    name_val = name if name else None
    dept_val = department if department else None
    pos_val = position if position else None

    db = get_db_connection_safe()
    if db:
        try:
            admin_crud.update_employee(
                db, emp_no, name_val, dept_val, pos_val, parsed_date
            )
        except Exception as exc:
            print(f"직원 수정 실패: {exc}")
        finally:
            db.close()
    return RedirectResponse(url="/admin/employees", status_code=303)


@router.post("/employees/delete")
def delete_employee_view(
    request: Request,
    emp_no: str = Form(...),
):
    """직원 삭제 폼을 처리한다."""
    db = get_db_connection_safe()
    if db:
        try:
            admin_crud.delete_employee(db, emp_no)
        except Exception as exc:
            print(f"직원 삭제 실패: {exc}")
        finally:
            db.close()
    return RedirectResponse(url="/admin/employees", status_code=303)


# ============================================================
# 휴가 관리
# ============================================================


@router.get("/leaves", response_class=HTMLResponse)
def view_leaves(request: Request, employee_name=None):
    """휴가 잔여 현황 페이지를 렌더링한다."""
    db = get_db_connection_safe()
    leaves = []
    employees = []
    if db:
        try:
            leaves = admin_crud.get_all_leaves(db, employee_name)
            employees = admin_crud.get_all_employees(db)
        finally:
            db.close()

    return templates.TemplateResponse(
        "leaves.html",
        {
            "request": request,
            "active_page": "leaves",
            "leaves": leaves,
            "employees": employees,
            "search_employee_name": employee_name or "",
        },
    )


@router.post("/leaves/usage")
def record_leave_usage(
    request: Request,
    emp_no: str = Form(...),
    days: float = Form(...),
):
    """휴가 사용 등록 폼을 처리한다."""
    db = get_db_connection_safe()
    if db:
        try:
            admin_crud.update_leave_usage(db, emp_no, days)
        except ValueError as ve:
            print(f"연차 사용 등록 실패: {ve}")
        except Exception as exc:
            print(f"연차 사용 등록 오류: {exc}")
        finally:
            db.close()
    return RedirectResponse(url="/admin/leaves", status_code=303)


@router.post("/leaves/update")
def update_leave_view(
    request: Request,
    emp_no: str = Form(...),
    year: int = Form(...),
    total: float = Form(...),
    used: float = Form(...),
):
    """휴가 정보 수정 폼을 처리한다."""
    db = get_db_connection_safe()
    if db:
        try:
            admin_crud.update_leave_balance(db, emp_no, year, total, used)
        except Exception as exc:
            print(f"휴가 수정 실패: {exc}")
        finally:
            db.close()
    return RedirectResponse(url="/admin/leaves", status_code=303)


# ============================================================
# 매출 관리
# ============================================================


@router.get("/sales", response_class=HTMLResponse)
def view_sales(request: Request, dept=None, period_start=None, period_end=None):
    """매출 관리 페이지를 렌더링한다."""
    d_from = (
        datetime.date.fromisoformat(period_start) if period_start else None
    )
    d_to = datetime.date.fromisoformat(period_end) if period_end else None

    db = get_db_connection_safe()
    all_sales = []
    period_sales = []
    dept_summary = None
    employees = []
    if db:
        try:
            all_sales = admin_crud.get_all_sales(db, limit=50)
            period_sales = (
                admin_crud.get_all_sales(db, date_from=d_from, date_to=d_to)
                if (d_from or d_to)
                else []
            )
            dept_summary = (
                admin_crud.get_dept_summary(db, dept) if dept else None
            )
            employees = admin_crud.get_all_employees(db)
        finally:
            db.close()

    def format_sale(s):
        return {
            "department": s["department"],
            "name": s["name"],
            "amount": f"{s['amount']:,}",
            "date": (
                s["sale_date"].strftime("%Y-%m-%d")
                if hasattr(s["sale_date"], "strftime")
                else str(s["sale_date"])
            ),
            "description": s["description"] or "",
        }

    return templates.TemplateResponse(
        "sales.html",
        {
            "request": request,
            "active_page": "sales",
            "sales": [format_sale(s) for s in all_sales],
            "period_sales": [format_sale(s) for s in period_sales],
            "departments": DEPARTMENTS,
            "employees": employees,
            "dept_summary": (
                {
                    "department": dept_summary["department"],
                    "total_amount": f"{dept_summary['total_amount']:,}원",
                }
                if dept_summary
                else None
            ),
            "period_start": period_start or "",
            "period_end": period_end or "",
            "dept": dept or "",
        },
    )


@router.post("/sales/create")
def create_sale_view(
    request: Request,
    emp_no: str = Form(...),
    amount: int = Form(...),
    sale_date: str = Form(...),
    description: str = Form(""),
):
    """매출 등록 폼을 처리한다."""
    parsed_date = datetime.date.fromisoformat(sale_date)
    db = get_db_connection_safe()
    if db:
        try:
            admin_crud.create_sale(
                db, emp_no, amount, parsed_date, description
            )
        except Exception as exc:
            print(f"매출 등록 실패: {exc}")
        finally:
            db.close()
    return RedirectResponse(url="/admin/sales", status_code=303)
