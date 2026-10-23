"""Validate the supported telescope RawHit contract without MC dependencies."""
import hashlib
import json
import xml.etree.ElementTree as ET
from research_common import digest

RAW_COLLECTIONS = ('LocalSiMAPSRawHits', 'LocalMPGDRawHits', 'LocalACLGADRawHits')


def readout_signature(geometry):
    root = ET.parse(geometry).getroot()
    constants = {n.get('name'):n.get('value') for n in root.findall('./define/constant')}
    mappings = [(n.get('name'), constants.get(n.get('id'),n.get('id')), n.get('readout'))
                for n in root.findall('./detectors/detector')]
    payload = ET.tostring(root.find('readouts')) + json.dumps(mappings).encode()
    return hashlib.sha256(payload).hexdigest()


def inspect_raw(path):
    import awkward as ak
    import uproot
    with uproot.open(path) as file:
        tree = file['events']
        if tree.typenames().get('EventHeader') != 'vector<edm4hep::EventHeaderData>':
            raise ValueError('RawHit input requires an EDM4hep EventHeader collection')
        headers = [tree[f'EventHeader/EventHeader.{key}'].array() for key in ('runNumber','eventNumber','timeStamp')]
        if not all(bool(ak.all(ak.num(a)==1)) for a in headers):
            raise ValueError('Exactly one EventHeader per event is required')
        identifiers = list(zip(ak.to_list(ak.flatten(headers[0])),ak.to_list(ak.flatten(headers[1]))))
        if len(set(identifiers)) != len(identifiers):
            raise ValueError('Duplicate run/event identifiers in RawHit input')
        counts = {}
        for collection,system,layers in zip(RAW_COLLECTIONS,(31,100,92),({0,1,2,3,4},{5},{6})):
            if tree.typenames().get(collection) != 'vector<edm4eic::RawTrackerHitData>':
                raise ValueError(f'Missing/wrong RawTrackerHit type: {collection}; use an explicit empty collection for inactive detectors')
            arrays = {key:tree[f'{collection}/{collection}.{key}'].array() for key in ('cellID','charge','timeStamp')}
            ids = ak.flatten(arrays['cellID'])
            if not bool(ak.all((ids & 255)==system)) or not set(ak.to_list((ids >> 11)&63)) <= layers:
                raise ValueError(f'Unsupported Cell ID system/layer mapping in {collection}')
            if not bool(ak.all(arrays['charge']>=0)):
                raise ValueError('The current energy-equivalent RawHit contract requires nonnegative charge')
            counts[collection] = int(ak.sum(ak.num(arrays['cellID'])))
        return {'events':tree.num_entries, 'raw_hit_counts':counts,
                'collections':{n:tree.typenames()[n] for n in tree.keys(recursive=False) if n in tree.typenames() and ('edm4eic::' in tree.typenames()[n] or 'edm4hep::' in tree.typenames()[n])},
                'event_identifiers_sha256':hashlib.sha256(json.dumps(ak.to_list(ak.zip(headers))).encode()).hexdigest()}


def validate_contract(path, metadata, geometry):
    record = json.loads(metadata.read_text())
    schema=record.get('schema')
    if schema not in ('local-telescope-rawhits-v1','local-telescope-rawhits-v2') or record.get('raw_sha256') != digest(path):
        raise ValueError('Missing/unsupported RawHit contract or file checksum mismatch')
    if record.get('readout_signature_sha256') != readout_signature(geometry):
        raise ValueError('RawHit and reconstruction Geometry readout definitions differ')
    if record.get('charge_unit') != 'keV_equivalent' or record.get('timestamp_unit') != 'ps':
        raise ValueError('Unsupported RawHit charge/time calibration encoding')
    required=('source_kind','conditions','producer')
    if schema=='local-telescope-rawhits-v1':
        from research_common import REPO
        if topology_signature(geometry)!=topology_signature(REPO/'geometry/nominal/seven_layer_telescope.xml'):
            raise ValueError('Legacy v1 requires the validated telescope topology; migrate metadata explicitly')
        required+=('measured_geometry_sha256',)
    elif record.get('topology_signature_sha256')!=topology_signature(geometry):raise ValueError('RawHit and reconstruction sensor topology differ')
    for name in required:
        if not record.get(name): raise ValueError(f'Missing RawHit provenance: {name}')
    kinds=('simulation','daq') if schema=='local-telescope-rawhits-v1' else ('simulation','daq','simulation_test_without_truth')
    if record['source_kind'] not in kinds or not isinstance(record['producer'],dict) or not isinstance(record['conditions'],dict):
        raise ValueError('RawHit source, producer and conditions must follow the documented contract')
    if schema=='local-telescope-rawhits-v2' and 'measured_geometry_sha256' in record:
        raise ValueError('Legacy measured_geometry_sha256 belongs to v1; migrate provenance explicitly')
    if record['source_kind']=='simulation_test_without_truth' and (
        record.get('simulation_truth_geometry_sha256') or record['producer'].get('simulation_sha256')):
        raise ValueError('Truth-excluded test metadata must not contain simulation truth identifiers')
    report = inspect_raw(path)
    if report['events'] <= 0: raise ValueError('Empty RawHit input file')
    return record, report


def topology_signature(geometry):
    """Readout identities and sensor topology, excluding all physical placement parameters."""
    root=ET.parse(geometry).getroot();rows=[]
    for detector in root.findall('./detectors/detector'):
        if detector.get('readout'):
            rows.append({'name':detector.get('name'),'layers':[
                {'id':layer.get('id'),'rings':[{'modules':ring.get('nmodules'),'module':ring.get('module')} for ring in layer.findall('ring')]}
                for layer in detector.findall('layer')],
                'sensors':[sum(component.get('sensitive')=='true' for component in module.findall('module_component')) for module in detector.findall('module')]})
    return hashlib.sha256(json.dumps({'readout':readout_signature(geometry),'topology':rows},sort_keys=True).encode()).hexdigest()
