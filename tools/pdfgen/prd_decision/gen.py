import html, re, os, sys
sys.path.insert(0, os.path.dirname(__file__))
import data1, data2, data3

DEC = data1.DEC + data2.DEC + data3.DEC
assert [d['no'] for d in DEC] == list(range(1, 54))
OUT = sys.argv[1]
os.makedirs(OUT, exist_ok=True)

def t(s):
    s = html.escape(s, quote=False)
    return re.sub(r'`([^`]+)`', r'<code>\1</code>', s)

CSS = '''
@page { size: A4; margin: 16mm 15mm 16mm 15mm; }
body { font-family: "Apple SD Gothic Neo", sans-serif; font-size: 10pt; color: #222; line-height: 1.55; }
h1 { color: #1f4e79; font-size: 19pt; border-bottom: 3px solid #1f4e79; padding-bottom: 6px; margin: 0 0 6px; }
.meta { color: #555; font-size: 9pt; margin-bottom: 14px; }
h2 { color: #2a6099; font-size: 14pt; margin: 18px 0 8px; }
h3 { font-size: 11pt; margin: 14px 0 6px; }
table { border-collapse: collapse; width: 100%; margin: 4px 0 6px; font-size: 9.3pt; }
th, td { border: 1px solid #c9ced6; padding: 5px 7px; vertical-align: top; text-align: left; }
th { background: #edf0f4; font-weight: 600; }
tr.sel td { background: #e3eefb; }
td.lab { white-space: nowrap; width: 34px; }
td.rec { font-weight: 700; }
code { font-family: Menlo, monospace; font-size: 8.6pt; background: #f1f3f5; padding: 0 3px; border-radius: 3px; }
p { margin: 4px 0 8px; }
.rec { margin: 2px 0 10px; }
.ans { background: #f2f4f7; border-left: 5px solid #1f4e79; padding: 6px 12px; margin: 8px 0; font-weight: 600; }
.box { border: 1px solid #d5d9df; padding: 4px 14px 6px; margin: 8px 0; }
.box h4 { margin: 8px 0 4px; font-size: 10.5pt; }
ul { margin: 4px 0 6px; padding-left: 20px; }
.toc { columns: 2; column-gap: 28px; font-size: 10pt; }
.toc h4 { margin: 8px 0 2px; font-size: 10.5pt; break-after: avoid; }
.toc div { padding-left: 10px; }
.pat { break-inside: auto; } table { break-inside: avoid; } h2, h3 { break-after: avoid; }
.note { color: #444; font-size: 9.3pt; }
'''

def opt_table(sub, mark_sel):
    rows = ['<tr><th>선택지</th><th>방식</th><th>장점</th><th>단점</th></tr>']
    for (l, m, pro, con) in sub['opts']:
        cls = ' class="sel"' if mark_sel and l == sub['chosen'] else ''
        rc = ' rec' if l == sub['rec'] else ''
        rows.append(f'<tr{cls}><td class="lab{rc}">{l}</td><td>{t(m)}</td><td>{t(pro)}</td><td>{t(con)}</td></tr>')
    return '<table>' + ''.join(rows) + '</table>'

def rec_line(sub):
    if sub['rec']:
        return f'<p class="rec"><b>추천: {sub["rec"]}.</b> {t(sub["why"])}</p>'
    return f'<p class="rec"><b>추천:</b> {t(sub["why"])}</p>' if sub['why'] else ''

def page(title, body):
    return f'<!doctype html><html lang="ko"><head><meta charset="utf-8"><title>{html.escape(title)}</title><style>{CSS}</style></head><body>{body}</body></html>'

