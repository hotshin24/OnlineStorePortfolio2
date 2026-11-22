#!/bin/bash
# 회원 도메인 PDF 생성: 공통코드, 테이블이름, 컬럼정의서, 정책명세, 회원결정 변경 안내 쪽
# 사용법: tools/pdfgen/build.sh [출력폴더] [--install]
#   출력폴더를 생략하면 임시 폴더에 만든다. --install이면 docs/pdf/의 해당 PDF를 덮어쓴다.
set -euo pipefail
export PYTHONDONTWRITEBYTECODE=1
HERE="$(cd "$(dirname "$0")" && pwd)"; ROOT="$(cd "$HERE/../.." && pwd)"
OUT="${1:-$(mktemp -d)}"; mkdir -p "$OUT"
CHROME="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"

python3 "$HERE/cmm/cmm.py" "$OUT/cmm.html"          # code_ids.json도 만든다 (컬럼정의서가 읽음)
python3 "$HERE/cols/render.py" "$OUT"               # names.html, columns.html
python3 "$HERE/policy/render.py" "$OUT/policy.html"
python3 "$HERE/decision_change/chg.py" "$OUT"       # chg17/28/31/39/47.html

for n in cmm names columns policy chg17 chg28 chg31 chg39 chg47; do
  "$CHROME" --headless=new --disable-gpu --no-pdf-header-footer --user-data-dir="$OUT/chrome-profile" \
    --print-to-pdf="$OUT/$n.pdf" "file://$OUT/$n.html" >/dev/null 2>&1
  echo "$n.pdf $(grep -a -E -c '/Type /Page($|[^s])' "$OUT/$n.pdf")쪽"
done

if [[ "${2:-}" == "--install" ]]; then
  P="$ROOT/docs/pdf"
  cp "$OUT/cmm.pdf"     "$P/테이블_컬럼/공통/공통코드_CMM_CODE_회원도메인.pdf"
  cp "$OUT/names.pdf"   "$P/테이블_컬럼/회원/회원_테이블이름_확정.pdf"
  cp "$OUT/columns.pdf" "$P/테이블_컬럼/회원/회원_컬럼정의서_검토용.pdf"
  cp "$OUT/policy.pdf"  "$P/정책명세/회원도메인_정책명세.pdf"
  find "$ROOT" -name '._*' -not -path '*/.git/*' -print0 | xargs -0 rm -f
  echo "설치 완료. 변경 안내 쪽(chg*.pdf)은 README의 방법으로 따로 붙인다."
fi
echo "출력: $OUT"
