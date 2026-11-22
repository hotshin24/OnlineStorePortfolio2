import sys, os, re, html
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from content import P, HANDOFF, OPEN
def il(s):
    s = html.escape(s); p = s.split('`')
    return ''.join(f'<code>{x}</code>' if i % 2 else x for i, x in enumerate(p))
CSS = """
@page { size: A4; margin: 18mm 16mm; }
body { font-family: 'Apple SD Gothic Neo', sans-serif; font-size: 9.8pt; color:#222; line-height:1.6; }
h1 { font-size: 18pt; margin:0 0 4px; border-bottom: 3px solid #1f4e79; padding-bottom:6px; color:#1f4e79; }
.meta { color:#666; font-size:8.6pt; margin-bottom:12px; }
h2 { font-size: 13pt; margin:22px 0 8px; color:#fff; background:#1f4e79; padding:4px 8px; page-break-after: avoid; }
h3 { font-size: 10.6pt; margin:12px 0 3px; color:#1f4e79; page-break-after: avoid; }
ol.c { margin:2px 0 6px; padding-left:26px; } ol.c li { margin:2px 0; page-break-inside: avoid; }
.b { color:#888; font-size:8pt; white-space:nowrap; }
code { font-family: Menlo, monospace; font-size:8.6pt; background:#f1f1f1; padding:0 2px; }
table { border-collapse: collapse; width:100%; margin:4px 0 8px; } tr { page-break-inside: avoid; }
th, td { border:1px solid #bbb; padding:3px 6px; vertical-align:top; text-align:left; } th { background:#eef2f7; }
.box { border:1px solid #c9d6e6; background:#f6f9fc; padding:6px 10px; margin:6px 0; }
.toc td { border:none; padding:1px 6px; }
"""
CIRC = '①②③④⑤⑥⑦⑧⑨⑩⑪⑫⑬⑭⑮'
art = 0; body = ''; toc = ''
for ci, (ch, arts) in enumerate(P, 1):
    first = art + 1
    sec = f'<h2>제{ci}장 {il(ch)}</h2>'
    for title, cls in arts:
        art += 1
        sec += f'<h3>제{art}조 ({il(title)})</h3>'
        if len(cls) == 1:
            t, b = cls[0]; sec += f'<p>{il(t)} ' + (f'<span class="b">[{il(b)}]</span>' if b else '') + '</p>'
        else:
            sec += '<ol class="c" style="list-style:none;padding-left:4px">' + ''.join(
                f'<li>{CIRC[k]} {il(t)} ' + (f'<span class="b">[{il(b)}]</span>' if b else '') + '</li>' for k, (t, b) in enumerate(cls)) + '</ol>'
    toc += f'<tr><td>제{ci}장</td><td>{il(ch)}</td><td>제{first}조 ~ 제{art}조</td></tr>'
    body += sec
body += '<h2>부칙</h2><h3>제1조 (다른 도메인으로 넘기는 사항)</h3><p>아래 사항은 회원 도메인에서 정한 기준이며, 상세 구조는 해당 도메인에서 정한다.</p><table><tr><th>도메인</th><th>내용</th></tr>' + ''.join(f'<tr><td>{il(a)}</td><td>{il(b)}</td></tr>' for a, b in HANDOFF) + '</table>'
body += '<h3>제2조 (아직 정하지 않은 사항)</h3><p>아래 사항은 이 명세에 포함하지 않았으며, 정해지면 이 명세를 개정한다.</p><ol class="c">' + ''.join(f'<li>{il(x)}</li>' for x in OPEN) + '</ol>'
body += '<h3>제3조 (시행)</h3><p>이 명세는 2026-11-21 확정한 결정과 2026-11-22 법률 검토 결정(L1~L6)을 기준으로 한다.</p>'
head = ('<h1>회원 도메인 정책 명세</h1>'
        '<div class="meta">자체 브랜드 패션 온라인몰 DB 설계 · Oracle 21c XE · 2026-11-22 기준 (법률 검토 반영) · 회원 도메인 결정 1~47번, 선행 결정 1~17번, 법률 검토 결정 L1~L6의 명문화</div>'
        '<div class="box">이 문서는 회원 도메인에서 확정한 결정을 조문 형식으로 정리한 것이다. 각 항 끝의 [번호]는 근거 결정이다 (숫자만 있으면 회원 도메인 결정, "선행"은 선행 결정, "법률 L"은 법률 검토 결정). 법령 조문은 해당 정책의 법적 근거다. "변경"은 법률 검토로 바뀐 결정이다. '
        '테이블과 컬럼의 상세는 <code>docs/pdf/테이블_컬럼/회원/</code>, 결정 과정은 <code>docs/pdf/회원결정/</code>, 법률 검토 과정은 <code>docs/pdf/법률검토/</code>를 본다.</div>'
        f'<h3>목차</h3><table class="toc">{toc}<tr><td>부칙</td><td>다른 도메인으로 넘기는 사항, 미정 사항, 시행</td><td></td></tr></table>')
open(sys.argv[1], 'w', encoding='utf-8').write(f'<!doctype html><html lang="ko"><head><meta charset="utf-8"><title>회원 도메인 정책 명세</title><style>{CSS}</style></head><body>{head}{body}</body></html>')
print('articles', art)
