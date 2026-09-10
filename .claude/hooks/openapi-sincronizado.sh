#!/usr/bin/env bash
# PreToolUse/Bash hook: bloquea `git commit` si openapi.json en la raíz no
# coincide con la especificación que genera el código ahora mismo.
#
# La regeneración usa el comando canónico del README.md (tabla "Desarrollo",
# fila "Regenerar openapi.json"). Si la comprobación se cuelga, el timeout del
# hook (configurado en .claude/settings.json) la corta y el commit falla.
set -euo pipefail

entrada="$(cat)"
comando="$(printf '%s' "$entrada" | jq -r '.tool_input.command // ""')"

# Doble guarda: el campo `if` del hook ya filtra por "Bash(git commit:*)",
# pero un `git commit` incrustado en una cadena más larga también cuenta.
case "$comando" in
  *"git commit"*) ;;
  *) exit 0 ;;
esac

raiz="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
cd "$raiz"

if [ ! -f openapi.json ]; then
  exit 0
fi

# Misma invocación que README.md. Salida a un temporal, no a openapi.json.
generado="$(mktemp)"
trap 'rm -f "$generado"' EXIT

uv run python -c "import json, sys; from app.main import app; json.dump(app.openapi(), sys.stdout, indent=2, ensure_ascii=False); print()" > "$generado"

if diff -q openapi.json "$generado" >/dev/null 2>&1; then
  exit 0
fi

cat <<'EOF'
{
  "hookSpecificOutput": {
    "hookEventName": "PreToolUse",
    "permissionDecision": "deny",
    "permissionDecisionReason": "openapi.json no coincide con la especificación que genera el código. Regenéralo con el comando de la tabla \"Desarrollo\" del README.md:\n\n  uv run python -c \"import json, sys; from app.main import app; json.dump(app.openapi(), sys.stdout, indent=2, ensure_ascii=False); print()\" > openapi.json\n\nRevisa el diff (git diff openapi.json), inclúyelo en este commit si el cambio de esquema es intencional, y vuelve a intentar el commit."
  }
}
EOF
exit 0
