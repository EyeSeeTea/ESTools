-- Interpretation triggers for postgreSQL (>= 9.5)
--
-- Insert interpretations event in DHIS2 data store as JSON. For efficiency on retrieving, group
-- events into time-slot buckets, each bucket containing an array of event objects sorted by date.
--
--   - namespace = 'notifications'
--   - key = 'ev-month-YYYY-MM'
--
-- Events:
--
--   - Interpretations:
--
--       {
--         "model": "interpretation",
--         "type": "insert" | "update",
--         "interpretationId": ID,
--         "created": TIMESTAMP ("YYYY-MM-DDTHH24:MI:SSZ")
--       }
--
--   - Comments:
--
--       {
--         "model": "comment",
--         "type": "insert" | "update",
--         "interpretationId": ID,
--         "commentId": CID,
--         "created": TIMESTAMP ("YYYY-MM-DDTHH24:MI:SSZ")
--       }

-- Helpers

CREATE OR REPLACE FUNCTION insert_event(VARIADIC params text[]) RETURNS SETOF keyjsonvalue AS $$
  BEGIN
    DECLARE
      now timestamp := now() at time zone 'utc';
      hibernate_sequence int := nextval ('hibernate_sequence');
      namespace varchar := 'notifications';
      bucket_key text := concat('ev-month-', to_char(now, 'YYYY-MM'));
      timestamp_iso8601 text := to_char(now, 'YYYY-MM-DD"T"HH24:MI:SS.MS"Z"');
      params_with_timestamp text[] := array_cat(params, Array['created', timestamp_iso8601]);
      payload jsonb := json_build_object(VARIADIC params_with_timestamp);
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
        bucket_key,
        json_build_array(payload)
      )
      ON CONFLICT ON CONSTRAINT keyjsonvalue_unique_key_in_namespace DO UPDATE
        SET value = keyjsonvalue.value::jsonb || payload,
            lastupdated = now;
    END;
  END;
$$ LANGUAGE PLPGSQL;

-- Interpretations

CREATE OR REPLACE FUNCTION event_interpretation_insert() RETURNS trigger AS $$
  BEGIN
    PERFORM insert_event(
      'type', 'insert',
      'model', 'interpretation',
      'interpretationId', NEW.uid
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

-- Commments

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

-- Create the comment insertion trigger in `interpretation_comments` table instead of
-- interpretationcomment, since we have no reference to the interpretation at this point.

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
