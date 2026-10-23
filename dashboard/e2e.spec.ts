import { test, expect } from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';
import { mkdir } from 'node:fs/promises';

test('dashboard reads persisted results, filters, details, and exports', async ({ page, request }) => {
  const runsResponse = await request.get('/api/runs');
  expect(runsResponse.ok(), 'The dashboard API must be running').toBeTruthy();
  const runs = await runsResponse.json();
  const runId = runs[0]?.id ?? '';
  const [trialsResponse, summaryResponse] = await Promise.all([request.get('/api/trials'), request.get('/api/summary')]);
  expect(trialsResponse.ok()).toBeTruthy(); expect(summaryResponse.ok()).toBeTruthy();
  const trials = await trialsResponse.json(); const summary = await summaryResponse.json();

  await page.goto('/');
  await expect(page.getByRole('heading', { name: 'Benchmark results' })).toBeVisible();
  await page.keyboard.press('Tab');
  await expect(page.getByRole('link', { name: 'Skip to results' })).toBeFocused();
  await page.keyboard.press('Enter');
  await expect(page.locator('#main-content')).toBeFocused();
  const accessibility = await new AxeBuilder({ page }).analyze();
  expect(accessibility.violations, JSON.stringify(accessibility.violations.map(v => ({ id: v.id, nodes: v.nodes.map(n => n.target) })))).toEqual([]);
  await expect(page.getByTestId('onboarding')).toBeHidden();
  await page.getByRole('button', { name: 'Quick start' }).click();
  await expect(page.getByTestId('onboarding')).toBeVisible();
  await expect(page.getByTestId('onboarding')).toContainText('free reference task');
  await expect(page.getByTestId('onboarding').locator('pre code')).toContainText('abl start --root');
  await page.getByRole('button', { name: 'Close quick start' }).click();
  await expect(page.getByTestId('onboarding')).toBeHidden();
  await expect(page.getByTestId('trial-row')).toHaveCount(Math.min(100, trials.length));
  const expectedCompletion = summary.completion_rate == null ? 'Unavailable' : `${(summary.completion_rate > 1 ? summary.completion_rate : summary.completion_rate * 100).toLocaleString(undefined, { maximumFractionDigits: 1 })}%`;
  await expect(page.getByTestId('completion-rate')).toHaveText(expectedCompletion);
  const expectedMedian = summary.median_wall_seconds == null ? 'Unavailable' : `${summary.median_wall_seconds.toLocaleString(undefined, { maximumFractionDigits: 1 })}s`;
  await expect(page.getByTestId('median-wall')).toHaveText(expectedMedian);

  const expectedRows = async (query: string) => Math.min(100, (await (await request.get(`/api/trials/page?limit=100&offset=0${query ? `&${query}` : ''}`)).json()).total);
  if (runId) { await page.getByTestId('filter-run').selectOption(runId); await expect(page.getByTestId('trial-row')).toHaveCount(await expectedRows(`run_id=${encodeURIComponent(runId)}`)); }
  const provider = trials.find((t: { provider?: string }) => t.provider)?.provider;
  if (provider) { await page.getByTestId('filter-provider').selectOption(provider); await expect(page.getByTestId('trial-row')).toHaveCount(await expectedRows(`run_id=${encodeURIComponent(runId)}&provider=${encodeURIComponent(provider)}`)); }
  const model = trials.find((t: { model?: string }) => t.model)?.model;
  if (model) { await page.getByTestId('filter-model').selectOption(model); await expect(page.getByTestId('trial-row')).toHaveCount(await expectedRows(`run_id=${encodeURIComponent(runId)}&provider=${encodeURIComponent(provider ?? '')}&model=${encodeURIComponent(model)}`)); }
  const task = trials.find((t: { task_id?: string }) => t.task_id)?.task_id;
  if (task) { await page.getByTestId('filter-task').selectOption(task); await expect(page.getByTestId('trial-row')).toHaveCount(await expectedRows(`run_id=${encodeURIComponent(runId)}&provider=${encodeURIComponent(provider ?? '')}&model=${encodeURIComponent(model ?? '')}&task_id=${encodeURIComponent(task)}`)); }
  await page.getByRole('button', { name: 'Reset' }).click();
  const allResponse = await request.get('/api/trials/page?limit=100&offset=0'); const allPage = await allResponse.json(); const allTrials = allPage.items;
  await expect(page.getByTestId('trial-row')).toHaveCount(Math.min(100, allPage.total));
  const row = page.getByTestId('trial-row').first(); const openButton = row.getByRole('button'); await openButton.focus(); await openButton.press('Enter');
  await expect(page.getByTestId('trial-detail')).toBeVisible(); await expect(page.getByTestId('verifier-evidence')).toBeVisible();
  await page.keyboard.press('Escape');
  await expect(page.getByTestId('trial-detail')).toBeHidden();
  await expect(openButton).toBeFocused();
  await openButton.press('Enter');
  await expect(page.getByTestId('trial-detail')).toBeVisible();
  const detail = await request.get(`/api/trials/${encodeURIComponent(allTrials[0].id)}`); const selected = await detail.json();
  if (selected.verifier?.stdout) await expect(page.getByTestId('verifier-evidence')).toContainText(selected.verifier.stdout.slice(0, 30));
  await page.getByRole('button', { name: 'Close trial details' }).click();
  await page.getByRole('button', { name: 'Quick start' }).click();
  await expect(page.getByTestId('onboarding')).toBeVisible();
  await expect(page.getByTestId('onboarding')).toContainText('Reference controls validate task contracts');
  await page.getByRole('button', { name: 'Close quick start' }).click();
  await page.reload();
  await expect(page.getByTestId('onboarding')).toBeHidden();
  await mkdir('test-results', { recursive: true }); await page.screenshot({ path: 'test-results/dashboard.png', fullPage: true });
  await page.setViewportSize({ width: 390, height: 844 });
  const widths = await page.evaluate(() => ({ viewport: document.documentElement.clientWidth, page: document.documentElement.scrollWidth }));
  expect(widths.page).toBeLessThanOrEqual(widths.viewport);
  const longMetric = page.getByText('Median time to first output', { exact: true });
  const metricTitle = await longMetric.boundingBox();
  const metricIcon = await longMetric.locator('xpath=..').locator('.metric-icon').boundingBox();
  expect(metricTitle).not.toBeNull(); expect(metricIcon).not.toBeNull();
  expect(metricTitle!.x + metricTitle!.width).toBeLessThanOrEqual(metricIcon!.x);
  await page.screenshot({ path: 'test-results/dashboard-mobile.png', fullPage: true });
  await page.setViewportSize({ width: 640, height: 900 });
  const zoomWidths = await page.evaluate(() => ({ viewport: document.documentElement.clientWidth, page: document.documentElement.scrollWidth }));
  expect(zoomWidths.page).toBeLessThanOrEqual(zoomWidths.viewport);
});

