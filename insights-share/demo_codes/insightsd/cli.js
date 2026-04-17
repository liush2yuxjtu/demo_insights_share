(function () {
  const storageKey = "insights-cli-sidebar-hidden";
  const narrowQuery = window.matchMedia("(max-width: 1100px)");

  const state = {
    panes: [],
    selectedTarget: "",
    content: "",
    connected: false,
    available: false,
    inputEnabled: false,
    lastUpdated: "",
    lineCount: 0,
    pollTimer: null,
    loading: false,
    sidebarOpen: false,
    sidebarVisible: readSidebarPreference(),
  };

  function readSidebarPreference() {
    try {
      return window.localStorage.getItem(storageKey) !== "1";
    } catch {
      return true;
    }
  }

  function saveSidebarPreference(hidden) {
    try {
      window.localStorage.setItem(storageKey, hidden ? "1" : "0");
    } catch {}
  }

  function escapeHtml(value) {
    return String(value ?? "")
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;")
      .replaceAll('"', "&quot;");
  }

  function isNarrowViewport() {
    return narrowQuery.matches;
  }

  function formatTime(value) {
    if (!value) return "--";
    const date = new Date(value);
    if (Number.isNaN(date.getTime())) return value;
    return date.toLocaleString("zh-CN", {
      month: "2-digit",
      day: "2-digit",
      hour: "2-digit",
      minute: "2-digit",
      second: "2-digit",
      hour12: false,
    });
  }

  function chooseDefaultPane(panes) {
    const claudePane = panes.find((item) => /claude/i.test(String(item.command || "")));
    return (claudePane || panes[0] || {}).target || "";
  }

  function currentPane() {
    return state.panes.find((item) => item.target === state.selectedTarget) || null;
  }

  function setStatus(text) {
    const node = document.getElementById("cli-send-state");
    if (node) node.textContent = text;
  }

  async function fetchJson(url) {
    const resp = await fetch(url, { cache: "no-store" });
    const payload = await resp.json().catch(() => ({}));
    if (!resp.ok) {
      throw new Error(payload.detail || payload.error || `${url} -> ${resp.status}`);
    }
    return payload;
  }

  async function postJson(url, body) {
    const resp = await fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json; charset=utf-8" },
      body: JSON.stringify(body || {}),
    });
    const payload = await resp.json().catch(() => ({}));
    if (!resp.ok) {
      throw new Error(payload.detail || payload.error || `${url} -> ${resp.status}`);
    }
    return payload;
  }

  function applyLayoutState() {
    const narrow = isNarrowViewport();
    document.body.classList.toggle("sidebar-open", narrow && state.sidebarOpen);
    document.body.classList.toggle("sidebar-hidden", !narrow && !state.sidebarVisible);

    const toggle = document.getElementById("cli-sidebar-toggle");
    if (!toggle) return;
    const expanded = narrow ? state.sidebarOpen : state.sidebarVisible;
    toggle.textContent = expanded ? "收起 pane 列表" : "展开 pane 列表";
    toggle.setAttribute("aria-expanded", expanded ? "true" : "false");
  }

  function render() {
    applyLayoutState();

    const connection = document.getElementById("cli-connection");
    const inputBadge = document.getElementById("cli-input-badge");
    const paneCount = document.getElementById("cli-pane-count");
    const paneList = document.getElementById("cli-pane-list");
    const targetMeta = document.getElementById("cli-target-meta");
    const targetLabel = document.getElementById("cli-target-label");
    const paneName = document.getElementById("cli-pane-name");
    const lastUpdated = document.getElementById("cli-last-updated");
    const captureLines = document.getElementById("cli-capture-lines");
    const screen = document.getElementById("cli-screen");
    const input = document.getElementById("cli-input");
    const send = document.getElementById("cli-send");
    const ctrlC = document.getElementById("cli-ctrl-c");

    if (connection) {
      connection.textContent = state.loading ? "更新中" : state.connected ? "tmux 已连接" : state.available ? "tmux 无 session" : "tmux 不可用";
    }
    if (inputBadge) {
      inputBadge.textContent = state.inputEnabled ? "本机浏览器可输入" : "当前只读";
    }
    if (paneCount) {
      paneCount.textContent = `${state.panes.length} 个 pane`;
    }

    if (paneList) {
      paneList.innerHTML = state.panes.length
        ? state.panes
            .map((pane) => {
              const active = pane.target === state.selectedTarget ? "active" : "";
              return `<button class="pane-chip ${active}" data-pane-target="${escapeHtml(pane.target)}">
                <strong>${escapeHtml(pane.target)}</strong>
                <span>${escapeHtml(pane.command || "shell")} · ${escapeHtml(pane.window || "")}</span>
                <span>${escapeHtml(pane.title || "")}</span>
              </button>`;
            })
            .join("")
        : '<div class="empty-note">当前没有可映射的 tmux pane。</div>';
    }

    const pane = currentPane();
    if (targetLabel) {
      targetLabel.textContent = pane ? pane.target : "未选择 pane";
    }
    if (paneName) {
      paneName.textContent = pane ? pane.target : "--";
    }
    if (lastUpdated) {
      lastUpdated.textContent = formatTime(state.lastUpdated);
    }
    if (captureLines) {
      captureLines.textContent = `${state.lineCount} 行`;
    }
    if (targetMeta) {
      targetMeta.innerHTML = pane
        ? `session：${escapeHtml(pane.session || "--")}<br>window：${escapeHtml(pane.window || "--")}<br>command：${escapeHtml(pane.command || "--")}<br>title：${escapeHtml(pane.title || "--")}<br>last updated：${escapeHtml(formatTime(state.lastUpdated))}`
        : "等待 tmux pane。";
    }
    if (screen) {
      const nextText = state.content || "等待 tmux pane ...";
      const changed = screen.textContent !== nextText;
      const pinnedBottom = screen.scrollTop + screen.clientHeight >= screen.scrollHeight - 48;
      if (changed) {
        screen.textContent = nextText;
        screen.classList.remove("live-pulse");
        void screen.offsetWidth;
        screen.classList.add("live-pulse");
        if (pinnedBottom) {
          screen.scrollTop = screen.scrollHeight;
        }
      }
    }
    if (input) input.disabled = !state.inputEnabled || !state.selectedTarget;
    if (send) send.disabled = !state.inputEnabled || !state.selectedTarget;
    if (ctrlC) ctrlC.disabled = !state.inputEnabled || !state.selectedTarget;
  }

  async function loadSummary() {
    state.loading = true;
    render();
    try {
      const payload = await fetchJson("/api/cli/tmux/summary");
      state.available = Boolean(payload.available);
      state.connected = Boolean(payload.connected);
      state.inputEnabled = Boolean(payload.input_enabled);
      state.panes = Array.isArray(payload.panes) ? payload.panes : [];
      if (!state.selectedTarget || !state.panes.some((item) => item.target === state.selectedTarget)) {
        state.selectedTarget = chooseDefaultPane(state.panes);
      }
    } finally {
      state.loading = false;
    }
  }

  async function loadCapture() {
    if (!state.selectedTarget) {
      state.content = "";
      state.lastUpdated = "";
      state.lineCount = 0;
      render();
      return;
    }
    try {
      const payload = await fetchJson(`/api/cli/tmux?target=${encodeURIComponent(state.selectedTarget)}&lines=400`);
      state.content = payload.content || "";
      state.lastUpdated = payload.updated_at || "";
      state.lineCount = String(payload.content || "").split("\n").length;
    } catch (error) {
      state.content = `capture failed:\n${error.message}`;
      state.lineCount = String(state.content).split("\n").length;
    }
    render();
  }

  async function refreshAll() {
    await loadSummary();
    await loadCapture();
  }

  function startPolling() {
    clearInterval(state.pollTimer);
    state.pollTimer = window.setInterval(() => {
      refreshAll().catch((error) => {
        state.content = `poll failed:\n${error.message}`;
        state.lineCount = String(state.content).split("\n").length;
        render();
      });
    }, 1200);
  }

  async function sendInput(control) {
    const input = document.getElementById("cli-input");
    if (!state.selectedTarget) return;
    setStatus("发送中");
    try {
      if (control) {
        await postJson("/api/cli/tmux/input", {
          target: state.selectedTarget,
          control,
        });
      } else {
        const text = (input?.value || "").trim();
        if (!text) {
          setStatus("输入为空");
          return;
        }
        await postJson("/api/cli/tmux/input", {
          target: state.selectedTarget,
          text,
          enter: true,
        });
        if (input) input.value = "";
      }
      setStatus("已发送");
      await loadCapture();
    } catch (error) {
      setStatus(`发送失败: ${error.message}`);
    }
  }

  function toggleSidebar() {
    if (isNarrowViewport()) {
      state.sidebarOpen = !state.sidebarOpen;
    } else {
      state.sidebarVisible = !state.sidebarVisible;
      saveSidebarPreference(!state.sidebarVisible);
    }
    render();
  }

  function closeSidebar() {
    if (!isNarrowViewport()) return;
    state.sidebarOpen = false;
    render();
  }

  function bind() {
    document.getElementById("cli-refresh")?.addEventListener("click", () => {
      refreshAll().catch((error) => setStatus(`刷新失败: ${error.message}`));
    });
    document.getElementById("cli-sidebar-toggle")?.addEventListener("click", () => {
      toggleSidebar();
    });
    document.getElementById("cli-sidebar-close")?.addEventListener("click", () => {
      closeSidebar();
    });
    document.getElementById("cli-copy-screen")?.addEventListener("click", async () => {
      try {
        await navigator.clipboard.writeText(state.content || "");
        setStatus("屏幕已复制");
      } catch (error) {
        setStatus("复制失败");
      }
    });
    document.getElementById("cli-ctrl-c")?.addEventListener("click", async () => {
      await sendInput("c");
    });
    document.getElementById("cli-compose")?.addEventListener("submit", async (event) => {
      event.preventDefault();
      await sendInput(null);
    });
    document.getElementById("cli-input")?.addEventListener("keydown", async (event) => {
      if ((event.metaKey || event.ctrlKey) && event.key === "Enter") {
        event.preventDefault();
        await sendInput(null);
      }
    });
    document.addEventListener("click", async (event) => {
      const pane = event.target.closest("[data-pane-target]");
      if (!pane) return;
      state.selectedTarget = pane.getAttribute("data-pane-target") || "";
      render();
      if (isNarrowViewport()) {
        state.sidebarOpen = false;
      }
      await loadCapture();
    });
    document.addEventListener("keydown", (event) => {
      if (event.key === "Escape") {
        closeSidebar();
      }
    });
    window.addEventListener("resize", () => {
      if (!isNarrowViewport()) {
        state.sidebarOpen = false;
      }
      render();
    });
  }

  window.addEventListener("DOMContentLoaded", () => {
    bind();
    render();
    refreshAll()
      .then(startPolling)
      .catch((error) => {
        state.content = `init failed:\n${error.message}`;
        state.lineCount = String(state.content).split("\n").length;
        render();
      });
  });
})();
