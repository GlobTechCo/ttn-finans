#!/usr/bin/env python3
import datetime as dt, json, re, sys, urllib.request
from pathlib import Path
from zoneinfo import ZoneInfo

SOURCES = {
 'BLS': ('https://www.bls.gov/schedule/news_release/bls.ics', 'https://www.bls.gov/schedule/news_release/'),
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

def main():
    try: old=json.loads(DEST.read_text())
    except (OSError,ValueError): old={'sources':{}}
    sources=old.get('sources',{})
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
    if not success: raise SystemExit('All calendar sources failed; previous snapshot retained')
    DEST.parent.mkdir(parents=True,exist_ok=True)
    DEST.write_text(json.dumps({'sources':sources},indent=2)+'\n')
if __name__=='__main__': main()
