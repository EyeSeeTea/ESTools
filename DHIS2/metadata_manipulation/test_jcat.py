"""
Test functions in jcat.
"""

import tempfile
import pytest

import jcat


files_directory = "jcat_test_json/"
expected_join_json = files_directory + "expected_join.json"


json_text = """\
{
  "planets": [
    {
      "name": "mercury",
      "position": "1",
      "satellites": []
    },
    {
      "name": "venus",
      "position": "2",
      "satellites": []
    },
    {
      "name": "earth",
      "position": "3",
      "satellites": [
        {
          "name": "moon"
        }
      ]
    },
    {
      "name": "mars",
      "position": "4",
      "satellites": [
        {
          "name": "phobos"
        },
        {
          "name": "deimos"
        }
      ]
    }
  ],
  "stars": [
    {
      "name": "sun",
      "class": "G"
    },
    {
      "name": "proxima centauri",
      "class": "M"
    }
  ]
}
"""


json_text_filtered_stars = """\
{
  "planets": [
    {
      "name": "mercury",
      "position": "1",
      "satellites": []
    },
    {
      "name": "venus",
      "position": "2",
      "satellites": []
    },
    {
      "name": "earth",
      "position": "3",
      "satellites": [
        {
          "name": "moon"
        }
      ]
    },
    {
      "name": "mars",
      "position": "4",
      "satellites": [
        {
          "name": "phobos"
        },
        {
          "name": "deimos"
        }
      ]
    }
  ],
  "stars": [
    {
      "name": "sun",
      "class": "G"
    }
  ]
}
"""


json_text_filtered_planets_multi = """\
{
  "planets": [
    {
      "name": "mercury",
      "position": "1",
      "satellites": []
    },
    {
      "name": "earth",
      "position": "3",
      "satellites": [
        {
          "name": "moon"
        }
      ]
    }
  ],
  "stars": [
    {
      "name": "sun",
      "class": "G"
    },
    {
      "name": "proxima centauri",
      "class": "M"
    }
  ]
}
"""


json_text_selected_stars = """\
{
  "stars": [
    {
      "name": "sun",
      "class": "G"
    },
    {
      "name": "proxima centauri",
      "class": "M"
    }
  ]
}
"""


json_text_filtered_satellites = """\
{
  "planets": [
    {
      "name": "mercury",
      "position": "1",
      "satellites": []
    },
    {
      "name": "venus",
      "position": "2",
      "satellites": []
    },
    {
      "name": "earth",
      "position": "3",
      "satellites": [
        {
          "name": "moon"
        }
      ]
    },
    {
      "name": "mars",
      "position": "4",
      "satellites": [
        {
          "name": "phobos"
        }
      ]
    }
  ],
  "stars": [
    {
      "name": "sun",
      "class": "G"
    },
    {
      "name": "proxima centauri",
      "class": "M"
    }
  ]
}
"""


json_text_all_filters = """\
{
  "planets": [
    {
      "name": "mercury",
      "position": "1",
      "satellites": []
    },
    {
      "name": "earth",
      "position": "3",
      "satellites": [
        {
          "name": "moon"
        }
      ]
    }
  ],
  "stars": [
    {
      "name": "sun",
      "class": "G"
    }
  ]
}
"""


json_text_sorted = """\
{
  "planets": [
    {
      "name": "earth",
      "position": "3",
      "satellites": [
        {
          "name": "moon"
        }
      ]
    },
    {
      "name": "mars",
      "position": "4",
      "satellites": [
        {
          "name": "deimos"
        },
        {
          "name": "phobos"
        }
      ]
    },
    {
      "name": "mercury",
      "position": "1",
      "satellites": []
    },
    {
      "name": "venus",
      "position": "2",
      "satellites": []
    }
  ],
  "stars": [
    {
      "class": "M",
      "name": "proxima centauri"
    },
    {
      "class": "G",
      "name": "sun"
    }
  ]
}
"""


json_no_satellites = """\
{
  "planets": [
    {
      "name": "mercury",
      "position": "1"
    },
    {
      "name": "venus",
      "position": "2"
    },
    {
      "name": "earth",
      "position": "3"
    },
    {
      "name": "mars",
      "position": "4"
    }
  ],
  "stars": [
    {
      "name": "sun",
      "class": "G"
    },
    {
      "name": "proxima centauri",
      "class": "M"
    }
  ]
}
"""


filters_exps = """\
stars:class:^G$
planets:name:^m
::satellites:name:(moon|phobos)
"""


def test_get_filters():
    with tempfile.NamedTemporaryFile('wt') as tmp:
        tmp.write(filters_exps)
        tmp.flush()

        assert (jcat.get_filters(filters_exps.splitlines(), None) ==
                jcat.get_filters(None, tmp.name))


def test_compact():
    assert jcat.compact("""  {  "one" :  1,
      "two":    2,  "three" : [
        1, 2,  3]
    } """) == '{"one":1,"two":2,"three":[1,2,3]}'


def test_expand():
    assert jcat.expand(jcat.compact(json_text)) == json_text


def test_select():
    assert jcat.select(json_text, ['stars'], []) == json_text_selected_stars
    assert jcat.select(json_text, [], ['planets']) == json_text_selected_stars
    assert jcat.select(json_text, ['planets'], []).endswith(']\n}\n')  # no ','


def test_filter_parts():
    jfilter = jcat.Filter(nesting=1, part='stars', field='class', regexp='^G$')
    broken_json = jcat.filter_parts(json_text, jfilter)
    assert jcat.fix(broken_json) == json_text_filtered_stars


def test_multi():
    jfilter = jcat.Filter(nesting=1, part='planets', field='name', regexp='^m')
    with pytest.raises(SystemExit):
        jcat.filter_parts(json_text, jfilter)

    broken_json = jcat.filter_parts(json_text, jfilter, multi=True)
    assert jcat.fix(broken_json) == json_text_filtered_planets_multi


def test_nesting():
    filters = jcat.get_filters(filters_exps.splitlines(), None)

    assert filters[0].nesting == 1 and filters[1].nesting == 1

    satellite_filter = filters[2]
    assert satellite_filter.nesting == 3

    broken_json = jcat.filter_parts(json_text, satellite_filter)
    assert jcat.fix(broken_json) == json_text_filtered_satellites


def test_apply_filters():
    filters = jcat.get_filters(filters_exps.splitlines(), None)
    broken_json = jcat.apply_filters(json_text, filters, multi=True)
    assert jcat.fix(broken_json) == json_text_all_filters


def test_replacements():
    with pytest.raises(SystemExit):
        jcat.apply_replacements(json_text, ['from'])

    with pytest.raises(SystemExit):
        jcat.apply_replacements(json_text, ['from', 'to', 'alone'])

    assert (jcat.apply_replacements('a message from earth',
                                    ['earth', 'mars', 'message', 'kiss']) ==
            'a kiss from mars')


def test_remove_fields():
    broken_json = jcat.remove_field(json_text, 'satellites')
    assert jcat.fix(broken_json) == json_no_satellites


def test_sort():
    jcat.sort_fields = ['name', 'id', 'property']
    assert jcat.jsort(json_text) == json_text_sorted


def test_join():
    list_of_files = list()
    list_of_files.append(files_directory+"user2.json", )
    list_of_files.append(files_directory+"user1.json")
    list_of_files.append(files_directory+"categoryOptions.json")
    expected_file = jcat.read(expected_join_json)

    text = jcat.get_text(list_of_files)

    assert jcat.compact(text) == jcat.compact(expected_file)
