#!/usr/bin/env node
const _ = require("lodash");
const fs = require("fs");
const ejs = require('ejs');

const {Dhis2Api} = require('./api');
const {debug, getOptionsFromArgsAndConfigFile} = require('./helpers');

class Dhis2Newsletter {
    constructor(options) {
        this.api = new Dhis2Api(options.api);
    }

    async run() {
        const users = await this.api.get("/users", {filter: "displayName:eq:John Kamara"});
        console.log(users)

        const templateStr = fs.readFileSync("templates/newsletter.ejs", "utf8");
        const template = ejs.compile(templateStr, {});
        const html = template({title: "My title"});
        console.log(html);
    }
}

if (require.main === module) {
    const options = getOptionsFromArgsAndConfigFile("config.json");
    new Dhis2Newsletter(options).run();
}
