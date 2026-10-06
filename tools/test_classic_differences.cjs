'use strict';
const assert=require('node:assert/strict');
const {run}=require('./divination.cjs');
const {getLuYangTuoMaIndex}=require('iztro/lib/star/location');
const branches=[...'寅卯辰巳午未申酉戌亥子丑'];
const expected={寅:'申',午:'申',戌:'申',申:'寅',子:'寅',辰:'寅',巳:'亥',酉:'亥',丑:'亥',亥:'巳',卯:'巳',未:'巳'};
for(const [year,horse] of Object.entries(expected))assert.equal(branches[getLuYangTuoMaIndex('甲',year).maIndex],horse);
const base={method:'ziwei',date:'1985-01-01',calendar:'lunar',isLeapMonth:false,time:'00:00',timeBasis:'local-standard',place:'虚构测试地点',standardUtcOffset:'+08:00',sex:'男'};
const male=run(base),female=run({...base,sex:'女'});
const at=(z,b)=>z.chart.palaces.find(p=>p.earthlyBranch===b);
assert.equal(male.chart.fiveElementsClass,'土五局');
assert.equal(at(male,'申').changsheng12,'长生');
assert.equal(at(male,'未').changsheng12,'沐浴'); // 阴男逆，与古籍仅男顺不同
assert.equal(at(female,'酉').changsheng12,'沐浴'); // 阴女顺，与古籍仅女逆不同
assert.deepEqual(at(male,'寅').decadal.range,[5,14]);
assert.deepEqual(at(male,'丑').decadal.range,[15,24]);
assert.deepEqual(at(female,'卯').decadal.range,[15,24]);
assert.deepEqual(male.rules.fourTransformations['壬'],['天梁','紫微','左辅','武曲']);
const leap15=run({...base,date:'2023-02-15',isLeapMonth:true});
const leap16=run({...base,date:'2023-02-16',isLeapMonth:true});
assert.equal(leap15.chart.earthlyBranchOfSoulPalace,'卯');
assert.equal(leap16.chart.earthlyBranchOfSoulPalace,'辰');
console.log(JSON.stringify({passed:true,checks:['天马十二年支逐项对应古籍','1985乙丑土五局长生男女顺逆对照','大限命宫首段及男女下一段','壬干四化表','闰二月十五十六分界'],limits:'仅验证列明规则；不验证预测效力，不穷尽全部杂曜。'}));
