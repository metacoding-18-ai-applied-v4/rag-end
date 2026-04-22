"""ex11 서버 실행 — 커넥트HR 에이전트 완성 (파이프라인 + 근거 이미지).

인덱싱·모델 로드·uvicorn 기동까지 rich 스피너로 진행 상황을 한눈에 볼 수 있게 표시한다.
"""

import logging
import os

import uvicorn
from dotenv import load_dotenv
from rich.console import Console

# `.env`의 값이 아래 os.getenv 호출에 반영되도록 먼저 로드
load_dotenv()

os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")
# 외부 라이브러리 로그는 WARNING으로 낮춰 스피너와 덜 섞이게
logging.basicConfig(level=logging.WARNING, format="%(levelname)s:%(name)s: %(message)s")

console = Console()


def _banner(port: int) -> None:
    console.rule("[bold cyan]ex11 커넥트HR 에이전트[/]")
    console.print(f"[dim]VISION_MODEL={os.getenv('VISION_MODEL', 'qwen2.5vl:7b')}  ·  PORT={port}[/]")
    console.print()


def _warmup() -> None:
    """벡터DB·모델을 서버 기동 전에 전부 준비. 스피너로 진행 표시."""
    from src.tools.search_documents import _get_store
    from src.tuning.reranker import CrossEncoderReranker

    console.print("[bold]1. 벡터DB 준비[/]")
    _get_store()  # 내부에서 스피너 단계별 표시
    console.print()

    console.print("[bold]2. Cross-Encoder 리랭커 로드[/]")
    with console.status("[cyan]BAAI/bge-reranker-v2-m3 로드 중[/] [dim](첫 실행은 모델 다운로드)[/]", spinner="dots"):
        CrossEncoderReranker()
    console.log("[green]✓[/] 리랭커 준비 완료")
    console.print()


def main() -> None:
    port = int(os.getenv("PORT", "8000"))
    reload = os.getenv("UVICORN_RELOAD", "1") not in ("0", "false", "False")

    _banner(port)
    _warmup()

    console.print("[bold]3. 서버 기동[/]")
    console.print(f"[green]✓[/] 준비 완료 → [bold]http://localhost:{port}/chat[/]")
    console.rule()
    uvicorn.run("app.main:app", host="0.0.0.0", port=port, reload=reload)


if __name__ == "__main__":
    main()
