# 차수(1차 범위) 결정 기록: 결정 하나당 HTML 하나 → Chrome PDF → docs/pdf/결정/차수결정/
# 원문은 decision.txt (inv/add_decision.py와 같은 형식: @@번호, #title, #target, #what, #ex, #opt X 세 줄, #rec, #reason, #choice, #answer, #apply).
# 화면 모양은 재고 결정 PDF와 같다 (inv/decision.py의 one, CSS를 빌려 쓴다).
# 사용: python3 tools/pdfgen/scope/build.py <출력폴더>
import os, re, sys
H = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(H, '..', 'inv'))
from decision import CSS, EXTRA_CSS, il, one

DAY = '2026-11-28'


def load():
    recs = []
    for blk in open(os.path.join(H, 'decision.txt'), encoding='utf-8').read().split('@@')[1:]:
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
        recs.append((no, f['title'], f['target'], f['what'], f['ex'], opts, f['rec'], f['reason'].replace('\n', ' '),
                     f['choice'], f['answer'], f['apply'].replace('\n', ' ')))
    return recs


def main(out):
    os.makedirs(out, exist_ok=True)
    for c in load():
        no, ti, tg = c[0], c[1], c[2]
        meta = f'자체 브랜드 패션 온라인몰 DB 설계 · Oracle 21c XE · 차수(1차 범위) 결정 · {tg.replace("`", "")} · {DAY} 대화로 결정'
        body = (f'<h1>차수 결정 {no}. {il(ti)}</h1><div class="meta">{meta}</div>'
                '<div class="box">질문, 설명·예시, 선택지, 추천 이유는 당시 대화 원문 그대로이고, 반영은 답을 받은 뒤 알린 내용이다. '
                '굵은 기호가 추천안, 파란 행이 고른 안이다. 2026-11-28 사용자 요청으로 대화 원문을 옮겨 적었다.</div>' + one(c))
        n = f"차수결정_{no}_{re.sub(r'[^0-9A-Za-z가-힣]', '', ti)}"
        open(os.path.join(out, n + '.html'), 'w', encoding='utf-8').write(
            f'<!doctype html><html lang="ko"><head><meta charset="utf-8"><title>차수 결정 {no}. {il(ti)}</title>'
            f'<style>{CSS}{EXTRA_CSS}</style></head><body>{body}</body></html>')
        print(n)


if __name__ == '__main__':
    main(sys.argv[1])
