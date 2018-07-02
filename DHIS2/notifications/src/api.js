const request = require("request-promise");
const basicAuth = require("basic-authorization-header");

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

    get(path, options = {}) {
        const url = this._getUrl(path);
        return request({
            method: "GET",
            url: url,
            qs: options,
            headers: this.headers,
            json: true,
        });
    }
}

//export default Dhis2Api;
exports.Dhis2Api = Dhis2Api;