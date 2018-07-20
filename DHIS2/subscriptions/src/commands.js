const _ = require("lodash");
const fs = require("fs");
const util = require('util');
const path = require("path");
const nodemailer = require('nodemailer');
const ejs = require('ejs');
const moment = require('moment');
const child_process = require('child_process');

const helpers = require('./helpers');
const {Dhis2Api} = require('./api');
const {objectsInfo} = require('./objects-info');

const exec = util.promisify(child_process.exec);
const {debug} = helpers;

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

function getNotificationMessages(i18n, event, publicUrl, interpretationsById, usersById, text) {
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
        const bodyText = [
            [
                interpretation.user.displayName,
                `(${interpretation.user.userCredentials.username})`,
                i18n.t(`${event.model}_${event.type}`),
                i18n.t("object_subscribed") + ":",
            ].join(" "),
            interpretationUrl,
            text,
        ].join("\n\n");

        return user.email ? {subject, text: bodyText, recipients: [user.email]} : null;
    };

    const subscribers = interpretation.object.subscribers || [];
    debug(`Object ${interpretation.object.id} subscribers: ${subscribers.join(", ") || "-"}`);

    return _(interpretation.object.subscribers).map(getMessageForUser).compact().value();
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

async function getNewTriggerEvents(api, cacheKey, options, action) {
    const {cacheFilePath, namespace, maxTimeWindow, ignoreCache} = _.defaults(options, {
        cacheFilePath: ".notifications-cache.json",
        namespace: "notifications",
        ignoreCache: false,
        maxTimeWindow: [1, "hour"],
    });
    const cache = JSON.parse(helpers.fileRead(cacheFilePath, JSON.stringify({})));
    const lastTime = ignoreCache ? null : cache[cacheKey];
    const getBucketFromTime = (time) => "ev-month-" + time.format("YYYY-MM");
    const defaultStartTime = moment().subtract(...maxTimeWindow);
    const startTime = lastTime ? moment.max(moment(lastTime), defaultStartTime) : defaultStartTime;
    const endTime = moment();

    debug(`startTime=${startTime}, endTime=${endTime}`);
    const buckets = helpers.getMonthDatesBetween(startTime, endTime).map(getBucketFromTime);
    const eventsInBuckets = await helpers.mapPromise(buckets,
        bucket => api.get(`/dataStore/${namespace}/${bucket}`).catch(err => []));
    const newTriggerEvents = _(eventsInBuckets)
        .flatten()
        .filter(event => moment(event.created) >= startTime && moment(event.created) < endTime)
        .sortBy("created")
        .value();

    const actionResult = await action(newTriggerEvents, startTime, endTime);

    const newCache = {...cache, [cacheKey]: endTime};
    helpers.fileWrite(cacheFilePath, JSON.stringify(newCache, null, 4) + "\n");
    return actionResult;
}

