"""Readout/provenance semantics tests; ROOT structure is covered by integration probes."""
import json,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from digitization.contract import validate_contract,readout_signature,topology_signature
from research_common import REPO,digest


class MetadataTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name)
        self.raw=self.root/'raw.root';self.raw.write_bytes(b'schema-test-only')
        self.geometry=REPO/'geometry/nominal/seven_layer_telescope.xml';self.meta=self.root/'contract.json'
        self.record={'schema':'local-telescope-rawhits-v2','raw_sha256':digest(self.raw),
          'readout_signature_sha256':readout_signature(self.geometry),'topology_signature_sha256':topology_signature(self.geometry),
          'charge_unit':'keV_equivalent','timestamp_unit':'ps','source_kind':'simulation_test_without_truth',
          'producer':{'test':'schema test'},'conditions':{'encoding':'documented'}}
    def tearDown(self):self.temp.cleanup()
    def check(self):
        self.meta.write_text(json.dumps(self.record));return validate_contract(self.raw,self.meta,self.geometry)
    @patch('digitization.contract.inspect_raw',return_value={'events':1})
    def test_truth_optional_and_topology_required(self,_):
        self.check()
        self.record['topology_signature_sha256']='wrong'
        with self.assertRaises(ValueError):self.check()
    @patch('digitization.contract.inspect_raw',return_value={'events':1})
    def test_legacy_field_not_reinterpreted(self,_):
        self.record['schema']='local-telescope-rawhits-v1'
        with self.assertRaises(ValueError):self.check()
        self.record['source_kind']='simulation';self.record['measured_geometry_sha256']='legacy-value-preserved'
        record,_=self.check();self.assertEqual(record['measured_geometry_sha256'],'legacy-value-preserved')
    @patch('digitization.contract.inspect_raw',return_value={'events':1})
    def test_incompatible_readout_rejected(self,_):
        self.record['readout_signature_sha256']='incompatible'
        with self.assertRaises(ValueError):self.check()

    @patch('digitization.contract.inspect_raw',return_value={'events':1})
    def test_v2_rejects_ambiguous_truth_metadata(self,_):
        self.record['measured_geometry_sha256']='ambiguous-legacy-field'
        with self.assertRaises(ValueError):self.check()
        self.record.pop('measured_geometry_sha256');self.record['producer']['simulation_sha256']='excluded-truth-identifier'
        with self.assertRaises(ValueError):self.check()


if __name__=='__main__':unittest.main()
