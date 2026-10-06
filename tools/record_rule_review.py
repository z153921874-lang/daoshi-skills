"""Persist this manually completed rule comparison and its executable examples."""
from collect import ROOT
import json,subprocess,hashlib
def main():
    result=subprocess.run(['E:/ai/node/node.exe',str(ROOT/'tools/test_classic_differences.cjs')],capture_output=True,text=True,encoding='utf-8',check=True)
    data=json.loads(result.stdout); assert data['passed']
    evidence=['验收/紫微规则差异细读.md','验收/classic-rule-tests.json']
    paths=evidence+['tools/test_classic_differences.cjs','tools/divination.cjs','tools/package-lock.json','skill/daoshi/references/calculation.md','原文/ziwei/chapters/ziwei-db430d6a02.txt']
    paths+=['tools/node_modules/iztro/lib/'+p for p in ['star/location.js','star/minorStar.js','star/decorativeStar.js','astro/palace.js','utils/index.js','data/heavenlyStems.js']]
    (ROOT/evidence[1]).write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
    hashes={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in paths}
    p=ROOT/'验收/final-review-tasks.json'; tasks=json.loads(p.read_text(encoding='utf-8'))
    check=next(x for x in tasks['checks'] if x['id']=='calculation_classic_differences')
    check.update(status='passed',assessment='逐条对读闰月、十干四化、长生、大限和天马的源文与固定源码；天马十二支一致，其余明确标注差异及解释限度；五组针对性运算检查通过，未扩称全部杂曜已独立验证。',evidence_paths=evidence,source_sha256=hashes)
    p.write_text(json.dumps(tasks,ensure_ascii=False,indent=2),encoding='utf-8')
    print('指定计算规则对读完成；紫微长篇、内经长篇、来源层次三项仍待细校。')
if __name__=='__main__':main()
