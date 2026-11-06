from pathlib import Path
import hashlib
import json
import sys
import tempfile
import unittest

SCRIPTS=Path(__file__).resolve().parents[1]/'scripts'
sys.path.insert(0,str(SCRIPTS))
from archive_timing_results import snapshot


class EvidenceTest(unittest.TestCase):
    def test_preserves_versions_deduplicates_and_keeps_deleted_original(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td); run=root/'run'; run.mkdir()
            out=root/'evidence'; out.mkdir(); (out/'objects').mkdir()
            first=run/'timing.rpt'; second=run/'copy.rpt'
            first.write_text('first report'); second.write_text('first report')
            snapshot([run],out)
            self.assertEqual(len(list((out/'objects').iterdir())),1)
            first.write_text('second report with another length')
            snapshot([run],out)
            index=json.loads((out/'index.json').read_text())
            versions=index['files'][str(first)]['versions']
            self.assertEqual(len(versions),2)
            self.assertEqual((out/'objects'/versions[0]['sha256']).read_text(),'first report')
            self.assertEqual((out/'objects'/versions[1]['sha256']).read_text(),'second report with another length')
            first.unlink()
            snapshot([run],out)
            index=json.loads((out/'index.json').read_text())
            self.assertEqual(len(index['files'][str(first)]['versions']),2)
            for obj in (out/'objects').iterdir():
                self.assertEqual(hashlib.sha256(obj.read_bytes()).hexdigest(),obj.name)


if __name__=='__main__':unittest.main()
