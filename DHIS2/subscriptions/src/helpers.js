const bluebird = require("bluebird");
const fs = require("fs");
const util = require("util");
const _ = require('lodash');
const path = require('path');
const properties = require("properties-file");
const moment = require('moment');

let DEBUG_ENABLED = false;

function debug(object) {
    if (!DEBUG_ENABLED) {
        return;
    } else if (typeof object === "string") {
        console.error(`[DEBUG] ${object}`);
    } else {
        console.error(`[DEBUG] ${util.inspect(object, false, null)}`);
    }
}

function setDebug(isEnabled) {
    DEBUG_ENABLED = isEnabled;
}

function mapPromise(values, mapper, {concurrency = 1} = {}) {
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

function getMonthDatesBetween(dateStart, dateEnd) {
    const dateEndOfMonth = dateEnd.clone().endOf("month");
    let currentDate = dateStart.clone();
    let dates = [];

    while (currentDate.isBefore(dateEndOfMonth)) {
       dates.push(currentDate.clone().startOf('month'));
       currentDate.add(1, 'month');
    }

    return dates;
}

function loadTranslations(directory) {
    const templateSettings = {
        interpolate: /{{([\s\S]+?)}}/g,  /* {{variable}} */
    };

    return _(fs.readdirSync(directory))
        .filter(filename => filename.endsWith(".properties"))
        .map(filename => {
            const locale = filename.split(".")[0];
            const obj = properties.parse(fileRead(path.join(directory, filename)));
            const objWithTemplates = _.mapValues(obj, s => _.template(s, templateSettings));
            const t = (key, namespace = {}) =>
                (objWithTemplates[key] || (() => `**${key}**`))(namespace);
            const i18nObj = {t, formatDate: date => moment(date).format('L')};

            return [locale, i18nObj];
        })
        .fromPairs()
        .value();
}

function sendEmail(mailer, {subject, text, html, recipients}) {
    debug("Send email to " + recipients.join(", ") + ": " + subject);
    return mailer.sendMail({to: recipients, subject, text, html});
}


Object.assign(module.exports, {
    debug,
    setDebug,
    mapPromise,
    fileRead,
    fileWrite,
    sendMessage,
    getMonthDatesBetween,
    loadTranslations,
    sendEmail,
});