#!/usr/bin/env python3
import datetime as dt, json, re, sys, urllib.request
from pathlib import Path
from zoneinfo import ZoneInfo

SOURCES = {
 'BEA': ('https://www.bea.gov/news/schedule/ics/online-calendar-subscription.ics', 'https://www.bea.gov/news/schedule'),
}
DEST=Path('data/market-calendar.json')
NOW=dt.datetime.now(dt.timezone.utc)

def parse(text, source, link):
    text=re.sub(r'\r?\n[ \t]', '', text)
    if 'BEGIN:VCALENDAR' not in text or 'END:VCALENDAR' not in text: raise ValueError('not an iCalendar')
    out=[]
    for chunk in text.split('BEGIN:VEVENT')[1:]:
        if 'END:VEVENT' not in chunk: raise ValueError('incomplete event')
        item={}
        for line in chunk.split('END:VEVENT')[0].splitlines():
            if ':' in line:
                key, value=line.split(':',1); item[key]=value
        title=item.get('SUMMARY','').replace('\\,',',').replace('\\;',';').replace('\\n',' ')
        if not re.search(r'consumer price index|employment situation|producer price index|gross domestic product|personal income and outlays',title,re.I): continue
        if re.search(r'by state|by industry|county|regional',title,re.I): continue
        start=next(((k,v) for k,v in item.items() if k.split(';')[0]=='DTSTART'),None)
        if not start: continue
        key,value=start
        try:
            if value.endswith('Z'): date=dt.datetime.strptime(value,'%Y%m%dT%H%M%SZ').replace(tzinfo=dt.timezone.utc)
            elif 'TZID=America/New_York' in key: date=dt.datetime.strptime(value,'%Y%m%dT%H%M%S').replace(tzinfo=ZoneInfo('America/New_York')).astimezone(dt.timezone.utc)
            else: continue
        except ValueError: continue
        if date > NOW and date < NOW+dt.timedelta(days=180):
            out.append({'title':title,'time':date.isoformat().replace('+00:00','Z'),'source':source,'url':link})
    return out

FED_URL='https://www.federalreserve.gov/monetarypolicy/fomccalendars.htm'

def parse_fed(text):
    # Each year has a labeled panel; accept only explicit two-day scheduled meetings.
    headings=list(re.finditer(r'(20\d{2})\s+FOMC\s+Meetings', text, re.I))
    out=[]
    for i, heading in enumerate(headings):
        year=int(heading.group(1))
        if year not in (NOW.year, NOW.year+1): continue
        body=text[heading.end():headings[i+1].start() if i+1<len(headings) else len(text)]
        months=list(re.finditer(r'<div\b[^>]*class=["\'][^"\']*fomc-meeting__month[^"\']*["\'][^>]*>(.*?)</div>',body,re.I|re.S))
        for j,month in enumerate(months):
            block=body[month.end():months[j+1].start() if j+1<len(months) else len(body)]
            date_match=re.search(r'<div\b[^>]*class=["\'][^"\']*fomc-meeting__date[^"\']*["\'][^>]*>(.*?)</div>',block,re.I|re.S)
            if not date_match: continue
            label=re.sub(r'<[^>]+>','',month.group(1)).strip()
            days=re.sub(r'<[^>]+>','',date_match.group(1)).strip()
            m=re.fullmatch(r'(\d{1,2})\s*[-–]\s*(\d{1,2})\s*\*?',days)
            parts=[v.strip() for v in label.split('/')]
            if not m or len(parts)>2: continue
            def month_number(name):
                for fmt in ('%B','%b'):
                    try: return dt.datetime.strptime(name,fmt).month
                    except ValueError: pass
                raise ValueError('invalid month')
            try:
                first=month_number(parts[0]); last=month_number(parts[-1]); d1=int(m.group(1));d2=int(m.group(2))
                endyear=year+(1 if last<first else 0)
                start=dt.date(year,first,d1); end=dt.date(endyear,last,d2)
                if not 0 <= (end-start).days <= 2: continue
                cutoff=dt.datetime.combine(end,dt.time(23,59,59),ZoneInfo('America/New_York')).astimezone(dt.timezone.utc)
                if NOW < cutoff < NOW+dt.timedelta(days=370):
                    out.append({'title':'FOMC meeting','startDate':start.isoformat(),'endDate':end.isoformat(),'time':cutoff.isoformat().replace('+00:00','Z'),'source':'Federal Reserve','url':FED_URL})
            except ValueError: continue
    if not out: raise ValueError('No upcoming FOMC meetings could be validated')
    return out

def main():
    try: old=json.loads(DEST.read_text())
    except (OSError,ValueError): old={'sources':{}}
    sources=old.get('sources',{})
    sources.pop('BLS',None)
    success=0
    for name,(url,link) in SOURCES.items():
        try:
            req=urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0 (compatible; TTNFinanceCalendar/1.0)'})
            with urllib.request.urlopen(req,timeout=25) as res: text=res.read(3000000).decode('utf-8-sig')
            events=parse(text,name,link)
            if not events: raise ValueError('no matching upcoming events')
            sources[name]={'checkedAt':NOW.isoformat().replace('+00:00','Z'),'events':events}
            success+=1
            print(name, len(events), 'events')
        except Exception as exc: print(name,'unavailable:',str(exc),file=sys.stderr)
    try:
        req=urllib.request.Request(FED_URL,headers={'User-Agent':'TTNFinanceCalendar/1.0'})
        with urllib.request.urlopen(req,timeout=25) as res: text=res.read(3000000).decode('utf-8-sig')
        events=parse_fed(text)
        sources['Federal Reserve']={'checkedAt':NOW.isoformat().replace('+00:00','Z'),'events':events}
        success+=1
        print('Federal Reserve',len(events),'meetings')
    except Exception as exc: print('Federal Reserve unavailable:',str(exc),file=sys.stderr)
    if not success: raise SystemExit('All calendar sources failed; previous snapshot retained')
    DEST.parent.mkdir(parents=True,exist_ok=True)
    DEST.write_text(json.dumps({'sources':sources},indent=2)+'\n')
if __name__=='__main__': main()
