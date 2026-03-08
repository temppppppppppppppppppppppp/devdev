# UI 구현 오더 (Sonnet 터미널용)

> 제안서: `docs/2026-03-05/codex-ui-webgal-light-proposal.md` v1.18
> 작성일: 2026-03-08

---

## 터미널 배정 계획

| Step | 작업 | 터미널 수 | 병렬 가능 | 선행 조건 |
|------|------|----------|----------|----------|
| 1 | 메뉴 3카테고리 구조 변경 | 1 | - | 없음 |
| 2 | 장르설정 모달 | 1 | Step 3과 병렬 | Step 1 완료 |
| 3 | 설정 패널 (API 키) | 1 | Step 2와 병렬 | Step 1 완료 |
| 4 | ProcessRunner 실체화 | 1 | Step 2,3과 병렬 | 없음 (백엔드) |
| 5 | WS 이벤트 → UI 연결 | 1 | - | Step 1,4 완료 |

**최적 터미널**: Step 2+3 시점에서 **최대 3개** (Step 2 + Step 3 + Step 4 병렬)

---

## Step 1 오더: 메뉴 3카테고리 구조 변경

### 대상 파일
- `geuldobi-desktop/src/index.html` (단일 파일, 인라인 CSS+JS)

### 참고 문서
- `docs/2026-03-05/codex-ui-webgal-light-proposal.md` → "v1.18 메뉴 재구조화" 섹션

### 지시 사항

현재 실행 패널(좌측)에 Stage 0~4, One-Stop, Rollback, Wipe, Reset, Rewind, Stop 버튼이 **flat 목록**으로 나열되어 있다. 이것을 **3개 카테고리 아코디언**으로 재구조화해라.

#### 1. 카테고리 구조

```
▶ 재료 넣기          ← 클릭 시 하위 펼침/접기
   Bible 설정         (data-key="0", data-sub-key="1")
   Treatment 확장     (data-key="0", data-sub-key="5")
   역설계             (data-key="0", data-sub-key="3")
   스타일 분석         (data-key="0", data-sub-key="6")

▶ 상품 생산          ← 클릭 시 하위 펼침/접기
   [장르설정]          (UI 전용, 백엔드 키 없음 — Step 2에서 구현, 지금은 비활성 버튼만)
   Arc 설계           (data-key="2")
   Blueprint          (data-key="3")
   원고 생산           (data-key="4")
   One-Stop           (data-key="6")

▶ 운영              ← 클릭 시 하위 펼침/접기
   Rollback           (data-key="44")
   Wipe               (data-key="77")
   Reset              (data-key="88")
   Rewind             (data-key="99")
   Stop               (data-action="stop")
```

#### 2. Stage 1 숨김

- Stage 1 버튼(data-key="1")에 `style="display:none"` 또는 CSS 클래스 `.hidden-stage` 적용
- HTML에서 삭제하지 말 것 — 숨기기만
- 관련 JS 이벤트 핸들러도 삭제하지 말 것

#### 3. 아코디언 동작

- 카테고리 헤더 클릭 시 하위 버튼 목록 토글 (slideDown/slideUp 또는 display 토글)
- 기본 상태: 전부 펼침 (첫 로드 시)
- 한 카테고리 펼칠 때 다른 카테고리 자동 접기 안 함 (독립 토글)
- 카테고리 헤더 스타일: 기존 버튼보다 약간 큰 폰트 + `▶`/`▼` 토글 아이콘 + 배경색 `#e2e8f0`

#### 4. "재료 넣기" 하위 버튼의 data 속성 변경

기존 Stage 0 버튼은 `data-key="0"` 하나였다. 이제 Stage 0의 sub_key별로 분리된 버튼이 되므로:

```html
<button class="menu-btn material-btn" data-key="0" data-sub-key="1">Bible 설정</button>
<button class="menu-btn material-btn" data-key="0" data-sub-key="5">Treatment 확장</button>
<button class="menu-btn material-btn" data-key="0" data-sub-key="3">역설계</button>
<button class="menu-btn material-btn" data-key="0" data-sub-key="6">스타일 분석</button>
```

