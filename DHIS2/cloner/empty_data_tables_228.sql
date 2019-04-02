-- Example sql script that would empty the tables in a dhis2 database
-- that actually contain the data (as opposed to only metadata).

-- You can run it as part of the cloning process by passing this file
-- as argument --post-sql in dhis2_clone.

DELETE FROM trackedentitydatavalueaudit;
DELETE FROM trackedentitydatavalue;
DELETE FROM datavalueaudit;
DELETE FROM datavalue;
DELETE FROM programstageinstance_messageconversation;
DELETE FROM programstageinstancecomments;
DELETE FROM programstageinstance;
DELETE FROM trackedentityattributevalue;
DELETE FROM programinstancecomments;
DELETE FROM programinstanceaudit;
DELETE FROM programinstance;
DELETE FROM trackedentityattributevalueaudit;
DELETE FROM trackedentityprogramowner;
DELETE FROM trackedentityinstance;
DELETE FROM documentusergroupaccesses;
DELETE FROM document;
DELETE FROM dataapprovalaudit;
DELETE FROM dataapproval;
DELETE FROM fileresource;
DELETE FROM interpretation_comments;
DELETE FROM interpretationcomment;
DELETE FROM messageconversation_messages;
DELETE FROM messageconversation_usermessages;
DELETE FROM messageconversation;
