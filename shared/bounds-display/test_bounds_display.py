"""Integration checks: outward enclosure, decisions, exact families, offline copy."""
from fractions import Fraction as F
import hashlib
import json
from pathlib import Path
import random
import shutil
import subprocess
import sys
import tempfile
import unittest

import bounds_display as app


class DisplayTests(unittest.TestCase):
    def setUp(self):
        self.raw = app.bounds.demo_csv()
        self.pin = hashlib.sha256(self.raw).hexdigest()

    def test_demo_retains_complete_original_analysis(self):
        result = app.summarize(self.raw, self.pin)
        self.assertEqual(result['analysis'], app.bounds.analyze(self.raw))
        self.assertEqual(result['analysis']['candidate_count'], 2)
        a,b = result['candidates']
        self.assertEqual([a['percentage_point_interval'][k] for k in ['lower','upper']], ['26.36','53.47'])
        self.assertEqual([b['percentage_point_interval'][k] for k in ['lower','upper']], ['-4.15','4.15'])
        self.assertTrue(a['exact_criteria']['candidate_exceeds_positive_margin'])
        self.assertTrue(b['exact_criteria']['entire_interval_strictly_inside_equivalence_margin'])

    def test_seeded_outward_enclosures_independent_fraction_oracle(self):
        rng=random.Random(737)
        for _ in range(200):
            lo,hi=sorted([F(rng.randint(-10000,10000),rng.randint(1,10000)) for _ in range(2)])
            places=rng.randrange(7); scale=10**places
            shown=app.display_interval(lo,hi,places)
            lower,upper=map(F,[shown['lower'],shown['upper']])
            self.assertEqual(lower,F((lo*100*scale).__floor__(),scale))
            self.assertEqual(upper,F((hi*100*scale).__ceil__(),scale))
            self.assertLessEqual(lower,lo*100); self.assertGreaterEqual(upper,hi*100)
            self.assertLess(lo*100-lower,F(1,scale))
            self.assertLess(upper-hi*100,F(1,scale))
            self.assertEqual(F(shown['lower_rounding_error']),lower-lo*100)
            self.assertEqual(F(shown['upper_rounding_error']),upper-hi*100)

    def test_negative_and_exact_grid_endpoints(self):
        shown=app.display_interval(F(-1,300),F(-1,700),2)
        self.assertEqual([shown[k] for k in ['lower','upper']],['-0.34','-0.14'])
        shown=app.display_interval(F(-1,10),F(1,10),0)
        self.assertEqual([shown[k] for k in ['lower','upper']],['-10','10'])
        self.assertEqual(shown['lower_rounding_error'],'0')

    def test_strict_boundary_and_loss_never_gain(self):
        margin=F(1,10)
        self.assertFalse(any(app.criteria(-margin,margin,margin).values()))
        # An exact interval just inside the margin loses equivalence at a
        # zero-place percentage-point display whose endpoints touch the limit.
        lo,hi=F(-99,1000),F(99,1000)
        shown=app.display_interval(lo,hi,0)
        self.assertTrue(app.criteria(lo,hi,margin)['entire_interval_strictly_inside_equivalence_margin'])
        self.assertFalse(app.criteria(F(shown['lower'])/100,F(shown['upper'])/100,margin)['entire_interval_strictly_inside_equivalence_margin'])
        for places in range(7):
            result=app.summarize(self.raw,self.pin,places=places)
            for row in result['candidates']:
                for k,v in row['displayed_interval_criteria'].items():
                    self.assertFalse(v and not row['exact_criteria'][k])

    def test_pins_and_input_validation(self):
        for pin in [None,'',self.pin.upper(),'f'*64]:
            with self.assertRaises(ValueError): app.summarize(self.raw,pin)
        for places in [-1,7,True,1.0]:
            with self.assertRaises(ValueError): app.summarize(self.raw,self.pin,places=places)
        for raw in [b'case,baseline,a\nx,0,1\nx,1,1\n',b'case,baseline,a\nx,0,2\n',b'\xff']:
            with self.assertRaises(ValueError): app.summarize(raw,hashlib.sha256(raw).hexdigest())

    def test_bom_crlf_and_unicode_identities_remain(self):
        raw='\ufeffcase,baseline,\u00e9,e\u0301\r\n\u03bb,0,1,0\r\n'.encode()
        result=app.summarize(raw,hashlib.sha256(raw).hexdigest())
        self.assertEqual([r['candidate'] for r in result['candidates']],['\u00e9','e\u0301'])
        self.assertEqual(result['analysis']['paired_cases'],1)
        self.assertEqual(result['analysis']['candidate_count'],2)
        self.assertEqual(result['input_sha256'],hashlib.sha256(raw).hexdigest())

    def test_snapshot_provenance(self):
        here=Path(app.__file__).parent
        for row in json.loads((here/'provenance.json').read_text()):
            self.assertEqual(hashlib.sha256((here/row['copy']).read_bytes()).hexdigest(),row['sha256'])

    def test_copied_folder_cli_pins_and_no_partial_output(self):
        scratch=Path('test/scratch').resolve(); scratch.mkdir(parents=True,exist_ok=True)
        with tempfile.TemporaryDirectory(dir=scratch) as tmp:
            folder=Path(tmp)/'tool'; shutil.copytree(Path(app.__file__).parent,folder,ignore=shutil.ignore_patterns('__pycache__'))
            cmd=[sys.executable,'-B','bounds_display.py']
            def run(args,raw=None):
                return subprocess.run(cmd+args,cwd=folder,input=raw,capture_output=True,timeout=30)
            demo=run(['demo']); self.assertEqual(demo.returncode,0,demo.stderr)
            self.assertEqual(json.loads(demo.stdout)['data_kind'],'synthetic_demonstration')
            good=run(['analyze','--expected-input-sha256',self.pin],self.raw)
            self.assertEqual(good.returncode,0,good.stderr)
            self.assertEqual(json.loads(good.stdout)['analysis'],app.bounds.analyze(self.raw))
            for args,raw in [(['analyze'],self.raw),(['analyze','--expected-input-sha256','f'*64],self.raw),(['demo','--places','-1'],None),(['demo','--margin','NaN'],None),(['demo','--expected-input-sha256',self.pin],None),(['analyze','--expected-input-sha256',self.pin],self.raw+b'\n')]:
                bad=run(args,raw); self.assertEqual(bad.returncode,2,bad.stderr)
                self.assertEqual(bad.stdout,b'')


if __name__ == '__main__':
    unittest.main()
