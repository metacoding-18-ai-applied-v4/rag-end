from langchain_classic.chains import RetrievalQA
from langchain_chroma import Chroma
from langchain_ollama import OllamaEmbeddings, ChatOllama
from langchain_core.documents import Document
from langchain_core.prompts import PromptTemplate
from rich.console import Console

console = Console()

# 1. 더미 데이터 준비 (검색이 잘 되도록 키워드 보강)
docs = [
    Document(page_content="[인사규정] 신입사원 휴가 및 연차: 신입사원은 입사 후 처음 3년 동안은 법정 연차가 발생하지 않습니다. 대신 매월 1회의 유급 '리프레시 데이'를 휴가로 사용할 수 있습니다.", metadata={"source": "인사규정"}),
    Document(page_content="[보안규정] 업무 보안: 모든 임직원은 회사에서 지급한 승인된 보안 USB만 사용해야 하며, 개인 USB나 외부 저장 매체 사용은 엄격히 금지됩니다.", metadata={"source": "보안규정"}),
    Document(page_content="[복지규정] 식대 지원: 점심 식사는 무제한 법인카드로 지원하며, 저녁 식사는 오후 9시 이후 야근 시에만 사용이 가능합니다.", metadata={"source": "복지규정"}),
]

console.print("문서를 학습(임베딩) 중입니다...")
try:
    # TODO: OllamaEmbeddings(nomic-embed-text)로 임베딩 생성 → Chroma.from_documents로 벡터DB 저장
    # 1. 문서를 숫자 벡터로 변환하는 임베딩 모델 로드
    embeddings = OllamaEmbeddings(model="nomic-embed-text")
    # 2. 문서 3개를 벡터로 변환해서 ChromaDB에 저장
    vectorstore = Chroma.from_documents(documents=docs, embedding=embeddings)

    # TODO: vectorstore.as_retriever로 검색기 생성 (search_kwargs={"k": 3})
    # 3. 질문과 가장 비슷한 문서 3개를 가져오는 검색기 생성
    retriever = vectorstore.as_retriever(search_kwargs={"k": 3})

    # 4. 프롬프트 템플릿
    template = """당신은 회사의 규정에 대해 설명해주는 AI 비서입니다.
아래의 참고 정보를 바탕으로 질문에 답하세요. 반드시 한국어로 답변해야 합니다.

참고 정보: {context}

질문: {question}
답변:"""

    PROMPT = PromptTemplate(
        template=template, input_variables=["context", "question"]
    )

    # TODO: ChatOllama(deepseek-r1:8b) → RetrievalQA.from_chain_type으로 체인 조립
    # 4. LLM 로드
    llm = ChatOllama(model="deepseek-r1:8b", temperature=0)
    # 5. 검색기 + LLM을 체인으로 연결 (검색된 문서를 LLM에 자동 전달)
    qa_chain = RetrievalQA.from_chain_type(
        llm=llm,
        retriever=retriever,
        return_source_documents=True,
        chain_type_kwargs={"prompt": PROMPT}
    )

    question = "신입사원 휴가 규정에 대해 알려줘."
    console.print(f"\n질문: {question}")
    console.print("-" * 30)

    # TODO: qa_chain.invoke로 질문 실행 → 검색된 문서(근거) 출력 → AI 답변 출력
    # 6. 질문 실행 — 검색 + LLM 답변이 한 번에 동작
    result = qa_chain.invoke({"query": question})

    # 7. 어떤 문서를 참고했는지 출처 출력
    console.print("\n--- 검색된 문서(근거) ---")
    for doc in result['source_documents']:
        console.print(f"[{doc.metadata['source']}]: {doc.page_content}")

    # 8. AI 답변 출력
    console.print("\n--- AI 답변 ---")
    console.print(result['result'])

except Exception as e:
    console.print(f"\n에러 발생: {e}")
