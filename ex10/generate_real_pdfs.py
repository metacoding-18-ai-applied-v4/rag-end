import os
import urllib.request
from pathlib import Path

# Install reportlab if not exists
try:
    import reportlab
except ImportError:
    import subprocess
    import sys
    subprocess.check_call([sys.executable, "-m", "pip", "install", "reportlab"])

import fitz  # PyMuPDF
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

font_url = "https://github.com/google/fonts/raw/main/ofl/nanumgothic/NanumGothic-Regular.ttf"
font_path = "NanumGothic.ttf"

def ensure_font():
    if not os.path.exists(font_path):
        print("Downloading NanumGothic font...")
        urllib.request.urlretrieve(font_url, font_path)
    pdfmetrics.registerFont(TTFont("NanumGothic", font_path))

BASE_DIR = Path("/Users/nomadlab/Desktop/김주혁/workspace/coding-study/집필에이전트 v2/projects/사내AI비서_v2/code")
SOURCE_DOCS_DIR = BASE_DIR / "ex07" / "data" / "docs"
TARGET_DOCS_DIR = BASE_DIR / "ex10" / "data" / "docs"

def create_extra_pages(filename, output_path):
    c = canvas.Canvas(str(output_path))
    c.setFont("NanumGothic", 12)
    
    if "정보보안서약서" in filename:
        # Page 2
        c.setFont("NanumGothic", 16)
        c.drawString(50, 780, "제 3 조 (비밀유지 의무)")
        c.setFont("NanumGothic", 12)
        c.drawString(50, 750, "1. 본인은 회사에 재직하는 동안은 물론 퇴직 후에도 업무상 알게 된 모든 비밀을")
        c.drawString(50, 730, "   회사의 사전 서면 승인 없이 제3자에게 누설하거나 부당한 목적으로 사용하지 않습니다.")
        c.drawString(50, 700, "2. 회사의 비밀 정보에는 다음 각 호의 사항이 포함되나, 이에 엄격히 국한되지 않습니다.")
        c.drawString(50, 680, "   가. 기술 정보: 소스코드, 시스템 아키텍처, 서버 구성도, 데이터베이스 스키마 등")
        c.drawString(50, 660, "   나. 경영 정보: 사업 계획, 마케팅 전략, 고객 정보, 인사 현황, 재무 데이터 등")
        
        c.setFont("NanumGothic", 16)
        c.drawString(50, 610, "제 4 조 (자료의 반환 및 폐기)")
        c.setFont("NanumGothic", 12)
        c.drawString(50, 580, "본인은 퇴직 시 또는 회사의 반환 요구가 있을 시, 회사의 소유이거나 업무와 관련된")
        c.drawString(50, 560, "모든 유형적 자료(문서, USB, 노트북 등) 및 무형적 자료(이메일, 클라우드 파일 등)를")
        c.drawString(50, 540, "지체 없이 반환하거나 안전하게 폐기할 것을 서약합니다.")
        c.showPage()
        
        # Page 3
        c.setFont("NanumGothic", 16)
        c.drawString(50, 780, "제 5 조 (손해배상 및 책임)")
        c.setFont("NanumGothic", 12)
        c.drawString(50, 750, "1. 본인이 본 서약서의 의무를 위반하여 회사에 손해를 끼친 경우, 민/형사상의 책임을")
        c.drawString(50, 730, "   부담함은 물론 회사에 발생한 직/간접적인 모든 손해를 배상할 것을 동의합니다.")
        c.drawString(50, 700, "2. 본 서약서의 효력은 퇴직 후에도 5년간 유효하게 존속됩니다.")
        
        c.drawString(50, 550, "2024년  11월  1일")
        c.drawString(50, 500, "서약자: __________________ (인)")
        c.showPage()
        
    elif "취업규칙" in filename:
        # Page 2
        c.setFont("NanumGothic", 18)
        c.drawString(50, 780, "제 3 장 근로시간 및 휴게")
        c.setFont("NanumGothic", 16)
        c.drawString(50, 740, "제 12 조 (근로시간)")
        c.setFont("NanumGothic", 12)
        c.drawString(50, 710, "1. 1주간의 근로시간은 휴게시간을 제외하고 40시간으로 한다.")
        c.drawString(50, 690, "2. 1일의 근로시간은 휴게시간을 제외하고 8시간으로 한다.")
        
        c.setFont("NanumGothic", 16)
        c.drawString(50, 640, "제 13 조 (시업 및 종업시간, 휴게시간)")
        c.setFont("NanumGothic", 12)
        c.drawString(50, 610, "1. 시업시간: 09:00")
        c.drawString(50, 590, "2. 종업시간: 18:00")
        c.drawString(50, 570, "3. 휴게시간: 12:00 ~ 13:00 (1시간)")
        c.drawString(50, 540, "※ 단, 업무상 필요에 따라 부서별로 협의하여 시간을 조정할 수 있다.")
        c.showPage()
        
        # Page 3
        c.setFont("NanumGothic", 18)
        c.drawString(50, 780, "제 4 장 휴일 및 휴가")
        c.setFont("NanumGothic", 16)
        c.drawString(50, 740, "제 15 조 (유급휴일)")
        c.setFont("NanumGothic", 12)
        c.drawString(50, 710, "1. 주휴일 (매주 일요일)")
        c.drawString(50, 690, "2. 근로자의 날 (5월 1일)")
        c.drawString(50, 670, "3. 법정공휴일 및 대체공휴일")
        
        c.setFont("NanumGothic", 16)
        c.drawString(50, 620, "제 16 조 (연차 유급휴가)")
        c.setFont("NanumGothic", 12)
        c.drawString(50, 590, "1. 1년간 80퍼센트 이상 출근한 근로자에게 15일의 유급휴가를 부여한다.")
        c.drawString(50, 570, "2. 계속하여 근로한 기간이 1년 미만인 근로자에게는 1개월 개근 시 1일의")
        c.drawString(50, 550, "   유급휴가를 부여한다.")
        c.showPage()
        
    elif "신규서비스" in filename:
        # Page 2
        c.setFont("NanumGothic", 18)
        c.drawString(50, 780, "2. 시장 분석 (Market Analysis)")
        c.setFont("NanumGothic", 16)
        c.drawString(50, 740, "2.1 타겟 고객층 (Target Audience)")
        c.setFont("NanumGothic", 12)
        c.drawString(50, 710, "- 연령대: 25~35세 직장인 및 프리랜서")
        c.drawString(50, 690, "- 주요 니즈: 업무 효율성 증대, AI 기반 자동화 업무 툴")
        
        c.setFont("NanumGothic", 16)
        c.drawString(50, 640, "2.2 경쟁사 분석 (Competitor Analysis)")
        c.setFont("NanumGothic", 12)
        c.drawString(50, 610, "- A사: 시장 점유율 1위, 그러나 UI/UX가 복잡하고 무거움")
        c.drawString(50, 590, "- B사: 가격 경쟁력이 있으나 핵심 기능(문서 요약) 성능이 떨어짐")
        
        c.setFont("NanumGothic", 16)
        c.drawString(50, 540, "2.3 자사 서비스 차별화 포인트 (USP)")
        c.setFont("NanumGothic", 12)
        c.drawString(50, 510, "- 압도적인 한국어 처리 성능 (자체 파인튜닝 모델 적용)")
        c.drawString(50, 490, "- 슬랙/팀즈 등 기존 사내 메신저와의 원클릭 연동 지원")
        c.showPage()
        
        # Page 3
        c.setFont("NanumGothic", 18)
        c.drawString(50, 780, "3. 마케팅 및 런칭 일정 (Timeline)")
        c.setFont("NanumGothic", 16)
        c.drawString(50, 740, "3.1 티징 페이즈 (D-30 ~ D-10)")
        c.setFont("NanumGothic", 12)
        c.drawString(50, 710, "- 랜딩 페이지 오픈 및 사전 예약 이벤트 진행")
        c.drawString(50, 690, "- IT 관련 커뮤니티 및 블로그 대상 시딩(Seeding) 캠페인")
        
        c.setFont("NanumGothic", 16)
        c.drawString(50, 640, "3.2 공식 런칭 (D-Day)")
        c.setFont("NanumGothic", 12)
        c.drawString(50, 610, "- 보도자료 배포 (매체: Tech/비즈니스 분야)")
        c.drawString(50, 590, "- 웨비나 개최: 'AI 시대의 업무 자동화 전략'")
        
        c.setFont("NanumGothic", 16)
        c.drawString(50, 540, "3.3 런칭 후 그로스 페이즈 (D+1 ~ D+30)")
        c.setFont("NanumGothic", 12)
        c.drawString(50, 510, "- 초기 사용자 피드백 수집 및 핫픽스 릴리즈")
        c.drawString(50, 490, "- 레퍼럴(추천) 프로그램 가동으로 바이럴 루프 구축")
        c.showPage()
    else:
        # Default fallback
        c.setFont("NanumGothic", 16)
        c.drawString(50, 780, "상세 내용 - 페이지 2")
        c.setFont("NanumGothic", 12)
        c.drawString(50, 750, "여기에 본문 내용이 포함됩니다.")
        c.showPage()
        
        c.setFont("NanumGothic", 16)
        c.drawString(50, 780, "상세 내용 - 페이지 3")
        c.setFont("NanumGothic", 12)
        c.drawString(50, 750, "여기에 결론 및 요약이 포함됩니다.")
        c.showPage()
        
    c.save()

