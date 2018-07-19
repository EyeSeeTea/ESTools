const commands = require('../commands');
const fs = require('fs');
const moment = require('moment');
const _ = require('lodash');

const helpers = require('../../src/helpers.js');
const {Dhis2Api} = require('../../src/api.js');
const {createInterpretation, createComment, updateInterpretation, updateComment} =
  require('../../src/test-helpers.js');

function setup() {
  const configFile = process.env.CONFIG_FILE;

  if (!configFile) {
    throw new Error("Set environment: CONFIG_FILE=path/to/config.json");
  } else {
    const configOptions = JSON.parse(fs.readFileSync(configFile));
    const api = new Dhis2Api(configOptions.api);
    return {api, configFile, configOptions};
  }
}

function wait(seconds) {
  return new Promise((resolve) => setTimeout(resolve, seconds * 1000));
}

function clearCache(configOptions, key) {
  const startDate = moment();
  fs.writeFileSync(configOptions.cacheFilePath, JSON.stringify({[key]: startDate}));
};

let config = setup();
let currentUser, interpretations;

async function setupObjects(config, cacheKey) {
  jest.setTimeout(30000);
  helpers.sendEmail = jest.fn(() => Promise.resolve(true));

  const objectPath = "chart/R9A0rvAydpn";
  currentUser = await config.api.get("/me");

  await config.api.post(`/charts/R9A0rvAydpn/subscriber`);
  const interpretation1 = await createInterpretation(config.api, objectPath, "Interpretation1");
  const comment1 = await createComment(config.api, interpretation1, "Comment");

  clearCache(config.configOptions, cacheKey);

  await updateInterpretation(config.api, interpretation1, "Interpretation1-updated");
  await updateComment(config.api, interpretation1, comment1, "Comment-updated");

  const interpretation2 = await createInterpretation(config.api, objectPath, "Interpretation2");
  await updateInterpretation(config.api, interpretation2, "Interpretation2-updated");
  const comment2 = await createComment(config.api, interpretation2, "Comment2");
  await updateComment(config.api, interpretation2, comment2, "Comment2-updated");

  return {1: interpretation1, 2: interpretation2};
}

async function deleteInterpretations() {
  await helpers.concurrent(_.values(interpretations), (interpretation) => {
    return config.api.delete(interpretation.path);
  });
  interpretations = {};
}

describe("commands", () => {
  describe("sendNotifications", () => {
    beforeAll(async () => {
      interpretations = await setupObjects(config, "notifications");
      await commands.sendNotifications({configFile: config.configFile});
    });

    afterAll(deleteInterpretations);

    it("sends 4 emails", () => {
      expect(helpers.sendEmail).toHaveBeenCalledTimes(4);
    });

    it("sends emails to subscribers on interpretation created", () => {
      expect(helpers.sendEmail).toBeCalledWith(expect.any(Object), expect.objectContaining({
        "recipients": [currentUser.email],
        "subject": "John Traore created an interpretation",
        "text": expect.stringContaining(`/dhis-web-visualizer/index.html?id=R9A0rvAydpn&interpretationid=${interpretations[2].id}`),
      }));
    });

    it("sends emails to subscribers on interpretation update", () => {
      expect(helpers.sendEmail).toBeCalledWith(expect.any(Object), expect.objectContaining({
        "recipients": [currentUser.email],
        "subject": "John Traore updated an interpretation",
        "text": expect.stringContaining(`/dhis-web-visualizer/index.html?id=R9A0rvAydpn&interpretationid=${interpretations[1].id}`),
      }));
    });

    it("sends emails to subscribers on comment created", () => {
      expect(helpers.sendEmail).toBeCalledWith(expect.any(Object), expect.objectContaining({
        "recipients": [currentUser.email],
        "subject": "John Traore created an interpretation comment",
        "text": expect.stringContaining(`/dhis-web-visualizer/index.html?id=R9A0rvAydpn&interpretationid=${interpretations[2].id}`),
      }));
    });

    it("sends emails to subscribers on comment update", () => {
      expect(helpers.sendEmail).toBeCalledWith(expect.any(Object), expect.objectContaining({
        "recipients": [currentUser.email],
        "subject": "John Traore updated an interpretation comment",
        "text": expect.stringContaining(`/dhis-web-visualizer/index.html?id=R9A0rvAydpn&interpretationid=${interpretations[1].id}`),
      }));
    });
  });

  describe("sendNewsletters", () => {
    beforeAll(async () => {
      interpretations = await setupObjects(config, "newsletter");
      await commands.sendNewsletters({configFile: config.configFile});
    });

    afterAll(deleteInterpretations);

    it("sends 1 email", () => {
      expect(helpers.sendEmail).toHaveBeenCalledTimes(1);

      expect(helpers.sendEmail).toBeCalledWith(expect.any(Object), expect.objectContaining({
        "recipients": [currentUser.email],
        "subject": "DHIS2 Interpretations Digest",
      }));
    });
  });
});
