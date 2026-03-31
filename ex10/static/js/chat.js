/**
 * ConnectHR ex10 - 채팅 UI 스크립트
 * ex07 기반 + PDF 캡처 이미지 근거 표시 + 에이전트 토글
 */

'use strict';

const STORAGE_KEY = 'connecthr_v10_chat';

// ============================================================
// 1. 쿼리 전송 (메인 진입점)
// ============================================================

async function submitQuery(event) {
  event.preventDefault();

  const input = document.getElementById('queryInput');
  const query = input.value.trim();
  if (!query) return;

  const agentToggle = document.getElementById('agentModeToggle');
  const useAgent = agentToggle ? agentToggle.checked : true;
  const sendBtn = document.querySelector('.btn-send');

  // ① 사용자 메시지 표시
  appendUserMessage(query);
  input.value = '';
  input.style.height = 'auto';

  // ② 로딩 표시
  const loading = document.getElementById('loadingIndicator');
  loading.style.display = 'flex';
  sendBtn.disabled = true;

  try {
    // ③ API 호출
    const response = await fetch('/api/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ query, use_agent: useAgent }),
    });

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }

    const data = await response.json();

    // ④ AI 응답 표시
    appendAiMessage(data);
    saveChatHistory();
  } catch (err) {
    appendAiMessage({
      answer: `오류가 발생했습니다: ${escapeHtml(err.message)}`,
      query_type: 'unstructured',
      mode: 'error',
      structured_data: {},
      unstructured_data: [],
      evidence_images: [],
    });
  } finally {
    loading.style.display = 'none';
    sendBtn.disabled = false;
    scrollToBottom();
  }
}

// ============================================================
// 2. 메시지 렌더링
// ============================================================

function appendUserMessage(text) {
  const history = document.getElementById('chatHistory');
  const div = document.createElement('div');
  div.className = 'chat-message user-message';
  div.innerHTML = `
    <div class="avatar">나</div>
    <div class="message-content">${escapeHtml(text)}</div>
  `;
  history.appendChild(div);
  scrollToBottom();
}

function appendAiMessage(data) {
  const history = document.getElementById('chatHistory');
  const div = document.createElement('div');
  div.className = 'chat-message ai-message';

  const typeBadge = buildQueryTypeBadge(data.query_type || 'unstructured');
  const modeBadge = data.mode === 'agent'
    ? '<span class="mode-badge">에이전트</span>'
    : '<span class="mode-badge" style="background:rgba(160,160,160,0.15);color:#aaa;border-color:rgba(160,160,160,0.2);">RAG</span>';

  // 소스 아코디언 (문서 + DB 결과)
  const accordion = buildSourceAccordion(data);

  // 캡처 이미지 근거
  const imageSection = buildEvidenceImages(data);

  div.innerHTML = `
    <div class="avatar">AI</div>
    <div class="message-content">
      ${formatAnswer(data.answer || '')}
      <div class="message-meta" style="padding-left:0;">
        ${typeBadge}
        ${modeBadge}
      </div>
      ${accordion}
      ${imageSection}
    </div>
  `;

  history.appendChild(div);
  rebindAccordions(div);
  rebindImageCards(div);
  scrollToBottom();
}

function buildQueryTypeBadge(queryType) {
  const config = {
    structured: { cls: 'type-structured', label: '정형' },
    unstructured: { cls: 'type-unstructured', label: '비정형' },
    hybrid: { cls: 'type-hybrid', label: '복합' },
  };
  const { cls, label } = config[queryType] || config.unstructured;
  return `<span class="query-type-badge ${cls}">${label}</span>`;
}

