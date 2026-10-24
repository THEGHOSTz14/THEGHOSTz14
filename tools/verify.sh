#!/usr/bin/env bash
# Rebuild every generated artefact, then fail if anything on the profile would break.
# Run this before and after every push:  bash tools/verify.sh
set -uo pipefail
cd "$(dirname "$0")/.."

status=0
python tools/build-card.py || status=1
python tools/build-readme.py || status=1

for gate in check-readme-links render-check check-live-profile; do
  if python "tools/${gate}.py"; then
    printf 'PASS  %s\n' "$gate"
  else
    printf 'FAIL  %s\n' "$gate"
    status=1
  fi
done

python - <<'PY' || exit 1
import pathlib, yaml
d = yaml.safe_load(pathlib.Path(".github/workflows/snake.yml").read_text(encoding="utf-8"))
steps = d["jobs"]["generate"]["steps"]
assert len(steps) == 2 and all("uses" in s for s in steps), "snake workflow steps changed shape"
assert d["permissions"]["contents"] == "write", "workflow cannot push the snake branch"
print("PASS  snake.yml")
PY

echo "verify: $([ "$status" -eq 0 ] && echo OK || echo FAILED)"
exit $status
