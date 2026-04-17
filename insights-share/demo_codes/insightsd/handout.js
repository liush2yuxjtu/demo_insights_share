const PROMPT_TEXT = "请只回复：CLI 输入链路已验证";
const HANDOUT_ROOT = "/Users/m1/projects/demo_insights_share/insights-share/demo_codes";
const DAEMON_COMMAND = `cd ${HANDOUT_ROOT} && export NO_PROXY=127.0.0.1,localhost && ./.venv/bin/python insights_cli.py serve --host 127.0.0.1 --port 7821 --store-mode tree --store ./wiki_tree --runtime-dir ./runtime-web --enable-runners`;
const WATCH_INTERVAL_MS = 3000;

const state = {
  baselineSessionIds: new Set(),
  watchers: new Map(),
  recordingStatus: null,
};

const BASELINE_STORAGE_KEY = "handoutBaselineSessionIds";

function stepNode(stepId) {
  return document.querySelector(`[data-step-id="${stepId}"]`);
}

function setText(target, value) {
  if (!target) {
    return;
  }
  target.textContent = value;
}

function setStep(stepId, payload) {
  const node = stepNode(stepId);
  if (!node) {
    return;
  }
  const status = node.querySelector("[data-step-status]");
  const signal = node.querySelector("[data-step-signal]");
  const failure = node.querySelector("[data-step-failure]");
  const why = node.querySelector("[data-step-why]");
  if (status && payload.status) {
    status.textContent = payload.status;
  }
  if (signal && payload.signal) {
    signal.textContent = payload.signal;
  }
  if (failure && payload.failure) {
    failure.textContent = payload.failure;
  }
  if (why && payload.why) {
    why.textContent = payload.why;
  }
  node.dataset.state = payload.tone || "idle";
}

async function getJson(url) {
  const response = await fetch(url, { cache: "no-store" });
  if (!response.ok) {
    throw new Error(`${url} -> ${response.status}`);
  }
  return response.json();
}

function extractSessions(payload) {
  if (Array.isArray(payload)) {
    return payload;
  }
  if (Array.isArray(payload?.sessions)) {
    return payload.sessions;
  }
  if (Array.isArray(payload?.items)) {
    return payload.items;
  }
  return [];
}

function sessionId(session) {
  return String(
    session?.id ??
      session?.session_id ??
      session?.run_id ??
      session?.slug ??
      session?.created_at ??
      JSON.stringify(session)
  );
}

function asText(values) {
  return values
    .filter((value) => value !== null && value !== undefined)
    .map((value) => String(value))
    .join(" ")
    .toLowerCase();
}

function matchesSession(session, keyword) {
  const haystack = asText([
    session?.type,
    session?.kind,
    session?.mode,
    session?.name,
    session?.label,
    session?.title,
    session?.summary,
  ]);
  return haystack.includes(keyword);
}

function isFinished(session) {
  const status = asText([session?.status, session?.state, session?.phase]);
  if (["done", "passed", "completed", "succeeded", "success", "finished"].some((item) => status.includes(item))) {
    return true;
  }
  if (session?.completed_at || session?.finished_at) {
    return true;
  }
  return false;
}

function validationCounts(session) {
  const total = Number(
    session?.total ??
      session?.summary?.total ??
      session?.metrics?.total ??
      session?.headline_metrics?.total ??
      0
  );
  const passed = Number(
    session?.passed ??
      session?.summary?.passed ??
      session?.metrics?.passed ??
      session?.headline_metrics?.passed ??
      0
  );
  return { total, passed };
}

function persistBaseline() {
  try {
    window.sessionStorage.setItem(
      BASELINE_STORAGE_KEY,
      JSON.stringify(Array.from(state.baselineSessionIds))
    );
  } catch (error) {
    console.warn("baseline persist failed", error);
  }
}

function hydrateBaseline() {
  if (state.baselineSessionIds.size > 0) {
    return;
  }
  try {
    const raw = window.sessionStorage.getItem(BASELINE_STORAGE_KEY);
    if (!raw) {
      return;
    }
    const parsed = JSON.parse(raw);
    if (!Array.isArray(parsed) || !parsed.length) {
      return;
    }
    parsed.forEach((item) => state.baselineSessionIds.add(String(item)));
    setText(
      document.getElementById("handout-baseline"),
      `已恢复基线：本轮浏览器会话里已有 ${parsed.length} 条 session 被视为起点。`
    );
  } catch (error) {
    console.warn("baseline hydrate failed", error);
  }
}

