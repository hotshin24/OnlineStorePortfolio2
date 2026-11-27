# 재고(INV) 결정 기록을 결정 하나당 HTML 하나로 만든다 (주문·결제 결정 PDF와 같은 이름 형식 *_NN-NN_제목, 테이블 단계는 *_T-NN_제목, 컬럼 검토는 *_IC-NN_제목).
# 데이터와 본문은 decision.py에 있다. 모든 결정은 2026-11-27 대화로 했다 (다른 날 결정하면 날짜를 번호별로 나눈다).
# 사용: python3 split.py <출력폴더>  → <출력폴더>/재고결정_<NN-NN>_<제목>.html과 목록 names.txt
#       각 HTML을 Chrome headless로 PDF → docs/pdf/결정/재고결정/
import os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from decision import C, CSS, EXTRA_CSS, il, one


def fname(no, title):
    t = re.match(r'(T|IC)-(\d+)$', no)
    if t: return f"재고결정_{t.group(1)}-{int(t.group(2)):02d}_{re.sub(r'[^0-9A-Za-z가-힣]', '', title)}"
    a, b = re.match(r'(\d+)-(\d+)', no).groups()
    return f"재고결정_{int(a):02d}-{int(b):02d}{'후속' if '후속' in no else ''}_{re.sub(r'[^0-9A-Za-z가-힣]', '', title)}"


def main(out):
    os.makedirs(out, exist_ok=True)
    names = []
    for c in C:
        no, ti, tg = c[0], c[1], c[2]
        meta = f'자체 브랜드 패션 온라인몰 DB 설계 · Oracle 21c XE · 재고(INV) 도메인 결정 · {tg.replace("`", "")} · 2026-11-27 대화로 결정'
        body = (f'<h1>재고 결정 {no}. {il(ti)}</h1><div class="meta">{meta}</div>'
                '<div class="box">질문, 설명·예시, 선택지, 추천 이유는 당시 대화 원문 그대로이고, 반영은 답을 받은 뒤 알린 내용이다. '
                '굵은 기호가 추천안, 파란 행이 고른 안이다.</div>' + one(c))
        n = fname(no, ti)
        doc = (f'<!doctype html><html lang="ko"><head><meta charset="utf-8"><title>재고 결정 {no}. {il(ti)}</title>'
               f'<style>{CSS}{EXTRA_CSS}</style></head><body>{body}</body></html>')
        open(os.path.join(out, n + '.html'), 'w', encoding='utf-8').write(doc)
        names.append(n)
    assert len(set(names)) == len(names)
    open(os.path.join(out, 'names.txt'), 'w', encoding='utf-8').write('\n'.join(names) + '\n')
    print(len(names))


if __name__ == '__main__':
    main(sys.argv[1])
