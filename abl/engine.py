"""Trial lifecycle, bounded agent loop, and observable verifier decisions."""
import fcntl
import hashlib
import json
import os
from pathlib import Path
import signal
import time
import uuid
from .models import Config, load_tasks, tree_hash
from .store import Store, now
from .isolation import Sandbox, runtime_name, BoundaryError, TrialTimeout, TrialCancelled
from .providers import CompatibleProvider, ProviderError, Unsupported, CredentialsMissing, BudgetExceeded

class StepLimit(RuntimeError): pass

def trial_record(rid,slot,task,folder,config,root):
    tid=uuid.uuid4().hex
    return dict(id=tid,run_id=rid,slot=slot,task_id=task.id,task_version=task.version,category=task.category,
        provider=config.provider,model=config.model,runner=config.runner,config_hash=config.fingerprint(),
        started_at=now(),completed_at=None,status='RUNNING',failure_category=None,wall_seconds=None,
        ttft_seconds=None,api_seconds=None,input_tokens=None,output_tokens=None,cached_input_tokens=None,
        tool_calls=0,failed_tool_calls=0,retry_count=0,timed_out=False,cost_usd=0 if config.runner=='reference' else None,
        cost_source='no_provider_requests' if config.runner=='reference' else 'unavailable',
        verifier=None,environment_id='abl-'+tid,artifact_dir=str(root/'artifacts'/tid),
        task_artifact_id=tree_hash(folder),fixture_hash=tree_hash(folder/'fixture'),image_id=None,
        sources={'identity':'orchestrator UUID/config SHA256','status':'orchestrator/independent verifier exit status',
            'wall_seconds':'monotonic clock including setup/verification/cleanup', 'ttft_seconds':'unavailable',
            'api_seconds':'unavailable','input_tokens':'unavailable','output_tokens':'unavailable',
            'cached_input_tokens':'unavailable','tool_calls':'executor trace','failed_tool_calls':'nonzero tool exit, interruption, or validation failure',
            'retry_count':'orchestrator; requests are never automatically retried','timed_out':'orchestrator deadline',
            'cost_usd':'no_provider_requests' if config.runner=='reference' else 'unavailable',
            'artifacts':'SHA256 task/fixture and container image identifiers','timestamps':'UTC system clock'})

