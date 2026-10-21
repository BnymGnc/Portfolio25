"""Runs an isolated API on 8001, copying inputs into a NEW temporary QA directory.

Never assigns the main application's DATA_FILE or writes user input files.
"""
import sys
import tempfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'backend'))
import main
import uvicorn

if __name__=='__main__':
    directory=Path(tempfile.mkdtemp(prefix='qa-',dir=ROOT/'artifacts'))
    for name in ('campus.json','campus.result.json'):
        source=ROOT/'artifacts/delivery/before'/name
        if source.exists():
            with (directory/name).open('xb') as target:
                target.write(source.read_bytes())
    main.DATA_FILE=directory/'campus.json'
    print(f'Isolated QA data: {directory}',flush=True)
    uvicorn.run(main.app,host='127.0.0.1',port=8001)
