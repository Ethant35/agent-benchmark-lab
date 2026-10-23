"""Real host subprocess and trusted input boundary regression tests. Author: Ethan."""
import io
import os
from pathlib import Path
import signal
import subprocess
import sys
import time

import pytest
from abl.isolation import Sandbox, BoundaryError, archive_tree


def test_exited_client_does_not_leave_its_process_group(tmp_path):
    marker = tmp_path/'child'
    script = "import subprocess,sys; p=subprocess.Popen([sys.executable,'-c','import time; time.sleep(60)']); open(sys.argv[1],'w').write(str(p.pid))"
    parent = subprocess.Popen([sys.executable,'-c',script,str(marker)], start_new_session=True)
    parent.wait(timeout=5)
    child = int(marker.read_text())
    try:
        Sandbox.terminate_client(parent)
        deadline=time.monotonic()+3
        while time.monotonic()<deadline:
            state=subprocess.run(['ps','-o','stat=','-p',str(child)],capture_output=True,text=True).stdout.strip()
            if not state or state.startswith('Z'): break
            time.sleep(.02)
        assert not state or state.startswith('Z'), 'Child still alive after client exit'
    finally:
        try: os.killpg(parent.pid,signal.SIGKILL)
        except ProcessLookupError: pass


def test_archive_rejects_special_files_and_oversized_inputs(tmp_path):
    fifo=tmp_path/'pipe'; os.mkfifo(fifo)
    with pytest.raises(BoundaryError,match='regular'):
        archive_tree(tmp_path)
    fifo.unlink()
    with (tmp_path/'large').open('wb') as f: f.truncate(64_000_001)
    with pytest.raises(BoundaryError,match='limit'):
        archive_tree(tmp_path)
