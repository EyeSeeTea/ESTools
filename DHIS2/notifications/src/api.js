const request = require("request-promise");
const basicAuth = require("basic-authorization-header");
const { debug } = require('./helpers');
const util = require("util");

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

    get(path, params = null, options = {}) {
        const url = this._getUrl(path);
        debug(`GET ${url}`);

        return request({
            method: "GET",
            url: url,
            qs: params,
            headers: this.headers,
            json: true,
            ...options,
        });
    }

    post(path, data) {
        const url = this._getUrl(path);
        debug(`POST ${url}`);
        
        return request({
            method: POST,
            url: url,
            body: data,
            headers: this.headers,
            json: true,
        });
    }
}

//export default Dhis2Api;
exports.Dhis2Api = Dhis2Api;