def process_pdfs():
    ensure_font()
    TARGET_DOCS_DIR.mkdir(parents=True, exist_ok=True)
    
    # 1. source docs iter
    if not SOURCE_DOCS_DIR.exists():
        print(f"Directory {SOURCE_DOCS_DIR} not found.")
        return
        
    for pdf_path in SOURCE_DOCS_DIR.rglob("*.pdf"):
        rel_path = pdf_path.relative_to(SOURCE_DOCS_DIR)
        target_path = TARGET_DOCS_DIR / rel_path
        target_path.parent.mkdir(parents=True, exist_ok=True)
        
        # temp file for extra pages
        temp_extra_pdf = "temp_extra.pdf"
        create_extra_pages(pdf_path.name, temp_extra_pdf)
        
        doc_original = fitz.open(pdf_path)
        doc_extra = fitz.open(temp_extra_pdf)
        
        doc_new = fitz.open()
        
        # insert page 1
        if len(doc_original) >= 1:
            doc_new.insert_pdf(doc_original, from_page=0, to_page=0)
        
        # insert extra pages
        doc_new.insert_pdf(doc_extra)
        
        doc_new.save(target_path)
        
        doc_new.close()
        doc_original.close()
        doc_extra.close()
        if os.path.exists(temp_extra_pdf):
            os.remove(temp_extra_pdf)
            
        print(f"Processed with real content: {target_path}")

if __name__ == '__main__':
    process_pdfs()
