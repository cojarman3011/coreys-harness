import csv
import json
import tempfile
import unittest
from pathlib import Path

from skylinee_linear.model import ModelError, predict, verify
from skylinee_linear.training import save_release, train_csv


class TestLinear(unittest.TestCase):
    def setUp(self):
        t=tempfile.TemporaryDirectory();self.addCleanup(t.cleanup)
        self.root=Path(t.name);self.csv=self.root/"data.csv"
        with self.csv.open("w",newline="") as f:
            w=csv.writer(f);w.writerow(["x","y"]);w.writerows((x,2*x+3) for x in range(30))
    def fit(self):
        m=train_csv(self.csv,"y",["x"]);a=self.root/"m.json";b=self.root/"p.json";save_release(m,a,b);return m,a,b
    def test_fit(self):
        m,a,b=self.fit();self.assertAlmostEqual(m["coefficients"][0],2);self.assertAlmostEqual(m["intercept"],3)
        self.assertEqual(verify(a,b)["status"],"PASS")
    def test_tampering(self):
        m,a,b=self.fit();m["intercept"]=999;a.write_text(json.dumps(m))
        with self.assertRaisesRegex(ModelError,"digest"):verify(a,b)
    def test_bad_input(self):
        m,_,_=self.fit()
        with self.assertRaises(ModelError):predict(m,{"x":"four"})
    def test_extrapolation(self):
        m,_,_=self.fit();self.assertTrue(predict(m,{"x":-10})["outside_training_range"])
    def test_zero_intercept_quality(self):
        a=train_csv(self.csv,"y",["x"]);b=train_csv(self.csv,"y",["x"],no_intercept=True)
        self.assertGreater(b["metrics"]["rmse"],a["metrics"]["rmse"])
if __name__=="__main__":unittest.main()
