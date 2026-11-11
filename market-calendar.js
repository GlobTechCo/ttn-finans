(() => {
  const target=document.getElementById('market-calendar-list');
  if(!target) return;
  const note=document.getElementById('market-calendar-status');
  const formatter=new Intl.DateTimeFormat('en-US',{timeZone:'America/New_York',month:'short',day:'numeric',hour:'numeric',minute:'2-digit',timeZoneName:'short'});
  fetch('https://raw.githubusercontent.com/GlobTechCo/ttn-finans/main/data/market-calendar.json',{cache:'no-store'})
    .then(r=>{if(!r.ok)throw Error('unavailable');return r.json()})
    .then(data=>{
      const now=Date.now(); const age=48*60*60*1000;
      const entries=Object.entries(data.sources||{}).filter(([name,s])=>['BEA','Federal Reserve'].includes(name)&&Number.isFinite(Date.parse(s.checkedAt))&&now-Date.parse(s.checkedAt)<age&&now>=Date.parse(s.checkedAt)-300000);
      const events=entries.flatMap(([name,s])=>(s.events||[]).filter(e=>e.source===name&&typeof e.title==='string'&&e.title.length<250&&Date.parse(e.time)>now).map(e=>({...e,checkedAt:s.checkedAt}))).sort((a,b)=>Date.parse(a.time)-Date.parse(b.time)).slice(0,3);
      if(!events.length)throw Error('no current events');
      target.textContent='';
      for(const event of events){const li=document.createElement('li'),a=document.createElement('a'),time=document.createElement('time');a.href=event.source==='Federal Reserve'?'https://www.federalreserve.gov/monetarypolicy/fomccalendars.htm':'https://www.bea.gov/news/schedule';a.target='_blank';a.rel='noopener noreferrer';a.textContent=event.title;time.dateTime=event.time;time.textContent=event.source==='Federal Reserve' && /^\d{4}-\d{2}-\d{2}$/.test(event.startDate||'') && /^\d{4}-\d{2}-\d{2}$/.test(event.endDate||'') ? new Intl.DateTimeFormat('en-US',{timeZone:'UTC',month:'short',day:'numeric',year:'numeric'}).formatRange(new Date(event.startDate+'T12:00:00Z'),new Date(event.endDate+'T12:00:00Z'))+' · Federal Reserve · Tentative' : formatter.format(new Date(event.time))+' · '+event.source;li.append(a,document.createElement('br'),time);target.append(li)}
      const oldest=Math.min(...events.map(e=>Date.parse(e.checkedAt)));
      note.textContent='Sources checked: '+formatter.format(new Date(oldest))+(entries.length<2?' · Partial coverage':'');
    }).catch(()=>{target.textContent='Calendar data is temporarily unavailable.';note.textContent='Check official schedules: ';for(const [label,url] of [['BEA','https://www.bea.gov/news/schedule'],['Federal Reserve','https://www.federalreserve.gov/monetarypolicy/fomccalendars.htm']]){const a=document.createElement('a');a.href=url;a.textContent=label;a.target='_blank';a.rel='noopener noreferrer';note.append(a,document.createTextNode('  '))}});
})();