function recordBaseline(sessions) {
  if (state.baselineSessionIds.size > 0) {
    return;
  }
  sessions.forEach((session) => state.baselineSessionIds.add(sessionId(session)));
  persistBaseline();
  setText(document.getElementById("handout-baseline"), `已记录基线：当前已有 ${sessions.length} 条 session；后续只统计你现场新增的结果。`);
}

async function fetchSessions() {
  const payload = await getJson("/api/sessions");
  return extractSessions(payload);
}

async function checkStartService() {
  try {
    await getJson("/healthz");
    setText(document.getElementById("handout-daemon-state"), "daemon 已连接");
    setStep("start_service", {
      status: "已通过",
      tone: "passed",
      signal: "通过标准已满足：/healthz 可达，本页确认 daemon 在线。",
      failure: "如果后面突然失败，优先回终端确认启动命令是否还在运行。",
      why: "说服价值：这是“服务确实在这台 Mac 上跑起来”的第一手证据。",
    });
    return true;
  } catch (error) {
    setText(document.getElementById("handout-daemon-state"), "daemon 未连接");
    setStep("start_service", {
      status: "未通过",
      tone: "failed",
      signal: "当前还没连上 daemon；先在终端执行启动命令，再刷新进入本页。",
      failure: `检查失败：${error.message}`,
      why: "说服价值：把冷启动这件事讲清楚，比假装页面能在服务关闭时工作更可信。",
    });
    return false;
  }
}

async function checkDashboardLive() {
  try {
    const [summary, sessions] = await Promise.all([getJson("/api/system/summary"), fetchSessions()]);
    recordBaseline(sessions);
    const runnerLabel = summary?.runner_enabled ?? summary?.runnerEnabled ?? summary?.runner?.enabled;
    const runnerOn = runnerLabel === true || /on|true|ready|running/.test(asText([runnerLabel, summary?.runner?.status]));
    setText(document.getElementById("handout-summary-runner"), runnerOn ? "ON" : "未知");
    setText(document.getElementById("handout-summary-sessions"), `${sessions.length} 条`);
    setStep("dashboard_live", {
      status: runnerOn && sessions.length > 0 ? "已通过" : "需关注",
      tone: runnerOn && sessions.length > 0 ? "passed" : "pending",
      signal: runnerOn && sessions.length > 0 ? `Runner=ON，当前已看到 ${sessions.length} 条 session。` : "Dashboard 已连上，但还需要确认 Runner 和最近 session 是否齐全。",
      failure: "如果 Dashboard 看起来像空壳，先刷新页面，再检查 daemon 是否加载了 artifact。",
      why: "说服价值：评审会先确认页面不是静态假数据，然后才会继续看动作链路。",
    });
    return true;
  } catch (error) {
    setText(document.getElementById("handout-summary-runner"), "失败");
    setText(document.getElementById("handout-summary-sessions"), "失败");
    setStep("dashboard_live", {
      status: "未通过",
      tone: "failed",
      signal: "Dashboard 还没拿到实时 summary。",
      failure: `检查失败：${error.message}`,
      why: "说服价值：这里过不了，就说明评审看到的还不是实时系统状态。",
    });
    return false;
  }
}

async function checkRunDemo() {
  try {
    const sessions = await fetchSessions();
    recordBaseline(sessions);
    const demo = sessions.find((session) => !state.baselineSessionIds.has(sessionId(session)) && matchesSession(session, "demo") && isFinished(session));
    if (demo) {
      setStep("run_demo", {
        status: "已通过",
        tone: "passed",
        signal: `已检测到新 demo session：${demo.title || demo.name || demo.id || "现场触发"}。`,
        failure: "如果你想重复演示，再点一次 Demo，本页会继续自动追踪新结果。",
        why: "说服价值：这条新增记录证明 Demo 是你刚刚点出来的。",
      });
      return true;
    }
    setStep("run_demo", {
      status: "等待新 Demo",
      tone: "pending",
      signal: "本页正在持续轮询；你在 Dashboard 点完“运行 Demo”后，这里会自动回填为通过。",
      failure: "如果长时间没变化，先回 Dashboard 看请求是否真正触发。",
      why: "说服价值：让评审看到“现场点击”与“新结果出现”之间的因果关系。",
    });
    return false;
  } catch (error) {
    setStep("run_demo", {
      status: "未通过",
      tone: "failed",
      signal: "暂时还无法确认 Demo 结果。",
      failure: `检查失败：${error.message}`,
      why: "说服价值：这一步失败时，优先说明是数据还没出来，而不是页面逻辑消失了。",
    });
    return false;
  }
}

