#!/usr/bin/env python3
"""Validate the complete published Git tree without printing matched values."""
import argparse
import gzip
import json
from pathlib import PurePosixPath
import re
import subprocess
import sys

RULES = {
    'private key': rb'-----BEGIN (?:OPENSSH |RSA |EC |DSA )?PRIVATE KEY-----',
    'GitHub token': rb'\b(?:gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{30,})\b',
    'cloud access key': rb'\b(?:AKIA|ASIA)[A-Z0-9]{16}\b',
    'service token': rb'\b(?:sk-(?:proj-|ant-)?[A-Za-z0-9_-]{20,}|xox[baprs]-[A-Za-z0-9-]{15,})\b',
    'literal credential': rb'''(?i)(?:api[_-]?key|access[_-]?token|auth[_-]?token|password|secret)\s*[=:]\s*["']([^"'\s]{12,})["']''',
    'authorization value': rb'(?i)\bBearer\s+[A-Za-z0-9_.-]{20,}',
    'private filesystem path': rb'/(?:home|Users|scratch|data|projects|mnt)/[A-Za-z0-9_.-]+/',
    'private network address': rb'\b(?:10\.[0-9]+\.[0-9]+\.[0-9]+|192\.168\.[0-9]+\.[0-9]+|172\.(?:1[6-9]|2[0-9]|3[01])\.[0-9]+\.[0-9]+|100\.(?:6[4-9]|[7-9][0-9]|1[01][0-9]|12[0-7])\.[0-9]+\.[0-9]+)\b|[A-Za-z0-9.-]+\.ts\.net',
}
CONTROL_FILES = {'publication-files.json', 'scripts/check_publication.py', '.github/workflows/publication.yml'}

def git(*arguments):
    return subprocess.check_output(['git', *arguments])

def inspect(body):
    if body.startswith(b'\x1f\x8b'):
        body = gzip.decompress(body)
    if body.startswith(b'%PDF'):
        body = subprocess.run(['pdftotext', '-layout', '-', '-'], input=body,
                              stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                              check=True).stdout
    return [name for name, pattern in RULES.items() if re.search(pattern, body)]

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--ref', default='HEAD', help='Complete commit/tree to inspect')
    args = parser.parse_args()
    ref = git('rev-parse', '--verify', args.ref + '^{tree}').decode().strip()
    manifest = json.loads(git('show', ref + ':publication-files.json'))
    allowed = set(manifest['files'])
    if len(allowed) != len(manifest['files']) or not CONTROL_FILES <= allowed:
        raise SystemExit('Publication manifest is incomplete or contains duplicate paths.')
    failures = []
    seen = set()
    for entry in git('ls-tree', '-rz', ref).split(b'\0'):
        if not entry:
            continue
        metadata, raw_name = entry.split(b'\t', 1)
        mode, kind, oid = metadata.split()
        name = raw_name.decode()
        seen.add(name)
        if name not in allowed or mode not in (b'100644', b'100755') or kind != b'blob':
            failures.append((name, ['unapproved file or file type']))
            continue
        if any(part in {'local', 'drafts', 'reference', 'continuation', 'campaigns', '.ssh', '.aws'}
               or part.startswith('.env') for part in PurePosixPath(name).parts):
            failures.append((name, ['operational or private file']))
            continue
        try:
            labels = inspect(git('cat-file', 'blob', oid.decode()))
            labels += inspect(raw_name)
        except (OSError, ValueError, subprocess.CalledProcessError):
            labels = ['content could not be inspected']
        if labels:
            failures.append((name, sorted(set(labels))))
    for name in sorted(allowed - seen):
        failures.append((name, ['manifest file missing']))
    for name, labels in failures:
        print(name + ': ' + ', '.join(labels), file=sys.stderr)
    if failures:
        return 1
    print(f'Publication check passed: {len(seen)} reviewed files.')
    return 0

if __name__ == '__main__':
    sys.exit(main())
