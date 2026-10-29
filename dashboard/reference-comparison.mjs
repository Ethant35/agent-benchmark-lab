// Real reference/recovery comparison acceptance. Author: Ethan.
// Run after tests/usability_e2e.py --recovery-mode success; serve its result root.
import { chromium, expect } from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';
import assert from 'node:assert/strict';
import { mkdir, readFile, writeFile } from 'node:fs/promises';
import path from 'node:path';

const [base, output] = process.argv.slice(2);
assert(base && output, 'Usage: node dashboard/reference-comparison.mjs http://127.0.0.1:PORT OUTPUT');
assert(['127.0.0.1', 'localhost'].includes(new URL(base).hostname), 'Use a local dashboard');
await mkdir(output, { recursive: true });
const get = async endpoint => {
  const response = await fetch(new URL(endpoint, base));
  assert(response.ok, `${endpoint}: ${response.status}`);
  return response.json();
};
const trials = await get('/api/trials');
const interrupted = trials.find(t => t.runner === 'reference' && t.status === 'INTERRUPTED');
assert(interrupted, 'Requires a real interrupted reference attempt');
const resumed = trials.find(t => t.run_id === interrupted.run_id && t.status === 'PASS');
const first = trials.find(t => t.runner === 'reference' && t.status === 'PASS' && t.config_hash !== interrupted.config_hash);
assert(resumed && first, 'Requires the resumed PASS and a distinct reference configuration');
const endpoint = `/api/comparison?left=${first.config_hash}&right=${resumed.config_hash}`;
const comparison = await get(endpoint);
assert.equal(comparison.matched_tasks, 1);
const match = comparison.matches[0];
assert.equal(match.runner, 'reference');
assert.equal(match.task_version, first.task_version);
assert.equal(match.left.attempts, 1);
assert.equal(match.left.passes, 1);
assert.equal(match.right.attempts, 2);
assert.equal(match.right.passes, 1);
assert.deepEqual(match.right.evidence.map(e => e.id).sort(), [interrupted.id, resumed.id].sort());
assert.equal(match.left.cost_usd, 0);
assert.equal(match.right.cost_usd, 0);
assert.equal(match.pass_rate_delta, -0.5); // Attempt history, not recovered schedule success.
assert.match(comparison.uncertainty, /not independent paired trials/);
await writeFile(path.join(output, 'comparison-api.json'), JSON.stringify(comparison, null, 2) + '\n');
const browser = await chromium.launch();
try {
  const context = await browser.newContext({ colorScheme: 'dark' });
  const page = await context.newPage();
  await page.goto(base);
  const panel = page.getByTestId('matched-comparisons');
  await panel.locator(':scope > summary').click();
  await panel.getByLabel('Comparison configuration A').selectOption(first.config_hash);
  await panel.getByLabel('Comparison configuration B').selectOption(resumed.config_hash);
  await expect(panel.getByTestId('matched-results')).toContainText('1 matched task contracts');
  await expect(panel).toContainText('Reference control');
  await expect(panel).toContainText('1/1 passed (100.0%)');
  await expect(panel).toContainText('1/2 passed (50.0%)');
  await expect(panel).toContainText('1 interrupted or cancelled');
  await panel.getByText('B attempt evidence', { exact: true }).click();
  const evidence = panel.getByRole('button', { name: new RegExp(`Open comparison attempt ${interrupted.id}`) });
  await evidence.click();
  await expect(page.getByTestId('trial-detail')).toContainText('INTERRUPTED');
  await page.keyboard.press('Escape');
  await expect(evidence).toBeFocused();
  const pending = page.waitForEvent('download');
  await panel.getByRole('link', { name: 'Export comparison JSON' }).click();
  const download = await pending;
  assert.equal(download.suggestedFilename(), 'matched-comparison.json');
  const downloaded = path.join(output, 'comparison-download.json');
  await download.saveAs(downloaded);
  assert.deepEqual(JSON.parse(await readFile(downloaded, 'utf8')), comparison);
  const accessibility = await new AxeBuilder({ page }).include('.matched-comparisons').withRules(['color-contrast']).analyze();
  assert.deepEqual(accessibility.violations, []);
  await page.screenshot({ path: path.join(output, 'reference-comparison-dark.png'), fullPage: true });
  await page.setViewportSize({ width: 320, height: 800 });
  assert(await page.evaluate(() => document.documentElement.scrollWidth <= document.documentElement.clientWidth));
  await page.screenshot({ path: path.join(output, 'reference-comparison-mobile.png'), fullPage: true });
  await writeFile(path.join(output, 'checks.json'), JSON.stringify({author:'Ethan',status:'PASS',provider_calls:0,cost_usd:0,real_reference_attempts:3,recovered_attempt_unchanged:'verified by usability_e2e.py',matched_contracts:1,attempt_counts:[1,2],pass_counts:[1,1],download_matches_api:true,dark_label_contrast:'PASS',mobile_320px:'PASS',evidence_navigation_and_focus:'PASS',scope:'Reference and harness behavior only; not model quality'}, null, 2) + '\n');
  console.log('PASS: real recovered reference comparison, retained evidence, download, contrast and mobile layout');
} finally {
  await browser.close();
}
