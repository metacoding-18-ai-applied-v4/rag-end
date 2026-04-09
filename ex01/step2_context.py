from langchain_ollama import ChatOllama
from rich.console import Console

console = Console()
# 1. step1과 동일하게 LLM 로드
llm = ChatOllama(model="deepseek-r1:8b", temperature=0)

# 정보를 변수에 담습니다 (아직 DB 안 씀)
context_data = """
[커넥트 취업규칙]
1. 신입사원은 입사 후 3년 동안은 연차가 없다. (파격적인 규정)
2. 대신 매월 1회 '리프레시 데이'를 유급으로 제공한다.
3. 3년 근속 시 30일의 연차가 일시에 발생한다.
"""

question = "우리 회사(커넥트)의 신입사원 연차 발생 규정이 어떻게 돼?"

# 1. 규정 문서(context_data)를 프롬프트에 직접 넣어서 LLM에 전달
prompt = f"""
아래 [참고 정보]를 보고 질문에 답해줘.
[참고 정보]
{context_data}

질문: {question}
"""
# 2. 질문 출력 → LLM 호출 → 답변 출력
console.print(f"[bold]질문:[/bold] {question}\n")
response = llm.invoke(prompt)
console.print(f"[bold]답변:[/bold]\n{response.content}")
