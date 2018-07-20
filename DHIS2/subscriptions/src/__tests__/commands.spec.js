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
let user, interpretations;

async function createInterpretationForObject(config, user, objectPath) {
  const [model, objectId] = objectPath.split("/");
  const objectPluralPath = `${model}s/${objectId}`;

  await config.api.post(`/${objectPluralPath}/subscriber`);
  const interpretation = await createInterpretation(config.api, objectPath, "Interpretation");
  const comment = await createComment(config.api, interpretation, "Comment");
  //await updateInterpretation(config.api, interpretation, "Interpretation-updated");
  //await updateComment(config.api, interpretation, comment, "Comment-updated");

  return interpretation;
}

async function deleteInterpretations() {
  await helpers.mapPromise(interpretations, interpretation => {
    return config.api.delete(interpretation.path);
  });
  interpretations = [];
}

jest.setTimeout(30000);

describe("commands", () => {
  describe("sendNotifications", () => {
    beforeAll(async () => {
      helpers.sendEmail = jest.fn(() => Promise.resolve(true));
      clearCache(config.configOptions, "notifications");
      user = await config.api.get("/me");
      const interpretation = await createInterpretationForObject(config, user, "chart/R9A0rvAydpn");
      interpretations = [interpretation];
      await commands.sendNotifications({configFile: config.configFile});
    });

    afterAll(deleteInterpretations);

    it("sends as many emails as events", () => {
      expect(helpers.sendEmail).toHaveBeenCalledTimes(2);
    });

    it("sends emails to subscribers on interpretation created", () => {
      expect(helpers.sendEmail).toBeCalledWith(expect.any(Object), expect.objectContaining({
        "recipients": [user.email],
        "subject": "John Traore created an interpretation",
        "text": expect.stringContaining(`/dhis-web-visualizer/index.html?id=R9A0rvAydpn&interpretationid=${interpretations[0].id}`),
      }));
    });

    it("sends emails to subscribers on comment created", () => {
      expect(helpers.sendEmail).toBeCalledWith(expect.any(Object), expect.objectContaining({
        "recipients": [user.email],
        "subject": "John Traore created an interpretation comment",
        "text": expect.stringContaining(`/dhis-web-visualizer/index.html?id=R9A0rvAydpn&interpretationid=${interpretations[0].id}`),
      }));
    });
  });

  describe("sendNewsletters", () => {
    beforeAll(async () => {
      helpers.sendEmail = jest.fn(() => Promise.resolve(true));
      clearCache(config.configOptions, "newsletter");
      user = await config.api.get("/me");
      const objectPaths = [
        "chart/R9A0rvAydpn",
        "map/zDP78aJU8nX",
        "reportTable/qfMh2IjOxvw",
        "eventReport/YZzuVprU7aZ",
        "eventChart/WIxuUpm5m4U",
      ];
      interpretations = await helpers.mapPromise(objectPaths, objectPath => {
        return createInterpretationForObject(config, user, objectPath);
      });

      await commands.sendNewsletters({configFile: config.configFile});
    });

    afterAll(deleteInterpretations);

    it("sends as many emails as subscribers", () => {
      expect(helpers.sendEmail).toHaveBeenCalledTimes(1);
    });

    it("sends newsletter to subscriber", () => {
      expect(helpers.sendEmail).toBeCalledWith(expect.any(Object), expect.objectContaining({
        "recipients": [user.email],
        "subject": "DHIS2 Interpretations Digest",
      }));
    });
  });
});
