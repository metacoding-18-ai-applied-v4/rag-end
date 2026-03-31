"""
Jinja2 뷰(View) 라우터 모듈.

Admin UI 페이지 렌더링을 담당합니다.
GET 요청 → DB 조회 → Jinja2 템플릿 렌더링 흐름으로 동작합니다.
"""

import datetime
from typing import Optional

from fastapi import APIRouter, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from app import crud
from app.database import get_connection
from app.models import Sale

router = APIRouter(prefix="/admin")
templates = Jinja2Templates(directory="templates")

DEPARTMENTS = ["개발팀", "영업팀", "인사팀", "마케팅팀"]
POSITIONS = ["사원", "대리", "과장", "차장", "부장"]


# ============================================================
# 대시보드
# ============================================================

@router.get("/dashboard", response_class=HTMLResponse)
def view_dashboard(request: Request) -> HTMLResponse:
    """대시보드 페이지 — 직원/연차/매출 통계 카드를 렌더링합니다.

    Args:
        request: FastAPI Request 객체

    Returns:
        대시보드 HTML 페이지
    """
    # [INPUT] DB에서 통계 조회
    try:
        with get_connection() as conn:
            stats = crud.get_dashboard_stats(conn)          # ①
            recent_sales = crud.get_recent_sales(conn, 5)   # ②
    except RuntimeError:
        stats = {"employees_count": 0, "leaves_count": 0, "sales_count": 0, "sales_total": 0}
        recent_sales = []

    # [OUTPUT] 템플릿 렌더링
    return templates.TemplateResponse(                       # ③
        "dashboard.html",
        {
            "request": request,
            "active_page": "dashboard",
            "db_path": "PostgreSQL (metacoding_db)",
            **stats,
            "recent_sales": [
                {
                    "dept": s.dept,
                    "amount": f"{s.amount:,}원",
                    "date": s.sale_date.strftime("%Y-%m-%d"),
                    "description": s.item,
                }
                for s in recent_sales
            ],
        },
    )


@router.get("/", response_class=HTMLResponse)
def view_root(request: Request) -> RedirectResponse:
    """루트 경로를 대시보드로 리다이렉트합니다.

    Args:
        request: FastAPI Request 객체

    Returns:
        대시보드로의 리다이렉트 응답
    """
    return RedirectResponse(url="/admin/dashboard")


# ============================================================
# 직원 관리
# ============================================================

