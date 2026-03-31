/**
 * ex05 RAG Q&A 채팅 로직
 *
 * ex02의 qa.js 패턴을 기반으로 작성된 Fetch 기반 채팅 스크립트.
 * 멀티턴 대화: 세션 ID를 localStorage에 저장하여 이전 대화 맥락을 유지한다.
 * 출처 아코디언: 각 AI 답변 아래에 근거 문서 목록을 펼칠 수 있다.
 */

'use strict';

// ---- DOM 요소 참조 ----
const chatHistory = document.getElementById('chatHistory');
const loadingIndicator = document.getElementById('loadingIndicator');
const questionInput = document.getElementById('questionInput');
const chatForm = document.getElementById('chatForm');

// ---- 세션 ID 관리 (localStorage 기반 멀티턴) ----
const SESSION_STORAGE_KEY = 'rag_chat_session_id';

/**
 * localStorage에서 세션 ID를 읽거나 신규 생성한다.
 * @returns {string} 세션 ID 문자열
 */
function getOrCreateSessionId() {
    let sessionId = localStorage.getItem(SESSION_STORAGE_KEY);
    if (!sessionId) {
        // 간단한 UUID v4 생성
        sessionId = 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, (c) => {
            const r = (Math.random() * 16) | 0;
            return (c === 'x' ? r : (r & 0x3) | 0x8).toString(16);
        });
        localStorage.setItem(SESSION_STORAGE_KEY, sessionId);
    }
    return sessionId;
}

// ---- 스크롤 유틸리티 ----

/**
 * 채팅 히스토리를 최하단으로 스크롤한다.
 */
function scrollToBottom() {
    if (chatHistory) {
        chatHistory.scrollTop = chatHistory.scrollHeight;
    }
}

// ---- 메시지 렌더링 ----

/**
 * 사용자 메시지 말풍선을 채팅 히스토리에 추가한다.
 * @param {string} text - 표시할 질문 텍스트
 */
function appendUserMessage(text) {
    const div = document.createElement('div');
    div.className = 'chat-message user-message';

    const content = document.createElement('div');
    content.className = 'message-content';
    content.textContent = text; // XSS 방지: textContent 사용

    div.appendChild(content);
    chatHistory.appendChild(div);
    scrollToBottom();
}

/**
 * AI 답변 말풍선과 출처 아코디언을 채팅 히스토리에 추가한다.
 * @param {string} answer - AI 답변 텍스트
 * @param {Array<{doc: string, page: number, snippet: string}>} sources - 출처 목록
 */
function appendAiMessage(answer, sources) {
    const div = document.createElement('div');
    div.className = 'chat-message ai-message';

    // AI 아바타
    const avatar = document.createElement('div');
    avatar.className = 'avatar';
    avatar.textContent = '🤖';

    // 메시지 본문
    const content = document.createElement('div');
    content.className = 'message-content';

    // 답변 텍스트 (줄바꿈을 <br>로 변환)
    const answerDiv = document.createElement('div');
    answerDiv.className = 'ai-ans-text';
    answerDiv.innerHTML = escapeHtml(answer).replace(/\n/g, '<br>');
    content.appendChild(answerDiv);

    // 출처 아코디언
    const accordionHtml = buildSourceAccordion(sources);
    if (accordionHtml) {
        const accordionWrapper = document.createElement('div');
        accordionWrapper.innerHTML = accordionHtml;
        content.appendChild(accordionWrapper.firstElementChild);
    }

    div.appendChild(avatar);
    div.appendChild(content);
    chatHistory.appendChild(div);
    scrollToBottom();
}

/**
 * 오류 메시지 말풍선을 채팅 히스토리에 추가한다.
 * @param {string} errorMsg - 표시할 오류 메시지
 */
function appendErrorMessage(errorMsg) {
    const div = document.createElement('div');
    div.className = 'chat-message ai-message error-message';

    const avatar = document.createElement('div');
    avatar.className = 'avatar';
    avatar.textContent = '⚠️';

    const content = document.createElement('div');
    content.className = 'message-content';
    content.textContent = errorMsg;

    div.appendChild(avatar);
    div.appendChild(content);
    chatHistory.appendChild(div);
    scrollToBottom();
}

// ---- 출처 아코디언 생성 ----

/**
 * 출처 목록으로 아코디언 HTML 문자열을 생성한다.
 * 출처가 없으면 빈 문자열을 반환한다.
 *
 * @param {Array<{doc: string, page: number, snippet: string}>} sources - 출처 배열
 * @returns {string} 아코디언 HTML 문자열
 */
