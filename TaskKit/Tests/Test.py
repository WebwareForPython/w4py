import os
import sys
import unittest

sys.path.insert(1, os.path.abspath(os.path.join(os.pardir, os.pardir)))

from TaskKit.Scheduler import Scheduler


class TaskKitTest(unittest.TestCase):

    def setUp(self):
        self._scheduler = Scheduler()

    def checkBasics(self):
        sched = self._scheduler
        sched.start()

    def tearDown(self):
        self._scheduler.stop()
        self._scheduler = None


def makeTestSuite():
    suite1 = unittest.makeSuite(TaskKitTest, 'check')
    return unittest.TestSuite((suite1,))


if __name__ == '__main__':
    runner = unittest.TextTestRunner(stream=sys.stdout)
    unittest.main(defaultTest='makeTestSuite', testRunner=runner)
