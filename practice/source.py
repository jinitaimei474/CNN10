from pathlib import Path
import re, json
ROOT = Path(__file__).resolve().parents[1]

def episodes():
    source = Path(r'C:\Users\mike\.codex\attachments\9268eead-9932-4582-a2ca-d00392677d32\pasted-text.txt').read_text(encoding='utf-8')
    blocks = [p.strip() for p in re.split(r'\n\s*\n', source) if p.strip()]
    en = [p for p in blocks[1:] if not re.search(r'[\u4e00-\u9fff]', p)]
    en = [p.replace('normal.I', 'normal. I').replace('sauna.And', 'sauna. And') for p in en]
    assert len(en) == 60
    first = dict(date='20260710', title='Why do we need eight hours of sleep?', en=en, inferred=False)
    rest = json.loads((ROOT/'batch/episodes.json').read_text(encoding='utf-8'))
    return [first] + rest

def selections():
    result = {}
    for line in (ROOT/'practice/targets.tsv').read_text(encoding='utf-8').splitlines():
        date, index, answer = line.split('\t')
        result.setdefault(date, []).append(dict(paragraph=int(index), answer=answer))
    return result

def audit():
    selected = selections()
    errors = []
    for ep in episodes():
        date = ep['date']
        targets = selected.get(date, [])
        if len(targets) != 30:
            errors.append(f'{date}: count {len(targets)}')
        for t in targets:
            en = ep['en'][t['paragraph']-1]
            pattern = r'(?<!\w)' + re.escape(t['answer']) + r'(?!\w)'
            matches = list(re.finditer(pattern, en))
            if len(matches) != 1:
                errors.append(f'{date} P{t["paragraph"]} {t["answer"]!r}: {len(matches)} matches')
            if not 1 <= len(t['answer'].split()) <= 3:
                errors.append(f'{date}: word limit {t["answer"]}')
        print(date, len(targets), 'targets')
    assert not errors, '\n'.join(errors)
    print('PASS: 21 episodes / 630 unique, bounded answer spans')

if __name__ == '__main__':
    audit()
