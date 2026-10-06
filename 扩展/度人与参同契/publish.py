"""Verify acquisition and publish clearly pending reading pages into Obsidian."""
from pathlib import Path
import json,hashlib,re
ROOT=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 m=json.loads((ROOT/'目录/下载清单.json').read_text(encoding='utf-8'))
 errors=list(m['errors']);seen=set();hashes={};warnings=[]
 for r in m['pages']:
  if r['title'] in seen:errors.append('重复页面：'+r['title'])
  seen.add(r['title'])
  for name,field in [('raw_path','sha256'),('text_path','text_sha256')]:
   if sha(ROOT/r[name])!=r[field]:errors.append('哈希不符：'+r[name])
  text=(ROOT/r['text_path']).read_text(encoding='utf-8')
  if '\ufffd' in text:warnings.append('替代字符待校：'+r['title'])
  if len(text)<100:errors.append('页面异常短：'+r['title'])
  if r['role'] in ['卷正文页','章正文页','经注合刊页']:
   h=r['text_sha256']
   if h in hashes:errors.append('重复正文：'+r['title'])
   hashes[h]=r['title']
 for i in range(1,62):
  if f'靈寶無量度人上品妙經/{i}' not in seen:errors.append('缺度人卷'+str(i))
 for i in range(1,36):
  if f'周易參同契/{i:02}章' not in seen:errors.append('缺参同章'+str(i))
 if len(m['pages'])!=m['expected_pages']:errors.append('下载数量不足')
 report={'download_status':'passed' if not errors else 'failed','pages':len(m['pages']),'errors':errors,'warnings':warnings,'review_status':'pending','reviewed_units':0,'note':'仅验证所选目录页面齐备、字节一致与无重复文本；未宣称全文校勘或研读完成。'}
 (ROOT/'验收.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
 if errors:raise SystemExit(json.dumps(report,ensure_ascii=False))
 vault=Path('E:/Obsidian/道士');out=vault/'度人与参同契待研读';out.mkdir(exist_ok=True)
 lines=['# 度人经与参同契 · 待研读','', '已归档所选版本原文页面；尚未逐卷研读，不计入已完成的595单元。', '[[首页]] · [[道藏扩展入口]]','']
 labels={'duren':'度人经61卷','cantong':'参同契35章','peng':'彭晓分章通真义','zhu':'朱熹考异'}
 for k,label in labels.items():
  lines += ['## '+label,'']
  for r in [p for p in m['pages'] if p['book']==k]:
   filename=r['id'];t=(ROOT/r['text_path']).read_text(encoding='utf-8')
   content=f"# {r['title']}\n\n状态：待研读。{r['role']}。\n\n来源：[{r['title']}]({r['url']})；修订 {r['revision_id']}；下载 {r['retrieved_at']}。\n\n{r['license_notice']}\n\n{r['layer_notice']}\n\n[[度人与参同契入口]]\n\n```text\n{t}\n```\n"
   (out/(filename+'.md')).write_text(content,encoding='utf-8')
   assert t in (out/(filename+'.md')).read_text(encoding='utf-8')
   lines.append(f"- [[度人与参同契待研读/{filename}|{r['title']}]]")
 entry=vault/'度人与参同契入口.md';entry.write_text('\n'.join(lines)+'\n\n'+(ROOT/'阅读总览.md').read_text(encoding='utf-8'),encoding='utf-8')
 for name in ['首页.md','道藏扩展入口.md']:
  p=vault/name;s=p.read_text(encoding='utf-8')
  if '[[度人与参同契入口]]' not in s:p.write_text(s+'\n\n[[度人与参同契入口]]：新收录，待逐卷研读。\n',encoding='utf-8')
 for link in re.findall(r'\[\[([^\]|]+)(?:\|[^\]]+)?\]\]',entry.read_text(encoding='utf-8')):
  assert (vault/(link+'.md')).exists(),link
 print(json.dumps(report,ensure_ascii=False));print('Obsidian全文副本和入口链接核验通过')
if __name__=='__main__':main()
