-- Replace HTML to Markdown tags:
--
--  * <i>Italic</i> -> _Italic_
--  * <b>Bold</b> -> *Bold*
--  * <strong>Strong</strong> -> *Strong*
--  * <br> -> \n
--
-- Example: cat favorites-html-to-markdown.sql | psql dhis2db

CREATE OR REPLACE FUNCTION html_to_markdown(source TEXT, html_tag TEXT, markdown_tag TEXT) RETURNS TEXT AS $$
    BEGIN
        RETURN REGEXP_REPLACE(source, CONCAT('<[/]?', html_tag, '>'), markdown_tag, 'gi');
    END
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION convert(source TEXT) RETURNS TEXT AS $$
    BEGIN
        RETURN
            html_to_markdown(
                html_to_markdown(
                    html_to_markdown(
                        html_to_markdown(
                            source, 'i', '_'), 'b', '*'), 'strong', '*'), 'br', '\n');
    END
$$ LANGUAGE plpgsql;

-- Interpretation/comments text
UPDATE interpretation SET interpretationtext = convert(interpretationtext);
UPDATE interpretationcomment SET commenttext = convert(commenttext);

-- Favorites description
UPDATE eventreport SET description = convert(description);
UPDATE eventchart SET description = convert(description);
UPDATE chart SET description = convert(description);
UPDATE reporttable SET description = convert(description);
