"""Fail-closed container execution; no agent-controlled host shell commands."""
import io
import json
import os
import selectors
import signal
import hashlib
from pathlib import Path
import shutil
import subprocess
import tarfile
import time

class BoundaryError(RuntimeError): pass
class TrialTimeout(RuntimeError): pass
class TrialCancelled(RuntimeError): pass
class OutputLimit(BoundaryError): pass
class ArtifactLimit(BoundaryError): pass

OUTPUT_LIMIT = 2_000_000
RETAIN_LIMIT = 200_000
ARTIFACT_LIMIT = 64_000_000


def runtime_name(preferred='auto'):
    for name in (['podman','docker'] if preferred=='auto' else [preferred]):
        if shutil.which(name):
            try:
                p=subprocess.run([name,'info'],capture_output=True,timeout=15)
                if p.returncode==0: return name
            except subprocess.TimeoutExpired: pass
    raise BoundaryError('No working Docker or Podman engine. Install/start one; host execution is forbidden.')


def archive_tree(path, prefix=''):
    class BoundedBuffer(io.BytesIO):
        def write(self, data):
            if self.tell()+len(data)>ARTIFACT_LIMIT:
                raise BoundaryError('Trusted input archive exceeds 64,000,000 byte limit')
            return super().write(data)
    out=BoundedBuffer()
    with tarfile.open(fileobj=out,mode='w') as tar:
        for p in sorted(Path(path).rglob('*')):
            if '__pycache__' in p.parts or p.suffix=='.pyc': continue
            if p.is_symlink(): raise BoundaryError('Fixture symlinks are forbidden')
            if not (p.is_file() or p.is_dir()):
                raise BoundaryError('Trusted inputs must be regular files or directories')
            if p.is_file() and p.stat().st_size>ARTIFACT_LIMIT:
                raise BoundaryError('Trusted input exceeds archive byte limit')
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
        self.keeper_name=self.name+'-keeper'
        self.deadline=deadline; self.cancelled=cancelled; self.image_id=None; self.artifact=None
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
        self.raw(['volume','create','--label','abl.managed=true',
            '--opt','type=tmpfs','--opt','device=tmpfs',
            '--opt','o=size=128m,nr_inodes=16384,nodev,nosuid,mode=0777',self.volume])
        # A live owner keeps tmpfs mounted after agent shutdown, through snapshot
        # and verification. It has a separate PID namespace and no agent commands.
        self.raw(['run','-d',*self.flags(self.keeper_name,'0:0'),self.image,'sleep','infinity'])
        # Setup runs trusted commands only; agent execution always uses unprivileged UID.
        self.raw(['run','--rm','-i',*self.flags(self.name+'-setup','0:0'),self.image,'sh','-c',
            'tar --no-same-owner -xf - -C /workspace && find /workspace -mindepth 1 -exec chmod a+rwX {} +'],input=archive_tree(fixture))
        self.check()
        self.raw(['run','-d',*self.flags(self.name),self.image,'sleep','infinity'])
    @staticmethod
    def terminate_client(process):
        # The CLI's process group belongs to this call; never signal the caller.
        # Children can still hold pipes after their parent has already exited.
        def signal_group(sig):
            try: os.killpg(process.pid, sig)
            except ProcessLookupError: pass
            except PermissionError:
                # Darwin may retain a zombie-only process group briefly after
                # SIGTERM. Confirm that it has no live member before accepting
                # EPERM; a real permission failure must remain visible.
                states=subprocess.run(['ps','-axo','pgid=,stat='],capture_output=True,text=True,check=True,timeout=2)
                for line in states.stdout.splitlines():
                    fields=line.split()
                    if len(fields)==2 and fields[0]==str(process.pid) and not fields[1].startswith('Z'):
                        raise
        signal_group(signal.SIGTERM)
        try: process.wait(timeout=1)
        except subprocess.TimeoutExpired: pass
        signal_group(signal.SIGKILL)
        process.wait(timeout=2)

    def collect(self, args, *, sink=None, deadline=None):
        """Drain both pipes through EOF, including bytes buffered after fast exit.

        Only a bounded prefix stays in RAM. A binary sink never receives bytes
        above ARTIFACT_LIMIT. Observed byte counts are lower bounds on abort.
        """
        started=time.monotonic()
        counts={'stdout':0,'stderr':0}; retained={'stdout':bytearray(),'stderr':bytearray()}
        written=0; digest=hashlib.sha256(); limit_exceeded=False; complete=False
        p=subprocess.Popen([self.runtime,*args],stdout=subprocess.PIPE,stderr=subprocess.PIPE,
            stdin=subprocess.DEVNULL,start_new_session=True,bufsize=0)
        def result():
            return dict(exit_code=p.returncode,stdout=retained['stdout'].decode(errors='replace'),
                stderr=retained['stderr'].decode(errors='replace'),seconds=time.monotonic()-started,
                stdout_bytes=counts['stdout'],stderr_bytes=counts['stderr'],
                stdout_retained_bytes=len(retained['stdout']),stderr_retained_bytes=len(retained['stderr']),
                stdout_truncated=counts['stdout']>len(retained['stdout']),
                stderr_truncated=counts['stderr']>len(retained['stderr']),
                output_complete=complete,limit_exceeded=limit_exceeded,
                byte_count_source='host pipe bytes observed; lower bound when output_complete=false',
                bytes_written=written,sha256=digest.hexdigest() if complete and sink is not None else None)
        try:
            with selectors.DefaultSelector() as selector:
                for name,pipe in [('stdout',p.stdout),('stderr',p.stderr)]:
                    os.set_blocking(pipe.fileno(),False)
                    selector.register(pipe,selectors.EVENT_READ,name)
                while selector.get_map():
                    self.check()
                    if deadline is not None and time.monotonic()>deadline:
                        raise TrialTimeout('Artifact collection deadline exceeded')
                    for key,_ in selector.select(timeout=.05):
                        name=key.data
                        if sink is not None and name=='stdout':
                            allowance=ARTIFACT_LIMIT-counts['stdout']+1
                        elif sink is not None:
                            allowance=OUTPUT_LIMIT-counts['stderr']+1
                        else:
                            allowance=OUTPUT_LIMIT-sum(counts.values())+1
                        try: chunk=os.read(key.fd,min(65536,max(1,allowance)))
                        except BlockingIOError: continue
                        if not chunk:
                            selector.unregister(key.fileobj); key.fileobj.close(); continue
                        counts[name]+=len(chunk)
                        if sink is not None and name=='stdout':
                            accepted=chunk[:max(0,ARTIFACT_LIMIT-written)]
                            sink.write(accepted); digest.update(accepted); written+=len(accepted)
                            if counts['stdout']>ARTIFACT_LIMIT:
                                limit_exceeded=True
                                raise ArtifactLimit('Artifact stream exceeded 64,000,000 bytes')
                        else:
                            retained[name].extend(chunk[:max(0,RETAIN_LIMIT-len(retained[name]))])
                            used=counts['stderr'] if sink is not None else sum(counts.values())
                            if used>OUTPUT_LIMIT:
                                limit_exceeded=True
                                raise OutputLimit('Combined tool output exceeded 2,000,000 bytes')
                # A child can close its pipes while it keeps running.
                while p.poll() is None:
                    self.check()
                    if deadline is not None and time.monotonic()>deadline:
                        raise TrialTimeout('Artifact collection deadline exceeded')
                    time.sleep(.05)
            complete=True
            return result()
        except BaseException as error:
            self.terminate_client(p)
            error.result=result()
            raise
        finally:
            self.terminate_client(p)
            for pipe in (p.stdout,p.stderr):
                if not pipe.closed: pipe.close()

    def command(self,args,container=None,user=None):
        self.check()
        command=['exec']
        if user: command += ['--user',user]
        command += [container or self.name,*args]
        try:
            return self.collect(command)
        except BaseException:
            # Terminating the client alone does not terminate container work.
            try: subprocess.run([self.runtime,'kill',container or self.name],capture_output=True,timeout=15)
            except (OSError,subprocess.TimeoutExpired): pass
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
        # Never extract untrusted paths. Publish only complete, bounded archives.
        partial=output.with_suffix(output.suffix+'.partial')
        self.artifact={'status':'collecting','bytes_written':0,'limit_bytes':ARTIFACT_LIMIT,
            'source':'host-observed container tar stream'}
        try:
            self.check()
            with partial.open('xb') as f:
                result=self.collect(['cp',self.name+':/workspace/.','-'],sink=f,
                    deadline=min(self.deadline,time.monotonic()+20))
            if result['exit_code']:
                error=BoundaryError('Could not preserve workspace artifacts')
                error.result=result; raise error
            os.replace(partial,output)
            self.artifact.update(status='complete',bytes_written=result['bytes_written'],
                bytes_observed=result['stdout_bytes'],sha256=result['sha256'])
            return self.artifact
        except BaseException as error:
            result=getattr(error,'result',{})
            state='limit_exceeded' if isinstance(error,(ArtifactLimit,OutputLimit)) else (
                'cancelled' if isinstance(error,TrialCancelled) else 'timeout' if isinstance(error,TrialTimeout) else 'interrupted' if isinstance(error,(KeyboardInterrupt,SystemExit)) else 'error')
            self.artifact.update(status=state,bytes_written=result.get('bytes_written',0),
                bytes_observed=result.get('stdout_bytes',0),detail=str(error))
            partial.unlink(missing_ok=True)
            raise
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
        for name in (self.name,self.verifier_name,self.name+'-setup',self.keeper_name):
            try:
                subprocess.run([self.runtime,'kill',name],capture_output=True,timeout=15)
                p=subprocess.run([self.runtime,'rm','-f',name],capture_output=True,timeout=15)
                if p.returncode and b'no such' not in p.stderr.lower() and b'does not exist' not in p.stderr.lower(): errors.append(p.stderr.decode())
            except (OSError,subprocess.TimeoutExpired) as error:
                errors.append(f'Could not remove {name}: {error}')
        for name in (self.volume,self.volume+'-verifier'):
            try:
                p=subprocess.run([self.runtime,'volume','rm','-f',name],capture_output=True,timeout=15)
                if p.returncode and b'no such' not in p.stderr.lower() and b'not found' not in p.stderr.lower(): errors.append(p.stderr.decode())
            except (OSError,subprocess.TimeoutExpired) as error:
                errors.append(f'Could not remove {name}: {error}')
        return errors
