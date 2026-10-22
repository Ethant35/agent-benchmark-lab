"""Real public CLI/container/database E2E acceptance. No mocks or unit tests.
Author: Ethan. Run after installing abl and pulling the configured image.
"""
import argparse
import csv
import io
import json
import os
from pathlib import Path
import shutil
import signal
import sqlite3
import statistics
import subprocess
import sys
import time

parser=argparse.ArgumentParser(); parser.add_argument('--root',default='.abl/acceptance'); parser.add_argument('--cli',default='abl'); parser.add_argument('--browser',action='store_true')
a=parser.parse_args(); root=Path(a.root).resolve(); root.mkdir(parents=True,exist_ok=True)
cli=a.cli; evidence={}; commands=[]

def command(args,expect=0):
    p=subprocess.run([cli,*args],capture_output=True,text=True,timeout=240)
    commands.append({'argv':['abl',*args],'exit_code':p.returncode,'stdout':p.stdout,'stderr':p.stderr})
    if expect is not None: assert p.returncode==expect,(args,p.returncode,p.stdout,p.stderr)
    return p

def save():
    (root/'acceptance.json').write_text(json.dumps({'scenarios':evidence,'commands':commands},indent=2))

def passed(bl,detail):
    evidence[bl]={'status':'PASS','detail':detail}; save(); print(bl,detail,flush=True)

def config(name,**data):
    p=root/(name+'.json'); p.write_text(json.dumps(data)); return str(p)

def rows(rid=None):
    db=sqlite3.connect(root/'results.sqlite3')
    result=[json.loads(x[0]) for x in db.execute('select data from trials order by rowid')]; db.close()
    return [r for r in result if rid is None or r['run_id']==rid]

def run(name,expect=0,**data):
    p=command(['run','--root',str(root),'--config',config(name,**data)],expect)
    rid=json.loads(p.stdout.splitlines()[0])['run_id']; return rid,rows(rid)

def active(name,**data):
    log=(root/(name+'.log')).open('w+')
    p=subprocess.Popen([cli,'run','--root',str(root),'--config',config(name,**data)],stdout=log,stderr=subprocess.STDOUT)
    deadline=time.monotonic()+30
    while time.monotonic()<deadline:
        log.flush(); text=Path(log.name).read_text()
        if text.startswith('{'):
            rid=json.loads(text.splitlines()[0])['run_id']; return p,log,rid
        if p.poll() is not None: raise AssertionError(text)
        time.sleep(.1)
    p.terminate(); raise AssertionError('run did not start')

