"""Offline skill entry. Personal calculations require current release evidence."""
import argparse, json, shutil, subprocess, sys
from pathlib import Path
ROOT=Path('E:/国学/道士')
sys.path.insert(0,str(ROOT/'tools'))
from audit import require_ready

def main():
    p=argparse.ArgumentParser();s=p.add_subparsers(dest='action',required=True)
    s.add_parser('status');s.add_parser('check');s.add_parser('calculate')
    q=s.add_parser('search');q.add_argument('query');q.add_argument('--book');q.add_argument('--limit',type=int,default=5)
    c=s.add_parser('chapter');c.add_argument('id');a=p.parse_args()
    if a.action=='status':
        state=json.loads((ROOT/'目录/status.json').read_text(encoding='utf-8'))
        print(json.dumps({k:v for k,v in state.items() if k!='pending_ids'},ensure_ascii=False,indent=2));return 0
    if a.action in ['check','calculate']:
        evidence=require_ready()
        if not evidence['eligible']:
            print(json.dumps({'enabled':False,'message':'研读与验收尚未全部完成，个人服务未启用。','pending':evidence['blockers']},ensure_ascii=False),file=sys.stderr);return 2
        if a.action=='check': print('验收与文件版本一致，可以使用。');return 0
        node=Path('E:/ai/node/node.exe');exe=str(node) if node.exists() else shutil.which('node')
        if not exe: raise RuntimeError('没有可用的 Node.js，请先恢复本地工具运行环境。')
        # Child inherits stdin/stdout; no temporary file and no personal command-line args.
        return subprocess.run([exe,str(ROOT/'tools/divination.cjs')]).returncode
    cmd=[sys.executable,str(ROOT/'tools/library.py')]
    if a.action=='chapter': cmd+=['--chapter',a.id]
    else:
        cmd += [a.query,'--limit',str(a.limit)]
        if a.book: cmd+=['--book',a.book]
    return subprocess.run(cmd).returncode

if __name__=='__main__':
    try: sys.exit(main())
    except (OSError,ValueError,RuntimeError) as e: print(str(e),file=sys.stderr);sys.exit(2)
