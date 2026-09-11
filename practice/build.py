from pathlib import Path
import re, json, html, sys
from collections import defaultdict
from reportlab.pdfgen import canvas
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.pagesizes import A4
from pypdf import PdfReader
import pdfplumber
from source import ROOT, episodes, selections, audit

OUT = ROOT/'output/pdf/listening'
OUT.mkdir(parents=True, exist_ok=True)
for name, file in [('EN','arial.ttf'),('ENB','arialbd.ttf'),('ZH','msyh.ttc'),('ZHB','msyhbd.ttc')]:
    pdfmetrics.registerFont(TTFont(name, 'C:/Windows/Fonts/'+file, subfontIndex=0))
INK = colors.HexColor('#172E42')
MUTED = colors.HexColor('#577082')
RED = colors.HexColor('#B51E2B')
LIGHT = colors.HexColor('#F2F6F8')
WIDTH = A4[0]-96
ST = {
    'body': ParagraphStyle('body',fontName='EN',fontSize=10.5,leading=22,textColor=INK,spaceAfter=10,allowWidows=0,allowOrphans=0),
    'note': ParagraphStyle('note',fontName='ZH',fontSize=8.5,leading=14,textColor=MUTED,wordWrap='CJK'),
    'instructions': ParagraphStyle('instructions',fontName='ZH',fontSize=9.5,leading=17,textColor=INK,wordWrap='CJK'),
    'section': ParagraphStyle('section',fontName='ZHB',fontSize=13,leading=20,textColor=RED,spaceBefore=10,spaceAfter=12,keepWithNext=True),
    'answer': ParagraphStyle('answer',fontName='EN',fontSize=10.5,leading=16,textColor=INK),
    'number': ParagraphStyle('number',fontName='ENB',fontSize=10,leading=16,textColor=RED),
    'ref': ParagraphStyle('ref',fontName='EN',fontSize=8,leading=16,textColor=MUTED),
}
def p(s, style='note'):
    return Paragraph(html.escape(s), ST[style])

class PageCanvas(canvas.Canvas):
    def __init__(self,*args,issue='',**kwargs):
        super().__init__(*args,**kwargs)
        self.states=[]
        self.issue=issue
    def showPage(self):
        self.states.append(dict(self.__dict__))
        self._startPage()
    def save(self):
        total=len(self.states)
        for state in self.states:
            self.__dict__.update(state)
            w,h=A4
            self.setStrokeColor(colors.HexColor('#D9E3EA'))
            self.setLineWidth(.5)
            self.line(48,43,w-48,43)
            self.setFont('EN',8)
            self.setFillColor(MUTED)
            self.drawString(48,29,'CNN 10  |  '+self.issue+'  |  LISTENING PRACTICE')
            self.drawRightString(w-48,29,f'{self._pageNumber} / {total}')
            if self._pageNumber>1:
                self.setFont('ZH',8)
                self.drawString(48,h-29,'CNN 10 · 听力挖空练习')
                self.setFont('EN',8)
                self.drawRightString(w-48,h-29,self.issue.replace('-',''))
            canvas.Canvas.showPage(self)
        canvas.Canvas.save(self)

def prepare(ep, targets):
    spans=[]
    for t in targets:
        en=ep['en'][t['paragraph']-1]
        matches=list(re.finditer(r'(?<!\w)'+re.escape(t['answer'])+r'(?!\w)',en))
        assert len(matches)==1
        m=matches[0]
        spans.append(dict(**t,start=m.start(),end=m.end()))
    spans.sort(key=lambda t:(t['paragraph'],t['start']))
    bypara=defaultdict(list)
    for i,t in enumerate(spans,1):
        t['number']=i
        bypara[t['paragraph']].append(t)
    paragraphs=[]
    omitted={('20260724',49),('20260807',36)}
    for i,en in enumerate(ep['en'],1):
        if (ep['date'],i) in omitted:
            assert not bypara[i]
            continue
        chunks=[];cursor=0
        for t in bypara[i]:
            assert t['start']>=cursor
            chunks.append(en[cursor:t['start']])
            chunks.append(f'[[Q{t["number"]:02d}]]')
            cursor=t['end']
        chunks.append(en[cursor:])
        cloze=''.join(chunks)
        restored=cloze
        for t in bypara[i]:
            restored=restored.replace(f'[[Q{t["number"]:02d}]]',t['answer'],1)
        assert restored==en, f'Original restoration mismatch: {ep["date"]} P{i}'
        paragraphs.append(dict(index=i,original=en,cloze=cloze))
    return spans,paragraphs

