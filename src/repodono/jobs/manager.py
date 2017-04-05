# -*- coding: utf-8 -*-
"""
Manager test case
"""

from subprocess import Popen

from tempfile import TemporaryDirectory
from tempfile import mkdtemp
from .exc import ManagerRuntimeError


class WDManager(object):
    """
    Simple manager class for creation and management of working
    directories.
    """

    def __init__(self):
        # simply create the object for now
        self.root = NotImplemented
        self.tempdir = None

    def start(self):
        tempdir = self.tempdir = TemporaryDirectory()
        self.root = tempdir.name

    def stop(self):
        self.root = NotImplemented
        if self.tempdir:
            self.tempdir.cleanup()

    def create_working_dir(self):
        return mkdtemp(dir=self.root)

    def execute(self, working_dir, **kw):
        raise NotImplementedError

    def run(self, **kw):
        if self.root is NotImplemented:
            raise ManagerRuntimeError('manager not started')
        working_dir = self.create_working_dir()
        self.execute(working_dir=working_dir, **kw)
        return working_dir


class TaskRunnerManager(WDManager):

    def __init__(self):
        super(TaskRunnerManager, self).__init__()
        self.mapping = {}

    def get_args(self, working_dir, **kw):
        raise NotImplementedError

    def execute(self, working_dir, **kw):
        args = self.get_args(working_dir=working_dir, **kw)
        self.mapping[working_dir] = Popen(args)
