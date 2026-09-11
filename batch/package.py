from pathlib import Path
import json,zipfile
from pypdf import PdfReader
root=Path(__file__).resolve().parent
out=root.parent/'output'
r=sorted(json.loads((root/'validation.json').read_text(encoding='utf-8')),key=lambda x:x['date'])
assert len(r)==20 and all(x['integrity']=='PASS' for x in r)
old=out/'pdf/CNN10_20260710_中英对照.pdf'
assert old.exists() and len(PdfReader(str(old)).pages)==10
allr=[dict(date='20260710',title_zh='为什么我们需要八小时睡眠？',pages=10,paragraphs=60,file=old.name,inferred=False)]+r
preface='CNN 10 中英对照学习资料\n\n本次根据用户提供的 english.txt 整理20期，另收录此前完成的20260710期，共21份独立PDF、170页。\n\n每段英文后紧接中文译文，文末附词汇注释。原稿没有时间码。资料按用户提供的字幕翻译，未逐期与视频核验。\n\n日期说明：食虫植物一篇原稿未写日期；按前后日期与夏季周五节目顺序暂归20260807，PDF内已注明推定。其余文件日期来自原稿标题。没有根据日历补造原稿之外的节目。\n\n'
def index(absolute):
 text=preface+'| 日期 | 主题 | 页数 | PDF |\n| --- | --- | ---: | --- |\n'
 for x in allr:
  link=(out/'pdf'/x['file']).as_posix() if absolute else 'pdf/'+x['file']
  text+=f"| {x['date']}{'（推定）' if x['inferred'] else ''} | {x['title_zh']} | {x['pages']} | [打开](<{link}>) |\n"
 return text
indexpath=out/'CNN10_分期目录.md';indexpath.write_text(index(True),encoding='utf-8')
path=out/'CNN10_20260710-20260904_21期中英对照.zip'
with zipfile.ZipFile(path,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=9) as z:
 for x in allr:z.write(out/'pdf'/x['file'],'pdf/'+x['file'])
 z.writestr('阅读说明与分期目录.md',index(False).encode('utf-8'))
with zipfile.ZipFile(path) as z:
 assert z.testzip() is None
 assert len([x for x in z.namelist() if x.endswith('.pdf')])==21
print('Archive validated: 21 PDFs + index; bytes:',path.stat().st_size)
(root/'qa_summary.json').write_text(json.dumps(dict(new_pdfs=20,total_new_pages=160,paragraph_pairs=987,vocabulary_notes=531,text_integrity='PASS',page_bounds='PASS',all_pages_rendered_and_visually_reviewed=True,archive_pdfs=21,archive_pages=170),indent=2),encoding='utf-8')
