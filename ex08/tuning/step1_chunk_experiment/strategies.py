"""청킹 전략 — Fixed-size / Recursive Character / Semantic."""

from rich.console import Console

console = Console()


def fixed_size_chunking(text: str, chunk_size: int = 500, overlap: int = 100) -> list[str]:
    """고정 크기 청킹을 수행합니다.

    Args:
        text: 분할할 원본 텍스트.
        chunk_size: 청크 하나의 최대 글자 수.
        overlap: 인접 청크 간 겹치는 글자 수.

    Returns:
        분할된 청크 리스트.
    """
    chunks = []
    start = 0
    text_length = len(text)

    while start < text_length:
        end = min(start + chunk_size, text_length)
        chunk = text[start:end]

        if chunk.strip():
            chunks.append(chunk.strip())

        if end >= text_length:
            break

        start = end - overlap

    return chunks


def recursive_character_chunking(
    text: str, chunk_size: int = 500, overlap: int = 100
) -> list[str]:
    """재귀적 문자 분할 청킹을 수행합니다.

    LangChain RecursiveCharacterTextSplitter 를 사용하며,
    패키지가 없으면 fixed_size_chunking 으로 폴백합니다.

    Args:
        text: 분할할 원본 텍스트.
        chunk_size: 청크 하나의 최대 글자 수.
        overlap: 인접 청크 간 겹치는 글자 수.

    Returns:
        분할된 청크 리스트.
    """
    try:
        from langchain_text_splitters import RecursiveCharacterTextSplitter

        splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=overlap,
            separators=["\n\n", "\n", "。", ".", " ", ""],
        )
        return splitter.split_text(text)

    except ImportError:
        console.print(
            "[yellow]langchain_text_splitters 가 설치되지 않아 "
            "기본 청킹으로 대체합니다.[/yellow]"
        )
        return fixed_size_chunking(text, chunk_size, overlap)


def semantic_chunking(
    text: str,
    embedding_model: str = "jhgan/ko-sroberta-multitask",
    percentile: int = 70,
) -> list[str]:
    """의미 단위 기반 시맨틱 청킹을 수행합니다.

    LangChain SemanticChunker + HuggingFace 임베딩을 사용합니다.
    패키지가 없으면 recursive_character_chunking 으로 폴백합니다.

    Args:
        text: 분할할 원본 텍스트.
        embedding_model: HuggingFace 임베딩 모델 이름.
        percentile: 시맨틱 분할 임계값 백분위.

    Returns:
        분할된 청크 리스트.
    """
    try:
        from langchain_community.embeddings import HuggingFaceEmbeddings
        from langchain_experimental.text_splitter import SemanticChunker

        console.print("[dim]시맨틱 청킹: 임베딩 모델 로드 중...[/dim]")
        embeddings = HuggingFaceEmbeddings(
            model_name=embedding_model,
            model_kwargs={"device": "cpu"},
        )

        chunker = SemanticChunker(
            embeddings,
            breakpoint_threshold_type="percentile",
            breakpoint_threshold_amount=percentile,
        )
        return chunker.split_text(text)

    except ImportError:
        console.print(
            "[yellow]langchain_experimental 패키지가 없어 "
            "재귀 청킹으로 대체합니다.[/yellow]"
        )
        console.print("pip install langchain-experimental 을 실행하십시오.")
        return recursive_character_chunking(text, chunk_size=500, overlap=100)
