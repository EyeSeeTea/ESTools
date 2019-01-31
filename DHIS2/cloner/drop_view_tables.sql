-- Sql script to create the getTableViewNames() and dropViewTables() psql functions
-- and execute dropViewTables()

-- You can run it as part of the cloning process by passing this file
-- as argument --post-sql in dhis2_clone.

-- Create getTableViewNames function
-- Return a list of view tables propertly formatted
CREATE FUNCTION getTableViewNames()
RETURNS SETOF record
LANGUAGE plpgsql as $$
DECLARE
 rec record;
 BEGIN
  FOR rec IN
	SELECT CONCAT('_view_', REPLACE(LOWER(this_.name), ' ', '_'))
	from sqlview this_ where this_.type = 'VIEW';
  LOOP
	return next rec;
  END LOOP;
END $$;

-- Create dropViewTables() function

CREATE FUNCTION dropViewTables()
RETURNS SETOF record
LANGUAGE plpgsql as $$
DECLARE
 rec record;
 BEGIN
  FOR rec IN
	(select * from getTableViewNames() as (names text))
  LOOP
	RAISE NOTICE 'DROP DATABASE %', rec;
	'DROP DATABASE %', rec;
  END LOOP;
END $$;

-- Execute drop view tables

SELECT dropViewTables();
