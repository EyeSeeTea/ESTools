const bluebird = require("bluebird");
const fs = require("fs");
const util = require("util");
const _ = require('lodash');

function debug(object) {
    if (typeof object === "string") {
        console.error(`[DEBUG] ${object}`);
    } else {
        console.error(`[DEBUG] ${util.inspect(object, false, null)}`);
    }
}

function concurrent(values, mapper, {concurrency = 5} = {}) {
    return bluebird.map(values, mapper, {concurrency: concurrency});
}

function fileRead(path, defaultValue) {
    if (fs.existsSync(path)) {
        return fs.readFileSync(path, "utf8");
    } else if (defaultValue !== undefined) {
        return defaultValue;
    } else {
        throw new Error(`File not found: ${path}`);
    }
}

function fileWrite(path, contents) {
    return fs.writeFileSync(path, contents, "utf8");
}

function sendMessage(api, subject, body, recipients) {
    const recipientsByModel = _(recipients)
        .groupBy("type")
        .mapValues(models => models.map(model => ({id: model.id})))
        .value();
    const message = {
        subject: subject,
        text: body,
        users: recipientsByModel.user,
        userGroups: recipientsByModel.userGroup,
        organisationUnits: recipientsByModel.organisationUnit,
    };

    if (_.isEmpty(recipients)) {
        return Promise.resolve();
    } else {
        return api.post("/messageConversations", message);
    }
}

Object.assign(exports, {
    debug,
    concurrent,
    fileRead,
    fileWrite,
    sendMessage,
});