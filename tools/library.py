"""Offline text search with simplified/traditional matching and exact source links."""
from collect import ROOT, BOOKS
import argparse,json,re
from opencc import OpenCC
from source_layers import info as layer_info
cc=OpenCC('t2s')
def search(query,book=None,limit=8):
    if not query.strip():raise ValueError('检索词不能为空')
    query=cc.convert(query);terms=query.split();index=json.loads((ROOT/'目录/chapters.json').read_text(encoding='utf-8'));hits=[]
    for x in index:
        if book and x['book']!=book:continue
        raw=(ROOT/x['path']).read_text(encoding='utf-8');text=cc.convert(raw);title=cc.convert(x['chapter']);matched=[t for t in terms if t in text or t in title]
        if not matched:continue
        score=sum(text.count(t)+5*title.count(t) for t in matched)+len(matched)*10
        term=next((t for t in matched if t in text),None)
        pos=text.find(term) if term else 0
        # Converter may change length: locate the original paragraph by converting each paragraph.
        paragraph=next((p for p in raw.split('\n\n') if term and term in cc.convert(p)),raw[:500])
        hits.append({**x,'score':score,'excerpt':paragraph[:1200],'excerpt_truncated':len(paragraph)>1200,'absolute_path':str(ROOT/x['path']),'text_layers':layer_info(x['id'])})
    return sorted(hits,key=lambda x:-x['score'])[:limit]
def main():
    p=argparse.ArgumentParser();p.add_argument('query',nargs='?');p.add_argument('--book',choices=BOOKS);p.add_argument('--limit',type=int,default=8);p.add_argument('--chapter');p.add_argument('--status',action='store_true');args=p.parse_args()
    if args.status: print((ROOT/'目录/status.json').read_text(encoding='utf-8'));return
    if args.chapter:
        data=json.loads((ROOT/'目录/chapters.json').read_text(encoding='utf-8'))
        x=next((x for x in data if x['id']==args.chapter),None)
        if not x:raise ValueError('找不到该章节编号')
        print(json.dumps({**x,'text_layers':layer_info(x['id'])},ensure_ascii=False));print((ROOT/x['path']).read_text(encoding='utf-8'));return
    if not args.query: p.error('请提供检索词、--chapter 或 --status')
    if not 1<=args.limit<=30:p.error('limit须为1至30')
    print(json.dumps(search(args.query,args.book,args.limit),ensure_ascii=False,indent=2))
if __name__=='__main__':main()
