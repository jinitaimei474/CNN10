from pathlib import Path
import json,subprocess,concurrent.futures,math
from PIL import Image,ImageOps,ImageDraw
import pdfplumber
root=Path(__file__).resolve().parent
reports=json.loads((root/'validation.json').read_text(encoding='utf-8'))
qa=root/'qa';qa.mkdir(exist_ok=True)
poppler=r'C:\Users\mike\.cache\codex-runtimes\codex-primary-runtime\dependencies\native\poppler\Library\bin\pdftoppm.exe'
def run(r):
 path=root.parent/'output/pdf'/r['file']; dest=qa/r['date'];dest.mkdir(exist_ok=True)
 subprocess.run([poppler,'-r','90','-png',str(path),str(dest/'page')],check=True,stdout=subprocess.DEVNULL,stderr=subprocess.PIPE)
 imgs=sorted(dest.glob('page-*.png'));assert len(imgs)==r['pages']
 sheet=Image.new('RGB',(1140,math.ceil(len(imgs)/3)*560),'#D6DEE4');draw=ImageDraw.Draw(sheet)
 for i,f in enumerate(imgs):
  x=i%3*380;y=i//3*560
  sheet.paste(ImageOps.contain(Image.open(f),(370,525)),(x+5,y+25));draw.text((x+8,y+7),r['date']+'  '+str(i+1),fill='black')
 sheet.save(qa/(r['date']+'.png'))
 with pdfplumber.open(path) as doc:
  for i,page in enumerate(doc.pages):
   for c in page.chars:
    assert c['x0']>=40 and c['x1']<=page.width-38 and c['top']>=15 and c['bottom']<=page.height-15,(r['date'],i,'outside margins',c)
 return r['date']
with concurrent.futures.ThreadPoolExecutor(max_workers=4) as ex:
 for d in ex.map(run,reports): print(d,'rendered, bounds PASS',flush=True)
print('TOTAL',len(reports),'PDFs',sum(x['pages'] for x in reports),'pages',sum(x['paragraphs'] for x in reports),'pairs')
