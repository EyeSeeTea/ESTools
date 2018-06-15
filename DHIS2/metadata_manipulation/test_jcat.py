"""
Test functions in jcat.
"""

import tempfile

import jcat


json_text = """\
{
  "resources":[
    {
      "displayName":"Dashboard Items",
      "singular":"dashboardItem",
      "plural":"dashboardItems",
      "href":"http://who-dev.essi.upc.edu:8081/api/dashboardItems"
    },
    {
      "displayName":"Dashboards",
      "singular":"dashboard",
      "plural":"dashboards",
      "href":"http://who-dev.essi.upc.edu:8081/api/dashboards"
    }
  ]
}
"""

json_text_filtered = """\
{
  "resources":[
    {
      "displayName":"Dashboard Items",
      "singular":"dashboardItem",
      "plural":"dashboardItems",
      "href":"http://who-dev.essi.upc.edu:8081/api/dashboardItems"
    }
  ]
}
"""

filters = """\
userRoles:name:^HEP
users:username:(^(hep|sarah|yvan|ignacio|jordi)\.|\.dataentry$)
userGroups:name:^HEP
indicators:name:^HEP_
programIndicators:displayName:^HEP
validationRules:name:^HEP
indicatorGroups:name:^HEP
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
    part, field, regexp =  'resources', 'displayName', 'Items'
    assert (jcat.filter_parts(json_text, part, field, regexp) ==
            json_text_filtered)


# TODO:
# def test_multi():
#    pass
