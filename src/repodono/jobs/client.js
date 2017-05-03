'use strict';

var default_kwargs = {
    'base_url': '/',
    'poll_timeout': 100,
    'route_execute': 'execute',
    'route_poll': 'poll',
};

var Client = function(kwargs) {
    for (var key in default_kwargs) {
        this[key] = kwargs[key] || default_kwargs[key];
    }
};


Client.prototype.set_status_msg = function(state, msg) {
    console.log(state + ': ' + msg);
};


Client.prototype.raw_request = function(before, after) {
    var self = this;
    var xhr = new XMLHttpRequest();
    xhr.onreadystatechange = function() {
        if (xhr.readyState == XMLHttpRequest.DONE) {
            try {
                var obj = JSON.parse(xhr.responseText);
            }
            catch (e) {
                self.set_status_msg(
                    'error', 'server did not return valid JSON');
                return false;
            }
            after.apply(self, [obj]);
        }
    };
    xhr.send(before(xhr));
};


Client.prototype.generate_request = function(xhr) {
    throw Error('NotImplementedError');
};


Client.prototype.response_job_created = function(obj) {
    if (obj.status == 'created') {
        this.set_status_msg('status', 'job created');
        this.poll(obj.location);
        return true;
    }
    // XXX error can be undefined...
    this.set_status_msg('error', obj.error);
};


Client.prototype.execute = function() {
    var self = this;
    var execute_url = this.base_url + this.route_execute;
    var before = function (xhr) {
        xhr.open('POST', execute_url, true);
        return self.generate_request(xhr);
    };

    this.raw_request(before, this.response_job_created);
};


Client.prototype.poll = function(poll_url) {
    /*
    Legacy polling behavior.
    */

    var self = this

    var before = function(xhr) {
        xhr.open('GET', poll_url, true);
    };

    var after = function(obj) {
        if (obj.error) {
            self.set_status_msg('error', obj.error);
            return false;
        }
        else if (obj.status == 'running') {
            _poll();
            self.set_status_msg('status', 'job running');
        }
        else if (obj.status == 'success') {
            self.set_status_msg('status', 'success');
            self.response_job_success(poll_url, obj.keys)
        }
    };

    var _poll = function() {
        setTimeout(function() {
            self.raw_request(before, after);
        }, self.poll_timeout);
    };

    _poll();
};


Client.prototype.response_job_success = function(poll_url, keys) {
    throw Error('NotImplementedError');
};


exports.Client = Client;
