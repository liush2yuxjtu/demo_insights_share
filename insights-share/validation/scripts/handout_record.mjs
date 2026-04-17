import { spawn, spawnSync, execSync } from 'node:child_process';
import { mkdir, writeFile } from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import http from 'node:http';
import { setTimeout as delay } from 'node:timers/promises';
import { chromium } from 'playwright';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const VALIDATION_DIR = path.resolve(__dirname, '..');
const PROJECT_ROOT = path.resolve(VALIDATION_DIR, '..');
const SERVER_DIR = path.join(PROJECT_ROOT, 'demo_codes');
const ARTIFACT_ROOT = path.join(VALIDATION_DIR, 'artifacts', 'handout');
const RUNS_DIR = path.join(ARTIFACT_ROOT, 'runs');
const NOW = new Date().toISOString().replace(/[:.]/g, '-');
const RUN_DIR = path.join(RUNS_DIR, NOW);
const VIDEO_PATH = path.join(RUN_DIR, 'user-flow.mp4');
const CONSOLE_PATH = path.join(RUN_DIR, 'console.log');
const MANIFEST_PATH = path.join(RUN_DIR, 'manifest.json');
const LATEST_PATH = path.join(ARTIFACT_ROOT, 'latest.json');
const BASE_URL = 'http://127.0.0.1:7821';
const PROMPT_TEXT = '请只回复：CLI 输入链路已验证';
const DAEMON_COMMAND = `cd ${SERVER_DIR} && export NO_PROXY=127.0.0.1,localhost && ./.venv/bin/python insights_cli.py serve --host 127.0.0.1 --port 7821 --store-mode tree --store ./wiki_tree --runtime-dir ./runtime-web --enable-runners`;

const stepArtifacts = [];
const consoleLines = [];

function log(message) {
  const line = `[${new Date().toISOString()}] ${message}`;
  consoleLines.push(line);
  console.log(line);
}

function appleScriptLiteral(text) {
  return JSON.stringify(text);
}

function runAppleScript(script) {
  const result = spawnSync('/usr/bin/osascript', ['-e', script], {
    encoding: 'utf8',
    timeout: 2000,
  });
  if (result.error && result.error.code !== 'ETIMEDOUT') {
    throw result.error;
  }
}

function stopExistingDaemon() {
  try {
    execSync(`pkill -f ${JSON.stringify(path.join(SERVER_DIR, 'insights_cli.py') + ' serve')}`, { stdio: 'ignore' });
  } catch (error) {
    // ignore when no daemon is running
  }
  try {
    execSync(`lsof -tiTCP:7821 -sTCP:LISTEN | xargs kill -9`, { stdio: 'ignore', shell: '/bin/zsh' });
  } catch (error) {
    // ignore when no listener is running
  }
}

function spawnDaemonFallback() {
  const daemon = spawn(
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
      detached: true,
      stdio: 'ignore',
      env: {
        ...process.env,
        NO_PROXY: '127.0.0.1,localhost',
      },
    }
  );
  daemon.unref();
}

async function waitForHealth(timeoutMs = 30000) {
  const started = Date.now();
  while (Date.now() - started < timeoutMs) {
    const ok = await new Promise((resolve) => {
      const request = http.get(`${BASE_URL}/healthz`, { timeout: 2000 }, (response) => {
        resolve(response.statusCode === 200);
        response.resume();
      });
      request.on('error', () => resolve(false));
      request.on('timeout', () => {
        request.destroy();
        resolve(false);
      });
    });
    if (ok) {
      return;
    }
    await delay(1000);
  }
  throw new Error('等待 /healthz 超时');
}

async function waitForText(page, text, timeout = 45000) {
  await page.getByText(text, { exact: false }).first().waitFor({ timeout });
}

async function screenshot(page, name, label) {
  const filename = `${name}.png`;
  const target = path.join(RUN_DIR, filename);
  await page.screenshot({ path: target, fullPage: true });
  stepArtifacts.push({ id: name, label, href: `/artifacts/validation/artifacts/handout/runs/${NOW}/${filename}` });
}

async function withResponse(page, matcher, action) {
  const responsePromise = page.waitForResponse((response) => matcher(response), { timeout: 45000 });
  await action();
  return responsePromise;
}

