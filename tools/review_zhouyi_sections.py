"""Render manually reviewed section notes with exact local line anchors."""
import json,re,hashlib
from collect import ROOT

NOTES={
'繫辭上':[
'天地刚柔至乾坤易简：由宇宙分类转入德业，不将尊卑视作现代人的价值高低。',
'设卦系辞与居动观玩：吉凶悔吝在传统象占体系中说明，不是心理测量。',
'彖爻辞位与善补过：无咎不等于从未犯错，可作改错的有限类比。',
'天地幽明、精气游魂与仁：记录古代宇宙观，不证实鬼神经验。',
'一阴一阳、生生、成象效法：占与事与神分别定义，不混为实证规律。',
'乾专直、坤翕辟与广大：象征乾坤动静，非男女心理定型。',
'崇德广业、知崇礼卑：解释德行修养语境，不作服从或自贬要求。',
'拟象观动与拟议；依次解中孚、同人、大过、谦、乾、节、解七例。末段冶容诲淫是历史责任观，不转为责备受害者。',
'天地数55、大衍50用49、四营十八变及策数：属于蓍法；216+144=360，(216+144)*32=11520。不能把360当精确回归年或当梅花算法。',
'辞变象占四道及精变神：四种用途有别，问答如响属于传统论述，非有效性验证。',
'开物成务、阖辟通变、太极两仪四象八卦及河洛：本文没有给出今日常见河图洛书图形的完整数阵。',
'天助顺人助信、言象意、道器变通：末再述象爻与人德行；言不尽意不等于允许编写原文。'],
'繫辭下':[
'重卦爻象与刚柔变通，接生位仁财义：篇首同时涉及政治伦理，不缩为起卦说明。',
'包牺至书契的制器取象链：离益噬嗑乾坤涣随豫小过睽大壮大过夬；保留末处周易/夬网页残留，不作考古事实。',
'象彖爻定义及阳卦多阴阴卦多阳：一君二民等是古代政治类比，不据此贬低阴或女性。',
'咸困解噬嗑否鼎豫复损益等爻辞与子曰：包括屈伸、待时、积善恶、居安思危、任重、知几、改过、安身后动，死期断语不能落在人身上。',
'乾坤为门、名小类大与衰世：论述命名取类的解释空间，不支持无限附会。',
'履谦复恒损益困井巽九卦，分别列德之作用、性质、行动三组；不能只摘第一组冒充全章。',
'唯变所适及原始要终：兼论初上爻与中爻；不是无规则随意解释。',
'二四三五位差，三才六画，再论殷周忧危背景：不能简化为二必吉三必凶。',
'乾健坤顺、情迁利害及言辞性情：末尾叛者辞惭等不能用作测谎或人格诊断；诸侯之虑等所选字形保留。'],
'說卦':[
'生蓍倚数、阴阳刚柔与性命：成卦理论语境。',
'天地人三才各两分，六画六位：人道仁义与天道阴阳并非同义词。',
'天地山泽雷风水火对举与逆数：与第五章方位次序分开；本段未直接题先天八卦图。',
'雷动风散雨润日烜及艮止兑说乾君坤藏：是作用类象。',
'帝出震至成艮，配方位时序；明列震东巽东南离南乾西北坎北艮东北，坤养兑秋语句不能冒充原文已逐一写全八方向。',
'神妙万物与雷风火泽水艮：重在作用配合，不说神秘力量已被证明。',
'健顺动入陷丽止说八德：与日常同字意义分别解释。',
'马牛龙鸡豕雉狗羊八动物：符号配属不是动物预测。',
'首腹足股耳目手口八身体类象：不能据卦诊病。',
'父母长中少男女与一二三索：古代家族类象，不限定现实家庭身份。',
'乾至兑八类长表，涵盖物、人、马、木、地等子类；寡发近利心病盗等不作现实性格疾病财运证据。'],
'序卦':[
'上篇由天地生物至屯蒙需讼师比，沿聚畜礼通否、同人大有谦豫、随蛊临观噬嗑贲、剥复无妄大畜颐大过坎离。解释卦序，不是个人成长必经阶段。',
'下篇从天地男女夫妇社会关系起，再自恒至未济；咸未在开篇直书卦名。关系伦理是古代论述，不规定现代人的婚育选择。'],
'雜卦':[
'一篇：对举卦义，末八卦并非简单按今卦序两两紧邻；保留蒙杂、随无故、亲寡旅、小人道消所选字句。',
'校诂版：独立版本层，蒙稚、随无事、旅寡亲、小人道忧与前文不同。来源未充分说明，不自动以此改正正文。']}