test('both export formats download from the persisted API', async ({ page }) => {
  await page.goto('/');
  const csvDownload = page.waitForEvent('download'); await page.getByRole('link', { name: 'Export CSV' }).click(); const csv = await csvDownload; expect(csv.suggestedFilename().toLowerCase()).toContain('csv');
  const jsonDownload = page.waitForEvent('download'); await page.getByRole('link', { name: 'Export JSON' }).click(); const json = await jsonDownload; expect(json.suggestedFilename().toLowerCase()).toContain('json');
});

test('cross-run provider and model filters exclude nonmatching persisted records', async ({page,request}) => {
  const allResponse = await (await request.get('/api/trials/page?limit=100&offset=0')).json(); const all = allResponse.items;
  expect(all.some((t: {status:string}) => t.status === 'PASS')).toBeTruthy();
  const reference = all.find((t: {runner:string}) => t.runner === 'reference');
  await page.goto('/');
  await expect(page.getByTestId('trial-row')).toHaveCount(Math.min(100, allResponse.total));
  await page.getByRole('button', {name:'Reset'}).click();
  await expect(page.getByTestId('trial-row')).toHaveCount(Math.min(100, allResponse.total));
  await page.getByTestId('filter-provider').selectOption(reference.provider);
  await expect(page.getByTestId('trial-row')).toHaveCount(await (async () => Math.min(100, (await (await request.get(`/api/trials/page?limit=100&offset=0&provider=${encodeURIComponent(reference.provider)}`)).json()).total))());
  await page.getByTestId('filter-provider').selectOption('');
  await page.getByTestId('filter-model').selectOption(reference.model);
  await expect(page.getByTestId('trial-row')).toHaveCount(await (async () => Math.min(100, (await (await request.get(`/api/trials/page?limit=100&offset=0&model=${encodeURIComponent(reference.model)}`)).json()).total))());
});

