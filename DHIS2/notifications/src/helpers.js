const bluebird = require("bluebird");
const fs = require("fs");
const util = require("util");
const nconf = require('nconf');

function debug(object) {
    if (typeof object === "string") {
        console.error(`[DEBUG] ${object}`);
    } else {
        console.error(`[DEBUG] ${util.inspect(object)}`);
    }
}

function concurrent(values, mapper, {concurrency = 5} = {}) {
    return bluebird.map(values, mapper, {concurrency: concurrency});
}

function getOptionsFromArgsAndConfigFile(configPath) {
    const config = nconf.argv().file({file: configPath});
    return config.get();
}

function fileRead(path, defaultValue) {
    if (fs.existsSync(path)) {
        return fs.readFileSync(path, "utf8");
    } else if (defaultValue !== undefined) {
        return defaultValue;
    } else {
        throw new Error(`File not found: ${defaultValue}`);
    }
}

function fileWrite(path, contents) {
    return fs.writeFileSync(path, contents, "utf8");
}

function merge(obj1, obj2) {
    return Object.assign({}, obj1, obj2);
}

Object.assign(exports, {debug, concurrent, getOptionsFromArgsAndConfigFile, fileRead, fileWrite, merge});