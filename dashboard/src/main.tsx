import React, { useEffect, useMemo, useRef, useState } from 'react';
import { createRoot } from 'react-dom/client';
import { Activity, ArrowDownToLine, BarChart3, Check, CircleHelp, Clock3, Database, Filter, Gauge, Layers3, RefreshCw, Search, ShieldAlert, Sparkles, Wrench, X } from 'lucide-react';
import './style.css';

type Run = { id: string; status: string; created_at: string; config?: { runner?: string; provider?: string; model?: string; [key: string]: unknown } };
type Workspace = { workspace_id: string; start_command: string; dashboard_command: string };
type Trial = {
  id: string; run_id: string; task_id: string; task_version?: string; category?: string; provider?: string; model?: string; runner?: string;
  config?: Record<string, unknown>;
  config_hash?: string; corpus_hash?: string | null; status: string; failure_category?: string | null; started_at?: string; completed_at?: string;
  wall_seconds?: number | null; ttft_seconds?: number | null; input_tokens?: number | null; output_tokens?: number | null;
  cached_input_tokens?: number | null; tool_calls?: number; failed_tool_calls?: number; retry_count?: number; timed_out?: boolean;
  cost_usd?: number | null; known_cost_subtotal_usd?: number | null; trace_truncated?: boolean; trace_error?: string | null; cost_source?: string | null; verifier?: { exit_code?: number | null; stdout?: string; stderr?: string; stdout_truncated?: boolean; stderr_truncated?: boolean; output_complete?: boolean };
  artifact_dir?: string | null; environment_id?: string | null; sources?: Record<string, string>; trace?: Record<string, unknown>[];
  task_context?: { status: 'verified' | 'unavailable'; description?: string; expected_artifacts?: string[]; reason?: string };
};
type Metrics = { trials?: number; successes?: number; completion_rate?: number | null; total_failures?: number; timeout_rate?: number | null; tool_failure_frequency?: number | null; median_wall_seconds?: number | null; p95_wall_seconds?: number | null; median_ttft_seconds?: number | null; mean_tokens?: number | null; median_tokens?: number | null; total_spend_usd?: number | null; known_spend_usd?: number | null; cost_per_success_usd?: number | null; wall_stddev_seconds?: number | null; measured_cost_trials?: number; actual_cost_trials?: number; estimated_cost_trials?: number; measured_token_trials?: number; status_counts?: Record<string, number>; categories?: Record<string, { trials?: number; successes?: number; completion_rate?: number | null }>; groups?: (Metrics & { runner?: string; provider?: string; model?: string; config_hash?: string; corpus_hash?: string | null })[] };
type ScheduleSummary = { run_id?: string | null; run_status?: string | null; tasks?: number; passed?: number; failed?: number; recovered?: number; pending?: number; unknown?: number; incomplete?: number };
type Overview = { summary: Metrics; schedule?: ScheduleSummary | null; providers: string[]; models: string[]; tasks: string[]; chart_trials: Trial[]; chart_sampled: boolean; chart_total: number };
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
const money = (n: number | null | undefined) => n == null || !Number.isFinite(n) ? 'Unavailable' : `$${n.toLocaleString(undefined, { minimumFractionDigits: 4, maximumFractionDigits: 12 })}`;
const count = (n: number | null | undefined) => n == null ? 'Unavailable' : Math.round(n).toLocaleString();
const date = (s?: string) => s ? new Date(s).toLocaleString() : '—';
const statusClass = (s: string) => `status status-${s.toLowerCase()}`;
const configKey = (t: Trial) => [t.runner || 'runner', t.provider || '', t.model || '', t.config_hash || '', t.corpus_hash || 'legacy-unknown'].join('|');
const describeConfig = (t: Trial) => {
  const options: Record<string, unknown> = t.config ?? t as Record<string, unknown>;
  if (t.runner === 'reference' || options.runner === 'reference') {
    return typeof options.reference_mode === 'string' ? `reference control ${options.reference_mode}` : 'reference control';
  }
  const readable = [
    options.streaming === true ? 'streaming' : options.streaming === false ? 'non-streaming' : '',
    typeof options.reasoning_effort === 'string' ? `reasoning ${options.reasoning_effort}` : '',
    typeof options.spend_limit_usd === 'number' ? `reserve $${options.spend_limit_usd}` : '',
  ].filter(Boolean);
  return readable.join(' · ');
};
const configLabel = (t: Trial, runConfig?: Record<string, unknown>) => {
  const details = describeConfig({ ...t, config: { ...runConfig, ...t.config } });
  return `${t.model || (t.runner === 'reference' ? 'Reference runner' : 'Unknown model')}${details ? ` · ${details}` : ''} · settings ${(t.config_hash || 'unknown').slice(0, 8)} · corpus ${t.corpus_hash?.slice(0, 8) || 'unknown'}`;
};
const primaryConfigLabel = (t: Trial, runConfig?: Record<string, unknown>) => {
  const details = describeConfig({ ...t, config: { ...runConfig, ...t.config } });
  return `${t.runner === 'reference' ? 'Reference runner' : t.model || 'Unknown model'}${details ? ` · ${details}` : ''}`;
};
const BENCHMARK_SETTINGS: Array<[string, string]> = [
  ['Runner', 'runner'], ['Provider', 'provider'], ['Model', 'model'], ['Reasoning effort', 'reasoning_effort'],
  ['Streaming', 'streaming'], ['Stream usage', 'stream_usage'], ['Temperature', 'temperature'],
  ['Maximum requests', 'max_requests'], ['Maximum output tokens', 'max_output_tokens'], ['Maximum tool steps', 'max_tool_steps'],
  ['Runtime limit (seconds)', 'runtime_seconds'], ['Token budget', 'token_budget'], ['Spending reserve (USD)', 'spend_limit_usd'],
  ['Input price / million tokens', 'input_price_per_million'], ['Output price / million tokens', 'output_price_per_million'],
  ['Repeats', 'repeats'], ['Tasks', 'tasks'], ['Container runtime', 'runtime'], ['Container image', 'image'],
  ['Reference mode', 'reference_mode'], ['Tool support', 'supports_tools'],
];
function benchmarkSettings(config?: Record<string, unknown>) {
  if (!config) return [];
  return BENCHMARK_SETTINGS.flatMap(([label, key]) => {
    const value = config[key];
    if (value === undefined || value === null) return [];
    if (Array.isArray(value)) return [[label, value.map(item => String(item)).join(', ') || 'None'] as [string, string]];
    if (typeof value === 'string' || typeof value === 'number' || typeof value === 'boolean') return [[label, String(value)] as [string, string]];
    return [];
  });
}
const groupDescription = (group: Metrics & { config_hash?: string; corpus_hash?: string | null }, sample?: Trial, runConfig?: Record<string, unknown>) => {
  const details = sample ? describeConfig({ ...sample, config: { ...runConfig, ...sample.config } }) : '';
  return `${details ? `${details} · ` : ''}settings ${(group.config_hash || 'unknown').slice(0, 8)} · corpus ${group.corpus_hash?.slice(0, 8) || 'unknown'}`;
};
const runKind = (t: Trial) => t.runner === 'reference' ? 'Reference control' : (t.task_version || '').toLowerCase().includes('integration') ? `Integration check · ${t.task_version}` : 'Model benchmark';
const costLabel = (source?: string | null) => !source ? 'Cost source unavailable' : source.includes('estimated') ? `Estimated · ${source}` : source === 'provider.usage.cost' ? 'Actual provider charge' : source === 'no_provider_requests' ? 'No provider requests' : source;

