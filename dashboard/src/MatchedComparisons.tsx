import { useEffect, useRef, useState } from 'react';

type Evidence = { id: string; status: string; outcome_kind: string; verifier_exit_code: number | null; cost_usd: number | null; known_cost_subtotal_usd: number | null; cost_source: string | null };
type Side = { attempts: number; passes: number; outcomes: Record<string, number>; cost_usd: number | null; known_cost_subtotal_usd: number | null; cost_sources: Record<string, number>; median_wall_seconds: number | null; measured_wall_attempts: number; active_run: boolean; evidence: Evidence[]; evidence_sampled: boolean };
type Match = { task_id: string; task_version: string; task_artifact_id: string; image_id: string; runner: string; left: Side; right: Side; pass_rate_delta: number; cost_delta_usd: number | null; wall_delta_seconds: number | null };
type Comparison = { matches: Match[]; matched_tasks: number; display_limited: boolean; differences: { setting: string; left: unknown; right: unknown }[]; excluded: { left: Record<string, number>; right: Record<string, number> }; uncertainty: string; basis: string };
const money = (value: number | null) => value == null ? 'Unavailable' : `$${value.toLocaleString(undefined, {minimumFractionDigits: 4, maximumFractionDigits: 12})}`;
const seconds = (value: number | null) => value == null ? 'Unavailable' : `${value.toFixed(2)}s`;
const words = (value: string) => value.replaceAll('_', ' ');
const valueText = (value: unknown) => value == null ? 'Default / unset' : typeof value === 'object' ? JSON.stringify(value) : String(value);

function SideResult({ side, task, label, onEvidence }: { side: Side; task: string; label: string; onEvidence: (id: string, task: string, trigger: HTMLButtonElement) => void }) {
    return <>
      <strong>{side.passes}/{side.attempts} passed ({(side.passes / side.attempts * 100).toFixed(1)}%)</strong>
      <small>{Object.entries(side.outcomes).map(([kind, n]) => `${n} ${words(kind)}`).join(' · ')}</small>
      <small>Median {seconds(side.median_wall_seconds)} · {side.measured_wall_attempts}/{side.attempts} measured</small>
      <small>{side.cost_usd == null ? `${money(side.known_cost_subtotal_usd)} known subtotal; total unavailable` : `${money(side.cost_usd)} terminal attempt cost`}</small>
      <small>{Object.entries(side.cost_sources).map(([kind, n]) => `${n} ${kind}`).join(' · ')}</small>
      {side.active_run && <small>Run active; final total unavailable.</small>}
      <details><summary>{label} attempt evidence</summary>
        {side.evidence_sampled && <p>First 100 attempts shown; totals include all attempts.</p>}
        <ul>{side.evidence.map(e => <li key={e.id}><button className="trial-open" onClick={event => onEvidence(e.id, task, event.currentTarget)} aria-label={`${e.status} · ${e.id.slice(0, 8)} — Open comparison attempt ${e.id}`}>{e.status} · {e.id.slice(0, 8)}</button><small>Verifier exit {e.verifier_exit_code ?? 'unavailable'} · {money(e.cost_usd)} · {words(e.outcome_kind)}</small></li>)}</ul>
      </details>
    </>;
  }


