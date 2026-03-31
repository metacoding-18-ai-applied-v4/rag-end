"""샘플 문서·메타데이터 상수 및 환경 설정."""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent.parent
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "jhgan/ko-sroberta-multitask")

# ── 인메모리 샘플 문서 ───────────────────────────────────────────
SAMPLE_DOCUMENTS = [
    "연차유급휴가는 1년 이상 근속한 직원에게 15일이 부여됩니다. 3년 이상 근속 시 매 2년마다 1일씩 추가됩니다.",
    "연차 신청은 사용 예정일 3일 전까지 인사담당자에게 서면으로 제출하고 팀장 승인을 받아야 합니다.",
    "재택근무는 입사 6개월 이상 정규직 직원에 한해 주 2회까지 신청 가능합니다. 팀장 사전 승인이 필요합니다.",
    "출장비는 출장 완료 후 5영업일 이내에 영수증과 함께 경비 정산 시스템에 제출해야 합니다.",
    "성과 평가는 상반기와 하반기에 각 1회 실시하며, 목표달성도 60%, 역량평가 30%, 동료평가 10%입니다.",
    "자기계발비는 연간 50만원 한도로 직무 관련 도서, 온라인 강의, 자격증 취득 비용을 지원합니다.",
    "개인 USB 사용은 원칙적으로 금지되며, IT보안팀 승인 장치만 사용 가능합니다.",
    "신입사원 온보딩은 1주차 오리엔테이션, 2-4주차 부서 적응, 2-3개월차 업무 통합 3단계로 진행됩니다.",
    "퇴직금은 근속 1년 이상 시 계속근로기간 1년에 대해 30일분 평균임금으로 산정하여 지급합니다.",
    "육아휴직은 만 8세 이하 자녀를 둔 직원이 신청할 수 있으며 최대 1년 사용이 가능합니다.",
    "고충처리는 1차 팀장 처리 후 미해결 시 인사팀 고충처리위원회에 서면 신청하며 15일 내 결과를 통보받습니다.",
    "건강검진은 연 1회 전액 회사 부담으로 실시하며, 검진 당일은 유급 처리됩니다.",
]

SAMPLE_METADATAS = [
    {"source": "HR_취업규칙_v1.0.pdf", "section": "3.1"},
    {"source": "HR_취업규칙_v1.0.pdf", "section": "3.2"},
    {"source": "HR_근무규정_v2.1.pdf", "section": "4.1"},
    {"source": "재무_출장규정_v2.0.pdf", "section": "3"},
    {"source": "HR_성과평가지침_v2.0.pdf", "section": "2.1"},
    {"source": "HR_복리후생규정_v3.0.pdf", "section": "6.2"},
    {"source": "IT_보안정책_v3.0.pdf", "section": "5.3"},
    {"source": "HR_온보딩가이드_v1.5.pdf", "section": "2"},
    {"source": "HR_취업규칙_v1.0.pdf", "section": "12"},
    {"source": "HR_복리후생규정_v3.0.pdf", "section": "7"},
    {"source": "HR_취업규칙_v1.0.pdf", "section": "9"},
    {"source": "HR_복리후생규정_v3.0.pdf", "section": "8"},
]
