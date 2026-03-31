"""
Pydantic 스키마 모듈.

FastAPI의 요청(Request) / 응답(Response) 데이터 검증을 위한
Pydantic 모델을 정의합니다.
"""

from datetime import date
from typing import Optional

from pydantic import BaseModel, Field


# ============================================================
# 직원 (Employee) 스키마
# ============================================================

class EmployeeCreate(BaseModel):
    """직원 등록 요청 스키마 (사번은 서버에서 자동 생성)."""

    name:      str  = Field(..., description="직원 이름",         max_length=50)
    dept:      str  = Field(..., description="소속 부서",         max_length=50)
    position:  str  = Field(..., description="직급",             max_length=50)
    hire_date: date = Field(..., description="입사일 (YYYY-MM-DD)")


class EmployeeUpdate(BaseModel):
    """직원 수정 요청 스키마 (모든 필드 선택)."""

    name:      Optional[str]  = Field(None, description="직원 이름 (미입력 시 유지)")
    dept:      Optional[str]  = Field(None, description="소속 부서 (미입력 시 유지)")
    position:  Optional[str]  = Field(None, description="직급     (미입력 시 유지)")
    hire_date: Optional[date] = Field(None, description="입사일   (미입력 시 유지)")


class EmployeeResponse(BaseModel):
    """직원 응답 스키마."""

    id:        int
    emp_no:    str
    name:      str
    dept:      str
    position:  str
    hire_date: date

    class Config:
        from_attributes = True


# ============================================================
# 연차 (LeaveBalance) 스키마
# ============================================================

class LeaveBalanceCreate(BaseModel):
    """연차 잔여량 생성 요청 스키마."""

    employee_id: int   = Field(..., description="직원 ID")
    year:        int   = Field(..., description="연도 (예: 2025)")
    total_days:  float = Field(..., description="총 연차 일수",   ge=0)
    used_days:   float = Field(0.0, description="사용 연차 일수", ge=0)


class LeaveBalanceUpdate(BaseModel):
    """연차 정보 수정 요청 스키마."""

    total_days: Optional[float] = Field(None, description="총 연차 일수",   ge=0)
    used_days:  Optional[float] = Field(None, description="사용 연차 일수", ge=0)


class LeaveUsageRequest(BaseModel):
    """연차 사용 등록 요청 스키마 (사용 일수 누적)."""

    emp_no: str   = Field(..., description="직원 사번 (예: EMP001)")
    days:   float = Field(..., description="사용할 일수",    gt=0)


class LeaveBalanceResponse(BaseModel):
    """연차 잔여량 응답 스키마."""

    id:             int
    employee_id:    int
    year:           int
    total_days:     float
    used_days:      float
    remaining_days: float

    class Config:
        from_attributes = True


# ============================================================
# 매출 (Sale) 스키마
# ============================================================

class SaleCreate(BaseModel):
    """매출 등록 요청 스키마."""

    dept:      str  = Field(..., description="매출 부서",   max_length=50)
    sale_date: date = Field(..., description="매출 일자")
    amount:    int  = Field(..., description="금액 (원)",   gt=0)
    item:      str  = Field(..., description="매출 항목",   max_length=200)


class SaleResponse(BaseModel):
    """매출 응답 스키마."""

    id:        int
    dept:      str
    sale_date: date
    amount:    int
    item:      str

    class Config:
        from_attributes = True


class DeptSummaryResponse(BaseModel):
    """부서별 매출 집계 응답 스키마."""

    dept:         str
    total_amount: int
