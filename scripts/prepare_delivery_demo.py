"""Compute two scenarios through the real API in an isolated temporary workspace.

Reads saved user inputs, never writes to the live DATA_FILE or its result file.
Run with .venv/Scripts/python.exe from the repository root.
"""
import hashlib
import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'backend'))
import main
from fastapi.testclient import TestClient


def run():
    source = main.DATA_FILE
    original_bytes = source.read_bytes()
    source_hash = hashlib.sha256(original_bytes).hexdigest()
    destination = ROOT / 'artifacts/delivery/scenarios'
    destination.mkdir(parents=True, exist_ok=True)
    manifest = {'source_input_sha256': source_hash, 'isolation': 'Temporary DATA_FILE; live inputs unchanged', 'scenarios': []}
    try:
        with tempfile.TemporaryDirectory() as directory:
            main.DATA_FILE = Path(directory) / 'campus.json'
            with TestClient(main.app) as client:
                for label, mode, patch in [
                    ('scenario-a', 'A', {}),
                    ('scenario-b', 'B', {'budget_try': 8_000_000, 'electric_capacity_kw': 1_000, 'savings_target_pct': 25}),
                ]:
                    main.DATA_FILE.write_bytes(original_bytes)
                    main.result_path().unlink(missing_ok=True)
                    snapshot = client.get('/api/campus/snapshot').json()
                    if patch:
                        campus = snapshot['campus']
                        update = {'revision': campus['revision'], 'buildings': campus['buildings'],
                                  'scenario': {**campus['scenario'], **patch}}
                        saved = client.put('/api/campus', json=update)
                        saved.raise_for_status()
                        snapshot = saved.json()
                    revision = snapshot['campus']['revision']
                    calculated = client.post('/api/calculate', json={'revision': revision, 'mode': mode, 'time_limit_s': 10})
                    calculated.raise_for_status()
                    snapshot = client.get('/api/campus/snapshot').json()
                    result = snapshot['calculation']
                    for scope in ('inputs', 'result'):
                        for extension in ('json', 'csv'):
                            params = {'scope': scope, 'revision': revision}
                            if scope == 'result':
                                params['expected_calculation_id'] = snapshot['calculation_id']
                            exported = client.get('/api/export/' + extension, params=params)
                            exported.raise_for_status()
                            (destination / f'{label}-{scope}.{extension}').write_bytes(exported.content)
                    manifest['scenarios'].append({
                        'name': label, 'mode': mode, 'revision': revision, 'scenario': snapshot['campus']['scenario'],
                        'calculation_id': snapshot['calculation_id'], 'status': result['status'], 'solver': result['solver'],
                        'investment_try': result['investment_try'], 'energy_savings_kwh_year': result['energy_savings_kwh_year'],
                        'energy_savings_pct': result['energy_savings_pct'], 'net_savings_try_year': result['net_savings_try_year'],
                        'target_met': result['target_met'], 'before': result['baseline'], 'after': result['after'],
                        'packages': {p['building_id']: p['package'] for p in result['selected_packages']},
                    })
    finally:
        main.DATA_FILE = source
    assert source.read_bytes() == original_bytes, 'Live inputs changed'
    (destination / 'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(manifest, ensure_ascii=True, indent=2))


if __name__ == '__main__':
    run()
