"""Explicit ready-manifest delivery adapter; no assumed E0 transport or filename order."""
import json
import re
import time
from pathlib import Path
from digitization.contract import validate_contract
from research_common import digest


def inspect_manifest(path,input_dir,geometry,ordering):
    manifest=json.loads(path.read_text())
    required={'schema','input_id','raw_file','raw_sha256','metadata_file','metadata_sha256'}
    if set(manifest)-required-{'sequence'} or not required<=set(manifest) or manifest['schema']!='rawhit-delivery-v1':
        raise ValueError('Unsupported readiness manifest')
    identity=manifest['input_id']
    if not isinstance(identity,str) or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.-]{0,95}',identity):
        raise ValueError('Input identifier must be an unambiguous safe local identifier')
    sequence=manifest.get('sequence')
    if ordering=='sequence' and (type(sequence)!=int or sequence<0):raise ValueError('Upstream sequence is required in sequence mode')
    if ordering=='identity' and sequence is not None:raise ValueError('Do not discard upstream sequence; select sequence ordering')
    paths=[]
    for key,hash_key in [('raw_file','raw_sha256'),('metadata_file','metadata_sha256')]:
        relative=Path(manifest[key])
        if relative.is_absolute():raise ValueError('Delivery filenames must be relative to input directory')
        target=(input_dir/relative).resolve()
        if not target.is_relative_to(input_dir) or not target.is_file():raise ValueError('Delivery component missing or escapes input directory')
        if digest(target)!=manifest[hash_key]:raise ValueError('Delivery component checksum mismatch: '+key)
        paths.append(target)
    validate_contract(paths[0],paths[1],geometry)
    return {'id':identity,'sequence':sequence,'raw_name':manifest['raw_file'],
            'raw_path':str(paths[0]),'metadata_path':str(paths[1]),
            'raw_sha256':manifest['raw_sha256'],'metadata_sha256':manifest['metadata_sha256'],
            'marker_path':str(path),'marker_sha256':digest(path),'ready':True,'discovered_at':time.time(),
            'status':'pending','reconstruction_status':'pending','calibration_status':'not_attempted',
            'attempts':[],'geometry':None,'outputs':[]}


def verify_input(record):
    for name,sha in [('raw_path','raw_sha256'),('metadata_path','metadata_sha256'),('marker_path','marker_sha256')]:
        if digest(Path(record[name]))!=record[sha]:raise RuntimeError('Input changed after readiness: '+record['id'])


def scan(queue,input_dir,geometry,ordering):
    records=[]
    existing={j['marker_path']:j for j in queue.jobs()}
    for path in sorted(input_dir.glob('*.ready.json')):
        try:
            if str(path) in existing:
                verify_input(existing[str(path)])
                continue
            records.append(inspect_manifest(path,input_dir,geometry,ordering))
        except Exception as error:queue.issue(path,error)
    # Reject an ambiguous batch before accepting either side of a collision.
    for record in records:
        fields=['id','raw_sha256']+(['sequence'] if ordering=='sequence' else [])
        if any(sum(other[field]==record[field] for other in records)>1 for field in fields):
            queue.issue(record['marker_path'],'Ambiguous duplicate identity, payload or sequence in ready batch')
            continue
        try:
            queue.add(record)
        except Exception as error:queue.issue(record['marker_path'],'Duplicate identity/payload/sequence: '+str(error))
