#!/usr/bin/env node
const _ = require("lodash");
const fs = require("fs");
const util = require('util');
const path = require("path");
const properties = require("properties-file");
const nodemailer = require('nodemailer');
const yargs = require('yargs');
const ejs = require('ejs');
const moment = require('moment');
const child_process = require('child_process');

const {Dhis2Api} = require('./api');
const {debug, fileRead, fileWrite, concurrent} = require('./helpers');

const exec = util.promisify(child_process.exec);

const objectsInfo = [
    {
        type: "MAP",
        field: "map",
        appPath: "dhis-web-mapping",
        visualizationType: "image",
        apiModel: "maps",
    },
    {
        type: "REPORT_TABLE",
        field: "reportTable",
        appPath: "dhis-web-pivot",
        apiModel: "reportTables",
        visualizationType: "html",
    },
    {
        type: "CHART",
        field: "chart",
        appPath: "dhis-web-visualizer",
        apiModel: "charts",
        visualizationType: "image",
    },
    {
        type: "EVENT_REPORT",
        field: "eventReport",
        appPath: "dhis-web-event-reports",
        apiModel: "eventReports",
        visualizationType: "none",
    },
    {
        type: "EVENT_CHART",
        field: "eventChart",
        appPath: "dhis-web-event-visualizer",
        apiModel: "eventCharts",
        visualizationType: "image",
    },
];

const templateSettings = {
    interpolate: /{{([\s\S]+?)}}/g,  /* {{variable}} */
};

function getObjectFromInterpretation(interpretation) {
    const matchingInfo = objectsInfo.find(info => info.type === interpretation.type);

    if (!matchingInfo) {
        throw new Error(`Cannot find object type for interpretation ${interpretation.id}`);
    } else {
        const object = interpretation[matchingInfo.field];
        return {...object, extraInfo: matchingInfo};
    }
}

function getInterpretationUrl(interpretation, publicUrl) {
    const object = interpretation.object;
    const {appPath} = object.extraInfo;
    return `${publicUrl}/${appPath}/index.html?id=${object.id}&interpretationid=${interpretation.id}`;
}

function getObjectUrl(object, publicUrl) {
    return `${publicUrl}/${object.extraInfo.appPath}/index.html?id=${object.id}`;
}

function loadTranslations(directory) {
    return _(fs.readdirSync(path.join(__dirname, directory)))
        .filter(filename => filename.endsWith(".properties"))
        .map(filename => {
            const locale = filename.split(".")[0];
            const obj = properties.parse(fileRead(path.join(__dirname, directory, filename)));
            const objWithTemplates = _.mapValues(obj, s => _.template(s, templateSettings));
            const t = (key, namespace = {}) =>
                (objWithTemplates[key] || (() => `**${key}**`))(namespace);
            const i18nObj = {t, formatDate: date => moment(date).format('L')};

            return [locale, i18nObj];
        })
        .fromPairs()
        .value();
}

function getMessages(i18n, event, publicUrl, interpretationsById, usersById, text) {
    const interpretation = interpretationsById[event.interpretationId];
    if (!interpretation)
        return null;

    const interpretationUrl = getInterpretationUrl(interpretation, publicUrl);
    const getMessageForUser = (userId) => {
        const user = usersById[userId] || {};
        const subject = [
            interpretation.user.displayName,
            i18n.t(`${event.model}_${event.type}`),
        ].join(" ");
        const body = [
            [
                interpretation.user.displayName,
                `(${interpretation.user.userCredentials.username})`,
                i18n.t(`${event.model}_${event.type}`),
                i18n.t("object_subscribed") + ":",
            ].join(" "),
            interpretationUrl,
            text,
        ].join("\n\n");

        return user.email ? {subject, body, recipients: [user.email]} : null;
    };

    return _(interpretation.object.subscribers).toArray().map(getMessageForUser).compact().value();
}

function sendEmail(mailer, {subject, body, recipients}) {
    debug("Send email to " + recipients.join(", ") + ": " + subject);
    mailer.sendMail({to: recipients, subject, text: body});
}

