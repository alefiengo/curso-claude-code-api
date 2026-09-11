#!/usr/bin/env bash
# PostToolUse/Edit,Write hook: cuando el archivo editado afecta al esquema
# OpenAPI (app/main.py, app/models.py o app/schemas.py), regenera
# openapi.json con el comando canónico del README.md y avisa de que
# docs/esquema.md puede haber quedado desactualizado.
set -euo pipefail

entrada="$(cat)"
archivo="$(printf '%s' "$entrada" | jq -r '.tool_input.file_path // ""')"

case "$archivo" in
  */app/main.py|*/app/models.py|*/app/schemas.py) ;;
  *) exit 0 ;;
esac

raiz="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
cd "$raiz"

uv run python -c "import json, sys; from app.main import app; json.dump(app.openapi(), sys.stdout, indent=2, ensure_ascii=False); print()" > openapi.json

cat <<'EOF'
{
  "hookSpecificOutput": {
    "hookEventName": "PostToolUse",
    "additionalContext": "openapi.json se regeneró automáticamente. docs/esquema.md puede haber quedado desactualizado: si el cambio afectó modelos o migraciones, regénéralo con la skill describir-esquema."
  }
}
EOF
