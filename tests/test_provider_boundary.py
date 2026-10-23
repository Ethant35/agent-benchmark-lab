"""Fault-injected HTTP responses on loopback; these are not live-provider tests."""
from contextlib import contextmanager
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import threading
import time

import pytest
from pydantic import ValidationError

from abl.models import Config
from abl.providers import CompatibleProvider, ProviderError, BudgetExceeded
from abl.engine import Execution
from abl.models import load_tasks
from abl.store import Store


@contextmanager
def endpoint(payload, *, status=200, headers=None, stall=False):
    hits = []
    release = threading.Event()
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            return  # Controlled server logs must never print Authorization.
        def do_POST(self):
            body = self.rfile.read(int(self.headers['Content-Length']))
            hits.append(json.loads(body))
            self.send_response(status)
            self.send_header('Content-Type', 'text/event-stream')
            if not stall:
                self.send_header('Content-Length', str(len(payload)))
            for name, value in (headers or {}).items():
                self.send_header(name, value)
            self.end_headers()
            try:
                self.wfile.write(payload)
                self.wfile.flush()
                if stall:
                    release.wait(3)
            except (BrokenPipeError, ConnectionResetError):
                return
    server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
    server.daemon_threads = True
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f'http://127.0.0.1:{server.server_port}', hits
    finally:
        release.set()
        server.shutdown()
        server.server_close()
        thread.join()


def provider(monkeypatch, url, streaming=True):
    monkeypatch.setenv('ABL_TEST_KEY', 'controlled-secret-do-not-log')
    return CompatibleProvider(Config(runner='agent', provider='openai-compatible',
        model='controlled', api_key_env='ABL_TEST_KEY', endpoint=url,
        supports_tools=True, streaming=streaming,
        input_price_per_million=1, output_price_per_million=1))


def frame(data):
    return ('data: '+json.dumps(data)+'\n\n').encode()


def test_stream_requires_completion_marker(monkeypatch):
    payload = frame({'id':'gen-cut','choices':[{'index':0,'delta':{'content':'partial'}}]})
    with endpoint(payload) as (url, hits):
        with pytest.raises(ProviderError, match='incomplete|completion'):
            provider(monkeypatch,url).request([], ['finish'], lambda:None, 1)
        assert len(hits) == 1


@pytest.mark.parametrize('streaming,payload', [
    (True, b'data: '+b'x'*1_100_000+b'\n\n'),
    (False, json.dumps({'choices':[{'message':{'role':'assistant','content':'x'*8_100_000}}]}).encode()),
], ids=['oversized-sse-line','oversized-json-body'])
def test_response_limits_are_enforced(monkeypatch, streaming, payload):
    with endpoint(payload) as (url, _):
        with pytest.raises(ProviderError, match='limit'):
            provider(monkeypatch,url,streaming).request([], ['finish'], lambda:None, 1)


def test_generation_header_is_retained_before_interruption(monkeypatch):
    with endpoint(b': waiting\n\n', headers={'X-Generation-Id':'gen-interrupted'}, stall=True) as (url, hits):
        progress = []
        def event(kind, **data): progress.append((kind,data))
        def check():
            if any(kind == 'generation' for kind,_ in progress):
                raise TimeoutError('controlled cancellation')
        with pytest.raises(TimeoutError):
            provider(monkeypatch,url).request([], ['finish'], check, 1, progress=event)
        assert ('generation', {'response_id':'gen-interrupted'}) in progress
        assert sum(kind == 'request_started' for kind,_ in progress) == 1
        assert len(hits) == 1


def test_budget_refusal_never_marks_request_started(monkeypatch):
    with endpoint(b'') as (url, hits):
        progress = []
        with pytest.raises(BudgetExceeded):
            provider(monkeypatch,url).request([], ['finish'], lambda:None, 0,
                progress=lambda kind,**data:progress.append(kind))
        assert hits == [] and progress == []


