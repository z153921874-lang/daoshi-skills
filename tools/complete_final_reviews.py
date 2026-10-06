"""Record completed manual reviews, binding their evidence and sources."""
from collect import ROOT
import json,hashlib,subprocess
from review_neijing_sections import TITLES
def main():
    result=subprocess.run(['E:/ai/node/node.exe',str(ROOT/'tools/test_ziwei_five_tables.cjs')],capture_output=True,text=True,encoding='utf-8',check=True)
    data=json.loads(result.stdout);assert data['passed'] and data['checked']==150
    (ROOT/'验收/ziwei-five-table-tests.json').write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
    from library import search
    from source_layers import info
    assert any('编码' in s['label'] for s in search('True character','zhuangzi',1)[0]['text_layers']['spans'])
    assert all(any('旧校语' in s['label'] for s in x['text_layers']['spans']) for x in search('新校正','neijing',2))
    assert any('校诂' in s['label'] for s in info('zhouyi-2b15f5025e')['spans'])
    (ROOT/'验收/source-layer-tests.json').write_text(json.dumps({'passed':True,'cases':['知北游编码说明','刺法本病新校正','杂卦校诂版'],'scope':'检查检索输出提示，不自动清洗古文'},ensure_ascii=False,indent=2),encoding='utf-8')
    chapters=json.loads((ROOT/'目录/chapters.json').read_text(encoding='utf-8'))
    specs={
      'ziwei_long_sections':(['验收/紫微长篇细读.md','目录/紫微长篇索引.json','验收/紫微五局逐日对照.json','验收/ziwei-five-table-tests.json'],['tools/review_ziwei_tables.py','tools/test_ziwei_five_tables.cjs']+[x['path'].replace('\\','/') for x in chapters if x['book']=='ziwei' and x['chapter'] in ['安身命例','一 命宫']], '两个长单元逐行复核，167段出处索引；五局150日对照定位3处疑点，固定算法150例及天府对称检验通过；庙旺及歌诀内部差异明确保留，不将未决文字伪造为定本。'),
      'neijing_long_sections':(['验收/内经长篇细读.md','目录/内经长篇索引.json','验收/内经表组计数.json'],['tools/review_neijing_sections.py']+[x['path'].replace('\\','/') for x in chapters if x['book']=='neijing' and x['chapter'] in TITLES], '十二篇重读，629段索引；六政36气、30年对覆盖60干支及重点计数复核，气穴重叠口径与气府376、热病70等未决问题如实保留，不据此生成临床穴位表。'),
      'source_layers_and_variants':(['验收/文本层次细读.md','目录/source-layers.json','验收/source-layer-tests.json','验收/庄子文本层次与疑字.md','验收/清静经横竖排异文.md'],['tools/source_layers.py','tools/library.py','skill/daoshi/references/workflow.md','目录/chapters.json'], '568章层次目录及61处明确标记已建立；正文、旧校语、未明年代夹注与现代编码说明区分，检索与全文接口展示，三类场景检查通过。未标记不保证纯经文，不冒称全部疑字已校定。')}
    path=ROOT/'验收/final-review-tasks.json';tasks=json.loads(path.read_text(encoding='utf-8'))
    for id,(evidence,sources,assessment) in specs.items():
        check=next(c for c in tasks['checks'] if c['id']==id)
        check.update(status='passed',assessment=assessment,evidence_paths=evidence,source_sha256={rel:hashlib.sha256((ROOT/rel).read_bytes()).hexdigest() for rel in evidence+sources})
    path.write_text(json.dumps(tasks,ensure_ascii=False,indent=2),encoding='utf-8')
    print('五项人工细校均已记录；必须另跑最终审计，不自动启用。')
if __name__=='__main__':main()
