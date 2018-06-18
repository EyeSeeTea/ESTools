"""
Test functions in jcat.
"""

import tempfile
import pytest

import jcat


json_text = """\
{
  "planets":[
    {
      "name":"mercury",
      "position":"1",
      "satellites":[
      ]
    },
    {
      "name":"venus",
      "position":"2",
      "satellites":[
      ]
    },
    {
      "name":"earth",
      "position":"3",
      "satellites":[
        {
          "name":"moon"
        }
      ]
    }
  ],
  "stars":[
    {
      "name":"sun",
      "class":"G"
    },
    {
      "name":"proxima centauri",
      "class":"M"
    }
  ]
}
"""

json_text_filtered_stars = """\
{
  "planets":[
    {
      "name":"mercury",
      "position":"1",
      "satellites":[
      ]
    },
    {
      "name":"venus",
      "position":"2",
      "satellites":[
      ]
    },
    {
      "name":"earth",
      "position":"3",
      "satellites":[
        {
          "name":"moon"
        }
      ]
    }
  ],
  "stars":[
    {
      "name":"sun",
      "class":"G"
    }
  ]
}
"""

json_text_filtered_planets = """\
{
  "planets":[
    {
      "name":"mercury",
      "position":"1",
      "satellites":[
      ]
    },
    {
      "name":"earth",
      "position":"3",
      "satellites":[
        {
          "name":"moon"
        }
      ]
    }
  ],
  "stars":[
    {
      "name":"sun",
      "class":"G"
    },
    {
      "name":"proxima centauri",
      "class":"M"
    }
  ]
}
"""

filters = """\
stars:class:^G$
planets:name:^m
"""


def test_get_filters():
    with tempfile.NamedTemporaryFile('wt') as tmp:
        tmp.write(filters)
        tmp.flush()

        assert (jcat.get_filters(filters.splitlines(), None) ==
                jcat.get_filters(None, tmp.name))


def test_compact():
    assert jcat.compact("""  {  "one" :  1,
      "two":    2,  "three" : [
        1, 2,  3]
    } """) == '{"one":1,"two":2,"three":[1,2,3]}'


def test_expand():
    assert jcat.expand(jcat.compact(json_text)) == json_text


def test_filter_parts():
    part, field, regexp =  'stars', 'class', '^G$'
    assert (jcat.filter_parts(json_text, part, field, regexp) ==
            json_text_filtered_stars)


def test_multi():
    part, field, regexp =  'planets', 'name', '^m'
    with pytest.raises(SystemExit):
        jcat.filter_parts(json_text, part, field, regexp)

    assert (jcat.filter_parts(json_text, part, field, regexp, multi=True) ==
            json_text_filtered_planets)
