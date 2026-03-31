-- ============================================================
-- 사내 AI 비서 ex02 -- 데이터베이스 스키마 및 시드 데이터
-- PostgreSQL 16
-- ============================================================

-- 기존 테이블 삭제 (재실행 안전)
DROP TABLE IF EXISTS sales CASCADE;
DROP TABLE IF EXISTS leave_balance CASCADE;
DROP TABLE IF EXISTS employee CASCADE;

-- ============================================================
-- 1. 직원 테이블 (employee)
-- ============================================================
CREATE TABLE employee (
    id          SERIAL PRIMARY KEY,
    emp_no      VARCHAR(10)  NOT NULL UNIQUE,   -- 사번
    name        VARCHAR(50)  NOT NULL,           -- 이름
    dept        VARCHAR(50)  NOT NULL,           -- 부서
    position    VARCHAR(50)  NOT NULL,           -- 직급
    hire_date   DATE         NOT NULL            -- 입사일
);

COMMENT ON TABLE  employee             IS '직원 기본 정보';
COMMENT ON COLUMN employee.emp_no      IS '사번 (예: EMP001)';
COMMENT ON COLUMN employee.name        IS '직원 이름';
COMMENT ON COLUMN employee.dept        IS '소속 부서';
COMMENT ON COLUMN employee.position    IS '직급 (예: 사원, 대리, 과장)';
COMMENT ON COLUMN employee.hire_date   IS '입사일';

-- ============================================================
-- 2. 휴가 잔여량 테이블 (leave_balance)
-- ============================================================
CREATE TABLE leave_balance (
    id              SERIAL  PRIMARY KEY,
    employee_id     INTEGER NOT NULL REFERENCES employee(id) ON DELETE CASCADE,
    year            INTEGER NOT NULL,            -- 연도
    total_days      NUMERIC(4,1) NOT NULL,       -- 총 연차
    used_days       NUMERIC(4,1) NOT NULL DEFAULT 0,  -- 사용 연차
    remaining_days  NUMERIC(4,1) GENERATED ALWAYS AS (total_days - used_days) STORED,  -- 잔여 연차
    UNIQUE (employee_id, year)
);

COMMENT ON TABLE  leave_balance                IS '연차 잔여량';
COMMENT ON COLUMN leave_balance.total_days     IS '연간 총 연차 일수';
COMMENT ON COLUMN leave_balance.used_days      IS '사용한 연차 일수';
COMMENT ON COLUMN leave_balance.remaining_days IS '잔여 연차 (자동 계산)';

-- ============================================================
-- 3. 매출 테이블 (sales)
-- ============================================================
CREATE TABLE sales (
    id          SERIAL PRIMARY KEY,
    dept        VARCHAR(50)  NOT NULL,           -- 부서
    sale_date   DATE         NOT NULL,           -- 매출 일자
    amount      BIGINT       NOT NULL,           -- 금액 (원)
    item        VARCHAR(200) NOT NULL            -- 매출 항목
);

COMMENT ON TABLE  sales            IS '부서별 매출 기록';
COMMENT ON COLUMN sales.dept       IS '매출 발생 부서';
COMMENT ON COLUMN sales.sale_date  IS '매출 발생 일자';
COMMENT ON COLUMN sales.amount     IS '매출 금액 (원 단위)';
COMMENT ON COLUMN sales.item       IS '매출 항목 / 설명';

-- ============================================================
-- 시드 데이터 -- 직원 5명
-- ============================================================
INSERT INTO employee (emp_no, name, dept, position, hire_date) VALUES
    ('EMP001', '김민준', '개발팀',   '과장',   '2019-03-02'),
    ('EMP002', '이서연', '영업팀',   '대리',   '2021-07-12'),
    ('EMP003', '박지호', '인사팀',   '사원',   '2023-01-09'),
    ('EMP004', '최유나', '마케팅팀', '차장',   '2016-11-01'),
    ('EMP005', '정도현', '개발팀',   '사원',   '2024-02-26');

-- ============================================================
-- 시드 데이터 -- 연차 잔여량 (2025년)
-- ============================================================
INSERT INTO leave_balance (employee_id, year, total_days, used_days) VALUES
    (1, 2025, 15.0, 5.0),
    (2, 2025, 15.0, 3.0),
    (3, 2025, 11.0, 0.0),
    (4, 2025, 15.0, 10.0),
    (5, 2025,  8.0, 0.0);

-- ============================================================
-- 시드 데이터 -- 매출 10건 (2025년)
-- ============================================================
INSERT INTO sales (dept, sale_date, amount, item) VALUES
    ('영업팀',   '2025-01-05',  8500000, '신규 계약 A사'),
    ('영업팀',   '2025-01-20',  3200000, '유지보수 B사'),
    ('개발팀',   '2025-02-10', 12000000, '솔루션 개발 C사'),
    ('마케팅팀', '2025-02-14',  1500000, '광고 캠페인 집행'),
    ('영업팀',   '2025-03-01',  9800000, '신규 계약 D사'),
    ('개발팀',   '2025-03-15',  6700000, '커스터마이징 E사'),
    ('마케팅팀', '2025-04-02',  2300000, '콘텐츠 마케팅'),
    ('영업팀',   '2025-04-18',  4100000, '재계약 F사'),
    ('인사팀',   '2025-05-01',   850000, '교육 프로그램 운영'),
    ('개발팀',   '2025-05-20', 15000000, '플랫폼 구축 G사');
