import html, re, os, sys
sys.path.insert(0, os.path.dirname(__file__))
import d1, d2, d3, md
HERE = os.path.dirname(os.path.abspath(__file__))
def orig(k):
    a, c = k.split('-'); x = open(f'{HERE}/orig/{int(a):02d}-{int(c):02d}.md', encoding='utf-8').read()
    q, ans = x.split('<!--ANSWER-->'); return q, ans
def field_intro(i): return open(f'{HERE}/orig/field_{i:02d}.md', encoding='utf-8').read()
F = d1.F + d2.F + d3.F
P = [p for f in F for p in f[2]]
assert len(P) == 80, len(P)
OUT = sys.argv[1]; os.makedirs(OUT + '/dec', exist_ok=True)
def t(s): return html.escape(s, quote=False)
CSS = open(os.path.join(os.path.dirname(__file__), 'style.css')).read()
def page(title, body): return f'<!doctype html><html lang="ko"><head><meta charset="utf-8"><title>{t(title)}</title><style>{CSS}</style></head><body>{body}</body></html>'
def table(p, mark):
    r = ['<tr><th>선택지</th><th>방식</th><th>장점</th><th>단점</th></tr>']
    for (l, m, a, b) in p[3]:
        cls = ' class="sel"' if mark and l == p[6] else ''
        rc = ' rec' if l == p[4] else ''
        r.append(f'<tr{cls}><td class="lab{rc}">{l}</td><td>{t(m)}</td><td>{t(a)}</td><td>{t(b)}</td></tr>')
    return '<table>' + ''.join(r) + '</table>'
def rec(p): return f'<p class="rec"><b>추천: {p[4]}.</b> {t(p[5])}</p>'
# 나중에 바뀐 결정: 결정 문서 맨 위에 변경 안내를 붙인다
CHANGES = {
 '5-5': ('2026-11-25 주문 컬럼 검토 OC-16 A로 일부 변경',
         '선택한 A(주문자·수령인·배송지를 주문 컬럼으로 둠)는 그대로다. 바뀐 것은 "바꾸면 덮어쓰고 이전 값은 데이터 변경 감사 로그에 남는다" 부분이다. '
         '감사 로그는 3년 보관이고 이전 값을 남기지 않는 방식(회원 C-16)이라 주문 보관 5년과 맞지 않는다는 외부 검토 지적에 따라, '
         '바꾸기 전 배송지는 암호화해 새 테이블 주문 변경 이력(ORD_ORDER_CHANGE_HIST)에 남기고 주문 개인정보와 같은 기한에 파기한다. '
         '기록은 docs/pdf/테이블_컬럼/주문/주문_컬럼검토_결정.pdf의 OC-16.'),
}
META = '자체 브랜드 패션 온라인몰 DB 설계 · Oracle 21c XE · 주문 도메인 · 테이블 이름은 모두 후보'
# 설계 패턴 전체 소개
b = ['<h1>주문 도메인 설계 패턴 (10개 분야, 80개)</h1>',
     f'<div class="meta">{META} · 2026-11-25 기준 최종 패턴</div>',
     '<p class="note">외부 검토 자료 두 개와 주문 관련 법령(전자상거래법과 시행령, 민법, 상법, 국세기본법, 개인정보 보호법) 검토를 반영해 다시 정리한 최종 80개 패턴입니다. 굵은 글씨가 추천안입니다. 사용자가 고른 안은 <code>docs/pdf/결정/주문결정/</code>에 패턴마다 한 파일로 있습니다. 법령 검토 결과는 <code>docs/pdf/법률검토/주문도메인_법률검토.pdf</code>(로컬 전용)에 있습니다.</p>',
     '<h2>제목</h2><div class="toc">']
for (g, gi, ps) in F:
    b.append(f'<h4>{t(g)} ({len(ps)})</h4>')
    b += [f'<div>{p[0]} {t(p[1])}</div>' for p in ps]