def decision(d):
    b = [f'<h1>상품 도메인 결정 {d["no"]}. {t(d["title"])}</h1>',
         f'<div class="meta">자체 브랜드 패션 온라인몰 DB 설계 · Oracle 21c XE · 결정일 {d["date"]} · 모든 결정은 사용자가 선택함 (파란 행 = 선택한 안, 굵은 글씨 = 추천안) · 테이블 이름은 모두 후보</div>',
         '<h2>결정 요약</h2><table><tr><th style="width:62px">번호</th><th style="width:150px">질문</th><th style="width:34px;white-space:nowrap">결정</th><th>내용</th></tr>']
    for s in d['subs']:
        m = next(o[1] for o in s['opts'] if o[0] == s['chosen'])
        b.append(f'<tr><td class="lab">{t(s["id"])}</td><td>{t(s["t"])}</td><td><b>{s["chosen"]}</b></td><td>{t(m)}</td></tr>')
    b.append('</table>')
    b.append('<h2>질문과 선택지 (결정 당시 제시한 내용)</h2>')
    if d['intro']:
        b.append(f'<p>{t(d["intro"])}</p>')
    for s in d['subs']:
        b.append(f'<h3>{t(s["id"])}. {t(s["t"])}</h3>')
        if s['intro']:
            b.append(f'<p>{t(s["intro"])}</p>')
        b.append(opt_table(s, True))
        b.append(rec_line(s))
    if d['links']:
        b.append(f'<h3>{d["no"]}번과 이어진 결정</h3><ul>' + ''.join(f'<li>{t(x)}</li>' for x in d['links']) + '</ul>')
    b.append('<h2>결정 과정</h2>')
    b.append(f'<div class="ans">사용자 답변: {t(d["answer"])}</div>')
    for (h, items) in d['process']:
        li = ('<ul>' + ''.join(f'<li>{t(x)}</li>' for x in items) + '</ul>') if items else ''
        b.append(f'<div class="box"><h4>{t(h)}</h4>{li}</div>')
    return page(f'상품 도메인 결정 {d["no"]}. {d["title"]}', ''.join(b))

def patterns():
    b = ['<h1>상품 도메인 설계 패턴 (1~53)</h1>',
         '<div class="meta">자체 브랜드 패션 온라인몰 DB 설계 · Oracle 21c XE / Spring Boot + Flyway (JPA 사용 안 함) · 2026-11-23 검토본, 2026-11-24 결정 단계 최종 선택지 기준</div>',
         '<p class="note">처음 17개로 설명했다가 판매 조건·운영 흐름·법정 표시·고객 기능 패턴을 더해 42개로 늘렸고, 외부 검토 자료와 대조해 기존 16개를 보완하고 11개(43~53번)를 더해 53개가 되었습니다. 선택지와 추천은 결정 단계에서 제시한 최종본이고, 굵은 글씨가 추천안입니다. 실제 선택은 <code>docs/pdf/결정/상품결정/</code>에 있습니다.</p>',
         '<h2>제목</h2><div class="toc">']
    g = None
    for d in DEC:
        if d['group'] != g:
            g = d['group']
            b.append(f'<h4>{t(g)}</h4>')
        b.append(f'<div>{d["no"]}. {t(d["title"])}</div>')
    b.append('</div>')
    b.append('<h2 style="break-before:page">추천이 바뀐 패턴</h2><ul>'
             '<li>6 상품 속성: A → C (상세 표시 속성까지 고정 컬럼으로 두면 NULL 컬럼이 크게 늘어남)</li>'
             '<li>15 세트·묶음 상품: C → D (묶어 생산하는 상품은 원래 SKU 하나)</li>'
             '<li>20 브랜드 구조: B → C (10번 시즌 마스터와 일관)</li>'
             '<li>21 컬러 체계: C → D (SKU 코드에 컬러 코드가 들어가 통일 필요)</li>'
             '<li>24 소재·혼용률: B → D (같은 원단 = 같은 소재 정보)</li>'
             '<li>39 판매·인기 집계: B → D (사이즈별 판매 비율이 리오더에 쓰임)</li>'
             '<li>46 세탁·취급 표시: 선택지 수정 (라벨은 완제품 단위)</li></ul>')
    for d in DEC:
        b.append(f'<div class="pat"><h2>{d["no"]}. {t(d["title"])}</h2>')
        if d['intro']:
            b.append(f'<p>{t(d["intro"])}</p>')
        for s in d['subs']:
            if any(k in s['id'] for k in ('충돌', '재확인', '세부')):
                continue
            if s['id'] != str(d['no']):
                b.append(f'<h3>{t(s["id"])}. {t(s["t"])}</h3>')
            b.append(opt_table(s, False))
            b.append(rec_line(s))
        b.append('</div>')
    return page('상품 도메인 설계 패턴 (1~53)', ''.join(b))

os.makedirs(os.path.join(OUT, 'dec'), exist_ok=True)
names = []
for d in DEC:
    fn = f'상품결정_{d["no"]:02d}_{d["fname"]}'
    open(os.path.join(OUT, 'dec', fn + '.html'), 'w').write(decision(d))
    names.append(fn)
open(os.path.join(OUT, 'patterns.html'), 'w').write(patterns())
open(os.path.join(OUT, 'names.txt'), 'w').write('\n'.join(names) + '\n')
print(len(names))
