from langchain_ollama import ChatOllama
from rich.console import Console

console = Console()

# TODO: ChatOllama로 deepseek-r1:8b 모델 연결 (temperature=0)
# 1. Ollama에서 deepseek-r1:8b 모델을 로드 (temperature=0: 가장 확률 높은 답변)
llm = ChatOllama(model="deepseek-r1:8b", temperature=0)

# 질문: 모델이 학습했을 리 없는 가상의 회사 규정
question = "우리 회사(커넥트)의 신입사원 연차 발생 규정이 어떻게 돼?"

# TODO: 질문 출력 → llm.invoke로 답변 받기 → 답변 출력
# 2. 질문을 터미널에 출력
console.print(f"[bold]질문:[/bold] {question}\n")
# 3. LLM에 질문을 보내고 답변을 받음
response = llm.invoke(question)
# 4. 답변을 출력
console.print(f"[bold]답변:[/bold]\n{response.content}")
