"""ex05 — 슬라이딩 윈도우 메모리 모듈."""

from collections import deque


class WindowMemory:
    """최근 N턴의 대화만 유지하는 슬라이딩 윈도우 메모리."""

    def __init__(self, k=5, human_prefix="사용자", ai_prefix="AI 비서"):
        self.k = k
        self.human_prefix = human_prefix
        self.ai_prefix = ai_prefix
        self._turns = deque(maxlen=k)

    def get_history(self):
        """최근 N턴의 대화를 텍스트로 반환한다."""
        lines = []
        for question, answer in self._turns:
            lines.append(f"{self.human_prefix}: {question}")
            lines.append(f"{self.ai_prefix}: {answer}")
        return "\n".join(lines)

    def save_turn(self, question, answer):
        """사용자 질문과 AI 답변 1턴을 저장한다."""
        self._turns.append((question, answer))

    def clear(self):
        """히스토리를 초기화한다."""
        self._turns.clear()
