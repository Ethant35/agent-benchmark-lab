import React, { useEffect, useMemo, useRef, useState } from 'react';
import { createRoot } from 'react-dom/client';
import { Activity, ArrowDownToLine, BarChart3, Check, CircleHelp, Clock3, Database, Filter, Gauge, Layers3, RefreshCw, Search, ShieldAlert, Sparkles, Wrench, X } from 'lucide-react';
import './style.css';

type Run = { id: string; status: string; created_at: string; config?: { runner?: string; provider?: string; model?: string; [key: string]: unknown } };
type Trial = {
  id: string; run_id: string; task_id: string; task_version?: string; category?: string; provider?: string; model?: string; runner?: string;
  config_hash?: string; corpus_hash?: string | null; status: string; failure_category?: string | null; started_at?: string; completed_at?: string;
  wall_seconds?: number | null; ttft_seconds?: number | null; input_tokens?: number | null; output_tokens?: number | null;
  cached_input_tokens?: number | null; tool_calls?: number; failed_tool_calls?: number; retry_count?: number; timed_out?: boolean;
  cost_usd?: number | null; known_cost_subtotal_usd?: number | null; trace_truncated?: boolean; trace_error?: string | null; cost_source?: string | null; verifier?: { exit_code?: number | null; stdout?: string; stderr?: string; stdout_truncated?: boolean; stderr_truncated?: boolean; output_complete?: boolean };
  artifact_dir?: string | null; environment_id?: string | null; sources?: Record<string, string>; trace?: Record<string, unknown>[];
};
type Metrics = { trials?: number; successes?: number; completion_rate?: number | null; total_failures?: number; timeout_rate?: number | null; tool_failure_frequency?: number | null; median_wall_seconds?: number | null; p95_wall_seconds?: number | null; median_ttft_seconds?: number | null; mean_tokens?: number | null; median_tokens?: number | null; total_spend_usd?: number | null; known_spend_usd?: number | null; cost_per_success_usd?: number | null; wall_stddev_seconds?: number | null; measured_cost_trials?: number; actual_cost_trials?: number; estimated_cost_trials?: number; measured_token_trials?: number; status_counts?: Record<string, number>; categories?: Record<string, { trials?: number; successes?: number; completion_rate?: number | null }>; groups?: (Metrics & { runner?: string; provider?: string; model?: string; config_hash?: string; corpus_hash?: string | null })[] };
type Overview = { summary: Metrics; providers: string[]; models: string[]; tasks: string[]; chart_trials: Trial[]; chart_sampled: boolean; chart_total: number };
type TrialPage = { items: Trial[]; total: number; limit: number; offset: number };
const PAGE_SIZE = 100;
const MATRIX_TASK_LIMIT = 100;
const MATRIX_CONFIGURATION_LIMIT = 20;
function initialQueryValue(name: string) { return new URLSearchParams(window.location.search).get(name) ?? ''; }
function initialOffset() {
  const value = Number(initialQueryValue('offset'));
  return Number.isSafeInteger(value) && value >= 0 ? Math.floor(value / PAGE_SIZE) * PAGE_SIZE : 0;
}
const fmt = (n: number | null | undefined, digits = 1) => n == null || !Number.isFinite(n) ? 'Unavailable' : n.toLocaleString(undefined, { maximumFractionDigits: digits });
const pct = (n: number | null | undefined) => n == null ? 'Unavailable' : `${fmt(n > 1 ? n : n * 100, 1)}%`;
const money = (n: number | null | undefined) => n == null ? 'Unavailable' : `$${n.toFixed(4)}`;
const count = (n: number | null | undefined) => n == null ? 'Unavailable' : Math.round(n).toLocaleString();
const date = (s?: string) => s ? new Date(s).toLocaleString() : '—';
const statusClass = (s: string) => `status status-${s.toLowerCase()}`;
const configKey = (t: Trial) => [t.runner || 'runner', t.provider || '', t.model || '', t.config_hash || '', t.corpus_hash || 'legacy-unknown'].join('|');
const configLabel = (t: Trial) => `${t.model || (t.runner === 'reference' ? 'Reference runner' : 'Unknown model')} · ${(t.config_hash || 'no hash').slice(0, 8)} · corpus ${t.corpus_hash?.slice(0, 8) || 'unknown'}`;
const costLabel = (source?: string | null) => !source ? 'Cost source unavailable' : source.includes('estimated') ? `Estimated · ${source}` : source === 'provider.usage.cost' ? 'Actual provider charge' : source === 'no_provider_requests' ? 'No provider requests' : source;

