import unittest,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from timing_night import ranking,jobs_for_winner
class NightPolicyTest(unittest.TestCase):
 def test_failed_jobs_cannot_win_and_tns_breaks_ties(self):
  rows=[dict(execution='failed',synthesis='bad'),dict(execution='complete',synthesis='carry',wns_ns=-.5,tns_ns=-20),dict(execution='complete',synthesis='defaults',wns_ns=-.5,tns_ns=-10)]
  self.assertEqual(ranking(rows)[0]['synthesis'],'defaults')
  self.assertEqual(jobs_for_winner(rows),[('defaults','netdelay_high'),('defaults','wl_block'),('defaults','explore_postroute')])
 def test_no_complete_baseline_does_not_schedule_implementations(self):
  self.assertEqual(jobs_for_winner([dict(execution='synthesis_failed')]),[])
