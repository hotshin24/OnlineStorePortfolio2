# 결제 도메인 설계 패턴(76개)과 결제결정 PDF용 HTML을 만든다.
# 원문은 orig/*.md (2026-11-25 대화에서 패턴을 하나씩 올린 메시지 그대로, <!--ANSWER--> 뒤는 답변과 그 뒤 기록).
# 사용: python3 tools/pdfgen/pay_decision/gen.py <출력폴더>  → patterns.html, dec/*.html, names.txt
import html, re, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, '..', 'ord_decision'))
import md, fields
_inline = md.inline
def inline(s):  # 결제 원문은 표 칸 안에서 <br>로 줄을 나눈다
    return _inline(s).replace('&lt;br&gt;', '<br>')
md.inline = inline
def t(s): return html.escape(s, quote=False)
def orig(k):
    a, c = k.split('-'); x = open(f'{HERE}/orig/{int(a):02d}-{int(c):02d}.md', encoding='utf-8').read()
    q, ans = x.split('<!--ANSWER-->'); return q, ans
def plain(s): return re.sub(r'<br>', ' ', s).replace('**', '').replace('`', '')

# 대화에서 답이 한 글자가 아니었던 것: 2-1은 "1 a, 2 a"의 2번, 7-1은 충돌 확인 뒤 다시 고른 절충안 C, 12-4는 질문 두 개에 "a"
CHOSEN = {'2-1': 'A', '7-1': 'C', '12-4': 'A'}
# 나중에 바뀐 결정: 결정 문서 맨 위에 변경 안내를 붙인다 (ord_decision/gen.py의 CHANGES와 같은 방식)
CHANGES = {
 '10-1': ('2026-11-26 결제 컬럼 검토 PYC-11 A, PYC-15 A로 일부 변경',
          '선택한 A(결제 행에 즉시 할인 컬럼 그룹을 두고, 주문 금액과 상품 배분은 건드리지 않음)는 그대로다. 바뀐 것은 할인 금액을 담는 방식이다. '
          '토스페이먼츠는 카드사 할인과 간편결제사 할인을 한 결제에 함께 돌려줄 수 있고 취소 내역도 부담 주체별로 준다는 외부 검토 지적에 따라, '
          '즉시 할인 금액 1개와 부담 주체 코드 대신 부담 주체별 금액 3개(카드사, 간편결제사, PG)를 결제 행과 취소 행에 둔다. 부담 주체 코드(INSTANT_DISCOUNT_FUNDER_CD)는 없앴다. '
          'CHECK는 요청 금액 = 승인 금액 + 할인 금액 3개의 합이다. PG 행사 코드·이름은 그대로다. '
          '기록은 docs/pdf/테이블_컬럼/결제/결제_컬럼검토_결정.pdf의 PYC-11, PYC-15.'),
}
NOTE = {
 '1-5': '1-4를 고른 뒤 사용자가 여신전문금융업법과 시행령을 법률 폴더에 올리고 검토를 지시했다. 검토 결과를 반영해 1-5를 다시 올렸고, 이 문서의 원문은 다시 올린 것이다. 처음 올린 원문과 검토 결과는 설계 패턴 문서 부록 3에 있다.',
 '2-1': '사용자 답 "1 a, 2 a" 중 2번이 2-1이다 (1번은 CLAUDE.md 개선안 A).',
 '2-2': '주문결정 1-2 A 원문의 예시(카드 + 네이버페이로 나눠 결제 = 결제 2건)와 충돌하는 것을 알리고 C를 받았다. 주문 1 : 결제 N 구조는 재시도와 추가 결제 때문에 유지한다. 주문결정 1-2에 변경 안내를 붙이는 일은 남아 있다. '
        'UK 조건은 뒤 패턴에서 넓혔다: 용도 ORDER이고 상태가 승인·결과 불명(3-7 A)·입금 대기(4-1 A)이며 이상 승인 표시가 N(3-8 A)인 행.',
 '7-1': '처음 답한 C(로그를 DB 밖에 둠)는 선행 6과 충돌하고 3-2 C의 전제를 바꿔서, 확정하기 전에 알리고 다시 물었다. 다시 고른 C는 절충안(DB에는 원문 없는 요약 행, 원문은 외부 로그 도구)이다. 원문 표의 C와 다르므로 원문 표에는 파란 행을 칠하지 않았다.',
 '12-4': '질문 두 개(출금 요청 처리, 원장 보관)에 사용자가 "a"로 답해 둘 다 A로 받았다.',
}
METHOD = {'7-1': '절충안: DB에는 원문 없이 요약 행(PG 업체 코드, API 종류, 결제·취소 ID, 요청·응답 일시, 소요 시간, 결과 코드·메시지, 성공 여부, 외부 로그 추적 ID)만 둔다. 원문은 외부 로그 도구에 두고 추적 ID로 찾아간다.',
          '12-4': '질문 1 A: 출금은 요청하는 순간 원장에서 차감하고, 실패하면 출금 취소 행으로 같은 입금 건에 되돌린다. 질문 2 A: 원장은 파티션 없이 두고, 남은 금액 0인 건만 마지막 변동 뒤 5년이 지나면 나눠서 DELETE한다.'}