기존 Stage 0 단일 버튼은 삭제하거나 숨김 처리.

#### 5. "장르설정" 버튼 (플레이스홀더)

```html
<button class="menu-btn genre-btn" disabled data-action="genre_setting">장르설정</button>
```

- `disabled` 상태로 배치 (Step 2에서 활성화)
- 스타일: 회색 + "준비 중" 느낌

#### 6. 스타일 가이드

- 카테고리 헤더: `font-weight: 600`, `font-size: 0.95em`, `padding: 8px 12px`, `cursor: pointer`, `background: #e2e8f0`, `border-radius: 6px`, `margin-bottom: 4px`
- 하위 버튼: 기존 스타일 유지, 좌측 패딩 8px 추가 (들여쓰기 효과)
- 카테고리 간 간격: `margin-top: 12px`
- Office Chic 톤 유지 (저채도, 가독성 우선)

#### 7. 하지 말 것

- 백엔드 파일(bridge_server.py, run_validator.py, main_a.py) 수정 금지
- Canvas 시각화 패널, 로그 패널 변경 금지
- 기존 JS 이벤트 핸들러 로직 변경 금지 (DOM 구조만 변경)
- 새 파일 생성 금지 (index.html 내 인라인으로 작업)

#### 8. 완료 기준

- `npm start`로 Electron 앱 실행 시 3카테고리가 보임
- 각 카테고리 클릭 시 하위 버튼 접기/펼치기 동작
- Stage 1 버튼이 화면에 안 보임
- "재료 넣기" 하위 4개 버튼에 data-sub-key 속성 존재
- "장르설정" 버튼이 disabled 상태로 존재
- 기존 버튼 클릭 시 로그 패널에 메시지 표시 (기존 동작 유지)

---

## Step 2 오더: 장르설정 모달 [터미널 A]

> **선행**: Step 1 완료
> **대상 파일**: `geuldobi-desktop/src/index.html` (인라인 CSS+JS)
> **참고**: `docs/2026-03-05/codex-ui-webgal-light-proposal.md` → "장르설정 모달 명세" 섹션

### 지시 사항

Step 1에서 "상품 생산" 카테고리 안에 `disabled` 상태로 배치된 "장르설정" 버튼을 활성화하고, 클릭 시 장르 선택 모달을 표시해라.

#### 1. "장르설정" 버튼 활성화

- `disabled` 속성 제거
- `data-action="genre_setting"` 유지
- 클릭 시 장르 선택 모달 표시

#### 2. 모달 HTML 구조

```html
<div id="genre-modal" class="modal-overlay" style="display:none">
  <div class="modal-content">
    <h3>장르 선택</h3>
    <p class="modal-desc">프로젝트에 적용할 장르를 선택하세요.</p>
    <div class="genre-grid">
      <!-- 10개 장르 버튼 -->
    </div>
    <div class="modal-footer">
      <button class="modal-cancel-btn">취소</button>
    </div>
  </div>
</div>
```

#### 3. 장르 목록 (10개)

```html
<button class="genre-option active-genre" data-genre="investment">투자물</button>
<button class="genre-option untested-genre" data-genre="wuxia">무협 <span class="untested-label">(테스트 없음)</span></button>
<button class="genre-option untested-genre" data-genre="hunter">헌터물 <span class="untested-label">(테스트 없음)</span></button>
<button class="genre-option untested-genre" data-genre="fantasy">판타지 <span class="untested-label">(테스트 없음)</span></button>
<button class="genre-option untested-genre" data-genre="medical">의료물 <span class="untested-label">(테스트 없음)</span></button>
<button class="genre-option untested-genre" data-genre="alt_history">대체역사 <span class="untested-label">(테스트 없음)</span></button>
<button class="genre-option untested-genre" data-genre="composer">작곡물 <span class="untested-label">(테스트 없음)</span></button>
<button class="genre-option untested-genre" data-genre="sports">스포츠물 <span class="untested-label">(테스트 없음)</span></button>
<button class="genre-option untested-genre" data-genre="actor">배우/연예물 <span class="untested-label">(테스트 없음)</span></button>
<button class="genre-option untested-genre" data-genre="cooking">요리물 <span class="untested-label">(테스트 없음)</span></button>
```