function findWritableTarget(summary) {
  const panes = Array.isArray(summary?.panes) ? summary.panes : [];
  return (
    summary?.target ||
    summary?.default_target ||
    summary?.writable_target ||
    panes.find((pane) => pane?.writable)?.target ||
    panes[0]?.target ||
    "web_cli_demo:0.0"
  );
}

function extractPaneText(payload) {
  if (typeof payload === "string") {
    return payload;
  }
  if (typeof payload?.text === "string") {
    return payload.text;
  }
  if (typeof payload?.content === "string") {
    return payload.content;
  }
  if (typeof payload?.screen === "string") {
    return payload.screen;
  }
  if (Array.isArray(payload?.lines)) {
    return payload.lines.map((line) => (typeof line === "string" ? line : JSON.stringify(line))).join("\n");
  }
  return JSON.stringify(payload);
}

async function checkCliSend() {
  try {
    const summary = await getJson("/api/cli/tmux/summary");
    const target = findWritableTarget(summary);
    const pane = await getJson(`/api/cli/tmux?target=${encodeURIComponent(target)}`);
    const paneText = extractPaneText(pane);
    if (paneText.includes(PROMPT_TEXT)) {
      setStep("cli_send", {
        status: "已通过",
        tone: "passed",
        signal: `已在 ${target} 看到固定 prompt 回显。`,
        failure: "如果你要重复验证，可以再次发送同一条中文提示词。",
        why: "说服价值：这一步把网页输入和 tmux / Claude 会话直接连起来了。",
      });
      return true;
    }
    setStep("cli_send", {
      status: "等待 pane 回显",
      tone: "pending",
      signal: "本页正在后台轮询 tmux pane；CLI 页面发送固定提示词后，这里会自动变绿。",
      failure: "如果 pane 仍为空，先检查 CLI 页是否显示“本机浏览器可输入”以及请求是否返回 202。",
      why: "说服价值：这是最适合让评审一眼看懂“网页真的驱动实际会话”的一步。",
    });
    return false;
  } catch (error) {
    setStep("cli_send", {
      status: "未通过",
      tone: "failed",
      signal: "暂时还没读到 CLI pane。",
      failure: `检查失败：${error.message}`,
      why: "说服价值：如果这里失败，优先解释为 pane 还没刷新，而不是链路一定坏了。",
    });
    return false;
  }
}

async function checkRunValidation() {
  try {
    const sessions = await fetchSessions();
    recordBaseline(sessions);
    const validation = sessions.find((session) => {
      if (state.baselineSessionIds.has(sessionId(session))) {
        return false;
      }
      if (!matchesSession(session, "validation")) {
        return false;
      }
      const counts = validationCounts(session);
      return counts.total > 0 && counts.passed === counts.total && isFinished(session);
    });
    if (validation) {
      const counts = validationCounts(validation);
      setStep("run_validation", {
        status: "已通过",
        tone: "passed",
        signal: `已检测到新 validation session：${counts.passed}/${counts.total} 通过。`,
        failure: "如果你想重新录一遍，回 Dashboard 再点一次 Validation 即可。",
        why: "说服价值：最后这一步把“可演示”收敛成“可验证”。",
      });
      return true;
    }
    setStep("run_validation", {
      status: "等待验证完成",
      tone: "pending",
      signal: "本页会继续轮询最新 validation；你在 Dashboard 点击后，这里会自动回填通过结果。",
      failure: "如果长时间未完成，先看 Dashboard 中 validation 是否仍在运行。",
      why: "说服价值：让评审看到这是有闭环、有结果判定的系统，不是只会跑动画。",
    });
    return false;
  } catch (error) {
    setStep("run_validation", {
      status: "未通过",
      tone: "failed",
      signal: "暂时还无法确认 Validation 结果。",
      failure: `检查失败：${error.message}`,
      why: "说服价值：如果这里失败，应该先解释为验证仍在处理中。",
    });
    return false;
  }
}