test('filters and page are encoded in the URL and restored by a direct link', async ({ page, request }) => {
  const response = await request.get('/api/trials/page?limit=100&offset=0');
  const pageData = await response.json();
  const trial = pageData.items.find((item: { provider?: string; model?: string; task_id?: string }) => item.provider && item.model && item.task_id);
  expect(trial, 'Persisted acceptance fixture must contain a provider/model/task record').toBeDefined();
  const query = new URLSearchParams({ provider: trial.provider, model: trial.model, task_id: trial.task_id, offset: '0' });
  await page.goto(`/?${query}`);
  await expect(page.getByTestId('filter-provider')).toHaveValue(trial.provider);
  await expect(page.getByTestId('filter-model')).toHaveValue(trial.model);
  await expect(page.getByTestId('filter-task')).toHaveValue(trial.task_id);
  const filtered = await (await request.get(`/api/trials/page?limit=100&${query}`)).json();
  await expect(page.getByTestId('trial-row')).toHaveCount(filtered.items.length);
  await page.reload();
  await expect(page.getByTestId('filter-provider')).toHaveValue(trial.provider);
  await expect(page.getByTestId('filter-model')).toHaveValue(trial.model);
  await expect(page.getByTestId('filter-task')).toHaveValue(trial.task_id);
  await expect(page.getByTestId('trial-row')).toHaveCount(filtered.items.length);
});

test('loading, API errors, and a valid empty result each have a clear recovery path', async ({ page }) => {
  let fail = true;
  let releaseLoading!: () => void;
  const holdFirstResponses = new Promise<void>(resolve => { releaseLoading = resolve; });
  let firstResponse = true;
  await page.route('**/api/runs', route => route.fulfill({ json: [] }));
  await page.route('**/api/trials/page**', async route => {
    if (firstResponse) await holdFirstResponses;
    firstResponse = false;
    return fail ? route.fulfill({ status: 503, json: { detail: 'local store unavailable' } }) : route.fulfill({ json: { items: [], total: 0, limit: 100, offset: 0 } });
  });
  await page.route('**/api/overview**', async route => {
    if (firstResponse) await holdFirstResponses;
    firstResponse = false;
    return fail
      ? route.fulfill({ status: 503, json: { detail: 'local store unavailable' } })
      : route.fulfill({ json: { summary: {}, providers: [], models: [], tasks: [], chart_trials: [], chart_sampled: false, chart_total: 0 } });
  });
  await page.goto('/');
  await expect(page.getByRole('status')).toContainText('Loading persisted trials');
  releaseLoading();
  await expect(page.getByRole('alert')).toContainText('Could not load benchmark results');
  fail = false;
  await page.getByRole('button', { name: 'Retry' }).click();
  await expect(page.getByRole('heading', { name: 'No benchmark results yet' })).toBeVisible();
  await expect(page.getByRole('button', { name: 'Clear filters' })).toHaveCount(0);
});

test('empty workspace, filter miss, and returning state stay distinct', async ({ page }) => {
  const trial = { id: 'return-trial', run_id: 'run-1', task_id: 'rounding', task_version: '1.0', status: 'PASS', provider: 'openrouter', model: 'example-model', runner: 'agent', config_hash: 'cfg-hash', corpus_hash: 'corpus-hash', config: { streaming: true, reasoning_effort: 'low', spend_limit_usd: 0.02 } };
  let mode: 'empty' | 'filtered' | 'saved' = 'empty';
  await page.route('**/api/workspace', route => route.fulfill({ json: { workspace_id: 'workspace-test', start_command: 'abl start --root /tmp/results', dashboard_command: 'abl dashboard --root /tmp/results' } }));
  await page.route('**/api/runs', route => route.fulfill({ json: mode === 'empty' ? [] : [{ id: 'run-1', status: 'COMPLETED', created_at: '2026-01-01', config: trial.config }] }));
  await page.route('**/api/trials/page**', route => route.fulfill({ json: mode === 'filtered' ? { items: [], total: 0, limit: 100, offset: 0 } : mode === 'saved' ? { items: [trial], total: 1, limit: 100, offset: 0 } : { items: [], total: 0, limit: 100, offset: 0 } }));
  await page.route('**/api/overview**', route => route.fulfill({ json: { summary: { trials: mode === 'saved' ? 1 : 0, groups: [] }, providers: mode === 'empty' ? [] : ['openrouter'], models: mode === 'saved' ? ['example-model'] : [], tasks: mode === 'saved' ? ['rounding'] : [], chart_trials: mode === 'saved' ? [trial] : [], chart_total: mode === 'saved' ? 1 : 0, chart_sampled: false } }));
  await page.route('**/api/trials/return-trial', route => route.fulfill({ json: { ...trial, verifier: { exit_code: 0, stdout: 'reference evidence' } } }));

  await page.goto('/');
  await expect(page.getByRole('heading', { name: 'No benchmark results yet' })).toBeVisible();
  await expect(page.getByText('abl start --root /tmp/results')).toBeVisible();
  mode = 'filtered';
  await page.goto('/?provider=no-such-provider');
  await expect(page.getByRole('heading', { name: 'No trials match these filters' })).toBeVisible();
  await expect(page.getByRole('button', { name: 'Clear filters' })).toBeVisible();

  mode = 'saved';
  await page.addInitScript(() => localStorage.setItem('abl.dashboard.state.workspace-test', JSON.stringify({ provider: 'openrouter', offset: 0, trialId: 'return-trial' })));
  await page.goto('/');
  await expect(page.getByTestId('filter-provider')).toHaveValue('openrouter');
  await expect(page.getByTestId('trial-detail')).toBeVisible();
  await expect(page.getByTestId('trial-detail')).toContainText('reference evidence');
  await expect(page.getByTestId('trial-row')).toContainText('streaming · reasoning low · reserve $0.02');
  await page.getByRole('button', { name: 'Close trial details' }).click();
  await page.reload();
  await expect(page.getByTestId('filter-provider')).toHaveValue('openrouter');
  await expect(page.getByTestId('trial-detail')).toBeHidden();
});