#### 4. 스타일

```css
/* 모달 오버레이 */
.modal-overlay {
  position: fixed; top: 0; left: 0; width: 100%; height: 100%;
  background: rgba(0,0,0,0.4); z-index: 1000;
  display: flex; align-items: center; justify-content: center;
}
.modal-content {
  background: #ffffff; border-radius: 12px; padding: 24px 28px;
  min-width: 400px; max-width: 520px; box-shadow: 0 8px 32px rgba(0,0,0,0.15);
}
.modal-content h3 { margin: 0 0 8px; font-size: 1.1em; color: #1e293b; }
.modal-desc { color: #64748b; font-size: 0.85em; margin-bottom: 16px; }

/* 장르 그리드 */
.genre-grid {
  display: grid; grid-template-columns: 1fr 1fr; gap: 8px; margin-bottom: 16px;
}
.genre-option {
  padding: 10px 14px; border: 1px solid #cbd5e1; border-radius: 8px;
  background: #f8fafc; cursor: pointer; text-align: left;
  font-size: 0.9em; color: #334155; transition: all 0.15s;
}
.genre-option:hover { border-color: #94a3b8; background: #f1f5f9; }
.genre-option.selected { border-color: #3b82f6; background: #eff6ff; color: #1e40af; }

/* 활성 장르 (투자물) */
.active-genre { font-weight: 600; }

/* 테스트 없음 라벨 */
.untested-label { color: #94a3b8; font-size: 0.8em; font-weight: 400; }

/* 모달 푸터 */
.modal-footer { display: flex; justify-content: flex-end; gap: 8px; }
.modal-cancel-btn {
  padding: 6px 16px; border: 1px solid #cbd5e1; border-radius: 6px;
  background: #f8fafc; cursor: pointer; color: #64748b; font-size: 0.85em;
}
```

#### 5. JS 동작

```javascript
// 장르설정 버튼 클릭 → 모달 표시
document.querySelector('[data-action="genre_setting"]').addEventListener('click', () => {
  document.getElementById('genre-modal').style.display = 'flex';
});

// 장르 선택
document.querySelectorAll('.genre-option').forEach(btn => {
  btn.addEventListener('click', () => {
    // 테스트 없음 장르 선택 시 확인
    if (btn.classList.contains('untested-genre')) {
      if (!confirm('이 장르는 실파이프라인 테스트가 완료되지 않았습니다. 진행하시겠습니까?')) return;
    }
    // 선택 표시
    document.querySelectorAll('.genre-option').forEach(b => b.classList.remove('selected'));
    btn.classList.add('selected');
    // 로컬 저장
    localStorage.setItem('geuldobi_genre', btn.dataset.genre);
    // 로그 표시
    appendLog(`장르 설정: ${btn.textContent.trim()}`);
    // 모달 닫기
    document.getElementById('genre-modal').style.display = 'none';
  });
});

// 취소 버튼
document.querySelector('.modal-cancel-btn').addEventListener('click', () => {
  document.getElementById('genre-modal').style.display = 'none';
});

// 오버레이 클릭으로 닫기
document.getElementById('genre-modal').addEventListener('click', (e) => {
  if (e.target === e.currentTarget) e.currentTarget.style.display = 'none';
});

// 앱 로드 시 저장된 장르 복원
const savedGenre = localStorage.getItem('geuldobi_genre');
if (savedGenre) {
  const btn = document.querySelector(`[data-genre="${savedGenre}"]`);
  if (btn) btn.classList.add('selected');
}
```