class Execution:
    def __init__(self,store,rid,slot,task,folder,config,runtime):
        self.store=store; self.rid=rid; self.task=task; self.folder=folder; self.config=config
        self.t=trial_record(rid,slot,task,folder,config,store.root)
        self.dir=Path(self.t['artifact_dir']); self.dir.mkdir(parents=True)
        (self.dir/'agent').mkdir(); (self.dir/'verifier').mkdir()
        self.start=time.monotonic(); self.trace=[]
        deadline=self.start+min(task.runtime_seconds,config.runtime_seconds or task.runtime_seconds)
        self.box=Sandbox(runtime,config.image,self.t['id'],deadline,lambda:store.cancelled(rid))
        self.limit=min(task.max_tool_steps,config.max_tool_steps if config.max_tool_steps is not None else task.max_tool_steps)
        self.store.save(self.t); self.requests=[]; self.request_pending=False
    def event(self,kind,**data):
        event=dict(timestamp=now(),kind=kind,**data); self.trace.append(event)
        with (self.dir/'trace.jsonl').open('a') as f: f.write(json.dumps(event)+'\n')
        self.store.save(self.t)
    def tool(self,name,args):
        self.box.check()
        if self.t['tool_calls']>=self.limit: raise StepLimit('Maximum tool calls reached')
        self.t['tool_calls']+=1
        try:
            if name not in self.task.allowed_tools: raise ValueError('Tool not permitted')
            if not isinstance(args,dict): raise ValueError('Tool arguments must be an object')
            result=self.box.tool(name,args)
        except (TrialTimeout,TrialCancelled) as e:
            self.t['failed_tool_calls']+=1
            self.event('tool',tool=name,arguments=args,result={'exit_code':None,'stdout':'','stderr':str(e),'interrupted':True})
            raise
        except (KeyError,ValueError,TypeError) as e:
            result=dict(exit_code=2,stdout='',stderr=str(e),seconds=0)
        if result['exit_code']!=0: self.t['failed_tool_calls']+=1
        self.event('tool',tool=name,arguments=args,result=result)
        return result
    def reference(self):
        mode=self.config.reference_mode
        if mode=='fail': return
        if mode=='timeout': self.tool('shell',{'command':'sleep 3600'}); return
        if mode=='tool_failure': self.tool('shell',{'command':'python -c "raise SystemExit(7)"'})
        if mode=='isolation':
            probe="""import os,pathlib,socket
for name in ['/verifier/check.py','/root/.ssh/id_rsa','HOST_SENTINEL']:
 try:
  pathlib.Path(name).read_bytes()
 except (FileNotFoundError,PermissionError,NotADirectoryError): pass
 else: raise AssertionError('Forbidden path readable: '+name)
assert not os.environ.get('OPENROUTER_API_KEY')
assert not os.environ.get('ABL_ISOLATION_SECRET')
s=socket.socket(); s.settimeout(1)
try: s.connect(('1.1.1.1',443))
except OSError: pass
else: raise AssertionError('Network available')
print('ISOLATION_DENIED')
"""
            import shlex
            probe=probe.replace('HOST_SENTINEL',str(self.store.root/'host-sentinel'))
            self.tool('shell',{'command':'python -c '+shlex.quote(probe)})
        actions=json.loads((self.folder/'reference.json').read_text())
        for action in actions:
            result=self.tool(action['tool'],action['arguments'])
            if result['exit_code']!=0: raise RuntimeError('Reference action failed: '+result['stderr'])
    def usage(self,result):
        self.requests.append(result)
        for field,key in [('input_tokens','prompt_tokens'),('output_tokens','completion_tokens'),('cached_input_tokens','cached_tokens')]:
            values=[]
            for r in self.requests:
                usage=r.get('usage') or {}
                value=(usage.get('prompt_tokens_details') or {}).get(key) if key=='cached_tokens' else usage.get(key)
                values.append(value if isinstance(value,(float,int)) and value>=0 else None)
            self.t[field]=sum(values) if all(v is not None for v in values) else None
            self.t['sources'][field]='provider.usage.'+key if self.t[field] is not None else 'unavailable/incomplete provider usage'
        costs=[(r.get('usage') or {}).get('cost') for r in self.requests]
        if all(isinstance(v,(float,int)) and v>=0 for v in costs):
            self.t['cost_usd']=sum(costs); self.t['cost_source']='provider.usage.cost'
        else:
            # Estimates are explicit and conservative; include every request.
            self.t['cost_usd']=sum(r['request_reserve_usd'] for r in self.requests)
            self.t['cost_source']='estimated request reserves; byte upper bound and configured prices'
        self.t['sources']['cost_usd']=self.t['cost_source']
        self.t['api_seconds']=sum(r['api_seconds'] for r in self.requests)
        self.t['sources']['api_seconds']='monotonic per request, distinct from wall time'
        if self.t['ttft_seconds'] is None and result['ttft_seconds'] is not None:
            self.t['ttft_seconds']=result['ttft_seconds']; self.t['sources']['ttft_seconds']='first streamed output measured from request start'
    def agent(self):
        provider=CompatibleProvider(self.config)
        messages=[{'role':'system','content':'Complete the task using the permitted tools. Files are in /workspace. Do not assume success; finish when done.'},
            {'role':'user','content':self.task.description}]
        budget=min(self.config.spend_limit_usd,self.task.cost_budget_usd or self.config.spend_limit_usd)
        # Run-level spend ceiling includes earlier failures and resumed attempts.
        earlier=[t for t in self.store.trials(run_id=self.rid) if t['id']!=self.t['id']]
        if any(t.get('cost_usd') is None for t in earlier): raise BudgetExceeded('Earlier attempt has unknown cost; cannot safely continue run spending')
        prior=sum(t['cost_usd'] for t in earlier)
        budget-=prior
        for _ in range(self.config.max_requests):
            token_limit=self.config.token_budget or self.task.token_budget
            if token_limit and len(json.dumps(messages).encode())+4096+self.config.max_output_tokens > token_limit-(self.t['input_tokens'] or 0)-(self.t['output_tokens'] or 0):
                raise BudgetExceeded('Conservative request token reserve exceeds remaining token budget')
            self.request_pending=True
            self.event('request_started',request_number=len(self.requests)+1)
            result=provider.request(messages,self.task.allowed_tools,self.box.check,budget-(self.t['cost_usd'] or 0))
            self.request_pending=False
            self.usage(result); self.event('provider',**result)
            token_limit=self.config.token_budget or self.task.token_budget
            if token_limit and (self.t['input_tokens'] is None or self.t['output_tokens'] is None): raise BudgetExceeded('Cannot enforce token budget without usage metadata')
            if token_limit and self.t['input_tokens']+self.t['output_tokens']>=token_limit: raise BudgetExceeded('Token budget reached')
            message=result['message']; messages.append(message)
            calls=message.get('tool_calls') or []
            if not calls: return
            finished=False
            for call in calls:
                try: args=json.loads(call['function']['arguments'])
                except (KeyError,ValueError,TypeError): args=None
                name=call.get('function',{}).get('name','invalid')
                outcome=self.tool(name,args)
                messages.append({'role':'tool','tool_call_id':call.get('id',''),'content':json.dumps(outcome)})
                if name=='finish' and outcome['exit_code']==0: finished=True
            if finished: return
        raise StepLimit('Maximum model requests reached')
    def execute(self):
        failure=None
        try:
            self.box.start(self.folder/'fixture'); self.t['image_id']=self.box.image_id
            info=json.loads(self.box.raw(['inspect',self.box.name]))[0]
            host=info['HostConfig']
            self.event('environment',network=host.get('NetworkMode'),memory=host.get('Memory'),pids_limit=host.get('PidsLimit'),read_only=host.get('ReadonlyRootfs'),security_opt=host.get('SecurityOpt'),mounts=info.get('Mounts'),user=info['Config'].get('User'))
            for command in self.task.setup:
                r=self.box.command(['sh','-c',command]); self.event('setup',result=r)
                if r['exit_code']: raise RuntimeError('Workspace setup failed')
            if self.config.runner=='reference': self.reference()
            else: self.agent()
        except StepLimit as e: failure=('FAIL','step_limit',str(e))
        except TrialCancelled as e: failure=('CANCELLED','cancelled',str(e))
        except TrialTimeout as e: failure=('TIMEOUT','runtime_limit',str(e))
        except Unsupported as e: failure=('UNSUPPORTED','unsupported_tools',str(e))
        except CredentialsMissing as e: failure=('BLOCKED_EXTERNAL','credentials_missing',str(e))
        except BudgetExceeded as e: failure=('FAIL','budget_limit',str(e))
        except ProviderError as e: failure=('ERROR','provider_error',str(e))
        except BoundaryError as e: failure=('ERROR','isolation_error',str(e))
        except Exception as e: failure=('ERROR','runner_error',str(e))
        except BaseException:
            failure=('INTERRUPTED','interrupted','Process interrupted')
            raise
        finally:
            if self.request_pending:
                self.t['known_cost_subtotal_usd']=self.t['cost_usd']
                for key in ('cost_usd','input_tokens','output_tokens','cached_input_tokens'):
                    self.t[key]=None; self.t['sources'][key]='unavailable: incomplete request'
                self.t['cost_source']='unavailable: incomplete request'
            try:
                # Stop all agent processes before snapshot and independent verification.
                self.box.raw(['stop','--time','0',self.box.name],timeout=15)
                self.box.snapshot(self.dir/'agent/workspace.tar')
                if failure is None or failure[1] in ('step_limit','budget_limit'):
                    result=self.box.verify(self.folder/'verifier',self.task.verifier)
                    self.t['verifier']=result; self.event('verifier',result=result)
                    (self.dir/'verifier/result.json').write_text(json.dumps(result,indent=2))
                    if failure is not None and result['exit_code']==0:
                        self.t['termination_reason']=failure[1]
                        failure=None
                    if failure is None:
                        failure=('PASS',None,'Verifier passed') if result['exit_code']==0 else ('FAIL','verification_failed','Verifier rejected result')
            except TrialTimeout: failure=('TIMEOUT','runtime_limit','Deadline reached during verification')
            except TrialCancelled: failure=('CANCELLED','cancelled','Cancelled during verification')
            except Exception as e:
                if failure is None: failure=('ERROR','verification_error',str(e))
            try: cleanup=self.box.cleanup()
            except Exception as e: cleanup=[str(e)]
            self.t['cleanup_errors']=cleanup
            if cleanup: failure=('ERROR','cleanup_error','Container cleanup incomplete')
            failure=failure or ('ERROR','unknown','No outcome')
            self.t.update(status=failure[0],failure_category=failure[1],completed_at=now(),
                wall_seconds=time.monotonic()-self.start,timed_out=failure[0]=='TIMEOUT')
            self.event('outcome',status=failure[0],failure_category=failure[1],detail=failure[2])
            (self.dir/'trial.json').write_text(json.dumps(self.t,indent=2))
            self.store.save(self.t)
        return self.t

