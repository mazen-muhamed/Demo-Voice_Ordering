#!/usr/bin/env bash
# End-to-end check of the session service, no phone required.
# Usage: ./scripts/smoke_test.sh   (SESSION_API_URL overrides the default)
set -euo pipefail

BASE="${SESSION_API_URL:-http://127.0.0.1:8001/api/v1}"
JSON='content-type: application/json'

echo "1) menu"
curl -fsS "$BASE/menu" | python3 -c 'import json,sys; m=json.load(sys.stdin); print("   %d items; first=%s" % (len(m), m[0]["name"]))'

echo "2) voice-order path (add -> request confirmation -> confirm)"
SID=$(curl -fsS -X POST "$BASE/sessions" -H "$JSON" -d '{"caller_number":"smoke-voice"}' \
  | python3 -c 'import json,sys; print(json.load(sys.stdin)["id"])')
curl -fsS -X POST "$BASE/sessions/$SID/items" -H "$JSON" \
  -d '{"name":"بيتزا مارجريتا","quantity":2}' >/dev/null
curl -fsS -X POST "$BASE/sessions/$SID/request-confirmation" -H "$JSON" -d '{}' >/dev/null
curl -fsS -X POST "$BASE/sessions/$SID/confirm" >/dev/null
curl -fsS "$BASE/sessions/$SID" \
  | python3 -c 'import json,sys; s=json.load(sys.stdin); print("   state=%s total=%s lines=%d" % (s["state"], s["total"], len(s["items"])))'

echo "3) DTMF floor (1 -> pending, 1 -> confirm)"
SID2=$(curl -fsS -X POST "$BASE/sessions" -H "$JSON" -d '{"caller_number":"smoke-dtmf"}' \
  | python3 -c 'import json,sys; print(json.load(sys.stdin)["id"])')
curl -fsS -X POST "$BASE/sessions/$SID2/items" -H "$JSON" \
  -d '{"name":"كولا","quantity":1}' >/dev/null
curl -fsS -X POST "$BASE/sessions/$SID2/dtmf" -H "$JSON" -d '{"digit":"1"}' >/dev/null
curl -fsS -X POST "$BASE/sessions/$SID2/dtmf" -H "$JSON" -d '{"digit":"1"}' >/dev/null
curl -fsS "$BASE/sessions/$SID2" \
  | python3 -c 'import json,sys; s=json.load(sys.stdin); print("   state=%s dtmf=%s" % (s["state"], ["%s:%s" % (d["digit"], d["action"]) for d in s["dtmf_history"]]))'

echo "4) by-caller lookup (what listener.py uses)"
SID3=$(curl -fsS -X POST "$BASE/sessions" -H "$JSON" -d '{"caller_number":"smoke-lookup"}' \
  | python3 -c 'import json,sys; print(json.load(sys.stdin)["id"])')
curl -fsS "$BASE/sessions/by-caller/smoke-lookup" \
  | python3 -c 'import json,sys; s=json.load(sys.stdin); print("   session=%s caller=%s" % (s["id"][:8] + "...", s["caller_number"]))'

echo "OK — session service, confirmation gate and DTMF floor are healthy."