function buildSourceAccordion(data) {
  const docs = data.unstructured_data || [];
  const dbData = data.structured_data || {};

  const hasUnstructured = docs.length > 0;
  const hasStructured = Object.keys(dbData).length > 0;

  if (!hasUnstructured && !hasStructured) return '';

  let cards = '';

  // 비정형 문서 카드
  docs.forEach((doc) => {
    const source = escapeHtml(doc.source || '사내 문서');
    const content = escapeHtml(doc.content || '');
    const score = doc.score ? ` (${doc.score})` : '';
    cards += `
      <div class="source-card">
        <div class="source-card-title">${source}${score}</div>
        <div class="source-card-content">${content}</div>
      </div>
    `;
  });

  // 정형 DB 결과 카드
  Object.entries(dbData).forEach(([toolName, result]) => {
    const title = {
      leave_balance: '연차 조회 결과',
      sales_sum: '매출 집계 결과',
      list_employees: '직원 목록 결과',
    }[toolName] || toolName;

    const content = typeof result === 'object'
      ? JSON.stringify(result, null, 2).slice(0, 200)
      : String(result).slice(0, 200);

    cards += `
      <div class="source-card db-result-card">
        <div class="source-card-title">${escapeHtml(title)}</div>
        <div class="source-card-content" style="white-space:pre-wrap;font-family:monospace">${escapeHtml(content)}</div>
      </div>
    `;
  });

  const totalCount = docs.length + Object.keys(dbData).length;

  return `
    <div class="source-container">
      <div class="source-header" role="button" tabindex="0" aria-expanded="false">
        <span class="arrow">&#9660;</span>
        <span>근거 ${totalCount}건 보기</span>
      </div>
      <div class="source-body">
        <div class="source-grid">${cards}</div>
      </div>
    </div>
  `;
}

/**
 * PDF 캡처 이미지 근거 섹션을 생성한다 (URL 기준 중복 제거).
 */
function buildEvidenceImages(data) {
  const images = data.evidence_images || [];
  if (images.length === 0) return '';

  // URL 기준 중복 제거
  const seen = new Set();
  const unique = [];
  images.forEach((img) => {
    if (img.url && !seen.has(img.url)) {
      seen.add(img.url);
      unique.push(img);
    }
  });

  if (unique.length === 0) return '';

  let cards = '';
  unique.forEach((img) => {
    const source = escapeHtml(img.source || '');
    const page = img.page ? `p.${img.page}` : '';
    cards += `
      <div class="evidence-image-card" data-url="${escapeHtml(img.url)}">
        <img src="${escapeHtml(img.url)}" alt="${source} ${page}" loading="lazy">
        <div class="evidence-image-meta">
          <span class="source-name">${source}</span>
          ${page ? `<span> - ${page}</span>` : ''}
        </div>
      </div>
    `;
  });

  return `
    <div class="evidence-images">
      <div class="evidence-images-title">근거 페이지 이미지 (${unique.length}건)</div>
      <div class="evidence-image-grid">${cards}</div>
    </div>
  `;
}

// ============================================================
// 3. 아코디언 + 이미지 라이트박스 바인딩
// ============================================================

function rebindAccordions(container) {
  const headers = container.querySelectorAll('.source-header');
  headers.forEach((header) => {
    if (header.dataset.bound) return;
    header.dataset.bound = 'true';

    const toggle = () => {
      const sc = header.closest('.source-container');
      const expanded = header.getAttribute('aria-expanded') === 'true';
      header.setAttribute('aria-expanded', String(!expanded));
      if (sc) sc.classList.toggle('active', !expanded);
    };

    header.addEventListener('click', toggle);
    header.addEventListener('keydown', (e) => {
      if (e.key === 'Enter' || e.key === ' ') {
        e.preventDefault();
        toggle();
      }
    });
  });
}

function rebindImageCards(container) {
  const cards = container.querySelectorAll('.evidence-image-card');
  cards.forEach((card) => {
    if (card.dataset.bound) return;
    card.dataset.bound = 'true';

    card.addEventListener('click', () => {
      const url = card.dataset.url;
      if (!url) return;
      showLightbox(url);
    });
  });
}

