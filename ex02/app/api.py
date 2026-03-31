"""
REST JSON API 라우터 모듈.

/api/* 경로로 직원(employee), 연차(leave_balance), 매출(sales)에 대한
JSON 기반 CRUD 엔드포인트를 제공합니다.
Swagger UI(/docs)에서 직접 테스트할 수 있습니다.
"""

from typing import Optional

from fastapi import APIRouter, HTTPException, Query

from app import crud
from app.database import get_connection
from app.schemas import (
    DeptSummaryResponse,
    EmployeeCreate,
    EmployeeResponse,
    EmployeeUpdate,
    LeaveBalanceCreate,
    LeaveBalanceResponse,
    LeaveBalanceUpdate,
    LeaveUsageRequest,
    SaleCreate,
    SaleResponse,
)

router = APIRouter(prefix="/api", tags=["API"])


# ============================================================
# 직원 API
# ============================================================

@router.get("/employees", response_model=list[EmployeeResponse], summary="직원 전체 조회")
def api_get_employees(
    name: Optional[str] = Query(None, description="이름 검색 (부분 일치)"),
    dept: Optional[str] = Query(None, description="부서 검색 (부분 일치)"),
) -> list[EmployeeResponse]:
    """직원 목록을 JSON으로 반환합니다.

    Args:
        name: 이름 필터 (쿼리 파라미터)
        dept: 부서 필터 (쿼리 파라미터)

    Returns:
        EmployeeResponse 리스트
    """
    try:
        with get_connection() as conn:
            employees = crud.get_all_employees(conn, name, dept)    # ①
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail="데이터베이스에 연결할 수 없습니다.") from exc

    return [                                                         # ②
        EmployeeResponse(
            id=e.id, emp_no=e.emp_no, name=e.name,
            dept=e.dept, position=e.position, hire_date=e.hire_date,
        )
        for e in employees
    ]


@router.get("/employees/{emp_no}", response_model=EmployeeResponse, summary="직원 단건 조회")
def api_get_employee(emp_no: str) -> EmployeeResponse:
    """사번으로 단일 직원 정보를 반환합니다.

    Args:
        emp_no: 직원 사번 (URL 경로)

    Returns:
        EmployeeResponse

    Raises:
        HTTPException 404: 해당 사번의 직원이 없을 때
    """
    try:
        with get_connection() as conn:
            emp = crud.get_employee_by_emp_no(conn, emp_no)        # ①
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail="데이터베이스에 연결할 수 없습니다.") from exc

    if emp is None:
        raise HTTPException(                                        # ②
            status_code=404,
            detail=f"사번 '{emp_no}'을(를) 찾을 수 없습니다."
        )

    return EmployeeResponse(
        id=emp.id, emp_no=emp.emp_no, name=emp.name,
        dept=emp.dept, position=emp.position, hire_date=emp.hire_date,
    )


@router.post("/employees", response_model=EmployeeResponse, status_code=201, summary="직원 등록")
def api_create_employee(body: EmployeeCreate) -> EmployeeResponse:
    """직원을 등록합니다 (사번은 자동 생성).

    Args:
        body: EmployeeCreate (JSON body)

    Returns:
        등록된 EmployeeResponse (HTTP 201)
    """
    try:
        with get_connection() as conn:
            emp = crud.create_employee(                             # ①
                conn, body.name,
                body.dept, body.position, body.hire_date,
            )
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail="데이터베이스에 연결할 수 없습니다.") from exc

    return EmployeeResponse(
        id=emp.id, emp_no=emp.emp_no, name=emp.name,
        dept=emp.dept, position=emp.position, hire_date=emp.hire_date,
    )


@router.patch("/employees/{emp_no}", response_model=EmployeeResponse, summary="직원 수정")
def api_update_employee(emp_no: str, body: EmployeeUpdate) -> EmployeeResponse:
    """직원 정보를 부분 수정합니다 (입력된 필드만 변경).

    Args:
        emp_no: 직원 사번 (URL 경로)
        body:   EmployeeUpdate (JSON body)

    Returns:
        수정된 EmployeeResponse

    Raises:
        HTTPException 404: 해당 사번의 직원이 없을 때
    """
    try:
        with get_connection() as conn:
            emp = crud.update_employee(                             # ①
                conn, emp_no,
                body.name, body.dept, body.position, body.hire_date,
            )
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail="데이터베이스에 연결할 수 없습니다.") from exc

    if emp is None:
        raise HTTPException(status_code=404, detail=f"사번 '{emp_no}'을(를) 찾을 수 없습니다.")

    return EmployeeResponse(
        id=emp.id, emp_no=emp.emp_no, name=emp.name,
        dept=emp.dept, position=emp.position, hire_date=emp.hire_date,
    )


