from bs4 import BeautifulSoup
import urllib.request
from itertools import groupby
import sys
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
        },
        "services": [dict(method="GET", url=url) for url in service_urls],
    }
    with open('dhis2-android-dashboard.yaml', 'w') as outfile:
        yaml.dump(config, outfile)

if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))