async function getObjectVisualization(api, assets, object, date) {
    const [width, height] = [500, 350];
    const baseParams = {date: moment(date).format("YYYY-MM-DD")};

    switch (object.extraInfo.visualizationType) {
        case "image":
            const imageUrl = `/${object.extraInfo.apiModel}/${object.id}/data.png`;
            debug(`Get image visualization: ${imageUrl}`);
            const imageParams = {...baseParams, width, height};
            const imageData = await api.get(imageUrl, imageParams, {encoding: null});
            const imageFilename = _(["image", object.id, date]).compact().join("-") + ".png";
            const imagePath = path.join(__dirname, imageFilename);
            const uploadTemplate = _.template(assets.upload, templateSettings);
            const uploadCommand = uploadTemplate({files: [imagePath].join(" ")});
            helpers.fileWrite(imagePath, imageData);
            debug(`Upload visualization image: ${uploadCommand}`);
            await exec(uploadCommand);
            debug(`Remove temporal file: ${imagePath}`);
            fs.unlinkSync(imagePath);
            return `<img width="500" height="350" src="${assets.url}/resources/${imageFilename}" />`
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

async function getCachedVisualizationFun(api, assets, events) {
    // Package ejs doesn't support calling async functions, so we preload visualizations beforehand.
    const argsList = _(events)
        .map(event => ({object: event.object, date: event.interpretation.created}))
        .uniqWith(_.isEqual)
        .value();
    // Build array of objects {args: {object, date}, value: html} for all entries.
    const cachedEntries = await helpers.mapPromise(argsList, async (args) => ({
        args: args,
        value: await getObjectVisualization(api, assets, args.object, args.date),
    }));

    return (object, date) => {
        const cachedEntry = cachedEntries.find(entry => _.isEqual(entry.args, {object, date}));

        if (cachedEntry) {
            return cachedEntry.value;
        } else {
            throw new Error(`No cached visualization for objectId=${object.id} and date=${date}`);
        }
    };
}

function getLikes(i18n, interpretation) {
    const nlikes = interpretation.likes || 0;

    switch (nlikes) {
        case 0: return "";
        case 1: return " (" + i18n.t("1_like") + ")";
        default: return " (" + i18n.t("n_likes", {n: nlikes}) + ")";
    }
}

async function sendNewslettersForEvents(api, triggerEvents, startDate, endDate, options) {
    const {dataStore, publicUrl, smtp, locale, assets} = options;
    const translations = helpers.loadTranslations(path.join(__dirname, "i18n"));
    const i18n = translations[locale || "en"];
    const mailer = nodemailer.createTransport(smtp);
    const templatePath = path.join(__dirname, "templates/newsletter.ejs");
    const templateStr = fs.readFileSync(templatePath, "utf8");
    const template = ejs.compile(templateStr, {filename: templatePath});
    const data = await getDataForTriggerEvents(api, triggerEvents);
    
    const eventsByUsers = _(data.events)
        .flatMap(event => _(event.object.subscribers).toArray().map(userId => ({userId, event})).value())
        .groupBy("userId")
        .map((objs, userId) => ({user: data.users[userId], events: objs.map(obj => obj.event)}))
        .filter(({user}) => user.email)
        .value();

    const baseNamespace = {
        startDate,
        endDate,
        i18n: i18n,
        footerText: options.footer.text,
        publicUrl,
        assetsUrl: assets.url,

        routes: {
            object: object => getObjectUrl(object, publicUrl),
            interpretation: interpretation => getInterpretationUrl(interpretation, publicUrl),
            objectImage: object => getObjectImage(object, publicUrl),
        },
        helpers: {
            _,
            getObjectVisualization: await getCachedVisualizationFun(api, assets, data.events),
            getLikes: interpretation => getLikes(i18n, interpretation),
        },
    };

    return helpers.mapPromise(eventsByUsers, async ({user, events}) => {
        const html = await buildNewsletterForUser(i18n, baseNamespace, template, assets, user, events, data);
        const message = {
            subject: i18n.t("newsletter_title"),
            recipients: [user.email],
            html,
        };
        return helpers.sendEmail(mailer, message);
    });
}

async function buildNewsletterForUser(i18n, baseNamespace, template, assets, user, events, data) {
    const interpretationEvents = events.filter(event => event.model === "interpretation");
    const interpretationIds = new Set(interpretationEvents.map(ev => ev.interpretationId));

    const commentEvents = events.filter(event =>
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

    const details_title = i18n.t("n_interpretations_and_comments_on_m_favorites", {
        n: _.size(events),
        m: _(events).map("object").uniqBy("id").size(),
    });

    const namespace = {...baseNamespace, entries, details_title};

    return template(namespace);
}

function loadConfigOptions(configFile) {
    return JSON.parse(helpers.fileRead(configFile));
}

async function sendNotificationsForEvents(api, i18n, triggerEvents, options) {
    const {smtp, publicUrl} = options;
    const mailer = nodemailer.createTransport(smtp);

    const {events, interpretations, users, comments} =
        await getDataForTriggerEvents(api, triggerEvents);

    const messages = _(events).flatMap(event => {
        switch (event.model) {
            case "interpretation":
                const interpretation = interpretations[event.interpretationId];
                return getNotificationMessages(i18n, event, publicUrl, interpretations, users, interpretation.text);
            case "comment":
                const comment = comments[event.commentId];
                return getNotificationMessages(i18n, event, publicUrl, interpretations, users, comment.text);
            default:
                debug(`Unknown event model: ${event.model}`)
                return [];
        }
    }).value();
    debug(`${messages.length} messages to send`);
    await helpers.mapPromise(messages, message => helpers.sendEmail(mailer, message));
}

/* Main functions */

async function sendNotifications(argv) {
    const options = loadConfigOptions(argv.configFile);
    const {api: apiOptions, dataStore, cacheFilePath, locale} = options;
    const api = new Dhis2Api(apiOptions);
    const translations = helpers.loadTranslations(path.join(__dirname, "i18n"));
    const i18n = translations[locale || "en"];
    const triggerOptions = {
        cacheFilePath: cacheFilePath,
        namespace: dataStore.namespace,
        ignoreCache: argv.ignoreCache,
        maxTimeWindow: [1, "hour"],
    };

    return getNewTriggerEvents(api, "notifications", triggerOptions, async (triggerEvents) =>
        sendNotificationsForEvents(api, i18n, triggerEvents, options)
    );
}

async function sendNewsletters(argv) {
    const options = loadConfigOptions(argv.configFile);
    const {cacheFilePath, dataStore, api: apiOptions, locale} = options;
    const api = new Dhis2Api(apiOptions);
    moment.locale(locale || "en");
    const triggerOptions = {
        cacheFilePath: cacheFilePath,
        namespace: dataStore.namespace,
        ignoreCache: argv.ignoreCache,
        maxTimeWindow: [7, "days"],
    };
    return getNewTriggerEvents(api, "newsletter", triggerOptions, async (triggerEvents, startDate, endDate) =>
        sendNewslettersForEvents(api, triggerEvents, startDate, endDate, options)
    );
}

Object.assign(module.exports, {
    sendNotifications,
    sendNewsletters,
});