def parse(k):
    q, ans = orig(k)
    title = re.search(r'^## \S+\. (.+)$', q, re.M).group(1)
    m = re.search(r'\*\*무엇을 정하나요\?\*\*\n(.+?)(?:\n\n|\n\|)', q, re.S)
    desc = plain(m.group(1).strip()) if m else ''
    opts = []; rec = None
    for ln in q.split('\n'):
        if ln.startswith('| ') and not ln.startswith('| 선택지') and not ln.startswith('|---'):
            cs = [c.strip() for c in ln.strip().strip('|').split('|')]
            lab = cs[0].replace('*', '')
            if re.fullmatch(r'[A-D]', lab) and len(cs) >= 4:
                if any(o[0] == lab for o in opts): break   # 12-4: 첫 표(질문 1)만
                opts.append((lab, plain(cs[1]), plain(cs[2]), plain(cs[3])))
                if cs[0].startswith('**'): rec = lab
    rm = re.search(r'\*\*추천: ([A-D])\.\*\*', q)
    rec = rm.group(1) if rm else rec
    ch = CHOSEN.get(k) or re.search(r'\*\*사용자:\*\* ([a-dA-D])\s*$', ans, re.M).group(1).upper()
    return (k, title, desc, opts, rec, ch)

F = []; P = []
n = 0
for fi, (g, gi, cnt) in enumerate(fields.F, 1):
    ps = [parse(f'{fi}-{j}') for j in range(1, cnt + 1)]
    F.append((g, gi, ps)); P += ps
assert len(P) == 76, len(P)

OUT = sys.argv[1]; os.makedirs(OUT + '/dec', exist_ok=True)
CSS = open(os.path.join(HERE, '..', 'ord_decision', 'style.css')).read()
def page(title, body): return f'<!doctype html><html lang="ko"><head><meta charset="utf-8"><title>{t(title)}</title><style>{CSS}</style></head><body>{body}</body></html>'
META = '자체 브랜드 패션 온라인몰 DB 설계 · Oracle 21c XE · 결제 도메인 · 테이블 이름은 모두 후보'
def field_md(fi):
    g, gi, ps = F[fi - 1]
    return f'## {fi}분야. {g}\n{gi}\n\n' + '\n'.join(f'- {p[0]} {p[1]}' for p in ps)

# 설계 패턴 문서
b = ['<h1>결제 도메인 설계 패턴 (12개 분야, 76개)</h1>',
     f'<div class="meta">{META} · 2026-11-25 기준 최종 패턴</div>',
     '<p class="note">처음 제안한 47개 패턴과 외부 정리본(11개 분야, 66개)을 합쳐 74개로 정리하고, 여신전문금융업법과 시행령 검토로 1-7(카드 가맹점 계약 형태)과 9-5(카드 본인 확인 방식 기록)를 더한 최종 76개 패턴이다. '
     '굵은 기호가 추천안이고 파란 행이 사용자가 고른 안이다. 사용자가 고른 안은 <code>docs/pdf/결정/결제결정/</code>에 패턴마다 한 파일로 있다.</p>',
     '<h2>제목</h2><div class="toc">']
for (g, gi, ps) in F:
    b.append(f'<h4>{t(g)} ({len(ps)})</h4>')
    b += [f'<div>{p[0]} {t(p[1])} — <b>{p[5]}</b></div>' for p in ps]
b.append('</div>')
# 메모한 선택 요약
rows = ['<tr><th>분야</th><th>A가 아닌 선택</th><th>나머지</th></tr>']
for fi, (g, gi, ps) in enumerate(F, 1):
    na = ', '.join(f'{p[0]} {p[5]}' for p in ps if p[5] != 'A') or '없음'
    rows.append(f'<tr><td>{fi}. {t(g)} ({len(ps)})</td><td>{na}</td><td>A</td></tr>')
