from bs4 import BeautifulSoup
import urllib.request
from itertools import groupby
import sys
import os
import yaml

def main(args):
    url = args[0]
    response = urllib.request.urlopen(url)
    html = response.read()
    soup = BeautifulSoup(html, 'html.parser')

    pattern = "https://play.dhis2.org/android-previous1/api"
    hrefs = [link.get("href") for link in soup.findAll('a')]
    api_hrefs = [href for href in hrefs if href.startswith(pattern)]
    unique_hrefs = [key for (key, values) in groupby(api_hrefs)]
    service_urls = [url[len(pattern):] for url in unique_hrefs]

    config = {
        "server": {
          "url": "https://play.dhis2.org/android-previous1",
          "auth": 'admin:district',
          "nrequests": 100,
        },
        "services": [dict(method="GET", url=url) for url in service_urls],
    }
    name = os.path.basename(os.path.dirname(url))
    yaml_path = name + '.yaml'
    with open(yaml_path, 'w') as outfile:
        yaml.dump(config, outfile)
    print(yaml_path)

if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))