function App() {
  const [runs, setRuns] = useState<Run[]>([]);
  const [trials, setTrials] = useState<Trial[]>([]);
  const [chartTrials, setChartTrials] = useState<Trial[]>([]);
  const [chartSampled, setChartSampled] = useState(false);
  const [totalTrials, setTotalTrials] = useState(0);
  const [providers, setProviders] = useState<string[]>([]);
  const [models, setModels] = useState<string[]>([]);
  const [allTasks, setAllTasks] = useState<string[]>([]);
  const [offset, setOffset] = useState(initialOffset);
  const [summary, setSummary] = useState<Metrics>({});
  const [runId, setRunId] = useState(() => initialQueryValue('run_id'));
  const [provider, setProvider] = useState(() => initialQueryValue('provider'));
  const [model, setModel] = useState(() => initialQueryValue('model'));
  const [task, setTask] = useState(() => initialQueryValue('task_id'));
  const [selected, setSelected] = useState<Trial | null>(null);
  const trialTrigger = useRef<HTMLButtonElement | null>(null);
  const [error, setError] = useState('');
  const [detailFailure, setDetailFailure] = useState<{trial: Trial; trigger: HTMLButtonElement; message: string} | null>(null);
  const [detailLoading, setDetailLoading] = useState(false);
  const [loading, setLoading] = useState(true);
  const [refresh, setRefresh] = useState(0);
  const [showGettingStarted, setShowGettingStarted] = useState(() => {
    try { return localStorage.getItem('abl.dashboard.getting-started.v1') !== 'dismissed'; }
    catch { return true; }
  });

  useEffect(() => { const controller = new AbortController(); fetch('/api/runs', { signal: controller.signal }).then(r => { if (!r.ok) throw new Error(`Runs request failed (${r.status})`); return r.json() as Promise<Run[]>; }).then(setRuns).catch(e => { if (e.name !== 'AbortError') setError(String(e)); }); return () => controller.abort(); }, [refresh]);
  useEffect(() => {
    const params = new URLSearchParams();
    if (runId) params.set('run_id', runId); if (provider) params.set('provider', provider); if (model) params.set('model', model); if (task) params.set('task_id', task);
    const filters = params.toString();
    const pageParams = new URLSearchParams(filters); pageParams.set('limit', String(PAGE_SIZE)); pageParams.set('offset', String(offset));
    setLoading(true); setError('');
    const controller = new AbortController();
    Promise.all([fetch(`/api/trials/page?${pageParams}`, { signal: controller.signal }).then(r => { if (!r.ok) throw new Error(`Trial page request failed (${r.status})`); return r.json() as Promise<TrialPage>; }), fetch(`/api/overview${filters ? `?${filters}` : ''}`, { signal: controller.signal }).then(r => { if (!r.ok) throw new Error(`Overview request failed (${r.status})`); return r.json() as Promise<Overview>; })])
      .then(([page, overview]) => { setTrials(page.items); setTotalTrials(page.total); setSummary(overview.summary); setChartTrials(overview.chart_trials); setChartSampled(overview.chart_sampled); setProviders(overview.providers); setModels(overview.models); setAllTasks(overview.tasks); setLoading(false); }).catch(e => { if (e.name !== 'AbortError') { setError(String(e)); setTrials([]); setChartTrials([]); setTotalTrials(0); setSummary({}); setLoading(false); } });
    return () => controller.abort();
  }, [runId, provider, model, task, offset, refresh]);
  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const values: Record<string, string> = { run_id: runId, provider, model, task_id: task };
    for (const [key, value] of Object.entries(values)) value ? params.set(key, value) : params.delete(key);
    if (offset) params.set('offset', String(offset)); else params.delete('offset');
    const query = params.toString();
    window.history.replaceState(null, '', `${window.location.pathname}${query ? `?${query}` : ''}${window.location.hash}`);
  }, [runId, provider, model, task, offset]);
  const categories = summary.categories ?? {};
  const sortedCategories = Object.entries(categories).sort(([a], [b]) => a.localeCompare(b));
  const configurations = [...new Map(chartTrials.map(t => [configKey(t), t])).entries()];
  const estimatedCostTrials = summary.estimated_cost_trials;
  const actualCostTrials = summary.actual_cost_trials;
  const tasks = [...new Set(chartTrials.map(t => t.task_id))].sort();
  const matrixTasks = tasks.slice(0, MATRIX_TASK_LIMIT);
  const matrixConfigurations = configurations.slice(0, MATRIX_CONFIGURATION_LIMIT);
  const matrixLimited = tasks.length > matrixTasks.length || configurations.length > matrixConfigurations.length;
  const matrixSubtitle = matrixLimited
    ? `Showing ${count(matrixTasks.length)} of ${count(tasks.length)} tasks and ${count(matrixConfigurations.length)} of ${count(configurations.length)} configurations${chartSampled ? ' in recent sample.' : '.'}`
    : chartSampled ? 'Recent sample only. Use trial records for the full filtered set.' : 'Observed results by task and distinct configuration.';
  const matrixCounts = new Map<string, { total: number; passed: number }>();
  for (const trial of chartTrials) {
    const key = `${trial.task_id}\u0000${configKey(trial)}`;
    const entry = matrixCounts.get(key) ?? { total: 0, passed: 0 };
    entry.total += 1;
    if (trial.status === 'PASS') entry.passed += 1;
    matrixCounts.set(key, entry);
  }
  const rows = useMemo(() => summary.groups ?? [], [summary.groups]);
  const exportUrl = (format: string) => { const p = new URLSearchParams({ format }); if (runId) p.set('run_id', runId); if (provider) p.set('provider', provider); if (model) p.set('model', model); if (task) p.set('task_id', task); return `/api/export?${p.toString()}`; };
  async function openTrial(t: Trial, trigger: HTMLButtonElement) { if (detailLoading) return; trialTrigger.current = trigger; setDetailFailure(null); setDetailLoading(true); try { const r = await fetch(`/api/trials/${encodeURIComponent(t.id)}`); if (!r.ok) throw new Error(`Trial evidence request failed (${r.status})`); setSelected(await r.json()); } catch (error) { setDetailFailure({trial: t, trigger, message: String(error)}); } finally { setDetailLoading(false); } }
  function closeTrial() { setSelected(null); trialTrigger.current?.focus({ preventScroll: true }); }
  function dismissGettingStarted() {
    setShowGettingStarted(false);
    try { localStorage.setItem('abl.dashboard.getting-started.v1', 'dismissed'); } catch { /* Keep the help available for this session. */ }
  }

  return <div className="app-shell">
    <header className="topbar"><a className="skip-link" href="#main-content">Skip to results</a><a className="brand" href="#"><span className="brand-mark"><Activity size={18}/></span><span>Agent Benchmark <b>Lab</b></span></a><div className="top-actions"><span className="local-pill"><span/> Local results</span><button className="help-button" onClick={() => setShowGettingStarted(value => !value)}><CircleHelp size={16} aria-hidden="true"/> Getting started</button><button className="icon-button" aria-label="Refresh results" disabled={loading} onClick={() => setRefresh(x => x + 1)}><RefreshCw size={16}/></button></div></header>
    <main className="page" id="main-content" tabIndex={-1}>
      <div className="page-heading"><div><h1>Benchmark results</h1><p>Review locally saved task outcomes, measurements, and evidence.</p></div><div className="export-actions"><a className="button secondary" href={exportUrl('csv')} download><ArrowDownToLine size={15}/> Export CSV</a><a className="button primary" href={exportUrl('json')} download><ArrowDownToLine size={15}/> Export JSON</a></div></div>
      {showGettingStarted && <section className="getting-started" aria-label="Getting started" data-testid="onboarding"><div><h2>Getting started</h2><p>Run <code>abl doctor</code> to check Python and your Docker or Podman engine. Then use the CLI to run tasks and open this dashboard on the same results folder.</p><ul><li><strong>Reference run:</strong> Reference runs validate the benchmark in containers; they do not call a model or measure model quality.</li><li><strong>Model run:</strong> needs a provider config and credentials. It can incur charges; the dashboard itself never starts a run or sends data.</li><li><strong>Refresh:</strong> after a CLI run finishes, refresh to read the updated local results.</li></ul><a href="https://github.com/Ethant35/agent-benchmark-lab#run-the-entire-reference-suite" target="_blank" rel="noreferrer">CLI quickstart</a></div><button className="icon-button" aria-label="Dismiss getting started" onClick={dismissGettingStarted}><X size={16}/></button></section>}
      <section className="filterbar" aria-label="Benchmark filters"><div className="filter-title"><Filter size={15}/> Filters</div><label>Run<select data-testid="filter-run" value={runId} onChange={e => { setOffset(0); setRunId(e.target.value); }}><option value="">All runs</option>{runs.map(r => <option key={r.id} value={r.id}>{r.id.slice(0, 12)} · {r.config?.runner ?? r.status}</option>)}</select></label><label>Provider<select data-testid="filter-provider" value={provider} onChange={e => { setOffset(0); setProvider(e.target.value); }}><option value="">All providers</option>{providers.map(x => <option key={x}>{x}</option>)}</select></label><label>Model<select data-testid="filter-model" value={model} onChange={e => { setOffset(0); setModel(e.target.value); }}><option value="">All models</option>{models.map(x => <option key={x}>{x}</option>)}</select></label><label>Task<select data-testid="filter-task" value={task} onChange={e => { setOffset(0); setTask(e.target.value); }}><option value="">All tasks</option>{allTasks.map(x => <option key={x}>{x}</option>)}</select></label><button className="reset-button" onClick={() => { setOffset(0); setRunId(''); setProvider(''); setModel(''); setTask(''); }}><X size={14}/> Reset</button></section>
      {error && <div className="error-banner" role="alert"><ShieldAlert size={18}/><span>Could not load benchmark results. Check that the local `abl dashboard` process is running, then retry. <small>{error}</small></span><button className="button secondary" onClick={() => setRefresh(x => x + 1)}>Retry</button></div>}
      {detailLoading && <p role="status">Loading trial evidence…</p>}
      {detailFailure && <div className="error-banner" role="alert"><ShieldAlert size={18}/><span>Could not load trial evidence for {detailFailure.trial.task_id}. <small>{detailFailure.message}</small></span><button className="button secondary" onClick={() => openTrial(detailFailure.trial, detailFailure.trigger)}>Retry evidence</button></div>}
      {loading ? <div className="loading" role="status" aria-live="polite" aria-busy="true"><RefreshCw size={18}/> Loading persisted trials…</div> : trials.length === 0 ? <div className="empty-state"><Database size={28}/><h2>No trials match these filters</h2><p>Run a benchmark or adjust the filters to see persisted results.</p><button className="button secondary" onClick={() => { setOffset(0); setRunId(''); setProvider(''); setModel(''); setTask(''); }}>Clear filters</button></div> : <>
      <section className="metrics-grid" aria-label="Summary metrics" data-testid="summary-metrics">
        <Metric title="Task completion" value={pct(summary.completion_rate)} helper={`${count(summary.successes)} of ${count(summary.trials)} trials`} icon={<Check/>} accent="teal" test="completion-rate"/>
        <Metric title="Total failures" value={count(summary.total_failures)} helper={`${pct(summary.timeout_rate)} timed out`} icon={<ShieldAlert/>} accent="rose"/>
        <Metric title="Median task time" value={summary.median_wall_seconds == null ? 'Unavailable' : `${fmt(summary.median_wall_seconds)}s`} helper={`95th percentile ${summary.p95_wall_seconds == null ? 'Unavailable' : `${fmt(summary.p95_wall_seconds)}s`}`} icon={<Clock3/>} accent="blue" test="median-wall"/>
        <Metric title="Median time to first output" value={summary.median_ttft_seconds == null ? 'Unavailable' : `${fmt(summary.median_ttft_seconds)}s`} helper="Measured from request start; streaming only" icon={<Clock3/>} accent="blue" test="median-ttft"/>
        <Metric title="Cost per success" value={money(summary.cost_per_success_usd)} helper={`${summary.total_spend_usd == null ? `${money(summary.known_spend_usd)} known subtotal; total unknown` : `${money(summary.total_spend_usd)} total`} · ${count(actualCostTrials)} actual / ${count(estimatedCostTrials)} estimated`} icon={<Gauge/>} accent="amber" test="cost-per-success"/>
      </section>
      <div className="dashboard-grid">
        <section className="panel comparison-panel"><PanelTitle icon={<Layers3/>} title="Configuration comparison" subtitle="Every attempt contributes to time, cost, and reliability."/><div className="table-wrap" role="region" aria-label="Configuration comparisons" tabIndex={0}><table data-testid="comparison-table"><thead><tr><th>Configuration</th><th>Trials</th><th>Success</th><th>Median time</th><th>Tokens avg.</th><th>Cost / success</th></tr></thead><tbody>{rows.length ? rows.map((g, i) => <tr key={`${g.config_hash}-${i}`}><td><strong>{g.model || (g.runner === 'reference' ? 'Reference runner' : 'Unknown model')}</strong><small>{g.provider || 'No provider'} · {g.runner || 'runner'} · {g.config_hash?.slice(0, 8)} · corpus {g.corpus_hash?.slice(0, 8) || 'unknown'}{g.runner === 'reference' && <em className="reference-tag">Reference</em>}</small></td><td>{count(g.trials)}</td><td><span className="success-value">{pct(g.completion_rate)}</span><small>{count(g.successes)} / {count(g.trials)}</small></td><td>{g.median_wall_seconds == null ? 'Unavailable' : `${fmt(g.median_wall_seconds)}s`}</td><td>{count(g.mean_tokens)}</td><td>{money(g.cost_per_success_usd)}</td></tr>) : <tr><td colSpan={6} className="muted-cell">No grouped comparison data returned by the API.</td></tr>}</tbody></table></div></section>
        <section className="panel"><PanelTitle icon={<BarChart3/>} title="Category breakdown" subtitle=""/>{sortedCategories.length ? <div className="category-list">{sortedCategories.map(([name, v]) => <div className="category-row" key={name}><div className="category-label"><span>{name.replaceAll('_', ' ')}</span><b>{pct(v.completion_rate)}</b></div><div className="track"><div className="bar teal" style={{ width: `${v.completion_rate == null ? 0 : Math.max(0, Math.min(100, v.completion_rate > 1 ? v.completion_rate : v.completion_rate * 100))}%` }}/></div><small>{count(v.successes)} of {count(v.trials)} trials</small></div>)}</div> : <NoData text="Category metrics unavailable."/>}</section>
        <section className="panel"><PanelTitle icon={<Clock3/>} title="Latency distribution" subtitle={chartSampled ? 'Recent sample; summary metrics cover all selected trials.' : 'Trial wall time, including failed and timed-out attempts.'}/><LatencyChart trials={chartTrials}/><div className="chart-legend"><span><i className="dot teal-dot"/> Wall time</span><span>Median {summary.median_wall_seconds == null ? 'Unavailable' : `${fmt(summary.median_wall_seconds)}s`}</span><span>Variation {summary.wall_stddev_seconds == null ? 'Unavailable' : `±${fmt(summary.wall_stddev_seconds)}s`}</span></div></section>
        <section className="panel"><PanelTitle icon={<Sparkles/>} title="Token usage" subtitle={chartSampled ? 'Recent sample; summary metrics cover all selected trials.' : ''}/><TokenChart trials={chartTrials}/><div className="stat-strip"><span>Mean total <b>{count(summary.mean_tokens)}</b></span><span>Median total <b>{count(summary.median_tokens)}</b></span><span>Measured trials <b>{count(summary.measured_token_trials)}</b></span></div></section>
        <section className="panel"><PanelTitle icon={<Wrench/>} title="Tool reliability" subtitle="Failed tool calls divided by all recorded tool calls."/><div className="reliability-number">{pct(summary.tool_failure_frequency)}</div><div className="reliability-label">tool failure frequency across all selected trials</div></section>
        <section className="panel"><PanelTitle icon={<ShieldAlert/>} title="Failures and timeouts" subtitle="Outcomes across every selected attempt."/><div className="outcome-list">{['FAIL','TIMEOUT','ERROR','CANCELLED','UNSUPPORTED','BLOCKED_EXTERNAL','INTERRUPTED'].map(s => { const n = summary.status_counts?.[s] ?? 0; return <div key={s}><span className={statusClass(s)}>{s.replace('_', ' ')}</span><b>{n.toLocaleString()}</b></div>})}</div></section>
        <section className="panel matrix-panel"><PanelTitle icon={<Layers3/>} title="Task success matrix" subtitle={matrixSubtitle}/><div className="matrix-wrap" role="region" aria-label="Task outcome matrix" tabIndex={0}><table data-testid="success-matrix"><thead><tr><th>Task</th>{matrixConfigurations.map(([key, t]) => <th key={key}>{configLabel(t)}</th>)}</tr></thead><tbody>{matrixTasks.map(tid => <tr key={tid}><th>{tid}</th>{matrixConfigurations.map(([key]) => { const entry = matrixCounts.get(`${tid}\u0000${key}`); const total = entry?.total ?? 0; const passed = entry?.passed ?? 0; return <td key={`${tid}-${key}`} title={`${passed} pass / ${total} trials`}>{!total ? <span className="matrix-empty">—</span> : <span className={`matrix-score ${passed === total ? 'all-pass' : passed ? 'partial' : 'no-pass'}`}>{passed}/{total}</span>}</td>})}</tr>)}</tbody></table></div></section>
      </div>
      <section className="panel trial-panel"><PanelTitle icon={<Database/>} title="Trial records" subtitle="Select a trial to inspect its verifier evidence and execution trace."/><div className="table-wrap"><table data-testid="trial-table"><thead><tr><th>Task</th><th>Configuration</th><th>Outcome</th><th>Duration</th><th>Tokens</th><th>Cost</th><th>Started</th></tr></thead><tbody>{trials.map(t => <tr key={t.id} data-testid="trial-row"><td><button className="trial-open" aria-label={`Open ${t.task_id}, ${t.status}, ${configLabel(t)}`} onClick={event => openTrial(t, event.currentTarget)}><strong>{t.task_id}</strong></button><small>{t.category || 'Uncategorized'} · v{t.task_version || '—'}</small></td><td><strong>{configLabel(t)}</strong><small>{t.provider || 'No provider'} · {t.runner || 'runner'}</small></td><td><span className={statusClass(t.status)}>{t.status.replace('_', ' ')}</span>{t.failure_category && <small>{t.failure_category}</small>}</td><td>{t.wall_seconds == null ? 'Unavailable' : `${fmt(t.wall_seconds)}s`}</td><td>{t.input_tokens == null && t.output_tokens == null ? 'Unavailable' : `${count(t.input_tokens)} / ${count(t.output_tokens)}`}</td><td>{money(t.cost_usd)}<small>{costLabel(t.cost_source)}</small></td><td>{date(t.started_at)}</td></tr>)}</tbody></table></div><nav className="pagination" aria-label="Trial record pages"><span>Showing {totalTrials === 0 ? 0 : offset + 1}–{Math.min(offset + trials.length, totalTrials)} of {totalTrials.toLocaleString()}</span><button className="button secondary" disabled={loading || offset === 0} onClick={() => setOffset(Math.max(0, offset - PAGE_SIZE))}>Previous</button><button className="button secondary" disabled={loading || offset + PAGE_SIZE >= totalTrials} onClick={() => setOffset(offset + PAGE_SIZE)}>Next</button></nav></section>
      <footer>{chartSampled && <span>Charts and success matrix use a recent sample. Summary metrics use all selected trials.</span>} <span>Reference runs validate the benchmark; they are not model scores.</span></footer>
      </>}
    </main>
    {selected && <TrialDrawer trial={selected} close={closeTrial}/>}
  </div>;
}

