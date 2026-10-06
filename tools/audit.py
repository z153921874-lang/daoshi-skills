"""Local evidence audit. No network, no personal inputs. Fail closed before release."""
from pathlib import Path
import argparse, hashlib, json, re, sys
from datetime import datetime, timezone
ROOT=Path(__file__).resolve().parents[1]
COUNTS={'zhouyi':69,'neijing':162,'meihua':124,'ziwei':89,'laozi':81,'zhuangzi':33,'qingjing':2,'zuowang':8}
SCENARIOS={'work_anxiety','relationship','ominous_hexagram','prescription','self_harm'}
FINAL_REVIEWS={'zhouyi_internal_sections','ziwei_long_sections','neijing_long_sections','source_layers_and_variants','calculation_classic_differences'}

def digest(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def read(path): return json.loads(path.read_text(encoding='utf-8'))
def save(path,data): path.write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
def local_path(rel):
    p=(ROOT/rel).resolve()
    if not p.is_relative_to(ROOT): raise ValueError('路径越出资料库')
    return p

def audit():
    blockers=[]; warnings=[]; files={}; stats={}; source_count=0; quote_count=0
    def track(p):
        p=p.resolve(); files[str(p.relative_to(ROOT)).replace('\\','/')]=digest(p)
    try:
        manifest=read(ROOT/'目录/download_manifest.json');index=read(ROOT/'目录/chapters.json');records=read(ROOT/'研读/records.json')
        if manifest['errors'] or len(manifest['pages'])!=manifest['expected_pages']:
            blockers.append('下载目录不完整或有失败记录')
        page_keys=set()
        for x in manifest['pages']:
            key=(x['book'],x['title'])
            if key in page_keys: blockers.append('重复下载目录条目：'+str(key))
            page_keys.add(key)
            p=local_path(x['raw_path']); track(p); source_count+=1
            if digest(p)!=x['sha256']: blockers.append('原始快照哈希变动：'+x['title'])
            if not all(x.get(k) for k in ['revision_id','retrieved_at','url','license_notice']): blockers.append('来源信息不全：'+x['title'])
            if not any('by-sa/4.0' in s for s in x.get('license_links',[])): blockers.append('授权待核：'+x['title'])
        ids=[x['id'] for x in index]
        if len(ids)!=len(set(ids)): blockers.append('重复章节编号')
        if set(x['id'] for x in records)!=set(ids) or len(records)!=len(index): blockers.append('研读记录与正文目录不同步')
        mapped={x['id']:x for x in records}
        for book,count in COUNTS.items():
            chapters=[x for x in index if x['book']==book]
            reviewed=sum(mapped.get(x['id'],{}).get('review_status')=='reviewed' for x in chapters)
            stats[book]={'total':len(chapters),'reviewed':reviewed}
            if len(chapters)!=count: blockers.append(f'{book} 目录数量变化：{len(chapters)}，预期 {count}，须重新核对版本')
            if reviewed!=len(chapters): blockers.append(f'{book} 尚有 {len(chapters)-reviewed} 个单元待研读')
        for x in index:
            p=local_path(x['path']);track(p);t=p.read_text(encoding='utf-8')
            if not t.strip() or '\ufffd' in t: blockers.append('空篇或替代乱码：'+x['id'])
            # Chapter and study manifests hash Unicode text with normalized LF.
            # Raw source snapshots and release files use exact byte hashes instead.
            text_sha=hashlib.sha256(t.encode('utf-8')).hexdigest()
            if text_sha!=x['sha256']: blockers.append('正文哈希变动：'+x['id'])
            if (x['book'],x['page_title']) not in page_keys: blockers.append('章节无下载来源：'+x['id'])
            r=mapped.get(x['id'],{})
            if r.get('review_status')=='reviewed':
                note=r.get('note',{})
                if r.get('reviewed_sha256')!=text_sha: blockers.append('笔记对应旧正文：'+x['id'])
                if not all(note.get(k) for k in ['concepts','explanation','application','quote','related','uncertainty']): blockers.append('笔记字段缺失：'+x['id'])
                q=note.get('quote','')
                if not q or q not in re.sub(r'\s+','',t): blockers.append('引文不符：'+x['id'])
                else: quote_count+=1
        # Evidence files are authored/reviewed separately, never synthesized into a pass by this audit.
        for filename in ['extraction-integrity.json','quote-spotchecks.json','scenario-checks.json','calculation-tests-current.json','skill-format.json']:
            p=ROOT/'验收'/filename
            if not p.exists(): blockers.append('缺验收凭据：'+filename);continue
            track(p);data=read(p)
            if filename=='extraction-integrity.json':
                if data.get('status')!='passed' or data.get('errors') or data.get('pages')!=len(manifest['pages']): blockers.append('原文提取覆盖检查未通过')
                for rel in ['tools/extract.py','tools/check_extraction.py','目录/chapters.json','目录/download_manifest.json']:
                    if data.get('source_sha256',{}).get(rel)!=digest(ROOT/rel): blockers.append('提取验收版本已变化：'+rel)
            elif filename=='quote-spotchecks.json':
                for b in COUNTS:
                    checks=[x for x in data.get('checks',[]) if x.get('book')==b and x.get('status')=='passed']
                    expected=2 if b=='qingjing' else 3
                    if len({x.get('id') for x in checks})<expected: blockers.append(b+' 引文和解释抽查未完成')
                    for check in checks:
                        r=mapped.get(check.get('id'),{})
                        if not r or check.get('reviewed_sha256')!=r.get('reviewed_sha256') or not check.get('assessment'): blockers.append('抽查无有效正文或解释记录：'+b)
            elif filename=='scenario-checks.json':
                passed={x.get('id') for x in data.get('checks',[]) if x.get('status')=='passed' and x.get('response') and x.get('assessment')}
                if not SCENARIOS.issubset(passed): blockers.append('五类谈话情景验收未完成')
                for rel,h in data.get('skill_sha256',{}).items():
                    if digest(local_path(rel))!=h: blockers.append('场景检验后技能已变化：'+rel)
                if not data.get('skill_sha256'): blockers.append('场景验收未绑定技能版本')
            elif filename=='skill-format.json':
                if data.get('status')!='passed' or data.get('skill_sha256')!=digest(ROOT/'skill/daoshi/SKILL.md') or data.get('interface_sha256')!=digest(ROOT/'skill/daoshi/agents/openai.yaml'): blockers.append('技能格式验收缺失或版本已变化')
            else:
                if data.get('passed')!=data.get('total') or data.get('total',0)<12: blockers.append('计算测试未全部通过')
                required=['tools/divination.cjs','tools/test_divination.cjs','tools/package-lock.json']
                if not all(data.get('source_sha256',{}).get(r)==digest(ROOT/r) for r in required): blockers.append('计算测试未绑定当前工具版本')
        # Chapter-level reading does not certify internal tables or textual layers.
        final_review=ROOT/'验收/final-review-tasks.json'
        if not final_review.exists():
            blockers.append('缺最终细项复核清单')
        else:
            track(final_review)
            checks=read(final_review).get('checks',[])
            for task in FINAL_REVIEWS:
                entries=[c for c in checks if c.get('id')==task]
                if len(entries)!=1:
                    blockers.append('最终细项复核缺失或重复：'+task);continue
                check=entries[0]
                if check.get('status')!='passed':
                    blockers.append('最终细项待复核：'+task);continue
                evidence=check.get('evidence_paths',[]); hashes=check.get('source_sha256',{})
                if not check.get('assessment') or not evidence or not hashes:
                    blockers.append('最终复核无充分证据：'+task);continue
                for rel in evidence:
                    p=local_path(rel)
                    if not p.is_file() or rel not in hashes: blockers.append('最终复核证据缺失或未绑定：'+rel)
                for rel,h in hashes.items():
                    p=local_path(rel)
                    if not p.is_file() or digest(p)!=h: blockers.append('最终复核版本已变化：'+rel)
                    else: track(p)
        # Include dependencies, sources, notes and skill assets in the release fingerprint.
        # The first Daozang supplement has its own index and content-bound review.
        import importlib.util
        extension=ROOT/'扩展/道藏首批'
        spec=importlib.util.spec_from_file_location('daozang_extension',extension/'library.py')
        module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        ext_result=module.validate()
        if ext_result['status']!='passed':blockers.extend('道藏扩展：'+e for e in ext_result['errors'])
        else:
            for rel in ext_result['files']:track(extension/rel)
            stats['daozang_extension']={'books':3,'total':27,'reviewed':27}
        for folder in ['skill/daoshi','研读']:
            for p in (ROOT/folder).rglob('*'):
                if p.is_file() and '__pycache__' not in p.parts: track(p)
        for p in (ROOT/'tools').glob('*'):
            if p.is_file(): track(p)
        for p in (ROOT/'tools/node_modules').rglob('*'):
            if p.is_file(): track(p)
        for rel in ['目录/chapters.json','目录/download_manifest.json','书目与版本.md']:
            track(ROOT/rel)
        warnings.append('所选网络录入本已发现异文和疑字；不等于影印底本逐字精校。')
        warnings.append('章节初读与可验证计算不等于永久训练模型或证明预测有效。')
    except (OSError,ValueError,KeyError,TypeError) as e:
        blockers.append('审计未完成：'+str(e))
    snapshot=hashlib.sha256(json.dumps(files,ensure_ascii=False,sort_keys=True).encode()).hexdigest()
    return {'updated_at':datetime.now(timezone.utc).isoformat(),'eligible':not blockers,'books':stats,'raw_pages_checked':source_count,'quotes_checked':quote_count,'blockers':blockers,'warnings':warnings,'snapshot_sha256':snapshot,'files':files}

def require_ready():
    try:
        state=read(ROOT/'目录/status.json'); release=read(ROOT/'验收/release.json')
        if state.get('status')!='ready' or state.get('enabled') is not True:
            return {'eligible':False,'blockers':['当前未启用；全部研读与验收完成后才允许个人计算。']}
        result=audit()
        if release.get('snapshot_sha256')!=result['snapshot_sha256'] or release.get('status')!='passed': result['blockers'].append('发布验收凭据缺失或已过期')
    except (OSError,ValueError): return {'eligible':False,'blockers':['尚无正式发布凭据']}
    result['eligible']=not result['blockers'];return result

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--write',action='store_true');p.add_argument('--seal',action='store_true');args=p.parse_args()
    result=audit()
    if args.write: save(ROOT/'验收/library-audit.json',result)
    if args.seal and result['eligible']:
        save(ROOT/'验收/release.json',{'status':'passed','created_at':result['updated_at'],'snapshot_sha256':result['snapshot_sha256']})
        state=read(ROOT/'目录/status.json');state.update(status='ready',enabled=True);save(ROOT/'目录/status.json',state)
    # No writes to release or status when blocked, even if --seal was requested.
    print(json.dumps({k:v for k,v in result.items() if k!='files'},ensure_ascii=False,indent=2))
    sys.exit(0 if result['eligible'] else 2)
