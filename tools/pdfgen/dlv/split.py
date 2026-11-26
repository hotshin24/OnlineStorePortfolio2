# 배송 결정 기록을 결정 하나당 HTML 하나로 만든다 (다른 도메인의 결정별 PDF와 맞춤, 2026-11-27).
# 전체 묶음은 다른 도메인에 없어 두지 않는다 (사용자 A 선택). 데이터와 본문은 col_review.py에 있다.
# 사용: python3 split.py <출력폴더>  → <출력폴더>/배송결정_<번호>_<제목>.html 42개와 목록 names.txt
#       각 HTML을 Chrome headless로 PDF → docs/pdf/결정/배송결정/
import os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from col_review import C, STAGE, CSS, EXTRA_CSS, il, one


def fname(no, title):
    if no.startswith('DC-'):  # 정렬이 맞도록 두 자리
        no = 'DC-%02d' % int(no[3:])
    return f"배송결정_{no}_{re.sub(r'[^0-9A-Za-z가-힣]', '', title)}"


def main(out):
    os.makedirs(out, exist_ok=True)
    names = []
    for c in C:
        no, ti, tg = c[0], c[1], c[2]
        stage = next(g for g, f in STAGE if f(no))
        meta = (f'자체 브랜드 패션 온라인몰 DB 설계 · Oracle 21c XE · 배송 도메인 결정 · {stage} · '
                '2026-11-26 대화로 결정')
        body = (f'<h1>배송 결정 {no}. {il(ti)}</h1><div class="meta">{meta}</div>'
                '<div class="box">질문과 선택지, 추천 이유는 당시 대화 원문 그대로이고, 반영은 답을 받은 뒤 알린 내용이다. '
                '굵은 기호가 추천안, 파란 행이 고른 안이다.</div>' + one(c))
        n = fname(no, ti)
        doc = (f'<!doctype html><html lang="ko"><head><meta charset="utf-8"><title>배송 결정 {no}. {il(ti)}</title>'
               f'<style>{CSS}{EXTRA_CSS}</style></head><body>{body}</body></html>')
        open(os.path.join(out, n + '.html'), 'w', encoding='utf-8').write(doc)
        names.append(n)
    assert len(set(names)) == len(names)
    open(os.path.join(out, 'names.txt'), 'w', encoding='utf-8').write('\n'.join(names) + '\n')
    print(len(names))


if __name__ == '__main__':
    main(sys.argv[1])