test('active runs refresh in place and report safe terminal cancellation guidance', async ({ page }) => {
  let runReads = 0;
  await page.route('**/api/workspace', route => route.fulfill({ json: { workspace_id: 'active-test', start_command: 'abl start --root /tmp/results', dashboard_command: 'abl dashboard --root /tmp/results' } }));
  await page.route('**/api/runs', route => {
    runReads += 1;
    return route.fulfill({ json: [{ id: 'active-run', status: runReads < 2 ? 'RUNNING' : 'COMPLETED', created_at: '2026-01-01' }] });
  });
  await page.route('**/api/trials/page**', route => route.fulfill({ json: { items: [], total: 0, limit: 100, offset: 0 } }));
  await page.route('**/api/overview**', route => route.fulfill({ json: { summary: {}, providers: [], models: [], tasks: [], chart_trials: [], chart_total: 0, chart_sampled: false } }));
  await page.goto('/');
  await expect(page.getByText('A benchmark run is active')).toBeVisible();
  await expect(page.getByText('Cancel it from the terminal running the CLI.')).toBeVisible();
  await expect(page.getByText('A benchmark run is active')).toHaveCount(0, { timeout: 5000 });
  expect(runReads).toBeGreaterThanOrEqual(2);
});

test('workspace state waits for its identity before loading filters or restoring evidence', async ({ page }) => {
  let releaseWorkspace!: () => void;
  const workspaceGate = new Promise<void>(resolve => { releaseWorkspace = resolve; });
  let pageRequests = 0;
  let querySeen = '';
  await page.addInitScript(() => localStorage.setItem('abl.dashboard.state.workspace-delayed', JSON.stringify({ provider: 'openrouter', model: 'example-model', offset: 0, trialId: 'outside-current-page' })));
  await page.route('**/api/workspace', async route => {
    await workspaceGate;
    return route.fulfill({ json: { workspace_id: 'workspace-delayed', start_command: 'abl start --root /tmp/saved-results', dashboard_command: 'abl dashboard --root /tmp/saved-results' } });
  });
  await page.route('**/api/runs', route => route.fulfill({ json: [] }));
  await page.route('**/api/trials/page**', route => {
    pageRequests += 1; querySeen = new URL(route.request().url()).search;
    return route.fulfill({ json: { items: [], total: 0, limit: 100, offset: 0 } });
  });
  await page.route('**/api/overview**', route => route.fulfill({ json: { summary: {}, providers: ['openrouter'], models: ['example-model'], tasks: [], chart_trials: [], chart_total: 0, chart_sampled: false } }));
  await page.route('**/api/trials/outside-current-page', route => route.fulfill({ json: { id: 'outside-current-page', run_id: 'old-run', task_id: 'saved-trial', status: 'PASS', runner: 'agent', verifier: { exit_code: 0, stdout: 'restored by id' } } }));
  await page.goto('/');
  await expect(page.getByRole('status')).toContainText('Loading persisted trials');
  expect(pageRequests).toBe(0);
  releaseWorkspace();
  await expect(page.getByTestId('filter-provider')).toHaveValue('openrouter');
  await expect(page.getByTestId('filter-model')).toHaveValue('example-model');
  await expect(page.getByTestId('trial-detail')).toBeVisible();
  await expect(page.getByTestId('trial-detail')).toContainText('restored by id');
  expect(querySeen).toContain('provider=openrouter');
  expect(querySeen).toContain('model=example-model');
});

