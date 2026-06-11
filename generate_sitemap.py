#!/usr/bin/env python3
"""
Auto-discover sitemap generator for one-time-deals.github.io
Crawls the site, finds all .html pages, and builds sitemap.xml
Run locally or in GitHub Actions daily.
"""
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from datetime import datetime
import xml.etree.ElementTree as ET

BASE_URL = "https://one-time-deals.github.io/"
DOMAIN = urlparse(BASE_URL).netloc

def crawl(start_url, max_pages=200):
    seen = set()
    to_visit = {start_url}
    
    while to_visit and len(seen) < max_pages:
        url = to_visit.pop()
        if url in seen:
            continue
        try:
            r = requests.get(url, timeout=10, headers={"User-Agent": "OneTimeDeals-SitemapBot/1.0"})
            if r.status_code != 200:
                continue
            seen.add(url)
            soup = BeautifulSoup(r.text, "html.parser")
            for a in soup.find_all("a", href=True):
                link = urljoin(url, a["href"].split("#")[0])
                parsed = urlparse(link)
                if parsed.netloc == DOMAIN and link.startswith("http"):
                    # keep html pages and root
                    if link.endswith(".html") or link.rstrip("/") == BASE_URL.rstrip("/"):
                        if link not in seen:
                            to_visit.add(link)
        except Exception as e:
            print(f"Skip {url}: {e}")
    return sorted(seen)

def build_sitemap(urls):
    urlset = ET.Element("urlset", xmlns="http://www.sitemaps.org/schemas/sitemap/0.9")
    today = datetime.utcnow().strftime("%Y-%m-%d")
    
    for i, url in enumerate(urls):
        url_el = ET.SubElement(urlset, "url")
        ET.SubElement(url_el, "loc").text = url
        ET.SubElement(url_el, "lastmod").text = today
        ET.SubElement(url_el, "changefreq").text = "daily" if url == BASE_URL else "weekly"
        ET.SubElement(url_el, "priority").text = "1.0" if url == BASE_URL else "0.9"
    
    tree = ET.ElementTree(urlset)
    ET.indent(tree, space="  ")
    tree.write("sitemap.xml", encoding="utf-8", xml_declaration=True)
    print(f"Generated sitemap.xml with {len(urls)} URLs")

if __name__ == "__main__":
    print(f"Crawling {BASE_URL}...")
    urls = crawl(BASE_URL)
    # ensure homepage first
    if BASE_URL not in urls:
        urls.insert(0, BASE_URL)
    build_sitemap(urls)
