from pathlib import Path
import json,re,html,sys
from reportlab.pdfgen import canvas
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,KeepTogether,PageBreak,Table,TableStyle
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.pagesizes import A4
from pypdf import PdfReader
root=Path(__file__).resolve().parent
out=root.parent/'output/pdf'
out.mkdir(exist_ok=True,parents=True)
eps=json.loads((root/'episodes.json').read_text(encoding='utf-8'))
for name,file in [('EN','arial.ttf'),('ENB','arialbd.ttf'),('ZH','msyh.ttc'),('ZHB','msyhbd.ttc')]:
 pdfmetrics.registerFont(TTFont(name,'C:/Windows/Fonts/'+file,subfontIndex=0))
ink=colors.HexColor('#172E42'); muted=colors.HexColor('#577082'); red=colors.HexColor('#B51E2B')
styles={
 'en':ParagraphStyle('en',fontName='EN',fontSize=10.5,leading=15,textColor=ink,spaceAfter=5),
 'zh':ParagraphStyle('zh',fontName='ZH',fontSize=10,leading=16,textColor=colors.HexColor('#334B5B'),wordWrap='CJK'),
 'note':ParagraphStyle('note',fontName='ZH',fontSize=8,leading=12,textColor=muted,wordWrap='CJK'),
 'section':ParagraphStyle('section',fontName='ZHB',fontSize=12,leading=18,textColor=red,spaceBefore=12,spaceAfter=10,keepWithNext=True),
 'vocab':ParagraphStyle('vocab',fontName='ZH',fontSize=9,leading=14,textColor=ink,wordWrap='CJK')}
def p(s,style):return Paragraph(html.escape(s),styles[style])
class NumberedCanvas(canvas.Canvas):
 def __init__(self,*a,**kw):super().__init__(*a,**kw);self.saved=[]
 def showPage(self):self.saved.append(dict(self.__dict__));self._startPage()
 def save(self):
  count=len(self.saved)
  for s in self.saved:
   self.__dict__.update(s); w,h=A4
   self.setStrokeColor(colors.HexColor('#D9E3EA'));self.setLineWidth(.5);self.line(48,43,w-48,43)
   self.setFont('EN',8);self.setFillColor(muted);self.drawString(48,29,'CNN 10  |  '+self.issue);self.drawRightString(w-48,29,f'{self._pageNumber} / {count}')
   if self._pageNumber>1:
    self.setFont('ZH',8);self.drawString(48,h-29,'CNN 10 · 中英对照学习稿');self.setFont('EN',8);self.drawRightString(w-48,h-29,self.issue.replace('-',''))
   canvas.Canvas.showPage(self)
  canvas.Canvas.save(self)
report=[]
for ep in eps:
 date=ep['date']; zpath=root/(date+'.zh.txt')
 if not zpath.exists():continue
 if len(sys.argv)>1 and date not in sys.argv[1:]:continue
 zh=zpath.read_text(encoding='utf-8').splitlines();titlezh=zh.pop(0)
 assert len(zh)==len(ep['en']),f'{date}: {len(zh)} ZH != {len(ep["en"])} EN'
 issue=f'{date[:4]}-{date[4:6]}-{date[6:]}'
 story=[Paragraph('CNN 10',ParagraphStyle('brand',fontName='ENB',fontSize=25,leading=29,textColor=red)),Spacer(1,7),Paragraph(issue.replace('-','.')+'  /  中英对照学习稿',ParagraphStyle('date',fontName='ZH',fontSize=11,leading=17,textColor=muted)),Spacer(1,16),Paragraph(html.escape(ep['title']),ParagraphStyle('title',fontName='ENB',fontSize=19,leading=24,textColor=ink)),Spacer(1,5),Paragraph(html.escape(titlezh),ParagraphStyle('ctitle',fontName='ZHB',fontSize=17,leading=25,textColor=ink,wordWrap='CJK')),Spacer(1,13),p('根据用户提供的 english.txt 整理并翻译。英文段落下方为对应中文，原稿词汇注释收于文末。段落编号用于对照，原稿未提供时间码。','note'),Spacer(1,6),p('文字说明：保留英文原稿；译文按所给文本和上下文处理，未与视频核验。无法确定的听写或残句在译文中注明。','note')]
 if ep['inferred']:story += [Spacer(1,6),p('日期说明：本篇原稿未标日期；根据前后两期日期及夏季周五播出顺序，暂归为2026年8月7日，尚未核实。','note')]
 story += [Spacer(1,8),p('正文  /  英文与中文逐段对照','section')]
 for i,(en,cn) in enumerate(zip(ep['en'],zh),1):
  # Keep each English/Chinese pair on the same page.
  story.append(KeepTogether([Paragraph(f'<font name="ENB" color="#B51E2B">{i:02d}</font>  '+html.escape(en),styles['en']),p(cn,'zh'),Spacer(1,12)]))
 if ep['vocab']:
  story += [PageBreak(),p('学习词汇  /  原稿注释','section'),p('以下保留用户原稿的词汇释义，并省略音标；部分词义未必是本期语境中的用法，理解时请结合正文译文。','note'),Spacer(1,12)]
  rows=[]
  for v in ep['vocab']:
   v=re.sub(r'\[[^\]]*\]','',v);v=re.sub(r'\s+',' ',v).strip()
   rows.append([p(v,'vocab')])
  table=Table(rows,colWidths=[A4[0]-96],hAlign='LEFT')
  table.setStyle(TableStyle([('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),9),('RIGHTPADDING',(0,0),(-1,-1),9),('TOPPADDING',(0,0),(-1,-1),7),('BOTTOMPADDING',(0,0),(-1,-1),7),('ROWBACKGROUNDS',(0,0),(-1,-1),[colors.white,colors.HexColor('#F2F6F8')]),('LINEBELOW',(0,0),(-1,-1),.3,colors.HexColor('#DDE5EB'))]))
  story.append(table)
 path=out/f'CNN10_{date}_中英对照.pdf'
 def cm(*a,**kw):c=NumberedCanvas(*a,**kw);c.issue=issue;return c
 SimpleDocTemplate(str(path),pagesize=A4,rightMargin=48,leftMargin=48,topMargin=49,bottomMargin=56,title=f'CNN 10 | {date} | {titlezh}',author='').build(story,canvasmaker=cm)
 reader=PdfReader(str(path));full='\n'.join(pg.extract_text() for pg in reader.pages);norm=lambda s:re.sub(r'\s+','',s)
 for en,cn in zip(ep['en'],zh):
  assert norm(en) in norm(full),f'{date} missing EN: {en[:50]}'
  assert norm(cn) in norm(full),f'{date} missing ZH: {cn[:25]}'
 row=dict(date=date,title=ep['title'],title_zh=titlezh,inferred=ep['inferred'],paragraphs=len(zh),vocabulary=len(ep['vocab']),pages=len(reader.pages),file=path.name,integrity='PASS')
 report.append(row);print(date,len(zh),len(reader.pages),'PASS',flush=True)
old=json.loads((root/'validation.json').read_text(encoding='utf-8')) if (root/'validation.json').exists() else []
merged={x['date']:x for x in old+report}
(root/'validation.json').write_text(json.dumps(list(merged.values()),ensure_ascii=False,indent=2),encoding='utf-8')
