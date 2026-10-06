"""Publish source inventory and truthful progress without converting pending work to completed."""
from collect import ROOT,BOOKS
import json
from collections import Counter

def main():
    manifest=json.loads((ROOT/'目录/download_manifest.json').read_text(encoding='utf-8'))
    status=json.loads((ROOT/'目录/status.json').read_text(encoding='utf-8'))
    records=json.loads((ROOT/'研读/records.json').read_text(encoding='utf-8'))
    notes={'zhouyi':'64卦经传合刊，含彖象及乾坤文言；另列系辞上、系辞下、说卦、序卦、杂卦。69个篇级单元，不将传文内部小章伪报成独立精读。另存独立彖、大小象、文言快照，因重复及录入疑字不作主读本。',
    'neijing':'所选素问24卷、灵枢12卷，分别提取81篇。刺法、本病等传承层次须在研读时核查；网络版本不作出土古本保证。',
    'meihua':'根页序与附录加卷一至三，按页面小标题共124单元；正文有显著录字与算例差异，逐条见研读疑点。',
    'ziwei':'卷一至三网络录入本，含罗序及各赋、问答、安星法，共89单元；题署归属与不同流派须分别说明。',
    'laozi':'王弼本81章。正文与尖括号旧注分离；合刊原文另存。初读覆盖经文，不声称已精读全部王弼注和附音义。',
    'zhuangzi':'内外杂33篇，采用各篇页面正文；尚不包含郭象注、成玄英疏的全套研读。',
    'qingjing':'正文及附言2单元；剔除网页重复竖排展示，原始页面仍保留。',
    'zuowang':'序加信敬、断缘、收心、简事、真观、泰定、得道七篇，共8单元。'}
    md=['# 道士资料库：书目与版本','\n本库使用维基文库选定网络录入本。古籍原作年代久远，正文与历史注释按其古典来源保存；维基文库贡献者的录入整理，依下载页面声明保留署名与 CC BY-SA 4.0 信息。未下载商业现代译注，未以本库自写解释冒充古文。\n',
    '[维基文库使用条款](https://foundation.wikimedia.org/wiki/Policy:Terms_of_Use/zh) · [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/deed.zh)\n',
    '归属：各页面所署古代作者/编者及维基文库贡献者。页面标题和来源链接见下表；每页修订号可拼接 `https://zh.wikisource.org/w/index.php?oldid=修订号` 查阅相应版本，历史页可查看贡献记录。\n',
    '改动声明：从 HTML 提取正文、删导航与重复展示、按标题拆章；道德经分离旧注。原始字形不改。相关疑字未静默校正。研读笔记为助手在本任务编写的现代解释；对来源文本的引用与改编保留相同授权说明。\n',
    '复用前请保留书名、页面来源、贡献者归属、许可链接和改动说明；不要冒称获得机构背书。网页图片与商标不属于本次正文复用范围。\n']
    for book,title in BOOKS.items():
        root=json.loads((ROOT/'目录'/f'{book}.json').read_text(encoding='utf-8'))
        pages=[x for x in manifest['pages'] if x['book']==book]
        md += [f'## {title}（{book}）\n',f"[目录与所选版本]({root['meta']['url']})。{notes[book]}\n",'| 下载页 | 修订号 | 下载时间（UTC） | 原始快照 |\n|---|---|---|---|']
        for x in pages:
            md.append(f"| [{x['title']}]({x['url']}) | {x['revision_id']} | {x['retrieved_at']} | [{x['raw_path']}](./{x['raw_path'].replace(chr(92),'/')}) |")
    (ROOT/'书目与版本.md').write_text('\n'.join(md)+'\n',encoding='utf-8')
    done=sum(x['reviewed'] for x in status['books'].values());total=sum(x['total'] for x in status['books'].values())
    report=['# 道士建设进度',f"\n更新：{status['updated_at']}。当前状态：**{'已启用' if status['enabled'] else '尚未启用'}**。\n",f'已完成章级初读及精确引文匹配 **{done}/{total}** 个单元。这是外部资料研读记录，不是模型训练，也不是全部底本的学术精校。\n','| 典籍 | 已初读 | 目录单元 | 笔记 |\n|---|---:|---:|---|']
    for b,t in BOOKS.items():
        s=status['books'][b];report.append(f"| {t} | {s['reviewed']} | {s['total']} | [研读记录](./研读/{b}.md) |")
    report += ['\n## 已落地\n',f"- 原始页面：{len(manifest['pages'])}/{manifest['expected_pages']}，下载错误：{len(manifest['errors'])}；见[书目与版本](./书目与版本.md)。",'- 梅花与固定版本紫微计算工具已建；结果与原典、独立安星规则及公开例对照。最新结果见[计算校验](./验收/calculation-tests-current.json)。', '- 技能草稿及入口见[道士说明](./skill/daoshi/SKILL.md)，没有安装到个人技能目录。','\n## 尚需完成\n','1. 所有 pending 篇章的完整阅读、针对性笔记与引文校验；传文内部章节还须进一步细化复核。','2. 每部至少三处引文与解释抽查，短篇全检；必要的疑字和算例校勘处理。','3. 五类谈心情景与所有工具、技能格式、资料完整性验收。','4. 全通过后生成发布凭据，再安装到 `C:/Users/USER/.codex/skills/daoshi`。','\n## 下一批从这里接续\n']
    pending=[x for x in records if x['review_status']=='pending']
    tasks=json.loads((ROOT/'验收/final-review-tasks.json').read_text(encoding='utf-8'))['checks']
    report += ['\n章级待读：'+str(len(pending))+'；最终细项已完成：'+str(sum(x['status']=='passed' for x in tasks))+'/'+str(len(tasks))+'。以下任务状态为当前接续依据。\n']
    for task in tasks:
        report.append('- '+task['id']+'：'+task['status']+'。'+task['assessment'])
    for x in pending[:8]: report.append(f"- {BOOKS[x['book']]}：{x['chapter']}（{x['id']}）")
    report += ['\n完整待办保存在 `目录/status.json` 的 pending_ids。未创建自动任务，未额外保存倾诉或出生资料。','\n## 验收后用法示例\n','- `$daoshi 我工作压力很大，先陪我梳理，不用起卦。`','- `$daoshi 读一读道德经第四十四章，区分原意与现代应用。`','- `$daoshi 按双数约定，用 8 和 16 起卦，展示计算过程。`','- `$daoshi 我想了解紫微排盘，先告诉我哪些出生信息不可缺。`']
    if done==total:
        report=[s.replace('1. 所有 pending 篇章的完整阅读、针对性笔记与引文校验；传文内部章节还须进一步细化复核。','1. 章级初读已完成；具体细校结果见下列五项任务。').replace('2. 每部至少三处引文与解释抽查，短篇全检；必要的疑字和算例校勘处理。','2. 引文抽查已保存；未决异文与数字冲突见细读报告，不代表无疑点定本。').replace('3. 五类谈心情景与所有工具、技能格式、资料完整性验收。','3. 最终发布须通过当前版本的工具、场景、格式和资料完整性审计。') for s in report]
    if status['enabled']:
        report=[s.replace('没有安装到个人技能目录。','安装结果另见验收目录的安装核验记录。').replace('## 尚需完成','## 验收说明').replace('4. 全通过后生成发布凭据，再安装到 `C:/Users/USER/.codex/skills/daoshi`。','4. 已生成发布凭据，安装路径为 `C:/Users/USER/.codex/skills/daoshi`；文件改动后需要重新验收。') for s in report]
    (ROOT/'建设进度.md').write_text('\n'.join(report)+'\n',encoding='utf-8')
    chapter_md=['# 全部章节目录','\n以本目录和 JSON 索引为准，未引用的旧提取文件不计入覆盖。初读记录与原文分别列示。\n']
    for book,title in BOOKS.items():
        chapter_md += [f'## {title}\n','| 篇章单元 | 初读状态 | 字符数 | 本地原文 |\n|---|---|---:|---|']
        for x in records:
            if x['book']==book:
                state='已初读' if x['review_status']=='reviewed' else '待研读'
                chapter_md.append(f"| {x['chapter']} | {state} | {x['chars']} | [{x['id']}](./{x['path'].replace(chr(92),'/')}) |")
    (ROOT/'章节目录.md').write_text('\n'.join(chapter_md)+'\n',encoding='utf-8')
    print(f'书目与真实覆盖报告已更新：{done}/{total}')
    from build_obsidian import main as update_obsidian
    update_obsidian()

if __name__=='__main__':main()
