(function () {
  const state = {
    summary: null,
    sessions: [],
    sessionsById: new Map(),
    eventsBySession: new Map(),
    selectedSessionId: null,
    selectedEventIndex: 0,
    compareSessionId: "",
    streamState: "connecting",
    stream: null,
    pollTimer: null,
    playbackTimer: null,
    playbackLive: true,
    filters: { kind: "", status: "", q: "" },
    wikiCards: [],
    topics: [],
    activeSubtab: "wiki",
  };

  function escapeHtml(value) {
    return String(value ?? "")
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;")
      .replaceAll('"', "&quot;");
  }

  function formatTime(value) {
    if (!value) return "--";
    const date = new Date(value);
    if (Number.isNaN(date.getTime())) return String(value);
    return date.toLocaleTimeString("zh-CN", {
      hour: "2-digit",
      minute: "2-digit",
      second: "2-digit",
    });
  }

  function formatMetric(value) {
    if (typeof value === "number") {
      return Number.isInteger(value) ? String(value) : value.toFixed(3).replace(/\.?0+$/, "");
    }
    if (typeof value === "boolean") {
      return value ? "true" : "false";
    }
    if (value == null || value === "") {
      return "--";
    }
    return String(value);
  }

  async function fetchJson(url) {
    const resp = await fetch(url, { cache: "no-store" });
    if (!resp.ok) {
      throw new Error(`${url} -> ${resp.status}`);
    }
    return await resp.json();
  }

  async function postJson(url, body) {
    const resp = await fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json; charset=utf-8" },
      body: JSON.stringify(body || {}),
    });
    const payload = await resp.json().catch(() => ({}));
    if (!resp.ok) {
      throw new Error(payload.error || `${url} -> ${resp.status}`);
    }
    return payload;
  }

  function upsertSession(session) {
    if (!session || !session.id) return;
    state.sessionsById.set(session.id, session);
    state.sessions = Array.from(state.sessionsById.values()).sort((a, b) =>
      String(b.started_at || "").localeCompare(String(a.started_at || ""))
    );
    if (!state.selectedSessionId) {
      state.selectedSessionId = session.id;
    }
  }

  function setSessionEvents(sessionId, events) {
    state.eventsBySession.set(sessionId, Array.isArray(events) ? events : []);
    const active = state.eventsBySession.get(sessionId) || [];
    if (state.playbackLive) {
      state.selectedEventIndex = Math.max(active.length - 1, 0);
    } else if (state.selectedEventIndex > active.length - 1) {
      state.selectedEventIndex = Math.max(active.length - 1, 0);
    }
  }

  function pushEvent(event) {
    if (!event || !event.session_id) return;
    const events = state.eventsBySession.get(event.session_id) || [];
    events.push(event);
    state.eventsBySession.set(event.session_id, events);
    if (state.selectedSessionId === event.session_id && state.playbackLive) {
      state.selectedEventIndex = Math.max(events.length - 1, 0);
    }
  }

  function selectedSession() {
    return state.sessionsById.get(state.selectedSessionId) || null;
  }

  function selectedEvents() {
    return state.eventsBySession.get(state.selectedSessionId) || [];
  }

  function selectedEvent() {
    const events = selectedEvents();
    if (events.length === 0) return null;
    return events[Math.max(0, Math.min(state.selectedEventIndex, events.length - 1))];
  }

  function dashboardCliCommand() {
    const port = window.location.port || "7821";
    return [
      "cd insights-share",
      "PYTHONPATH=demo_codes demo_codes/.venv/bin/python demo_codes/insights_cli.py serve \\",
      "  --host 0.0.0.0 \\",
      `  --port ${port} \\`,
      "  --store-mode tree \\",
      "  --store demo_codes/wiki_tree \\",
      "  --enable-runners",
    ].join("\n");
  }

  async function copyCliCommand(stateId) {
    const stateEl = document.getElementById(stateId);
    try {
      await navigator.clipboard.writeText(dashboardCliCommand());
      if (stateEl) stateEl.textContent = "已复制";
    } catch (error) {
      if (stateEl) stateEl.textContent = "复制失败";
    }
  }

  function renderCliCommand(targetId) {
    const target = document.getElementById(targetId);
    if (target) {
      target.textContent = dashboardCliCommand();
    }
  }

  function renderArtifacts(target, refs) {
    if (!target) return;
    const list = Array.isArray(refs) ? refs : [];
    if (list.length === 0) {
      target.innerHTML = '<div class="empty-note">当前没有证据链接。</div>';
      return;
    }
    target.innerHTML = list
      .map(
        (item) =>
          `<a class="artifact-link" href="${escapeHtml(item.href)}" target="_blank" rel="noreferrer">
            <strong>${escapeHtml(item.label || "artifact")}</strong>
            <div class="muted">${escapeHtml(item.href)}</div>
          </a>`
      )
      .join("");
  }

  function renderMetricGrid(target, metrics) {
    if (!target) return;
    const entries = Object.entries(metrics || {});
    if (entries.length === 0) {
      target.innerHTML = '<div class="empty-note">等待阶段指标。</div>';
      return;
    }
    target.innerHTML = entries
      .map(
        ([key, value]) =>
          `<div class="metric-item">
            <span class="metric-label">${escapeHtml(key)}</span>
            <strong>${escapeHtml(formatMetric(value))}</strong>
          </div>`
      )
      .join("");
  }

  function renderTimeline(target, events, activeIndex, attrName = "data-event-index") {
    if (!target) return;
    if (!events.length) {
      target.innerHTML = '<div class="empty-note">还没有过程事件。</div>';
      return;
    }
    target.innerHTML = events
      .map((event, index) => {
        const active = index === activeIndex ? "active" : "";
        return `<button class="timeline-event ${escapeHtml(event.status || "")} ${active}" ${attrName}="${index}">
          <strong>${escapeHtml(event.stage)}</strong>
          <div class="timeline-sub">${escapeHtml(event.message)}</div>
          <div class="timeline-sub">${escapeHtml(formatTime(event.ts))} · ${escapeHtml(event.status)}</div>
        </button>`;
      })
      .join("");
  }

  function renderPreview() {
    const session = selectedSession();
    const events = selectedEvents();
    const event = selectedEvent();

    const streamState = document.getElementById("stream-state");
    const liveLabel = document.getElementById("preview-live-label");
    const title = document.getElementById("preview-title");
    const kind = document.getElementById("preview-kind");
    const progress = document.getElementById("preview-progress");
    const stageName = document.getElementById("preview-stage-name");
    const status = document.getElementById("preview-status");
    const message = document.getElementById("preview-message");
    const metrics = document.getElementById("preview-metrics");
    const sessionStrip = document.getElementById("preview-session-strip");
    const slider = document.getElementById("preview-slider");
    const sliderLabel = document.getElementById("preview-slider-label");
    const timeline = document.getElementById("preview-timeline");
    const detail = document.getElementById("preview-event-detail");
    renderCliCommand("preview-cli-command");

    if (streamState) {
      streamState.textContent = state.streamState;
    }
    if (liveLabel) {
      liveLabel.textContent = state.playbackLive ? "实时流 /api/stream" : "历史回放";
    }
    if (session) {
      title.textContent = session.title;
      kind.textContent = String(session.kind || "").toUpperCase();
      progress.textContent = `${Math.round((session.progress || 0) * 100)}%`;
      stageName.textContent = session.current_stage || "pending";
      status.textContent = session.status || "running";
      message.textContent = session.latest_message || "等待事件";
      renderMetricGrid(metrics, session.headline_metrics || {});
    renderArtifacts(document.getElementById("preview-artifacts"), session.artifact_refs || []);
    } else {
      title.textContent = "等待实时 session";
      kind.textContent = "DEMO";
      progress.textContent = "0%";
      stageName.textContent = "pending";
      status.textContent = "idle";
      message.textContent = "连接到 daemon 后，这里会显示最新一条过程消息。";
      renderMetricGrid(metrics, {});
      renderArtifacts(document.getElementById("preview-artifacts"), []);
    }

    sessionStrip.innerHTML = state.sessions
      .slice(0, 8)
      .map((item) => {
        const active = item.id === state.selectedSessionId ? "active" : "";
        return `<button class="session-chip ${active}" data-session-id="${item.id}">
          <strong>${escapeHtml(item.title)}</strong>
          <div class="session-sub">${escapeHtml(item.kind)} · ${escapeHtml(item.status)} · ${escapeHtml(formatTime(item.started_at))}</div>
        </button>`;
      })
      .join("");

    slider.max = Math.max(events.length - 1, 0);
    slider.value = Math.max(0, Math.min(state.selectedEventIndex, Math.max(events.length - 1, 0)));
    sliderLabel.textContent = `${events.length ? state.selectedEventIndex + 1 : 0} / ${events.length}`;
    renderTimeline(timeline, events, state.selectedEventIndex);

    if (event) {
      detail.innerHTML = `
        <div class="section-label">当前节点</div>
        <h3>${escapeHtml(event.stage)} · ${escapeHtml(event.status)}</h3>
        <div>${escapeHtml(event.message)}</div>
        <div class="muted">${escapeHtml(formatTime(event.ts))} · ${escapeHtml(event.source)}</div>
        <pre class="payload">${escapeHtml(JSON.stringify({ payload: event.payload, metrics: event.metrics }, null, 2))}</pre>
      `;
    } else {
      detail.textContent = "选择某个 session 后，这里会展示当前回放节点的 message / payload / metrics。";
    }
  }

  function renderDashboard() {
    const session = selectedSession();
    const events = selectedEvents();
    const event = selectedEvent();

    const stateEl = document.getElementById("dashboard-stream-state");
    const liveSession = document.getElementById("dashboard-live-session");
    const summaryGrid = document.getElementById("dashboard-summary-grid");
    const cliCommand = document.getElementById("dashboard-cli-command");
    const title = document.getElementById("dashboard-title");
    const kind = document.getElementById("dashboard-kind");
    const progress = document.getElementById("dashboard-progress");
    const stageName = document.getElementById("dashboard-stage-name");
    const status = document.getElementById("dashboard-status");
    const timer = document.getElementById("dashboard-timer");
    const message = document.getElementById("dashboard-message");
    const metrics = document.getElementById("dashboard-metrics");
    const sessionStrip = document.getElementById("dashboard-session-strip");
    const slider = document.getElementById("dashboard-slider");
    const sliderLabel = document.getElementById("dashboard-slider-label");
    const timeline = document.getElementById("dashboard-timeline");
    const sessionList = document.getElementById("dashboard-session-list");
    const spotlight = document.getElementById("dashboard-event-spotlight");
    const eventList = document.getElementById("dashboard-event-list");
    const compareSelect = document.getElementById("dashboard-compare-select");
    const compareEl = document.getElementById("dashboard-compare");
    const runDemo = document.getElementById("dashboard-run-demo");
    const runValidation = document.getElementById("dashboard-run-validation");

    if (stateEl) {
      stateEl.textContent = state.streamState;
    }
    if (cliCommand) {
      cliCommand.textContent = dashboardCliCommand();
    }

    const summary = state.summary || { counts: { total: 0, by_kind: {}, by_status: {} }, runner_enabled: false };
    if (runDemo) runDemo.disabled = !summary.runner_enabled;
    if (runValidation) runValidation.disabled = !summary.runner_enabled;
    if (liveSession) {
      const live = summary.live_session || session;
      liveSession.textContent = live ? `${live.title} · ${live.status}` : "等待 session";
    }
    if (summaryGrid) {
      summaryGrid.innerHTML = `
        <div class="dashboard-summary-item">
          <span class="metric-label">总 Session</span>
          <strong>${escapeHtml(summary.counts?.total ?? 0)}</strong>
        </div>
        <div class="dashboard-summary-item">
          <span class="metric-label">Runner</span>
          <strong>${summary.runner_enabled ? "ON" : "OFF"}</strong>
        </div>
        <div class="dashboard-summary-item">
          <span class="metric-label">Demo</span>
          <strong>${escapeHtml(summary.counts?.by_kind?.demo ?? 0)}</strong>
        </div>
        <div class="dashboard-summary-item">
          <span class="metric-label">Validation</span>
          <strong>${escapeHtml(summary.counts?.by_kind?.validation ?? 0)}</strong>
        </div>
      `;
    }

    if (session) {
      title.textContent = session.title;
      kind.textContent = String(session.kind || "").toUpperCase();
      progress.textContent = `${Math.round((session.progress || 0) * 100)}%`;
      stageName.textContent = session.current_stage || "pending";
      status.textContent = session.status || "running";
      message.textContent = session.latest_message || "等待事件";
      renderMetricGrid(metrics, session.headline_metrics || {});
      renderArtifacts(document.getElementById("dashboard-artifacts"), session.artifact_refs || []);
    } else {
      title.textContent = "等待实时 session";
      kind.textContent = "DEMO";
      progress.textContent = "0%";
      stageName.textContent = "pending";
      status.textContent = "idle";
      message.textContent = "连接到 daemon 后，这里会显示当前主 session 的最新过程。";
      renderMetricGrid(metrics, {});
      renderArtifacts(document.getElementById("dashboard-artifacts"), []);
    }

    if (timer) {
      timer.textContent = `${events.length ? state.selectedEventIndex + 1 : 0} / ${events.length}`;
    }

    sessionStrip.innerHTML = state.sessions
      .slice(0, 6)
      .map((item) => {
        const active = item.id === state.selectedSessionId ? "active" : "";
        return `<button class="session-chip ${active}" data-dashboard-session-id="${item.id}">
          <strong>${escapeHtml(item.title)}</strong>
          <div class="session-sub">${escapeHtml(item.kind)} · ${escapeHtml(item.status)} · ${escapeHtml(formatTime(item.started_at))}</div>
        </button>`;
      })
      .join("");

    slider.max = Math.max(events.length - 1, 0);
    slider.value = Math.max(0, Math.min(state.selectedEventIndex, Math.max(events.length - 1, 0)));
    sliderLabel.textContent = `${events.length ? state.selectedEventIndex + 1 : 0} / ${events.length}`;
    renderTimeline(timeline, events, state.selectedEventIndex, "data-dashboard-event-index");

    sessionList.innerHTML = state.sessions
      .map((item) => {
        const active = item.id === state.selectedSessionId ? "active" : "";
        return `<button class="session-row ${active}" data-dashboard-session-id="${item.id}">
          <strong>${escapeHtml(item.title)}</strong>
          <div class="session-sub">${escapeHtml(item.kind)} · ${escapeHtml(item.status)} · ${escapeHtml(item.current_stage || "pending")}</div>
          <div class="session-sub">${escapeHtml(item.latest_message || "")}</div>
        </button>`;
      })
      .join("") || '<div class="empty-note">还没有运行中的 session。</div>';

    if (event) {
      spotlight.innerHTML = `
        <div class="section-label">当前节点</div>
        <h3>${escapeHtml(event.stage)} · ${escapeHtml(event.status)}</h3>
        <div>${escapeHtml(event.message)}</div>
        <div class="muted">${escapeHtml(formatTime(event.ts))} · ${escapeHtml(event.source)}</div>
        <pre class="payload">${escapeHtml(JSON.stringify({ payload: event.payload, metrics: event.metrics }, null, 2))}</pre>
      `;
    } else {
      spotlight.textContent = "选择 session 或拖动时间线后，这里会显示当前节点的 payload 与 metrics。";
    }

    renderTimeline(eventList, events, state.selectedEventIndex, "data-dashboard-event-index");

    if (session) {
      const options = state.sessions
        .filter((item) => item.kind === session.kind && item.id !== session.id)
        .map((item) => `<option value="${item.id}" ${item.id === state.compareSessionId ? "selected" : ""}>${escapeHtml(item.title)}</option>`)
        .join("");
      compareSelect.innerHTML = `<option value="">选择对比对象</option>${options}`;
      const compareTarget = state.sessionsById.get(state.compareSessionId) || null;
      if (compareTarget) {
        const currentMetrics = session.headline_metrics || {};
        const otherMetrics = compareTarget.headline_metrics || {};
        const keys = Array.from(new Set([...Object.keys(currentMetrics), ...Object.keys(otherMetrics)]));
        compareEl.innerHTML = keys.length
          ? `<div class="dashboard-compare-grid">${keys
              .map((key) => {
                const a = currentMetrics[key];
                const b = otherMetrics[key];
                return `<div class="dashboard-compare-row">
                  <strong>${escapeHtml(key)}</strong>
                  <div class="muted">当前 ${escapeHtml(formatMetric(a))}</div>
                  <div class="muted">对比 ${escapeHtml(formatMetric(b))}</div>
                </div>`;
              })
              .join("")}</div>`
          : '<div class="empty-note">两条 session 还没有可比的 headline metrics。</div>';
      } else {
        compareEl.textContent = "选择对比对象后，这里会显示 headline metrics 的差异。";
      }
    } else {
      compareSelect.innerHTML = '<option value="">选择对比对象</option>';
      compareEl.textContent = "选择对比对象后，这里会显示 headline metrics 的差异。";
    }

    renderOpsCollections();
  }

  function renderOps() {
    const sessionsEl = document.getElementById("ops-sessions");
    const timelineEl = document.getElementById("ops-timeline");
    const summaryBar = document.getElementById("ops-summary-bar");
    const detailEl = document.getElementById("ops-session-detail");
    const compareSelect = document.getElementById("ops-compare-select");
    const compareEl = document.getElementById("ops-compare");
    const stateEl = document.getElementById("ops-stream-state");
    const runDemo = document.getElementById("run-demo");
    const runValidation = document.getElementById("run-validation");
    renderCliCommand("ops-cli-command");

    if (stateEl) {
      stateEl.textContent = state.streamState;
    }

    const summary = state.summary || { counts: { total: 0, by_kind: {}, by_status: {} }, runner_enabled: false };
    if (runDemo) runDemo.disabled = !summary.runner_enabled;
    if (runValidation) runValidation.disabled = !summary.runner_enabled;

    summaryBar.innerHTML = `
      <div class="badge-inline">总 session ${escapeHtml(summary.counts?.total ?? 0)}</div>
      <div class="badge-inline">demo ${escapeHtml(summary.counts?.by_kind?.demo ?? 0)}</div>
      <div class="badge-inline">validation ${escapeHtml(summary.counts?.by_kind?.validation ?? 0)}</div>
      <div class="badge-inline">runner ${summary.runner_enabled ? "ON" : "OFF"}</div>
    `;

    sessionsEl.innerHTML = state.sessions
      .filter((item) => !state.filters.kind || item.kind === state.filters.kind)
      .filter((item) => !state.filters.status || item.status === state.filters.status)
      .filter((item) => {
        if (!state.filters.q) return true;
        const q = state.filters.q.toLowerCase();
        return String(item.title || "").toLowerCase().includes(q) || String(item.latest_message || "").toLowerCase().includes(q);
      })
      .map((item) => {
        const active = item.id === state.selectedSessionId ? "active" : "";
        return `<button class="session-row ${active}" data-session-id="${item.id}">
          <strong>${escapeHtml(item.title)}</strong>
          <div class="session-sub">${escapeHtml(item.kind)} · ${escapeHtml(item.status)} · ${escapeHtml(item.current_stage || "pending")}</div>
          <div class="session-sub">${escapeHtml(item.latest_message || "")}</div>
        </button>`;
      })
      .join("") || '<div class="empty-note">没有命中的 session。</div>';

    const events = selectedEvents();
    renderTimeline(timelineEl, events, state.selectedEventIndex);

    const session = selectedSession();
    const event = selectedEvent();
    if (session) {
      detailEl.innerHTML = `
        <strong>${escapeHtml(session.title)}</strong>
        <div class="muted">${escapeHtml(session.kind)} · ${escapeHtml(session.status)} · ${escapeHtml(session.current_stage || "pending")}</div>
        <div class="muted">开始于 ${escapeHtml(formatTime(session.started_at))}</div>
        <pre class="payload">${escapeHtml(JSON.stringify({
          latest_message: session.latest_message,
          headline_metrics: session.headline_metrics,
          current_event: event,
          artifact_refs: session.artifact_refs,
        }, null, 2))}</pre>
      `;
    } else {
      detailEl.textContent = "选择左侧 session 查看详情。";
    }

    if (session) {
      const options = state.sessions
        .filter((item) => item.kind === session.kind && item.id !== session.id)
        .map((item) => `<option value="${item.id}" ${item.id === state.compareSessionId ? "selected" : ""}>${escapeHtml(item.title)}</option>`)
        .join("");
      compareSelect.innerHTML = `<option value="">选择对比对象</option>${options}`;
      const compareTarget = state.sessionsById.get(state.compareSessionId) || null;
      if (compareTarget) {
        const currentMetrics = session.headline_metrics || {};
        const otherMetrics = compareTarget.headline_metrics || {};
        const keys = Array.from(new Set([...Object.keys(currentMetrics), ...Object.keys(otherMetrics)]));
        compareEl.innerHTML = keys.length
          ? keys
              .map((key) => {
                const a = currentMetrics[key];
                const b = otherMetrics[key];
                return `<div class="wiki-row">
                  <strong>${escapeHtml(key)}</strong>
                  <div class="muted">当前 ${escapeHtml(formatMetric(a))} · 对比 ${escapeHtml(formatMetric(b))}</div>
                </div>`;
              })
              .join("")
          : '<div class="empty-note">两条 session 还没有可比的 headline metrics。</div>';
      } else {
        compareEl.textContent = "选择对比对象后，这里会显示 headline metrics 差异。";
      }
    } else {
      compareSelect.innerHTML = '<option value="">选择对比对象</option>';
      compareEl.textContent = "选择对比对象后，这里会显示 headline metrics 差异。";
    }

    renderOpsCollections();
  }

  function renderOpsCollections() {
    const wikiPanel = document.getElementById("ops-wiki-panel");
    const topicsPanel = document.getElementById("ops-topics-panel");
    const dashboardWiki = document.getElementById("dashboard-wiki-panel");
    const dashboardTopics = document.getElementById("dashboard-topics-panel");

    const wikiHtml = state.wikiCards.length
      ? state.wikiCards
          .slice(0, 8)
          .map(
            (card) => `<div class="wiki-row">
              <strong>${escapeHtml(card.title || card.id)}</strong>
              <div class="muted">${escapeHtml(card.id)} · ${escapeHtml((card.tags || []).join(", "))}</div>
            </div>`
          )
          .join("")
      : '<div class="empty-note">还没有加载到 wiki 卡片。</div>';

    const topicsHtml = state.topics.length
      ? state.topics
          .slice(0, 8)
          .map(
            (topic) => `<div class="topic-row">
              <strong>${escapeHtml(topic.title || topic.id)}</strong>
              <div class="muted">${escapeHtml(topic.id)} · ${escapeHtml(topic.wiki_type || "general")}</div>
            </div>`
          )
              .join("")
      : '<div class="empty-note">当前没有 topic 数据。</div>';

    if (wikiPanel) wikiPanel.innerHTML = wikiHtml;
    if (topicsPanel) topicsPanel.innerHTML = topicsHtml;
    if (dashboardWiki) dashboardWiki.innerHTML = wikiHtml;
    if (dashboardTopics) dashboardTopics.innerHTML = topicsHtml;
  }

  async function hydrateCollections() {
    try {
      const cards = await fetchJson("/insights");
      state.wikiCards = cards.cards || [];
    } catch (error) {
      state.wikiCards = [];
    }
    try {
      const topics = await fetchJson("/topics");
      state.topics = topics.topics || [];
    } catch (error) {
      state.topics = [];
    }
  }

  async function refreshSummary() {
    state.summary = await fetchJson("/api/system/summary");
    (state.summary.recent_sessions || []).forEach(upsertSession);
    if (!state.selectedSessionId && state.summary.live_session) {
      state.selectedSessionId = state.summary.live_session.id;
    }
  }

  async function refreshSessions() {
    const params = new URLSearchParams();
    if (state.filters.kind) params.set("kind", state.filters.kind);
    if (state.filters.status) params.set("status", state.filters.status);
    if (state.filters.q) params.set("q", state.filters.q);
    params.set("limit", "30");
    const payload = await fetchJson(`/api/sessions?${params.toString()}`);
    (payload.sessions || []).forEach(upsertSession);
  }

  async function loadSession(sessionId) {
    if (!sessionId) return;
    state.selectedSessionId = sessionId;
    const payload = await fetchJson(`/api/sessions/${sessionId}/events`);
    if (payload.session) {
      upsertSession(payload.session);
    }
    setSessionEvents(sessionId, payload.events || []);
    renderAll();
  }

  function applyMessage(message) {
    if (!message || message.type !== "session.update") return;
    if (message.session) {
      upsertSession(message.session);
    }
    if (message.event) {
      pushEvent(message.event);
    }
    if (!state.selectedSessionId && message.session) {
      state.selectedSessionId = message.session.id;
    }
    renderAll();
  }

  function startPolling() {
    clearInterval(state.pollTimer);
    state.pollTimer = window.setInterval(async () => {
      try {
        await refreshAll();
      } catch (error) {
        state.streamState = "polling-error";
        renderAll();
      }
    }, 5000);
  }

  function connectStream() {
    if (state.stream) {
      state.stream.close();
    }
    if (typeof EventSource === "undefined") {
      state.streamState = "polling";
      startPolling();
      renderAll();
      return;
    }
    state.streamState = "live";
    const stream = new EventSource("/api/stream");
    state.stream = stream;
    stream.addEventListener("hello", (event) => {
      try {
        const payload = JSON.parse(event.data);
        state.summary = payload;
        (payload.recent_sessions || []).forEach(upsertSession);
        if (!state.selectedSessionId && payload.live_session) {
          state.selectedSessionId = payload.live_session.id;
        }
      } catch (error) {}
      renderAll();
    });
    stream.addEventListener("session.update", async (event) => {
      try {
        applyMessage(JSON.parse(event.data));
      } catch (error) {}
      const session = selectedSession();
      if (session && !state.eventsBySession.has(session.id)) {
        await loadSession(session.id);
      }
    });
    stream.onerror = () => {
      state.streamState = "polling";
      renderAll();
      stream.close();
      startPolling();
    };
  }

  async function refreshAll() {
    await refreshSummary();
    await refreshSessions();
    if (state.selectedSessionId) {
      await loadSession(state.selectedSessionId);
    } else {
      renderAll();
    }
    if (["ops", "dashboard"].includes(document.body.dataset.mode || "")) {
      await hydrateCollections();
      renderAll();
    }
  }

  function togglePlayback() {
    if (state.playbackTimer) {
      clearInterval(state.playbackTimer);
      state.playbackTimer = null;
      renderPlayButton();
      return;
    }
    state.playbackLive = false;
    state.playbackTimer = window.setInterval(() => {
      const events = selectedEvents();
      if (!events.length) return;
      if (state.selectedEventIndex >= events.length - 1) {
        clearInterval(state.playbackTimer);
        state.playbackTimer = null;
        renderPlayButton();
        return;
      }
      state.selectedEventIndex += 1;
      renderAll();
    }, 900);
    renderPlayButton();
  }

  function renderPlayButton() {
    const label = state.playbackTimer ? "暂停回放" : "播放回放";
    const previewPlay = document.getElementById("preview-play");
    const dashboardPlay = document.getElementById("dashboard-play");
    if (previewPlay) previewPlay.textContent = label;
    if (dashboardPlay) dashboardPlay.textContent = label;
  }

  function renderAll() {
    if (document.body.dataset.mode === "preview") {
      renderPreview();
      renderPlayButton();
    } else if (document.body.dataset.mode === "dashboard") {
      renderDashboard();
      renderPlayButton();
    } else {
      renderOps();
    }
  }

  function bindPreview() {
    document.getElementById("preview-play")?.addEventListener("click", togglePlayback);
    document.getElementById("preview-live")?.addEventListener("click", () => {
      state.playbackLive = true;
      const events = selectedEvents();
      state.selectedEventIndex = Math.max(events.length - 1, 0);
      renderAll();
    });
    document.getElementById("preview-slider")?.addEventListener("input", (event) => {
      state.playbackLive = false;
      state.selectedEventIndex = Number(event.target.value || 0);
      renderAll();
    });
    document.getElementById("preview-copy-cli")?.addEventListener("click", async () => {
      await copyCliCommand("preview-copy-state");
    });
    document.addEventListener("click", (event) => {
      const sessionBtn = event.target.closest("[data-session-id]");
      if (sessionBtn && document.body.dataset.mode === "preview") {
        state.playbackLive = true;
        loadSession(sessionBtn.getAttribute("data-session-id"));
      }
      const eventBtn = event.target.closest("[data-event-index]");
      if (eventBtn && document.body.dataset.mode === "preview") {
        state.playbackLive = false;
        state.selectedEventIndex = Number(eventBtn.getAttribute("data-event-index") || 0);
        renderAll();
      }
    });
  }

  function bindOps() {
    document.getElementById("filter-kind")?.addEventListener("change", async (event) => {
      state.filters.kind = event.target.value;
      await refreshSessions();
      renderAll();
    });
    document.getElementById("filter-status")?.addEventListener("change", async (event) => {
      state.filters.status = event.target.value;
      await refreshSessions();
      renderAll();
    });
    document.getElementById("filter-q")?.addEventListener("input", async (event) => {
      state.filters.q = event.target.value;
      await refreshSessions();
      renderAll();
    });
    document.getElementById("run-demo")?.addEventListener("click", async () => {
      const payload = await postJson("/api/runs/demo", { problem: "postgres 连接池耗尽" });
      await loadSession(payload.session_id);
    });
    document.getElementById("run-validation")?.addEventListener("click", async () => {
      const payload = await postJson("/api/runs/validation", {});
      await loadSession(payload.session_id);
    });
    document.getElementById("stream-reconnect")?.addEventListener("click", () => {
      connectStream();
    });
    document.getElementById("ops-compare-select")?.addEventListener("change", (event) => {
      state.compareSessionId = event.target.value;
      renderAll();
    });
    document.getElementById("ops-copy-cli")?.addEventListener("click", async () => {
      await copyCliCommand("ops-copy-state");
    });
    document.addEventListener("click", (event) => {
      const sessionBtn = event.target.closest("[data-session-id]");
      if (sessionBtn && document.body.dataset.mode === "ops") {
        loadSession(sessionBtn.getAttribute("data-session-id"));
      }
      const eventBtn = event.target.closest("[data-event-index]");
      if (eventBtn && document.body.dataset.mode === "ops") {
        state.selectedEventIndex = Number(eventBtn.getAttribute("data-event-index") || 0);
        renderAll();
      }
      const subtab = event.target.closest("[data-subtab]");
      if (subtab) {
        state.activeSubtab = subtab.getAttribute("data-subtab");
        document.querySelectorAll(".subtab").forEach((node) => node.classList.toggle("active", node === subtab));
        document.getElementById("ops-wiki-panel")?.classList.toggle("hidden", state.activeSubtab !== "wiki");
        document.getElementById("ops-topics-panel")?.classList.toggle("hidden", state.activeSubtab !== "topics");
      }
    });
  }

  function bindDashboard() {
    document.getElementById("dashboard-run-demo")?.addEventListener("click", async () => {
      const payload = await postJson("/api/runs/demo", { problem: "postgres 连接池耗尽" });
      state.playbackLive = true;
      await loadSession(payload.session_id);
    });
    document.getElementById("dashboard-run-validation")?.addEventListener("click", async () => {
      const payload = await postJson("/api/runs/validation", {});
      state.playbackLive = true;
      await loadSession(payload.session_id);
    });
    document.getElementById("dashboard-play")?.addEventListener("click", togglePlayback);
    document.getElementById("dashboard-live")?.addEventListener("click", () => {
      state.playbackLive = true;
      const events = selectedEvents();
      state.selectedEventIndex = Math.max(events.length - 1, 0);
      renderAll();
    });
    document.getElementById("dashboard-slider")?.addEventListener("input", (event) => {
      state.playbackLive = false;
      state.selectedEventIndex = Number(event.target.value || 0);
      renderAll();
    });
    document.getElementById("dashboard-compare-select")?.addEventListener("change", (event) => {
      state.compareSessionId = event.target.value;
      renderAll();
    });
    document.getElementById("dashboard-copy-cli")?.addEventListener("click", async () => {
      await copyCliCommand("dashboard-copy-state");
    });
    document.addEventListener("click", (event) => {
      const sessionBtn = event.target.closest("[data-dashboard-session-id]");
      if (sessionBtn) {
        state.playbackLive = true;
        loadSession(sessionBtn.getAttribute("data-dashboard-session-id"));
      }
      const eventBtn = event.target.closest("[data-dashboard-event-index]");
      if (eventBtn) {
        state.playbackLive = false;
        state.selectedEventIndex = Number(eventBtn.getAttribute("data-dashboard-event-index") || 0);
        renderAll();
      }
      const subtab = event.target.closest("[data-dashboard-subtab]");
      if (subtab) {
        state.activeSubtab = subtab.getAttribute("data-dashboard-subtab");
        document.querySelectorAll("[data-dashboard-subtab]").forEach((node) => node.classList.toggle("active", node === subtab));
        document.getElementById("dashboard-wiki-panel")?.classList.toggle("hidden", state.activeSubtab !== "wiki");
        document.getElementById("dashboard-topics-panel")?.classList.toggle("hidden", state.activeSubtab !== "topics");
      }
    });
  }

  async function init() {
    if (document.body.dataset.mode === "preview") {
      bindPreview();
    } else if (document.body.dataset.mode === "dashboard") {
      bindDashboard();
    } else {
      bindOps();
    }
    await refreshAll();
    connectStream();
  }

  window.addEventListener("DOMContentLoaded", () => {
    init().catch((error) => {
      state.streamState = `error: ${error.message}`;
      renderAll();
    });
  });
})();
