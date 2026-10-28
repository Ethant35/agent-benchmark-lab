#!/usr/bin/env python3
"""Build tracked working bytes without collecting unrelated local files. Author: Ethan."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True, help='new staging directory')
    parser.add_argument('--include', action='append', default=[], help='explicit new source file not yet tracked')
    args = parser.parse_args()
    repo = Path(__file__).resolve().parents[3]
    output = args.output.resolve()
    if output.exists():
        parser.error('Output must be new; existing evidence is never overwritten.')
    source = output / 'source'
    source.mkdir(parents=True, mode=0o700)
    tracked = subprocess.check_output(['git', 'ls-files', '-z'], cwd=repo).decode().split('\0')
    selected = {name for name in tracked if name}
    selected.update(args.include)
    selected.update(str(path.relative_to(repo)) for path in (repo / 'abl/static').rglob('*') if path.is_file())
    hashes = {}
    for name in sorted(selected):
        path = repo / name
        if not path.is_file() or path.is_symlink() or not path.resolve().is_relative_to(repo):
            raise ValueError(f'Expected a regular source file inside the repository: {name}')
        target = source / name
        if not target.resolve().is_relative_to(source):
            raise ValueError(f'Invalid staging path: {name}')
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, target)
        hashes[name] = hashlib.sha256(path.read_bytes()).hexdigest()
    (output / 'source-manifest.json').write_text(json.dumps({'author': 'Ethan', 'files': hashes}, indent=2) + '\n')
    subprocess.run(['uv', 'build', '--sdist', '--wheel', '--out-dir', str(output / 'dist')], cwd=source, check=True)


if __name__ == '__main__':
    main()