@router.delete("/employees/{emp_no}", status_code=204, summary="직원 삭제")
def api_delete_employee(emp_no: str) -> None:
    """직원을 삭제합니다.

    Args:
        emp_no: 직원 사번 (URL 경로)

    Raises:
        HTTPException 404: 해당 사번의 직원이 없을 때
    """
    try:
        with get_connection() as conn:
            deleted = crud.delete_employee(conn, emp_no)           # ①
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail="데이터베이스에 연결할 수 없습니다.") from exc

    if not deleted:
        raise HTTPException(status_code=404, detail=f"사번 '{emp_no}'을(를) 찾을 수 없습니다.")


# ============================================================
# 연차 API
# ============================================================

@router.get("/leaves", response_model=list[LeaveBalanceResponse], summary="연차 전체 조회")
def api_get_leaves(
    employee_name: Optional[str] = Query(None, description="직원 이름 검색"),
) -> list[LeaveBalanceResponse]:
    """연차 잔여량 목록을 JSON으로 반환합니다.

    Args:
        employee_name: 직원 이름 필터

    Returns:
        LeaveBalanceResponse 리스트
    """
    try:
        with get_connection() as conn:
            leaves = crud.get_all_leaves(conn, employee_name)       # ①
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail="데이터베이스에 연결할 수 없습니다.") from exc

    return [
        LeaveBalanceResponse(
            id=lb.id, employee_id=lb.employee_id, year=lb.year,
            total_days=lb.total_days, used_days=lb.used_days,
            remaining_days=lb.remaining_days,
        )
        for lb in leaves
    ]


@router.post("/leaves", response_model=LeaveBalanceResponse, status_code=201, summary="연차 생성")
def api_create_leave(body: LeaveBalanceCreate) -> LeaveBalanceResponse:
    """연차 잔여량 레코드를 생성합니다.

    Args:
        body: LeaveBalanceCreate (JSON body)

    Returns:
        생성된 LeaveBalanceResponse (HTTP 201)
    """
    try:
        with get_connection() as conn:
            lb = crud.create_leave_balance(                         # ①
                conn, body.employee_id, body.year,
                body.total_days, body.used_days,
            )
    except psycopg2.errors.UniqueViolation:
        raise HTTPException(
            status_code=409,
            detail=f"직원 ID {body.employee_id}의 {body.year}년 연차 레코드가 이미 존재합니다."
        )
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail="데이터베이스에 연결할 수 없습니다.") from exc

    return LeaveBalanceResponse(
        id=lb.id, employee_id=lb.employee_id, year=lb.year,
        total_days=lb.total_days, used_days=lb.used_days,
        remaining_days=lb.remaining_days,
    )


@router.post("/leaves/usage", response_model=LeaveBalanceResponse, summary="연차 사용 등록")
def api_use_leave(body: LeaveUsageRequest) -> LeaveBalanceResponse:
    """연차 사용량을 누적 등록합니다.

    Args:
        body: LeaveUsageRequest (JSON body) — emp_no + days

    Returns:
        갱신된 LeaveBalanceResponse

    Raises:
        HTTPException 400: 잔여 연차 부족 시
        HTTPException 404: 해당 직원의 연차 레코드가 없을 때
    """
    try:
        with get_connection() as conn:
            lb = crud.update_leave_usage(conn, body.emp_no, body.days)  # ①
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail="데이터베이스에 연결할 수 없습니다.") from exc

    if lb is None:
        raise HTTPException(
            status_code=404,
            detail=f"사번 '{body.emp_no}'의 연차 레코드를 찾을 수 없습니다."
        )

    return LeaveBalanceResponse(
        id=lb.id, employee_id=lb.employee_id, year=lb.year,
        total_days=lb.total_days, used_days=lb.used_days,
        remaining_days=lb.remaining_days,
    )


