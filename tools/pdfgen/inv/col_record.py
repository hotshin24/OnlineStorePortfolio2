# 재고 컬럼 검토 결정 기록 (IC-n만). 다른 도메인의 *_컬럼검토_결정.pdf와 같은 자리에 둔다 (배송 col_record.py와 같은 구조).
# 축 결정과 T-n은 docs/pdf/결정/재고결정/의 결정별 PDF에만 있다. 데이터와 본문 렌더링은 decision.py.
# 사용: python3 col_record.py <출력.html>  → Chrome headless로 PDF → docs/pdf/테이블_컬럼/재고/재고_컬럼검토_결정.pdf
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from decision import C, CSS, EXTRA_CSS, il, one


def main(out):
    ic = [c for c in C if c[0].startswith('IC-')]
    done = sum(1 for c in ic if c[8])
    diff = [c[0] for c in ic if c[8] and c[8] != c[6]]
    b = [f'<h1>재고 도메인 컬럼 검토 결정 (IC-1~IC-{len(ic)})</h1>',
         '<div class="meta">자체 브랜드 패션 온라인몰 DB 설계 · Oracle 21c XE · 2026-11-27~28 대화로 결정 · '
         f'재고 축 결정 54개와 테이블 결정 T-1~T-11, 컬럼 정의서(제안) 기준 · {done}개 결정, {len(ic) - done}개 답변 전'
         + (f' · 추천과 다른 결정 {", ".join(diff)}' if diff else '') + '</div>',
         '<div class="box">재고 테이블·컬럼을 설계하며 정할 사항을 질문으로 정리했다. 질문과 선택지, 추천 이유는 당시 대화 원문 그대로이고, '
         '반영은 답을 받은 뒤 알린 내용이다. 굵은 기호가 추천안, 파란 행이 고른 안이다. IC-1~IC-4는 사용자가 준 외부 제안(테이블 추가 없이 컬럼 보강)을 '
         '결정 기록과 대조해 바로잡은 뒤 물은 것이다. 축 결정과 테이블 결정(T-n)은 <code>docs/pdf/결정/재고결정/</code>에 결정 하나당 PDF로 있고, 컬럼 결정도 같은 내용이 결정별 PDF로 있다.</div>',
         '<h2>목록</h2><table><tr><th style="width:56px">번호</th><th>제목</th><th style="width:56px">선택</th></tr>'
         + ''.join(f'<tr><td>{c[0]}</td><td>{il(c[1])}</td><td>{c[8] or "답변 전"}</td></tr>' for c in ic) + '</table>']
    b += [one(c) for c in ic]
    open(out, 'w', encoding='utf-8').write(
        f'<!doctype html><html lang="ko"><head><meta charset="utf-8"><title>재고 도메인 컬럼 검토 결정</title>'
        f'<style>{CSS}{EXTRA_CSS}</style></head><body>{"".join(b)}</body></html>')
    print(out, len(ic))


if __name__ == '__main__':
    main(sys.argv[1])