export default function MatchedComparisons({ configurations, filters, refresh, onEvidence }: {
  configurations: { hash: string; label: string }[]; filters: string; refresh: number;
  onEvidence: (id: string, task: string, trigger: HTMLButtonElement) => void;
}) {
  const [left, setLeft] = useState('');
  const [right, setRight] = useState('');
  const [opened, setOpened] = useState(false);
  const [data, setData] = useState<Comparison | null>(null);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [retry, setRetry] = useState(0);
  const valid = left !== right && configurations.some(c => c.hash === left) && configurations.some(c => c.hash === right);
  const params = new URLSearchParams(filters); params.set('left', left); params.set('right', right);
  const url = `/api/comparison?${params}`;
  const previousUrl = useRef('');
  useEffect(() => {
    if (previousUrl.current !== url || !valid) setData(null);
    previousUrl.current = url; setError(''); setLoading(false);
    if (!opened || !valid) return;
    const controller = new AbortController(); setLoading(true);
    fetch(url, { signal: controller.signal }).then(r => {
      if (!r.ok) throw new Error(`Comparison request failed (${r.status})`);
      return r.json() as Promise<Comparison>;
    }).then(value => { setData(value); setLoading(false); }).catch(reason => {
      if (reason.name !== 'AbortError') { setError(String(reason)); setLoading(false); }
    });
    return () => controller.abort();
  }, [url, valid, opened, refresh, retry]);


  return <details className="analysis-details matched-comparisons" onToggle={event => setOpened(event.currentTarget.open)} data-testid="matched-comparisons">
    <summary>Matched comparisons</summary>
    <section className="panel" aria-label="Matched configuration comparison">
      <p>Compare saved attempts on identical task contracts. Current filters apply.</p>
      <div className="comparison-controls">{(['A', 'B'] as const).map((label, i) => <label key={label}>Configuration {label}<select aria-label={`Comparison configuration ${label}`} value={i === 0 ? left : right} onChange={event => (i === 0 ? setLeft : setRight)(event.target.value)}><option value="">Choose configuration</option>{configurations.map(c => <option key={c.hash} value={c.hash}>{c.label}</option>)}</select></label>)}</div>
      {configurations.length < 2 && <p>At least two configurations are needed. Clear filters to inspect other saved runs.</p>}
      {left && right && left === right && <p role="status">Choose two different configurations.</p>}
      {loading && <p role="status">Loading matched attempts…</p>}
      {error && <div role="alert"><p>{error}</p><button onClick={() => setRetry(v => v + 1)}>Retry comparison</button></div>}
      {data && <div data-testid="matched-results">
        <p>{data.matched_tasks} matched task contracts. {data.uncertainty}</p>
        <details><summary>Matching rules and exclusions</summary><p>{data.basis}</p>{(['left', 'right'] as const).map((side, i) => <p key={side}>Configuration {i === 0 ? 'A' : 'B'}: {Object.entries(data.excluded[side]).map(([reason, n]) => `${n} ${words(reason)}`).join(' · ') || 'No excluded attempts'}</p>)}</details>
        {data.differences.length > 0 && <div className="table-wrap" role="region" aria-label="Changed configuration settings" tabIndex={0}><table><thead><tr><th>Changed setting</th><th>A</th><th>B</th></tr></thead><tbody>{data.differences.map(d => <tr key={d.setting}><th>{words(d.setting)}</th><td>{valueText(d.left)}</td><td>{valueText(d.right)}</td></tr>)}</tbody></table></div>}
        {!data.matches.length && <p>No verified equivalent tasks. Different versions, images, runner kinds or missing identities cannot be matched.</p>}
        {data.display_limited && <p>First 200 matched contracts shown. Narrow the task filter for the rest.</p>}
        {data.matches.length > 0 && <div className="table-wrap" role="region" aria-label="Matched task results" tabIndex={0}><table><thead><tr><th>Task contract</th><th>Configuration A</th><th>Configuration B</th><th>Difference (B − A)</th></tr></thead><tbody>{data.matches.map(m => <tr key={`${m.task_artifact_id}-${m.image_id}-${m.runner}`}><th>{m.task_id}<small>v{m.task_version} · {m.runner === 'reference' ? 'Reference control' : m.task_version.includes('integration') ? 'Integration check' : 'Model benchmark'}</small><details><summary>Contract identity</summary><small>Task {m.task_artifact_id}</small><small>Image {m.image_id}</small></details></th><td><SideResult side={m.left} task={m.task_id} label="A" onEvidence={onEvidence}/></td><td><SideResult side={m.right} task={m.task_id} label="B" onEvidence={onEvidence}/></td><td><small>{(m.pass_rate_delta * 100).toFixed(1)} percentage points</small><small>{seconds(m.wall_delta_seconds)} median time</small><small>{money(m.cost_delta_usd)} total cost</small><small>{m.left.attempts === 1 || m.right.attempts === 1 ? 'One-attempt sample; reliability unknown.' : 'Retained attempts include retries; reliability uncertain.'}</small></td></tr>)}</tbody></table></div>}
        <a className="button secondary" href={url} download="matched-comparison.json">Export comparison JSON</a>
      </div>}
    </section>
  </details>;
}
