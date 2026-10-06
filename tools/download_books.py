from collect import *
from concurrent.futures import ThreadPoolExecutor, as_completed

jobs=[]
for book in BOOKS:
    index=json.loads((ROOT/'目录'/f'{book}.json').read_text(encoding='utf-8'))
    prefix={'zhouyi':'周易/','neijing':'黃帝內經/','meihua':'梅花易數/卷','ziwei':'紫微斗數全書/卷','zhuangzi':'莊子/'}.get(book)
    if prefix:
        jobs.extend((book,x['title']) for x in index['links'] if x['title'].startswith(prefix))
        if book=='meihua': jobs.append((book,index['title']))
    else: jobs.append((book,index['title']))

def task(item):
    book,title=item
    html,meta=fetch(title,book)
    return {'book':book,'title':title,**meta}

success=[]; errors=[]
with ThreadPoolExecutor(3) as pool:
    futures={pool.submit(task,j):j for j in jobs}
    for future in as_completed(futures):
        try:
            item=future.result();success.append(item);print('OK',item['book'],item['title'],flush=True)
        except Exception as e:
            item={'job':futures[future],'error':str(e)};errors.append(item);print('ERROR',item,flush=True)
manifest={'source':'Wikisource selected online editions','expected_pages':len(jobs),'pages':sorted(success,key=lambda x:(x['book'],x['title'])),'errors':errors}
(ROOT/'目录'/'download_manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
print('DONE',len(success),'errors',len(errors))
