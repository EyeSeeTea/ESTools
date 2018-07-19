const _ = require('lodash');
const moment = require('moment');

function getBucket() {
  return "ev-month-" + moment().format("YYYY-MM");
}

async function createInterpretation(api, objectPath, text = "My interpretation") {
  const bucket = getBucket();
  const response = await api.post(`/interpretations/${objectPath}`,
    {body: text, headers: {"content-type": "text/plain"}, resolveWithFullResponse: true});
  const interpretationPath = response.headers.location;
  const interpretationId = _.last(interpretationPath.split("/"));
  return {id: interpretationId, path: interpretationPath, bucket};
}

async function createComment(api, interpretation, text = "My comment") {
  const bucket = getBucket();
  const response = await api.post(`/interpretations/${interpretation.id}/comments`,
    {body: text, headers: {"content-type": "text/plain"}, resolveWithFullResponse: true});
  const commentPath = response.headers.location;
  const commentId = _.last(commentPath.split("/"));
  return {id: commentId, path: commentPath, bucket};
}

async function updateInterpretation(api, interpretation, text) {
  return api.put(`/interpretations/${interpretation.id}`,
    {body: text, headers: {"content-type": "text/plain"}});
}

async function updateComment(api, interpretation, comment, text) {
  return api.put(`/interpretations/${interpretation.id}/comments/${comment.id}`,
    {body: text, headers: {"content-type": "text/plain"}});
}

Object.assign(module.exports, {
  createInterpretation,
  createComment,
  updateInterpretation,
  updateComment,
});