test('workspace lookup error gives retry and never shows a guessed results path', async ({ page }) => {
  let fail = true;
  let trialPageRequests = 0;
  await page.route('**/api/workspace', route => fail ? route.fulfill({ status: 503 }) : route.fulfill({ json: { workspace_id: 'retry-workspace', start_command: 'abl start --root /tmp/correct-results', dashboard_command: 'abl dashboard --root /tmp/correct-results' } }));
  await page.route('**/api/runs', route => route.fulfill({ json: [] }));
  await page.route('**/api/trials/page**', route => { trialPageRequests += 1; return route.fulfill({ json: { items: [], total: 0, limit: 100, offset: 0 } }); });
  await page.route('**/api/overview**', route => route.fulfill({ json: { summary: {}, providers: [], models: [], tasks: [], chart_trials: [], chart_total: 0, chart_sampled: false } }));
  await page.goto('/');
  await page.getByRole('button', { name: 'Quick start' }).click();
  await expect(page.getByRole('alert')).toContainText('No run command will be shown');
  await expect(page.getByText('./benchmark-results', { exact: false })).toHaveCount(0);
  await expect(page.getByRole('button', { name: 'Retry workspace lookup' })).toBeVisible();
  expect(trialPageRequests).toBe(0);
  fail = false;
  await page.getByRole('button', { name: 'Retry workspace lookup' }).click();
  await expect(page.getByTestId('onboarding')).toContainText('/tmp/correct-results');
  expect(trialPageRequests).toBeGreaterThanOrEqual(1);
});

test('stale result offset returns to the first page', async ({ page }) => {
  await page.route('**/api/workspace', route => route.fulfill({ json: { workspace_id: 'stale-page', start_command: 'abl start --root /tmp/results', dashboard_command: 'abl dashboard --root /tmp/results' } }));
  await page.route('**/api/runs', route => route.fulfill({ json: [{ id: 'run', status: 'COMPLETED', created_at: '2026-01-01' }] }));
  await page.route('**/api/trials/page**', route => {
    const offset = Number(new URL(route.request().url()).searchParams.get('offset'));
    return route.fulfill({ json: offset ? { items: [], total: 1, limit: 100, offset } : { items: [{ id: 'only', run_id: 'run', task_id: 'only-task', status: 'PASS' }], total: 1, limit: 100, offset } });
  });
  await page.route('**/api/overview**', route => route.fulfill({ json: { summary: { trials: 1, groups: [] }, providers: [], models: [], tasks: [], chart_trials: [], chart_total: 0, chart_sampled: false } }));
  await page.goto('/?offset=100');
  await expect(page.getByRole('heading', { name: 'No trials on this page' })).toBeVisible();
  await page.getByRole('button', { name: 'First page' }).click();
  await expect(page.getByTestId('trial-row')).toHaveCount(1);
  expect(new URL(page.url()).searchParams.get('offset')).toBeNull();
});

test('filter changes replace old rows with a compact loading state until new matches arrive', async ({ page }) => {
  let pageReads = 0;
  let filteredPageReads = 0;
  let releaseFiltered!: () => void;
  const filteredGate = new Promise<void>(resolve => { releaseFiltered = resolve; });
  const trial = { id: 'filter-trial', run_id: 'run', task_id: 'task', status: 'PASS', provider: 'openrouter', model: 'model', runner: 'agent' };
  await page.route('**/api/workspace', route => route.fulfill({ json: { workspace_id: 'filter-loading', start_command: 'abl start --root /tmp/results', dashboard_command: 'abl dashboard --root /tmp/results' } }));
  await page.route('**/api/runs', route => route.fulfill({ json: [] }));
  await page.route('**/api/trials/page**', async route => {
    pageReads += 1;
    const provider = new URL(route.request().url()).searchParams.get('provider');
    if (provider) { filteredPageReads += 1; await filteredGate; }
    return route.fulfill({ json: provider ? { items: [trial], total: 1, limit: 100, offset: 0 } : { items: [trial], total: 1, limit: 100, offset: 0 } });
  });
  await page.route('**/api/overview**', async route => {
    if (new URL(route.request().url()).searchParams.has('provider')) await filteredGate;
    return route.fulfill({ json: { summary: { trials: 1, groups: [] }, providers: ['openrouter'], models: ['model'], tasks: ['task'], chart_trials: [trial], chart_total: 1, chart_sampled: false } });
  });
  await page.goto('/');
  await expect(page.getByTestId('trial-row')).toHaveCount(1);
  await page.getByTestId('filter-provider').selectOption('openrouter');
  await expect(page.getByRole('status')).toContainText('Loading filtered results');
  await expect(page.getByTestId('trial-row')).toHaveCount(0);
  releaseFiltered();
  await expect(page.getByTestId('trial-row')).toHaveCount(1);
  expect(pageReads).toBeGreaterThanOrEqual(2);
  expect(filteredPageReads).toBeGreaterThanOrEqual(1);
});

