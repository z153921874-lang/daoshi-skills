"""Expose source-layer labels without silently editing quoted source text."""
from collect import ROOT
import json,re,hashlib

RULES=[
 ('页面异文校记，注者年代未核',r'一作「[^」]+」'),
 ('页面现代字符编码说明',r'↑True character[^\n]+'),
 ('来源标为新校正的旧校语，不是经文',r'（新校正[^）]+）'),
 ('页面错简提示，注者年代未核',r'（\*以下文義不屬，當有錯簡\*）'),
 ('网页强调标记残留',r'==[^=\n]+=='),
 ('缺字或补字标记，未校定',r'■\{[^}]+\}|【】'),
 ('页面补释或脚注标记，年代未核',r'\[[^\[\]\n]+\]'),
 ('字形替换校记，年代未核',r'\([^()\n]{1,8}\)\[[^\[\]\n]+\]'),
 ('字形构件说明或音注，不与正文连引',r'〈[^〉]+〉|（音[^）]+）'),
]

def info(chapter_id):
    path=ROOT/'目录/source-layers.json'
    if not path.exists():return {'notice':'尚未加载文本层次目录，引用须回看原始页面。'}
    data=json.loads(path.read_text(encoding='utf-8'))
    return data['chapters'].get(chapter_id,{'notice':'无已登记夹注不表示无疑字；仍须回查正文语境。'})

def main():
    chapters=json.loads((ROOT/'目录/chapters.json').read_text(encoding='utf-8'));catalog={}
    for c in chapters:
        text=(ROOT/c['path']).read_text(encoding='utf-8');spans=[]
        for label,pattern in RULES:
            for m in re.finditer(pattern,text):
                spans.append({'label':label,'start':m.start(),'end':m.end(),'line':text[:m.start()].count('\n')+1,'text':m.group()})
        if c['book']=='zhouyi' and text.startswith('←'):
            end=text.index('\n\n')
            spans.append({'label':'网页导航与作者年代题署，不作传文或确定作者证据','start':0,'end':end,'line':1,'text':text[:end]})
        for m in re.finditer(r'本作品收錄於[^\n]+',text):
            spans.append({'label':'网页收录元数据','start':m.start(),'end':m.end(),'line':text[:m.start()].count('\n')+1,'text':m.group()})
        if c['chapter']=='雜卦':
            start=text.index('校詁版');spans.append({'label':'独立校诂版，不能与前面一篇混引','start':start,'end':len(text),'line':text[:start].count('\n')+1,'text':'校詁版（至篇末）'})
        notice='所选来源正文层；引文保留字形。标记探测只是辅助，并不证明未标处均为纯经文。'
        if c['book']=='laozi':notice='本索引为王弼本经文；尖括号旧注已在提取时分开，原始合刊另存，未声称研读全套王注。'
        if c['book']=='qingjing' and c['id']=='qingjing-38f3323db3':notice='葛玄、左玄真人、正一真人附言层，非经文主段；题署不等于已核实成书年代。'
        if '遺篇' in text:notice+=' 本页包含遗篇层，须与新校正失篇说明区分，不当作无争议的早期完整原文。'
        catalog[c['id']]={'notice':notice,'source_sha256':c['sha256'],'spans':sorted(spans,key=lambda x:x['start'])}
    out={'offset_unit':'LF规范化Unicode字符，start含end不含；不是UTF8字节偏移','method':'明确标记类型人工审定；具体出现位置按模式登记，未覆盖所有隐性校记','chapters':catalog}
    (ROOT/'目录/source-layers.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({'chapters':len(catalog),'marked_spans':sum(len(v['spans']) for v in catalog.values())}))
if __name__=='__main__':main()
