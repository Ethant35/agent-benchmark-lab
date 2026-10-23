"""Offline, verifiable backups and payload-free support reports. Author: Ethan."""
from contextlib import contextmanager
import fcntl
import hashlib
import json
import os
from pathlib import Path
import shutil
import sqlite3
import tempfile

from . import __version__
from .store import Store, now


@contextmanager
def store_lock(root, *, exclusive=False):
    path=Path(root)/'activity.lock'
    with os.fdopen(os.open(path,os.O_CREAT|os.O_RDWR|os.O_NOFOLLOW,0o600),'a+') as handle:
        try: fcntl.flock(handle, (fcntl.LOCK_EX if exclusive else fcntl.LOCK_SH)|fcntl.LOCK_NB)
        except BlockingIOError as error:
            raise ValueError('Store is active; stop runs and retry') from error
        yield


def file_hash(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda:f.read(1024*1024),b''): h.update(chunk)
    return h.hexdigest()


def inventory(root):
    if root.is_symlink(): raise ValueError('Backup root must not be a symlink')
    files={}
    for path in sorted(root.rglob('*')):
        if path.is_symlink() or not (path.is_file() or path.is_dir()):
            raise ValueError('Backups require regular files; symlinks are not supported')
        if path.is_file() and path.relative_to(root).as_posix()!='backup.json':
            files[path.relative_to(root).as_posix()]=file_hash(path)
    return files


def new_destination(source, destination):
    destination=Path(destination).absolute()
    if destination.exists(): raise ValueError('Backup/restore destination already exists')
    if destination.is_relative_to(source.resolve()): raise ValueError('Destination must be outside the source store')
    destination.parent.mkdir(parents=True,exist_ok=True)
    return destination


def backup_store(source, destination):
    source=Path(source).resolve()
    if not (source/'results.sqlite3').is_file(): raise ValueError('Source result store does not exist')
    destination=new_destination(source,destination)
    store=Store(source)
    with store_lock(source,exclusive=True):
        # Legacy runners have no activity lock; refuse their active states too.
        if any(r['status'] in ('RUNNING','CANCELLING') for r in store.runs()):
            raise ValueError('Store has active runs; cancel/recover them before backup')
        staging=Path(tempfile.mkdtemp(prefix='.abl-backup-',dir=destination.parent))
        try:
            with store.connect() as src:
                if src.execute('PRAGMA integrity_check').fetchone()[0]!='ok':
                    raise ValueError('Source failed database integrity check')
                dst=sqlite3.connect(staging/'results.sqlite3')
                try: src.backup(dst)
                finally: dst.close()
            artifacts=source/'artifacts'
            if artifacts.exists():
                inventory(artifacts)
                shutil.copytree(artifacts,staging/'artifacts')
            for p in staging.rglob('*'): p.chmod(0o700 if p.is_dir() else 0o600)
            data={'schema_version':1,'author':'Ethan','created_at':now(),'app_version':__version__,'files':inventory(staging)}
            (staging/'backup.json').write_text(json.dumps(data,indent=2)); (staging/'backup.json').chmod(0o600)
            staging.rename(destination)
        finally:
            if staging.exists(): shutil.rmtree(staging)
    return {'backup':str(destination),'files':len(data['files'])}


def restore_store(source, destination):
    source=Path(source).resolve(); destination=new_destination(source,destination)
    manifest=json.loads((source/'backup.json').read_text())
    if manifest.get('schema_version')!=1 or manifest.get('files')!=inventory(source):
        raise ValueError('Backup checksum verification failed')
    staging=Path(tempfile.mkdtemp(prefix='.abl-restore-',dir=destination.parent))
    try:
        for name in manifest['files']:
            target=staging/name; target.parent.mkdir(parents=True,exist_ok=True,mode=0o700)
            shutil.copyfile(source/name,target); target.chmod(0o600)
        with Store(staging).connect() as db:
            if db.execute('PRAGMA integrity_check').fetchone()[0]!='ok':
                raise ValueError('Restored database failed integrity check')
        staging.rename(destination)
    finally:
        if staging.exists(): shutil.rmtree(staging)
    return {'restored':str(destination),'files':len(manifest['files'])}


def diagnostics(store):
    """Allow only fixed operational categories and scalar counts, never bodies."""
    from collections import Counter
    rows=store.trial_page(1)['total']
    with store.connect() as db:
        values=[json.loads(r[0]) for r in db.execute('SELECT data FROM trials')]
    allowed_status={'PASS','FAIL','TIMEOUT','ERROR','CANCELLED','INTERRUPTED','RUNNING','UNSUPPORTED','BLOCKED_EXTERNAL'}
    return {'author':'Ethan','app_version':__version__,'created_at':now(),'trials':rows,
            'statuses':dict(Counter(t.get('status') if t.get('status') in allowed_status else 'UNKNOWN' for t in values)),
            'unknown_cost_trials':sum(t.get('cost_usd') is None for t in values),
            'cleanup_failure_trials':sum(bool(t.get('cleanup_errors')) for t in values),
            'pending_request_trials':sum(bool(t.get('request_pending')) for t in values)}
