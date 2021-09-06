geojsonfile = "/home/idelcano/Documents/guinea/guinea2.json"
jsonfile = "/home/idelcano/Documents/GUINEA-BISSAU.json"


import json

with open(geojsonfile) as f:
  data = json.load(f)
  with open(jsonfile) as jsonf:
      jsondata = json.load(jsonf)
      for geojson in data["features"]:
          print(geojson["properties"]["name"])
          for orgunit in jsondata["organisationUnits"]:
            if geojson["properties"]["name"] == orgunit["name"]:
              orgunit["geometry"] = geojson["geometry"]

      with open('guinea_fixed.json', 'w') as json_file:
        json.dump(jsondata, json_file)