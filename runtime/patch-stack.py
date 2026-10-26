#!/usr/bin/env python3
"""Apply/check an ordered stack, including patches sharing source context."""
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile


def manage(mode, source, patches):
    source = Path(source).resolve()
    patches = [Path(p).resolve() for p in patches]
    if mode not in ('prepare', 'check') or not patches:
        raise RuntimeError('Expected prepare/check and a non-empty patch stack.')
    # Stage only patch-owned source paths into a disposable index. The real
    # index and unrelated user files are never staged or reset.
    paths = set()
    for patch in patches:
        for line in patch.read_text().splitlines():
            if line.startswith(('+++ b/', '--- a/')):
                paths.add(line[6:])
    def git(*args, env=None):
        return subprocess.run(['git', '-C', str(source), *args], env=env,
                              text=True, capture_output=True)
    with tempfile.TemporaryDirectory(prefix='lilac-patch-check-') as temp:
        snapshot = Path(temp) / 'snapshot'
        index = Path(temp) / 'index'
        env = {**os.environ, 'GIT_INDEX_FILE': str(snapshot)}
        result = git('read-tree', 'HEAD', env=env)
        if result.returncode:
            raise RuntimeError(result.stderr.strip())
        existing = [p for p in sorted(paths) if (source / p).exists() or
                    git('ls-files', '--error-unmatch', '--', p).returncode == 0]
        if existing:
            result = git('add', '-A', '--', *existing, env=env)
            if result.returncode:
                raise RuntimeError(result.stderr.strip())
        trial_env = {**os.environ, 'GIT_INDEX_FILE': str(index)}
        # Undo each candidate in reverse order in the disposable index. Earlier
        # patches need their original context restored before recognition.
        applied = 0
        for count in range(len(patches), -1, -1):
            shutil.copyfile(snapshot, index)
            if all(git('apply', '--cached', '--reverse', str(p), env=trial_env).returncode == 0
                   for p in reversed(patches[:count])):
                applied = count
                break
        if mode == 'check':
            if applied != len(patches):
                raise RuntimeError('Patch stack is incomplete or conflicts with local edits. Run bash runtime/prepare.sh.')
            print(f'All {len(patches)} runtime patches verified.')
            return
        # Preflight the entire remaining sequence before changing source files.
        shutil.copyfile(snapshot, index)
        for patch in patches[applied:]:
            result = git('apply', '--cached', str(patch), env=trial_env)
            if result.returncode:
                raise RuntimeError(f'{patch.name} conflicts; source files were not changed.\n{result.stderr.strip()}')
        for patch in patches[applied:]:
            result = git('apply', str(patch))
            if result.returncode:
                raise RuntimeError(f'{patch.name}: {result.stderr.strip()}')
            print(f'Applied: {patch.name}')
        if applied == len(patches):
            print('Runtime source patches are already current.')


if __name__ == '__main__':
    try:
        if len(sys.argv) != 3:
            raise RuntimeError('Usage: patch-stack.py prepare|check SOURCE_DIR')
        manage(sys.argv[1], sys.argv[2], sorted((Path(__file__).parent / 'patches').glob('*.patch')))
    except (RuntimeError, OSError) as error:
        print(error, file=sys.stderr)
        sys.exit(2)
