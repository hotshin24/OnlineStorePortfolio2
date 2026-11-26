# 결정 원문에서 패턴 번호별 (제목, 고른 안, 고른 방식)을 읽는다. 축별 정리 문서(gen.py)가 쓴다.
# 결제: pay_decision/orig/*.md, 주문: ord_decision/d1~d3.py, 상품: prd_decision/data1~3.py. 회원은 결정 생성 스크립트가 없어 mbr.py에 직접 적었다.
import os, re, sys
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, '..')


def plain(s):
    """합니다체를 한다체로 바꾼다 (결제 원문은 대화체라 문서 문체와 맞춘다)."""
    s = s.replace('있습니다', '있다').replace('없습니다', '없다').replace('입니다', '이다').replace('아닙니다', '아니다')

    def bnida(m):  # 받침 ㅂ + 니다 → 받침 ㄴ + 다 (둡니다 → 둔다)
        c = ord(m.group(1)) - 0xAC00
        return chr(0xAC00 + c - 17 + 4) + '다'

    def seumnida(m):  # 받침 있는 어간 + 습니다 → 는다 (막습니다 → 막는다)
        return m.group(1) + '는다'
    s = re.sub(r'([가-힣])습니다', seumnida, s)
    s = re.sub(r'([가-힣])니다', lambda m: bnida(m) if (ord(m.group(1)) - 0xAC00) % 28 == 17 else m.group(0), s)
    return s


def first(s, n=170):
    """방식 설명에서 첫 문장(또는 첫 항목 앞)만 남긴다."""
    s = plain(s.replace('**', '').replace('<br>', ' '))
    s = re.split(r'\s•\s|\s•', s)[0].strip()
    m = re.search(r'^(.+?[다요]\.)(\s|$)', s)
    if m: s = m.group(1)
    return s if len(s) <= n else s[:n].rstrip() + '…'


def pay():
    sys.path.insert(0, os.path.join(ROOT, 'pay_decision'))
    import fields
    chosen = {'2-1': 'A', '7-1': 'C', '12-4': 'A'}
    out = {}
    for fi, (g, gi, cnt) in enumerate(fields.F, 1):
        for j in range(1, cnt + 1):
            k = f'{fi}-{j}'
            x = open(os.path.join(ROOT, 'pay_decision', 'orig', f'{fi:02d}-{j:02d}.md'), encoding='utf-8').read()
            q, ans = x.split('<!--ANSWER-->')
            title = re.search(r'^## \S+\. (.+)$', q, re.M).group(1)
            opts = {}
            for ln in q.split('\n'):
                if ln.startswith('| '):
                    cs = [c.strip() for c in ln.strip().strip('|').split('|')]
                    lab = cs[0].replace('*', '')
                    if re.fullmatch(r'[A-D]', lab) and len(cs) >= 4 and lab not in opts:
                        opts[lab] = cs[1].replace('`', '')
            ch = chosen.get(k) or re.search(r'\*\*사용자:\*\* ([a-dA-D])\s*$', ans, re.M).group(1).upper()
            out[k] = (title, ch, first(opts.get(ch, '')))
    assert len(out) == 76, len(out)
    return out


def ord_():
    sys.path.insert(0, os.path.join(ROOT, 'ord_decision'))
    import d1, d2, d3
    out = {}
    for f in d1.F + d2.F + d3.F:
        for p in f[2]:
            m = dict((o[0], o[1]) for o in p[3]).get(p[6], '')
            out[p[0]] = (p[1], p[6], first(m))
    assert len(out) == 80, len(out)
    return out


def prd():
    sys.path.insert(0, os.path.join(ROOT, 'prd_decision'))
    import data1, data2, data3
    out = {}
    for m in (data1, data2, data3):
        for d in m.DEC:
            no = str(d['no']); main = None; subs = []
            for s in d['subs']:
                o = dict((x[0], x[1]) for x in s['opts'])
                txt = o.get(s['chosen'], '')
                if s['id'] == no: main = [s['chosen'], txt]
                elif s['id'] in (no + ' 충돌', no + '-1 재확인'):
                    if s['id'] == no + ' 충돌':
                        main = [main[0] + ' → 충돌 확인 뒤 ' + s['chosen'], txt]
                    else:
                        subs.append(f"재확인 {s['chosen']}")
                else:
                    sid = s['id'].replace(' 세부', ' 세부')
                    subs.append(f"{sid} {s['chosen']}")
            out[no] = (d['title'], main[0] + (' · ' + ', '.join(subs) if subs else ''), first(main[1], 190))
    assert len(out) == 53, len(out)
    return out


LOAD = {'pay': pay, 'ord': ord_, 'prd': prd}