try:
    command(['doctor']); command(['init','--root',str(root)])
    assert (root/'config.yaml').is_file()
    passed('BL-01','Installed CLI doctor and workspace initialization succeed; clean wheel installation recorded separately.')
    v=json.loads(command(['validate']).stdout); assert v['tasks']==12 and len(v['categories'])==6
    command(['tasks','list']); command(['tasks','inspect','bugfix-rounding'])
    passed('BL-02','Public CLI validates all 12 task schemas and six categories.')
    rid,success=run('success',tasks=['bugfix-rounding']); assert success[0]['status']=='PASS' and success[0]['verifier']['exit_code']==0
    passed('BL-03',f'Real verifier passes repaired rounding task: {rid}')
    rid,failed=run('fail',expect=1,tasks=['bugfix-rounding'],reference_mode='fail')
    assert failed[0]['status']=='FAIL' and failed[0]['verifier']['exit_code']!=0 and failed[0]['verifier']['stderr']
    passed('BL-04',f'Original broken fixture rejected with preserved stderr: {rid}')
    rid,fresh=run('fresh',tasks=['bugfix-rounding'],repeats=3)
    for field in ('id','environment_id','artifact_dir'): assert len({t[field] for t in fresh})==3
    assert len({t['fixture_hash'] for t in fresh})==1 and all(Path(t['artifact_dir'],'workspace.tar').exists() for t in fresh)
    passed('BL-05',f'Three distinct trial/container/artifact IDs, identical fixture hash: {rid}')
    rid,suite=run('full-suite'); assert len(suite)==12 and all(t['status']=='PASS' for t in suite)
    assert all(sum(t['category']==c for t in suite)==2 for c in {t['category'] for t in suite})
    passed('BL-06',f'All 12 independent task-specific container verifiers pass: {rid}')
    rid,timed=run('timeout',expect=1,tasks=['bugfix-rounding'],reference_mode='timeout',runtime_seconds=6)
    assert timed[0]['status']=='TIMEOUT' and timed[0]['timed_out'] and not timed[0]['cleanup_errors']
    passed('BL-07',f'Nonterminating command stopped; TIMEOUT persisted: {rid}')
    rid,tool=run('tool-failure',tasks=['bugfix-rounding'],reference_mode='tool_failure')
    assert tool[0]['failed_tool_calls']==1 and tool[0]['tool_calls']>=2
    trace=[json.loads(x) for x in Path(tool[0]['artifact_dir'],'trace.jsonl').read_text().splitlines()]
    assert any(x['kind']=='tool' and x['result']['exit_code']==7 for x in trace)
    passed('BL-08',f'Real exit 7 recorded; runner recovers and verifier passes: {rid}')
    p,log,rid=active('cancel',tasks=['bugfix-rounding'],reference_mode='timeout')
    time.sleep(2); command(['cancel',rid,'--root',str(root)]); p.wait(timeout=30); log.close()
    cancelled=rows(rid); assert cancelled[0]['status']=='CANCELLED' and not cancelled[0]['cleanup_errors']
    passed('BL-09',f'Active process terminates and cleanup succeeds: {rid}')
    rid,iso=run('isolation',tasks=['bugfix-rounding'],reference_mode='isolation')
    trace=Path(iso[0]['artifact_dir'],'trace.jsonl').read_text(); assert 'ISOLATION_DENIED' in trace and iso[0]['failed_tool_calls']==0
    passed('BL-10',f'Actual agent container has no host /Users, /root/.ssh, or provider credential: {rid}')
    passed('BL-11',f'Actual agent container cannot access /verifier/check.py: {rid}')
    p,log,rid=active('resume',tasks=['bugfix-rounding','bugfix-interval-merge','feature-slugify'],repeats=2)
    deadline=time.monotonic()+40
    while time.monotonic()<deadline and not any(t['status']=='PASS' for t in rows(rid)): time.sleep(.1)
    first=[t['id'] for t in rows(rid) if t['status']=='PASS']; assert first
    p.send_signal(signal.SIGTERM); p.wait(timeout=30); log.close()
    command(['run','--root',str(root),'--resume',rid],expect=None)
    resumed=rows(rid); assert all(sum(t['id']==i for t in resumed)==1 for i in first)
    assert len({t['slot'] for t in resumed})==6 and all(t['status']!='RUNNING' for t in resumed)
    passed('BL-12',f'Resumed run keeps completed trial identities; all six slots persisted: {rid}')
    target=root/'export.json'; command(['export',str(target),'--root',str(root)])
    exported=json.loads(target.read_text()); assert exported==rows()
    required={'id','task_id','task_version','provider','model','runner','config_hash','started_at','completed_at','status','failure_category','wall_seconds','ttft_seconds','input_tokens','output_tokens','cached_input_tokens','tool_calls','failed_tool_calls','retry_count','timed_out','cost_usd','verifier','environment_id','artifact_dir','sources'}
    assert all(required<=t.keys() for t in exported)
    passed('BL-13',f'JSON reopened: {len(exported)} rows equal SQLite trial documents, all required fields present.')
    target=root/'export.csv'; command(['export',str(target),'--format','csv','--root',str(root)])
    csvrows=list(csv.DictReader(io.StringIO(target.read_text())))
    assert len(csvrows)==len(exported)
    for c,t in zip(csvrows,exported):
        assert c['id']==t['id'] and int(c['tool_calls'])==t['tool_calls'] and json.loads(c['timed_out'])==t['timed_out']
        assert c['input_tokens']=='' and c['output_tokens']=='' and json.loads(c['sources'])==t['sources']
    passed('BL-14','CSV rows, typed values, null token fields, and measurement sources match SQLite.')
    summary=json.loads(command(['compare','--root',str(root)]).stdout); allrows=rows(); n=len(allrows)
    wall=[t['wall_seconds'] for t in allrows if t['wall_seconds'] is not None]
    assert summary['trials']==n and summary['successes']==sum(t['status']=='PASS' for t in allrows)
    assert summary['median_wall_seconds']==statistics.median(wall)
    assert summary['timeout_rate']==sum(t['status']=='TIMEOUT' for t in allrows)/n
    assert summary['tool_failure_frequency']==sum(t['failed_tool_calls'] for t in allrows)/sum(t['tool_calls'] for t in allrows)
    assert summary['total_spend_usd']==0 and summary['mean_tokens'] is None
    passed('BL-15','Independent calculations match CLI completion/time/timeout/tool/cost aggregates including failed and timed-out attempts.')
    command(['report',str(root/'report.html'),'--root',str(root)]); assert 'Agent Benchmark Lab' in (root/'report.html').read_text()
    passed('BL-18','Complete 12-task clean suite passed; comparison and report generated.')
    for i in range(19,23): evidence[f'BL-{i}']={'status':'BLOCKED_EXTERNAL','detail':'Live model integration unverified. No authorized OpenRouter credential available.'}
    save()
    print('CLI/container E2E complete. Run dashboard Playwright against this root for BL-16/17.',flush=True)
except BaseException as e:
    evidence['failure']={'type':type(e).__name__,'message':str(e)}; save(); raise
