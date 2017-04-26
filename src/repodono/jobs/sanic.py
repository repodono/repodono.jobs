# -*- coding: utf-8 -*-
"""
Sanic implementation
"""

from sanic import response
from sanic import Blueprint

from random import getrandbits


class JobServer(object):
    """
    A basic job server that will setup a couple routes.

    The target usage is to encapsulate and expose a service that takes
    some input argument and output some files onto some temporary dir,
    which is to be provided by a specific job_manager implementation.
    This job server will provide access to the functionality by the
    above.
    """

    def __init__(
            self, job_manager, base_url='/', name=None, hook_start_stop=True):
        """
        Takes in a subclass of job_manager, and provide some standard
        ways of interfacing with it.
        """

        self.job_manager = job_manager
        self.base_url = base_url
        self.name = name or '%s_%d' % (__name__, id(self))
        self.blueprint = Blueprint(self.name)
        self.setup(hook_start_stop)

    def start(self, sanic, loop):
        self.job_manager.start()
        self.mapping = {}

    def stop(self, sanic, loop):
        self.job_manager.stop()
        self.mapping.clear()

    def _response(self, obj, **kwargs):
        return response.json(obj, **kwargs)

    def _report(self, error_msg=None, status_msg=None, status=200):
        # shorthand to generate the standardized responses.
        response = {}
        if error_msg:
            response['error'] = error_msg
        if status_msg:
            response['status'] = status_msg
        return self._response(response, status=status)

    def _error(self, error_msg=None, status_msg=None, status=400):
        return self._report(
            error_msg=error_msg, status_msg=status_msg, status=status)

    def _generate_job_id(self):
        return '%032x' % getrandbits(128)

    def setup(self, hook_start_stop=True):
        blueprint = self.blueprint

        if hook_start_stop:
            blueprint.listener('before_server_start')(self.start)
            blueprint.listener('after_server_stop')(self.stop)

        # The callables must be unbounded functions, given how they must
        # fully be associated with the given blueprint.  The only way to
        # do so is to provide the following functions within the closure
        # formed by this method; instance methods cannot have attributes
        # assigned to it (can only be on the unbound method on the class
        # definition itself).

        @blueprint.route('/execute', methods=['POST'])
        async def execute(request):
            """
            The post end point for starting a job
            """

            try:
                kwargs = self.job_manager.verify_run_kwargs(
                    **dict(request.form))
            except ValueError as e:
                return self._error(error_msg=str(e))

            working_dir = self.job_manager.run(**kwargs)
            job_id = self._generate_job_id()
            self.mapping[job_id] = working_dir
            return self._response(
                {
                    'status': 'created',
                    'location': '/poll/' + job_id,
                },
                headers={
                    'Location': '/poll/' + job_id,
                },
                status=201,
            )

        @blueprint.route('/poll/<job_id:string>')
        async def poll(request, job_id):
            if job_id not in self.mapping:
                return self._error(error_msg='no such job_id', status=404)

            # XXX whenever the API for dealing with the actual Popen
            # objects (i.e. the actual polling) are done it should be
            # used instead
            working_dir = self.mapping[job_id]
            process = self.job_manager.mapping[working_dir]
            status = process.poll()

            # TODO clean this up
            if status is None:
                return self._report(status_msg='running')
            elif status != 0:
                return self._error(
                    status_msg='failure',
                    error_msg='job execution terminated with an error',
                )
            else:
                result = {'status': 'success'}
                result['keys'] = self.job_manager.list_working_dir(
                    working_dir)
                return self._response(result)

        @blueprint.route('/poll/<job_id:string>/<key:string>')
        async def results(request, job_id, key):
            if job_id not in self.mapping:
                return self._error(error_msg='no such job_id', status=404)

            working_dir = self.mapping[job_id]
            target = self.job_manager.lookup_path(working_dir, key)
            if target is None:
                return self._error(
                    error_msg='no such key for job', status=404)
            return await response.file(target)

    def register(self, app):
        app.blueprint(self.blueprint)
