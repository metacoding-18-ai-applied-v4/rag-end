import os
from pathlib import Path

# PyMuPDF 및 Pillow 임포트
try:
    import fitz  # PyMuPDF
    from PIL import Image, ImageEnhance, ImageFilter, ImageOps
except ImportError as e:
    import builtins
    print(f"Required package not found: {e}. Please 'pip install PyMuPDF Pillow'.")
    exit(1)

BASE_DIR = Path(__file__).resolve().parent.parent
TARGET_DOCS_DIR = BASE_DIR / "ex10" / "data" / "docs"

def add_scan_effect(img):
    # 스캔 문서 느낌을 위해 흑백(Grayscale) 변환
    img_gray = img.convert("L")
    
    # 약간의 가우시안 블러 추가 (인쇄/스캔 디테일 뭉개짐)
    img_blur = img_gray.filter(ImageFilter.GaussianBlur(radius=0.5))
    
    # 대비를 조금 낮추고 밝기를 올려서 실제 스캔본의 흐릿한 회색 톤 재현
    enhancer = ImageEnhance.Contrast(img_blur)
    img_contrast = enhancer.enhance(1.5)
    
    enhancer_bright = ImageEnhance.Brightness(img_contrast)
    img_bright = enhancer_bright.enhance(0.95)
    
    return img_bright

def make_pdf_scanned_look(pdf_path):
    print(f"Processing: {pdf_path}")
    doc = fitz.open(pdf_path)
    temp_imgs = []
    
    # 전체 페이지를 이미지(스캔본) 형태로 변환
    for page_num in range(len(doc)):
        page = doc.load_page(page_num)
        
        # 스캔 품질 재현을 위해 150 DPI 정도로 렌더링 (Matrix 2, 2 = 144 DPI)
        pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        
        # 스캔 품질 효과 반영
        img_scanned = add_scan_effect(img)
        
        # 임시 이미지로 저장 (품질을 약간 낮춰서 JPEG 노이즈 추가)
        temp_img_path = str(pdf_path.parent / f"temp_{pdf_path.stem}_{page_num}.jpeg")
        img_scanned.save(temp_img_path, format="JPEG", quality=65)
        temp_imgs.append(temp_img_path)

    doc.close()
    
    # 기존 파일 삭제 후 이미지 기반의 새 PDF 병합 생성
    os.remove(pdf_path)
    
    new_doc = fitz.open()
    for img_path in temp_imgs:
        # 이미지를 PDF 페이지로 변환
        img_doc = fitz.open(img_path)
        pdf_bytes = img_doc.convert_to_pdf()
        pdf_img_doc = fitz.open("pdf", pdf_bytes)
        new_doc.insert_pdf(pdf_img_doc)
        
        # 자원 정리
        img_doc.close()
        pdf_img_doc.close()
        os.remove(img_path)
        
    new_doc.save(pdf_path)
    new_doc.close()
    print(f"Scanned effect applied to: {pdf_path}")

def process_all_pdfs():
    if not TARGET_DOCS_DIR.exists():
        print(f"Directory {TARGET_DOCS_DIR} not found.")
        return
        
    for pdf_path in TARGET_DOCS_DIR.rglob("*.pdf"):
        make_pdf_scanned_look(pdf_path)

if __name__ == '__main__':
    process_all_pdfs()
