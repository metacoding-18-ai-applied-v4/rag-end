import fitz
import os
from pathlib import Path
import urllib.request

font_url = "https://github.com/google/fonts/raw/main/ofl/nanumgothic/NanumGothic-Regular.ttf"
font_path = "NanumGothic.ttf"

if not os.path.exists(font_path):
    print("Downloading NanumGothic font...")
    urllib.request.urlretrieve(font_url, font_path)

BASE_DIR = Path("/Users/nomadlab/Desktop/김주혁/workspace/coding-study/집필에이전트 v2/projects/사내AI비서_v2/code")
SOURCE_DOCS_DIR = BASE_DIR / "ex07" / "data" / "docs"
TARGET_DOCS_DIR = BASE_DIR / "ex10" / "data" / "docs"

def insert_korean_text(page, point, text, fontsize=12, bold=False):
    # PyMuPDF insert_text does not fully support OTF/TTF natively without Font objects,
    # but we can insert a font into the doc and use it.
    # Actually insert_font is needed.
    fontname = "F0"
    page.insert_font(fontname=fontname, fontfile=font_path)
    page.insert_text(point, text, fontname=fontname, fontsize=fontsize, color=(0,0,0))

def sync_format():
    if not SOURCE_DOCS_DIR.exists():
        return
        
    for pdf_path in SOURCE_DOCS_DIR.rglob("*.pdf"):
        doc = fitz.open(pdf_path)
        if len(doc) == 0:
            doc.close()
            continue
            
        page1 = doc[0]
        rect_width = page1.rect.width
        rect_height = page1.rect.height
        
        target_path = TARGET_DOCS_DIR / pdf_path.relative_to(SOURCE_DOCS_DIR)
        
        # We will create a new doc, copy page 1 three times, and modify page 2 and 3
        new_doc = fitz.open()
        
        # P1
        new_doc.insert_pdf(doc, from_page=0, to_page=0)
        # P2
        new_doc.insert_pdf(doc, from_page=0, to_page=0)
        # P3
        new_doc.insert_pdf(doc, from_page=0, to_page=0)
        
        p2 = new_doc[1]
        p3 = new_doc[2]
        
        # Clear main content areas by drawing white boxes
        if "정보보안서약서" in pdf_path.name:
            # clear rect
            p2.draw_rect(fitz.Rect(40, 100, rect_width - 40, rect_height - 100), color=(1,1,1), fill=(1,1,1))
            p3.draw_rect(fitz.Rect(40, 100, rect_width - 40, rect_height - 100), color=(1,1,1), fill=(1,1,1))
            
            # P2 text
            insert_korean_text(p2, (50, 130), "제 3 조 (비밀유지 의무)", fontsize=16)
            insert_korean_text(p2, (50, 160), "1. 본인은 회사에 재직하는 동안은 물론 퇴직 후에도 업무상 알게 된 모든 비밀을")
            insert_korean_text(p2, (50, 180), "   회사의 사전 서면 승인 없이 제3자에게 누설하거나 부당한 목적으로 사용하지 않습니다.")
            insert_korean_text(p2, (50, 210), "2. 회사의 비밀 정보에는 다음 각 호의 사항이 포함되나, 이에 엄격히 국한되지 않습니다.")
            insert_korean_text(p2, (50, 230), "   가. 기술 정보: 소스코드, 시스템 아키텍처, 서버 구성도, 데이터베이스 스키마 등")
            insert_korean_text(p2, (50, 250), "   나. 경영 정보: 사업 계획, 마케팅 전략, 고객 정보, 인사 현황, 재무 데이터 등")
            
            insert_korean_text(p2, (50, 300), "제 4 조 (자료의 반환 및 폐기)", fontsize=16)
            insert_korean_text(p2, (50, 330), "본인은 퇴직 시 또는 회사의 반환 요구가 있을 시, 회사의 소유이거나 업무와 관련된")
            insert_korean_text(p2, (50, 350), "모든 유형적 자료(문서, USB, 노트북 등) 및 무형적 자료(이메일, 클라우드 파일 등)를")
            insert_korean_text(p2, (50, 370), "지체 없이 반환하거나 안전하게 폐기할 것을 서약합니다.")
            
            # P3 text
            insert_korean_text(p3, (50, 130), "제 5 조 (손해배상 및 책임)", fontsize=16)
            insert_korean_text(p3, (50, 160), "1. 본인이 본 서약서의 의무를 위반하여 회사에 손해를 끼친 경우, 민/형사상의 책임을")
            insert_korean_text(p3, (50, 180), "   부담함은 물론 회사에 발생한 직/간접적인 모든 손해를 배상할 것을 동의합니다.")
            insert_korean_text(p3, (50, 210), "2. 본 서약서의 효력은 퇴직 후에도 5년간 유효하게 존속됩니다.")
            insert_korean_text(p3, (50, 350), "2024년  11월  1일")
            insert_korean_text(p3, (50, 400), "서약자: __________________ (인)")
            
        elif "취업규칙" in pdf_path.name:
            p2.draw_rect(fitz.Rect(50, 110, rect_width - 50, rect_height - 100), color=(1,1,1), fill=(1,1,1))
            p3.draw_rect(fitz.Rect(50, 110, rect_width - 50, rect_height - 100), color=(1,1,1), fill=(1,1,1))
            
            insert_korean_text(p2, (60, 140), "제 3 장 근로시간 및 휴게", fontsize=18)
            insert_korean_text(p2, (60, 180), "제 12 조 (근로시간)", fontsize=16)
            insert_korean_text(p2, (60, 210), "1. 1주간의 근로시간은 휴게시간을 제외하고 40시간으로 한다.")
            insert_korean_text(p2, (60, 230), "2. 1일의 근로시간은 휴게시간을 제외하고 8시간으로 한다.")
            
            insert_korean_text(p2, (60, 280), "제 13 조 (시업 및 종업시간, 휴게시간)", fontsize=16)
            insert_korean_text(p2, (60, 310), "1. 시업시간: 09:00")
            insert_korean_text(p2, (60, 330), "2. 종업시간: 18:00")
            insert_korean_text(p2, (60, 350), "3. 휴게시간: 12:00 ~ 13:00 (1시간)")
            insert_korean_text(p2, (60, 380), "※ 단, 업무상 필요에 따라 부서별로 협의하여 시간을 조정할 수 있다.")
            
            insert_korean_text(p3, (60, 140), "제 4 장 휴일 및 휴가", fontsize=18)
            insert_korean_text(p3, (60, 180), "제 15 조 (유급휴일)", fontsize=16)
            insert_korean_text(p3, (60, 210), "1. 주휴일 (매주 일요일)")
            insert_korean_text(p3, (60, 230), "2. 근로자의 날 (5월 1일)")
            insert_korean_text(p3, (60, 250), "3. 법정공휴일 및 대체공휴일")
            
            insert_korean_text(p3, (60, 300), "제 16 조 (연차 유급휴가)", fontsize=16)
            insert_korean_text(p3, (60, 330), "1. 1년간 80퍼센트 이상 출근한 근로자에게 15일의 유급휴가를 부여한다.")
            insert_korean_text(p3, (60, 350), "2. 계속하여 근로한 기간이 1년 미만인 근로자에게는 1개월 개근 시 1일의")
            insert_korean_text(p3, (60, 370), "   유급휴가를 부여한다.")
            
        elif "신규서비스" in pdf_path.name: # Landscape one
            p2.draw_rect(fitz.Rect(30, 90, rect_width - 30, rect_height - 90), color=(1,1,1), fill=(1,1,1))
            p3.draw_rect(fitz.Rect(30, 90, rect_width - 30, rect_height - 90), color=(1,1,1), fill=(1,1,1))
            
            insert_korean_text(p2, (40, 120), "2. 시장 분석 (Market Analysis)", fontsize=18)
            insert_korean_text(p2, (40, 160), "2.1 타겟 고객층 (Target Audience)", fontsize=16)
            insert_korean_text(p2, (40, 190), "- 연령대: 25~35세 직장인 및 프리랜서")
            insert_korean_text(p2, (40, 210), "- 주요 니즈: 업무 효율성 증대, AI 기반 자동화 업무 툴")
            
            insert_korean_text(p2, (40, 260), "2.2 경쟁사 분석 (Competitor Analysis)", fontsize=16)
            insert_korean_text(p2, (40, 290), "- A사: 시장 점유율 1위, 그러나 UI/UX가 복잡하고 무거움")
            insert_korean_text(p2, (40, 310), "- B사: 가격 경쟁력이 있으나 핵심 기능(문서 요약) 성능이 떨어짐")
            
            insert_korean_text(p2, (40, 360), "2.3 자사 서비스 차별화 포인트 (USP)", fontsize=16)
            insert_korean_text(p2, (40, 390), "- 압도적인 한국어 처리 성능 (자체 파인튜닝 모델 적용)")
            insert_korean_text(p2, (40, 410), "- 슬랙/팀즈 등 기존 사내 메신저와의 원클릭 연동 지원")
            
            insert_korean_text(p3, (40, 120), "3. 마케팅 및 런칭 일정 (Timeline)", fontsize=18)
            insert_korean_text(p3, (40, 160), "3.1 티징 페이즈 (D-30 ~ D-10)", fontsize=16)
            insert_korean_text(p3, (40, 190), "- 랜딩 페이지 오픈 및 사전 예약 이벤트 진행")
            insert_korean_text(p3, (40, 210), "- IT 관련 커뮤니티 및 블로그 대상 시딩(Seeding) 캠페인")
            
            insert_korean_text(p3, (40, 260), "3.2 공식 런칭 (D-Day)", fontsize=16)
            insert_korean_text(p3, (40, 290), "- 보도자료 배포 (매체: Tech/비즈니스 분야)")
            insert_korean_text(p3, (40, 310), "- 웨비나 개최: 'AI 시대의 업무 자동화 전략'")
            
            insert_korean_text(p3, (40, 360), "3.3 런칭 후 그로스 페이즈 (D+1 ~ D+30)", fontsize=16)
            insert_korean_text(p3, (40, 390), "- 초기 사용자 피드백 수집 및 핫픽스 릴리즈")
            insert_korean_text(p3, (40, 410), "- 레퍼럴(추천) 프로그램 가동으로 바이럴 루프 구축")
        
        # Rewrite Page 2, Page 3 Footer string if exists
        # Actually it's simpler to just not overwrite the footer in the rectangle! 
        # (I left bottom ~100px un-cleared so the original Page 1 footer is visible on Page 2 and 3)
        # But we can try to draw over "Page 1 / 2" if we really want to, or just leave it. 
        # Leaving the footer is totally fine and shows the exact same layout.
        
        new_doc.save(target_path)
        new_doc.close()
        doc.close()
        print("Format Synced:", target_path)

if __name__ == "__main__":
    sync_format()
