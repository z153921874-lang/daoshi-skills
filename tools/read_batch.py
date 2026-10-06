"""Print a bounded full-text reading batch; never silently truncates a chapter."""
from collect import ROOT
import argparse,json
p=argparse.ArgumentParser();p.add_argument('book');p.add_argument('--start',type=int,default=0);p.add_argument('--count',type=int,default=10);args=p.parse_args()
a=[x for x in json.loads((ROOT/'目录/chapters.json').read_text(encoding='utf-8')) if x['book']==args.book]
for i,x in list(enumerate(a))[args.start:args.start+args.count]:
    print(f"\n【{i} {x['id']} {x['chapter']}】\n"+(ROOT/x['path']).read_text(encoding='utf-8'))
