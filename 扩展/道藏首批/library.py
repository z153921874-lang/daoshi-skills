"""Offline, separately indexed Daozang supplement. Source text is never corrected."""
from pathlib import Path
import json, hashlib, sys, argparse, re
ROOT=Path(__file__).resolve().parent
MAIN=ROOT.parents[1]
sys.path.insert(0,str(MAIN/'tools/vendor'))
from bs4 import BeautifulSoup
from opencc import OpenCC
TITLES={'neiguan':'太上老君内观经','dingguan':'洞玄灵宝定观经','yinfu':'黄帝阴符经'}
COUNTS={'neiguan':14,'dingguan':10,'yinfu':3}
def read(p): return json.loads(p.read_text(encoding='utf-8'))
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,s):
    p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(s,encoding='utf-8')
def dump(p,d): write(p,json.dumps(d,ensure_ascii=False,indent=2))
def paragraphs(key):
    d=read(ROOT/'目录'/f'{key}.json')
    soup=BeautifulSoup((ROOT/d['meta']['raw_path']).read_text(encoding='utf-8'),'html.parser')
    body=max(soup.select('.mw-parser-output'),key=lambda e:len(e.get_text()))
    out=[]
    for e in body.find_all('p'):
        t=e.get_text('',strip=False).strip()
        if not t.replace('\u200b','').strip():continue
        if t.startswith('此作品'):break
        out.append(t)
    assert len(out)==COUNTS[key],(key,len(out))
    return d,out
def build():
    notes=read(ROOT/'notes.json'); records=[]
    intro=['# 道藏首批扩展：三部经典','',
      '状态：选定网络录入本全文初读及逐段笔记完成；来源提取、引文与完整性核验见验收.json。不是影印本逐字精校。',
      '原有八部、568单元另行保留；本扩展新增三部、27阅读单元。内观14段、定观10段（含开场与结颂）是项目阅读划分，不冒称古籍原章名；阴符3章采用页面章目。',
      '古籍原文为公有领域；网页贡献遵循页面标明的 CC BY-SA 4.0，链接、修订号、下载日期与原始HTML保存在目录和原文中。本站提取与笔记如涉及网页改编按同协议署名共享。未下载现代译注。',
      '新增能力：本地全文检索、段落引用、身心观与定慧术语解释、时机和利害的文本讨论。未新增八字算法、预测准确性或临床能力。',
      '《内观经》《阴符经》页面标明收录于《正统道藏》；《定观经》此次选经文独立录入本，道藏收入的《定观经注》尚未纳入，不能宣称已研读注本。目录依据：[中国哲学书电子化计划](https://ctext.org/library.pl?by_collection=132&if=gb&remap=gb&res=84063)。',
      '已知层次：《内观经》第10段两处“一作通”为网页夹注，年代未定；第8段“水由形有”、第9段“四見者”留疑。《阴符经》下章有零宽字符与换行，原样保存。各正文文件不含导航和版权页脚。',
      '全文可通过本目录 library.py search 关键词 或 chapter 编号读取；check 检查内容是否仍与研读时相同。','']
    for key,title in TITLES.items():
        d,parts=paragraphs(key); assert len(notes[key])==len(parts)
        meta=d['meta']; sections=[f'# {title}','',f"来源：[{d['title']}]({meta['url']})；修订 {meta['revision_id']}；下载 {meta['retrieved_at']}",
         '网络录入本，未与影印底本逐字校勘。以下标题（除阴符三章）与白话说明是本项目撰写。',
         '关联：原库《清静经》《坐忘论》；关联只表示适合比较，不自动证明传承或直接影响。','']
        for i,(t,n) in enumerate(zip(parts,notes[key]),1):
            concept,quote,explanation,application,uncertainty=n
            assert quote in t,(key,i,quote)
            sid=f'{key}-{i:02d}'; path=ROOT/'正文'/f'{sid}.txt';write(path,t+'\n')
            rec={'id':sid,'book':key,'title':concept,'path':str(path.relative_to(ROOT)),
             'sha256':sha(path),'review_status':'reviewed','quote':quote,'explanation':explanation,
             'application':application,'uncertainty':uncertainty,'related':['清静经','坐忘论'],
             'source_url':meta['url'],'revision_id':meta['revision_id'],'source_paragraph':i}
            records.append(rec)
            sections += [f'## {sid} · {concept}',f'原文：[完整段落]({path.as_posix()})',f'> {quote}',
             f'白话解释：{explanation}',f'现代应用（类比）：{application}',f'疑点与边界：{uncertainty}','']
        write(ROOT/'研读'/f'{title}.md','\n\n'.join(sections))
        intro += [f"- [{title}](研读/{title}.md)：{len(parts)}单元，[来源]({meta['url']})，修订 {meta['revision_id']}。"]
    dump(ROOT/'目录/chapters.json',records)
    write(ROOT/'阅读总览.md','\n\n'.join(intro))
    paths=[ROOT/'notes.json',ROOT/'library.py',ROOT/'阅读总览.md',ROOT/'目录/chapters.json']
    for folder in ['正文','原文','研读']:
        paths.extend(p for p in (ROOT/folder).rglob('*') if p.is_file())
    paths.extend(ROOT/'目录'/f'{k}.json' for k in TITLES)
    dump(ROOT/'manifest.json',{'files':{str(p.relative_to(ROOT)):sha(p) for p in paths},
         'scope':'三部网络录入本，27单元；无影印精校或注本全文研读声明'})
    print(json.dumps(validate(),ensure_ascii=False))
