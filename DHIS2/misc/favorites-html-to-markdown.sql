-- Replace HTML to Markdown tags on interpretation/comment text and favorites descriptions:
--
--  * <i>Italic</i> -> _Italic_
--  * <b>Bold</b> -> *Bold*
--  * <strong>Strong</strong> -> *Strong*
--  * <br> -> \n
--  * <li>item1</li> -> "- item1"
--  * <ol>item2</ol> -> "- item2"
--
-- Example: $ cat favorites-html-to-markdown.sql | psql DBNAME

CREATE OR REPLACE FUNCTION repl(source TEXT, _from TEXT, _to TEXT) RETURNS TEXT AS $$ BEGIN
    RETURN REGEXP_REPLACE(source, _from, _to, 'gi');
END $$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION convert(source TEXT) RETURNS TEXT AS $$ BEGIN
    RETURN repl(repl(repl(repl(repl(repl(repl(repl(source,
        '</?i>', '_'),
        '</?b>', '*'),
        '</?strong>', '*'),
        '<br>', '\n'),
        '<li>', '- '),
        '</li>', ''),
        '<ol>', '- '),
        '</ol>', '');
END $$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION update_database() RETURNS VOID AS $$ BEGIN
    -- Interpretation/comments text
    UPDATE interpretation SET interpretationtext = convert(interpretationtext);
    UPDATE interpretationcomment SET commenttext = convert(commenttext);

    -- Favorites description
    UPDATE eventreport SET description = convert(description);
    UPDATE eventchart SET description = convert(description);
    UPDATE chart SET description = convert(description);
    UPDATE reporttable SET description = convert(description);
END $$ LANGUAGE plpgsql;

DO $$
    DECLARE
        input TEXT := CONCAT(
            'Example: <br><li>item 1</li>, <ol>item2</ol>, <b>bold</b>, ',
            '<i>italic</i>, <strong>strong</strong><br>'
        );
        expected_output TEXT := 'Example: \n- item 1, - item2, *bold*, _italic_, *strong*\n';
        result TEXT;
    BEGIN
        SELECT convert(input) INTO result;
        IF result <> expected_output THEN
            RAISE EXCEPTION E'Test error:\n  input    = %,\n  output   = %,\n  expected = %', input, result, expected_output;
        ELSE
            PERFORM update_database();
        END IF;
    END
$$ LANGUAGE plpgsql;
