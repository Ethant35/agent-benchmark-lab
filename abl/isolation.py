"""Fail-closed container execution; no agent-controlled host shell commands."""
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import tarfile
import time

class BoundaryError(RuntimeError): pass
class TrialTimeout(RuntimeError): pass
class TrialCancelled(RuntimeError): pass


def runtime_name(preferred='auto'):
    for name in (['podman','docker'] if preferred=='auto' else [preferred]):
        if shutil.which(name):
            try:
                p=subprocess.run([name,'info'],capture_output=True,timeout=15)
                if p.returncode==0: return name
            except subprocess.TimeoutExpired: pass
    raise BoundaryError('No working Docker or Podman engine. Install/start one; host execution is forbidden.')


def archive_tree(path, prefix=''):
    out=io.BytesIO()
    with tarfile.open(fileobj=out,mode='w') as tar:
        for p in sorted(Path(path).rglob('*')):
            if p.is_symlink(): raise BoundaryError('Fixture symlinks are forbidden')
            name=str(Path(prefix)/p.relative_to(path))
            info=tar.gettarinfo(str(p),arcname=name)
            info.uid=65534; info.gid=65534; info.uname=''; info.gname=''
            if p.is_file():
                with p.open('rb') as f: tar.addfile(info,f)
            else: tar.addfile(info)
    return out.getvalue()

