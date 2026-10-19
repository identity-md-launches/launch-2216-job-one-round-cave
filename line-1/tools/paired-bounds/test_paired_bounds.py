"""Independent exact probability and interface checks; no network or packages."""
import hashlib
import itertools
import json
import math
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from fractions import Fraction as F

import paired_bounds as p


class BoundsTests(unittest.TestCase):
    def test_integer_cdf_matches_independent_fraction_sum(self):
        for n in range(1, 11):
            for a in range(9):
                prob = F(a, 8)
                for k in range(-1, n + 1):
                    expected = sum((math.comb(n, j) * prob**j * (1-prob)**(n-j)
                                    for j in range(max(0, min(k, n) + 1))), F(0))
                    self.assertEqual(F(p.cdf_numerator(n, k, a, 8), 8**n), expected)

    def test_outward_endpoint_brackets(self):
        # Independent direct polynomial, no runtime CDF reused.
        for n in range(1, 13):
            for count in range(n + 1):
                tail = F(1, 80)
                low, high = p.binomial_bounds(n, count, tail)
                if count:
                    def sf(q):
                        return sum((math.comb(n,j)*q**j*(1-q)**(n-j)
                                    for j in range(count, n+1)), F(0))
                    self.assertLessEqual(sf(low), tail)
                    self.assertGreater(sf(low + F(1, p.GRID)), tail)
                else:
                    self.assertEqual(low, 0)
                if count < n:
                    def cdf(q):
                        return sum((math.comb(n,j)*q**j*(1-q)**(n-j)
                                    for j in range(count+1)), F(0))
                    self.assertLessEqual(cdf(high), tail)
                    self.assertGreater(cdf(high-F(1,p.GRID)), tail)
                else:
                    self.assertEqual(high, 1)

    def test_binomial_marginal_coverage_exhaustive(self):
        for n in range(1, 10):
            bounds = [p.binomial_bounds(n,k,F(1,40)) for k in range(n+1)]
            for a in range(17):
                prob = F(a,16)
                missed = sum((math.comb(n,k)*prob**k*(1-prob)**(n-k)
                              for k,(lo,hi) in enumerate(bounds) if not lo <= prob <= hi), F(0))
                self.assertLessEqual(missed,F(1,20))

    def test_paired_difference_coverage_multinomial(self):
        # Exhaust all win/loss/concordant counts at small n, including negative effects.
        for n in range(1, 8):
            bs = [p.binomial_bounds(n,k,F(1,80)) for k in range(n+1)]
            for aw in range(5):
                for al in range(5-aw):
                    qw,ql=F(aw,4),F(al,4)
                    qc=1-qw-ql
                    missed=F(0)
                    for w in range(n+1):
                        for l in range(n-w+1):
                            c=n-w-l
                            lo,hi=bs[w][0]-bs[l][1],bs[w][1]-bs[l][0]
                            if not lo <= qw-ql <= hi:
                                coefficient=math.factorial(n)//(math.factorial(w)*math.factorial(l)*math.factorial(c))
                                missed += coefficient*qw**w*ql**l*qc**c
                    self.assertLessEqual(missed,F(1,20))

    def test_symmetry_family_and_alpha(self):
        raw=b'case,baseline,a\nx,0,1\ny,0,1\nz,1,0\n'
        swap=b'case,baseline,a\nx,1,0\ny,1,0\nz,0,1\n'
        def ends(report):
            return [F(int(x['numerator']),int(x['denominator'])) for x in
                    report['candidates'][0]['candidate_minus_baseline_bounds']]
        lo,hi=ends(p.analyze(raw))
        self.assertEqual(ends(p.analyze(swap)),[-hi,-lo])
        wide=ends(p.analyze(raw,F(1,100)))
        self.assertLessEqual(wide[0],lo)
        self.assertGreaterEqual(wide[1],hi)
        family=b'case,baseline,a,b\nx,0,1,1\ny,0,1,1\nz,1,0,0\n'
        wide=ends(p.analyze(family))
        self.assertLessEqual(wide[0],lo)
        self.assertGreaterEqual(wide[1],hi)

    def test_demo_and_margin(self):
        raw=p.demo_csv()
        result=p.analyze(raw)
        self.assertTrue(result['candidates'][0]['candidate_exceeds_positive_margin'])
        self.assertTrue(result['candidates'][1]['entire_interval_strictly_inside_equivalence_margin'])
        self.assertEqual(result['input_sha256'],hashlib.sha256(raw).hexdigest())
        self.assertEqual(result,p.analyze(raw))
        zero_margin=p.analyze(raw,margin=F(0))
        self.assertFalse(any(c['entire_interval_strictly_inside_equivalence_margin'] for c in zero_margin['candidates']))
        broad=p.analyze(raw,margin=F(1))
        self.assertFalse(any(c['candidate_exceeds_positive_margin'] for c in broad['candidates']))

    def test_bom_crlf_and_unicode_names_preserved(self):
        raw='\ufeffcase,baseline,"系统,a"\r\n"é,一",0,1\r\n'.encode()
        names,rows=p.parse_csv(raw)
        self.assertEqual(names,['系统,a'])
        self.assertEqual(rows,[(0,1)])
        self.assertEqual(p.analyze(raw)['candidates'][0]['name'],'系统,a')

    def test_invalid_csv(self):
        cases=[b'', b'case,baseline,a\n', b'case,baseline,a\nx,0,1\nx,1,0\n',
               b'case,baseline,a\nx,0,true\n', b'case,baseline,a\n\n',
               b'case,baseline,a\nx,0,1,0\n', b'case,baseline,a\n x,0,1\n',
               b'case,baseline,baseline\nx,0,1\n', b'case,baseline,a,a\nx,0,1,1\n',
               b'case,baseline,a\n"x,0,1\n', b'case,baseline,a\nx,0,1\n\xff',
               'case,baseline,a\nx\u202e,0,1\n'.encode(),
               b'case,baseline,a\nx,0,1\n'+b'z'*(p.MAX_BYTES+1)]
        for raw in cases:
            with self.subTest(raw=raw[:60]),self.assertRaises(p.InputError):
                p.parse_csv(raw)
        too_many=('case,baseline,a\n'+''.join(f'x{i},0,1\n' for i in range(513))).encode()
        with self.assertRaises(p.InputError): p.parse_csv(too_many)

    def test_scalar_validation(self):
        for value in ['NaN','0.05e0',' 0.05','0.0000000001','-1','1/20','2','0.2\n']:
            with self.assertRaises(p.InputError): p.decimal(value,'alpha',F(1,1000000),F(1,5))
        for args in [(True,0,F(1,40)),(1,True,F(1,40)),(0,0,F(1,40)),(513,0,F(1,40)),
                     (4,5,F(1,40)),(1,0,0.1)]:
            with self.assertRaises(p.InputError): p.binomial_bounds(*args)
        for alpha,margin in [(0.05,F(1,10)),(F(0),F(1,10)),(F(1,20),1.0)]:
            with self.assertRaises(p.InputError): p.analyze(p.demo_csv(),alpha,margin)

    def test_maximum_precision_and_endpoints(self):
        tail=F(1,64000000)
        for count in [0,1,256,511,512]:
            low,high=p.binomial_bounds(512,count,tail)
            self.assertLessEqual(low,F(count,512))
            self.assertGreaterEqual(high,F(count,512))
            self.assertTrue(0 <= low <= high <= 1)

    def test_standalone_cli_and_pins(self):
        root=Path.cwd().resolve()
        scratch=root/'test'/'scratch'
        scratch.mkdir(parents=True,exist_ok=True)
        with tempfile.TemporaryDirectory(dir=scratch) as temp:
            folder=Path(temp)
            script=folder/'paired_bounds.py'
            shutil.copyfile(Path(p.__file__),script)
            raw=p.demo_csv()
            data=folder/'data.csv'
            data.write_bytes(raw)
            def run(*args):
                return subprocess.run([sys.executable,'-B',str(script),*args],cwd=folder,
                                      capture_output=True,text=True,timeout=30)
            demo=run('--demo')
            self.assertEqual(demo.returncode,0,demo.stderr)
            self.assertEqual(json.loads(demo.stdout)['data_kind'],'synthetic_demonstration')
            pin=hashlib.sha256(raw).hexdigest()
            actual=run('--input','data.csv','--expected-input-sha256',pin)
            self.assertEqual(actual.returncode,0,actual.stderr)
            for args in [('--input','data.csv'),('--input','data.csv','--expected-input-sha256','0'*64),
                         ('--demo','--margin','NaN'),('--demo','--expected-input-sha256',pin)]:
                bad=run(*args)
                self.assertEqual(bad.returncode,2)
                self.assertEqual(bad.stdout,'')
            # Escape target is still inside the task workspace; tool's cwd is narrower.
            target=folder.parent/'paired-bounds-outside.txt'
            target.write_bytes(raw)
            try:
                (folder/'escape.csv').symlink_to(target)
                bad=run('--input','escape.csv','--expected-input-sha256',pin)
                self.assertEqual(bad.returncode,2)
                self.assertEqual(bad.stdout,'')
            finally:
                target.unlink()
            self.assertEqual(data.read_bytes(),raw)


if __name__=='__main__':
    unittest.main()
