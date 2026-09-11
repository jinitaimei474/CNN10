from pathlib import Path
import re,json,datetime
root=Path(__file__).resolve().parent
src=Path(r'C:\Users\mike\Desktop\english.txt').read_text(encoding='utf-8-sig')
blocks=[p.strip() for p in re.split(r'\n\s*\n',src) if p.strip()]
episodes=[]
for b in blocks:
 m=re.search(r'(July|August|September)\s+\d{1,2},\s+2026\s*$',b)
 inferred=b=='How an insect-eating plant is proving Charles Darwin right 150 years later'
 if m or inferred:
  date=datetime.datetime.strptime(m.group(),'%B %d, %Y').strftime('%Y%m%d') if m else '20260807'
  title=b[:m.start()].rstrip(' -') if m else b
  episodes.append(dict(date=date,title=title,inferred=inferred,en=[],vocab=[]))
 else:
  episodes[-1]['vocab' if re.search(r'[\u4e00-\u9fff]',b) else 'en'].append(b)
assert len(episodes)==20
(root/'episodes.json').write_text(json.dumps(episodes,ensure_ascii=False,indent=2),encoding='utf-8')
for ep in episodes:
 (root/(ep['date']+'.en.txt')).write_text('\n'.join(f'{i:02} {s}' for i,s in enumerate(ep['en'],1)),encoding='utf-8')
 print(ep['date'],len(ep['en']),len(ep['vocab']),ep['title'])
