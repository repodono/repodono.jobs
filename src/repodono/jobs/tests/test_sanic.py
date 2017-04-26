# -*- coding: utf-8 -*-
"""
Manager test case
"""

import io
import json
import logging
import unittest
from textwrap import dedent

import sys
from os.path import join
from time import sleep

try:
    from sanic import Sanic
    from repodono.jobs.sanic import JobServer
except ImportError:  # pragma: no cover
    Sanic = None

from repodono.jobs.manager import JobManager
from repodono.jobs.manager import logger as manager_logger

sanic_logger = logging.getLogger('sanic')


class DummyManager(JobManager):

    def get_args(self, working_dir, timeout, msg, **kw):
        target = join(working_dir, 'out')

        prog = dedent("""
        import sys
        from time import sleep
        from os.path import dirname
        from os.path import isdir

        target = '%(target)s'
        timeout = %(timeout)f

        if not timeout:
            sys.exit(1)

        sleep(timeout)

        if isdir(dirname(target)):
            with open(target, 'w') as fd:
                fd.write('%(msg)s')
        """) % locals()

        return (sys.executable, '-c', prog)

    def verify_run_kwargs(self, **kw):
        try:
            # assuming both are provided as lists, assuming form-data
            return {
                'timeout': float(kw['timeout'][0]),
                'msg': '\n'.join(kw['msg']),
            }
        except (KeyError, ValueError):
            raise ValueError("missing or invalid arguments")

    def _cleanup_subprocess(self, working_dir, subprocess):
        # just wait a little...
        for x in range(10):
            sleep(0.1)
            if subprocess.poll() is not None:
                break


@unittest.skipIf(Sanic is None, 'sanic is unavailable')
class SanicProviderTestCase(unittest.TestCase):

    def setUp(self):
        manager = DummyManager()
        self.server = JobServer(job_manager=manager)

        self.stream = io.StringIO()
        self.handler = logging.StreamHandler(self.stream)
        manager_logger.addHandler(self.handler)
        self.sanic_level = sanic_logger.level
        sanic_logger.setLevel(logging.CRITICAL)

    def tearDown(self):
        manager_logger.removeHandler(self.handler)
        sanic_logger.setLevel(self.sanic_level)

    def create_app(self, hook_start_stop=False):
        manager = DummyManager()
        job_server = JobServer(manager, hook_start_stop=hook_start_stop)
        app = Sanic()
        job_server.register(app)
        if not hook_start_stop:
            job_server.start(None, None)
            self.addCleanup(job_server.stop, None, None)
        return app

    def test_base(self):
        self.server.start(None, None)
        self.assertIsNot(self.server.job_manager.root, NotImplemented)
        self.server.stop(None, None)
        self.assertIs(self.server.job_manager.root, NotImplemented)

    def test_run_error_args(self):
        app = self.create_app(hook_start_stop=True)
        # this will leave an orphan, which will be cleaned up.
        request, response = app.test_client.post('/execute', data={
            'timeout': 'xxxx',
            'msg': 'hello',
        })
        j = json.loads(response.text)
        self.assertEqual(j['error'], 'missing or invalid arguments')

        # since no job will be created...
        request, response = app.test_client.get('/poll/no_such_job/out')
        j = json.loads(response.text)
        self.assertEqual(j['error'], 'no such job_id')

    def test_run_standard(self):
        app = self.create_app(hook_start_stop=True)
        # this will leave an orphan, which will be cleaned up.
        request, response = app.test_client.post('/execute', data={
            'timeout': '0.1',
            'msg': 'hello',
        })
        j = json.loads(response.text)
        self.assertEqual(j['status'], 'created')

        # since the server has stopped with the hooks enabled, the job
        # will simply be cleared.
        request, response = app.test_client.get(j['location'])
        j = json.loads(response.text)
        self.assertEqual(j['error'], 'no such job_id')

    def test_run_continous(self):
        app = self.create_app()
        request, response = app.test_client.post('/execute', data={
            'timeout': '0.1',
            'msg': 'hello',
        })
        j = json.loads(response.text)
        location = j['location']
        self.assertEqual(j['status'], 'created')

        request, response = app.test_client.get(location)
        j = json.loads(response.text)
        self.assertEqual(j['status'], 'running')

        sleep(0.2)
        request, response = app.test_client.get(location)
        j = json.loads(response.text)
        self.assertEqual(j['status'], 'success')

        request, response = app.test_client.get(location + '/' + j['keys'][0])
        self.assertEqual(response.text, 'hello')

    def test_run_errored_process(self):
        app = self.create_app()
        request, response = app.test_client.post('/execute', data={
            'timeout': '0',
            'msg': 'hello',
        })
        j = json.loads(response.text)
        location = j['location']
        self.assertEqual(j['status'], 'created')

        sleep(0.2)
        request, response = app.test_client.get(location)
        j = json.loads(response.text)
        self.assertEqual(j['status'], 'failure')

        sleep(0.2)
        request, response = app.test_client.get(location + '/out')
        j = json.loads(response.text)
        self.assertEqual(j['error'], 'no such key for job')