nna = sum(p[5] != 'A' for p in P)
diff = [p for p in P if p[5] != p[4]]
b.append('<h2>고른 안 요약</h2><table>' + ''.join(rows) + f'</table><p>A가 아닌 선택은 {nna}개, A는 {76 - nna}개다. 추천과 다른 안을 고른 패턴: '
         + ', '.join(f'{p[0]}(추천 {p[4]} → {p[5]})' for p in diff) + '.</p>')
b.append('<p class="note">아래 본문은 2026-11-25 대화에서 패턴을 하나씩 올린 원문 그대로다 (설명, 이미 정한 것, 법에서 오는 조건, 예시, 선택지 표, 추천 이유, 고르면 생기는 것). 패턴마다 끝에 그때 받은 답과 답한 뒤 덧붙인 기록을 붙였다. 맨 뒤 부록에 패턴을 정리해 온 과정의 원문을 실었다.</p>')
for fi, (g, gi, ps) in enumerate(F, 1):
    b.append('<div style="break-before:page"></div>' + md.render(field_md(fi), shift=0))
    for p in ps:
        q, ans = orig(p[0])
        b.append(f'<div class="pat">{md.render(q, chosen=None if p[0] == "7-1" else p[5], shift=1)}<div class="box abox"><h4>{p[0]} 답변과 그 뒤 기록</h4>{md.render(ans, shift=3)}</div></div>')
b.append('<h2 style="break-before:page">부록: 패턴을 정리해 온 과정 (대화 원문)</h2>')
for i, ti in enumerate(['처음 제안 (9개 분야, 47개)', '외부 정리본과 합친 정리 (12개 분야, 74개)', '여신전문금융업법 검토 (76개로 변경)', '76개 검토를 마치고 메모한 선택'], 1):
    b.append(f'<h2 style="break-before:page">부록 {i}. {ti}</h2>' + md.render(open(f'{HERE}/orig/history_{i}.md', encoding='utf-8').read(), shift=1))
open(OUT + '/patterns.html', 'w').write(page('결제 도메인 설계 패턴', ''.join(b)))

# 결정 파일
names = []
for (g, gi, ps) in F:
    for p in ps:
        a, c = p[0].split('-')
        fn = f'결제결정_{int(a):02d}-{int(c):02d}_' + re.sub(r'[^0-9A-Za-z가-힣]', '', p[1])
        m = METHOD.get(p[0]) or next(o[1] for o in p[3] if o[0] == p[5])
        q, ans = orig(p[0])
        chg = ''
        if p[0] in CHANGES:
            h, x = CHANGES[p[0]]
            chg = f'<div class="ans" style="border-left-color:#b03a00;background:#fff6e0">변경 안내: {t(h)}</div><p>{t(x)}</p>'
        b = [f'<h1>결제 도메인 결정 {p[0]}. {t(p[1])}</h1>',
             f'<div class="meta">{META} · 분야: {t(g)} · 답변 2026-11-25 · 모든 결정은 사용자가 선택함 (파란 행 = 선택한 안, 굵은 글씨 = 추천안)</div>',
             chg + f'<h2>결정 요약</h2><table><tr><th style="width:50px">번호</th><th style="width:150px">질문</th><th style="width:34px;white-space:nowrap">결정</th><th>내용</th></tr><tr><td class="lab">{p[0]}</td><td>{t(p[1])}</td><td><b>{p[5]}</b></td><td>{t(m)}</td></tr></table>',
             '<h2>결정 당시 올린 원문 (2026-11-25 대화 그대로)</h2><p class="note">설명, 예시, 선택지 표(파란 행 = 선택한 안, 굵은 기호 = 추천안), 추천 이유, 고르면 생기는 것을 그때 올린 그대로 싣는다.</p>',
             md.render(q, chosen=None if p[0] == '7-1' else p[5], shift=1),
             f'<h2>결정 과정</h2><div class="ans">사용자 답변: {p[5]}</div>',
             '<h3>답변과 그 뒤 기록 (대화 원문)</h3>' + md.render(ans, shift=2),
             f'<div class="box"><h4>분야 소개</h4>{md.render(field_md(int(a)), shift=3)}</div>']
        if p[5] != p[4]:
            b.append(f'<p class="note">추천({p[4]})과 다른 안을 골랐습니다.</p>')
        if p[0] in NOTE:
            b.append(f'<div class="box"><h4>결정 단계에서 함께 기록한 내용</h4><p>{t(NOTE[p[0]])}</p></div>')
        open(f'{OUT}/dec/{fn}.html', 'w').write(page(f'결제 도메인 결정 {p[0]}', ''.join(b)))
        names.append(fn)
open(OUT + '/names.txt', 'w').write('\n'.join(names) + '\n')
print(len(names), 'A 아님', nna, '추천과 다름', [(p[0], p[4], p[5]) for p in diff])
