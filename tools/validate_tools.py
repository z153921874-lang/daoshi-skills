"""Run real calculation tests and skill-format checks, bind evidence to tested sources."""
from collect import ROOT
import hashlib,json,os,subprocess,sys
from datetime import datetime,timezone
import yaml

def sha(rel):return hashlib.sha256((ROOT/rel).read_bytes()).hexdigest()
def write(name,data):
    (ROOT/'验收'/name).write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')

def main():
    env={**os.environ,'PYTHONUTF8':'1','PYTHONPATH':str(ROOT/'tools/vendor')}
    calc=subprocess.run(['E:/ai/node/node.exe',str(ROOT/'tools/test_divination.cjs')],capture_output=True,text=True,encoding='utf-8')
    if calc.returncode or not calc.stdout.strip():raise RuntimeError(calc.stdout+calc.stderr)
    result=json.loads(calc.stdout)
    result.update(tested_at=datetime.now(timezone.utc).isoformat(),source_sha256={p:sha(p) for p in ['tools/divination.cjs','tools/test_divination.cjs','tools/package-lock.json']})
    write('calculation-tests-current.json',result)
    validator='C:/Users/USER/.codex/skills/.system/skill-creator/scripts/quick_validate.py'
    format_result=subprocess.run([sys.executable,validator,str(ROOT/'skill/daoshi')],capture_output=True,text=True,encoding='utf-8',env=env)
    interface=yaml.safe_load((ROOT/'skill/daoshi/agents/openai.yaml').read_text(encoding='utf-8'))
    assert interface['interface']['display_name']=='道士'
    assert 25<=len(interface['interface']['short_description'])<=64
    assert '$daoshi' in interface['interface']['default_prompt']
    assert interface['policy']['allow_implicit_invocation'] is False
    if format_result.returncode:raise RuntimeError(format_result.stdout+format_result.stderr)
    write('skill-format.json',{'status':'passed','tested_at':result['tested_at'],'validator':validator,'result':format_result.stdout.strip(),'interface':'UTF-8 YAML、中文名称、描述长度、显式调用提示与策略检查通过','skill_sha256':sha('skill/daoshi/SKILL.md'),'interface_sha256':sha('skill/daoshi/agents/openai.yaml')})
    print(f"计算：{result['passed']}/{result['total']}；技能格式：通过。尚不等于全部服务验收。")

if __name__=='__main__':main()
