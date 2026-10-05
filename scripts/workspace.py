#!/usr/bin/env python3
"""Project front door to the pinned shared workflow implementation."""
import json
import os
from pathlib import Path
import runpy
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
home=os.environ.get('WORKFLOWS_HOME') or private.get('workflow_home')
if not home:raise SystemExit('Set WORKFLOWS_HOME or configure ignored local/fleet.json.')
script=Path(home).expanduser()/'scripts/workflow.py'
if not script.is_file():raise SystemExit('Shared workflow unavailable at configured location.')
os.environ['PROJECT_ROOT']=str(project)
sys.path.insert(0,str(script.parent))
runpy.run_path(str(script),run_name='__main__')
