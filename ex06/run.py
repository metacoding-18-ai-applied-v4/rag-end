import os
import uvicorn

os.environ["TOKENIZERS_PARALLELISM"] = "false"

if __name__ == "__main__":
    from src.db_helper import get_vectorstore
    # TODO: 서버 실행 전 문서 임베딩(자동 구축)을 선행 처리한다
    get_vectorstore()  # 서버 실행 전 문서 임베딩(자동 구축) 선행 처리
    # TODO: uvicorn으로 FastAPI 앱을 실행한다 (host="0.0.0.0", port=8000)
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
