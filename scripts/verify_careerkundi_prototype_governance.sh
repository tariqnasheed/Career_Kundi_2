#!/usr/bin/env bash
set -euo pipefail

REPO_DIR="${1:-/Users/tariqnasheed/Desktop/Career_Kundi_2_F3}"
PROTO="$REPO_DIR/docs/prototype/approved/careerkundi_complete_interface_v1"

required=(
  "$REPO_DIR/AGENTS.md"
  "$REPO_DIR/.cursor/rules/00-careerkundi-governance.mdc"
  "$REPO_DIR/.cursor/rules/10-approved-prototype-contract.mdc"
  "$REPO_DIR/.cursor/rules/20-evidence-and-scanner-security.mdc"
  "$REPO_DIR/.cursor/rules/30-frontend-prototype-traceability.mdc"
  "$REPO_DIR/.cursor/rules/40-phase-gate-and-evidence.mdc"
  "$REPO_DIR/docs/product/careerkundi_approved_prototype_governance.md"
  "$REPO_DIR/docs/product/careerkundi_approved_prototype_page_registry.md"
  "$PROTO/CareerKundi_Complete_Interface_Image_Manifest.json"
  "$PROTO/CareerKundi_Complete_Interface_Image_Index.md"
  "$REPO_DIR/prompts/cursor/01_Adopt_Approved_Prototype_Read_Only.md"
  "$REPO_DIR/prompts/cursor/02_0053_F28_Read_Only_Planning.md"
)

for path in "${required[@]}"; do
  if [ ! -e "$path" ]; then
    echo "MISSING: $path" >&2
    exit 1
  fi
done

python3 - "$PROTO/CareerKundi_Complete_Interface_Image_Manifest.json" <<'PY'
import json, sys
p=sys.argv[1]
data=json.load(open(p))
assert data["sheet_count"] == 135, data["sheet_count"]
refs=sorted(set(row["page_ref"] for row in data["pages"]))
assert refs[0] == "P01" and refs[-1] == "P46" and len(refs) == 46, refs
print("Prototype manifest OK: 135 sheets, P01-P46.")
PY

count="$(find "$PROTO/images" -type f -name '*.png' | wc -l | tr -d ' ')"
if [ "$count" != "135" ]; then
  echo "ERROR: Expected 135 PNG images, found $count" >&2
  exit 1
fi

echo "Prototype image count OK: $count"
echo
echo "Git status (verification does not stage anything):"
git -C "$REPO_DIR" status --short
echo
echo "CAREERKUNDI_PROTOTYPE_GOVERNANCE_INSTALL_OK"