async function getDataForTriggerEvents(api, triggerEvents) {
    const interpretationIds = triggerEvents.map(event => event.interpretationId);
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
            "created",
            "likes",
            userField,
            `comments[id,text,${userField}]`,
            ...objectModelFields,
        ].join(","),
    });

    const {users} = await api.get("/users/", {
        paging: false,
        fields: ["id", "email"].join(","),
    });

    const interpretationsByIdWithObject = _(interpretations)
        .map(interpretation =>
            ({...interpretation, object: getObjectFromInterpretation(interpretation)}))
        .keyBy("id")
        .value();

    const commentsById = _(interpretations).flatMap("comments").keyBy("id").value();

    const getEventModel = event => {
        switch (event.model) {
            case "interpretation": return interpretationsByIdWithObject[event.interpretationId];
            case "comment": return commentsById[event.commentId];
            default: throw new Error("Unknown event model", event);
        }
    };

    const events = _(triggerEvents)
        // Get only events with existing interpretation and comments
        .filter(event => interpretationsByIdWithObject[event.interpretationId])
        .filter(event => !event.commentId || commentsById[event.commentId])
        // Take only 1 event over the same interpretation/comment (preference for creation events)
        .groupBy(event => [event.interpretationId, event.commentId].join("-"))
        .map((eventsInGroups, key) =>
            _(eventsInGroups).sortBy(event => event.type !== "created").first()
        )
        // Build a rich event object
        .map(event => {
            const interpretation = interpretationsByIdWithObject[event.interpretationId];
            return {
                ...event,
                user: getEventModel(event).user,
                interpretation: interpretation,
                object: interpretation.object,
                comment: event.commentId ? commentsById[event.commentId] : null,
            };
        })
        .value();
        
    return {
        events: events,
        interpretations: interpretationsByIdWithObject,
        comments: commentsById,
        objects: _(interpretationsByIdWithObject).values().map("object").keyBy("id").value(),
        users: _.keyBy(users, "id"),
    };
}

function sendNotifications(options) {
    const {dataStore, publicUrl, smtp, locale} = options;
    const api = new Dhis2Api(options.api);
    const mailer = nodemailer.createTransport(smtp);
    const translations = loadTranslations("i18n");
    const i18n = translations[locale || "en"];

    return getNewTriggerEvents(api, options, async (triggerEvents) => {
        const {events, interpretations, users, comments} =
            await getDataForTriggerEvents(api, triggerEvents);

        const messages = _(events).flatMap(event => {
            switch (event.model) {
                case "interpretation":
                    const interpretation = interpretations[event.interpretationId];
                    return getMessages(i18n, event, publicUrl, interpretations, users, interpretation.text);
                case "comment":
                    const comment = comments[event.commentId];
                    return getMessages(i18n, event, publicUrl, interpretations, users, comment.text);
                default:
                    debug(`Unknown event model: ${event.model}`)
                    return [];
            }
        }).value();
        debug(`${messages.length} messages to send`);

        return messages.map(message => sendEmail(mailer, message));
    });
}

async function getNewTriggerEvents(api, options, action) {
    const {cacheFilePath, dataStore} = options;
    const initialCache = {lastKey: null};
    const cache = JSON.parse(fileRead(cacheFilePath, JSON.stringify(initialCache)));
    const allKeys = await api.get(`/dataStore/${dataStore.namespace}`);

    // TODO: Group events by day or week.

    const eventKeys = _(allKeys).filter(key => key.startsWith(dataStore.keyPrefix)).sortBy().value();

    let newEventKeys;
    if (cache.lastKey) {
        const splitIndex = _(eventKeys).findIndex(key => key > cache.lastKey);
        newEventKeys = splitIndex >= 0 ? eventKeys.slice(splitIndex) : [];
    } else {
        newEventKeys = eventKeys;
    }

    const newTriggerEvents = await concurrent(newEventKeys,
        eventKey => api.get(`/dataStore/${dataStore.namespace}/${eventKey}`));
    const actionResult = await action(newTriggerEvents);
    const newCache = {...cache, lastKey: _.last(eventKeys)};

    fileWrite(cacheFilePath, JSON.stringify(newCache) + "\n");
    return actionResult;
}

async function getObjectVisualization(api, assets, object, options = {}) {
    const {width, height, date} = _.defaults(options, {
        width: 500,
        height: 350,
        date: null,
    });

    if (!assets)
        throw new Error("No assets configuration");

    const baseParams = date ? {date: moment(date).format("YYYY-MM-DD")} : {};
    switch (object.extraInfo.visualizationType) {
        case "image":
            const imageUrl = `/${object.extraInfo.apiModel}/${object.id}/data.png`;
            debug(`Get image visualization: ${imageUrl}`);
            const imageParams = {...baseParams, width, height};
            const imageData = await api.get(imageUrl, imageParams, {encoding: null});
            const imageFilename = _(["image", object.id, date]).compact().join("-") + ".png";
            const uploadTemplate = _.template(assets.upload, templateSettings);
            const uploadCommand = uploadTemplate({files: [imageFilename].join(" ")});
            fileWrite(imageFilename, imageData);
            debug(`Upload visualization image: ${uploadCommand}`);
            await exec(uploadCommand);
            return `<img width="500" height="350" src="${assets.url}/${imageFilename}" />`
        case "html":
            const tableUrl = `/${object.extraInfo.apiModel}/${object.id}/data.html`;
            debug(`Get table visualization: ${tableUrl}`);
            const tableHtml = await api.get(tableUrl, baseParams);
            return `<div style="display: block; overflow: auto; height: ${height}px">${tableHtml}</div>`;
        case "none":
            return "";
        default:
            throw new Error(`Unsupported visualization type: ${object.extraInfo.visualizationType}`);
    }
}

