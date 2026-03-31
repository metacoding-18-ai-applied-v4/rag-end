"""ex07 — 에이전트 인프라 헬퍼."""

import logging
import os

logger = logging.getLogger(__name__)


def build_rag_chain(llm):
    """LangChain LCEL 기반 RAG 체인을 구성합니다."""
    chroma_dir = os.getenv("CHROMA_PERSIST_DIR", "./data/chroma_db")
    embedding_model = os.getenv("EMBEDDING_MODEL", "jhgan/ko-sroberta-multitask")

    try:
        import chromadb
        from langchain_chroma import Chroma
        from langchain_community.embeddings import HuggingFaceEmbeddings
        from langchain_core.output_parsers import StrOutputParser
        from langchain_core.runnables import RunnablePassthrough

        # ① 임베딩 모델 초기화
        embeddings = HuggingFaceEmbeddings(model_name=embedding_model)

        # ② ChromaDB 벡터스토어 연결
        collection_name = os.getenv("CHROMA_COLLECTION_NAME", "metacoding_documents")
        vectorstore = Chroma(
            persist_directory=chroma_dir,
            embedding_function=embeddings,
            collection_name=collection_name,
        )
        retriever = vectorstore.as_retriever(search_kwargs={"k": 5})

        # ③ RAG 프롬프트 정의
        from langchain_core.prompts import ChatPromptTemplate as PromptTemplate

        rag_prompt = PromptTemplate.from_template(
            """다음 참고 문서를 바탕으로 질문에 답변하십시오.
모르는 내용은 "해당 내용을 문서에서 찾을 수 없습니다."라고 답변하십시오.
반드시 출처(source)를 함께 표시하십시오.

[참고 문서]
{context}

[질문]
{question}

[답변]"""
        )

        def format_docs(docs):
            return "\n\n".join(
                f"[출처: {doc.metadata.get('source', '알 수 없음')}]\n{doc.page_content}"
                for doc in docs
            )

        # ④ LCEL 파이프라인 구성
        rag_chain = (
            {"context": retriever | format_docs, "question": RunnablePassthrough()}
            | rag_prompt
            | llm
            | StrOutputParser()
        )

        logger.info("[agent_helpers] RAG 체인 구성 완료 (ChromaDB: %s)", chroma_dir)
        return rag_chain

    except Exception as exc:
        logger.warning(
            "[agent_helpers] RAG 체인 구성 실패 (search_documents 도구로 대체): %s", exc
        )
        return None


def classify_route(query, router=None):
    """QueryRouter를 활용하여 라우팅 경로를 결정합니다."""
    if router is not None:
        raw_route = router.classify_query(query)
        route_map = {"structured": "db", "unstructured": "rag", "hybrid": "agent"}
        route = route_map.get(raw_route, "agent")
    else:
        # QueryRouter 미사용 시 키워드 기반 폴백
        query_lower = query.lower()
        db_keywords = ["직원", "부서", "목록", "매출", "실적", "합계", "휴가 잔여", "남은 휴가", "연차 잔여"]
        rag_keywords = ["규정", "정책", "절차", "가이드", "어떻게", "방법", "온보딩", "보안"]
        db_score = sum(1 for kw in db_keywords if kw in query_lower)
        rag_score = sum(1 for kw in rag_keywords if kw in query_lower)
        if db_score > 0 and rag_score == 0:
            route = "db"
        elif rag_score > 0 and db_score == 0:
            route = "rag"
        else:
            route = "agent"

    logger.info("[Router] 쿼리 분류 완료: route=%s", route)
    return route
