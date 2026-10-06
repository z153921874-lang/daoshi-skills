"""Render reviewed notes and report real coverage. Pending items stay pending."""
from collect import ROOT, BOOKS
from study_data import AUTHORED
from study_zhouyi import AUTHORED_ZHOUYI
from study_meihua import AUTHORED_MEIHUA
from study_ziwei import AUTHORED_ZIWEI
from study_ziwei_remaining import AUTHORED_ZIWEI_REMAINING
from study_zhuangzi import AUTHORED_ZHUANGZI
from study_neijing import AUTHORED_NEIJING
AUTHORED['zhouyi']=AUTHORED_ZHOUYI
AUTHORED['meihua']=AUTHORED_MEIHUA
AUTHORED['ziwei']={**AUTHORED_ZIWEI,**AUTHORED_ZIWEI_REMAINING}
AUTHORED['zhuangzi']=AUTHORED_ZHUANGZI
AUTHORED['neijing']=AUTHORED_NEIJING
import json, re, argparse, hashlib
from datetime import datetime, timezone

def main():
    index=json.loads((ROOT/'目录/chapters.json').read_text(encoding='utf-8'))
    out=ROOT/'研读';out.mkdir(exist_ok=True)
    records=[];errors=[]
    for book,title in BOOKS.items():
        docs=[f'# {title}：章级研读记录\n\n以下解释与应用由助手编写，不是古籍原文；引用来自本地所选网络录入本。\n']
        for chapter in [x for x in index if x['book']==book]:
            note=AUTHORED.get(book,{}).get(chapter['chapter'])
            if not note:
                records.append({**chapter,'review_status':'pending'});continue
            text=(ROOT/chapter['path']).read_text(encoding='utf-8')
            if note['quote'] not in re.sub(r'\s+','',text):errors.append(chapter['id']+' 引文不匹配');continue
            record={**chapter,'review_status':'reviewed','review_level':'章级初读：已读本地正文并写出解释；非全注本精校或学术定论',
                'reviewed_sha256':hashlib.sha256(text.encode()).hexdigest(),'note':note}
            records.append(record)
            docs.append(f"## {chapter['chapter']}\n\n原文：[本地正文](../{chapter['path'].replace(chr(92),'/')})；[来源]({chapter['url']})，修订 {chapter['revision_id']}。\n\n- 概念：{note['concepts']}。\n- 引文：『{note['quote']}』。\n- 白话解释：{note['explanation']}\n- 应用：{note['application']}\n- 关联：{note['related']}。\n- 疑点或边界：{note['uncertainty']}。\n")
        (out/(book+'.md')).write_text('\n'.join(docs),encoding='utf-8')
    if errors:raise ValueError(errors)
    (out/'records.json').write_text(json.dumps(records,ensure_ascii=False,indent=2),encoding='utf-8')
    stats={b:{'total':sum(x['book']==b for x in records),'reviewed':sum(x['book']==b and x['review_status']=='reviewed' for x in records)} for b in BOOKS}
    result={'updated_at':datetime.now(timezone.utc).isoformat(),'enabled':False,'status':'studying' if any(x['review_status']=='pending' for x in records) else 'awaiting_validation','books':stats,'pending_ids':[x['id'] for x in records if x['review_status']=='pending']}
    (ROOT/'目录/status.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(stats,ensure_ascii=False))
if __name__=='__main__':main()
