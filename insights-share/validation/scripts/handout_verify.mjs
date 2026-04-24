import { copyFile, mkdir, stat, writeFile } from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import http from 'node:http';
import { spawn, spawnSync } from 'node:child_process';
import { setTimeout as delay } from 'node:timers/promises';
import { chromium } from 'playwright';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const VALIDATION_DIR = path.resolve(__dirname, '..');
const PROJECT_ROOT = path.resolve(VALIDATION_DIR, '..');
const SERVER_DIR = path.join(PROJECT_ROOT, 'demo_codes');
const ARTIFACT_ROOT = path.join(VALIDATION_DIR, 'artifacts', 'handout');
const RUN_ID = `verify-${new Date().toISOString().replace(/[:.]/g, '-')}`;
const RUN_DIR = path.join(ARTIFACT_ROOT, 'runs', RUN_ID);
const VIDEO_TEMP_DIR = path.join(RUN_DIR, 'video-temp');
const VIDEO_PATH = path.join(RUN_DIR, 'verify.webm');
const CONSOLE_PATH = path.join(RUN_DIR, 'console.log');
const MANIFEST_PATH = path.join(RUN_DIR, 'manifest.json');
const LATEST_PATH = path.join(ARTIFACT_ROOT, 'verify-latest.json');
const BASE_URL = process.env.HANDOUT_BASE_URL || 'http://127.0.0.1:7821';
const FIXED_PROMPT = '请只回复：CLI 输入链路已验证';

const consoleLines = [];
const screenshots = [];
let startedDaemon = null;
let startedTmuxSession = false;

function log(message) {
  const line = `[${new Date().toISOString()}] ${message}`;
  consoleLines.push(line);
  console.log(line);
}

function artifactHref(...parts) {
  return `/artifacts/validation/artifacts/handout/${parts.join('/')}`;
}

async function fetchJson(url) {
  return new Promise((resolve, reject) => {
    const request = http.get(url, { timeout: 4000 }, (response) => {
      let body = '';
      response.setEncoding('utf8');
      response.on('data', (chunk) => {
        body += chunk;
      });
      response.on('end', () => {
        if ((response.statusCode || 500) >= 400) {
          reject(new Error(`${url} -> ${response.statusCode}`));
          return;
        }
        try {
          resolve(JSON.parse(body));
        } catch (error) {
          reject(error);
        }
      });
    });
    request.on('error', reject);
    request.on('timeout', () => {
      request.destroy();
      reject(new Error(`${url} -> timeout`));
    });
  });
}

async function isHealthy() {
  try {
    const health = await fetchJson(`${BASE_URL}/healthz`);
    return Boolean(health.ok);
  } catch (error) {
    return false;
  }
}

async function ensureDaemon() {
  if (await isHealthy()) {
    log(`复用已在线 daemon: ${BASE_URL}`);
    return;
  }

  log('daemon 未在线，handout verify 临时启动 insightsd');
  startedDaemon = spawn(
    path.join(SERVER_DIR, '.venv', 'bin', 'python'),
    [
      'insights_cli.py',
      'serve',
      '--host',
      '127.0.0.1',
      '--port',
      '7821',
      '--store-mode',
      'tree',
      '--store',
      './wiki_tree',
      '--runtime-dir',
      './runtime-web',
      '--enable-runners',
    ],
    {
      cwd: SERVER_DIR,
      env: {
        ...process.env,
        NO_PROXY: '127.0.0.1,localhost',
      },
      stdio: ['ignore', 'ignore', 'pipe'],
    }
  );
  startedDaemon.stderr.on('data', (chunk) => {
    consoleLines.push(`[daemon] ${String(chunk).trim()}`);
  });

  const started = Date.now();
  while (Date.now() - started < 30000) {
    if (await isHealthy()) {
      log('临时 daemon 已在线');
      return;
    }
    await delay(1000);
  }
  throw new Error('等待临时 daemon /healthz 超时');
}

