#!/usr/bin/env python3
"""Merge upstream into main, publish the fork, and refresh built-in copies."""

import argparse
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import jdthomas24_sync_builtin as builtin


SOURCE = Path(__file__).resolve().parent


def run(*args: str, cwd: Path = SOURCE) -> str:
    """Run a command in cwd and return its stripped standard output."""
    print('+ ' + ' '.join(map(str, args)), flush=True)
    result = subprocess.run(args, cwd=cwd, text=True, stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT)
    if result.stdout:
        print(result.stdout, end='' if result.stdout.endswith('\n') else '\n')
    if result.returncode:
        raise RuntimeError(f'Command failed ({result.returncode}); stopping. See output above.')
    return result.stdout.strip()


def main() -> int:
    """Execute the update workflow and return zero only after verification."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--target', type=Path, default=builtin.DEFAULT_TARGET,
                        help='driversAndApps checkout')
    parser.add_argument('--classpath', default=os.environ.get('CLASSPATH'),
                        help='Hubitat compiler classpath (default: CLASSPATH or sibling backend build)')
    args = parser.parse_args()
    classpath = args.classpath
    if not classpath:
        candidates = list(SOURCE.parent.parent.glob('hub_*/build/classes/groovy/main'))
        if len(candidates) == 1:
            classpath = str(candidates[0])
    if not classpath:
        parser.error('Set --classpath or CLASSPATH to the Hubitat backend build classes.')
    compiler = ['groovyc'] + (['-cp', classpath] if classpath else [])
    target = args.target.resolve()
    try:
        # Refuse to merge over tracked work or an unfinished Git operation.
        run('git', 'rev-parse', '--show-toplevel')
        if run('git', 'status', '--porcelain', '--untracked-files=no'):
            raise RuntimeError('Source repository has tracked changes. Commit or stash them first.')
        for name in ('MERGE_HEAD', 'CHERRY_PICK_HEAD', 'REVERT_HEAD', 'rebase-merge', 'rebase-apply'):
            path = Path(run('git', 'rev-parse', '--git-path', name))
            if not path.is_absolute():
                path = SOURCE / path
            if path.exists():
                raise RuntimeError(f'Finish the existing Git operation first: {name}')
        if not shutil.which('groovyc'):
            raise RuntimeError('groovyc is required to verify each Groovy file before publishing.')
        if not (target / 'apps/src').is_dir() or not (target / 'devicetypes/src').is_dir():
            raise RuntimeError(f'Not a driversAndApps source tree: {target}')
        outputs = builtin.destinations(target)
        # Only generated destinations must be clean; unrelated target work is allowed.
        for output in outputs.values():
            if output.exists() and not output.read_text().startswith(builtin.HEADER):
                raise RuntimeError(f'Refusing unmanaged destination: {output}')
            if run('git', 'status', '--porcelain', '--', str(output), cwd=target):
                raise RuntimeError(f'Destination has local changes: {output}. Commit them before updating.')

        # Fetch both histories, then use normal merges so local commits are preserved.
        run('git', 'fetch', 'origin')
        run('git', 'fetch', 'upstream')
        run('git', 'switch', 'main')
        for ref in ('origin/main', 'upstream/main'):
            run('git', 'merge', '--no-edit', ref)

        # Compile each original and transformed file separately before publishing.
        with tempfile.TemporaryDirectory(prefix='reolink-verify-') as temp:
            stage = Path(temp)
            for filename in outputs:
                run(*compiler, '-d', str(stage / 'original' / filename), str(SOURCE / filename))
                generated = stage / filename
                generated.write_text(builtin.generated_source(filename), encoding='utf-8')
                run(*compiler, '-d', str(stage / 'builtin' / filename), str(generated))

        run('git', 'push', 'origin', 'main:main')
        run(sys.executable, str(SOURCE / 'jdthomas24_sync_builtin.py'), '--target', str(target))
        run(sys.executable, str(SOURCE / 'jdthomas24_sync_builtin.py'), '--target', str(target), '--check')
        print('Updated origin/main and verified built-in copies. Target changes remain uncommitted.')
        return 0
    except (RuntimeError, OSError, ValueError) as error:
        print(f'Update stopped: {error}', file=sys.stderr)
        print('No reset or force-push was performed. Resolve the reported issue before rerunning.', file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
