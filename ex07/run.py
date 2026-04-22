import logging
import os
import uvicorn

from src._rich_logging import setup_rich_logging

os.environ["TOKENIZERS_PARALLELISM"] = "false"
setup_rich_logging(level=logging.INFO)

if __name__ == "__main__":
    from src.tools.search_documents import _get_vectorstore
    _get_vectorstore()  # 서버 실행 전 문서 임베딩(자동 구축) 선행 처리
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
