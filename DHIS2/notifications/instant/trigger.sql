-- Triggers to insert a dataStore value (namespace = 'notifications', key = 'ev-TIMESTAMP-ID') on:
--
--   - Interpretation creation:
--       {"model": "interpretation", "type": "insert", "interpretationId": ID, created: TIMESTAMP}
--
--   - Interpretation update:
--       {"model": "interpretation", "type": "update", "interpretationId": ID, created: TIMESTAMP}
--
--   - Comment creation:
--       {"model": "comment", "type": "insert", "interpretationId": ID, "commentId": CID, created: TIMESTAMP}
--
--   - Comment update:
--       {"model": "comment", "type": "update", "interpretationId": ID, "commentId": CID2, created: TIMESTAMP}

-- Event helpers

CREATE OR REPLACE FUNCTION insert_event(VARIADIC params text[]) RETURNS SETOF keyjsonvalue AS $$
  BEGIN
    DECLARE
      hibernate_sequence int := nextval ('hibernate_sequence');
      namespace varchar := 'notifications';
      key_prefix varchar := 'ev-';
      now timestamp := NOW();
      timestamp_iso8601 text := to_char(now, 'YYYY-MM-DD"T"HH24:MI:SS"Z"');
      params_with_timestamp text[] := array_cat(params, Array['created', timestamp_iso8601]);
    BEGIN
      INSERT INTO keyjsonvalue (
        keyjsonvalueid,
        created,
        lastupdated,
        encrypted,
        namespace,
        namespacekey,
        value
      )
      VALUES (
        hibernate_sequence,
        now,
        now,
        FALSE,
        namespace,
        CONCAT(key_prefix, timestamp_iso8601, '-', hibernate_sequence),
        json_build_object(VARIADIC params_with_timestamp)
      );
    END;
  END;
$$ LANGUAGE PLPGSQL;

-- Interpretation

CREATE OR REPLACE FUNCTION event_interpretation_insert() RETURNS trigger AS $$
  BEGIN
    PERFORM insert_event(
      'type', 'insert',
      'model', 'interpretation',
      'interpretationId', NEW.uid,
      'ts', to_char(NEW.created, 'YYYY-MM-DD"T"HH24:MI:SS"Z"')
    );
     
    RETURN NEW;
  END;
$$ LANGUAGE PLPGSQL;

CREATE OR REPLACE FUNCTION event_interpretation_update() RETURNS trigger AS $$
  BEGIN
    IF NEW.interpretationtext <> OLD.interpretationtext THEN
      PERFORM insert_event(
        'type', 'update',
        'model', 'interpretation',
        'interpretationId', NEW.uid
      );
    END IF;
     
    RETURN NEW;
  END;
$$ LANGUAGE PLPGSQL;

DROP TRIGGER IF EXISTS event_interpretation_insert_trigger ON interpretation;
CREATE TRIGGER event_interpretation_insert_trigger
  AFTER INSERT
  ON interpretation
  FOR EACH ROW
  EXECUTE PROCEDURE event_interpretation_insert();

DROP TRIGGER IF EXISTS event_interpretation_update_trigger ON interpretation;
CREATE TRIGGER event_interpretation_update_trigger
  AFTER UPDATE
  ON interpretation
  FOR EACH ROW
  EXECUTE PROCEDURE event_interpretation_update();

-- Commment

CREATE OR REPLACE FUNCTION comment_event(type text, comment_id int) RETURNS keyjsonvalue AS $$
  DECLARE
    comment interpretationcomment;
    interpretation_uid varchar := (
      SELECT uid
        FROM interpretation
        WHERE interpretationid =
          (SELECT interpretationid FROM interpretation_comments WHERE interpretationcommentid = comment_id)
    );
  BEGIN
    SELECT INTO comment * FROM interpretationcomment WHERE interpretationcommentid = comment_id LIMIT 1;

    RETURN insert_event(
      'model', 'comment',
      'type', type,
      'commentId', comment.uid,
      'interpretationId', interpretation_uid
    );
  END
$$ LANGUAGE PLPGSQL;

CREATE OR REPLACE FUNCTION event_comment_insert() RETURNS trigger AS $$
  BEGIN
    PERFORM comment_event('insert', NEW.interpretationcommentid);
    RETURN NEW;
  END;
$$ LANGUAGE PLPGSQL;

CREATE OR REPLACE FUNCTION event_comment_update() RETURNS trigger AS $$
  BEGIN
    IF NEW.commenttext <> OLD.commenttext THEN
      PERFORM comment_event('update', NEW.interpretationcommentid);
    END IF;
     
    RETURN NEW;
  END;
$$ LANGUAGE PLPGSQL;

-- Create the trigger on comment insert in the <interpretation_comments> join table instead of
-- interpretationcomment, as we have no reference to the interpretation when the comment is created.

DROP TRIGGER IF EXISTS event_comment_insert_trigger ON interpretation_comments;
CREATE TRIGGER event_comment_insert_trigger
  AFTER INSERT
  ON interpretation_comments
  FOR EACH ROW
  EXECUTE PROCEDURE event_comment_insert();

DROP TRIGGER IF EXISTS event_comment_update_trigger ON interpretationcomment;
CREATE TRIGGER event_comment_update_trigger
  AFTER UPDATE
  ON interpretationcomment
  FOR EACH ROW
  EXECUTE PROCEDURE event_comment_update();
