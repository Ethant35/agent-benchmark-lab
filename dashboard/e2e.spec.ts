import { test, expect } from '@playwright/test';
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
  await expect(page.getByTestId('trial-row')).toHaveCount(trials.length);
  const expectedCompletion = summary.completion_rate == null ? 'Unavailable' : `${(summary.completion_rate > 1 ? summary.completion_rate : summary.completion_rate * 100).toFixed(1)}%`;
  await expect(page.getByTestId('completion-rate')).toHaveText(expectedCompletion);
  const expectedMedian = summary.median_wall_seconds == null ? 'Unavailable' : `${summary.median_wall_seconds.toLocaleString(undefined, { maximumFractionDigits: 1 })}s`;
  await expect(page.getByTestId('median-wall')).toHaveText(expectedMedian);

  if (runId) { await page.getByTestId('filter-run').selectOption(runId); const filtered = await request.get(`/api/trials?run_id=${encodeURIComponent(runId)}`); await expect(page.getByTestId('trial-row')).toHaveCount((await filtered.json()).length); }
  const provider = trials.find((t: { provider?: string }) => t.provider)?.provider;
  if (provider) { await page.getByTestId('filter-provider').selectOption(provider); const filtered = await request.get(`/api/trials?run_id=${encodeURIComponent(runId)}&provider=${encodeURIComponent(provider)}`); await expect(page.getByTestId('trial-row')).toHaveCount((await filtered.json()).length); }
  const model = trials.find((t: { model?: string }) => t.model)?.model;
  if (model) { await page.getByTestId('filter-model').selectOption(model); const filtered = await request.get(`/api/trials?run_id=${encodeURIComponent(runId)}&provider=${encodeURIComponent(provider ?? '')}&model=${encodeURIComponent(model)}`); await expect(page.getByTestId('trial-row')).toHaveCount((await filtered.json()).length); }
  const task = trials.find((t: { task_id?: string }) => t.task_id)?.task_id;
  if (task) { await page.getByTestId('filter-task').selectOption(task); const filtered = await request.get(`/api/trials?run_id=${encodeURIComponent(runId)}&provider=${encodeURIComponent(provider ?? '')}&model=${encodeURIComponent(model ?? '')}&task_id=${encodeURIComponent(task)}`); await expect(page.getByTestId('trial-row')).toHaveCount((await filtered.json()).length); }
  await page.getByRole('button', { name: 'Reset' }).click();
  const allResponse = await request.get('/api/trials'); const allTrials = await allResponse.json();
  await expect(page.getByTestId('trial-row')).toHaveCount(allTrials.length);
  const row = page.getByTestId('trial-row').first(); await row.click();
  await expect(page.getByTestId('trial-detail')).toBeVisible(); await expect(page.getByTestId('verifier-evidence')).toBeVisible();
  const detail = await request.get(`/api/trials/${encodeURIComponent(allTrials[0].id)}`); const selected = await detail.json();
  if (selected.verifier?.stdout) await expect(page.getByTestId('verifier-evidence')).toContainText(selected.verifier.stdout.slice(0, 30));
  await page.getByRole('button', { name: 'Close trial details' }).click();
  await mkdir('test-results', { recursive: true }); await page.screenshot({ path: 'test-results/dashboard.png', fullPage: true });
  await page.setViewportSize({ width: 390, height: 844 });
  const widths = await page.evaluate(() => ({ viewport: document.documentElement.clientWidth, page: document.documentElement.scrollWidth }));
  expect(widths.page).toBeLessThanOrEqual(widths.viewport);
  await page.screenshot({ path: 'test-results/dashboard-mobile.png', fullPage: true });
});

test('both export formats download from the persisted API', async ({ page }) => {
  await page.goto('/');
  const csvDownload = page.waitForEvent('download'); await page.getByRole('link', { name: 'Export CSV' }).click(); const csv = await csvDownload; expect(csv.suggestedFilename().toLowerCase()).toContain('csv');
  const jsonDownload = page.waitForEvent('download'); await page.getByRole('link', { name: 'Export JSON' }).click(); const json = await jsonDownload; expect(json.suggestedFilename().toLowerCase()).toContain('json');
});
