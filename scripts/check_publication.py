#!/usr/bin/env python3
"""Validate the complete published Git tree without printing matched values."""
import argparse
import gzip
import json
from pathlib import PurePosixPath
import re
import subprocess
import sys

# Build patterns from fragments to avoid literal sensitive strings
_p1, _p2 = 'p' + 'a', 'x'  # private hostname fragment
_m1, _m2 = 'm' + 'i', 'm' + 'as'  # private hostname fragment
_rpi = 'r' + 'p' + 'i'  # private institution fragment

RULES = {
    'private key': rb'-----BEGIN (?:OPENSSH |RSA |EC |DSA )?PRIVATE KEY-----',
    'GitHub token': rb'\b(?:gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{30,})\b',
    'cloud access key': rb'\b(?:AKIA|ASIA)[A-Z0-9]{16}\b',
    'service token': rb'\b(?:sk-(?:proj-|ant-)?[A-Za-z0-9_-]{20,}|xox[baprs]-[A-Za-z0-9-]{15,})\b',
    'literal credential': rb'''(?i)(?:api[_-]?key|access[_-]?token|auth[_-]?token|password|secret)\s*[=:]\s*["']([^"'\s]{12,})["']''',
    'authorization value': rb'(?i)\bBearer\s+[A-Za-z0-9_.-]{20,}',
    'private filesystem path': rb'/(?:home|Users|scratch|data|projects|mnt)/[A-Za-z0-9_.-]+/',
    'private network address': rb'\b(?:10\.[0-9]+\.[0-9]+\.[0-9]+|192\.168\.[0-9]+\.[0-9]+|172\.(?:1[6-9]|2[0-9]|3[01])\.[0-9]+\.[0-9]+|100\.(?:6[4-9]|[7-9][0-9]|1[01][0-9]|12[0-7])\.[0-9]+\.[0-9]+)\b|[A-Za-z0-9.-]+\.ts\.net',
    'private hostname': ('(?i)(?:^|[^a-z])(?:' + _p1 + _p2 + '|' + _m1 + _m2 + ')(?:[^a-z]|$)').encode(),
    'private git host': ('(?i)github\\.' + _rpi + '\\.edu').encode(),
    'ssh config': rb'(?i)(?:^|\n)\s*(?:Host|HostName|IdentityFile|ProxyCommand|RemoteCommand)\s+[^\n]+',
}

# File extensions to exclude from certain pattern checks
# Protein sequences contain AKIA-like substrings
PROTEIN_DATA_EXTENSIONS = {'.fasta', '.a3m', '.pdb', '.cif', '.csv'}

# Specific files excluded from credential/hostname checks by path
# These files legitimately contain test fixtures or detection patterns as string literals
FIXTURE_FILES = {
    'scripts/check_publication.py',  # Contains the patterns it checks for
    'scripts/test_check_publication.py',  # Contains fake credentials/paths as test data
}

CONTROL_FILES = {'publication-files.json', 'scripts/check_publication.py', '.github/workflows/publication.yml'}

def git(*arguments):
    return subprocess.check_output(['git', *arguments])

