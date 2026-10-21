"""Explicit local administrator import; never assigns legacy data on registration."""
import argparse,sys,hashlib
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'backend'))
import main
from models import Campus
from auth import user_context
from profiles import generate_profiles
from interventions import candidates

if __name__=='__main__':
    if main.get_store() is not None:
        raise SystemExit('This legacy tool is SQLite-only. For PostgreSQL use backend/import_postgres.py with an explicit private backup.')
    p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);p.add_argument('--email',required=True);p.add_argument('--apply',action='store_true');args=p.parse_args()
    source=args.source.resolve()
    if source.suffix.lower()!='.json' or not source.is_file():raise SystemExit('Choose an existing project JSON, not a secret/environment file.')
    raw=source.read_bytes();campus=Campus.model_validate_json(raw)
    with main.accounts.db() as db:row=db.execute('SELECT id FROM users WHERE email=?',(args.email.strip().lower(),)).fetchone()
    if not row:raise SystemExit('Register the target account first.')
    for b in campus.buildings:candidates(b,generate_profiles(b,campus.profile_settings),campus.scenario)
    uid=row['id'];digest=hashlib.sha256(raw).hexdigest();campus.id='project-'+hashlib.sha256((uid+digest).encode()).hexdigest()[:12]
    campus.migration_notes.append('Explicit local import. Original input backed up; old results retained as historical, never current.')
    token=user_context.set(uid);project_token=main.project_context.set(campus.id)
    try:
        if main.data_file().exists():raise SystemExit('Already imported. No overwrite performed.')
        print('Validated private copy:',campus.id,'buildings:',len(campus.buildings))
        if not args.apply:print('Dry run only. Repeat with --apply to import into the named account.')
        else:
            backup=main.data_root()/'import-backups'/digest;backup.mkdir(parents=True,exist_ok=True)
            (backup/'original-input.json').write_bytes(raw)
            result=source.with_name(source.stem+'.result.json')
            if result.exists():(backup/'historical-result.json').write_bytes(result.read_bytes())
            main.write_campus(campus);print('Imported. Original files unchanged; refresh the project list.')
    finally:main.project_context.reset(project_token);user_context.reset(token)
