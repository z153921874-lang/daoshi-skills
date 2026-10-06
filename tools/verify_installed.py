"""Read-only installed skill comparison and synthetic public-interface smoke checks."""
from collect import ROOT
from pathlib import Path
import json,subprocess,sys,hashlib,os
from datetime import datetime,timezone
def main():
    source=ROOT/'skill/daoshi';installed=Path('C:/Users/USER/.codex/skills/daoshi')
    files={}
    for p in source.rglob('*'):
        if not p.is_file() or '__pycache__' in p.parts:continue
        rel=p.relative_to(source);target=installed/rel
        assert target.read_bytes()==p.read_bytes(),str(rel)
        files[str(rel)]=hashlib.sha256(p.read_bytes()).hexdigest()
    env={**os.environ,'PYTHONUTF8':'1','PYTHONPATH':str(ROOT/'tools/vendor')}
    validator='C:/Users/USER/.codex/skills/.system/skill-creator/scripts/quick_validate.py'
    valid=subprocess.run([sys.executable,validator,str(installed)],env=env,capture_output=True,text=True,encoding='utf-8',check=True)
    entry=installed/'scripts/entry.py'
    check=subprocess.run([sys.executable,str(entry),'check'],env=env,capture_output=True,text=True,encoding='utf-8',check=True)
    calc=subprocess.run([sys.executable,str(entry),'calculate'],input=json.dumps({'method':'meihua','mode':'numbers','upperNumber':8,'lowerNumber':16}),env=env,capture_output=True,text=True,encoding='utf-8',check=True)
    result=json.loads(calc.stdout);assert result['movingLine']==6
    report={'status':'passed','tested_at':datetime.now(timezone.utc).isoformat(),'installed':str(installed),'files':files,'format':valid.stdout.strip(),'entry':check.stdout.strip(),'synthetic_calculation':'公开双数8、16经已安装入口计算，动爻6；无个人信息','limits':'模板场景走查是人工检查，不是临床研究或独立模型评测。'}
    (ROOT/'验收/安装核验.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(report,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
