"""Real isolated grader acceptance; reference and mutant controls, no provider.
Author: Ethan
Run: uv run --frozen python tests/grader_v2_e2e.py --root .abl/grader-v2/acceptance
"""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import signal
import uuid

from abl.engine import Execution, corpus_manifest, image_identity, manifest_hash
from abl.models import Config, load_tasks
from abl.store import Store


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--root',type=Path,required=True)
    parser.add_argument('--only',default='');args=parser.parse_args()
    root=args.root.resolve();root.mkdir(parents=True,exist_ok=True)
    store=Store(root/'results');tasks=load_tasks();config=Config(runtime='podman')
    image=image_identity('podman',config.image);results=[]
    def stop(signum,frame):raise KeyboardInterrupt()
    signal.signal(signal.SIGTERM,stop)
    def execute(tid,label,expected,mutation=None,mode='success'):
        if args.only and args.only not in f'{tid}/{label}':return
        task,original=tasks[tid];folder=root/'cases'/f'{tid}-{label}'
        shutil.copytree(original,folder)
        actions=json.loads((folder/'reference.json').read_text())
        if mutation: mutation(actions)
        (folder/'reference.json').write_text(json.dumps(actions,indent=2)+'\n')
        cfg=config.model_copy(update={'reference_mode':mode});rid=uuid.uuid4().hex
        manifest=corpus_manifest({tid:(task,folder)},[tid],image)
        store.create_run(rid,cfg.model_dump(),manifest)
        execution=Execution(store,rid,0,task,folder,cfg,'podman');execution.box.image=image
        execution.t['corpus_hash']=manifest_hash(manifest)
        record=execution.execute();store.state(rid,'COMPLETED')
        result={'task':tid,'case':label,'expected':expected,'status':record['status'],'trial_id':record['id'],
                'failure_category':record['failure_category'],'verifier':record['verifier'],
                'wall_seconds':record['wall_seconds'],'cost_usd':record['cost_usd'],'cleanup_errors':record['cleanup_errors']}
        results.append(result);(root/'acceptance.json').write_text(json.dumps({'author':'Ethan','kind':'local reference and deliberately altered controls, not model scores','image_id':image,'cases':results},indent=2)+'\n')
        print(tid,label,record['status'],flush=True)
        assert record['status']==expected,result
        assert not record['cleanup_errors'] and record['cost_usd']==0,result
        assert record['verifier'] is not None,result
    def source_replace(old,new):
        def mutate(actions):
            action=next(a for a in actions if a['tool']=='write_file' and a['arguments']['path'].endswith('.py'))
            assert old in action['arguments']['content'],old
            action['arguments']['content']=action['arguments']['content'].replace(old,new)
        return mutate
    def append_source(code):
        def mutate(actions):
            action=next(a for a in actions if a['tool']=='write_file' and a['arguments']['path'].endswith('.py'))
            action['arguments']['content']+='\n'+code+'\n'
        return mutate
    def output_change(code):
        import shlex
        return lambda actions: actions.append({'tool':'shell','arguments':{'command':'python -c '+shlex.quote(code)}})
    def answer_change(change):
        def mutate(actions):
            action=next(a for a in actions if a['tool']=='write_file' and a['arguments']['path'].endswith('.json'))
            answer=json.loads(action['arguments']['content']);change(answer)
            action['arguments']['content']=json.dumps(answer,indent=4,sort_keys=True)+'\n'
        return mutate
    for tid in tasks:
        execute(tid,'reference','PASS');execute(tid,'unsolved','FAIL',mode='fail')
    for tid,code in [
        ('bugfix-rounding','def format_price(x): return "wrong"'),
        ('bugfix-interval-merge','def merge_intervals(x): return []'),
        ('feature-slugify','def slugify(x): return "wrong"'),
        ('refactor-csv-summary','def summarize(rows): return {}'),
        ('refactor-text-stats','def count_words(tokens): return {}')]:
        execute(tid,'broken-helper-correct-cli','FAIL',append_source(code))
    execute('bugfix-interval-merge','tuple-return','FAIL',source_replace(' return out',' return tuple(out)'))
    execute('refactor-text-stats','tuple-tokens','FAIL',source_replace('return [w.casefold() for w in text.split()]','return tuple(w.casefold() for w in text.split())'))
    execute('bugfix-interval-merge','exclusive-boundary','FAIL',source_replace('a<=out[-1][1]','a<out[-1][1]'))
    execute('feature-order-filter','paid-only','FAIL',source_replace("r['status']==a.status","r['status']=='paid'"))
    execute('feature-order-filter','exclusive-minimum','FAIL',source_replace("r['total']>=a.minimum","r['total']>a.minimum"))
    execute('feature-slugify','no-unicode-normalization','FAIL',source_replace('unicodedata.normalize("NFKD",s)','s'))
    execute('refactor-csv-summary','unsorted-json','FAIL',source_replace('sort_keys=True','sort_keys=False'))
    execute('refactor-text-stats','unsorted-json','FAIL',source_replace('sort_keys=True','sort_keys=False'))
    baseline=(tasks['refactor-csv-summary'][1]/'fixture/summary.py').read_text()
    execute('refactor-csv-summary','unused-helpers','FAIL',source_replace('if __name__=="__main__": print(json.dumps(summarize(parse_rows(sys.argv[1])),sort_keys=True))',baseline))
    baseline=(tasks['refactor-text-stats'][1]/'fixture/text_stats.py').read_text()
    execute('refactor-text-stats','unused-helpers','FAIL',source_replace('if __name__=="__main__": print(json.dumps(count_words(tokenize(open(sys.argv[1],encoding="utf-8").read())),sort_keys=True))',baseline))
    for tid,file,field in [('multistep-document-index','docs.json','bytes'),('multistep-ledger','transactions.json','cents')]:
        code=f"import json,hashlib; p={file!r}; d=json.load(open(p)); d[0][{field!r}]=float(d[0][{field!r}]); open(p,'w').write(json.dumps(d)); m=json.load(open('manifest.json')); m['sha256'][p]=hashlib.sha256(open(p,'rb').read()).hexdigest(); open('manifest.json','w').write(json.dumps(m))"
        execute(tid,'float-value-with-valid-digest','FAIL',output_change(code))
        count='document_count' if 'document' in tid else 'row_count'
        execute(tid,'float-count','FAIL',output_change(f"import json; m=json.load(open('manifest.json')); m[{count!r}]=float(m[{count!r}]); open('manifest.json','w').write(json.dumps(m))"))
        execute(tid,'missing-saved-output','FAIL',output_change(f"from pathlib import Path; Path({file!r}).unlink()"))
        execute(tid,'saved-output-only-no-general-program','FAIL',output_change("from pathlib import Path; Path("+repr('indexer.py' if 'document' in tid else 'pipeline.py')+").write_text('pass\\n')"))
    execute('navigation-config','contradictory-claim','FAIL',answer_change(lambda a:a['explanation']['cache'].update(value=True)))
    execute('navigation-routes','contradictory-claim','FAIL',answer_change(lambda a:a['explanation']['health'].update(methods=['POST'])))
    for tid in ['navigation-config','navigation-routes']:
        execute(tid,'keyword-salad','FAIL',answer_change(lambda a:a.update(explanation='port retry cache formats /health /items GET POST DELETE')))
        execute(tid,'reordered-structured-explanation','PASS',answer_change(lambda a:None))
        source='settings.py' if tid.endswith('config') else 'routes.py'
        execute(tid,'modified-source','FAIL',output_change(f"from pathlib import Path; p=Path({source!r}); p.write_text(p.read_text()+'# changed\\n')"))
    execute('extraction-contacts','changed-phone','FAIL',answer_change(lambda a:a[0].update(phone='15415550198')))
    execute('extraction-contacts','extra-field','FAIL',answer_change(lambda a:a[0].update(extra='no')))
    execute('extraction-invoices','float-cents','FAIL',answer_change(lambda a:a[0].update(amount_cents=1995.0)))
    for tid in ['extraction-contacts','extraction-invoices']:
        execute(tid,'wrong-order','FAIL',answer_change(lambda a:a.reverse()))
        execute(tid,'alternate-json-format','PASS',answer_change(lambda a:None))
    print('All',len(results),'isolated cases matched expectations',flush=True)

if __name__=='__main__':main()