#### 6. 하지 말 것

- 백엔드 파일 수정 금지
- Canvas/로그 패널 변경 금지
- Step 1에서 만든 카테고리 아코디언 구조 변경 금지
- 새 파일 생성 금지 (index.html 내 인라인)

#### 7. 완료 기준

- "장르설정" 버튼 클릭 시 모달이 표시됨
- 10개 장르가 2열 그리드로 보임
- 투자물만 굵은 글씨, 나머지 9개에 "(테스트 없음)" 회색 라벨
- 투자물 외 장르 선택 시 confirm 대화상자 표시
- 장르 선택 후 모달 자동 닫힘 + 로그 패널에 "장르 설정: ..." 표시
- 취소 버튼/오버레이 클릭으로 모달 닫힘
- 새로고침 후에도 선택한 장르 유지 (localStorage)

---

## Step 3 오더: 설정 패널 (API 키) [터미널 B — Step 2와 병렬]

> **선행**: Step 1 완료
> **대상 파일**: `geuldobi-desktop/src/index.html` (인라인 CSS+JS)
> **참고**: `docs/2026-03-05/codex-ui-webgal-light-proposal.md` → "설정 패널 명세" 섹션

### 지시 사항

상단바의 "설정" 버튼을 클릭하면 사이드 패널이 열리고, Gemini API 키를 입력/저장/테스트할 수 있게 해라.

#### 1. 설정 패널 HTML

```html
<div id="settings-panel" class="settings-panel" style="display:none">
  <div class="settings-header">
    <h3>설정</h3>
    <button class="settings-close-btn">✕</button>
  </div>
  <div class="settings-body">
    <!-- 탭 네비게이션 -->
    <div class="settings-tabs">
      <button class="settings-tab active" data-tab="api">API 키</button>
      <button class="settings-tab" data-tab="system">시스템</button>
    </div>

    <!-- 탭 1: API 키 -->
    <div class="settings-tab-content" data-tab-content="api">
      <div class="setting-group">
        <label class="setting-label">Gemini API Key (기본) <span class="required-mark">*필수</span></label>
        <div class="api-key-row">
          <input type="password" id="api-key-1" class="setting-input api-key-input"
                 placeholder="AIza..." autocomplete="off">
          <button class="key-toggle-btn" title="보기/숨기기">👁</button>
        </div>
      </div>

      <details class="extra-keys-section">
        <summary>추가 키 (쿼터 분산용, 선택)</summary>
        <div class="setting-group" data-key-index="2">
          <label class="setting-label">API Key 2</label>
          <input type="password" class="setting-input api-key-input extra-key" placeholder="AIza...">
        </div>
        <div class="setting-group" data-key-index="3">
          <label class="setting-label">API Key 3</label>
          <input type="password" class="setting-input api-key-input extra-key" placeholder="AIza...">
        </div>
        <!-- 4~9는 동일 패턴, 총 8개 추가 키 -->
      </details>

      <div class="setting-group">
        <label class="setting-label">Slack Webhook URL (선택)</label>
        <input type="text" id="slack-webhook" class="setting-input" placeholder="https://hooks.slack.com/...">
      </div>

      <div class="settings-actions">
        <button id="save-settings-btn" class="primary-btn">저장</button>
        <button id="test-key-btn" class="secondary-btn">키 테스트</button>
        <span id="settings-status" class="settings-status"></span>
      </div>
    </div>

    <!-- 탭 2: 시스템 (읽기 전용, 향후 확장) -->
    <div class="settings-tab-content" data-tab-content="system" style="display:none">
      <p class="placeholder-text">시스템 설정은 준비 중입니다.</p>
    </div>
  </div>
</div>
```

#### 2. 스타일

