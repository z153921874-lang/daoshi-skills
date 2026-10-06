"""Identify visible source text excluded by the old block-only extractor."""
from collect import ROOT,BeautifulSoup
from bs4 import Comment
import json,re

REMOVE='table.ws-header, .ws-header, .ws-noexport, .noprint, .navbox, .licenseContainer, .licensetpl, .mw-editsection, .sistersitebox, .toc, script, style'
def main():
    pages=json.loads((ROOT/'目录/download_manifest.json').read_text(encoding='utf-8'))['pages'];report=[]
    for p in pages:
        soup=BeautifulSoup((ROOT/p['raw_path']).read_text(encoding='utf-8'),'html.parser');body=max(soup.select('.mw-parser-output'),key=lambda e:len(e.get_text()))
        for el in body.select(REMOVE):el.decompose()
        gaps=[]
        for node in body.find_all(string=True):
            if isinstance(node,Comment) or not re.sub(r'\s+','',str(node)):continue
            if not node.find_parent(['h2','h3','h4','h5','p','li','dd','dt','tr']):
                gaps.append({'text':str(node).strip(),'parent':node.parent.name,'class':node.parent.get('class',[])})
        if gaps:report.append({'book':p['book'],'title':p['title'],'gaps':gaps})
    (ROOT/'验收/extraction-omissions.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(report,ensure_ascii=False,indent=2))

if __name__=='__main__':main()
