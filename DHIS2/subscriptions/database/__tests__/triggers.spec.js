const util = require('util');
const fs = require('fs');
const path = require('path');
const child_process = require('child_process');
const exec = util.promisify(child_process.exec);
const moment = require('moment');
const _ = require('lodash');

const {Dhis2Api} = require('../../src/api.js');
const {createInterpretation, createComment, updateInterpretation, updateComment} =
  require('../../src/test-helpers.js');

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

const objectPath = "chart/R9A0rvAydpn";

describe("Database triggers", () => {
  let config = setup();
  let interpretation, comment;

  beforeAll(() => {
    const triggersFile = path.join(__dirname, "..", "triggers.sql");
    return exec(`psql -v ON_ERROR_STOP=1 -f "${triggersFile}" ${config.database}`);
  });

  describe("interpretation creation", () => {
    beforeAll(async () => {
      interpretation = await createInterpretation(config.api, objectPath);
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
      interpretation = await createInterpretation(config.api, objectPath);
      await updateInterpretation(config.api, interpretation, "My edited interpretation");
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
      interpretation = await createInterpretation(config.api, objectPath);
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
      interpretation = await createInterpretation(config.api, objectPath);
      comment = await createComment(config.api, interpretation);
      await updateComment(config.api, interpretation, comment, "My edited comment");
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
