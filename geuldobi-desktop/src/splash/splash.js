const statusMessageEl = document.getElementById("statusMessage");

let pollTimer = null;
let didNotifyReady = false;

function setMessage(text) {
  statusMessageEl.textContent = text;
}

async function fetchStatus(statusBaseUrl) {
  try {
    const res = await fetch(`${statusBaseUrl}/status`, {
      method: "GET",
      cache: "no-store"
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
  window.geuldobiDesktop.notifyBackendReady();
}

async function startPolling(config) {
  const { statusBaseUrl } = config;
  pollTimer = setInterval(async () => {
    const result = await fetchStatus(statusBaseUrl);
    if (!result.ok) {
      return;
    }

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

  const config = await window.geuldobiDesktop.getSplashConfig();
  if (config.firstRun) {
    setMessage("첫 실행은 잠시 시간이 걸립니다");
  } else {
    setMessage("시작하는 중...");
  }

  startPolling(config);
});

window.addEventListener("beforeunload", () => {
  if (pollTimer) {
    clearInterval(pollTimer);
    pollTimer = null;
  }
});