function ensureWatcher(stepId, fn) {
  if (state.watchers.has(stepId)) {
    return;
  }
  const timer = window.setInterval(async () => {
    const passed = await fn();
    if (passed) {
      window.clearInterval(timer);
      state.watchers.delete(stepId);
    }
  }, WATCH_INTERVAL_MS);
  state.watchers.set(stepId, timer);
}

function ensureWatchers() {
  if (!state.baselineSessionIds.size) {
    return;
  }
  ensureWatcher("run_demo", checkRunDemo);
  ensureWatcher("cli_send", checkCliSend);
  ensureWatcher("run_validation", checkRunValidation);
}

function renderRecording(data) {
  const summary = document.getElementById("handout-recording-summary");
  const video = document.getElementById("handout-recording-video");
  const steps = document.getElementById("handout-recording-steps");
  const kind = data?.mode === "record" ? "冷启动用户录像" : "技术验证录像";
  summary.textContent = `最近一次默认资产：${kind}；时间：${data?.captured_at || "未知"}；状态：${data?.status || "unknown"}`;
  if (data?.video_href) {
    video.innerHTML = `<video controls preload="metadata" src="${data.video_href}"></video>`;
  } else {
    video.innerHTML = "<p>latest.json 已存在，但暂时没有视频文件。</p>";
  }
  const screenshotItems = Array.isArray(data?.screenshots)
    ? data.screenshots
    : Object.entries(data?.steps || {}).flatMap(([stepId, detail]) => detail?.screenshot ? [{ stepId, href: detail.screenshot }] : []);
  if (!screenshotItems.length) {
    steps.innerHTML = "<p>这次录像还没有步骤截图。</p>";
    return;
  }
  steps.innerHTML = screenshotItems
    .map((item) => `<a class="recording-step" href="${item.href}" target="_blank" rel="noreferrer">${item.label || item.stepId || item.id}</a>`)
    .join("");
}

async function loadRecording() {
  try {
    const data = await getJson("/artifacts/validation/artifacts/handout/latest.json");
    state.recordingStatus = data;
    renderRecording(data);
  } catch (error) {
    const summary = document.getElementById("handout-recording-summary");
    const video = document.getElementById("handout-recording-video");
    const steps = document.getElementById("handout-recording-steps");
    summary.textContent = "当前还没有默认用户录像。";
    video.innerHTML = "<p>先运行 `npm --prefix insights-share/validation run handout:record`，这里就会展示最新整屏录像。</p>";
    steps.innerHTML = `<p>${error.message}</p>`;
  }
}

async function runAllChecks() {
  await Promise.all([checkStartService(), checkDashboardLive()]);
  ensureWatchers();
  await Promise.all([checkRunDemo(), checkCliSend(), checkRunValidation(), loadRecording()]);
}

function bind() {
  const commandNode = document.getElementById("handout-cli-command");
  const copyState = document.getElementById("handout-copy-state");
  if (commandNode) {
    commandNode.textContent = DAEMON_COMMAND;
  }
  document.getElementById("handout-copy-cli")?.addEventListener("click", async () => {
    try {
      await navigator.clipboard.writeText(DAEMON_COMMAND);
      setText(copyState, "已复制");
    } catch (error) {
      setText(copyState, `复制失败：${error.message}`);
    }
  });
  document.getElementById("handout-refresh-all")?.addEventListener("click", () => {
    runAllChecks();
  });
  document.querySelectorAll('[data-action="check-step"]').forEach((button) => {
    button.addEventListener("click", async () => {
      const stepId = button.dataset.stepId;
      if (stepId === "start_service") {
        await checkStartService();
        return;
      }
      if (stepId === "dashboard_live") {
        await checkDashboardLive();
        ensureWatchers();
        return;
      }
      if (stepId === "run_demo") {
        await checkRunDemo();
        return;
      }
      if (stepId === "cli_send") {
        await checkCliSend();
        return;
      }
      if (stepId === "run_validation") {
        await checkRunValidation();
      }
    });
  });
  document.addEventListener("visibilitychange", () => {
    if (!document.hidden) {
      runAllChecks();
    }
  });
}

document.addEventListener("DOMContentLoaded", async () => {
  hydrateBaseline();
  bind();
  await runAllChecks();
});
