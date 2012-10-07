#!/usr/bin/python
from lxml import html
import yaml
import sys
import urllib2
import urlparse

with open('bloggers.yml') as f:
    users = yaml.safe_load(f.read())

def fetch_links(url):
    tree = html.fromstring(urllib2.urlopen(url).read())
    links = tree.xpath(
        '//link[@rel="alternate"][contains(@type, "rss") or ' +
        'contains(@type, "atom") or contains(@type, "rdf")]')
    candidates = [l for l in links if
                  'atom' in l.attrib['type'] and
                  'comments' not in l.attrib['href'].lower() and
                  'comments' not in l.attrib.get('title','')]
    if candidates:
        return candidates[0].attrib['href']
    elif links:
        return links[0].attrib['href']
    else:
        print >>sys.stderr, "No link found for %s" % (url,)
        return None

for (name, u) in users.items():
    for e in u['links']:
        (title, url) = e[1:3]
        try:
    	    e[1] = e[1].strip()
    	except:
    	    e[1] = e[1]
        if len(e) == 4:
            continue
        link = fetch_links(url)
        if link:
            if not link.startswith('http:'):
                link = urlparse.urljoin(url, link)
            e.append(link)

with open('bloggers.yml', 'w') as f:
    yaml.safe_dump(users, f)