```css
.settings-panel {
  position: fixed; top: 0; right: 0; width: 380px; height: 100%;
  background: #ffffff; box-shadow: -4px 0 16px rgba(0,0,0,0.1);
  z-index: 900; display: flex; flex-direction: column;
  font-family: -apple-system, "Malgun Gothic", sans-serif;
}
.settings-header {
  display: flex; justify-content: space-between; align-items: center;
  padding: 16px 20px; border-bottom: 1px solid #e2e8f0;
}
.settings-header h3 { margin: 0; font-size: 1.05em; color: #1e293b; }
.settings-close-btn {
  background: none; border: none; font-size: 1.2em; cursor: pointer; color: #94a3b8;
}
.settings-body { padding: 16px 20px; overflow-y: auto; flex: 1; }

/* 탭 */
.settings-tabs {
  display: flex; gap: 4px; margin-bottom: 16px;
  border-bottom: 1px solid #e2e8f0; padding-bottom: 8px;
}
.settings-tab {
  padding: 6px 14px; border: none; background: none; cursor: pointer;
  color: #64748b; font-size: 0.85em; border-radius: 4px;
}
.settings-tab.active { background: #f1f5f9; color: #1e293b; font-weight: 600; }

/* 입력 */
.setting-group { margin-bottom: 14px; }
.setting-label { display: block; font-size: 0.8em; color: #475569; margin-bottom: 4px; font-weight: 500; }
.required-mark { color: #ef4444; font-size: 0.85em; }
.setting-input {
  width: 100%; padding: 8px 10px; border: 1px solid #cbd5e1; border-radius: 6px;
  font-size: 0.85em; box-sizing: border-box;
}
.setting-input:focus { outline: none; border-color: #3b82f6; }

/* API 키 행 */
.api-key-row { display: flex; gap: 6px; }
.api-key-row .setting-input { flex: 1; }
.key-toggle-btn {
  padding: 6px 10px; border: 1px solid #cbd5e1; border-radius: 6px;
  background: #f8fafc; cursor: pointer; font-size: 0.9em;
}

/* 추가 키 섹션 */
.extra-keys-section { margin-bottom: 14px; }
.extra-keys-section summary {
  font-size: 0.8em; color: #64748b; cursor: pointer; padding: 6px 0;
}

/* 액션 */
.settings-actions { display: flex; gap: 8px; align-items: center; margin-top: 8px; }
.primary-btn {
  padding: 8px 20px; background: #3b82f6; color: white; border: none;
  border-radius: 6px; cursor: pointer; font-size: 0.85em; font-weight: 500;
}
.primary-btn:hover { background: #2563eb; }
.secondary-btn {
  padding: 8px 16px; background: #f1f5f9; color: #475569; border: 1px solid #cbd5e1;
  border-radius: 6px; cursor: pointer; font-size: 0.85em;
}
.settings-status { font-size: 0.8em; color: #64748b; }
.placeholder-text { color: #94a3b8; font-size: 0.85em; text-align: center; padding: 40px 0; }
```

#### 3. JS 동작

