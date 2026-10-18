#!/usr/bin/env python3
"""Read-only date provenance check against Git's first HTML version.

Git addition dates establish repository history, not necessarily first publication.
Differences are review flags, never instructions to rewrite published timestamps.
Use --details to print the affected article IDs and the dates being compared.
"""
from pathlib import Path
from collections import Counter
import argparse,datetime,json,re,subprocess
ROOT=Path(__file__).resolve().parents[1]

def audit(details=False):
    if subprocess.check_output(['git','rev-parse','--is-shallow-repository'],cwd=ROOT,text=True).strip()=='true':
        raise SystemExit('A full Git history is required for this provenance check.')
    catalog=json.loads((ROOT/'articles.js').read_text().split('=',1)[1].strip().removesuffix(';'))
    counts=Counter();flags=[]
    for article in catalog:
        name=article['id']+'.html'
        records=subprocess.check_output(['git','log','--diff-filter=A','--reverse','--format=%H %cI','--',name],cwd=ROOT,text=True).splitlines()
        if not records:counts['missing_addition_record']+=1;continue
        commit,added=records[0].split(' ',1)
        original=subprocess.check_output(['git','show',commit+':'+name],cwd=ROOT,text=True)
        first=re.search(r'"datePublished"\s*:\s*"([^\"]+)"',original)
        published=datetime.datetime.fromisoformat(article['date']);introduced=datetime.datetime.fromisoformat(added)
        counts['articles_checked']+=1
        if published.tzinfo is None:counts['legacy_timestamp_without_timezone']+=1
        if published.date()<introduced.date():
            counts['publication_day_precedes_git_addition']+=1
            flags.append({'article':article['id'],'flag':'publication_day_precedes_git_addition','published':article['date'],'gitAdded':added})
        if not first:counts['first_html_has_no_structured_date']+=1;continue
        if first[1]==article['date']:counts['first_html_date_unchanged']+=1
        elif first[1][:10]==article['date'][:10]:counts['same_day_different_timestamp_representation']+=1
        else:
            counts['first_html_calendar_day_differs']+=1
            flags.append({'article':article['id'],'flag':'first_html_calendar_day_differs','firstHtmlDate':first[1],'currentCatalogDate':article['date']})
    result={'counts':dict(counts),'interpretation':'Review flags do not prove backdating. Initial catalog labels, HTML metadata, imports and real publication history may differ. No dates were changed.'}
    if details:result['flags']=flags
    print(json.dumps(result,indent=2))
if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--details',action='store_true');audit(parser.parse_args().details)