function buildSourceAccordion(sources) {
    if (!sources || sources.length === 0) {
        return '';
    }

    const itemsHtml = sources.map((src) => {
        const doc = escapeHtml(src.doc || '알 수 없는 문서');
        const page = src.page > 0 ? `p.${src.page}` : '-';
        const snippet = escapeHtml(src.snippet || '');

        return `
            <div class="source-item">
                <span class="source-doc">📄 ${doc}</span>
                <span class="source-page">${page}</span>
                <div class="source-snippet">${snippet}</div>
            </div>
        `;
    }).join('');

    return `
        <div class="source-container">
            <div class="source-header" onclick="this.parentElement.classList.toggle('active')">
                <span>🔍 근거 문서 보기 (${sources.length}건)</span>
                <i class="arrow">▼</i>
            </div>
            <div class="source-body">
                <div class="source-list">
                    ${itemsHtml}
                </div>
            </div>
        </div>
    `;
}

// ---- XSS 방지 유틸리티 ----

/**
 * HTML 특수문자를 이스케이프한다.
 * @param {string} text - 이스케이프할 문자열
 * @returns {string} 이스케이프된 문자열
 */
function escapeHtml(text) {
    const map = {
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#039;',
    };
    return String(text).replace(/[&<>"']/g, (m) => map[m]);
}

// ---- 채팅 전송 로직 ----

/**
 * 폼 제출 이벤트 핸들러.
 * 사용자 질문을 /api/chat에 Fetch POST로 전송하고 응답을 렌더링한다.
 *
 * @param {Event} event - 폼 제출 이벤트
 */
async function handleSubmit(event) {
    event.preventDefault();

    const question = questionInput.value.trim();
    if (!question) return;

    // 1. 사용자 메시지 표시
    appendUserMessage(question);
    questionInput.value = '';

    // 2. 로딩 표시
    loadingIndicator.style.display = 'flex';

    const sessionId = getOrCreateSessionId();

    try {
        // 3. Fetch POST 요청
        const response = await fetch('/api/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                question: question,
                session_id: sessionId,
            }),
        });

        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            throw new Error(errorData.error || `서버 오류 (HTTP ${response.status})`);
        }

        // 4. 응답 파싱
        const data = await response.json();

        // 서버에서 신규 세션 ID가 오면 갱신
        if (data.session_id) {
            localStorage.setItem(SESSION_STORAGE_KEY, data.session_id);
        }

        // 5. AI 답변 표시
        appendAiMessage(data.answer || '답변을 받지 못했습니다.', data.sources || []);

    } catch (error) {
        console.error('[ERROR] 채팅 요청 실패:', error);
        appendErrorMessage(
            `오류가 발생했습니다: ${error.message}\n` +
            'LLM 서버(Ollama)가 실행 중인지 확인해 주세요.'
        );
    } finally {
        // 6. 로딩 숨기기
        loadingIndicator.style.display = 'none';
    }
}

// ---- 대화 내역 초기화 ----

/**
 * 화면의 채팅 내역을 지우고 세션을 초기화한다.
 * 서버의 대화 히스토리(WindowMemory)도 함께 삭제한다.
 */
async function clearChatHistory() {
    if (!confirm('대화 내역을 모두 지우시겠습니까?\n이전 대화 맥락도 초기화됩니다.')) {
        return;
    }

    // 서버 세션 초기화 요청
    try {
        await fetch('/api/chat/session', { method: 'DELETE' });
    } catch (e) {
        console.warn('[WARN] 서버 세션 초기화 실패:', e);
    }

    // 로컬 세션 ID 삭제 (다음 질문 시 신규 생성)
    localStorage.removeItem(SESSION_STORAGE_KEY);

    // 화면 초기화: 환영 메시지만 남기기
    if (chatHistory) {
        chatHistory.innerHTML = `
            <div class="chat-message ai-message">
                <div class="avatar">🤖</div>
                <div class="message-content">
                    대화 내역이 초기화되었습니다. 새 질문을 입력해 주세요.
                </div>
            </div>
        `;
    }
}

// ---- 이벤트 리스너 등록 ----
if (chatForm) {
    chatForm.addEventListener('submit', handleSubmit);
}

// 페이지 로드 시 입력창에 포커스
window.addEventListener('DOMContentLoaded', () => {
    if (questionInput) {
        questionInput.focus();
    }
    scrollToBottom();
});
