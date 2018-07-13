#!/usr/bin/env node
const _ = require("lodash");
const fs = require("fs");
const path = require("path");
const properties = require("properties-file");
const nodemailer = require('nodemailer');
const yargs = require('yargs');
const ejs = require('ejs');
const moment = require('moment');

const {Dhis2Api} = require('./api');
const {debug, fileRead, fileWrite, concurrent} = require('./helpers');

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

const translations = loadTranslations("i18n");

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
    return `${publicUrl}/${object.extraInfo.appPath}/index.html?id=${object.id}&interpretationid=${interpretation.id}`;
}

function getObjectUrl(object, publicUrl) {
    return `${publicUrl}/${object.extraInfo.appPath}/index.html?id=${object.id}`;
}

function loadTranslations(directory) {
    const templateSettings = {
        interpolate: /{{([\s\S]+?)}}/g,  /* {{interpolateThisString}} */
    };

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

function getI18nForUser(userId) {
    return translations["en"];
}

function getMessages(event, publicUrl, interpretationsById, usersById, text) {
    const interpretation = interpretationsById[event.interpretationId];
    if (!interpretation)
        return null;
    const interpretationUrl = getInterpretationUrl(interpretation, publicUrl);
    const getMessageForUser = (userId) => {
        const i18n = getI18nForUser(userId);
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
        .map(interpretation => ({...interpretation, object: getObjectFromInterpretation(interpretation)}))
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
    const {dataStore, publicUrl, smtp} = options;
    const api = new Dhis2Api(options.api);
    const mailer = nodemailer.createTransport(smtp);

    return getNewTriggerEvents(api, options, async (triggerEvents) => {
        const data = await getDataForTriggerEvents(api, triggerEvents);

        const messages = _(events).flatMap(event => {
            switch (event.model) {
                case "interpretation":
                    const interpretation = data.interpretations[event.interpretationId];
                    return interpretation ? getMessages(event, publicUrl, data.interpretations, data.users, interpretation.text) : null;
                case "comment":
                    const comment = data.comments[event.commentId];
                    return comment ? getMessages(event, publicUrl, data.interpretations, data.users, comment.text) : null;
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
    const actionResult = action(newTriggerEvents);
    const newCache = {...cache, lastKey: _.last(eventKeys)};

    fileWrite(cacheFilePath, JSON.stringify(newCache) + "\n");
    return actionResult;
}

function getObjectVisualization(object, publicUrl, {date} = {}) {
    const params = _.omitBy({
        date: date ? moment(date).format("YYYY-MM-DD") : null,
    }, _.isNull);
    const queryString = _(params).isEmpty() ? "" : `?${_(params).map((v, k) => `${k}=${v}`).join("&")}`;

    switch (object.extraInfo.visualizationType) {
        case "image":
            const imageUrl = `${publicUrl}/api/${object.extraInfo.apiModel}/${object.id}/data` + queryString;
            return `<img width="500" height="350" src="${imageUrl}" />`
        default:
            return "";
    }
}

async function sendNewsletters(options) {
    const {dataStore, publicUrl, smtp} = options;
    const api = new Dhis2Api(options.api);
    const mailer = nodemailer.createTransport(smtp);

    const i18n = translations["en"];
    moment.locale('en');
    const templatePath = path.join(__dirname, "templates/newsletter.ejs");
    const templateStr = fs.readFileSync(templatePath, "utf8");
    const template = ejs.compile(templateStr, {filename: templatePath});
    const startDate = moment(new Date(2017, 1, 1)).format('L');
    const endDate = moment().format('L');

    const triggerEvents = [
        {
          "type": "update",
          "model": "interpretation",
          "interpretationId": "BR11Oy1Q4yR",
          "created": "2018-07-10T13:52:39Z"
        },
        {
          "type": "insert",
          "model": "interpretation",
          "interpretationId": "h5rF6km1STK",
          "ts": "2018-07-10T13:52:39Z",
          "created": "2018-07-10T13:52:39Z"
        },
        {
          "type": "update",
          "model": "interpretation",
          "interpretationId": "h5rF6km1STK",
          "ts": "2018-07-10T13:52:39Z",
          "created": "2018-07-10T13:52:39Z"
        },
        {
          "model": "comment",
          "type": "update",
          "commentId": "oRmqfmnCLsQ",
          "interpretationId": "BR11Oy1Q4yR",
          "created": "2018-07-10T13:52:39Z"
        },
        {
          "model": "comment",
          "type": "insert",
          "commentId": "xoH3XG0tkQZ",
          "interpretationId": "BR11Oy1Q4yR",
          "created": "2018-07-10T13:52:39Z"
        },
    ];

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
        .sortBy(entry => [
            entry.object.name,
            entry.model !== "interpretation",
        ])
        .value();

    const namespace = {
        _,
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
            getObjectVisualization: (object, date) => getObjectVisualization(object, publicUrl, {date}),
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

function main() {
    yargs
        .help('help', 'Display this help message and exit')
        .option('config-file', {alias: 'c', default: "config.json"})
        .command('send-instant-notifications', 'Send instant email notifications to subscribers', (yargs) => {
            const options = loadConfigOptions(yargs);
            sendNotifications(options);
        })
        .command('send-newsletters', 'Send newsletter emails to subscribers', (yargs) => {
            const options = loadConfigOptions(yargs);
            sendNewsletters(options);
        })
        .demandCommand()
        .strict()
        .argv;
}

if (require.main === module) {
    main();
}
