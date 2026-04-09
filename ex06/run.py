import os
import uvicorn

os.environ["TOKENIZERS_PARALLELISM"] = "false"

if __name__ == "__main__":
    from src.db_helper import get_vectorstore
    get_vectorstore()  # 서버 실행 전 문서 임베딩(자동 구축) 선행 처리
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
