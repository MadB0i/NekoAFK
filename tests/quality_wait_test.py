"""Regression for premature async-Promise acceptance in the native test harness."""
import time,unittest
from quality_wait import wait_for_snapshot

class NativeConditionTests(unittest.TestCase):
    def test_false_snapshot_keeps_polling_until_resolved_condition(self):
        snapshots=iter([{'count':487,'open':1},{'count':500,'open':1},{'count':500,'open':0}])
        pumps=[]
        result=wait_for_snapshot(lambda:next(snapshots),lambda s:s['count']==500 and s['open']==0,pumps.append)
        self.assertEqual(result,{'count':500,'open':0})
        self.assertEqual(len(pumps),2)

    def test_false_snapshot_times_out(self):
        with self.assertRaisesRegex(AssertionError,'condition timed out'):
            wait_for_snapshot(lambda:False,bool,lambda ms:time.sleep(ms/1000),timeout=.01)

if __name__=='__main__':unittest.main()