def test_multiline_sse_and_usage_frame_are_parsed(monkeypatch):
    payload = b': comment\r\ndata: {"id":"gen-ok",\r\ndata: "choices":[{"index":0,"delta":{"content":"hello"},"finish_reason":"stop"}]}\r\n\r\n'
    payload += frame({'id':'gen-ok','choices':[], 'usage':{'prompt_tokens':2,'completion_tokens':1,'cost':.001}})
    payload += b'data: [DONE]\n\n'
    with endpoint(payload) as (url, _):
        result=provider(monkeypatch,url).request([], ['finish'], lambda:None, 1)
        assert result['message']['content'] == 'hello'
        assert result['usage']['cost'] == .001
        assert result['response_id'] == 'gen-ok'


@pytest.mark.parametrize('bad', [True, -1, float('inf'), float('nan'), '4'])
def test_invalid_usage_is_not_accepted_as_a_measurement(monkeypatch,bad):
    payload=json.dumps({'id':'gen-usage','choices':[{'message':{'role':'assistant','content':'ok'}}],
                       'usage':{'prompt_tokens':bad,'completion_tokens':1,'cost':.001}}).encode()
    with endpoint(payload) as (url,_):
        with pytest.raises(ProviderError):
            provider(monkeypatch,url,False).request([],['finish'],lambda:None,1)


def test_provider_errors_do_not_echo_credentials(monkeypatch):
    payload=b'{"error":"controlled-secret-do-not-log"}'
    with endpoint(payload,status=401) as (url,_):
        with pytest.raises(ProviderError) as error:
            provider(monkeypatch,url,False).request([],['finish'],lambda:None,1)
        assert 'controlled-secret-do-not-log' not in str(error.value)


@pytest.mark.parametrize('field',['input_price_per_million','output_price_per_million'])
def test_configuration_rejects_infinite_price_bounds(field):
    with pytest.raises(ValidationError):
        Config(**{field:float('inf')})


def execution(tmp_path, config):
    store=Store(tmp_path)
    rid='a'*32
    store.create_run(rid,config.model_dump())
    task,folder=load_tasks()['bugfix-rounding']
    return Execution(store,rid,0,task,folder,config,'unused-no-container-execution')


def test_engine_records_zero_cost_for_preflight_refusal(monkeypatch,tmp_path):
    with endpoint(b'') as (url,hits):
        config=provider(monkeypatch,url).config.model_copy(update={'spend_limit_usd':.000001})
        run=execution(tmp_path,config)
        with pytest.raises(BudgetExceeded): run.agent()
        saved=run.store.trials()[0]
        assert saved['cost_usd'] == 0
        assert saved['cost_source'] == 'no_provider_requests'
        assert not run.request_pending
        assert hits == []


def test_engine_persists_inflight_identity_and_unknown_cost(monkeypatch,tmp_path):
    payload=frame({'id':'gen-incomplete','choices':[{'index':0,'delta':{'content':'partial'}}]})
    with endpoint(payload) as (url,_):
        run=execution(tmp_path,provider(monkeypatch,url).config)
        with pytest.raises(ProviderError): run.agent()
        saved=run.store.trials()[0]
        assert saved['generation_ids'] == ['gen-incomplete']
        assert saved['cost_usd'] is None
        assert saved['known_cost_subtotal_usd'] == 0
        assert saved['request_pending'] is True


def test_echoed_credential_in_object_key_is_redacted(monkeypatch):
    payload=json.dumps({'controlled-secret-do-not-log':{'key':'controlled-secret-do-not-log'},'choices':[{'message':{'role':'assistant','content':'ok'}}]}).encode()
    with endpoint(payload) as (url,_):
        result=provider(monkeypatch,url,False).request([],['finish'],lambda:None,1)
        assert 'controlled-secret-do-not-log' not in json.dumps(result)


def test_unrepresentable_usage_cost_is_a_provider_error(monkeypatch):
    payload=json.dumps({'choices':[{'message':{'role':'assistant','content':'ok'}}],'usage':{'cost':10**400}}).encode()
    with endpoint(payload) as (url,_):
        with pytest.raises(ProviderError):provider(monkeypatch,url,False).request([],['finish'],lambda:None,1)