def run_suite(root,config,resume=None):
    store=Store(root); runtime=runtime_name(config.runtime); tasks=load_tasks()
    chosen=config.tasks or list(tasks)
    if any(t not in tasks for t in chosen): raise ValueError('Unknown task ID')
    rid=resume or uuid.uuid4().hex
    lock=(store.root/(rid+'.lock')).open('w')
    try:
        try: fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        except BlockingIOError: raise ValueError('This run is already active')
        if resume:
            old=store.run(rid)
            if not old: raise ValueError('Run not found')
            if old['config']!=config.model_dump(): raise ValueError('Resume config must match persisted configuration')
            # Crash-recovery keeps completed slots and records abandoned running attempts.
            for t in store.trials(run_id=rid):
                if t['status']=='RUNNING':
                    box=Sandbox(runtime,config.image,t['id'],time.monotonic()+30,lambda:False)
                    t['cleanup_errors']=box.cleanup()
                    t.update(status='INTERRUPTED',failure_category='process_lost',completed_at=now())
                    store.save(t)
            store.state(rid,'RUNNING',False)
        else: store.create_run(rid,config.model_dump())
        print(json.dumps({'run_id':rid}),flush=True)
        previous={t['slot']:t for t in store.trials(run_id=rid)}
        old_handler=signal.getsignal(signal.SIGTERM)
        def terminate(signum,frame): raise KeyboardInterrupt()
        signal.signal(signal.SIGTERM,terminate)
        try:
            for slot,tid in enumerate(chosen*config.repeats):
                if slot in previous and previous[slot]['status'] not in ('INTERRUPTED','CANCELLED'): continue
                if store.cancelled(rid): break
                t=Execution(store,rid,slot,*tasks[tid],config,runtime).execute()
                print(json.dumps({'trial_id':t['id'],'task_id':tid,'status':t['status']}),flush=True)
            store.state(rid,'CANCELLED' if store.cancelled(rid) else 'COMPLETED')
        except KeyboardInterrupt:
            store.state(rid,'INTERRUPTED'); raise
        finally: signal.signal(signal.SIGTERM,old_handler)
    finally: lock.close()
    return rid
