#!/usr/bin/env python3
"""Project front door to the pinned shared workflow implementation."""
import json
import hashlib
import os
from pathlib import Path
import runpy
import subprocess
import sys

project=Path(__file__).resolve().parent.parent
config=project/'local/fleet.json'
private=json.loads(config.read_text()) if config.is_file() else {}
# The private binding selects a runtime without changing shell activation.
selected=private.get('control_python')
if selected:
    interpreter=Path(selected).expanduser()
    if not interpreter.is_absolute() or not interpreter.is_file() or not os.access(interpreter,os.X_OK):
        raise SystemExit('Configured control interpreter is unavailable; inspect Fleet environment binding.')
    if Path(sys.executable).resolve()!=interpreter.resolve() or not sys.flags.isolated:
        os.execv(str(interpreter),[str(interpreter),'-I','-B',str(Path(__file__).resolve()),*sys.argv[1:]])
source_relative=Path('external/research-workflows')
submodule=project/source_relative
gitmodules=project/'.gitmodules'
adopted=False
if gitmodules.is_file():
    try:
        import configparser
        config=configparser.ConfigParser(interpolation=None)
        config.read(gitmodules)
        adopted=any(config.get(section,'path',fallback=None)==source_relative.as_posix()
                    for section in config.sections())
    except configparser.Error as error:
        raise SystemExit(f'Cannot read .gitmodules; repair it before using the shared workflow: {error}')

if adopted:
    pin_path=project/'workflow.lock.json'
    if not pin_path.is_file():raise SystemExit('Adopted workflow submodule requires workflow.lock.json.')
    try:
        pin=json.loads(pin_path.read_text())['workflow']
        expected=pin['commit']; hashes=pin['files_sha256']
    except (KeyError,TypeError,json.JSONDecodeError) as error:
        raise SystemExit(f'Invalid workflow.lock.json workflow pin: {error}')
    if not isinstance(expected,str) or len(expected)!=40 or any(c not in '0123456789abcdef' for c in expected):
        raise SystemExit('workflow.lock.json must pin a full 40-character workflow commit.')
    if pin.get('repository_id')!='research-workflows':
        raise SystemExit('workflow.lock.json must identify repository_id as research-workflows.')
    script=submodule/'scripts/workflow.py'
    if submodule.is_symlink() or not script.is_file():
        raise SystemExit('Pinned workflow submodule is missing; run `git submodule update --init -- external/research-workflows`.')
    try:
        actual=subprocess.run(['git','-C',str(submodule),'rev-parse','--verify','HEAD^{commit}'],
                              check=True,capture_output=True,text=True).stdout.strip()
    except (OSError,subprocess.CalledProcessError):
        raise SystemExit('Cannot read the workflow submodule commit; initialize or repair external/research-workflows.')
    if actual!=expected:
        raise SystemExit(f'Workflow submodule is at {actual}, but workflow.lock.json pins {expected}; checkout the pinned commit or deliberately update the project pin.')
    if not isinstance(hashes,dict) or not hashes:
        raise SystemExit('workflow.lock.json has no shared workflow file hashes.')
    for name,digest in hashes.items():
        relative=Path(name)
        path=submodule/relative
        cursor=submodule
        unsafe=relative.is_absolute() or '..' in relative.parts
        for part in relative.parts:
            cursor=cursor/part
            unsafe=unsafe or cursor.is_symlink()
        if (unsafe or not path.is_file() or not isinstance(digest,str)
                or len(digest)!=64 or any(c not in '0123456789abcdef' for c in digest)
                or hashlib.sha256(path.read_bytes()).hexdigest()!=digest):
            raise SystemExit(f'Pinned workflow file changed or is missing: {name}; restore the pinned submodule or deliberately update the project pin.')
    effective={'repository_id':pin.get('repository_id'),'commit':actual,
               'source':source_relative.as_posix(),'files_verified':len(hashes)}
elif sys.argv[1:]==['pin']:
    effective=None
else:
    home=os.environ.get('WORKFLOWS_HOME') or private.get('workflow_home')
    if not home:raise SystemExit('Set WORKFLOWS_HOME or configure ignored local/fleet.json for this unadopted project.')
    script=Path(home).expanduser()/'scripts/workflow.py'
    if not script.is_file():raise SystemExit('Shared workflow unavailable at configured location.')
    effective={'repository_id':'research-workflows','commit':None,'source':str(Path(home).expanduser()),
               'files_verified':0}

if sys.argv[1:]==['pin']:
    if effective is None:
        raise SystemExit('No pinned research-workflows submodule is configured for this project.')
    print(json.dumps(effective,indent=2))
    raise SystemExit(0)
os.environ['PROJECT_ROOT']=str(project)
sys.path.insert(0,str(script.parent))
runpy.run_path(str(script),run_name='__main__')