@router.patch("/leaves/{emp_no}/{year}", response_model=LeaveBalanceResponse, summary="연차 수정")
def api_update_leave(emp_no: str, year: int, body: LeaveBalanceUpdate) -> LeaveBalanceResponse:
    """연차 잔여량을 직접 수정합니다.

    Args:
        emp_no: 직원 사번 (URL 경로)
        year:   대상 연도 (URL 경로)
        body:   LeaveBalanceUpdate (JSON body)

    Returns:
        갱신된 LeaveBalanceResponse

    Raises:
        HTTPException 404: 해당 레코드가 없을 때
    """
    try:
        with get_connection() as conn:
            lb = crud.update_leave_balance(conn, emp_no, year, body.total_days, body.used_days)  # ①
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail="데이터베이스에 연결할 수 없습니다.") from exc

    if lb is None:
        raise HTTPException(status_code=404, detail=f"사번 '{emp_no}'의 {year}년 연차 레코드를 찾을 수 없습니다.")

    return LeaveBalanceResponse(
        id=lb.id, employee_id=lb.employee_id, year=lb.year,
        total_days=lb.total_days, used_days=lb.used_days,
        remaining_days=lb.remaining_days,
    )


# ============================================================
# 매출 API
# ============================================================

@router.get("/sales", response_model=list[SaleResponse], summary="매출 전체 조회")
def api_get_sales(
    dept: Optional[str] = Query(None, description="부서 검색 (부분 일치)"),
    period_start: Optional[str] = Query(None, description="시작일 (YYYY-MM-DD)"),
    period_end: Optional[str] = Query(None, description="종료일 (YYYY-MM-DD)"),
) -> list[SaleResponse]:
    """매출 목록을 JSON으로 반환합니다.

    Args:
        dept:         부서 필터
        period_start: 조회 시작일
        period_end:   조회 종료일

    Returns:
        SaleResponse 리스트
    """
    import datetime

    d_from = datetime.date.fromisoformat(period_start) if period_start else None  # ①
    d_to   = datetime.date.fromisoformat(period_end)   if period_end   else None  # ②

    try:
        with get_connection() as conn:
            sales = crud.get_all_sales(conn, dept, d_from, d_to)   # ③
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail="데이터베이스에 연결할 수 없습니다.") from exc

    return [
        SaleResponse(
            id=s.id, dept=s.dept, sale_date=s.sale_date,
            amount=s.amount, item=s.item,
        )
        for s in sales
    ]


@router.post("/sales", response_model=SaleResponse, status_code=201, summary="매출 등록")
def api_create_sale(body: SaleCreate) -> SaleResponse:
    """매출 기록을 등록합니다.

    Args:
        body: SaleCreate (JSON body)

    Returns:
        등록된 SaleResponse (HTTP 201)
    """
    try:
        with get_connection() as conn:
            sale = crud.create_sale(                                # ①
                conn, body.dept, body.sale_date, body.amount, body.item,
            )
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail="데이터베이스에 연결할 수 없습니다.") from exc

    return SaleResponse(
        id=sale.id, dept=sale.dept, sale_date=sale.sale_date,
        amount=sale.amount, item=sale.item,
    )


@router.get("/sales/dept-summary", response_model=DeptSummaryResponse, summary="부서별 매출 집계")
def api_dept_summary(
    dept: str = Query(..., description="부서명 (부분 일치)"),
) -> DeptSummaryResponse:
    """특정 부서의 누적 매출 합계를 반환합니다.

    Args:
        dept: 부서명 (쿼리 파라미터, 필수)

    Returns:
        DeptSummaryResponse

    Raises:
        HTTPException 404: 해당 부서의 매출 기록이 없을 때
    """
    try:
        with get_connection() as conn:
            summary = crud.get_dept_summary(conn, dept)             # ①
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail="데이터베이스에 연결할 수 없습니다.") from exc

    if summary is None:
        raise HTTPException(
            status_code=404,
            detail=f"'{dept}' 부서의 매출 기록을 찾을 수 없습니다."
        )

    return DeptSummaryResponse(dept=summary.dept, total_amount=summary.total_amount)
