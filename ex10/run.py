"""ex10 서버 실행 — PDF 문서 Q&A + 캡처 이미지."""

import logging
import os

import uvicorn

os.environ["TOKENIZERS_PARALLELISM"] = "false"
logging.basicConfig(level=logging.INFO, format="%(levelname)s:%(name)s: %(message)s")

if __name__ == "__main__":
    from src.tools.search_documents import _get_vectorstore
    _get_vectorstore()  # 서버 실행 전 문서 임베딩(자동 구축) 선행 처리
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
