'use strict';
// Local-only deterministic calculation. No network calls or personal data writes.
const {Solar,Lunar}=require('lunar-typescript');
const iztro=require('iztro');
const fixedConfig={yearDivide:'normal',horoscopeDivide:'normal',ageDivide:'normal',dayDivide:'forward',algorithm:'default'};
const baseConfig=JSON.parse(JSON.stringify(iztro.astro.getConfig()));
const {getMutagensByHeavenlyStem}=require('iztro/lib/utils');
const NAMES=['','乾','兑','离','震','巽','坎','艮','坤'];
const LINES=[null,[1,1,1],[1,1,0],[1,0,1],[1,0,0],[0,1,1],[0,1,0],[0,0,1],[0,0,0]];
const ELEMENTS=['','金','金','火','木','木','水','土','土'];
// Row upper, column lower, both in 先天 order.
const HEX=[['乾','履','同人','无妄','姤','讼','遁','否'],['夬','兑','革','随','大过','困','咸','萃'],['大有','睽','离','噬嗑','鼎','未济','旅','晋'],['大壮','归妹','丰','震','恒','解','小过','豫'],['小畜','中孚','家人','益','巽','涣','渐','观'],['需','节','既济','屯','井','坎','蹇','比'],['大畜','损','贲','颐','蛊','蒙','艮','剥'],['泰','临','明夷','复','升','师','谦','坤']];
const mod=(n,d)=>((n-1)%d+d)%d+1;
function integer(n,name,min,max){if(!Number.isSafeInteger(n)||n<min||n>max)throw Error(`${name}须为${min}至${max}的整数`);return n;}
function dateParts(s){if(typeof s!=='string'||!/^\d{4}-\d{1,2}-\d{1,2}$/.test(s))throw Error('日期须为 YYYY-MM-DD');let a=s.split('-').map(Number);integer(a[0],'年份',1900,2100);integer(a[1],'月份',1,12);integer(a[2],'日期',1,31);return a;}
function dates(input){
 const a=dateParts(input.date); let solar,lunar;
 if(input.calendar==='solar'){
   const check=new Date(Date.UTC(a[0],a[1]-1,a[2]));if(check.getUTCMonth()!==a[1]-1||check.getUTCDate()!==a[2])throw Error('不存在的公历日期');
   if(input.isLeapMonth===true)throw Error('公历输入不能设置农历闰月');
   solar=Solar.fromYmd(...a);lunar=solar.getLunar();
 }else if(input.calendar==='lunar'){
   if(typeof input.isLeapMonth!=='boolean')throw Error('农历输入须明确 isLeapMonth');
   lunar=Lunar.fromYmd(a[0],input.isLeapMonth?-a[1]:a[1],a[2]);solar=lunar.getSolar();
 }else throw Error('calendar 须为 solar 或 lunar');
 return {solar,lunar};
}
function timeIndex(s){if(typeof s!=='string'||!/^([01]\d|2[0-3]):[0-5]\d$/.test(s))throw Error('须提供明确的标准时间 HH:mm；未知时辰不能排唯一命盘');const hour=Number(s.slice(0,2));return hour===23?12:Math.floor((hour+1)/2);}
function standardInput(i){
 if(i.timeBasis!=='local-standard')throw Error('请先确认并换算为出生地/起卦地当地标准时间（去除夏令时），设置 timeBasis=local-standard');
 if(typeof i.place!=='string'||!i.place.trim())throw Error('请提供地点 place');
 if(typeof i.standardUtcOffset!=='string'||!/^[-+](0\d|1[0-4]):[0-5]\d$/.test(i.standardUtcOffset))throw Error('请提供当地标准 UTC 偏移，如 +08:00');
 if(i.standardUtcOffset.slice(1,3)==='14'&&!i.standardUtcOffset.endsWith(':00'))throw Error('UTC 偏移超出范围');
 return timeIndex(i.time);
}
function trigram(lines){return LINES.findIndex(x=>x&&x.join('')===lines.join(''));}
function hex(lines){const lower=trigram(lines.slice(0,3)),upper=trigram(lines.slice(3));return {name:HEX[upper-1][lower-1],upper:NAMES[upper],lower:NAMES[lower],linesBottomUp:lines};}
function buildMeihua(upper,lower,moving,trace){
 const original=[...LINES[lower],...LINES[upper]],changed=[...original];changed[moving-1]^=1;
 const mutual=[...original.slice(1,4),...original.slice(2,5)];const ti=moving<=3?upper:lower, yong=moving<=3?lower:upper;
 return {method:'meihua',trace,upper:{number:upper,name:NAMES[upper]},lower:{number:lower,name:NAMES[lower]},movingLine:moving,
  original:hex(original),mutual:hex(mutual),changed:hex(changed),body:{name:NAMES[ti],element:ELEMENTS[ti],position:moving<=3?'upper':'lower'},use:{name:NAMES[yong],element:ELEMENTS[yong],position:moving<=3?'lower':'upper'},
  notice:'传统起卦计算；计算正确不代表具备预测效力。体为不动经卦，用为动爻所在经卦。互卦统一取二三四爻为下、三四五爻为上；乾坤亦按此式，原典的变卦取互另作异说记录。'};
}
function meihua(i){
 if(i.mode==='numbers'){
  const a=integer(i.upperNumber,'上卦数',1,1000000000),b=integer(i.lowerNumber,'下卦数',1,1000000000);
  return buildMeihua(mod(a,8),mod(b,8),mod(a+b,6),{mode:'双数起卦约定',upperNumber:a,lowerNumber:b,movingSum:a+b,rule:'第一数取上卦，第二数取下卦，两数相加取动爻，不额外加时；这是本技能明确约定，非原典唯一方法'});
 }
 if(i.mode!=='datetime')throw Error('mode 须为 numbers 或 datetime');
 const ti=standardInput(i);let {solar}=dates(i);
 // Explicit convention: late 子 hour belongs to following civil/lunar day.
 if(ti===12)solar=solar.next(1);
 const lunar=solar.getLunar(), yearBranch=lunar.getYearZhi(),yn='子丑寅卯辰巳午未申酉戌亥'.indexOf(yearBranch)+1;
 const mn=Math.abs(lunar.getMonth()),dn=lunar.getDay(),hn=(ti%12)+1,sum=yn+mn+dn;
 return buildMeihua(mod(sum,8),mod(sum+hn,8),mod(sum+hn,6),{mode:'年月日時',input:i,effectiveSolarDate:solar.toYmd(),lunarDate:lunar.toString(),yearBranch,yearNumber:yn,monthNumber:mn,dayNumber:dn,hourNumber:hn,upperSum:sum,lowerAndMovingSum:sum+hn,
  rule:'农历年支子1至亥12，月日用农历数；闰月沿用该月数；23时归次日，作为本工具明确约定。依据《梅花易数》卷一年月日時起卦。'});
}
function ziwei(i){
 const ti=standardInput(i);if(!['男','女'].includes(i.sex))throw Error('须明确传统排盘参数 sex=男 或 女，不据姓名推断');
 const {solar,lunar}=dates(i);
 const effectiveSolar=ti===12?solar.next(1):solar;
 const effectiveTimeIndex=ti===12?0:ti;
 // In pinned iztro 2.6.1 config() merges maps; getConfig() exposes those maps.
 // Clear them before restoring defaults, otherwise a previous school leaks in.
 const prior=iztro.astro.getConfig();for(const k of Object.keys(prior.mutagens))delete prior.mutagens[k];for(const k of Object.keys(prior.brightness))delete prior.brightness[k];
 iztro.astro.config({...baseConfig,...fixedConfig});
 const chart=iztro.astro.bySolar(effectiveSolar.toYmd(),effectiveTimeIndex,i.sex,true,'zh-CN');
 const output={method:'ziwei',engineVersion:require('iztro/package.json').version,input:i,calendarConversion:{solar:solar.toYmd(),lunar:lunar.toString(),effectiveSolar:effectiveSolar.toYmd(),effectiveLunar:effectiveSolar.getLunar().toString(),effectiveTimeIndex},rules:{...iztro.astro.getConfig(),fourTransformations:Object.fromEntries([...'甲乙丙丁戊己庚辛壬癸'].map(x=>[x,getMutagensByHeavenlyStem(x)])),fourTransformationOrder:['禄','权','科','忌'],fixLeap:true,leapRule:'闰月初一至十五按本月，十六起按下月；先作晚子时整日换日，再调用库',clock:'当地标准时间，无真太阳时校正；夏令时须事先扣除',lateZi:'23:00–23:59 显式换为次日早子时，年/月/日/安星一并换日；此为本技能约定，比库原生 dayDivide 更严格'},chart:chart.toJSON(),notice:'传统排盘资料，用于文化研究与反思，不作诊断或确定预测。'};
 if(i.targetYear!==undefined){integer(i.targetYear,'目标农历年份',1900,2100);const target=Lunar.fromYmd(i.targetYear,1,1).getSolar();if(target.toYmd()<solar.toYmd())throw Error('目标流年开始早于出生日期，请指定出生之后的农历年');let h=chart.horoscope(target.toYmd(),0).toJSON();output.horoscope={targetLunarYear:i.targetYear,representativeDate:target.toYmd(),yearly:h.yearly,decadal:h.decadal,age:h.age};}
 return output;
}
function run(i){if(!i||typeof i!=='object'||Array.isArray(i))throw Error('输入须为 JSON 对象');if(i.method==='meihua')return meihua(i);if(i.method==='ziwei')return ziwei(i);throw Error('method 须为 meihua 或 ziwei');}
module.exports={run,meihua,ziwei,buildMeihua,dates,timeIndex};
if(require.main===module){let input='';process.stdin.setEncoding('utf8');process.stdin.on('data',c=>input+=c);process.stdin.on('end',()=>{try{console.log(JSON.stringify(run(JSON.parse(input)),null,2));}catch(e){console.error(JSON.stringify({error:e.message}));process.exitCode=1;}});}