function cleanupDaemon() {
  if (!startedDaemon) {
    return;
  }
  startedDaemon.kill('SIGTERM');
  startedDaemon = null;
}

function tmux(args) {
  return spawnSync('tmux', args, {
    encoding: 'utf8',
    env: {
      ...process.env,
      TMUX: '',
    },
  });
}

function ensureTmuxTarget() {
  const existing = tmux(['has-session', '-t', 'web_cli_demo']);
  if (existing.status === 0) {
    log('复用已存在 tmux session: web_cli_demo');
    return;
  }
  const created = tmux(['new-session', '-d', '-s', 'web_cli_demo', '-x', '120', '-y', '30']);
  if (created.status !== 0) {
    throw new Error(`创建 web_cli_demo tmux session 失败: ${created.stderr || created.stdout}`);
  }
  startedTmuxSession = true;
  tmux(['send-keys', '-t', 'web_cli_demo:0.0', 'printf "web cli demo ready\\n"', 'Enter']);
  log('已创建临时 tmux session: web_cli_demo');
}

function cleanupTmuxTarget() {
  if (!startedTmuxSession) {
    return;
  }
  tmux(['kill-session', '-t', 'web_cli_demo']);
  startedTmuxSession = false;
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

async function waitForNewSession(kind, knownIds, isReady, timeoutMs = 20000) {
  const started = Date.now();
  while (Date.now() - started < timeoutMs) {
    const sessions = extractSessions(await fetchJson(`${BASE_URL}/api/sessions?limit=30`));
    const found = sessions.find((session) => session.kind === kind && !knownIds.has(session.id));
    if (found && (!isReady || isReady(found))) {
      return found;
    }
    await delay(800);
  }
  throw new Error(`等待新的 ${kind} session 超时`);
}

async function saveScreenshot(page, id) {
  const filename = `${id}.png`;
  await page.screenshot({ path: path.join(RUN_DIR, filename), fullPage: true });
  screenshots.push({ id, href: artifactHref('runs', RUN_ID, filename) });
}

async function main() {
  await mkdir(VIDEO_TEMP_DIR, { recursive: true });
  const browser = await chromium.launch({ headless: process.env.PW_HEADLESS !== '0' });
  const context = await browser.newContext({
    viewport: { width: 1440, height: 960 },
    recordVideo: { dir: VIDEO_TEMP_DIR, size: { width: 1440, height: 960 } },
  });
  const page = await context.newPage();
  const pageVideo = page.video();

  page.on('console', (message) => {
    consoleLines.push(`[browser:${message.type()}] ${message.text()}`);
  });
  page.on('pageerror', (error) => {
    consoleLines.push(`[browser:pageerror] ${error.message}`);
  });

  try {
    ensureTmuxTarget();
    await ensureDaemon();

    log('验证 /handout 自动检查');
    await page.goto(`${BASE_URL}/handout`, { waitUntil: 'domcontentloaded' });
    await page.locator('[data-step-id="start_service"][data-state="passed"]').waitFor({ timeout: 60000 });
    await saveScreenshot(page, 'verify-step-1-handout');

    const baselineSessions = extractSessions(await fetchJson(`${BASE_URL}/api/sessions?limit=30`));
    const baselineIds = new Set(baselineSessions.map((item) => item.id));

    log('验证 Dashboard 实时状态与 Demo');
    await page.goto(`${BASE_URL}/dashboard`, { waitUntil: 'domcontentloaded' });
    await page.waitForSelector('#dashboard-summary-grid');
    const summary = await fetchJson(`${BASE_URL}/api/system/summary`);
    if (!summary.runner_enabled) {
      throw new Error('Runner=OFF');
    }
    await saveScreenshot(page, 'verify-step-2-dashboard-live');

    const demoResponse = page.waitForResponse((response) => response.url().includes('/api/runs/demo') && response.status() === 202);
    await page.getByRole('button', { name: /运行 Demo/ }).click();
    await demoResponse;
    await waitForNewSession('demo', baselineIds, (session) => session.status === 'completed');
    await delay(1200);
    await saveScreenshot(page, 'verify-step-3-demo');

    log('验证 CLI 输入链路');
    await page.goto(`${BASE_URL}/cli`, { waitUntil: 'domcontentloaded' });
    await page.waitForSelector('#cli-compose');
    await page.getByRole('textbox').first().fill(FIXED_PROMPT);
    const cliResponse = page.waitForResponse((response) => response.url().includes('/api/cli/tmux/input') && response.status() === 202);
    await page.getByRole('button', { name: /发送并回车/ }).click();
    await cliResponse;
    await page.waitForFunction((prompt) => document.body.innerText.includes(prompt) && document.body.innerText.includes('已发送'), FIXED_PROMPT);
    await saveScreenshot(page, 'verify-step-4-cli');

    log('验证 Validation 与 handout 自动回填');
    const afterDemoSessions = extractSessions(await fetchJson(`${BASE_URL}/api/sessions?limit=30`));
    const afterDemoIds = new Set(afterDemoSessions.map((item) => item.id));
    await page.goto(`${BASE_URL}/dashboard`, { waitUntil: 'domcontentloaded' });
    await page.waitForSelector('#dashboard-summary-grid');
    const validationResponse = page.waitForResponse((response) => response.url().includes('/api/runs/validation') && response.status() === 202);
    await page.getByRole('button', { name: /运行 Validation/ }).click();
    await validationResponse;
    await waitForNewSession(
      'validation',
      afterDemoIds,
      (session) => session.status === 'completed' && session.headline_metrics?.total > 0 && session.headline_metrics?.passed === session.headline_metrics?.total,
      120000,
    );
    await page.goto(`${BASE_URL}/handout`, { waitUntil: 'domcontentloaded' });
    await page.locator('[data-step-id="dashboard_live"][data-state="passed"]').waitFor({ timeout: 60000 });
    await page.locator('[data-step-id="run_demo"][data-state="passed"]').waitFor({ timeout: 60000 });
    await page.locator('[data-step-id="cli_send"][data-state="passed"]').waitFor({ timeout: 60000 });
    await page.locator('[data-step-id="run_validation"][data-state="passed"]').waitFor({ timeout: 120000 });
    await saveScreenshot(page, 'verify-step-5-handout-final');

    await context.close();
    const videoFile = await pageVideo.path();
    if (videoFile) {
      await copyFile(videoFile, VIDEO_PATH);
      await stat(VIDEO_PATH);
    }

    const manifest = {
      mode: 'verify',
      status: 'passed',
      captured_at: new Date().toISOString(),
      base_url: BASE_URL,
      video_href: artifactHref('runs', RUN_ID, 'verify.webm'),
      console_href: artifactHref('runs', RUN_ID, 'console.log'),
      screenshots,
      steps: {
        start_service: { status: 'passed', screenshot: screenshots[0]?.href || null },
        dashboard_live: { status: 'passed', screenshot: screenshots[1]?.href || null },
        run_demo: { status: 'passed', screenshot: screenshots[2]?.href || null },
        cli_send: { status: 'passed', screenshot: screenshots[3]?.href || null },
        run_validation: { status: 'passed', screenshot: screenshots[4]?.href || null },
      },
    };
    await writeFile(CONSOLE_PATH, `${consoleLines.join('\n')}\n`, 'utf8');
    await writeFile(MANIFEST_PATH, `${JSON.stringify(manifest, null, 2)}\n`, 'utf8');
    await writeFile(LATEST_PATH, `${JSON.stringify(manifest, null, 2)}\n`, 'utf8');
  } catch (error) {
    await writeFile(CONSOLE_PATH, `${consoleLines.join('\n')}\n${String(error && error.stack ? error.stack : error)}\n`, 'utf8');
    throw error;
  } finally {
    await page.close().catch(() => undefined);
    await context.close().catch(() => undefined);
    await browser.close().catch(() => undefined);
    cleanupDaemon();
    cleanupTmuxTarget();
  }
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
