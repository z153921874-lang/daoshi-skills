"""Check semantic coverage and regression for the repaired source extraction."""
from collect import ROOT, BeautifulSoup
from bs4 import Comment
from extract import blocks
from find_omissions import REMOVE
import json,re,hashlib

def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def norm(t): return re.sub(r'\s+','',t)
def check():
    pages=json.loads((ROOT/'目录/download_manifest.json').read_text(encoding='utf-8'))['pages']
    index=json.loads((ROOT/'目录/chapters.json').read_text(encoding='utf-8'))
    errors=[]; exclusions=[]; checked=0; special=[]
    for page in pages:
        html=(ROOT/page['raw_path']).read_text(encoding='utf-8')
        soup=BeautifulSoup(html,'html.parser');body=max(soup.select('.mw-parser-output'),key=lambda e:len(e.get_text()))
        for el in body.select(REMOVE): el.decompose()
        selected=norm(''.join(t for _,t in blocks(html)))
        for node in body.find_all(string=True):
            t=norm(str(node))
            if isinstance(node,Comment) or not t: continue
            checked+=1
            if t in selected: continue
            reason=None
            if node.find_parent('h1'): reason='卷篇标题或所选正文之外的跋文标题；原网页保留'
            elif node.find_parent('sup') and node.find_parent('sup').get('class')==['reference']: reason='脚注跳转标记；原网页保留'
            elif page['book']=='laozi' and t in ['更多资料：','道德經']: reason='站内导航；原网页保留'
            elif page['book']=='qingjing':
                # Manually collated parallel rendition, including recorded variants.
                canonical=''.join((ROOT/x['path']).read_text(encoding='utf-8') for x in index if x['book']=='qingjing')
                def clean(s):
                    s=re.sub(r'[\s。！？；，：、「」『』（）]','',s).replace('慾','欲').replace('名謂','名為')
                    for a,b in [('內觀於心','內觀其心'),('外觀於形','外觀其形'),('遠觀於物','遠觀其物')]: s=s.replace(a,b)
                    return s
                if t=='太上老君說常清靜經' or clean(t) in clean(canonical): reason='竖排平行文本；异文见验收/清静经横竖排异文.md；正文采用横排，原网页保留竖排'
            item={'book':page['book'],'title':page['title'],'text':str(node).strip(),'reason':reason}
            (exclusions if reason else errors).append(item)
        # All formerly missing special-format blocks must reach indexed text.
        destination='\n'.join((ROOT/x['path']).read_text(encoding='utf-8') for x in index if x['book']==page['book'] and x['page_title']==page['title'])
        for el in body.find_all(['pre','caption']):
            t=el.get_text().strip('\r\n') if el.name=='pre' else el.get_text('',strip=True)
            passed=t in destination
            special.append({'title':page['title'],'tag':el.name,'chars':len(t),'passed':passed})
            if not passed: errors.append({'title':page['title'],'reason':'特殊格式正文未进入章节','text':t[:100]})
    before=json.loads((ROOT/'验收/extraction-before-repair.json').read_text(encoding='utf-8'))
    old={x['id']:x for x in before}
    changes=[{'id':x['id'],'chapter':x['chapter'],'added_chars':x['chars']-old[x['id']]['chars']} for x in index if x['id'] in old and x['sha256']!=old[x['id']]['sha256']]
    result={'status':'passed' if not errors else 'failed','scope':'152页语义块覆盖及pre/caption入库回归；不等于影印底本校勘或所有附录均列为研读范围',
        'pages':len(pages),'text_nodes_checked':checked,'errors':errors,'documented_exclusions':exclusions,'special_blocks':special,'changed_units':changes,
        'source_sha256':{r:sha(ROOT/r) for r in ['tools/extract.py','tools/check_extraction.py','目录/chapters.json','目录/download_manifest.json']}}
    (ROOT/'验收/extraction-integrity.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({k:v for k,v in result.items() if k not in ['documented_exclusions','source_sha256']},ensure_ascii=False,indent=2))
    return result
if __name__=='__main__':
    import sys
    sys.exit(0 if check()['status']=='passed' else 2)
