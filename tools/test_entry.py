"""Check usable offline search and that incomplete research cannot be released or calculated."""
from collect import ROOT
import subprocess,sys,json,hashlib
from datetime import datetime,timezone

entry=ROOT/'skill/daoshi/scripts/entry.py'
def run(*args,input=None):return subprocess.run([sys.executable,str(entry),*args],input=input,capture_output=True,text=True,encoding='utf-8')
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    state_path=ROOT/'目录/status.json';state=json.loads(state_path.read_text(encoding='utf-8'))
    assert state['enabled'] is False, '这个测试用于建设状态；发布后改用已启用入口的验收场景'
    results=[]
    r=run('search','知止','--book','laozi','--limit','2')
    assert r.returncode==0 and '四十四章' in r.stdout,(r.stdout,r.stderr)
    results.append({'name':'离线简繁检索返回道德经第四十四章','status':'passed'})
    r=run('chapter','qingjing-6df5b33e1a')
    assert r.returncode==0 and '真常應物' in r.stdout
    results.append({'name':'可按编号读取完整经典，不受个人服务关闭影响','status':'passed'})
    r=run('calculate',input='{"method":"meihua","mode":"numbers","upperNumber":8,"lowerNumber":16}')
    assert r.returncode==2 and '未启用' in r.stderr and '本卦' not in r.stdout
    results.append({'name':'未验收入口拒绝个人计算，不消耗输入形成卦象','status':'passed'})
    before=sha(state_path);release=ROOT/'验收/release.json';prior=release.read_bytes() if release.exists() else None
    r=subprocess.run([sys.executable,str(ROOT/'tools/audit.py'),'--seal'],capture_output=True,text=True,encoding='utf-8')
    assert r.returncode==2 and sha(state_path)==before
    assert (release.read_bytes() if release.exists() else None)==prior
    results.append({'name':'有待研读项时不能生成发布凭据，状态不变','status':'passed'})
    audit_result=json.loads(r.stdout)
    checks=json.loads((ROOT/'验收/final-review-tasks.json').read_text(encoding='utf-8'))['checks']
    pending={x['id'] for x in checks if x['status']!='passed'}
    assert pending and all('最终细项待复核：'+task in audit_result['blockers'] for task in pending)
    results.append({'name':'篇内复核和版本层次未验收时，发布闸门明确阻止启用','status':'passed'})
    report={'tested_at':datetime.now(timezone.utc).isoformat(),'passed':len(results),'total':len(results),'results':results,'source_sha256':{str(p.relative_to(ROOT)):sha(p) for p in [entry,ROOT/'tools/audit.py',ROOT/'tools/library.py']}}
    (ROOT/'验收/entry-tests.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(report,ensure_ascii=False,indent=2))

if __name__=='__main__':main()
