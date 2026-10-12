"""Check the built blog's navigation, article coverage and metadata."""
import json
import re
import xml.etree.ElementTree as ET
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT=Path(__file__).resolve().parent
OUT=ROOT/'docs'
errors=[]
class Page(HTMLParser):
    def __init__(self):
        super().__init__();self.links=[];self.ids=[];self.h1=0;self.lang=None
    def handle_starttag(self, tag, attrs):
        attrs=dict(attrs)
        if tag=='html':self.lang=attrs.get('lang')
        if tag=='h1':self.h1+=1
        if attrs.get('id'):self.ids.append(attrs['id'])
        if tag in ('a','img','script','link'):
            value=attrs.get('href') or attrs.get('src')
            if value:self.links.append(value)

pages={}
for path in OUT.rglob('*.html'):
    page=Page();page.feed(path.read_text());pages[path.resolve()]=page
    if page.h1!=1:errors.append(f'{path}: expected one main heading')
    if page.lang!='ja':errors.append(f'{path}: wrong language')
    if len(page.ids)!=len(set(page.ids)):errors.append(f'{path}: duplicate anchor IDs')
    if re.search(r'【\d+†',path.read_text()):errors.append(f'{path}: unresolved retrieval reference')

for path,page in pages.items():
    # The custom 404 uses a hosting base path; it has no article links.
    if path.name=='404.html':continue
    for value in page.links:
        url=urlsplit(value)
        if url.scheme or url.netloc:continue
        if not url.path:
            target=path
        else:
            target=(OUT/url.path.lstrip('/') if url.path.startswith('/') else path.parent/unquote(url.path)).resolve()
            if target.is_dir():target=target/'index.html'
        if not target.exists():errors.append(f'{path}: missing {value}')
        elif url.fragment and target in pages and url.fragment not in pages[target].ids:errors.append(f'{path}: missing anchor {value}')

mapping=json.loads((ROOT/'migration-map.json').read_text())
article_pages=list((OUT/'posts').glob('*/index.html'))
if len(article_pages)!=len(list((ROOT/'posts').glob('*.md'))):errors.append('Not all source articles were built')
for item in mapping:
    path=OUT/item['new_path']/'index.html'
    if not path.exists():errors.append(f'Missing migrated article {path}')
    elif item['source_url'] not in path.read_text():errors.append(f'Missing original URL {path}')
for filename in ['feed.xml','sitemap.xml']:
    if (OUT/filename).exists():ET.parse(OUT/filename)
preview='noindex,nofollow' in (OUT/'index.html').read_text()
for path in pages:
    if preview and 'noindex,nofollow' not in path.read_text():errors.append(f'Preview guard missing {path}')
    if not preview and '移行プレビュー' in path.read_text():errors.append(f'Preview banner on public build {path}')
for path in (ROOT/'assets').glob('*.svg'):ET.parse(path)
print(f'{len(pages)} HTML pages; {len(article_pages)} articles; {len(errors)} errors')
for error in errors:print(error)
raise SystemExit(bool(errors))