test('run configuration labels use actual cost field and keep reference controls plain', async ({ page }) => {
  const agent = { id: 'agent-trial', run_id: 'agent-run', task_id: 'agent-task', status: 'PASS', runner: 'agent', provider: 'openrouter', model: 'example-model', config_hash: 'agent-config', corpus_hash: 'corpus', config: { streaming: true, reasoning_effort: 'low', spend_limit_usd: 0.02 } };
  const reference = { ...agent, id: 'ref-trial', run_id: 'ref-run', task_id: 'reference-task', status: 'PASS', runner: 'reference', provider: 'reference', model: 'deterministic-reference', config: { runner: 'reference', streaming: false, spend_limit_usd: 0.25, reference_mode: 'success' } };
  await page.route('**/api/workspace', route => route.fulfill({ json: { workspace_id: 'config-labels', start_command: 'abl start --root /tmp/results', dashboard_command: 'abl dashboard --root /tmp/results' } }));
  await page.route('**/api/runs', route => route.fulfill({ json: [{ id: 'agent-run', status: 'COMPLETED', created_at: '2026-01-01', config: agent.config }, { id: 'ref-run', status: 'COMPLETED', created_at: '2026-01-01', config: reference.config }] }));
  await page.route('**/api/trials/page**', route => route.fulfill({ json: { items: [agent, reference], total: 2, limit: 100, offset: 0 } }));
  await page.route('**/api/overview**', route => route.fulfill({ json: { summary: { trials: 2, groups: [] }, providers: [], models: [], tasks: [], chart_trials: [agent, reference], chart_total: 2, chart_sampled: false } }));
  await page.goto('/');
  const agentRow = page.getByTestId('trial-row').filter({ hasText: 'agent-task' });
  const referenceRow = page.getByTestId('trial-row').filter({ hasText: 'reference-task' });
  await expect(agentRow).toContainText('streaming · reasoning low · reserve $0.02');
  await expect(referenceRow).toContainText('reference control success');
  await expect(referenceRow).not.toContainText('non-streaming');
  await expect(referenceRow).not.toContainText('reserve $0.25');
});

