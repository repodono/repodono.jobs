# -*- coding: utf-8 -*-
"""
Manager test case
"""

import unittest

from os.path import isdir

from repodono.jobs.manager import WDManager
from repodono.jobs.manager import JobManager
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

    def test_base_manager_verify_run_kwargs(self):
        manager = WDManager()
        self.assertEqual(manager.verify_run_kwargs(some='kwargs'), {
            'some': 'kwargs'
        })


class JobManagerTestCase(unittest.TestCase):

    def setUp(self):
        self.manager = JobManager()

    def tearDown(self):
        self.manager.stop()

    def test_execute(self):
        with self.assertRaises(NotImplementedError):
            self.manager.execute('some_dir')

    def test_get_args(self):
        with self.assertRaises(NotImplementedError):
            self.manager.get_args('some_dir')

    def test_list_working_dir(self):
        self.manager.start()
        wd = self.manager.create_working_dir()
        self.assertEqual(self.manager.list_working_dir(wd), [])

    def test_lookup_path(self):
        self.manager.start()
        wd = self.manager.create_working_dir()
        self.assertEqual(self.manager.lookup_path(wd, 'nothing'), None)

    def test_get_result_by_key(self):
        self.manager.start()
        wd = self.manager.create_working_dir()
        with self.assertRaises(KeyError):
            self.manager.get_result_by_key(wd, 'nothing')

    # rest of the tests will be done under lifecycle for the successful
    # runs require an actual get_args implementation
