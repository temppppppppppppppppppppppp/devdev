const statusMessageEl = document.getElementById("statusMessage");

let pollTimer = null;
let didNotifyReady = false;
let pollFailCount = 0;
const MAX_POLL_FAILS = 30; // 30초 연속 실패 시 오류 표시

function setMessage(text) {
  statusMessageEl.textContent = text;
}

async function fetchStatus(statusBaseUrl) {
  try {
    const res = await fetch(`${statusBaseUrl}/status`, {
      method: "GET",
      cache: "no-store",
      signal: AbortSignal.timeout(5000),
    });

    if (!res.ok) {
      return { ok: false, status: res.status, data: null };
    }

    const data = await res.json();
    return { ok: true, status: res.status, data };
  } catch {
    return { ok: false, status: 0, data: null };
  }
}

function notifyReadyOnce() {
  if (didNotifyReady) return;
  didNotifyReady = true;
  try {
    window.geuldobiDesktop.notifyBackendReady();
  } catch (err) {
    console.error("[splash] notifyBackendReady failed:", err);
  }
}

async function startPolling(config) {
  const { statusBaseUrl } = config;
  pollTimer = setInterval(async () => {
    const result = await fetchStatus(statusBaseUrl);
    if (!result.ok) {
      pollFailCount++;
      if (pollFailCount >= MAX_POLL_FAILS) {
        clearInterval(pollTimer);
        pollTimer = null;
        setMessage("백엔드 연결 실패 — 앱을 재시작하세요");
      }
      return;
    }

    pollFailCount = 0; // 성공하면 카운트 리셋
    const state = result.data && result.data.data ? result.data.data.state : result.data?.state;
    if (state === "idle") {
      notifyReadyOnce();
      clearInterval(pollTimer);
      pollTimer = null;
    }
  }, 1000);
}

window.addEventListener("DOMContentLoaded", async () => {
  if (window.lucide && typeof window.lucide.createIcons === "function") {
    window.lucide.createIcons();
  }

  try {
    const config = await window.geuldobiDesktop.getSplashConfig();
    if (config.firstRun) {
      setMessage("첫 실행은 잠시 시간이 걸립니다");
    } else {
      setMessage("시작하는 중...");
    }
    startPolling(config);
  } catch (err) {
    console.error("[splash] getSplashConfig failed:", err);
    setMessage("초기화 오류 — 앱을 재시작하세요");
  }
});

window.addEventListener("beforeunload", () => {
  if (pollTimer) {
    clearInterval(pollTimer);
    pollTimer = null;
  }
});
