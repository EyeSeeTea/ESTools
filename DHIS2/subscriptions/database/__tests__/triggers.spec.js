const util = require('util');
const fs = require('fs');
const path = require('path');
const child_process = require('child_process');
const exec = util.promisify(child_process.exec);
const moment = require('moment');
const _ = require('lodash');

const helpers = require('../../src/helpers');
const {Dhis2Api} = require('../../src/api.js');

helpers.DEBUG_ENABLED = false;

function setup() {
  const configFile = process.env.CONFIG_FILE;
  const database = process.env.DATABASE;

  if (!database) {
    throw new Error("Set environment: DATABASE=database");
  } else if (!configFile) {
    throw new Error("Set environment: CONFIG_FILE=path/to/config.json");
  } else {
    const configOptions = JSON.parse(fs.readFileSync(configFile));
    const api = new Dhis2Api(configOptions.api);
    return {api, database};
  }
}

async function createInterpretation(api) {
  const bucket = "ev-month-" + moment().format("YYYY-MM");
  const response = await api.post("/interpretations/chart/R9A0rvAydpn",
    {body: "My interpretation", headers: {"content-type": "text/plain"}, resolveWithFullResponse: true});
  const interpretationPath = response.headers.location;
  const interpretationId = _.last(interpretationPath.split("/"));
  return {id: interpretationId, path: interpretationPath, bucket};
}

async function createComment(api, interpretation) {
  const bucket = "ev-month-" + moment().format("YYYY-MM");
  const response = await api.post(`/interpretations/${interpretation.id}/comments`,
    {body: "My comment", headers: {"content-type": "text/plain"}, resolveWithFullResponse: true});
  const commentPath = response.headers.location;
  const commentId = _.last(commentPath.split("/"));
  return {id: commentId, path: commentPath, bucket};
}

describe("Database triggers", () => {
  let config = setup();
  let interpretation;
  let comment;

  beforeAll(() => {
    const triggersFile = path.join(__dirname, "..", "triggers.sql");
    return exec(`psql -v ON_ERROR_STOP=1 -f "${triggersFile}" ${config.database}`);
  });

  describe("interpretation creation", () => {
    beforeAll(async () => {
      interpretation = await createInterpretation(config.api);
    });

    afterAll(() => {
      api.delete(interpretation.path);
    });

    it("creates an event", async () => {
      const events = await config.api.get(`/dataStore/notifications/${interpretation.bucket}`);
      const event = _.last(events);
      expect(event).toEqual(expect.objectContaining({
          type: "insert",
          model: "interpretation",
          interpretationId: interpretation.id,
      }));
    });
  });

  describe("interpretation update", () => {
    beforeAll(async () => {
      interpretation = await createInterpretation(config.api);
      await config.api.put(`/interpretations/${interpretation.id}`,
        {body: "My edited interpretation", headers: {"content-type": "text/plain"}});
    });

    afterAll(() => {
      api.delete(interpretation.path);
    });

    it("creates an event", async () => {
      const events = await config.api.get(`/dataStore/notifications/${interpretation.bucket}`);
      const event = _.last(events);
      expect(event).toEqual(expect.objectContaining({
          type: "update",
          model: "interpretation",
          interpretationId: interpretation.id,
      }));
    });
  });

  describe("comment creation", () => {
    beforeAll(async () => {
      interpretation = await createInterpretation(config.api);
      comment = await createComment(config.api, interpretation);
    });

    afterAll(() => {
      api.delete(interpretation.path);
    });

    it("creates an event", async () => {
      const events = await config.api.get(`/dataStore/notifications/${interpretation.bucket}`);
      const event = _.last(events);
      expect(event).toEqual(expect.objectContaining({
          type: "insert",
          model: "comment",
          interpretationId: interpretation.id,
          commentId: comment.id,
      }));
    });
  });

  describe("comment update", () => {
    beforeAll(async () => {
      interpretation = await createInterpretation(config.api);
      comment = await createComment(config.api, interpretation);
      const response = await config.api.put(`/interpretations/${interpretation.id}/comments/${comment.id}`,
        {body: "My edited comment", headers: {"content-type": "text/plain"}, resolveWithFullResponse: true});
    });

    afterAll(() => {
      api.delete(interpretation.path);
    });

    it("creates an event", async () => {
      const events = await config.api.get(`/dataStore/notifications/${interpretation.bucket}`);
      const event = _.last(events);
      expect(event).toEqual(expect.objectContaining({
          type: "update",
          model: "comment",
          interpretationId: interpretation.id,
          commentId: comment.id,
      }));
    });
  });
});
