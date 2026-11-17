"""Import the supplied Dongren PDFs by text-run positions, without OCR guesses.

Usage: python import-pdfs.py teacher.pdf class.pdf
Raw extraction and reconciliation reports are retained under audit/.
"""
from pathlib import Path
import collections
import hashlib
import json
import re
import sys
import unicodedata
from pypdf import PdfReader

ROOT = Path(__file__).resolve().parent
TIMES = [('08:30','09:15'),('09:25','10:10'),('10:20','11:05'),('11:15','12:00'),('13:20','14:05'),('14:15','15:00'),('15:10','15:55'),('16:05','16:50')]
CENTERS = [200, 266, 334, 403, 477]

def dump(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')

def runs_for(page):
    result=[]
    def visit(text, cm, tm, font, size):
        text=text.strip()
        if not text or cm[0] < 0.1: return
        x=tm[4]*cm[0]+tm[5]*cm[2]+cm[4]
        y=float(page.mediabox.height)-(tm[4]*cm[1]+tm[5]*cm[3]+cm[5])
        size=abs(size*cm[0])
        result.append(dict(text=text, x=round(x,3), y=round(y,3), size=round(size,3)))
    page.extract_text(visitor_text=visit)
    return result

def center(run):
    width=sum(1 if unicodedata.east_asian_width(ch) in 'WF' else .5 for ch in run['text'])*run['size']
    return run['x']+width/2

def extract(path, kind):
    records=[]
    raw=[]
    for page_index,page in enumerate(PdfReader(path).pages):
        runs=runs_for(page)
        raw.append(runs)
        if kind=='teacher':
            heads=[r for r in runs if 110<r['y']<130 and r['size']>19]
            assert len(heads)==2, (page_index, heads)
            record=dict(name=heads[0]['text'], role=heads[1]['text'], sourcePage=page_index+1, lessons=[])
        else:
            name=next(r['text'].split(':',1)[1] for r in runs if r['text'].startswith('班級名稱:'))
            record=dict(id=name,label=name+' 班',sourcePage=page_index+1,lessons=[])
        for number,(start,end) in enumerate(TIMES,1):
            sy=next(r['y'] for r in runs if r['text']==start and r['x']<150)
            ey=next(r['y'] for r in runs if r['text']==end and r['x']<150)
            slots=collections.defaultdict(dict)
            for r in runs:
                if r['x']<150 or not sy-2<r['y']<ey+5: continue
                if abs(r['y']-sy)<2: field='subject'
                elif abs(r['y']-ey)<5: field='classIds' if kind=='teacher' else 'teachers'
                else: continue
                day=min(range(5),key=lambda d:abs(center(r)-CENTERS[d]))+1
                slots[day][field]=slots[day].get(field,'')+r['text']
            for day,slot in slots.items():
                slot.setdefault('subject','科目未載')
                field='classIds' if kind=='teacher' else 'teachers'
                assert field in slot, (kind,page_index,number,day,slot)
                value=slot[field]
                slot[field]=[value]
                lesson=dict(day=day,period=number,**slot)
                if kind=='teacher':
                    lesson['annotations']=[r['text'].strip('()') for r in runs if sy+2<r['y']<ey-4 and r['text'].startswith('(') and min(range(5),key=lambda d:abs(center(r)-CENTERS[d]))+1==day]
                record['lessons'].append(lesson)
        record['lessons'].sort(key=lambda l:(l['day'],l['period']))
        if kind=='teacher':
            totals=[r['text'] for r in runs if r['y']>550 and re.fullmatch(r'\d+ \d+ \d+ \d+',r['text'])]
            assert len(totals)==1 and int(totals[0].split()[-1])==len(record['lessons']), ('PDF total differs',record['name'],totals,len(record['lessons']))
        records.append(record)
    return records,raw

if __name__=='__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    teacher_path,class_path=map(Path,sys.argv[1:3])
    (ROOT/'audit').mkdir(exist_ok=True)
    teachers,traw=extract(teacher_path,'teacher')
    classes,craw=extract(class_path,'class')
    dump(ROOT/'audit/raw-runs.json',dict(teachers=traw,classes=craw))
    dump(ROOT/'audit/extracted.json',dict(teachers=teachers,classes=classes))
    print('Extracted',len(teachers),'teachers,',len(classes),'class sheets;',sum(len(t['lessons']) for t in teachers),'teacher lessons,',sum(len(c['lessons']) for c in classes),'class lessons')
    print('Teacher class IDs:',sorted(set(i for t in teachers for l in t['lessons'] for i in l['classIds'])))
    print('Unknown teachers:', sorted(set(n for c in classes for l in c['lessons'] for n in l['teachers'])-set(t['name'] for t in teachers)))
    teacher_keys={(t['name'],l['day'],l['period'],c,l['subject']) for t in teachers for l in t['lessons'] for c in l['classIds']}
    class_keys={(n,l['day'],l['period'],c['id'],l['subject']) for c in classes for l in c['lessons'] for n in l['teachers']}
    assert teacher_keys==class_keys, ('Sources disagree',teacher_keys-class_keys,class_keys-teacher_keys)
    assert len(teacher_keys)==733 and len(teachers)==47 and len(classes)==23
    review_ids={'707','807','906'}
    # User confirmed dotted sheets are co-teaching supplements on 2026-11-17.
    by_class={c['id']:c for c in classes}
    for c in classes: c['sourcePages']=[c['sourcePage']]
    for dotted in ['106.','206.','305.']:
        supplement=by_class[dotted]
        main=by_class[dotted[:-1]]
        main['sourcePages'].append(supplement['sourcePage'])
        for extra in supplement['lessons']:
            matches=[l for l in main['lessons'] if (l['day'],l['period'],l['subject'])==(extra['day'],extra['period'],extra['subject'])]
            assert len(matches)==1, ('Co-teaching subject mismatch',dotted,extra)
            matches[0]['teachers']=list(dict.fromkeys(matches[0]['teachers']+extra['teachers']))
    classes=[c for c in classes if not c['id'].endswith('.')]
    for index,t in enumerate(teachers,1):
        t.update(id=f't{index:03}',page=t.pop('sourcePage'),scheduleStatus='complete')
        for l in t['lessons']:
            l['sourceClassIds']=l['classIds'][:]
            l['classIds']=[code.rstrip('.') for code in l['classIds']]
    for c in classes:
        c.update(page=c.pop('sourcePage'),mentor=None)
        if c['id'] in review_ids: c['swapPolicy']='review'
        if c['id'] in review_ids: c['label']=c['id']+' 資源班'
    data=dict(semester='115 學年度第一學期',validFrom='2026-08-31',validThrough='2027-01-20',version='教師 ver9.1／班級 ver8.27',periods=[dict(number=i,start=s,end=e) for i,(s,e) in enumerate(TIMES,1)],teachers=teachers,classes=classes,sources=[dict(filename=p.name,sha256=hashlib.sha256(p.read_bytes()).hexdigest()) for p in [teacher_path,class_path]])
    dump(ROOT/'timetable.json',data)
    groups=collections.defaultdict(list)
    for t in teachers:
        group='homerooms' if t['role']=='導師' else 'subject' if t['role'] in ['專任教師','兼任教師'] else 'admin'
        groups[group].append(dict(name=t['name'],tag=t['role'],hasSchedule=True))
    menu=dict(admin=[dict(label='行政',items=groups['admin'])],homerooms=[dict(label='導師',items=groups['homerooms'])],subject=[dict(label=role,items=[p for p in groups['subject'] if p['tag']==role]) for role in ['專任教師','兼任教師']],special=[],native=[],classes=[dict(classId=c['id'],**{'class':c['id']},label=c['id'],grade=int(c['id'][0])+6 if re.fullmatch('[123][0-9]{2}',c['id']) else 0) for c in classes])
    dump(ROOT/'menu.json',menu)
    dump(ROOT/'data-validation.json',dict(teacherPages=len(teachers),classPages=23,displayedClasses=len(classes),coTeachingLessons=15,teacherLessons=len(teacher_keys),classTeachingAssignments=len(class_keys),matchedLessons=len(teacher_keys&class_keys),mismatches=0,teacherTotalsVerified=47,swapReviewClasses=sorted(review_ids),coTeachingConfirmedByUser='2026-11-17',sources=data['sources']))