def cloze_html(para):
    text=html.escape(para['cloze'])
    def gap(m):
        return '<nobr><font color="#577082">['+m.group(1)+']&#160;'+'_'*29+'</font></nobr>'
    text=re.sub(r'\[\[Q(\d{2})\]\]',gap,text)
    return f'<font size="7.5" color="#577082">P{para["index"]:02d}</font>  '+text

def build(ep, targets, leading=22):
    date=ep['date'];issue=f'{date[:4]}-{date[4:6]}-{date[6:]}'
    spans,paras=prepare(ep,targets)
    story=[
        Paragraph('CNN 10',ParagraphStyle('brand',fontName='ENB',fontSize=25,leading=29,textColor=RED)),
        Spacer(1,7),
        Paragraph(issue.replace('-','.')+'  /  听力挖空练习',ParagraphStyle('date',fontName='ZH',fontSize=11,leading=17,textColor=MUTED)),
        Spacer(1,15),
        Paragraph(html.escape(ep['title']),ParagraphStyle('title',fontName='ENB',fontSize=19,leading=24,textColor=INK)),
        Spacer(1,15),
    ]
    rules=[
        '共30题。每空填写原文中的1至3个英文单词；留意拼写、单复数及词形。',
        '方括号[01]为题号，P01为原稿段落号。答案集中在末页，练习时请先遮住。',
        '建议先浏览正文，再配合本期视频听写；完成后重听检查，每题1分，满分30分。',
    ]
    box=Table([[p(rule,'instructions')] for rule in rules],colWidths=[WIDTH])
    box.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,-1),LIGHT),('LEFTPADDING',(0,0),(-1,-1),12),('RIGHTPADDING',(0,0),(-1,-1),12),('TOPPADDING',(0,0),(-1,-1),5),('BOTTOMPADDING',(0,0),(-1,-1),5)]))
    story.extend([box,Spacer(1,12),p('姓名：________________    练习日期：________________    得分：____ / 30','instructions'),Spacer(1,12),p('依据用户提供的字幕原稿制作，未与视频核验。难度参考雅思听力，采用原文挖空形式，非官方模拟试卷。')])
    if ep['inferred']:
        story.extend([Spacer(1,5),p('日期说明：本篇原稿未标日期；沿用中英对照稿暂定的2026年8月7日，日期尚未核实。')])
    story.append(p('听写正文  /  QUESTIONS 01–30','section'))
    body_style=ParagraphStyle('episode-body',parent=ST['body'],leading=leading)
    for para in paras:
        story.append(Paragraph(cloze_html(para),body_style))
    story.extend([PageBreak(),p('参考答案  /  ANSWER KEY','section'),p(issue+'  ·  共30题。以下为对应空格的原文答案；P编号便于回查中英对照稿。'),Spacer(1,6),p('本练习自评时不区分大小写，拼写与单复数须符合原文。每题1分；此分数不换算为雅思分数。'),Spacer(1,16)])
    rows=[[p('题号'),p('答案'),p('段落'),'',p('题号'),p('答案'),p('段落')]]
    for i in range(15):
        a,b=spans[i],spans[i+15]
        rows.append([p(f'{a["number"]:02d}','number'),p(a['answer'],'answer'),p(f'P{a["paragraph"]:02d}','ref'),'',p(f'{b["number"]:02d}','number'),p(b['answer'],'answer'),p(f'P{b["paragraph"]:02d}','ref')])
    half=(WIDTH-15)/2
    table=Table(rows,colWidths=[29,half-64,35,15,29,half-64,35],hAlign='LEFT')
    table.setStyle(TableStyle([('VALIGN',(0,0),(-1,-1),'TOP'),('BACKGROUND',(0,0),(-1,0),colors.HexColor('#E8EFF3')),('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,LIGHT]),('BACKGROUND',(3,0),(3,-1),colors.white),('LEFTPADDING',(0,0),(-1,-1),6),('RIGHTPADDING',(0,0),(-1,-1),6),('TOPPADDING',(0,0),(-1,-1),9),('BOTTOMPADDING',(0,0),(-1,-1),9),('LINEBELOW',(0,0),(2,0),.5,MUTED),('LINEBELOW',(4,0),(6,0),.5,MUTED)]))
    story.append(table)
    path=OUT/f'CNN10_{date}_听力挖空练习.pdf'
    def cm(*args,**kwargs):return PageCanvas(*args,issue=issue,**kwargs)
    SimpleDocTemplate(str(path),pagesize=A4,leftMargin=48,rightMargin=48,topMargin=49,bottomMargin=56,title=f'CNN 10 | {date} | Listening Practice',author='').build(story,canvasmaker=cm)
    reader=PdfReader(path)
    page_text=[pg.extract_text() for pg in reader.pages]
    answers=[i for i,t in enumerate(page_text) if 'ANSWER KEY' in t]
    assert answers==[len(page_text)-1], f'{date}: answer key must occupy only last page {answers}'
    with pdfplumber.open(path) as cropped_doc:
        last=cropped_doc.pages[-2]
        last_chars=last.crop((48,49,last.width-48,last.height-56)).chars
        last_body_height=max(c['bottom'] for c in last_chars)-49
        body='\n'.join(pg.crop((48,49,pg.width-48,pg.height-56)).extract_text() or '' for pg in cropped_doc.pages[:-1])
    if last_body_height<200 and leading>20:
        print(date,'balancing final body page; leading',leading-.5,flush=True)
        return build(ep,targets,leading-.5)
    key=page_text[-1]
    # Instructions include [01], so verify question markers within body paragraphs only.
    body=body[body.index('QUESTIONS 01–30')+len('QUESTIONS 01–30'):]
    found=re.findall(r'\[(\d{2})\]\s*_+',body)
    assert found==[f'{i:02d}' for i in range(1,31)],(date,found)
    norm=lambda s:re.sub(r'\s+','',s)
    for t in spans:
        assert norm(t['answer']) in norm(key),f'{date}: missing answer {t}'
    # Verify every original paragraph's visible segments survived PDF generation.
    normalized_body=norm(body)
    for para in paras:
        rendered=re.sub(r'\[\[Q(\d{2})\]\]',lambda m:'['+m[1]+']'+'_'*29,para['cloze'])
        assert norm(rendered) in normalized_body, f'{date}: incomplete paragraph P{para["index"]}'
    return dict(date=date,title=ep['title'],inferred=ep['inferred'],questions=30,pages=len(reader.pages),leading=leading,last_body_height=last_body_height,file=path.name,answers=spans,paragraphs=paras,integrity='PASS')

if __name__=='__main__':
    audit()
    data=selections();manifest=[]
    for ep in episodes():
        if len(sys.argv)>1 and ep['date'] not in sys.argv[1:]:continue
        entry=build(ep,data[ep['date']]);manifest.append(entry)
        print(ep['date'],entry['pages'],'pages / 30 questions / PASS',flush=True)
    path=ROOT/'practice/manifest.json'
    old=json.loads(path.read_text(encoding='utf-8')) if path.exists() else []
    merged={x['date']:x for x in old+manifest}
    path.write_text(json.dumps(sorted(merged.values(),key=lambda x:x['date']),ensure_ascii=False,indent=2),encoding='utf-8')
