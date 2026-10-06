"""Deterministic paragraph extraction; raw HTML remains the source of record."""
from collect import *
from bs4 import Tag

def blocks(html):
    soup=BeautifulSoup(html,'html.parser')
    body=max(soup.select('.mw-parser-output'),key=lambda e:len(e.get_text()))
    for el in body.select('table.ws-header, .ws-header, .ws-noexport, .noprint, .navbox, .licenseContainer, .licensetpl, .mw-editsection, .sistersitebox, .toc, script, style'):
        el.decompose()
    # Keep a semantic block only once; lists have their own leaf paragraphs.
    result=[]
    for el in body.find_all(['h2','h3','h4','h5','p','li','dd','dt','tr','pre','caption']):
        if el.find_parent(['p','li','dd','dt','tr','pre','caption']): continue
        # Preformatted star charts depend on internal spaces and newlines.
        text=el.get_text().strip('\r\n') if el.name=='pre' else el.get_text('',strip=True)
        if text: result.append((el.name,text))
    return result

def sections(book,title,html):
    seq=blocks(html)
    if book=='qingjing':
        ps=[s for t,s in seq[:next((i for i,x in enumerate(seq) if x[1]=='豎排版'),len(seq))] if t=='p']
        return [('正文','\n\n'.join(ps[:3])),('附言','\n\n'.join(ps[3:]))]
    if book in ['zhouyi','zhuangzi']:
        return [(title.split('/')[-1],'\n\n'.join(s for t,s in seq))]
    groups=[]; name='序'; buf=[]
    for tag,text in seq:
        is_heading=tag.startswith('h')
        if book=='laozi': is_heading=is_heading and bool(re.fullmatch('[一二三四五六七八九十百]+章',text))
        if is_heading:
            if buf: groups.append((name,'\n\n'.join(buf)))
            name=text;buf=[]
        else: buf.append(text)
    if buf: groups.append((name,'\n\n'.join(buf)))
    if book=='laozi':
        groups=[x for x in groups if x[0]!='序']
        groups=[(name,text.split('王弼老子道德經二卷')[0] if name=='八十一章' else text) for name,text in groups]
    if book=='neijing': groups=[x for x in groups if x[0] not in ['序','附註']]
    if book=='meihua' and title=='梅花易數':
        groups=[x for x in groups if x[0] in ['序','附錄'] and len(x[1])>100]
    return groups

def main():
    manifest=json.loads((ROOT/'目录/download_manifest.json').read_text(encoding='utf-8'))
    index=[]; issues=[]
    for page in manifest['pages']:
        book,title=page['book'],page['title']; html=(ROOT/page['raw_path']).read_text(encoding='utf-8')
        if book=='zhouyi' and title.split('/')[-1] in ['彖','大象','小象','文言']:
            continue # Preserved supplementary snapshots; use 经传合刊 within the 64 hexagram pages.
        for n,(name,text) in enumerate(sections(book,title,html),1):
            if not text.strip(): continue
            sid=book+'-'+hashlib.sha256((title+'#'+name+str(n)).encode()).hexdigest()[:10]
            dest=ROOT/'原文'/book/'chapters';dest.mkdir(exist_ok=True)
            raw_text=text
            if book=='laozi':
                text=re.sub('〈.*?〉','',text,flags=re.S)
                text=re.sub(r'\n{3,}','\n\n',text).strip()
                text=text.replace('華亭張氏原本','').replace('晉　王弼注','').strip()
                notes=dest/(sid+'-王弼注合刊.txt');notes.write_text(raw_text,encoding='utf-8')
            path=dest/(sid+'.txt');path.write_text(text,encoding='utf-8')
            record={'id':sid,'book':book,'page_title':title,'chapter':name,'path':str(path.relative_to(ROOT)),
              'chars':len(text),'sha256':hashlib.sha256(text.encode()).hexdigest(),'url':page['url'],
              'revision_id':page['revision_id'],'raw_path':page['raw_path'], 'review_status':'pending'}
            index.append(record)
            if len(text)<20 or '\ufffd' in text: issues.append({'id':sid,'reason':'short_or_replacement_character','text':text})
    (ROOT/'目录/chapters.json').write_text(json.dumps(index,ensure_ascii=False,indent=2),encoding='utf-8')
    (ROOT/'目录/extraction_issues.json').write_text(json.dumps(issues,ensure_ascii=False,indent=2),encoding='utf-8')
    for book in BOOKS:
        items=[x for x in index if x['book']==book]
        print(book,len(items),sum(x['chars'] for x in items))
        print([(x['id'],x['chapter'],x['chars']) for x in items][:12])
    print('issues',issues)
if __name__=='__main__':main()
