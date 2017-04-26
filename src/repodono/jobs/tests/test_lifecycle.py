# -*- coding: utf-8 -*-
"""
Simple lifecycles test cases
"""

import io
import logging
import unittest
from textwrap import dedent

import sys
from os.path import exists
from os.path import join
from time import sleep

from repodono.jobs.manager import JobManager
from repodono.jobs.manager import logger as manager_logger


class DummyManagerTestCase(unittest.TestCase):

    class DummyManager(JobManager):
        def get_args(self, working_dir, s, t, **kw):
            target = join(working_dir, 'out')

            prog = dedent("""
            from time import sleep
            from os.path import dirname
            from os.path import isdir

            target = '%(target)s'
            sleep(%(t)f)

            if isdir(dirname(target)):
                with open(target, 'w') as fd:
                    fd.write('%(s)s')
            """) % locals()

            return (sys.executable, '-c', prog)

    def setUp(self):
        self.manager = self.DummyManager()
        self.manager.start()
        self.stream = io.StringIO()
        self.handler = logging.StreamHandler(self.stream)
        manager_logger.addHandler(self.handler)

    def tearDown(self):
        self.manager.stop()
        manager_logger.removeHandler(self.handler)

    def test_execute(self):
        working_dir = self.manager.run(s='hello', t=0.1)
        self.assertEqual(self.manager.list_working_dir(working_dir), [])
        f = join(working_dir, 'out')
        self.assertFalse(exists(f))
        sleep(0.3)  # account for startup overhead.
        self.assertEqual(self.manager.list_working_dir(working_dir), ['out'])
        self.assertTrue(exists(f))
        self.assertEqual(self.manager.lookup_path(working_dir, 'out'), f)
        self.assertEqual(self.manager.get_result_by_key(
            working_dir, 'out'), 'hello')

    def test_stray_process(self):
        self.manager.run(s='hello', t=0.05)
        self.manager.stop()
        self.assertIn('is still running', self.stream.getvalue())
        sleep(0.2)  # to actually let it terminate
