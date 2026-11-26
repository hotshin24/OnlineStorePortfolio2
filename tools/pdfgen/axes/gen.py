# 결정을 마친 도메인(결제·주문·상품·회원)의 설계 패턴을 큰 결정 축으로 다시 묶은 문서. 배송 패턴 문서(dlv_pattern/gen.py)와 같은 형식이다.
# 축 구성과 패턴 비교는 사용자가 받은 외부 정리본(docs/pdf/설계패턴/*_N개축.pdf)을 바탕으로 하고, 고른 안은 결정 원문(src.py)에서 읽는다.
# 사용: python3 tools/pdfgen/axes/gen.py <pay|ord|prd|mbr> <출력.html>  → Chrome headless로 PDF
import os, sys, re, html, importlib
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import src

CSS = open(os.path.join(HERE, '..', 'ord_decision', 'style.css'), encoding='utf-8').read()
CSS += ('td.no { white-space: nowrap; width: 34px; } td.ti { width: 118px; } td.ch { width: 64px; } td.bs { width: 150px; } '
        'h4 { break-after: avoid; } .pat h3 + p { break-after: avoid; } tr.sel td { background: #e6effa; } '
        '.chg { color: #b03a00; } td.g { background: #eef2f7; font-weight: 700; white-space: nowrap; } '
        'table.dt { break-inside: auto; } table.dt tr { break-inside: avoid; } table.dt td.bs { width: 130px; }')

# 도메인마다 가장 무거운 축 (네 문서 끝에 같은 표를 둔다)
HEAVY = [
    ('회원', '상태·유형·자격 모델과 개인정보 생명주기', '누구이고, 지금 무엇을 할 수 있으며, 언제 잊어야 하는가'),
    ('상품', '시간에 따라 바뀌는 값 (가격, 판매 상태, 표시 내용)', '언제 얼마였고 무엇을 보여 줬는가'),
    ('주문', '금액 모델과 상태 모델', '무엇을 얼마에 샀고 지금 어디까지 왔는가'),
    ('결제', '결제 결과를 무엇으로 확정하는가', '돈이 실제로 움직였는가'),
    ('배송', '배송 데이터의 중심 단위', '무엇이 언제 어떤 상자로 나갔는가'),
]


def t(s):
    s = html.escape(str(s), quote=False)
    s = re.sub(r'`([^`]+)`', r'<code>\1</code>', s)
    return re.sub(r'\[(확인 필요[^\]]*)\]', r'<span class="warn">[\1]</span>', s)