function Metric({ title, value, helper, icon, accent, test }: { title:string; value:string; helper:string; icon:React.ReactNode; accent:string; test?:string }) { return <article className="metric-card"><div className={`metric-icon ${accent}`}>{icon}</div><div className="metric-title">{title}</div><div className="metric-value" data-testid={test}>{value}</div><div className="metric-helper">{helper}</div></article>; }
function PanelTitle({ icon, title, subtitle }: { icon:React.ReactNode; title:string; subtitle:string }) { return <div className="panel-title"><span className="panel-icon">{icon}</span><div><h2>{title}</h2><p>{subtitle}</p></div></div>; }
function NoData({ text }: { text:string }) { return <div className="no-data"><CircleHelp size={16}/>{text}</div>; }
function LatencyChart({ trials }: { trials:Trial[] }) { const vals = trials.map(t => t.wall_seconds).filter((n): n is number => n != null && Number.isFinite(n)); if (!vals.length) return <NoData text="Latency was not reported for these trials."/>; const max = Math.max(1, ...vals); const width = 520, height = 150; return <div className="chart"><svg viewBox={`0 0 ${width} ${height}`} role="img" aria-label="Wall time for each trial in seconds"><line x1="32" y1="126" x2="510" y2="126" className="axis"/><line x1="32" y1="16" x2="32" y2="126" className="axis"/>{[0, .5, 1].map(p => <g key={p}><line x1="32" y1={126 - p * 100} x2="510" y2={126 - p * 100} className="gridline"/><text x="26" y={130 - p * 100} textAnchor="end" className="chart-label">{fmt(max * p, 0)}s</text></g>)}{vals.map((n, i) => { const step = 478 / Math.max(vals.length, 1); const x = 34 + i * step + Math.max(1, step * .15); const w = Math.max(3, step * .7); const h = Math.max(2, n / max * 100); return <rect key={i} x={x} y={126-h} width={w} height={h} rx="3" className="latency-bar"><title>{fmt(n)} seconds</title></rect>})}</svg></div>; }
function TokenChart({ trials }: { trials:Trial[] }) { const measured = trials.filter(t => t.input_tokens != null || t.output_tokens != null); if (!measured.length) return <NoData text="Token usage was not reported for these trials."/>; const max = Math.max(1, ...measured.flatMap(t => [t.input_tokens ?? 0, t.output_tokens ?? 0])); return <div className="token-chart">{trials.slice(0, 9).map(t => <div className="token-column" key={t.id}><div className="token-pair">{t.input_tokens == null ? <i className="unknown-token" title="Input tokens unavailable"/> : <i style={{ height: `${Math.max(2,t.input_tokens / max * 104)}px` }} title={`Input ${count(t.input_tokens)}`}/>}{t.output_tokens == null ? <b className="unknown-token" title="Output tokens unavailable"/> : <b style={{ height: `${Math.max(2,t.output_tokens / max * 104)}px` }} title={`Output ${count(t.output_tokens)}`}/>}</div><small>{t.task_id.slice(0, 9)}</small></div>)}</div>; }
function TrialDrawer({ trial, close }: { trial:Trial; close:()=>void }) {
  function dismiss() { dialog.current?.close(); close(); }
  const dialog = useRef<HTMLDialogElement>(null);
  useEffect(() => {
    const node = dialog.current;
    if (!node) return;
    node.showModal();
    return () => { if (node.open) node.close(); };
  }, []);
  function keepFocus(event: React.KeyboardEvent<HTMLDialogElement>) {
    if (event.key !== 'Tab') return;
    const items = event.currentTarget.querySelectorAll<HTMLElement>('button, [tabindex="0"]');
    const first = items[0], last = items[items.length - 1];
    if (event.shiftKey && document.activeElement === first) { event.preventDefault(); last?.focus(); }
    else if (!event.shiftKey && document.activeElement === last) { event.preventDefault(); first?.focus(); }
  }
  const fields: [string, string | number | null | undefined][] = [
    ['Trial ID', trial.id], ['Run ID', trial.run_id], ['Task version', trial.task_version], ['Category', trial.category],
    ['Provider', trial.provider], ['Runner', trial.runner], ['Started', date(trial.started_at)], ['Completed', date(trial.completed_at)],
    ['Wall time', trial.wall_seconds == null ? 'Unavailable' : `${fmt(trial.wall_seconds)}s`],
    ['Time to first output', trial.ttft_seconds == null ? 'Unavailable' : `${fmt(trial.ttft_seconds)}s`],
    ['Input tokens', count(trial.input_tokens)], ['Output tokens', count(trial.output_tokens)], ['Cached input', count(trial.cached_input_tokens)],
    ['Cost', money(trial.cost_usd)], ['Known cost subtotal', money(trial.known_cost_subtotal_usd)], ['Cost source', costLabel(trial.cost_source)], ['Environment', trial.environment_id], ['Artifact directory', trial.artifact_dir],
  ];
  return <dialog ref={dialog} className="drawer" aria-labelledby="detail-title" data-testid="trial-detail" onKeyDown={keepFocus} onCancel={event => { event.preventDefault(); dismiss(); }} onClick={event => { if (event.target === event.currentTarget) dismiss(); }}>
    <div className="drawer-head"><div><h2 id="detail-title">{trial.task_id}</h2></div><button className="icon-button" aria-label="Close trial details" onClick={dismiss}><X size={18}/></button></div>
    <div className="drawer-content" role="region" aria-label="Trial evidence and measurements" tabIndex={0}><div className="detail-status"><span className={statusClass(trial.status)}>{trial.status}</span><span>{configLabel(trial)}</span></div>
      <dl className="detail-grid">{fields.map(([key, value]) => <div key={key}><dt>{key}</dt><dd>{value || 'Unavailable'}</dd></div>)}</dl>
      <section className="evidence" data-testid="verifier-evidence"><h3><Check size={16}/> Verifier evidence</h3><div className="evidence-meta">Exit code: {trial.verifier?.exit_code == null ? 'Unavailable' : trial.verifier.exit_code}</div>{(trial.verifier?.stdout_truncated || trial.verifier?.stderr_truncated) && <p>Output truncated. The execution trace records observed and retained byte counts.</p>}{trial.verifier?.output_complete === false && <p>Output collection was interrupted; observed byte counts may be incomplete.</p>}<h4>Output</h4><pre tabIndex={0} aria-label="Verifier output">{trial.verifier?.stdout || 'No verifier output recorded.'}</pre>{trial.verifier?.stderr && <><h4>Errors</h4><pre tabIndex={0} aria-label="Verifier errors">{trial.verifier.stderr}</pre></>}</section>
      {trial.trace_truncated && <p role="status">Trace preview is truncated. The full trace remains in the local results folder.</p>}{trial.trace_error && <p role="status">{trial.trace_error}</p>}{trial.trace?.length ? <section className="evidence"><h3><Activity size={16}/> Execution trace</h3>{trial.trace.map((event, index) => <div className="trace-row" key={index}><span>{String(event.timestamp || 'Event')}</span><b>{String(event.kind || event.tool || 'Operation')} · {String(event.status || 'recorded')}</b><pre tabIndex={0} aria-label={`Execution trace event ${index + 1}`}>{JSON.stringify(event, null, 2)}</pre></div>)}</section> : <NoData text="No execution trace was recorded."/>}
      <section className="evidence"><h3><Search size={16}/> Measurement sources</h3>{trial.sources && Object.keys(trial.sources).length ? Object.entries(trial.sources).map(([key, value]) => <div className="source-row" key={key}><b>{key.replaceAll('_', ' ')}</b><span>{value}</span></div>) : <NoData text="No measurement sources were recorded."/>}</section>
    </div>
  </dialog>;
}

createRoot(document.getElementById('root')!).render(<React.StrictMode><App/></React.StrictMode>);