def inspect(body, filename=''):
    """Inspect content for sensitive patterns.
    
    Args:
        body: Content to inspect
        filename: Original filename, used for path-based and extension-based filtering
    
    Returns:
        List of matched rule names
    """
    import tempfile
    import os
    import zipfile
    import io
    
    file_ext = os.path.splitext(filename)[1].lower()
    exclude_protein_patterns = file_ext in PROTEIN_DATA_EXTENSIONS
    # Path-based exclusion for test fixtures only, not extension-based
    is_fixture_file = filename in FIXTURE_FILES
    
    if body.startswith(b'\x1f\x8b'):
        body = gzip.decompress(body)
    
    # Office Open XML documents (.docx, .xlsx, .pptx) are ZIP files containing XML
    if file_ext in {'.docx', '.xlsx', '.pptx', '.docm', '.xlsm', '.pptm'}:
        try:
            with zipfile.ZipFile(io.BytesIO(body)) as zf:
                for name in zf.namelist():
                    if name.endswith('.xml') or name.endswith('.xml.rels'):
                        try:
                            xml_content = zf.read(name)
                            # Recursively scan XML content
                            xml_filename = f'{filename}:{name}'
                            xml_labels = inspect(xml_content, filename=xml_filename)
                            if xml_labels:
                                raise SystemExit(f'{filename}: Office XML "{name}" contains sensitive data: {", ".join(sorted(set(xml_labels)))}')
                        except SystemExit:
                            raise  # Re-raise our own errors
                        except Exception as e:
                            # Unreadable XML is a hard failure
                            raise SystemExit(f'{filename}: Office XML "{name}" is unreadable: {e}')
        except SystemExit:
            raise  # Re-raise our own errors
        except Exception as e:
            # ZIP extraction failure is a hard error
            raise SystemExit(f'{filename}: Failed to extract Office XML: {e}')
    
    if body.startswith(b'%PDF'):
        # Extract visible text from PDF
        visible_text = subprocess.run(['pdftotext', '-layout', '-', '-'], input=body,
                                     stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                     check=True).stdout
        
        # Extract and check PDF attachments - failures are hard errors
        with tempfile.TemporaryDirectory() as tmpdir:
            # Save PDF to temp file for pdfdetach
            pdf_path = os.path.join(tmpdir, 'temp.pdf')
            with open(pdf_path, 'wb') as f:
                f.write(body)
            
            # List attachments - must succeed
            list_result = subprocess.run(['pdfdetach', '-list', pdf_path],
                                       capture_output=True, text=True, check=True)
            
            if 'embedded file' in list_result.stdout:
                # Extract all attachments - must succeed
                extract_result = subprocess.run(['pdfdetach', '-saveall', '-o', tmpdir, pdf_path],
                                              capture_output=True, text=True, check=True)
                
                # Read and recursively scan attachment contents
                for item in os.listdir(tmpdir):
                    item_path = os.path.join(tmpdir, item)
                    if os.path.isfile(item_path) and item != 'temp.pdf':
                        try:
                            with open(item_path, 'rb') as f:
                                attachment_content = f.read()
                        except Exception as e:
                            # Unreadable attachment is a hard failure
                            raise SystemExit(f'{filename}: PDF attachment "{item}" is unreadable: {e}')
                        
                        # Recursively scan attachment (handles nested PDFs, Office docs, etc.)
                        attachment_filename = f'{filename}:{item}'
                        attachment_labels = inspect(attachment_content, filename=attachment_filename)
                        if attachment_labels:
                            raise SystemExit(f'{filename}: PDF attachment "{item}" contains sensitive data: {", ".join(sorted(set(attachment_labels)))}')
        
        body = visible_text
    
    # Detect non-text binary content to avoid false positives from regex on compressed streams
    # Check for common binary image/video/audio signatures
    is_binary_content = (
        body.startswith(b'\x89PNG') or  # PNG
        body.startswith(b'\xff\xd8\xff') or  # JPEG
        body.startswith(b'GIF8') or  # GIF
        body.startswith(b'RIFF') or  # WAV, AVI, WebP
        body.startswith(b'\x00\x00\x00\x0cjP') or  # JPEG2000
        body.startswith(b'\x00\x00\x01\x00') or  # ICO
        body.startswith(b'BM') or  # BMP
        body.startswith(b'II*\x00') or  # TIFF little-endian
        body.startswith(b'MM\x00*') or  # TIFF big-endian
        body.startswith(b'\x1a\x45\xdf\xa3') or  # WebM/MKV
        body.startswith(b'ftyp')  # MP4/MOV (at offset 4, but checking start)
    )
    
    # Check main body
    labels = []
    for name, pattern in RULES.items():
        # Skip all credential/secret patterns ONLY for specific test fixture files by path
        # Other .py/.js/.sh files are fully scanned - hardcoded hostnames in scripts are dangerous
        if is_fixture_file and name in ('GitHub token', 'cloud access key', 
                                        'private filesystem path', 'private hostname',
                                        'private key', 'service token', 'literal credential',
                                        'authorization value', 'private git host', 'ssh config',
                                        'private network address'):
            continue
        # Skip AWS key pattern for protein data files (sequences contain AKIA-like substrings)
        if exclude_protein_patterns and name == 'cloud access key':
            continue
        # Skip hostname pattern for binary image/video/audio content (compressed data has random byte patterns)
        if is_binary_content and name == 'private hostname':
            continue
        if re.search(pattern, body):
            labels.append(name)
    
    return labels

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
            labels = inspect(git('cat-file', 'blob', oid.decode()), filename=name)
            labels += inspect(raw_name, filename=name)
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