def validate():
    errors=[]
    try:
        manifest=read(ROOT/'manifest.json'); records=read(ROOT/'目录/chapters.json')
        for rel,h in manifest['files'].items():
            p=(ROOT/rel).resolve()
            if not p.is_relative_to(ROOT) or not p.is_file() or sha(p)!=h:errors.append('版本变化：'+rel)
        if len(records)!=27 or len({r['id'] for r in records})!=27:errors.append('单元数量或编号不符')
        for key in TITLES:
            d,parts=paragraphs(key); meta=d['meta']; rr=[r for r in records if r['book']==key]
            if len(rr)!=COUNTS[key]:errors.append('目录覆盖不符：'+key)
            if sha(ROOT/meta['raw_path'])!=meta['sha256']:errors.append('原始快照变化')
            if not meta.get('revision_id') or not meta.get('retrieved_at') or not any('by-sa/4.0' in u for u in meta['license_links']):errors.append('来源元数据不全')
            for r,t in zip(rr,parts):
                p=ROOT/r['path']; actual=p.read_text(encoding='utf-8')
                if actual!=t+'\n' or sha(p)!=r['sha256'] or '\ufffd' in actual:errors.append('原文提取不符：'+r['id'])
                if r['quote'] not in actual or not all(r[f] for f in ['explanation','application','uncertainty','related']):errors.append('笔记无效：'+r['id'])
        return {'status':'passed' if not errors else 'failed','books':3,'units':len(records),
          'quote_checks':len(records),'errors':errors,'files':list(manifest['files'])+['manifest.json']}
    except Exception as e:return {'status':'failed','errors':[str(e)]}
def publish():
    result=validate();assert result['status']=='passed',result
    vault=Path('E:/Obsidian/道士'); target=vault/'道藏扩展';target.mkdir(exist_ok=True)
    lines=['# 道藏扩展','', '三部经典、27阅读单元。全文初读完成；网络录入本，保留疑点，未作影印精校。', '[[首页]]','']
    for key,title in TITLES.items():
        records=[r for r in read(ROOT/'目录/chapters.json') if r['book']==key]
        note=(ROOT/'研读'/f'{title}.md').read_text(encoding='utf-8')
        note+='\n\n## 所选版本全文\n\n'
        for r in records: note+=f"### {r['id']}\n\n```text\n{(ROOT/r['path']).read_text(encoding='utf-8')}```\n\n"
        note+='\n[[道藏扩展入口]] · [[典籍/qingjing|清静经]] · [[典籍/zuowang|坐忘论]]\n'
        write(target/f'{title}.md',note);lines.append(f'- [[道藏扩展/{title}|{title}]]')
    write(vault/'道藏扩展入口.md','\n'.join(lines))
    home=vault/'首页.md'; text=home.read_text(encoding='utf-8')
    if '[[道藏扩展入口]]' not in text:write(home,text+'\n\n## 道藏新增资料\n\n[[道藏扩展入口]]：内观经、定观经、阴符经。\n')
    # Verify copied original strings and links in the four generated pages.
    for key,title in TITLES.items():
        t=(target/f'{title}.md').read_text(encoding='utf-8')
        for r in read(ROOT/'目录/chapters.json'):
            if r['book']==key: assert (ROOT/r['path']).read_text(encoding='utf-8') in t
    for file in [vault/'道藏扩展入口.md',*target.glob('*.md')]:
        for link in re.findall(r'\[\[([^\]|]+)(?:\|[^\]]+)?\]\]',file.read_text(encoding='utf-8')):
            assert (vault/(link+'.md')).exists(),link
    print('Obsidian：三部全文、27单元与链接核对通过。')
if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('action',choices=['build','check','search','chapter','publish']);parser.add_argument('value',nargs='?');a=parser.parse_args()
    if a.action=='build':build()
    elif a.action=='publish':publish()
    else:
        result=validate()
        if a.action=='check':
            print(json.dumps(result,ensure_ascii=False,indent=2));sys.exit(0 if result['status']=='passed' else 2)
        if result['status']!='passed':raise SystemExit('扩展校验未通过，请先修复。')
        if not a.value:parser.error('需要关键词或篇章编号')
        cc=OpenCC('t2s');found=[]
        for r in read(ROOT/'目录/chapters.json'):
            text=(ROOT/r['path']).read_text(encoding='utf-8')
            if (a.action=='chapter' and r['id']==a.value) or (a.action=='search' and cc.convert(a.value) in cc.convert(text)):
                found.append({**r,'absolute_path':str(ROOT/r['path']),'text':text})
        print(json.dumps(found,ensure_ascii=False,indent=2))