test('large histories page compact rows and label chart samples', async ({ page }) => {
  let legacyUnpagedRequests = 0;
  const row = (index: number) => ({ id: `trial-${index}`, run_id: 'run-large', task_id: `task-${String(index).padStart(4, '0')}`, task_version: '1', category: 'navigation', provider: 'reference', model: 'Reference runner', runner: 'reference', status: index % 2 ? 'PASS' : 'FAIL', started_at: '2026-01-01T00:00:00Z', wall_seconds: 2, input_tokens: null, output_tokens: null, cost_usd: null });
  await page.route('**/api/runs', route => route.fulfill({ json: [] }));
  await page.route(/\/api\/trials$/, route => { legacyUnpagedRequests += 1; return route.fulfill({ status: 410, json: { error: 'Unpaged endpoint must not be used by the dashboard.' } }); });
  await page.route('**/api/trials/page**', route => {
    const url = new URL(route.request().url()); const offset = Number(url.searchParams.get('offset'));
    return route.fulfill({ json: { items: Array.from({ length: Math.min(100, 250 - offset) }, (_, index) => row(offset + index)), total: 250, limit: 100, offset } });
  });
  await page.route(/\/api\/trials\/trial-\d+$/, route => route.fulfill({ json: {
    ...row(0), task_id: `task-${'very-long-task-name-'.repeat(12)}`, artifact_dir: `/private/local/results/${'a-long-path-segment/'.repeat(20)}`,
    verifier: { exit_code: 0, stdout: 'Verifier output\n'.repeat(40), stderr: '' },
    trace: Array.from({ length: 20 }, (_, index) => ({ timestamp: '2026-01-01T00:00:00Z', kind: 'tool', status: 'complete', payload: `trace-value-${index}` })),
    sources: { cost: 'Unavailable' },
  } }));
  await page.route('**/api/overview**', route => route.fulfill({ json: {
    summary: { trials: 250, successes: 125, completion_rate: 0.5, total_failures: 125, status_counts: { FAIL: 125 }, groups: [], categories: {} },
    providers: ['reference'], models: ['Reference runner'], tasks: Array.from({ length: 250 }, (_, index) => `task-${String(index).padStart(4, '0')}`),
    chart_trials: Array.from({ length: 2000 }, (_, index) => ({ ...row(index), id: `chart-${index}`, task_id: `matrix-task-${String(index).padStart(4, '0')}`, config_hash: `config-${String(index).padStart(4, '0')}` })), chart_sampled: true, chart_total: 250,
  } }));
  await page.goto('/');
  const accessibility = await new AxeBuilder({ page }).analyze();
  console.log('axe violations:', accessibility.violations.flatMap(v => v.nodes.map(n => `${n.target.join(' ')} — ${n.any[0]?.data?.fgColor ?? ''} / ${n.any[0]?.data?.bgColor ?? ''} (${n.any[0]?.data?.contrastRatio ?? ''})`)).join(' | '));
  expect(accessibility.violations.map(v => v.id)).toEqual([]);
  await expect(page.getByTestId('trial-row')).toHaveCount(100);
  await expect(page.getByText('Showing 1–100 of 250')).toBeVisible();
  await expect(page.getByText('Recent sample; summary metrics cover all selected trials.')).toHaveCount(2);
  await expect(page.getByTestId('success-matrix').locator('tbody tr')).toHaveCount(100);
  await expect(page.getByTestId('success-matrix').locator('thead th')).toHaveCount(21);
  await expect(page.getByText('Showing 100 of 2,000 tasks and 20 of 2,000 configurations')).toBeVisible();
  await expect(page.getByTestId('success-matrix').locator('tbody tr').first().locator('td').first()).toHaveText('0/1');
  await page.getByRole('button', { name: 'Next' }).click();
  await expect(page.getByText('Showing 101–200 of 250')).toBeVisible();
  await expect(page.getByTestId('trial-row').first()).toContainText('task-0100');
  expect(new URL(page.url()).searchParams.get('offset')).toBe('100');
  await page.reload();
  await expect(page.getByText('Showing 101–200 of 250')).toBeVisible();
  await expect(page.getByTestId('trial-row').first()).toContainText('task-0100');
  await expect(page.getByRole('button', { name: 'Previous' })).toBeEnabled();
  expect(legacyUnpagedRequests).toBe(0);
  await page.setViewportSize({ width: 320, height: 740 });
  const firstTrial = page.getByTestId('trial-row').first().getByRole('button');
  await firstTrial.click();
  const dialog = page.getByTestId('trial-detail');
  await expect(dialog).toBeVisible();
  await expect(dialog.getByRole('heading', { level: 2 })).toContainText('very-long-task-name');
  const detailA11y = await new AxeBuilder({ page }).analyze();
  console.log('detail axe:', detailA11y.violations.flatMap(v => v.nodes.map(n => n.target.join(' '))).join(' | '));
  expect(detailA11y.violations.map(v => v.id)).toEqual([]);
  const close = page.getByRole('button', { name: 'Close trial details' });
  await expect(close).toBeFocused();
  await page.keyboard.press('Tab');
  await expect(dialog.getByRole('region', { name: 'Trial evidence and measurements' })).toBeFocused();
  await page.keyboard.press('Tab');
  await expect(dialog.getByLabel('Verifier output', { exact: true })).toBeFocused();
  for (let index = 1; index <= 20; index += 1) {
    await page.keyboard.press('Tab');
    await expect(dialog.getByLabel(`Execution trace event ${index}`, { exact: true })).toBeFocused();
  }
  await page.keyboard.press('Tab');
  await expect(close).toBeFocused();
  await page.keyboard.press('Shift+Tab');
  await expect(dialog.getByLabel('Execution trace event 20', { exact: true })).toBeFocused();
  const widths = await page.evaluate(() => ({ viewport: document.documentElement.clientWidth, page: document.documentElement.scrollWidth }));
  expect(widths.page).toBeLessThanOrEqual(widths.viewport);
  await page.keyboard.press('Escape');
  await expect(dialog).toBeHidden();
  await expect(firstTrial).toBeFocused();
});

