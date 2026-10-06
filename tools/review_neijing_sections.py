"""Build auditable anchors and check enumerations in the reread long chapters."""
import json,re,hashlib
from collect import ROOT
TITLES=['天元紀大論六十六','五運行大論六十七','六微旨大論六十八','氣交變大論六十九','五常政大論七十','六元正紀大論七十一','至真要大論七十四','氣穴論五十八','氣府論五十九','水熱穴論六十一','熱病第二十三','九宮八風第七十七']
def main():
    chapters=json.loads((ROOT/'目录/chapters.json').read_text(encoding='utf-8')); rows=[];texts={}
    for title in TITLES:
        c=next(x for x in chapters if x['book']=='neijing' and x['chapter']==title)
        text=(ROOT/c['path']).read_text(encoding='utf-8');texts[title]=text;offset=0
        for block in re.split(r'\n\s*\n',text):
            start=text.find(block,offset);end=start+len(block);offset=end
            if not block.strip():continue
            rows.append({'chapter':title,'id':c['id'],'path':c['path'],'start_line':text[:start].count('\n')+1,'end_line':text[:end].count('\n')+1,'anchor':block[:60]})
    six=texts['六元正紀大論七十一'];period=six[six.index('甲子甲午歲上'):six.index('凡此定期之紀')]
    pairs=re.findall(r'([甲乙丙丁戊己庚辛壬癸][子丑寅卯辰巳午未申酉戌亥])([甲乙丙丁戊己庚辛壬癸][子丑寅卯辰巳午未申酉戌亥])(?:歲)?上',period)
    assert len(pairs)==30 and len(set(sum((list(p) for p in pairs),[])))==60
    phases={phase:len(re.findall(phase+'之氣',six[:six.index('夫子言可謂悉矣')])) for phase in ['初','二','三','四','五','終']}
    assert set(phases.values())=={6}
    counts={'六元年对':pairs,'六政逐气数量':phases,'气府九组明列总数':sum([78,62,68,36,22,32,28,28,22]),'水热水俞':25+20+12,'水热热俞':25+8+8+8+10,'灵枢热病按所列小计足亦如是翻倍':(12+8)*2+6+10+6+1+1+1+1+2+2,'九宫八风居日':46*6+45*2,'五十营里程丈':162*50/10,'note':'算术复核不解决名目重叠、缺文及古度量含义；不作诊疗推算'}
    (ROOT/'目录/内经长篇索引.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2),encoding='utf-8')
    (ROOT/'验收/内经表组计数.json').write_text(json.dumps(counts,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({'段落索引':len(rows),'年对':len(pairs),'逐气':phases,'计数':counts},ensure_ascii=False))
if __name__=='__main__':main()
