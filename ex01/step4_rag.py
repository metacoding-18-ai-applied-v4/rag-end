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

# 2. VectorDB 생성
console.print("문서를 학습(임베딩) 중입니다...")
try:
    embeddings = OllamaEmbeddings(model="nomic-embed-text")
    vectorstore = Chroma.from_documents(
        documents=docs,
        embedding=embeddings
    )

    # 3. 검색기(Retriever) 설정
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

    # 5. RAG 체인 연결
    llm = ChatOllama(model="deepseek-r1:8b", temperature=0)
    qa_chain = RetrievalQA.from_chain_type(
        llm=llm,
        retriever=retriever,
        return_source_documents=True,
        chain_type_kwargs={"prompt": PROMPT}
    )

    # 6. 질문하기 — 추론이 필요한 복잡한 질문
    question = "입사 6개월차 신입인데 리프레시 데이 2번 썼어. 몇 번 남았는지 규정 기반으로 계산해줘."
    console.print(f"\n질문: {question}")
    console.print("-" * 30)

    result = qa_chain.invoke({"query": question})

    console.print("\n--- 검색된 문서(근거) ---")
    for doc in result['source_documents']:
        console.print(f"[{doc.metadata['source']}]: {doc.page_content}")

    console.print("\n--- AI 답변 ---")
    console.print(result['result'])

except Exception as e:
    console.print(f"\n에러 발생: {e}")
