import os
import shutil
from pathlib import Path
import fitz  # PyMuPDF

BASE_DIR = Path(__file__).resolve().parent.parent
SOURCE_DOCS_DIR = BASE_DIR / "ex07" / "data" / "docs"
TARGET_DOCS_DIR = BASE_DIR / "ex10" / "data" / "docs"

def extend_pdf_pages():
    if not SOURCE_DOCS_DIR.exists():
        print(f"Source dir {SOURCE_DOCS_DIR} does not exist.")
        return

    for pdf_path in SOURCE_DOCS_DIR.rglob("*.pdf"):
        # Create corresponding target path
        rel_path = pdf_path.relative_to(SOURCE_DOCS_DIR)
        target_path = TARGET_DOCS_DIR / rel_path
        
        target_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Open source PDF
        try:
            doc = fitz.open(pdf_path)
            
            # Create a new document to hold the pages
            new_doc = fitz.open()
            
            # Take only the first page and duplicate to make 3 pages
            if len(doc) >= 1:
                # Get the first page
                page1 = doc[0]
                
                # Copy page 1 to new doc
                new_doc.insert_pdf(doc, from_page=0, to_page=0)
                
                # Duplicate page 1 twice (for page 2 and page 3)
                for i in range(2):
                    new_doc.insert_pdf(doc, from_page=0, to_page=0)
                    # Add some text to indicate the page number
                    page_idx = i + 1  # 0-based for new_doc, so page 1 and page 2 are the duplicated ones
                    page = new_doc[page_idx]
                    
                    # Draw text at the top center
                    rect = page.rect
                    text = f"- {page_idx + 1} -"
                    point = fitz.Point(rect.width / 2 - 20, 30)
                    page.insert_text(point, text, fontsize=12, color=(0,0,0))
            
            # Save the new document
            new_doc.save(target_path)
            new_doc.close()
            doc.close()
            print(f"Processed: {target_path}")
            
        except Exception as e:
            print(f"Error processing {pdf_path}: {e}")

if __name__ == "__main__":
    extend_pdf_pages()
