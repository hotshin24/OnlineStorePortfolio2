"""재고 결정 기록(IC-n 등)을 inv/decision.py의 C 끝에 더하고 CHANGED 변경 안내를 고친다.

사용: python3 tools/pdfgen/inv/add_decision.py <결정.txt> [<변경안내.txt>]

결정.txt 형식 (결정 하나는 @@번호로 시작):
  @@IC-81
  #title 제목            #target 대상(축)
  #what  무엇을 정하나 (다음 줄부터 여러 줄 가능, 간단한 마크다운)
  #ex    설명·예시
  #opt A  다음 세 줄: 방식 / 장점 / 단점 (선택지마다 반복)
  #rec A  #reason 추천 이유  #choice A  #answer 사용자 답변 원문  #apply 반영
변경안내.txt 형식:
  @@IC-17 =   다음 줄에 새 안내문 (끝은 "아래 본문은 당시 기록이다.")
  @@IC-24 +   다음 줄에 덧붙일 문장 (기존 안내의 "아래 본문은 당시 기록이다." 앞에 넣음)
결정 날짜는 decision.py의 day()가 번호로 정하므로, 다른 날 결정이면 day()를 먼저 고친다.
"""
import sys, os
P = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'decision.py')
DEC = sys.argv[1]
CHG = sys.argv[2] if len(sys.argv) > 2 else None
def lit(s, ind):
    parts = []
    while s:
        parts.append(s[:180]); s = s[180:]
    return ('\n' + ' ' * ind).join(repr(p) for p in parts)
recs = []
for blk in open(DEC, encoding='utf-8').read().split('@@')[1:]:
    lines = blk.split('\n'); no = lines[0].strip(); f = {}; opts = []; key = None; buf = []
    def flush():
        if key is None: return
        txt = '\n'.join(buf).strip('\n')
        if key.startswith('opt'):
            m, p, c = txt.split('\n'); opts.append((key[4:], m, p, c))
        else: f[key] = txt
    for ln in lines[1:]:
        if ln.startswith('#'):
            flush(); k, _, v = ln[1:].partition(' ')
            if k == 'opt': key = 'opt ' + v; buf = []
            else: key = k; buf = [v] if v else []
        else: buf.append(ln)
    flush()
    f['apply'] = f['apply'].replace(' \n', ' ').replace('\n', ' ')
    f['reason'] = f['reason'].replace('\n', ' ')
    o = [f"({no!r}, {f['title']!r}, {f['target']!r},", ' (' + lit(f['what'], 2) + '),', ' (' + lit(f['ex'], 2) + '), [']
    for a, m, p, c in opts:
        o.append(f" ({a!r}, (" + lit(m, 2) + '),'); o.append('  ' + lit(p, 2) + ','); o.append('  ' + lit(c, 2) + '),')
    o.append(f" ], {f['rec']!r}, (" + lit(f['reason'], 2) + '),')
    o.append(f" {f['choice']!r}, {f['answer']!r}, (" + lit(f['apply'], 2) + ')),')
    recs.append('\n'.join(o))
s = open(P, encoding='utf-8').read()
k = '\n]\nCHANGED = {\n'; assert s.count(k) == 1
s = s.replace(k, '\n' + '\n'.join(recs) + k)
# CHANGED
a = s.index('CHANGED = {\n'); b = s.index('\n}\n', a) + 3
ns = {}; exec(s[a:b], ns); ch = ns['CHANGED']
for blk in (open(CHG, encoding='utf-8').read().split('@@')[1:] if CHG else []):
    head, txt = blk.split('\n', 1); key, mode = head.split(); txt = txt.strip()
    if mode == '=':
        assert key not in ch, key; ch[key] = txt
    else:
        t = ch[key]; tail = '아래 본문은 당시 기록이다.'; assert t.endswith(tail), key
        ch[key] = t[:-len(tail)] + txt + ' ' + tail
out = ['CHANGED = {']
for kk, v in ch.items():
    out.append(f' {kk!r}: (' + lit(v, len(kk) + 6) + '),')
out.append('}\n')
s = s[:a] + '\n'.join(out) + s[b:]
open(P, 'w', encoding='utf-8').write(s)
print(len(recs), len(ch))
