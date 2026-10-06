"""Download explicitly selected public Wikisource editions, preserving raw evidence."""
import sys, json, hashlib, time, re, argparse
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.parse import quote, unquote, urlparse
from datetime import datetime, timezone
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools/vendor'))
from bs4 import BeautifulSoup

BOOKS = {'zhouyi':'周易', 'neijing':'黃帝內經', 'meihua':'梅花易數',
 'ziwei':'紫微斗數全書', 'laozi':'道德經', 'zhuangzi':'莊子',
 'qingjing':'太上老君說常清靜經', 'zuowang':'坐忘論'}

def fetch(title, book):
    folder=ROOT/'原文'/book/'raw'; folder.mkdir(parents=True, exist_ok=True)
    stem=hashlib.sha256(title.encode()).hexdigest()[:16]
    path=folder/(stem+'.html'); meta_path=folder/(stem+'.json')
    url='https://zh.wikisource.org/wiki/'+quote(title, safe='/')
    if path.exists() and meta_path.exists():
        return path.read_text(encoding='utf-8'),json.loads(meta_path.read_text(encoding='utf-8'))
    for attempt in range(3):
        try:
            with urlopen(Request(url,headers={'User-Agent':'Mozilla/5.0 (Personal classic research; low-rate archival)'}),timeout=30) as res:
                data=res.read(); final=res.url
            html=data.decode('utf-8'); soup=BeautifulSoup(html,'html.parser')
            if not soup.select_one('.mw-parser-output'): raise ValueError('Missing article body')
            rev=re.search(r'"wgRevisionId"\s*:\s*(\d+)',html)
            meta={'requested_title':title,'url':url,'resolved_url':final,'retrieved_at':datetime.now(timezone.utc).isoformat(),
              'revision_id':rev.group(1) if rev else None,'sha256':hashlib.sha256(data).hexdigest(),
              'raw_path':str(path.relative_to(ROOT)), 'license_notice':soup.select_one('#footer-info-copyright').get_text(' ',strip=True) if soup.select_one('#footer-info-copyright') else None,
              'license_links':[a.get('href') for a in soup.select('#footer-info-copyright a')],
              'edition_notice':'网络录入本；按页面所列版本记录；不冒称完成影印本逐字校勘'}
            path.write_bytes(data); meta_path.write_text(json.dumps(meta,ensure_ascii=False,indent=2),encoding='utf-8')
            time.sleep(.3)
            return html,meta
        except Exception:
            if attempt==2: raise
            time.sleep(attempt+1)

def inspect(title,book):
    html,meta=fetch(title,book); soup=BeautifulSoup(html,'html.parser'); body=max(soup.select('.mw-parser-output'),key=lambda e:len(e.get_text()))
    links=[]
    for a in body.select('a[href]'):
        href=a.get('href','')
        if href.startswith('/wiki/'):
            target=unquote(href[6:]).split('#')[0]
            if ':' not in target and target not in [x['title'] for x in links]: links.append({'title':target,'label':a.get_text(' ',strip=True)})
    return {'book':book,'title':title,'text':body.get_text('\n',strip=True),'links':links,'meta':meta}

if __name__=='__main__':
    p=argparse.ArgumentParser(); p.add_argument('--book',choices=list(BOOKS)); p.add_argument('--title'); args=p.parse_args()
    books=[args.book] if args.book else BOOKS
    for book in books:
        result=inspect(args.title or BOOKS[book],book)
        dest=ROOT/'目录';dest.mkdir(exist_ok=True)
        (dest/(book+'.json')).write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
        print(json.dumps({'book':book,'text':result['text'][:2200],'links':result['links']},ensure_ascii=False))
