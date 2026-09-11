from pathlib import Path
import json, zipfile, hashlib, html
from urllib.parse import quote
from pypdf import PdfReader
from source import ROOT, episodes

rows=json.loads((ROOT/'practice/manifest.json').read_text(encoding='utf-8'))
qa=json.loads((ROOT/'practice/qa_summary.json').read_text(encoding='utf-8'))
assert len(rows)==len(qa)==21
assert {r['date'] for r in rows}=={e['date'] for e in episodes()}
assert all(r['questions']==30 and r['integrity']=='PASS' for r in rows)
assert all(r['bounds']==r['inline_blanks']==r['render']=='PASS' for r in qa)
out=ROOT/'output'
pdfdir=out/'pdf/listening'
files=[pdfdir/r['file'] for r in rows]
assert len(list(pdfdir.glob('*.pdf')))==21
assert all((out/'pdf'/f'CNN10_{r["date"]}_中英对照.pdf').exists() for r in rows)
pages=sum(len(PdfReader(f).pages) for f in files)
assert pages==sum(r['pages'] for r in rows)==132
for r,f in zip(rows,files):
    assert 'ANSWER KEY' in PdfReader(f).pages[-1].extract_text()
    assert r['last_body_height']>=200

readme='''CNN 10 听力挖空练习（2026-07-10 至 2026-09-04）

共21期，每期独立PDF；每期30题，合计630题、132页。
每空填写1至3个英文单词。选题难度参考雅思听力，以新闻关键词、常用搭配和短语为主；这是一套原文挖空练习，非官方模拟试卷。

使用方法
1. 打开目录.html，按日期选择练习，也可直接打开对应的PDF。
2. 先浏览英文正文，再配合自己已有的本期视频听写；原文中保留P段落号，方括号内为题号。
3. 完成后重听检查，再查看每份PDF的最后一页答案。答案表附有原稿段落号，方便回查中英对照稿。
4. 每题1分，满分30分。自评不区分大小写，拼写、单复数与词形须符合原文；成绩不换算为雅思分数。
5. A4纸按实际大小打印。若需先隐藏答案，可先打印第1页至倒数第2页，末页答案另外保留。也可使用PDF阅读器的批注工具填写。

原稿说明
依据用户提供的文本及已整理的21份中英对照稿制作，未与视频核验。新闻事实、听写误差和片段缺失均可能来自所给原稿。
2026-08-07篇原稿未标日期，沿用此前按前后期次顺序暂定的日期，尚未核实。
练习正文省略原稿词汇注释及中文译文；2026-07-24的P49和2026-08-07的P36是英文词汇注释，也已省略，因此原稿段落号会跳号。
'''

def index_html(prefix):
    trs=[]
    for r in rows:
        d=r['date'];label=f'{d[:4]}-{d[4:6]}-{d[6:]}'
        if r['inferred']:label+='（日期暂定）'
        trs.append(f'<tr><td><a href="{prefix}{quote(r["file"])}">{label}</a></td><td>{html.escape(r["title"])}</td><td>30</td><td>{r["pages"]}</td></tr>')
    return '''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>CNN 10 听力练习目录</title><style>body{max-width:1000px;margin:48px auto;padding:0 24px;font:16px/1.7 Arial,"Microsoft YaHei",sans-serif;color:#172e42}h1{color:#b51e2b;font-size:30px}p{color:#577082}table{width:100%;border-collapse:collapse}th,td{text-align:left;padding:14px 12px;border-bottom:1px solid #d9e3ea}th{background:#e8eff3}tr:nth-child(even){background:#f2f6f8}a{color:#b51e2b}td:first-child{min-width:120px}td:nth-last-child(-n+2){white-space:nowrap}</style><h1>CNN 10 · 听力挖空练习</h1><p>2026.07.10—2026.09.04 · 21期 · 每期30题 · 合计630题、132页</p><p>每空填写1至3个英文单词。难度参考雅思听力；答案均在各期PDF末页，附原稿段落号。先听写，再对照答案和已有的中英对照稿复习。</p><p>依据用户原稿制作，未与视频核验。2026年8月7日篇日期为暂定。</p><table><thead><tr><th>日期 / 打开练习</th><th>本期标题</th><th>题数</th><th>页数</th></tr></thead><tbody>'''+''.join(trs)+'</tbody></table></html>'

(out/'CNN10_听力练习目录.html').write_text(index_html('pdf/listening/'),encoding='utf-8')
(out/'CNN10_听力练习说明.txt').write_text(readme,encoding='utf-8-sig')
bundle=out/'CNN10_20260710-20260904_21期听力挖空练习.zip'
with zipfile.ZipFile(bundle,'w',zipfile.ZIP_DEFLATED) as z:
    for f in files:z.write(f,f.name)
    z.writestr('目录.html',index_html(''))
    z.writestr('使用说明.txt','\ufeff'+readme)
with zipfile.ZipFile(bundle) as z:
    assert z.testzip() is None
    assert len([n for n in z.namelist() if n.endswith('.pdf')])==21
    for f in files:assert z.read(f.name)==f.read_bytes()
report=dict(pdf_count=21,questions=630,pages=pages,source_coverage='21 of 21',answer_pages='21 of 21 at end',visual_review='21 contact sheets / 132 pages reviewed; representative full pages reviewed',zip_integrity='PASS',bundle_bytes=bundle.stat().st_size,files=[dict(name=f.name,sha256=hashlib.sha256(f.read_bytes()).hexdigest()) for f in files])
(ROOT/'practice/delivery_validation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({k:v for k,v in report.items() if k!='files'},ensure_ascii=False,indent=2))
print(bundle)