function showLightbox(imageUrl) {
  const overlay = document.createElement('div');
  overlay.className = 'lightbox-overlay';
  overlay.innerHTML = `<img src="${escapeHtml(imageUrl)}" alt="근거 이미지">`;
  overlay.addEventListener('click', () => overlay.remove());
  document.addEventListener('keydown', function handler(e) {
    if (e.key === 'Escape') {
      overlay.remove();
      document.removeEventListener('keydown', handler);
    }
  });
  document.body.appendChild(overlay);
}

// ============================================================
// 4. 유틸리티
// ============================================================

function escapeHtml(text) {
  const div = document.createElement('div');
  div.textContent = String(text);
  return div.innerHTML;
}

function formatAnswer(text) {
  return escapeHtml(text).replace(/\n/g, '<br>');
}

function scrollToBottom() {
  const history = document.getElementById('chatHistory');
  history.scrollTop = history.scrollHeight;
}

// ============================================================
// 5. 로컬스토리지 대화 기록
// ============================================================

function saveChatHistory() {
  try {
    const history = document.getElementById('chatHistory');
    localStorage.setItem(STORAGE_KEY, history.innerHTML);
  } catch (e) {
    // 스토리지 용량 초과 등 무시
  }
}

function loadChatHistory() {
  try {
    const saved = localStorage.getItem(STORAGE_KEY);
    if (saved) {
      const history = document.getElementById('chatHistory');
      history.innerHTML = saved;
      rebindAccordions(history);
      rebindImageCards(history);
      scrollToBottom();
    }
  } catch (e) {
    // 스토리지 오류 무시
  }
}

function clearChatHistory() {
  if (!window.confirm('대화 기록을 모두 삭제하시겠습니까?')) return;
  localStorage.removeItem(STORAGE_KEY);
  location.reload();
}

/**
 * 서버 응답 캐시를 초기화한다.
 */
async function clearResponseCache() {
  try {
    const res = await fetch('/api/cache/clear', { method: 'POST' });
    const data = await res.json();
    window.alert(data.message || '캐시 초기화 완료');
  } catch (err) {
    window.alert('캐시 초기화 실패: ' + err.message);
  }
}

// ============================================================
// 6. 초기화
// ============================================================

document.addEventListener('DOMContentLoaded', () => {
  // 저장된 대화 기록 복원
  loadChatHistory();

  // 텍스트에어리어 자동 높이 조절
  const textarea = document.getElementById('queryInput');
  if (textarea) {
    textarea.addEventListener('input', () => {
      textarea.style.height = 'auto';
      textarea.style.height = Math.min(textarea.scrollHeight, 120) + 'px';
    });

    // IME 상태 추적
    let isComposing = false;
    textarea.addEventListener('compositionstart', () => { isComposing = true; });
    textarea.addEventListener('compositionend', () => { isComposing = false; });

    // Shift+Enter: 줄바꿈, Enter: 제출
    textarea.addEventListener('keydown', (e) => {
      if (e.key === 'Enter' && !e.shiftKey) {
        if (isComposing || e.isComposing || e.keyCode === 229) return;
        e.preventDefault();
        document.getElementById('chatForm').dispatchEvent(new Event('submit'));
      }
    });
  }

  // 에이전트 모드 토글 → 레이블 업데이트
  const toggle = document.getElementById('agentModeToggle');
  const modeLabel = document.getElementById('modeLabel');
  if (toggle && modeLabel) {
    const updateLabel = () => {
      if (toggle.checked) {
        modeLabel.textContent = 'ON';
        modeLabel.className = 'mode-label mode-agent';
      } else {
        modeLabel.textContent = 'OFF';
        modeLabel.className = 'mode-label mode-rag';
      }
    };
    toggle.addEventListener('change', updateLabel);
    updateLabel();
  }

  // 예시 질문 클릭 → 입력창에 복사
  document.querySelectorAll('.example-category li').forEach((li) => {
    li.addEventListener('click', () => {
      const inputEl = document.getElementById('queryInput');
      if (inputEl) {
        inputEl.value = li.textContent.trim();
        inputEl.focus();
      }
    });
  });
});
