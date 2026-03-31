"""ex05 — 세션별 대화 히스토리 관리 모듈."""

import os
import time

from dotenv import load_dotenv

from src.conversation import WindowMemory

load_dotenv()


class ConversationManager:
    """세션별 대화 히스토리를 관리하는 클래스."""

    def __init__(self, window_size=None, session_ttl=None):
        self.window_size = window_size or int(
            os.getenv("CONVERSATION_WINDOW_SIZE", "5")
        )
        self.session_ttl = session_ttl or int(
            os.getenv("SESSION_TTL_SECONDS", "3600")
        )
        self._sessions = {}

    def _get_or_create_memory(self, session_id):
        """세션 ID에 해당하는 Memory를 반환하거나 신규 생성한다."""
        now = time.time()
        self._cleanup_expired(now)

        if session_id not in self._sessions:
            memory = WindowMemory(
                k=self.window_size,
                human_prefix="사용자",
                ai_prefix="AI 비서",
            )
            self._sessions[session_id] = (memory, now)
        else:
            memory, _ = self._sessions[session_id]
            self._sessions[session_id] = (memory, now)

        return self._sessions[session_id][0]

    def _cleanup_expired(self, now):
        """TTL이 지난 만료된 세션을 삭제한다."""
        expired_keys = [
            sid
            for sid, (_, last_access) in self._sessions.items()
            if now - last_access > self.session_ttl
        ]
        for key in expired_keys:
            del self._sessions[key]

    def get_history_text(self, session_id):
        """세션의 대화 히스토리를 프롬프트 삽입용 문자열로 반환한다."""
        memory = self._get_or_create_memory(session_id)
        history = memory.get_history()
        return history if history else "없음"

    def save_turn(self, session_id, question, answer):
        """사용자 질문과 AI 답변을 세션 히스토리에 저장한다."""
        memory = self._get_or_create_memory(session_id)
        memory.save_turn(question, answer)

    def clear_session(self, session_id):
        """지정한 세션의 대화 히스토리를 초기화한다."""
        if session_id in self._sessions:
            memory, last_access = self._sessions[session_id]
            memory.clear()
            self._sessions[session_id] = (memory, last_access)

    def get_session_count(self):
        """현재 활성 세션 수를 반환한다."""
        return len(self._sessions)


# 앱 전역 싱글턴 인스턴스
_conversation_manager = None


def get_conversation_manager():
    """ConversationManager 싱글턴 인스턴스를 반환한다."""
    global _conversation_manager
    if _conversation_manager is None:
        _conversation_manager = ConversationManager()
    return _conversation_manager