test('unknown final cost retains its known subtotal and distinct corpus groups', async ({page}) => {
  const trial = {id:'one',run_id:'run',task_id:'task',task_version:'1.0-integration-120s',status:'TIMEOUT',runner:'agent',provider:'openrouter',model:'model',config_hash:'same',corpus_hash:'corpus-one',cost_usd:null,cost_source:'unavailable: incomplete request',known_cost_subtotal_usd:0.02,trace:[],trace_truncated:true,trace_error:null};
  const tiny = {...trial,id:'tiny',task_id:'tiny-cost',task_version:'1.0',status:'PASS',cost_usd:0.000000042,cost_source:'provider.usage.cost',known_cost_subtotal_usd:null,trace_truncated:false};
  await page.route('**/api/runs',route=>route.fulfill({json:[]}));
  await page.route('**/api/trials/page**',route=>route.fulfill({json:{items:[trial,tiny],total:2,limit:100,offset:0}}));
  await page.route('**/api/trials/one',route=>route.fulfill({json:trial}));
  await page.route('**/api/trials/tiny',route=>route.fulfill({json:tiny}));
  await page.route('**/api/overview**',route=>route.fulfill({json:{summary:{trials:3,total_spend_usd:null,known_spend_usd:.020000042,groups:[{config_hash:'same',corpus_hash:'corpus-one',trials:1},{config_hash:'same',corpus_hash:'corpus-two',trials:2},{config_hash:'outside12345',corpus_hash:'outside67890',trials:1}]},providers:['openrouter'],models:['model'],tasks:['task'],chart_trials:[trial,{...trial,id:'two',corpus_hash:'corpus-two'},tiny],chart_total:3,chart_sampled:false}}));
  await page.goto('/');
  await expect(page.getByText('$0.020000042 known subtotal', {exact:false}).first()).toBeVisible();
  await expect(page.getByTestId('mixed-summary')).toContainText('3 configurations and task contracts');
  await expect(page.locator('.comparison-panel')).toContainText('not rankings');
  await expect(page.locator('.comparison-panel')).toContainText('settings outside1 · corpus outside6');
  await expect(page.getByTestId('trial-row').filter({hasText:'tiny-cost'})).toContainText('$0.000000042');
  await expect(page.getByTestId('success-matrix').locator('thead th')).toHaveCount(3);
  await page.getByTestId('trial-row').first().getByRole('button').click();
  await expect(page.getByTestId('trial-detail')).toContainText('Known cost subtotal');
  await expect(page.getByTestId('trial-detail')).toContainText('Integration check · 1.0-integration-120s');
  await expect(page.getByTestId('trial-detail')).toContainText('Trace preview is truncated');
  await expect(page.getByTestId('trial-detail')).not.toContainText('Actual · unavailable');
  await page.keyboard.press('Escape');
  await page.getByTestId('trial-row').filter({hasText:'tiny-cost'}).getByRole('button').click();
  await expect(page.getByTestId('trial-detail')).toContainText('$0.000000042');
});

test('failed detail request retries the same evidence without replacing the trial list', async ({page}) => {
  const trial={id:'retry-trial',run_id:'run',task_id:'retry-task',status:'PASS',runner:'reference',provider:'reference',model:'reference',config_hash:'config'};
  let requests=0;
  await page.route('**/api/runs',route=>route.fulfill({json:[]}));
  await page.route('**/api/trials/page**',route=>route.fulfill({json:{items:[trial],total:1,limit:100,offset:0}}));
  await page.route('**/api/overview**',route=>route.fulfill({json:{summary:{trials:1,groups:[]},providers:[],models:[],tasks:[],chart_trials:[],chart_total:0,chart_sampled:false}}));
  await page.route('**/api/trials/retry-trial',route=>{requests++;return requests===1?route.fulfill({status:503}):route.fulfill({json:{...trial,verifier:{exit_code:0,stdout:'Recovered evidence'}}});});
  await page.goto('/');
  await page.getByTestId('trial-row').getByRole('button').click();
  await expect(page.getByRole('alert')).toContainText('Could not load trial evidence');
  await expect(page.getByTestId('trial-row')).toHaveCount(1);
  await page.getByRole('button',{name:'Retry evidence'}).click();
  await expect(page.getByTestId('trial-detail')).toContainText('Recovered evidence');
  expect(requests).toBe(2);
  await expect(page.getByRole('alert')).toHaveCount(0);
});
