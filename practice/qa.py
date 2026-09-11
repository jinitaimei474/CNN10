from pathlib import Path
import json, subprocess, concurrent.futures, math, re
from PIL import Image, ImageOps, ImageDraw
import pdfplumber
from source import ROOT

reports=json.loads((ROOT/'practice/manifest.json').read_text(encoding='utf-8'))
qa=ROOT/'tmp/pdfs/listening_qa'
qa.mkdir(parents=True,exist_ok=True)
poppler=r'C:\Users\mike\.cache\codex-runtimes\codex-primary-runtime\dependencies\native\poppler\Library\bin\pdftoppm.exe'

def run(r):
    path=ROOT/'output/pdf/listening'/r['file']
    dest=qa/r['date'];dest.mkdir(exist_ok=True)
    subprocess.run([poppler,'-r','90','-png',str(path),str(dest/'page')],check=True,stdout=subprocess.DEVNULL,stderr=subprocess.PIPE)
    imgs=[f for f in sorted(dest.glob('page-*.png')) if int(f.stem.split('-')[-1])<=r['pages']]
    assert len(imgs)==r['pages']
    sheet=Image.new('RGB',(1440,math.ceil(len(imgs)/3)*720),'#D6DEE4')
    draw=ImageDraw.Draw(sheet)
    for i,file in enumerate(imgs):
        x=i%3*480;y=i//3*720
        sheet.paste(ImageOps.contain(Image.open(file),(470,680)),(x+5,y+25))
        draw.text((x+8,y+7),r['date']+' / '+str(i+1),fill='black')
    sheet.save(qa/(r['date']+'.png'))
    with pdfplumber.open(path) as doc:
        markers=[]
        for i,page in enumerate(doc.pages):
            for c in page.chars:
                assert 40<=c['x0'] and c['x1']<=page.width-38 and c['top']>=15 and c['bottom']<=page.height-15,(r['date'],i,'outside margins',c)
            text=page.crop((48,49,page.width-48,page.height-56)).extract_text()
            # Every numbered blank is on one physical line with its full writing space.
            for line in text.splitlines():
                if '_'*10 not in line:continue
                nums=re.findall(r'\[(\d{2})\]\s*_{29}',line)
                if re.search(r'\[\d{2}\]',line):
                    assert nums,(r['date'],i,'split blank',line)
                markers.extend(nums)
        assert markers==[f'{i:02d}' for i in range(1,31)],(r['date'],markers)
    return dict(date=r['date'],pages=r['pages'],questions=30,bounds='PASS',inline_blanks='PASS',render='PASS')

with concurrent.futures.ThreadPoolExecutor(max_workers=4) as ex:
    results=[]
    for row in ex.map(run,reports):
        results.append(row)
        print(row['date'],row['pages'],'pages rendered; bounds and blanks PASS',flush=True)
(ROOT/'practice/qa_summary.json').write_text(json.dumps(results,indent=2),encoding='utf-8')
print('TOTAL',len(results),'PDFs',sum(x['pages'] for x in results),'pages',sum(x['questions'] for x in results),'questions')
