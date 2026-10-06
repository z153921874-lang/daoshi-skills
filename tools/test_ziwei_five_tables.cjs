const assert=require('node:assert/strict');
const {Lunar}=require('lunar-typescript');
const {getStartIndex}=require('iztro/lib/star/location');
const {getFiveElementsClass}=require('iztro/lib/astro/palace');
const branches=[...'寅卯辰巳午未申酉戌亥子丑'];
const cases=[[2,'丙','子','水二局'],[3,'壬','子','木三局'],[4,'甲','子','金四局'],[5,'庚','子','土五局'],[6,'戊','子','火六局']];
let checked=0;
for(const [n,stem,branch,name] of cases){
 assert.equal(getFiveElementsClass(stem,branch),name);
 for(let day=1;day<=30;day++){
  const lunar=Lunar.fromYmd(2023,8,day);assert.equal(lunar.getDay(),day);
  const q=Math.ceil(day/n),pad=q*n-day;
  const expected=((q-1+(pad%2===0?pad:-pad))%12+12)%12;
  const actual=getStartIndex({solarDate:lunar.getSolar().toYmd(),timeIndex:0,fixLeap:true,from:{heavenlyStem:stem,earthlyBranch:branch}});
  assert.equal(actual.ziweiIndex,expected,`${name} ${day}`);
  assert.equal(actual.tianfuIndex,(12-expected)%12);checked++;
 }
}
console.log(JSON.stringify({passed:true,checked,method:'固定局干支与农历日期，补数奇退偶进逐日核对；天府寅申轴反射',scope:'与程序规则独立表达一致；原图三处疑点另记，非预测有效性'}));
