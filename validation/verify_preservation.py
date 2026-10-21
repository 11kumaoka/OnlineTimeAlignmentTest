#!/usr/bin/env python3
"""Read-only check that every inventoried baseline XML/data/log is unchanged."""
import hashlib,json
from pathlib import Path
repo=Path(__file__).resolve().parents[1]
records=json.loads((repo/'validation/preserved_files.json').read_text())
relocated=json.loads((repo/'validation/relocated_data_sha256.json').read_text())
fail=[]
for name,expected in list(records.items()) + list(relocated.items()):
 p=repo/name
 if not p.is_file() or hashlib.sha256(p.read_bytes()).hexdigest()!=expected:fail.append(name)
assert not fail, 'Changed or missing baseline files: '+str(fail)
for link in json.loads((repo/'validation/path_migration.json').read_text())['updated_input_symlinks']:
 p=repo/link['path']
 if not p.is_symlink() or not p.is_file() or hashlib.sha256(p.read_bytes()).hexdigest()!=link['content_sha256']:
  fail.append(link['path'])
assert not fail, 'Changed relocated input links: '+str(fail)
# Pin validated source content independently of staged or committed Git state.
for name,expected in json.loads((repo/'validation/validated_sources.json').read_text()).items():
 p=repo/name
 assert p.is_file() and hashlib.sha256(p.read_bytes()).hexdigest()==expected, 'Validated source changed: '+name
print(f'PASS: {len(records)} baseline records and {len(relocated)} relocated files unchanged; electron diff preserved')
