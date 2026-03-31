"""
데이터 모델 모듈.

PostgreSQL 테이블 행(row)을 Python dataclass로 표현합니다.
dataclass는 ORM 없이도 타입 힌트와 구조를 명확히 합니다.
"""

from dataclasses import dataclass
from datetime import date
from typing import Optional


# ------------------------------------------------------------------
# [OUTPUT] 도메인 모델 (DB 행 → Python 객체)
# ------------------------------------------------------------------

@dataclass
class Employee:
    """직원 정보 모델.

    Attributes:
        id: 자동 증가 PK
        emp_no: 사번 (예: EMP001)
        name: 직원 이름
        dept: 소속 부서
        position: 직급
        hire_date: 입사일
    """
    id: int
    emp_no: str
    name: str
    dept: str
    position: str
    hire_date: date


@dataclass
class LeaveBalance:
    """연차 잔여량 모델.

    Attributes:
        id: 자동 증가 PK
        employee_id: 직원 FK
        year: 연도
        total_days: 총 연차 일수
        used_days: 사용 연차 일수
        remaining_days: 잔여 연차 (DB 계산 컬럼)
        name: 직원 이름 (JOIN 결과, 선택)
    """
    id: int
    employee_id: int
    year: int
    total_days: float
    used_days: float
    remaining_days: float
    name: Optional[str] = None
    emp_no: Optional[str] = None


@dataclass
class Sale:
    """매출 기록 모델.

    Attributes:
        id: 자동 증가 PK
        dept: 매출 발생 부서
        sale_date: 매출 일자
        amount: 금액 (원)
        item: 매출 항목
    """
    id: int
    dept: str
    sale_date: date
    amount: int
    item: str


@dataclass
class DeptSummary:
    """부서별 매출 집계 모델.

    Attributes:
        dept: 부서명
        total_amount: 합계 금액 (원)
    """
    dept: str
    total_amount: int