def main():
    records=json.loads((ROOT/'目录/chapters.json').read_text(encoding='utf-8'))
    rows=[]; hashes={}; md=['# 周易传文内部细读复核','本轮逐段重读所选五篇全文。章号遵从所选网络版本，以下为现代解释，不是补写经文。导航、作者题署、收录信息和孤立标点不是传文。孔子题署只记作页面署名，不据此判定现代学术作者归属。']
    for title,notes in NOTES.items():
        r=next(x for x in records if x['book']=='zhouyi' and x['chapter']==title)
        p=ROOT/r['path']; lines=p.read_text(encoding='utf-8').splitlines()
        starts=[i for i,l in enumerate(lines) if re.fullmatch(r'第[一二三四五六七八九十]+章|上篇|下篇|一篇|校詁版',l)]
        assert len(starts)==len(notes),(title,len(starts))
        rel=r['path'].replace('\\','/'); hashes[rel]=hashlib.sha256(p.read_bytes()).hexdigest()
        md.append('## '+title)
        for j,(start,note) in enumerate(zip(starts,notes)):
            end=starts[j+1] if j+1<len(starts) else len(lines)
            quote=next(l for l in lines[start+1:end] if l.strip())[:32]
            item={'chapter_id':r['id'],'section':lines[start],'start_line':start+1,'end_line':end,'quote':quote,'assessment':note,'source_path':rel}
            rows.append(item)
            md.append(f'### {lines[start]}\n\n出处：`{rel}`，第 {start+1}—{end} 行。\n\n引文起句：『{quote}』\n\n{note}')
    md.append('## 结论\n\n36个篇内单元已对应出处并补写细读说明：系辞上12、系辞下9、说卦11、序卦2、杂卦2。原有篇级笔记未出现与这次全文复核冲突的解释；细读补充保存在本报告，不将内部单元另计入568篇覆盖。异文未擅改；未声称所有历史底本已校勘。')
    assert len(rows)==36
    out=ROOT/'验收/周易传文细读.md'; out.write_text('\n\n'.join(md)+'\n',encoding='utf-8')
    index=ROOT/'目录/周易传文章内索引.json'; index.write_text(json.dumps(rows,ensure_ascii=False,indent=2),encoding='utf-8')
    evidence=['验收/周易传文细读.md','目录/周易传文章内索引.json']
    for rel in evidence+['tools/review_zhouyi_sections.py']: hashes[rel]=hashlib.sha256((ROOT/rel).read_bytes()).hexdigest()
    path=ROOT/'验收/final-review-tasks.json'; tasks=json.loads(path.read_text(encoding='utf-8'))
    check=next(x for x in tasks['checks'] if x['id']=='zhouyi_internal_sections')
    check.update(status='passed',assessment='五篇全文再次逐段核对，36个篇内单元有本地行号与人工解释；保留所选章法及杂卦两版本差异，区分导航和正文，不扩大为全底本学术精校。',evidence_paths=evidence,source_sha256=hashes)
    path.write_text(json.dumps(tasks,ensure_ascii=False,indent=2),encoding='utf-8')
    print('周易传文章内复核完成：36个单元；其余四项状态不变。')

if __name__=='__main__': main()