class Sandbox:
    def __init__(self,runtime,image,trial_id,deadline,cancelled):
        self.runtime=runtime; self.image=image; self.name='abl-'+trial_id
        self.volume=self.name+'-work'; self.verifier_name=self.name+'-verify'
        self.deadline=deadline; self.cancelled=cancelled; self.image_id=None
    def check(self):
        if self.cancelled(): raise TrialCancelled('Cancellation requested')
        if time.monotonic()>self.deadline: raise TrialTimeout('Trial runtime exceeded')
    def raw(self,args,input=None,timeout=30):
        p=subprocess.run([self.runtime,*args],input=input,capture_output=True,timeout=timeout)
        if p.returncode: raise BoundaryError(p.stderr.decode(errors='replace')[:2000])
        return p.stdout
    def flags(self,name,user='65534:65534'):
        return ['--name',name,'--label','abl.managed=true','--network','none','--read-only',
            '--cap-drop','ALL','--security-opt','no-new-privileges','--pids-limit','64',
            '--memory','256m','--memory-swap','256m','--cpus','1','--user',user,
            '--tmpfs','/tmp:rw,noexec,nosuid,size=32m','-e','PYTHONDONTWRITEBYTECODE=1',
            '-v',self.volume+':/workspace:rw','-w','/workspace']
    def start(self,fixture):
        self.check()
        self.image_id=self.raw(['image','inspect',self.image,'--format','{{.Id}}']).decode().strip()
        self.raw(['volume','create',self.volume])
        # Setup runs trusted commands only; agent execution always uses unprivileged UID.
        self.raw(['run','--rm','-i',*self.flags(self.name+'-setup','0:0'),self.image,'sh','-c',
            'chmod 777 /workspace && tar --no-same-owner -xf - -C /workspace && chmod -R a+rwX /workspace'],input=archive_tree(fixture))
        self.check()
        self.raw(['run','-d',*self.flags(self.name),self.image,'sleep','infinity'])
    def command(self,args,container=None,user=None):
        self.check(); start=time.monotonic()
        command=[self.runtime,'exec']
        if user: command += ['--user',user]
        command += [container or self.name,*args]
        # Temporary files cap in-memory output; hard output limit aborts the trial.
        import tempfile
        with tempfile.TemporaryFile() as stdout, tempfile.TemporaryFile() as stderr:
            p=subprocess.Popen(command,stdout=stdout,stderr=stderr,start_new_session=True)
            try:
                while p.poll() is None:
                    self.check()
                    if stdout.tell()+stderr.tell()>2_000_000:
                        raise BoundaryError('Tool output exceeded 2 MB')
                    time.sleep(.05)
                stdout.seek(0); stderr.seek(0)
                return dict(exit_code=p.returncode,stdout=stdout.read(200_000).decode(errors='replace'),
                    stderr=stderr.read(200_000).decode(errors='replace'),seconds=time.monotonic()-start)
            except BaseException:
                p.terminate()
                try: p.wait(timeout=2)
                except subprocess.TimeoutExpired: p.kill(); p.wait()
                # Stop all descendants inside container, not only the exec client.
                subprocess.run([self.runtime,'kill',container or self.name],capture_output=True,timeout=15)
                raise
    def tool(self,name,args):
        if name=='shell': return self.command(['sh','-c',args['command']])
        if name=='finish': return dict(exit_code=0,stdout=args.get('message','Finished'),stderr='',seconds=0)
        script='''import json,pathlib,sys
x=json.loads(sys.argv[1]); p=(pathlib.Path('/workspace')/x['path']).resolve()
if not p.is_relative_to('/workspace') or p == pathlib.Path('/workspace'): raise ValueError('Path outside workspace')
if sys.argv[2]=='read_file': print(p.read_text()[:100000])
else:
 p.parent.mkdir(parents=True,exist_ok=True); p.write_text(x['content']); print('written')
'''
        if name not in ('read_file','write_file'): raise ValueError('Unknown tool')
        return self.command(['python','-c',script,json.dumps(args),name])
    def snapshot(self,output):
        # Keep tar as opaque bytes. Never extract untrusted symlinks on the host.
        with output.open('wb') as f:
            p=subprocess.run([self.runtime,'cp',self.name+':/workspace/.','-'],stdout=f,stderr=subprocess.PIPE,timeout=20)
        if p.returncode: raise BoundaryError('Could not preserve workspace artifacts')
        if output.stat().st_size>64_000_000: raise BoundaryError('Artifacts exceed 64 MB')
    def verify(self,verifier,command):
        self.raw(['rm','-f',self.name])
        self.check()
        # Private verifier volume is never attached to the agent container.
        v=self.volume+'-verifier'; self.raw(['volume','create',v])
        try:
            self.raw(['run','--rm','-i','--network','none','--cap-drop','ALL','--security-opt','no-new-privileges',
                '-v',v+':/verifier:rw',self.image,'sh','-c','tar --no-same-owner -xf - -C /verifier && chmod -R go-rwx /verifier'],
                input=archive_tree(verifier))
            # Verifier may drop UID for child code, but has no other capabilities.
            flags=self.flags(self.verifier_name,'0:0')
            self.raw(['run','-d',*flags,'--cap-add','SETUID','--cap-add','SETGID',
                '-v',v+':/verifier:ro',self.image,'sleep','infinity'])
            return self.command(command,container=self.verifier_name,user='0:0')
        finally:
            subprocess.run([self.runtime,'kill',self.verifier_name],capture_output=True,timeout=15)
            subprocess.run([self.runtime,'rm','-f',self.verifier_name],capture_output=True,timeout=15)
            subprocess.run([self.runtime,'volume','rm','-f',v],capture_output=True,timeout=15)
    def cleanup(self):
        errors=[]
        for name in (self.name,self.verifier_name,self.name+'-setup'):
            subprocess.run([self.runtime,'kill',name],capture_output=True,timeout=15)
            p=subprocess.run([self.runtime,'rm','-f',name],capture_output=True,timeout=15)
            if p.returncode and b'no such' not in p.stderr.lower() and b'does not exist' not in p.stderr.lower(): errors.append(p.stderr.decode())
        for name in (self.volume,self.volume+'-verifier'):
            p=subprocess.run([self.runtime,'volume','rm','-f',name],capture_output=True,timeout=15)
            if p.returncode and b'no such' not in p.stderr.lower() and b'not found' not in p.stderr.lower(): errors.append(p.stderr.decode())
        return errors