b.append('</div>')
b.append('<h2>추천이 바뀐 패턴</h2><ul><li>3-6 판매 채널·OS·유입 정보 위치: B → A (규칙 5가 기본이고 컬럼 7개는 무겁지 않음)</li><li>7-2 주문 상태와 클레임 상태의 경계: B → C (끝난 결과를 주문 상품에서 바로 보고, 출고하면 안 되는 상품을 상태로 거름)</li></ul>')
b.append('<p class="note">아래 본문은 2026-11-24 대화에서 패턴을 하나씩 올린 원문 그대로다 (설명, 예시, 선택지 표, 추천 이유, 고르면 생기는 컬럼). 패턴마다 끝에 그때 받은 답과 답한 뒤 덧붙인 기록을 붙였다. 맨 뒤 부록에 패턴을 정리해 온 과정의 원문을 실었다.</p>')
for fi, (g, gi, ps) in enumerate(F, 1):
    b.append(f'<div style="break-before:page"></div>' + md.render(field_intro(fi), shift=0))
    for p in ps:
        q, ans = orig(p[0])
        b.append(f'<div class="pat">{md.render(q, shift=1)}<div class="box abox"><h4>{p[0]} 답변과 그 뒤 기록</h4>{md.render(ans, shift=3)}</div></div>')
b.append('<h2 style="break-before:page">부록: 패턴을 정리해 온 과정 (대화 원문)</h2>')
for i, ti in enumerate(['처음 제안 (1)', '처음 제안 (2)', '처음 제안 (3)', '외부 정리본 두 개와 합친 정리 (73개)', '법률 검토 뒤 다시 정리 (80개)', '80개 검토를 마치고 메모한 선택'], 1):
    b.append(f'<h2 style="break-before:page">부록 {i}. {ti}</h2>' + md.render(open(f'{HERE}/orig/history_{i}.md', encoding='utf-8').read(), shift=1))
open(OUT + '/patterns.html', 'w').write(page('주문 도메인 설계 패턴', ''.join(b)))
# 결정 파일
names = []
for (g, gi, ps) in F:
    for p in ps:
        a, c = p[0].split('-')
        fn = f'주문결정_{int(a):02d}-{int(c):02d}_' + re.sub(r'[^0-9A-Za-z가-힣]', '', p[1])
        m = next(o[1] for o in p[3] if o[0] == p[6])
        chg = ''
        if p[0] in CHANGES:
            h, x = CHANGES[p[0]]
            chg = f'<div class="ans" style="border-left-color:#b03a00;background:#fff6e0">변경 안내: {t(h)}</div><p>{t(x)}</p>'
        b = [f'<h1>주문 도메인 결정 {p[0]}. {t(p[1])}</h1>',
             f'<div class="meta">{META} · 분야: {t(g)} · 답변 2026-11-24~25 · 모든 결정은 사용자가 선택함 (파란 행 = 선택한 안, 굵은 글씨 = 추천안)</div>',
             chg + f'<h2>결정 요약</h2><table><tr><th style="width:50px">번호</th><th style="width:150px">질문</th><th style="width:34px;white-space:nowrap">결정</th><th>내용</th></tr><tr><td class="lab">{p[0]}</td><td>{t(p[1])}</td><td><b>{p[6]}</b></td><td>{t(m)}</td></tr></table>',
             f'<h2>결정 당시 올린 원문 (2026-11-24 대화 그대로)</h2><p class="note">설명, 예시, 선택지 표(파란 행 = 선택한 안, 굵은 기호 = 추천안), 추천 이유, 고르면 생기는 컬럼을 그때 올린 그대로 싣는다.</p>',
             md.render(orig(p[0])[0], chosen=p[6], shift=1),
             f'<h2>결정 과정</h2><div class="ans">사용자 답변: {p[6]}</div>',
             '<h3>답변과 그 뒤 기록 (대화 원문)</h3>' + md.render(orig(p[0])[1], shift=2),
             f'<div class="box"><h4>분야 소개 (원문)</h4>{md.render(field_intro(int(p[0].split("-")[0])), shift=3)}</div>']
        if p[6] != p[4]:
            b.append(f'<p class="note">추천({p[4]})과 다른 안을 골랐습니다.</p>')
        if p[7]:
            b.append(f'<div class="box"><h4>결정 단계에서 함께 기록한 내용</h4><p>{t(p[7])}</p></div>')
        open(f'{OUT}/dec/{fn}.html', 'w').write(page(f'주문 도메인 결정 {p[0]}', ''.join(b)))
        names.append(fn)
open(OUT + '/names.txt', 'w').write('\n'.join(names) + '\n')
print(len(names))
