#!/usr/bin/env bash
# Convert a scene document to an editable .styk through the app's service, then re-import it to verify.
# Usage: export_styk.sh <doc.json> <out.styk>
set -euo pipefail
DOC="$1"; OUT="$2"; PORT="${STYK_PORT:-47831}"; BASE="http://127.0.0.1:$PORT"
TMP="$(mktemp -d)"
curl -sf -X POST "$BASE/api/import?filename=scene.json" -H "Origin: $BASE" --data-binary @"$DOC" > "$TMP/imported.json"
python3 - "$TMP" "$(basename "$OUT")" <<'EOF'
import json, sys
tmp, name = sys.argv[1], sys.argv[2]
d = json.load(open(f'{tmp}/imported.json'))
if not d.get('ok'): sys.exit(f"import failed: {d}")
json.dump({'document': d['document'], 'sourceId': d.get('sourceId'), 'format': 'styk', 'filename': name}, open(f'{tmp}/export.json', 'w'))
EOF
code=$(curl -s -X POST "$BASE/api/export" -H "Origin: $BASE" -H "Content-Type: application/json" \
  --data-binary @"$TMP/export.json" -o "$OUT" -w "%{http_code}")
[ "$code" = 200 ] || { echo "export failed ($code): $(cat "$OUT")" >&2; exit 1; }
curl -sf -X POST "$BASE/api/import?filename=check.styk" -H "Origin: $BASE" --data-binary @"$OUT" | python3 -c "
import json, sys
d = json.load(sys.stdin); doc = d['document']
print('verified', sys.argv[1], '-', len(doc['keyframes']), 'frames,', len(doc['figure_types']), 'figures')" "$OUT"