```javascript
// 설정 패널 열기/닫기
document.querySelector('[data-action="settings"]').addEventListener('click', () => {
  const panel = document.getElementById('settings-panel');
  panel.style.display = panel.style.display === 'none' ? 'flex' : 'none';
  if (panel.style.display === 'flex') loadSettings();
});
document.querySelector('.settings-close-btn').addEventListener('click', () => {
  document.getElementById('settings-panel').style.display = 'none';
});

// 탭 전환
document.querySelectorAll('.settings-tab').forEach(tab => {
  tab.addEventListener('click', () => {
    document.querySelectorAll('.settings-tab').forEach(t => t.classList.remove('active'));
    tab.classList.add('active');
    document.querySelectorAll('.settings-tab-content').forEach(c => c.style.display = 'none');
    document.querySelector(`[data-tab-content="${tab.dataset.tab}"]`).style.display = 'block';
  });
});

// 비밀번호 토글
document.querySelector('.key-toggle-btn').addEventListener('click', () => {
  const input = document.getElementById('api-key-1');
  input.type = input.type === 'password' ? 'text' : 'password';
});

// 저장 (localStorage — 실제 .env 쓰기는 Step 4에서 IPC 연결 후)
document.getElementById('save-settings-btn').addEventListener('click', () => {
  const key1 = document.getElementById('api-key-1').value.trim();
  if (!key1) { setStatus('⚠ 기본 API 키를 입력해주세요', '#ef4444'); return; }
  const settings = { apiKey: key1, extraKeys: [], slackWebhook: '' };
  document.querySelectorAll('.extra-key').forEach(input => {
    if (input.value.trim()) settings.extraKeys.push(input.value.trim());
  });
  settings.slackWebhook = document.getElementById('slack-webhook').value.trim();
  localStorage.setItem('geuldobi_settings', JSON.stringify(settings));
  setStatus('✓ 저장됨', '#22c55e');
  appendLog('설정 저장 완료');
});

// 키 테스트 (현재는 형식 검증만, 실제 API 호출은 백엔드 연결 후)
document.getElementById('test-key-btn').addEventListener('click', () => {
  const key = document.getElementById('api-key-1').value.trim();
  if (!key) { setStatus('⚠ 키를 먼저 입력해주세요', '#ef4444'); return; }
  if (!key.startsWith('AIza')) { setStatus('⚠ 유효하지 않은 키 형식', '#ef4444'); return; }
  setStatus('✓ 형식 확인 (API 연결 후 실제 테스트 가능)', '#3b82f6');
});

// 설정 로드
function loadSettings() {
  try {
    const saved = JSON.parse(localStorage.getItem('geuldobi_settings') || '{}');
    if (saved.apiKey) document.getElementById('api-key-1').value = saved.apiKey;
    if (saved.slackWebhook) document.getElementById('slack-webhook').value = saved.slackWebhook;
    (saved.extraKeys || []).forEach((key, i) => {
      const input = document.querySelector(`[data-key-index="${i+2}"] .extra-key`);
      if (input) input.value = key;
    });
  } catch(e) { /* ignore parse errors */ }
}

function setStatus(msg, color) {
  const el = document.getElementById('settings-status');
  el.textContent = msg;
  el.style.color = color;
  setTimeout(() => { el.textContent = ''; }, 3000);
}
```

#### 4. 상단바 "설정" 버튼 연결

- 상단바에 이미 "설정" 텍스트/버튼이 있으면 `data-action="settings"` 속성 추가
- 없으면 상단바 우측에 추가: `<button class="topbar-btn" data-action="settings">⚙ 설정</button>`

#### 5. 하지 말 것

- 백엔드 파일 수정 금지
- `.env` 파일 직접 쓰기 금지 (이 단계에서는 localStorage만 사용, .env 쓰기는 IPC 연결 후)
- Canvas/로그 패널 변경 금지
- Step 1 카테고리 구조, Step 2 장르 모달 변경 금지
- 새 파일 생성 금지

#### 6. 완료 기준

- 상단바 "설정" 클릭 시 우측에서 설정 패널이 슬라이드인
- API 키 입력 필드 + 보기/숨기기 토글 동작
- "추가 키" 접기/펼치기로 Key 2~9 입력 가능
- "저장" 클릭 시 localStorage에 저장 + "✓ 저장됨" 표시
- "키 테스트" 클릭 시 형식 검증 + 결과 표시
- 탭 전환 (API 키 / 시스템) 동작
- 패널 닫기 (✕ 버튼) 동작
- 새로고침 후 저장된 값 복원

---

## Step 4 오더 (예고 — 백엔드, Step 2/3과 병렬 가능)

`modules/api/process_runner.py` 실체화. `asyncio.create_subprocess_exec` 기반 main_a.py 실행 + stdin/stdout 스트리밍.

## Step 5 오더 (예고 — Step 1,4 완료 후)

프론트엔드 WS `/events` 연결 → 로그 패널 실시간 표시 + verdict 파싱 + 에이전트 상태 반영.
