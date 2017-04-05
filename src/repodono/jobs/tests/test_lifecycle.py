# -*- coding: utf-8 -*-
"""
Manager test case
"""

import unittest
from textwrap import dedent

import sys
from os.path import exists
from os.path import isdir
from os.path import join
from time import sleep

from repodono.jobs.manager import WDManager
from repodono.jobs.manager import TaskRunnerManager
from repodono.jobs.exc import ManagerRuntimeError


class WDManagerTestCase(unittest.TestCase):

    def test_base_manager_simple(self):
        manager = WDManager()
        manager.start()
        root = manager.root
        self.assertTrue(isdir(root))
        manager.stop()
        self.assertFalse(isdir(root))

    def test_base_manager_stop(self):
        manager = WDManager()
        manager.stop()  # should not error even when not started.

    def test_base_manager_run(self):
        manager = WDManager()

        with self.assertRaises(ManagerRuntimeError):
            # not started yet
            manager.run()

        manager.start()
        with self.assertRaises(NotImplementedError):
            # since the implementation was not implemented
            manager.run()

        manager.stop()
        with self.assertRaises(ManagerRuntimeError):
            # not started yet
            manager.run()

    def test_base_manager_execute(self):
        manager = WDManager()
        with self.assertRaises(NotImplementedError):
            manager.execute('some_dir')


class TaskRunnerManagerTestCase(unittest.TestCase):

    def test_execute(self):
        manager = TaskRunnerManager()
        with self.assertRaises(NotImplementedError):
            manager.execute('some_dir')

    def test_get_args(self):
        manager = TaskRunnerManager()
        with self.assertRaises(NotImplementedError):
            manager.get_args('some_dir')


class DummyManagerTestCase(unittest.TestCase):

    class DummyManager(TaskRunnerManager):
        def get_args(self, working_dir, s, t, **kw):
            target = join(working_dir, 'output.txt')

            prog = dedent("""
            from time import sleep

            sleep(%(t)f)

            with open('%(target)s', 'w') as fd:
                fd.write('%(s)s')
            """) % locals()

            return (sys.executable, '-c', prog)

    def setUp(self):
        self.manager = self.DummyManager()
        self.manager.start()

    def tearDown(self):
        self.manager.stop()

    def test_execute(self):
        working_dir = self.manager.run(s='hello', t=0.1)
        f = join(working_dir, 'output.txt')
        self.assertFalse(exists(f))
        sleep(0.3)  # account for startup overhead.
        self.assertTrue(exists(f))