async function getCachedVisualizationFun(api, assets, entries) {
    // Package ejs doesn't support calling async functions, so we preload visualizations beforehand.
    const getArgsForEntry = entry => {
        switch (entry.model) {
            case "interpretation":
                return entry.events
                    .map(event => ({object: entry.object, date: event.interpretation.created}));
            case "comment":
                return [{object: entry.object, date: entry.interpretation.created}];
        }
    };
    const argsList = _(entries).flatMap(getArgsForEntry).uniqWith(_.isEqual).value();
    // Build array of objects {args: {object, date}, value: html} for all entries.
    const cachedEntries = await concurrent(argsList, async (args) => ({
        args: args,
        value: await getObjectVisualization(api, assets, args.object, {date: args.date}),
    }));

    return (object, date) => {
        const cachedEntry = cachedEntries.find(entry => _.isEqual(entry.args, {object, date}));

        if (cachedEntry) {
            return cachedEntry.value;
        } else {
            debug({cachedEntries});
            throw new Error(`No cached visualization for objectId=${object.id} and date=${date}`);
        }
    };
}

async function sendNewsletters(options, api, triggerEvents) {
    const {dataStore, publicUrl, smtp, locale, assets} = options;
    moment.locale(locale);
    const translations = loadTranslations("i18n");
    const i18n = translations[locale || "en"];

    const mailer = nodemailer.createTransport(smtp);
    const templatePath = path.join(__dirname, "templates/newsletter.ejs");
    const templateStr = fs.readFileSync(templatePath, "utf8");
    const template = ejs.compile(templateStr, {filename: templatePath});
    const startDate = moment(new Date(2017, 1, 1)).format('L'); // TODO
    const endDate = moment().format('L');

    const data = await getDataForTriggerEvents(api, triggerEvents);
    const interpretationEvents = data.events.filter(event => event.model === "interpretation");
    const interpretationIds = new Set(interpretationEvents.map(ev => ev.interpretationId));
    const commentEvents = data.events.filter(event =>
        event.model === "comment" && interpretationIds.has(event.interpretationId));

    const interpretationEntries = _(interpretationEvents)
        .groupBy(event => event.object.id)
        .map((interpretationEventsForObject, objectId) => ({
            model: "interpretation",
            object: data.objects[objectId],
            events: _.sortBy(interpretationEventsForObject, "created"),
        }))
        .value();

    const commentEntries = _(commentEvents)
        .groupBy(event => event.interpretation.id)
        .map((commentEventsForInterpretation, interpretationId) => {
            const interpretation = data.interpretations[interpretationId];
            return {
                model: "comment",
                object: data.objects[interpretation.object.id],
                interpretation: interpretation,
                events: _.sortBy(commentEventsForInterpretation, "created"),
            }
        })
        .value();

    const entries = _(interpretationEntries)
        .concat(commentEntries)
        .sortBy(entry => [entry.object.name, entry.model !== "interpretation"])
        .value();

    const getCachedVisualization = await getCachedVisualizationFun(api, assets, entries);

    const namespace = {
        startDate,
        endDate,
        data,
        entries,
        i18n: i18n,
        routes: {
            object: object => getObjectUrl(object, publicUrl),
            interpretation: interpretation => getInterpretationUrl(interpretation, publicUrl),
            objectImage: object => getObjectImage(object, publicUrl),
        },
        helpers: {
            _,
            getObjectVisualization: getCachedVisualization,
            getLikes: interpretation => {
                const nlikes = interpretation.likes || 0;
                switch (nlikes) {
                    case 0: return "";
                    case 1: return " (" + i18n.t("1_like") + ")";
                    default: return " (" + i18n.t("n_likes", {n: nlikes}) + ")";
                }
            },
        },
    };
    const html = template(namespace);
    console.log(html);
}

function loadConfigOptions(yargs) {
    return JSON.parse(fileRead(yargs.argv.configFile));
}

async function main() {
    yargs
        .help('help', 'Display this help message and exit')
        .option('config-file', {alias: 'c', default: "config.json"})
        .command('send-instant-notifications', 'Send instant email notifications to subscribers', (yargs) => {
            const options = loadConfigOptions(yargs);
            sendNotifications(options);
        })
        .command('send-newsletters', 'Send newsletter emails to subscribers', async (yargs) => {
            const options = loadConfigOptions(yargs);
            const api = new Dhis2Api(options.api);
            await getNewTriggerEvents(api, options, async (triggerEvents) => {
                sendNewsletters(options, api, triggerEvents);
            });
        })
        .demandCommand()
        .strict()
        .argv;
}

if (require.main === module) {
    main();
}
