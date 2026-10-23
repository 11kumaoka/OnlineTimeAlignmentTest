"""Immutable Geometry bytes with separate, explicit review/activation lifecycle."""
import json
import shutil
import time
import xml.etree.ElementTree as ET
from pathlib import Path
from geometry.placements import geometry
from research_common import digest,write_json


def l2_scope(nominal,other):
    from correction.scope import verify_scope
    verify_scope(nominal,other,(2,))


class Geometries:
    def __init__(self,queue,config):self.queue=queue;self.config=config
    def verify(self,record):
        if digest(Path(record['path']))!=record['sha256']:raise RuntimeError('Geometry version was modified: '+record['id'])
        return record
    def register(self,path,kind,parent=None,evidence=None):
        sha=digest(path);identity='geo-'+sha
        try:
            record=self.verify(self.queue.geometry(identity))
            if evidence and evidence.get('converged'):
                record.setdefault('evidence_history',[]).append(evidence)
                record['evidence']=evidence;self.queue.geometry_put(record)
                self.queue.event('geometry_evidence_added',version=identity,evidence=evidence)
            return record
        except ValueError:pass
        directory=self.queue.state/'geometries'/identity;directory.mkdir(parents=True,exist_ok=False)
        shutil.copyfile(path,directory/'geometry.xml')
        if digest(directory/'geometry.xml')!=sha:raise RuntimeError('Geometry copy changed')
        record={'id':identity,'path':str(directory/'geometry.xml'),'sha256':sha,'status':kind,
                'parent':parent,'created_at':time.time(),'evidence':evidence}
        write_json(directory/'creation.json',record);self.queue.geometry_put(record)
        self.queue.event('geometry_registered',version=identity,geometry_kind=kind,parent=parent)
        return record
    def initialize(self):
        if self.queue.get('active_geometry') is None:
            nominal=self.register(Path(self.config['fallback_geometry']),'fallback')
            self.queue.put('active_geometry',nominal['id'])
            self.queue.event('fallback_selected',version=nominal['id'])
    def active(self):return self.verify(self.queue.geometry(self.queue.get('active_geometry')))
    def review(self,identity,evidence_path):
        record=self.verify(self.queue.geometry(identity));evidence=json.loads(evidence_path.read_text())
        if not record.get('evidence') or not record['evidence'].get('converged'):
            raise ValueError('Version has no converged calibration evidence')
        # This is an explicit human review, not automatic scientific certification.
        if evidence.get('version_id')!=identity or evidence.get('approved') is not True or not all(evidence.get(k) for k in ('reviewer','rationale','independent_validation')):
            raise ValueError('Review requires exact version, explicit approval, reviewer, rationale and independent validation evidence')
        calibration=record['evidence']
        if digest(Path(calibration['report_path']))!=calibration['report_sha256']:
            raise RuntimeError('Calibration evidence changed')
        validation=evidence['independent_validation']
        if not isinstance(validation,dict) or not validation.get('path') or not validation.get('sha256'):
            raise ValueError('Independent validation report path and checksum are required')
        report_path=Path(validation['path']).resolve()
        if digest(report_path)!=validation['sha256']:raise ValueError('Independent validation checksum mismatch')
        report=json.loads(report_path.read_text())
        if report.get('geometry_sha256')!=record['sha256'] or report.get('passed') is not True:
            raise ValueError('Independent report must identify and approve this exact Geometry')
        if report.get('raw_sha256')==calibration['raw_sha256'] or not report.get('raw_sha256'):
            raise ValueError('Independent validation must identify a distinct fixed RawHit dataset')
        saved=Path(record['path']).parent/('validation-'+str(time.time_ns())+'.json')
        write_json(saved,report)
        evidence['independent_validation']={'path':str(saved),'sha256':digest(saved)}
        dest=Path(record['path']).parent/('review-'+str(time.time_ns())+'.json')
        write_json(dest,evidence)
        record['status']='validated';record['review']={'path':str(dest),'sha256':digest(dest)}
        self.queue.geometry_put(record);self.queue.event('geometry_reviewed',version=identity,review=record['review'])
    def activate(self,identity):
        record=self.verify(self.queue.geometry(identity))
        if record['status']!='validated':raise ValueError('Only explicitly validated Geometry can be activated')
        review=record['review']
        if digest(Path(review['path']))!=review['sha256']:raise RuntimeError('Review evidence was modified')
        evidence=json.loads(Path(review['path']).read_text())
        validation=evidence['independent_validation']
        if digest(Path(validation['path']))!=validation['sha256']:raise RuntimeError('Independent validation evidence was modified')
        calibration=record['evidence']
        if digest(Path(calibration['report_path']))!=calibration['report_sha256']:raise RuntimeError('Calibration report was modified')
        previous=self.queue.get('active_geometry');self.queue.put('active_geometry',identity)
        self.queue.event('geometry_activated',version=identity,previous=previous)
