from langchain_ollama import ChatOllama
from rich.console import Console

console = Console()

# 로컬 LLM 연결
llm = ChatOllama(model="deepseek-r1:8b", temperature=0)

# 질문: 모델이 학습했을 리 없는 가상의 회사 규정
question = "우리 회사(커넥트)의 신입사원 연차 발생 규정이 어떻게 돼?"

console.print(f"[bold]질문:[/bold] {question}\n")
response = llm.invoke(question)
console.print(f"[bold]답변:[/bold]\n{response.content}")