@router.get("/employees", response_class=HTMLResponse)
def view_employees(
    request: Request,
    name: Optional[str] = None,
    dept: Optional[str] = None,
) -> HTMLResponse:
    """직원 목록 페이지를 렌더링합니다 (이름/부서 검색 지원).

    Args:
        request: FastAPI Request 객체
        name:    이름 검색 필터 (쿼리 파라미터)
        dept:    부서 검색 필터 (쿼리 파라미터)

    Returns:
        직원 관리 HTML 페이지
    """
    # [INPUT] DB 조회
    try:
        with get_connection() as conn:
            employees = crud.get_all_employees(conn, name, dept)    # ①
    except RuntimeError:
        employees = []

    # [PROCESS] dataclass → dict 변환 (템플릿 호환)
    emp_dicts = [
        {
            "emp_no": e.emp_no,
            "name": e.name,
            "dept": e.dept,
            "position": e.position,
            "hire_date": e.hire_date.strftime("%Y-%m-%d"),
        }
        for e in employees
    ]

    # [OUTPUT] 렌더링
    return templates.TemplateResponse(                               # ②
        "employees.html",
        {
            "request": request,
            "active_page": "employees",
            "employees": emp_dicts,
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
    dept: str = Form(...),
    position: str = Form(...),
    hire_date: str = Form(...),
) -> RedirectResponse:
    """직원 등록 폼을 처리하고 목록 페이지로 리다이렉트합니다.

    Args:
        request:   FastAPI Request 객체
        name:      이름
        dept:      부서
        position:  직급
        hire_date: 입사일 (YYYY-MM-DD 문자열)

    Returns:
        직원 목록으로 리다이렉트
    """
    # [INPUT] 날짜 문자열 파싱
    parsed_date = datetime.date.fromisoformat(hire_date)             # ①

    # [PROCESS] DB 저장 (사번은 자동 생성)
    try:
        with get_connection() as conn:
            crud.create_employee(conn, name, dept, position, parsed_date)  # ②
    except Exception as exc:
        print(f"직원 등록 실패: {exc}")

    # [OUTPUT] 목록으로 리다이렉트
    return RedirectResponse(url="/admin/employees", status_code=303)  # ③


@router.post("/employees/update")
def update_employee_view(
    request: Request,
    emp_no: str = Form(...),
    name: Optional[str] = Form(None),
    dept: Optional[str] = Form(None),
    position: Optional[str] = Form(None),
    hire_date: Optional[str] = Form(None),
) -> RedirectResponse:
    """직원 수정 폼을 처리합니다.

    Args:
        request:   FastAPI Request 객체
        emp_no:    대상 직원 사번
        name:      수정할 이름 (빈 문자열이면 None으로 처리)
        dept:      수정할 부서
        position:  수정할 직급
        hire_date: 수정할 입사일 문자열

    Returns:
        직원 목록으로 리다이렉트
    """
    # [PROCESS] 빈 문자열을 None으로 정규화
    parsed_date = datetime.date.fromisoformat(hire_date) if hire_date else None
    name_val = name if name else None
    dept_val = dept if dept else None
    pos_val  = position if position else None

    try:
        with get_connection() as conn:
            crud.update_employee(conn, emp_no, name_val, dept_val, pos_val, parsed_date)
    except Exception as exc:
        print(f"직원 수정 실패: {exc}")

    return RedirectResponse(url="/admin/employees", status_code=303)


@router.post("/employees/delete")
def delete_employee_view(
    request: Request,
    emp_no: str = Form(...),
) -> RedirectResponse:
    """직원 삭제 폼을 처리합니다.

    Args:
        request: FastAPI Request 객체
        emp_no:  삭제할 직원 사번

    Returns:
        직원 목록으로 리다이렉트
    """
    try:
        with get_connection() as conn:
            deleted = crud.delete_employee(conn, emp_no)
            if not deleted:
                print(f"사번 {emp_no}를 찾을 수 없습니다.")
    except Exception as exc:
        print(f"직원 삭제 실패: {exc}")

    return RedirectResponse(url="/admin/employees", status_code=303)


# ============================================================
# 휴가 관리
# ============================================================

@router.get("/leaves", response_class=HTMLResponse)
def view_leaves(
    request: Request,
    employee_name: Optional[str] = None,
) -> HTMLResponse:
    """휴가 잔여 현황 페이지를 렌더링합니다.

    Args:
        request:       FastAPI Request 객체
        employee_name: 직원 이름 검색 필터

    Returns:
        휴가 관리 HTML 페이지
    """
    try:
        with get_connection() as conn:
            leaves = crud.get_all_leaves(conn, employee_name)      # ①
            employees = crud.get_all_employees(conn)               # ② 드롭다운용
    except RuntimeError:
        leaves = []
        employees = []

    # [PROCESS] LeaveBalance → 템플릿용 dict 변환
    leave_dicts = [
        {
            "emp_no": lb.emp_no or "-",
            "name": lb.name or "-",
            "year": lb.year,
            "total": lb.total_days,
            "used": lb.used_days,
            "remaining": lb.remaining_days,
        }
        for lb in leaves
    ]

    emp_options = [{"emp_no": e.emp_no, "name": e.name} for e in employees]

    return templates.TemplateResponse(                              # ③
        "leaves.html",
        {
            "request": request,
            "active_page": "leaves",
            "leaves": leave_dicts,
            "employees": emp_options,
            "search_employee_name": employee_name or "",
        },
    )


@router.post("/leaves/usage")
def record_leave_usage(
    request: Request,
    emp_no: str = Form(...),
    days: float = Form(...),
) -> RedirectResponse:
    """휴가 사용 등록 폼을 처리합니다.

    Args:
        request: FastAPI Request 객체
        emp_no:  직원 사번
        days:    사용할 연차 일수

    Returns:
        휴가 목록으로 리다이렉트
    """
    try:
        with get_connection() as conn:
            crud.update_leave_usage(conn, emp_no, days)            # ①
    except ValueError as ve:
        print(f"연차 사용 등록 실패: {ve}")
    except Exception as exc:
        print(f"연차 사용 등록 오류: {exc}")

    return RedirectResponse(url="/admin/leaves", status_code=303)


@router.post("/leaves/update")
def update_leave_view(
    request: Request,
    emp_no: str = Form(...),
    year: int = Form(...),
    total: float = Form(...),
    used: float = Form(...),
) -> RedirectResponse:
    """휴가 정보 수정 폼을 처리합니다.

    Args:
        request: FastAPI Request 객체
        emp_no:  직원 사번
        year:    대상 연도
        total:   수정할 총 연차
        used:    수정할 사용 연차

    Returns:
        휴가 목록으로 리다이렉트
    """
    try:
        with get_connection() as conn:
            crud.update_leave_balance(conn, emp_no, year, total, used)  # ①
    except Exception as exc:
        print(f"휴가 수정 실패: {exc}")

    return RedirectResponse(url="/admin/leaves", status_code=303)


# ============================================================
# 매출 관리
# ============================================================

@router.get("/sales", response_class=HTMLResponse)
def view_sales(
    request: Request,
    dept: Optional[str] = None,
    period_start: Optional[str] = None,
    period_end: Optional[str] = None,
) -> HTMLResponse:
    """매출 관리 페이지를 렌더링합니다.

    Args:
        request:      FastAPI Request 객체
        dept:         부서 필터 (쿼리 파라미터)
        period_start: 조회 시작일 (YYYY-MM-DD)
        period_end:   조회 종료일 (YYYY-MM-DD)

    Returns:
        매출 관리 HTML 페이지
    """
    # [INPUT] 날짜 파싱
    d_from = datetime.date.fromisoformat(period_start) if period_start else None  # ①
    d_to   = datetime.date.fromisoformat(period_end)   if period_end   else None  # ②

    try:
        with get_connection() as conn:
            all_sales    = crud.get_all_sales(conn, limit=50)                      # ③
            period_sales = (
                crud.get_all_sales(conn, date_from=d_from, date_to=d_to)
                if (d_from or d_to) else []
            )
            dept_summary = crud.get_dept_summary(conn, dept) if dept else None     # ④
    except RuntimeError:
        all_sales = []
        period_sales = []
        dept_summary = None

    def sale_to_dict(s: Sale) -> dict:
        """Sale 객체를 템플릿용 딕셔너리로 변환합니다."""
        return {
            "dept": s.dept,
            "amount": f"{s.amount:,}",
            "date": s.sale_date.strftime("%Y-%m-%d"),
            "description": s.item,
        }

    return templates.TemplateResponse(                                             # ⑤
        "sales.html",
        {
            "request": request,
            "active_page": "sales",
            "sales": [sale_to_dict(s) for s in all_sales],
            "period_sales": [sale_to_dict(s) for s in period_sales],
            "departments": DEPARTMENTS,
            "dept_summary": (
                {"dept": dept_summary.dept, "total_amount": f"{dept_summary.total_amount:,}원"}
                if dept_summary else None
            ),
            "period_start": period_start or "",
            "period_end": period_end or "",
            "dept": dept or "",
        },
    )


@router.post("/sales/create")
def create_sale_view(
    request: Request,
    dept: str = Form(...),
    amount: int = Form(...),
    sale_date: str = Form(...),
    description: str = Form(""),
) -> RedirectResponse:
    """매출 등록 폼을 처리합니다.

    HTML 폼 필드명: dept, amount, sale_date, description

    Args:
        request:     FastAPI Request 객체
        dept:        부서
        amount:      금액
        sale_date:   매출 일자 (YYYY-MM-DD 문자열)
        description: 항목 설명

    Returns:
        매출 목록으로 리다이렉트
    """
    # [INPUT] 날짜 문자열 → date 객체
    parsed_date = datetime.date.fromisoformat(sale_date)            # ①

    # [PROCESS] DB 저장
    try:
        with get_connection() as conn:
            crud.create_sale(conn, dept, parsed_date, amount, description)  # ②
    except Exception as exc:
        print(f"매출 등록 실패: {exc}")

    # [OUTPUT] 리다이렉트
    return RedirectResponse(url="/admin/sales", status_code=303)    # ③
