const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const {createEngine} = require('./timetable-engine.js');
function fixture(firstPeriod=1,secondPeriod=2){return {teachers:[
 {name:'A',lessons:[{day:1,period:firstPeriod,subject:'數學',classIds:['701']}]},
 {name:'B',lessons:[{day:2,period:secondPeriod,subject:'英語文',classIds:['701']}]}
],classes:[{id:'701',lessons:[
 {day:1,period:firstPeriod,subject:'數學',teachers:['A']},
 {day:2,period:secondPeriod,subject:'英語文',teachers:['B']}
]}]};}
let data=fixture();
assert.equal(createEngine(data).findCandidates('A',data.teachers[0].lessons[0]).candidates.length,1,'Regular lessons can exchange when both teachers are free');
data=fixture(1,8);
assert.equal(createEngine(data).findCandidates('A',data.teachers[0].lessons[0]).candidates.length,0,'Regular lessons cannot swap with period 8');
data=fixture(8,1);
assert.equal(createEngine(data).findCandidates('A',data.teachers[0].lessons[0]).candidates.length,0,'Period 8 cannot swap with regular lessons');
data=fixture(8,8);
assert.equal(createEngine(data).findCandidates('A',data.teachers[0].lessons[0]).candidates.length,1,'Period 8 can exchange with period 8 on another day');
data=fixture(1,7);
assert.equal(createEngine(data).findCandidates('A',data.teachers[0].lessons[0]).candidates.length,1,'The full regular period range remains eligible');
data=fixture();data.teachers[0].lessons.push({day:2,period:2,subject:'數學',classIds:['702']});
assert.equal(createEngine(data).findCandidates('A',data.teachers[0].lessons[0]).candidates.length,0,'Requesting teacher conflict excludes the candidate');
data=fixture();data.classes.push({id:'702',lessons:[{day:1,period:1,subject:'英語文',teachers:['B']}]});
assert.equal(createEngine(data).findCandidates('A',data.teachers[0].lessons[0]).candidates.length,0,'Reciprocal conflict from the class source also excludes the candidate');
data=fixture();data.classes[0].lessons[0].teachers.push('C');
assert.equal(createEngine(data).findCandidates('A',data.teachers[0].lessons[0]).status,'needs-review','Multi-teacher source is not treated as an ordinary swap');
data=fixture();data.teachers[1].lessons=[];
assert.equal(createEngine(data).findCandidates('A',data.teachers[0].lessons[0]).candidates.length,0,'Missing teacher corroboration is not mistaken for availability');
data=fixture();data.teachers[0].scheduleStatus='partial';
assert.deepEqual(createEngine(data).findCandidates('A',data.teachers[0].lessons[0]),{status:'incomplete-data',candidates:[]},'Incomplete requesting timetable is blocked even when its known lesson is corroborated');
data=fixture();data.teachers[1].scheduleStatus='partial';
assert.equal(createEngine(data).findCandidates('A',data.teachers[0].lessons[0]).candidates.length,0,'A teacher with an incomplete timetable is never offered as the other participant');
const actual=JSON.parse(vm.runInNewContext(fs.readFileSync(__dirname+'/timetable-data.js','utf8')+'\nJSON.stringify(timetableData)'));
const engine=createEngine(actual);let count=0,review=0;
for(const teacher of actual.teachers)for(const lesson of teacher.lessons){
 const result=engine.findCandidates(teacher.name,lesson);
 if(result.status!=='ok'){review++;continue;}
 for(const candidate of result.candidates){
  const incomingBusy=actual.teachers.find(t=>t.name===teacher.name).lessons.some(l=>l.day===candidate.day&&l.period===candidate.period);
  const outgoingBusy=actual.teachers.find(t=>t.name===candidate.teacher).lessons.some(l=>l.day===lesson.day&&l.period===lesson.period);
  assert.equal(incomingBusy,false);assert.equal(outgoingBusy,false);
  assert(lesson.classIds.includes(candidate.classId));assert.notEqual(candidate.teacher,teacher.name);
  assert.notEqual(teacher.scheduleStatus,'partial');
  assert.notEqual(actual.teachers.find(t=>t.name===candidate.teacher).scheduleStatus,'partial');
  assert.equal(candidate.period===8,lesson.period===8,'Actual-data candidates cannot cross the period-8 boundary');count++;
 }
}
const liao=actual.teachers.find(t=>t.name==='廖翎吾');
assert.deepEqual(liao.lessons.filter(l=>l.day===1).map(l=>[l.period,l.subject,l.classIds[0]]),[[3,'自然','205'],[7,'天文地質','301'],[8,'自然','302']],'Teacher PDF page 1 visual check');
for(const t of actual.teachers)for(const l of t.lessons){
 if(actual.classes.find(c=>c.id===l.classIds[0])?.swapPolicy==='review')assert.equal(engine.findCandidates(t.name,l).status,'needs-review');
}
assert.equal(actual.teachers.length,47);assert.equal(actual.classes.length,20);
assert.equal(actual.teachers.reduce((n,t)=>n+t.lessons.length,0),733);
const teacherAssignments=actual.teachers.flatMap(t=>t.lessons.flatMap(l=>l.classIds.map(c=>[t.name,c,l.day,l.period,l.subject].join('|')))).sort();
const classAssignments=actual.classes.flatMap(c=>c.lessons.flatMap(l=>l.teachers.map(t=>[t,c.id,l.day,l.period,l.subject].join('|')))).sort();
assert.deepEqual(teacherAssignments,classAssignments,'Co-teaching merge retains every source teaching assignment');
let joint=0;
for(const c of actual.classes)for(const l of c.lessons)if(l.teachers.length>1){
 joint++;
 for(const name of l.teachers){
  const t=engine.teachers.get(name), lesson=t.lessons.find(x=>x.day===l.day&&x.period===l.period&&x.classIds.includes(c.id));
  assert.equal(engine.findCandidates(name,lesson).status,'needs-review','Co-teaching source cannot be swapped independently');
 }
}
assert.equal(joint,15);
console.log(JSON.stringify({fixtureChecks:11,actualCandidatesChecked:count,excludedSourceLessons:review,sourcePageSpotCheck:'passed'}));
