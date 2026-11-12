import unittest
from pathlib import Path
from deployment_utils import add_duration, paginate, recent_latency_stats
from tutor_backend import Tutor, load_lessons

ROOT=Path(__file__).resolve().parents[1]

class DeploymentTests(unittest.TestCase):
    def test_paginate(self):
        self.assertEqual(paginate(list(range(8)), 2, 3),(list(range(3,6)),3,6))
    def test_paginate_invalid(self):
        with self.assertRaises(ValueError):paginate([1], 0, 3)
    def test_latency(self):
        v=add_duration([],0.15)
        self.assertEqual(recent_latency_stats(v)['mean'],0.15)
    def test_latency_no_messages(self):
        self.assertEqual(recent_latency_stats([])['count'],0)
    def test_limit_measurements(self):
        self.assertEqual(len(add_duration([.1]*100,.2)),100)
    def test_lessons_supplied(self):
        data=load_lessons(ROOT/'lessons.json')
        twin=Tutor(lessons_data=data)
        self.assertEqual(len(twin.lessons),len(data))
        self.assertTrue(twin.reply('What is SQL?')['sources'])
    def test_deploy_files(self):
        for name in ['app.py','requirements.txt','.streamlit/config.toml','README.md','lessons.json']:
            self.assertTrue((ROOT/name).is_file(),name)

if __name__=='__main__':unittest.main()