async function main() {
  await mkdir(RUN_DIR, { recursive: true });
  stopExistingDaemon();

  log('启动整屏录制');
  const ffmpeg = spawn('/opt/homebrew/bin/ffmpeg', [
    '-y',
    '-f', 'avfoundation',
    '-framerate', '30',
    '-capture_cursor', '1',
    '-i', '1:none',
    '-vcodec', 'libx264',
    '-pix_fmt', 'yuv420p',
    VIDEO_PATH,
  ], {
    stdio: ['pipe', 'ignore', 'pipe'],
  });
  ffmpeg.stderr.on('data', (chunk) => {
    consoleLines.push(String(chunk).trim());
  });
  await delay(1500);

  log('通过 Terminal 冷启动 daemon');
  runAppleScript(`tell application "Terminal"
    activate
    do script ${appleScriptLiteral(DAEMON_COMMAND)}
  end tell`);
  await delay(1200);
  try {
    await waitForHealth(4000);
  } catch (error) {
    log('Terminal 自动化未在预期时间内拉起 daemon，改用同命令后台兜底启动');
    spawnDaemonFallback();
    await waitForHealth();
  }
  log('daemon 已在线');

  const browser = await chromium.launch({
    headless: false,
    channel: 'chrome',
    args: ['--window-position=72,56', '--window-size=1440,960'],
  });
  const context = await browser.newContext({ viewport: { width: 1440, height: 900 } });
  const page = await context.newPage();
  page.on('console', (msg) => {
    consoleLines.push(`[browser:${msg.type()}] ${msg.text()}`);
  });

  try {
    log('打开 /handout');
    await page.goto(`${BASE_URL}/handout`, { waitUntil: 'domcontentloaded' });
    await waitForText(page, 'Handout Verification');
    await delay(1800);
    await screenshot(page, 'step-1-handout-cold-start', 'step-1-handout-cold-start');

    log('进入 Dashboard 并触发 Demo');
    await page.goto(`${BASE_URL}/dashboard`, { waitUntil: 'domcontentloaded' });
    await waitForText(page, '运行 Demo');
    await delay(1200);
    await withResponse(
      page,
      (response) => response.url().includes('/api/runs/demo') && response.status() === 202,
      async () => {
        await page.getByRole('button', { name: /运行 Demo/ }).click();
      }
    );
    await delay(3500);
    await screenshot(page, 'step-2-dashboard-demo', 'step-2-dashboard-demo');

    log('进入 CLI 页面发送固定提示词');
    await page.goto(`${BASE_URL}/cli`, { waitUntil: 'domcontentloaded' });
    await waitForText(page, '发送并回车');
    await delay(1200);
    await page.getByRole('textbox').first().fill(PROMPT_TEXT);
    await withResponse(
      page,
      (response) => response.url().includes('/api/cli/tmux/input') && response.status() === 202,
      async () => {
        await page.getByRole('button', { name: /发送并回车/ }).click();
      }
    );
    await delay(2500);
    await screenshot(page, 'step-3-cli-send', 'step-3-cli-send');

    log('回到 Dashboard 触发 Validation');
    await page.goto(`${BASE_URL}/dashboard`, { waitUntil: 'domcontentloaded' });
    await waitForText(page, '运行 Validation');
    await delay(1200);
    await withResponse(
      page,
      (response) => response.url().includes('/api/runs/validation') && response.status() === 202,
      async () => {
        await page.getByRole('button', { name: /运行 Validation/ }).click();
      }
    );
    await waitForText(page, '6/6 通过', 120000);
    await delay(2500);
    await screenshot(page, 'step-4-dashboard-validation', 'step-4-dashboard-validation');

    log('回到 handout 等待自动回填');
    await page.goto(`${BASE_URL}/handout`, { waitUntil: 'domcontentloaded' });
    await page.locator('[data-step-id="start_service"][data-state="passed"]').waitFor({ timeout: 60000 });
    await page.locator('[data-step-id="run_demo"][data-state="passed"]').waitFor({ timeout: 60000 });
    await page.locator('[data-step-id="cli_send"][data-state="passed"]').waitFor({ timeout: 60000 });
    await page.locator('[data-step-id="run_validation"][data-state="passed"]').waitFor({ timeout: 120000 });
    await delay(2500);
    await screenshot(page, 'step-5-handout-autofill', 'step-5-handout-autofill');

    const manifest = {
      mode: 'record',
      status: 'passed',
      captured_at: new Date().toISOString(),
      video_href: `/artifacts/validation/artifacts/handout/runs/${NOW}/user-flow.mp4`,
      console_href: `/artifacts/validation/artifacts/handout/runs/${NOW}/console.log`,
      screenshots: stepArtifacts,
      steps: {
        start_service: { status: 'passed', screenshot: stepArtifacts[0]?.href || null },
        dashboard_live: { status: 'passed', screenshot: stepArtifacts[1]?.href || null },
        run_demo: { status: 'passed', screenshot: stepArtifacts[1]?.href || null },
        cli_send: { status: 'passed', screenshot: stepArtifacts[2]?.href || null },
        run_validation: { status: 'passed', screenshot: stepArtifacts[4]?.href || stepArtifacts[3]?.href || null },
      },
    };
    await writeFile(CONSOLE_PATH, `${consoleLines.join('\n')}\n`, 'utf8');
    await writeFile(MANIFEST_PATH, `${JSON.stringify(manifest, null, 2)}\n`, 'utf8');
    await writeFile(LATEST_PATH, `${JSON.stringify(manifest, null, 2)}\n`, 'utf8');
    log('录像产物写入完成');
  } finally {
    await context.close().catch(() => undefined);
    await browser.close().catch(() => undefined);
    ffmpeg.stdin.write('q\n');
    await new Promise((resolve) => ffmpeg.once('exit', resolve));
    stopExistingDaemon();
  }
}

main().catch(async (error) => {
  console.error(error);
  await mkdir(RUN_DIR, { recursive: true });
  await writeFile(CONSOLE_PATH, `${consoleLines.join('\n')}\n${String(error && error.stack ? error.stack : error)}\n`, 'utf8');
  process.exitCode = 1;
});
