'use strict';

var client = require('repodono/jobs/client');

window.mocha.setup('bdd');


describe('repodono/jobs/client base test cases', function() {

    var logs;

    beforeEach(function() {
        logs = [];
        this.console_log = console.log;
        console.log = function(msg) {
            logs.push(msg);
        };
        this.clock = sinon.useFakeTimers();
        this.server = sinon.fakeServer.create();
        this.server.autoRespond = true;
    });

    afterEach(function() {
        this.server.restore();
        this.clock.restore();
        console.log = this.console_log;
    });

    it('test basic', function() {
        var cli = new client.Client();
        expect(cli.base_url).to.equal('/');
        expect(cli.route_execute).to.equal('execute');

        var cli1 = new client.Client({});
        expect(cli1.base_url).to.equal('/');
        expect(cli1.route_execute).to.equal('execute');

        var cli2 = new client.Client({'base_url': '/some/nested/endpoint'});
        expect(cli2.base_url).to.equal('/some/nested/endpoint');
    });

    it('test default errors', function() {
        var cli = new client.Client();
        expect(cli.execute).to.throw(Error);
        expect(cli.generate_request).to.throw(Error);
        expect(cli.response_job_success).to.throw(Error);
    });

    it('test response_job_created success', function() {
        var cli = new client.Client();
        sinon.spy(cli, 'poll');
        cli.response_job_created({'status': 'created', 'location': '/j/1'});
        expect(logs[0]).to.equal('status: job created');
        expect(cli.poll.calledWith('/j/1')).to.be.true;
    });

    it('test response_job_created failure', function() {
        var cli = new client.Client();
        sinon.spy(cli, 'poll');
        cli.response_job_created({'error': 'some error'});
        expect(logs[0]).to.equal('error: some error');
        expect(cli.poll.called).to.be.false;
    });

    it('test execute failure', function() {
        var cli = new client.Client();
        cli.generate_request = function() {};
        cli.execute();
        this.clock.tick(100);
        expect(logs[0]).to.equal('error: server did not return valid JSON');
    });

});


describe('repodono/jobs/client test case with dummy', function() {

    var logs;
    var response;

    var DummyClient = function(kwargs) {
        client.Client.call(this, kwargs);
        this.success = false;
    };
    DummyClient.prototype = Object.create(client.Client.prototype);
    DummyClient.prototype.constructor = DummyClient;

    DummyClient.prototype.set_status_msg = function(state, msg) {
        logs.push([state, msg]);
    };

    DummyClient.prototype.generate_request = function(xhr) {
        xhr.setRequestHeader('Content-Type', 'application/json');
        return '{"job": "1"}';
    };

    DummyClient.prototype.response_job_success = function(poll_url, keys) {
        this.success = true;
        this.last_poll_url = poll_url;
        this.last_keys = keys;
    };

    beforeEach(function() {
        this.clock = sinon.useFakeTimers();
        this.server = sinon.fakeServer.create();
        this.server.autoRespond = true;

        logs = [];
        response = {
            'status': 200,
            'headers': {'Content-Type': 'application/json'},
            'object': {},
        };

        this.server.respondWith('GET', '/poll/1', function (xhr) {
            xhr.respond(
                response.status, response.headers,
                JSON.stringify(response.object)
            );
        });

        this.server.respondWith('POST', '/execute', function (xhr) {
            xhr.respond(
                200, {'Content-Type': 'application/json'},
                JSON.stringify({'status': 'created', 'location': '/poll/1'})
            );
        });
    });

    afterEach(function() {
        this.server.restore();
        this.clock.restore();
        document.body.innerHTML = "";
    });

    it('test execute default complete', function() {
        var cli = new DummyClient({});
        cli.execute();
        this.clock.tick(100);
        expect(logs[0]).to.deep.equal(['status', 'job created']);
        // XXX emulating running state

        response.object.status = 'running';
        this.clock.tick(100);
        expect(logs[1]).to.deep.equal(['status', 'job running']);
        this.clock.tick(100);
        expect(logs[2]).to.deep.equal(['status', 'job running']);

        response.object.status = 'success';
        response.object.keys = ['key1', 'key2'];
        this.clock.tick(100);
        expect(logs[3]).to.deep.equal(['status', 'success']);
        expect(cli.success).to.be.true;
        expect(cli.last_poll_url).to.equal('/poll/1');
        expect(cli.last_keys).to.deep.equal(['key1', 'key2']);
    });

    it('test execute default error', function() {
        var cli = new DummyClient({});
        cli.execute();
        this.clock.tick(100);
        expect(logs[0]).to.deep.equal(['status', 'job created']);
        // XXX emulating running state
        response.object.error = 'job errored out';
        this.clock.tick(100);
        expect(logs[1]).to.deep.equal(['error', 'job errored out']);
        this.clock.tick(100);
        // no further log entries.
        expect(logs.length).to.equal(2);
        expect(cli.success).to.be.false;
    });

});
