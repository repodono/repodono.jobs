# -*- coding: utf-8 -*-
"""
Manager test case
"""

import logging

from os.path import isfile
from os.path import join
from os.path import normpath
from os import listdir
from subprocess import Popen

from tempfile import TemporaryDirectory
from tempfile import mkdtemp
from .exc import ManagerRuntimeError

logger = logging.getLogger(__name__)


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


class JobManager(WDManager):

    def __init__(self):
        super(JobManager, self).__init__()
        self.mapping = {}

    def get_args(self, working_dir, **kw):
        raise NotImplementedError

    def execute(self, working_dir, **kw):
        args = self.get_args(working_dir=working_dir, **kw)
        self.mapping[working_dir] = Popen(args)

    def _cleanup_subprocess(self, working_dir, subprocess):
        """
        Subclass can implement this for explicit cleanup instructions.

        Must accept both the working_dir and the subprocess argument.
        """

        pass

    def stop(self):
        for wd, p in self.mapping.items():
            if p.poll() is None:
                logger.warning('subprocess %d is still running' % p.pid)
                self._cleanup_subprocess(wd, p)
        super(JobManager, self).stop()

    def lookup_path(self, working_dir, key):
        """
        Look up the path associated with the given working_dir and key.

        By default it is a simple normpath and verify that it is inside
        working_dir, though some implementations may want to have a more
        specific abstraction in place.
        """

        target = normpath(join(working_dir, key))
        if not (target.startswith(working_dir) and isfile(target)):
            return None
        return target

    def list_working_dir(self, working_dir):
        """
        Return a list of result keys that are associated with the
        working directory.  By default, the keys are a direct mapping to
        the file names.
        """

        return listdir(working_dir)

    def get_result_by_key(self, working_dir, key):
        """
        Retrieve the raw results.

        Default implementation is very naive - simply use lookup_path to
        locate the results.
        """

        target = self.lookup_path(working_dir, key)
        if not target:
            raise KeyError('no such working_dir or key')

        with open(target) as fd:
            return fd.read()
