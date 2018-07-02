#!/usr/bin/env node
const _ = require("lodash");
const fs = require("fs");

const {Dhis2Api} = require('./api');
const {
    debug,
    merge,
    fileRead,
    fileWrite,
    getOptionsFromArgsAndConfigFile,
    concurrent,
} = require('./helpers');

function getObjectUrl(interpretation) {
    return '/TODO';
}

function sendNotifications(options) {
    const {dataStore} = options;
    const api = new Dhis2Api(options.api);

    return getNewEvents(api, options, async (events) => {
        // TODO: get subscribers for those objects -> send email (html?)
        debug(events)
        debug(events.map(event => event.interpretationId))
        const interpretations = await concurrent(events,
            event => api.get(`/interpretations/${event.interpretationId}`));
        debug({events, interpretations});
        const objects = await concurrent(interpretations,
            interpretation => api.get(getObjectUrl(interpretation)));
    });
}

async function getNewEvents(api, options, action) {
    const {clearCache, cacheFilePath, dataStore} = options;
    const emptyCache = {lastKey: null};
    const cache = clearCache ? {} : JSON.parse(fileRead(cacheFilePath, JSON.stringify(emptyCache)));
    const allKeys = await api.get(`/dataStore/${dataStore.namespace}`);
    const eventKeys = _(allKeys)
        .filter(key => key.startsWith(dataStore.keyPrefix))
        .sortBy()
        .value();
    let newEventKeys;
    if (cache.lastKey) {
        const splitIndex = _(eventKeys).findIndex(key => key > cache.lastKey);
        newEventKeys = splitIndex >= 0 ? eventKeys.slice(splitIndex) : [];
    } else {
        newEventKeys = eventKeys;
    }
    debug({cache, eventKeys, newEventKeys});

    const newEvents = await concurrent(newEventKeys,
        eventKey => api.get(`/dataStore/${dataStore.namespace}/${eventKey}`));
    const actionResult = action(newEvents);

    const newCache = merge(cache, {lastKey: _.last(eventKeys)});
    fileWrite(cacheFilePath, JSON.stringify(newCache) + "\n");
    debug({newCache});

    return actionResult;
}

if (require.main === module) {
    const options = getOptionsFromArgsAndConfigFile("notifications-config.json");
    sendNotifications(options);
}
