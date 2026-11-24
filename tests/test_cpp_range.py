"""Cross-language boundary test for the shared numerical rejection contract."""
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
import numpy as np
from swallowguard.evaluate.selective import range_acceptance
from swallowguard.export.int8 import input_range


@unittest.skipUnless(shutil.which('g++'),'C++ compiler unavailable')
class CrossLanguageRange(unittest.TestCase):
    def test_python_cpp_agree_at_float32_boundaries(self):
        root=Path(__file__).resolve().parents[1];rng=np.random.default_rng(2026)
        cases=[];expected=[]
        for scale,z in [(np.float32(.1),-3),(np.float32(.5),-10),(np.float32(.30551189),0)]:
            lo,hi=input_range(float(scale),z)
            for value in [np.float32(lo),np.nextafter(np.float32(lo),np.float32(-np.inf)),
                          np.float32(hi),np.nextafter(np.float32(hi),np.float32(np.inf)),np.float32(0)]:
                x=np.array([value],dtype=np.float32)
                cases.append((scale,z,x));expected.append(int(range_acceptance(x[None],float(scale),z)[0]))
            for _ in range(20):
                x=rng.uniform(lo*1.05,hi*1.05,16).astype(np.float32)
                cases.append((scale,z,x));expected.append(int(range_acceptance(x[None],float(scale),z)[0]))
        with tempfile.TemporaryDirectory() as td:
            binary=Path(td)/'range_gate'
            subprocess.run(['g++','-std=c++17','-Wall','-Wextra','-Werror','-I',str(root/'firmware/include'),
                            str(root/'firmware/host_tests/range_gate_cli.cpp'),'-o',str(binary)],check=True,capture_output=True)
            payload=''.join(f'{float(scale):.9g} {z} {len(x)} '+' '.join(f'{float(v):.9g}' for v in x)+'\n' for scale,z,x in cases)
            actual=subprocess.run([str(binary)],input=payload,check=True,text=True,capture_output=True)
        self.assertEqual([int(x) for x in actual.stdout.split()],expected)


if __name__=='__main__':unittest.main()
