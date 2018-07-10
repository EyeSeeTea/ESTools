#!/usr/bin/env node
const _ = require("lodash");
const fs = require("fs");
const path = require("path");
const properties = require("properties-file");
const nodemailer = require('nodemailer');
const yargs = require('yargs');

const {Dhis2Api} = require('./api');
const {debug, fileRead, fileWrite, concurrent} = require('./helpers');

const objectsInfo = [
    {
        type: "MAP",
        field: "map",
        appPath: "dhis-web-mapping",
    },
    {
        type: "REPORT_TABLE",
        field: "reportTable",
        appPath: "dhis-web-pivot",
    },
    {
        type: "CHART",
        field: "chart",
        appPath: "dhis-web-visualizer",
    },
    {
        type: "EVENT_REPORT",
        field: "eventReport",
        appPath: "dhis-web-event-reports",
    },
    {
        type: "EVENT_CHART",
        field: "eventChart",
        appPath: "dhis-web-event-visualizer",
    },
];

const translations = loadTranslations("i18n");

function getObjectFromInterpretation(interpretation) {
    const matchingInfo = objectsInfo.find(info => info.type === interpretation.type);

    if (!matchingInfo) {
        throw new Error(`Cannot find object type for interpretation ${interpretation.id}`);
    } else {
        return interpretation[matchingInfo.field];
    }
}

function getInterpretationUrl(publicUrl, interpretation) {
    const matchingInfo = objectsInfo.find(info => info.type === interpretation.type);

    if (!matchingInfo) {
        throw new Error(`Cannot find object type for interpretation ${interpretation.id}`);
    } else {
        const object = getObjectFromInterpretation(interpretation);
        return `${publicUrl}/${matchingInfo.appPath}/index.html?id=${object.id}&interpretationid=${interpretation.id}`;
    }
}

function loadTranslations(directory) {
    return _(fs.readdirSync(path.join(__dirname, directory)))
        .filter(filename => filename.endsWith(".properties"))
        .map(filename => [
            filename.split(".")[0],
            properties.parse(fileRead(path.join(__dirname, directory, filename))),
        ])
        .fromPairs()
        .value();
}

function getMessages(event, publicUrl, interpretationsById, usersById, text) {
    const interpretation = interpretationsById[event.interpretationId];
    const interpretationUrl = getInterpretationUrl(publicUrl, interpretation);
    const object = getObjectFromInterpretation(interpretation);
    const i18n = translations["en"]; // Currently there is no way to get user setting keyUiLocale
    const getMessageForUser = (userId) => {
        const user = usersById[userId];
        const subject = [
            interpretation.user.displayName,
            i18n[`${event.model}_${event.type}`],
        ].join(" ");
        const body = [
            [
                interpretation.user.displayName,
                `(${interpretation.user.userCredentials.username})`,
                i18n[`${event.model}_${event.type}`],
                i18n.object_subscribed + ":",
            ].join(" "),
            interpretationUrl,
            text,
        ].join("\n\n");

        return {subject, body, recipients: [user.email]};
    };

    return _(object.subscribers).toArray().map(getMessageForUser).value();
}

function sendEmail(mailer, {subject, body, recipients}) {
    debug("Send email to " + recipients.join(", ") + ": " + subject);
    mailer.sendMail({to: recipients, subject, text: body});
}

function sendNotifications(options) {
    const {dataStore, publicUrl, smtp} = options;
    const api = new Dhis2Api(options.api);
    const mailer = nodemailer.createTransport(smtp);

    return getNewEvents(api, options, async (events) => {
        const interpretationIds = events.map(event => event.interpretationId);
        const userField = "user[id,displayName,userCredentials[username]]";
        const objectModelFields = objectsInfo.map(info => `${info.field}[` + [
            "id",
            "name",
            "subscribers",
            userField,
        ].join(",") + "]");
        const {interpretations} = await api.get("/interpretations/", {
            paging: false,
            filter: `id:in:[${interpretationIds.join(',')}]`,
            fields: [
                "id",
                "text",
                "type",
                userField,
                `comments[id,text,${userField}]`,
                ...objectModelFields,
            ].join(","),
        });
        const {users} = await api.get("/users/", {
            paging: false,
            fields: ["id", "email"].join(","),
        });
        const interpretationsById = _.keyBy(interpretations, "id");
        const commentsById = _(interpretations).flatMap("comments").keyBy("id").value();
        const usersById = _.keyBy(users, "id");

        const messages = _(events).flatMap(event => {
            switch (event.model) {
                case "interpretation":
                    const interpretation = interpretationsById[event.interpretationId];
                    return getMessages(event, publicUrl, interpretationsById, usersById, interpretation.text);
                case "comment":
                    const comment = commentsById[event.commentId];
                    return getMessages(event, publicUrl, interpretationsById, usersById, comment.text);
                default:
                    debug(`Unknown event model: ${event.model}`)

            }
        }).value();

        return messages.map(message => sendEmail(mailer, message));
    });
}

async function getNewEvents(api, options, action) {
    const {cacheFilePath, dataStore} = options;
    const initialCache = {lastKey: null};
    const cache = JSON.parse(fileRead(cacheFilePath, JSON.stringify(initialCache)));
    const allKeys = await api.get(`/dataStore/${dataStore.namespace}`);
    const eventKeys = _(allKeys).filter(key => key.startsWith(dataStore.keyPrefix)).sortBy().value();

    let newEventKeys;
    if (cache.lastKey) {
        const splitIndex = _(eventKeys).findIndex(key => key > cache.lastKey);
        newEventKeys = splitIndex >= 0 ? eventKeys.slice(splitIndex) : [];
    } else {
        newEventKeys = eventKeys;
    }

    const newEvents = await concurrent(newEventKeys,
        eventKey => api.get(`/dataStore/${dataStore.namespace}/${eventKey}`));
    const actionResult = action(newEvents);
    const newCache = {...cache, lastKey: _.last(eventKeys)};

    fileWrite(cacheFilePath, JSON.stringify(newCache) + "\n");
    return actionResult;
}

function sendNewsletters() {
    console.log("TODO");
}

function main() {
    yargs
        .help('help', 'Show help message')
        .option('config-file', {
           alias: 'c',
           default: "config.json",
        })
        .command('send-instant-notifications', 'Send instant email notifications', (yargs) => {
            const options = JSON.parse(fileRead(yargs.argv.configFile));
            sendNotifications(options);
        })
        .command('send-newsletters', 'Send newsletter emails', (args) => {
            const options = JSON.parse(fileRead(yargs.argv.configFile));
            sendNewsletters(options);
        })
        .demandCommand()
        .strict()
        .argv;
}

if (require.main === module) {
    main();
}
