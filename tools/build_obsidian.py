"""Rebuild derived Obsidian navigation; canonical originals/notes stay outside vault."""
from pathlib import Path
import json, hashlib, re
from collect import ROOT, BOOKS
from source_layers import info as layer_info

VAULT = Path('E:/Obsidian/道士')

def write(name, text):
    p = VAULT / name
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text + '\n', encoding='utf-8')

def main():
    records = json.loads((ROOT/'研读/records.json').read_text(encoding='utf-8'))
    status = json.loads((ROOT/'目录/status.json').read_text(encoding='utf-8'))
    tasks = json.loads((ROOT/'验收/final-review-tasks.json').read_text(encoding='utf-8'))
    links = []
    def link(target, label):
        links.append(target)
        return f'[[{target}|{label}]]'
    by_title = {}
    for r in records:
        by_title.setdefault(r['chapter'], []).append(r)
    doubts = ['# 疑点与边界索引', '以下是逐章初读提出的问题，不表示所有疑点已校定。']
    for r in records:
        text = (ROOT/r['path']).read_text(encoding='utf-8')
        digest = hashlib.sha256(text.encode()).hexdigest()
        assert digest == r['sha256'], r['id']
        raw = '原文/'+r['id']
        note = '章节/'+r['id']
        meta = f'---\nchapter_id: {r["id"]}\nbook: {r["book"]}\nsource_sha256: {digest}\nrevision: "{r["revision_id"]}"\n---\n'
        write(raw+'.md', meta+f'# {r["chapter"]}：原文阅读副本\n\n'+link(note,'返回研读')+f' · [维基文库来源]({r["url"]})\n\n原始文件：`{r["path"]}`。下面逐字保留本地正文；其中可能夹有旧注、录入注及疑字，不能一概当作纯经文。代码框用于避免网页遗留符号被当成排版。\n\n```text\n'+text+'\n```')
        n = r.get('note', {})
        related = []
        # Only resolve unambiguous exact titles; do not invent conceptual equivalence.
        for title in re.split('[；;、，,]', n.get('related','')):
            matches = by_title.get(title.strip(), [])
            same = [x for x in matches if x['book'] == r['book']]
            if len(same)==1: related.append(link('章节/'+same[0]['id'],title.strip()))
            else: related.append(title.strip())
        body = [meta, f'# {r["chapter"]}', link('典籍/'+r['book'],BOOKS[r['book']])+' · '+link(raw,'完整原文'),
                f'状态：{r["review_status"]}；章级初读不等于细校通过。', '以下为现代研读笔记。']
        layers=layer_info(r['id'])
        body += ['## 文本层次',layers['notice']]
        for span in layers.get('spans',[]):
            body.append(f'- 原文第 {span["line"]} 行：{span["label"]}；`{span["text"]}`')
        for key, label in [('concepts','核心概念'),('quote','精确引文'),('explanation','白话解释'),('application','适用情境'),('uncertainty','疑点与边界')]:
            body += [f'## {label}', n.get(key,'待研读')]
        body += ['## 相关篇章', ' · '.join(related), '## 自己的补充', '个人批注请写入「个人批注」目录，以免下次生成覆盖；不要放入出生资料或倾诉内容。']
        write(note+'.md','\n\n'.join(body))
        if n.get('uncertainty'): doubts.append('- '+link(note,BOOKS[r['book']]+'·'+r['chapter'])+'：'+n['uncertainty'])
    for book, title in BOOKS.items():
        write('典籍/'+book+'.md', '\n\n'.join(['# '+title,link('首页','返回首页')]+['- '+link('章节/'+r['id'],r['chapter'])+'（'+r['review_status']+'）' for r in records if r['book']==book]))
    write('疑点索引.md','\n\n'.join(doubts))
    detail_links=[]
    for p in sorted((ROOT/'验收').glob('*细读.md')):
        target='细读/'+p.stem
        write(target+'.md',p.read_text(encoding='utf-8'))
        detail_links.append('- '+link(target,p.stem))
    write('细读索引.md','# 细读与规则复核\n\n'+ '\n\n'.join(detail_links))
    write('验收进度.md','# 验收进度\n\n研读记录更新时间：'+status['updated_at']+'\n\n技能已启用：'+str(status['enabled'])+'\n\n以下为验收任务原始状态快照；不能仅凭笔记数量认定可用。\n\n```json\n'+json.dumps(tasks,ensure_ascii=False,indent=2)+'\n```')
    write('首页.md','\n\n'.join(['# 道士 · 经典研读库','这是本地资料库的阅读视图，非心理诊疗服务。',f'章级初读：{sum(r["review_status"]=="reviewed" for r in records)}/{len(records)}。技能是否启用以主库验收为准。']+['- '+link('典籍/'+b,t) for b,t in BOOKS.items()]+[link('细读索引','新增细读与规则复核'),link('疑点索引','疑点与边界'),link('验收进度','验收进度'),link('使用说明','使用与更新方法')]))
    write('使用说明.md','# 使用说明\n\n在 Obsidian 选择「打开文件夹作为仓库」，选本目录，从首页开始。使用反向链接追查章节间联系，也可搜索全文。无需社区插件或同步账号。\n\n每章连接完整原文、来源修订号、现代解释、应用边界和明确匹配的相关篇章。原文副本与主库哈希一致；不把自动生成链接算作学习成果。\n\n后续先读主库原文、人工撰写研读笔记并校验，再生成本仓库。生成目录为章节、原文、典籍及首页等导航；请勿直接改这些派生文件。个人批注单独保存，重建不会覆盖。原始快照及正式验收仍以父目录为准。\n\n本仓库不会收集倾诉、出生信息，不自动发布或同步。\n\n来源、许可与改动说明见主库「书目与版本.md」；正文源自维基文库，保留 CC BY-SA 4.0 署名要求。\n\n[Obsidian 官方内部链接说明](https://help.obsidian.md/links)')
    guide = VAULT/'使用说明.md'
    guide.write_text(guide.read_text(encoding='utf-8').replace('仍以父目录为准','仍以 E:/国学/道士 为准'),encoding='utf-8')
    write('书目与版本.md',(ROOT/'书目与版本.md').read_text(encoding='utf-8').replace('(./原文/', '(file:///E:/国学/道士/原文/'))
    (VAULT/'个人批注').mkdir(exist_ok=True)
    cfg=VAULT/'.obsidian'; cfg.mkdir(exist_ok=True)
    if not (cfg/'app.json').exists():
        (cfg/'app.json').write_text(json.dumps({'alwaysUpdateLinks':True,'newFileLocation':'folder','newFileFolderPath':'个人批注'},ensure_ascii=False,indent=2),encoding='utf-8')
    missing = sorted({x for x in links if not (VAULT/(x+'.md')).exists()})
    assert not missing, missing
    report={'chapters':len(records),'original_copies_hash_checked':len(records),'internal_links_checked':len(links),'broken_links':missing,'vault':str(VAULT),'note':'派生阅读视图，不改变正式验收状态'}
    (ROOT/'验收/obsidian-build.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(report,ensure_ascii=False))

if __name__=='__main__': main()
