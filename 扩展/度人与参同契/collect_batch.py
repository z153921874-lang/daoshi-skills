"""Resumable source acquisition, never marks a downloaded page as studied."""
import sys,json,hashlib,re
from pathlib import Path
ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT.parents[1]/'tools'))
import collect
collect.ROOT=ROOT
def save(p,d):
 p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding='utf-8')
def main():
 roots={k:json.loads((ROOT/'目录'/f'{k}.json').read_text(encoding='utf-8')) for k in ['duren','cantong','peng','zhu']}
 jobs=[(k,r['title'],'目录页' if k in ['duren','cantong'] else '经注合刊页') for k,r in roots.items()]
 for k,pattern in [('duren',r'靈寶無量度人上品妙經/\d+$'),('cantong',r'周易參同契/\d+章$')]:
  links=[x for x in roots[k]['links'] if re.fullmatch(pattern,x['title'])]
  assert len(links)==(61 if k=='duren' else 35),(k,len(links))
  jobs.extend((k,x['title'],'卷正文页' if k=='duren' else '章正文页') for x in links)
 manifest={'scope':'度人经61卷；参同契网络35章本；彭晓分章通真义、朱熹考异各三卷合刊。独立序目高上神霄宗师授经式不在本批。', 'expected_pages':len(jobs),'pages':[],'errors':[],'review_status':'pending','enabled':False}
 for n,(k,title,role) in enumerate(jobs,1):
  try:
   r=collect.inspect(title,k); meta=r['meta'];stem=hashlib.sha256(title.encode()).hexdigest()[:16]
   p=ROOT/'页面文本'/f'{k}-{stem}.txt';p.parent.mkdir(exist_ok=True);p.write_text(r['text'],encoding='utf-8')
   html=(ROOT/meta['raw_path']).read_text(encoding='utf-8');s=collect.BeautifulSoup(html,'html.parser');body=max(s.select('.mw-parser-output'),key=lambda e:len(e.get_text()))
   headings=[h.get_text(' ',strip=True) for h in body.select('h2,h3,h4')]
   item={**meta,'id':f'{k}-{stem}','book':k,'title':title,'role':role,'text_path':str(p.relative_to(ROOT)),'text_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'characters':len(r['text']),'headings':headings,'review_status':'pending', 'layer_notice':'页面文本保留题解、经文、旧注、校记及页内导航；尚未逐段分层，不能整页冒称纯经文。'}
   assert item['revision_id'] and item['license_notice'] and any('by-sa/4.0' in x for x in item['license_links'])
   manifest['pages'].append(item)
   print(f'{n}/{len(jobs)} {title} {len(r["text"])}字',flush=True)
  except Exception as e:manifest['errors'].append({'title':title,'error':str(e)});print('ERROR',title,str(e),flush=True)
  save(ROOT/'目录/下载清单.json',manifest)
 print('DONE',len(manifest['pages']),'errors',len(manifest['errors']))
if __name__=='__main__':main()