def main(dom, out):
    m = importlib.import_module(dom)
    dec = m.DEC if hasattr(m, 'DEC') else src.LOAD[dom]()
    short = getattr(m, 'SHORT', {}); chg = getattr(m, 'CHG', {})
    common = getattr(m, 'COMMON', [])
    nums = [r[0] for ax in m.D.values() for _, rows in ax for r in rows] + [r[0] for _, rows in common for r in rows]
    assert len(nums) == len(set(nums)), [x for x in nums if nums.count(x) > 1]
    assert set(nums) == set(dec), (set(dec) - set(nums), set(nums) - set(dec))
    assert len(nums) == m.N, len(nums)
    for k in list(short) + list(chg): assert k in dec, k

    def row(no, rel):
        title, ch, txt = dec[no]
        body = t(short.get(no, txt))
        if no in chg: body += f'<br><span class="chg">바뀜: {t(chg[no])}</span>'
        return f'<tr><td class="no">{t(no)}</td><td class="ti">{t(title)}</td><td class="ch">{t(ch)}</td><td>{body}</td><td class="bs">{t(rel)}</td></tr>'

    head = '<tr><th>No</th><th>패턴</th><th>고른 안</th><th>결정 내용</th><th>{}</th></tr>'
    b = [f'<h1>{t(m.TITLE)}</h1>', f'<div class="meta">{t(m.META)}</div>',
         '<div class="box"><p>' + '</p><p>'.join(t(x) for x in m.INTRO) + '</p></div>']
    b.append('<h2>목차</h2><div class="toc">')
    for no, name, *_ in m.AXES:
        b.append(f'<h4>축 {no}. {t(name)} ({sum(len(r) for _, r in m.D[no])}개)</h4>')
        for g, rows in m.D[no]:
            if g: b.append(f'<div><b>{t(g)}</b></div>')
            b.append('<div>' + ', '.join(f'{r[0]} {t(dec[r[0]][0])}' for r in rows) + '</div>')
    if common:
        b.append(f'<h4>공통 규칙층 ({sum(len(r) for _, r in common)}개)</h4>')
        for g, rows in common:
            b.append(f'<div><b>{t(g)}</b> ' + ', '.join(f'{r[0]} {t(dec[r[0]][0])}' for r in rows) + '</div>')
    b.append('</div>')
    b.append('<h2>외부 정리본에서 바로잡은 점</h2><ol>' + ''.join(f'<li>{t(x)}</li>' for x in m.FIXES) + '</ol>')
    b.append(f'<h2>큰 틀: {len(m.AXES)}개 축</h2>')
    for no, name, desc, pats, sel, field, fit in m.AXES:
        b.append(f'<div class="pat"><h3>축 {no}. {t(name)}</h3><p>{t(desc)}</p>')
        b.append('<table><tr><th>패턴</th><th>구조</th><th>장점</th><th>단점</th></tr>')
        for p, s, a, c in pats:
            cls = ' class="sel"' if p[:1] == sel else ''
            b.append(f'<tr{cls}><td class="ti"><b>{t(p)}</b></td><td>{t(s)}</td><td>{t(a)}</td><td>{t(c)}</td></tr>')
        b.append('</table>')
        if field: b.append(f'<p class="note"><b>현업:</b> {t(field)}</p>')
        b.append(f'<p class="rec"><b>고른 안:</b> {t(fit)}</p></div>')
    b.append(f'<h3>{len(m.AXES)}개 축을 합친 그림</h3><table><tr><th>축</th><th>고른 안</th><th>그 결과로 생긴 핵심 단위</th></tr>')
    b += [f'<tr><td>{a}</td><td>{t(x)}</td><td>{t(y)}</td></tr>' for a, x, y in m.PICTURE]
    b.append('</table>')
    if getattr(m, 'PICTURE_NOTE', ''): b.append(f'<p>{t(m.PICTURE_NOTE)}</p>')
    b.append(f'<h2>세부 {len(nums)}개</h2><p>파란 행이 아니라 "고른 안" 칸이 결정이다. 붉은 글씨는 결정 뒤 컬럼 검토 등으로 바뀐 내용이다.</p>')
    for no, name, *_ in m.AXES:
        b.append(f'<h3>축 {no}. {t(name)}</h3>')
        for g, rows in m.D[no]:
            if g: b.append(f'<h4>{t(g)}</h4>')
            b.append('<table class="dt">' + head.format('이 축과의 관계') + ''.join(row(*r) for r in rows) + '</table>')
    if common:
        b.append(f'<h3>공통 규칙층</h3><p>{t(m.COMMON_NOTE)}</p>')
        for g, rows in common:
            b.append(f'<h4>{t(g)}</h4><table class="dt">' + head.format('얹히는 곳') + ''.join(row(*r) for r in rows) + '</table>')
    b.append('<h2>축 사이의 관계</h2><table><tr><th>축</th><th>다른 축에 주는 영향</th></tr>')
    b += [f'<tr><td class="ti">{t(a)}</td><td>{t(x)}</td></tr>' for a, x in m.RELATION]
    b.append('</table>')
    if getattr(m, 'REMAIN', []):
        b.append('<h2>아직 남은 일</h2><ul>' + ''.join(f'<li>{t(x)}</li>' for x in m.REMAIN) + '</ul>')
    b.append('<h2>도메인별 가장 무거운 축</h2><table><tr><th>도메인</th><th>가장 무거운 축</th><th>답하는 질문</th></tr>')
    b += [f'<tr><td class="ti">{t(a)}</td><td>{t(x)}</td><td>{t(y)}</td></tr>' for a, x, y in HEAVY]
    b.append('</table>')
    doc = (f'<!doctype html><html lang="ko"><head><meta charset="utf-8"><title>{t(m.TITLE)}</title>'
           f'<style>{CSS}</style></head><body>{"".join(b)}</body></html>')
    open(out, 'w', encoding='utf-8').write(doc)
    print(out, len(nums))


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
