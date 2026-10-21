"""Read-only evidence report: never rewrites the campus or old exported artifacts."""
import csv
import hashlib
import io
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    summaries = []
    paths = [ROOT/'artifacts/portfolio25-grid.json', ROOT/'backend/data/campus.json',
             ROOT/'backend/data/campus.result.json', ROOT/'docs/sample-campus.json']
    for path in paths:
        if not path.exists():
            continue
        raw = path.read_bytes()
        value = json.loads(raw.decode('utf-8-sig'))
        campus = value.get('campus', value)
        baseline = value.get('baseline', {})
        summaries.append({'path':str(path.relative_to(ROOT)), 'sha256':hashlib.sha256(raw).hexdigest(),
            'schema_version':campus.get('schema_version'), 'revision':campus.get('revision',value.get('input_revision')),
            'name_0':campus.get('buildings',[{}])[0].get('name'), 'scenario':campus.get('scenario'),
            'electric_peak_sum_kw':baseline.get('electric_peak_sum_kw'),
            'electric_peak_kw':baseline.get('electric_peak_kw'),
            'after_present':value.get('after') is not None,
            'investment_plan_present':value.get('investment_plan') is not None,
            'selected_package_count':len(value.get('selected_packages',[]) or []),
            'optimization_status':campus.get('optimization_status'),
            'status':value.get('status')})
    csv_path = ROOT/'artifacts/portfolio25-grid.csv'
    if csv_path.exists():
        rows=list(csv.DictReader(io.StringIO(csv_path.read_text(encoding='utf-8-sig'))))
        summaries.append({'path':str(csv_path.relative_to(ROOT)), 'row_count':len(rows), 'first_row':rows[0] if rows else None})
    out=ROOT/'artifacts/delivery'
    out.mkdir(exist_ok=True)
    (out/'data-audit.json').write_text(json.dumps(summaries,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(summaries,ensure_ascii=True,indent=2))


if __name__=='__main__':
    main()
