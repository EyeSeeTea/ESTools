const request = require("request-promise");
const basicAuth = require("basic-authorization-header");
const { debug } = require('./helpers');
const util = require("util");
const { merge } = require('lodash/fp');

class Dhis2Api {
    constructor(options) {
        const {url, auth: {username, password}} = options;
        this.baseUrl = url;
        this.headers = {
            "authorization": basicAuth(username, password),
            "accept": "application/json",
            "content-type": "application/json",
        };
    }

    _getUrl(path) {
        return this.baseUrl.replace(/\/+$/, '') + "/" + path.replace(/^\/+/, '');
    }

    get(path, params = {}, options = {}) {
        const url = this._getUrl(path);
        debug(`GET ${url}`);

        return request({
            method: "GET",
            url: url,
            qs: params,
            headers: this.headers,
            body: {},
            json: true,
            ...options,
        });
    }

    post(path, options = {}) {
        const url = this._getUrl(path);
        debug(`POST ${url}`);
        const defaultOptions = {
            method: "POST",
            url: url,
            body: null,
            headers: this.headers,
            json: true,
        };
        const fullOptions = merge(defaultOptions, options);
        return request(fullOptions);
    }

    put(path, options = {}) {
        const url = this._getUrl(path);
        debug(`PUT ${url}`);
        const defaultOptions = {
            method: "PUT",
            url: url,
            body: null,
            headers: this.headers,
            json: true,
        };
        const fullOptions = merge(defaultOptions, options);
        return request(fullOptions);
    }

    patch(path, options = {}) {
        const url = this._getUrl(path);
        debug(`PATCH ${url}`);
        const defaultOptions = {
            method: "PATCH",
            url: url,
            body: null,
            headers: this.headers,
            json: true,
        };
        const fullOptions = merge(defaultOptions, options);
        return request(fullOptions);
    }

    delete(path, options = {}) {
        const url = this._getUrl(path);
        debug(`DELETE ${url}`);

        return request({
            method: "DELETE",
            url: url,
            headers: this.headers,
            ...options,
        });
    }
}

//export default Dhis2Api;
exports.Dhis2Api = Dhis2Api;