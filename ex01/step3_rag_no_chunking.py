from langchain_classic.chains import RetrievalQA
from langchain_chroma import Chroma
from langchain_ollama import OllamaEmbeddings, ChatOllama
from langchain_core.documents import Document
from langchain_core.prompts import PromptTemplate
from rich.console import Console

console = Console()

# 1. 청킹 미적용: 모든 텍스트를 하나의 문자열로 합침 (통짜 데이터)
context_all = """
[인사규정] 신입사원 휴가 및 연차: 신입사원은 입사 후 처음 3년 동안은 법정 연차가 발생하지 않습니다. 대신 매월 1회의 유급 '리프레시 데이'를 휴가로 사용할 수 있습니다.
[보안규정] 업무 보안: 모든 임직원은 회사에서 지급한 승인된 보안 USB만 사용해야 하며, 개인 USB나 외부 저장 매체 사용은 엄격히 금지됩니다.
[복지규정] 식대 지원: 점심 식사는 무제한 법인카드로 지원하며, 저녁 식사는 오후 9시 이후 야근 시에만 사용이 가능합니다.
"""

# 하나의 거대한 문서로 만듦 -> 검색이 비효율적임
docs_bad = [Document(page_content=context_all, metadata={"source": "전체규정"})]

# 2. VectorDB 생성
console.print("문서를 학습(임베딩) 중입니다... (청킹 미적용)")
try:
    embeddings = OllamaEmbeddings(model="nomic-embed-text")
    vectorstore = Chroma.from_documents(documents=docs_bad, embedding=embeddings)

    # 3. 검색기 및 프롬프트 설정 (통째로 하나뿐이므로 k=1로 검색해도 전체가 다 나옴)
    retriever = vectorstore.as_retriever(search_kwargs={"k": 1})

    template = """당신은 회사의 규정에 대해 설명해주는 AI 비서입니다.
아래의 참고 정보를 바탕으로 질문에 답하세요. 반드시 한국어로 답변해야 합니다.

참고 정보: {context}

질문: {question}
답변:"""
    PROMPT = PromptTemplate(template=template, input_variables=["context", "question"])

    # 4. RAG 체인 실행
    llm = ChatOllama(model="deepseek-r1:8b", temperature=0)
    qa_chain = RetrievalQA.from_chain_type(
        llm=llm,
        retriever=retriever,
        chain_type_kwargs={"prompt": PROMPT},
        return_source_documents=True
    )

    question = "신입사원 휴가 규정에 대해 알려줘."
    console.print(f"\n질문: {question}")
    console.print("-" * 30)

    result = qa_chain.invoke({"query": question})
    console.print(f"\nAI 답변:\n{result['result']}")

except Exception as e:
    console.print(f"\n에러 발생: {e}")