function App() {
  const urlHasState = useRef([...new URLSearchParams(window.location.search).keys()].some(key => ['run_id', 'provider', 'model', 'task_id', 'offset'].includes(key)));
  const [workspace, setWorkspace] = useState<Workspace | null>(null);
  const [workspaceReady, setWorkspaceReady] = useState(false);
  const [workspaceError, setWorkspaceError] = useState('');
  const [workspaceRetry, setWorkspaceRetry] = useState(0);
  const [restoreTrialId, setRestoreTrialId] = useState('');
  const [restoreRetry, setRestoreRetry] = useState(0);
  const [restoreError, setRestoreError] = useState('');
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
  const [schedule, setSchedule] = useState<ScheduleSummary | null>(null);
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
  const [hasLoaded, setHasLoaded] = useState(false);
  const hasLoadedRef = useRef(false);
  const [refresh, setRefresh] = useState(0);
  const [showGettingStarted, setShowGettingStarted] = useState(() => {
    try { return localStorage.getItem('abl.dashboard.getting-started.v1') === 'open'; }
    catch { return false; }
  });

  useEffect(() => {
    const controller = new AbortController();
    setWorkspaceReady(false); setWorkspaceError('');
    fetch('/api/workspace', { signal: controller.signal }).then(response => {
      if (!response.ok) throw new Error(`Workspace request failed (${response.status})`);
      return response.json() as Promise<Workspace>;
    }).then(value => {
      setWorkspace(value);
      if (!urlHasState.current) {
        try {
          const saved = JSON.parse(localStorage.getItem(`abl.dashboard.state.${value.workspace_id}`) || 'null') as { runId?: string; provider?: string; model?: string; task?: string; offset?: number; trialId?: string } | null;
          if (saved) {
            setRunId(saved.runId || ''); setProvider(saved.provider || ''); setModel(saved.model || ''); setTask(saved.task || '');
            setOffset(Number.isSafeInteger(saved.offset) && (saved.offset || 0) >= 0 ? Math.floor((saved.offset || 0) / PAGE_SIZE) * PAGE_SIZE : 0);
            setRestoreTrialId(saved.trialId || '');
          }
        } catch { /* Ignore unavailable or malformed local dashboard state. */ }
      }
      setWorkspaceReady(true);
    }).catch(error => { if (error.name !== 'AbortError') setWorkspaceError(String(error)); });
    return () => controller.abort();
  }, [workspaceRetry]);

  useEffect(() => { const controller = new AbortController(); fetch('/api/runs', { signal: controller.signal }).then(r => { if (!r.ok) throw new Error(`Runs request failed (${r.status})`); return r.json() as Promise<Run[]>; }).then(setRuns).catch(e => { if (e.name !== 'AbortError') setError(String(e)); }); return () => controller.abort(); }, [refresh]);
  const activeRuns = runs.some(run => {
    if (!['RUNNING', 'CANCELLING'].includes(run.status.toUpperCase())) return false;
    if (runId && run.id !== runId) return false;
    const config = run.config ?? {};
    if (provider && config.provider !== provider) return false;
    if (model && config.model !== model) return false;
    const configuredTasks = Array.isArray(config.tasks) ? config.tasks : [];
    if (task && configuredTasks.length > 0 && !configuredTasks.includes(task)) return false;
    return true;
  });
  useEffect(() => {
    const refreshWhenVisible = () => { if (!loading && document.visibilityState === 'visible') setRefresh(value => value + 1); };
    const timer = window.setInterval(refreshWhenVisible, 3000);
    document.addEventListener('visibilitychange', refreshWhenVisible);
    return () => { window.clearInterval(timer); document.removeEventListener('visibilitychange', refreshWhenVisible); };
  }, [loading]);
  useEffect(() => {
    const params = new URLSearchParams();
    if (runId) params.set('run_id', runId); if (provider) params.set('provider', provider); if (model) params.set('model', model); if (task) params.set('task_id', task);
    const filters = params.toString();
    const pageParams = new URLSearchParams(filters); pageParams.set('limit', String(PAGE_SIZE)); pageParams.set('offset', String(offset));
    if (!hasLoadedRef.current) setLoading(true);
    setError('');
    if (!workspaceReady || !workspace) return;
    const controller = new AbortController();
    Promise.all([fetch(`/api/trials/page?${pageParams}`, { signal: controller.signal }).then(r => { if (!r.ok) throw new Error(`Trial page request failed (${r.status})`); return r.json() as Promise<TrialPage>; }), fetch(`/api/overview${filters ? `?${filters}` : ''}`, { signal: controller.signal }).then(r => { if (!r.ok) throw new Error(`Overview request failed (${r.status})`); return r.json() as Promise<Overview>; })])
      .then(([page, overview]) => { setTrials(page.items); setTotalTrials(page.total); setSummary(overview.summary); setSchedule(overview.schedule ?? null); setChartTrials(overview.chart_trials); setChartSampled(overview.chart_sampled); setProviders(overview.providers); setModels(overview.models); setAllTasks(overview.tasks); setLoading(false); hasLoadedRef.current = true; setHasLoaded(true); }).catch(e => { if (e.name !== 'AbortError') { setError(String(e)); setLoading(false); hasLoadedRef.current = true; setHasLoaded(true); } });
    return () => controller.abort();
  }, [workspaceReady, workspace, runId, provider, model, task, offset, refresh]);
  useEffect(() => {
    if (!workspaceReady || !workspace) return;
    try { localStorage.setItem(`abl.dashboard.state.${workspace.workspace_id}`, JSON.stringify({ runId, provider, model, task, offset, trialId: selected?.id ?? restoreTrialId })); } catch { /* Dashboard remains usable without localStorage. */ }
  }, [workspaceReady, workspace, runId, provider, model, task, offset, selected?.id, restoreTrialId]);
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
  const runConfig = (trial: Trial) => runs.find(run => run.id === trial.run_id)?.config as Record<string, unknown> | undefined;
  const exportUrl = (format: string) => { const p = new URLSearchParams({ format }); if (runId) p.set('run_id', runId); if (provider) p.set('provider', provider); if (model) p.set('model', model); if (task) p.set('task_id', task); return `/api/export?${p.toString()}`; };
  async function openTrial(t: Trial, trigger: HTMLButtonElement) { if (detailLoading) return; trialTrigger.current = trigger; setDetailFailure(null); setDetailLoading(true); try { const r = await fetch(`/api/trials/${encodeURIComponent(t.id)}`); if (!r.ok) throw new Error(`Trial evidence request failed (${r.status})`); setSelected(await r.json()); } catch (error) { setDetailFailure({trial: t, trigger, message: String(error)}); } finally { setDetailLoading(false); } }
  function closeTrial() {
    setSelected(null);
    setRestoreTrialId(''); setRestoreError('');
    const trigger = trialTrigger.current ?? Array.from(document.querySelectorAll<HTMLButtonElement>('[data-trial-id]')).find(button => button.dataset.trialId === selected?.id);
    trigger?.focus({ preventScroll: true });
  }
  function dismissGettingStarted() {
    setShowGettingStarted(false);
    try { localStorage.setItem('abl.dashboard.getting-started.v1', 'closed'); } catch { /* Keep the help available for this session. */ }
  }
  function toggleGettingStarted() {
    setShowGettingStarted(value => {
      const next = !value;
      try { localStorage.setItem('abl.dashboard.getting-started.v1', next ? 'open' : 'closed'); } catch { /* Help remains available for this session. */ }
      return next;
    });
  }

  useEffect(() => {
    if (!workspaceReady || !workspace || !restoreTrialId) return;
    const controller = new AbortController();
    fetch(`/api/trials/${encodeURIComponent(restoreTrialId)}`, { signal: controller.signal }).then(response => {
      if (!response.ok) throw new Error(`Trial evidence request failed (${response.status})`);
      return response.json() as Promise<Trial>;
    }).then(trial => { setSelected(trial); setRestoreError(''); setRestoreTrialId(''); }).catch(reason => { if (reason.name !== 'AbortError') setRestoreError(String(reason)); });
    return () => controller.abort();
  }, [workspaceReady, workspace, restoreTrialId, restoreRetry]);

  return <div className="app-shell">
    <header className="topbar"><a className="skip-link" href="#main-content">Skip to results</a><a className="brand" href="#"><span className="brand-mark"><Activity size={18}/></span><span>Agent Benchmark <b>Lab</b></span></a><div className="top-actions"><span className="local-pill"><span/> Local results</span><button className="help-button" aria-expanded={showGettingStarted} onClick={toggleGettingStarted}><CircleHelp size={16} aria-hidden="true"/> Quick start</button><button className="icon-button" aria-label="Refresh results" disabled={loading} onClick={() => setRefresh(x => x + 1)}><RefreshCw size={16}/></button></div></header>
    <main className="page" id="main-content" tabIndex={-1}>
      <div className="page-heading"><div><h1>Benchmark results</h1></div><div className="export-actions"><a className="button secondary" href={exportUrl('csv')} download><ArrowDownToLine size={15}/> Export CSV</a><a className="button primary" href={exportUrl('json')} download><ArrowDownToLine size={15}/> Export JSON</a></div></div>
      {showGettingStarted && <section className="getting-started" aria-label="Quick start" data-testid="onboarding"><div><h2>Start with a free reference task</h2><p>In Terminal, run the command below. It checks the local container setup and runs one reference task without a provider key or model charge.</p>{workspace ? <pre><code>{workspace.start_command}</code></pre> : <p>{workspaceError ? 'Workspace details could not be loaded. Retry workspace lookup before running a command.' : 'Loading the command for this results folder…'}</p>}<p>To reopen these steps, choose <strong>Quick start</strong>. Optional model runs require a selected provider and model configuration, and may incur charges under that configuration’s request limits, token limits, and spending reserve.</p><p><strong>Reference controls validate task contracts. They are not model benchmark scores.</strong> Integration checks may use a longer task deadline; they do not change historical benchmark results.</p><a href="https://github.com/Ethant35/agent-benchmark-lab#get-a-first-result-without-model-charges" target="_blank" rel="noreferrer">CLI guide</a></div><button className="icon-button" aria-label="Close quick start" onClick={dismissGettingStarted}><X size={16}/></button></section>}
      <section className="filterbar" aria-label="Benchmark filters"><div className="filter-title"><Filter size={15}/> Filters</div><label>Run<select data-testid="filter-run" value={runId} onChange={e => { setLoading(true); setOffset(0); setRunId(e.target.value); }}><option value="">All runs</option>{runs.map(r => <option key={r.id} value={r.id}>{r.id.slice(0, 12)} · {r.config?.runner ?? r.status}</option>)}</select></label><label>Provider<select data-testid="filter-provider" value={provider} onChange={e => { setLoading(true); setOffset(0); setProvider(e.target.value); }}><option value="">All providers</option>{providers.map(x => <option key={x}>{x}</option>)}</select></label><label>Model<select data-testid="filter-model" value={model} onChange={e => { setLoading(true); setOffset(0); setModel(e.target.value); }}><option value="">All models</option>{models.map(x => <option key={x}>{x}</option>)}</select></label><label>Task<select data-testid="filter-task" value={task} onChange={e => { setLoading(true); setOffset(0); setTask(e.target.value); }}><option value="">All tasks</option>{allTasks.map(x => <option key={x}>{x}</option>)}</select></label><button className="reset-button" onClick={() => { if (offset || runId || provider || model || task) { setLoading(true); setOffset(0); setRunId(''); setProvider(''); setModel(''); setTask(''); } }}><X size={14}/> Reset</button></section>
      {workspaceError && <div className="error-banner" role="alert"><ShieldAlert size={18}/><span>Could not identify this results folder. No run command will be shown until workspace lookup succeeds. <small>{workspaceError}</small></span><button className="button secondary" onClick={() => { setWorkspace(null); setWorkspaceReady(false); setWorkspaceRetry(value => value + 1); }}>Retry workspace lookup</button></div>}
      {error && <div className="error-banner" role="alert"><ShieldAlert size={18}/><span>Could not load benchmark results. Check that the local `abl dashboard` process is running, then retry. <small>{error}</small></span><button className="button secondary" onClick={() => { setLoading(true); setRefresh(x => x + 1); }}>Retry</button></div>}
      {restoreError && <div className="error-banner" role="alert"><ShieldAlert size={18}/><span>Could not restore the last opened trial evidence. <small>{restoreError}</small></span><button className="button secondary" onClick={() => setRestoreRetry(value => value + 1)}>Retry evidence</button><button className="button secondary" onClick={() => { setRestoreTrialId(''); setRestoreError(''); }}>Clear saved evidence</button></div>}
      {detailLoading && <p role="status">Loading trial evidence…</p>}
      {detailFailure && <div className="error-banner" role="alert"><ShieldAlert size={18}/><span>Could not load trial evidence for {detailFailure.trial.task_id}. <small>{detailFailure.message}</small></span><button className="button secondary" onClick={() => openTrial(detailFailure.trial, detailFailure.trigger)}>Retry evidence</button></div>}
      {activeRuns && <p className="run-progress" role="status" aria-live="polite"><RefreshCw size={15}/> A benchmark run is active. Results refresh automatically every 3 seconds. Cancel it from the terminal running the CLI.</p>}
      {!loading && !error && schedule && <section className="schedule-summary" aria-label="Scheduled task outcomes" data-testid="schedule-summary">
        <div className="schedule-heading"><div><h2>{runId ? 'Selected run outcome' : 'Latest matching run outcome'}</h2><p>{schedule.run_status || 'Run status unavailable'} · {count(schedule.tasks)} scheduled tasks{schedule.run_id ? ` · ${schedule.run_id.slice(0, 12)}` : ''}</p></div><span className={statusClass(schedule.run_status || 'UNKNOWN')}>{schedule.run_status || 'UNKNOWN'}</span></div>
        <div className="schedule-stats">{schedule.tasks == null ? <div><b>Unavailable</b><span>scheduled task count</span></div> : <div><b>{count(schedule.passed)} / {count(schedule.tasks)}</b><span>tasks passed</span></div>}{Boolean(schedule.recovered) && <div><b>{count(schedule.recovered)}</b><span>passed after recovery</span></div>}{Boolean(schedule.failed) && <div><b>{count(schedule.failed)}</b><span>tasks failed</span></div>}{Boolean(schedule.incomplete) && <div><b>{count(schedule.incomplete)}</b><span>incomplete</span></div>}{Boolean(schedule.pending) && <div><b>{count(schedule.pending)}</b><span>not started</span></div>}{Boolean(schedule.unknown) && <div><b>{count(schedule.unknown)}</b><span>outcome unavailable</span></div>}<div><b>{activeRuns ? `${money(summary.known_spend_usd)} known terminal subtotal · active total unavailable` : summary.total_spend_usd == null ? `${money(summary.known_spend_usd)} known subtotal · total unavailable` : money(summary.total_spend_usd)}</b><span>{activeRuns ? 'matching active run total' : 'recorded terminal attempt cost'}</span></div></div>
        <p className="schedule-note">Counts reflect saved results at this refresh. Attempt metrics and cost below cover terminal attempts matching the current filters.</p>
      </section>}
      {loading ? workspaceError ? null : <div className={`loading ${hasLoaded ? 'loading-inline' : ''}`} role="status" aria-live="polite" aria-busy="true"><RefreshCw size={18}/> {hasLoaded ? 'Loading filtered results…' : 'Loading persisted trials…'}</div> : error || workspaceError ? null : trials.length === 0 ? <div className="empty-state"><Database size={28}/><h2>{totalTrials === 0 && !runId && !provider && !model && !task && runs.length === 0 ? 'No benchmark results yet' : totalTrials === 0 && (runId || provider || model || task) ? 'No trials match these filters' : totalTrials === 0 ? 'No trial records are saved for these runs' : 'No trials on this page'}</h2><p>{totalTrials === 0 && !runId && !provider && !model && !task && runs.length === 0 ? <>Start with the free reference task: {workspace && <code>{workspace.start_command}</code>}</> : totalTrials === 0 && (runId || provider || model || task) ? 'No saved trials match the current filters. Clear filters to return to all results.' : totalTrials === 0 ? 'The selected runs exist, but no trial records were returned. Refresh or check the local results folder.' : 'This page has no records. Return to the first page or check the saved filter state.'}</p>{(runId || provider || model || task) && <button className="button secondary" onClick={() => { setLoading(true); setOffset(0); setRunId(''); setProvider(''); setModel(''); setTask(''); }}>Clear filters</button>}{totalTrials > 0 && offset > 0 && <button className="button secondary" onClick={() => { setLoading(true); setOffset(0); }}>First page</button>}</div> : <>
      <section className="panel trial-panel" aria-label="Attempt history"><PanelTitle icon={<Database/>} title="Attempt history" subtitle="Each row is one retained attempt. Select a task to inspect its expected output and verifier evidence."/><div className="table-wrap"><table data-testid="trial-table"><thead><tr><th>Task</th><th>Configuration</th><th>Attempt result</th><th>Duration</th><th>Tokens</th><th>Cost</th><th>Started</th></tr></thead><tbody>{trials.map(t => <tr key={t.id} data-testid="trial-row"><td><button className="trial-open" data-trial-id={t.id} aria-label={`Open ${t.task_id}, ${t.status}, ${primaryConfigLabel(t, runConfig(t))}`} onClick={event => openTrial(t, event.currentTarget)}><strong>{t.task_id}</strong></button><small>{t.category || 'Uncategorized'} · v{t.task_version || '—'} · {runKind(t)}</small></td><td><strong>{primaryConfigLabel(t, runConfig(t))}</strong><small>{t.runner === 'reference' ? 'Reference control' : t.provider || 'Provider unavailable'}</small></td><td><span className={statusClass(t.status)}>{t.status.replace('_', ' ')}</span>{t.failure_category && <small>{t.failure_category}</small>}</td><td>{t.wall_seconds == null ? 'Unavailable' : `${fmt(t.wall_seconds)}s`}</td><td>{t.input_tokens == null && t.output_tokens == null ? 'Unavailable' : `${count(t.input_tokens)} / ${count(t.output_tokens)}`}</td><td>{money(t.cost_usd)}<small>{costLabel(t.cost_source)}</small></td><td>{date(t.started_at)}</td></tr>)}</tbody></table></div><nav className="pagination" aria-label="Attempt record pages"><span>Showing {totalTrials === 0 ? 0 : offset + 1}–{Math.min(offset + trials.length, totalTrials)} of {totalTrials.toLocaleString()}</span><button className="button secondary" disabled={loading || offset === 0} onClick={() => { setLoading(true); setOffset(Math.max(0, offset - PAGE_SIZE)); }}>Previous</button><button className="button secondary" disabled={loading || offset + PAGE_SIZE >= totalTrials} onClick={() => { setLoading(true); setOffset(offset + PAGE_SIZE); }}>Next</button></nav></section>
      <details className="analysis-details"><summary>Attempt metrics and configuration analysis</summary>
      <section className="metrics-grid" aria-label="Summary metrics" data-testid="summary-metrics">
        <Metric title="Attempt pass rate" value={pct(summary.completion_rate)} helper={`${count(summary.successes)} of ${count(summary.trials)} attempts`} icon={<Check/>} accent="teal" test="completion-rate"/>
        <Metric title="Total failures" value={count(summary.total_failures)} helper={`${pct(summary.timeout_rate)} timed out`} icon={<ShieldAlert/>} accent="rose"/>
        <Metric title="Median task time" value={summary.median_wall_seconds == null ? 'Unavailable' : `${fmt(summary.median_wall_seconds)}s`} helper={`95th percentile ${summary.p95_wall_seconds == null ? 'Unavailable' : `${fmt(summary.p95_wall_seconds)}s`}`} icon={<Clock3/>} accent="blue" test="median-wall"/>
        <Metric title="Median time to first output" value={summary.median_ttft_seconds == null ? 'Unavailable' : `${fmt(summary.median_ttft_seconds)}s`} helper="Measured from request start; streaming only" icon={<Clock3/>} accent="blue" test="median-ttft"/>
        <Metric title="Cost per success" value={money(summary.cost_per_success_usd)} helper={`${summary.total_spend_usd == null ? `${money(summary.known_spend_usd)} known subtotal; total unknown` : `${money(summary.total_spend_usd)} total`} · ${count(actualCostTrials)} actual / ${count(estimatedCostTrials)} estimated`} icon={<Gauge/>} accent="amber" test="cost-per-success"/>
      </section>
      {rows.length > 1 && <p className="summary-context" data-testid="mixed-summary">Summary across {count(summary.trials)} selected attempts in {count(rows.length)} configurations and task contracts. Comparisons below report independent groups.</p>}
      <div className="dashboard-grid">
        <section className="panel comparison-panel"><PanelTitle icon={<Layers3/>} title="Configuration comparison" subtitle="Independent groups by provider, model settings, and task corpus; rows are not rankings."/><div className="table-wrap" role="region" aria-label="Configuration comparisons" tabIndex={0}><table data-testid="comparison-table"><thead><tr><th>Configuration</th><th>Trials</th><th>Success</th><th>Median time</th><th>Tokens avg.</th><th>Cost / success</th></tr></thead><tbody>{rows.length ? rows.map((g, i) => { const sample = chartTrials.find(t => t.config_hash === g.config_hash && t.corpus_hash === g.corpus_hash); return <tr key={`${g.config_hash}-${i}`}><td><strong>{g.model || (g.runner === 'reference' ? 'Reference runner' : 'Unknown model')}</strong><small>{g.provider || 'No provider'} · {g.runner || 'runner'} · {groupDescription(g, sample, sample ? runConfig(sample) : undefined)}</small></td><td>{count(g.trials)}</td><td><span className="success-value">{pct(g.completion_rate)}</span><small>{count(g.successes)} / {count(g.trials)}</small></td><td>{g.median_wall_seconds == null ? 'Unavailable' : `${fmt(g.median_wall_seconds)}s`}</td><td>{count(g.mean_tokens)}</td><td>{money(g.cost_per_success_usd)}</td></tr>; }) : <tr><td colSpan={6} className="muted-cell">No grouped comparison data returned by the API.</td></tr>}</tbody></table></div></section>
        <section className="panel"><PanelTitle icon={<BarChart3/>} title="Category breakdown" subtitle=""/>{sortedCategories.length ? <div className="category-list">{sortedCategories.map(([name, v]) => <div className="category-row" key={name}><div className="category-label"><span>{name.replaceAll('_', ' ')}</span><b>{pct(v.completion_rate)}</b></div><div className="track"><div className="bar teal" style={{ width: `${v.completion_rate == null ? 0 : Math.max(0, Math.min(100, v.completion_rate > 1 ? v.completion_rate : v.completion_rate * 100))}%` }}/></div><small>{count(v.successes)} of {count(v.trials)} trials</small></div>)}</div> : <NoData text="Category metrics unavailable."/>}</section>
        <section className="panel"><PanelTitle icon={<Clock3/>} title="Latency distribution" subtitle={chartSampled ? 'Recent sample; summary metrics cover all selected trials.' : 'Trial wall time, including failed and timed-out attempts.'}/><LatencyChart trials={chartTrials}/><div className="chart-legend"><span><i className="dot teal-dot"/> Wall time</span><span>Median {summary.median_wall_seconds == null ? 'Unavailable' : `${fmt(summary.median_wall_seconds)}s`}</span><span>Variation {summary.wall_stddev_seconds == null ? 'Unavailable' : `±${fmt(summary.wall_stddev_seconds)}s`}</span></div></section>
        <section className="panel"><PanelTitle icon={<Sparkles/>} title="Token usage" subtitle={chartSampled ? 'Recent sample; summary metrics cover all selected trials.' : ''}/><TokenChart trials={chartTrials}/><div className="stat-strip"><span>Mean total <b>{count(summary.mean_tokens)}</b></span><span>Median total <b>{count(summary.median_tokens)}</b></span><span>Measured trials <b>{count(summary.measured_token_trials)}</b></span></div></section>
        <section className="panel"><PanelTitle icon={<Wrench/>} title="Tool reliability" subtitle="Failed tool calls divided by all recorded tool calls."/><div className="reliability-number">{pct(summary.tool_failure_frequency)}</div><div className="reliability-label">tool failure frequency across all selected trials</div></section>
        <section className="panel"><PanelTitle icon={<ShieldAlert/>} title="Failures and timeouts" subtitle="Outcomes across every selected attempt."/><div className="outcome-list">{['FAIL','TIMEOUT','ERROR','CANCELLED','UNSUPPORTED','BLOCKED_EXTERNAL','INTERRUPTED'].map(s => { const n = summary.status_counts?.[s] ?? 0; return <div key={s}><span className={statusClass(s)}>{s.replace('_', ' ')}</span><b>{n.toLocaleString()}</b></div>})}</div></section>
        <section className="panel matrix-panel"><PanelTitle icon={<Layers3/>} title="Task success matrix" subtitle={matrixSubtitle}/><p className="contract-note">Reference controls test the benchmark contracts. Model benchmark results and versioned integration checks remain separate, even when their task prompts match.</p><div className="matrix-wrap" role="region" aria-label="Task outcome matrix" tabIndex={0}><table data-testid="success-matrix"><thead><tr><th>Task</th>{matrixConfigurations.map(([key, t]) => <th key={key}>{configLabel(t, runConfig(t))}</th>)}</tr></thead><tbody>{matrixTasks.map(tid => <tr key={tid}><th>{tid}</th>{matrixConfigurations.map(([key]) => { const entry = matrixCounts.get(`${tid}\u0000${key}`); const total = entry?.total ?? 0; const passed = entry?.passed ?? 0; return <td key={`${tid}-${key}`} title={`${passed} pass / ${total} trials`}>{!total ? <span className="matrix-empty">—</span> : <span className={`matrix-score ${passed === total ? 'all-pass' : passed ? 'partial' : 'no-pass'}`}>{passed}/{total}</span>}</td>})}</tr>)}</tbody></table></div></section>
      </div>
      </details>
      <footer>{chartSampled && <span>Charts and success matrix use a recent sample. Summary metrics use all selected attempts.</span>} <span>Reference runs validate the benchmark; they are not model scores.</span></footer>
      </>}
    </main>
    {selected && <TrialDrawer trial={{...selected, config: runConfig(selected)}} close={closeTrial}/>}
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
    const items = Array.from(event.currentTarget.querySelectorAll<HTMLElement>('button, summary, [tabindex="0"]'))
      .filter(item => {
        if (!item.getClientRects().length) return false;
        // Closed details can retain descendant layout boxes. Only their summary
        // participates in keyboard navigation until the disclosure is open.
        for (let parent = item.parentElement; parent; parent = parent.parentElement) {
          if (parent instanceof HTMLDetailsElement && !parent.open
              && !parent.querySelector(':scope > summary')?.contains(item)) return false;
        }
        return true;
      });
    const first = items[0], last = items[items.length - 1];
    if (event.shiftKey && document.activeElement === first) { event.preventDefault(); last?.focus(); }
    else if (!event.shiftKey && document.activeElement === last) { event.preventDefault(); first?.focus(); }
  }
  const fields: [string, string | number | null | undefined][] = [
    ['Trial ID', trial.id], ['Run ID', trial.run_id], ['Result type', runKind(trial)], ['Task version', trial.task_version], ['Category', trial.category],
    ['Provider', trial.provider], ['Runner', trial.runner], ['Started', date(trial.started_at)], ['Completed', date(trial.completed_at)],
    ['Configuration identity', configLabel(trial)], ['Settings fingerprint', trial.config_hash], ['Corpus fingerprint', trial.corpus_hash],
    ['Wall time', trial.wall_seconds == null ? 'Unavailable' : `${fmt(trial.wall_seconds)}s`],
    ['Time to first output', trial.ttft_seconds == null ? 'Unavailable' : `${fmt(trial.ttft_seconds)}s`],
    ['Input tokens', count(trial.input_tokens)], ['Output tokens', count(trial.output_tokens)], ['Cached input', count(trial.cached_input_tokens)],
    ['Cost', money(trial.cost_usd)], ['Known cost subtotal', money(trial.known_cost_subtotal_usd)], ['Cost source', costLabel(trial.cost_source)], ['Environment', trial.environment_id], ['Artifact directory', trial.artifact_dir],
  ];
  const settings = benchmarkSettings(trial.config);
  return <dialog ref={dialog} className="drawer" aria-labelledby="detail-title" data-testid="trial-detail" onKeyDown={keepFocus} onCancel={event => { event.preventDefault(); dismiss(); }} onClick={event => { if (event.target === event.currentTarget) dismiss(); }}>
    <div className="drawer-head"><div><h2 id="detail-title">{trial.task_id}</h2></div><button className="icon-button" aria-label="Close trial details" onClick={dismiss}><X size={18}/></button></div>
    <div className="drawer-content" role="region" aria-label="Trial evidence and measurements" tabIndex={0}><div className="detail-status"><span className={statusClass(trial.status)}>{trial.status.replace('_', ' ')}</span><span>{runKind(trial)} · {primaryConfigLabel(trial)}</span></div>
      <section className="detail-primary" aria-label="Task and result summary" data-testid="task-result-summary">
        <div><h3>Task</h3>{trial.task_context?.status === 'verified' && trial.task_context.description ? <p>{trial.task_context.description}</p> : <p>Historical task description unavailable. {trial.task_context?.reason || 'The saved task identity could not be verified.'}</p>}</div>
        <div><h3>Expected output</h3>{trial.task_context?.status === 'verified' && trial.task_context.expected_artifacts?.length ? <ul>{trial.task_context.expected_artifacts.map((artifact, index) => <li key={`${artifact}-${index}`}>{artifact}</li>)}</ul> : <p>Expected output unavailable for this saved task.</p>}</div>
        <div className="detail-result-pair"><div><h3>Verifier result</h3><p>{trial.verifier?.exit_code == null ? 'Unavailable' : trial.verifier.exit_code === 0 ? 'Passed · exit code 0' : `Failed · exit code ${trial.verifier.exit_code}`}</p></div><div><h3>Total attempt cost</h3><p>{trial.cost_usd == null ? `${money(trial.known_cost_subtotal_usd)} known subtotal · total unavailable` : money(trial.cost_usd)}</p><small>{costLabel(trial.cost_source)}</small></div></div>
      </section>
      <section className="evidence" data-testid="verifier-evidence"><h3><Check size={16}/> Verifier evidence</h3><div className="evidence-meta">Exit code: {trial.verifier?.exit_code == null ? 'Unavailable' : trial.verifier.exit_code}</div>{(trial.verifier?.stdout_truncated || trial.verifier?.stderr_truncated) && <p>Output truncated. The execution trace records observed and retained byte counts.</p>}{trial.verifier?.output_complete === false && <p>Output collection was interrupted; observed byte counts may be incomplete.</p>}<h4>Output</h4><pre tabIndex={0} aria-label="Verifier output">{trial.verifier?.stdout || 'No verifier output recorded.'}</pre>{trial.verifier?.stderr && <><h4>Errors</h4><pre tabIndex={0} aria-label="Verifier errors">{trial.verifier.stderr}</pre></>}</section>
      <details className="technical-details"><summary>Technical details</summary>
        <section className="evidence" aria-label="Benchmark settings" data-testid="benchmark-settings"><h3>Benchmark settings</h3>{settings.length ? <dl className="settings-list">{settings.map(([label, value]) => <div key={label}><dt>{label}</dt><dd>{value}</dd></div>)}</dl> : <NoData text="Benchmark settings are unavailable for this saved attempt."/>}</section>
        <dl className="detail-grid">{fields.map(([key, value]) => <div key={key}><dt>{key}</dt><dd>{value || 'Unavailable'}</dd></div>)}</dl>
        {trial.trace_truncated && <p role="status">Trace preview is truncated. The full trace remains in the local results folder.</p>}{trial.trace_error && <p role="status">{trial.trace_error}</p>}{trial.trace?.length ? <section className="evidence"><h3><Activity size={16}/> Execution trace</h3>{trial.trace.map((event, index) => <div className="trace-row" key={index}><span>{String(event.timestamp || 'Event')}</span><b>{String(event.kind || event.tool || 'Operation')} · {String(event.status || 'recorded')}</b><pre tabIndex={0} aria-label={`Execution trace event ${index + 1}`}>{JSON.stringify(event, null, 2)}</pre></div>)}</section> : <NoData text="No execution trace was recorded."/>}
        <section className="evidence"><h3><Search size={16}/> Measurement sources</h3>{trial.sources && Object.keys(trial.sources).length ? Object.entries(trial.sources).map(([key, value]) => <div className="source-row" key={key}><b>{key.replaceAll('_', ' ')}</b><span>{value}</span></div>) : <NoData text="No measurement sources were recorded."/>}</section>
      </details>
    </div>
  </dialog>;
}

createRoot(document.getElementById('root')!).render(<React.StrictMode><App/></React.StrictMode>);
