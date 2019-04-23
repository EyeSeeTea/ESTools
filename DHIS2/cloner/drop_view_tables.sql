-- Sql script to drop all the view tables

-- You can run it as part of the cloning process by passing this file
-- as argument --post-sql in dhis2_clone.

DO $$
DECLARE
 rec RECORD;
BEGIN
     	FOR rec IN SELECT CONCAT('_view_', REPLACE(REPLACE(LOWER(this_.name), ' ', '_'), '_-_', '_')) as name from sqlview this_ where this_.type = 'VIEW'
		LOOP
			RAISE NOTICE 'DROP VIEW %', rec.name;
			EXECUTE CONCAT('DROP VIEW IF EXISTS ', rec.name);
		END LOOP;
END; $$
